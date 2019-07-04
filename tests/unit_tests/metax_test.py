# coding=utf-8
# pylint: disable=no-member
"""Tests for ``metax_access.metax`` module"""
from __future__ import unicode_literals

import json

import httpretty
import lxml.etree
import pytest

from metax_access.metax import (
    Metax, MetaxConnectionError,
    DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
    DatasetNotFoundError,
    ContractNotFoundError,
    DataCatalogNotFoundError,
    DataciteGenerationError
)

METAX_URL = 'https://foobar'
METAX_REST_URL = METAX_URL+'/rest/v1'
METAX_USER = 'tpas'
METAX_PASSWORD = 'password'
METAX_CLIENT = Metax(METAX_URL, METAX_USER, METAX_PASSWORD, verify=False)


@pytest.mark.usefixtures('testmetax')
def test_get_datasets():
    """Test get_datasets function. Reads sample datasets JSON from testmetax
    and checks that returned dict contains the correct values.

    :returns: None
    """
    datasets = METAX_CLIENT.get_datasets('datasets')
    assert len(datasets["results"]) == 2


def test_get_datasets_http_503(requests_mock):
    """Test that get_datasets function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    requests_mock.get(METAX_REST_URL + '/datasets', status_code=503)
    with pytest.raises(MetaxConnectionError):
        METAX_CLIENT.get_datasets()


def test_get_datasets_http_404(requests_mock):
    """Test that get_datasets function throws a DatasetNotFoundError
    exception when requests.get() returns http 404 error
    """
    requests_mock.get(METAX_REST_URL + '/datasets', status_code=404)
    with pytest.raises(DatasetNotFoundError):
        METAX_CLIENT.get_datasets()


@pytest.mark.usefixtures('testmetax')
def test_get_dataset():
    """Test get_dataset function. Reads sample dataset JSON from testmetax and
    checks that returned dict contains the correct values.

    :returns: None
    """
    dataset = METAX_CLIENT.get_dataset("mets_test_dataset")
    assert (dataset["research_dataset"]["provenance"][0]['preservation_event']
            ['pref_label']['en'] == 'creation')


@pytest.mark.usefixtures('testmetax')
def test_get_contracts():
    """Test get_contracts function. Reads sample contracts JSON from testmetax
    and checks that returned dict contains the correct values.

    :returns: None
    """
    contracts = METAX_CLIENT.get_contracts()
    assert len(contracts['results']) == 2


def test_get_contracts_http_503(requests_mock):
    """Test that get_contracts function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    requests_mock.get(METAX_REST_URL+'/contracts', status_code=503)
    with pytest.raises(MetaxConnectionError):
        METAX_CLIENT.get_contracts()


def test_get_contracts_http_404(requests_mock):
    """Test that get_contracts function throws a ContractNotFoundError
    exception when requests.get() returns http 503 error
    """
    requests_mock.get(METAX_REST_URL+'/contracts', status_code=404)
    with pytest.raises(ContractNotFoundError):
        METAX_CLIENT.get_contracts()


@pytest.mark.usefixtures('testmetax')
def test_get_contract():
    """Test get_contract function. Reads sample contract JSON from testmetax
    and checks that returned dict contains the correct values.

    :returns: None
    """
    contract = METAX_CLIENT.get_contract(
        'urn:uuid:99ddffff-2f73-46b0-92d1-614409d83001'
    )
    assert contract['contract_json']['identifier'] \
        == 'urn:uuid:99ddffff-2f73-46b0-92d1-614409d83001'


