# pylint: disable=no-member
"""Tests for ``metax_access.metax`` module."""
from contextlib import ExitStack as does_not_raise
from urllib.parse import quote

import lxml.etree
import pytest
import requests

from metax_access.metax import (
    Metax,
    DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
    DatasetNotAvailableError,
    ContractNotAvailableError,
    DirectoryNotAvailableError,
    DataCatalogNotAvailableError,
    DataciteGenerationError,
    ResourceAlreadyExistsError,
    FileNotAvailableError
)

METAX_URL = 'https://foobar'
METAX_REST_ROOT_URL = f'{METAX_URL}/rest'
METAX_REST_URL = f'{METAX_URL}/rest/v2'
METAX_RPC_URL = f'{METAX_URL}/rpc/v2'
METAX_USER = 'tpas'
METAX_PASSWORD = 'password'
METAX_CLIENT = Metax(METAX_URL, METAX_USER, METAX_PASSWORD, verify=False)


def test_init():
    """Test init function.

    Init function should raise exception if required parameters are not given.
    """
    with pytest.raises(ValueError) as exception:
        Metax(METAX_URL)
    assert str(exception.value) == "Metax user or access token is required."


def test_get_datasets(requests_mock, caplog):
    """Test ``get_datasets`` function.

    Mocks Metax to return simple JSON as HTTP response and checks that the
    returned dict contains the correct values.

    :returns: None
    """
    metax_mock = requests_mock.get(
        METAX_REST_URL + "/datasets",
        json={"results": [{"identifier": "foo"}, {"identifier": "bar"}]}
    )
    datasets = METAX_CLIENT.get_datasets()
    assert len(datasets["results"]) == 2

    # Check that correct query parameter were used
    query_string = metax_mock.last_request.qs
    assert query_string['preservation_state'][0] \
        == '0,10,20,30,40,50,60,65,70,75,80,90,100,110,120,130,140'
    assert query_string['limit'][0] == '1000000'
    assert query_string['offset'][0] == '0'
    assert query_string['include_user_metadata'][0] == 'true'

    # No errors should be logged
    logged_errors = [r for r in caplog.records if r.levelname == 'ERROR']
    assert not logged_errors


def test_get_datasets_with_parameters(requests_mock):
    """Test ``get_datasets`` function parameters.

    :returns: None
    """
    metax_mock = requests_mock.get(METAX_REST_URL + "/datasets", json={})
    METAX_CLIENT.get_datasets(
        states="states-param",
        limit="limit-param",
        offset="offset-param",
        pas_filter='pas-filter-param',
        metadata_owner_org='owner-org-param',
        metadata_provider_user='provider-user-param',
        ordering='ordering-param',
        include_user_metadata=False
    )
    query_string = metax_mock.last_request.qs
    assert query_string['preservation_state'][0] == 'states-param'
    assert query_string['limit'][0] == 'limit-param'
    assert query_string['offset'][0] == 'offset-param'
    assert query_string['pas_filter'][0] == 'pas-filter-param'
    assert query_string['metadata_owner_org'][0] == 'owner-org-param'
    assert query_string['metadata_provider_user'][0] == 'provider-user-param'
    assert query_string['ordering'][0] == 'ordering-param'
    assert 'include_user_metadata' not in query_string


def test_get_dataset(requests_mock):
    """Test ``get_dataset`` function.

    Mocks Metax to return simple JSON as HTTP
    response and checks that the returned dict contains the correct values.

    :returns: None
    """
    requests_mock.get(METAX_REST_URL + "/datasets/test_id?include_user_metadata=true&file_details=true",
                      json={"foo": "bar"})
    dataset = METAX_CLIENT.get_dataset("test_id")
    assert dataset["foo"] == "bar"


def test_get_contracts(requests_mock):
    """Test ``get_contracts`` function.

    Mocks Metax to return simple JSON as HTTP
    response and checks that the returned dict contains the correct values.

    :returns: None
    """
    requests_mock.get(
        METAX_REST_URL + "/contracts",
        json={"results": [{"identifier": "foo"}, {"identifier": "bar"}]}
    )
    contracts = METAX_CLIENT.get_contracts()
    assert len(contracts['results']) == 2


def test_get_contract(requests_mock):
    """Test ``get_contract`` function.

    Mocks Metax to return simple JSON as HTTP
    response and checks that the returned dict contains the correct values.

    :returns: None
    """
    requests_mock.get(METAX_REST_URL + "/contracts/test_id",
                      json={"foo": "bar"})
    contract = METAX_CLIENT.get_contract('test_id')
    assert contract['foo'] == "bar"


