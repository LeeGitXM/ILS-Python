'''
Created on Feb 2, 2015

@author: Pete
'''
import system, time
DEBUG = False

def createConfigurationTags(ds, log):
    log.infof("Processing %d configuration tags...", ds.rowCount)
    pds = system.dataset.toPyDataSet(ds)

    for row in pds:
        path = row["Path"]
        name = row["Name"]
        dataType = row["Data Type"]
        val = row["Value"]
        
        if path[len(path)-1] == "/":
            path = path[:len(path) - 1]
        
        fullName = path + "/" + name
        if DEBUG: log.infof("Checking if %s already exists...", fullName)
                
        # Check if the tag exists, only set the default value when we create the tag
        if not(system.tag.exists(fullName)):
            if dataType == "DataSet":
                if DEBUG: log.infof("  ...creating configuration tag %s - %s - %s", path, name, dataType) 
            else:
                if DEBUG: log.infof("  ...creating configuration tag %s - %s - %s - <%s>", path, name, dataType, str(val)) 
                
            if dataType == "Int8":
                val = int(val)
            elif dataType == "Float4":
                val = float(val)
            elif dataType == "Boolean":
                from ils.common.cast import toBool
                val = toBool(val)
            elif dataType == "DataSet":
                val = val

            i = 0
            doWork = True
            while doWork:
                i = i + 1
                success = createTag(path, name, dataType, val, log)
                if success:
                    doWork = False
                elif i > 10:
                    log.warnf("Giving up after 10 failed attempts to create configuration tag: <%s> in <%s>", name, path)
                    doWork = False
                else:
                    time.sleep(10)
        else:
            if DEBUG: log.infof("...tag already exists!")
            
def createTag(path, name, dataType, val, log):
    try:
        if DEBUG: log.infof("Creating Tag %s - %s", path, name)
        system.tag.addTag(parentPath=path, name=name, tagType="MEMORY", dataType=dataType, value=val)
        
    except:
        log.errorf("Caught an error creating the tag")
        return False
        
    if DEBUG: log.infof("...Tag was created!")
    return True