def test_get_contract_http_503(requests_mock):
    """Test that get_contract function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    requests_mock.get(METAX_REST_URL+'/contracts/foo', status_code=503)
    with pytest.raises(MetaxConnectionError):
        METAX_CLIENT.get_contract('foo')


def test_get_contract_http_404(requests_mock):
    """Test that get_contract function throws a ContractNotFoundError
    exception when requests.get() returns http 404 error
    """
    requests_mock.get(METAX_REST_URL+'/contracts/foo', status_code=404)
    with pytest.raises(ContractNotFoundError):
        METAX_CLIENT.get_contract('foo')


@pytest.mark.usefixtures('testmetax')
def test_get_datacatalog():
    """Test get_datacatalog function. Reads sample dataset JSON from testmetax
    and checks that returned dict contains the correct values.

    :returns: None
    """
    contract = METAX_CLIENT.get_datacatalog(
        'urn:nbn:fi:att:2955e904-e3dd-4d7e-99f1-3fed446f96d2'
    )
    assert contract['catalog_json']['identifier'] \
        == 'urn:nbn:fi:att:2955e904-e3dd-4d7e-99f1-3fed446f96d2'


def test_get_catalog_http_503(requests_mock):
    """Test that get_datacatalog function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    requests_mock.get(METAX_REST_URL+'/datacatalogs/foo', status_code=503)
    with pytest.raises(MetaxConnectionError):
        METAX_CLIENT.get_datacatalog('foo')


def test_get_catalog_http_404(requests_mock):
    """Test that get_datacatalog function throws a DataCatalogNotFoundError
    exception when requests.get() returns http 404 error
    """
    requests_mock.get(METAX_REST_URL+'/datacatalogs/foo', status_code=404)
    with pytest.raises(DataCatalogNotFoundError):
        METAX_CLIENT.get_datacatalog('foo')


@pytest.mark.usefixtures('testmetax')
def test_get_dataset_filestypes():
    """Test get_xml function. Reads some test xml from testmetax checks that
    the function returns dictionary with correct items

    :returns: None
    """
    filetypes = METAX_CLIENT.get_dataset_filetypes('mets_test_dataset')
    assert isinstance(filetypes, dict)
    assert filetypes['total_count'] == 2
    assert filetypes['filetypes'][0]['encoding'] == 'UTF-8'
    assert filetypes['filetypes'][0]['file_format'] == 'text/plain' or\
        filetypes['filetypes'][0]['file_format'] == 'text/html'
    assert filetypes['filetypes'][0]['format_version'] == '' or\
        filetypes['filetypes'][0]['format_version'] == '4.01'


@pytest.mark.usefixtures('testmetax')
def test_patch_dataset():
    """Test patch_dataset function. Patch a dataset with few updated key/value
    pairs and check that correct HTTP request was sent to Metax.

    :returns: None
    """
    update = {
        'foo1': 'bar1',
        'research_dataset': {
            'foo2': 'bar2'
        }
    }
    METAX_CLIENT.patch_dataset('mets_test_dataset', update)
    assert httpretty.last_request().method == 'PATCH'
    request_body = json.loads(httpretty.last_request().body)

    assert isinstance(request_body['research_dataset']['provenance'], list)
    assert request_body['research_dataset']['foo2'] == 'bar2'
    assert request_body['foo1'] == 'bar1'


@pytest.mark.usefixtures('testmetax')
def test_get_xml():
    """Test get_xml function. Reads some test xml from testmetax checks that
    the function returns dictionary with correct items

    :returns: None
    """
    xml_dict = METAX_CLIENT.get_xml('files', "metax_xml_test")
    assert isinstance(xml_dict, dict)

    # The keys of returned dictionary should be xml namespace urls and
    # the values of returned dictionary should be lxml.etree.ElementTree
    # objects with the namespaces defined
    addml_url = "http://www.arkivverket.no/standarder/addml"
    assert xml_dict[addml_url].getroot().nsmap['addml'] == addml_url
    mets_url = "http://www.loc.gov/METS/"
    assert xml_dict[mets_url].getroot().nsmap['mets'] == mets_url


