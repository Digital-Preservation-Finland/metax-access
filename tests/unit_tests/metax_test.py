# pylint: disable=no-member
"""Tests for ``metax_access.metax`` module."""
import copy
from contextlib import ExitStack as does_not_raise
from urllib.parse import urlencode

import lxml.etree
import pytest
import requests

from metax_access import (
    DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
    Metax,
)
from metax_access.error import (ContractNotAvailableError,
                                DataciteGenerationError,
                                DatasetNotAvailableError,
                                FileNotAvailableError,
                                ResourceAlreadyExistsError)
from tests.unit_tests.utils import (V3_CONTRACT, V3_FILE,
                                    V3_MINIMUM_TEMPLATE_DATASET,
                                    create_test_v3_dataset,
                                    create_test_v3_file)

METAX_URL = "https://foobar"
METAX_REST_ROOT_URL = f"{METAX_URL}/rest"
METAX_REST_URL = f"{METAX_URL}/rest/v2"
METAX_RPC_URL = f"{METAX_URL}/rpc/v2"
METAX_USER = "tpas"
METAX_PASSWORD = "password"

DATASET = copy.deepcopy(V3_MINIMUM_TEMPLATE_DATASET)
del DATASET['created']
del DATASET['modified']


@pytest.fixture(autouse=True, scope='function')
def metax():
    """Metax V3 client instance"""
    return Metax(METAX_URL, token='token_foo', verify=False)


def test_init():
    """Test init function.

    Init function should raise exception if required parameters are not given.
    """
    with pytest.raises(ValueError) as exception:
        Metax(METAX_URL)
    assert str(exception.value) == "Metax user or access token is required."


def test_get_dataset_files(requests_mock, metax):
    """File metadata is retrived with ``get_dataset_files`` method and
    the output is compared to the expected output.
    """
    dataset_id = 'dataset_id'
    url = f'{metax.baseurl}/datasets/{dataset_id}/files'

    file_id = 'id_foo'
    expected_file = copy.deepcopy(V3_FILE)
    expected_file['id'] = file_id

    file_id2 = 'id_bar'
    expected_file2 = copy.deepcopy(V3_FILE)
    expected_file2['id'] = file_id2

    expected_output = [expected_file, expected_file2]

    json = {'next': None,'results': expected_output}

    requests_mock.get(
        url, json=json
    )
    files = metax.get_dataset_files(dataset_id)

    assert expected_output == files


def test_get_file(requests_mock, metax):
    """File metadata is retrived with ``get_file`` method and
    the output is compared to the expected output.
    """
    file_id = 'id_foo'
    url = f'{metax.baseurl}/files/{file_id}'
    expected_file = copy.deepcopy(V3_FILE)
    expected_file['id'] = file_id
    json = expected_file

    requests_mock.get(url, json=json)
    file = metax.get_file(file_id)
    assert file == expected_file


def test_get_datasets(requests_mock, caplog, metax):
    """Test ``get_datasets`` function.

    Mocks Metax to return simple JSON as HTTP response and checks that the
    returned dict contains the correct values.

    :returns: None
    """
    ids = ['foo', 'bar']
    expected_datasets = [_update_dict(DATASET, {'id': id_}) for id_ in ids]
    json = [_update_dict(V3_MINIMUM_TEMPLATE_DATASET, {'id': id_})
            for id_ in ids]
    metax_mock = requests_mock.get(
        f"{metax.baseurl}/datasets/foo/files", json={}
    )
    metax_mock = requests_mock.get(
        f"{metax.baseurl}/datasets/bar/files", json={}
    )
    metax_mock = requests_mock.get(
        f"{metax.baseurl}/datasets",
        json={"results": json},
    )

    datasets = metax.get_datasets()

    assert len(datasets["results"]) == 2
    # Check that correct query parameter were used
    query_string = metax_mock.last_request.qs
    assert query_string["limit"][0] == "1000000"
    assert query_string["offset"][0] == "0"

    # No errors should be logged
    logged_errors = [r for r in caplog.records if r.levelname == "ERROR"]
    assert not logged_errors

    _check_values(datasets['results'][0], expected_datasets[0])
    _check_values(datasets['results'][1], expected_datasets[1])


