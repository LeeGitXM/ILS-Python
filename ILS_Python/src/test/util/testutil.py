'''
Created on Oct 21, 2014

@author: rforbes
'''

class FakeDataSet(object):
    '''
    classdocs
    '''
    rows = None
    columnNames = None
    columnCount = 0
    rowCount = 0
   
    def __init__(self, _columnNames, _rows):
        self.rows = _rows
        self.columnNames = _columnNames
        self.columnCount = len(self.columnNames)
        self.rowCount = len(self.rows)
        
    def __getitem__(self, i):
        return self.rows[i]
    
    def getValueAt(self, row, col):
        return self.rows[row][col]
    
    def getColumnName(self, col):
        return self.columnNames[col]