@pytest.mark.usefixtures('testmetax')
def test_set_xml():
    """Test set_xml functions. Reads XML file and posts it to Metax. The body
    and headers of HTTP request are checked.

    :returns: None
    """
    # Read sample MIX xml file
    mix = lxml.etree.parse('./tests/data/mix_sample.xml').getroot()

    # POST XML to Metax
    assert METAX_CLIENT.set_xml('set_xml_1', mix)

    # Check that posted message body is valid XML
    lxml.etree.fromstring(httpretty.last_request().body)

    # Check message headers
    assert httpretty.last_request().headers['content-type'] \
        == 'application/xml'

    # Check that message method is correct
    assert httpretty.last_request().method == 'POST'

    # Check that message query string has correct parameters
    assert httpretty.last_request().querystring['namespace'][0] \
        == 'http://www.loc.gov/mix/v20'


@pytest.mark.usefixtures('testmetax')
# pylint: disable=invalid-name
def test_set_xml_metadata_already_set():
    """Test set_xml functions. Reads XML file and posts it to Metax. The body
    and headers of HTTP request are checked.

    :returns: None
    """
    # Read sample MIX xml file
    mix = lxml.etree.parse('./tests/data/mix_sample.xml').getroot()

    # POST XML to Metax
    assert not METAX_CLIENT.set_xml('xml_metadata_already_set', mix)

    # Check that message method is correct
    assert httpretty.last_request().method == 'GET'
    assert httpretty.last_request().querystring['namespace'][0] ==\
        'http://www.loc.gov/mix/v20'


@pytest.mark.usefixtures('testmetax')
def test_get_datacite():
    """Test get_datacite function. Read one field from returned etree object
    and check its correctness.
    :returns: None
    """
    xml = METAX_CLIENT.get_datacite("datacite_test_1")
    # make sure Metax is called for preservation_identifier generation
    assert httpretty.HTTPretty.latest_requests[-2].path == \
        ("/rpc/datasets/set_preservation_identifier?identifier="
         "datacite_test_1")
    # Read field "creatorName" from xml file
    ns_string = 'http://datacite.org/schema/kernel-4'
    xpath_str = '/ns:resource/ns:creators/ns:creator/ns:creatorName'
    creatorname = xml.xpath(xpath_str, namespaces={'ns': ns_string})[0].text
    # Check that "creatorName" is same as in the original XML file
    assert creatorname == "Puupää, Pekka"


