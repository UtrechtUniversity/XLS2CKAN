#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 17:13:03 2019

@author: otto
"""
import logging

from ckanapi import RemoteCKAN
import ckanapi
import json
import requests
import connection_manager as portal_profile
import hashlib
import lib
import sys
import socket

# create database_manager logger
# db_log = lib.redirect_logging_stdio('xl2ckan_logger.db_manager',
#                                     logging.DEBUG)
#
# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# db_log.addHandler(handler)

db_log = logging.getLogger(__name__)

class CkanInstance:
    """
    Base class for managing a CKAN portal (e.g. production, staging, testing)
    """

    def __init__(self, ckan_sys_profile):
        """
        ckan_sys_profile: profile entry in CKAN configuration file config/portals.json
        """
        try:
            self.ckan_instance = portal_profile.CkanProfile(ckan_sys_profile)
            self.host = self.ckan_instance.HOST
            self.server_port = self.ckan_instance.PORT
            self.action_create = _PortalActionCreate(self.ckan_instance)
            self.action_get = _PortalActionGet(self.ckan_instance)
        except Exception as e:
            print(e)
            print('an error occurred during CKAN Portal object initialization')

    def package_publish(self, ckan_package, private=True):
        try:
            publish_dict = ckan_package
            package_name = publish_dict['name']
            publish_dict.update({"private": private})
            update = self.action_get.lookup_package_name(package_name)
            if update:
                db_log.info('Package ' + package_name + ' already exists: updating...')
                self.action_create.update_package(publish_dict)
            else:
                db_log.info('Creating new package ' + package_name + ':')
                self.action_create.create_package(publish_dict)
        except Exception as e:
            db_log.exception('Caught an error when uploading package ' + ckan_package['name'])
            db_log.debug(e)

    def servertest(self):
        time_out = 10
        args = socket.getaddrinfo(self.host, self.server_port, socket.AF_INET, socket.SOCK_STREAM)
        for family, socktype, proto, canonname, sockaddr in args:
            s = socket.socket(family, socktype, proto)
            s.settimeout(time_out)
            try:
                s.connect(sockaddr)
            except socket.error:
                db_log.debug('Server is DOWN')
                return False
            except time_out:
                db_log.debug('Server did not respond within timeout of '
                         + str(time_out) + ' seconds')
                return False
            else:
                db_log.info('Server is UP')
                s.close()
                return True


class _PortalActionGet:
    def __init__(self, profile):
        self.profile = profile

    def get_all_keywords(self):
        try:
            portal_request = requests.get(self.profile.PORTAL_CKAN_API_BASE + 'tag_list')
            portal_request.encoding = 'UTF-8'
            json_payload = json.loads(portal_request.text)
            if json_payload['success']:
                return json_payload['result']
            else:
                raise Exception('get_all_keywords returned False')
        except requests.HTTPError as e:
            print(e)
            print('\nhttp server error')
            print('an error occurred during keywords collecting')
            return None

    def get_organization(self, identifier, **kwargs):
        """
        Returns organization with specified identifier as datadict
        :param identifier:
        :return:
        """
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey, get_only=True)
        try:
            if kwargs:
                options = {'id': identifier}
                options.update(kwargs)
                organization = connection.call_action('organization_show', options)
            else:
                organization = connection.action.organization_show(id=identifier)
            return organization
        except ckanapi.errors.NotFound as e:
            db_log.info(e)
            db_log.info('No organization with this identifier')
        except ckanapi.remoteckan.HTTPError as e:
            db_log.debug(e.info)
            connection.close()
        except Exception as e:
            db_log.debug(e)
        finally:
            connection.close()

    def get_all_organizations(self):
        """
        Get list of all organization identifiers

        :return: list of strings
        """
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey, get_only=True)
        try:
            organizations = connection.action.organization_list()
            return organizations
        except ckanapi.errors.CKANAPIError as e:
            print(e)

    def dump_all_organizations(self, file_out=None):
        lab_ids = self.get_all_organizations()
        export = {'labs': []}
        for identifier in lab_ids:
            export['labs'].append(self.get_organization(identifier))
        if file_out is not None:
            with open(file_out, 'a', encoding="utf-8") as file:
                json.dump(export, file)
        return export

    def get_all_groups(self):
        """
        Get list of all group names

        :return: list of strings
        """
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey)
        try:
            organization = connection.action.group_list()
            return organization
        except ckanapi.errors.CKANAPIError as e:
            print(e)

    def get_group(self, name):
        """
        Returns group with specified name as datadict
        :param name: identifier of the group
        :return:
        """
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey)
        try:
            organization = connection.action.group_show(id=name)
            return organization
        except ckanapi.errors.NotFound as e:
            db_log.info(e)
            db_log.info('No group with this name')

    def get_all_tags(self):
        """
        Get list of all site's tags

        :return: list of strings
        """
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey)
        try:
            tags = connection.action.tag_list()
            return tags
        except ckanapi.errors.CKANAPIError as e:
            print(e)

    def get_datasets_by_organization(self, identifier):
        """
        returns a json package with all data publications from the specified lab
        (i.e. dataset of type lab with id identifier)
        :param identifier:
        :return:
        """
        try:
            result = self.package_search([{'organization': identifier}])
            # TODO: SOLR activation for scheming fields (IPackageController before_index)
            return result
        except Exception as e:
            print(e)
            return {"EXCEPTION": e}

    def lookup_package_name(self, name):
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey)
        try:
            # package = connection.action.package_show(id=name)
            connection.action.package_show(id=name)
            return True
        except ckanapi.errors.NotFound as e:
            db_log.info(e)
            return False

    def package_search(self, dict_list):
        """
        dict_list is a list of key-value pairs for searching, e.g. [{'field': 'value'}]
        to search across all field an asterisk (*) must be applied for the field name
        TODO: allow additional search parameters (e.g. fuzzy search or literals)
        """
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey)
        solr_query = ''
        for constraint in dict_list:
            key, value = list(constraint.items())[0]
            if key == '*':
                solr_query += '+' + value + ' '
            else:
                solr_query += '+' + key + ':' + value + ' '
        db_log.info('Searching for: ' + solr_query)
        packages = connection.action.package_search(q=solr_query)
        return packages


class _PortalActionCreate:

    def __init__(self, profile):
        """
        Creation. Requires a valid CKAN connection object.
        :param profile: connection profile
        """
        self.profile = profile
        self.instance = self.profile.PORTAL_URL
        # why is this not in use anymore? is it because ckan api expects a common path to tje api?
        # self.action_base = self.instance + self.profile.PORTAL_ACTION_BASE

    def create_package(self, data_dict):
        # package_name = data_dict['name']  # check whether name exists as key in dict!
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey)
        try:
            if "name" in data_dict:
                connection.call_action('package_create', data_dict)
            else:
                msg = 'No valid package name in dict'
                db_log.error(msg)
                raise Exception(msg)
        except ckanapi.errors.ValidationError as e:
            db_log.error(e)
        except ckanapi.errors.CKANAPIError as err:
            db_log.debug(data_dict)
            db_log.error(err)

    def update_package(self, data_dict):
        # package_name = data_dict['name']  # check whether name exists as key in dict!
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey)
        try:
            if "name" in data_dict:
                connection.call_action('package_update', data_dict)
            else:
                msg = 'No valid package name in dict'
                db_log.error(msg)
                raise Exception(msg)
        except ckanapi.errors.ValidationError as e:
            db_log.error(e)

    def create_organization(self, data_dict):
        """
        Create organization from given dictionary
        :param data_dict:
        :return:
        """
        # org_name = data_dict['name']  # check whether name exists as key in dict!
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey)
        try:
            if "name" in data_dict:
                connection.call_action('organization_create', data_dict)
            else:
                msg = 'No valid organization name in dict'
                db_log.error(msg)
                raise Exception(msg)
        except ckanapi.CKANAPIError as e:
            print(e)

    def create_group(self, data_dict):
        """
        Create group from given dictionary
        :param data_dict:
        :return:
        """
        # group_name = data_dict['name']  # check whether name exists as key in dict!
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey)
        try:
            if "name" in data_dict:
                connection.call_action('group_create', data_dict)
            else:
                msg = 'No valid group name in dict'
                db_log.error(msg)
                raise Exception(msg)
        except ckanapi.CKANAPIError as e:
            print(e)

    @staticmethod
    def generate_dataset_name(input_string):
        id_base_name = input_string
        id_base_name = id_base_name.replace(':', '')
        id_base_name = id_base_name.replace('/', '')
        id_base_name = id_base_name.lower()
        return hashlib.md5(id_base_name.encode()).hexdigest()

    def delete_dataset(self, identifier, private=True):
        current_ids = self.get_ids()
        dataset = {"id": identifier, "include_private": private}
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey)
        # connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.API_KEY)
        if identifier in current_ids:
            try:
                connection.call_action('package_delete', dataset)
                print(identifier + ' deleted from database')
            except ckanapi.ValidationError as e:
                db_log.info(e)
                raise
        else:
            print(identifier + ' not in database')

    def get_ids(self, private=True):
        connection = RemoteCKAN(self.profile.PORTAL_URL, self.profile.APIkey)
        full_result = connection.call_action('package_search', {"include_private": private})
        print('Number of ids: ')
        print(full_result['count'])
        id_list = []
        for entry in full_result['results']:
            id_list.append(entry['name'])
        return id_list
