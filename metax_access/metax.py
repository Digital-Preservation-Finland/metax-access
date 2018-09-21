# encoding=utf8
"""Metax interface class."""

import lxml.etree
from requests import get, post, patch
from requests.auth import HTTPBasicAuth
from flask import abort
import requests

DS_STATE_INITIALIZED = 0
DS_STATE_PROPOSED_FOR_DIGITAL_PRESERVATION = 10
DS_STATE_TECHNICAL_METADATA_GENERATED = 20
DS_STATE_TECHNICAL_METADATA_GENERATION_FAILED = 30
DS_STATE_INVALID_METADATA = 40
DS_STATE_METADATA_VALIDATION_FAILED = 50
DS_STATE_VALIDATED_METADATA_UPDATED = 60
DS_STATE_VALID_METADATA = 70
DS_STATE_METADATA_CONFIRMED = 75
DS_STATE_ACCEPTED_TO_DIGITAL_PRESERVATION = 80
DS_STATE_IN_PACKAGING_SERVICE = 90
DS_STATE_PACKAGING_FAILED = 100
DS_STATE_SIP_SENT_TO_INGESTION_IN_DPRES_SERVICE = 110
DS_STATE_IN_DIGITAL_PRESERVATION = 120
DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE = 130
DS_STATE_IN_DISSEMINATION = 140

DS_STATE_ALL_STATES = (
    DS_STATE_INITIALIZED, DS_STATE_PROPOSED_FOR_DIGITAL_PRESERVATION,
    DS_STATE_TECHNICAL_METADATA_GENERATED,
    DS_STATE_TECHNICAL_METADATA_GENERATION_FAILED,
    DS_STATE_INVALID_METADATA, DS_STATE_METADATA_VALIDATION_FAILED,
    DS_STATE_VALIDATED_METADATA_UPDATED, DS_STATE_VALID_METADATA,
    DS_STATE_METADATA_CONFIRMED, DS_STATE_ACCEPTED_TO_DIGITAL_PRESERVATION,
    DS_STATE_IN_PACKAGING_SERVICE, DS_STATE_PACKAGING_FAILED,
    DS_STATE_SIP_SENT_TO_INGESTION_IN_DPRES_SERVICE,
    DS_STATE_IN_DIGITAL_PRESERVATION,
    DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
    DS_STATE_IN_DISSEMINATION
)


class MetaxConnectionError(Exception):
    """Exception raised when Metax is not available"""
    message = 'No connection to Metax'


class DatasetNotFoundError(Exception):
    """Exception raised when dataset is not found from metax"""


class ContractNotFoundError(Exception):
    """Exception raised when contract is not found from metax"""


class DataCatalogNotFoundError(Exception):
    """Exception raised when contract is not found from metax"""


