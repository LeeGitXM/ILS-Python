'''
Demonstration of a custom action module
'''
def act(blockName, uuid, parentuuid, provider, database):
    print "demo.act block class = ",blockName
    print uuid
    print parentuuid
    # The handler is a com.ils.blt.gateway.PythonRequestHandler
    print database
    print provider
       
