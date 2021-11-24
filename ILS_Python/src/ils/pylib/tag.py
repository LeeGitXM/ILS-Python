# Copyright 2015-2016. ILS Automation. All rights reserved.
# Direct tag operations for use with the test framework

from ils.io.util import readTag, writeTag

# Read the timestamp of a tag and return as an integer
# milliseconds since the start of the Unix epoch.
def getTagTime(common,provider,tpath):
	# Convert to the proper provider
	path = "["+provider+"]"+tpath
	qv = readTag(path)
	msecs = qv.getTimestamp().getTime()
	print "getTagTime: ",path,"=",msecs
	common['result'] = msecs

# Explicitly set the value of a tag that is a String data type
def setStringValue(common,provider,tpath,text):
	# Convert to the proper provider
	path = "["+provider+"]"+tpath
	writeTag(path,text)
	print "setStringValue: ",path,"=",text
	
# Explicitly set the value of a tag that is a Date data type.
# The value is a text of the form "YYYY/MM/dd HH:mm:ss"
def setDateValue(common,provider,tpath,text):
	import java.text.SimpleDateFormat as SimpleDateFormat
	
	parser = SimpleDateFormat('yyyy/MM/dd HH:mm:ss')
	date = parser.parse(text)
	# Convert to the proper provider
	path = "["+provider+"]"+tpath
	writeTag(path,date)
	print "setDateValue: ",path,"=",text