'''
Created on Jan 23, 2021

@author: phass
'''
from ils.sfc.recipeData.export import Exporter
from ils.sfc.recipeData.import import Importer

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
            
            chartXML=exporter.export(chartPath)
            print chartXML
            importer.