def test_get_datasets_with_parameters(requests_mock, metax):
    """Test ``get_datasets`` function parameters.

    :returns: None
    """
    json = {'results':[V3_MINIMUM_TEMPLATE_DATASET]}
    metax_mock = requests_mock.get(f'{metax.baseurl}/datasets', json=json)
    datasets = metax.get_datasets(
        states="states-param",
        limit="limit-param",
        offset="offset-param",
        pas_filter="pas-filter-param",
        metadata_owner_org="owner-org-param",
        metadata_provider_user="provider-user-param",
        ordering="ordering-param",
        include_user_metadata=False,
        search='search-param',
        metadata_owner_user='metadata-owner-user'
    )['results']
    query_string = metax_mock.last_request.qs
    assert query_string["limit"][0] == "limit-param"
    assert query_string["offset"][0] == "offset-param"
    assert query_string["ordering"][0] == "ordering-param"
    assert query_string["preservation__state"][0] == "states-param"
    assert query_string["search"][0] == "search-param"
    assert query_string["metadata_owner__organization"][0] == "owner-org-param"
    assert query_string["metadata_owner__user"][0] == "metadata-owner-user"

    _check_values(datasets[0], DATASET)


def test_get_dataset(requests_mock, metax):
    """Test ``get_dataset`` function.

    Mocks Metax to return simple JSON as HTTP
    response and checks that the returned dict contains the correct values.

    :returns: None
    """
    dataset_id = "123"
    url = f"{metax.baseurl}/datasets/{dataset_id}"
    json = copy.deepcopy(V3_MINIMUM_TEMPLATE_DATASET)
    json["id"] = dataset_id

    requests_mock.get(
        url,
        json=json,
    )

    dataset = metax.get_dataset(dataset_id)

    expected_dataset = copy.deepcopy(DATASET)
    expected_dataset["id"] = dataset_id
    _check_values(dataset, expected_dataset)


def test_get_contracts(requests_mock, metax):
    """Test ``get_contracts`` function.

    Mocks Metax to return simple JSON as HTTP
    response and checks that the returned dict contains the correct values.

    :returns: None
    """
    ids = ['foo', 'bar']
    contract = copy.deepcopy(V3_CONTRACT)
    del contract['id']
    expected_contracts = [
        _update_dict(contract,
                     {'id': id_})
                     for id_ in ids
    ]
    v3_output_contracts = [
        _update_dict(contract,
                     {'id': id_})
                     for id_ in ids
    ]
    json = {
            "results": v3_output_contracts
        }
    requests_mock.get(
        f'{metax.baseurl}/contracts',
        json=json,
    )
    contracts = metax.get_contracts()
    assert len(contracts["results"]) == 2
    assert expected_contracts == contracts['results']


def test_get_contract(requests_mock, metax):
    """Test ``get_contract`` function.

    Mocks Metax to return simple JSON as HTTP
    response and checks that the returned dict contains the correct values.

    :returns: None
    """
    contract_id = "bar"
    url = f"{metax.baseurl}/contracts/{contract_id}"
    contract = copy.deepcopy(V3_CONTRACT)
    del contract['id']
    expected_contract = copy.deepcopy(contract)
    expected_contract |= {"id": contract_id}
    v3_output = copy.deepcopy(V3_CONTRACT)
    v3_output |= {'id': contract_id}
    json = v3_output

    requests_mock.get(url, json=json)

    contract = metax.get_contract(contract_id)
    assert expected_contract == contract


def test_get_dataset_file_count(requests_mock, metax):
    """Test retrieving the total file count for a dataset."""

    def _request_has_correct_params(req):
        return req.qs["file_fields"] == ["id"]

    url = f"{metax.baseurl}/datasets/fake-dataset"
    json = {"fileset": {"total_files_count": 3}}

    requests_mock.get(
        url,
        json=json,
    )

    file_count = metax.get_dataset_file_count("fake-dataset")
    assert file_count == 3


def test_get_dataset_file_count_not_found(requests_mock, metax):
    """
    Test retrieving the total file count for a dataset and ensure that
    DatasetNotAvailableError is raised if the dataset does not exist.
    """

    url = f"{metax.baseurl}/datasets/does-not-exist"
    requests_mock.get(
        url,
        status_code=404,
    )

    with pytest.raises(DatasetNotAvailableError):
        metax.get_dataset_file_count("does-not-exist")


