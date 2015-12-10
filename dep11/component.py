#!/usr/bin/env python

"""
Contains the definition of a DEP-11 component.
"""

# Copyright (c) 2014 Abhishek Bhattacharjee <abhishek.bhattacharjee11@gmail.com>
# Copyright (c) 2014 Matthias Klumpp <mak@debian.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program.

import yaml
import datetime
from dep11.utils import str_enc_dec, build_cpt_global_id
from dep11.hints import HintSeverity, hint_tag_is_error
import logging as log
import hashlib

###########################################################################
DEP11_VERSION = "0.8"
time_str = str(datetime.date.today())
dep11_header_template = {
    "File": "DEP-11",
    "Version": DEP11_VERSION
}
###########################################################################

class DEP11YamlDumper(yaml.SafeDumper):
    """
    Custom YAML dumper, to ensure resulting YAML file can be read by
    all parsers (even the Java one)
    """
    def increase_indent(self, flow=False, indentless=False):
        return super(DEP11YamlDumper, self).increase_indent(flow, False)


def get_dep11_header(repo_name, suite_name, component_name, base_url, priority):
    """
    Build a DEP-11 header YAML document. This document must always be at the start of
    a valid DEP-11 YAML file.
    """
    head_dict = dep11_header_template

    origin = "%s-%s-%s" % (repo_name, suite_name, component_name)
    head_dict['Origin'] = origin.lower()
    head_dict['MediaBaseUrl'] = base_url
    if priority != 0:
        head_dict['Priority'] = priority

    return yaml.dump(head_dict, Dumper=DEP11YamlDumper,
                            default_flow_style=False, explicit_start=True,
                            explicit_end=False, width=200, indent=2)


def dict_to_dep11_yaml(d):
    return yaml.dump(d, Dumper=DEP11YamlDumper,
                    default_flow_style=False, explicit_start=True,
                    explicit_end=False, width=100, indent=2,
                    allow_unicode=True)


class IconSize:
    '''
    A simple type representing an icon size
    '''
    size = int()


    def __init__(self, size):
        if isinstance(size, str):
            self.set_from_string(size)
        else:
            self.size = size


    def __str__(self):
        return "%ix%i" % (self.size, self.size)


    def __int__(self):
        return self.size


    def set_from_string(self, s):
        wd, ht = s.split('x')
        if int(wd) != int(ht):
            log.warning("Processing asymetric icon.")
        self.size = int(wd)


    def __eq__(self, other):
        if type(other) is str:
            return str(self) == other
        if type(other) is IconSize:
            return self.size == other.size
        return self.size == other

    def __lt__(self, other):
        if type(other) is IconSize:
            return self.size < other.size
        return self.size < other

    def __gt__(self, other):
        if type(other) is IconSize:
            return self.size > other.size
        return self.size > other

    def __hash__(self):
        return self.size


class ProvidedItemType:
    '''
    Types supported as publicly provided interfaces. Used as keys in
    the 'Provides' field
    '''
    BINARY = 'binaries'
    LIBRARY = 'libraries'
    MIMETYPE = 'mimetypes'
    DBUS = 'dbus'
    PYTHON_2 = 'python2'
    PYTHON_3 = 'python3'
    FIRMWARE = 'firmware'
    CODEC = 'codecs'


