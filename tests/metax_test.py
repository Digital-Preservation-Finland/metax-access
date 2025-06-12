import pytest
import requests
import lxml.etree

from contextlib import ExitStack as does_not_raise
from metax_access import (
    Metax,
    DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
)
from tests.utils import (
    create_test_dataset,
    create_test_contract,
    create_test_file,
    create_test_directory_files,
)
from metax_access.error import (
    ContractNotAvailableError,
    DataciteGenerationError,
    DatasetNotAvailableError,
    FileNotAvailableError,
    ResourceAlreadyExistsError,
)


@pytest.fixture
def metax():
    """Metax V3 client instance"""
    return Metax(url="https://foobar", token="token_foo", verify=False)


def test_init():
    """Test init function.

    Init function should raise exception if required parameters are not given.
    """
    error = "missing 2 required positional argument"
    with pytest.raises(TypeError, match=error) as exception:
        Metax()


@pytest.mark.parametrize(
    ("url", "method", "parameters", "expected_error"),
    [
        ("/datasets", "get_datasets", [], DatasetNotAvailableError),
        ("/datasets/foo", "get_dataset", ["foo"], DatasetNotAvailableError),
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
            "/files/foo",
            "get_file",
            ["foo"],
            FileNotAvailableError,
        ),
        (
            "/datasets/foo/files/bar",
            "get_dataset_file",
            ["foo", "bar"],
            FileNotAvailableError,
        ),
        (
            "/datasets/foo/files",
            "get_dataset_files",
            ["foo"],
            DatasetNotAvailableError,
        ),
        (
            "/datasets/foo/metadata-download",
            "get_datacite",
            ["foo"],
            DatasetNotAvailableError,
        ),
        (
            "/datasets/foo",
            "get_dataset_file_count",
            ["foo"],
            DatasetNotAvailableError,
        ),
    ],
)
def test_get_http_404(
    requests_mock, metax, url, method, parameters, expected_error
):
    """Test a method when Metax responds with 404 "Not found" error.

    The function should throw an exception.

    :param request_mock: requests mocker
    :param url: Metax url to be mocked
    :param method: Method to be tested
    :param parameters: Parameters for method call
    :param expected_error: Exception expected to raise
    """
    requests_mock.get(f"{metax.baseurl}{url}", status_code=404)
    with pytest.raises(expected_error):
        getattr(metax, method)(*parameters)


def test_get_http_503(requests_mock, metax, caplog):
    """Test a method when Metax responds with 503 "Server error".

    A method using `Metax.request()` should throw a HTTPError,
    and the content of response to failed request should be logged.
    This feature tested with one arbitarily selected method.

    :param request_mock: requests mocker
    :param caplog: log capturer
    """
    url = f"{metax.baseurl}/datasets?limit=1000000&offset=0&include_nulls=True"
    requests_mock.get(
        url,
        status_code=503,
        reason="Metax error",
        text="Metax failed to process request",
    )
    with pytest.raises(requests.HTTPError) as error:
        metax.get_datasets()
    assert error.value.response.status_code == 503

    # Check logs
    logged_messages = [record.message for record in caplog.records]
    expected_message = (
        f"HTTP request to {url} failed. Response from "
        "server was: Metax failed to process request"
    )
    assert expected_message in logged_messages


