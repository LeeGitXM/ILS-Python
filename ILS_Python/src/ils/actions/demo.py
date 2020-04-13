'''
Demonstration of a custom action module
'''
# def act(block):
#     print "****************************************************************************************************************************demo.act block class = ",block.getClassName()
#     print dir(block)
#     print block.blockId
#     print block.parentId
       
#      With recent changes, the act function should be called with database, handler, etc
def act(block, provider, database):
    print "demo.act block class = ",block.getClassName()
    print "Block ID = ",block.blockId
    print "Block Parent Id = ",block.parentId
    # The handler is a com.ils.blt.gateway.PythonRequestHandler
    print "Block database = ",database
    print "Block Tag Provider =",provider
       
