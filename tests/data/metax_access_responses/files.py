"""Sample metax_access file response data."""

import copy


def _construct_file_response(**kwargs):
    response = copy.deepcopy(BASE)
    response.update(kwargs)
    return response


BASE = {
    "id": "test_id",
    "storage_identifier": "pas_storage_id",
    "pathname": "/filename.txt",
    "filename": "filename.txt",
    "size": 14798,
    "checksum": "sha256:test_checksum",
    "csc_project": "user_test_project",
    "storage_service": "test_pas",
    "dataset_metadata": {"use_category": None},
    "characteristics": {
        "file_format_version": {
            "file_format": None,
            "format_version": None,
        },
        "encoding": None,
        "csv_delimiter": None,
        "csv_record_separator": None,
        "csv_quoting_char": None,
        "csv_has_header": None,
    },
    "characteristics_extension": None,
    "pas_compatible_file": None,
    "non_pas_compatible_file": None,
}


FULL = _construct_file_response(
    dataset_metadata={
        "use_category": {
            "pref_label": {"en": "Use Category", "fi": "Käyttökategoria"},
            "url": "http://use_category_url.test",
        }
    },
    characteristics={
        "file_format_version": {
            "file_format": "test/format",
            "format_version": "",
        },
        "encoding": "UTF-TEST",
        "csv_delimiter": None,
        "csv_record_separator": None,
        "csv_quoting_char": None,
        "csv_has_header": None,
    },
    characteristics_extension="test extension value",
)


MINIMAL_CHARACTERISTICS_FIELD = _construct_file_response(
    characteristics={
        "file_format_version": {
            "file_format": None,
            "format_version": None,
        },
        "encoding": "UTF-TEST",
        "csv_delimiter": None,
        "csv_record_separator": None,
        "csv_quoting_char": None,
        "csv_has_header": None,
    }
)
