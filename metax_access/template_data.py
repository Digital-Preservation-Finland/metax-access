"""Template Metax data for testing purposes."""

CONTRACT = {
    "id": "urn:uuid:abcd1234-abcd-1234-5678-abcd1234abcd",
    "title": {"und": "Test Contract Title"},
    "quota": 111205,
    "organization": {
        "name": "Test organization",
        "organization_identifier": "test_org_identifier",
    },
    "contact": [
        {
            "name": "Contact Name",
            "email": "contact.email@csc.fi",
            "phone": "+358501231234",
        }
    ],
    "related_service": [
        {"identifier": "local:service:id", "name": "Name of Service"}
    ],
    "description": {"und": "Description of unknown length"},
    "created": "test_created_date",
    "validity": {"start_date": "2014-01-17", "end_date": None},
}

DATASET = {
    "id": "test_dataset_id",
    "access_rights": {
        "available": None,
        "description": None,
        "license": [
            {
                "custom_url": None,
                "description": None,
                "title": {"en": "Title here"},
                "pref_label": {"en": "Title here"},
                "url": "http://urn.fi/urn:nbn:fi:csc-3388475675",
            }
        ],
    },
    "actors": [],
    "bibliographic_citation": None,
    "cumulative_state": 0,
    "data_catalog": "urn:nbn:fi:att:data-catalog-pas",
    "description": None,
    "field_of_science": [],
    "fileset": {
        "total_files_size": 0,
        "csc_project": None,
        "total_files_count": 0,
    },
    "generate_pid_on_publish": None,
    "infrastructure": [],
    "issued": None,
    "keyword": [],
    "language": [],
    "metadata_owner": {
        "id": "test_metadata_owner_id",
        "user": "service_tpas",
        "organization": "service_tpas",
    },
    "other_identifiers": [],
    "persistent_identifier": None,
    "preservation": {
        "state": -1,
        "description": None,
        "reason_description": None,
        "dataset_version": {
            "id": None,
            "persistent_identifier": None,
            "preservation_state": None,
        },
        "contract": "test_contract_id",
        "preservation_identifier": None,
    },
    "projects": [],
    "provenance": [],
    "relation": [],
    "remote_resources": [],
    "spatial": [],
    "state": "draft",
    "temporal": [],
    "theme": [],
    "title": {"en": "testing"},
    "created": "test_created_date",
    "cumulation_started": None,
    "cumulation_ended": None,
    "deprecated": None,
    "removed": None,
    "modified": "test_modified_date",
    "dataset_versions": [
        {
            "id": "test_dataset_id",
            "title": {"en": "testing"},
            "persistent_identifier": None,
            "state": "draft",
            "created": "test_created_date",
            "removed": None,
            "deprecated": None,
            "next_draft": None,
            "draft_of": None,
            "version": 1,
        }
    ],
    "published_revision": 0,
    "draft_revision": 1,
    "draft_of": None,
    "next_draft": None,
    "version": 1,
    "api_version": 3,
    "metadata_repository": "Fairdata",
}

FILE = {
    "id": "pid:urn:identifier",
    "storage_identifier": "urn:uuid:identifier",
    "pathname": "/path/to/file",
    "filename": "file",
    "size": 14798,
    "checksum": "md5:58284d6cdd8deaffe082d063580a9df3",
    "csc_project": "test_project",
    "storage_service": "ida",
    "dataset_metadata": {"use_category": None},
    "characteristics": {
        "file_format_version": {"file_format": None, "format_version": None},
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
