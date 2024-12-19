# pylint: disable=no-member
"""
Tests for ``metax_access.v2_to_v3_converter``
and ``metax_access.v3_to_v2_converter`` modules.
"""
import copy

from metax_access import v2_to_v3_converter, v3_to_v2_converter

PAS_CATALOG_IDENTIFIER = "urn:nbn:fi:att:data-catalog-pas"

FILEV2 = {
    "identifier": "pid:urn:1",
    "file_path": "/path/to/file",
    "file_storage": {"identifier": "urn:nbn:fi:att:file-storage-ida"},
    "checksum": {
        "algorithm": "MD5",
        "value": "58284d6cdd8deaffe082d063580a9df3",
        "checked": "2000-01-01T12:00:00+03:00",
    },
    "project_identifier": "test_project",
    "file_characteristics": {
        "encoding": "UTF-8",
        "file_created": "2014-01-17T08:19:31Z",
        "file_format": "text/plain",
    },
    "file_characteristics_extension": {
        "streams": {0: {"mimetype": "text/plain", "stream_type": "text"}}
    },
}

CONVERTED_FILEV2 = {
    "id": "pid:urn:1",
    "identifier": "pid:urn:1",
    "file_storage": {"identifier": "urn:nbn:fi:att:file-storage-ida"},
    "file_path": "/path/to/file",
    "checksum": {
        "algorithm": "MD5",
        "value": "58284d6cdd8deaffe082d063580a9df3",
    },
    "service_created": "ida",
    "project_identifier": "test_project",
    "file_characteristics": {
        "encoding": "UTF-8",
        "file_format": "text/plain",
    },
    "file_characteristics_extension": {
        "streams": {0: {"mimetype": "text/plain", "stream_type": "text"}}
    }
}


FILEV3 = {
    "id": "pid:urn:1",
    "storage_identifier": "pid:urn:1",
    "pathname": "/path/to/file",
    "filename": None,
    "size": None,
    "checksum": "md5:58284d6cdd8deaffe082d063580a9df3",
    "storage_service": "ida",
    "csc_project": "test_project",
    "frozen": None,
    "modified": None,
    "removed": None,
    "published": None,
    "dataset_metadata": {
        "title": None,
        "file_type": None,
        "use_category": None,
    },
    "characteristics": {
        "file_created": "2014-01-17T08:19:31Z",
        "encoding": "UTF-8",
        "csv_has_header": None,
        "csv_quoting_char": None,
        "csv_delimiter": None,
        "csv_record_separator": None,
        "file_format_version": {
            "pref_label": None,
            "file_format": "text/plain",
            "format_version": None,
        },
    },
    "characteristics_extension": {
        "streams": {0: {"mimetype": "text/plain", "stream_type": "text"}}
    },
}


def test_convert_file_v2_to_v3():
    result = v2_to_v3_converter.convert_file(FILEV2)
    assert result == FILEV3


def test_convert_file_v3_to_v2():
    result = v3_to_v2_converter.convert_file(FILEV3)
    assert result == CONVERTED_FILEV2


def test_convert_file_v2_to_v3_with_research_dataset():
    research_dataset_info = {
        "title": "File metadata title 1",
        "file_type": {
            "in_scheme": "http://uri.suomi.fi/codelist/fairdata/file_type",
            "identifier": "http://uri.suomi.fi/codelist/fairdata/file_type/code/text",
            "pref_label": {"en": "Text", "fi": "Teksti", "und": "Teksti"},
        },
        "identifier": "pid:urn:1",
        "use_category": {
            "in_scheme": "http://uri.suomi.fi/codelist/fairdata/use_category",
            "identifier": "http://uri.suomi.fi/codelist/fairdata/use_category/code/source",
            "pref_label": {
                "en": "Source material",
                "fi": "Lähdeaineisto",
                "und": "Lähdeaineisto",
            },
        },
        "details": {"project_identifier": "project_identifier"},
    }

    result = v2_to_v3_converter.convert_file(FILEV2, research_dataset_info)
    file = copy.deepcopy(FILEV3)
    del research_dataset_info["details"]
    del research_dataset_info["identifier"]
    file["dataset_metadata"] = research_dataset_info
    assert result == file


