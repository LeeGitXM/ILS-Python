'''
Created on Mar 31, 2015

@author: Pete
'''
import system
def launcher(payload):
    valueId=payload.get("valueId", -1)
    valueName=payload.get("valueName", "")
    
    system.nav.openWindow("Lab Data/Validity Limit Warning", {"valueId":valueId, "valueName": valueName})