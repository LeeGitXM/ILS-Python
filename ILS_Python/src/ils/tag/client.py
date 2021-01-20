'''
Copyright 2017 ILS Automation. All rights reserved.
Client/Designer scope tag utilities
'''
import com.inductiveautomation.factorypmi.application.FPMIApp as FPMIApp
import com.inductiveautomation.ignition.common.sqltags.parser.TagPathParser as TagPathParser

# Determine tag type given a path.
def typeForTagPath(path):
    app = FPMIApp.getInstance();
    context = app.getAdapterContext()
    try:
        tp = TagPathParser.parse(path)
        #print "typeForTag: tagPath = ",tp.toStringFull()
        tags = context.getTagManager().getTags([tp])
        for tag in tags:
            if tag<>None:
                return tag.getType().name()
        return "Tag ("+str(path)+") not found"
    except:
        return "Illegal tag name ("+path+")"
    
def dataTypeForTagPath(path):
    app = FPMIApp.getInstance();
    context = app.getAdapterContext()
    try:
        tp = TagPathParser.parse(path)
        #print "typeForTag: tagPath = ",tp.toStringFull()
        tags = context.getTagManager().getTags([tp])
        for tag in tags:
            if tag<>None:
                return tag.getDataType().name()
        return "Tag ("+str(path)+") not found"
    except:
        return "Illegal tag name ("+path+")"