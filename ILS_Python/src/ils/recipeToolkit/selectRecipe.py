'''
Created on Sep 10, 2014

@author: Pete
'''

import system
from ils.config.client import getDatabase
from ils.recipeToolkit.common import RECIPE_VALUES_INDEX, PROCESS_VALUES_INDEX

def initialize(rootContainer):
    print "In recipeToolkit.selectRecipe.initialize()..."
    db = getDatabase()
    familyName = rootContainer.familyName
    print "Recipe Family Name: %s" % (familyName)

    from ils.recipeToolkit.fetch import ids
    pds = ids(familyName, db)
    print "IDs: ", pds
    
    recipeTable = rootContainer.getComponent('Power Table')
    recipeTable.data = pds


def okCallback(event):
    print "In recipe.selectRecipe.okCallback()"
    rootContainer = event.source.parent
    
    recipeTable = rootContainer.getComponent('Power Table')
    if recipeTable.selectedRow < 0:
        system.gui.warningBox('Please select a grade!')
        return
    
    selectedRow = recipeTable.selectedRow
    ds = recipeTable.data
    grade = ds.getValueAt(selectedRow, 'Grade')
    version = ds.getValueAt(selectedRow, 'Version')
    
    # The recipe family name is passed into the window, and now on to the viewer
    familyName = rootContainer.familyName

    system.nav.openWindow('Recipe/Recipe Viewer', {'familyName': familyName, 'grade': grade, 'version': version,'downloadTypeIndex': RECIPE_VALUES_INDEX, 'mode': 'manual'})
    system.nav.centerWindow('Recipe/Recipe Viewer')
    
    system.nav.closeParentWindow(event)