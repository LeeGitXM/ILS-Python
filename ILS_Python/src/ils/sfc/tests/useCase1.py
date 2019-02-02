'''
Created on Jan 29, 2019

@author: phass
'''

from ils.sfc.recipeData.api import s88CopyFolderValues 

def initData(chart, step):
    print "In initData()"

def copyFolderToFolder(chart, step):
    print "In copyFolderToFolder()"
    
    fromChartPath = "Use Cases/Use Case 1 Recipe Data Access/UseCase1"
    fromStepName = "UP"
    fromKey = "F1.H1.I1"
    
    toChartPath = fromChartPath
    toStepName = fromStepName
    toKey = "F1.H1.I2"
    
    recursive = False
    category = ""
    db = "XOM"

    s88CopyFolderValues(fromChartPath, fromStepName, fromKey, toChartPath, toStepName, toKey, recursive, category, db)
