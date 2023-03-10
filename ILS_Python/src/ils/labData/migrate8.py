'''
Created on Jul 25, 2022

@author: phass
'''
'''
Created on May 31, 2017

@author: phass
'''

import system, os, string
from ils.sfc.recipeData.hierarchyWithBrowser import fetchHierarchy
from ils.common.config import getDatabaseClient
from ils.common.error import notifyError
from ils.log import getLogger
log =getLogger(__name__)

def exportCallback(event):

    try:
        db = getDatabaseClient()
        log.infof("In %s.exportCallback()...", __name__)

        rootContainer = event.source.parent

        filename = rootContainer.fileName
        if filename == None:
            return
        
        exporter = Exporter(db)
        cnt, txt = exporter.export()
        
        system.file.writeFile(filename, txt, False)
        system.gui.messageBox("%d unit parameters were exported!" % (cnt))
    except:
        notifyError("%s.exportCallback()" % (__name__), "Check the console log for details.")
       
class Exporter():
    sfcRecipeDataShowProductionOnly = False
    db = None

    def __init__(self, db):
        self.db = db

    def export(self):
        log.infof("In %s.export()", __name__)
        
        print "Browsing..."
        browseTags = system.tag.browseTags(parentPath="", udtParentType="Lab Data/Unit Parameter", recursive=True)

        for browseTag in browseTags:
            print browseTag.name
            print browseTag.fullPath
            print "==========="

            log.tracef("...fetched Unit Parameter: %s", browseTag.fullPath)
            numberOfPoints = system.tag.read("%s/numberOfPoints" % (browseTag.fullPath)).value
            ignoreSampleTime = system.tag.read("%s/ignoreSampleTime" % (browseTag.fullPath)).value
            valueReference = system.tag.getAttribute(browseTag.fullPath + "/rawValue", "Expression")
            sampleTimeReference = system.tag.getAttribute(browseTag.fullPath + "/sampleTime", "Expression")
            
            ''' The two references are actually the expressions of an expression tag, so strip off the { and } that enclose the expression. '''
            valueReference = valueReference[1:len(valueReference)-1]
            sampleTimeReference = sampleTimeReference[1:len(sampleTimeReference)-1]
            
            ''' 
            The tag provider names may change from the old system to the new system.  Create the new Unit Parameter in the 
            default tag provider.
            '''
            valueReference = valueReference[valueReference.index("]")+1:]
            sampleTimeReference = sampleTimeReference[sampleTimeReference.index("]")+1:]
            
            txt = "<unitParameter "
            txt = txt + " name=\"%s\" " % (browseTag.name)
            txt = txt + "fullPath=\"%s\" " % (browseTag.fullPath)
            txt = txt + "ignoreSampleTime=\"%s\" " % (str(ignoreSampleTime))
            txt = txt + "numberOfPoints=\"%d\" " % (numberOfPoints)
            txt = txt + "valueReference=\"%s\" " % (valueReference)
            txt = txt + "sampleTimeReference=\"%s\" " % (sampleTimeReference)
            txt = txt + "/>\n\n"
            
        txt = "<data>\n" + txt + "</data>"
        return len(browseTags), txt