def test_get_datacatalog(requests_mock):
    """Test ``get_datacatalog`` function.

    Mocks HTTP response to return simple JSON and checks that returned dict
    contains the correct values.

    :returns: ``None``
    """
    requests_mock.get(METAX_REST_URL + "/datacatalogs/test_catalog",
                      json={"catalog_json": {"identifier": 'foo'}})

    catalog = METAX_CLIENT.get_datacatalog('test_catalog')
    assert catalog['catalog_json']['identifier'] == 'foo'


def test_get_dataset_filetypes(requests_mock):
    """Test ``get_dataset`` filetypes function.

    Mocks Metax HTTP response and checks that the function returns dictionary
    with correct items.

    :returns: ``None``
    """
    requests_mock.get(
        METAX_REST_URL + '/datasets/test_id/files',
        json=[
            {
                "file_characteristics": {
                    "file_format": "text/plain",
                    "format_version": "",
                    "encoding": "UTF-8",
                }
            },
            {
                "file_characteristics": {
                    "file_format": "text/html",
                    "format_version": "4.01",
                    "encoding": "UTF-8",
                }
            }
        ]
    )

    filetypes = METAX_CLIENT.get_dataset_filetypes('test_id')
    assert isinstance(filetypes, dict)
    assert filetypes['total_count'] == 2
    assert filetypes['filetypes'][0]['encoding'] == 'UTF-8'
    assert filetypes['filetypes'][0]['file_format'] == 'text/plain' or\
        filetypes['filetypes'][0]['file_format'] == 'text/html'
    assert filetypes['filetypes'][0]['format_version'] == '' or\
        filetypes['filetypes'][0]['format_version'] == '4.01'


def test_get_dataset_file_count(requests_mock):
    """Test retrieving the total file count for a dataset"""
    def _request_has_correct_params(req):
        return req.qs["file_fields"] == ["id"]

    requests_mock.get(
        f"{METAX_REST_URL}/datasets/fake-dataset/files",
        additional_matcher=_request_has_correct_params,
        json=[
            {
                "id": 1
            },
            {
                "id": 3
            },
            {
                "id": 10
            }
        ]
    )

    file_count = METAX_CLIENT.get_dataset_file_count("fake-dataset")
    assert file_count == 3


def test_get_dataset_file_count_not_found(requests_mock):
    """
    Test retrieving the total file count for a dataset and ensure that
    DatasetNotAvailableError is raised if the dataset does not exist.
    """
    requests_mock.get(
        f"{METAX_REST_URL}/datasets/does-not-exist/files",
        additional_matcher=lambda req: req.qs["file_fields"] == ["id"],
        status_code=404
    )

    with pytest.raises(DatasetNotAvailableError):
        METAX_CLIENT.get_dataset_file_count("does-not-exist")


def test_patch_dataset(requests_mock):
    """Test ``patch_dataset`` function.

    Patch a dataset with few updated key/value pairs and check that correct
    HTTP request was sent to Metax.

    :returns: ``None``
    """
    requests_mock.patch(METAX_REST_URL + '/datasets/test_id', json={})
    requests_mock.get(
        METAX_REST_URL + '/datasets/test_id',
        json={'research_dataset': {"provenance": ['foo', 'bar']}}
    )

    update = {
        'foo1': 'bar1',
        'research_dataset': {
            'foo2': 'bar2'
        }
    }
    METAX_CLIENT.patch_dataset('test_id', update)
    assert requests_mock.last_request.method == 'PATCH'

    request_body = requests_mock.last_request.json()
    assert isinstance(request_body['research_dataset']['provenance'], list)
    assert request_body['research_dataset']['foo2'] == 'bar2'
    assert request_body['foo1'] == 'bar1'


