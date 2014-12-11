#############################################################################
#
# Copyright (C) 2014 Impex-Sat Gmbh & Co.KG
# Written by Sandro Cavazzoni <sandro@skanetwork.com>
# All Rights Reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#############################################################################

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.List import List

from OMBManagerCommon import OMB_DATA_DIR, OMB_UPLOAD_DIR, OMB_TMP_DIR
from OMBManagerLocale import _

from enigma import eTimer

import os
import glob
import struct

try:
	from boxbranding import *
	BRANDING = True
except:
	BRANDING = False

if BRANDING:
	OMB_GETBOXTYPE = getBoxType()
	OMB_GETBRANDOEM = getBrandOEM()
	OMB_GETIMAGEDISTRO = getImageDistro()
	OMB_GETIMAGEVERSION = getImageVersion()
	OMB_GETIMAGEFILESYSTEM = getImageFileSystem() # needed
	OMB_GETIMAGEFOLDER = getImageFolder() # needed
	OMB_GETMACHINEMTDKERNEL = getMachineMtdKernel()
	OMB_GETMACHINEKERNELFILE = getMachineKernelFile() # needed
	OMB_GETMACHINEMTDROOT = getMachineMtdRoot()
	OMB_GETMACHINEROOTFILE = getMachineRootFile() # needed
	OMB_GETMACHINEMKUBIFS = getMachineMKUBIFS()
	OMB_GETMACHINEUBINIZE = getMachineUBINIZE()
	OMB_GETMACHINEBUILD = getMachineBuild()
	OMB_GETMACHINEPROCMODEL = getMachineProcModel()
	OMB_GETMACHINEBRAND = getMachineBrand()
	OMB_GETMACHINENAME = getMachineName()
	OMB_GETOEVERSION = getOEVersion()
else:
	OMB_GETIMAGEFILESYSTEM = "ubi"
	f=open("/proc/mounts","r")
	for line in f:
		if line.find("rootfs")>-1:
			if line.find("jffs2")>-1:
				OMB_GETIMAGEFILESYSTEM = "jffs2"
				break

#
# SAMPLE-DATA BOXBRANDING
#
# getMachineBuild=gbquadplus<
# getMachineProcModel=gbquadplus<
# getMachineBrand=GigaBlue<
# getMachineName=Quad Plus<
# getMachineMtdKernel=mtd2<
# getMachineKernelFile=kernel.bin<
# getMachineMtdRoot=mtd0<
# getMachineRootFile=rootfs.bin<
# getMachineMKUBIFS=-m 2048 -e 126976 -c 4000 -F<
# getMachineUBINIZE=-m 2048 -p 128KiB<
# getBoxType=gbquadplus<
# getBrandOEM=gigablue<
# getOEVersion=OE-Alliance 2.3<
# getDriverDate=20140828<
# getImageVersion=4.2<
# getImageBuild=1<
# getImageDistro=openmips<
# getImageFolder=gigablue/quadplus<
# getImageFileSystem=ubi<
# 

OMB_DD_BIN = '/bin/dd'
OMB_CP_BIN = '/bin/cp'
OMB_RM_BIN = '/bin/rm'
OMB_UBIATTACH_BIN = '/usr/sbin/ubiattach'
OMB_UBIDETACH_BIN = '/usr/sbin/ubidetach'
OMB_MOUNT_BIN = '/bin/mount'
OMB_UMOUNT_BIN = '/bin/umount'
OMB_MODPROBE_BIN = '/sbin/modprobe'
OMB_RMMOD_BIN = '/sbin/rmmod'
OMB_UNZIP_BIN = '/usr/bin/unzip'
OMB_LOSETUP_BIN = '/sbin/losetup'
OMB_ECHO_BIN = '/bin/echo'
OMB_MKNOD_BIN = '/bin/mknod'