def test_set_contract(requests_mock, metax):
    """Test ``set_contract`` function.

    Patch the contract of a dataset and check that a correct
    HTTP request was sent to Metax.

    :returns: ``None``
    """
    dataset_id = 'test_id'
    url = f'{metax.baseurl}/datasets/{dataset_id}/preservation'
    requests_mock.patch(url, json={})
    # TODO: Only used in v2 test
    requests_mock.get(
        metax.baseurl + "/datasets/test_id",
        json={}
    )

    metax.set_contract(dataset_id, 'new:contract:id')
    assert requests_mock.last_request.method == "PATCH"

    request_body = requests_mock.last_request.json()
    assert request_body["contract"] == "new:contract:id"


def test_get_datacite(requests_mock, metax):
    """Test ``get_datacite`` function.

    Read one field from returned XML and check its correctness.

    :returns: ``None``
    """
    # Read sample datacite from file and create mocked HTTP response
    dataset_id = 'test_id'
    url = f'{metax.baseurl}/datasets/{dataset_id}/metadata-download?format=datacite&include_nulls=True'

    datacite = lxml.etree.parse("tests/data/datacite_sample.xml")
    requests_mock.get(url,
        complete_qs=True,
        content=lxml.etree.tostring(datacite),
    )

    xml = lxml.etree.fromstring(metax.get_datacite(dataset_id))

    # Read field "creatorName" from xml file
    ns_string = "http://datacite.org/schema/kernel-4"
    xpath_str = "/ns:resource/ns:creators/ns:creator/ns:creatorName"
    creatorname = xml.xpath(xpath_str, namespaces={"ns": ns_string})[0].text

    # Check that "creatorName" is same as in the original XML file
    assert creatorname == "Puupää, Pekka"


def test_get_datacite_fails(requests_mock, metax):
    """Test ``get_datacite`` function when Metax returns 400.

    :returns: ``None``
    """
    # Mock datacite request response. Mocked response has status code 400, and
    # response body contains error information.
    response = {
        "detail": "Foobar.",
        "error_identifier": "2019-03-28T12:39:01-f0a7e3ae",
    }
    requests_mock.get(
        f"{METAX_URL}/v3/datasets/foo/metadata-download?format=datacite",
        json=response,
        status_code=400,
    )

    with pytest.raises(DataciteGenerationError) as exception:
        metax.get_datacite("foo")

    assert exception.value.message == "Datacite generation failed: Foobar."


def test_set_preservation_state(requests_mock, metax):
    """Test ``set_preservation_state`` function.

    Metadata in Metax is modified by sending HTTP PATCH request with modified
    metadata in JSON format. This test checks that correct HTTP request is sent
    to Metax. The effect of the request is not tested.

    :returns: ``None``
    """
    requests_mock.patch(
        f"{metax.baseurl}/datasets/test_id/preservation"
    )

    metax.set_preservation_state(
        "test_id",
        DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
        "Accepted to preservation",
    )

    # Check the body of last HTTP request
    request_body = requests_mock.last_request.json()
    assert (
        request_body["state"]
        == DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE
    )
    assert (
        request_body["description"] == {"en": "Accepted to preservation"}
    )

    # Check the method of last HTTP request
    assert requests_mock.last_request.method == "PATCH"


def test_copy_dataset_to_pas_catalog(requests_mock, metax):
    """Test ``copy_dataset_to_pas_catalog`` function.

    Metadata in Metax is modified by sending HTTP PATCH request with
    modified metadata in JSON format. This test checks that correct HTTP
    request is sent to Metax and the PAS catalog endpoint was called
    with POST when dataset is copied to PAS data catalog.

    :returns: ``None``
    """
    dataset_id = "test_id"
    contract_id = "contract_id"
    url = (
        f"{metax.baseurl}/datasets/{dataset_id}/create-preservation-version"
    )
    dataset_url = f"{metax.baseurl}/datasets/{dataset_id}"
    response = copy.deepcopy(V3_MINIMUM_TEMPLATE_DATASET)
    response['id'] = dataset_id
    response['preservation']['contract'] = contract_id
    requests_mock.get(
        dataset_url,
        json=response
    )
    post_create_preservation_version = requests_mock.post(url)

    metax.copy_dataset_to_pas_catalog( dataset_id)

    # Check that expected request was sent to Metax
    assert post_create_preservation_version.called_once