def test_get_xml(requests_mock):
    """Test ``get_xml`` function.

    Mocks Metax HTTP responses and and checks that the function returns
    dictionary that contains xml objects.

    :returns: ``None``
    """
    requests_mock.get(METAX_REST_URL + '/files/test_id/xml',
                      json=["http://www.loc.gov/METS/",
                            "http://www.arkivverket.no/standarder/addml"])
    requests_mock.get((METAX_REST_URL + '/files/test_id/xml?namespace=http://'
                       'www.arkivverket.no/standarder/addml'),
                      text=('<root xmlns:addml="http://www.arkivverket.no/'
                            'standarder/addml"></root>'))
    requests_mock.get(
        METAX_REST_URL+'/files/test_id/xml?namespace=http://www.loc.gov/METS/',
        text='<root xmlns:mets="http://www.loc.gov/METS/"></root>'
    )

    xml_dict = METAX_CLIENT.get_xml("test_id")
    assert isinstance(xml_dict, dict)

    # The keys of returned dictionary should be xml namespace urls and
    # the values of returned dictionary should be lxml.etree.ElementTree
    # objects with the namespaces defined
    addml_url = "http://www.arkivverket.no/standarder/addml"
    assert xml_dict[addml_url].getroot().nsmap['addml'] == addml_url
    mets_url = "http://www.loc.gov/METS/"
    assert xml_dict[mets_url].getroot().nsmap['mets'] == mets_url


def test_set_xml(requests_mock):
    """Test ``set_xml`` functions.

    Reads XML file and posts it to Metax. The body
    and headers of HTTP request are checked.

    :returns: ``None``
    """
    requests_mock.get(METAX_REST_URL + '/files/set_xml_1/xml', json=[])
    requests_mock.post(METAX_REST_URL + '/files/set_xml_1/xml',
                       status_code=201)

    # Read sample MIX xml file
    mix = lxml.etree.parse('./tests/data/mix_sample.xml').getroot()

    # POST XML to Metax
    assert METAX_CLIENT.set_xml('set_xml_1', mix)

    # Check that posted message body is valid XML
    lxml.etree.fromstring(requests_mock.last_request.body)

    # Check message headers
    assert requests_mock.last_request.headers['content-type'] \
        == 'application/xml'

    # Check that message method is correct
    assert requests_mock.last_request.method == 'POST'

    # Check that message query string has correct parameters
    assert requests_mock.last_request.qs['namespace'][0] \
        == 'http://www.loc.gov/mix/v20'


# pylint: disable=invalid-name
def test_set_xml_metadata_already_set(requests_mock):
    """Test ``set_xml`` functions.

    Reads XML file and posts it to Metax. The body and headers of HTTP request
    are checked.

    :returns: ``None``
    """
    requests_mock.get(METAX_REST_URL + '/files/xml_metadata_already_set/xml',
                      json=['http://www.loc.gov/mix/v20'])
    requests_mock.get(METAX_REST_URL + '/files/xml_metadata_already_set/xml'
                      '?namespace=http://www.loc.gov/mix/v20',
                      text='<foo></foo>')

    # Read sample MIX xml file
    mix = lxml.etree.parse('./tests/data/mix_sample.xml').getroot()

    # POST XML to Metax
    assert not METAX_CLIENT.set_xml('xml_metadata_already_set', mix)

    # Check that message method is correct
    assert requests_mock.last_request.method == 'GET'
    assert requests_mock.last_request.qs['namespace'][0] ==\
        'http://www.loc.gov/mix/v20'


def test_get_datacite(requests_mock):
    """Test ``get_datacite`` function.

    Read one field from returned XML and check its correctness.

    :returns: ``None``
    """
    # Read sample datacite from file and create mocked HTTP response
    datacite = lxml.etree.parse('tests/data/datacite_sample.xml')
    requests_mock.get(
        METAX_REST_URL +
        '/datasets/test_id?dataset_format=datacite&dummy_doi=false',
        complete_qs=True,
        content=lxml.etree.tostring(datacite)
    )

    requests_mock.get(METAX_REST_URL + "/datasets/test_id",
                      complete_qs=True,
                      json={'identifier': 'test_id'})

    xml = lxml.etree.fromstring(METAX_CLIENT.get_datacite("test_id"))

    # Read field "creatorName" from xml file
    ns_string = 'http://datacite.org/schema/kernel-4'
    xpath_str = '/ns:resource/ns:creators/ns:creator/ns:creatorName'
    creatorname = xml.xpath(xpath_str, namespaces={'ns': ns_string})[0].text

    # Check that "creatorName" is same as in the original XML file
    assert creatorname == "Puupää, Pekka"