V2_LICENSE = {
    "identifier": "foo",
    "license": "test_license",
    "title": "license_title",
    "description": "license description",
}
V3_LICENSE = {
    "url": "foo",
    "custom_url": "test_license",
    "title": "license_title",
    "description": "license description",
}


def test_convert_license_v2_to_v3():
    assert v2_to_v3_converter._convert_license(V2_LICENSE) == V3_LICENSE


BASE_DATASETV2 = {
    "identifier": "dataset_identifier",
    "data_catalog": {"identifier": "urn:nbn:fi:att:data-catalog-pas"},
    "preservation_identifier": "doi:test",
    "contract": {"identifier": "contract_identifier"},
    "research_dataset": {
        "metadata_version_identifier": "1955e904-e3dd-4d7e-99f1-3fed446f96d1"
    },
    "preservation_state": 0,
    "date_created": 'now',
    'date_modified': 'now'
}

BASE_DATASETV3 = {
    "metadata_owner": None,
    "data_catalog": "urn:nbn:fi:att:data-catalog-pas",
    "cumulation_started": None,
    "cumulation_ended": None,
    "cumulative_state": None,
    "created": "now",
    "deprecated": None,
    "state": None,
    "last_cumulative_addition": None,
    "id": "dataset_identifier",
    "api_version": 1,
    "preservation": {
        "contract": "contract_identifier",
        "id": "doi:test",
        "state": 0,
        "description": None,
        "reason_description": None,
        "dataset_version": {
            "id": None,
            'persistent_identifier': None,
            'preservation_state': -1
        },
    },
    "modified": "now",
    "persistent_identifier": None,
    "title": None,
    "description": None,
    "issued": None,
    "keyword": [],
    "bibliographic_citation": None,
    "actors": [],
    "provenance": [],
    "projects": [],
    "field_of_science": [],
    "theme": [],
    "language": [],
    "infrastructure": [],
    "spatial": [],
    "temporal": [],
    "other_identifiers": [],
    "relation": [],
    "remote_resources": [],
    "fileset": {"csc_project": None, "total_files_size": 0},
    "version": None,
    "access_rights": None,
}


def test_convert_base_dataset_v2_to_v3():
    result = v2_to_v3_converter.convert_dataset(BASE_DATASETV2)
    assert result == BASE_DATASETV3