def test_copy_dataset_to_pas_catalog_no_contract(requests_mock, metax):
    """"Test copy_dataset_to_pas_catalog function without a contract.

    A dataset without a contract can't be added to PAS Catalog.
    Check that an error is raised, for such dataset.
    """
    dataset_id = 'dataset_id'
    url = (
        f"{metax.baseurl}/datasets/{dataset_id}/create-preservation-version"
    )
    dataset_url = f"{metax.baseurl}/datasets/{dataset_id}"
    response = copy.deepcopy(V3_MINIMUM_TEMPLATE_DATASET)
    response['id'] = dataset_id
    requests_mock.get(
        dataset_url,
        json=response
    )
    requests_mock.post(url)

    with pytest.raises(
        ValueError,
        match="Dataset has no contract set.",
    ):
        metax.copy_dataset_to_pas_catalog(dataset_id)


def test_set_preservation_reason(requests_mock, metax):
    """Test ``set_preservation_reason`` method.

    Test that the method sends correct PATCH request to Metax.

    :returns: ``None``
    """
    dataset_id = 'test_id'
    url = f'{metax.baseurl}/datasets/{dataset_id}/preservation'
    requests_mock.patch(url)

    metax.set_preservation_reason(dataset_id, "The reason.")

    # Check the method of last HTTP request
    assert requests_mock.last_request.method == "PATCH"
    assert requests_mock.last_request.json() == {
        "reason_description": "The reason."
    }


def test_set_pas_package_created(requests_mock, metax):
    """Test `set_pas_package_created` method."""
    patch_preservation \
        = requests_mock.patch("/v3/datasets/test-dataset-id/preservation")
    metax.set_pas_package_created("test-dataset-id")
    assert patch_preservation.called_once
    assert patch_preservation.last_request.json() \
        == {"pas_package_created": True}


@pytest.mark.parametrize("patch_characteristics_status", [200, 404])
def test_patch_file_characteristics(requests_mock, metax,
                                    patch_characteristics_status):
    """Test patch_file_characteristics.

    :param requests_mock: HTTP Request mocker
    :param metax: Metax client
    :param patch_characteristics_status: HTTP status code of response
        for patching file characteristics.
    """
    # Mock Metax
    patch_characteristics = requests_mock.patch(
        f"{metax.baseurl}/files/file-id/characteristics",
        status_code=patch_characteristics_status
    )
    put_characteristics = requests_mock.put(
        f"{metax.baseurl}/files/file-id/characteristics",
    )
    patch_file = requests_mock.patch(
        f"{metax.baseurl}/files/file-id",
    )

    characteristics = {"ham": "spam"}
    extension = {"foo": "bar"}
    metax.patch_file_characteristics(
        "file-id",
        {
            "characteristics": characteristics,
            "characteristics_extension": extension,
        }
    )

    assert patch_characteristics.called_once
    assert patch_characteristics.last_request.json() == characteristics

    # If patching characteristics fails with HTTP 404 "Not found", the
    # "characteristics" object does not exist, so PUT request should be
    # used instead.
    if patch_characteristics_status == 404:
        assert put_characteristics.called_once
        assert put_characteristics.last_request.json() == characteristics
    else:
        assert not put_characteristics.called_once

    assert patch_file.called_once
    assert patch_file.last_request.json() \
        == {"characteristics_extension": extension}


