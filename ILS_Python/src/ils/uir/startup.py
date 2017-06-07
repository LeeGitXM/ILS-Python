'''
Created on Oct 9, 2015

@author: Pete
'''

import system

def gateway(provider):
    # Create gateway loggers
    log = system.util.getLogger("com.ils.uir")
    
    from ils.uir.version import version
    version, revisionDate = version()
    log.info("Starting UIR modules version %s - %s" % (version, revisionDate))
    
    createTags("[" + provider + "]", log)

def createTags(tagProvider, log):
    print "Creating UIR configuration tags...."
    path = tagProvider + "Configuration/UIR/"
    
    data = []

    # Make an empty dataset for the email list
    header=['First Name','Last Name','Email','Automatic UIR Email']
    rows=[['Fred','Smith','fredsmith@gmail.com',True]]
    ds = system.dataset.toDataSet(header, rows)
    
    data.append([path, "EmailList", "DataSet", ds])
    
    headers = ['Path', 'Name', 'Data Type', 'Value']
    ds = system.dataset.toDataSet(headers, data)
    
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
