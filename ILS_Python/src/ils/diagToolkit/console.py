'''
Created on Mar 18, 2016

@author: ils
'''
import system

# This is called from a timer embedded in the Setpoint Spreadsheet Button on the console window.
# It does a quick little query to see if there are any active outputs for this console .
# If there are then it sets the "active" state of the template to True which in turn is 
# used to animate the color of the arrow. The user can launch the setpoint spreadsheet 
# any time they want, even if there isn't an active output, but the arrow animation is useful 
# to quickly see if there is something to see. 
def checkRecommendationState(buttonContainer):
    database=system.tag.read("[Client]Database").value    
    post = buttonContainer.post
    
    from ils.diagToolkit.common import fetchActiveOutputsForPost
    pds = fetchActiveOutputsForPost(post, database)
    
    if len(pds) == 0:
        from ils.diagToolkit.common import fetchActiveTextRecommendationsForPost
        pds = fetchActiveTextRecommendationsForPost(post, database)
        if len(pds) == 0:
            state=False
        else:
            state = True
    else:
        state=True
    
    buttonContainer.active=state