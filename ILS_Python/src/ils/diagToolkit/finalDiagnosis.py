'''
Created on Sep 12, 2014

@author: Pete
'''

import system

def test(txt):
    print "You say hello..."
    print "...and I say goodbye!"

def dispatcher(calculationMethodName, FD_UUID, arg2):
    import emc, ils, project
    print "Dispatching..."
    func = eval(calculationMethodName)
    status = func(FD_UUID, arg2)
    print "Function returned: ", status
    
def dispatcherWithArguments(func, argumentDictionary):
    print func, argumentDictionary
    eval(func, {"__builtins__":None}, argumentDictionary)

def f1():
    print "** In f1() **"
    return 76.4, 99.12

def f2(arg1, arg2):
    print "In f2() with ", arg1, arg2
    return 896.45, 45873.2

def calc1(FD_UUID, arg2):
    print "** In calc1 **"
    return "success"

def calc2(FD_UUID, arg2):
    print "** In calc2 **"
    return "success"

# This gets called whenever the state of the final diagnosis changes.  The state is expected
# to be True, False or unknown.
# to be TRUE, FALSE, UNKNOWN, or UNSET.
# This is called by the BLT engine, the Java module, which is running in the gateway.  There is
# uncertainty if the runtime environment is part of a project and if it has a default database
def evaluate(block, state):
    print "In finalDiagnosis.evaluate, state = ", state

    # Test to see if we know about a project
    project = system.util.getProjectName()
    print "Hey - I belong to the ", project, " project!"
     
    if state != "unknown":
        # Clear any wait for data marker
        # TODO 
        pass
    

# Insert a record into the diagnosis queue
def postDiagnosisEntry(grade, applicationName, familyName, familyPriority, finalDiagnosisName, finalDiagnosisPriority,  
                       calculationMethod, postTextRecommendation, textRecommendationCallback, refreshRate, textRecommendation):
    print "Post a diagnosis entry"

    # Lookup the application Id
    from ils.diagToolkit.common import fetchApplicationId
    applicationId = fetchApplicationId(applicationName)

    # Insert an entry into the diagnosis queue
    SQL = "insert into DiagnosisQueue (Status, Timestamp, Grade, ApplicationId, FamilyName, FamilyPriority, "\
        "FinalDiagnosisName, FinalDiagnosisPriority, CalculationMethod, PostTextRecommendation, TextRecommendationCallback, "\
        "RefreshRate, TextRecommendation, RecommendationStatus) "\
        "values ('Active', getdate(), %i, %i, '%s', %f, '%s', %f, '%s', %i, '%s', %i, '%s', 'NONE-MADE')" \
        % (grade, applicationId, familyName, familyPriority, finalDiagnosisName, finalDiagnosisPriority, calculationMethod, \
           postTextRecommendation, textRecommendationCallback, refreshRate, textRecommendation)

    print SQL
    system.db.runUpdateQuery(SQL)

# This replaces _em-manage-diagnosis().  Its job is to prioritize the active diagnosis for an application diagnosis queue.
def manage(applicationName):

    # Lookup the application Id
    from ils.diagToolkit.common import fetchApplicationId
    applicationId = fetchApplicationId(applicationName)
    
    SQL = "select FamilyName, FamilyPriority, FinalDiagnosisName, FinalDiagnosisPriority" \
        " from DiagnosisQueue " \
        " where ApplicationId = %i" \
        " and Status = 'Active' " \
        " and not (CalculationMethod != 'Constant' and (RecommendationStatus in ('WAIT','NO-DOWNLOAD','DOWNLOAD'))) " \
        " order by FamilyPriority, FinalDiagnosisPriority" % (applicationId)

    print SQL
    pds = system.db.runQuery(SQL)
    
    # If there are no active diagnosis then there is nothing to manage
    if len(pds) == 0:
        print "Exiting the diagnosis manager because there are no active diagnosis!"
        # TODO we may need to clear something!
        return
    
    list1 = []
    highestPriority = pds[0]['FamilyPriority']
    for record in pds:
        if record['FamilyPriority'] == highestPriority:
            print record['FamilyName'], record['FamilyPriority'], record['FinalDiagnosisName'], record['FinalDiagnosisPriority']
            list1.append(record)

    # Sort out tdiagnosis where there are multiple diagnosis for the same family
    familyName = ''
    list2 = []
    for record in list1:
        if record['FamilyName'] != familyName:
            familyName = record['FamilyName']
            finalDiagnosisPriority = record['FinalDiagnosisPriority']
            list2.append(record)
        elif finalDiagnosisPriority == record['FinalDiagnosisPriority']:
            list2.append(record)
    
    print "The final diagnosis that must be acted upon are:"
    for record in list2:
        print "  ", record['FamilyName'], record['FamilyPriority'], record['FinalDiagnosisName'], record['FinalDiagnosisPriority']

            
# Initialize the diagnosis 
def initializeView(rootContainer):
    console = rootContainer.getPropertyValue("console")
    title = console + ' Console Diagnosis Message Queue'
    rootContainer.setPropertyValue('title', title) 
    print "Done initializing!    Yookoo"
