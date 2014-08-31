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

OMB_STB_MAP = {
	'gbquadplus': 'quadplus',
    'gbquad': 'quad',
    'gb800ueplus': 'ueplus',
    'gb800seplus': 'seplus',
    'gbipbox': 'ipbox',
    'gb800ue': 'ue',
    'gb800se': 'se'
}

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
		self.session.openWithCallback(self.installStart, MessageBox, _("Do you want to copy settings from the current image?"), MessageBox.TYPE_YESNO)

	def installStart(self, install_settings):
		self.install_settings = install_settings
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
		
	def installPrepare(self):
		self.timer.stop()
		
		selected_image = self.selected_image

		source_file = self.mount_point + '/' + OMB_UPLOAD_DIR + '/' + selected_image + '.zip'
		target_folder = self.mount_point + '/' + OMB_DATA_DIR + '/' + selected_image.replace(' ', '_')
		kernel_target_folder = self.mount_point + '/' + OMB_DATA_DIR + '/.kernels'
		kernel_target_file = kernel_target_folder + '/' + selected_image.replace(' ', '_') + '.bin'

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
		except OSError as exception:
			self.showError(_("Cannot create folder %s") % tmp_folder)
			return
				
		if os.system(OMB_UNZIP_BIN + ' ' + source_file + ' -d ' + tmp_folder) != 0:
			self.showError(_("Cannot deflate image"))
			return
			
		if self.installImage(tmp_folder, target_folder, kernel_target_file, tmp_folder):
			os.system(OMB_RM_BIN + ' -f ' + source_file)
			self.messagebox.close()
			self.close()
		
		os.system(OMB_RM_BIN + ' -rf ' + tmp_folder)
			
	def installImage(self, src_path, dst_path, kernel_dst_path, tmp_folder):
		for i in range(0, 20):
			mtdfile = "/dev/mtd" + str(i)
			if os.path.exists(mtdfile) is False:
				break
		mtd = str(i)

		model = open('/proc/stb/info/model').read().strip()
		if not model in OMB_STB_MAP:
			self.showError(_("Your STB doesn\'t seem supported"))
			return False

		model = OMB_STB_MAP[model]

		base_path = src_path + '/gigablue/' + model
		rootfs_path = base_path + '/rootfs.bin'
		kernel_path = base_path + '/kernel.bin'
		ubi_path = src_path + '/ubi'

		virtual_mtd = tmp_folder + '/virtual_mtd'
		os.system(OMB_MODPROBE_BIN + ' nandsim cache_file=' + virtual_mtd + ' first_id_byte=0x20 second_id_byte=0xaa third_id_byte=0x00 fourth_id_byte=0x15')
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
		
		if self.install_settings:
			if not os.path.exists(dst_path + '/etc/enigma2'):
				os.makedirs(dst_path + '/etc/enigma2')
			os.system(OMB_CP_BIN + ' /etc/enigma2/*.tv ' + dst_path + '/etc/enigma2')
			os.system(OMB_CP_BIN + ' /etc/enigma2/*.radio ' + dst_path + '/etc/enigma2')
			os.system(OMB_CP_BIN + ' /etc/enigma2/lamedb ' + dst_path + '/etc/enigma2')
			os.system(OMB_CP_BIN + ' /etc/enigma2/settings ' + dst_path + '/etc/enigma2')
		
		return True