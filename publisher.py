import json
from logging import raiseExceptions

import database_manager as db
import package_builder as pb
import globals
import glob
import lib
import logging

# create connection_manager logger
# publish_log = lib.redirect_logging_stdio('xl2ckan_logger.publish',
#                                             logging.DEBUG)

publish_log = logging.getLogger(__name__)

class Publisher:
    """
    base class for creating and uploading bulk and individual packages
    """
    def __init__(self, ckan_instance, excel_file=None, config=globals.CONFIG_FILE):
        """
        :param ckan_instance: ckan profile name
        :type str:
        :param excel_file: sources in Excel format
        :type str:
        :param config: optional custom globals file
        :type: str
        """

        self.ckan_db = db.CkanInstance(ckan_instance)
        self.config = config
        if excel_file is not None:  # we need to have this optional because we want to be able to upload sources independently
            self.package_builder = pb.PackageBuilder(excel_file, config)
        else:
            self.package_builder = None  # useful when created for merely uploading source packages

    def publish(self):
        try:
            if self.package_builder is None:
                raise Exception('No Excel file loaded: necessary for Publisher::publish()')
            else:
                self.package_builder.generate_full_loadables_collection()
                self.upload_sources()
        except Exception as e:
            publish_log.debug(e)

    def generate_loadables(self, rowset=None):
        try:
            if self.package_builder is None:
                raise Exception('No Excel file loaded: necessary for Publisher::generate_loadables()')
            else:
                if rowset is None:  # generate all
                    self.package_builder.generate_full_loadables_collection()
                else:
                    if not isinstance(rowset, list):
                        raise Exception('Rowset (Publisher::generate_loadables) was not given as a list.')
                    else:
                        for row in rowset:
                            self._generate_loadable_package(int(row))
        except Exception as e:
            publish_log.debug(e)

    def upload_sources(self):
        try:
            for package_file in glob.glob(globals.OUTPUT_FOLDER + '*.json'):
                with open(package_file, 'r') as f:
                    publish_log.info('Opening datapackage: ' + str(package_file))
                    package = json.load(f)
                    self.ckan_db.package_publish(package, False)
        except Exception as e:
            publish_log.debug(e)

    # -------- Privte functions for class Publisher --------

    def _generate_loadable_package(self, rownum):
        # only offered for startsheet, if needed otherwise call function from package_builder
        try:
            if self.package_builder is None:
                raise Exception('No Excel file loaded: necessary for Publisher::_generate_loadable_package()')
            else:
                self.package_builder.generate_package(rownum)
                self.package_builder.save_package_to_file(include_row=True)
                # TODO: we include rownum for indvidual packages, may be set to default in save_package_to_file
        except Exception as e:
            publish_log.debug(e)