def test_get_datacite_fails(requests_mock):
    """Test ``get_datacite`` function when Metax returns 400.

    :returns: ``None``
    """
    # Mock metax dataset request response. Response body contains simplified
    # dataset metadata.
    requests_mock.get(
        METAX_REST_URL + '/datasets/foo',
        json={"identifier": "foo"}
    )

    # Mock datacite request response. Mocked response has status code 400, and
    # response body contains error information.
    response = \
        {
            "detail": "Foobar.",
            "error_identifier": "2019-03-28T12:39:01-f0a7e3ae"
        }
    requests_mock.get(
        METAX_REST_URL + '/datasets/foo?dataset_format=datacite',
        json=response,
        status_code=400
    )

    with pytest.raises(DataciteGenerationError) as exception:
        METAX_CLIENT.get_datacite("foo")

    assert exception.value.message == "Datacite generation failed: Foobar."


def test_set_preservation_state(requests_mock):
    """Test ``set_preservation_state`` function.

    Metadata in Metax is modified by sending HTTP PATCH request with modified
    metadata in JSON format. This test checks that correct HTTP request is sent
    to Metax. The effect of the request is not tested.

    :returns: ``None``
    """
    requests_mock.get(METAX_REST_URL + '/datasets/test_id', json={})
    requests_mock.patch(METAX_REST_URL + '/datasets/test_id')

    METAX_CLIENT.set_preservation_state(
        "test_id",
        DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
        'Accepted to preservation'
    )

    # Check the body of last HTTP request
    request_body = requests_mock.last_request.json()
    assert request_body["preservation_state"] ==\
        DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE
    assert request_body["preservation_description"] \
        == "Accepted to preservation"

    # Check the method of last HTTP request
    assert requests_mock.last_request.method == 'PATCH'


def test_set_preservation_reason(requests_mock):
    """Test ``set_preservation_reason`` method.

    Test that the method sends correct PATCH request to Metax.

    :returns: ``None``
    """
    requests_mock.patch(METAX_REST_URL + '/datasets/test_id')

    METAX_CLIENT.set_preservation_reason("test_id", 'The reason.')

    # Check the method of last HTTP request
    assert requests_mock.last_request.method == 'PATCH'
    assert requests_mock.last_request.json() \
        == {'preservation_reason_description': 'The reason.'}


def test_patch_file(requests_mock):
    """Test ``patch_file`` function.

    Metadata in Metax is modified by sending HTTP PATCH request with modified
    metadata in JSON format. This test checks that correct HTTP request is sent
    to Metax, and that patch_file returns JSON response from Metax.

    :returns: None
    """
    # Mock Metax
    requests_mock.get(METAX_REST_URL + '/files/test_id', json={})
    requests_mock.patch(METAX_REST_URL + '/files/test_id', json={'foo': 'bar'})

    # Patch a file
    sample_data = {
        "file_characteristics": {
            "file_format": "text/plain",
            "format_version": "1.0",
            "encoding": "UTF-8"
        }
    }
    assert METAX_CLIENT.patch_file('test_id', sample_data) == {'foo': 'bar'}

    # Check the body of last HTTP request
    request_body = requests_mock.last_request.json()
    assert request_body == sample_data

    # Check the method of last HTTP request
    assert requests_mock.last_request.method == 'PATCH'


def test_delete_file(requests_mock):
    """Test ``delete_file`` function.

    Test that HTTP DELETE request is sent to correct url.
    """
    requests_mock.delete(METAX_REST_URL + "/files/file1",
                         json={"deleted_files_count": 1})

    METAX_CLIENT.delete_file('file1')

    assert requests_mock.last_request.method == "DELETE"
    assert requests_mock.last_request.hostname == 'foobar'
    assert requests_mock.last_request.path == '/rest/v2/files/file1'


def test_delete_dataset(requests_mock):
    """Test ``delete_dataset`` function.

    Test that HTTP DELETE request is sent to correct url.
    """
    requests_mock.delete(METAX_REST_URL + "/datasets/dataset1")

    METAX_CLIENT.delete_dataset('dataset1')

    assert requests_mock.last_request.method == "DELETE"
    assert requests_mock.last_request.hostname == 'foobar'
    assert requests_mock.last_request.path == '/rest/v2/datasets/dataset1'


def test_post_file(requests_mock):
    """Test ``post_file`` function.

    Test that HTTP POST request is sent to correct url.
    """
    requests_mock.post(METAX_REST_URL + '/files/', json={'identifier': '1'})

    METAX_CLIENT.post_file({'identifier': '1'})

    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.hostname == 'foobar'
    assert requests_mock.last_request.path == '/rest/v2/files/'


