# Copyright 2015. ILS Automation. All rights reserved.
# Test the client/designer "toolkit" scripting interfaces

import system.ils.blt.diagram as script

# Return a list of name of blocks that are downstream of the 
# specified block - and in the same diagram
def listBlocksConnectedAtPort(common,dpath,blockName,port):
	diagid = getDiagram(dpath).getSelf().toString()
	blockId  = script.getBlockId(diagid,blockName)
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listBlocksConnectedAtPort(diagid,blockId,port)
	print "==================== listBlocksConnectedAtPort ",port," =============="
	lst = []
	for block in blocks:
		print block.getAttributes().get("parent"),block.getName()
		lst.append(block.getName())
	common['result'] = lst 
	
# Return a list of name of blocks that are downstream of the 
# specified block - and in the same diagram
def listBlocksDownstreamOf(common,dpath,blockName):
	diagid = getDiagram(dpath).getSelf().toString()
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listBlocksDownstreamOf(diagid,blockName)
	print "==================== listBlocksDownstreamOf ",blockName," =============="
	lst = []
	for block in blocks:
		print block.getAttributes().get("parent"),block.getName()
		lst.append(block.getName())
	common['result'] = lst 
	
# Return a list of names of blocks that are downstream of the 
# specified block - on the same and linked diagrams
def listBlocksGloballyDownstreamOf(common,dpath,blockName):
	diagid = getDiagram(dpath).getSelf().toString()
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listBlocksGloballyDownstreamOf(diagid,blockName)
	print "==================== listBlocksGloballyDownstreamOf ",blockName,"=============="
	lst = []
	for block in blocks:
		print block.getAttributes().get("parent"),block.getName()
		lst.append(block.getName())
	common['result'] = lst 
	
# Return a list of names of blocks that are upstream of the 
# specified block - on the same and linked diagrams
def listBlocksGloballyUpstreamOf(common,dpath,blockName):
	diagid = getDiagram(dpath).getSelf().toString()
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listBlocksGloballyUpstreamOf(diagid,blockName)
	print "==================== listBlocksGloballyUpstreamOf ",blockName,"=============="
	lst = []
	for block in blocks:
		print block.getAttributes().get("parent"),block.getName()
		lst.append(block.getName())
	common['result'] = lst 
	
# Return a list of names of blocks that are downstream of the 
# specified block - and in the same diagram
def listBlocksUpstreamOf(common,dpath,blockName):
	diagid = getDiagram(dpath).getSelf().toString()
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listBlocksUpstreamOf(diagid,blockName)
	print "==================== listBlocksUpstreamOf ",blockName,"=============="
	lst = []
	for block in blocks:
		print block.getName()
		lst.append(block.getName())
	common['result'] = lst 

# Return a list of block names that are upstream of a 
# specified block and of a specified class.
def listBlocksOfClassUpstream(common,dpath,blockName,classname):
	diagid = getDiagram(dpath).getSelf().toString()
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listBlocksUpstreamOf(diagid,blockName)
	lst = []
	print "==================== listBlocksOfClassUpstream ",blockName,"=============="
	for block in blocks:
		print block.getName()," is ",block.getClassName()
		if block.getClassName()==classname:
			lst.append(block.getName())
	common['result'] = lst 
#
# Return a list of block names that are downstream of a 
# specified block and of a specified class.
def listBlocksOfClassDownstream(common,dpath,blockName,classname):
	diagid = getDiagram(dpath).getSelf().toString()
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listBlocksDownstreamOf(diagid,blockName)
	lst = []
	print "==================== listBlocksOfClassDownstream ",blockName,"=============="
	for block in blocks:
		print block.getName()," is ",block.getClassName()
		if block.getClassName()==classname:
			lst.append(block.getName())
	common['result'] = lst 
#
# Return a list of block names that match the class criterion
def listBlocksOfClass(common,dpath,classname):
	diagid = getDiagram(dpath).getSelf().toString()
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listDiagramBlocksOfClass(diagid,classname)
	lst = []
	for block in blocks:
		lst.append(block.getName())
	common['result'] = lst 

# Return a list of names of all blocks in the specified diagram
def listBlocksInDiagram(common,dpath):
	diagid = getDiagram(dpath).getSelf().toString()
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listBlocksInDiagram(diagid)
	lst = []
	for block in blocks:
		lst.append(block.getName())
	common['result'] = lst 

# Return a list of names of blocks that with one or more properties
# that are bound to the specified tag. The search is across all
# diagrams.
def listBlocksForTag(common,tagpath):
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listBlocksForTag(tagpath)
	print "==================== listBlocksForTag ",tagpath,"=============="
	lst = []
	for block in blocks:
		print block.getName()
		lst.append(block.getName())
	common['result'] = lst 

# Return a list of sink blocks that are "connected" to the
# input of the specified source. All blocks in the 
# gateway are considered.
def listSinksForSource(common,dpath,blockId):
	diagid = getDiagram(dpath).getSelf().toString()
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listSinksForSource(diagid,blockId)
	#print "==================== sinksForSource ",blockName,"=============="
	lst = []
	for block in blocks:
		#print block.getName()
		lst.append(block.getName())

	common['result'] = lst 

# Return a list of source blocks that are "connected" to
# the output of the specified sink. All blocks in the 
# gateway are considered.
def listSourcesForSink(common,dpath,blockId):
	diagid = getDiagram(dpath).getSelf().toString()
	# blocks is a list of SerializableBlockStateDescriptor
	blocks = script.listSourcesForSink(diagid,blockId)
	print "==================== sourcesForSink ",blockId,"=============="
	lst = []
	for block in blocks:
		print block.getName()
		lst.append(block.getName())

	common['result'] = lst 


# Propagate a signal to any receivers on the diagram
def sendLocalSignal(common,dpath,command,message,arg):
	diagid = getDiagram(dpath).getSelf().toString()
	script.sendLocalSignal(diagid,command,message,arg)

# Propagate a signal to any receivers on the diagram
# Timestamp the signal with the current test time
# Ignore "message" and "arg"
def sendTimestampedSignal(common,dpath,command,year,mon,day,hr,min,sec):
	import datetime,time
	diagid = getDiagram(dpath).getSelf().toString()
	testtime = datetime.datetime(int(year),int(mon),int(day),int(hr),int(min),int(sec))
	ts = time.mktime(testtime.timetuple())*1000
	script.sendTimestampedSignal(diagid,command,"","",long(ts))

# -------------------------- Helper methods ----------------------
# Return the ProcessDiagram at the specified path
def getDiagram(dpath):
	diagram = None
	# The descriptor paths are :-separated, the input uses /
	# the descriptor path starts with ":root:", 
	# the input starts with the application
	descriptors = script.getDiagramDescriptors()
	handler = script.getHandler()
	for desc in descriptors:
		path = desc.path[6:]
		path = path.replace(":","/")
		#print desc.id, path
		if dpath == path:
			diagram = handler.getDiagram(desc.id)
	return diagram

