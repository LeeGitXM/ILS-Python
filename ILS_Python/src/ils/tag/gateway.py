'''
Copyright 2017 ILS Automation. All rights reserved.
Gateway scope tag utilities
'''

import com.inductiveautomation.ignition.gateway.SRContext as SRContext
import com.inductiveautomation.ignition.common.sqltags.parser.TagPathParser as TagPathParser

# Determine tag type given its path
def typeForTagPath(path):
    context = SRContext.get()
    try:
        tp = TagPathParser.parse(path)
        print "typeForTag: path =  ",path
        provider = context.getTagManager().getTagProvider(tp.getSource())
        if provider<>None:
            tag = provider.getTag(tp)
            if tag==None:
                return provider.getName()+" did not find "+tp.toStringFull()
            return tag.getType().name()
        else:
            return "typeForTag: provider ("+str(tp.getSource())+") not found"
    except:
        return "typeForTag: Unknown/Illegal tag path("+str(path)+")"
