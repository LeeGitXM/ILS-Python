# Copyright 2015. ILS Automation. All rights reserved.
# Execute a chart from a client/
import ils.sfc.client.windows.controlPanel as controlPanel


# Argument is the name of the control panel
def closeControlPanel(common,name):
	controlPanelId = controlPanel.getControlPanelIdForName(name)
	controlPanel.closeControlPanel(controlPanelId, True)

# Argument is the name of the control panel
def openControlPanel(common,name):
	controlPanelId = controlPanel.getControlPanelIdForName(name)
	controlPanel.openControlPanel(controlPanelId, True)
	
# Argument is the name of the control panel
def openDynamicControlPanel(common,chartPath,name):
	controlPanel.openDynamicControlPanel(chartPath, True,name)