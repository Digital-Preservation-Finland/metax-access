# pylint: disable=no-member
"""Tests for ``metax_access.metax`` module."""
import copy
from contextlib import ExitStack as does_not_raise
from urllib.parse import quote, urlencode

import lxml.etree
import pytest
import requests

from metax_access import (DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
                          DS_STATE_ACCEPTED_TO_DIGITAL_PRESERVATION,
                          Metax)
from metax_access.error import (ContractNotAvailableError,
                                DataCatalogNotAvailableError,
                                DataciteGenerationError,
                                DatasetNotAvailableError,
                                DirectoryNotAvailableError,
                                FileNotAvailableError,
                                ResourceAlreadyExistsError)
from tests.unit_tests.utils import (V3_CONTRACT, V3_FILE,
                                    V3_MINIMUM_TEMPLATE_DATASET,
                                    create_test_file)

METAX_URL = "https://foobar"
METAX_REST_ROOT_URL = f"{METAX_URL}/rest"
METAX_REST_URL = f"{METAX_URL}/rest/v2"
METAX_RPC_URL = f"{METAX_URL}/rpc/v2"
METAX_USER = "tpas"
METAX_PASSWORD = "password"
METAX_CLIENT = Metax(METAX_URL, METAX_USER, METAX_PASSWORD, verify=False)

DATASET = copy.deepcopy(V3_MINIMUM_TEMPLATE_DATASET)
del DATASET['created']
del DATASET['modified']