DATASETV2 = {
    "preservation_identifier": "preservation_identifier",
    "identifier": "dataset_identifier",
    "contract": {"id": 2, "identifier": "agreement:identifier1"},
    "metadata_owner_org": "csc.fi",
    "metadata_provider_org": "csc.fi",
    "metadata_provider_user": "teppo",
    "research_dataset": {
        "files": [
            {
                "title": "File metadata title 1",
                "identifier": "pid:urn:1",
                "details": {"project_identifier": "project_identifier"},
            },
            {
                "title": "File metadata title 2",
                "identifier": "pid:urn:2",
                "details": {"project_identifier": "project_identifier"},
            },
        ],
        "directories": [
            {
                "title": "Title for directory",
                "identifier": "directory-identifier1",
                "details": {"project_identifier": "project_identifier"},
            }
        ],
        "curator": [
            {
                "name": "Rahikainen",
                "email": "contact.email@csc.fi",
                "@type": "Person",
            },
            {
                "name": "Rahikainen",
                "email": "contact2.email@csc.fi",
                "@type": "Person",
            },
        ],
        "access_rights": {"license": [V2_LICENSE]},
        "title": {"en": "Wonderful Title"},
        "language": [
            {
                "title": {
                    "en": "English language",
                    "fi": "Englannin kieli",
                    "sv": "engelska",
                    "und": "Englannin kieli",
                },
                "identifier": "http://lexvo.org/id/iso639-3/eng",
            }
        ],
        "description": {
            "en": "A descriptive description describing the content."
        },
        "total_files_byte_size": 300,
        "preferred_identifier": "doi:preferred_identifier",
        "issued": "2000-01-01",
        "creator": [
            {
                "name": "Teppo Testaaja",
                "@type": "Person",
                "member_of": {
                    "name": {
                        "en": "CSC – IT Center for Science",
                        "fi": "CSC - Tieteen tietotekniikan keskus Oy",
                    },
                    "@type": "Organization",
                    "identifier": "org_id_csc",
                },
            },
            {
                "name": {
                    "en": "CSC – IT Center for Science",
                    "fi": "CSC - Tieteen tietotekniikan keskus Oy",
                },
                "@type": "Organization",
                "identifier": "org_id_csc",
            },
        ],
        "publisher": {
            "name": "Jussi Julkaisija",
            "@type": "Person",
            "member_of": {
                "name": {
                    "en": "Mysterious Organization",
                    "fi": "Mysteeriorganisaatio",
                },
                "@type": "Organization",
                "identifier": "org_id_mysterious",
            },
            "identifier": "publisher_identifier",
        },
        "keyword": ["foo", "bar"],
        "theme": [
            {
                "in_scheme": "http://www.yso.fi/onto/koko/",
                "identifier": "http://www.yso.fi/onto/koko/p51647",
                "pref_label": {
                    "en": "long-term preservation",
                    "fi": "pitk\u00e4aikaiss\u00e4ilytys",
                    "sv": "l\u00e5ngtidsf\u00f6rvaring",
                    "und": "pitk\u00e4aikaiss\u00e4ilytys",
                },
            }
        ],
        "spatial": [
            {"geographic_name": "foo"},
            {"geographic_name": "bar"},
        ],
        "field_of_science": [
            {
                "pref_label": {
                    "en": "Computer and information sciences",
                    "fi": "Tietojenk\u00e4sittely ja informaatiotieteet",
                    "sv": "Data- och informationsvetenskap",
                    "und": "Tietojenk\u00e4sittely ja informaatiotieteet",
                }
            }
        ],
        "provenance": [
            {
                "title": {"en": "Data collection"},
                "temporal": {
                    "end_date": "1999-02-01T00:00:00.000Z",
                    "start_date": "1999-01-01T00:00:00.000Z",
                },
                "description": {"en": "Data collection process"},
                "event_outcome": {
                    "pref_label": {
                        "en": "Success",
                    }
                },
                "lifecycle_event": {
                    "pref_label": {
                        "en": "Collected",
                    }
                },
                "outcome_description": {"en": "Great success"},
                "was_associated_with": [
                    {
                        "name": "Teppo Testaaja",
                        "@type": "Person",
                        "member_of": {
                            "name": {
                                "en": "CSC",
                            },
                        },
                    }
                ],
            }
        ],
        "version": "version",
        "modified": "modified",
    },
    "preservation_state": "preservation_state",
    "preservation_state_modified": "preservation_state_modified",
    "preservation_description": "preservation_description",
    "preservation_reason_description": "preservation_reason_description",
    "data_catalog": {"id": 1, "identifier": PAS_CATALOG_IDENTIFIER},
    "preservation_dataset_version": {
        "id": 2,
        "identifier": "pas_version_identifier",
        "preferred_identifier": "doi:pas_version_preferred_identifier",
    },
    'date_modified': 'now',
    'date_created': 'now'
}

