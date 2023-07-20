"""Metax interface class."""
import copy
import logging
import re

import lxml.etree
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

DS_STATE_INITIALIZED = 0
DS_STATE_PROPOSED_FOR_DIGITAL_PRESERVATION = 10
DS_STATE_TECHNICAL_METADATA_GENERATED = 20
DS_STATE_TECHNICAL_METADATA_GENERATION_FAILED = 30
DS_STATE_INVALID_METADATA = 40
DS_STATE_METADATA_VALIDATION_FAILED = 50
DS_STATE_VALIDATED_METADATA_UPDATED = 60
DS_STATE_VALIDATING_METADATA = 65
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
    DS_STATE_INITIALIZED,
    DS_STATE_PROPOSED_FOR_DIGITAL_PRESERVATION,
    DS_STATE_TECHNICAL_METADATA_GENERATED,
    DS_STATE_TECHNICAL_METADATA_GENERATION_FAILED,
    DS_STATE_INVALID_METADATA,
    DS_STATE_METADATA_VALIDATION_FAILED,
    DS_STATE_VALIDATED_METADATA_UPDATED,
    DS_STATE_VALIDATING_METADATA,
    DS_STATE_VALID_METADATA,
    DS_STATE_METADATA_CONFIRMED,
    DS_STATE_ACCEPTED_TO_DIGITAL_PRESERVATION,
    DS_STATE_IN_PACKAGING_SERVICE,
    DS_STATE_PACKAGING_FAILED,
    DS_STATE_SIP_SENT_TO_INGESTION_IN_DPRES_SERVICE,
    DS_STATE_IN_DIGITAL_PRESERVATION,
    DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
    DS_STATE_IN_DISSEMINATION
)


class MetaxError(Exception):
    """Generic invalid usage Exception."""

    def __init__(self, message="Metax error", response=None):
        """Init MetaxError."""
        super().__init__(message)
        self.message = message
        self.response = response


class ResourceNotAvailableError(MetaxError):
    """Exception raised when resource is not found from metax."""

    def __init__(self, message="Resource not found"):
        """Init ResourceNotAvailableError."""
        super().__init__(message)


class ResourceAlreadyExistsError(MetaxError):
    """Exception raised when resource to be created already exists."""

    def __init__(self, message="Resource already exists.", response=None):
        """Init ResourceAlreadyExistsError.

        :param message: error message
        :param dict errors: Key-value pairs that caused the exception
        """
        super().__init__(message, response=response)


class FileNotAvailableError(ResourceNotAvailableError):
    """Exception raised when file is not found from metax."""

    def __init__(self):
        """Init FileNotAvailableError."""
        super().__init__("File not found")


class DatasetNotAvailableError(ResourceNotAvailableError):
    """Exception raised when dataset is not found from metax."""

    def __init__(self):
        """Init DatasetNotAvailableError."""
        super().__init__("Dataset not found")


class ContractNotAvailableError(ResourceNotAvailableError):
    """Exception raised when contract is not found from metax."""

    def __init__(self):
        """Init ContractNotAvailableError."""
        super().__init__("Contract not found")


class DataCatalogNotAvailableError(ResourceNotAvailableError):
    """Exception raised when contract is not found from metax."""

    def __init__(self):
        """Init DataCatalogNotAvailableError."""
        super().__init__("Datacatalog not found")


class DirectoryNotAvailableError(ResourceNotAvailableError):
    """Exception raised when directory is not found from metax."""

    def __init__(self):
        """Init DirectoryNotAvailableError."""
        super().__init__('Directory not found')


class DataciteGenerationError(MetaxError):
    """Exception raised when Metax returned 400 for datacite."""

    def __init__(self, message="Datacite generation failed in Metax"):
        """Init DataciteGenerationError."""
        super().__init__(message)


