'''
Created on Jul 21, 2020

@author: phass
'''
EXPONENTIAL = "Exponential"
PID = "PID"
EDIT_MODE = "edit"

import system
from ils.common.config import getTagProviderClient
from ils.common.cast import extendedPropertiesToDictionary
from ils.log import getLogger
log =getLogger(__name__)

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened", __name__)
    
    mode = rootContainer.mode
    log.infof("   mode: %s", mode)
    
    if mode == EDIT_MODE: 
        biasType = rootContainer.biasType
        biasName = rootContainer.biasName
        unit = rootContainer.unit

        log.infof("   biasType: %s", biasType)
        log.infof("   biasName: %s", biasName)
        log.infof("   unit: %s", unit)
        
        if biasType == EXPONENTIAL:
            udtPath = "LabData/" + unit + "/LabFeedback/" + biasName
            log.infof("   udtPath: %s", udtPath)
    
            extendedProperties = system.tag.read(udtPath +".ExtendedProperties").value
            properties = extendedPropertiesToDictionary(extendedProperties)
            log.infof("   Property Dictionary: %s", str(properties))
            
            tagValues = system.tag.readAll([udtPath+"/averageWindowMinutes", udtPath+"/filterConstant", udtPath+"/modelDeadTimeMinutes", udtPath+"/multiplicative", udtPath+"/rateOfChangeLimit" ])
            
            averageWindowMinutes = tagValues[0].value
            filterConstant = tagValues[1].value
            modelDeadTimeMinutes = tagValues[2].value
            multiplicative = tagValues[3].value
            rateOfChangeLimit = tagValues[4].value
            
            log.infof("   averageWindowMinutes: %s", str(averageWindowMinutes))
            log.infof("   filterConstant: %s", str(filterConstant))
            log.infof("   modelDeadTimeMinutes: %s", str(modelDeadTimeMinutes))
            log.infof("   multiplicative: %s", str(multiplicative))
            log.infof("   rateOfChangeLimit: %s", str(rateOfChangeLimit))
            
            container = rootContainer.getComponent("Exponential Container")
            print "Container: ", container
            
            ''' UDT Properties '''
            biasTargetServerType = properties.get("Bias Target Server Type", "")
            rootContainer.getComponent("Server Type").selectedStringValue = biasTargetServerType
            
            if biasTargetServerType == "OPC":
                rootContainer.getComponent("Server Name OPC").selectedStringValue = properties.get("Bias Target Server Name", "")
            else:
                rootContainer.getComponent("Server Name HDA").selectedStringValue = properties.get("Bias Target Server Name", "")
                
            rootContainer.getComponent("Item Id").text = properties.get("Bias Target Item Id", "")
            rootContainer.getComponent("Lab Value Name").text = properties.get("Lab Value Name", "")
            rootContainer.getComponent("Model Name").text = properties.get("Model Name", "")
            
            ''' UDT member tags '''
            container.getComponent("Average Window Minutes").floatValue = averageWindowMinutes
            container.getComponent("Filter Constant").floatValue = filterConstant
            container.getComponent("Model Dead Time Minutes").floatValue = modelDeadTimeMinutes
            container.getComponent("Multiplicative").selected = multiplicative
            container.getComponent("Rate of Change Limit").floatValue = rateOfChangeLimit
            
        elif biasType == PID:
            udtPath = "LabData/" + unit + "/LabFeedback/" + biasName
    
            extendedProperties = system.tag.read(udtPath +".ExtendedProperties").value
            properties = extendedPropertiesToDictionary(extendedProperties)
            log.infof("Property Dictionary: %s", str(properties))
            
            tagValues = system.tag.readAll([udtPath+"/averageWindowMinutes", udtPath+"/initializingBias", udtPath+"/integralGain", udtPath+"/modelDeadTimeMinutes", udtPath+"/multiplicative", udtPath+"/proportionalGain", udtPath+"/rateOfChangeLimit" ])
            
            averageWindowMinutes = tagValues[0].value
            initializingBias = tagValues[1].value
            integralGain = tagValues[2].value
            modelDeadTimeMinutes = tagValues[3].value
            multiplicative = tagValues[4].value
            proportionalGain = tagValues[5].value
            rateOfChangeLimit = tagValues[6].value
            
            container = rootContainer.getComponent("PID Container")
            
            ''' UDT Properties '''
            rootContainer.getComponent("Server Type").selectedStringValue = properties.get("Bias Target Server Type", "")
            rootContainer.getComponent("Server Name").text = properties.get("Bias Target Server Name", "")
            rootContainer.getComponent("Item Id").text = properties.get("Bias Target Item Id", "")
            rootContainer.getComponent("Lab Value Name").text = properties.get("Lab Value Name", "")
            rootContainer.getComponent("Model Name").text = properties.get("Model Name", "")
            
            ''' UDT member tags '''
            container.getComponent("Average Window Minutes").floatValue = averageWindowMinutes
            container.getComponent("Initializing Bias").floatValue = initializingBias
            container.getComponent("Integral Gain").floatValue = integralGain
            container.getComponent("Model Dead Time Minutes").floatValue = modelDeadTimeMinutes
            container.getComponent("Proportional Gain").floatValue = proportionalGain
            container.getComponent("Rate of Change Limit").floatValue = rateOfChangeLimit
            container.getComponent("Multiplicative").selected = multiplicative


