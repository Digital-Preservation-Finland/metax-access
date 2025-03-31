import copy
from datetime import datetime

from metax_access import DS_STATE_METADATA_CONFIRMED

V3_FILE = {
    "id": None,
    "pathname": None,
    "storage_identifier": None,
    "filename": None,
    "size": None,
    "checksum": None,
    "csc_project": None,
    "storage_service": None,
    "dataset_metadata": {"use_category": None},
    "characteristics": None,
    "characteristics_extension": None,
    "pas_compatible_file": None,
    "non_pas_compatible_file": None,
}

V3_CONTRACT = {
    "id": None,
    "title": {"und": None},
    "quota": None,
    "organization": None,
    "contact": None,
    "related_service": None,
    "description": {"und": None},
    "created": None,
    "validity": None,
}

# Minimum reponse from metax_access according to Metax V3 documentation
# Has some default values, which are not normalized in metax-access
V3_MINIMUM_TEMPLATE_DATASET = {
    "id": None,
    "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), # a default value
    "title": None, # non nullable
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
            "reason_description": None,
            "dataset_version": {
                "id": None,
                "persistent_identifier": None,
                "preservation_state": -1
            },
            "contract":None
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
    "metadata_owner": None,
    "data_catalog": None
    }


PAS_CATALOG_IDENTIFIER = "urn:nbn:fi:att:data-catalog-pas"
DATASET_V3 = {
    'access_rights': {
        'available': None,
        'description': None,
        'license': [
            {
                'custom_url': None,
                'description': None,
                'title': [{'en': 'Title here'}],
                'url': 'http://urn.fi/urn:nbn:fi:csc-3388475675'
            }
        ]
    },
    'actors': [
        {
            'organization': {
                'email': None,
                'external_identifier': 'org_id_csc',
                'homepage': None,
                'parent': None,
                'pref_label': {
                    'en': 'CSC – IT Center for Science',
                    'fi': 'CSC - Tieteen tietotekniikan keskus Oy'
                },
                'url': 'org_id_csc'
            },
            'person': {
                'email': None,
                'external_identifier': None,
                'homepage': None,
                'name': 'Teppo Testaaja'
            },
            'roles': ['creator']
        },
        {
            'organization': {
                'email': None,
                'external_identifier': 'org_id_csc',
                'homepage': None,
                'parent': None,
                'pref_label': {
                    'en': 'CSC – IT Center for Science',
                    'fi': 'CSC - Tieteen tietotekniikan keskus Oy'
                },
                'url': 'org_id_csc'
            },
            'roles': ['creator']
        },
        {
            'organization': {
                'email': None,
                'external_identifier': 'org_id_mysterious',
                'homepage': None,
                'parent': None,
                'pref_label': {
                    'en': 'Mysterious Organization',
                    'fi': 'Mysteeriorganisaatio'
                },
                'url': 'org_id_mysterious'
            },
            'person': {
                'email': None,
                'external_identifier': 'publisher_identifier',
                'homepage': None,
                'name': 'Jussi Julkaisija'
            },
            'roles': ['publisher']
        },
        {
            'person': {
                'email': 'contact.email@csc.fi',
                'external_identifier': None,
                'homepage': None,
                'name': 'Rahikainen'
            },
            'roles': ['curator']
        },
        {
            'person': {
                'email': 'contact2.email@csc.fi',
                'external_identifier': None,
                'homepage': None,
                'name': 'Rahikainen'
            },
            'roles': ['curator']
        }
    ],
    'created': 'date_created',
    'data_catalog': PAS_CATALOG_IDENTIFIER,
    'description': {'en': 'A descriptive description describing the content.'},
    'field_of_science': [
        {
            'id': None,
            'in_scheme': None,
            'pref_label': {
                'en': 'Computer and information sciences',
                'fi': 'Tietojenkäsittely ja informaatiotieteet',
                'sv': 'Data- och informationsvetenskap',
                'und': 'Tietojenkäsittely ja informaatiotieteet'
            },
            'url': None}
    ],
    'fileset': {
        'storage_service': 'pas',
        'csc_project': None,
        'total_files_size': 300,
        'total_files_count': 3,
    },
    'id': 'dataset_identifier',
    'issued': '2000-01-01',
    'keyword': ['foo', 'bar'],
    'language': [
        {
            'id': None,
            'in_scheme': None,
            'pref_label': {
                'en': 'English language',
                'fi': 'Englannin kieli',
                'sv': 'engelska',
                'und': 'Englannin kieli'
            },
            'url': 'http://lexvo.org/id/iso639-3/eng'
        }
    ],
    'metadata_owner': {'organization': 'csc.fi', 'user': 'teppo'},
    'modified': 'date_modified',
    'persistent_identifier': 'doi:preferred_identifier',
    'preservation': {
        'contract': 'agreement:identifier1',
        'dataset_version': {
            'id': 'pas_version_identifier',
            'persistent_identifier': 'doi:pas_version_preferred_identifier',
            'preservation_state': DS_STATE_METADATA_CONFIRMED
        },
        'description': {'en': 'preservation_description'},
        'id': 'abcdefgh1',
        'reason_description': 'preservation_reason_description',
        'state': 75,
        'preservation_identifier': None
    },
    'projects': [],
    'provenance': [
        {
            'description': {'en': 'Data collection process'},
            'event_outcome': {
                'id': None,
                'in_scheme': None,
                'pref_label': {'en': 'Success'},
                'url': None
            },
            'is_associated_with': [
                {
                    'organization': {
                        'email': None,
                        'external_identifier': None,
                        'homepage': None,
                        'parent': None,
                        'pref_label': {'en': 'CSC'},
                        'url': None
                    },
                    'person': {
                        'email': None,
                        'external_identifier': None,
                        'homepage': None,
                        'name': 'Teppo Testaaja'
                    }
                }
            ],
            'lifecycle_event': {
                'id': None,
                'in_scheme': None,
                'pref_label': {'en': 'Collected'},
                'url': None
            },
            'outcome_description': {'en': 'Great success'},
            'spatial': None,
            'temporal': {
                'end_date': '1999-02-01T00:00:00.000Z',
                'start_date': '1999-01-01T00:00:00.000Z',
                'temporal_coverage': None
            },
            'title': {'en': 'Data collection'},
            'variables': []
        }
    ],
    'spatial': [
        {
            'altitude_in_meters': None,
            'full_address': None,
            'geographic_name': 'foo',
            'reference': None
        },
        {
            'altitude_in_meters': None,
            'full_address': None,
            'geographic_name': 'bar',
            'reference': None
        }
    ],
    'theme': [
        {
            'id': None,
            'in_scheme': 'http://www.yso.fi/onto/koko/',
            'pref_label': {
                'en': 'long-term preservation',
                'fi': 'pitkäaikaissäilytys',
                'sv': 'långtidsförvaring',
                'und': 'pitkäaikaissäilytys'
            },
            'url': 'http://www.yso.fi/onto/koko/p51647'
        }
    ],
    'title': {'en': 'Wonderful Title'},
    'version': 'version'
}


