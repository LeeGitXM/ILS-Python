'''
Created on Jun 17, 2020

@author: phass
'''

import system, string
from ils.config.client import getDatabase
from ils.common.util import parseFilename
from ils.log import getLogger
log = getLogger(__name__)

def internalFrameOpened(event):
    log.infof("In %s.internalFrameOpened()", __name__)
    db = getDatabase()
    rootContainer = event.source.rootContainer
    windowId = rootContainer.windowId
    
    title = system.db.runScalarQuery("select title from sfcWindow where windowId = '%s'" % (windowId), db)
    rootContainer.title = title
        
    SQL = "select * from SfcSaveData where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, db)
    record = pds[0]

    fileLocation = record["fileLocation"]
    print "File Location: ", fileLocation
    
    filename = record["filePath"]
    drive, rootFilename, extension = parseFilename(filename)
    print "Filename: ", filename
    print "Drive: ", drive
    print "File root: ", rootFilename
    print "Extension: ", extension

    rootContainer.extension = extension
    
    if string.upper(fileLocation) == "CLIENT":
        exists = system.file.fileExists(filename)
        if not(exists):
            system.gui.errorBox("File: %s does not exist!" % (filename))
            return
        
        if string.upper(extension) == "PDF":        
            viewer = rootContainer.getComponent("PDF Viewer")
            binaryData = system.file.readFileAsBytes(filename) 
            viewer.setBytes(binaryData)
        else:
            stringData = system.file.readFileAsString(filename)
            rootContainer.textData = stringData
        
    else:
        if string.upper(extension) == "PDF":        
            viewer = rootContainer.getComponent("PDF Viewer")
            viewer.setBytes(record["binaryData"])
        else:
            rootContainer.textData = record["textData"]
            rootContainer.extension = extension


def displayGIF(event):
    '''
    Got this off of the IA forum - it would be useful if we want to display a graphics object in an image widget...
    Not sure we need to support this right now.
    '''
    from javax.swing import ImageIcon
    from java.io import ByteArrayInputStream
    from javax.imageio import ImageIO
    from java.awt import Image
    from java.net import URL
    from java.io import File
    
    image = system.db.runQuery("SELECT IMG FROM assets where Num=%d" % (event.source.parent.Num))
    bais = ByteArrayInputStream(image)
    bImageFromConvert = ImageIO.read(bais)
    lbl3 = event.source.parent.getComponent('lblImage3')
    boundWidth = lbl3.width
    boundHeight = lbl3.height
    originalWidth = bImageFromConvert.width
    originalHeight = bImageFromConvert.height
    newWidth = originalWidth
    newHeight = originalHeight
    
    if originalWidth > boundWidth:
        newWidth = boundWidth
        newHeight = (newWidth * originalHeight) / originalWidth
        
    if newHeight > boundHeight:
        newHeight = boundHeight
        newWidth = (newHeight * originalWidth) / originalHeight
    
    scaledImage = bImageFromConvert.getScaledInstance(newWidth,newHeight,Image.SCALE_SMOOTH)
    lbl3.setIcon(ImageIcon(scaledImage))


    
