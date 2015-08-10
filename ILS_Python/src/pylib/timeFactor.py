# Copyright 2015. ILS Automation. All rights reserved.
# Argument is the diagram path
def setFactor(common,factor):
	import system.ils.blt.diagram as script
	script.setTimeFactor(float(factor))

def setSfcTimeFactor(common,factor):
	import system.ils.sfc as ilssfc
	ilssfc.setTimeFactor(float(factor))
