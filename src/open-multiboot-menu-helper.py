#!/usr/bin/env python

from __future__ import print_function
import sys

sys.path.insert(0, '/usr/lib/enigma2/python/Plugins/Extensions/')
from OpenMultiboot import OMBList

if __name__ == "__main__":

	debug = None
	ombdir = "/omb"

	if len(sys.argv) >= 2:
		ombdir = sys.argv[1]
	
	if len(sys.argv) == 3 and sys.argv[2].upper() == "DEBUG":
		debug = True

	ombList = OMBList.OMBList(ombdir, debug = debug)

	ombList.populateImagesList()
	print (ombList.getJson(debug = debug))

