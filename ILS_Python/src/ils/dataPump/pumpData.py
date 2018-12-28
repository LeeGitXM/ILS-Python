'''
Created on Jun 20, 2017

@author: phass
'''

import system, time, string
from ils.common.cast import toDateTime
log = system.util.getLogger("com.ils.dataPump")

'''
This is called from the client and it runs entirly in the client.  It's main job is to write the dataset in the table to the datapump dataset tag
and then writ eto the data pump command tag to start the data pump running in the gateway.
'''
def pumpData(rootContainer):
    tagProvider = rootContainer.getComponent("TagProviderField").text

    # Write the data from the table to a dataset tag
    table = rootContainer.getComponent("Table")
    ds = table.data
    system.tag.write("%sData Pump/data" % (tagProvider), ds)
    
    # Write the PLAY command to the command tag
    system.tag.write("%sData Pump/command" % (tagProvider), "PLAY")
    

'''
This is called from a tag change script on the data pump's command tag.  It runs in the gateway.
If the command is PLAY then it will start the data pump which will run continuously until it is aborted or 
we reach the end of the dataset.
'''
def commandHandler(tagPath, command):
    command = command.value
    
    if command == "PLAY":
        player(tagPath)


def player(commandTagpath):
    log.info("Starting data pump player...")
    
    dataPumpPath, tagName, provider = parseTagPath(commandTagpath)
    
    ds = system.tag.getTagValue("%s/data" % (dataPumpPath))
    pds = system.dataset.toPyDataSet(ds)
    log.tracef("There are %d rows in the dataset...", len(pds))

    system.tag.writeToTag("%s/simulationState" % (dataPumpPath), "Running")
    
    # We have to give these writes a chance to get there
    time.sleep(1)    
    
    i = 0
    for row in pds:
        command = system.tag.getTagValue("%s/command" % (dataPumpPath))

        if command == "Abort":
            log.infof("*** ABORTING THE DATAPUMP ***")
            break

        system.tag.writeToTag("%s/lineNumber" % (dataPumpPath), i)
        j = 0
        for val in row:
            if (j == 0):
                j = j
            else:
                tagname = ds.getColumnName(j)
                fullTagPath = "[%s]%s" % (provider, tagname)
                
                txt = string.upper(tagname)

                if txt.find("TIME") > -1:
                    val = toDateTime(val)

                status = system.tag.write(fullTagPath, val)
                log.tracef("Tag: %s, Value: %s, Status: %s", fullTagPath, str(val), str(status) )

            j = j + 1

        # I don't want to go into a long wait state because I won't be able to react to a command if I do
        startTime = system.date.now()
        delay = system.tag.getTagValue("%s/timeDelay" % (dataPumpPath))
        while system.date.addSeconds(startTime, delay) > system.date.now():
            time.sleep(1)
            delay = system.tag.getTagValue("%s/timeDelay" % (dataPumpPath))

        i = i + 1

    log.infof("Done Pumping!")
    system.tag.writeToTag("%s/simulationState" % (dataPumpPath), "Idle")
    system.tag.writeToTag("%s/command" % (dataPumpPath), "Stop")

# The tagPath must begin with the provider surrounded by square brackets
def parseTagPath(tagPath):
    end = tagPath.rfind(']')
    provider = tagPath[1:end]
    end = tagPath.rfind('/')
    tagPathRoot = tagPath[:end]
    end = tagPath.rfind('/')
    tagName = tagPath[end + 1:]
    return tagPathRoot, tagName, provider