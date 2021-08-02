from __future__ import absolute_import
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

from .OMBManagerList import OMBManagerList
from .OMBManagerCommon import OMB_MAIN_DIR, OMB_DATA_DIR, OMB_UPLOAD_DIR
from .OMBManagerInstall import OMB_GETIMAGEFILESYSTEM, BRANDING, OMB_UNJFFS2_BIN
from .OMBManagerLocale import _

from enigma import eTimer

import os
from subprocess import Popen, PIPE, STDOUT


class OMBManagerInit:
	def __init__(self, session):
		self.session = session

		message = _("Where do you want to install openMultiboot?")
		disks_list = []
		for partition in harddiskmanager.getMountedPartitions():
			if partition and partition.mountpoint and partition.device and partition.mountpoint != '/' and partition.device[:2] == 'sd':
				disks_list.append((partition.description, partition))

		if len(disks_list) > 0:
			disks_list.append((_("Cancel"), None))
			self.session.openWithCallback(self.initCallback, MessageBox, message, list=disks_list)
		else:
			self.session.open(
				MessageBox,
				_("No suitable devices found"),
				type=MessageBox.TYPE_ERROR
			)

	def getFSType(self, device):
		p = Popen("mount | cut -f 1,5 -d ' '", shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
		tmp = p.stdout.read().strip()
		for line in tmp.split('\n'):
			parts = line.split(' ')
			if len(parts) == 2:
				if parts[0] == '/dev/' + device:
					return parts[1]
		return "none"

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
				type=MessageBox.TYPE_ERROR
			)
			return
# by Meo. We are installing in flash. We can link init to open_multiboot
# so we can disable it in open multiboot postinst.
# In this way we will be sure to have not open_multiboot init in mb installed images.
		if os.path.isfile('/sbin/open_multiboot'):
			os.system("ln -sfn /sbin/open_multiboot /sbin/init")

		self.session.open(OMBManagerList, partition.mountpoint)

	def formatDevice(self, confirmed):
		if confirmed:
			self.messagebox = self.session.open(MessageBox, _('Please wait while format is in progress.'), MessageBox.TYPE_INFO, enable_input=False)
			self.timer = eTimer()
			self.timer.callback.append(self.doFormatDevice)
			self.timer.start(100)

	def doFormatDevice(self):
		self.timer.stop()
		self.error_message = ''
		if os.system('umount /dev/' + self.response.device) != 0:
			self.error_message = _('Cannot umount the device')
		else:
			if os.system('/sbin/mkfs.ext4 -F /dev/' + self.response.device) != 0:
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
				type=MessageBox.TYPE_ERROR
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
					type=MessageBox.TYPE_YESNO
				)
			else:
				self.createDir(response)


class OMBManagerKernelModule:
	def __init__(self, session, kernel_module):
		self.session = session
		self.kernel_module = kernel_module

		message = _("You need the module ") + self.kernel_module + _(" to use openMultiboot\nDo you want install it?")
		disks_list = []
		for partition in harddiskmanager.getMountedPartitions():
			if partition.mountpoint != '/':
				disks_list.append((partition.description, partition.mountpoint))

		self.session.openWithCallback(self.installCallback, MessageBox, message, MessageBox.TYPE_YESNO)

	def installCallback(self, confirmed):
		if confirmed:
			self.messagebox = self.session.open(MessageBox, _('Please wait while installation is in progress.'), MessageBox.TYPE_INFO, enable_input=False)
			self.timer = eTimer()
			self.timer.callback.append(self.installModule)
			self.timer.start(100)

	def installModule(self):
		self.timer.stop()
		self.error_message = ''
		if os.system('opkg update && opkg install ' + self.kernel_module) != 0:
			self.error_message = _('Cannot install ') + self.kernel_module

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
				type=MessageBox.TYPE_ERROR
			)
		else:
			OMBManager(self.session)


def OMBManager(session, **kwargs):
	found = False

	kernel_module = 'kernel-module-nandsim'
	if "jffs2" in OMB_GETIMAGEFILESYSTEM:
		if os.path.exists(OMB_UNJFFS2_BIN):
			kernel_module = None
		else:
			kernel_module = 'kernel-module-block2mtd'
	if "tar.bz2" in OMB_GETIMAGEFILESYSTEM:
		kernel_module = None

	if kernel_module and os.system('opkg list_installed | grep ' + kernel_module) != 0 and BRANDING:
		OMBManagerKernelModule(session, kernel_module)
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
					if not os.path.ismount('/usr/lib/enigma2/python/Plugins/Extensions/OpenMultiboot'):
						if os.readlink("/sbin/init") == "/sbin/init.sysvinit":
							if os.path.isfile('/sbin/open_multiboot'):
								os.system("ln -sfn /sbin/open_multiboot /sbin/init")
					session.open(OMBManagerList, partition.mountpoint)
					found = True
					break

	if not found:
# by meo: Allow plugin installation only for images in flash. We don't need plugin in mb installed images.
# The postinst link creation in open_multiboot will be also disabled to avoid conflicts between init files.
		if not os.path.ismount('/usr/lib/enigma2/python/Plugins/Extensions/OpenMultiboot'):
			OMBManagerInit(session)
