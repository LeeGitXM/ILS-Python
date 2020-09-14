'''
Created on Aug 21, 2020

@author: phass
'''

PRODUCTION = "production"
ISOLATION = "isolation"
RECIPE_DATA_ID = "RecipeDataId"
VALUE_ID = "ValueId"

''' Column data types '''
STRING = "string"
LOOKUP_FOLDER = "lookupFolder"
LOOKUP = "lookup"
LOOKUP_WITH_TWO_KEYS = "lookupWithTwoKeys"
BOOLEAN = "boolean"
FLOAT = "float"
INTEGER = "integer"


config = [
    {
        "table": "DtApplication", 
        "selectQueryName": "DB Transfer/DtApplication", 
        "primaryKey": "ApplicationId",
        "columnsToCompareAndUpdate": [
                {"columnName": "ApplicationName", "dataType": STRING},
                {"columnName": "UnitName", "dataType": LOOKUP},
                {"columnName": "Description", "dataType": STRING},
                {"columnName": "IncludeInMainMenu", "dataType": BOOLEAN},
                {"columnName": "GroupRampMethod", "dataType": LOOKUP},
                {"columnName": "QueueKey", "dataType": LOOKUP},
                {"columnName": "NotificationStrategy", "dataType": STRING},
                {"columnName": "Managed", "dataType": BOOLEAN}
                ],
        "uniqueColumns": ["ApplicationName"]
        },
          
    {
        "table": "DtFamily", 
        "selectQueryName": "DB Transfer/DtFamily",
        "primaryKey": "FamilyId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ApplicationName", "dataType": LOOKUP},
            {"columnName": "FamilyName", "dataType": STRING},
            {"columnName": "FamilyPriority", "dataType": FLOAT},
            {"columnName": "Description", "dataType": STRING}
            ],
        "uniqueColumns": ["ApplicationName", "FamilyName"]
        },
          
    {
        "table": "DtFinalDiagnosis", 
        "selectQueryName": "DB Transfer/DtFinalDiagnosis",
        "primaryKey": "FinalDiagnosisId",
        "columnsToCompareAndUpdate": [
            {"columnName": "FamilyName", "dataType": LOOKUP},
            {"columnName": "FinalDiagnosisName", "dataType": STRING},
            {"columnName": "FinalDiagnosisLabel", "dataType": STRING},
            {"columnName": "FinalDiagnosisPriority", "dataType": FLOAT},
            {"columnName": "CalculationMethod", "dataType": STRING},
            {"columnName": "Constant", "dataType": BOOLEAN},
            {"columnName": "PostTextRecommendation", "dataType": BOOLEAN},
            {"columnName": "PostProcessingCallback", "dataType": STRING},
            {"columnName": "RefreshRate", "dataType": INTEGER},
            {"columnName": "Comment", "dataType": STRING},
            {"columnName": "TextRecommendation", "dataType": STRING},
            {"columnName": "Explanation", "dataType": STRING},
            {"columnName": "TrapInsignificantRecommendations", "dataType": BOOLEAN},
            {"columnName": "ManualMoveAllowed", "dataType": BOOLEAN},
            {"columnName": "ShowExplanationWithRecommendation", "dataType": BOOLEAN}
            ],
        "uniqueColumns": ["ApplicationName", "FamilyName", "FinalDiagnosisName"]
        },
    
    {
        "table": "DtQuantOutput", 
        "selectQueryName": "DB Transfer/DtQuantOutput",
        "primaryKey": "QuantOutputId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ApplicationName", "dataType": LOOKUP},
            {"columnName": "QuantOutputName", "dataType": STRING},
            {"columnName": "TagPath", "dataType": STRING},
            {"columnName": "MostNegativeIncrement", "dataType": FLOAT},
            {"columnName": "MostPositiveIncrement", "dataType": FLOAT},
            {"columnName": "MinimumIncrement", "dataType": FLOAT},
            {"columnName": "IgnoreMinimumIncrement", "dataType": BOOLEAN},
            {"columnName": "SetpointHighLimit", "dataType": FLOAT},
            {"columnName": "SetpointLowLimit", "dataType": FLOAT},
            {"columnName": "IncrementalOutput", "dataType": BOOLEAN},
            {"columnName": "FeedbackMethod", "dataType": LOOKUP}
            ],
        "uniqueColumns": ["ApplicationName", "QuantOutputName"]
        },
          
    {
        "table": "DtQuantOutputRamp", 
        "selectQueryName": "DB Transfer/DtQuantOutputRamp",
        "primaryKey": "QuantOutputId",
        "columnsToCompareAndUpdate": [
            {"columnName": "QuantOutputName", "dataType": LOOKUP},
            {"columnName": "Ramp", "dataType": FLOAT},
            {"columnName": "RampType", "dataType": LOOKUP}
            ],
        "uniqueColumns": ["ApplicationName", "QuantOutputName"]
        },
          
    {
        "table": "DtRecommendationDefinition", 
        "selectQueryName": "DB Transfer/DtRecommendationDefinition",
        "primaryKey": "RecommendationDefinitionId",
        "columnsToCompareAndUpdate": [
            {"columnName": "FinalDiagnosisName", "dataType": LOOKUP},
            {"columnName": "QuantOutputName", "dataType": LOOKUP}
            ],
        "uniqueColumns": ["FinalDiagnosisName", "QuantOutputName"]
        },
          
    # SFC basic lookup tables
    
    {
        "table": "SfcNames", 
        "selectQuery": "select * from SfcNames",
        "primaryKey": "SfcName",
        "columnsToCompareAndUpdate": [
            {"columnName": "SfcName", "dataType": STRING}
            ],
        "uniqueColumns": ["SfcName"]
        },
    
    {
        "table": "SfcStepType", 
        "selectQuery": "select * from SfcStepType",
        "primaryKey": "StepTypeId",
        "columnsToCompareAndUpdate": [
            {"columnName": "StepType", "dataType": STRING},
            {"columnName": "FactoryId", "dataType": STRING}
            ],
        "uniqueColumns": ["StepType"]
        },
        
    {
        "table": "SfcRecipeDataType", 
        "selectQuery": "select * from SfcRecipeDataType",
        "primaryKey": "RecipeDataTypeId",
        "columnsToCompareAndUpdate": [
            {"columnName": "RecipeDataType", "dataType": STRING},
            {"columnName": "JavaClassName", "dataType": STRING}
            ],
        "uniqueColumns": ["RecipeDataType"]
        },
            
    {
        "table": "SfcValueType", 
        "selectQuery": "select * from SfcValueType",
        "primaryKey": "ValueTypeId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ValueType", "dataType": STRING}
            ],
        "uniqueColumns": ["ValueType"]
        },
    
    {
        "table": "SfcRecipeDataKeyMaster", 
        "selectQuery": "select * from SfcRecipeDataKeyMaster",
        "primaryKey": "KeyId",
        "columnsToCompareAndUpdate": [
            {"columnName": "KeyName", "dataType": STRING}
            ],
        "uniqueColumns": ["KeyName"]
        },
          
        {
        "table": "SfcRecipeDataKeyDetail", 
        "selectQueryName":  "DB Transfer/SfcRecipeDataKeyDetail",
        "primaryKey": "KeyId, KeyValue, KeyIndex",
        "columnsToCompareAndUpdate": [
            {"columnName": "KeyName", "dataType": LOOKUP},
            {"columnName": "KeyValue", "dataType": STRING},
            {"columnName": "KeyIndex", "dataType": INTEGER}
            ],
        "uniqueColumns": ["KeyId", "KeyValue", "KeyIndex"]
        },
    
    # SFC Chart and step tables
          
    {
        "table": "SfcChart", 
        "selectQueryName": "DB Transfer/SfcChart",
        "primaryKey": "ChartId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": STRING},
            {"columnName": "IsProduction", "dataType": BOOLEAN}
            ],
        "uniqueColumns": ["ChartPath"]
        },

    {
        "table": "SfcStep", 
        "selectQueryName": "DB Transfer/SfcStep",
        "primaryKey": "StepId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP},
            {"columnName": "StepName", "dataType": STRING},
            {"columnName": "StepUUID", "dataType": STRING},
            {"columnName": "StepType", "dataType": LOOKUP}
            ],
        "uniqueColumns": ["ChartPath", "StepName"]
        },
          
        {
        "table": "SfcHierarchy", 
        "selectQueryName": "DB Transfer/SfcHierarchy",
        "primaryKey": "HierarchyId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP},
            {"columnName": "StepName", "dataType": LOOKUP_WITH_TWO_KEYS},
            {"columnName": "ChildChartPath", "dataType": LOOKUP}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "ChildChartPath"]
        },
          
        {
        "table": "SfcHierarchyHandler", 
        "selectQueryName": "DB Transfer/SfcHierarchyHandler",
        "primaryKey": "HierarchyId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP},
            {"columnName": "Handler", "dataType": STRING},
            {"columnName": "HandlerChartPath", "dataType": LOOKUP}
            ],
        "uniqueColumns": ["ChartPath", "Handler", "HandlerChartPath"]
        },
          
        # SFC Recipe Data Tables 
        
        {
        "table": "SfcRecipeDataFolder", 
        "selectQueryName": "DB Transfer/SfcRecipeDataFolder",
        "primaryKey": "RecipeDataFolderId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": STRING, "insert": False},
            {"columnName": "StepName", "dataType": STRING, "insert": False},
            {"columnName": "StepId", "dataType": LOOKUP_WITH_TWO_KEYS, "compare": False},
            {"columnName": "RecipeDataKey", "dataType": STRING},
            {"columnName": "Description", "dataType": STRING},
            {"columnName": "Label", "dataType": STRING},
            {"columnName": "ParentFolderName", "dataType": STRING, "insert": False, "compare": True},
            {"columnName": "ParentRecipeDataFolderId", "dataType": LOOKUP, "compare": False}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey", "FolderPath"]
        },
    
        {
        "table": "SfcRecipeDataSimpleValue", 
        "className": "simpleValue.SimpleValue",
        "selectQueryName": "DB Transfer/SfcRecipeDataSimpleValue",
        "primaryKey": "RecipeDataId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP},
            {"columnName": "StepName", "dataType": LOOKUP_WITH_TWO_KEYS},
            {"columnName": "RecipeDataKey", "dataType": LOOKUP},
            {"columnName": "RecipeDataType", "dataType": LOOKUP},
            {"columnName": "Description", "dataType": STRING},
            {"columnName": "Label", "dataType": STRING},
            {"columnName": "Units", "dataType": STRING},
            {"columnName": "FolderPath", "dataType": LOOKUP_FOLDER, "idColumnName": "RecipeDataFolderId"},
            {"columnName": "ValueType", "dataType": LOOKUP},
            {"columnName": "BooleanValue", "dataType": BOOLEAN},
            {"columnName": "FloatValue", "dataType": FLOAT},
            {"columnName": "IntegerValue", "dataType": INTEGER},
            {"columnName": "StringValue", "dataType": STRING}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey",  "FolderPath"]
        },
          
        {
        "table": "SfcRecipeDataTimer", 
        "selectQueryName": "DB Transfer/SfcRecipeDataTimer",
        "primaryKey": "RecipeDataId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP, "insert": False},
            {"columnName": "StepName", "dataType": LOOKUP_WITH_TWO_KEYS, "insert": False},
            {"columnName": "RecipeDataKey", "dataType": LOOKUP},
            {"columnName": "RecipeDataType", "dataType": LOOKUP},
            {"columnName": "Description", "dataType": STRING},
            {"columnName": "Label", "dataType": STRING},
            {"columnName": "Units", "dataType": STRING},
            {"columnName": "FolderPath", "dataType": LOOKUP_FOLDER, "idColumnName": "RecipeDataFolderId"}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey",  "FolderPath"]
        },
          
        {
        "table": "SfcRecipeDataRecipe", 
        "selectQueryName": "DB Transfer/SfcRecipeDataRecipe",
        "primaryKey": "RecipeDataId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP, "insert": False},
            {"columnName": "StepName", "dataType": LOOKUP_WITH_TWO_KEYS, "insert": False},
            {"columnName": "RecipeDataKey", "dataType": LOOKUP},
            {"columnName": "RecipeDataType", "dataType": LOOKUP},
            {"columnName": "Description", "dataType": STRING},
            {"columnName": "Label", "dataType": STRING},
            {"columnName": "Units", "dataType": STRING},
            {"columnName": "FolderPath", "dataType": LOOKUP_FOLDER, "idColumnName": "RecipeDataFolderId"},
            {"columnName": "PresentationOrder", "dataType": INTEGER},
            {"columnName": "StoreTag", "dataType": STRING},
            {"columnName": "CompareTag", "dataType": STRING},
            {"columnName": "ModeAttribute", "dataType": STRING},
            {"columnName": "ModeValue", "dataType": STRING},
            {"columnName": "ChangeLevel", "dataType": STRING},
            {"columnName": "RecommendedValue", "dataType": STRING},
            {"columnName": "LowLimit", "dataType": STRING},
            {"columnName": "HighLimit", "dataType": STRING}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey",  "FolderPath"]
        },
          
        {
        "table": "SfcRecipeDataSQC", 
        "selectQueryName": "DB Transfer/SfcRecipeDataSQC",
        "primaryKey": "RecipeDataId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP, "insert": False},
            {"columnName": "StepName", "dataType": LOOKUP_WITH_TWO_KEYS, "insert": False},
            {"columnName": "RecipeDataKey", "dataType": LOOKUP},
            {"columnName": "RecipeDataType", "dataType": LOOKUP},
            {"columnName": "Description", "dataType": STRING},
            {"columnName": "Label", "dataType": STRING},
            {"columnName": "Units", "dataType": STRING},
            {"columnName": "FolderPath", "dataType": LOOKUP_FOLDER, "idColumnName": "RecipeDataFolderId"},
            {"columnName": "LowLimit", "dataType": FLOAT},
            {"columnName": "TargetValue", "dataType": FLOAT},
            {"columnName": "HighLimit", "dataType": FLOAT}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey",  "FolderPath"]
        },
          
        {
        "table": "SfcRecipeDataInput", 
        "selectQueryName": "DB Transfer/SfcRecipeDataInput",
        "primaryKey": "RecipeDataId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP},
            {"columnName": "StepName", "dataType": LOOKUP_WITH_TWO_KEYS},
            {"columnName": "RecipeDataKey", "dataType": LOOKUP},
            {"columnName": "RecipeDataType", "dataType": LOOKUP},
            {"columnName": "Description", "dataType": STRING},
            {"columnName": "Label", "dataType": STRING},
            {"columnName": "Units", "dataType": STRING},
            {"columnName": "Tag", "dataType": STRING},
            {"columnName": "FolderPath", "dataType": LOOKUP_FOLDER, "idColumnName": "RecipeDataFolderId"},
            {"columnName": "ValueType", "dataType": LOOKUP},
            {"columnName": "PVBooleanValue", "dataType": BOOLEAN},
            {"columnName": "PVFloatValue", "dataType": FLOAT},
            {"columnName": "PVIntegerValue", "dataType": INTEGER},
            {"columnName": "PVStringValue", "dataType": STRING},
            {"columnName": "TargetBooleanValue", "dataType": BOOLEAN},
            {"columnName": "TargetFloatValue", "dataType": FLOAT},
            {"columnName": "TargetIntegerValue", "dataType": INTEGER},
            {"columnName": "TargetStringValue", "dataType": STRING}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey",  "FolderPath"]
        },
          
        {
        "table": "SfcRecipeDataOutput", 
        "selectQueryName": "DB Transfer/SfcRecipeDataOutput",
        "primaryKey": "RecipeDataId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP},
            {"columnName": "StepName", "dataType": LOOKUP_WITH_TWO_KEYS},
            {"columnName": "RecipeDataKey", "dataType": LOOKUP},
            {"columnName": "RecipeDataType", "dataType": LOOKUP},
            {"columnName": "Description", "dataType": STRING},
            {"columnName": "Label", "dataType": STRING},
            {"columnName": "Units", "dataType": STRING},
            {"columnName": "Tag", "dataType": STRING},
            
            {"columnName": "Download", "dataType": BOOLEAN},
            {"columnName": "Timing", "dataType": FLOAT},
            {"columnName": "MaxTiming", "dataType": FLOAT},
            {"columnName": "WriteConfirm", "dataType": BOOLEAN},
            
            {"columnName": "FolderPath", "dataType": LOOKUP_FOLDER, "idColumnName": "RecipeDataFolderId"},
            {"columnName": "ValueType", "dataType": LOOKUP},
            {"columnName": "OutputType", "dataType": LOOKUP},
            
            {"columnName": "OutputBooleanValue", "dataType": BOOLEAN},
            {"columnName": "OutputFloatValue", "dataType": FLOAT},
            {"columnName": "OutputIntegerValue", "dataType": INTEGER},
            {"columnName": "OutputStringValue", "dataType": STRING},
            
            {"columnName": "PVBooleanValue", "dataType": BOOLEAN},
            {"columnName": "PVFloatValue", "dataType": FLOAT},
            {"columnName": "PVIntegerValue", "dataType": INTEGER},
            {"columnName": "PVStringValue", "dataType": STRING},
            
            {"columnName": "TargetBooleanValue", "dataType": BOOLEAN},
            {"columnName": "TargetFloatValue", "dataType": FLOAT},
            {"columnName": "TargetIntegerValue", "dataType": INTEGER},
            {"columnName": "TargetStringValue", "dataType": STRING}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey",  "FolderPath"]
        },
          
        {
        "table": "SfcRecipeDataOutputRamp", 
        "selectQueryName": "DB Transfer/SfcRecipeDataOutputRamp",
        "primaryKey": "RecipeDataId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP},
            {"columnName": "StepName", "dataType": LOOKUP_WITH_TWO_KEYS},
            {"columnName": "RecipeDataKey", "dataType": LOOKUP},
            {"columnName": "RecipeDataType", "dataType": LOOKUP},
            {"columnName": "Description", "dataType": STRING},
            {"columnName": "Label", "dataType": STRING},
            {"columnName": "Units", "dataType": STRING},
            {"columnName": "Tag", "dataType": STRING},
            
            {"columnName": "Download", "dataType": BOOLEAN},
            {"columnName": "Timing", "dataType": FLOAT},
            {"columnName": "MaxTiming", "dataType": FLOAT},
            {"columnName": "WriteConfirm", "dataType": BOOLEAN},
            {"columnName": "RampTimeMinutes", "dataType": FLOAT},
            {"columnName": "UpdateFrequencySeconds", "dataType": FLOAT},
            
            {"columnName": "FolderPath", "dataType": LOOKUP_FOLDER, "idColumnName": "RecipeDataFolderId"},
            {"columnName": "ValueType", "dataType": LOOKUP},
            {"columnName": "OutputType", "dataType": LOOKUP},
            
            {"columnName": "OutputBooleanValue", "dataType": BOOLEAN},
            {"columnName": "OutputFloatValue", "dataType": FLOAT},
            {"columnName": "OutputIntegerValue", "dataType": INTEGER},
            {"columnName": "OutputStringValue", "dataType": STRING},
            
            {"columnName": "PVBooleanValue", "dataType": BOOLEAN},
            {"columnName": "PVFloatValue", "dataType": FLOAT},
            {"columnName": "PVIntegerValue", "dataType": INTEGER},
            {"columnName": "PVStringValue", "dataType": STRING},
            
            {"columnName": "TargetBooleanValue", "dataType": BOOLEAN},
            {"columnName": "TargetFloatValue", "dataType": FLOAT},
            {"columnName": "TargetIntegerValue", "dataType": INTEGER},
            {"columnName": "TargetStringValue", "dataType": STRING}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey",  "FolderPath"]
        },
          
        {
        "table": "SfcRecipeDataArray", 
        "selectQueryName": "DB Transfer/SfcRecipeDataArray",
        "primaryKey": "RecipeDataId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP, "insert": False},
            {"columnName": "StepName", "dataType": LOOKUP_WITH_TWO_KEYS, "insert": False},
            {"columnName": "RecipeDataKey", "dataType": LOOKUP},
            {"columnName": "RecipeDataType", "dataType": LOOKUP},
            {"columnName": "Description", "dataType": STRING},
            {"columnName": "Label", "dataType": STRING},
            {"columnName": "Units", "dataType": STRING},
            {"columnName": "FolderPath", "dataType": LOOKUP_FOLDER, "idColumnName": "RecipeDataFolderId"},
            {"columnName": "ValueType", "dataType": LOOKUP},
            {'columnName': "KeyName",  "dataType": STRING}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey",  "FolderPath"]
        },
          
        {
        "table": "SfcRecipeDataArrayElement", 
        "selectQueryName": "DB Transfer/SfcRecipeDataArrayElement",
        "primaryKey": "RecipeDataId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": STRING},
            {"columnName": "StepName", "dataType": STRING},
            {"columnName": "RecipeDataKey", "dataType": STRING},
            {"columnName": "ArrayIndex", "dataType": INTEGER},
            {"columnName": "BooleanValue", "dataType": BOOLEAN},
            {"columnName": "FloatValue", "dataType": FLOAT},
            {"columnName": "IntegerValue", "dataType": INTEGER},
            {"columnName": "StringValue", "dataType": STRING}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey",  "FolderPath", "ArrayIndex"]
        },
    
        {
        "table": "SfcRecipeDataMatrix", 
        "selectQueryName": "DB Transfer/SfcRecipeDataMatrix",
        "primaryKey": "RecipeDataId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": LOOKUP, "insert": False},
            {"columnName": "StepName", "dataType": LOOKUP_WITH_TWO_KEYS, "insert": False},
            {"columnName": "RecipeDataKey", "dataType": LOOKUP},
            {"columnName": "RecipeDataType", "dataType": LOOKUP},
            {"columnName": "Description", "dataType": STRING},
            {"columnName": "Label", "dataType": STRING},
            {"columnName": "Units", "dataType": STRING},
            {"columnName": "FolderPath", "dataType": LOOKUP_FOLDER, "idColumnName": "RecipeDataFolderId"},
            {"columnName": "ValueType", "dataType": LOOKUP},
            {'columnName': "RowIndexKey",  "dataType": STRING},
            {'columnName': "ColumnIndexKey",  "dataType": STRING}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey",  "FolderPath"]
        },

        {
        "table": "SfcRecipeDataMatrixElement", 
        "selectQueryName": "DB Transfer/SfcRecipeDataMatrixElement",
        "primaryKey": "RecipeDataId",
        "columnsToCompareAndUpdate": [
            {"columnName": "ChartPath", "dataType": STRING},
            {"columnName": "StepName", "dataType": STRING},
            {"columnName": "RecipeDataKey", "dataType": STRING},
            {"columnName": "RowIndex", "dataType": INTEGER},
            {"columnName": "ColumnIndex", "dataType": INTEGER},
            {"columnName": "BooleanValue", "dataType": BOOLEAN},
            {"columnName": "FloatValue", "dataType": FLOAT},
            {"columnName": "IntegerValue", "dataType": INTEGER},
            {"columnName": "StringValue", "dataType": STRING}
            ],
        "uniqueColumns": ["ChartPath", "StepName", "RecipeDataKey",  "FolderPath", "RowIndex", "ColumnIndex"]
        }
    ]


