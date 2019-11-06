'''
Created on Nov 13, 2016

@author: Pete
'''
# This an entry point for special model post-processing
# The module calls this to report execution complete.
#

import system
from xom.emre.test.common.engine import stopExecution
from xom.emre.test.file.output import writeLine

def reportComplete(modelResults):

    def stopTheShow(key):
        print "Stopping the show (stopping the engine and setting the tag)"
        # Stop the Java execution engine
        stopExecution(key)
      
        # Signal the client that the test is finished
        system.tag.write("[AED]FT/Control/TestingStatus", "Stop")
        
        
    print "============== Execution Complete (Final Test) =============="
    
    #
    # We should really exec() the alternateScript
    # For the moment we hard code it.
    #app.engine.core.wrapper.reportComplete(modelResults)
    # I think the idea here is that we call the normal engine stuff and then we call out special
    # test environment logic
    from xom.emre.aed.engine.main import main
    main(modelResults)

    print "=========== End Results (Final Test) ========  "
    # Read the next value from the data file
    if len(modelResults) > 0 :
        properties = modelResults[0]
        try :
            maxCycles = int(properties.get('maxCycles',1000000))
            cycles =    int(properties.get('executionCycles',0))
        except:
            maxCycles = 1000000
            cycles = 0
            print "Caught an exception"
             
        key = properties.get('session','unknown')
        print "Key: ", key
        print properties
        print "Cycles: ", cycles
        if cycles <= maxCycles :
            print "...more work to do..."
            writeLine(modelResults)
            from xom.emre.test.common.data import playNextPoint
            finished = playNextPoint(cycles, properties)
            if finished:
                stopTheShow(key)
                
        if cycles == maxCycles :
            stopTheShow(key)
