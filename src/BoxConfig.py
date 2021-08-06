#
#	derived from code by OpenVision now in OE-A replacing earlier BoxBranding extraction code  code by Huevos 
#	this version uses the base functionality without reinventing the wheel  
#
import errno
import os
from subprocess import Popen, PIPE, STDOUT
from elftools.elf.elffile import ELFFile
from elftools.elf.segments import InterpSegment

e2_path = '/usr/lib/enigma2/python'

class BoxConfig:  # To maintain data integrity class variables should not be accessed from outside of this class!
	def __init__(self, root="", debug=True):
		self.procList = []
		self.boxInfo = {}
		path = "%s/usr/lib/enigma.info" % root
		# print("[BoxConfig] BoxConfig Info path = %s." % path)
		lines = None

		try:
			with open(path, "r") as fd:
				lines = fd.read().splitlines()
				lines.append("probemode=boxconfig")
			if debug:
				print ("[BoxConfig(OMB)]: BoxConfig (%s)" % root)
		except (IOError, OSError) as err:
			if err.errno != errno.ENOENT:  # ENOENT - No such file or directory.
				print("[BoxConfig] Error %d: Unable to read lines from file '%s'! (%s)" % (err.errno, path, err.strerror))
			elif os.path.exists(root + e2_path + '/boxbranding.so'):
				if debug:
					print ("[BoxConfig(OMB)]: fallback BoxBranding (%s)" % (root + e2_path))
				# retrieve dynamic_loader for target path
				dynamic_loader = None
				header = None
				with open(root + "/usr/bin/enigma2", 'rb') as file:
					elffile = ELFFile(file)
					header = elffile.header
					for segment in elffile.iter_segments():
						if isinstance(segment, InterpSegment):
							dynamic_loader = segment.get_interp_name()

				# hack to fix loading of branding for image with different libc then the main one
				cmd = "LD_PRELOAD= LC_ALL=C LD_LIBRARY_PATH=" + root + "/lib:" + root + "/usr/lib "  + dynamic_loader + " " + root + "/usr/bin/python " + os.path.dirname(os.path.abspath(__file__)) + "/open-multiboot-branding-helper.py " + root + e2_path + " all"
				# print ("OMBDEBUG:", cmd)
				p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True, universal_newlines=True)
				rc = p.wait()
				if debug:
					print ("[BoxConfig(OMB)]: rc=%d" % rc)
				if rc == 0:
					lines = p.stdout.readlines()
					lines.append("probemode=boxbranding")
				else:
				#	print ("OMBDEBUG:", "\n".join(p.stdout.readlines()))
					lines = [ "dynamic_loader="+dynamic_loader , "boxbranding_stdout="+"\n".join(p.stdout.readlines()), "elf_machine=" + header['e_machine'] ]

		if not lines:
			lines = []
			if debug:
				print ("[BoxConfig(OMB)]: fallback Alternate (%s)" % root)

			distro_name = None
			distro_version = None
			
			if os.path.exists(root + "/etc/vtiversion.info"):
				(distro_name, distro_dummy1, distro_dummy2, distro_version) = open(root + "/etc/vtiversion.info", "r").readlines()[0].strip().split(" ")
				lines.append("distro=" + distro_name)
				lines.append("imageversion=" + distro_version)
			else:
				try:
					issue = "%s/etc/issue" % root
					(distro_name,distro_version) = open(issue, "r").readlines()[-2].split(" ")[0:2]
					lines.append("distro=" + distro_name)
					lines.append("imageversion=" + distro_version)
				except Exception as e:
					print ("OMBDEBUG:",e)
					pass

			try:
				archconffile = "%s/etc/opkg/arch.conf" % root
				box_type = None
				with open(archconffile, "r") as arch:
					for line in arch:
						archinfo = line.strip().split()
						if (distro_name == "openpli" and archinfo[2] == "41" or
						    distro_name != "openpli" and archinfo[2] == "21" ):
							box_type = archinfo[1]
					lines.append("model=" + box_type)
			except:
				pass

			if len(lines) != 3:
				lines = None
			else:
				lines.append("probemode=alernate")
				if debug:
					print ("[BoxConfig(OMB)]: Alternate [%s]" % ", ".join(lines))

		if lines:
			lines.append("ombroot=%s" % root)
			for line in lines:
				if line.startswith("#") or line.strip() == "":
					continue
				if "=" in line:
					item, value = [x.strip() for x in line.split("=", 1)]
					if item:
						self.procList.append(item)
						self.boxInfo[item] = self.processValue(value)
			self.procList = sorted(self.procList)

			if "brand" in self.boxInfo.keys() and self.boxInfo["brand"] == "vuplus" and self.boxInfo["model"][0:2] != "vu" and self.boxInfo["model"] != "bm750":
				self.boxInfo["model"] = "vu" + self.boxInfo["model"]
				if debug:
					print("[BoxConfig(OMB)]: buggy image, fixed model is %s" % self.boxInfo["model"])

			if "brand" in self.boxInfo.keys() and self.boxInfo["brand"] == 'formuler':
				if self.boxInfo["model"] != "formuler4turbo":
					self.boxInfo["brand"] = self.boxInfo["brand"][:9]

			# print("[BoxConfig] Information file data loaded into BoxConfig.")
			# print("[BoxConfig] ProcList = %s." % self.procList)
			# print("[BoxConfig] BoxInfo = %s." % self.boxInfo)
		else:
			print("[BoxConfig] ERROR: Information file is not available!  The system is unlikely to boot or operate correctly. (%s)" % root)


	def processValue(self, value):
		if value is None:
			pass
		elif value.startswith("\"") or value.startswith("'") and value.endswith(value[0]):
			value = value[1:-1]
		elif value.startswith("(") and value.endswith(")"):
			data = []
			for item in [x.strip() for x in value[1:-1].split(",")]:
				data.append(self.processValue(item))
			value = tuple(data)
		elif value.startswith("[") and value.endswith("]"):
			data = []
			for item in [x.strip() for x in value[1:-1].split(",")]:
				data.append(self.processValue(item))
			value = list(data)
		elif value.upper() == "NONE":
			value = None
		elif value.upper() in ("FALSE", "NO", "OFF", "DISABLED"):
			value = False
		elif value.upper() in ("TRUE", "YES", "ON", "ENABLED"):
			value = True
		elif value.isdigit() or (value[0:1] == "-" and value[1:].isdigit()):
			value = int(value)
		elif value.startswith("0x") or value.startswith("0X"):
			value = int(value, 16)
		elif value.startswith("0o") or value.startswith("0O"):
			value = int(value, 8)
		elif value.startswith("0b") or value.startswith("0B"):
			value = int(value, 2)
		else:
			try:
				value = float(value)
			except ValueError:
				pass
		return value

	def getProcList(self):
		return self.procList

	def getItemsList(self):
		return sorted(list(self.boxInfo.keys()))

	def getItem(self, item, default=None):
		if item in self.boxInfo:
			value = self.boxInfo[item]
		else:
			value = default
		return value

	def setItem(self, item, value):
		self.boxInfo[item] = value
		return True

	def deleteItem(self, item):
		if item in self.procList:
			print("[BoxConfig] Error: Item '%s' is immutable and can not be deleted!" % item)
		elif item in self.boxInfo:
			del self.boxInfo[item]
			return True
		return False

	def getItemsDict(self):
		return self.boxInfo
