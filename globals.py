import os

# ==== CONSTANTS =======

# logging
LOG_FOLDER = os.path.join(os.path.dirname(__file__), 'logs/')
LOG_FILE = os.path.join(LOG_FOLDER, 'xl2ckan.log')

# used in connection_manager
CKAN_PROFILES_FILE = os.path.join(os.path.dirname(__file__), 'config/portals.json')

# used in package_builder
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config/config.yml')  # default
MAPPER_ROOT = 'field_mapper'  # mandatory in configuration file
BASE_FIELDS_ROOT = 'base_fields'  # mandatory in configuration file
STRUCTURE_FIELDS_ROOT = 'structure_fields'  # mandatory in configuration file
START_SHEET = 'start_sheet'  # mandatory in configuration file
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'out/')  # default

# ==== GLOBAL MESSAGES =======

MSG_MISSING_FIELD_MAPPER = 'Invalid config file: key field_mapper is missing'
MSG_MISSING_STRUCTURE_FIELDS = 'Invalid config file: key structure_fields is missing'
MSG_MISSING_FIELD_DEFINITION = 'Field definition missing: '
MSG_MISSING_START_SHEET_DEFINTION = 'Start sheet missing in config file.'

# ==== UI Messages =======

MSG_UI_START = 'Choose your next step:'