# coding=utf-8
# pylint: disable=no-member
"""Tests for ``metax_access.metax`` module"""
import json
import httpretty
import lxml.etree
try:
    import mock
except ImportError:
    from unittest import mock
import pytest
from metax_access.metax import (
    Metax, MetaxConnectionError,
    DS_STATE_INITIALIZED,
    DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
    DatasetNotFoundError,
    ContractNotFoundError,
    DataCatalogNotFoundError
)

METAX_URL = 'https://metax-test.csc.fi'
METAX_USER = 'tpas'
METAX_PASSWORD = 'password'
METAX_CLIENT = Metax(METAX_URL, METAX_USER, METAX_PASSWORD)


@pytest.mark.usefixtures('testmetax')
def test_get_datasets():
    """Test get_dataset function. Reads sample dataset JSON from testmetax and
    checks that returned dict contains the correct values.

    :returns: None
    """
    datasets = METAX_CLIENT.get_datasets('datasets')
    assert len(datasets["results"]) == 2


@pytest.mark.usefixtures('testmetax')
def test_get_datasets_http_503_error():
    """Test that get_datasets function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_503_response):
        with pytest.raises(MetaxConnectionError):
            METAX_CLIENT.get_datasets()


@pytest.mark.usefixtures('testmetax')
def test_get_datasets_http_404_error():
    """Test that get_elasticsearchdata function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_404_response):
        with pytest.raises(DatasetNotFoundError):
            METAX_CLIENT.get_datasets()


@pytest.mark.usefixtures('testmetax')
def test_get_dataset():
    """Test get_dataset function. Reads sample dataset JSON from testmetax and
    checks that returned dict contains the correct values.

    :returns: None
    """
    dataset = METAX_CLIENT.get_dataset("mets_test_dataset")
    print dataset
    print type(dataset)
    assert dataset["research_dataset"]["provenance"][0]\
        ['preservation_event']['pref_label']['en'] == 'creation'


@pytest.mark.usefixtures('testmetax')
def test_get_contracts():
    """Test get_dataset function. Reads sample dataset JSON from testmetax and
    checks that returned dict contains the correct values.

    :returns: None
    """
    contracts = METAX_CLIENT.get_contracts()
    assert len(contracts['results']) == 2


@pytest.mark.usefixtures('testmetax')
def test_get_contracts_503_error():
    """Test that get_contracts function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_503_response):
        with pytest.raises(MetaxConnectionError):
            METAX_CLIENT.get_contracts()


@pytest.mark.usefixtures('testmetax')
def test_get_contracts_404_error():
    """Test that get_contracts function throws a ContractNotFoundError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_404_response):
        with pytest.raises(ContractNotFoundError):
            METAX_CLIENT.get_contracts()


@pytest.mark.usefixtures('testmetax')
def test_get_contract():
    """Test get_dataset function. Reads sample dataset JSON from testmetax and
    checks that returned dict contains the correct values.

    :returns: None
    """
    contract = METAX_CLIENT.get_contract(
        'urn:uuid:99ddffff-2f73-46b0-92d1-614409d83001'
    )
    assert contract['contract_json']['identifier'] \
        == 'urn:uuid:99ddffff-2f73-46b0-92d1-614409d83001'


@pytest.mark.usefixtures('testmetax')
def test_get_contract_503_error():
    """Test that get_contracts function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_503_response):
        with pytest.raises(MetaxConnectionError):
            METAX_CLIENT.get_contract(
                'urn:uuid:99ddffff-2f73-46b0-92d1-614409d83001'
            )


@pytest.mark.usefixtures('testmetax')
def test_get_contract_404_error():
    """Test that get_contracts function throws a ContractNotFoundError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_404_response):
        with pytest.raises(ContractNotFoundError):
            METAX_CLIENT.get_contract(
                'urn:uuid:99ddffff-2f73-46b0-92d1-614409d83001'
            )


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


