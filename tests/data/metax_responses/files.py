"""Sample Metax file data."""

import copy


def _construct_file(**kwargs):
    file = copy.deepcopy(BASE)
    file.update(kwargs)
    return file


BASE = {
    "id": "test_id",
    "storage_identifier": "pas_storage_id",
    "pathname": "/filename.txt",
    "filename": "filename.txt",
    "size": 14798,
    "storage_service": "test_pas",
    "csc_project": "user_test_project",
    "checksum": "sha256:test_checksum",
    "frozen": "frozen_date",
    "modified": "modified_date",
    "removed": None,
    "published": "published_date",
    "user": "test_user",
    "characteristics": None,
    "characteristics_extension": None,
    "pas_process_running": False,
    "pas_compatible_file": None,
    "non_pas_compatible_file": None,
}


FULL = _construct_file(
    dataset_metadata={
        "title": "filename.txt",
        "description": "test_description",
        "file_type": {
            "id": "file_type_id",
            "url": "http://url_to_file_type.test",
            "in_scheme": "http://url_to_schema",
            "pref_label": {"en": "File type", "fi": "Tiedoston tyyppi"},
        },
        "use_category": {
            "id": "use_category_id",
            "url": "http://use_category_url.test",
            "in_scheme": "http://use_category_schema.test",
            "pref_label": {"en": "Use Category", "fi": "Käyttökategoria"},
        },
    },
    characteristics={
        "file_format_version": {
            "id": "test_file_format_version_id",
            "url": "http://file_format_version_url.test",
            "in_scheme": "http://file_format_version_schema.test",
            "pref_label": {
                "en": "test/format",
                "fi": "test/format",
                "und": "test/format",
            },
            "deprecated": None,
            "file_format": "test/format",
            "format_version": "",
        },
        "encoding": "UTF-TEST",
        "csv_has_header": None,
        "csv_quoting_char": None,
        "csv_delimiter": None,
        "csv_record_separator": None,
    },
    characteristics_extension="test extension value",
)

MINIMAL_CHARACTERISTICS_FIELD = _construct_file(
    characteristics={
        "file_format_version": None,
        "encoding": "UTF-TEST",
        "csv_has_header": None,
        "csv_quoting_char": None,
        "csv_delimiter": None,
        "csv_record_separator": None,
    }
)
