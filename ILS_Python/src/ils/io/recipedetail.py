'''
Created on Jul 9, 2014

@author: chuckc
'''
import ils.io.recipe as recipe
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.io")

class RecipeDetail(recipe.Recipe):
    def __init__(self,path):
        recipe.Recipe.__init__(self,path)


    def writeRecipeDetail(self,command):
    
        #---------------------------------------------------------
        log.info("In RecipeDetail::writeRecipeDetail() with <%s>" % (self.path))
 
        # Get the path to this tag, the other tags will be in the same folder
        rootPath=self.path[0:self.path.rfind('/')+1]
        
        # Get the configuration of this recipeDetail object
        tags = []
        for attr in ['highLimitTagName', 'lowLimitTagName','valueTagName']:
            tags.append(self.path + '/' + attr)
 
        vals = system.tag.readAll(tags)
 
        highLimitTagName = vals[0].value
        writeHighLimit = False if highLimitTagName == "" else True

        lowLimitTagName = vals[1].value
        writeLowLimit = False if lowLimitTagName == "" else True

        valueTagName = vals[2].value
        writeValue = False if valueTagName == "" else True

        if writeHighLimit:
            oldHighLimitValue = system.tag.read(rootPath + highLimitTagName + '/tag').value
            newHighLimitValue = system.tag.read(rootPath + highLimitTagName + '/writeVal').value                   
            log.trace("Changing High limit from %s to %s" % (str(oldHighLimitValue), str(newHighLimitValue)))

        if writeLowLimit:
            oldLowLimitValue = system.tag.read(rootPath + lowLimitTagName + '/tag').value
            newLowLimitValue = system.tag.read(rootPath + lowLimitTagName + '/writeVal').value                    
            log.trace("Changing Low limit from %s to %s" % (str(oldLowLimitValue), str(newLowLimitValue)))

        if writeValue:
            oldValue = system.tag.read(rootPath + valueTagName + '/tag').value
            newValue = system.tag.read(rootPath + valueTagName + '/writeVal').value
            log.trace("Changing Value from %s to %s" % (str(oldValue), str(newValue)))

        highLimitWritten = False
        lowLimitWritten = False
        valueWritten = False

        # TODO - Should I bail as soon as one of the writes cannot be confirmed?
        status = True
        reason = ''
        
        # If moving the upper limit up then writ it before the value
        if writeHighLimit:
            if newHighLimitValue > oldHighLimitValue:
                log.trace("** Writing the high limit: %s **" % (str(newHighLimitValue)))
                highLimitWritten = True
                confirmed, r = self.writeConfirm(rootPath + highLimitTagName, 'WRITEDATUM', newHighLimitValue)
                reason = reason + r
                status = status and confirmed

        # If moving the upper limit up then writ it before the value
        if writeLowLimit:
            if newLowLimitValue < oldLowLimitValue:
                log.trace("** Writing the Low limit: %s **" % (str(newLowLimitValue)))
                lowLimitWritten = True
                confirmed, r = self.writeConfirm(rootPath + lowLimitTagName, 'WRITEDATUM', newLowLimitValue)
                reason = reason + r
                status = status and confirmed
 
        if writeValue:
            log.trace("** Writing the Value: %s **" % (str(newValue)))
            confirmed, r = self.writeConfirm(rootPath + valueTagName, 'WRITEDATUM', newValue)
            reason = reason + r
            status = status and confirmed
                
        if writeHighLimit and not(highLimitWritten):
            log.trace("** Writing the high limit: %s **" % (str(newHighLimitValue)))
            confirmed, r = self.writeConfirm(rootPath + highLimitTagName, 'WRITEDATUM', newHighLimitValue)
            reason = reason + r
            status = status and confirmed
                
        if writeLowLimit and not(lowLimitWritten):
            log.trace("** Write the low limit: %s **" % (str(newLowLimitValue)))
            confirmed, r = self.writeConfirm(rootPath + lowLimitTagName, 'WRITEDATUM', newLowLimitValue)
            reason = reason + r
            status = status and confirmed
                
        log.info("Done writing recipe detail: %s - %s - %s" % (self.path, status, reason))
        return status, reason