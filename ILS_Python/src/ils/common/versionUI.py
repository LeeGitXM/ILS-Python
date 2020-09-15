'''
Created on Jul 31, 2015

@author: Pete
'''

# This module initializes the version UI WINDOW

def internalFrameActivated(rootContainer):
    print "In internalFrameActivated()..."
    
    import ils.common.version as common 
    version, releaseDate = common.version()
    rootContainer.CommonVersion=version
    rootContainer.CommonReleaseDate=releaseDate
    
    import ils.common.database as database 
    version, releaseDate = database.version()
    rootContainer.DatabaseVersion=version
    rootContainer.DatabaseReleaseDate=releaseDate
    
    import ils.diagToolkit.version as diagToolkit 
    version, releaseDate = diagToolkit.version()
    rootContainer.DiagToolkitVersion=version
    rootContainer.DiagToolkitReleaseDate=releaseDate
    
    import ils.io.version as io 
    version, releaseDate = io.version()
    rootContainer.IOVersion=version
    rootContainer.IOReleaseDate=releaseDate
    
    import ils.labData.version as labData 
    version, releaseDate = labData.version()
    rootContainer.LabDataToolkitVersion=version
    rootContainer.LabDataToolkitReleaseDate=releaseDate

    import ils.recipeToolkit.version as recipe 
    version, releaseDate = recipe.version()
    rootContainer.RecipeToolkitVersion=version
    rootContainer.RecipeToolkitReleaseDate=releaseDate
    
    import ils.sfc.version as sfc 
    version, releaseDate = sfc.version()
    rootContainer.SFCVersion=version
    rootContainer.SFCReleaseDate=releaseDate
    print "The SFC version is: ", version
    
    import ils.sqc.version as sqc 
    version, releaseDate = sqc.version()
    rootContainer.SQCVersion=version
    rootContainer.SQCReleaseDate=releaseDate