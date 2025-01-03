"""Metax interface class."""

import logging
from typing import Union

import requests
from requests.auth import HTTPBasicAuth

import metax_access.metax_v2 as metax_v2

# These imports are used by other projects (eg. upload-rest-api)
# pylint: disable=unused-import
from metax_access import (  # noqa: F401
    DS_STATE_ACCEPTED_TO_DIGITAL_PRESERVATION,
    DS_STATE_ALL_STATES, DS_STATE_GENERATING_METADATA,
    DS_STATE_IN_DIGITAL_PRESERVATION,
    DS_STATE_IN_DISSEMINATION,
    DS_STATE_IN_PACKAGING_SERVICE, DS_STATE_INITIALIZED,
    DS_STATE_INVALID_METADATA,
    DS_STATE_METADATA_CONFIRMED,
    DS_STATE_METADATA_VALIDATION_FAILED, DS_STATE_NONE,
    DS_STATE_PACKAGING_FAILED, DS_STATE_REJECTED_BY_USER,
    DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
    DS_STATE_SIP_SENT_TO_INGESTION_IN_DPRES_SERVICE,
    DS_STATE_TECHNICAL_METADATA_GENERATED,
    DS_STATE_TECHNICAL_METADATA_GENERATION_FAILED,
    DS_STATE_VALIDATED_METADATA_UPDATED,
    DS_STATE_VALIDATING_METADATA)
from metax_access.error import *  # noqa: F403, F401
from metax_access.response import MetaxFile

logger = logging.getLogger(__name__)


