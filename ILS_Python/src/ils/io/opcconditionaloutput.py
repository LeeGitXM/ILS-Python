'''
Copyright 2014 ILS Automation

This can be a float or a text

Created on Jul 9, 2014

@author: phassler
'''
import emc.io.opcoutput as opcoutput
class OPCConditionalOutput(opcoutput.OPCOutput):
    def __init__(self,path):
        opcoutput.OPCOutput.__init__(self,path)