DATASETV3 = {
    "metadata_owner": {"user": "teppo", "organization": "csc.fi"},
    "data_catalog": "urn:nbn:fi:att:data-catalog-pas",
    "cumulation_started": None,
    "cumulation_ended": None,
    "cumulative_state": None,
    "created": "now",
    "deprecated": None,
    "state": None,
    "last_cumulative_addition": None,
    "id": "dataset_identifier",
    "api_version": 1,
    "preservation": {
        "contract": "agreement:identifier1",
        "id": "preservation_identifier",
        "state": "preservation_state",
        "description": "preservation_description",
        "reason_description": "preservation_reason_description",
        "dataset_version": {
            "id": "pas_version_identifier",
            'persistent_identifier': 'doi:pas_version_preferred_identifier',
            'preservation_state': -1
        },
    },
    "modified": "now",
    "persistent_identifier": "doi:preferred_identifier",
    "title": {"en": "Wonderful Title"},
    "description": {"en": "A descriptive description describing the content."},
    "issued": "2000-01-01",
    "keyword": ["foo", "bar"],
    "bibliographic_citation": None,
    "actors": [
        {
            "person": {
                "name": "Teppo Testaaja",
                "external_identifier": None,
                "email": None,
                "homepage": None,
            },
            "organization": {
                "pref_label": {
                    "en": "CSC – IT Center for Science",
                    "fi": "CSC - Tieteen tietotekniikan keskus Oy",
                },
                "email": None,
                "homepage": None,
                'external_identifier': 'org_id_csc',
                'parent': None,
                "url": "org_id_csc",
            },
            "roles": ["creator"],
        },
        {
            "organization": {
                "pref_label": {
                    "en": "CSC – IT Center for Science",
                    "fi": "CSC - Tieteen tietotekniikan keskus Oy",
                },
                "email": None,
                "homepage": None,
                "url": "org_id_csc",
                'external_identifier': 'org_id_csc',
                'parent': None,
            },
            "roles": ["creator"],
        },
        {
            "person": {
                "name": "Jussi Julkaisija",
                "external_identifier": "publisher_identifier",
                "email": None,
                "homepage": None,
            },
            "organization": {
                "pref_label": {
                    "en": "Mysterious Organization",
                    "fi": "Mysteeriorganisaatio",
                },
                "email": None,
                "homepage": None,
                "url": "org_id_mysterious",
                'external_identifier': 'org_id_mysterious',
                'parent': None,
            },
            "roles": ["publisher"],
        },
        {
            "person": {
                "name": "Rahikainen",
                "external_identifier": None,
                "email": "contact.email@csc.fi",
                "homepage": None,
            },
            "roles": ["curator"],
        },
        {
            "person": {
                "name": "Rahikainen",
                "external_identifier": None,
                "email": "contact2.email@csc.fi",
                "homepage": None,
            },
            "roles": ["curator"],
        },
    ],
    "provenance": [
        {
            "title": {"en": "Data collection"},
            "description": {"en": "Data collection process"},
            "preservation_event": None,
            "temporal": {
                "start_date": "1999-01-01T00:00:00.000Z",
                "end_date": "1999-02-01T00:00:00.000Z",
                "temporal_coverage": None,
            },
            "outcome_description": {"en": "Great success"},
            "spatial": None,
            "event_outcome": {
                "id": None,
                "url": None,
                "in_scheme": None,
                "pref_label": {"en": "Success"},
            },
            "lifecycle_event": {
                "id": None,
                "url": None,
                "in_scheme": None,
                "pref_label": {"en": "Collected"},
            },
            "variables": [],
            "is_associated_with": [
                {
                    "person": {
                        "name": "Teppo Testaaja",
                        "external_identifier": None,
                        "email": None,
                        "homepage": None,
                    },
                    "organization": {
                        "pref_label": {"en": "CSC"},
                        "email": None,
                        "homepage": None,
                        "url": None,
                        'external_identifier': None,
                        'parent': None,
                    },
                }
            ],
        }
    ],
    "field_of_science": [
        {
            "id": None,
            "url": None,
            "in_scheme": None,
            "pref_label": {
                "en": "Computer and information sciences",
                "fi": "Tietojenkäsittely ja informaatiotieteet",
                "sv": "Data- och informationsvetenskap",
                "und": "Tietojenkäsittely ja informaatiotieteet",
            },
        }
    ],
    "theme": [
        {
            "id": None,
            "url": "http://www.yso.fi/onto/koko/p51647",
            "in_scheme": "http://www.yso.fi/onto/koko/",
            "pref_label": {
                "en": "long-term preservation",
                "fi": "pitkäaikaissäilytys",
                "sv": "långtidsförvaring",
                "und": "pitkäaikaissäilytys",
            },
        }
    ],
    "language": [
        {
            "id": None,
            "url": "http://lexvo.org/id/iso639-3/eng",
            "in_scheme": None,
            "pref_label": {
                "en": "English language",
                "fi": "Englannin kieli",
                "sv": "engelska",
                "und": "Englannin kieli",
            },
        }
    ],
    "spatial": [
        {
            "reference": None,
            "geographic_name": "foo",
            "full_address": None,
            "altitude_in_meters": None,
        },
        {
            "reference": None,
            "geographic_name": "bar",
            "full_address": None,
            "altitude_in_meters": None,
        },
    ],
    "fileset": {"csc_project": "project_identifier", "total_files_size": 300},
    "access_rights": {
        "license": [
            {
                "url": "foo",
                "custom_url": "test_license",
                "title": "license_title",
                "description": "license description",
            }
        ],
        "description": None,
        "available": None,
    },
    "temporal": [],
    "remote_resources": [],
    "relation": [],
    "projects": [],
    "other_identifiers": [],
    "infrastructure": [],
    "version": "version"
}


