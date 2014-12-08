'''
Created on Nov 18, 2014

@author: Pete
'''
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil

def client():    
    print "In ils.common.startup.client()"
    
    # Create client loggers
    log = LogUtil.getLogger("com.ils.recipeToolkit.ui")
    log.info("Initializing...")


def gateway():
    print "In ils.common.startup.gateway()"
    
    # Create gateway loggers
    log = LogUtil.getLogger("com.ils.io")
    log.info("Initializing...")
    