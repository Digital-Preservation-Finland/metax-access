from datetime import datetime

# Minimum reponse from metax_access
V3_MINIMUM_TEMPLATE_DATASET = {
    "id": 123,
    "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), # a default value
    "title": "The title of the Dataset",
    "description": None,
    "modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), # a default value
    "fileset": 
        {
            "csc_project": None,
            "total_files_size": 0 # what's the minimum files size
        },
    "preservation": {
        "state": -1,
        "description": None,
        "reason_description": "User-provided reason for rejecting or accepting a dataset in DPRES",
        "dataset_version": {
            "id": "123" #uuid
            },
        },
    "access_rights": None,
    "version": None, #has a default value?
    "language": [], #default is an empty list
    "persistent_identifier": None,
    "issued": None,
    "actors": [], # default is an empty list
    "keyword": [], # default is an empty list
    "theme": [], #default is an empty list
    "spatial": [], #default is an empty list
    "field_of_science": [], # default is an empty list 
    "provenance": [], # default is an empty list
    }

# Reponse without empty lists
V3_TEMPLATE_DATASET = {
    "id": 123,
    "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), # a default value
    "title": "The title of the Dataset",
    "description": None,
    "modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), # a default value
    "fileset": 
        {
            "csc_project": None,
            "total_files_size": 0 # what's the minimum files size
        },
    "preservation": {
        "state": -1,
        "description": None,
        "reason_description": "User-provided reason for rejecting or accepting a dataset in DPRES",
        "dataset_version": {
            "id": "123" #uuid
            },
        },
    "access_rights": {
        "license": [
            {
                "url": None, 
                "title": None
            }
        ]
    },
    "version": None,
    "language": [
        {
            "url": "http://lexvo.org/id/iso639-3/eng"
        }
    ],
    "persistent_identifier": None,
    "issued": None,
    "actors": [
        {
            "roles": "creator",
            "person": None,
            "organization": {
                "pref_label": None,
                "url": None,
                "external_identifier": None,
                "parent": None,
            },
        }
    ],
    "keyword": ["test"],
    "theme": [
        {"pref_label": None}
    ],
    "spatial": [
        {
            "geographic_name": None
        }
    ],
    "field_of_science": [
        {
            "pref_label": None
        }
    ],
    "provenance": [
        {
            "title": None,
            "temporal": None,
            "description": None,
            "event_outcome": None,
            "outcome_description": None,
            "is_associated_with": []
        }
    ],
}
