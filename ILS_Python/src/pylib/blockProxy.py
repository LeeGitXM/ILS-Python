# Copyright 2015. ILS Automation. All rights reserved.
# Operations on a block
import system
import system.ils.blt.diagram as script

# This is a little convoluted because we already have the diagram path,
# but it does test a different set of scripting functions
def getDiagramForBlock(common,dpath,blockName):
	diagram = getDiagram(dpath)
	for block in diagram.getProcessBlocks():
		if block.getName() == blockName:
			blkid = block.getBlockId().toString()
			desc = script.getDiagramForBlock(blkid)
			if desc==None:
				common['result'] = "Diagram not found for block ",blkid
			else:
				common['result'] = desc.getName()
	return 
# Internal status is a SerializableBlockStateDescriptor
# -- the descriptor has methods getAttributes(), getBuffer()
# -- both return lists of dictionaries.
# dpath - the diagram path
# blockName - name of the block within the diagram
# attName - name of the desired parameter in the internal structure
def internalAttribute(common,dpath,blockName,attName):
	diagram = getDiagram(dpath)
	for block in diagram.getProcessBlocks():
		if block.getName() == blockName:
			attributes = block.getInternalStatus().getAttributes()
			attribute = attributes.get(attName)
			common['result'] = attribute
	return 
			
# Internal status is a SerializableBlockStateDescriptor
# -- the descriptor has methods getAttributes(), getBuffer()
# -- both return lists of dictionaries.
# dpath - the diagram path
# blockName - name of the block within the diagram
def internalBufferSize(common,dpath,blockName):
	diagram = getDiagram(dpath)
	for block in diagram.getProcessBlocks():
		print block.getName()
		if block.getName() == blockName:
			size = block.getInternalStatus().getBuffer().size()
			common['result'] = size
	return 

# Internal status is a SerializableBlockStateDescriptor
# -- the descriptor has methods getAttributes(), getBuffer()
# -- both return lists of dictionaries.
# dpath - the diagram path
# blockName - name of the block within the diagram
# attName - name of the attribute to read from the dictionary
# index - position in buffer (zero-based)
def internalBufferValue(common,dpath,blockName,attName,index):
	diagram = getDiagram(dpath)
	for block in diagram.getProcessBlocks():
		if block.getName() == blockName:
			attmap = block.getInternalStatus().getBuffer().get(int(index))
			common['result'] = attmap.get(attName)
			return
	print 'internalBufferValue for ',dpath,', ',blockName,' not found'
			
# Return the value of a property of a block
def getBlockProperty(common,dpath,blockName,propName):
	diagram = getDiagram(dpath)
	for block in diagram.getProcessBlocks():
		if block.getName() == blockName:
			prop = block.getProperty(propName)
			if prop != None:
				common['result'] = prop.getValue()
				return
			else:
				print 'getBlockProperty ',dpath,':',blockName,' property ',propName,' not found'
				return
	print 'getBlockProperty ',dpath,': block',blockName,' not found'

# Set the value of a property of a block. Use the controller
# request handler in order to set the property in such a way
# that the block is notified.
def setBlockProperty(common,dpath,blockName,propName,value):
	requestHandler = script.getRequestHandler()
	diagid = getDiagram(dpath).getSelf().toString()
	requestHandler.setBlockPropertyValue(diagid,blockName,propName,value)

# Return the state of a block
def getBlockState(common,dpath,blockName):
	diagram = getDiagram(dpath)
	result = blockName+" NOT FOUND"
	for block in diagram.getProcessBlocks():
		if block.getName() == blockName:
			result = block.getState()
			break

	common['result'] = result

#
# Return the state of a block
def getExplanation(common,dpath,blockName):
	diagram = getDiagram(dpath)
	diagId = getDiagram(dpath).getSelf().toString()
	result = blockName+" NOT FOUND"
	for block in diagram.getProcessBlocks():
		if block.getName() == blockName:
			blockId = block.getBlockId().toString()
			result = script.getExplanation(diagId,blockId)
			break

	common['result'] = result
# Reset an individual block
def reset(common,dpath,blockName):
	diagid = getDiagram(dpath).getSelf().toString()
	script.resetBlock(diagid,blockName)
	
# Stop then start a block
def restart(common,dpath,blockName):
	diagid = getDiagram(dpath).getSelf().toString()
	script.restartBlock(diagid,blockName)

# -------------------------- Helper methods ----------------------
# Return a ProcessDiagram at the specified path
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

