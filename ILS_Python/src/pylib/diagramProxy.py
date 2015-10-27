# Copyright 2015. ILS Automation. All rights reserved.
# Operations on a diagram
import system.ils.blt.diagram as script

# Return the name of the production tag provider
def getProductionProvider(common):
	provider = script.getToolkitProperty("Provider")
	return provider

# Return the name of the isolation-mode tag provider
def getIsolationProvider(common):
	provider = script.getToolkitProperty("SecondaryProvider")
	return provider
	
# Return the state of the diagram
def getState(common,dpath):
	diagid = getDiagram(dpath).getSelf().toString()
	state = script.getDiagramState(diagid)
	common['result'] = state

# Legal states are: ACTIVE,DISABLED,ISOLATED
def setState(common,dpath,state):
	diagid = getDiagram(dpath).getSelf().toString()
	script.setDiagramState(diagid,state)
	

# Argument is the diagram path
def reset(common,dpath):
	diagid = getDiagram(dpath).getSelf().toString()
	script.resetDiagram(diagid)

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
