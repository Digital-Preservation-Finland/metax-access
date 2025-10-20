"""Sample metax access dataset response data."""

import copy
from metax_access import DS_STATE_METADATA_CONFIRMED


def _construct_dataset_response(**kwargs):
    response = copy.deepcopy(BASE)
    response.update(kwargs)
    return response


PAS_CATALOG_IDENTIFIER = "urn:nbn:fi:att:data-catalog-pas"


BASE = {
    "id": "test_dataset_id",
    "created": "test_created_date",
    "title": {"en": "testing"},
    "description": None,
    "modified": "test_modified_date",
    "fileset": {
        "total_files_size": 0,
        "csc_project": None,
        "total_files_count": 0,
    },
    "preservation": {
        "state": -1,
        "description": None,
        "reason_description": None,
        "dataset_version": {
            "id": None,
            "persistent_identifier": None,
            "preservation_state": None,
        },
        "contract": None,
        "pas_package_created": None,
    },
    "access_rights": None,
    "version": 1,
    "language": [],
    "persistent_identifier": None,
    "issued": None,
    "actors": [],
    "keyword": [],
    "theme": [],
    "spatial": [],
    "field_of_science": [],
    "provenance": [],
    "metadata_owner": {"organization": "service_tpas", "user": "service_tpas"},
    "data_catalog": None,
}

FULL = _construct_dataset_response(
    description={"en": "A descriptive description describing the content."},
    fileset={
        "total_files_size": 300,
        "csc_project": None,
        "total_files_count": 3,
    },
    preservation={
        "state": 75,
        "description": {"en": "preservation_description"},
        "reason_description": "preservation_reason_description",
        "dataset_version": {
            "id": "pas_version_identifier",
            "persistent_identifier": "doi:pas_version_preferred_identifier",
            "preservation_state": 75,
        },
        "contract": "agreement:identifier1",
        "pas_package_created": True,
    },
    access_rights={
        "license": [
            {
                "url": "http://license_url.test",
                "pref_label": {
                    "en": "Licence Label Test 1.0",
                    "fi": "Lisenssin Nimi Testi 1.0",
                },
            }
        ]
    },
    language=[{"url": "http://lexvo.org/id/iso639-3/eng"}],
    actors=[
        {
            "roles": ["creator"],
            "person": {
                "name": "Teppo Testaaja",
                "external_identifier": None,
                "email": None,
            },
            "organization": {
                "pref_label": {
                    "en": "CSC – IT Center for Science",
                    "fi": "CSC - Tieteen tietotekniikan keskus Oy",
                },
                "url": "org_id_csc",
                "external_identifier": "org_id_csc",
                "parent": None,
            },
        },
        {
            "roles": ["creator"],
            "person": None,
            "organization": {
                "pref_label": {
                    "en": "CSC – IT Center for Science",
                    "fi": "CSC - Tieteen tietotekniikan keskus Oy",
                },
                "url": "org_id_csc",
                "external_identifier": "org_id_csc",
                "parent": None,
            },
        },
        {
            "roles": ["publisher"],
            "person": {
                "name": "Jussi Julkaisija",
                "external_identifier": "publisher_identifier",
                "email": None,
            },
            "organization": {
                "pref_label": {
                    "en": "Mysterious Organization",
                    "fi": "Mysteeriorganisaatio",
                },
                "url": "org_id_mysterious",
                "external_identifier": "org_id_mysterious",
                "parent": None,
            },
        },
        {
            "roles": ["curator"],
            "person": {
                "name": "Rahikainen",
                "external_identifier": None,
                "email": "contact.email@csc.fi",
            },
            "organization": None,
        },
        {
            "roles": ["curator"],
            "person": {
                "name": "Rahikainen",
                "external_identifier": None,
                "email": "contact2.email@csc.fi",
            },
            "organization": None,
        },
    ],
    keyword=["foo", "bar"],
    theme=[
        {
            "pref_label": {
                "en": "long-term preservation",
                "fi": "pitkäaikaissäilytys",
                "sv": "långtidsförvaring",
                "und": "pitkäaikaissäilytys",
            }
        }
    ],
    spatial=[{"geographic_name": "foo"}, {"geographic_name": "bar"}],
    field_of_science=[
        {
            "pref_label": {
                "en": "Computer and information sciences",
                "fi": "Tietojenkäsittely ja informaatiotieteet",
                "sv": "Data- och informationsvetenskap",
                "und": "Tietojenkäsittely ja informaatiotieteet",
            }
        }
    ],
    provenance=[
        {
            "title": {"en": "Data collection"},
            "temporal": {
                "start_date": "1999-01-01T00:00:00.000Z",
            },
            "description": {"en": "Data collection process"},
            "event_outcome": {"pref_label": {"en": "Success"}, "url": None},
            "outcome_description": {"en": "Great success"},
            "lifecycle_event": {"pref_label": {"en": "Collected"}},
        }
    ],
    data_catalog=PAS_CATALOG_IDENTIFIER,
    metadata_owner={
        "organization": None,
        "user": None,
    },
)