@pytest.mark.parametrize(
    ("status_code", "reason", "response", "expectation"),
    [
        # Success
        (
            200,
            None,
            {
                "success": [
                    {"action": "insert", "object": {"pathname": "/foo1"}},
                    {"action": "insert", "object": {"pathname": "/foo2"}},
                    {"action": "insert", "object": {"pathname": "/foo3"}},
                ],
                "failed": [],
            },
            does_not_raise(),
        ),
        # V2: Some files already exist
        (
            400,
            "Bad Request",
            {
                "success": [
                    {"action": "insert", "object": {"pathname": "/foo1"}},
                ],
                "failed": [
                    {
                        "object": {"identifier": "foo2", "pathname": "/foo2"},
                        "errors": {
                            "pathname": (
                                "A file with the same value already exists, "
                                "id='foo'"
                            )
                        },
                    },
                    {
                        "object": {"identifier": "foo3", "pathname": "/foo3"},
                        "errors": {
                            "pathname": (
                                "A file with the same value already exists, "
                                "id='foo'"
                            )
                        },
                    },
                ],
            },
            pytest.raises(
                ResourceAlreadyExistsError,
                match="Some of the files already exist.",
            ),
        ),
        # V2: Other errors occur
        (
            400,
            "Bad Request",
            {
                "success": [
                    {"object": {"pathname": "/foo1"}},
                ],
                "failed": [
                    {
                        "object": {"pathname": "/foo2"},
                        "errors": {"pathname": "Unknown error"},
                    },
                    {
                        "object": {"pathname": "/foo3"},
                        "errors": {"pathname": "Unknown error"},
                    },
                ],
            },
            pytest.raises(
                requests.HTTPError,
                match="400 Client Error: Bad Request for url: "
                "https://foobar/v3/files/post-many.*",
            ),
        ),
        # V2: Some files already exist, also other errors occur
        (
            400,
            "Bad Request",
            {
                "success": [
                    {"object": {"pathname": "/foo1"}},
                ],
                "failed": [
                    {
                        "object": {"pathname": "/foo2"},
                        "errors": {
                            "pathname": (
                                "A file with the same value already exists, "
                                "id='foo'"
                            )
                        },
                    },
                    {
                        "object": {"pathname": "/foo3"},
                        "errors": {"pathname": "Unknown error"},
                    },
                ],
            },
            pytest.raises(
                requests.HTTPError,
                match="400 Client Error: Bad Request for url: "
                "https://foobar/v3/files/post-many.*",
            ),
        ),
        # V3: Some files already exist
        (
            400,
            "Bad Request",
            {
                "success": [
                    {"action": "insert", "object": {"pathname": "/foo1"}},
                ],
                "failed": [
                    {
                        "object": {"id": "foo2", "pathname": "/foo2"},
                        "errors": {
                            "pathname": (
                                "A file with the same value already exists, "
                                "id='foo'"
                            )
                        },
                    },
                    {
                        "object": {"id": "foo3", "pathname": "/foo3"},
                        "errors": {
                            "pathname": (
                                "A file with the same value already exists, "
                                "id='foo'"
                            )
                        },
                    },
                ],
            },
            pytest.raises(
                ResourceAlreadyExistsError,
                match="Some of the files already exist.",
            ),
        ),
    ],
)
def test_post_multiple_files(
    requests_mock, metax, status_code, reason, response, expectation
):
    """Test posting multiple files to Metax.

    If Metax responds with HTTP 400 "Bad request" error, an exception
    should be raised. The exception should always contain the response
    from Metax.

    :param request_mock: Request mocker
    :param status_code: Status code of mocked Metax response
    :param reason: Reason of mocked Metax response
    :param response: JSON content of Mocked Metax response
    :param expectation: expected context
    """
    requests_mock.post(
        f"{METAX_URL}/v3/files/post-many",
        status_code=status_code,
        json=response,
        reason=reason,
    )

    with expectation as exception_info:
        metax.post_files(
            [
                {
                    "id": "1",
                    "pathname": "/foo1",
                    "filename": "foo1",
                    "csc_project": "testproject",
                },
                {
                    "id": "2",
                    "pathname": "/foo2",
                    "filename": "foo2",
                    "csc_project": "testproject",
                },
                {
                    "id": "3",
                    "pathname": "/foo3",
                    "filename": "foo3",
                    "csc_project": "testproject",
                },
            ]
        )

    if not isinstance(exception_info, does_not_raise):
        assert exception_info.value.response.json() == response


def test_post_dataset(requests_mock, metax):
    """Test ``post_dataset`` function.

    Test that HTTP POST request is sent to correct url.
    """
    url = f'{metax.baseurl}/datasets'
    json = copy.deepcopy(V3_MINIMUM_TEMPLATE_DATASET)
    json |= {
        "title": {"en": "A Test Dataset"}
    }

    requests_mock.post(url, json=json)

    metax.post_dataset(json)

    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.hostname == "foobar"
    assert requests_mock.last_request.path == "/v3/datasets"


def test_get_dataset_by_ids(requests_mock, metax):
    """Test ``get_datasets_by_ids`` function.

    Test that correct results are returned depending on whether specific
    fields are requested.
    """
    requests_mock.get(
        f"{METAX_URL}/v3/datasets/1",
        json=create_test_v3_dataset(id=1)
    )
    requests_mock.get(
        f"{METAX_URL}/v3/datasets/3",
        json=create_test_v3_dataset(id=3)
    )

    datasets = metax.get_datasets_by_ids([1, 3])
    assert len(datasets) == 2

    assert datasets[0]["id"] == 1
    assert datasets[1]["id"] == 3


