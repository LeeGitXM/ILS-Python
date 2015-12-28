# Copyright 2015. ILS Automation
#
# Scripts to control the SFC step monitor
# NOTE: These are available in Gateway scope only.
#
import system.ils.sfc as ilssfc
def clear(common):
	ilssfc.clearStepMonitor()
def start(common):
	ilssfc.startStepMonitor()
def stop(common):
	ilssfc.stopStepMonitor()