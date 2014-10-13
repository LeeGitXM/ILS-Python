'''
Created on Sep 10, 2014

@author: Pete
'''

# This should be the only place in teh project that we hard-code the provider name EMC.
# It would be better to get this from some configurable place.  
# This will generally get called by some top-level entry point and then passed along to anyone 
# that needs it.
def getTagProvider():
    return 'XOM'