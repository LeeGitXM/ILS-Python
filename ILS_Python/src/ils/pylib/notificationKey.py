# Copyright 2015. ILS Automation. All rights reserved.
# Argument is the diagram path
import system.ils.blt.diagram as script

def construct(common,diagramPath,blockName,port):
	handler = script.getHandler()     # PythonRequestHandler
	error = "Diagram "+diagramPath+" NOT FOUND"
	notification = "KEY-NOT-FOUND"
	# The descriptor paths are :-separated, the input uses /
	# the descriptor path starts with ":root:", the input stars with the application
	descriptors = script.getDiagramDescriptors()
	for desc in descriptors:
		path = desc.path[6:]
		path = path.replace(":","/")
		#print desc.id, path
		if diagramPath == path:
			diagram = handler.getDiagram(desc.id)
			blockId = handler.getBlockId(diagram,blockName)
			if len(blockId) <= 0:
				error = "BLOCK "+blockName+" NOT FOUND in DIAGRAM"
			else:
				error = "ok"
			notification = "C:"+blockId+":"+port
			break
	print "notificationKey.construct="+notification+"("+error+")"
	common['result'] = notification 
