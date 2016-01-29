'''
Created on Jan 15, 2016
Methods supported by the test framework
'''
def createExpression(provider,path,dataType,expr):
    pass
def createTag(provider,path,dataType):
    pass
# Define a test where data resides in a database table
def defineTablebasedTest(provider,database,table,timecol,mintime,maxtime,timefact):
    pass
def deleteTag(provider,path):
    pass
def executeSQL(SQL,database):
    pass
# Dataset has columns: "ColumnName","TagPath","DataType"
def populateColumnTagMap(database,table,dataset):
    pass