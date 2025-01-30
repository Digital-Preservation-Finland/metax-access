"""Metax interface class."""

import logging
import re
from typing import Union

import requests
from requests.auth import HTTPBasicAuth

from metax_access import metax_v2
from metax_access.error import (ContractNotAvailableError,
                                DataciteGenerationError,
                                DatasetNotAvailableError,
                                DirectoryNotAvailableError,
                                FileNotAvailableError,
                                ResourceAlreadyExistsError)
from metax_access.response import MetaxFile
from metax_access.response_mapper import (map_contract, map_dataset,
                                          map_directory_files, map_file)
from metax_access.utils import extended_result, update_nested_dict

# These imports are used by other projects (eg. upload-rest-api)
# pylint: disable=unused-import
from metax_access import (  # noqa: F401 isort:skip
    DS_STATE_ALL_STATES,
    DS_STATE_ACCEPTED_TO_DIGITAL_PRESERVATION,
    DS_STATE_GENERATING_METADATA,
    DS_STATE_IN_DIGITAL_PRESERVATION,
    DS_STATE_IN_DISSEMINATION,
    DS_STATE_IN_PACKAGING_SERVICE,
    DS_STATE_INITIALIZED,
    DS_STATE_INVALID_METADATA,
    DS_STATE_METADATA_CONFIRMED,
    DS_STATE_METADATA_VALIDATION_FAILED,
    DS_STATE_NONE,
    DS_STATE_PACKAGING_FAILED,
    DS_STATE_REJECTED_BY_USER,
    DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
    DS_STATE_SIP_SENT_TO_INGESTION_IN_DPRES_SERVICE,
    DS_STATE_TECHNICAL_METADATA_GENERATED,
    DS_STATE_TECHNICAL_METADATA_GENERATION_FAILED,
    DS_STATE_VALIDATED_METADATA_UPDATED,
    DS_STATE_VALIDATING_METADATA
)

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
        if api_version not in ("v2", "v3"):
            raise ValueError(f"API version '{api_version}' is invalid.")

        self.username = user
        self.password = password
        self.token = token
        self.url = url
        if api_version == "v3":
            self.baseurl = f"{url}/v3"
        else:
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
        # V3 params:
        search=None,
        metadata_owner_user=None,
    ):
        """Get the metadata of datasets from Metax.

        :param str states: dataset preservation state value as a string
                           e.g "10" for filtering. Kept for V2 backward
                           compatibility, recommended to use `state` instead.
        :param str limit: max number of datasets to be returned
        :param str offset: offset for paging
        :param str pas_filter: string for filtering datasets, Used for the
                               following attributes in metax:
                                   1. research_dataset['title']
                                   2. research_dataset['curator']['name']
                                   3. contract['contract_json']['title']
                                Deprecated in V3. Use `search` instead.
        :param str metadata_owner_org: Filter by dataset field
                                       metadata_owner_org
        :param str metadata_provider_user: Filter by dataset field
                                           metadata_provider_user.
                                           Deprecated in V3. Use
                                           `metadata_owner_user` instead.
        :param str ordering: metax dataset attribute for sorting datasets
                             e.g V2 "preservation_state"
                             or V3 "preservation__state"
        :param bool include_user_metadata: Metax parameter for including
                                           metadata for files.
                                           Deprecaed in V3.
        :param str search: string for filtering datasets.
        :param str metadata_owner_user: Filter by dataset field
                                        metadata_owner_user.
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

        params = []
        if search is not None:
            params += [("search", search)]
        if metadata_owner_org is not None:
            params += [("metadata_owner__organization", metadata_owner_org)]
        # V3 metadata_owner_user is same as metadata provider user in V2
        if metadata_owner_user is not None:
            params += [("metadata_owner__user", metadata_owner_user)]
        if ordering is not None:
            params += [("ordering", ordering)]
        if isinstance(states, str):
            states = states.split(",")
        if states is not None:
            for state_ in states:
                params += [("preservation__state", str(state_))]
        params += [("limit", limit)]
        params += [("offset", offset)]

        url = f"{self.baseurl}/datasets"
        response = self.get(url, allowed_status_codes=[404], params=params)
        if response.status_code == 404:
            raise DatasetNotAvailableError
        json = response.json()
        if "results" in json:
            json["results"] = [
                map_dataset(dataset) for dataset in json["results"]
            ]
        return json

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
        # TODO: Does not have a implementation in v3
        # just looks for the datasets seperately
        params = {}
        if fields is not None:
            params["fields"] = fields
        datasets = []
        for dataset_id in dataset_ids:
            url = f"{self.baseurl}/datasets/{dataset_id}"
            response = self.get(url, params=params)
            datasets.append(response.json())
        return datasets

    def get_contracts(self, limit="1000000", offset="0", org_filter=None):
        """Get the data for contracts list from Metax.

        :param str limit: max number of contracts to be returned
        :param str offset: offset for paging
        :param str org_filter: string for filtering contracts based on
                               contract['contract_json']['organization']
                               ['organization_identifier'] attribute value.
                               Deprecated in V3.
        :returns: contracts from Metax as json.
        """
        if self.api_version == "v2":
            return metax_v2.get_contracts(self, limit, offset, org_filter)
        params = {}
        params["limit"] = limit
        params["offset"] = offset
        url = f"{self.baseurl}/contracts"
        response = self.get(url, allowed_status_codes=[404], params=params)
        if response.status_code == 404:
            raise ContractNotAvailableError
        json = response.json()
        json |= {
            "results": [
                map_contract(contract) for contract in json.get("results", [])
            ]
        }
        return json

    def get_contract(self, pid):
        """Get the contract data from Metax.

        state=None,
        :param str pid: id or ientifier attribute of contract
        :returns: The contract from Metax as json.
        """
        if self.api_version == "v2":
            return metax_v2.get_contract(self, pid)

        url = f"{self.baseurl}/contracts/{pid}"
        response = self.get(url, allowed_status_codes=[404])
        if response.status_code == 404:
            raise ContractNotAvailableError
        return map_contract(response.json())

    def patch_contract(self, contract_id, data):
        """Patch a contract.

        :param str contract_id: id or identifier of the contract
        :param dict data: A contract metadata dictionary that contains only the
                          key/value pairs that will be updated
        :returns: ``None``
        """
        if self.api_version == "v2":
            return metax_v2.patch_contract(self, contract_id, data)
        original_data = self.get_contract(contract_id)
        for key in data:
            if isinstance(data[key], dict) and key in original_data:
                data[key] = update_nested_dict(original_data[key], data[key])
        url = f"{self.baseurl}/contracts/{contract_id}"
        response = self.patch(url, json=data)
        return map_contract(response.json())

    def get_dataset(self, dataset_id, include_user_metadata=True, v2=False):
        """Get dataset metadata from Metax.

        :param str dataset_id: id or identifier attribute of dataset
        :param bool include_user_metadata: Metax parameter for including
                                           metadata for files
                                           Deprecated in V3.
        :param bool v2: Parameter used in V2->V3 migration period.
        :returns: dataset as json
        """
        if self.api_version == "v2":
            return metax_v2.get_dataset(
                self,
                dataset_id,
                include_user_metadata,
                v2,
            )
        url = f"{self.baseurl}/datasets/{dataset_id}"
        response = self.get(
            url,
            allowed_status_codes=[404],
        )
        if response.status_code == 404:
            raise DatasetNotAvailableError
        return map_dataset(response.json())

    def get_dataset_template(self):
        """Get minimal dataset template.

        :returns: Template as json
        """
        if self.api_version == "v2":
            return metax_v2.get_dataset_template(self)
        raise NotImplementedError("Metax API V3 support not implemented")

    def patch_dataset(
        self, dataset_id, data, overwrite_objects=False, v2=False
    ):
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
        """Update the contract of a dataset.

        :param str dataset_id: identifier of the dataset
        :param str contract_if: the new contract id of the dataset
        :returns: ``None``
        """
        if self.api_version == "v2":
            return metax_v2.set_contract(self, dataset_id, contract_id)
        data = {"contract": contract_id}
        url = f"{self.baseurl}/datasets/{dataset_id}/preservation"
        response = self.patch(url, json=data)
        return response.json()

    def get_contract_datasets(self, pid):
        """Get the datasets of a contract from Metax.

        :param str pid: id or identifier attribute of contract
        :returns: The datasets from Metax as json.
        """
        if self.api_version == "v2":
            return metax_v2.get_contract_datasets(self, pid)
        url = f"{self.baseurl}/datasets"
        params = {"preservation__contract": pid}
        response = extended_result(url, self, params)
        return [map_dataset(dataset) for dataset in response]

    def get_file(self, file_id, v2=False) -> MetaxFile:
        """Get file metadata from Metax.

        :param str file_id: id or identifier attribute of file
        :param bool v2: Parameter used in V2->3 migration period.
        :returns: file metadata as json
        """
        if self.api_version == "v2":
            return metax_v2.get_file(self, file_id, v2)

        url = f"{self.baseurl}/files/{file_id}"
        response = self.get(url, allowed_status_codes=[404])
        if response.status_code == 404:
            raise FileNotAvailableError
        return map_file(response.json())

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
        files = []
        url = f"{self.baseurl}/files?limit=10000&csc_project={project}"
        # GET 10000 files every iteration until all files are read
        files = extended_result(url, self)

        file_dict = {}
        for _file in files:
            file_dict[_file["pathname"]] = {
                "identifier": _file["id"],
                "storage_service": _file["storage_service"],
            }
        return file_dict

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
            return metax_v2.get_directory_id(self, project, path)
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
        if state == DS_STATE_ACCEPTED_TO_DIGITAL_PRESERVATION:
            self.copy_dataset_to_pas_catalog(dataset_id)

        url = f"{self.baseurl}/datasets/{dataset_id}/preservation"
        # TODO: description has a language support, e.g. it expects
        # a dictionary in format {'en': '<desc>', 'und':'<desc>, 'fi':....}
        # such format is not currently used in services using this method.
        # We seem to only use english description, so for now this is just
        # coped in this method.
        data = {
            "state": state,
            "description": {"en": description},
        }
        self.patch(url, json=data)

    def copy_dataset_to_pas_catalog(self, dataset_id):
        """Copies dataset to the PAS catalog.

        Dataset can be copied only if it has a contract and
        a preservation state set.

        :param str dataset_id: id of the dataset
        :returns: ``None``
        """
        if self.api_version == 'v2':
            raise NotImplementedError("Metax API V2 support not implemented")
        dataset = self.get_dataset(dataset_id)
        if dataset["preservation"]["contract"] is None:
            raise ValueError("Dataset has no contract set.")
        url = (
            f"{self.baseurl}/datasets/"
            + f"{dataset_id}/create-preservation-version"
        )
        self.post(url)

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
        url = f"{self.baseurl}/datasets/{dataset_id}/preservation"
        self.patch(url, json={"reason_description": reason})

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

        characteristics_url = f"{self.baseurl}/files/{file_id}/characteristics"
        extension_url = f"{self.baseurl}/files/{file_id}"
        self.patch(
            characteristics_url,
            json=file_characteristics.get("characteristics", {}),
        )
        self.patch(
            extension_url,
            json={
                "characteristics_extension": file_characteristics.get(
                    "characteristics_extension"
                )
            },
        )

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
        url = f"{self.baseurl}/datasets/{dataset_id}/metadata-download"
        params = {"format": "datacite"}
        response = self.get(
            url, allowed_status_codes=[400, 404], params=params
        )
        if response.status_code == 400:
            detail = response.json()["detail"]
            raise DataciteGenerationError(
                f"Datacite generation failed: {detail}"
            )
        if response.status_code == 404:
            raise DatasetNotAvailableError
        # pylint: disable=no-member
        return response.content

    def get_dataset_file_count(self, dataset_id):
        """
        Get total file count for a dataset in Metax, including those
        in directories.

        :param str dataset_id: id or identifier of dataset
        :raises DatasetNotAvailableError: If dataset is not available

        :returns: total count of files
        """
        if self.api_version == "v2":
            return metax_v2.get_dataset_file_count(self, dataset_id)
        url = f"{self.baseurl}/datasets/{dataset_id}"
        response = self.get(url, allowed_status_codes=[404])
        if response.status_code == 404:
            raise DatasetNotAvailableError
        result = response.json()
        if result["fileset"] is not None:
            return result["fileset"]["total_files_count"]
        else:
            return 0

    def get_dataset_files(self, dataset_id) -> list[MetaxFile]:
        """Get files metadata of dataset Metax.

        :param str dataset_id: id or identifier attribute of dataset
        :returns: metadata of dataset files as json
        """
        if self.api_version == "v2":
            return metax_v2.get_dataset_files(self, dataset_id)
        url = f"{self.baseurl}/datasets/{dataset_id}/files?limit=10000"
        result = []
        while url is not None:
            response = self.get(url, allowed_status_codes=[404])
            if response.status_code == 404:
                raise DatasetNotAvailableError
            url = response.json()["next"]
            result.extend(response.json()["results"])

        return [map_file(file) for file in result]

    def get_file_datasets(self, file_id):
        """Get a list of research datasets associated with file_id.

        :param file_id: File identifier
        :returns: List of datasets associated with file_id
        """
        if self.api_version == "v2":
            return metax_v2.get_file_datasets(self, file_id)
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
        if not file_ids:
            # Querying with an empty list of file IDs causes an error
            # with Metax V2 and is silly anyway, since the result would be
            # empty as well.
            return {}
        url = f"{self.baseurl}/files/datasets?relations=true"
        response = self.post(url, json=file_ids)
        return response.json()

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

        url = f"{self.baseurl}/files/delete-many"
        response = self.delete(
            url,
            json=[{"id": file_id} for file_id in file_id_list]
        )

        return response

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
        url = f"{self.baseurl}/files"
        response = self.post(
            url, json=metadata, allowed_status_codes=[400, 404]
        )
        if response.status_code == 404:
            raise FileNotAvailableError
        if response.status_code == 400:
            # Read the response and parse list of failed files
            try:
                failed_files = response.json()["failed"]
            except KeyError:
                # Most likely only one file was posted, so Metax
                # response is formatted differently: just one error
                # instead of list of errors
                failed_files = [
                    {"object": metadata, "errors": response.json()}
                ]
            # If all errors are caused by files that already exist,
            # raise ResourceAlreadyExistsError.
            all_errors = []
            for file_ in failed_files:
                for error_message in file_["errors"].values():
                    all_errors.extend(error_message)
            path_exists_pattern = (
                "a file with path .* already exists in project .*"
            )
            identifier_exists_pattern = (
                "a file with given identifier already exists"
            )
            if all(
                re.search(path_exists_pattern, string)
                or re.search(identifier_exists_pattern, string)
                for string in all_errors
            ):
                raise ResourceAlreadyExistsError(
                    "Some of the files already exist.", response=response
                )
            # Raise HTTPError for unknown "bad request error"
            response.raise_for_status()

        return response.json()

    def post_dataset(self, metadata):
        """Post dataset metadata.

        :param metadata: dataset metadata dictionary
        :returns: JSON response from Metax
        """
        if self.api_version == "v2":
            return metax_v2.post_dataset(self, metadata)
        url = f"{self.baseurl}/datasets"
        response = self.post(url, json=metadata)
        return map_dataset(response.json())

    def post_contract(self, metadata):
        """Post contract metadata.

        :param metadata: contract metadata dictionary
        :returns: JSON response from Metax
        """
        if self.api_version == "v2":
            return metax_v2.post_contract(self, metadata)
        url = f"{self.baseurl}/contracts"
        response = self.post(url, json=metadata)
        return map_contract(response.json())

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
        raise NotImplementedError(
            "Metax API V3 support will not be implemented. "
            "Use `get_dataset_directory` instead."
        )

    def get_dataset_directory(self, dataset_id: str, path: str):
        """Get directory metadata, directories and files for given dataset.

        :param dataset_id: Dataset identifier
        :param path: Path of the directory
        """
        if self.api_version == "v2":
            raise NotImplementedError(
                "This is a V3 only API. Get with the times."
            )

        url = f"{self.baseurl}/datasets/{dataset_id}/directories"
        response = self.get(
            url, params={"path": path, "limit": 10_000},
            allowed_status_codes=[404]
        )
        if response.status_code == 404:
            raise DirectoryNotAvailableError  # noqa: F405

        data = response.json()

        result = {
            "directory": data["results"]["directory"],
            "directories": data["results"]["directories"],
            "files": data["results"]["files"]
        }

        # Endpoint has pagination that involves two lists at the same time:
        # 'files' and 'directories'
        next = data["next"]

        while next:
            response = self.get(next)
            data = response.json()
            result["directories"] += data["results"]["directories"]
            result["files"] += data["results"]["files"]
            next = data["next"]

        return map_directory_files(result)

    def get_project_file(self, project, path) -> MetaxFile:
        """Get file of project by path.

        :param str project: project identifier of the file
        :param str path: path of the file
        :returns: file metadata
        """
        if self.api_version == "v2":
            return metax_v2.get_project_file(self, project, path)
        url = f"{self.baseurl}/files"
        result = extended_result(
            url, self, params={"pathname": path, "csc_project": project}
        )
        try:
            return next(
                map_file(file)
                for file in result
                if file["pathname"].strip("/") == path.strip("/")
            )
        except StopIteration:
            raise FileNotAvailableError

    def lock_dataset(self, dataset_id: str):
        """Lock the dataset's files and the dataset.

        This will prevent the dataset and its file metadata from being updated.

        :param dataset_id: Dataset identifier
        """
        if self.api_version == "v2":
            raise ValueError(
                "Dataset locking not available for Metax V2"
            )

        # Lock the dataset first; this should hopefully prevent files
        # from being added/removed, which is probably the lesser evil.
        self.request(
            "PATCH",
            f"{self.baseurl}/datasets/{dataset_id}/preservation",
            json={"pas_process_running": True}
        )

        # TODO: Metax V3 does not allow retrieving only selected fields
        # for files (yet); retrieving only 'id' would be far more efficient.
        files = self.get_dataset_files(dataset_id)

        self.post(
            f"{self.baseurl}/files/patch-many",
            json=[
                {
                    "id": file_["id"],
                    "pas_process_running": True
                }
                for file_ in files
            ]
        )

    def unlock_dataset(self, dataset_id: str):
        """Unlock dataset.

        This will allow the dataset and its file metadata to be updated.

        :param dataset_id: Dataset identifier
        """
        if self.api_version == "v2":
            raise ValueError(
                "Dataset locking not available for Metax V2"
            )

        # Unlock files first; if we unlock the dataset first there is a small
        # chance that files could be removed from the dataset, meaning they
        # won't be unlocked.
        # TODO: Metax V3 does not allow retrieving only selected fields
        # for files (yet); retrieving only 'id' would be far more efficient.
        files = self.get_dataset_files(dataset_id)

        self.post(
            f"{self.baseurl}/files/patch-many",
            json=[
                {
                    "id": file_["id"],
                    "pas_process_running": False
                }
                for file_ in files
            ]
        )

        self.request(
            "PATCH",
            f"{self.baseurl}/datasets/{dataset_id}/preservation",
            json={"pas_process_running": False}
        )

    def get_file_format_versions(self):
        """Get reference data for file formats.

        :returns: Reference data for file formats
        """
        if self.api_version == "v2":
            error = "This method has only Metax API V3 support"
            raise NotImplementedError(error)

        url = f"{self.baseurl}/reference-data/file-format-versions"
        params = {"pagination": False}
        response = self.get(url, params=params)
        result = response.json()

        return [
            {
                "url": file_format_version["url"],
                "file_format": file_format_version["file_format"],
                "format_version": file_format_version["format_version"],
            }
            for file_format_version in result
        ]

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

        if self.api_version == "v3":
            try:
                kwargs.setdefault("params", {}).setdefault(
                    "include_nulls", True
                )
            except (AttributeError, TypeError):
                # 'params' is a 'param -> list[value]' mapping instead of
                # 'param -> value' mapping. Add `include_nulls` at the
                # beginning; this ensures any explicit 'include_nulls' provided
                # by the caller will be honored.
                kwargs["params"].insert(0, ("include_nulls", True))

        if self.token:
            if self.api_version == "v2":
                if "headers" in kwargs:
                    kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
                else:
                    kwargs["headers"] = {
                        "Authorization": f"Bearer {self.token}"
                    }
            if self.api_version == "v3":
                kwargs["headers"] = {"Authorization": f"Token {self.token}"}
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
