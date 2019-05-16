# encoding=utf8
"""Metax interface class."""

import lxml.etree
from requests import get, post, patch
from requests.auth import HTTPBasicAuth
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


class MetaxError(Exception):
    """Generic invalid usage Exception"""

    def __init__(self, message="Metax error", status_code=400, payload=None):
        super(MetaxError, self).__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Return dict with the error message"""
        return_val = dict(self.payload or ())
        return_val['error'] = self.message
        return_val['code'] = self.status_code
        return return_val


class MetaxConnectionError(MetaxError):
    """Exception raised when Metax is not available"""
    def __init__(self):
        super(MetaxConnectionError, self).__init__(
            "No connection to Metax", 503
        )


class DatasetNotFoundError(MetaxError):
    """Exception raised when dataset is not found from metax"""
    def __init__(self, message="Dataset not found"):
        super(DatasetNotFoundError, self).__init__(message, 404)


class ContractNotFoundError(MetaxError):
    """Exception raised when contract is not found from metax"""
    def __init__(self):
        super(ContractNotFoundError, self).__init__("Contract not found", 404)


class DataCatalogNotFoundError(MetaxError):
    """Exception raised when contract is not found from metax"""
    def __init__(self):
        super(DataCatalogNotFoundError, self).__init__(
            "Datacatalog not found", 404
        )


class DirectoryNotFoundError(MetaxError):
    """Exception raised when directory is not found from metax"""
    def __init__(self):
        super(DirectoryNotFoundError, self).__init__(
            'Directory not found', 404
        )


class DataciteGenerationError(MetaxError):
    """Exception raised when Metax returned 400 for datacite"""
    def __init__(self, message="Datacite generation failed in Metax",
                 status_code=400):
        super(DataciteGenerationError, self).__init__(message, status_code)


# pylint: disable=too-many-public-methods
class Metax(object):
    """Get metadata from metax as dict object."""

    def __init__(self, metax_url, metax_user, metax_password, verify=True):
        """ Initialize Metax object.

        :param metax_url: Metax url
        :param user: Metax user
        :param password: Metax user password
        """
        self.username = metax_user
        self.password = metax_password
        self.baseurl = metax_url + '/rest/v1/'
        self.elasticsearch_url = metax_url + '/es/'
        self.rpcurl = metax_url + '/rpc'
        self.verify = verify

    # pylint: disable=too-many-arguments
    def get_datasets(self, states=None,
                     limit="1000000",
                     offset="0",
                     pas_filter=None,
                     org_filter=None,
                     ordering=None):
        """Gets the metadata of datasets from Metax.

        :param str states: string containing dataset preservation state values
        e.g "10,20" for filtering
        :param str limit: max number of datasets to be returned
        :param str offset: offset for paging
        :param str pas_filter: string for filtering datasets, Used for the
                               following attributes in metax:
                                   1. research_dataset['title']
                                   2. research_dataset['curator']['name']
                                   3. contract['contract_json']['title']
        :param str org_filter: string for filtering datasets based on
                               research_dataset=>metadata_owner_org attribute
                               value
        :param str ordering: metax dataset attribute for sorting datasets
                             e.g "preservation_state"
        :returns: datasets from Metax as json.
        """
        if states is None:
            states = ','.join(str(state) for state in DS_STATE_ALL_STATES)

        pas_filter_str = ''
        if pas_filter is not None:
            pas_filter_str += '&pas_filter=' + pas_filter
        org_filter_str = ''
        if org_filter is not None:
            org_filter_str += '&metadata_owner_org=' + org_filter
        ordering_str = ''
        if ordering is not None:
            ordering_str += '&ordering=' + ordering
        url = "".join([self.baseurl,
                       "datasets", "?state=", states, "&limit=",
                       limit, "&offset=", offset, pas_filter_str,
                       org_filter_str, ordering_str])
        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))
        if response.status_code == 404:
            raise DatasetNotFoundError
        response.raise_for_status()
        return response.json()

    def get_contracts(self, limit="1000000", offset="0", org_filter=None):
        """Gets the data for contracts list from Metax.

        :param str limit: max number of contracts to be returned
        :param str offset: offset for paging
        :param str org_filter: string for filtering contracts based on
                               contract['contract_json']['organization']
                               ['organization_identifier'] attribute value
        :returns: contracts from Metax as json.
        """
        org_filter_str = ''
        if org_filter is not None:
            org_filter_str += '&organization=' + org_filter
        url = "".join([self.baseurl, 'contracts?limit=', limit,
                       '&offset=', offset,
                       org_filter_str])
        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))
        if response.status_code == 404:
            raise ContractNotFoundError
        response.raise_for_status()
        return response.json()

    def get_contract(self, pid):
        """Gets the contract data from Metax.

        :param str pid: id or ientifier attribute of contract
        :returns: The contract from Metax as json.
        """
        url = "".join([self.baseurl, "contracts/", pid])
        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))
        if response.status_code == 404:
            raise ContractNotFoundError
        response.raise_for_status()
        return response.json()

    def get_dataset(self, dataset_id):
        """Get dataset metadata from Metax.

        :param str dataset_id: id or identifier attribute of dataset
        :returns: dataset as json
        """
        url = self.baseurl + 'datasets' + '/' + dataset_id

        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))

        if response.status_code == 404:
            raise DatasetNotFoundError(
                message="Could not find metadata for dataset: %s" % dataset_id
            )
        response.raise_for_status()
        return response.json()

    def get_datacatalog(self, catalog_id):
        """Gets the metadata of a datacatalog from Metax.

        :param str catalog_id: id or identifier attribute of the datacatalog
        :returns: The datacatalog as json.
        """
        url = "".join([self.baseurl, "datacatalogs/", catalog_id])
        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))
        if response.status_code == 404:
            raise DataCatalogNotFoundError
        response.raise_for_status()
        return response.json()

    def set_contract_for_dataset(self, dataset_id, contract_id,
                                 contract_identifier):
        """Sets a contract for a dataset.

        :param str dataset_id: id or identifier of the dataset
        :param str contract_id: id attribute of the contract.
        :param str contract_identifier: identifier attribute of the contract.
        :returns:
        """
        if contract_id != 0:
            data = {'contract': {
                'id': contract_id,
                'identifier': contract_identifier
            }}
        else:
            data = {'contract': None}

        url = "".join([self.baseurl, "datasets/", dataset_id])
        response = self._do_patch_request(url, data,
                                          HTTPBasicAuth(self.username,
                                                        self.password))
        response.raise_for_status()

    def get_dataset_filetypes(self, dataset_id):
        """Gets the unique triples of file_format, format_version, encoding
        of the files in dataset.

        :param str dataset_id: id or identifier of the dataset
        :returns dict:
                  {
                      'total_count': len(filetypes),
                      'filetypes': [{'file_format': <format>,
                                     'format_version': <version>,
                                     'encoding': <encoding>}]
                  }
        """
        temp_types = set()
        mime_types = []
        url = "".join([self.baseurl,
                       "datasets/", str(dataset_id), '/files'])
        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))
        if response.status_code == 404:
            raise DatasetNotFoundError
        elif response.status_code >= 300:
            response.status_code = 500
            if 'detail' in response.json():
                response.reason = response.json()['detail']
                response.raise_for_status()
            else:
                response.raise_for_status()
        for fil in response.json():
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
        """Gets the datasets of a contract from Metax.

        :param str pid: id or identifier attribute of contract
        :returns: The datasets from Metax as json.
        """
        url = "".join([self.baseurl, "contracts/", str(pid), '/datasets'])
        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))
        response.raise_for_status()
        return response.json()

    def get_file(self, file_id):
        """Get file metadata from Metax.

        :param str file_id: id or identifier attribute of file
        :returns: file metadata as json
        """
        url = self.baseurl + 'files' + '/' + file_id

        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))

        if response.status_code == 404:
            raise Exception("Could not find metadata for file: %s" % file_id)
        response.raise_for_status()
        return response.json()

    def get_files(self, project):
        """Get all files of a given project

        :param project: project id
        :returns: list of files
        """
        files = []
        url = self.baseurl + 'files/?limit=10000&project_identifier=' + project

        # GET 10000 files every iteration until all files are read
        while url is not None:
            response = self._do_get_request(
                url, HTTPBasicAuth(self.username, self.password)
            ).json()
            url = response["next"]
            files.extend(response["results"])

        return files

    def get_files_dict(self, project):
        """GET all the files of a given project as a dict
        {file_path: {"id": id, "identifier": identifier}}

        :param project: project id
        :returns: Dict of all the files of a given project
        """
        files = self.get_files(project)

        file_dict = {}
        for _file in files:
            file_dict[_file["file_path"]] = {
                "id": _file["id"],
                "identifier": _file["identifier"]
            }

        return file_dict

    def get_xml(self, entity_url, entity_id):
        """Get xml data of dataset, contract or file with id from Metax.

        :param str entity_url: "datasets", "contracts" or "files"
        :param str entity_id: id or identifier attribute of object
        :returns: dict with XML namespace strings as keys and
                  lxml.etree.ElementTree objects as values
        """
        # Init result dict
        xml_dict = {}

        # Get list of xml namespaces
        ns_key_url = self.baseurl + entity_url + '/' + entity_id + '/xml'
        response = self._do_get_request(ns_key_url,
                                        HTTPBasicAuth(self.username,
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
            response = self._do_get_request(ns_key_url + query,
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

        :param str file_id: id or identifier attribute of file
        :param str xml_element: XML Element
        :returns bool: True: xml data set. False: xml data already set
        """
        # Read namespace from XML element
        namespace = \
            xml_element.attrib[
                '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'
            ].split()[0]
        xmls = self.get_xml('files', file_id)
        if namespace not in xmls:
            # Convert XML element to string
            # pylint: disable=no-member
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
                                               self.password),
                            verify=self.verify)
            if response.status_code != 201:
                raise requests.exceptions.HTTPError(
                    "Expected 201 Created, got {} instead".format(
                        response.status_code))
            return True
        else:
            return False

    def get_elasticsearchdata(self):
        """Get elastic search data from Metax

        :returns: json
        """
        url = self.elasticsearch_url + "reference_data/use_category/_search?"\
                                       "pretty&size=100"
        response = self._do_get_request(url)

        if response.status_code == 404:
            raise Exception("Could not find elastic search data.")
        response.raise_for_status()
        return response.json()

    def set_preservation_state(self, dataset_id, state=None,
                               user_description=None,
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
        75 = Metadata confirmed
        80 = Accepted to digital preservation
        90 = in packaging service
        100 = Packaging failed
        110 = SIP sent to ingestion in digital preservation service
        120 = in digital preservation
        130 = Rejected in digital preservation service
        140 = in dissemination

        :param str dataset_id: id or identifier attribute of dataset in Metax
        :param int state: The value for `preservation_state`
        :param str user_description: The value for
                                     `preservation_reason_description`
        :param str system_description: The value for `preservation_description`
        :returns: ``None``
        """
        url = self.baseurl + 'datasets/' + dataset_id
        data = {}
        if state is not None:
            data = {"preservation_state": state}
        if user_description is not None:
            data["preservation_reason_description"] = user_description
        if system_description is not None:
            data["preservation_description"] = system_description
        response = self._do_patch_request(url, data,
                                          HTTPBasicAuth(self.username,
                                                        self.password))
        # Raise exception if request fails
        response.raise_for_status()

    def set_file_characteristics(self, file_id, file_characteristics):
        """Updates `file_characteristics` attribute for a file in Metax.

        :param str file_id: id or identifier attribute of file
        :param dict file_characteristics: Dict object that contains new data
                                          for `file_characteristics` attribute
        :returns: ``None``
        """

        url = self.baseurl + 'files/' + file_id
        data = {"file_characteristics": file_characteristics}

        response = self._do_patch_request(url, data,
                                          HTTPBasicAuth(self.username,
                                                        self.password))
        # Raise exception if request fails
        response.raise_for_status()

    def set_preservation_id(self, dataset_id):
        """Generates preservation_identifier for dataset with identifier
        dataset_identifier. If preservation_identifier already exists, does
        nothing.

        :param dataset_id: id or identifier attribute of dataset
        :returns: ``None``
        """
        dataset_identifier = self.get_dataset(dataset_id)["identifier"]
        rpc_url = "%s/datasets/set_preservation_identifier?identifier=%s" % (
            self.rpcurl, dataset_identifier
        )

        response = self._do_post_request(
            rpc_url, auth=HTTPBasicAuth(self.username, self.password)
        )

        if response.status_code == 400:
            detail = _get_detailed_error(
                response,
                default='Assigning preservation identifier failed in Metax'
            )
            raise DataciteGenerationError(detail)
        elif response.status_code == 404:
            raise DatasetNotFoundError

        response.raise_for_status()

    def get_datacite(self, dataset_id):
        """Get descriptive metadata in datacite xml format.

        :param dataset_id: id or identifier attribute of dataset
        :returns: Datacite XML (lxml.etree.ElementTree object)
        """
        self.set_preservation_id(dataset_id)

        url = "%sdatasets/%s?dataset_format=datacite" % (self.baseurl,
                                                         dataset_id)
        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))

        if response.status_code == 400:
            detail = _get_detailed_error(
                response,
                default='Datacite generation failed in Metax'
            )
            raise DataciteGenerationError(detail)
        elif response.status_code == 404:
            raise DatasetNotFoundError

        response.raise_for_status()

        # pylint: disable=no-member
        return lxml.etree.fromstring(response.content).getroottree()

    def get_dataset_files(self, dataset_id):
        """Get files metadata of dataset Metax.

        :param str dataset_id: id or identifier attribute of dataset
        :returns: metadata of dataset files as json
        """
        url = self.baseurl + 'datasets/' + dataset_id + '/files'

        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))

        if response.status_code == 404:
            raise Exception("Could not find dataset files metadata.")
        response.raise_for_status()

        return response.json()

    def get_file_datasets(self, file_id):
        """GET a list of datasets associated with file_id

        :param file_id: File identifier
        :returns: List of datasets associated with file_id
        """
        url = self.baseurl + 'files/datasets'
        response = requests.post(
            url,
            json=[file_id],
            auth=HTTPBasicAuth(self.username, self.password),
            verify=self.verify
        )

        if response.status_code == 404:
            raise Exception("Could not find file metadata")
        response.raise_for_status()

        return response.json()

    def delete_file(self, file_id):
        """Delete metadata of a file.

        :param file_id: file identifier
        :returns: requests Response
        """
        url = self.baseurl + 'files/' + file_id
        response = requests.delete(
            url=url,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=self.verify
        )
        return response

    def delete_files(self, file_id_list):
        """Delete file metadata from Metax.

        :param file_id_list: List of ids to delete from Metax
        :returns: HTTP response returned by Metax
        """
        url = self.baseurl + 'files'
        response = requests.delete(
            url=url,
            json=file_id_list,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=self.verify
        )
        return response

    def delete_dataset(self, dataset_id):
        """Delete metadata of dataset.

        :param dataset_id: dataset identifier
        :returns: requests Response
        """
        url = self.baseurl + 'datasets/' + dataset_id
        response = requests.delete(
            url=url,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=self.verify
        )
        return response

    def delete_dataset_files(self, dataset_id):
        """Delete metadata of files of a dataset.

        :param dataset_id: dataset identifier
        :returns: list of requests Responses
        """
        dataset_files = self.get_dataset_files(dataset_id)

        for file_ in dataset_files:
            self.delete_file(file_['identifier'])

    def post_file(self, metadata):
        """Post file metadata.

        :param metadata: file metadata dictionary
        :returns: requests Response
        """
        url = self.baseurl + 'files/'
        response = requests.post(
            url=url,
            json=metadata,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=self.verify
        )
        return response

    def post_dataset(self, metadata):
        """Post dataset metadata.

        :param metadata: dataset metadata dictionary
        :returns: requests Response
        """
        url = self.baseurl + 'datasets/'
        response = requests.post(
            url, json=metadata,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=self.verify
        )
        return response

    def post_contract(self, metadata):
        """Post contract metadata.

        :param metadata: contract metadata dictionary
        :returns: requests Response
        """
        url = self.baseurl + 'contracts/'
        response = requests.post(
            url, json=metadata,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=self.verify
        )
        return response

    def delete_contract(self, contract_id):
        """Delete metadata of contract.

        :param dataset_id: contract identifier
        :returns: requests Response
        """
        url = self.baseurl + 'contracts/' + contract_id
        response = requests.delete(
            url=url,
            auth=HTTPBasicAuth(self.username, self.password),
            verify=self.verify
        )
        return response

    def get_directory_files(self, directory_identifier):
        """Get files of the directory.

        :param str directory_identifier: identifier attribute of directory
        :returns: directory files as json
        """
        url = self.baseurl + 'directories/' + directory_identifier + '/files'

        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))

        if response.status_code == 404:
            raise DirectoryNotFoundError
        response.raise_for_status()

        return response.json()

    def get_directory(self, directory_identifier):
        """Gets directory.

        :param str directory_identifier: identifier attribute of directory
        :returns: directory
        """
        url = self.baseurl + 'directories/' + directory_identifier

        response = self._do_get_request(url, HTTPBasicAuth(self.username,
                                                           self.password))

        if response.status_code == 404:
            raise DirectoryNotFoundError
        response.raise_for_status()

        return response.json()

    def _do_get_request(self, url, auth=None):
        """Wrapper function for requests.get() function. Raises
        MetaxConnectionError if status code is 503 (Service unavailable)

        :returns: requests response
        """
        response = get(url, auth=auth, verify=self.verify)
        if response.status_code == 503:
            raise MetaxConnectionError
        return response

    def _do_patch_request(self, url, data, auth=None):
        """Wrapper function for requests.patch() function. Raises
        MetaxConnectionError if status code is 503 (Service unavailable

        :returns: requests response
        """
        response = patch(url, json=data, auth=auth, verify=self.verify)
        if response.status_code == 503:
            raise MetaxConnectionError
        return response

    def _do_post_request(self, url, data=None, auth=None):
        """Wrapper function for requests.patch() function. Raises
        MetaxConnectionError if status code is 503 (Service unavailable

        :returns: requests response
        """
        response = post(url, json=data, auth=auth, verify=self.verify)
        if response.status_code == 503:
            raise MetaxConnectionError
        return response


def _get_detailed_error(response, default="Metax error"):
    try:
        response_json = response.json()
        detail = response_json['detail']
    except (ValueError, KeyError):
        detail = default
    return detail
