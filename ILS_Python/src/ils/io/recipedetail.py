'''
Created on Jul 9, 2014

@author: chuckc
'''
import ils.io.recipe as recipe
import system.tag as systemtag

class RecipeDetail(recipe.Recipe):
    def __init__(self,path):
        recipe.Recipe.__init__(self,path)


def writeRecipeDetail(self,command):
    
    #---------------------------------------------------------
    print "     downloading recipe detail: ", self.path,command
 
    # Get the configuration of this recipeDetail object
    tags = []
    for attr in ['highLimitTagName', 'lowLimitTagName','valueTagName']:
        tags.append(self.path + '/' + attr)
 
    print "Reading ", tags                                    
    vals = systemtag.readAll(tags)
 
    highLimitTagName = vals[0].value
    writeHighLimit = False if highLimitTagName == "" else True
                                                               
    lowLimitTagName = vals[1].value
    writeLowLimit = False if lowLimitTagName == "" else True
                               
    valueTagName = vals[2].value
    writeValue = False if valueTagName == "" else True
                               
    print highLimitTagName, valueTagName, lowLimitTagName
    print writeHighLimit, writeValue, writeLowLimit
                               
    if writeHighLimit:
        oldHighLimitValue = systemtag.read(self.path + '/' + highLimitTagName + '/Tag').value
        newHighLimitValue = systemtag.read(self.path + '/' + highLimitTagName + '/WriteVal').value                   
        print "Changing High limit from %f to %f" % (oldHighLimitValue, newHighLimitValue)
                               
    if writeLowLimit:
        oldLowLimitValue = systemtag.read(self.path + '/' + lowLimitTagName + '/Tag').value
        newLowLimitValue = systemtag.read(self.path + '/' + lowLimitTagName + '/WriteVal').value                    
        print "Changing Low limit from %f to %f" % (oldLowLimitValue, newLowLimitValue)
                               
    if writeValue:
        oldValue = systemtag.read(self.path + '/' + valueTagName + '/Tag').value
        newValue = systemtag.read(self.path + '/' + valueTagName + '/WriteVal').value
        print "Changing Value from %f to %f" % (oldValue, newValue)
                               
    highLimitWritten = False
    lowLimitWritten = False
    valueWritten = False
                               
    # If moving the upper limit up then writ it before the value
    if writeHighLimit:
        if newHighLimitValue > oldHighLimitValue:
            print "** Write the high limit ** ", newHighLimitValue
            highLimitWritten = True
            self.writeConfirm(self,highLimitTagName, 'WRITEDATUM', newHighLimitValue)
                               
    # If moving the upper limit up then writ it before the value
    if writeLowLimit:
        if newLowLimitValue < oldLowLimitValue:
            print "** Write the Low limit ** ", newLowLimitValue
            lowLimitWritten = True
            self.writeConfirm(self,lowLimitTagName, 'WRITEDATUM', newLowLimitValue)
 
    if writeValue:
        print "** Write the Value **", newValue
        self.writeConfirm(self,valueTagName, 'WRITEDATUM', newValue)
        valueWritten = True
 
    if writeHighLimit and not(highLimitWritten):
        print "** Write the high limit ** ", newHighLimitValue
        self.writeConfirm(self,highLimitTagName, 'WRITEDATUM', newHighLimitValue)
 
    if writeLowLimit and not(lowLimitWritten):
        print "** Write the low limit ** ", newLowLimitValue
        self.writeConfirm(self,lowLimitTagName, 'WRITEDATUM', newLowLimitValue)
            
    print "Done writing recipe detail: ", self.path