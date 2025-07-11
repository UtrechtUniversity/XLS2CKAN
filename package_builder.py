import logging
import yaml
import pandas as pd
import json
import lib
import globals
import sys

log = logging.getLogger(__name__)

class _Definitions:
    """
    Manages translation definitions
    """

    def __init__(self, config_file=globals.CONFIG_FILE):
        """
        :param config_file: text

        yaml file containing rules for translation
        """
        self.config_file = config_file
        try:
            self.config = self._load_config_excel_fields()
            self.config.update(self._load_config_base_fields())
            self.config.update(self._get_start_sheet_name())
        except Exception as e:
            if hasattr(e, 'message'):
                log.debug(e.message)
            else:
                log.debug(e)

    def _load_config_excel_fields(self):
        try:
            f = open(self.config_file)
            config = yaml.full_load(f)
            if not globals.MAPPER_ROOT in dict(config).keys():
                log.debug(globals.MSG_MISSING_FIELD_MAPPER)
                exit(None)
            # lower_case_dict = dict((k.lower(), v) for k, v in config[globals.MAPPER_ROOT].items())
            conf_dict = dict((k, v) for k, v in config[globals.MAPPER_ROOT].items())
            log.info('Loaded Excel column definitions from configuration.')
            return {globals.MAPPER_ROOT: conf_dict}
        except Exception as e:
            if hasattr(e, 'message'):
                log.debug(e.message)
            else:
                log.debug(e)

    def _get_start_sheet_name(self):
        try:
            f = open(self.config_file)
            config = yaml.full_load(f)
            if not globals.START_SHEET in dict(config).keys():
                log.debug(globals.MSG_MISSING_START_SHEET_DEFINTION)
                exit(None)
            return {globals.START_SHEET: config[globals.START_SHEET]}
        except Exception as e:
            if hasattr(e, 'message'):
                log.debug(e.message)
            else:
                log.debug(e)

    def _load_config_base_fields(self):
        try:
            f = open(self.config_file)
            config = yaml.full_load(f)
            if not globals.BASE_FIELDS_ROOT in dict(config).keys():
                log.debug(globals.MSG_MISSING_FIELD_MAPPER)
                exit(None)
            # lower_case_dict = dict((k.lower(), v) for k, v in config[BASE_FIELDS_ROOT].items())
            conf_dict = dict((k, v) for k, v in config[globals.BASE_FIELDS_ROOT].items())
            return {globals.BASE_FIELDS_ROOT: conf_dict}
        except Exception as e:
            if hasattr(e, 'message'):
                log.debug(e.message)
            else:
                log.debug(e)

    def get_excel_field_definition(self, source_field, sheet_name):
        try:
            field_definition = self.config[globals.MAPPER_ROOT][sheet_name][source_field]['field_name']
            return field_definition
        except KeyError:
            log_msg = 'Key [\'' + globals.MAPPER_ROOT + '\'][' + source_field + '\']'
            log.debug(globals.MSG_MISSING_FIELD_DEFINITION + log_msg)

    def list_all_excel_sheets(self):
        return list(self.config[globals.MAPPER_ROOT].keys())

    def list_all_excel_fields_for_sheet(self, sheet_name):
        return list(self.config[globals.MAPPER_ROOT][sheet_name].keys())

    def list_all_base_fields(self):
        return list(self.config[globals.BASE_FIELDS_ROOT].keys())

    def list_all_field_definitions(self):
        return self.config[globals.MAPPER_ROOT]


class _Xls:
    """
    Contains the full set of data retrieved from the Excel file
    """

    def __init__(self, source_file):
        self.xl = pd.ExcelFile(source_file)
        self.sheet_names = self.xl.sheet_names  # see all sheet names
        self.xls_source_file = source_file
        self.data = None  # pd.read_excel(self.xls_source_file, self.xls_sheet_name)
        self._read_data_from_excel()

    def _read_data_from_excel(self):
        self.data = {}
        for sheet_name in self.sheet_names:
            data = self.xl.parse(sheet_name)
            self.data.update({sheet_name: data})
        log.info('Loaded data from Excel file.')

    def get_column_names(self, sheet_name):
        return list(self.data[sheet_name].keys())

    def get_column_values(self, column_name):
        try:
            return list(self.data[column_name])
        except KeyError as e:
            log.debug(e)

    def get_row_values_as_dict(self, row_num):
        try:
            return dict(self.data.iloc[row_num])
        except IndexError:
            log.debug('Index error with get_row_values_as_dict: row_num')