@pytest.mark.usefixtures('testmetax')
def test_get_catalog_503_error():
    """Test that get_datacatalog function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_503_response):
        with pytest.raises(MetaxConnectionError):
            METAX_CLIENT.get_datacatalog(
                'urn:nbn:fi:att:2955e904-e3dd-4d7e-99f1-3fed446f96d2'
            )


@pytest.mark.usefixtures('testmetax')
def test_get_catalog_404_error():
    """Test that get_datacatalog function throws a ContractNotFoundError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_404_response):
        with pytest.raises(DataCatalogNotFoundError):
            METAX_CLIENT.get_datacatalog(
                'urn:nbn:fi:att:2955e904-e3dd-4d7e-99f1-3fed446f96d2'
            )


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
def test_set_contract_for_dataset():
    """Test get_xml function. Reads some test xml from testmetax checks that
    the function returns dictionary with correct items

    :returns: None
    """

    METAX_CLIENT.set_contract_for_dataset('dataset_id',
                                          'contract_id',
                                          'contract_identifier')
    assert httpretty.last_request().method == 'PATCH'
    request_body = json.loads(httpretty.last_request().body)
    assert request_body['contract']['id'] == 'contract_id'
    assert request_body['contract']['identifier'] == 'contract_identifier'


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

    # Read field "creatorName" from xml file
    ns_string = 'http://datacite.org/schema/kernel-4'
    xpath_str = '/ns:resource/ns:creators/ns:creator/ns:creatorName'
    creatorname = xml.xpath(xpath_str, namespaces={'ns': ns_string})[0].text
    # Check that "creatorName" is same as in the original XML file
    assert creatorname == u"Puupää, Pekka"


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
def test_set_file_characteristics():
    """Test set_file_characteristics function. Metadata in Metax is modified by
    sending HTTP PATCH request with modified metadata in JSON format. This test
    checks that correct HTTP request is sent to Metax. The effect of the
    request is not tested.

    :returns: None
    """
    sample_data = {"file_format": "text/plain",
                   "format_version": "1.0",
                   "encoding": "UTF-8"}
    METAX_CLIENT.set_file_characteristics('pid:urn:set_file_characteristics_1',
                                          sample_data)

    # Check the body of last HTTP request
    request_body = json.loads(httpretty.last_request().body)
    assert request_body["file_characteristics"] == sample_data

    # Check the method of last HTTP request
    assert httpretty.last_request().method == 'PATCH'


def mocked_503_response(*args, **kwargs):
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    return MockResponse(503)


def mocked_404_response(*args, **kwargs):
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    return MockResponse(404)


def test_get_dataset_returns_correct_error_when_http_503_error():
    """Test that get_dataset function throws a MetaxConnectionError exception
    when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get', side_effect=mocked_503_response):
        with pytest.raises(MetaxConnectionError):
            METAX_CLIENT.get_dataset('who_cares')


def test_get_xml_returns_correct_error_when_http_503_error():
    """Test that get_xml function throws a MetaxConnectionError exception
    when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_503_response):
        with pytest.raises(MetaxConnectionError):
            METAX_CLIENT.get_xml('who', 'cares')


def test_set_preservation_state_returns_correct_error_when_http_503_error():
    """Test that set_preservation_state function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.patch',
                    side_effect=mocked_503_response):
        with pytest.raises(MetaxConnectionError):
            METAX_CLIENT.set_preservation_state('foobar')


def test_get_elasticsearchdata_returns_correct_error_when_http_503_error():
    """Test that get_elasticsearchdata function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_503_response):
        with pytest.raises(MetaxConnectionError):
            METAX_CLIENT.get_elasticsearchdata()


def test_get_datacite_returns_correct_error_when_http_503_error():
    """Test that get_datacite function throws a MetaxConnectionError exception
    when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_503_response):
        with pytest.raises(MetaxConnectionError):
            METAX_CLIENT.get_datacite("x")


def test_get_dataset_files_returns_correct_error_when_http_503_error():
    """Test that get_dataset_files function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.get',
                    side_effect=mocked_503_response):
        with pytest.raises(MetaxConnectionError):
            METAX_CLIENT.get_dataset_files("x")


@httpretty.activate
def test_delete_file():
    """Test that ``delete_file`` function sends HTTP DELETE request to correct
    url
    """
    httpretty.register_uri(httpretty.DELETE, METAX_URL + '/rest/v1/files/file1')

    METAX_CLIENT.delete_file('file1')

    assert httpretty.last_request().method == httpretty.DELETE
    assert httpretty.last_request().headers.get('host') \
        == 'metax-test.csc.fi'
    assert httpretty.last_request().path == '/rest/v1/files/file1'


@httpretty.activate
def test_delete_dataset():
    """Test that ``delete_dataset`` function sends HTTP DELETE request to
    correct url
    """
    httpretty.register_uri(httpretty.DELETE, METAX_URL + '/rest/v1/datasets/dataset1')

    METAX_CLIENT.delete_dataset('dataset1')

    assert httpretty.last_request().method == httpretty.DELETE
    assert httpretty.last_request().headers.get('host') \
        == 'metax-test.csc.fi'
    assert httpretty.last_request().path == '/rest/v1/datasets/dataset1'


@httpretty.activate
def test_post_file():
    """Test that ``post_file`` function sends HTTP POST request to correct
    url
    """
    httpretty.register_uri(httpretty.POST, METAX_URL + '/rest/v1/files/')

    METAX_CLIENT.post_file({'identifier': '1'})

    assert httpretty.last_request().method == httpretty.POST
    assert httpretty.last_request().headers.get('host') \
        == 'metax-test.csc.fi'
    assert httpretty.last_request().path == '/rest/v1/files/'


@httpretty.activate
def test_post_dataset():
    """Test that ``post_dataset`` function sends HTTP POST request to
    correct url
    """
    httpretty.register_uri(httpretty.POST, METAX_URL + '/rest/v1/datasets/')

    METAX_CLIENT.post_dataset({'identifier': '1'})

    assert httpretty.last_request().method == httpretty.POST
    assert httpretty.last_request().headers.get('host') \
        == 'metax-test.csc.fi'
    assert httpretty.last_request().path == '/rest/v1/datasets/'