def test_convert_dataset_v2_to_v3():
    result = v2_to_v3_converter.convert_dataset(DATASETV2)
    assert DATASETV3 == result


CONTRACTV2 = {
    "id": 2,
    "contract_json": {
        "identifier": "agreement1",
        "quota": 111204,
        "organization": {"name": "koti", "organization_identifier": "koti.fi"},
    },
}

CONTRACTV3 = {
    "modified": None,
    "created": None,
    "service": None,
    "removed": None,
    "contract_identifier": "agreement1",
    "title": {"und": None},
    "description": {"und": None},
    "quota": 111204,
    "organization": {"name": "koti", "organization_identifier": "koti.fi"},
    "validity": None,
    "contact": None,
    "related_service": None,
}


def test_contract_v2_to_v3():
    result = v2_to_v3_converter.convert_contract(CONTRACTV2)
    assert result == CONTRACTV3


DIRECTORYV2 = {
    "directories": [
        {
            "identifier": "pid:urn:dir:2",
            "directory_name": "project_x_FROZEN",
            "byte_size": 0,
            "file_count": 0,
            "parent_directory": {"identifier": "pid:urn:dir:1", "id": 1},
            "date_created": "2017-05-23T13:07:22+03:00",
            "directory_modified": "2017-06-23T15:41:59+03:00",
            "directory_path": "/project_x_FROZEN",
            "id": 2,
            "project_identifier": "project_x",
            "date_modified": "2017-06-27T13:07:22+03:00",
            "service_created": "metax",
            "removed": "false",
        }
    ],
    "files": [],
    "identifier": "pid:urn:dir:1",
    "directory_name": "",
    "byte_size": 0,
    "file_count": 0,
    "date_created": "2017-05-23T13:07:22+03:00",
    "directory_modified": "2017-06-23T15:41:59+03:00",
    "directory_path": "/",
    "id": 1,
    "project_identifier": "project_x",
    "date_modified": "2017-06-27T13:07:22+03:00",
    "service_created": "metax",
    "removed": "false",
}

DIRECTORYV3 = {
    "count": None,
    "next": None,
    "previous": None,
    "results": {
        "directory": {
            "pathname": "/",
        },
        "directories": [
            {
                "name": "project_x_FROZEN",
                "size": 0,
                "file_count": 0,
                "pathname": "/project_x_FROZEN",
            }
        ],
        "files": [],
    },
}


def test_directory_files_response_v2_to_v3():
    result = v2_to_v3_converter.convert_directory_files_response(DIRECTORYV2)
    assert result == DIRECTORYV3
