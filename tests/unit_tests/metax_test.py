# coding=utf-8
# pylint: disable=no-member
"""Tests for ``metax_access.metax`` module"""
import json
from functools import wraps
import httpretty
import lxml.etree
import mock
import pytest
import metax_access.metax as metax
from metax_access.metax import Metax, MetaxConnectionError


METAX_URL = 'https://metax-test.csc.fi'
METAX_USER = 'tpas'
METAX_PASSWORD = 'password'


def metax_access_instance_required(f):
    @wraps(f)
    def dec_func(*args, **kwargs):
        metax_access = Metax(METAX_URL, METAX_USER, METAX_PASSWORD)
        kwargs["metax_access"] = metax_access
        return f(*args, **kwargs)
    return dec_func


@pytest.mark.usefixtures('testmetax')
@metax_access_instance_required
def test_get_dataset(metax_access):
    """Test get_dataset function. Reads sample dataset JSON from testmetax and
    checks that returned dict contains the correct values.

    :returns: None
    """
    dataset = metax_access.get_dataset("mets_test_dataset")
    print dataset
    print type(dataset)
    assert dataset["research_dataset"]["provenance"][0]\
        ['preservation_event']['pref_label']['en'] == 'creation'


@pytest.mark.usefixtures('testmetax')
@metax_access_instance_required
def test_get_xml(metax_access):
    """Test get_xml function. Reads some test xml from testmetax checks that
    the function returns dictionary with correct items

    :returns: None
    """
    xml_dict = metax_access.get_xml('files', "metax_xml_test")
    assert isinstance(xml_dict, dict)

    # The keys of returned dictionary should be xml namespace urls and
    # the values of returned dictionary should be lxml.etree.ElementTree
    # objects with the namespaces defined
    addml_url = "http://www.arkivverket.no/standarder/addml"
    assert xml_dict[addml_url].getroot().nsmap['addml'] == addml_url
    mets_url = "http://www.loc.gov/METS/"
    assert xml_dict[mets_url].getroot().nsmap['mets'] == mets_url


@pytest.mark.usefixtures('testmetax')
@metax_access_instance_required
def test_set_xml(metax_access):
    """Test set_xml functions. Reads XML file and posts it to Metax. The body
    and headers of HTTP request are checked.

    :returns: None
    """
    # Read sample MIX xml file
    mix = lxml.etree.parse('./tests/data/mix_sample.xml').getroot()

    # POST XML to Metax
    metax_access.set_xml('set_xml_1', mix)

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
@metax_access_instance_required
def test_get_datacite(metax_access):
    """Test get_datacite function. Read one field from returned etree object
    and check its correctness.
    :returns: None
    """
    xml = metax_access.get_datacite("datacite_test_1")

    # Read field "creatorName" from xml file
    ns_string = 'http://datacite.org/schema/kernel-4'
    xpath_str = '/ns:resource/ns:creators/ns:creator/ns:creatorName'
    creatorname = xml.xpath(xpath_str, namespaces={'ns': ns_string})[0].text
    # Check that "creatorName" is same as in the original XML file
    assert creatorname == u"Puupää, Pekka"


@pytest.mark.usefixtures('testmetax')
@metax_access_instance_required
def test_set_preservation_state(metax_access):
    """Test set_preservation_state function. Metadata in Metax is modified by
    sending HTTP PATCH request with modified metadata in JSON format. This test
    checks that correct HTTP request is sent to Metax. The effect of the
    request is not tested.

    :returns: None
    """
    metax_access.set_preservation_state("mets_test_dataset",
                                  metax.DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE,
                                  'Accepted to preservation')

    # Check the body of last HTTP request
    request_body = json.loads(httpretty.last_request().body)
    assert request_body["preservation_state"] ==\
        metax.DS_STATE_REJECTED_IN_DIGITAL_PRESERVATION_SERVICE
    assert request_body["preservation_description"] \
        == "Accepted to preservation"

    # Check the method of last HTTP request
    assert httpretty.last_request().method == 'PATCH'


@pytest.mark.usefixtures('testmetax')
@metax_access_instance_required
def test_set_file_characteristics(metax_access):
    """Test set_file_characteristics function. Metadata in Metax is modified by
    sending HTTP PATCH request with modified metadata in JSON format. This test
    checks that correct HTTP request is sent to Metax. The effect of the
    request is not tested.

    :returns: None
    """
    sample_data = {"file_format": "text/plain",
                   "format_version": "1.0",
                   "encoding": "UTF-8"}
    metax_access.set_file_characteristics('pid:urn:set_file_characteristics_1',
                                          sample_data)

    # Check the body of last HTTP request
    request_body = json.loads(httpretty.last_request().body)
    assert request_body["file_characteristics"] == sample_data

    # Check the method of last HTTP request
    assert httpretty.last_request().method == 'PATCH'


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    return MockResponse(503)


@metax_access_instance_required
def test_get_data_returns_correct_error_when_http_503_error(metax_access):
    """Test that get_dataset function throws a MetaxConnectionError exception
    when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.requests.get', side_effect=mocked_requests_get):
        # Run task like it would be run from command line
        exception_thrown = False
        try:
            metax_access.get_dataset('who_cares')
        except MetaxConnectionError:
            exception_thrown = True
        assert exception_thrown is True


@metax_access_instance_required
def test_get_xml_returns_correct_error_when_http_503_error(metax_access):
    """Test that get_xml function throws a MetaxConnectionError exception
    when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.requests.get',
                    side_effect=mocked_requests_get):
        exception_thrown = False
        try:
            metax_access.get_xml('who', 'cares')
        except MetaxConnectionError:
            exception_thrown = True
        assert exception_thrown is True


@metax_access_instance_required
def test_set_preservation_state_returns_correct_error_when_http_503_error(metax_access):
    """
    Test that set_preservation_state function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.requests.patch',
                    side_effect=mocked_requests_get):
        exception_thrown = False
        try:
            metax_access.set_preservation_state('who',
                                                metax.DS_STATE_INITIALIZED,
                                                'cares')
        except MetaxConnectionError:
            exception_thrown = True
        assert exception_thrown is True


@metax_access_instance_required
def test_get_elasticsearchdata_returns_correct_error_when_http_503_error(metax_access):
    """
    Test that get_elasticsearchdata function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.requests.get',
                    side_effect=mocked_requests_get):
        # Run task like it would be run from command line
        exception_thrown = False
        try:
            metax_access.get_elasticsearchdata()
        except MetaxConnectionError:
            exception_thrown = True
        assert exception_thrown is True


@metax_access_instance_required
def test_get_datacite_returns_correct_error_when_http_503_error(metax_access):
    """Test that get_datacite function throws a MetaxConnectionError exception
    when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.requests.get',
                    side_effect=mocked_requests_get):
        # Run task like it would be run from command line
        exception_thrown = False
        try:
            metax_access.get_datacite("x")
        except MetaxConnectionError:
            exception_thrown = True
        assert exception_thrown is True


@metax_access_instance_required
def test_get_dataset_files_returns_correct_error_when_http_503_error(metax_access):
    """
    Test that get_dataset_files function throws a MetaxConnectionError
    exception when requests.get() returns http 503 error
    """
    with mock.patch('metax_access.metax.requests.get',
                    side_effect=mocked_requests_get):
        # Run task like it would be run from command line
        exception_thrown = False
        try:
            metax_access.get_dataset_files("x")
        except MetaxConnectionError:
            exception_thrown = True
        assert exception_thrown is True


# TODO: test for retrieving other entities: contracts, files...