def test_get_files_dict(requests_mock, metax):
    """Test ``get_files_dict`` function.

    Metax is mocked to return files as two reponses.

    :returns: ``None``
    """
    url = f"{metax.baseurl}/files?limit=10000&csc_project=test"
    first_response = {
        "next": "https://next.url",
        "results": [
            _update_dict(V3_FILE, {
                "id": "file1_identifier",
                "pathname": "/path/file1",
                "storage_identifier": "urn:nbn:fi:att:file-storage-pas",
                "storage_service": 'pas'
            })
        ],
    }
    second_response = {
        "next": None,
        "results": [
            _update_dict(V3_FILE, {
                "id": "file2_identifier",
                "pathname": "/path/file2",
                "storage_identifier": "urn:nbn:fi:att:file-storage-pas",
                "storage_service": 'pas'
            })
        ],
    }
    requests_mock.get(
        url,
        json=first_response,
    )
    requests_mock.get("https://next.url", json=second_response)
    files = metax.get_files_dict("test")
    assert "/path/file1" in files
    assert "/path/file2" in files
    assert files["/path/file1"]["identifier"] == "file1_identifier"
    assert files["/path/file1"]["storage_service"] == "pas"


def test_get_dataset_directory(requests_mock, metax_v3):
    """Test get_dataset_directory function.

    :param requets_mock: HTTP request mocker
    """
    requests_mock.get(
        f"{METAX_URL}/v3/datasets/dataset_id/directories?{{}}".format(
            urlencode({"path": "/test_dir"})
        ),
        json={
            "count": 2,
            "next": (
                f"{METAX_URL}/v3/datasets/dataset_id/directories?{{}}".format(
                    urlencode({"path": "/test_dir", "page": 2})
                )
            ),
            "results": {
                "directory": {
                    "pathname": "/test_dir"
                },
                "directories": [
                    {
                        "name": "sub_test_dir",
                        "size": 50,
                        "file_count": 2,
                        "pathname": "/test_dir/sub_test_dir"
                    }
                ],
                "files": []
            }
        }
    )
    requests_mock.get(
        f"{METAX_URL}/v3/datasets/dataset_id/directories?{{}}".format(
            urlencode({"path": "/test_dir", "page": 2})
        ),
        json={
            "count": 2,
            "next": None,
            "results": {
                "directory": {
                    "pathname": "/test_dir"
                },
                "directories": [],
                "files": [
                    {
                        "id": "12345678",
                        "filename": "test.txt",
                        "size": 25
                    }
                ]
            }
        }
    )

    result = metax_v3.get_dataset_directory("dataset_id", "/test_dir")

    assert result["directory"]["pathname"] == "/test_dir"

    assert len(result["directories"]) == 1
    assert result["directories"][0]["pathname"] == "/test_dir/sub_test_dir"

    assert len(result["files"]) == 1
    assert result["files"][0]["filename"] == "test.txt"


@pytest.mark.parametrize(
    ("file_path", "results", "results_v3"),
    [
        # Only one matching file in Metax
        (
            "/dir/file",
            [{"file_path": "/dir/file"}],
            [{"pathname": "/dir/file"}]
        ),
        # Two matching files in Metax. First one is not exact match.
        (
            "/dir/file",
            [{"file_path": "/dir/file/foo"}, {"file_path": "/dir/file"}],
            [{"pathname": "/dir/file/foo"}, {"pathname": "/dir/file"}]
        ),
        # file_path without leading '/' should work as well
        (
            "dir/file",
            [{"file_path": "/dir/file"}],
            [{"pathname": "/dir/file"}],
        ),
    ],
)
def test_get_project_file(file_path, results, results_v3, requests_mock, metax):
    """Test get_project_file function.

    :param file_path: Path of file to get
    :param results: Matching files in Metax
    :param requets_mock: HTTP request mocker
    """
    requests_mock.get(
        metax.baseurl + "/files",
        json={
            "count": 1,
            "next": None,
            "previous": None,
            "results": [_update_dict(V3_FILE, res) for res in results_v3]
        },
    )
    expected_file = copy.deepcopy(V3_FILE)
    expected_file |= {
        'pathname': "/dir/file"
    }
    assert (
        metax.get_project_file("foo", file_path)
        == expected_file
    )
    assert requests_mock.last_request.qs["csc_project"] == ["foo"]
    assert requests_mock.last_request.qs["pathname"] == [file_path]


