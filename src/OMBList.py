from __future__ import print_function
from __future__ import absolute_import

import os
import json

from .BoxConfig import BoxConfig

from .OMBManagerCommon import OMB_DATA_DIR, OMB_UPLOAD_DIR
from .OMBConfig import omb_legacy

class OMBList():
	def __init__(self, mount_point, debug = True):
		mount_point = mount_point.rstrip("/")
		self.mount_point = mount_point
		self.data_dir = mount_point + '/' + OMB_DATA_DIR
		self.debug = debug
		self.debug_boxconfig = []
		self.images_list = []
		self.images_entries = []

		flashroot = "/"
		f = open("/proc/mounts", "r")
		for line in f:
			if line.find(self.data_dir + "/flash") > -1:
				flashroot = self.data_dir + "/flash"
		self.flashroot = flashroot
		self.boxinfo = BoxConfig(debug=self.debug, root = flashroot)

	def getBoxInfo(self):
		return self.boxinfo

	def imageTitleFromLabel(self, file_entry):
		f = open(self.data_dir + '/' + file_entry)
		label = f.readline().strip()
		f.close()
		return label

	def currentImage(self):
		selected = 'Flash'
		try:
			selected = open(omb_legacy and self.data_dir + '/.selected' or '%s/.%s-selected' % self.data_dir, self.boxinfo.getItem("model")).read()
		except:
			pass
		return selected

	def guessImageTitle(self, boxinfo, identifier):
		# for i in boxinfo.getItemsList():
		# 	print ("DEBUG:", i,boxinfo.getItem(i))

		try:
			# print (boxinfo.getItem("distro"))
			# print (boxinfo.getItem("imageversion"))
			return boxinfo.getItem("distro") + " " + str(boxinfo.getItem("imageversion"))
		except Exception as e:
			print ("OMB: ERROR %s" % e)
			return identifier

	def populateImagesList(self):

		self.debug_boxconfig.append(self.boxinfo.getItemsDict())

		file_entry = "flash"
		if os.path.exists(self.data_dir + '/.label_' + file_entry):
			title = self.imageTitleFromLabel('.label_' + file_entry)
		else:
			title = self.guessImageTitle(self.boxinfo, file_entry)

		self.images_entries.append({
			'label': title + ' (Flash)',
			'identifier': 'flash',
			'path': self.flashroot,
			'background': '/usr/share/bootlogo.mvi'
		})
		self.images_list.append(self.images_entries[0]['label'])

		if os.path.exists(self.data_dir):
			for file_entry in os.listdir(self.data_dir):
				if not os.path.isdir(self.data_dir + '/' + file_entry):
					continue

				if file_entry[0] == '.':
					continue

				if file_entry == "flash" or file_entry == '%s-flash' % self.boxinfo.getItem("model"):
					continue

				TargetBoxInfo = BoxConfig(root = self.data_dir + '/' + file_entry, debug=self.debug)

				self.debug_boxconfig.append(TargetBoxInfo.getItemsDict())

				# with following check you can switch back to your image in flash and  move your stick between different boxes.
				# print ("OMB: Compare flash model with target model %s %s" % (self.boxinfo.getItem("model"), TargetBoxInfo.getItem("model")))
				if self.boxinfo.getItem("model") != TargetBoxInfo.getItem("model"):
					continue

				if os.path.exists(self.data_dir + '/.label_' + file_entry):
					title = self.imageTitleFromLabel('.label_' + file_entry)
				else:
					title = self.guessImageTitle(TargetBoxInfo, file_entry)

				background = "/usr/share/bootlogo.mvi"
				if not os.path.exists(self.data_dir + '/' + file_entry + '/usr/share/bootlogo.mvi'):
					background = '/usr/share/' + self.boxinfo.getItem("brand") + '-bootlogo/bootlogo.mvi'

				self.images_entries.append({
					'label': title,
					'identifier': file_entry,
					'path': self.data_dir + '/' + file_entry,
					'labelfile': self.data_dir + '/' + '.label_' + file_entry,
					'kernelbin': self.data_dir + '/' + '.kernels' + '/' + file_entry + '.bin',
					'background': background
				})
				self.images_list.append(title)

	def getImagesList(self):
		return self.images_list

	def getImagesEntries(self):
		return self.images_entries

	def getJson(self, debug = None):
		parsed = { 'currentimage': self.currentImage(), 'images_entries': self.images_entries}
		if debug:
			parsed['debug_boxconfig'] = self.debug_boxconfig
		return json.dumps(parsed, indent=4)
