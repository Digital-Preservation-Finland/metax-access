# coding=utf-8
# pylint: disable=no-member
"""Tests for ``metax_access.metax`` module."""
from __future__ import unicode_literals

import json

import lxml.etree
import pytest
import requests

from metax_access.metax import (
    Metax,
    DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
    DatasetNotAvailableError,
    ContractNotAvailableError,
    DataCatalogNotAvailableError,
    DataciteGenerationError
)

METAX_URL = 'https://foobar'
METAX_REST_URL = METAX_URL+'/rest/v1'
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
    requests_mock.get(
        METAX_REST_URL + "/datasets",
        json={"results": [{"identifier": "foo"}, {"identifier": "bar"}]}
    )
    datasets = METAX_CLIENT.get_datasets('datasets')
    assert len(datasets["results"]) == 2

    # No errors should be logged
    logged_errors = [r for r in caplog.records if r.levelname == 'ERROR']
    assert not logged_errors


def test_get_dataset(requests_mock):
    """Test ``get_dataset`` function.

    Mocks Metax to return simple JSON as HTTP
    response and checks that the returned dict contains the correct values.

    :returns: None
    """
    requests_mock.get(METAX_REST_URL + "/datasets/test_id",
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

    request_body = json.loads(requests_mock.last_request.body)
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

    Read one field from returned etree object and check its correctness.

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

    xml = METAX_CLIENT.get_datacite("test_id")

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
        state=DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
        system_description='Accepted to preservation'
    )

    # Check the body of last HTTP request
    request_body = json.loads(requests_mock.last_request.body)
    assert request_body["preservation_state"] ==\
        DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE
    assert request_body["preservation_description"] \
        == "Accepted to preservation"

    # Check the method of last HTTP request
    assert requests_mock.last_request.method == 'PATCH'


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
    request_body = json.loads(requests_mock.last_request.body)
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
    assert requests_mock.last_request.path == '/rest/v1/files/file1'


def test_delete_dataset(requests_mock):
    """Test ``delete_dataset`` function.

    Test that HTTP DELETE request is sent to correct url.
    """
    requests_mock.delete(METAX_REST_URL + "/datasets/dataset1")

    METAX_CLIENT.delete_dataset('dataset1')

    assert requests_mock.last_request.method == "DELETE"
    assert requests_mock.last_request.hostname == 'foobar'
    assert requests_mock.last_request.path == '/rest/v1/datasets/dataset1'


def test_post_file(requests_mock):
    """Test ``post_file`` function.

    Test that HTTP POST request is sent to correct url.
    """
    requests_mock.post(METAX_URL + '/rest/v1/files/', json={'identifier': '1'})

    METAX_CLIENT.post_file({'identifier': '1'})

    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.hostname == 'foobar'
    assert requests_mock.last_request.path == '/rest/v1/files/'


def test_post_dataset(requests_mock):
    """Test ``post_dataset`` function.

    Test that HTTP POST request is sent to correct url.
    """
    requests_mock.post(
        METAX_URL + '/rest/v1/datasets/', json={'identifier': '1'}
    )

    METAX_CLIENT.post_dataset({'identifier': '1'})

    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.hostname == 'foobar'
    assert requests_mock.last_request.path == '/rest/v1/datasets/'


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
        ('/datasets?state=0,10,20,30,40,50,60,70,75,80,90,100,110,120,130,140'
         '&limit=1000000&offset=0', METAX_CLIENT.get_datasets, []),
        ('/contracts?limit=1000000&offset=0', METAX_CLIENT.get_contracts, []),
        ('/contracts/foo', METAX_CLIENT.get_contract, ['foo']),
        ('/datacatalogs/foo', METAX_CLIENT.get_datacatalog, ['foo']),
        ('/datasets/foo', METAX_CLIENT.get_dataset, ['foo']),
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
        'HTTP request to {} failed. Response from server was: Metax failed '
        'to process request'.format(METAX_REST_URL + url)
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
        METAX_CLIENT.set_preservation_state('foobar', '10', 'foo', 'bar')
    assert error.value.response.status_code == 503