@pytest.mark.parametrize(
    ('response', 'expected_exception'),
    [
        # Trying to post file, path already exists
        (
            {"file_path": ["a file with path /foo already exists in"
                           " project bar"]},
            ResourceAlreadyExistsError("Some of the files already exist.")
        ),
        # Trying to post file, path and identifier already exist
        (
            {"file_path": ["a file with path /foo already exists in"
                           " project bar"],
             "identifier": ["a file with given identifier already exists"]},
            ResourceAlreadyExistsError("Some of the files already exist.")
        ),
        # Unknown error
        (
            {"file_path": ["Some other error in file path"]},
            requests.HTTPError('400 Client Error: Bad Request for url: '
                               'https://foobar/rest/v2/files/')
        ),
        # Multiple files that already exist
        (
            {
                'failed': [
                    {
                        'object': {
                            'identifier': 'foo1',
                            'file_path': '/foo1'
                        },
                        'errors': {
                            "file_path": ["a file with path /foo1 already "
                                          "exists in project bar"]
                        }
                    },
                    {
                        'object': {
                            'identifier': 'foo2',
                            'file_path': '/foo2'
                        },
                        'errors': {
                            "file_path": ["a file with path /foo2 already "
                                          "exists in project bar"]
                        }
                    }
                ]
            },
            ResourceAlreadyExistsError("Some of the files already exist.")
        ),
        # Multiple files, one already exists, one has other error
        (
            {
                'failed': [
                    {
                        'errors': {
                            "file_path": ["a file with path /foo1 already "
                                          "exists in project bar"]
                        }
                    },
                    {
                        'errors': {
                            "file_path": ["Other error"]
                        }
                    }
                ]
            },
            requests.HTTPError('400 Client Error: Bad Request for url: '
                               'https://foobar/rest/v2/files/')
        ),
    ]
)
def test_post_file_bad_request(requests_mock, response, expected_exception):
    """Test post file failures.

    If Metax responds with HTTP 400 "Bad request" error, an exception
    should be raised.

    :param response: Mocked response from Metax
    :param expected_exception: expected exception
    """
    requests_mock.post(METAX_REST_URL + '/files/',
                       status_code=400,
                       json=response,
                       reason='Bad Request')

    with pytest.raises(expected_exception.__class__,
                       match=str(expected_exception)):
        METAX_CLIENT.post_file({'identifier': '1',
                                'file_path': '/foo',
                                'project_identifier': 'bar'})


@pytest.mark.parametrize(
    ('status_code', 'reason', 'response', 'expectation'),
    [
        # Success
        (
            200,
            None,
            {
                "success": [
                    {"object": {"file_path": "/foo1"}},
                    {"object": {"file_path": "/foo2"}},
                    {"object": {"file_path": "/foo3"}},
                ],
                "failed": []
            },
            does_not_raise()
        ),
        # Some files already exist
        (
            400,
            'Bad Request',
            {
                "success": [
                    {"object": {"file_path": "/foo1"}},
                ],
                "failed": [

                    {"object": {'identifier': 'foo2', "file_path": "/foo2"},
                     "errors": {"file_path": ["a file with path /foo2.png "
                                              "already exists in project "
                                              "testproject"]}},
                    {"object": {'identifier': 'foo3', "file_path": "/foo3"},
                     "errors": {"file_path": ["a file with path /foo3.png "
                                              "already exists in project "
                                              "testproject"]}},
                ]
            },
            pytest.raises(
                ResourceAlreadyExistsError,
                match="Some of the files already exist."
            )
        ),
        # Other errors occur
        (
            400,
            'Bad Request',
            {
                "success": [
                    {"object": {"file_path": "/foo1"}},
                ],
                "failed": [

                    {"object": {"file_path": "/foo2"},
                     "errors": {"file_path": ["Unknown error"]}},
                    {"object": {"file_path": "/foo3"},
                     "errors": {"file_path": ["Unknown error"]}},
                ]
            },
            pytest.raises(requests.HTTPError,
                          match='400 Client Error: Bad Request for url: '
                          'https://foobar/rest/v2/files/')
        ),
        # Some files already exist, also other errors occur
        (
            400,
            'Bad Request',
            {
                "success": [
                    {"object": {"file_path": "/foo1"}},
                ],
                "failed": [

                    {"object": {"file_path": "/foo2"},
                     "errors": {"file_path": ["a file with path /foo2.png "
                                              "already exists in project "
                                              "testproject"]}},
                    {"object": {"file_path": "/foo3"},
                     "errors": {"file_path": ["Unknown error"]}},
                ]
            },
            pytest.raises(requests.HTTPError,
                          match='400 Client Error: Bad Request for url: '
                          'https://foobar/rest/v2/files/')
        ),
    ]
)
def test_post_multiple_files(requests_mock, status_code, reason, response,
                             expectation):
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
    requests_mock.post(METAX_REST_URL + '/files/',
                       status_code=status_code,
                       json=response,
                       reason=reason)

    with expectation as exception_info:
        METAX_CLIENT.post_file([
            {'identifier': '1',
             'file_path': '/foo1',
             'project_identifier': 'testproject'},
            {'identifier': '2',
             'file_path': '/foo2',
             'project_identifier': 'testproject'},
            {'identifier': '3',
             'file_path': '/foo3',
             'project_identifier': 'testproject'},
        ])

    if not isinstance(exception_info, does_not_raise):
        assert exception_info.value.response.json() == response


