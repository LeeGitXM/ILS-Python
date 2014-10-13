'''
Created on Sep 10, 2014

@author: Pete
'''
import system

# This is called once it is deemed that the download is complete.  
# It summarizes the results of the download.
def downloadComplete(rootContainer):
    import string

    console = rootContainer.getPropertyValue("console")
    provider = rootContainer.getPropertyValue("provider")
    grade = rootContainer.getPropertyValue("grade")
    recipeKey = rootContainer.getPropertyValue("recipeKey")
    recipeType = rootContainer.getPropertyValue("recipeType")
    table = rootContainer.getComponent("Power Table")

    ds = table.processedData
    pds = system.dataset.toPyDataSet(ds)

    downloads = 0
    successes = 0
    failures = 0
    for record in pds:
        download = record["Download"]
        downloadType = record["Download Type"]
        downloadStatus = string.upper(record["Download Status"])

        if download:        
            downloads = downloads + 1

            if downloadStatus == 'SUCCESS':
                successes = successes + 1
            else:
                failures = failures + 1

    print "There are %i downloads (%i success, %i failed)" % (downloads, successes, failures)

    from ils.recipeToolkit.common import setBackgroundColor
    if failures == 0:    
        setBackgroundColor(rootContainer, "screenBackgroundColorSuccess")
    else:
        setBackgroundColor(rootContainer, "screenBackgroundColorFail")

    # Write a logbook message
    txt = "Recipe MANUAL download of %s for %s using %s has completed.  %i writes confirmed.  %i writes NOT confirmed." % \
        (grade, recipeKey, recipeType, successes, failures)
    
    from ils.queue.log import insert
    insert("Logfile", txt)