'''
Created on Oct 15, 2018

@author: phass
'''

from ils.sfc.gateway.api import cancelChart

def calcRate(chart, block):
    print "In %s.calcRate()" % (__name__)
    cancelCallback(chart)
    print "Hey, I shouldn't ever get here!"
    
def cancelCallback(chart):
    print "Cancelling the chart!"
    cancelChart(chart)