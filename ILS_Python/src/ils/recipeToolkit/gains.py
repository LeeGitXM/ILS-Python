'''
Created on Aug 2, 2015

@author: Pete
'''

import system

# Fetch and return the gain for a family, grade, parameter.  
# Gains are stored in the RtGainGrade table
def get(family, grade, key, db):   
    SQL = "select gain "\
        " from RtRecipeFamily F, RtGain G, RtGainGrade GG "\
        " where F.RecipeFamilyName = '%s' "\
        " and F.RecipeFamilyId = G.RecipeFamilyId "\
        " and G.Parameter = '%s' "\
        " and G.ParameterId = GG.ParameterId "\
        " and GG.Grade = '%s'" % (family, key, grade)
    gain = system.db.runScalarQuery(SQL, db)
    return gain 

# Validate that the requested family & grade exist in the gain table.  
# Gains are stored in the RtGainGrade table
def validate(family, grade, db):   
    valid=False
    SQL = "select count(*) "\
        " from RtRecipeFamily F, RtGain G, RtGainGrade GG "\
        " where F.RecipeFamilyName = '%s' "\
        " and F.RecipeFamilyId = G.RecipeFamilyId "\
        " and G.ParameterId = GG.ParameterId "\
        " and GG.Grade = '%s'" % (family, grade)
    rows = system.db.runScalarQuery(SQL, db)
    if rows > 0:
        valid=True
    return valid 