class OMBManagerInstall(Screen):
	skin = """
			<screen position="360,150" size="560,400">
				<widget name="info"
						position="10,10"
						size="540,50"
						font="Regular;18"
						zPosition="1" />
				<widget source="list"
						render="Listbox"
						position="10,60"
						zPosition="1"
						size="540,330"
						scrollbarMode="showOnDemand"
						transparent="1" >
						
					<convert type="StringList" />
				</widget>
			</screen>"""
			
	def __init__(self, session, mount_point, upload_list):
		Screen.__init__(self, session)
		
		self.setTitle(_('openMultiboot Install'))

		self.session = session
		self.mount_point = mount_point
		
		self['info'] = Label(_("Choose the image to install"))
		self["list"] = List(upload_list)
		self["actions"] = ActionMap(["SetupActions"],
		{
			"cancel": self.keyCancel,
			"ok": self.keyInstall
		})
		
	def keyCancel(self):
		self.close()
		
	def keyInstall(self):
		self.selected_image = self["list"].getCurrent()
		if not self.selected_image:
			return
			
		self.messagebox = self.session.open(MessageBox, _('Please wait while installation is in progress.\nThis operation may take a while.'), MessageBox.TYPE_INFO, enable_input = False)
		self.timer = eTimer()
		self.timer.callback.append(self.installPrepare)
		self.timer.start(100)
		self.error_timer = eTimer()
		self.error_timer.callback.append(self.showErrorCallback)
	
	
	def showErrorCallback(self):
		self.error_timer.stop()
		self.session.open(MessageBox, self.error_message, type = MessageBox.TYPE_ERROR)
		self.close()
		
	def showError(self, error_message):
		self.messagebox.close()
		self.error_message = error_message;
		self.error_timer.start(100)
		
	def guessIdentifierName(self, selected_image):
		selected_image = selected_image.replace(' ', '_')
		prefix = self.mount_point + '/' + OMB_DATA_DIR + '/'
		if not os.path.exists(prefix + selected_image):
			return selected_image
			
		count = 1
		while os.path.exists(prefix + selected_image + '_' + str(count)):
			count += 1
			
		return selected_image + '_' + str(count)
		
	def installPrepare(self):
		self.timer.stop()
		
		selected_image = self.selected_image
		selected_image_identifier = self.guessIdentifierName(selected_image)

		source_file = self.mount_point + '/' + OMB_UPLOAD_DIR + '/' + selected_image + '.zip'
		target_folder = self.mount_point + '/' + OMB_DATA_DIR + '/' + selected_image_identifier
		kernel_target_folder = self.mount_point + '/' + OMB_DATA_DIR + '/.kernels'
		kernel_target_file = kernel_target_folder + '/' + selected_image_identifier + '.bin'

		if not os.path.exists(kernel_target_folder):
			try:
				os.makedirs(kernel_target_folder)
			except OSError as exception:
				self.showError(_("Cannot create kernel folder %s") % kernel_target_folder)
				return
				
		if os.path.exists(target_folder):
			self.showError(_("The folder %s already exist") % target_folder)
			return
			
		try:
			os.makedirs(target_folder)
		except OSError as exception:
			self.showError(_("Cannot create folder %s") % target_folder)
			return

		tmp_folder = self.mount_point + '/' + OMB_TMP_DIR
		if os.path.exists(tmp_folder):
			os.system(OMB_RM_BIN + ' -rf ' + tmp_folder)			
		try:
			os.makedirs(tmp_folder)
			os.makedirs(tmp_folder + '/ubi')
			os.makedirs(tmp_folder + '/jffs2')
		except OSError as exception:
			self.showError(_("Cannot create folder %s") % tmp_folder)
			return
				
		if os.system(OMB_UNZIP_BIN + ' ' + source_file + ' -d ' + tmp_folder) != 0:
			self.showError(_("Cannot deflate image"))
			return

		nfifile = glob.glob('%s/*.nfi' % tmp_folder)
		if nfifile and not self.extractImageNFI(nfifile[0], tmp_folder):
			self.showError(_("Cannot extract nfi image"))
			return

		if self.installImage(tmp_folder, target_folder, kernel_target_file, tmp_folder):
			os.system(OMB_RM_BIN + ' -f ' + source_file)
			self.messagebox.close()
			self.close()

		os.system(OMB_RM_BIN + ' -rf ' + tmp_folder)

	def installImage(self, src_path, dst_path, kernel_dst_path, tmp_folder):
		if "ubi" in OMB_GETIMAGEFILESYSTEM:
			return self.installImageUBI(src_path, dst_path, kernel_dst_path, tmp_folder)
		elif "jffs2" in OMB_GETIMAGEFILESYSTEM:
			return self.installImageJFFS2(src_path, dst_path, kernel_dst_path, tmp_folder)
		else:
			self.showError(_("Your STB doesn\'t seem supported"))
			return False

	def installImageJFFS2(self, src_path, dst_path, kernel_dst_path, tmp_folder):
		mtdfile = "/dev/mtdblock0"
		for i in range(0, 20):
			mtdfile = "/dev/mtdblock%d" % i
			if not os.path.exists(mtdfile):
				break

		base_path = src_path + '/' + OMB_GETIMAGEFOLDER
		rootfs_path = base_path + '/' + OMB_GETMACHINEROOTFILE
		kernel_path = base_path + '/' + OMB_GETMACHINEKERNELFILE
		jffs2_path = src_path + '/jffs2'

		os.system(OMB_MODPROBE_BIN + ' loop')
		os.system(OMB_MODPROBE_BIN + ' mtdblock')
		os.system(OMB_MODPROBE_BIN + ' block2mtd')
		os.system(OMB_MKNOD_BIN + ' ' + mtdfile + ' b 31 0')
		os.system(OMB_LOSETUP_BIN + ' /dev/loop0 ' + rootfs_path)
		os.system(OMB_ECHO_BIN + ' "/dev/loop0,128KiB" > /sys/module/block2mtd/parameters/block2mtd')
		os.system(OMB_MOUNT_BIN + ' -t jffs2 ' + mtdfile + ' ' + jffs2_path)
		
		if os.path.exists(jffs2_path + '/usr/bin/enigma2'):
			os.system(OMB_CP_BIN + ' -rp ' + jffs2_path + '/* ' + dst_path)
			os.system(OMB_CP_BIN + ' ' + kernel_path + ' ' + kernel_dst_path)
			
		os.system(OMB_UMOUNT_BIN + ' ' + jffs2_path)
		os.system(OMB_RMMOD_BIN + ' block2mtd')
		os.system(OMB_RMMOD_BIN + ' mtdblock')
		os.system(OMB_RMMOD_BIN + ' loop')

		return True

	def installImageUBI(self, src_path, dst_path, kernel_dst_path, tmp_folder):
		for i in range(0, 20):
			mtdfile = "/dev/mtd" + str(i)
			if os.path.exists(mtdfile) is False:
				break
		mtd = str(i)

		#if OMB_GETBOXTYPE in ('whatever'):
		#	self.showError(_("Your STB doesn\'t seem supported"))
		#	return False

		base_path = src_path + '/' + OMB_GETIMAGEFOLDER
		rootfs_path = base_path + '/' + OMB_GETMACHINEROOTFILE
		kernel_path = base_path + '/' + OMB_GETMACHINEKERNELFILE
		ubi_path = src_path + '/ubi'

		virtual_mtd = tmp_folder + '/virtual_mtd'
		os.system(OMB_MODPROBE_BIN + ' nandsim cache_file=' + virtual_mtd + ' first_id_byte=0x20 second_id_byte=0xac third_id_byte=0x00 fourth_id_byte=0x15')
		if not os.path.exists('/dev/mtd' + mtd):
			os.system('rmmod nandsim')
			self.showError(_("Cannot create virtual MTD device"))
			return False

		os.system(OMB_DD_BIN + ' if=' + rootfs_path + ' of=/dev/mtdblock' + mtd + ' bs=2048')
		os.system(OMB_UBIATTACH_BIN + ' /dev/ubi_ctrl -m ' + mtd + ' -O 2048')
		os.system(OMB_MOUNT_BIN + ' -t ubifs ubi1_0 ' + ubi_path)
	
		if os.path.exists(ubi_path + '/usr/bin/enigma2'):
			os.system(OMB_CP_BIN + ' -rp ' + ubi_path + '/* ' + dst_path)
			os.system(OMB_CP_BIN + ' ' + kernel_path + ' ' + kernel_dst_path)
	
		os.system(OMB_UMOUNT_BIN + ' ' + ubi_path)
		os.system(OMB_UBIDETACH_BIN + ' -m ' + mtd)
		os.system(OMB_RMMOD_BIN + ' nandsim')
		
		return True

	# Based on nfi Extract by gutemine
	def extractImageNFI(self, nfifile, extractdir):
		nfidata = open(nfifile, 'r')
		header = nfidata.read(32)
		if header[:3] != 'NFI':
			print 'Sorry, old NFI format deteced'
			nfidata.close()
			return False
		else:
			machine_type = header[4:4+header[4:].find('\0')]
			if header[:4] == 'NFI3':
				machine_type = 'dm7020hdv2'

		print 'Dreambox image type: %s' % machine_type
		if machine_type == 'dm800' or machine_type == 'dm500hd' or machine_type == 'dm800se':
			flashsize=128  # we may have images larger then Flash 
			vidoff = 512
			bs = 512
			bso = 528
		elif machine_type == 'dm7020hd':
			flashsize = 1024
	                vidoff = 4096
			bs = 4096
			bso = 4224
		elif machine_type == 'dm8000':
	        	flashsize = 512
	                vidoff = 512
			bs = 2048
			bso = 2112
		else: # dm7020hdv2, dm500hdv2, dm800sev2
	        	flashsize = 1024
	                vidoff = 2048
			bs = 2048
			bso = 2112

		(total_size, ) = struct.unpack('!L', nfidata.read(4))
		print 'Total image size: %s Bytes' % total_size

		part = 0
		while nfidata.tell() < total_size:
		        (size, ) = struct.unpack('!L', nfidata.read(4))
			print 'Processing partition # %d size %d Bytes' % (part, size)
			output_names = { 2: 'kernel.bin', 3: 'rootfs.bin' }
			if part not in output_names:
				nfidata.seek(size, 1)
				print 'Skipping %d data...' % size
			else:
				print 'Extracting %s with %d blocksize...' % (output_names[part], bs)
				output_filename = extractdir + '/' + output_names[part];
				if os.path.exists(output_filename):
					os.remove(output_filename)
				output = open(output_filename, 'wb')
				for sector in range(size / bso):
					d = nfidata.read(bso)
					output.write(d[:bs])
				if p > 10:
					if p == 2:
						# padd boot image with zeros to 8MB to prevent corrupt kernel
						psize = 8
					else:
						# padd root image with zeros to flashsize
						psize = flashsize
					print 'Padding to %d MB ...' % psize
					blocks = psize*1024*1024 / bs
					output = open(output_filename, 'a')
					empty = open('/dev/zero', 'r').read(bso)
					while sector < blocks:
						output.write(empty[:bs])
						sector=sector+1
				output.close()
			part = part + 1

		nfidata.close()
		print 'Extracting %s to %s Finished!' % (nfifile, extractdir)

		return True
