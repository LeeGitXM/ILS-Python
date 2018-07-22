'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def initialize(rootContainer):
    print "In recipeToolkit.selectRecipe.initialize()..."

    familyName = rootContainer.familyName
    print "Recipe Family Name: %s" % (familyName)

#    from ils.recipeToolkit.fetch import recipeFamily
#    recipeFamily = recipeFamily(recipeKey)
#    print "Family: ", recipeFamily
    
#    familyName = recipeFamily['RecipeFamilyName']

    from ils.recipeToolkit.fetch import ids
    pds = ids(familyName)
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
    
    # Save the grade and type to the recipe family table.
    # grade looks like an int, but it is probably a string
    SQL = "update RtRecipeFamily set CurrentGrade = '%s', CurrentVersion = %s, Status = 'Initializing', "\
        "Timestamp = getdate() where RecipeFamilyName = '%s'" \
        % (str(grade), version, familyName)
    
    print "SQL: ", SQL
    rows = system.db.runUpdateQuery(SQL)
    print "Successfully updated %i rows" % (rows)

    system.nav.openWindow('Recipe/Recipe Viewer', {'familyName': familyName, 'grade': grade, 'version': version,'downloadType':'GradeChange', 'mode': 'manual'})
    system.nav.centerWindow('Recipe/Recipe Viewer')
    
    system.nav.closeParentWindow(event)