class PackageBuilder:
    def __init__(self, source_file,
                 config_file=globals.CONFIG_FILE):
        self.definitions = _Definitions(config_file)
        self.source = _Xls(source_file)
        self.package = {}
        self.current_row = None  # used for optional inclusion in filename

    def generate_full_loadables_collection(self):
        """
        Generates all CKAN JSON loadables for loaded Excel file
        :return:
        """
        #try:
        for i in [0, len(self.source.data)-1]:
            self.generate_package(i)
            self.save_package_to_file()
        #except Exception as e:
            #log.debug(e)

    def save_package_to_file(self, include_row=False, file_name=None):
        if file_name is None:
            file_name = self.package['name'] + '.json'
            if include_row:
                prefix = 'X' + str(self.current_row + 2) + '_'  # we generate Excel rownum as prefix
                file_name = prefix + file_name
        with open(globals.OUTPUT_FOLDER + file_name, 'w') as f:
            json.dump(self.package, f, indent=4)

    def generate_package(self, row, start_sheet=None):
        """

        :param int row: row number in Pandas Dataframe. Pandas dataframe is indexed zero-based.
        :param str start_sheet: Excel sheet where the call of generate_package will run from
        """

        if start_sheet is None:
            start_sheet = self.definitions.config[globals.START_SHEET]
        if not (row > -1):
            log.info('Row number must be greater than or equal to zero.')
        else:
            # (re-) initialize package holder if not in subsheet
            if start_sheet == self.definitions.config[globals.START_SHEET]:
                self.current_row = row
                self.package.clear()
                # generate mandatory ckan base fields and add them to package holder
                self.package.update(self._generate_base_fields(row))

            # process column definitions for start sheet
            for excel_field in self.definitions.list_all_excel_fields_for_sheet(start_sheet):

                # process possible reference sheet
                if 'ref_sheet' in self.definitions.config[globals.MAPPER_ROOT][start_sheet][excel_field].keys():
                    ref_sheet = self.definitions.config[globals.MAPPER_ROOT][start_sheet][excel_field]['ref_sheet']
                    if not ('key' in self.definitions.config[globals.MAPPER_ROOT][start_sheet][excel_field].keys()):
                        msg = 'Mandatory definition \"key\" not found in definition for ' + excel_field + ' while ref_sheet was defined.'
                        raise Exception(msg)
                    else:
                        unique_key = self.definitions.config[globals.MAPPER_ROOT][start_sheet][excel_field]['key']
                        ckan_field_value = str(self._get_excel_field_value(excel_field, row, start_sheet))
                        # check on multi-value field:
                        if 'multiple_value_separator' in self.definitions.config[globals.MAPPER_ROOT] \
                                [start_sheet][excel_field].keys():
                            sep = self.definitions.config[globals.MAPPER_ROOT] \
                                [start_sheet][excel_field]['multiple_value_separator']
                            ckan_field_value = ckan_field_value.split(sep)  # field_value is now of type array
                        # recursively process 'sub package'
                        if isinstance(ckan_field_value, list):  # because of multiple_value_separator
                            for value in ckan_field_value:
                                lookup_value = str(value).lstrip().rstrip()
                                rownum = self._get_rownum_for_unique_value(lookup_value, ref_sheet, unique_key)
                                self.generate_package(rownum, ref_sheet)

                else:  # no reference sheet

                    # get path definition for excel_field:
                    definition = self.definitions.get_excel_field_definition(excel_field, start_sheet)
                    # path_tree = str(definition).split('.')  # level separator not configurable

                    # get cell content for excel_field:
                    ckan_field_value = str(self._get_excel_field_value(excel_field, row, start_sheet))

                    # check on multi-value field:  # TODO: should this necessarily be done again as above?
                    if 'multiple_value_separator' in self.definitions.config[globals.MAPPER_ROOT]\
                            [start_sheet][excel_field].keys():
                        sep = self.definitions.config[globals.MAPPER_ROOT]\
                            [start_sheet][excel_field]['multiple_value_separator']
                        ckan_field_value = ckan_field_value.split(sep)  # field_value is now of type array

                    level_stack = str(definition).split('.')  # level separator not configurable
                    level_stack.reverse()

                    self._add_field_dict(level_stack, ckan_field_value, self.package)

    # -------- Privte functions for class PackageBuilder --------

    def _add_field_dict(self, path_stack, value, package):
        """
        :param path_stack stack: definition from config given as a stack of path levels (high to low)
        :param value object: value collected from Excel cell
        :param package object: can be list or dict, container for traversal through iterative growing self.package

        This routine iteratively updates self.package
        """

        while len(path_stack) > 1:
            # we have a structure field
            s_field = path_stack.pop()  # length stack -1
            if type(package) == dict:
                if not s_field in package.keys():
                    package.update({s_field: [{}]})  # structure field of type list is inserted
                    self._add_field_dict(path_stack, value, package[s_field][0])  # could of course also use -1 ;-)
                else:
                    # structure field s_field already exists as non-empty list
                    # check whether we need to insert new block in list
                    next_field = path_stack[0]
                    current_dict = package[s_field][-1]  # TODO is this indeed always the last one added?
                    new_block = False
                    if next_field in current_dict.keys():
                        # key already exists in one of the entries and is list because it's a structure_field
                        if len(path_stack) == 1:
                        # next_field is not structure field
                            new_block = True
                    if new_block:
                        package[s_field].append({})  # update the structure with new dict in list
                    self._add_field_dict(path_stack, value, package[s_field][-1])

            elif type(package) == list:
                if len(package) > 0: # key already exists with value non-emtpy list
                    package[-1].append({s_field: self._add_field_dict(path_stack, value, package[-1])})
            else:
                log.debug('Issues with non-dict and non-list package field value.')

        if len(path_stack) == 1:
            field = path_stack.pop()
            package.update({field: value})


    def _generate_base_fields(self, row):
        """
        :type row: int
        """
        ckan_basis = {"extras": []}
        for field in self.definitions.list_all_base_fields():
            ckan_basis.update({field: self._get_base_field_value(field, row)})
        return ckan_basis

    def _get_base_field_value(self, base_field, row=None):
        """
        row must have value when variable Excel field value is used in hash
        """
        try:
            field_value = self.definitions.config[globals.BASE_FIELDS_ROOT][base_field]
            if field_value[0] == '~':  # needs to be hashed
                hash_fields = field_value.split('.')  # first itemis '!': skip
                input_string = ''
                for field in hash_fields:
                    if field != '~':
                        if field[0] == '_':  # concerns an Excel-valued field
                            # field must be preceded with sheetname, e.g. _Sheet1::field_name
                            # TODO built-in check on presence valid sheetname identifier
                            field_name = field.split('::')[1]
                            sheet_name = field.split('::')[0].split('_')[1]
                            field_value = str(self._get_excel_field_value(field_name, row, sheet_name))
                        else:  # concerns a base_field
                            field_value = self._get_base_field_value(field, row).lower()
                        input_string = input_string + field_value
                field_value = lib.encode(input_string)
            return field_value
        except KeyError:
            log_msg = 'Key [\'' + globals.BASE_FIELDS_ROOT + '\'][' + base_field + '\']'
            log.debug(globals.MSG_MISSING_FIELD_DEFINITION + log_msg)
        except Exception as e:
            if hasattr(e, 'message'):
                log.debug(e.message)
            else:
                log.debug(e)

    def _get_excel_field_value(self, field, row, sheet_name):
        """
        field: str
        row: int ; pandas dataframe rows are indexed zero-based
        sheet_name: str ; name of sheet from which to get the value
        """
        return self.source.data[sheet_name].iloc[row][field]

    def _get_rownum_for_unique_value(self, value, sheet_name, column_name):
        """
        Returns a dataframe index if len == 1
        Raises Exception if len > 1
        Returns None if len == 0
        """
        try:
            df = self.source.data[sheet_name]
            idx = df[df[column_name].str.fullmatch(str(value).strip(), case=False)].index
            if len(idx) != 1:
                if len(idx) == 0:
                    msg = ('Unique value \"' + value + '\" in sheet '
                           + sheet_name + ': ' + column_name + ' not found!')
                else:
                    msg = 'Value ' + value + ' in column ' + sheet_name + ':' + column_name + ' not unique!'
                raise Exception(msg)
            return idx[0]  # we get the integer index from object of type Int64Index
        except Exception as e:
            log.debug(e)