class Metax(object):
    """Get metadata from metax as dict object."""

    def __init__(self, metax_url, metax_user, metax_password):
        """ Initialize Metax object.

        :metax_url: Metax url
        :user: Metax user
        :password: Metax user password
        """
        self.metax_url = metax_url
        self.username = metax_user
        self.password = metax_password
        self.baseurl = self.metax_url + '/rest/v1/'
        self.elasticsearch_url = self.metax_url + '/es/'

    def get_datasets(self, states=None,
                     limit="1000000",
                     offset="0",
                     pas_filter=None,
                     org_filter=None):
        """Gets the metadata of datasets from METAX.

        :returns: The data from METAX as json.
        """
        if states is None:
            states = ','.join(str(state) for state in DS_STATE_ALL_STATES)

        pas_filter_str = ''
        if pas_filter is not None:
            pas_filter_str += '&pas_filter=' + pas_filter
        org_filter_str = ''
        if org_filter is not None:
            org_filter_str += '&metadata_owner_org=' + org_filter
        url = "".join([self.baseurl,
                       "datasets", "?state=", states, "&limit=",
                       limit, "&offset=", offset, pas_filter_str,
                       org_filter_str])
        response = _do_get_request(url, HTTPBasicAuth(self.username,
                                                      self.password))
        if response.status_code == 404:
            raise DatasetNotFoundError
        response.raise_for_status()
        return response.json()

    def get_contracts(self, limit="1000000", offset="0", org_filter=None):
        """Gets the data for contracts list from METAX.

        :returns: The data from METAX as json.
        """
        org_filter_str = ''
        if org_filter is not None:
            org_filter_str += '&organization=' + org_filter
        url = "".join([self.baseurl, 'contracts?limit=', limit,
                       '&offset=', offset,
                       org_filter_str])
        response = _do_get_request(url, HTTPBasicAuth(self.username,
                                                      self.password))
        if response.status_code == 404:
            raise ContractNotFoundError
        response.raise_for_status()
        return response.json()

    def get_contract(self, pid):
        """Gets the data of a contract from METAX.

        :pid: Identifier of the contract
        :returns: The data from METAX as json.
        """
        url = "".join([self.baseurl, "contracts/", pid])
        response = _do_get_request(url, HTTPBasicAuth(self.username,
                                                      self.password))
        if response.status_code == 404:
            raise ContractNotFoundError
        response.raise_for_status()
        return response.json()

    def get_dataset(self, dataset_id):
        """Get dataset metadata from Metax.

        :dataset_id: ID number of object
        :returns: dataset as json
        """
        url = self.baseurl + 'datasets' + '/' + dataset_id

        response = _do_get_request(url, HTTPBasicAuth(self.username,
                                                      self.password))

        if response.status_code == 404:
            raise DatasetNotFoundError(
                "Could not find metadata for dataset: %s" % dataset_id
            )
        response.raise_for_status()
        return response.json()

    def get_datacatalog(self, catalog_id):
        """Gets the metadata of a datacatalog from METAX.

        :catalog_id: Identifier of the dataset
        :returns: The data from METAX as json.
        """
        url = "".join([self.baseurl, "datacatalogs/", catalog_id])
        response = _do_get_request(url, HTTPBasicAuth(self.username,
                                                      self.password))
        if response.status_code == 404:
            raise DataCatalogNotFoundError
        response.raise_for_status()
        return response.json()

    def set_contract_for_dataset(self, dataset_id, contract_id,
                                 contract_identifier):
        """Sends an update request of a dataset to METAX.

        :dataset_id: Identifier of the dataset
        :contract_id: id attribute of the contract.
        :contract_identifier: identifier attribute of the contract.
        """
        if contract_id != 0:
            data = {'contract':
                    {'id': contract_id,
                     'identifier': contract_identifier
                     }
                    }
        else:
            data = {'contract': None}

        url = "".join([self.baseurl, "datasets/", dataset_id])
        r = _do_patch_request(url, data, HTTPBasicAuth(self.username,
                                                       self.password))
        r.raise_for_status()

    def get_dataset_filetypes(self, dataset_id):
        """Gets the unique triples of file_format, format_version, encoding
        of the files in dataset.

        :dataset_id: id of the dataset
        """
        temp_types = set()
        mime_types = []
        url = "".join([self.baseurl,
                       "datasets/", str(dataset_id), '/files'])
        r = _do_get_request(url, HTTPBasicAuth(self.username,
                                               self.password))
        if r.status_code == 404:
            abort(404)
        elif r.status_code >= 300:
            if 'detail' in r.json():
                abort(500, r.json()['detail'])
            else:
                abort(500)
        for fil in r.json():
            file_format = ''
            format_version = ''
            encoding = ''
            if 'file_format' in fil['file_characteristics']:
                file_format = fil['file_characteristics']['file_format']
            if 'format_version' in fil['file_characteristics']:
                format_version = fil['file_characteristics']['format_version']
            if 'encoding' in fil['file_characteristics']:
                encoding = fil['file_characteristics']['encoding']
            if len(file_format) > 0:
                temp_types.add(file_format + '||' + format_version +
                               '||' + encoding)
        for temp_type in temp_types:
            attrs = str(temp_type).split('||')
            mime_types.append({'file_format': attrs[0],
                               'format_version': attrs[1],
                               'encoding': attrs[2]})
        file_types = {
            'total_count': len(mime_types),
            'filetypes': mime_types
        }
        return file_types

    def get_contract_datasets(self, pid):
        """Gets the datasets of a contract from METAX.

        :pid: Identifier of the contract
        :returns: The data from METAX as json.
        """
        url = "".join([self.baseurl, "contracts/", str(pid), '/datasets'])
        response = _do_get_request(url, HTTPBasicAuth(self.username,
                                                      self.password))
        response.raise_for_status()
        return response.json()

    def get_file(self, file_id):
        """Get file metadata from Metax.

        :file_id: ID number of object
        :returns: dict
        """
        url = self.baseurl + 'files' + '/' + file_id

        response = _do_get_request(url, HTTPBasicAuth(self.username,
                                                      self.password))

        if response.status_code == 404:
            raise Exception("Could not find metadata for file: %s" % file_id)
        response.raise_for_status()
        return response.json()

    def get_xml(self, entity_url, entity_id):
        """Get xml data of dataset, contract or file with id from Metax.

        :entity_url: "datasets", "contracts" or "files"
        :entity_id: ID number of object
        :returns: dict with XML namespace strings as keys and
                  lxml.etree.ElementTree objects as values
        """
        # Init result dict
        xml_dict = {}

        # Get list of xml namespaces
        ns_key_url = self.baseurl + entity_url + '/' + entity_id + '/xml'
        response = _do_get_request(ns_key_url, HTTPBasicAuth(self.username,
                                                             self.password))
        if response.status_code == 404:
            raise Exception("Could not retrieve list of additional metadata "
                            "XML for dataset %s: %s" % (entity_id, ns_key_url))
        response.raise_for_status()
        ns_key_list = response.json()

        # For each listed namespace, download the xml, create ElementTree, and
        # add it to result dict
        for ns_key in ns_key_list:
            query = '?namespace=' + ns_key
            response = _do_get_request(ns_key_url + query,
                                       HTTPBasicAuth(self.username,
                                                     self.password))
            if not response.status_code == 200:
                raise Exception("Could not retrieve additional metadata XML "
                                "for dataset %s: %s" % (entity_id,
                                                        ns_key_url + query))
            # pylint: disable=no-member
            xml_dict[ns_key] = lxml.etree.fromstring(response.content)\
                .getroottree()

        return xml_dict

    def set_xml(self, file_id, xml_element):
        """Add xml data to a file with in Metax.

        :file_id: ID of file
        :xml_element: XML Element
        :returns: None
        """
        # Read namespace from XML element
        namespace = \
            xml_element.attrib[
                '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'
            ].split()[0]

        # Convert XML element to string
        data = lxml.etree.tostring(xml_element, pretty_print=True)

        # POST to Metax
        url = '%sfiles/%s/xml?namespace=%s' % (self.baseurl,
                                               file_id,
                                               namespace)
        headers = {'Content-Type': 'application/xml'}
        response = post(url,
                        data=data,
                        headers=headers,
                        auth=HTTPBasicAuth(self.username,
                                           self.password))

        response.raise_for_status()
        if response.status_code != 201:
            raise requests.exceptions.HTTPError(
                "Expected 201 Created, got {} instead".format(
                    response.status_code)
            )

    def get_elasticsearchdata(self):
        """Get elastic search data from Metax

        :returns: dict"""
        url = self.elasticsearch_url + "reference_data/use_category/_search?"\
                                       "pretty&size=100"
        response = _do_get_request(url)

        if response.status_code == 404:
            raise Exception("Could not find elastic search data.")
        response.raise_for_status()
        return response.json()

    def set_preservation_state(self, dataset_id, state, user_description=None,
                               system_description=None):
        """Set values of attributes `preservation_state` and
        `preservation_state_description` for dataset in Metax

        0 = Initialized
        10 = Proposed for digital preservation
        20 = Technical metadata generated
        30 = Technical metadata generation failed
        40 = Invalid metadata
        50 = Metadata validation failed
        60 = Validated metadata updated
        70 = Valid metadata
        80 = Accepted to digital preservation
        90 = in packaging service
        100 = Packaging failed
        110 = SIP sent to ingestion in digital preservation service
        120 = in digital preservation
        130 = Rejected in digital preservation service
        140 = in dissemination

        :dataset_id: The ID of dataset in Metax
        :state (integer): The value for `preservation_state`
        :description (string): The value for `preservation_system_description`
        :returns: None

        """
        url = self.baseurl + 'datasets/' + dataset_id

        data = {"preservation_state": state}
        if user_description is not None:
            data["preservation_reason_description"] = user_description
        if system_description is not None:
            data["preservation_description"] = system_description
        response = patch(
            url,
            json=data,
            auth=HTTPBasicAuth(self.username, self.password)
        )
        if response.status_code == 503:
            raise MetaxConnectionError

        # Raise exception if request fails
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            raise Exception(response.json())

    def set_file_characteristics(self, file_id, file_characteristics):
        """Updates `file_characteristics` attribute for a file in Metax.

        :file_id: ID of file
        :file_characteristics: Dict object that contains new data for
                               `file_characteristics` attribute
        :returns: None
        """

        url = self.baseurl + 'files/' + file_id
        data = {"file_characteristics": file_characteristics}

        response = requests.patch(
            url,
            json=data,
            auth=HTTPBasicAuth(self.username, self.password)
        )

        if response.status_code == 503:
            raise MetaxConnectionError

        # Raise exception if request fails
        response.raise_for_status()

    def get_datacite(self, dataset_id):
        """Get descriptive metadata in datacite xml format.

        :dataset_id: ID of dataset
        :returns: Datacite XML (lxml.etree.ElementTree object)
        """
        url = "%sdatasets/%s?dataset_format=datacite" % (self.baseurl,
                                                         dataset_id)
        response = _do_get_request(url, HTTPBasicAuth(self.username,
                                                      self.password))

        if response.status_code == 404:
            raise Exception("Could not find descriptive metadata.")
        response.raise_for_status()

        # pylint: disable=no-member
        return lxml.etree.fromstring(response.content).getroottree()

    def get_dataset_files(self, dataset_id):
        """Get file metadata of dataset from Metax.

        :dataset_id: ID number of object
        :returns: dict"""
        url = self.baseurl + 'datasets/' + dataset_id + '/files'

        response = _do_get_request(url, HTTPBasicAuth(self.username,
                                                      self.password))

        if response.status_code == 404:
            raise Exception("Could not find dataset files metadata.")
        response.raise_for_status()

        return response.json()


def _do_get_request(url, auth=None):
    """Wrapper function for requests.get() function. Raises
    MetaxConnectionError if status code is 503 (Service unavailable

    :returns: requests response
    """
    response = get(url, auth=auth)
    if response.status_code == 503:
        raise MetaxConnectionError
    return response


def _do_patch_request(url, data, auth=None):
    """Wrapper function for requests.patch() function. Raises
    MetaxConnectionError if status code is 503 (Service unavailable

    :returns: requests response
    """
    response = patch(url, json=data, auth=auth)
    if response.status_code == 503:
        raise MetaxConnectionError
    return response
