'''
Created on Jan 9, 2017

@author: phass
'''

import xml.etree.ElementTree as ET

def migrateChart(chartPath, resourceId, chartResourceAsXML, database):
    print "***************"
    print "Migrating a charts (%s-%s) recipe data(PYTHON)..." % (chartPath, str(resourceId))
    print "***************"
    print chartResourceAsXML
    print "-------"
    
    print "parsing the tree..."
    root = ET.fromstring(chartResourceAsXML)
    
#    print "getting the root"
#    root = tree.getroot()

    for step in root.findall('step'):
        print "=============="
        print "Found a step"
        stepName = step.get("name")
        stepId = step.get("id")
        stepType = step.get("factory-id")
        
        for associatedData in step.findall('associated-data'):
            print "     Found an associated data"
            print associatedData
            print associatedData.text
            print associatedData.attrib
            
        print "   ...%s - %s - %s - %s" % (stepName, stepType, stepId, str(associatedData))

def migrateStep():
    print "Migrating a steps recipe data..."