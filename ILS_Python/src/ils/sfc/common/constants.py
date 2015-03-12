'''
Created on Oct 31, 2014

@author: rforbes
'''
CENTER = 'center'
TOP_LEFT = 'topLeft'
TOP_CENTER = 'topCenter'
TOP_RIGHT = 'topRight'
BOTTOM_LEFT = 'bottomLeft'
BOTTOM_CENTER = 'bottomCenter'
BOTTOM_RIGHT = 'bottomRight'
RIGHT = "right"
LEFT = "left"
TOP = 'top'
BOTTOM = 'bottom'

ACK_REQUIRED = "ackRequired"
ACK_TIME = "ackTime"
ACK_TIMED_OUT = "ackTimedOut"
AUTO_MODE = "autoMode"
AUTOMATIC = "automatic"
BUTTON = 'button'
BUTTON_LABEL = 'buttonLabel'
BUTTON_KEY = 'buttonKey'
BUTTON_KEY_LOCATION = 'buttonKeyLocation'
BY_NAME = 'stepsByName'
CALLBACK = "callback"
CANCELED = 'canceled'
CHART_NAME = 'chartName'
CHART_PROPERTIES = 'chartProperties'
CHART_RUN_ID = 'chartRunId'
CLASS_NAME = 'className'
COMMAND = "callback"
CHOICES= "choices"
CHOICES_KEY = "choicesKey"
CHOICES_RECIPE_LOCATION = "choicesRecipeLocation"
COMPUTER = 'computer'
CONFIG = 'config'
CREATE_TIME = 'createTime'
DATA = "data"
DESCRIPTION = "description"
DELAY = "delay"
DELAY_UNIT = "delayUnit"
DIALOG = "dialog"
DIALOG_TEMPLATE = "dialogTemplate"
DIRECTORY = "directory"
DYNAMIC = "dynamic"
DISPLAY_MODE = "displayMode"
ENABLE_PAUSE = 'enablePause'
ENABLE_RESUME = 'enableResume'
ENABLE_CANCEL = 'enableCancel'
EXTENSION = 'extension'
FETCH_MODE = "fetchMode"
FILEPATH = "filepath"
FILENAME = "filename"
GLOBAL = "global"
ID = 'id'
INPUT = 'input'
INSTANCE_ID = 'instanceId'
ISOLATION_MODE = 'isolationMode'
KEY = "key"
KEY_MODE = "keyMode"
LABEL = 'label'
LOCATION = 'location'
MESSAGE = "message"
MESSAGE_ID = 'messageId'
MESSAGE_QUEUE = 'messageQueue'
METHOD = "method"
MINIMUM_VALUE = "minimumValue"
MAXIMUM_VALUE = "maximumValue"
MULTIPLE = "multiple"
NAME = "name"
PARENT = 'parent'
POSITION = 'position'
POST_TO_QUEUE = "postToQueue"
POST_NOTIFICATION = "postNotification"
POSTING_METHOD = "postingMethod"
PRINT_FILE = "printFile"
PRIORITY = "priority"
PROJECT = 'project'
PROMPT = "prompt"
QUEUE = "queue"
RECIPE = "recipe"
RECIPE_LOCATION = "recipeLocation" 
RECIPE_DATA = "recipeData"
RESPONSE = 'response'
RESULTS_MODE = "resultsMode" 
REVIEW_DATA = "reviewData" 
REVIEW_DATA_WITH_ADVICE = "reviewDataWithAdvice" 
SCALE = 'scale'
SCREEN_HEADER = "screenHeader"
SECURITY = 'security'
SEMI_AUTOMATIC = 'semiAutomatic'
SERVER = 'server'
SINGLE = "single"
SQL = "sql"
START_TIME = 'startTime'
STATIC = "static"
STATUS = "status"
STEP_PROPERTIES = 'stepProperties'
STRATEGY = "strategy"
TAG_PATH = "tagPath"
STRATEGY = "strategy"
TEST_RESPONSE = 'testResponse'
TIMEOUT = "timeout"
TIMEOUT_UNIT = "timeoutUnit"
TIMESTAMP = "timestamp"
UPDATE = "update"
UPDATE_OR_CREATE = "updateOrCreate"
UNITS = "units"
USER = 'user'
VALUE = 'value'
VIEW_FILE = "viewFile"
WINDOW = 'window'
WINDOW_ID = 'windowId'
WINDOW_PROPERTIES = 'windowProperties'

MESSAGE_ID = 'messageId'
MESSAGE_QUEUE = 'messageQueue'
RECIPE_LOCATION = "recipeLocation"  

# The name of the second unit is really defined in the database,
# so this constant should agree with that. Likewise for type:
SECOND= "SEC"
MINUTE= "MIN"
TIME_UNIT_TYPE = "TIME"

# symbols for TimeDelayStep "units"
# nothing to do with unit conversion units
DELAY_UNIT_SECOND = "SEC";
DELAY_UNIT_MINUTE = "MIN";
DELAY_UNIT_HOUR = "HR";

#Recipe scopes:
LOCAL_SCOPE = 'local'
PREVIOUS_SCOPE = 'previous'
SUPERIOR_SCOPE ='superior'
PHASE_SCOPE ='phase'
OPERATION_SCOPE = 'operation'
GLOBAL_SCOPE = 'global'

# chart statuses corresponding to IA's ChartStateEnum in java
RUNNING = "Running"
PAUSED = "Paused"
ABORTED = "Aborted"
CANCELED = "Canceled"
STOPPED = "Stopped"