@pytest.mark.parametrize(
    ("qs"),
    [
        (None),
        (
            {
                "states": "states-param",
                "limit": "limit-param",
                "offset": "offset-param",
                "metadata_owner_org": "owner-org-param",
                "metadata_owner_user": "metadata-owner-user",
                "ordering": "ordering-param",
                "search": "search-param",
            }
        ),
    ],
)
def test_get_datasets(requests_mock, caplog, metax, qs):
    """Test ``get_datasets`` function.

    Mocks Metax to return simple JSON as HTTP response and checks that the
    returned dict contains the correct values.

    :returns: None
    """

    expected_datasets = [create_test_dataset(id=id_) for id_ in ["foo", "bar"]]
    metax_mock = requests_mock.get(
        f"{metax.baseurl}/datasets",
        json={"results": expected_datasets},
    )

    datasets = metax.get_datasets() if qs is None else metax.get_datasets(**qs)

    assert len(datasets["results"]) == 2
    # Check that correct query parameter were used
    query_string = metax_mock.last_request.qs
    if qs is None:
        assert query_string["limit"][0] == "1000000"
        assert query_string["offset"][0] == "0"
    else:
        assert query_string["limit"][0] == qs["limit"]
        assert query_string["offset"][0] == qs["offset"]
        assert query_string["ordering"][0] == qs["ordering"]
        assert query_string["preservation__state"][0] == qs["states"]
        assert query_string["search"][0] == qs["search"]
        assert (
            query_string["metadata_owner__organization"][0]
            == qs["metadata_owner_org"]
        )
        assert (
            query_string["metadata_owner__user"][0]
            == qs["metadata_owner_user"]
        )

    # No errors should be logged
    logged_errors = [r for r in caplog.records if r.levelname == "ERROR"]
    assert not logged_errors

    assert datasets["results"] == expected_datasets


def test_get_dataset_by_ids(requests_mock, caplog, metax):
    """Test ``get_datasets_by_ids`` function."""

    expected_datasets = [create_test_dataset(id=id_) for id_ in ["foo", "bar"]]
    metax_mock = requests_mock.get(
        f"{metax.baseurl}/datasets",
        json={"results": expected_datasets},
    )

    query_ids = ["foo", "bar", "cat"]
    datasets = metax.get_datasets_by_ids(query_ids)
    assert len(datasets["results"]) == 2
    # Check that correct query parameter were used
    query_string = metax_mock.last_request.qs

    assert query_string["limit"][0] == "1000000"
    assert query_string["offset"][0] == "0"
    assert query_string["id"] == query_ids

    # No errors should be logged
    logged_errors = [r for r in caplog.records if r.levelname == "ERROR"]
    assert not logged_errors

    assert datasets["results"] == expected_datasets


def test_get_dataset(requests_mock, metax):
    """Test ``get_dataset`` function.

    Mocks Metax to return simple JSON as HTTP
    response and checks that the returned dict contains the correct values.

    :returns: None
    """
    dataset_id = "123"
    url = f"{metax.baseurl}/datasets/{dataset_id}"
    json = create_test_dataset(id=dataset_id)

    requests_mock.get(
        url,
        json=json,
    )

    dataset = metax.get_dataset(dataset_id)
    assert dataset == json


def test_get_contract_datasets(requests_mock, metax, caplog):
    ids = ["foo", "bar"]
    contract_id = "contract"
    expected_datasets = [
        create_test_dataset(id=id_, preservation__contract=contract_id)
        for id_ in ids
    ]

    requests_mock.get(
        "https://url_to_next_page",
        json={"next": None, "results": [expected_datasets[1]]},
    )
    metax_mock = requests_mock.get(
        f"{metax.baseurl}/datasets",
        json={
            "next": "https://url_to_next_page",
            "results": [expected_datasets[0]],
        },
    )

    datasets = metax.get_contract_datasets(contract_id)
    assert len(datasets) == 2
    # Check that correct query parameter were used
    query_string = metax_mock.last_request.qs
    assert query_string["preservation__contract"][0] == contract_id

    # No errors should be logged
    logged_errors = [r for r in caplog.records if r.levelname == "ERROR"]
    assert not logged_errors

    assert datasets == expected_datasets


def test_post_dataset(requests_mock, metax):
    """Test ``post_dataset`` function.

    Test that HTTP POST request is sent to correct url.
    """
    url = f"{metax.baseurl}/datasets"
    json = create_test_dataset(title__en="A Test Dataset")

    requests_mock.post(url, json=json)

    dataset = metax.post_dataset(json)

    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.hostname == "foobar"
    assert requests_mock.last_request.path == "/v3/datasets"
    assert dataset == json


