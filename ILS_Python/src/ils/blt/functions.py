#  Copyright 2015 ILS Automation
#
# This library is referenced by translated procedures that are part
# of the diagnosic toolkit. It provides basic math functions 
# 
import org.apache.commons.math3.stat.descriptive.moment.Mean as Mean
import org.apache.commons.math3.stat.descriptive.moment.StandardDeviation as StandardDeviation
from jarray import array
import java.util.Date as Date
import java.lang.System as System
import system.tag

# Note: the following are Python builtin and require no translation:
#       abs, round
#
# a - first arg
# b - second arg
def average(a,b):
    return (a+b)/2

# Note: the following are Python builtin and require no translation:
#       abs, round
# path - the tag path
# d1 - from time in seconds before present
# d2 - to time in seconds before present
def averageOverTime(path,d1,d2):
    date1 = Date(System.currentTimeMillis()-1000*d1)
    date2 = None
    if( d2!=None):
        date2 = Date(System.currentTimeMillis()-1000*d2) 
    
    tags = []
    tags.add(path)
    # Column is the tag path 
    ds = system.tag.queryTagHistory(tags,date1,date2,0,aggregationMode="LastValue",noInterpolation=True)
    vals = []
    for row in range(ds.rowCount):
        vals.add(ds.getValueAt(row,0))
    dbls = array(vals,'d')
    mean = Mean()
    return mean.evaluate(dbls,0,len(vals))

# path - the tag path
# d1 - from time in seconds before present
# d2 - to time in seconds before present
def standardDeviationOverTime(path,d1,d2):
    date1 = Date(System.currentTimeMillis()-1000*d1)
    date2 = None
    if( d2!=None):
        date2 = Date(System.currentTimeMillis()-1000*d2)  
       
    tags = []
    tags.add(path)
    ds = system.tag.queryTagHistory(tags,date1,date2,0,aggregationMode="LastValue",noInterpolation=True)
    vals = []
    for row in range(ds.rowCount):
        vals.add(ds.getValueAt(row,0))
    dbls = array(vals,'d')
    m = Mean()
    mean =  m.evaluate(dbls,0,len(vals))
    sd = StandardDeviation()
    return sd.evaluate(dbls,mean,0,len(vals))