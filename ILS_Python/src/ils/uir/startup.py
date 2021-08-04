'''
Created on Oct 9, 2015

@author: Pete
'''

import system

def gateway(tagProvider, isolationTagProvider):
    # Create gateway loggers
    from ils.log.LogRecorder import LogRecorder
    log = LogRecorder(__name__)
    
    from ils.uir.version import version
    version, revisionDate = version()
    log.info("Starting UIR modules version %s - %s" % (version, revisionDate))
    
    createTags("[" + tagProvider + "]", log)
    createTags("[" + isolationTagProvider + "]", log)

def createTags(tagProvider, log):
    print "Creating UIR configuration tags for %s...." % (tagProvider)
    
    path = tagProvider + "Configuration/UIR"
    
    # Make an empty dataset for the email list
    header=['First Name','Last Name','Email','Automatic UIR Email','Manual Email']
    rows = []
    rows.append(['Michael','Kurtz','michael.kurtz@exxonmobil.com',False, False])
    rows.append(['Segun','Ojewole','olusegun@exxonmobil.com',True, False])
    rows.append(['Jeffrey','DeCicco','jdecicco@ils-automation.com',True, False])
    emailListds = system.dataset.toDataSet(header, rows)
    
    # Make an empty dataset for the from list
    header=['Post Contains','From Email', 'File Prefix']
    rows=[]
    rows.append(['RLA','rla3@vistalon.com', 'R'])
    rows.append(['VFU','vfu@vistalon.com', 'V'])
    rows.append(['HFU','hfu@vistalon.com', 'H'])
    fromListds = system.dataset.toDataSet(header, rows)
    
    data = []
    data.append([path, "EmailList", "DataSet", emailListds])
    data.append([path, "fromList", "DataSet", fromListds])
    
    headers = ['Path', 'Name', 'Data Type', 'Value']
    ds = system.dataset.toDataSet(headers, data)
    
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
