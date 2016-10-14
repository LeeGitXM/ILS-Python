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
AUTO_MODE = "autoMode"
AUTOMATIC = "automatic"
BUTTON = 'button'
BUTTON_LABEL = 'buttonLabel'
BUTTON_KEY = 'buttonKey'
BUTTON_KEY_LOCATION = 'buttonKeyLocation'
BY_NAME = 'stepsByName'
CALLBACK = "callback"
CANCELED = 'canceled'
CHART = 'chart'
CHART_NAME = 'chartName'
CHART_PROPERTIES = 'chartProperties'
CHART_RUN_ID = 'chartRunId'
CHOICES= "choices"
CHOICES_KEY = "choicesKey"
CHOICES_RECIPE_LOCATION = "choicesRecipeLocation"
CLASS_NAME = 'className'
CLIENT_ID = 'clientId'
COMMAND = "callback"
COMPUTER = 'computer'
CONFIG = 'config'
CONTROL_PANEL_ID = 'controlPanelId'
CONTROL_PANEL_NAME = 'controlPanelName'
CREATE_TIME = 'createTime'
CREATE = 'create'
DATA = "data"
DATABASE = 'database'
DESCRIPTION = "description"
DELAY = "delay"
DELAY_UNIT = "delayUnit"
#DIALOG = "dialog"
#DIALOG_TEMPLATE = "dialogTemplate"
DIRECTORY = "directory"
DOWNLOAD_STATUS = 'downloadStatus'
DYNAMIC = "dynamic"
DISPLAY_MODE = "displayMode"
ENABLE_PAUSE = 'enablePause'
ENABLE_RESUME = 'enableResume'
ENABLE_CANCEL = 'enableCancel'
END_TIME = "endTime"
EXTENSION = 'extension'
FETCH_MODE = "fetchMode"
FILEPATH = "filepath"
FILENAME = "filename"
GLOBAL = "global"
HANDLER = 'handler'
ID = 'id'
INPUT = 'input'
INSTANCE_ID = 'instanceId'
ISOLATION_MODE = 'isolationMode'
KEY = "key"
KEY_MODE = "keyMode"
LOCATION = 'location'
MESSAGE = "message"
DEFAULT_MESSAGE_QUEUE = 'SFC-Message-Queue'
MESSAGE_QUEUE = 'msgQueue'
MESSAGE_ID = 'msgId'
METHOD = "method"
MINIMUM_VALUE = "minimumValue"
MAXIMUM_VALUE = "maximumValue"
MSG_QUEUE_WINDOW = 'Queue/Message Queue'
MULTIPLE = "multiple"
NAME = "name"
NUMBER_OF_TIMEOUTS = "numberOfTimeouts"
NUMBER_OF_ERRORS = 'numberOfErrors'
OK = 'Ok'
ORIGINATOR = 'originator'
PARENT = 'parent'
POSITION = 'position'
POST_TO_QUEUE = "postToQueue"
POST_NOTIFICATION = "postNotification"
POSTING_METHOD = "postingMethod"
PRIMARY_CONFIG = 'primaryConfig'
PRIMARY_REVIEW_DATA = "primaryReviewData" 
PRIMARY_REVIEW_DATA_WITH_ADVICE = "primaryReviewDataWithAdvice" 
PRIMARY_TAB_LABEL = "primaryTabLabel"; 
PRINT_FILE = "printFile"
PRIORITY = "priority"
PROJECT = 'project'
PROMPT = "prompt"
PV_MONITOR_ACTIVE = "pvMonitorActive"
PV_MONITOR_STATUS = "pvMonitorStatus"
PV_VALUE = "pvValue"
RECIPE = "recipe"
RECIPE_LOCATION = "recipeLocation" 
RECIPE_DATA = "recipeData"
RESPONSE = 'response'
RESULTS_MODE = "resultsMode" 
SCALE = 'scale'
SECONDARY_CONFIG = 'secondaryConfig'
SECONDARY_REVIEW_DATA = "secondaryReviewData" 
SECONDARY_REVIEW_DATA_WITH_ADVICE = "secondaryReviewDataWithAdvice" 
SECONDARY_TAB_LABEL = "secondaryTabLabel"
SECURITY = 'security'
SEMI_AUTOMATIC = 'semiAutomatic'
SERVER = 'server'
SESSION = "session"
SESSION_ID = 'sessionId'
SESSIONS = "sessions"
SETPOINT = 'setpoint'
SETPOINT_STATUS = 'setpointStatus'
SINGLE = "single"
SQL = "sql"
START_TIME = 'startTime'
STATIC = "static"
STATUS = "status"
STEP = 'step'
STEP_PROPERTIES = 'stepProperties'
STRATEGY = "strategy"
SUM_FLOWS = 'sumFlows'
TAG_PATH = 'tagPath'
TAG = 'tag'
STRATEGY = "strategy"
TABLE = 'table'
TEST_CHART_PATHS = 'testChartPaths'
TEST_PATTERN = 'testPattern'
TEST_REPORT_FILE = 'testReportFile'
TIMED_OUT = "timedOut"
TIMEOUT = "timeout"
TIMEOUT_TIME = 'timeoutTime'
TIMEOUT_UNIT = "timeoutUnit"
TIMESTAMP = "timestamp"
UPDATE = "update"
UPDATE_OR_CREATE = "updateOrCreate"
UNITS = "units"
USER = 'user'
VALUE = 'value'
VALUE_TYPE = 'valueType'
VIEW_FILE = "viewFile"
WAITING_FOR_REPLY = 'waitingForReply'
WINDOW = 'window'
WINDOW_ID = 'windowId'
WINDOW_TITLE = 'windowTitle'
WINDOW_PROPERTIES = 'windowProperties'