FILE_V3 = {
    "id": None,
    "storage_identifier": None,
    "pathname": None,
    "filename": None,
    "size": 0,
    "storage_service": "pas",
    "csc_project": "",
    "checksum": None,
    "frozen": None,
    "modified": None,
    "removed": None,
    "user": None,
    "characteristics": {
        "file_format_version": {
            "id": None,
            "url": None,
            "in_scheme": None,
            "pref_label": None,
            "file_format": None,
            "format_version": None
        },
        "encoding": None,
        "csv_has_header": None,
        "csv_quoting_char": None,
        "csv_delimiter": None,
        "csv_record_separator": None,
    },
    "characteristics_extension": None,
    "pas_process_running": False,
    "pas_compatible_file": None,
    "non_pas_compatible_file": None,
    "dataset_metadata": {
        "title": None,
        "file_type": None,
        "use_category": {
            "id": "8cea0b9b-8cfa-4ff0-a8ff-0b3b85addf5f",
            "url": (
                "http://uri.suomi.fi/codelist/fairdata/"
                "use_category/code/source"
            ),
            "pref_label": {
                "en": "Source material",
                "fi": "Lähdeaineisto"
            }
        },
    }
}


def _create_merged_dict(data, **kwargs):
    """
    Create a new dict with fields merged from the given keyword arguments

    '__' can be used to separate nested dicts as with Metax API. For example,
    parameter
    `preservation__state="foo"`
    will be equivalent to `data['preservation']['state'] = "foo"`.
    """
    data = copy.deepcopy(data)

    # Use '__' as separator for nested dicts.
    # For example, 'preservation__state="foo"' will be equivalent to
    # `dataset["preservation"]["state"] = "foo"`
    for key, value in kwargs.items():
        fields = key.split("__")
        field = None
        field_dict = data

        while len(fields) > 1:
            field = fields.pop(0)
            with contextlib.suppress(ValueError):
                # Cast to integer in case one was provided; this allows
                # modifying lists
                field = int(field)

            field_dict = field_dict[field]

        last_field = fields.pop()

        # Ensure that the field we're trying to set actually exists.
        # We can do this as we deal with complete responses in Metax V3.
        assert last_field in field_dict, f"Field {key} does not exist!"

        field_dict[last_field] = value

    return data


def create_test_v3_file(**kwargs):
    return _create_merged_dict(FILE_V3, **kwargs)


def create_test_v3_dataset(**kwargs):
    return _create_merged_dict(DATASET_V3, **kwargs)