@pytest.fixture(autouse=True, scope='function')
def metax(request):
    """Choose which Metax implementation is used.

    Use Metax V3 if --v3 option is used and V2 otherwise.
    """
    if request.config.getoption("--v3"):
        return Metax(METAX_URL, token='token_foo', verify=False, api_version='v3')
    else:
        return Metax(METAX_URL, METAX_USER, METAX_PASSWORD, verify=False)


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

    if metax.api_version == 'v2':
        json = [{'identifier': file_id}, {'identifier': file_id2}]
    else:
        json = {'next': None,'results': expected_output}

    requests_mock.get(
        url, json=json
    )
    requests_mock.get(
        f"{metax.baseurl}/datasets/{dataset_id}?include_user_metadata=true&file_details=true",
        json={}
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

    if metax.api_version == 'v2':
        url = url = f'{metax.baseurl}/files/foo'
        json = {'identifier': file_id}

    requests_mock.get(url, json=json)
    file = metax.get_file('foo') if metax.api_version == 'v2' else metax.get_file(file_id)
    assert file == expected_file

def test_get_datasets(requests_mock, caplog, metax):
    """Test ``get_datasets`` function.

    Mocks Metax to return simple JSON as HTTP response and checks that the
    returned dict contains the correct values.

    :returns: None
    """
    ids = ['foo', 'bar']
    expected_datasets = [_update_dict(DATASET, {'id': id}) for id in ids]
    json = [_update_dict(V3_MINIMUM_TEMPLATE_DATASET, {'id': id}) for id in ids]
    if metax.api_version == 'v2':
        json = [{"identifier": id} for id in ids]
    metax_mock = requests_mock.get(
        f"{metax.baseurl}/datasets/foo/files", json={}
    )
    metax_mock = requests_mock.get(
        f"{metax.baseurl}/datasets/bar/files", json={}
    )
    metax_mock = requests_mock.get(
        f"{metax.baseurl}/datasets/foo?include_user_metadata=true&file_details=true",
        json={},
    )
    metax_mock = requests_mock.get(
        f"{metax.baseurl}/datasets/bar?include_user_metadata=true&file_details=true",
        json={},
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

    if metax.api_version == 'v2':
        assert query_string["include_user_metadata"][0] == "true"
        assert (
        query_string["preservation_state"][0]
        == "-1,0,10,20,30,40,50,60,65,70,75,80,90,100,110,120,130,140"
    )

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
    if metax.api_version == 'v2':
        json = {'results':[{}]}
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
    if metax.api_version == 'v2':
        assert query_string["preservation_state"][0] == "states-param"
        assert query_string["pas_filter"][0] == "pas-filter-param"
        assert query_string["metadata_owner_org"][0] == "owner-org-param"
        assert query_string["metadata_provider_user"][0] == "provider-user-param"
        assert "include_user_metadata" not in query_string
    if metax.api_version == 'v3':
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

    if metax.api_version == "v2":
        url = f"{metax.baseurl}/datasets/test_id?include_user_metadata=true&file_details=true"
        json = {"identifier": "123"}

    requests_mock.get(
        url,
        json=json,
    )
    # TODO: remove this when v2 is not tested
    requests_mock.get(
        METAX_REST_URL
        + "/datasets/123?include_user_metadata=true&file_details=true",
        json={},
    )
    # TODO: remove this when v2 is not tested
    requests_mock.get(METAX_REST_URL + "/datasets/123/files", json={})

    dataset = (
        metax.get_dataset(dataset_id)
        if metax.api_version == "v3"
        else metax.get_dataset("test_id")
    )

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
                     {'id': id})
                     for id in ids
    ]
    v3_output_contracts = [
        _update_dict(contract,
                     {'id': id})
                     for id in ids
    ]
    json = {
            "results": v3_output_contracts
        }
    if metax.api_version == 'v2':
        json = {
            "results": [
                {'contract_json':
                    {"identifier": id}
                }
            for id in ids]
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

    if metax.api_version == "v2":
        url = f"{metax.baseurl}/contracts/test_id"
        json = {"contract_json": {"identifier": contract_id}}

    requests_mock.get(url, json=json)

    contract = (
        metax.get_contract(contract_id)
        if metax.api_version == "v3"
        else metax.get_contract("test_id")
    )
    assert expected_contract == contract


def test_get_dataset_file_count(requests_mock, metax):
    """Test retrieving the total file count for a dataset"""

    def _request_has_correct_params(req):
        return req.qs["file_fields"] == ["id"]

    url = f"{metax.baseurl}/datasets/fake-dataset"
    json = {"fileset": {"total_files_count": 3}}
    if metax.api_version == "v2":
        url = f"{metax.baseurl}/datasets/fake-dataset/files"
        json = [{"id": 1}, {"id": 3}, {"id": 10}]

    requests_mock.get(
        url,
        additional_matcher=(
            _request_has_correct_params if metax.api_version == "v2" else None
        ),
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
    if metax.api_version == "v2":
        url = f"{metax.baseurl}/datasets/does-not-exist/files"
    requests_mock.get(
        url,
        additional_matcher=(lambda req: req.qs["file_fields"] == ["id"]) if metax.api_version == 'v2' else None,
        status_code=404,
    )

    with pytest.raises(DatasetNotAvailableError):
        metax.get_dataset_file_count("does-not-exist")


def test_patch_dataset(requests_mock):
    """Test ``patch_dataset`` function.

    Patch a dataset with few updated key/value pairs and check that correct
    HTTP request was sent to Metax.

    :returns: ``None``
    """
    requests_mock.patch(METAX_REST_URL + "/datasets/test_id", json={})
    requests_mock.get(
        METAX_REST_URL + "/datasets/test_id",
        json={
            "research_dataset": {
                "provenance": [{"foo": "bar"}, {"fiz": "buz"}]
            }
        },
    )

    update = {"foo1": "bar1", "research_dataset": {"foo2": "bar2"}}
    METAX_CLIENT.patch_dataset("test_id", update, False, True)
    assert requests_mock.last_request.method == "PATCH"

    request_body = requests_mock.last_request.json()
    assert isinstance(request_body["research_dataset"]["provenance"], list)
    assert request_body["research_dataset"]["foo2"] == "bar2"
    assert request_body["foo1"] == "bar1"

def test_set_contract(requests_mock, metax):
    """Test ``set_contract`` function.

    Patch the contract of a dataset and check that a correct
    HTTP request was sent to Metax.

    :returns: ``None``
    """
    dataset_id = 'test_id'
    url = f'{metax.baseurl}/datasets/{dataset_id}/preservation'
    if metax.api_version == 'v2':
        url = f'{metax.baseurl}/datasets/{dataset_id}'
    requests_mock.patch(url, json={})
    # TODO: Only used in v2 test
    requests_mock.get(
        metax.baseurl + "/datasets/test_id",
        json={}
    )

    metax.set_contract(dataset_id, 'new:contract:id')
    assert requests_mock.last_request.method == "PATCH"

    request_body = requests_mock.last_request.json()
    if metax.api_version == 'v2':
        assert isinstance(request_body["contract"], dict)
        assert request_body["contract"]["identifier"] == "new:contract:id"
    else:
        assert request_body["contract"] == "new:contract:id"


def test_get_datacite(requests_mock, metax):
    """Test ``get_datacite`` function.

    Read one field from returned XML and check its correctness.

    :returns: ``None``
    """
    # Read sample datacite from file and create mocked HTTP response
    dataset_id = 'test_id'
    url = f'{metax.baseurl}/datasets/{dataset_id}/metadata-download?format=datacite&include_nulls=True'
    if metax.api_version == 'v2':
        url = f'{metax.baseurl}/datasets/{dataset_id}?dataset_format=datacite&dummy_doi=false'

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


def test_get_datacite_fails(requests_mock):
    """Test ``get_datacite`` function when Metax returns 400.

    :returns: ``None``
    """
    # Mock metax dataset request response. Response body contains simplified
    # dataset metadata.
    requests_mock.get(
        METAX_REST_URL + "/datasets/foo", json={"identifier": "foo"}
    )

    # Mock datacite request response. Mocked response has status code 400, and
    # response body contains error information.
    response = {
        "detail": "Foobar.",
        "error_identifier": "2019-03-28T12:39:01-f0a7e3ae",
    }
    requests_mock.get(
        METAX_REST_URL + "/datasets/foo?dataset_format=datacite",
        json=response,
        status_code=400,
    )

    with pytest.raises(DataciteGenerationError) as exception:
        METAX_CLIENT.get_datacite("foo")

    assert exception.value.message == "Datacite generation failed: Foobar."


def test_set_preservation_state(requests_mock, metax):
    """Test ``set_preservation_state`` function.

    Metadata in Metax is modified by sending HTTP PATCH request with modified
    metadata in JSON format. This test checks that correct HTTP request is sent
    to Metax. The effect of the request is not tested.

    :returns: ``None``
    """
    patch_preservation_url = (
        f"{metax.baseurl}/datasets/test_id/preservation"
        if metax.api_version == "v3"
        else f"{metax.baseurl}/datasets/test_id"
    )

    requests_mock.patch(patch_preservation_url)

    metax.set_preservation_state(
        "test_id",
        DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
        "Accepted to preservation",
    )

    # Check the body of last HTTP request
    request_body = requests_mock.last_request.json()
    if metax.api_version == 'v2':
        assert (
            request_body["preservation_state"]
            == DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE
        )
        assert (
            request_body["preservation_description"] == "Accepted to preservation"
        )
    else:
        assert (
            request_body["state"]
            == DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE
        )
        assert (
            request_body["description"] == {"en": "Accepted to preservation"}
        )

    # Check the method of last HTTP request
    assert requests_mock.last_request.method == "PATCH"

def test_set_preservation_state_copy_to_pas_catalog(requests_mock, metax):
    """Test ``set_preservation_state`` function.

    Metadata in Metax is modified by sending HTTP PATCH request with modified
    metadata in JSON format. This test checks that correct HTTP request is sent
    to Metax and the PAS catalog endpoint was called with POST when the
    preservation state is accpeted to preservation.

    :returns: ``None``
    """
    dataset_id = "test_id"
    contract_id = "contract_id"
    url = (
            f"{metax.baseurl}/datasets/"
            + f"{dataset_id}/create-preservation-version"
        )
    dataset_url = f"{metax.baseurl}/datasets/{dataset_id}"
    response = copy.deepcopy(V3_MINIMUM_TEMPLATE_DATASET)
    response['id'] = dataset_id
    response['preservation']['contract'] = contract_id
    requests_mock.get(
        dataset_url,
        json=response
    )
    requests_mock.post(url)
    patch_preservation_url = (
        f"{metax.baseurl}/datasets/{dataset_id}/preservation"
        if metax.api_version == "v3"
        else f"{metax.baseurl}/datasets/{dataset_id}"
    )

    requests_mock.patch(patch_preservation_url)

    metax.set_preservation_state(
        dataset_id,
        DS_STATE_ACCEPTED_TO_DIGITAL_PRESERVATION,
        "Accepted to preservation",
    )

    # Check the body of last HTTP request
    request_body = requests_mock.last_request.json()
    if metax.api_version == 'v2':
        assert (
            request_body["preservation_state"]
            == DS_STATE_ACCEPTED_TO_DIGITAL_PRESERVATION
        )
        assert (
            request_body["preservation_description"] == "Accepted to preservation"
        )
    else:
        assert (
            request_body["state"]
            == DS_STATE_ACCEPTED_TO_DIGITAL_PRESERVATION
        )
        assert (
            request_body["description"] == {"en": "Accepted to preservation"}
        )
        assert len(requests_mock.request_history) == 3
        assert requests_mock.request_history[1].method == "POST"
        assert requests_mock.request_history[1].path ==  f"/v3/datasets/{dataset_id}/create-preservation-version"
        assert requests_mock.request_history[1].hostname == "foobar"

    # Check the method of last HTTP request
    assert requests_mock.last_request.method == "PATCH"


def test_copy_dataset_to_pas_catalog_no_contract(requests_mock, metax):
    """"Test copy_dataset_to_pas_catalog function without a contract.

    A dataset without a contract can't be added to PAS Catalog.
    Check that an error is raised, for such dataset.
    """
    dataset_id = 'dataset_id'
    url = (
            f"{metax.baseurl}/datasets/"
            + f"{dataset_id}/create-preservation-version"
        )
    dataset_url = f"{metax.baseurl}/datasets/{dataset_id}"
    response = copy.deepcopy(V3_MINIMUM_TEMPLATE_DATASET)
    response['id'] = dataset_id
    requests_mock.get(
        dataset_url,
        json=response
    )
    requests_mock.post(url)
    if metax.api_version == "v3":
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
    if metax.api_version == 'v2':
        url = f'{metax.baseurl}/datasets/{dataset_id}'
    requests_mock.patch(url)

    metax.set_preservation_reason(dataset_id, "The reason.")

    # Check the method of last HTTP request
    assert requests_mock.last_request.method == "PATCH"
    if metax.api_version == 'v2':
        assert requests_mock.last_request.json() == {
            "preservation_reason_description": "The reason."
        }
    if metax.api_version == 'v3':
        assert requests_mock.last_request.json() == {
            "reason_description": "The reason."
        }


def test_patch_file(requests_mock):
    """Test ``patch_file`` function.

    Metadata in Metax is modified by sending HTTP PATCH request with modified
    metadata in JSON format. This test checks that correct HTTP request is sent
    to Metax in V2 format, and that patch_file returns JSON response from Metax.

    :returns: None
    """
    # Mock Metax
    requests_mock.get(METAX_REST_URL + "/files/test_id", json={})
    requests_mock.patch(METAX_REST_URL + "/files/test_id", json={"foo": "bar"})

    # Patch a file
    sample_data = {
        "id": "42",
        "checksum": "sha256:212f954060735c8aea7af705e0b268723148d37898339f21014c24dc5cf6736b",
        "file_characteristics": {
            "file_format": "text/plain",
            "format_version": "1.0",
            "encoding": "UTF-8",
        },
    }
    assert METAX_CLIENT.patch_file("test_id", sample_data) == {"foo": "bar"}

    # Check that the JSON was converted to V2
    file_v2 = requests_mock.last_request.json()
    assert file_v2 == {
        "id": "42",
        "identifier": "42",
        "checksum": {
            "algorithm": "SHA-256",
            "value": "212f954060735c8aea7af705e0b268723148d37898339f21014c24dc5cf6736b",
        }
    }

    # Check the method of last HTTP request
    assert requests_mock.last_request.method == "PATCH"


@pytest.mark.parametrize("patch_characteristics_status", [200, 404])
def test_patch_file_characteristics(requests_mock, metax,
                                    patch_characteristics_status):
    """Test patch_file_characteristics.

    :param requests_mock: HTTP Request mocker
    :param metax: Metax client
    :param patch_characteristics_status: HTTP status code of response
        for patching file characteristics.
    """
    if metax.api_version == "v2":
        pytest.skip(
            "It does not make sense to create Metax V2 tests for this method "
            "anymore."
        )

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


def test_delete_file(requests_mock):
    """Test ``delete_file`` function.

    Test that HTTP DELETE request is sent to correct url.
    """
    requests_mock.delete(
        METAX_REST_URL + "/files/file1", json={"deleted_files_count": 1}
    )

    METAX_CLIENT.delete_file("file1")

    assert requests_mock.last_request.method == "DELETE"
    assert requests_mock.last_request.hostname == "foobar"
    assert requests_mock.last_request.path == "/rest/v2/files/file1"


def test_delete_dataset(requests_mock):
    """Test ``delete_dataset`` function.

    Test that HTTP DELETE request is sent to correct url.
    """
    requests_mock.delete(METAX_REST_URL + "/datasets/dataset1")

    METAX_CLIENT.delete_dataset("dataset1")

    assert requests_mock.last_request.method == "DELETE"
    assert requests_mock.last_request.hostname == "foobar"
    assert requests_mock.last_request.path == "/rest/v2/datasets/dataset1"


def test_post_file(requests_mock, metax):
    """Test ``post_file`` function.

    Test that HTTP POST request is sent to correct url.
    """
    url = f"{metax.baseurl}/files"
    if metax.api_version == 'v2':
        url = f"{metax.baseurl}/files/"
    requests_mock.post(url, json={"ide": "1"})

    metax.post_file({"id": "1"})

    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.hostname == "foobar"
    if metax.api_version == 'v2':
        assert requests_mock.last_request.path == "/rest/v2/files/"
    else:
        assert requests_mock.last_request.path == "/v3/files"


@pytest.mark.parametrize(
    ("response", "expected_exception"),
    [
        # V2: Trying to post file, path already exists
        (
            {
                "file_path": [
                    "a file with path /foo already exists in" " project bar"
                ]
            },
            ResourceAlreadyExistsError("Some of the files already exist."),
        ),
        # V2: Trying to post file, path and identifier already exist
        (
            {
                "file_path": [
                    "a file with path /foo already exists in" " project bar"
                ],
                "identifier": ["a file with given identifier already exists"],
            },
            ResourceAlreadyExistsError("Some of the files already exist."),
        ),
        # Unknown error
        (
            {"file_path": ["Some other error in file path"]},
            requests.HTTPError(
                "400 Client Error: Bad Request for url: "
                "https://foobar/rest/v2/files/"
            ),
        ),
        # Multiple files that already exist
        (
            {
                "failed": [
                    {
                        "object": {"identifier": "foo1", "file_path": "/foo1"},
                        "errors": {
                            "file_path": [
                                "a file with path /foo1 already "
                                "exists in project bar"
                            ]
                        },
                    },
                    {
                        "object": {"identifier": "foo2", "file_path": "/foo2"},
                        "errors": {
                            "file_path": [
                                "a file with path /foo2 already "
                                "exists in project bar"
                            ]
                        },
                    },
                ]
            },
            ResourceAlreadyExistsError("Some of the files already exist."),
        ),
        # Multiple files, one already exists, one has other error
        (
            {
                "failed": [
                    {
                        "errors": {
                            "file_path": [
                                "a file with path /foo1 already "
                                "exists in project bar"
                            ]
                        }
                    },
                    {"errors": {"file_path": ["Other error"]}},
                ]
            },
            requests.HTTPError(
                "400 Client Error: Bad Request for url: "
                "https://foobar/rest/v2/files/"
            ),
        ),
    ],
)
def test_post_file_bad_request(requests_mock, response, expected_exception):
    """Test post file failures.

    If Metax responds with HTTP 400 "Bad request" error, an exception
    should be raised.

    :param response: Mocked response from Metax
    :param expected_exception: expected exception
    """
    requests_mock.post(
        METAX_REST_URL + "/files/",
        status_code=400,
        json=response,
        reason="Bad Request",
    )

    with pytest.raises(
        expected_exception.__class__, match=str(expected_exception)
    ):
        METAX_CLIENT.post_file(
            {
                "identifier": "1",
                "file_path": "/foo",
                "project_identifier": "bar",
            }
        )


@pytest.mark.parametrize(
    ("status_code", "reason", "response", "expectation"),
    [
        # V2: Success
        (
            200,
            None,
            {
                "success": [
                    {"object": {"file_path": "/foo1"}},
                    {"object": {"file_path": "/foo2"}},
                    {"object": {"file_path": "/foo3"}},
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
                    {"object": {"file_path": "/foo1"}},
                ],
                "failed": [
                    {
                        "object": {"identifier": "foo2", "file_path": "/foo2"},
                        "errors": {
                            "file_path": [
                                "a file with path /foo2.png "
                                "already exists in project "
                                "testproject"
                            ]
                        },
                    },
                    {
                        "object": {"identifier": "foo3", "file_path": "/foo3"},
                        "errors": {
                            "file_path": [
                                "a file with path /foo3.png "
                                "already exists in project "
                                "testproject"
                            ]
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
                    {"object": {"file_path": "/foo1"}},
                ],
                "failed": [
                    {
                        "object": {"file_path": "/foo2"},
                        "errors": {"file_path": ["Unknown error"]},
                    },
                    {
                        "object": {"file_path": "/foo3"},
                        "errors": {"file_path": ["Unknown error"]},
                    },
                ],
            },
            pytest.raises(
                requests.HTTPError,
                match="400 Client Error: Bad Request for url: "
                "https://foobar/rest/v2/files/",
            ),
        ),
        # V2: Some files already exist, also other errors occur
        (
            400,
            "Bad Request",
            {
                "success": [
                    {"object": {"file_path": "/foo1"}},
                ],
                "failed": [
                    {
                        "object": {"file_path": "/foo2"},
                        "errors": {
                            "file_path": [
                                "a file with path /foo2.png "
                                "already exists in project "
                                "testproject"
                            ]
                        },
                    },
                    {
                        "object": {"file_path": "/foo3"},
                        "errors": {"file_path": ["Unknown error"]},
                    },
                ],
            },
            pytest.raises(
                requests.HTTPError,
                match="400 Client Error: Bad Request for url: "
                "https://foobar/rest/v2/files/",
            ),
        ),
        # V3: Some files already exist
        (
            400,
            "Bad Request",
            {
                "success": [
                    {"object": {"pathname": "/foo1"}},
                ],
                "failed": [
                    {
                        "object": {"id": "foo2", "pathname": "/foo2"},
                        "errors": {
                            "pathname": [
                                "a file with path /foo2.png "
                                "already exists in project testproject"
                            ]
                        },
                    },
                    {
                        "object": {"id": "foo3", "pathname": "/foo3"},
                        "errors": {
                            "pathname": [
                                "a file with path /foo3.png "
                                "already exists in project "
                                "testproject"
                            ]
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
    requests_mock, status_code, reason, response, expectation
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
        METAX_REST_URL + "/files/",
        status_code=status_code,
        json=response,
        reason=reason,
    )

    with expectation as exception_info:
        METAX_CLIENT.post_file(
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
    if metax.api_version == 'v2':
        url = f'{metax.baseurl}/datasets/'
        json = {"identifier": "1"}

    requests_mock.post(url, json=json)

    metax.post_dataset(json)

    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.hostname == "foobar"
    if metax.api_version == 'v2':
        assert requests_mock.last_request.path == "/rest/v2/datasets/"
    else:
        assert requests_mock.last_request.path == "/v3/datasets"

def test_query_datasets(requests_mock):
    """Test ``query_datasets`` function.

    Mocks Metax to return simple JSON as HTTP response and checks that the
    returned dict contains the correct values.

    :returns: ``None``
    """
    requests_mock.get(
        METAX_REST_URL + "/datasets?preferred_identifier=foobar",
        json = {
            "results": [
                {
                    "identifier": "foo",
                    'preservation_identifier': 1234,
                    'preservation_dataset_version': {
                        'preferred_identifier': 'foobar',
                        'identifier': 123
                    }
                }
            ]
        },
    )
    requests_mock.get(METAX_REST_URL + "/datasets/foo/files", json={})
    requests_mock.get(
        METAX_REST_URL
        + "/datasets/foo?include_user_metadata=true&file_details=true",
        json={},
    )
    datasets = METAX_CLIENT.query_datasets({"preferred_identifier": "foobar"})
    assert len(datasets["results"]) == 1
    expected_dataset = copy.deepcopy(DATASET)
    expected_dataset['preservation'] = {
        'contract': None,
        'description': None,
        'reason_description': None,
        'state': -1,
        'dataset_version': {
            'id': 123, 
            'persistent_identifier': 'foobar', 
            'preservation_state': -1
        }
    }
    expected_dataset['id'] = 'foo'
    _check_values(datasets['results'][0], expected_dataset)

@pytest.mark.parametrize(
    ("url", "response_json", "fields", "expected_response"),
    [
    (f"{METAX_REST_ROOT_URL}/datasets/list?limit=1000000&offset=0",
     {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": 1,
                },
                {
                    "id": 3,
                },
            ],
        },
        None,
        [{},{}]
     ),(
     f"{METAX_REST_ROOT_URL}/datasets/list"
        "?fields=id,project_identifier&limit=1000000&offset=0",
        {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {"id": 1,
                "research_dataset": {
                    "files": [
                        {
                            "details": {
                                "project_identifier": "blah"
                            }
                        }
                    ]
                 }
                }
                 ,
                {"id": 3, "research_dataset": {
                    "files": [
                        {
                            "details": {
                                "project_identifier": "bleh"
                            }
                        }
                    ]
                 }},
            ],
        },
        ["id", "project_identifier"],
        [
            {
                "fileset": 
            {
                "total_files_size": 0,
                "csc_project": 'blah',
            }
            },
            {
                "fileset": 
            {
                "total_files_size": 0,
                "csc_project": 'bleh',
            }
            }
        ]
     )
    ],
)
def test_get_dataset_by_ids(requests_mock, url, response_json, fields, expected_response):
    """Test ``get_datasets_by_ids`` function.

    Test that correct results are returned depending on whether specific
    fields are requested.
    """
    # TODO: do something to this test
    # it is annoying to convert v3
    requests_mock.post(
        url,
        additional_matcher=lambda req: req.json() == [1, 3],
        json=response_json,
    )

    response = METAX_CLIENT.get_datasets_by_ids([1, 3], fields = fields)
    datasets = response["results"]
    assert len(datasets) == 2
    expected_datasets = [_update_dict(DATASET, d) for d in expected_response]

    _check_values(datasets[0], expected_datasets[0])
    _check_values(datasets[1], expected_datasets[1])

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
    if metax.api_version == 'v2':
        url = f"{metax.baseurl}/files?limit=10000&project_identifier=test"
        first_response = {
            "next": "https://next.url",
            "results": [
                {
                    "id": 28260,
                    "file_path": "/path/file1",
                    "file_storage": {
                        "id": 1,
                        "identifier": "urn:nbn:fi:att:file-storage-pas",
                    },
                    "identifier": "file1_identifier",
                }
            ],
        }
        second_response = {
            "next": None,
            "results": [
                {
                    "id": 23125,
                    "file_path": "/path/file2",
                    "file_storage": {
                        "id": 1,
                        "identifier": "urn:nbn:fi:att:file-storage-pas",
                    },
                    "identifier": "file2_identifier",
                }
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


def test_get_project_directory(requests_mock):
    """Test get_project_directory function.

    :param requets_mock: HTTP request mocker
    """
    metadata = {
        "directories": [{"directory_path": "/testdir/bar"}],
        "files": [{"identifier": "file1"}],
        "directory_path": "/testdir",
    }
    metadata_v3 = {
        "directory": {"pathname": "/testdir"},
        "directories": [
            {
                "name": None,
                "size": None,
                "file_count": None,
                "pathname": "/testdir/bar",
            }
        ],
        "files": [{"id": "file1", "filename": None, "size": None}],
    }
    requests_mock.get(METAX_REST_URL + "/directories/files", json=metadata)
    assert (
        METAX_CLIENT.get_project_directory("foo", "/testdir")["results"]
        == metadata_v3
    )
    assert requests_mock.last_request.qs["project"] == ["foo"]
    assert requests_mock.last_request.qs["path"] == ["/testdir"]


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


def test_get_directory_id(requests_mock):
    """Test get_directory_id function.

    :param requets_mock: HTTP request mocker
    """
    metadata = {"identifier": "dir:id:1"}
    requests_mock.get(METAX_REST_URL + "/directories/files", json=metadata)
    assert (
        METAX_CLIENT.get_directory_id("foo", "/testdir")
        == metadata["identifier"]
    )
    assert requests_mock.last_request.qs["project"] == ["foo"]
    assert requests_mock.last_request.qs["path"] == ["/testdir"]


@pytest.mark.parametrize(
    "file_path,results,results_v3",
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
            "results": (
                [_update_dict(V3_FILE, res) for res in results_v3]
                if metax.api_version == "v3"
                else results
            ),
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
    if metax.api_version == 'v2':
        assert requests_mock.last_request.qs["project_identifier"] == ["foo"]
        assert requests_mock.last_request.qs["file_path"] == [file_path]
    else:
        assert requests_mock.last_request.qs["csc_project"] == ["foo"]
        assert requests_mock.last_request.qs["pathname"] == [file_path]


@pytest.mark.parametrize(
    "results,results_v3",
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
            "results": (
                [_update_dict(V3_FILE, res) for res in results_v3]
                if metax.api_version == "v3"
                else results
            ),
        },
    )
    with pytest.raises(FileNotAvailableError):
        metax.get_project_file("foo", "/testdir/testfile")


@pytest.mark.parametrize(
    ["method", "parameters", "url"],
    [
        (
            METAX_CLIENT.get_project_directory,
            ["foo", "bar"],
            "/directories/files",
        ),
    ],
)
def test_directory_not_found(requests_mock, method, parameters, url):
    """Test error handling for missing directories.

    Sensible exception should be raised when trying to fetch metadata of
    directory that does not exist.

    :param requets_mock: HTTP request mocker
    :param method: Method to be tested
    :param parameters: parameters for tested method
    :param url: Metax url to be mocked
    """

    requests_mock.get(METAX_REST_URL + url, status_code=404)

    with pytest.raises(
        DirectoryNotAvailableError, match="Directory not found"
    ):
        method(*parameters)


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
    (
        ("/datasets", METAX_CLIENT.get_datasets, [], DatasetNotAvailableError),
        (
            "/contracts",
            METAX_CLIENT.get_contracts,
            [],
            ContractNotAvailableError,
        ),
        (
            "/contracts/foo",
            METAX_CLIENT.get_contract,
            ["foo"],
            ContractNotAvailableError,
        ),
        (
            "/datasets/foo/files",
            METAX_CLIENT.get_dataset_files,
            ["foo"],
            DatasetNotAvailableError,
        ),
    ),
)
def test_get_http_404(requests_mock, url, method, parameters, expected_error):
    """Test a method when Metax responds with 404 "Not found" error.

    The function should throw an exception.

    :param request_mock: requests mocker
    :param url: Metax url to be mocked
    :param method: Method to be tested
    :param parameters: Parameters for method call
    :param expected_error: Exception expected to raise
    """
    requests_mock.get(METAX_REST_URL + url, status_code=404)
    with pytest.raises(expected_error):
        method(*parameters)


@pytest.mark.parametrize(
    ("url", "method", "parameters"),
    (
        (
            f"/datasets?include_user_metadata=true&preservation_state="
            f'{quote("-1,0,10,20,30,40,50,60,65,70,75,80,90,100,110,120,130,140")}'
            f"&limit=1000000&offset=0",
            METAX_CLIENT.get_datasets,
            [],
        ),
        ("/contracts?limit=1000000&offset=0", METAX_CLIENT.get_contracts, []),
        ("/contracts/foo", METAX_CLIENT.get_contract, ["foo"]),
        (
            "/datasets/foo?include_user_metadata=true&file_details=true",
            METAX_CLIENT.get_dataset,
            ["foo"],
        ),
        (
            "/datasets/foo?dataset_format=datacite&dummy_doi=false",
            METAX_CLIENT.get_datacite,
            ["foo"],
        ),
        ("/datasets/foo/files", METAX_CLIENT.get_dataset_files, ["foo"]),
    ),
)
def test_get_http_503(requests_mock, caplog, url, method, parameters):
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
        METAX_REST_URL + url,
        status_code=503,
        reason="Metax error",
        text="Metax failed to process request",
    )
    with pytest.raises(requests.HTTPError) as error:
        method(*parameters)
    assert error.value.response.status_code == 503

    # Check logs
    logged_messages = [record.message for record in caplog.records]
    expected_message = (
        f"HTTP request to {METAX_REST_URL}{url} failed. Response from "
        "server was: Metax failed to process request"
    )
    assert expected_message in logged_messages


def test_set_preservation_state_http_503(requests_mock, metax):
    """Test ``set_preservation_state`` function.

    ``set_preservation_state`` should throw a HTTPError when requests.patch()
    returns http 503 error.
    """
    patch_preservation_url = (
        f"{metax.baseurl}/datasets/foobar/preservation"
        if metax.api_version == "v3"
        else f"{metax.baseurl}/datasets/foobar"
    )
    requests_mock.patch(patch_preservation_url, status_code=503)
    with pytest.raises(requests.HTTPError) as error:
        metax.set_preservation_state("foobar", "10", "foo")
    assert error.value.response.status_code == 503


@pytest.mark.parametrize("action", ["lock", "unlock"])
def test_lock_dataset(requests_mock, metax_v3, action):
    """Test locking/unlocking a dataset

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
                create_test_file(id="file_1"),
                create_test_file(id="file_2")
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
                create_test_file(id="file_3")
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


def test_get_dataset_template(requests_mock):
    """Test get_dataset_template function."""
    requests_mock.get(
        METAX_RPC_URL + "/datasets/get_minimal_dataset_template",
        json={"foo": "bar"},
    )
    assert METAX_CLIENT.get_dataset_template() == {"foo": "bar"}


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

    if metax.api_version == "v2":
        with pytest.raises(NotImplementedError):
            metax.get_file_format_versions()
    else:
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
    for k, v in expected_val.items():
        assert json[k] == v
    assert 'modified' in json
    assert 'created' in json


def _update_dict(original, update):
    original_copy = copy.deepcopy(original)
    original_copy |= update
    return original_copy