RECIPE_LOCATION = "recipeLocation"  

# Some standard client responses
YES_RESPONSE = "Yes"
NO_RESPONSE = "No"

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
PRIOR_SCOPE = 'prior'
SUPERIOR_SCOPE ='superior'
PHASE_SCOPE ='phase'
OPERATION_SCOPE = 'operation'
GLOBAL_SCOPE = 'global'
TAG_SCOPE = 'tag'
# TAG is also acceptable as a scope

# chart statuses corresponding to IA's ChartStateEnum in java
RUNNING = "Running"
PAUSED = "Paused"
ABORTED = "Aborted"
CANCELED = "Canceled"
STOPPED = "Stopped"

# Message statuses
MSG_STATUS_INFO = 'Info'
MSG_STATUS_WARNING = 'Warning'
MSG_STATUS_ERROR = 'Error'

# Default window paths
REVIEW_DATA_WINDOW = 'reviewDataWindow'

#Step scope internal status
_STATUS = '_status'
ACTIVATE = 'Activate'
PAUSE = 'Pause'
RESUME = 'Resume'
CANCEL = 'Cancel'

#colors
WHITE = 'white'
YELLOW = 'yellow'
ORANGE = 'orange'
RED = 'red'
GREEN = '0,128,0'

# Write Output / PV Monitoring / Download Monitor STEP column status
STEP_PENDING = 'pending'
STEP_APPROACHING = 'approaching'
STEP_DOWNLOADING = 'downloading'
STEP_SUCCESS = 'success'
STEP_FAILURE = 'failure'

# Write Output / PV Monitoring / Download Monitor PV column status
PV_MONITORING = 'monitoring'
PV_WARNING = 'warning'
PV_OK_NOT_PERSISTENT = 'ok not persistent'
PV_OK = 'ok'
PV_BAD_NOT_CONSISTENT = 'bad not consistent'
PV_ERROR = 'error'
PV_NOT_MONITORED = 'not monitored'

# Write Output / PV Monitoring / Download Monitor SETPOINT column status
SETPOINT_OK = 'ok'
SETPOINT_PROBLEM = 'problem'

# the default sleep increment for loops, in seconds
SLEEP_INCREMENT = 5

# tag value types -- TODO: remove--duplicate with Java
DATE_TIME = 'date/time'
STRING = 'string'
INT = 'int'
FLOAT = 'float'
BOOLEAN = 'boolean'
# DATE = 'date'