class DEP11Component:
    '''
    Used to store the properties of component data. Used by MetadataExtractor
    '''

    def __init__(self, suitename, component, pkg, pkid=None):
        '''
        Used to set the properties to None.
        '''
        self._suitename = suitename
        self._component = component
        self._pkg = pkg
        self._pkid = pkid

        # properties
        self._hints = list()
        self._ignore = False
        self._srcdata_checksum = None
        self._global_id = None

        self._id = None
        self._type = None
        self._name = dict()
        self._categories = None
        self._icon = None
        self._summary = dict()
        self._description = None
        self._screenshots = None
        self._keywords = None
        self._archs = None
        self._provides = dict()
        self._url = None
        self._project_license = None
        self._project_group = None
        self._developer_name = dict()
        self._extends = list()
        self._compulsory_for_desktops = list()
        self._releases = list()
        self._languages = list()


    def add_hint(self, tag, params=dict()):
        if hint_tag_is_error(tag):
            self._ignore = True

        self._hints.append({'tag': tag, 'params': params})


    def has_ignore_reason(self):
        return self._ignore


    def get_hints_dict(self):
        if not self._hints:
            return None
        hdict = dict()
        # add some helpful data
        if self.cid:
            hdict['ID'] = self.cid
        if self.kind:
            hdict['Type'] = self.kind
        if self._pkg:
            hdict['Package'] = self._pkg
        if self._pkid:
            hdict['PackageID'] = self._pkid
        if self.has_ignore_reason():
            hdict['Ignored'] = True
        hdict['Hints'] = self._hints

        return hdict


    def get_hints_yaml(self):
        if not self._hints:
            return None
        return dict_to_dep11_yaml(self.get_hints_dict())


    def set_srcdata_checksum_from_data(self, data):
        b = bytes(data, 'utf-8')
        md5sum = hashlib.md5(b).hexdigest()
        self._srcdata_checksum = md5sum


    @property
    def srcdata_checksum(self):
        return self._srcdata_checksum

    @srcdata_checksum.setter
    def srcdata_checksum(self, val):
        self._srcdata_checksum = val
        self._global_id = None

    @property
    def global_id(self):
        """
        The global-id is used as a global, unique identifier for this component.
        Its primary usecase is to identify a media directory on the filesystem which is
        associated with this component.
        """
        if self._global_id:
            return self._global_id

        self._global_id = build_cpt_global_id(self._id, self.srcdata_checksum)
        return self._global_id

    @property
    def cid(self):
        return self._id

    @cid.setter
    def cid(self, val):
        self._id = val
        self._global_id = None

    @property
    def kind(self):
        return self._type

    @kind.setter
    def kind(self, val):
        self._type = val

    @property
    def pkgname(self):
        return self._pkg

    @property
    def pkid(self):
        return self._pkid

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        self._name = val

    @property
    def categories(self):
        return self._categories

    @categories.setter
    def categories(self, val):
        self._categories = val

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, val):
        self._icon = val

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, val):
        self._summary = val

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, val):
        self._description = val

    @property
    def screenshots(self):
        return self._screenshots

    @screenshots.setter
    def screenshots(self, val):
        self._screenshots = val

    @property
    def keywords(self):
        return self._keywords

    @keywords.setter
    def keywords(self, val):
        self._keywords = val

    @property
    def archs(self):
        return self._archs

    @archs.setter
    def archs(self, val):
        self._archs = val

    @property
    def provides(self):
        return self._provides

    @provides.setter
    def provides(self, val):
        self._provides = val

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, val):
        self._url = val

    @property
    def compulsory_for_desktops(self):
        return self._compulsory_for_desktops

    @compulsory_for_desktops.setter
    def compulsory_for_desktops(self, val):
        self._compulsory_for_desktops = val

    @property
    def project_license(self):
        return self._project_license

    @project_license.setter
    def project_license(self, val):
        self._project_license = val

    @property
    def project_group(self):
        return self._project_group

    @project_group.setter
    def project_group(self, val):
        self._project_group = val

    @property
    def developer_name(self):
        return self._developer_name

    @developer_name.setter
    def developer_name(self, val):
        self._developer_name = val

    @property
    def extends(self):
        return self._extends

    @extends.setter
    def extends(self, val):
        self._extends = val

    @property
    def releases(self):
        return self._releases

    @releases.setter
    def releases(self, val):
        self._releases = val


    def add_provided_item(self, kind, value):
        if kind not in self.provides.keys():
            self.provides[kind] = list()
        self.provides[kind].append(value)


    def _is_quoted(self, s):
        return (s.startswith("\"") and s.endswith("\"")) or (s.startswith("\'") and s.endswith("\'"))


    def _cleanup(self, d):
        '''
        Remove cruft locale, duplicates and extra encoding information
        '''
        if not d:
            return d

        if d.get('x-test'):
            d.pop('x-test')
        if d.get('xx'):
            d.pop('xx')

        unlocalized = d.get('C')
        if unlocalized:
            to_remove = []
            for k in list(d.keys()):
                val = d[k]
                # don't duplicate strings
                if val == unlocalized and k != 'C':
                    d.pop(k)
                    continue
                if self._is_quoted(val):
                    d[k] = val.strip("\"'")
                # should not specify encoding
                if k.endswith('.UTF-8'):
                    locale = k.strip('.UTF-8')
                    d.pop(k)
                    d[locale] = val
                    continue

        return d


    def _check_translated(self):
        '''
        Ensure each localized field has a translation template ('C') set.
        Some broken .desktop files do not properly set a template, and we don't want to return
        broken DEP-11 YAML because of broken upstream metadata.
        '''
        def check_for_template(field, id_str):
            if not field:
                return
            if not field.get('C'):
                self.add_hint("metainfo-localized-field-without-template", {'field_id': id_str})

        check_for_template(self.name, 'Name')
        check_for_template(self.summary, 'Summary')
        check_for_template(self.description, 'Description')
        check_for_template(self.developer_name, 'DeveloperName')
        if self.screenshots:
            for i, shot in enumerate(self.screenshots):
                caption = shot.get('caption')
                if caption:
                    check_for_template(self.developer_name, "Screenshots/%i/caption" % (i))


    def finalize_to_dict(self):
        '''
        Do sanity checks and finalization work, then serialize the component to
        a Python dict.
        '''

        # perform some cleanup work
        self.name = self._cleanup(self.name)
        self.summary = self._cleanup(self.summary)
        self.description = self._cleanup(self.description)
        self.developer_name = self._cleanup(self.developer_name)
        if self.screenshots:
            for shot in self.screenshots:
                caption = shot.get('caption')
                if caption:
                    shot['caption'] = self._cleanup(caption)

        # validate the basics (if we don't ignore this already)
        if not self.has_ignore_reason():
            if not self.cid:
                self.add_hint("metainfo-no-id")
            if not self.kind:
                self.add_hint("metainfo-no-type")
            if not self.name:
                self.add_hint("metainfo-no-name")
            if not self._pkg:
                self.add_hint("metainfo-no-package")
            if not self.summary:
                self.add_hint("metainfo-no-summary")
            # ensure translated elements have templates
            self._check_translated()

        d = dict()
        d['Package'] = str(self._pkg)
        if self.cid:
            d['ID'] = self.cid
        if self.kind:
            d['Type'] = self.kind

        # check if we need to print ignore information, instead
        # of exporting the software component
        if self.has_ignore_reason():
            d['Ignored'] = True
            return d

        if self.name:
            d['Name'] = self.name
        if self.summary:
            d['Summary'] = self.summary
        if self.categories:
            d['Categories'] = self.categories
        if self.description:
            d['Description'] = self.description
        if self.keywords:
            d['Keywords'] = self.keywords
        if self.screenshots:
            d['Screenshots'] = self.screenshots
        if self.archs:
            d['Architectures'] = self.archs
        if self.icon:
            d['Icon'] = {'cached': self.icon}
        if self.url:
            d['Url'] = self.url
        if self.provides:
            d['Provides'] = self.provides
        if self.project_license:
            d['ProjectLicense'] = self.project_license
        if self.project_group:
            d['ProjectGroup'] = self.project_group
        if self.developer_name:
            d['DeveloperName'] = self.developer_name
        if self.extends:
            d['Extends'] = self.extends
        if self.compulsory_for_desktops:
            d['CompulsoryForDesktops'] = self.compulsory_for_desktops
        if self.releases:
            d['Releases'] = self.releases
        return d


    def to_yaml_doc(self):
        return dict_to_dep11_yaml(self.finalize_to_dict())
