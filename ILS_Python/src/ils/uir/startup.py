'''
Created on Oct 9, 2015

@author: Pete
'''

import system

def gateway(tagProvider, isolationTagProvider):
    # Create gateway loggers
    log = system.util.getLogger("com.ils.uir")
    
    from ils.uir.version import version
    version, revisionDate = version()
    log.info("Starting UIR modules version %s - %s" % (version, revisionDate))
    
    createTags("[" + tagProvider + "]", log)
    createTags("[" + isolationTagProvider + "]", log)

def createTags(tagProvider, log):
    print "Creating UIR configuration tags...."
    path = tagProvider + "Configuration/UIR/"
    
    

    # Make an empty dataset for the email list
    header=['First Name','Last Name','Email','Automatic UIR Email']
    rows=[['Fred','Smith','fredsmith@gmail.com',True]]
    emailListds = system.dataset.toDataSet(header, rows)
    
    # Make an empty dataset for the from list
    header=['Post Contains','From Email']
    rows=[]
    rows.append(['RLA','rla3@vistalon.com'])
    rows.append(['VFU','vfu@vistalon.com'])
    rows.append(['HFU','hfu@vistalon.com'])
    fromListds = system.dataset.toDataSet(header, rows)
    
    data = []
    data.append([path, "EmailList", "DataSet", emailListds])
    data.append([path, "fromList", "DataSet", fromListds])
    
    headers = ['Path', 'Name', 'Data Type', 'Value']
    ds = system.dataset.toDataSet(headers, data)
    
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
