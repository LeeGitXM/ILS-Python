'''
Created on Feb 2, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil

def createConfigurationTags(ds, log):
    log.info("Creating configuration tags...")
    pds = system.dataset.toPyDataSet(ds)

    for row in pds:
        path = row["Path"]
        name = row["Name"]
        dataType = row["Data Type"]
        val = row["Value"]
        
        fullName = path + name
                
        # Check if the tag exists, only set the default value when we create the tag
        if not(system.tag.exists(fullName)):
            log.info("  ...creating configuration tag %s" % (fullName)) 
            
            if dataType == "Int8":
                val = int(val)
            elif dataType == "Float4":
                val = float(val)
            elif dataType == "Boolean":
                from ils.common.cast import toBool
                val = toBool(val)
            
            system.tag.addTag(parentPath=path, name=name, tagType="MEMORY", dataType=dataType, value=val)