def test_post_dataset(requests_mock):
    """Test ``post_dataset`` function.

    Test that HTTP POST request is sent to correct url.
    """
    requests_mock.post(METAX_REST_URL + '/datasets/', json={'identifier': '1'})

    METAX_CLIENT.post_dataset({'identifier': '1'})

    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.hostname == 'foobar'
    assert requests_mock.last_request.path == '/rest/v2/datasets/'


def test_query_datasets(requests_mock):
    """Test ``query_datasets`` function.

    Mocks Metax to return simple JSON as HTTP response and checks that the
    returned dict contains the correct values.

    :returns: ``None``
    """
    requests_mock.get(
        METAX_REST_URL + "/datasets?preferred_identifier=foobar",
        json={"results": [{"identifier": "foo"}]}
    )
    datasets = METAX_CLIENT.query_datasets({'preferred_identifier': 'foobar'})
    assert len(datasets["results"]) == 1


def test_get_dataset_by_ids(requests_mock):
    """Test ``get_datasets_by_ids`` function.

    Test that correct results are returned depending on whether specific
    fields are requested.
    """
    requests_mock.post(
        f"{METAX_REST_ROOT_URL}/datasets/list?limit=1000000&offset=0",
        additional_matcher=lambda req: req.json() == [1, 3],
        json={
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": 1,
                    "project_identifier": "blah",
                    "research_dataset": {"title": "Dataset 1"}
                },
                {
                    "id": 3,
                    "project_identifier": "bleh",
                    "research_dataset": {"title": "Dataset 3"}
                }
            ]
        }
    )
    requests_mock.post(
        f"{METAX_REST_ROOT_URL}/datasets/list"
        "?fields=id,project_identifier&limit=1000000&offset=0",
        additional_matcher=lambda req: req.json() == [1, 3],
        json={
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": 1,
                    "project_identifier": "blah"
                },
                {
                    "id": 3,
                    "project_identifier": "bleh"
                }
            ]
        }
    )

    response = METAX_CLIENT.get_datasets_by_ids([1, 3])
    assert len(response["results"]) == 2
    assert response["results"][0]["research_dataset"]["title"] == "Dataset 1"

    # Only retrieve 'id' and 'project_identifier' fields
    response = METAX_CLIENT.get_datasets_by_ids(
        [1, 3], fields=["id", "project_identifier"]
    )
    assert "research_dataset" not in response["results"][0]


def test_get_files_dict(requests_mock):
    """Test ``get_files_dict`` function.

    Metax is mocked to return files as two reponses.

    :returns: ``None``
    """
    first_response = {
        "next": "https://next.url",
        "results": [
            {
                "id": 28260,
                "file_path": "/path/file1",
                "file_storage": {
                    "id": 1,
                    "identifier": "urn:nbn:fi:att:file-storage-pas"
                },
                "identifier": "file1_identifier"
            }
        ]
    }
    second_response = {
        "next": None,
        "results": [
            {
                "id": 23125,
                "file_path": "/path/file2",
                "file_storage": {
                    "id": 1,
                    "identifier": "urn:nbn:fi:att:file-storage-pas"
                },
                "identifier": "file2_identifier"
            }
        ]
    }
    requests_mock.get(
        METAX_REST_URL + "/files?limit=10000&project_identifier=test",
        json=first_response
    )
    requests_mock.get(
        "https://next.url",
        json=second_response
    )
    files = METAX_CLIENT.get_files_dict("test")
    assert "/path/file1" in files
    assert "/path/file2" in files
    assert files["/path/file1"]['id'] == 28260
    assert files["/path/file1"]['identifier'] == "file1_identifier"
    assert files["/path/file1"]['storage_identifier'] ==\
        "urn:nbn:fi:att:file-storage-pas"


