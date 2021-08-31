'''
Created on Aug 12, 2021

@author: phass
'''

def act_1(block, uuid, parentuuid, provider, database):
    print "In %s.act_1()" % (__name__)
    print "  Block: %s" % (str(block))
    print "  UUID: %s" % (uuid)
    print "  Parent UUID: %s" % (parentuuid)
    print "  Provider: %s" % (provider)
    print "  Database: %s" % (database)
    #print "demo.act block class = ",block.getClassName()
    #print "Block ID = ",block.blockId
    #print "Block Parent Id = ",block.parentId
    
    # The handler is a com.ils.blt.gateway.PythonRequestHandler
    #print "Block database = ",database
    #print "Block Tag Provider =",provider