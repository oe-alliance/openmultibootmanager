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
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.Sources.List import List

from OMBManagerInstall import OMBManagerInstall, OMB_RM_BIN
from OMBManagerAbout import OMBManagerAbout
from OMBManagerCommon import OMB_DATA_DIR, OMB_UPLOAD_DIR
from OMBManagerLocale import _

from enigma import eTimer

import os

class OMBManagerList(Screen):
	skin = """
		<screen position="360,150" size="560,400">
			<widget name="background"
					zPosition="1"
					position="0,0"
					size="560,360"
					alphatest="on" />
					
			<widget source="list"
					render="Listbox"
					position="10,10"
					zPosition="3"
					size="540,340"
					scrollbarMode="showOnDemand"
					transparent="1">
					
				<convert type="StringList" />
			</widget>
			<widget name="key_red"
					position="0,360"
					size="140,40"
					valign="center"
					halign="center"
					zPosition="5"
					transparent="1"
					foregroundColor="white"
					font="Regular;18" />
					
			<widget name="key_green"
					position="140,360"
					size="140,40"
					valign="center"
					halign="center"
					zPosition="5"
					transparent="1"
					foregroundColor="white"
					font="Regular;18" />
					
			<widget name="key_yellow"
					position="280,360"
					size="140,40"
					valign="center"
					halign="center"
					zPosition="5"
					transparent="1"
					foregroundColor="white"
					font="Regular;18" />
					
			<widget name="key_blue"
					position="420,360"
					size="140,40"
					valign="center"
					halign="center"
					zPosition="5"
					transparent="1"
					foregroundColor="white"
					font="Regular;18" />
	
			<ePixmap name="red"
					 pixmap="skin_default/buttons/red.png"
					 position="0,360"
					 size="140,40"
					 zPosition="4"
					 transparent="1"
					 alphatest="on" />
					 
			<ePixmap name="green"
					 pixmap="skin_default/buttons/green.png"
					 position="140,360"
					 size="140,40"
					 zPosition="4"
					 transparent="1"
					 alphatest="on" />
					 
			<ePixmap name="yellow"
					 pixmap="skin_default/buttons/yellow.png"
					 position="280,360"
					 size="140,40"
					 zPosition="4"
					 transparent="1"
					 alphatest="on" />
					 
			<ePixmap name="blue"
					 pixmap="skin_default/buttons/blue.png"
					 position="420,360"
					 size="140,40"
					 zPosition="4"
					 transparent="1"
					 alphatest="on" />
		</screen>"""
		
	def __init__(self, session, mount_point):
		Screen.__init__(self, session)
		
		self.setTitle(_('openMultiboot Manager'))
		
		self.session = session
		self.mount_point = mount_point
		self.data_dir = mount_point + '/' + OMB_DATA_DIR
		self.upload_dir = mount_point + '/' + OMB_UPLOAD_DIR

		self.populateImagesList()
		
		self["list"] = List(self.images_list)
		self["list"].onSelectionChanged.append(self.onSelectionChanged)
		self["background"] = Pixmap()
		self["key_red"] = Button(_('Rename'))
		self["key_green"] = Button(_('Install'))
		self["key_yellow"] = Button()
		self["key_blue"] = Button(_('About'))
		self["config_actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"cancel": self.close,
			"red": self.keyRename,
			"yellow": self.keyDelete,
			"green": self.keyInstall,
			"blue": self.keyAbout
		})

	def guessImageTitle(self, base_path, identifier):
		image_distro = ""
		image_version = ""
		
		e2_path = base_path + '/usr/lib/enigma2/python'
		if os.path.exists(e2_path + '/boxbranding.so'):
			helper = os.path.dirname("/usr/bin/python " + os.path.abspath(__file__)) + "/open-multiboot-branding-helper.py"
			fin,fout = os.popen4(helper + " " + e2_path + " image_distro")
			image_distro = fout.read().strip()
			fin,fout = os.popen4(helper + " " + e2_path + " image_version")
			image_version = fout.read().strip()
		
		if len(image_distro) > 0:
			return image_distro + " " + image_version
		else:
			return identifier

	def imageTitleFromLabel(self, file_entry):
		f = open(self.data_dir + '/' + file_entry)
		label = f.readline().strip()
		f.close()
		return label
		
	def populateImagesList(self):
		self.images_list = []
		self.images_entries = []
		flashimageLabel = 'Flash image'

		if os.path.exists(self.data_dir + '/.label_flash'): # use label name
			flashimageLabel = self.imageTitleFromLabel('.label_flash') + ' (Flash)'

		self.images_entries.append({
			'label': flashimageLabel,
			'identifier': 'flash',
			'path': '/'
		})
		self.images_list.append(self.images_entries[0]['label'])
		if os.path.exists(self.data_dir):
			for file_entry in os.listdir(self.data_dir):
				if not os.path.isdir(self.data_dir + '/' + file_entry):
					continue

				if file_entry[0] == '.':
					continue

				if os.path.exists(self.data_dir + '/.label_' + file_entry):
					title = self.imageTitleFromLabel('.label_' + file_entry)
				else:
					title = self.guessImageTitle(self.data_dir + '/' + file_entry, file_entry)
				
				self.images_entries.append({
					'label': title,
					'identifier': file_entry,
					'path': self.data_dir + '/' + file_entry
				})
				self.images_list.append(title)
					
	def refresh(self):
		self.populateImagesList()
		self["list"].setList(self.images_list)
		
	def canDeleteEntry(self, entry):
		selected = 'flash'
		try:
			selected = open(self.data_dir + '/.selected').read()
		except:
			pass
			
		if entry['path'] == '/' or entry['identifier'] == selected:
			return False
		return True
		
	def onSelectionChanged(self):
		if len(self.images_entries) == 0:
			return
			
		index = self["list"].getIndex()
		if index >= 0 and index < len(self.images_entries):
			entry = self.images_entries[index]
			if self.canDeleteEntry(entry):
				self["key_yellow"].setText(_('Delete'))
			else:
				self["key_yellow"].setText('')
			
	def keyAbout(self):
		self.session.open(OMBManagerAbout)

	def keyRename(self):
		self.renameIndex = self["list"].getIndex()
		name = self["list"].getCurrent()
		if self["list"].getIndex() == 0:
			if name.endswith('(Flash)'):
				name = name[:-8]

		self.session.openWithCallback(self.renameEntryCallback, VirtualKeyBoard, title=_("Please enter new name:"), text=name)

	def renameEntryCallback(self, name):
		if name:
			renameimage = self.images_entries[self.renameIndex]

			if renameimage['identifier'] == 'flash':
				file_entry = self.data_dir + '/.label_flash'
			else:
				file_entry = self.data_dir + '/.label_' + renameimage['identifier']

			f = open(file_entry, 'w')
			f.write(name)
			f.close()
			self.refresh()
		
	def deleteConfirm(self, confirmed):
		if confirmed and len(self.entry_to_delete['path']) > 1:
			self.messagebox = self.session.open(MessageBox,_('Please wait while delete is in progress.'), MessageBox.TYPE_INFO, enable_input = False)
			self.timer = eTimer()
			self.timer.callback.append(self.deleteImage)
			self.timer.start(100)
		
	def deleteImage(self):
		self.timer.stop()
		os.system(OMB_RM_BIN + ' -rf ' + self.entry_to_delete['path'])
		self.messagebox.close()
		self.refresh()
		
	def keyDelete(self):
		if len(self.images_entries) == 0:
			return
			
		index = self["list"].getIndex()
		if index >= 0 and index < len(self.images_entries):
			self.entry_to_delete = self.images_entries[index]
			if self.canDeleteEntry(self.entry_to_delete):
				self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Do you want to delete %s?") % self.entry_to_delete['label'], MessageBox.TYPE_YESNO)
		
	def keyInstall(self):
		upload_list = []
		if os.path.exists(self.upload_dir):
			for file_entry in os.listdir(self.upload_dir):
				if file_entry[0] == '.' or file_entry == 'flash.zip':
					continue
					
				if len(file_entry) > 4 and file_entry[-4:] == '.zip':
					upload_list.append(file_entry[:-4])
		
		if len(upload_list) > 0:
			self.session.openWithCallback(self.refresh, OMBManagerInstall, self.mount_point, upload_list)
		else:
			self.session.open(
				MessageBox,
				_("Please upload an image inside %s") % self.upload_dir,
				type = MessageBox.TYPE_ERROR
			)
