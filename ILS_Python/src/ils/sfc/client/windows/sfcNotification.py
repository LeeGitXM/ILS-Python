'''
Created on Jan 15, 2015

@author: rforbes
'''
def visionWindowOpened(event):
    rootContainer = event.source.getRootContainer()
    rootContainer.getComponent('textField').text = rootContainer.message 