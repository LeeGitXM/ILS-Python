'''
Created on Jun 20, 2017

@author: phass
'''

import system, time, string
from ils.common.cast import toDateTime
from ils.io.util import writeTag, readTag
from ils.log import getLogger
log = getLogger(__name__)


def pumpData(rootContainer):
    '''
    This is called from the client.  It's job is to write the dataset in the table to the datapump dataset tag
    and then write to the data pump command tag to start the data pump running in the gateway from a tag change script.
    '''
    tagProvider = rootContainer.getComponent("TagProviderField").text

    # Write the data from the table to a dataset tag
    table = rootContainer.getComponent("Table")
    ds = table.data
    writeTag("%sData Pump/data" % (tagProvider), ds)
    
    # Write the PLAY command to the command tag
    writeTag("%sData Pump/command" % (tagProvider), "PLAY")
    

def commandHandler(tagPath, command):
    '''
    This is called from a tag change script on the data pump's command tag.  It runs in the gateway.
    If the command is PLAY then it will start the data pump which will run continuously until it is aborted or 
    we reach the end of the dataset.
    '''
    command = command.value
    
    if command == "PLAY":
        player(tagPath)


def player(commandTagpath):
    log.info("Starting data pump player...")
    
    dataPumpPath, tagName, provider = parseTagPath(commandTagpath)
    
    ds = readTag("%s/data" % (dataPumpPath)).value
    pds = system.dataset.toPyDataSet(ds)
    log.tracef("There are %d rows in the dataset...", len(pds))

    writeTag("%s/simulationState" % (dataPumpPath), "Running")
    
    # We have to give these writes a chance to get there
    time.sleep(1)    
    
    i = 0
    for row in pds:
        command = readTag("%s/command" % (dataPumpPath)).value

        if command == "Abort":
            log.infof("*** ABORTING THE DATAPUMP ***")
            break

        writeTag("%s/lineNumber" % (dataPumpPath), i)
        
        if row[0][0] == "#":
            log.tracef("Found a comment...")
            log.infof("%s", row[0])
        else:
            log.tracef("Handling a row...")
            j = 0
            for val in row:
                log.tracef("   val: %s", str(val))
                if (j == 0):
                    j = j
                else:
                    tagname = ds.getColumnName(j)
                    fullTagPath = "[%s]%s" % (provider, tagname)
                    
                    txt = string.upper(tagname)
    
                    if txt.find("TIME") > -1 and val <> "":
                        log.tracef("...converting a date string...")
                        val = toDateTime(val)
    
                    if val <> "":
                        writeTag(fullTagPath, val)
                        log.tracef("Tag: %s, Value: %s", fullTagPath, str(val))
    
                j = j + 1

        # I don't want to go into a long wait state because I won't be able to react to a command if I do
        startTime = system.date.now()
        delay = readTag("%s/timeDelay" % (dataPumpPath)).value
        while system.date.addSeconds(startTime, delay) > system.date.now():
            time.sleep(1)
            delay = readTag("%s/timeDelay" % (dataPumpPath)).value

        i = i + 1

    log.infof("Done Pumping!")
    writeTag("%s/simulationState" % (dataPumpPath), "Idle")
    writeTag("%s/command" % (dataPumpPath), "Stop")

# The tagPath must begin with the provider surrounded by square brackets
def parseTagPath(tagPath):
    end = tagPath.rfind(']')
    provider = tagPath[1:end]
    end = tagPath.rfind('/')
    tagPathRoot = tagPath[:end]
    end = tagPath.rfind('/')
    tagName = tagPath[end + 1:]
    return tagPathRoot, tagName, provider