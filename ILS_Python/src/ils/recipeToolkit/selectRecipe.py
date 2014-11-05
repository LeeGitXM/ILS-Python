'''
Created on Sep 10, 2014

@author: Pete
'''

import system

def initialize(rootContainer):
    print "In recipeToolkit.selectRecipe.initialize()..."

    recipeKey = rootContainer.recipeKey
    print "Recipe Key: %s" % (recipeKey)

    from ils.recipeToolkit.fetch import recipeMap
    recipeMap = recipeMap(recipeKey)
    print "Map: ", recipeMap
    
    family = recipeMap['RecipeFamily']

    from ils.recipeToolkit.fetch import ids
    pds = ids(family)
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
    
    # RecipeKey is synonomous with unitId
    recipeKey = rootContainer.recipeKey
    
    # Save the grade and type to the recipe map table.
    # grade looks like an int, but it is probably a string
    SQL = "update RtRecipeMap set CurrentRecipeGrade = %s, CurrentRecipeVersion = %s, Status = 'Initializing', "\
        "Timestamp = getdate() where RecipeKey = '%s'" \
        % (str(grade), version, recipeKey)
    
    print "SQL: ", SQL
    rows = system.db.runUpdateQuery(SQL)
    print "Successfully updated %i rows" % (rows)

    system.nav.openWindow('Recipe/Recipe Viewer', {'recipeKey': recipeKey, 'grade': grade, 'version': version,'downloadType':'GradeChange'})
    system.nav.centerWindow('Recipe/Recipe Viewer')
    
    system.nav.closeParentWindow(event)