'''
Created on Jul 1, 2019

@author: phass
'''

import system
from ils.io.util import readTag

def findFromAddress(post):
    '''
    Get the from address and the pile prefix for the specified post from the email configuration dataset tag
    '''
    ds = readTag("[XOM]Configuration/UIR/fromList").value

    fromEmail = "UIR"
    filePrefix = ""
    
    for row in range(ds.rowCount):
        postContains = ds.getValueAt(row,"Post Contains")
        if post.find(postContains) != -1:
            fromEmail = ds.getValueAt(row,"From Email")
            filePrefix = ds.getValueAt(row,"File Prefix")
            
    return fromEmail, filePrefix