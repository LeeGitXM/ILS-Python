'''
Created on Nov 13, 2016

@author: Pete
'''
# Modify models in the model set to add debugging and
# extended reporting. Skip the first dictionary - the 
# control header.
#
def modifyModelsForTest(models) :
    for model in models[1:]:
        model["debug"] = True
        model["extendedReporting"] = True
    