'''
Created on Jan 5, 2015

@author: Pete
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.SQL")

# Convert the Python Data Set (PDS) to a list of dictionaries 
def toDict(pds):
    records = []
    if len(pds) > 0:    
        ds = system.dataset.toDataSet(pds)
        for row in range(ds.rowCount):
            record={}
            for col in range(ds.columnCount):
                colName=ds.getColumnName(col)
                val=ds.getValueAt(row,col)
                record[colName]=val
            records.append(record)

    # If the dataset was empty then return an empty list
    return records

# Lookup the post id given the name
def getPostId(post, database=""):
    SQL = "select PostId from TkPost where Post = '%s'" % (post)
    log.trace(SQL)
    postId = system.db.runScalarQuery(SQL, database)
    return postId