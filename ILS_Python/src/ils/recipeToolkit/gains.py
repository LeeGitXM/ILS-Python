'''
Created on Aug 2, 2015

@author: Pete
'''

import system

def get(family, grade, key):
    print "Fetching the gain for family %s - grade %s - key %s " % (family, grade, key)
    
    SQL = "select gain "\
        " from RtRecipeFamily F, RtGain G, RtGainGrade GG "\
        " where F.RecipeFamilyName = '%s' "\
        " and F.RecipeFamilyId = G.RecipeFamilyId "\
        " and G.Parameter = '%s' "\
        " and G.ParameterId = GG.ParameterId "\
        " and GG.Grade = '%s'" % (family, key, grade)
    print SQL
    gain = system.db.runScalarQuery(SQL)
    print "Fetched gain = ", gain
    
    return gain 
    