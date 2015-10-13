# Copyright 2015. ILS Automation. All rights reserved.
# Read the timestamp of a tag and return as an integer
# milliseconds since the start of the Unix epoch.
def getTagTime(provider,tpath):
	# Convert to the proper provider
	path = "["+provider+"]"+tpath
	print "getTagTime: ",path
	qv =system.tag.read(path)
	print "getTagTime: completed read"
	msecs = qv.getTimestamp().getTime()
	print "getTagTime: ",msecs
	return msecs

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

def setTimeFactor(common,factor):
	import system.ils.blt.diagram as script
	script.setTimeFactor(float(factor))

def setSfcTimeFactor(common,factor):
	import system.ils.sfc as ilssfc
	ilssfc.setTimeFactor(float(factor))