def okCallback(event):
    rootContainer = event.source.parent
    log.infof("In %s.okCallback", __name__)
    
    oldBiasName = rootContainer.biasName
    mode = rootContainer.mode
    tagProvider = getTagProviderClient()
    
    unitName = rootContainer.getComponent("Unit Name").selectedStringValue
    if unitName == "":
        system.gui.warningBox("You must select a UNIT!")
        return
    
    biasType = rootContainer.getComponent("Bias Type").selectedStringValue
    if biasType == "":
        system.gui.warningBox("You must select a BIAS TYPE!")
        return
    
    newBiasName = rootContainer.getComponent("Bias Name").text
    if newBiasName == "":
        system.gui.warningBox("You must specify a BIAS NAME!")
        return
    
    ''' These UDT properties are common to both bias types '''
    serverType = str(rootContainer.getComponent("Server Type").selectedStringValue)
    if serverType == "":
        system.gui.warningBox("You must select a SERVER TYPE!")
        return
    
    if serverType == "OPC":
        serverName = str(rootContainer.getComponent("Server Name OPC").selectedStringValue)
        if serverName == "":
            system.gui.warningBox("You must specify a SERVER NAME!")
            return
    else:
        serverName = str(rootContainer.getComponent("Server Name HDA").selectedStringValue)
        if serverName == "":
            system.gui.warningBox("You must specify a SERVER NAME!")
            return
    
    itemId = str(rootContainer.getComponent("Item Id").text)
    if itemId == "":
        system.gui.warningBox("You must specify an ITEM ID!")
        return
    
    labValueName = str(rootContainer.getComponent("Lab Value Name").text)
    if labValueName == "":
        system.gui.warningBox("You must specify an LAB VALUE NAME!")
        return
    
    modelName = str(rootContainer.getComponent("Model Name").text)
    if modelName == "":
        system.gui.warningBox("You must specify an MODEL NAME!")
        return
    
    if biasType == PID:
        ''' PID '''
        container = rootContainer.getComponent("PID Container")
        
        averageWindowMinutes = container.getComponent("Average Window Minutes").floatValue
        initializingBias = container.getComponent("Initializing Bias").floatValue
        integralGain = container.getComponent("Integral Gain").floatValue
        modelDeadTimeMinutes = container.getComponent("Model Dead Time Minutes").floatValue
        proportionalGain = container.getComponent("Proportional Gain").floatValue
        rateOfChangeLimit = container.getComponent("Rate of Change Limit").floatValue
        multiplicative = container.getComponent("Multiplicative").selected
        
        parameters = {"Bias Target Server Type": serverType, "Bias Target Server Name": serverName, "Bias Target Item Id": itemId, "Lab Value Name": labValueName, "Model Name": modelName}
        print "Parameters: ", parameters
        
        if mode == EDIT_MODE:
            log.infof("...updating an existing UDT...")
            tagPath = "[" + tagProvider + "]LabData/" + unitName + "/LabFeedback/"  + oldBiasName
            attributes={"Name": newBiasName}
                
            system.tag.editTag(tagPath, parameters=parameters, attributes=attributes)
            
            tagPath = "[" + tagProvider + "]LabData/" + unitName + "/LabFeedback/"  + newBiasName
            system.tag.write(tagPath + "/averageWindowMinutes", averageWindowMinutes)
            system.tag.write(tagPath + "/initializingBias", initializingBias)
            system.tag.write(tagPath + "/integralGain", integralGain)
            system.tag.write(tagPath + "/modelDeadTimeMinutes", modelDeadTimeMinutes)
            system.tag.write(tagPath + "/proportionalGain", proportionalGain)
            system.tag.write(tagPath + "/rateOfChangeLimit", rateOfChangeLimit)
            system.tag.write(tagPath + "/multiplicative", multiplicative)
            
        else:
            UDTType='Lab Bias/Lab Bias PID'
            path = "LabData/" + unitName + "/LabFeedback"
            parentPath = "[%s]%s" % (tagProvider, path)  
            tagPath = parentPath + "/" + newBiasName
    
            tagExists = system.tag.exists(tagPath)
            
            if tagExists:
                log.infof("%s already exists!", tagPath)
            else:
                log.infof("Creating a %s, Name: %s, Path: %s", UDTType, newBiasName, tagPath)
                system.tag.addTag(parentPath=parentPath, name=newBiasName, tagType="UDT_INST", 
                                  attributes={"UDTParentType":UDTType}, parameters=parameters)
                
                tagPath = path + "/" + newBiasName

                system.tag.write(tagPath + "/averageWindowMinutes", averageWindowMinutes)
                system.tag.write(tagPath + "/initializingBias", initializingBias)
                system.tag.write(tagPath + "/integralGain", integralGain)
                system.tag.write(tagPath + "/modelDeadTimeMinutes", modelDeadTimeMinutes)
                system.tag.write(tagPath + "/proportionalGain", proportionalGain)
                system.tag.write(tagPath + "/rateOfChangeLimit", rateOfChangeLimit)
                system.tag.write(tagPath + "/multiplicative", multiplicative)
    
    elif biasType == EXPONENTIAL:
        '''   Exponential   '''
        container = rootContainer.getComponent("Exponential Container")
        
        averageWindowMinutes = container.getComponent("Average Window Minutes").floatValue
        filterConstant = container.getComponent("Filter Constant").floatValue
        modelDeadTimeMinutes = container.getComponent("Model Dead Time Minutes").floatValue
        multiplicative = container.getComponent("Multiplicative").selected
        rateOfChangeLimit = container.getComponent("Rate of Change Limit").floatValue
        
        parameters = {"Bias Target Server Type": serverType, "Bias Target Server Name": serverName, "Bias Target Item Id": itemId, "Lab Value Name": labValueName, "Model Name": modelName}
        print "Parameters: ", parameters
        
        if mode == EDIT_MODE:
            log.infof("...updating an existing UDT...")
            tagPath = "[" + tagProvider + "]LabData/" + unitName + "/LabFeedback/"  + oldBiasName
            attributes={"Name": newBiasName}
            
            system.tag.editTag(tagPath, parameters=parameters, attributes=attributes)
            
            tagPath = "[" + tagProvider + "]LabData/" + unitName + "/LabFeedback/"  + newBiasName
            system.tag.write(tagPath + "/averageWindowMinutes", averageWindowMinutes)
            system.tag.write(tagPath + "/filterConstant", filterConstant)
            system.tag.write(tagPath + "/modelDeadTimeMinutes", modelDeadTimeMinutes)
            system.tag.write(tagPath + "/multiplicative", multiplicative)
            system.tag.write(tagPath + "/rateOfChangeLimit", rateOfChangeLimit)
            
        else:
            UDTType='Lab Bias/Lab Bias Exponential Filter'
            path = "LabData/" + unitName + "/LabFeedback"
            parentPath = "[%s]%s" % (tagProvider, path)  
            tagPath = parentPath + "/" + newBiasName
    
            tagExists = system.tag.exists(tagPath)
            
            if tagExists:
                log.infof("%s already exists!", tagPath)
            else:
                log.infof("Creating a %s, Name: %s, Path: %s", UDTType, newBiasName, tagPath)
                system.tag.addTag(parentPath=parentPath, name=newBiasName, tagType="UDT_INST", 
                                  attributes={"UDTParentType":UDTType}, parameters=parameters)
                
                tagPath = path + "/" + newBiasName

                system.tag.write(tagPath + "/averageWindowMinutes", averageWindowMinutes)
                system.tag.write(tagPath + "/filterConstant", filterConstant)
                system.tag.write(tagPath + "/modelDeadTimeMinutes", modelDeadTimeMinutes)
                system.tag.write(tagPath + "/multiplicative", multiplicative)
                system.tag.write(tagPath + "/rateOfChangeLimit", rateOfChangeLimit)
    else:
        system.gui.errorBox("Unrecognized bias type: %s" % (biasType))
        return
    
    system.nav.closeParentWindow(event)
    