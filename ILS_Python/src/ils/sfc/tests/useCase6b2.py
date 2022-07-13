'''
Created on Nov 13, 2018

@author: phass
'''

import system
from ils.io.util import writeTag

def initFC100(chart, block):
    print "In %s.initFc100()" % (__name__)
    tagRoot = "[XOM]SFC/FC100/"
    writeTag(tagRoot + "value", 0.0)
    writeTag(tagRoot + "sp/value", 0.0)
    writeTag(tagRoot + "op/value", 0.0)
    writeTag(tagRoot + "mode/value", "----")
    
def initF101Ramp(chart, block):
    print "In %s.initF101Ramp()" % (__name__)
    tagRoot = "[XOM]SFC/F101_RAMP/"
    writeTag(tagRoot + "value", 0.0)
    writeTag(tagRoot + "sp/value", 0.0)
    writeTag(tagRoot + "op/value", 0.0)
    writeTag(tagRoot + "mode/value", "----")
    
def initF101(chart, block):
    '''
    Initialize a TDC AutoMan Controller
    '''
    print "In %s.initF101()" % (__name__)
    tagRoot = "[XOM]SFC/F101/"
    writeTag(tagRoot + "output/value", 0.0)
    writeTag(tagRoot + "mode/value", "----")
    
def initT101(chart, block):
    '''
    Initialize a TDC Digital Controller
    '''
    print "In %s.initT101()" % (__name__)
    tagRoot = "[XOM]SFC/T101/"
    writeTag(tagRoot + "op/value", "---")
    writeTag(tagRoot + "mode/value", "----")
    
def initFC102(chart, block):
    print "In %s.initFC102()" % (__name__)
    tagRoot = "[XOM]SFC/FC102/"
    writeTag(tagRoot + "value", 0.0)
    writeTag(tagRoot + "processingCommand", 0.0)
    writeTag(tagRoot + "sp/value", 0.0)
    writeTag(tagRoot + "op/value", 0.0)
    writeTag(tagRoot + "mode/value", "----")
    writeTag(tagRoot + "outputDisposability/value", "----")