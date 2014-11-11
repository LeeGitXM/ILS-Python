'''
Created on Sep 10, 2014

@author: Pete
'''
import system
import ils.recipeToolkit.update as update
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit.download")

# This is called once it is deemed that the download is complete.  
# It summarizes the results of the download.
def downloadComplete(rootContainer):
    import string

    log.info("Download complete...")
    logId = rootContainer.getPropertyValue("logId")
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

    log.info("...there were %i downloads (%i success, %i failed)" % (downloads, successes, failures))

    from ils.recipeToolkit.common import setBackgroundColor
    if failures == 0:
        status = "Success"
        update.recipeMapStatus(recipeKey, 'Download Passed')
        setBackgroundColor(rootContainer, "screenBackgroundColorSuccess")
    else:
        status = "Failed"
        update.recipeMapStatus(recipeKey, 'Download Failed')
        setBackgroundColor(rootContainer, "screenBackgroundColorFail")

    # Write a logbook message TODO - Do I need to do this
    txt = "Recipe MANUAL download of %s for %s using %s has completed.  %i writes confirmed.  %i writes NOT confirmed." % \
        (grade, recipeKey, recipeType, successes, failures)
    
    # Update the Master down table
    from ils.recipeToolkit.log import updateLogMaster
    updateLogMaster(logId, status, downloads, successes, failures)