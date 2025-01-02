"""Metax v2 implementation."""

import re
from typing import Union

import metax_access.v3_to_v2_converter as v3_to_v2_converter
from metax_access.response import MetaxFile
from metax_access.v2_to_v3_converter import (
    convert_contract,
    convert_dataset,
    convert_directory_files_response,
    convert_file,
)
from metax_access.response_mapper import (
    map_dataset,
    map_contract,
    map_file,
    map_directory_files,
)
from metax_access.utils import update_nested_dict


# plint: disable=too-many-arguments
def get_datasets(
    metax,
    states,
    limit,
    offset,
    pas_filter,
    metadata_owner_org,
    metadata_provider_user,
    ordering,
    include_user_metadata,
    DatasetNotAvailableError,
    DS_STATE_ALL_STATES,
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
    if states is None:
        states = ",".join(str(state) for state in DS_STATE_ALL_STATES)
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
    url = f"{metax.baseurl}/datasets"
    response = metax.get(url, allowed_status_codes=[404], params=params)
    if response.status_code == 404:
        raise DatasetNotAvailableError
    json = response.json()
    if "results" in json:
        json["results"] = [
            map_dataset(convert_dataset(d, metax)) for d in json["results"]
        ]
    return json


def query_datasets(metax, param_dict):
    """Get datasets from metax based on query parameters.
    :param dict param_dict: a dictionary containing attribute-value -pairs
        to be used as query parameters
    :returns: datasets from Metax as json.
    """
    url = f"{metax.baseurl}/datasets"
    response = metax.get(url, params=param_dict)
    json = response.json()
    if "results" in json:
        json["results"] = [
            map_dataset(convert_dataset(d, metax)) for d in json["results"]
        ]
    return json


def get_datasets_by_ids(
    metax, dataset_ids, limit=1000000, offset=0, fields=None
):
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
    url = f"{metax.url}/rest/datasets/list"
    params = {"limit": str(limit), "offset": str(offset)}
    if fields:
        params["fields"] = ",".join(fields)
    response = metax.post(url, json=dataset_ids, params=params)
    json = response.json()
    if "results" in json:
        json["results"] = [
            map_dataset(convert_dataset(d, metax)) for d in json["results"]
        ]
    return json


def get_contracts(metax, limit, offset, org_filter, ContractNotAvailableError):
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
    url = f"{metax.baseurl}/contracts"
    response = metax.get(url, allowed_status_codes=[404], params=params)
    if response.status_code == 404:
        raise ContractNotAvailableError
    json = response.json()
    json |= {
        "results": [
            map_contract(convert_contract(contract))
            for contract in json.get("results", [])
        ]
    }
    return json


def get_contract(metax, pid, ContractNotAvailableError):
    """Get the contract data from Metax.
    :param str pid: id or ientifier attribute of contract
    :returns: The contract from Metax as json.
    """
    url = f"{metax.baseurl}/contracts/{pid}"
    response = metax.get(url, allowed_status_codes=[404])
    if response.status_code == 404:
        raise ContractNotAvailableError
    return map_contract(convert_contract(response.json()))


def patch_contract(metax, contract_id, data):
    """Patch a contract.
    :param str contract_id: id or identifier of the contract
    :param dict data: A contract metadata dictionary that contains only the
                      key/value pairs that will be updated
    :returns: ``None``
    """
    # The original data must be added to updated objects since Metax patch
    # request will just overwrite them
    original_data = metax.get_contract(contract_id)
    for key in data:
        if isinstance(data[key], dict) and key in original_data:
            data[key] = update_nested_dict(original_data[key], data[key])
    url = f"{metax.baseurl}/contracts/{contract_id}"
    response = metax.patch(url, json=v3_to_v2_converter.convert_contract(data))
    return map_contract(convert_contract(response.json()))


def get_dataset(
    metax, dataset_id, include_user_metadata, v2, DatasetNotAvailableError
):
    """Get dataset metadata from Metax.
    :param str dataset_id: id or identifier attribute of dataset
    :param bool include_user_metadata: Metax parameter for including
                                       metadata for files
    :returns: dataset as json
    """
    url = f"{metax.baseurl}/datasets/{dataset_id}"
    response = metax.get(
        url,
        allowed_status_codes=[404],
        params={
            "include_user_metadata": (
                "true" if include_user_metadata else "false"
            ),
            "file_details": "true",
        },
    )
    if response.status_code == 404:
        raise DatasetNotAvailableError
    return (
        map_dataset(convert_dataset(response.json(), metax))
        if not v2
        else response.json()
    )


def get_dataset_template(metax):
    """Get minimal dataset template.
    :returns: Template as json
    """
    response = metax.get(
        f"{metax.rpcurl}/datasets/get_minimal_dataset_template"
        "?type=enduser_pas"
    )
    template = response.json()
    return template


def get_datacatalog(metax, catalog_id, DataCatalogNotAvailableError):
    """Get the metadata of a datacatalog from Metax.
    TODO: Only used by metax access, not normalized
    :param str catalog_id: id or identifier attribute of the datacatalog
    :returns: The datacatalog as json.
    """
    url = f"{metax.baseurl}/datacatalogs/{catalog_id}"
    response = metax.get(url, allowed_status_codes=[404])
    if response.status_code == 404:
        raise DataCatalogNotAvailableError
    return response.json()


def patch_dataset(metax, dataset_id, data, overwrite_objects=False, v2=False):
    """Patch a dataset.S
    :param str dataset_id: id or identifier of the dataset
    :param dict data: A dataset dictionary that contains only the
                      key/value pairs that will be updated
    :returns: ``None``
    """
    if not v2:
        data = v3_to_v2_converter.convert_dataset(data)
    if not overwrite_objects:
        # The original data must be added to updated
        # objects since Metax patch
        # request will just overwrite them
        original_data = metax.get_dataset(dataset_id, v2=True)
        for key in data:
            if isinstance(data[key], dict) and key in original_data:
                data[key] = update_nested_dict(original_data[key], data[key])
    url = f"{metax.baseurl}/datasets/{dataset_id}"
    response = metax.patch(url, json=data)
    return response.json()


def get_contract_datasets(metax, pid):
    """Get the datasets of a contract from Metax.
    :param str pid: id or identifier attribute of contract
    :returns: The datasets from Metax as json.
    """
    url = f"{metax.baseurl}/contracts/{pid}/datasets"
    response = metax.get(url)
    return [
        map_dataset(convert_dataset(dataset, metax))
        for dataset in response.json()
    ]


def get_file(metax, file_id, v2, FileNotAvailableError) -> MetaxFile:
    """Get file metadata from Metax.
    :param str file_id: id or identifier attribute of file
    :returns: file metadata as json
    """
    url = f"{metax.baseurl}/files/{file_id}"
    response = metax.get(url, allowed_status_codes=[404])
    if response.status_code == 404:
        raise FileNotAvailableError
    return (
        map_file(convert_file(response.json())) if not v2 else response.json()
    )


def get_files(metax, project) -> list[MetaxFile]:
    """Get all files of a given project.
    :param project: project id
    :returns: list of files
    """
    files = []
    url = f"{metax.baseurl}/files?limit=10000&project_identifier={project}"
    # GET 10000 files every iteration until all files are read
    while url is not None:
        response = metax.get(url).json()
        url = response["next"]
        files.extend(response["results"])
    return [map_file(convert_file(file)) for file in files]


def get_files_dict(metax, project):
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
    files = metax.get_files(project)
    file_dict = {}
    for _file in files:
        file_dict[_file["pathname"]] = {
            "identifier": _file["id"],
            "storage_service": _file["storage_service"],
        }
    return file_dict


def get_directory_id(metax, project, path, DirectoryNotAvailableError):
    """Get the identifier of a direcotry with project and a path.
    The directory id will be deprecated in Metax V3 but the V2's
    directory identifier is available with this method.
    :param str project: project identifier of the directory
    :param str path: path of the directory
    :returns: directory identifier
    """
    url = f"{metax.baseurl}/directories/files"
    params = {
        "path": path,
        "project": project,
        "include_parent": "true",
    }
    response = metax.get(url, allowed_status_codes=[404], params=params)
    if response.status_code == 404:
        raise DirectoryNotAvailableError
    return response.json()["identifier"]


def set_preservation_state(metax, dataset_id, state, description):
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
    url = f"{metax.baseurl}/datasets/{dataset_id}"
    data = {
        "preservation_state": state,
        "preservation_description": description,
    }
    metax.patch(url, json=data)


def set_preservation_reason(metax, dataset_id, reason):
    """Set preservation reason of dataset.
    Sets value of `preservation_reason_description` for dataset in
    Metax.
    :param str dataset_id: id or identifier attribute of dataset in Metax
    :param str reason: The value for `preservation_reason_description`
    :returns: ``None``
    """
    url = f"{metax.baseurl}/datasets/{dataset_id}"
    metax.patch(url, json={"preservation_reason_description": reason})


def patch_file(metax, file_id, data):
    """Patch file metadata.
    :param str file_id: id or identifier of the file
    :param dict data: A file metadata dictionary that contains only the
                      key/value pairs that will be updated
    :returns: JSON response from Metax
    """
    # The original data must be added to updated objects since Metax patch
    # request will just overwrite them
    original_data = metax.get_file(file_id, v2=True)
    data = v3_to_v2_converter.convert_file(data)
    for key in data:
        if isinstance(data[key], dict) and key in original_data:
            data[key] = update_nested_dict(original_data[key], data[key])
    url = f"{metax.baseurl}/files/{file_id}"
    response = metax.patch(url, json=data)
    return response.json()


def patch_file_characteristics(metax, file_id, file_characteristics):
    """Patch file characteristics
    TODO: documentation
    """
    original_data = metax.get_file(file_id, v2=True).get(
        "file_characteristics", {}
    )
    data = v3_to_v2_converter.convert_file(file_characteristics)
    for key in data:
        if isinstance(data[key], dict) and key in original_data:
            data[key] = update_nested_dict(original_data[key], data[key])
    url = f"{metax.baseurl}/files/{file_id}"
    response = metax.patch(url, json=data)
    return response.json()


def get_datacite(
    metax,
    dataset_id,
    dummy_doi,
    DataciteGenerationError,
    DatasetNotAvailableError,
):
    """Get descriptive metadata in datacite xml format.
    :param dataset_id: id or identifier attribute of dataset
    :param dummy_doi: "false" or "true". "true" asks Metax to use
                      a dummy DOI if the actual DOI is not yet generated
    :returns: Datacite XML as string
    """
    url = f"{metax.baseurl}/datasets/{dataset_id}"
    params = {"dataset_format": "datacite", "dummy_doi": dummy_doi}
    response = metax.get(url, allowed_status_codes=[400, 404], params=params)
    if response.status_code == 400:
        detail = response.json()["detail"]
        raise DataciteGenerationError(f"Datacite generation failed: {detail}")
    if response.status_code == 404:
        raise DatasetNotAvailableError
    # pylint: disable=no-member
    return response.content


def get_dataset_file_count(metax, dataset_id, DatasetNotAvailableError):
    """
    Get total file count for a dataset in Metax, including those
    in directories.
    :param str dataset_id: id or identifier of dataset
    :raises DatasetNotAvailableError: If dataset is not available
    :returns: total count of files
    """
    url = f"{metax.baseurl}/datasets/{dataset_id}/files"
    response = metax.get(
        url, params={"file_fields": "id"}, allowed_status_codes=[404]
    )
    if response.status_code == 404:
        raise DatasetNotAvailableError
    result = response.json()
    return len(result)


def get_dataset_files(
    metax, dataset_id, DatasetNotAvailableError
) -> list[MetaxFile]:
    """Get files metadata of dataset Metax.
    :param str dataset_id: id or identifier attribute of dataset
    :returns: metadata of dataset files as json
    """
    url = f"{metax.baseurl}/datasets/{dataset_id}/files"
    response = metax.get(url, allowed_status_codes=[404])
    if response.status_code == 404:
        raise DatasetNotAvailableError
    # use category is defined only in research dataset
    research_dataset_file_info = {
        file.get("identifier"): file
        for file in metax.get_dataset(dataset_id, v2=True)
        .get("research_dataset", {})
        .get("files", [])
    }
    return [
        map_file(
            convert_file(
                file,
                research_dataset_file_info.get(file.get("identifier"), {}),
            )
        )
        for file in response.json()
    ]


def get_file_datasets(metax, file_id, FileNotAvailableError):
    """Get a list of research datasets associated with file_id.
    :param file_id: File identifier
    :returns: List of datasets associated with file_id
    """
    url = f"{metax.baseurl}/files/datasets"
    response = metax.post(url, allowed_status_codes=[404], json=[file_id])
    if response.status_code == 404:
        raise FileNotAvailableError
    # same output is given by
    # 'https://metax.fd-test.csc.fi/v3/files/datasets?relations=false'
    return response.json()


def get_file2dataset_dict(metax, file_ids):
    """Get a dict of {file_identifier: [dataset_identifier...] mappings
    :param file_ids: List of file IDs
    :returns: Dictionary with the format
              {file_identifier: [dataset_identifier1, ...]}
    """
    if not file_ids:
        # Querying with an empty list of file IDs causes an error
        # with Metax V2 and is silly anyway, since the result would be
        # empty as well.
        return {}
    url = f"{metax.baseurl}/files/datasets?keys=files"
    response = metax.post(url, json=file_ids)
    # same output is given by
    # 'https://metax.fd-test.csc.fi/v3/files/datasets?relations=true'
    result = response.json()
    if not result:
        # Metax API always returns an empty list if there are no results,
        # even if the response would otherwise be a dictionary.
        # Take care of this inconsistency by returning an empty dict
        # instead.
        return {}
    return response.json()


def delete_file(metax, file_id):
    """Delete metadata of a file.
    :param file_id: file identifier
    :returns: JSON response from Metax
    """
    url = f"{metax.baseurl}/files/{file_id}"
    response = metax.delete(url)
    return response.json()


def delete_files(metax, file_id_list):
    """Delete file metadata from Metax.
    :param file_id_list: List of ids to delete from Metax
    :returns: JSON returned by Metax
    """
    url = f"{metax.baseurl}/files"
    response = metax.delete(url, json=file_id_list)
    return response.json()


def delete_dataset(metax, dataset_id):
    """Delete metadata of dataset.
    :param dataset_id: dataset identifier
    :returns: ``None``
    """
    url = f"{metax.baseurl}/datasets/{dataset_id}"
    metax.delete(url)


def post_file(
    metax,
    metadata: Union[MetaxFile, list[MetaxFile]],
    FileNotAvailableError,
    ResourceAlreadyExistsError,
):
    """Post file metadata.
    :param metadata: file metadata dictionary or list of files
    :returns: JSON response from Metax
    """
    url = f"{metax.baseurl}/files/"
    if isinstance(metadata, list):
        # List of files
        metadata = [
            v3_to_v2_converter.convert_file(metadata_)
            for metadata_ in metadata
        ]
    else:
        # Single file
        metadata = v3_to_v2_converter.convert_file(metadata)
    response = metax.post(url, json=metadata, allowed_status_codes=[400, 404])
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
            failed_files = [{"object": metadata, "errors": response.json()}]
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
    # We don't seem to process this response in any way, so
    # no normalization needs to be done for this. Chances are any would-be
    # users will just print it directly.
    return response.json()


def post_dataset(metax, metadata):
    """Post dataset metadata.
    :param metadata: dataset metadata dictionary
    :returns: JSON response from Metax
    """
    url = f"{metax.baseurl}/datasets/"
    response = metax.post(url, json=metadata)
    return response.json()


def post_contract(metax, metadata):
    """Post contract metadata.
    :param metadata: contract metadata dictionary
    :returns: JSON response from Metax
    """
    url = f"{metax.baseurl}/contracts/"
    response = metax.post(
        url, json=v3_to_v2_converter.convert_contract(metadata)
    )
    return convert_contract(response.json())


def delete_contract(metax, contract_id):
    """Delete metadata of contract.
    :param dataset_id: contract identifier
    :returns: ``None``
    """
    url = f"{metax.baseurl}/contracts/{contract_id}"
    metax.delete(url)


def get_project_directory(
    metax, project, path, dataset_identifier, DirectoryNotAvailableError
):
    """Get directory metadata, directories, and files of project by path.
    :param str project: project identifier of the directory
    :param str path: path of the directory
    :param str dataset_identifier: Only list files and directories
                                   that are part of specified
                                   dataset
    :returns: directory metadata
    """
    url = f"{metax.baseurl}/directories/files"
    params = {
        "path": path,
        "project": project,
        "depth": 1,
        "include_parent": "true",
    }
    if dataset_identifier:
        params["cr_identifier"] = dataset_identifier
    response = metax.get(url, allowed_status_codes=[404], params=params)
    if response.status_code == 404:
        raise DirectoryNotAvailableError
    response_json = convert_directory_files_response(response.json())
    response_json |= {"results": map_directory_files(response_json["results"])}
    return response_json


def get_project_file(metax, project, path, FileNotAvailableError) -> MetaxFile:
    """Get file of project by path.
    :param str project: project identifier of the file
    :param str path: path of the file
    :returns: directory metadata
    """
    url = f"{metax.baseurl}/files"
    response = metax.get(
        url, params={"file_path": path, "project_identifier": project}
    )
    try:
        return next(
            map_file(convert_file(file))
            for file in response.json()["results"]
            if file["file_path"].strip("/") == path.strip("/")
        )
    except StopIteration:
        raise FileNotAvailableError
