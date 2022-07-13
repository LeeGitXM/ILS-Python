'''
Created on Jun 29, 2022

@author: ils
'''

def defaultAction(block, diagramPath, blockName, blockUUID, provider, database):
    print "In %s.defaultAction()" % (__name__)
    print "       Class: ", block.getClassName()
    print " DiagramPath: ", diagramPath
    print "  Block Name: ", blockName
    print "  Block UUID: ", blockUUID
    print "    Provider: ", provider
    print "    Database: ", database

    
def action1(block, diagramPath, blockName, blockUUID, provider, database):
    print "In %s.action1()" % (__name__)
    print "       Class: ", block.getClassName()
    print " DiagramPath: ", diagramPath
    print "  Block Name: ", blockName
    print "  Block UUID: ", blockUUID
    print "    Provider: ", provider
    print "    Database: ", database
    
    
def action2(block, diagramPath, blockName, blockUUID, provider, database):
    print "In %s.action2()" % (__name__)
    print "       Class: ", block.getClassName()
    print " DiagramPath: ", diagramPath
    print "  Block Name: ", blockName
    print "  Block UUID: ", blockUUID
    print "    Provider: ", provider
    print "    Database: ", database