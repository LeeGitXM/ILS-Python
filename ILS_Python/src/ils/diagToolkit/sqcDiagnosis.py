'''
Created on June 16, 2015
'''
import system
import com.inductiveautomation.ignition.common.util.LogUtil as LogUtil
import system.ils.blt.diagram as script
from ils.diagToolkit.common import getDiagram

log = LogUtil.getLogger("com.ils.diagToolkit.recommendation")

# Return two lists:
# 1) the names of all of the input blocks in the diagram
# 2) the names of all the SQC diagnosis blocks in the diagram
# This mimics the functionality of the G2 procedure: em-get-input-blocks
def getInputBlocks(diagramPath):
    diagid = getDiagram(diagramPath).getSelf().toString()
    # blocks is a list of SerializableBlockStateDescriptor
    inputs = script.listDiagramBlocksOfClass(diagid,"com.ils.block.Input")
    observations = script.listDiagramBlocksOfClass(diagid,"xom.block.sqcdiagnosis.SQCDiagnosis")
    return inputs,observations 


def getSqcDiagnosisLabelByName(sqcDiagnosisName, db=""):
    SQL = "select sqcDiagnosisLabel from DtSqcDiagnosis where sqcDiagnosisName = '%s'" % (sqcDiagnosisName)
    label = system.db.runScalarQuery(SQL, db)
    return label