def test_get_contracts(requests_mock, metax):
    """Test ``get_contracts`` function.

    Mocks Metax to return simple JSON as HTTP
    response and checks that the returned dict contains the correct values.

    :returns: None
    """
    ids = ["foo", "bar"]
    expected_contracts = [create_test_contract(id=id_) for id_ in ids]
    metax_mock = requests_mock.get(
        f"{metax.baseurl}/contracts",
        json={"results": expected_contracts},
    )
    contracts = metax.get_contracts()
    assert len(contracts["results"]) == 2
    assert expected_contracts == contracts["results"]
    query_string = metax_mock.last_request.qs

    assert query_string["limit"][0] == "1000000"
    assert query_string["offset"][0] == "0"


def test_get_contract(requests_mock, metax):
    """Test ``get_contract`` function.

    Mocks Metax to return simple JSON as HTTP
    response and checks that the returned dict contains the correct values.

    :returns: None
    """
    contract_id = "bar"
    url = f"{metax.baseurl}/contracts/{contract_id}"
    expected_contract = create_test_contract(id=contract_id)

    contract = requests_mock.get(url, json=expected_contract)

    contract = metax.get_contract(contract_id)
    assert expected_contract == contract


def test_patch_contract(requests_mock, metax):
    """Test patch contract.

    If the update contains a dictionary value, i.e. organization field,
    only the new value is updated with `update_nested_dict` method.
    """
    contract_id = "contract_id"
    url = f"{metax.baseurl}/contracts/{contract_id}"

    requests_mock.get(url, json=create_test_contract(id=contract_id))

    update = {
        "title": {"und": "Testi otsikko"},
        "organization": {"name": "Testi organisaatio"},
    }
    updated_contract = create_test_contract(
        id=contract_id,
        title__und="Testi otsikko",
        organization__name="Testi organisaatio",
    )

    metax_mock = requests_mock.patch(url, json=updated_contract)
    result = metax.patch_contract(contract_id, update)

    assert updated_contract == result

    # utlis.update_nested_dict method updates the update dict
    # such that it now contains also the not updated values
    assert metax_mock.last_request.json() == update
    assert metax_mock.called_once


def test_post_contract(requests_mock, metax):
    """Test ``post_contract`` function.

    Test that HTTP POST request is sent to correct url.
    """
    url = f"{metax.baseurl}/contracts"
    json = create_test_contract(title__und="A Test contract")

    requests_mock.post(url, json=json)

    dataset = metax.post_contract(json)

    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.hostname == "foobar"
    assert requests_mock.last_request.path == "/v3/contracts"
    assert dataset == json


def test_get_file(requests_mock, metax):
    """File metadata is retrived with ``get_file`` method and
    the output is compared to the expected output.
    """
    file_id = "id_foo"
    url = f"{metax.baseurl}/files/{file_id}"
    expected_file = create_test_file(id=file_id)

    requests_mock.get(url, json=expected_file)
    file = metax.get_file(file_id)
    assert file == expected_file


def test_get_dataset_file(requests_mock, metax):
    """Test retrieving dataset specific file metadata."""
    dataset_id = "dataset-id"
    file_id = "file-id"
    url = f"{metax.baseurl}/datasets/{dataset_id}/files/{file_id}"
    expected_file = create_test_file(id=file_id)
    requests_mock.get(url, json=expected_file)

    assert metax.get_dataset_file(dataset_id, file_id) == expected_file


def test_get_dataset_files(requests_mock, metax):
    """File metadata is retrived with ``get_dataset_files`` method and
    the output is compared to the expected output.
    """
    dataset_id = "dataset_id"
    url = f"{metax.baseurl}/datasets/{dataset_id}/files"
    pagin_url = "https://plaa"
    files = [create_test_file(id=f"id_{i}") for i in range(0, 3)]

    requests_mock.get(url, json={"next": pagin_url, "results": files[0:2]})
    paging = requests_mock.get(
        pagin_url, json={"next": None, "results": files[2:]}
    )
    result_files = metax.get_dataset_files(dataset_id)

    assert files == result_files
    assert paging.called_once


