#!/usr/bin/env python
import sys

sys.path.insert(0, '/usr/lib/enigma2/python/Plugins/Extensions/')
from OpenMultiboot import OMBList

if __name__ == "__main__":

	ombList = OMBList.OMBList("/media/usb", debug=None)

	ombList.populateImagesList()
	print (ombList.getJson())

