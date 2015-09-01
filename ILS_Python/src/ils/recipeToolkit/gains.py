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