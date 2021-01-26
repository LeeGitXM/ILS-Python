'''
Created on Jan 23, 2021

@author: phass
'''
import system

from ils.sfc.recipeData.export import Exporter
from ils.sfc.recipeData.importer import Importer
from ils.common.config import getDatabaseClient
from ils.common.error import catchError, notifyError
log=system.util.getLogger(__name__)

def synchronizeCallback(chartPath, deep, sourceDb, destinationDb):
    '''
    This is called by the button on the SFC recipe data browser. 
    '''
    try:
        log.infof("The selected chart path is <%s>, deep: %s, from %s to %s", chartPath, str(deep), sourceDb, destinationDb)
        if chartPath == "" or chartPath == None:
            return
        
        synchronizer = Synchronizer(sourceDb, destinationDb)
        status = synchronizer.synchronize(chartPath, deep)
        
        if status:
            system.gui.messageBox("Recipe data was successfully synchronized!")
        else:
            system.gui.errorBox("An error was encountered while synchronizing recipe data!")
    except:
        notifyError("%s.exportCallback()" % (__name__), "Check the console log for details.")
        
    return status
        

class Synchronizer():
    sourceDb = None
    destinationDb = None
    
    def __init__(self, sourceDb, destinationDb):
        self.sourceDb = sourceDb
        self.destinationDb = destinationDb
    
    def synchronize(self, chartPath, deep):
        exporter =Exporter(self.sourceDb)
        importer = Importer(self.destinationDb)
        
        chartPaths = []
        chartPaths.append(chartPath)
        
        for chartPath in chartPaths:
            chartXML=exporter.export(chartPath, deep)
            
        status = importer.importFromString(chartXML)
        
        return status