def test_get_directory(requests_mock):
    """Test get_directory function.

    :param requets_mock: HTTP request mocker
    """
    metadata = {'identifier': 'foo'}
    requests_mock.get(METAX_REST_URL + "/directories/foo",
                      json=metadata)
    assert METAX_CLIENT.get_directory('foo') == metadata


def test_get_directory_files(requests_mock):
    """Test get_directory_files function.

    :param requets_mock: HTTP request mocker
    """
    metadata = {'identifier': 'foo'}
    requests_mock.get(METAX_REST_URL + "/directories/foo/files",
                      json=metadata)
    assert METAX_CLIENT.get_directory_files('foo') == metadata


def test_get_directory_files_dataset(requests_mock):
    """Test get_directory_files function with dataset_identifier parameter.

    :param requets_mock: HTTP request mocker
    """
    metadata = {'identifier': 'foo'}
    requests_mock.get(METAX_REST_URL + "/directories/foo/files?cr_identifier=bar",
                      json=metadata)
    assert METAX_CLIENT.get_directory_files('foo', dataset_identifier='bar') \
        == metadata


def test_get_project_directory(requests_mock):
    """Test get_project_directory function.

    :param requets_mock: HTTP request mocker
    """
    metadata = {
        'directories': [{'identifier': 'bar'}],
        'identifier': 'foo'
    }
    requests_mock.get(METAX_REST_URL + "/directories/files", json=metadata)
    assert METAX_CLIENT.get_project_directory('foo', '/testdir') \
        == {'identifier': 'foo'}
    assert requests_mock.last_request.qs['project'] == ['foo']
    assert requests_mock.last_request.qs['path'] == ['/testdir']
    assert requests_mock.last_request.qs['directories_only'] == ['true']


@pytest.mark.parametrize(
    'file_path,results',
    [
        # Only one matching file in Metax
        (
            '/dir/file',
            [{"file_path": "/dir/file"}],
        ),
        # Two matching files in Metax. First one is not exact match.
        (
            '/dir/file',
            [{"file_path": "/dir/file/foo"}, {"file_path": "/dir/file"}]
        ),
        # file_path without leading '/' should work as well
        (
            'dir/file',
            [{"file_path": "/dir/file"}],
        )
    ]
)
def test_get_project_file(file_path, results, requests_mock):
    """Test get_project_file function.

    :param file_path: Path of file to get
    :param results: Matching files in Metax
    :param requets_mock: HTTP request mocker
    """
    requests_mock.get(
        METAX_REST_URL + "/files",
        json={
            "count": 1,
            "next": None,
            "previous": None,
            "results": results
        }
    )
    assert METAX_CLIENT.get_project_file("foo", file_path)["file_path"] \
        == "/dir/file"
    assert requests_mock.last_request.qs['project_identifier'] == ['foo']
    assert requests_mock.last_request.qs['file_path'] == [file_path]


@pytest.mark.parametrize(
    'results',
    (
        # One match is found, but it is not exact match
        [
            {"file_path": "/testdir/testfile/foo", "identifier": "foo"}
        ],
        # No matches found
        []
    )
)
def test_get_project_file_not_found(results, requests_mock):
    """Test searching file_path that is not available.

    :param results: Matching files in Metax
    :param requets_mock: HTTP request mocker
    """
    requests_mock.get(
        METAX_REST_URL + "/files",
        json={
            "count": 1,
            "next": None,
            "previous": None,
            "results": results
        }
    )
    with pytest.raises(FileNotAvailableError):
        METAX_CLIENT.get_project_file('foo', '/testdir/testfile')


