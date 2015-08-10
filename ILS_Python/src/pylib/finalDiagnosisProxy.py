# Copyright 2015. ILS Automation. All rights reserved.

import system
import system.ils.blt.diagram as script

# Place a result of "true" in the common dictionary
# if the family is found in the default database.
# Argument is the family name
def family(common,app,family):
	handler = script.getHandler()
	db = handler.getDefaultDatabase(name)
	SQL = "SELECT FamilyId FROM DtFamily "\
          " WHERE Application = '%s' "\
		  "  AND  Family = '%s';" % app,family
	val = system.db.runScalarQuery(SQL,db)
	if val != None:
		common['result'] = True
	else:
		common['result'] = False

# Returns the value of a recommendation for a specific quant output for a final diagnosis
def getRecommendation(common,dpath,finalDiagnosisName, quantOutputName):
	diagid = getDiagram(dpath).getSelf().toString()
	state = diagram.getDiagramState(diagid)
	db = handler.getDatabaseForUUID(diagid)
	SQL = "SELECT FamilyId FROM DtFamily "\
          " WHERE Application = '%s' "\
		  "  AND  Family = '%s';" % app,family
	val = system.db.runScalarQuery(SQL,db)
	common['result'] = val

# Return the state of the diagram
def getRecommendationCount(common,dpath,finalDiagnosisName):
	diagid = getDiagram(dpath).getSelf().toString()
	state = diagram.getDiagramState(diagid)
	common['result'] = state