@pytest.mark.parametrize(
    ("results", "results_v3"),
    (
        # One match is found, but it is not exact match
        ([{"file_path": "/testdir/testfile/foo", "identifier": "foo"}],
         [{"pathname": "/testdir/testfile/foo", "id": "foo"}]),
        # No matches found
        ([], []),
    ),
)
def test_get_project_file_not_found(results, results_v3, requests_mock, metax):
    """Test searching file_path that is not available.

    :param results: Matching files in Metax
    :param requets_mock: HTTP request mocker
    """
    requests_mock.get(
        metax.baseurl + "/files",
        json={
            "count": 1,
            "next": None,
            "previous": None,
            "results": [_update_dict(V3_FILE, res) for res in results_v3]
        },
    )
    with pytest.raises(FileNotAvailableError):
        metax.get_project_file("foo", "/testdir/testfile")


def test_get_file2dataset_dict(requests_mock, metax):
    """Test Metax.get_file2dataset_dict

    Dictionary is returned for files that contain datasets. Files without
    datasets are not included in the response.
    """
    file_id1 = '161bc25962da8fed6d2f59922fb642'
    file_id2 = '161bc25962da8fed6d2f59922fb643'
    requests_mock.post(
        f"{metax.baseurl}/files/datasets",
        json={file_id1: ["urn:dataset:aaffaaff"]},
        # Ensure the request body has the requested file IDs
        additional_matcher=lambda req: req.json() == [file_id1, file_id2],
    )
    result = metax.get_file2dataset_dict([file_id1, file_id2])

    assert result[file_id1] == ["urn:dataset:aaffaaff"]


def test_get_file2dataset_dict_empty(requests_mock, metax):
    """Test Metax.get_file2dataset dict with an empty list of file identifiers"""
    mocked_req = requests_mock.post(
        f"{metax.baseurl}/files/datasets", status_code=400
    )
    result = metax.get_file2dataset_dict([])

    assert result == {}

    # The mocked endpoint was not called
    assert not mocked_req.request_history


@pytest.mark.parametrize(
    ("url", "method", "parameters", "expected_error"),
    [
        ("/datasets", "get_datasets", [], DatasetNotAvailableError),
        (
            "/contracts",
            "get_contracts",
            [],
            ContractNotAvailableError,
        ),
        (
            "/contracts/foo",
            "get_contract",
            ["foo"],
            ContractNotAvailableError,
        ),
        (
            "/datasets/foo/files",
            "get_dataset_files",
            ["foo"],
            DatasetNotAvailableError,
        ),
    ],
)
def test_get_http_404(requests_mock, metax, url, method, parameters, expected_error):
    """Test a method when Metax responds with 404 "Not found" error.

    The function should throw an exception.

    :param request_mock: requests mocker
    :param url: Metax url to be mocked
    :param method: Method to be tested
    :param parameters: Parameters for method call
    :param expected_error: Exception expected to raise
    """
    requests_mock.get(f"{METAX_URL}/v3{url}", status_code=404)
    with pytest.raises(expected_error):
        getattr(metax, method)(*parameters)