# pylint: disable=too-many-public-methods
class Metax:
    """Get metadata from metax as dict object."""

    # pylint: disable=too-many-arguments
    def __init__(self, url, user=None, password=None, token=None,
                 verify=True):
        """Initialize Metax object.

        :param url: Metax url
        :param user: Metax user
        :param password: Metax user password
        :param token: Metax access token
        """
        if not user and not token:
            raise ValueError('Metax user or access token is required.')
        self.username = user
        self.password = password
        self.token = token
        self.url = url
        self.baseurl = f'{url}/rest/v2'
        self.rpcurl = f'{url}/rpc/v2'
        self.verify = verify

    # pylint: disable=too-many-arguments
    def get_datasets(self, states=None,
                     limit="1000000",
                     offset="0",
                     pas_filter=None,
                     metadata_owner_org=None,
                     metadata_provider_user=None,
                     ordering=None,
                     include_user_metadata=True):
        """Get the metadata of datasets from Metax.

        :param str states: string containing dataset preservation state values
        e.g "10,20" for filtering
        :param str limit: max number of datasets to be returned
        :param str offset: offset for paging
        :param str pas_filter: string for filtering datasets, Used for the
                               following attributes in metax:
                                   1. research_dataset['title']
                                   2. research_dataset['curator']['name']
                                   3. contract['contract_json']['title']
        :param str metadata_owner_org: Filter by dataset field
                                       metadata_owner_org
        :param str metadata_provider_user: Filter by dataset field
                                           metadata_provider_user
        :param str ordering: metax dataset attribute for sorting datasets
                             e.g "preservation_state"
        :param bool include_user_metadata: Metax parameter for including
                                           metadata for files
        :returns: datasets from Metax as json.
        """
        if states is None:
            states = ','.join(
                str(state) for state in DS_STATE_ALL_STATES
            )

        params = {}
        if pas_filter is not None:
            params["pas_filter"] = pas_filter
        if metadata_owner_org is not None:
            params["metadata_owner_org"] = metadata_owner_org
        if metadata_provider_user is not None:
            params["metadata_provider_user"] = metadata_provider_user
        if ordering is not None:
            params["ordering"] = ordering
        if include_user_metadata:
            params["include_user_metadata"] = "true"

        params["preservation_state"] = states
        params["limit"] = limit
        params["offset"] = offset

        url = f"{self.baseurl}/datasets"
        response = self.get(url, allowed_status_codes=[404], params=params)
        if response.status_code == 404:
            raise DatasetNotAvailableError
        return response.json()

    def query_datasets(self, param_dict):
        """Get datasets from metax based on query parameters.

        :param dict param_dict: a dictionary containing attribute-value -pairs
            to be used as query parameters
        :returns: datasets from Metax as json.
        """
        url = f"{self.baseurl}/datasets"
        response = self.get(url, params=param_dict)

        return response.json()

    def get_datasets_by_ids(
            self, dataset_ids, limit=1000000, offset=0, fields=None):
        """Get datasets with given IDs.

        :param list dataset_ids: Dataset identifiers
        :param limit: Max number of datasets to return
        :param offset: Offset for paging
        :param list fields: Optional list of fields to retrieve for each
                            dataset. If not set, all fields are retrieved.
        :returns: List of found datasets
        """
        # Contrary to all other API commands, the "list datasets with IDs"
        # endpoint is found under "<metax>/rest/datasets/list"
        # (ie. no API version in the path)
        url = f"{self.url}/rest/datasets/list"

        params = {
            "limit": str(limit),
            "offset": str(offset)
        }
        if fields:
            params["fields"] = ",".join(fields)

        response = self.post(url, json=dataset_ids, params=params)
        return response.json()

    def get_contracts(self, limit="1000000", offset="0", org_filter=None):
        """Get the data for contracts list from Metax.

        :param str limit: max number of contracts to be returned
        :param str offset: offset for paging
        :param str org_filter: string for filtering contracts based on
                               contract['contract_json']['organization']
                               ['organization_identifier'] attribute value
        :returns: contracts from Metax as json.
        """
        params = {}
        if org_filter is not None:
            params["organization"] = org_filter

        params["limit"] = limit
        params["offset"] = offset

        url = f"{self.baseurl}/contracts"
        response = self.get(url, allowed_status_codes=[404], params=params)
        if response.status_code == 404:
            raise ContractNotAvailableError

        return response.json()

    def get_contract(self, pid):
        """Get the contract data from Metax.

        :param str pid: id or ientifier attribute of contract
        :returns: The contract from Metax as json.
        """
        url = f"{self.baseurl}/contracts/{pid}"
        response = self.get(url, allowed_status_codes=[404])
        if response.status_code == 404:
            raise ContractNotAvailableError

        return response.json()

    def patch_contract(self, contract_id, data):
        """Patch a contract.

        :param str contract_id: id or identifier of the contract
        :param dict data: A contract metadata dictionary that contains only the
                          key/value pairs that will be updated
        :returns: ``None``
        """
        # The original data must be added to updated objects since Metax patch
        # request will just overwrite them
        original_data = self.get_contract(contract_id)
        for key in data:
            if isinstance(data[key], dict) and key in original_data:
                data[key] = _update_nested_dict(original_data[key], data[key])

        url = f"{self.baseurl}/contracts/{contract_id}"
        response = self.patch(url, json=data)

        return response.json()

    def get_dataset(self, dataset_id, include_user_metadata=True):
        """Get dataset metadata from Metax.

        :param str dataset_id: id or identifier attribute of dataset
        :param bool include_user_metadata: Metax parameter for including
                                           metadata for files
        :returns: dataset as json
        """
        url = f'{self.baseurl}/datasets/{dataset_id}'

        response = self.get(
            url,
            allowed_status_codes=[404],
            params={
                "include_user_metadata":
                    "true" if include_user_metadata else "false"
            }
        )

        if response.status_code == 404:
            raise DatasetNotAvailableError

        return response.json()

    def get_dataset_template(self):
        """Get minimal dataset template.

        :returns: Template as json
        """
        response = self.get(
            f"{self.rpcurl}/datasets/get_minimal_dataset_template"
            "?type=enduser_pas"
        )
        template = response.json()

        return template

    def get_datacatalog(self, catalog_id):
        """Get the metadata of a datacatalog from Metax.

        :param str catalog_id: id or identifier attribute of the datacatalog
        :returns: The datacatalog as json.
        """
        url = f"{self.baseurl}/datacatalogs/{catalog_id}"
        response = self.get(url, allowed_status_codes=[404])
        if response.status_code == 404:
            raise DataCatalogNotAvailableError

        return response.json()

    def patch_dataset(self, dataset_id, data):
        """Patch a dataset.

        :param str dataset_id: id or identifier of the dataset
        :param dict data: A dataset dictionary that contains only the
                          key/value pairs that will be updated
        :returns: ``None``
        """
        # The original data must be added to updated objects since Metax patch
        # request will just overwrite them
        original_data = self.get_dataset(dataset_id)
        for key in data:
            if isinstance(data[key], dict) and key in original_data:
                data[key] = _update_nested_dict(original_data[key], data[key])

        url = f"{self.baseurl}/datasets/{dataset_id}"
        response = self.patch(url, json=data)

        return response.json()

    def get_dataset_filetypes(self, dataset_id):
        """Get list of filetypes in dataset.

        Returns unique triples of file_format, format_version, encoding of the
        files in dataset.

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

        url = f"{self.baseurl}/datasets/{dataset_id}/files"
        response = self.get(url, allowed_status_codes=[404])
        if response.status_code == 404:
            raise DatasetNotAvailableError

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
            if file_format:
                temp_types.add(f"{file_format}||{format_version}||{encoding}")

        for temp_type in temp_types:
            attrs = temp_type.split('||')
            mime_types.append({'file_format': attrs[0],
                               'format_version': attrs[1],
                               'encoding': attrs[2]})
        file_types = {
            'total_count': len(mime_types),
            'filetypes': mime_types
        }
        return file_types

    def get_contract_datasets(self, pid):
        """Get the datasets of a contract from Metax.

        :param str pid: id or identifier attribute of contract
        :returns: The datasets from Metax as json.
        """
        url = f"{self.baseurl}/contracts/{pid}/datasets"
        response = self.get(url)

        return response.json()

    def get_file(self, file_id):
        """Get file metadata from Metax.

        :param str file_id: id or identifier attribute of file
        :returns: file metadata as json
        """
        url = f'{self.baseurl}/files/{file_id}'

        response = self.get(url, allowed_status_codes=[404])

        if response.status_code == 404:
            raise FileNotAvailableError

        return response.json()

    def get_files(self, project):
        """Get all files of a given project.

        :param project: project id
        :returns: list of files
        """
        files = []
        url = f'{self.baseurl}/files?limit=10000&project_identifier={project}'

        # GET 10000 files every iteration until all files are read
        while url is not None:
            response = self.get(url).json()
            url = response["next"]
            files.extend(response["results"])

        return files

    def get_files_dict(self, project):
        """Get all the files of a given project.

        Files are returned as a dictionary:

            {
                file_path: {
                    "id": id,
                    "identifier": identifier
                }
            }

        :param project: project id
        :returns: Dict of all the files of a given project
        """
        files = self.get_files(project)

        file_dict = {}
        for _file in files:
            file_dict[_file["file_path"]] = {
                "id": _file["id"],
                "identifier": _file["identifier"],
                "storage_identifier": _file["file_storage"]["identifier"]
            }

        return file_dict

    def get_xml(self, identifier):
        """Get technical metadata of file in xml format.

        :param str identifier: id or identifier attribute of object
        :returns: dict with XML namespace strings as keys and
                  lxml.etree.ElementTree objects as values
        """
        # Init result dict
        xml_dict = {}

        # Get list of xml namespaces
        ns_key_url = f'{self.baseurl}/files/{identifier}/xml'
        response = self.get(ns_key_url, allowed_status_codes=[404])
        if response.status_code == 404:
            raise FileNotAvailableError
        ns_key_list = response.json()

        # For each listed namespace, download the xml, create ElementTree, and
        # add it to result dict
        for ns_key in ns_key_list:
            response = self.get(ns_key_url, params={"namespace": ns_key})
            # pylint: disable=no-member
            xml_dict[ns_key] \
                = lxml.etree.fromstring(response.content).getroottree()

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
        xmls = self.get_xml(file_id)
        if namespace not in xmls:
            # Convert XML element to string
            # pylint: disable=no-member
            data = lxml.etree.tostring(xml_element, pretty_print=True)
            # POST to Metax
            url = f'{self.baseurl}/files/{file_id}/xml'
            params = {
                "namespace": namespace
            }

            headers = {'Content-Type': 'application/xml'}
            self.post(url, data=data, headers=headers, params=params)

            return True

        return False

    def set_preservation_state(self, dataset_id, state, description):
        """Set preservation state of dataset.

        Sets values of `preservation_state` and
        `preservation_description` for dataset in Metax.

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
        :param str description: The value for `preservation_description`
        :returns: ``None``
        """
        url = f'{self.baseurl}/datasets/{dataset_id}'
        data = {
            'preservation_state': state,
            'preservation_description': description
        }

        self.patch(url, json=data)

    def set_preservation_reason(self, dataset_id, reason):
        """Set preservation reason of dataset.

        Sets value of `preservation_reason_description` for dataset in
        Metax.

        :param str dataset_id: id or identifier attribute of dataset in Metax
        :param str reason: The value for `preservation_reason_description`
        :returns: ``None``
        """
        url = f'{self.baseurl}/datasets/{dataset_id}'
        self.patch(url, json={'preservation_reason_description': reason})

    def patch_file(self, file_id, data):
        """Patch file metadata.

        :param str file_id: id or identifier of the file
        :param dict data: A file metadata dictionary that contains only the
                          key/value pairs that will be updated
        :returns: JSON response from Metax
        """
        # The original data must be added to updated objects since Metax patch
        # request will just overwrite them
        original_data = self.get_file(file_id)
        for key in data:
            if isinstance(data[key], dict) and key in original_data:
                data[key] = _update_nested_dict(original_data[key], data[key])

        url = f"{self.baseurl}/files/{file_id}"
        response = self.patch(url, json=data)

        return response.json()

    def get_datacite(self, dataset_id, dummy_doi="false"):
        """Get descriptive metadata in datacite xml format.

        :param dataset_id: id or identifier attribute of dataset
        :param dummy_doi: "false" or "true". "true" asks Metax to use
                          a dummy DOI if the actual DOI is not yet generated
        :returns: Datacite XML (lxml.etree.ElementTree object)
        """
        url = f"{self.baseurl}/datasets/{dataset_id}"
        params = {
            "dataset_format": "datacite",
            "dummy_doi": dummy_doi
        }
        response = self.get(
            url, allowed_status_codes=[400, 404], params=params
        )

        if response.status_code == 400:
            detail = response.json()['detail']
            raise DataciteGenerationError(
                f"Datacite generation failed: {detail}"
            )

        if response.status_code == 404:
            raise DatasetNotAvailableError

        # pylint: disable=no-member
        return lxml.etree.fromstring(response.content).getroottree()

    def get_dataset_file_count(self, dataset_id):
        """
        Get total file count for a dataset in Metax, including those
        in directories.

        :param str dataset_id: id or identifier of dataset
        :raises DatasetNotAvailableError: If dataset is not available

        :returns: total count of files
        """
        url = f"{self.baseurl}/datasets/{dataset_id}/files"

        response = self.get(
            url, params={"file_fields": "id"},
            allowed_status_codes=[404]
        )

        if response.status_code == 404:
            raise DatasetNotAvailableError

        result = response.json()
        return len(result)

    def get_dataset_files(self, dataset_id):
        """Get files metadata of dataset Metax.

        :param str dataset_id: id or identifier attribute of dataset
        :returns: metadata of dataset files as json
        """
        url = f'{self.baseurl}/datasets/{dataset_id}/files'

        response = self.get(url, allowed_status_codes=[404])

        if response.status_code == 404:
            raise DatasetNotAvailableError

        return response.json()

    def get_file_datasets(self, file_id):
        """Get a list of research datasets associated with file_id.

        :param file_id: File identifier
        :returns: List of datasets associated with file_id
        """
        url = f'{self.baseurl}/files/datasets'
        response = self.post(url, allowed_status_codes=[404], json=[file_id])

        if response.status_code == 404:
            raise FileNotAvailableError

        return response.json()

    def get_file2dataset_dict(self, file_ids):
        """Get a dict of {file_identifier: [dataset_identifier...] mappings

        :param file_ids: List of file IDs
        :returns: Dictionary with the format
                  {file_identifier: [dataset_identifier1, ...]}
        """
        url = f"{self.baseurl}/files/datasets?keys=files"
        response = self.post(url, json=file_ids)

        result = response.json()

        if not result:
            # Metax API always returns an empty list if there are no results,
            # even if the response would otherwise be a dictionary.
            # Take care of this inconsistency by returning an empty dict
            # instead.
            return {}

        return response.json()

    def delete_file(self, file_id):
        """Delete metadata of a file.

        :param file_id: file identifier
        :returns: JSON response from Metax
        """
        url = f'{self.baseurl}/files/{file_id}'
        response = self.delete(url)

        return response.json()

    def delete_files(self, file_id_list):
        """Delete file metadata from Metax.

        :param file_id_list: List of ids to delete from Metax
        :returns: JSON returned by Metax
        """
        url = f'{self.baseurl}/files'
        response = self.delete(url, json=file_id_list)

        return response.json()

    def delete_dataset(self, dataset_id):
        """Delete metadata of dataset.

        :param dataset_id: dataset identifier
        :returns: ``None``
        """
        url = f'{self.baseurl}/datasets/{dataset_id}'
        self.delete(url)

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
        :returns: JSON response from Metax
        """
        url = f'{self.baseurl}/files/'
        response = self.post(url,
                             json=metadata,
                             allowed_status_codes=[400, 404])

        if response.status_code == 404:
            raise FileNotAvailableError

        if response.status_code == 400:

            # Read the response and parse list of failed files
            try:
                failed_files = response.json()['failed']
            except KeyError:
                # Most likely only one file was posted, so Metax
                # response is formatted differently: just one error
                # instead of list of errors
                failed_files = [{'object': metadata,
                                 'errors': response.json()}]

            # If all errors are caused by files that already exist,
            # raise ResourceAlreadyExistsError.
            all_errors = []
            for file_ in failed_files:
                for error_message in file_['errors'].values():
                    all_errors.extend(error_message)
            path_exists_pattern \
                = 'a file with path .* already exists in project .*'
            identifier_exists_pattern \
                = 'a file with given identifier already exists'
            if all(
                    re.search(path_exists_pattern, string)
                    or re.search(identifier_exists_pattern, string)
                    for string in all_errors
            ):
                raise ResourceAlreadyExistsError(
                    'Some of the files already exist.',
                    response=response
                )

            # Raise HTTPError for unknown "bad request error"
            response.raise_for_status()

        return response.json()

    def post_dataset(self, metadata):
        """Post dataset metadata.

        :param metadata: dataset metadata dictionary
        :returns: JSON response from Metax
        """
        url = f'{self.baseurl}/datasets/'
        response = self.post(url, json=metadata)

        return response.json()

    def post_contract(self, metadata):
        """Post contract metadata.

        :param metadata: contract metadata dictionary
        :returns: JSON response from Metax
        """
        url = f'{self.baseurl}/contracts/'
        response = self.post(url, json=metadata)

        return response.json()

    def delete_contract(self, contract_id):
        """Delete metadata of contract.

        :param dataset_id: contract identifier
        :returns: ``None``
        """
        url = f'{self.baseurl}/contracts/{contract_id}'
        self.delete(url)

    def get_directory_files(self, directory_identifier):
        """Get files of the directory.

        :param str directory_identifier: identifier attribute of directory
        :returns: directory files as json
        """
        url = f'{self.baseurl}/directories/{directory_identifier}/files'
        response = self.get(url, allowed_status_codes=[404])

        if response.status_code == 404:
            raise DirectoryNotAvailableError

        return response.json()

    def get_directory(self, directory_identifier):
        """Get directory.

        :param str directory_identifier: identifier attribute of directory
        :returns: directory metadata
        """
        url = f'{self.baseurl}/directories/{directory_identifier}'

        response = self.get(url, allowed_status_codes=[404])

        if response.status_code == 404:
            raise DirectoryNotAvailableError

        return response.json()

    def get_project_directory(self, project, path):
        """Get directory of project by path.

        :param str project: project identifier of the directory
        :param str path: path of the directory
        :returns: directory metadata
        """
        url = f'{self.baseurl}/directories/files'
        response = self.get(url, allowed_status_codes=[404],
                            params={'path': path,
                                    'project': project,
                                    'depth': 1,
                                    'directories_only': 'true',
                                    'include_parent': 'true'})

        if response.status_code == 404:
            raise DirectoryNotAvailableError

        metadata = response.json()
        del metadata['directories']
        return metadata

    def get_project_file(self, project, path):
        """Get file of project by path.

        :param str project: project identifier of the file
        :param str path: path of the file
        :returns: directory metadata
        """
        url = f'{self.baseurl}/files'
        response = self.get(url, params={'file_path': path,
                                         'project_identifier': project})

        try:
            return next(
                file for file in response.json()['results']
                if file['file_path'].strip('/') == path.strip('/')
            )
        except StopIteration:
            raise FileNotAvailableError

    def request(self, method, url, allowed_status_codes=None, **kwargs):
        """Send authenticated HTTP request.

        This function is a wrapper function for requests.requets with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        if not allowed_status_codes:
            allowed_status_codes = []

        if "verify" not in kwargs:
            kwargs["verify"] = self.verify

        if self.token:
            if "headers" in kwargs:
                kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
            else:
                kwargs["headers"] = {"Authorization": f"Bearer {self.token}"}
        else:
            kwargs["auth"] = HTTPBasicAuth(self.username, self.password)

        response = requests.request(method, url, **kwargs)
        request = response.request
        logger.debug("%s %s\n%s", request.method, request.url, request.body)
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            if error.response.status_code not in allowed_status_codes:
                logger.error(
                    'HTTP request to %s failed. Response from server was: %s',
                    response.url, response.text
                )
                raise

        return response

    def get(self, url, allowed_status_codes=None, **kwargs):
        """Send authenticated HTTP GET request.

        This function is a wrapper function for requests.get with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request('GET', url, allowed_status_codes, **kwargs)

    def patch(self, url, allowed_status_codes=None, **kwargs):
        """Send authenticated HTTP PATCH request.

        This function is a wrapper function for requests.patch with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request('PATCH', url, allowed_status_codes, **kwargs)

    def post(self, url, allowed_status_codes=None, **kwargs):
        """Send authenticated HTTP POST request.

        This function is a wrapper function for requests.post with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request('POST', url, allowed_status_codes, **kwargs)

    def delete(self, url, allowed_status_codes=None, **kwargs):
        """Send authenticated HTTP DELETE request.

        This function is a wrapper function for requests.delete with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request('DELETE', url, allowed_status_codes, **kwargs)


def _update_nested_dict(original, update):
    """Update nested dictionary.

    The keys of update dictionary are appended to
    original dictionary. If original already contains the key, it will be
    overwritten. If key value is dictionary, the original value is updated with
    the value from update dictionary.

    :param original: Original dictionary
    :param update: Dictionary that contains only key/value pairs to be updated
    :returns: Updated dictionary
    """
    updated_dict = copy.deepcopy(original)

    for key in update:
        if key in original and isinstance(update[key], dict):
            updated_dict[key] = _update_nested_dict(original[key], update[key])
        else:
            updated_dict[key] = update[key]

    return updated_dict
