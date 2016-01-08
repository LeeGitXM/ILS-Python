# Copyright 2015. ILS Automation
#
# Scripts to control the SFC step monitor
# NOTE: These are available in Gateway scope only.
#
import system.ils.sfc as ilssfc

# Important: Clearing the step monitor also clears
#            the request/response buffer.
def clear(common):
	ilssfc.clearStepMonitor()
	ilssfc.clearRequestResponseMaps()
	
def start(common):
	ilssfc.startStepMonitor()
def stop(common):
	ilssfc.stopStepMonitor()