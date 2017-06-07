'''
Created on Sep 10, 2014

@author: Pete
'''

import system

import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
log = LogUtil.getLogger("com.ils.recipeToolkit")

def gateway(provider):
    from ils.recipeToolkit.version import version
    version, revisionDate = version()
    log.info("---------------------------------------------------------")
    log.info("Starting Recipe Toolkit version %s - %s" % (version, revisionDate))
    log.info("---------------------------------------------------------")

    createTags("[" + provider + "]")

def client():
    print "In recipeToolkit.startup.client()"
    log = LogUtil.getLogger("com.ils.recipeToolkit.download")
    log.info("Initializing the recipe toolkit")

def createTags(tagProvider):
    print "Creating global constant memory tags...."
    headers = ['Path', 'Name', 'Data Type', 'Value']
    data = []
    path = tagProvider + "Configuration/RecipeToolkit/"

    data.append([path, "localWriteAlias", "String", "LOCAL"])
    data.append([path, "itemIdPrefix", "String", ""])
    data.append([path, "recipeMinimumDifference", "Float8", "0.00001"])
    data.append([path, "recipeMinimumRelativeDifference", "Float8", "0.00001"])
    data.append([path, "recipeWriteEnabled", "Boolean", "True"])
    data.append([path, "downloadTimeout", "Int4", "120"])

    data.append([path, "backgroundColorReadOnly", "String", "lightblue"])  #'#ADD8E6'  light blue
    data.append([path, "backgroundColorReadWrite", "String", "lightcyan"]) #'#E0FFFF' light cyan
    data.append([path, "backgroundColorNoChange", "String", "lightblue"])  #'#ADD8E6'  light blue
    data.append([path, "backgroundColorMismatch", "String", "plum"])
    data.append([path, "backgroundColorError", "String", "pink"])
    data.append([path, "backgroundColorWritePending", "String", "yellow"])
    data.append([path, "backgroundColorWriteError", "String", "red"])
    data.append([path, "backgroundColorWriteSuccess", "String", "lime"])
    
    data.append([path, "screenBackgroundColorInitializing", "String", "lightGrey"])
    data.append([path, "screenBackgroundColorDownloading", "String", "white"])
    data.append([path, "screenBackgroundColorSuccess", "String", "limegreen"])
    data.append([path, "screenBackgroundColorUnknown", "String", "magenta"])
    data.append([path, "screenBackgroundColorFail", "String", "red"])
       
    ds = system.dataset.toDataSet(headers, data)
    from ils.common.tagFactory import createConfigurationTags
    createConfigurationTags(ds, log)
    
    # Now make two additional tags that are used to test how long the system has been RUNNING
    # First, make the tag that records when the gateway was restarted
    name = "startTime"
    fullName = path + name
    if not(system.tag.exists(fullName)):
        print "Creating the start time tag" 
        system.tag.addTag(parentPath = path, name = name, tagType = "MEMORY", dataType = "DateTime")
    
    # Unlike the configuration tags where we do not overwrite the value once it has been set, this needs to 
    # be reset EVERY time we restart
    import ils.common.util as util
    now = util.getDate()
    system.tag.write(fullName, now)
    
    # Now make an expression tag that calculates how many seconds the gateway has been running
    name = "runningSeconds"
    fullName = path + name
    if not(system.tag.exists(fullName)):
        print "Creating the running time tag" 
        expr = "dateDiff({[.]startTime}, now(0), 'sec')"
        system.tag.addTag(parentPath=path, name=name, tagType="EXPRESSION", dataType="Int8", attributes={"Expression":expr})


def restoreLocalRecipe(recipeFamily, grade, tagProvider = "", database=""):
    log.info("Restoring local recipe values for family: %s, grade: %s" % (str(recipeFamily), str(grade)) )

    if grade == None:
        log.warn("Unable to restore local recipe values for an unknown grade.")
        return

    SQL = "Select VD.StoreTag, GD.RecommendedValue "\
        " from RtGradeMaster GM, RtGradeDetail GD, RtValueDefinition VD, TkWriteLocation WL, RtRecipeFamily RF "\
        " where GM.Active = 1 "\
        " and GM.RecipeFamilyId = GD.RecipeFamilyId "\
        " and GM.Grade = GD.Grade "\
        " and GM.Version = GD.Version "\
        " and RF.RecipeFamilyId = GM.RecipeFamilyId "\
        " and VD.WriteLocationId = WL.WriteLocationId "\
        " and WL.Alias = 'Local' "\
        " and GD.RecipeFamilyId = VD.RecipeFamilyId"\
        " and GM.Grade = %s "\
        " and RF.RecipeFamilyName = '%s' "\
        " and GD.ValueId = VD.ValueId  "\
        " order by StoreTag" % (str(grade), recipeFamily)

    pds = system.db.runQuery(SQL, database)
    log.info("Fetched %i rows" % (len(pds)))
    
    tags=[]
    vals=[]
    from ils.recipeToolkit.common import formatLocalTagName
    for record in pds:
        log.info("  setting %s to %s..." % (record["StoreTag"], str(record["RecommendedValue"])))
        tagName=formatLocalTagName(tagProvider, record["StoreTag"])
        tags.append(tagName)
        vals.append(record["RecommendedValue"])
    
    if len(tags) > 0:
        system.tag.writeAll(tags, vals)
        
    log.info("Done restoring local recipe tags!")
