'''
Created on Jun 29, 2015

@author: Pete
'''

# Initialize the diagnosis Queue View
def initializeView(rootContainer):
    post = rootContainer.getPropertyValue("post")
    title = post + ' Console Diagnosis Message Queue'
    rootContainer.setPropertyValue('title', title) 
    print "Done initializing!"