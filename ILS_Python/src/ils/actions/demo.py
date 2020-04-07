'''
Demonstration of a custom action module
'''
def act(block):
    print "demo.act block class = ",block.getClassName()
    #print block.uuid
    #print block.parentuuid
    # The handler is a com.ils.blt.gateway.PythonRequestHandler
    #print block.getParentUuid()
    #print block.getDefaultDatabase()
    #print block.handler.getDefaultDatabase(block.parentuuid)
    #print block.handler.getDefaultTagProvider(block.parentuuid)
    