def test_get_datacite_fails(requests_mock):
    """Test get_datacite function when Metax returns 400

    :returns: None
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
            "detail": "Dataset does not have a publisher (field: "
                      "research_dataset.publisher), which is a required value "
                      "for datacite format",
            "error_identifier": "2019-03-28T12:39:01-f0a7e3ae"
        }
    requests_mock.get(
        METAX_REST_URL + '/datasets/foo?dataset_format=datacite',
        json=response,
        status_code=400
    )

    # Mock set_preservation_identifier API request
    requests_mock.post(
        METAX_URL + '/rpc/datasets/set_preservation_identifier?identifier=foo',
        text='foobar',
    )

    with pytest.raises(DataciteGenerationError):
        METAX_CLIENT.get_datacite("foo")


@pytest.mark.usefixtures('testmetax')
def test_set_preservation_state():
    """Test set_preservation_state function. Metadata in Metax is modified by
    sending HTTP PATCH request with modified metadata in JSON format. This test
    checks that correct HTTP request is sent to Metax. The effect of the
    request is not tested.

    :returns: None
    """
    METAX_CLIENT.set_preservation_state(
        "mets_test_dataset",
        state=DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
        system_description='Accepted to preservation'
    )

    # Check the body of last HTTP request
    request_body = json.loads(httpretty.last_request().body)
    assert request_body["preservation_state"] ==\
        DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE
    assert request_body["preservation_description"] \
        == "Accepted to preservation"

    # Check the method of last HTTP request
    assert httpretty.last_request().method == 'PATCH'


@pytest.mark.usefixtures('testmetax')
def test_patch_file():
    """Test patch_file function. Metadata in Metax is modified by sending HTTP
    PATCH request with modified metadata in JSON format. This test checks that
    correct HTTP request is sent to Metax. The effect of the request is not
    tested.

    :returns: None
    """
    sample_data = {
        "file_characteristics": {
            "file_format": "text/plain",
            "format_version": "1.0",
            "encoding": "UTF-8"
        }
    }
    METAX_CLIENT.patch_file('pid:urn:set_file_characteristics_1', sample_data)

    # Check the body of last HTTP request
    request_body = json.loads(httpretty.last_request().body)
    assert request_body == sample_data

    # Check the method of last HTTP request
    assert httpretty.last_request().method == 'PATCH'


def test_get_dataset_http_503(requests_mock):
    """Test that get_dataset function throws a MetaxConnectionError exception
    when requests.get() returns http 503 error
    """
    requests_mock.get(METAX_REST_URL + '/datasets/foo', status_code=503)
    with pytest.raises(MetaxConnectionError):
        METAX_CLIENT.get_dataset('foo')


def test_get_xml_http_503(requests_mock):
    """Test that get_xml function throws a MetaxConnectionError exception
    when requests.get() returns http 503 error
    """
    requests_mock.get(METAX_REST_URL + '/files/foo/xml', status_code=503)
    with pytest.raises(MetaxConnectionError):
        METAX_CLIENT.get_xml('files', 'foo')


# pylint: disable=invalid-name
def test_set_preservation_state_http_503(requests_mock):
    """Test that set_preservation_state function throws a MetaxConnectionError
    exception when requests.patch() returns http 503 error
    """
    requests_mock.get(METAX_REST_URL + '/datasets/foobar', json={})
    requests_mock.patch(METAX_REST_URL + '/datasets/foobar', status_code=503)
    with pytest.raises(MetaxConnectionError):
        METAX_CLIENT.set_preservation_state('foobar', '10', 'foo', 'bar')


# pylint: disable=invalid-name
def test_get_elasticsearchdata_http_503(requests_mock):
    """Test that get_elasticsearchdata function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """

    requests_mock.get(
        METAX_URL + "/es/reference_data/use_category/_search?pretty&size=100",
        status_code=503
    )
    with pytest.raises(MetaxConnectionError):
        METAX_CLIENT.get_elasticsearchdata()


def test_get_datacite_http_503(requests_mock):
    """Test that get_datacite function throws a MetaxConnectionError exception
    when requests.get() returns http 503 error
    """
    requests_mock.get(METAX_REST_URL + '/datasets/foo', json={'identifier': 'bar'})
    requests_mock.post(
        METAX_URL + '/rpc/datasets/set_preservation_identifier?identifier=bar',
        status_code=503
    )
    with pytest.raises(MetaxConnectionError):
        METAX_CLIENT.get_datacite("foo")


def test_get_dataset_files_http_503(requests_mock):
    """Test that get_dataset_files function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    requests_mock.get(METAX_REST_URL+'/datasets/foo/files', status_code=503)
    with pytest.raises(MetaxConnectionError):
        METAX_CLIENT.get_dataset_files("foo")


@httpretty.activate
def test_delete_file():
    """Test that ``delete_file`` function sends HTTP DELETE request to correct
    url
    """
    httpretty.register_uri(httpretty.DELETE,
                           METAX_URL + '/rest/v1/files/file1')

    METAX_CLIENT.delete_file('file1')

    assert httpretty.last_request().method == httpretty.DELETE
    assert httpretty.last_request().headers.get('host') \
        == 'foobar'
    assert httpretty.last_request().path == '/rest/v1/files/file1'


@httpretty.activate
def test_delete_dataset():
    """Test that ``delete_dataset`` function sends HTTP DELETE request to
    correct url
    """
    httpretty.register_uri(httpretty.DELETE,
                           METAX_URL + '/rest/v1/datasets/dataset1')

    METAX_CLIENT.delete_dataset('dataset1')

    assert httpretty.last_request().method == httpretty.DELETE
    assert httpretty.last_request().headers.get('host') \
        == 'foobar'
    assert httpretty.last_request().path == '/rest/v1/datasets/dataset1'