@pytest.mark.parametrize(
    ("file_path", "results"),
    [
        # Only one matching file in Metax
        ("/dir/file", [create_test_file(pathname="/dir/file")]),
        # Two matching files in Metax. First one is not exact match.
        (
            "/dir/file",
            [
                create_test_file(pathname="/dir/file"),
                create_test_file(pathname="/dir/file/foo"),
            ],
        ),
        # file_path without leading '/' should work as well
        (
            "dir/file",
            [create_test_file(pathname="/dir/file")],
        ),
    ],
)
def test_get_project_file(file_path, results, requests_mock, metax):
    """Test get_project_file function.

    :param file_path: Path of file to get
    :param results: Matching files in Metax
    :param requets_mock: HTTP request mocker
    """
    requests_mock.get(
        metax.baseurl + "/files",
        json={"count": 1, "next": None, "previous": None, "results": results},
    )
    expected_file = create_test_file(pathname="/dir/file")
    assert metax.get_project_file("foo", file_path) == expected_file
    assert requests_mock.last_request.qs["csc_project"] == ["foo"]
    assert requests_mock.last_request.qs["pathname"] == [file_path]


@pytest.mark.parametrize(
    "results",
    [
        # One match is found, but it is not exact match
        [create_test_file(pathname="/testdir/testfile/foo", id="foo")],
        # No matches found
        [],
    ],
)
def test_get_project_file_not_found(results, requests_mock, metax):
    """Test searching file_path that is not available.

    :param results: Matching files in Metax
    :param requets_mock: HTTP request mocker
    """
    requests_mock.get(
        metax.baseurl + "/files",
        json={"count": 1, "next": None, "previous": None, "results": results},
    )
    with pytest.raises(FileNotAvailableError):
        metax.get_project_file("foo", "/testdir/testfile")


def test_get_files_dict(requests_mock, metax):
    """Test ``get_files_dict`` function.

    Metax is mocked to return files as two reponses.

    :returns: ``None``
    """
    url_1 = f"{metax.baseurl}/files?include_nulls=True&limit=10000&csc_project=test"
    file_1 = create_test_file(
        id="file1_identifier", pathname="/path/file1", storage_service="pas1"
    )
    url_2 = "https://next.url"
    file_2 = create_test_file(
        id="file2_identifier", pathname="/path/file2", storage_service="pas2"
    )

    requests_mock.get(
        url_1,
        json={
            "next": url_2,
            "results": [file_1],
        },
    )
    requests_mock.get(
        url_2,
        json={
            "next": None,
            "results": [file_2],
        },
    )

    files = metax.get_files_dict("test")
    assert set(files.keys()) == {file_1["pathname"], file_2["pathname"]}
    assert files[file_1["pathname"]] == {
        "identifier": file_1["id"],
        "storage_service": file_1["storage_service"],
    }
    assert files[file_2["pathname"]] == {
        "identifier": file_2["id"],
        "storage_service": file_2["storage_service"],
    }


def test_get_dataset_directory(requests_mock, metax):
    """Test get_dataset_directory function.

    :param requets_mock: HTTP request mocker
    """
    dataset_id = "dataset_id"
    dirpath = "/test_dir"

    url = f"{metax.baseurl}/datasets/{dataset_id}/directories?path={dirpath}"
    pagin_url = f"{metax.baseurl}/datasets/{dataset_id}/directories?path={dirpath}&page=2"
    dir = {
        "name": "sub_test_dir",
        "size": 50,
        "file_count": 2,
        "pathname": f"{dirpath}/sub_test_dir",
    }
    file = {"id": "12345678", "filename": "test.txt", "size": 25}

    requests_mock.get(
        url,
        json={
            "count": 2,
            "next": pagin_url,
            "results": create_test_directory_files(
                directory__pathname=dirpath, files=[file], directories=[]
            ),
        },
    )
    requests_mock.get(
        pagin_url,
        json={
            "count": 2,
            "next": None,
            "results": create_test_directory_files(
                directory__pathname=dirpath, files=[], directories=[dir]
            ),
        },
    )

    result = metax.get_dataset_directory(dataset_id, dirpath)

    assert result["directory"]["pathname"] == "/test_dir"

    assert len(result["directories"]) == 1
    assert result["directories"][0] == dir

    assert len(result["files"]) == 1
    assert result["files"][0] == file


