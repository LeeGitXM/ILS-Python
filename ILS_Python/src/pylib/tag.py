# Copyright 2015. ILS Automation. All rights reserved.
# Direct tag operations for use with the test framework

# Read the timestamp of a tag and return as an integer
# milliseconds since the start of the Unix epoch.
def getTagTime(common,provider,tpath):
	import system
	# Convert to the proper provider
	path = "["+provider+"]"+tpath
	qv = system.tag.read(path)
	msecs = qv.getTimestamp().getTime()
	print "getTagTime: ",path,"=",msecs
	common['result'] = msecs

# Explicitly set the value of a tag that is a String data type
def setStringValue(common,provider,tpath,text):
	import system
	# Convert to the proper provider
	path = "["+provider+"]"+tpath
	system.tag.write(path,text)
	print "setStringValue: ",path,"=",text
	
# Explicitly set the value of a tag that is a Date data type.
# The value is a text of the form "YYYY/MM/dd hh:mm:ss"
def setDateValue(common,provider,tpath,text):
	import java.text.SimpleDateFormat as SimpleDateFormat
	import system
	
	parser = SimpleDateFormat(text)
	date = parser.parse()
	# Convert to the proper provider
	path = "["+provider+"]"+tpath
	system.tag.write(path,date)
	print "setDateValue: ",path,"=",text