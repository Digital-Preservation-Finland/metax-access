"""Sample Metax dataset data."""

import copy
from metax_access import DS_STATE_METADATA_CONFIRMED


def _construct_dataset(**kwargs):
    file = copy.deepcopy(BASE)
    file.update(kwargs)
    return file


PAS_CATALOG_IDENTIFIER = "urn:nbn:fi:att:data-catalog-pas"


BASE = {
    "id": "test_dataset_id",
    "access_rights": None,
    "actors": [],
    "bibliographic_citation": None,
    "cumulative_state": 0,
    "data_catalog": None,
    "description": None,
    "field_of_science": [],
    "fileset": None,
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
    "preservation": None,
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


FULL = _construct_dataset(
    access_rights={
        "available": None,
        "description": None,
        "license": [
            {
                "url": "http://license_url.test",
                "pref_label": {
                    "en": "Licence Label Test 1.0",
                    "fi": "Lisenssin Nimi Testi 1.0",
                },
                "id": "license_test_id",
                "custom_url": None,
                "title": None,
                "description": None,
                "in_scheme": "http://testi.fi/codelist/testi/license",
            }
        ],
    },
    actors=[
        {
            "organization": {
                "email": None,
                "external_identifier": "org_id_csc",
                "homepage": None,
                "parent": None,
                "pref_label": {
                    "en": "CSC – IT Center for Science",
                    "fi": "CSC - Tieteen tietotekniikan keskus Oy",
                },
                "url": "org_id_csc",
            },
            "person": {
                "external_identifier": None,
                "homepage": None,
                "name": "Teppo Testaaja",
            },
            "roles": ["creator"],
        },
        {
            "organization": {
                "email": None,
                "external_identifier": "org_id_csc",
                "homepage": None,
                "parent": None,
                "pref_label": {
                    "en": "CSC – IT Center for Science",
                    "fi": "CSC - Tieteen tietotekniikan keskus Oy",
                },
                "url": "org_id_csc",
            },
            "roles": ["creator"],
        },
        {
            "organization": {
                "email": None,
                "external_identifier": "org_id_mysterious",
                "homepage": None,
                "parent": None,
                "pref_label": {
                    "en": "Mysterious Organization",
                    "fi": "Mysteeriorganisaatio",
                },
                "url": "org_id_mysterious",
            },
            "person": {
                "email": None,
                "external_identifier": "publisher_identifier",
                "homepage": None,
                "name": "Jussi Julkaisija",
            },
            "roles": ["publisher"],
        },
        {
            "person": {
                "email": "contact.email@csc.fi",
                "external_identifier": None,
                "homepage": None,
                "name": "Rahikainen",
            },
            "roles": ["curator"],
        },
        {
            "person": {
                "email": "contact2.email@csc.fi",
                "external_identifier": None,
                "homepage": None,
                "name": "Rahikainen",
            },
            "roles": ["curator"],
        },
    ],
    data_catalog=PAS_CATALOG_IDENTIFIER,
    description={"en": "A descriptive description describing the content."},
    field_of_science=[
        {
            "id": None,
            "in_scheme": None,
            "pref_label": {
                "en": "Computer and information sciences",
                "fi": "Tietojenkäsittely ja informaatiotieteet",
                "sv": "Data- och informationsvetenskap",
                "und": "Tietojenkäsittely ja informaatiotieteet",
            },
            "url": None,
        }
    ],
    fileset={
        "storage_service": "pas",
        "csc_project": None,
        "total_files_size": 300,
        "total_files_count": 3,
    },
    keyword=["foo", "bar"],
    language=[
        {
            "id": None,
            "in_scheme": None,
            "pref_label": {
                "en": "English language",
                "fi": "Englannin kieli",
                "sv": "engelska",
                "und": "Englannin kieli",
            },
            "url": "http://lexvo.org/id/iso639-3/eng",
        }
    ],
    preservation={
        "contract": "agreement:identifier1",
        "dataset_version": {
            "id": "pas_version_identifier",
            "persistent_identifier": "doi:pas_version_preferred_identifier",
            "preservation_state": DS_STATE_METADATA_CONFIRMED,
        },
        "description": {"en": "preservation_description"},
        "id": "abcdefgh1",
        "reason_description": "preservation_reason_description",
        "state": 75,
        "preservation_identifier": None,
    },
    provenance=[
        {
            "description": {"en": "Data collection process"},
            "event_outcome": {
                "id": None,
                "in_scheme": None,
                "pref_label": {"en": "Success"},
                "url": None,
            },
            "is_associated_with": [
                {
                    "organization": {
                        "email": None,
                        "external_identifier": None,
                        "homepage": None,
                        "parent": None,
                        "pref_label": {"en": "CSC"},
                        "url": None,
                    },
                    "person": {
                        "email": None,
                        "external_identifier": None,
                        "homepage": None,
                        "name": "Teppo Testaaja",
                    },
                }
            ],
            "lifecycle_event": {
                "id": None,
                "in_scheme": None,
                "pref_label": {"en": "Collected"},
                "url": None,
            },
            "outcome_description": {"en": "Great success"},
            "spatial": None,
            "temporal": {
                "end_date": "1999-02-01T00:00:00.000Z",
                "start_date": "1999-01-01T00:00:00.000Z",
                "temporal_coverage": None,
            },
            "title": {"en": "Data collection"},
            "variables": [],
        }
    ],
    spatial=[
        {
            "altitude_in_meters": None,
            "full_address": None,
            "geographic_name": "foo",
            "reference": None,
        },
        {
            "altitude_in_meters": None,
            "full_address": None,
            "geographic_name": "bar",
            "reference": None,
        },
    ],
    theme=[
        {
            "id": None,
            "in_scheme": "http://www.yso.fi/onto/koko/",
            "pref_label": {
                "en": "long-term preservation",
                "fi": "pitkäaikaissäilytys",
                "sv": "långtidsförvaring",
                "und": "pitkäaikaissäilytys",
            },
            "url": "http://www.yso.fi/onto/koko/p51647",
        }
    ],
    metadata_owner={"id": "metadata_owner_test_id"},
)
