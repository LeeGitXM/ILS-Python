'''
Created on Oct 5, 2014

@author: Pete
'''
'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def gateway():
    from emc.vistalon.version import version
    version = version()
    print "Starting Vistalon ", version

    from ils.common.config import getTagProvider
    provider = getTagProvider()
    createTags("[" + provider + "]")

#
def createTags(tagProvider):
    print "Creating global constant memory tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []

    # Create site specific Vistalon "Local" recipe tags
    path = tagProvider + "Site/"
    data.append([path + "CATOUT-RECIPE-STATUS/", "CAST-TIME-TO-CLOSED", "Float8", "0.0"])
    data.append([path + "CATOUT-RECIPE-STATUS/", "IRG-TIME-TO-CLOSED", "Float8", "0.0"])
    data.append([path + "CATOUT-RECIPE-STATUS/", "OIL-TIME-TO-CLOSED", "Float8", "0.0"])
    data.append([path, "DML-ERROR-RATE-LIMIT", "Float8", "0.0"])
    data.append([path, "DML-SQC-FLAG", "Float8", "0.0"])
    data.append([path, "MLR-GRADE-FLAG", "Float8", "0.0"])
    data.append([path, "POLYMER-LAB-DATA-SOURCE", "Float8", "0.0"])
    data.append([path, "POLYSPLIT-SQC-FLAG", "Float8", "0.0"])
    data.append([path, "PROD-CA-SQC-FLAG", "Float8", "0.0"])
    data.append([path + "RX-RECIPE/", "CA-TARGET", "Float8", "0.0"])
    data.append([path + "RX-RECIPE/", "E202-BYPASS-DELTA-TIME", "Float8", "0.0"])
    data.append([path + "RX-RECIPE/", "E202-BYPASS-POSITION", "Float8", "0.0"])
    data.append([path + "RX-RECIPE/", "E204-LEVEL", "Float8", "0.0"])
    data.append([path + "RX-RECIPE/", "E204-TEMP", "Float8", "0.0"])
    data.append([path + "RX-RECIPE/", "GEL-DELAY", "Float8", "0.0"])
    data.append([path + "SERIES-PERMISSIVES/", "C3-TO-R2-OK-FLAG", "Float8", "0.0"])
    data.append([path + "SERIES-PERMISSIVES/", "C9-TO-R2-OK-FLAG", "Float8", "0.0"])
    data.append([path + "SERIES-PERMISSIVES/", "NO-C3-MIN-RATE", "Float8", "0.0"])
    data.append([path + "SERIES-PERMISSIVES/", "NO-C9-MIN-RATE", "Float8", "0.0"])
    data.append([path + "SERIES-PERMISSIVES/", "SERIES-MIN-C6-TO-R2", "Float8", "0.0"])

    data.append([path, "VFU-FTNIR-GRADE", "Float8", "0.0"])
    data.append([path, "VFU-FTNIR-BIAS-UPDATE", "Float8", "0.0"])
    data.append([path, "VFU-BALER-TEMP-CHK", "Float8", "0.0"])
    
    ds = system.dataset.toDataSet(headers, data)
    from ils.recipeToolkit.tagFactory import createConfigurationTags
    createConfigurationTags(ds)