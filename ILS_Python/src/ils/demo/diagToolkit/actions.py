'''
Created on Jun 29, 2022

@author: ils
'''

def defaultAction(block, provider, database):
    print "In %s.defaultAction(), class: %s" % (__name__, block.getClassName())

    
def action1(block, provider, database):
    print "In %s.action1(), class: %s" % (__name__, block.getClassName())
    print "Block ID = ",block.blockId
    print "Block Parent Id = ",block.parentId
    print "Block database = ",database
    print "Block Tag Provider =",provider
    
def action2(block, provider, database):
    print "In %s.action2(), class: %s" % (__name__, block.getClassName())
    print "Block ID = ",block.blockId
    print "Block Parent Id = ",block.parentId
    print "Block database = ",database
    print "Block Tag Provider =",provider