def test_post_file(requests_mock):
    """Test that ``post_file`` function sends HTTP POST request to correct
    url
    """
    requests_mock.post(METAX_URL + '/rest/v1/files/', json={'identifier': '1'})

    METAX_CLIENT.post_file({'identifier': '1'})

    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.hostname == 'foobar'
    assert requests_mock.last_request.path == '/rest/v1/files/'


def test_post_dataset(requests_mock):
    """Test that ``post_dataset`` function sends HTTP POST request to correct
    url
    """
    requests_mock.post(
        METAX_URL + '/rest/v1/datasets/', json={'identifier': '1'}
    )

    METAX_CLIENT.post_dataset({'identifier': '1'})

    assert requests_mock.last_request.method == "POST"
    assert requests_mock.last_request.hostname == 'foobar'
    assert requests_mock.last_request.path == '/rest/v1/datasets/'


def test_set_preservation_id(requests_mock):
    """Tests that ``set_preservation_id`` function sends correct http request
    to Metax. The same request should be sent when `id` or `identifier`
    attribute of dataset is used as parameter.
    """

    # Mock dataset with id="1234" and identifier="identifier1234"
    requests_mock.get(
        METAX_URL + '/rest/v1/datasets/1234',
        json={"identifier": "identifier1234"}
    )
    requests_mock.get(
        METAX_URL + '/rest/v1/datasets/identifier1234',
        json={"identifier": "identifier1234"}
    )
    requests_mock.post(
        METAX_URL + "/rpc/datasets/set_preservation_identifier?identifier="
        "identifier1234"
    )

    # Call function with id attribute as parameter
    METAX_CLIENT.set_preservation_id('1234')
    assert requests_mock.call_count == 2
    assert requests_mock.last_request.url \
        == (METAX_URL + "/rpc/datasets/set_preservation_identifier?identifier="
            "identifier1234")

    # Call function with identifier attricute as parameter
    METAX_CLIENT.set_preservation_id('identifier1234')
    assert requests_mock.call_count == 4
    assert requests_mock.last_request.url \
        == (METAX_URL + "/rpc/datasets/set_preservation_identifier?identifier="
            "identifier1234")


def test_get_dataset_file_mapping(requests_mock):
    """Tests that ``get_dataset_file_mapping`` function returns the correct
    PAS id -> IDA id mapping.
    """
    requests_mock.get(
        METAX_URL + '/rest/v1/datasets/pid:urn:pas',
        json={
            "identifier": "pid:urn:pas",
            "preservation_dataset_origin_version": {
                "identifier": "pid:urn:ida"
            }
        }
    )
    requests_mock.get(
        METAX_URL + '/rest/v1/datasets/pid:urn:pas/files',
        json=[
            {"identifier": "pid:urn:pas_file_1", "file_path": "/file_1"},
            {"identifier": "pid:urn:pas_file_2", "file_path": "/file_2"}
        ]
    )
    requests_mock.get(
        METAX_URL + '/rest/v1/datasets/pid:urn:ida',
        json={"identifier": "pid:urn:ida"}
    )
    requests_mock.get(
        METAX_URL + '/rest/v1/datasets/pid:urn:ida/files',
        json=[
            {"identifier": "pid:urn:ida_file_1", "file_path": "/file_1"},
            {"identifier": "pid:urn:ida_file_2", "file_path": "/file_2"}
        ]
    )

    assert METAX_CLIENT.get_dataset_file_mapping("pid:urn:pas") == {
        "pid:urn:pas_file_1": "pid:urn:ida_file_1",
        "pid:urn:pas_file_2": "pid:urn:ida_file_2"
    }
