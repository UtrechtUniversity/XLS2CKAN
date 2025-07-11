# created by otto at 10/12/2020
"""
The profiles module contains urls and public keys for connecting to a CKAN instance.
All information is managed through the class CkanProfile.
This module is necessary to receive and send information to CKAN, not for producing standalone
(loadable) packages.
"""
import json
import logging
import globals
import lib

# create connection_manager logger
connection_log = logging.getLogger(__name__)


class CkanProfile:
    def __init__(self, environment, profiles=globals.CKAN_PROFILES_FILE):
        try:
            self.profiles = load_json_from_file(profiles)
            configs = self.profiles['portal_api_configs']
            environments = \
                [sub['environment'] for sub in configs]
            if not (environment in environments):
                raise Exception("Sorry, no definition in configs for environment \"" + environment + "\"")
            else:
                index = environments.index(environment)
                self.environment = environment
                # obsolete: self.TCS_PORTAL_API_BASE = self.profiles['portal_api_configs'][index]['TCS_PORTAL_API_BASE']
                self.PORTAL_CKAN_API_BASE = \
                    self.profiles['portal_api_configs'][index]['PORTAL_CKAN_API_BASE']
                self.PORTAL_URL = self.profiles['portal_api_configs'][index]['PORTAL_URL']
                self.APIkey = self.profiles['portal_api_configs'][index]['APIkey']
                self.HOST = self.profiles['portal_api_configs'][index]['PORTAL_HOST']
                self.PORT = self.profiles['portal_api_configs'][index]['PORTAL_PORT']
        except Exception as err:
            connection_log.debug(err)

def load_json_from_file(file_name):
    # returns JSON-file's content as Python dictionary
    with open(file_name) as f:
        json_dict = json.load(f)
        return json_dict