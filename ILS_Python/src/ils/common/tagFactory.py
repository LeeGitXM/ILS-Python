'''
Created on Feb 2, 2015

@author: Pete
'''
import system, time
DEBUG = False

def createConfigurationTags(ds, log):
    '''
    The reason for the timeout is that occasionally, on startup, the tag system can be busy in the mad race for everything to startup.
    It is possible that this is called before the tag providers are started, so add in a retry and delay.
    In order to prevent startups from taking forever (and really hanging shutdowns, if someone shutsdown the system right after starting it -
    this is really common on an install, where they enable the projects in the gateway web page and then shutdown the system.  Enabling the
    projects triggers the project startup scripts in their own thread and the gateway shutdown stops the tag providers immediatly and then 
    these startup scripts will go into a massive long timeout loop that can go for a couple of hours....)
    So only delay for the first tag that has trouble, i.e., if we are creating 20 tags for lab data, then only do the timeout for the first one.
    '''
    log.infof("Processing %d configuration tags...", ds.rowCount)
    pds = system.dataset.toPyDataSet(ds)
    firstTag = True

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
                else:
                    if firstTag:
                        if i > 10:
                            log.warnf("Giving up after 10 failed attempts to create configuration tag: <%s> in <%s>", name, path)
                            doWork = False
                        else:
                            time.sleep(10)
                    else:
                        log.warnf("Unable to create configuration tag: <%s> in <%s>", name, path)
            firstTag = False
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