def test_get_dataset_directory_fails(requests_mock, metax):
    """get_dataset_directory returns an empty response when Metax responses 404."""
    requests_mock.get(
        f"{metax.baseurl}/datasets/dataset_id/directories?path=/test_dir",
        status_code=404,
    )
    result = metax.get_dataset_directory("dataset_id", "/test_dir")
    assert result == {"directory": None, "directories": [], "files": []}


def test_set_preservation_state(requests_mock, metax):
    """Test ``set_preservation_state`` function.

    Metadata in Metax is modified by sending HTTP PATCH request with modified
    metadata in JSON format. This test checks that correct HTTP request is sent
    to Metax. The effect of the request is not tested.

    :returns: ``None``
    """
    requests_mock.patch(f"{metax.baseurl}/datasets/test_id/preservation")

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
    assert request_body["description"] == {"en": "Accepted to preservation"}

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
    url = f"{metax.baseurl}/datasets/{dataset_id}/create-preservation-version"
    dataset_url = f"{metax.baseurl}/datasets/{dataset_id}"
    response = create_test_dataset(
        id=dataset_id, preservation__contract=contract_id
    )

    requests_mock.get(dataset_url, json=response)
    post_create_preservation_version = requests_mock.post(url)

    metax.copy_dataset_to_pas_catalog(dataset_id)

    # Check that expected request was sent to Metax
    assert post_create_preservation_version.called_once


def test_copy_dataset_to_pas_catalog_no_contract(requests_mock, metax):
    """ "Test copy_dataset_to_pas_catalog function without a contract.

    A dataset without a contract can't be added to PAS Catalog.
    Check that an error is raised, for such dataset.
    """
    dataset_id = "dataset_id"
    url = f"{metax.baseurl}/datasets/{dataset_id}/create-preservation-version"
    dataset_url = f"{metax.baseurl}/datasets/{dataset_id}"
    response = create_test_dataset(id=dataset_id)

    requests_mock.get(dataset_url, json=response)
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
    dataset_id = "test_id"
    url = f"{metax.baseurl}/datasets/{dataset_id}/preservation"

    requests_mock.patch(url)

    metax.set_preservation_reason(dataset_id, "The reason.")

    # Check the method of last HTTP request
    assert requests_mock.last_request.method == "PATCH"
    assert requests_mock.last_request.json() == {
        "reason_description": "The reason."
    }


def test_set_pas_package_created(requests_mock, metax):
    """Test `set_pas_package_created` method."""
    patch_preservation = requests_mock.patch(
        "/v3/datasets/test-dataset-id/preservation"
    )
    metax.set_pas_package_created("test-dataset-id")
    assert patch_preservation.called_once
    assert patch_preservation.last_request.json() == {
        "pas_package_created": True
    }


@pytest.mark.parametrize("patch_characteristics_status", [200, 404])
def test_patch_file_characteristics(
    requests_mock, metax, patch_characteristics_status
):
    """Test patch_file_characteristics.

    :param requests_mock: HTTP Request mocker
    :param metax: Metax client
    :param patch_characteristics_status: HTTP status code of response
        for patching file characteristics.
    """
    # TODO: missing the case when the method return 404
    # Mock Metax
    patch_characteristics = requests_mock.patch(
        f"{metax.baseurl}/files/file-id/characteristics",
        status_code=patch_characteristics_status,
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
        },
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
    assert patch_file.last_request.json() == {
        "characteristics_extension": extension
    }


def test_get_datacite(requests_mock, metax):
    """Test ``get_datacite`` function.

    Read one field from returned XML and check its correctness.

    :returns: ``None``
    """
    # Read sample datacite from file and create mocked HTTP response
    dataset_id = "test_id"
    url = f"{metax.baseurl}/datasets/{dataset_id}/metadata-download?format=datacite&include_nulls=True"

    datacite = lxml.etree.parse("tests/data/xml/datacite_sample.xml")
    requests_mock.get(
        url,
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
        f"{metax.baseurl}/datasets/foo/metadata-download?format=datacite",
        json=response,
        status_code=400,
    )

    with pytest.raises(DataciteGenerationError) as exception:
        metax.get_datacite("foo")

    assert exception.value.message == "Datacite generation failed: Foobar."


