# Copyright 2015. ILS Automation. All rights reserved.

# Argument is the diagram path
def setTestTimeOffset(common,yr,mon,dy,hr,min,sec):
	import datetime,time
	import system.ils.blt.diagram as script
	today = time.time()
	testday  = datetime.datetime(int(yr),int(mon),int(dy),int(hr),int(min),int(sec))
	ts = time.mktime(testday.timetuple())
	offset = (today - ts)*1000
	print "TestTimeOffset: ",offset
	script.setTestTimeOffset(long(offset))

# Time factor is the clock speedup ratio (factor>1)
def setTimeFactor(common,factor):
	import system.ils.blt.diagram as script
	script.setTimeFactor(float(factor))

def setSfcTimeFactor(common,factor):
	import system.ils.sfc as ilssfc
	ilssfc.setTimeFactor(float(factor))
