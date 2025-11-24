"""Metax interface class."""
from __future__ import annotations

import logging
import re
from typing import Any, TypedDict
from urllib.parse import parse_qs, urlparse, urlencode

import requests

from metax_access.error import (
    ContractNotAvailableError,
    DataciteGenerationError,
    DatasetNotAvailableError,
    FileNotAvailableError,
    ResourceAlreadyExistsError,
)
from metax_access.response import (
    MetaxContract,
    MetaxDataset,
    MetaxDirectoryFiles,
    MetaxFile,
    MetaxFileCharacteristics,
    MetaxFileFormatVersion,
)
from metax_access.response_mapper import (
    map_contract,
    map_dataset,
    map_directory_files,
    map_file,
)
from metax_access.utils import extended_result, update_nested_dict

# These imports are used by other projects (eg. upload-rest-api)
# pylint: disable=unused-import
from metax_access import (  # noqa: F401 isort:skip
    DS_STATE_ALL_STATES,
    DS_STATE_DATASET_VALIDATED,
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
    DS_STATE_VALIDATING_METADATA,
)

logger = logging.getLogger(__name__)


class _DatasetJsonResponse(TypedDict):
    results: list[MetaxDataset]


class _ContractJsonResponse(TypedDict):
    results: list[MetaxContract]


