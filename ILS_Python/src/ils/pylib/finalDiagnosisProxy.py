# Copyright 2015. ILS Automation. All rights reserved.

# This module provides functions for accessing the dynamic properties of 
# Final Diagnosis, Quant Outputs, and Recommendations.

import system, string

def getFinalDiagnosisProperty(common, application, finalDiagnosis, property, db):
	print "In getFinalDiagnosisProperty..."

	SQL = "select TextRecommendation, Active, Explanation "\
		" from DtApplication A, DtFamily F, DtFinalDiagnosis FD "\
		" where A.ApplicationId = F.ApplicationId "\
		" and F.FamilyId = FD.FamilyId "\
		" and A.applicationName = '%s' "\
		" and FD.FinalDiagnosisName = '%s'" % (application, finalDiagnosis)
	
	pds=system.db.runQuery(SQL, db)
	if len(pds) == 0:
		val = "No records found"
	elif len(pds) > 1:
		val = "Multiple records found"
	else:
		record = pds[0]

		if string.upper(property) == "TESTRECOMMENDATION":
			val = record["TextRecommendation"]
		elif string.upper(property) == "ACTIVE":
			val = record["Active"]
		elif string.upper(property) == "EXPLANATION":
			val = record["Explanation"]
		else:
			val = "Unknown parameter"
		
	print "Fetched: ", val
	common['result'] = val


def getRecommendationProperty(common, application, finalDiagnosis, quantOutput, property, db):
	print "In getRecommendationProperty..."
	
	SQL = "select Recommendation, AutoRecommendation, ManualRecommendation, AutoOrManual "\
		" from DtApplication A, DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO, DtRecommendation R "\
		" where QO.ApplicationId = A.ApplicationId "\
		" and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
		" and QO.QuantOutputId = RD.QuantOutputId "\
		" and RD.RecommendationDefinitionId = R.RecommendationDefinitionId" \
		" and A.applicationName = '%s' "\
		" and FD.FinalDiagnosisName = '%s'" \
		" and QO.QuantOutputName = '%s'" % (application, finalDiagnosis, quantOutput)
	
	pds=system.db.runQuery(SQL, db)
	if len(pds) == 0:
		val = "No records found"
	elif len(pds) > 1:
		val = "Multiple records found"
	else:
		record = pds[0]

		if string.upper(property) == "RECOMMENDATION":
			val = record["Recommendation"]
		elif string.upper(property) == "AUTORECOMMENDATION":
			val = record["AutoRecommendation"]
		elif string.upper(property) == "MANUALRECOMMENDATION":
			val = record["ManualRecommendation"]
		elif string.upper(property) == "AUTOORMANUAL":
			val = record["AutoOrManual"]
		else:
			val = "Unknown parameter"
		
	print "Fetched: ", val
	common['result'] = val


def getQuantOutputProperty(common, application, quantOutput, property, db):
	print "In getQuantOutputProperty, fetching property: %s..." % (property)
	
	SQL = "select FeedbackOutput, FeedbackOutputManual, FeedbackOutputConditioned, OutputLimitedStatus, OutputLimited, "\
		" OutputPercent, ManualOverride, Active, CurrentSetpoint, FinalSetpoint, DisplayedRecommendation"\
		" from DtQuantOutput QO, DtApplication A"\
		"  where QO.ApplicationId = A.ApplicationId "\
		" and A.applicationName = '%s' "\
		" and QO.QuantOutputName = '%s' " % (application, quantOutput)
	print SQL
	pds=system.db.runQuery(SQL, db)
	if len(pds) == 0:
		val = "No records found"
	elif len(pds) > 1:
		val = "Multiple records found"
	else:
		record = pds[0]
	
		if string.upper(property) == "FEEDBACKOUTPUT":
			val = record["FeedbackOutput"]
		elif string.upper(property) == "FEEDBACKOUTPUTMANUAL":
			val = record["FeedbackOutputManual"]
		elif string.upper(property) == "FEEDBACKOUTPUTCONDITIONED":
			val = record["FeedbackOutputConditioned"]
		elif string.upper(property) == "OUTPUTLIMITEDSTATUS":
			val = record["OutputLimitedStatus"]
		elif string.upper(property) == "OUTPUTLIMITED":
			val = record["OutputLimited"]
		elif string.upper(property) == "OUTPUTPERCENT":
			val = record["OutputPercent"]
		elif string.upper(property) == "MANUALOVERRIDE":
			val = record["ManualOverride"]
		elif string.upper(property) == "ACTIVE":
			val = record["Active"]
		elif string.upper(property) == "CURRENTSETPOINT":
			val = record["CurrentSetpoint"]
		elif string.upper(property) == "FINALSETPOINT":
			val = record["FinalSetpoint"]
		elif string.upper(property) == "DISPLAYEDRECOMMENDATION":
			val = record["DisplayedRecommendation"]
		else:
			val = "Unknown parameter"
		
	print "Fetched: ", val
	common['result'] = val