@pytest.mark.parametrize(
    ("url", "method", "parameters"),
    [
        (
            "/datasets?include_nulls=True&limit=1000000&offset=0",
            "get_datasets",
            [],
        ),
        (
            "/contracts?limit=1000000&offset=0&include_nulls=True",
            "get_contracts",
            []
        ),
        ("/contracts/foo?include_nulls=True", "get_contract", ["foo"]),
        (
            "/datasets/foo?include_nulls=True",
            "get_dataset",
            ["foo"],
        ),
        (
            "/datasets/foo/metadata-download?format=datacite&include_nulls=True",
            "get_datacite",
            ["foo"],
        ),
        (
            "/datasets/foo/files?limit=10000&include_nulls=True",
            "get_dataset_files",
            ["foo"]
        ),
    ],
)
def test_get_http_503(requests_mock, metax, caplog, url, method, parameters):
    """Test a method when Metax responds with 503 "Server error".

    The function should throw a HTTPError, and the content of response to
    failed request should be logged.

    :param request_mock: requests mocker
    :param caplog: log capturer
    :param url: Metax url to be mocked
    :param method: Method to be tested
    :param parameters: Parameters for method call
    """
    requests_mock.get(
        f"{METAX_URL}/v3{url}",
        status_code=503,
        reason="Metax error",
        text="Metax failed to process request",
    )
    with pytest.raises(requests.HTTPError) as error:
        getattr(metax, method)(*parameters)
    assert error.value.response.status_code == 503

    # Check logs
    logged_messages = [record.message for record in caplog.records]
    expected_message = (
        f"HTTP request to {METAX_URL}/v3{url} failed. Response from "
        "server was: Metax failed to process request"
    )
    assert expected_message in logged_messages


def test_set_preservation_state_http_503(requests_mock, metax):
    """Test ``set_preservation_state`` function.

    ``set_preservation_state`` should throw a HTTPError when
    requests.patch() returns http 503 error.
    """
    requests_mock.patch(
        f"{metax.baseurl}/datasets/foobar/preservation",
        status_code=503
    )
    with pytest.raises(requests.HTTPError) as error:
        metax.set_preservation_state("foobar", "10", "foo")
    assert error.value.response.status_code == 503


@pytest.mark.parametrize("action", ["lock", "unlock"])
def test_lock_dataset(requests_mock, metax_v3, action):
    """Test locking/unlocking a dataset.

    `pas_process_running` will be set to True or False for the dataset and its
    files, depending on whether the dataset is being locked or unlocked
    """
    requests_mock.patch(
        f"{METAX_URL}/v3/datasets/foobar/preservation?include_nulls=true",
        json={}
    )
    requests_mock.get(
        f"{METAX_URL}/v3/datasets/foobar/files?include_nulls=true&limit=10000",
        json={
            "results": [
                create_test_v3_file(id="file_1"),
                create_test_v3_file(id="file_2")
            ],
            "next": \
                f"{METAX_URL}/v3/datasets/foobar/files"
                "?include_nulls=true&page=2&limit=10000"
        }
    )
    requests_mock.get(
        f"{METAX_URL}/v3/datasets/foobar/files?include_nulls=true&page=2&limit=10000",
        json={
            "results": [
                create_test_v3_file(id="file_3")
            ],
            "next": None
        }
    )
    files_patch = requests_mock.post(
        f"{METAX_URL}/v3/files/patch-many?include_nulls=true",
        json={}
    )
    dataset_patch = requests_mock.patch(
        f"{METAX_URL}/v3/datasets/foobar/preservation", json={}
    )

    if action == "lock":
        metax_v3.lock_dataset("foobar")
        expected_status = True
    elif action == "unlock":
        metax_v3.unlock_dataset("foobar")
        expected_status = False

    # Files were patched to set the status
    assert files_patch.request_history[0].json() == [
        {"id": "file_1", "pas_process_running": expected_status},
        {"id": "file_2", "pas_process_running": expected_status},
        {"id": "file_3", "pas_process_running": expected_status},
    ]
    assert dataset_patch.request_history[0].json() == {
        "pas_process_running": expected_status
    }


def test_get_file_format_versions(requests_mock, metax):
    """Test get_file_format_versions."""
    requests_mock.get(
        f"{metax.baseurl}/reference-data/file-format-versions",
        json=[
            {
                "id": "id1",  # This is unnecessary and should be ignored
                "url": "url1",
                "file_format": "format1",
                "format_version": "version1",
            },
            {
                "url": "url2",
                "file_format": "format2",
                "format_version": "version2",
            },
        ],
    )

    assert metax.get_file_format_versions() == [
        {
            "url": "url1",
            "file_format": "format1",
            "format_version": "version1",
        },
        {
            "url": "url2",
            "file_format": "format2",
            "format_version": "version2",
        },
    ]


def _check_values(json, expected_val):
    assert 'modified' in json
    assert 'created' in json

    json = copy.deepcopy(json)
    del json["modified"]
    del json["created"]

    expected_val = copy.deepcopy(expected_val)

    assert json == expected_val


def _update_dict(original, update):
    original_copy = copy.deepcopy(original)
    original_copy |= update
    return original_copy