# pylint: disable=too-many-public-methods
class Metax:
    """Get metadata from metax as dict object."""

    def __init__(self, url, token, verify=True):
        """Initialize Metax object.

        :param url: Metax url
        :param token: Metax access token
        :param verify: Use SSL verification. `True` by default.
        """
        self.token = token
        self.url = url
        self.baseurl = f"{url}/v3"
        self.verify = verify

    # pylint: disable=too-many-arguments
    def get_datasets(
        self,
        states: str | None = None,
        limit: str = "1000000",
        offset: str = "0",
        metadata_owner_org: str | None = None,
        metadata_owner_user: str | None = None,
        ordering: str | None = None,
        search: str | None = None,
    ) -> _DatasetJsonResponse:
        """Get the metadata of datasets from Metax.

        :param str states: dataset preservation state value as a string
            e.g "10" for filtering.
        :param str limit: max number of datasets to be returned
        :param str offset: offset for paging
        :param str metadata_owner_org: Filter by dataset field
                                       metadata_owner_org
        :param str metadata_owner_user: Filter by dataset field
                                        metadata_owner_user.
        :param str ordering: metax dataset attribute for sorting
            datasets.
        :param str search: string for filtering datasets.
        :returns: datasets from Metax as json.
        """
        params = {
            "search": search,
            "metadata_owner__organization": metadata_owner_org,
            "metadata_owner__user": metadata_owner_user,
            "ordering": ordering,
            "preservation__state": states,
            "limit": limit,
            "offset": offset,
        }

        url = f"{self.baseurl}/datasets"
        response = self.get(url, allowed_status_codes=[404], params=params)
        if response.status_code == 404:
            raise DatasetNotAvailableError
        json: _DatasetJsonResponse = response.json()
        json["results"] = [map_dataset(dataset) for dataset in json["results"]]
        return json

    def get_datasets_by_ids(
        self, dataset_ids: list[str]
    ) -> list[MetaxDataset]:
        """Get datasets with given identifiers.

        :param list dataset_ids: Dataset identifiers
        :returns: List of found datasets
        """
        # TODO: This is initially get_datasets with extra params
        # and could be merged with get_datasets method.

        # This method is only used by upload_rest_api and no error is raised
        # in metax if dataset id does not exist, the non existens datasets
        # are simply left out from the response.
        dataset_results = []
        batch_size = 100
        total_batches = (len(dataset_ids) // batch_size) + 1

        for i in range(total_batches):
            if batch_ids := dataset_ids[i * batch_size:(i + 1) * batch_size]:
                params = {"id": ",".join(batch_ids), "pagination": False}
                url = f"{self.baseurl}/datasets"
                response = self.get(url, params=params)
                dataset_results.extend(response.json())

        return [map_dataset(dataset) for dataset in dataset_results]

    def get_contracts(
        self, limit: str = "1000000", offset: str = "0"
    ) -> _ContractJsonResponse:
        """Get the data for contracts list from Metax.

        :param str limit: max number of contracts to be returned
        :param str offset: offset for paging
        :returns: contracts from Metax as json.
        """
        params = {"limit": limit, "offset": offset}
        url = f"{self.baseurl}/contracts"
        response = self.get(url, allowed_status_codes=[404], params=params)
        if response.status_code == 404:
            raise ContractNotAvailableError
        json: _ContractJsonResponse = response.json()
        json["results"] = [
            map_contract(contract) for contract in json.get("results", [])
        ]
        return json

    def get_contract(self, pid: str) -> MetaxContract:
        """Get the contract data from Metax.

        :param str pid: Identifier of the contract
        :returns: The contract from Metax as json.
        """
        url = f"{self.baseurl}/contracts/{pid}"
        response = self.get(url, allowed_status_codes=[404])
        if response.status_code == 404:
            raise ContractNotAvailableError
        return map_contract(response.json())

    def patch_contract(
        self, contract_id: str, data: dict[str, Any]
    ) -> MetaxContract:
        """Patch a contract.

        :param str contract_id: Identifier of the contract
        :param dict data: A contract metadata dictionary that contains only the
                          key/value pairs that will be updated
        :returns: Updated contract.
        """
        original_data = self.get_contract(contract_id)
        for key in data:
            if isinstance(data[key], dict) and key in original_data:
                data[key] = update_nested_dict(original_data[key], data[key])
        url = f"{self.baseurl}/contracts/{contract_id}"
        response = self.patch(url, json=data)
        return map_contract(response.json())

    def get_dataset(self, dataset_id: str) -> MetaxDataset:
        """Get dataset metadata from Metax.

        :param str dataset_id: Identifier of the dataset
        :returns: dataset as json
        """
        url = f"{self.baseurl}/datasets/{dataset_id}"
        response = self.get(
            url,
            allowed_status_codes=[404],
        )
        if response.status_code == 404:
            raise DatasetNotAvailableError
        return map_dataset(response.json())

    def set_contract(self, dataset_id: str, contract_id: str) -> dict:
        """Update the contract of a dataset.

        :param str dataset_id: Identifier of the dataset
        :param str contract_if: the new contract identifier of the
            dataset
        :returns: Json response
        """
        data = {"contract": contract_id}
        url = f"{self.baseurl}/datasets/{dataset_id}/preservation"
        response = self.patch(url, json=data)
        return response.json()

    def get_contract_datasets(self, pid: str) -> list[MetaxDataset]:
        """Get the datasets of a contract from Metax.

        :param str pid: Identifier of the contract
        :returns: The datasets from Metax as json.
        """
        url = f"{self.baseurl}/datasets"
        params = {"preservation__contract": pid}
        response = extended_result(url, self, params)
        return [map_dataset(dataset) for dataset in response]

    def get_file(self, file_id: str) -> MetaxFile:
        """Get file metadata from Metax.

        :param str file_id: Identifier of the file
        :returns: file metadata as json
        """
        url = f"{self.baseurl}/files/{file_id}"
        response = self.get(url, allowed_status_codes=[404])
        if response.status_code == 404:
            raise FileNotAvailableError
        return map_file(response.json())

    def get_dataset_file(self, dataset_id: str, file_id: str) -> MetaxFile:
        """Get file metadata with dataset specific metadata.

        :param str dataset_id: Identifier of the dataset
        :param str file_id: Identifier of the file
        :returns: File metadata as json
        """
        url = f"{self.baseurl}/datasets/{dataset_id}/files/{file_id}"
        response = self.get(url, allowed_status_codes=[404])
        if response.status_code == 404:
            raise FileNotAvailableError
        return map_file(response.json())

    def get_files_dict(self, project: str) -> dict[str, dict[str, str]]:
        """Get all the files of a given project.

        Files are returned as a dictionary:

            {
                file_path: {
                    "identifier": identifier
                    "storage_service" : storage_service
                }
            }

        :param project: project id
        :returns: Dict of all the files of a given project
        """
        files = []
        url = f"{self.baseurl}/files"
        # GET 10000 files every iteration until all files are read
        files = extended_result(
            url, self, params={"limit": 10000, "csc_project": project}
        )

        file_dict = {}
        for _file in files:
            file_dict[_file["pathname"]] = {
                "identifier": _file["id"],
                "storage_service": _file["storage_service"],
            }
        return file_dict

    def set_preservation_state(
        self, dataset_id: str, state: int, description: str
    ) -> None:
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

        :param str dataset_id: Identifier of the dataset
        :param int state: The value for `preservation_state`
        :param str description: The value for `preservation_description`
        :returns: ``None``
        """
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

    def copy_dataset_to_pas_catalog(self, dataset_id: str) -> None:
        """Copies dataset to the PAS catalog.

        Dataset can be copied only if it has a contract and
        a preservation state set.

        :param str dataset_id: Identifier of the dataset
        :returns: ``None``
        """
        dataset = self.get_dataset(dataset_id)
        if dataset["preservation"]["contract"] is None:
            raise ValueError("Dataset has no contract set.")
        url = (
            f"{self.baseurl}/datasets/"
            + f"{dataset_id}/create-preservation-version"
        )
        self.post(url)

    def set_preservation_reason(self, dataset_id: str, reason: str) -> None:
        """Set preservation reason of dataset.

        Sets value of `preservation_reason_description` for dataset in
        Metax.

        :param str dataset_id: Identifier of the dataset
        :param str reason: The value for `preservation_reason_description`
        :returns: ``None``
        """
        url = f"{self.baseurl}/datasets/{dataset_id}/preservation"
        self.patch(url, json={"reason_description": reason})

    def set_pas_package_created(self, dataset_id: str) -> None:
        """Set value of `pas_package_created` to True.

        When `pas_package_created` is True, it means that dataset has
        been preserved, and can be shown in Etsin. In Metax API V2,
        `preservation_state` was used to check if dataset has been
        preserved.

        Because the name of the variable is a little misleading, it is
        good to notice that when `pas_package_created` is False:

            * it does NOT mean that SIP has not been created
            * it does NOT mean that SIP has not been sent to digital
              preservation service
            * it does NOT mean that dataset has not been copied to PAS
              data catalog
            * it only means that the dataset is not preserved

        :param str dataset_id: Identifier of the dataset
        """
        url = f"{self.baseurl}/datasets/{dataset_id}/preservation"
        self.patch(url, json={"pas_package_created": True})

    def patch_file_characteristics(
        self, file_id: str, file_characteristics: MetaxFileCharacteristics
    ) -> None:
        """Patch file characteristics ja file_characteristics_extension

        :param str file_id: Identifier of the file
        :param dict file_characteristics: A dictionary including file
            characteristics and file characteristics extension fields.
            Only key/value pairs that will be updated are required.
        """
        characteristics_url = f"{self.baseurl}/files/{file_id}/characteristics"
        extension_url = f"{self.baseurl}/files/{file_id}"
        response = self.patch(
            characteristics_url,
            allowed_status_codes=[404],
            json=file_characteristics.get("characteristics", {}),
        )
        if response.status_code == 404:
            # File characteristics object does not exist, so it must be
            # created
            response = self.put(
                characteristics_url,
                allowed_status_codes=[404],
                json=file_characteristics.get("characteristics", {}),
            )
            if response.status_code == 404:
                # If also PUT fails, the file probably does not exist
                raise FileNotAvailableError

        self.patch(
            extension_url,
            json={
                "characteristics_extension": file_characteristics.get(
                    "characteristics_extension"
                )
            },
        )

    def get_datacite(self, dataset_id: str) -> bytes:
        """Get descriptive metadata in datacite xml format.

        :param dataset_id: Identifier of the dataset
        :returns: Datacite XML as bytes
        """
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

    def get_dataset_file_count(self, dataset_id: str) -> int:
        """
        Get total file count for a dataset in Metax, including those
        in directories.

        :param str dataset_id: Identifier of the dataset
        :raises DatasetNotAvailableError: If dataset is not available

        :returns: total count of files
        """
        url = f"{self.baseurl}/datasets/{dataset_id}"
        response = self.get(url, allowed_status_codes=[404])
        if response.status_code == 404:
            raise DatasetNotAvailableError
        result = response.json()
        if result["fileset"] is not None:
            return result["fileset"]["total_files_count"]
        return 0

    def get_dataset_files(
            self, dataset_id: str, fields: None | list[str] = None
            ) -> list[MetaxFile]:
        """Get files metadata of dataset Metax.

        :param dataset_id: Identifier of the dataset
        :param fields: If provided, only given fields are returned
        :returns: metadata of dataset files as json
        """
        params = {"limit": 10000}
        if fields:
            params["fields"] = ",".join(fields)

        url = f"{self.baseurl}/datasets/{dataset_id}/files?{urlencode(params)}"
        result = []
        while url is not None:
            response = self.get(url, allowed_status_codes=[404])
            if response.status_code == 404:
                raise DatasetNotAvailableError
            url = response.json()["next"]
            result.extend(response.json()["results"])

        if fields:
            # If custom fields were provided, only provide said fields
            # skipping the mapping
            return [
                {key: value for key, value in file.items() if key in fields}
                for file in result
            ]

        return [map_file(file) for file in result]

    def get_file2dataset_dict(self, file_storage_ids: list[str]) -> dict:
        """Get a dict of {file_identifier: [dataset_identifier...] mappings

        :param file_storage_ids: List of file storage identifiers
        :returns: Dictionary with the format
                  {file_identifier: [dataset_identifier1, ...]}
        """
        if not file_storage_ids:
            return {}
        url = (
            f"{self.baseurl}/files/datasets?relations=true&"
            f"storage_service=pas"
        )
        response = self.post(url, json=file_storage_ids)
        return response.json()

    def delete_files(self, files: list[str]) -> requests.Response:
        """Delete file metadata from Metax.

        :param files: List of files to be deleted
        :returns: JSON returned by Metax
        """
        url = f"{self.baseurl}/files/delete-many"
        return self.post(url, json=files)

    def post_files(self, metadata: list[MetaxFile]) -> dict:
        """Create multiple files

        :param metadata: list of files
        :returns: JSON response from Metax
        """
        if not isinstance(metadata, list):
            metadata = [metadata]

        # TODO: This endpoint does not handle 'include_nulls=true', which
        # should be fixed
        url = f"{self.baseurl}/files/post-many"
        response = self.post(url, json=metadata, allowed_status_codes=[400])
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
                    all_errors.append(error_message)

            unique_field_exists_pattern = (
                "A file with the same value already exists, .*"
            )
            file_exists_pattern = "File already exists.*"
            if all(
                re.search(unique_field_exists_pattern, string)
                or re.search(file_exists_pattern, string)
                for string in all_errors
            ):
                raise ResourceAlreadyExistsError(
                    "Some of the files already exist.", response=response
                )
            # Raise HTTPError for unknown "bad request error"
            response.raise_for_status()

        return response.json()

    def post_dataset(self, metadata: MetaxDataset) -> MetaxDataset:
        """Post dataset metadata.

        :param metadata: dataset metadata dictionary
        :returns: JSON response from Metax
        """
        url = f"{self.baseurl}/datasets"
        response = self.post(url, json=metadata)
        return map_dataset(response.json())

    def post_contract(self, metadata: MetaxContract) -> MetaxContract:
        """Post contract metadata.

        :param metadata: contract metadata dictionary
        :returns: JSON response from Metax
        """
        url = f"{self.baseurl}/contracts"
        response = self.post(url, json=metadata)
        return map_contract(response.json())

    def get_dataset_directory(
        self, dataset_id: str, path: str
    ) -> MetaxDirectoryFiles:
        """Get directory metadata, directories and files for given dataset.

        :param dataset_id: Dataset identifier
        :param path: Path of the directory
        """
        url = f"{self.baseurl}/datasets/{dataset_id}/directories"
        response = self.get(
            url,
            params={"path": path, "limit": 10_000},
            allowed_status_codes=[404],
        )
        if response.status_code == 404:
            # Instead of raising error, return empty lists
            return map_directory_files(
                {"directory": None, "directories": [], "files": []}
            )

        data = response.json()

        result: MetaxDirectoryFiles = {
            "directory": data["results"]["directory"],
            "directories": data["results"]["directories"],
            "files": data["results"]["files"],
        }

        # Endpoint has pagination that involves two lists at the same time:
        # 'files' and 'directories'
        next_ = data["next"]

        while next_:
            response = self.get(next_)
            data = response.json()
            result["directories"] += data["results"]["directories"]
            result["files"] += data["results"]["files"]
            next_ = data["next"]

        return map_directory_files(result)

    def get_project_file(self, project: str, path: str) -> MetaxFile:
        """Get file of project by path.

        :param str project: project identifier of the file
        :param str path: path of the file
        :returns: file metadata
        """
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
        except StopIteration as exc:
            raise FileNotAvailableError from exc

    def lock_dataset(self, dataset_id: str) -> None:
        """Lock the dataset's files and the dataset.

        This will prevent the dataset and its file metadata from being updated.

        :param dataset_id: Dataset identifier
        """
        # Lock the dataset first; this should hopefully prevent files
        # from being added/removed, which is probably the lesser evil.
        self.request(
            "PATCH",
            f"{self.baseurl}/datasets/{dataset_id}/preservation",
            json={"pas_process_running": True},
        )

        # TODO: Metax V3 does not allow retrieving only selected fields
        # for files (yet); retrieving only 'id' would be far more efficient.
        files = self.get_dataset_files(dataset_id)

        self.post(
            f"{self.baseurl}/files/patch-many",
            json=[
                {"id": file_["id"], "pas_process_running": True}
                for file_ in files
            ],
        )

    def unlock_dataset(self, dataset_id: str) -> None:
        """Unlock dataset.

        This will allow the dataset and its file metadata to be updated.

        :param dataset_id: Dataset identifier
        """
        # Unlock files first; if we unlock the dataset first there is a small
        # chance that files could be removed from the dataset, meaning they
        # won't be unlocked.
        # TODO: Metax V3 does not allow retrieving only selected fields
        # for files (yet); retrieving only 'id' would be far more efficient.
        files = self.get_dataset_files(dataset_id)

        self.post(
            f"{self.baseurl}/files/patch-many",
            json=[
                {"id": file_["id"], "pas_process_running": False}
                for file_ in files
            ],
        )

        self.request(
            "PATCH",
            f"{self.baseurl}/datasets/{dataset_id}/preservation",
            json={"pas_process_running": False},
        )

    def get_file_format_versions(self) -> list[MetaxFileFormatVersion]:
        """Get reference data for file formats.

        :returns: Reference data for file formats
        """
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

    def request(
        self,
        method: str,
        url: str,
        allowed_status_codes: list[int] | None = None,
        params: dict[str, str | list[str] | bool] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send authenticated HTTP request.

        This function is a wrapper function for requests.requets with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param method: HTTP method (eg. GET, POST, ...)
        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :param params: Query parameters
        :returns: requests response
        """
        if not allowed_status_codes:
            allowed_status_codes = []

        if params is None:
            params = {}

        if "verify" not in kwargs:
            kwargs["verify"] = self.verify

        # Move all query parameters from URL to a dict and ensure the query
        # string is left empty. This prevents the default `?include_nulls=True`
        # value from being appended again with each successive call when
        # iterating paginated results, eventually resulting in the URL
        # exceeding the length limit and causing a failure.
        url_params = parse_qs(urlparse(url).query)
        params = url_params | params  # Prioritize user params

        url = urlparse(url)._replace(query="").geturl()

        params.setdefault("include_nulls", True)

        kwargs["headers"] = {"Authorization": f"Token {self.token}"}

        response = requests.request(method, url, params=params, **kwargs)
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

    def get(
        self,
        url: str,
        allowed_status_codes: list[int] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send authenticated HTTP GET request.

        This function is a wrapper function for requests.get with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request("GET", url, allowed_status_codes, **kwargs)

    def patch(
        self,
        url: str,
        allowed_status_codes: list[int] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send authenticated HTTP PATCH request.

        This function is a wrapper function for requests.patch with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request("PATCH", url, allowed_status_codes, **kwargs)

    def post(
        self,
        url: str,
        allowed_status_codes: list[int] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send authenticated HTTP POST request.

        This function is a wrapper function for requests.post with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request("POST", url, allowed_status_codes, **kwargs)

    def put(
        self,
        url: str,
        allowed_status_codes: list[int] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send authenticated HTTP PUT request.

        This function is a wrapper function for requests.put with
        automatic authentication. Raises HTTPError if request fails with
        status code other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request("PUT", url, allowed_status_codes, **kwargs)

    def delete(
        self,
        url: str,
        allowed_status_codes: list[int] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Send authenticated HTTP DELETE request.

        This function is a wrapper function for requests.delete with automatic
        authentication. Raises HTTPError if request fails with status code
        other than one of the allowed status codes.

        :param url: Request URL
        :param allowed_status_codes: List of allowed HTTP error codes
        :returns: requests response
        """
        return self.request("DELETE", url, allowed_status_codes, **kwargs)