@pytest.mark.parametrize(
    ['method', 'parameters', 'url'],
    [
        (
            METAX_CLIENT.get_directory,
            ['foo'],
            '/directories/foo'
        ),
        (
            METAX_CLIENT.get_directory_files,
            ['foo'],
            '/directories/foo/files'
        ),
        (
            METAX_CLIENT.get_project_directory,
            ['foo', 'bar'],
            '/directories/files'
        ),
    ]
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

    with pytest.raises(DirectoryNotAvailableError,
                       match='Directory not found'):
        method(*parameters)


def test_get_file2dataset_dict(requests_mock):
    """Test Metax.get_file2dataset_dict

    Dictionary is returned for files that contain datasets. Files without
    datasets are not included in the response.
    """
    requests_mock.post(
        f"{METAX_REST_URL}/files/datasets",
        json={"161bc25962da8fed6d2f59922fb642": ["urn:dataset:aaffaaff"]},
        # Ensure the request body has the requested file IDs
        additional_matcher=lambda req: req.json() == [10, 20]
    )
    result = METAX_CLIENT.get_file2dataset_dict([10, 20])

    # The response uses hex-formatted identifiers instead of integers
    assert result["161bc25962da8fed6d2f59922fb642"] == ["urn:dataset:aaffaaff"]


def test_get_file2dataset_dict_empty(requests_mock):
    """Test Metax.get_file2dataset dict with an empty list of file identifiers
    """
    mocked_req = requests_mock.post(
        f"{METAX_REST_URL}/files/datasets",
        status_code=400
    )
    result = METAX_CLIENT.get_file2dataset_dict([])

    assert result == {}

    # The mocked endpoint was not called
    assert not mocked_req.request_history


@pytest.mark.parametrize(
    ('url', 'method', 'parameters', 'expected_error'),
    (
        ('/datasets', METAX_CLIENT.get_datasets, [],
         DatasetNotAvailableError),
        ('/contracts', METAX_CLIENT.get_contracts, [],
         ContractNotAvailableError),
        ('/contracts/foo', METAX_CLIENT.get_contract, ['foo'],
         ContractNotAvailableError),
        ('/datacatalogs/foo', METAX_CLIENT.get_datacatalog, ['foo'],
         DataCatalogNotAvailableError),
        ('/datasets/foo/files', METAX_CLIENT.get_dataset_files, ['foo'],
         DatasetNotAvailableError),
    )
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
    ('url', 'method', 'parameters'),
    (
        (
            f'/datasets?include_user_metadata=true&preservation_state='
            f'{quote("0,10,20,30,40,50,60,65,70,75,80,90,100,110,120,130,140")}'
            f'&limit=1000000&offset=0',
            METAX_CLIENT.get_datasets,
            []
        ),
        ('/contracts?limit=1000000&offset=0', METAX_CLIENT.get_contracts, []),
        ('/contracts/foo', METAX_CLIENT.get_contract, ['foo']),
        ('/datacatalogs/foo', METAX_CLIENT.get_datacatalog, ['foo']),
        ('/datasets/foo?include_user_metadata=true&file_details=true',
         METAX_CLIENT.get_dataset, ['foo']),
        ('/files/foo/xml', METAX_CLIENT.get_xml, ['foo']),
        ('/datasets/foo?dataset_format=datacite&dummy_doi=false',
         METAX_CLIENT.get_datacite, ['foo']),
        ('/datasets/foo/files', METAX_CLIENT.get_dataset_files, ['foo']),
    )
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
    requests_mock.get(METAX_REST_URL + url,
                      status_code=503,
                      reason='Metax error',
                      text='Metax failed to process request')
    with pytest.raises(requests.HTTPError) as error:
        method(*parameters)
    assert error.value.response.status_code == 503

    # Check logs
    logged_messages = [record.message for record in caplog.records]
    expected_message = (
        f'HTTP request to {METAX_REST_URL}{url} failed. Response from '
        'server was: Metax failed to process request'
    )
    assert expected_message in logged_messages


def test_set_preservation_state_http_503(requests_mock):
    """Test ``set_preservation_state`` function.

    ``set_preservation_state`` should throw a HTTPError when requests.patch()
    returns http 503 error.
    """
    requests_mock.get(METAX_REST_URL + '/datasets/foobar', json={})
    requests_mock.patch(METAX_REST_URL + '/datasets/foobar', status_code=503)
    with pytest.raises(requests.HTTPError) as error:
        METAX_CLIENT.set_preservation_state('foobar', '10', 'foo')
    assert error.value.response.status_code == 503


def test_get_dataset_template(requests_mock):
    """Test get_dataset_template function."""
    requests_mock.get(
        METAX_RPC_URL + '/datasets/get_minimal_dataset_template',
        json={'foo': 'bar'}
    )
    assert METAX_CLIENT.get_dataset_template() == {'foo': 'bar'}