lookups = [       
        {
        "name": "ApplicationName",
        "sql": "select applicationId from DtApplication where ApplicationName = ",
        "idColumnName": "ApplicationId"
        },

        {
        "name": "ChartPath",
        "sql": "select chartId from SfcChart where ChartPath = ",
        "idColumnName": "ChartId"
        },

        {
        "name": "ChildChartPath",
        "sql": "select chartId from SfcChart where ChartPath = ",
        "idColumnName": "ChildChartId"
        },

        {
        "name": "FamilyName",
        "sql": "select familyId from DtFamily where FamilyName = ",
        "idColumnName": "FamilyId"
        },

        {
        "name": "FeedbackMethod",
        "sql": "select LookupId from Lookup where LookupTypeCode = 'FeedbackMethod' and LookupName = ",
        "idColumnName": "FeedbackMethodId"
        },

        {
        "name": "FinalDiagnosisName",
        "sql": "select finalDiagnosisId from DtFinalDiagnosis where FinalDiagnosisName = ",
        "idColumnName": "FinalDiagnosisId"
        },

        {
        "name": "GroupRampMethod",
        "sql": "select LookupId from Lookup where LookupTypeCode = 'GroupRampMethod' and LookupName = ",
        "idColumnName": "GroupRampMethodId"
        },
   
        {
        "name": "HandlerChartPath",
        "sql": "select chartId from SfcChart where ChartPath = ",
        "idColumnName": "HandlerChartId"
        },

        {
        "name": "KeyName",
        "sql": "select keyId from SfcRecipeDataKeyMaster where KeyName = ",
        "idColumnName": "KeyId"
        },

        {
        "name": "QuantOutputName",
        "sql": "select QuantOutputId from DtQuantOutput where QuantOutputName = ",
        "idColumnName": "QuantOutputId"
        },

        {
        "name": "QueueKey",
        "sql": "select queueId from QueueMaster where QueueKey = ",
        "idColumnName": "MessageQueueId"
        },

        {
        "name": "RampType",
        "sql": "select LookupId from Lookup where LookupTypeCode = 'RampType' and LookupName = ",
        "idColumnName": "RampTypeId"
        },
           
        {
        "name": "RecipeDataKey",
        "sql": "select RecipeDataId from SfcRecipeData where RecipeDataKey = ",
        "idColumnName": "RecipeDataId"
        },
           
        {
        "name": "RecipeDataType",
        "sql": "select RecipeDataTypeId from SfcRecipeDataType where RecipeDataType = ",
        "idColumnName": "RecipeDataTypeId"
        },

        {
        "name": "StepName",
        "sql1": "select stepId from SfcStepView where ChartPath = ",
        "key1": "chartPath",
        "key1Type": STRING,
        "sql2": "and StepName = ",
        "key2": "stepName",
        "key2Type": STRING,
        "idColumnName": "StepId"
        },
           
        {
        "name": "StepId",
        "sql1": "select stepId from SfcStepView where ChartPath = ",
        "key1": "chartPath",
        "key1Type": STRING,
        "sql2": "and StepName = ",
        "key2": "stepName",
        "key2Type": STRING,
        "idColumnName": "StepId"
        },

        {
        "name": "StepType",
        "sql": "select StepTypeId from SfcStepType where StepType = ",
        "idColumnName": "StepTypeId"
        },

        {
        "name": "UnitName",
        "sql": "select unitId from TkUnit where unitName = ",
        "idColumnName": "UnitId"
        },
           
        {
        "name": "ValueType",
        "sql": "select ValueTypeId from SfcValueType where ValueType = ",
        "idColumnName": "ValueTypeId"
        },
    
    ]