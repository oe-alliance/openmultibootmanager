#!/usr/bin/env python

from __future__ import print_function
import sys

sys.path.insert(0, '/usr/lib/enigma2/python/Plugins/Extensions/')
from OpenMultiboot import OMBList

if __name__ == "__main__":

	ombdir = "/omb"

	if len(sys.argv) == 2:
		ombdir = sys.argv[1]

	ombList = OMBList.OMBList( ombdir, debug=None)

	ombList.populateImagesList()
	print (ombList.getJson())

