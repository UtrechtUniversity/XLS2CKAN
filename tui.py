from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.shortcuts import message_dialog
from prompt_toolkit.shortcuts import input_dialog
from prompt_toolkit.shortcuts import yes_no_dialog

import json
import globals
import lib
from globals import MSG_UI_START
from publisher import Publisher
import logging

# create connection_manager logger
tui_log = logging.getLogger(__name__)

# since prompt_toolkit is running on top of asyncio and to het rid of asyncio.DEBUG spamming:
logging.getLogger('asyncio').setLevel(logging.WARNING)  # Remove asyncio debug and info messages, but leave warnings.

class UI:
    def __init__(self):
        self.settings = {'ckan': None, 'excel': None}
        self.info = ''
        self.publisher = None
        result = self.start_loop()
        tui_log.info(str(result))

    def start_loop(self):
        """
        Main loop for GUI
        :return:
        """
        if self.welcome():
            ckan = self.settings['ckan'] = self.choose_environment()
        else:
            ckan = None
        self.settings.update({'ckan': ckan})

        result = None
        self.info_update()
        default=None
        while result != 'quit':
            result = self.start_screen(self.info, default=default)
            match result:
                case 'environment':
                    result = self.choose_environment()
                    self.settings.update({'ckan': result})
                    self.info_update()
                    default = "environment"
                case "load_excel":
                    result = self.get_excel_path()
                    if result != None:
                        self.settings.update({'excel': result})
                    self.info_update()
                    default = 'load_excel'
                case "run_builder":
                    result = self.run_builder()
                    default = "run_builder"
                case "upload":
                    result = 'publisher upload'
                    info_txt = ("Upload current sources from\n"+
                                globals.OUTPUT_FOLDER + "?")
                    if yes_no_dialog('Confirmation', info_txt).run():
                        self.upload_current_sources()
                    default = "upload"
                case "all_in_one":
                    result = 'all in one publish'
                    self.publish_all()
                    default = "all_in_one"
                case "open_out":
                    lib.open_folder(globals.OUTPUT_FOLDER)
                case "help":
                    self.show_help()
                    default = "help"
                case _:
                    result = 'quit'
        result = 'bye'
        return result

    def info_update(self):
        self.info = self.get_settings() + '\n\n' + 'Current choices:\n===============\n\n'
        self.info = self.info + lib.get_dict_as_strings(self.settings) + '\n\nOptions:\n======='

    def welcome(self):
        result = yes_no_dialog(
            title='Excel2CKAN Package Builder',
            text='Do you want to start choosing an environment?').run()
        return result


    def start_screen(self, txt, default=None):
        result = radiolist_dialog(
            title=MSG_UI_START,
            text=txt,
            default=default,
            values=[
                ("environment", "Choose a CKAN instance"),
                ("load_excel", "Load an Excel file"),
                ("run_builder", "Start the package(s) builder"),
                ("upload", "Upload sources to CKAN"),
                ("all_in_one", "All-in-one publisher"),
                ("open_out", "Open output folder"),
                ("help", "Help"),
                ("quit", "Quit")
            ],
            style=Style.from_dict({
                'dialog': 'bg:#b4e8b8',
                'button': 'bg:#bfbbbb fg:#000000',
                'button focused': 'bg:#ff0000',
                'checkbox': '#e8612c',
                'dialog.body': 'bg:#1963a0 fg:#ffffff',
                'dialog shadow': 'bg:#325454',
                'frame.label': '#efec13',
                'dialog.body label': '#fcfa8a',
            })
        ).run()
        return result

    def choose_environment(self):
        environments = globals.CKAN_PROFILES_FILE
        with open(environments, 'r') as configfile:
            profiles = configfile.read()
        configurations = json.loads(profiles)
        config_choices = []
        for config in configurations['portal_api_configs']:
            config_choices.append((config['environment'],config['environment']))
        result = radiolist_dialog(
            title="Available CKAN instances",
            text="Choose your instance",
            values=config_choices).run()
        return result

    def get_excel_path(self):
        try:
            if self.settings['ckan'] is not None:
                if self.settings['excel'] is not None:
                    full_path = self.settings['excel']
                    full_path = input_dialog('Full path to Excel data file:', default=full_path).run()
                else:
                    full_path = input_dialog('Full path to Excel data file:').run()
                    full_path = os.path()
                if full_path is not None:
                    self.publisher = Publisher(self.settings['ckan'], full_path)
                    return f'{full_path}'
            else:
                message_dialog('No CKAN', 'You need to choose an environment first').run()
                return None
        except Exception as e:
            msg = 'Problem loading ' + full_path
            message_dialog('Problem loading Excel data', msg).run()
            tui_log.debug(msg)
            tui_log.debug(e)
            self.settings['excel'] = None

    def upload_current_sources(self):
        try:
            if self.settings['ckan'] is not None:
                if self.publisher is None:
                    self.publisher = Publisher(self.settings['ckan'])
                self.publisher.upload_sources()
                self.show_done()
            else:
                message_dialog('No CKAN', 'You need to choose an environment first').run()
                return None
        except Exception as e:
            msg = ('An exception occurred in loading sources:\n' +
                   str(e))
            message_dialog('Exception', msg).run()

    def publish_all(self):
        try:
            if self.publisher is not None:
                self.publisher.publish()
                self.show_done()
            else:
                msg = 'No publisher defined: make sure to load an Excel file and set the CKAN instance.'
                message_dialog('Error', msg).run()
                raise Exception(msg)
        except Exception as e:
            tui_log.debug(e)

    def get_settings(self):
        settings_info = ('CKAN Profiles: ' + globals.CKAN_PROFILES_FILE + '\n' +
                         'Config file: ' + globals.CONFIG_FILE + '\n' +
                         'Output folder: ' + globals.OUTPUT_FOLDER)
        return 'Settings: (from globals.py)\n========\n\n' + settings_info

    def show_help(self):
        help_msg = 'We will move to brief overveiw and option to open README.md (via module os).'
        example_style = Style.from_dict({
            'dialog': 'bg:#88ff88',
            'dialog frame.label': 'bg:#ffffff #000000',
            'dialog.body': 'bg:#000000 #00ff00',
            'dialog shadow': 'bg:#00aa00',
        })
        result = message_dialog('Xloader - HELP', help_msg, style=example_style).run()
        return result

    def run_builder(self):
        if (self.settings['ckan'] != None) and (self.settings['excel'] != None):
            info_msg = ('Comma separated list of row numbers from Excel, range like [n-m], or leave empty for all:' +
                        '\ne.g.: 1,2,[5-10],12')
            result = input_dialog('Package builder:', info_msg, default='').run()
            if result == '':
                self.publisher.generate_loadables()
                self.show_done()
            else:
                row_list = lib.row_string_to_integer_list(result)
                if len(row_list) == 0:
                    if yes_no_dialog('Confirmation needed',
                                            'No valid Excel row entries were given. Generate all instead?').run():
                        self.publisher.generate_loadables()
                        self.show_done()
                else:
                    self.publisher.generate_loadables(row_list)
                    self.show_done()
        else:
            message_dialog('Error:', 'Missing CKAN or Excel file').run()
            result = None
        return result

    def show_done(self):
        message_dialog('Operation finished', 'Done!').run()