# pylint: disable=too-many-public-methods
class Metax:
    """Get metadata from metax as dict object."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        url,
        user=None,
        password=None,
        token=None,
        verify=True,
        api_version="v2",
    ):
        """Initialize Metax object.

        :param url: Metax url
        :param user: Metax user
        :param password: Metax user password
        :param token: Metax access token
        """
        if not user and not token:
            raise ValueError("Metax user or access token is required.")
        self.username = user
        self.password = password
        self.token = token
        self.url = url
        self.baseurl = f"{url}/rest/v2"
        self.rpcurl = f"{url}/rpc/v2"
        self.verify = verify
        self.api_version = api_version

    # pylint: disable=too-many-arguments
    def get_datasets(
        self,
        states=None,
        limit="1000000",
        offset="0",
        pas_filter=None,
        metadata_owner_org=None,
        metadata_provider_user=None,
        ordering=None,
        include_user_metadata=True,
    ):
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
        if self.api_version == "v2":
            return metax_v2.get_datasets(
                self,
                states,
                limit,
                offset,
                pas_filter,
                metadata_owner_org,
                metadata_provider_user,
                ordering,
                include_user_metadata,
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def query_datasets(self, param_dict):
        """Get datasets from metax based on query parameters.

        :param dict param_dict: a dictionary containing attribute-value -pairs
            to be used as query parameters
        :returns: datasets from Metax as json.
        """
        if self.api_version == "v2":
            return metax_v2.query_datasets(self, param_dict)
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_datasets_by_ids(
        self, dataset_ids, limit=1000000, offset=0, fields=None
    ):
        """Get datasets with given IDs.

        :param list dataset_ids: Dataset identifiers
        :param limit: Max number of datasets to return
        :param offset: Offset for paging
        :param list fields: Optional list of fields to retrieve for each
                            dataset. If not set, all fields are retrieved.
        :returns: List of found datasets
        """
        if self.api_version == "v2":
            return metax_v2.get_datasets_by_ids(
                self, dataset_ids, limit, offset, fields
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_contracts(self, limit="1000000", offset="0", org_filter=None):
        """Get the data for contracts list from Metax.

        :param str limit: max number of contracts to be returned
        :param str offset: offset for paging
        :param str org_filter: string for filtering contracts based on
                               contract['contract_json']['organization']
                               ['organization_identifier'] attribute value
        :returns: contracts from Metax as json.
        """
        if self.api_version == "v2":
            return metax_v2.get_contracts(
                self, limit, offset, org_filter
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_contract(self, pid):
        """Get the contract data from Metax.

        :param str pid: id or ientifier attribute of contract
        :returns: The contract from Metax as json.
        """
        if self.api_version == "v2":
            return metax_v2.get_contract(self, pid)
        
        url = f"{self.baseurl_v3}/contracts/{pid}"
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
        if self.api_version == "v2":
            return metax_v2.patch_contract(self, contract_id, data)
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_dataset(self, dataset_id, include_user_metadata=True, v2=False):
        """Get dataset metadata from Metax.

        :param str dataset_id: id or identifier attribute of dataset
        :param bool include_user_metadata: Metax parameter for including
                                           metadata for files
        :returns: dataset as json
        """
        if self.api_version == "v2":
            return metax_v2.get_dataset(
                self,
                dataset_id,
                include_user_metadata,
                v2,
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_dataset_template(self):
        """Get minimal dataset template.

        :returns: Template as json
        """
        if self.api_version == "v2":
            return metax_v2.get_dataset_template(self)
        raise NotImplementedError("Metax API V3 support not implemented")

    def patch_dataset(self,
                      dataset_id,
                      data,
                      overwrite_objects=False,
                      v2=False):
        """Patch a dataset.S

        :param str dataset_id: id or identifier of the dataset
        :param dict data: A dataset dictionary that contains only the
                          key/value pairs that will be updated
        :returns: ``None``
        """
        if self.api_version == "v2":
            return metax_v2.patch_dataset(
                self, dataset_id, data, overwrite_objects, v2
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def set_contract(self, dataset_id, contract_id):
        """ Update the contract of a dataset.

        :param str dataset_id: identifier of the dataset
        :param str contract_if: the new contract id of the dataset
        :returns: ``None``
        """
        if self.api_version == 'v2':
            return metax_v2.set_contract(self, dataset_id, contract_id)
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_contract_datasets(self, pid):
        """Get the datasets of a contract from Metax.

        :param str pid: id or identifier attribute of contract
        :returns: The datasets from Metax as json.
        """
        if self.api_version == "v2":
            return metax_v2.get_contract_datasets(self, pid)
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_file(self, file_id, v2=False) -> MetaxFile:
        """Get file metadata from Metax.

        :param str file_id: id or identifier attribute of file
        :returns: file metadata as json
        """
        if self.api_version == "v2":
            return metax_v2.get_file(self, file_id, v2)
        raise NotImplementedError("Metax API V3 support not implemented")

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
        if self.api_version == "v2":
            return metax_v2.get_files_dict(self, project)
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_directory_id(
        self,
        project,
        path,
    ):
        """Get the identifier of a direcotry with project and a path.

        The directory id will be deprecated in Metax V3 but the V2's
        directory identifier is available with this method.

        :param str project: project identifier of the directory
        :param str path: path of the directory
        :returns: directory identifier
        """
        if self.api_version == "v2":
            return metax_v2.get_directory_id(
                self, project, path
            )
        raise NotImplementedError("Metax API V3 support not implemented")

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
        if self.api_version == "v2":
            return metax_v2.set_preservation_state(
                self, dataset_id, state, description
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def set_preservation_reason(self, dataset_id, reason):
        """Set preservation reason of dataset.

        Sets value of `preservation_reason_description` for dataset in
        Metax.

        :param str dataset_id: id or identifier attribute of dataset in Metax
        :param str reason: The value for `preservation_reason_description`
        :returns: ``None``
        """
        if self.api_version == "v2":
            return metax_v2.set_preservation_reason(self, dataset_id, reason)
        raise NotImplementedError("Metax API V3 support not implemented")

    def patch_file(self, file_id, data):
        """Patch file metadata.

        :param str file_id: identifier of the file
        :param dict data: A file metadata dictionary that contains only the
                          key/value pairs that will be updated
        :returns: JSON response from Metax
        """
        if self.api_version == "v2":
            return metax_v2.patch_file(self, file_id, data)
        raise NotImplementedError("Metax API V3 support not implemented")

    def patch_file_characteristics(self, file_id, file_characteristics):
        """Patch file characteristics ja file_characteristics_extension

        :param str file_id: identifier of the file
        :param dict file_characteristics: A dictionary including file
                                    characteristics and file characteristics
                                    extension fields. Only key/value pairs
                                    that will be updated are required.
        :returns: JSON response from Metax
        """
        if self.api_version == "v2":
            return metax_v2.patch_file_characteristics(
                self, file_id, file_characteristics
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_datacite(self, dataset_id, dummy_doi="false"):
        """Get descriptive metadata in datacite xml format.

        :param dataset_id: id or identifier attribute of dataset
        :param dummy_doi: "false" or "true". "true" asks Metax to use
                          a dummy DOI if the actual DOI is not yet generated
        :returns: Datacite XML as string
        """
        if self.api_version == "v2":
            return metax_v2.get_datacite(
                self,
                dataset_id,
                dummy_doi,
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_dataset_file_count(self, dataset_id):
        """
        Get total file count for a dataset in Metax, including those
        in directories.

        :param str dataset_id: id or identifier of dataset
        :raises DatasetNotAvailableError: If dataset is not available

        :returns: total count of files
        """
        if self.api_version == "v2":
            return metax_v2.get_dataset_file_count(
                self, dataset_id
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_dataset_files(self, dataset_id) -> list[MetaxFile]:
        """Get files metadata of dataset Metax.

        :param str dataset_id: id or identifier attribute of dataset
        :returns: metadata of dataset files as json
        """
        if self.api_version == "v2":
            return metax_v2.get_dataset_files(
                self, dataset_id
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_file_datasets(self, file_id):
        """Get a list of research datasets associated with file_id.

        :param file_id: File identifier
        :returns: List of datasets associated with file_id
        """
        if self.api_version == "v2":
            return metax_v2.get_file_datasets(
                self, file_id
            )
        # V3 endpoint
        # 'https://metax.fd-test.csc.fi/v3/files/datasets?relations=false'
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_file2dataset_dict(self, file_ids):
        """Get a dict of {file_identifier: [dataset_identifier...] mappings

        :param file_ids: List of file IDs
        :returns: Dictionary with the format
                  {file_identifier: [dataset_identifier1, ...]}
        """
        if self.api_version == "v2":
            return metax_v2.get_file2dataset_dict(self, file_ids)
        raise NotImplementedError("Metax API V3 support not implemented")

    def delete_file(self, file_id):
        """Delete metadata of a file.

        :param file_id: file identifier
        :returns: JSON response from Metax
        """
        if self.api_version == "v2":
            return metax_v2.delete_file(self, file_id)
        raise NotImplementedError("Metax API V3 support not implemented")

    def delete_files(self, file_id_list):
        """Delete file metadata from Metax.

        :param file_id_list: List of ids to delete from Metax
        :returns: JSON returned by Metax
        """
        if self.api_version == "v2":
            return metax_v2.delete_files(self, file_id_list)
        raise NotImplementedError("Metax API V3 support not implemented")

    def delete_dataset(self, dataset_id):
        """Delete metadata of dataset.

        :param dataset_id: dataset identifier
        :returns: ``None``
        """
        if self.api_version == "v2":
            return metax_v2.delete_dataset(self, dataset_id)
        raise NotImplementedError("Metax API V3 support not implemented")

    def post_file(self, metadata: Union[MetaxFile, list[MetaxFile]]):
        """Post file metadata.

        :param metadata: file metadata dictionary or list of files
        :returns: JSON response from Metax
        """
        if self.api_version == "v2":
            return metax_v2.post_file(
                self,
                metadata,
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def post_dataset(self, metadata):
        """Post dataset metadata.

        :param metadata: dataset metadata dictionary
        :returns: JSON response from Metax
        """
        if self.api_version == "v2":
            return metax_v2.post_dataset(self, metadata)
        raise NotImplementedError("Metax API V3 support not implemented")

    def post_contract(self, metadata):
        """Post contract metadata.

        :param metadata: contract metadata dictionary
        :returns: JSON response from Metax
        """
        if self.api_version == "v2":
            return metax_v2.post_contract(self, metadata)
        raise NotImplementedError("Metax API V3 support not implemented")

    def delete_contract(self, contract_id):
        """Delete metadata of contract.

        :param dataset_id: contract identifier
        :returns: ``None``
        """
        if self.api_version == "v2":
            return metax_v2.delete_contract(self, contract_id)
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_project_directory(self, project, path, dataset_identifier=None):
        """Get directory metadata, directories, and files of project by path.

        :param str project: project identifier of the directory
        :param str path: path of the directory
        :param str dataset_identifier: Only list files and directories
                                       that are part of specified
                                       dataset
        :returns: directory metadata
        """
        if self.api_version == "v2":
            return metax_v2.get_project_directory(
                self,
                project,
                path,
                dataset_identifier,
            )
        raise NotImplementedError("Metax API V3 support not implemented")

    def get_project_file(self, project, path) -> MetaxFile:
        """Get file of project by path.

        :param str project: project identifier of the file
        :param str path: path of the file
        :returns: file metadata
        """
        if self.api_version == "v2":
            return metax_v2.get_project_file(
                self, project, path
            )
        raise NotImplementedError("Metax API V3 support not implemented")

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
                    "HTTP request to %s failed. Response from server was: %s",
                    response.url,
                    response.text,
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
        return self.request("GET", url, allowed_status_codes, **kwargs)

    def patch(self, url, allowed_status_codes=None, **kwargs):
        """Send authenticated HTTP PATCH request.

        This function is a wrapper function for requests.patch with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request("PATCH", url, allowed_status_codes, **kwargs)

    def post(self, url, allowed_status_codes=None, **kwargs):
        """Send authenticated HTTP POST request.

        This function is a wrapper function for requests.post with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request("POST", url, allowed_status_codes, **kwargs)

    def delete(self, url, allowed_status_codes=None, **kwargs):
        """Send authenticated HTTP DELETE request.

        This function is a wrapper function for requests.delete with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request("DELETE", url, allowed_status_codes, **kwargs)
