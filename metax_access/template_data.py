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
    "data_sensitivity": {
        "is_sensitive": False,
        "rationales": [
            {
                "id": "contract-rationale-1",
                "rationale": {
                    "url": (
                        "http://uri.suomi.fi/codelist/fairdata/"
                        "sensitivity_rationale/code/tietosuojalaki-1050-2018"
                    ),
                    "pref_label": {
                        "en": "Data Protection Act (1050/2018)",
                        "fi": "Tietosuojalaki (1050/2018)",
                        "sv": "Dataskyddslag (1050/2018)"
                    }
                },
                "expiration_date": "2020-01-01"
            }
        ]
    },
    "description": {"und": "Description of unknown length"},
    "created": "test_created_date",
    "validity": {"start_date": "2014-01-17", "end_date": None},
}

DATASET = {
    "id": "test_dataset_id",
    "access_rights": {  # for visualizing Datacite
        "license": [
            {
                "pref_label": {"en": "Title here"},
                "url": "http://urn.fi/urn:nbn:fi:csc-3388475675",
            }
        ],
    },
    "actors": [],
    "data_catalog": "urn:nbn:fi:att:data-catalog-pas",
    "data_sensitivity": {
        "is_sensitive": False,
        "rationales": []
    },
    "description": None,  # for visualizing Datacite
    "field_of_science": [],  # for visualizing Datacite
    "fileset": {
        "total_files_size": 0,
        "csc_project": None,
        "total_files_count": 0,
    },
    "issued": None,  # for visualizing Datacite
    "keyword": [],  # for visualizing Datacite
    "language": [],
    "metadata_owner": {
        "user": "service_tpas",
        "organization": "service_tpas",
    },
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
        "pas_package_created": False,
        "pas_process_running": False,
    },
    "provenance": [],
    "spatial": [],  # for visualizing Datacite
    "state": "published",
    "theme": [],  # for visualizing Datacite
    "title": {"en": "testing"},
    "created": "test_created_date",
    "modified": "test_modified_date",
    "version": 1,  # Probably not used for anything
}

FILE = {
    "id": "pid:urn:identifier",
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
    "is_sensitive": False,
    "pas_process_running": False,
}
