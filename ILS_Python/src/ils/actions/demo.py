'''
Demonstration of a custom action module
'''
def act(block, provider, database):
    print "demo.act block class = ",block.getClassName()
    print "Block ID = ",block.blockId
    print "Block Parent Id = ",block.parentId
    print "Block database = ",database
    print "Block Tag Provider =",provider
       

def actOld(block):
    print "demo.act block class = ",block.getClassName()
    #print block.uuid
    #print block.parentuuid
    # The handler is a com.ils.blt.gateway.PythonRequestHandler
    #print block.getParentUuid()
    #print block.getDefaultDatabase()
    #print block.handler.getDefaultDatabase(block.parentuuid)
    #print block.handler.getDefaultTagProvider(block.parentuuid)
    
