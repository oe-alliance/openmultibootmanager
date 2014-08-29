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

from Components.Harddisk import harddiskmanager

from Screens.MessageBox import MessageBox

from OMBManagerList import OMBManagerList
from OMBManagerCommon import OMB_MAIN_DIR, OMB_DATA_DIR, OMB_UPLOAD_DIR
from OMBManagerLocale import _

from enigma import eTimer

import os

class OMBManagerInit:
	def __init__(self, session):
		self.session = session

		message = _("Where do you want to install openMultiboot?")
		disks_list = []
		for partition in harddiskmanager.getMountedPartitions():
			if partition and partition.mountpoint and partition.device and partition.mountpoint != '/' and partition.device[:2] == 'sd':
				disks_list.append((partition.description, partition))

		if len(disks_list) > 0:
			self.session.openWithCallback(self.initCallback, MessageBox, message, list=disks_list)
		else:
			self.session.open(
				MessageBox,
				_("No suitable devices found"),
				type = MessageBox.TYPE_ERROR
			)

	def getFSType(self, device):
		fin,fout = os.popen4("mount | cut -f 1,5 -d ' '")
		tmp = fout.read().strip()
		for line in tmp.split('\n'):
			parts = line.split(' ')
			if len(parts) == 2:
				if parts[0] == '/dev/' + device:
					return parts[1]
		return  "none"
		
	def createDir(self, partition):
		data_dir = partition.mountpoint + '/' + OMB_DATA_DIR
		upload_dir = partition.mountpoint + '/' + OMB_UPLOAD_DIR
		try:
			os.makedirs(data_dir)
			os.makedirs(upload_dir)
		except OSError as exception:
			self.session.open(
				MessageBox,
				_("Cannot create data folder"),
				type = MessageBox.TYPE_ERROR
			)
			return
		self.session.open(OMBManagerList, partition.mountpoint)
	
	def formatDevice(self, confirmed):
		if confirmed:
			self.messagebox = self.session.open(MessageBox, _('Please wait while format is in progress.'), MessageBox.TYPE_INFO, enable_input = False)
			self.timer = eTimer()
			self.timer.callback.append(self.doFormatDevice)
			self.timer.start(100)

	def doFormatDevice(self):
		self.timer.stop()
		self.error_message = ''
		if os.system('umount /dev/' + self.response.device) != 0:
			self.error_message = _('Cannot umount the device')
		else:
			if os.system('/sbin/mkfs.ext4 /dev/' + self.response.device) != 0:
				self.error_message = _('Cannot format the device')
			else:
				if os.system('mount /dev/' + self.response.device + ' ' + self.response.mountpoint) != 0:
					self.error_message = _('Cannot remount the device')
				
		self.messagebox.close()
		self.timer = eTimer()
		self.timer.callback.append(self.afterFormat)
		self.timer.start(100)
		
	def afterFormat(self):
		self.timer.stop()
		if len(self.error_message) > 0:
			self.session.open(
				MessageBox,
				self.error_message,
				type = MessageBox.TYPE_ERROR
			)
		else:
			self.createDir(self.response)
			
	def initCallback(self, response):
		if response:
			fs_type = self.getFSType(response.device)
			if fs_type not in ['ext3', 'ext4']:
				self.response = response
				self.session.openWithCallback(
					self.formatDevice,
					MessageBox,
					_("Filesystem not supported\nDo you want format your drive?"),
					type = MessageBox.TYPE_YESNO
				)
			else:
				self.createDir(response)

class OMBManagerKernelModule:
	def __init__(self, session):
		self.session = session

		message = _("You need the module kernel-module-nandsim to use openMultiboot\nDo you want install it?")
		disks_list = []
		for partition in harddiskmanager.getMountedPartitions():
			if partition.mountpoint != '/':
				disks_list.append((partition.description, partition.mountpoint))

		self.session.openWithCallback(self.installCallback, MessageBox, message, MessageBox.TYPE_YESNO)

	def installCallback(self, confirmed):
		if confirmed:
			self.messagebox = self.session.open(MessageBox,_('Please wait while installation is in progress.'), MessageBox.TYPE_INFO, enable_input = False)
			self.timer = eTimer()
			self.timer.callback.append(self.installModule)
			self.timer.start(100)
			
	def installModule(self):
		self.timer.stop()
		self.error_message = ''
		if os.system('opkg update && opkg install kernel-module-nandsim') != 0:
			self.error_message = _('Cannot install kernel-module-nandsim')
		
		self.messagebox.close()
		self.timer = eTimer()
		self.timer.callback.append(self.afterInstall)
		self.timer.start(100)
			
	def afterInstall(self):
		self.timer.stop()
		if len(self.error_message) > 0:
			self.session.open(
				MessageBox,
				self.error_message,
				type = MessageBox.TYPE_ERROR
			)
		else:
			OMBManager(self.session);
		
def OMBManager(session, **kwargs):
	found = False
	
	if os.system('opkg list_installed | grep kernel-module-nandsim') != 0:
		OMBManagerKernelModule(session)
		return
	
	data_dir = OMB_MAIN_DIR + '/' + OMB_DATA_DIR
	if os.path.exists(data_dir):
		session.open(OMBManagerList, OMB_MAIN_DIR)
		found = True
	else:
		for partition in harddiskmanager.getMountedPartitions():
			if partition.mountpoint != '/':
				data_dir = partition.mountpoint + '/' + OMB_DATA_DIR
				if os.path.exists(data_dir):
					session.open(OMBManagerList, partition.mountpoint)
					found = True
					break
				
	if not found:
		OMBManagerInit(session)