@pytest.mark.parametrize("fileset", [{"total_files_count": 3}, None])
def test_get_dataset_file_count(requests_mock, metax, fileset):
    """Test retrieving the total file count for a dataset."""

    url = f"{metax.baseurl}/datasets/fake-dataset"
    json = {"fileset": fileset}

    requests_mock.get(
        url,
        json=json,
    )

    file_count = metax.get_dataset_file_count("fake-dataset")
    if fileset:
        assert file_count == fileset["total_files_count"]
    else:
        assert file_count == 0


@pytest.mark.parametrize(
    ("file_id_list", "json"),
    [(["id1", "id2"], {"id1": ["urn:dataset:aaffaaff"]}), ([], {})],
)
def test_get_file2dataset_dict(requests_mock, metax, file_id_list, json):
    """Test Metax.get_file2dataset_dict

    Dictionary is returned for files that contain datasets. Files without
    datasets are not included in the response.
    """
    req = requests_mock.post(
        f"{metax.baseurl}/files/datasets",
        json=json,
        # Ensure the request body has the requested file IDs
        additional_matcher=lambda req: req.json() == file_id_list,
    )
    result = metax.get_file2dataset_dict(file_id_list)
    if not file_id_list:
        assert not req.request_history
    assert result == json


def test_delete_files(metax, requests_mock):
    files = [create_test_file(id="foo"), create_test_file(id="bar")]
    req = requests_mock.post(f"{metax.baseurl}/files/delete-many")
    metax.delete_files(files)
    assert req.called_once


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
        # Some files already exist
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
        # Other errors occur
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
        # Some files already exist, also other errors occur
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
    ],
)
def test_post_files(
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
        f"{metax.baseurl}/files/post-many",
        status_code=status_code,
        json=response,
        reason=reason,
    )

    with expectation as exception_info:
        metax.post_files(
            [
                create_test_file(
                    id=i,
                    pathname=f"/foo{i}",
                    filename=f"foo{i}",
                    csc_project="testproject",
                )
                for i in range(1, 4)
            ]
        )

    if not isinstance(exception_info, does_not_raise):
        assert exception_info.value.response.json() == response


@pytest.mark.parametrize("action", ["lock", "unlock"])
def test_lock_dataset(requests_mock, metax, action):
    """Test for methods unlock_dataset and lock_dataset

    `pas_process_running` will be set to True or False for the dataset and its
    files, depending on whether the dataset is being locked or unlocked
    """
    requests_mock.patch(
        f"{metax.baseurl}/datasets/foobar/preservation?include_nulls=true",
        json={},
    )
    requests_mock.get(
        f"{metax.baseurl}/datasets/foobar/files?include_nulls=true&limit=10000",
        json={
            "results": [
                create_test_file(id="file_1"),
                create_test_file(id="file_2"),
            ],
            "next": f"{metax.baseurl}/datasets/foobar/files"
            "?include_nulls=true&page=2&limit=10000",
        },
    )
    requests_mock.get(
        f"{metax.baseurl}/datasets/foobar/files?include_nulls=true&page=2&limit=10000",
        json={"results": [create_test_file(id="file_3")], "next": None},
    )
    files_patch = requests_mock.post(
        f"{metax.baseurl}/files/patch-many?include_nulls=true", json={}
    )
    dataset_patch = requests_mock.patch(
        f"{metax.baseurl}/datasets/foobar/preservation", json={}
    )

    if action == "lock":
        metax.lock_dataset("foobar")
        expected_status = True
    elif action == "unlock":
        metax.unlock_dataset("foobar")
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


def test_set_contract(requests_mock, metax):
    """Test ``set_contract`` function.

    Patch the contract of a dataset and check that a correct
    HTTP request was sent to Metax.

    :returns: ``None``
    """
    dataset_id = "test_id"
    url = f"{metax.baseurl}/datasets/{dataset_id}/preservation"
    requests_mock.patch(url, json={})

    metax.set_contract(dataset_id, "new:contract:id")
    assert requests_mock.last_request.method == "PATCH"

    request_body = requests_mock.last_request.json()
    assert request_body["contract"] == "new:contract:id"
