"""Payload converter from Metax v2 to Metax v3."""

import copy
from typing import Optional

from metax_access.response import (MetaxFile, MetaxFileCharacteristics,
                                   MetaxFileFormatVersion)

# We can also determine the storage service using `service_created`.
# `file_storage.identifier` <-> `storage_service` mapping is recommended by the
# Metax V3 migration guide, however.
FILE_STORAGE_V2_TO_STORAGE_SERVICE_V3 = {
    "urn:nbn:fi:att:file-storage-pas": "pas",
    "urn:nbn:fi:att:file-storage-ida": "ida",
}


def convert_contract(json):
    """Converts Metax V2 contract to Metax V3 contract.
    If a value is not defined in V2 payload, the value is not icluded in
    the output.

    :param dict json: Metax V2 contract as a JSON.
    :returns: Metax V3 contract as a dictionary
    """
    contract = {
        "modified": json.get("date_modified"),
        "created": json.get("date_created"),
        "service": json.get("service_created"),
        "removed": json.get("removed"),
    }
    contract_json = json.get("contract_json", {})
    contract |= {
        "contract_identifier": contract_json.get('identifier'),
        "title": {
            "und": contract_json.get('title')
        },
        "description": {
            "und": contract_json.get('description')
        },
        "quota": contract_json.get('quota'),
        "organization": contract_json.get('organization'),
        "validity": contract_json.get('validity'),
        "contact": contract_json.get('contact'),
        "related_service": contract_json.get('related_service')
    }
    return contract


def convert_directory_files_response(json):
    """Converts Metax V2 directory files response to Metax V3 directory
    info response. If a value is not defined in V2 payload,
    the value is not icluded in the output.
    :param dict json: Metax V2 directory files output as a JSON
    :returns: Metax V3 directory reponse from GET /v3/directories
    """
    directories = [
        {
            "name": directory.get("directory_name"),
            "size": directory.get("byte_size"),
            "file_count": directory.get("file_count"),
            "pathname": directory.get("directory_path"),
        }
        for directory in json.get("directories", [])
    ]

    files = [
        {
            "id": file.get("identifier"),
            "filename": file.get("file_name"),
            "size": file.get("byte_size"),
        }
        for file in json.get("files", [])
    ]

    directory = {
        "pathname": json.get("directory_path")
    }

    return {
        "count": None,
        "next": None,
        "previous": None,
        "results": {
            "directory": directory,
            "directories": directories,
            "files": files,
        },
    }


def convert_dataset(json, metax=None):
    """Converts Metax V2 dataset to Metax V3 dataset
    info response. If a value is not defined in V2 payload,
    the value is not icluded in the output. Most of this conversion is from
    https://gitlab.ci.csc.fi/fairdata/fairdata-metax-v3/
    -/blob/master/src/apps/core/models/legacy_converter.py
    but only relevant fields to FDPAS services are included.

    :param dict json: Metax V2 dataset as a JSON
    :returns: Metax V3 dataset
    """
    deprecated = None
    if json.get("deprecated"):
        date_deprecated = json.get("date_deprecated")
        # Use modification date for deprecation date if not already set
        deprecated = date_deprecated or json.get("modified")
    dataset = {
        "metadata_owner": _convert_metadata_owner(json),
        "data_catalog": json.get("data_catalog", {}).get("identifier"),
        "cumulation_started": json.get("date_cumulation_started"),
        "cumulation_ended": json.get("date_cumulation_ended"),
        "cumulative_state": json.get("cumulative_state"),
        "created": json.get("date_created", '2024-11-27T06:32:47Z'),
        "deprecated": deprecated,
        "state": json.get("state"),
        "last_cumulative_addition": json.get(
            "date_last_cumulative_addition"
        ),
        "id": json.get("identifier"),
        "api_version": json.get("api_meta", {}).get("version", 1),
        "preservation": _convert_preservation(json),
        "modified": json.get('date_modified', '2024-11-27T06:32:47Z')
    }

    research_dataset = json.get("research_dataset", {})
    dataset |= {
            "persistent_identifier": research_dataset.get(
                "preferred_identifier"
            ),
            "title": research_dataset.get("title"),
            "description": research_dataset.get("description"),
            "issued": research_dataset.get("issued"),
            "keyword": research_dataset.get("keyword") or [],
            "bibliographic_citation": research_dataset.get(
                "bibliographic_citation"
            ),
            "actors": _convert_actors(research_dataset),
            "provenance": [
                _convert_provenance(v)
                for v in research_dataset.get("provenance", [])
            ],
            "projects": [
                _convert_project(v)
                for v in research_dataset.get("is_output_of", [])
            ],
            "field_of_science": [
                _convert_reference(v)
                for v in research_dataset.get("field_of_science", [])
            ],
            "theme": [
                _convert_reference(v)
                for v in research_dataset.get("theme", [])
            ],
            "language": [
                _convert_reference(v, preferred_label="title")
                for v in research_dataset.get("language", [])
            ],
            "infrastructure": [
                _convert_reference(v)
                for v in research_dataset.get("infrastructure", [])
            ],
            "spatial": [
                _convert_spatial(v)
                for v in research_dataset.get("spatial", [])
            ],
            "temporal": [
                _convert_temporal(v)
                for v in research_dataset.get("temporal", [])
            ],
            "other_identifiers": [
                _convert_other_identifier(v)
                for v in research_dataset.get("other_identifier", [])
            ],
            "relation": [
                _convert_relation(v)
                for v in research_dataset.get("relation", [])
            ],
            "remote_resources": [
                _convert_remote_resource(v)
                for v in research_dataset.get("remote_resources", [])
            ],
            "fileset": _convert_fileset(
                research_dataset,
                metax,
                json.get('identifier')
            ),
            "version": research_dataset.get("version")
        }

    if access_rights := research_dataset.get("access_rights"):
        dataset["access_rights"] = {
            "license": [
                    _convert_license(license)
                    for license in access_rights.get("license", [])
                ],
            "description": access_rights.get("description"),
            "available": access_rights.get("available"),
        }
    else:
        dataset["access_rights"] = None

    return dataset


def convert_file(json, research_dataset_file={}) -> MetaxFile:
    """Converts Metax V2 file to Metax V3 file. If a value is not
    defined in V2 payload, the value is not icluded in the output.
    Except the characteristics extension is alway added.

    :param dict json: Metax V2 file as a JSON
    :param dict research_dataset_file: V2 dataset has research_dataset
    field which has information about files. Then information is in V3
    included to the file datatype. If the research dataset contains some
    relevant file information for the FDPAS services it is included here.
    :returns: Metax V3 file
    """
    # Metax V2 has two places for the file format:
    # * `file_format`
    # * `file_characteristics.file_format`
    #
    # The first one can always be set.
    # The second one can only be set if
    # `file_characteristics.format_version` has a valid value.
    #
    # Metax V3 only has `file_characteristics.file_format`. Therefore, remove
    # `file_format` in V3 -> V2 conversion as we can't meaningfully derive
    # it from V3 data.

    file_metadata: MetaxFile = {
        "id": json.get("identifier"),
        "storage_identifier": json.get("identifier"),
        "pathname": json.get("file_path"),
        "filename": json.get("file_name"),
        "size": json.get("byte_size"),
        # FIXME: 'checksum' is required in both V2 and V3, and can never be
        # None
        "checksum": _convert_checksum_v2_to_v3(json.get("checksum")),
        "storage_service": FILE_STORAGE_V2_TO_STORAGE_SERVICE_V3.get(
            json.get("file_storage", {}).get("identifier")
        ),
        "csc_project": json.get("project_identifier"),
        "frozen": json.get("file_frozen"),
        "modified": json.get("file_modified"),
        "removed": json.get("removed"),
        "published": json.get("date_created"),
        "dataset_metadata": {
            "title": research_dataset_file.get("title"),
            "file_type": research_dataset_file.get("file_type"),
            "use_category": research_dataset_file.get("use_category"),
        },
        "characteristics": _convert_file_characteristics(
            json.get("file_characteristics")
        ),
        "characteristics_extension": None
    }
    
    file_metadata["characteristics_extension"] = json.get(
        "file_characteristics_extension"
    )

    return file_metadata


def _convert_preservation(json):
    return {
        "contract": json.get("contract", {}).get("identifier"),
        "id": json.get("preservation_identifier"),
        "state": json.get("preservation_state") if json.get("preservation_state") is not None else -1,
        "description": json.get("preservation_description"),
        "reason_description": json.get("preservation_reason_description"),
        "dataset_version": { # TODO: preservation_status is missing from V3, it's probably added in near future
            'id': json.get("preservation_dataset_version",{}).get("identifier"),
            'persistent_identifier': json.get("preservation_dataset_version",{}).get("preferred_identifier"),
            'preservation_state': json.get("preservation_dataset_version",{}).get("preservation_state")
            if json.get("preservation_dataset_version",{}).get("preservation_state")
            is not None else -1
        }
    }


def _convert_csc_project(json, metax, dataset_id):
    if files := json.get("files", []):
        return (
            files[0].get("details", {}).get("project_identifier")
        )
    if directories := json.get("directories", []):
        return (
            directories[0]
            .get("details", {})
            .get("project_identifier")
        )
    if metax is not None and dataset_id is not None:
        for file in metax.get_dataset_files(dataset_id):
            return file["csc_project"]
    return None


def _convert_fileset(research_dataset, metax, dataset_id):
    return {
        "csc_project": _convert_csc_project(
            research_dataset,
            metax,
            dataset_id
        ),
        "total_files_size": research_dataset.get('total_files_byte_size')
    }


def _convert_file_characteristics(file_characteristics) -> \
        Optional[MetaxFileCharacteristics]:
    if not file_characteristics:
        return None

    file_format_version: MetaxFileFormatVersion = {
        "pref_label": file_characteristics.get("title"),
        "file_format": file_characteristics.get("file_format"),
        "format_version": file_characteristics.get("format_version"),
    }

    file_chars: MetaxFileCharacteristics = {
        "file_created": file_characteristics.get("file_created"),
        "encoding": file_characteristics.get("encoding"),
        "csv_has_header": file_characteristics.get("csv_has_header"),
        "csv_quoting_char": file_characteristics.get("csv_quoting_char"),
        "csv_delimiter": file_characteristics.get("csv_delimiter"),
        "csv_record_separator": file_characteristics.get(
            "csv_record_separator"
        ),
        "file_format_version": (
            file_format_version if len(file_format_version) > 0 else None
        ),
    }
    return file_chars


def _convert_license(license: dict) -> dict:
    url = license.get("identifier")
    if not url:
        url = (
            "http://uri.suomi.fi/codelist/fairdata/"
            + "license/code/notspecified"
        )
    return {
        "url": url,
        "custom_url": license.get("license", None),
        "title": license.get("title"),
        "description": license.get("description"),
    }


def _convert_metadata_owner(json):
    user = json.get("metadata_provider_user")
    org = json.get("metadata_provider_org") or json.get("metadata_owner_org")
    if user is None and org is None:
        return None
    return {"user": user, "organization": org}


def _convert_homepage(homepage):
    if not homepage:
        return None
    return {
        "title": homepage.get("title"),
        "url": homepage.get("identifier")
    }


def _convert_organization(organization: dict) -> Optional[dict]:
    """Convert organization from V2 dict to V3 dict."""
    if not organization:
        return None
    val = {
        "pref_label": organization.get("name"),
        "email": organization.get("email"),
        "homepage": _convert_homepage(organization.get("homepage")),
        # A duplicate definition because https://gitlab.ci.csc.fi/fairdata/
        # fairdata-metax-v3/-/blob/master/src/apps/core/models/
        # legacy_converter.py#L399 uses some conditional logic which I
        # (Milla) didn't bother to add here. External id is supported
        # because admin rest api uses it and when V3 is in use, and
        # there is a possibility that this can be a useful field in V3.
        "url": organization.get("identifier"),
        "external_identifier": organization.get("identifier"),
    }

    parent = _convert_organization(organization.get("is_part_of"))
    val["parent"] = parent
    return val


def _convert_actor(actor: dict, roles=None) -> Optional[dict]:
    """Convert actor from V2 dict (optionally with roles) to V3 dict."""
    val = {}
    typ = actor.get("@type")
    v2_org = None
    if typ == "Person":
        email = actor.get("email")
        val["person"] = {
            "name": actor.get("name"),
            "external_identifier": actor.get("identifier"),
            "email": email,
            "homepage": _convert_homepage(actor.get("homepage")),
        }
        if parent := actor.get("member_of"):
            v2_org = parent
    elif typ == "Organization":
        v2_org = actor

    if v2_org:
        val["organization"] = _convert_organization(v2_org)
    if roles:
        # Assign actor roles, not allowed for e.g. provenance actor
        val["roles"] = roles
    return val


def _convert_actors(research_dataset) -> list:
    """Collect V2 actors from dataset and convert to V3 actor dicts."""
    actors_data = []  # list of dicts with actor as "actor"
    # and list of roles as "roles"
    roles = ["creator", "publisher", "curator",
             "contributor", "rights_holder"]
    for role in roles:
        # Flatten actors list and add role data
        role_actors = research_dataset.get(role, [])
        if isinstance(role_actors, dict):
            # Publisher is dictionary instead of list
            role_actors = [role_actors]
        for actor in role_actors:
            actor_match = None  # Combine identical actors if found
            for other in actors_data:
                if other["actor"] == actor:
                    actor_match = other
                    actor_match["roles"].append(role)
                    actor_match["duplicates"].append(actor)
                    break
            if not actor_match:
                actors_data.append(
                    {"actor": actor, "roles": [role], "duplicates": []}
                )
    adapted = []
    for actor in actors_data:
        adapted_actor = _convert_actor(actor["actor"], roles=actor["roles"])
        if adapted_actor:
            adapted.append(adapted_actor)
        for dup in actor["duplicates"]:
            # Actor may have been annotated, copy values to its duplicates
            dup.update(copy.deepcopy(actor["actor"]))
    return adapted


def _convert_spatial(spatial: dict) -> Optional[dict]:
    if not spatial:
        return None
    obj = {
        "reference": spatial.get("place_uri"),
        "geographic_name": spatial.get("geographic_name"),
        "full_address": spatial.get("full_address"),
        "altitude_in_meters": spatial.get("alt"),
    }
    return obj


def _convert_temporal(temporal: dict) -> Optional[dict]:
    if not temporal:
        return None
    start_date = temporal.get("start_date")
    end_date = temporal.get("end_date")
    return {
        "start_date": start_date,
        "end_date": end_date,
        "temporal_coverage": temporal.get("temporal_coverage"),
    }


def _convert_concept(concept: dict) -> Optional[dict]:
    if not concept:
        return None
    return {
        "pref_label": concept.get("pref_label"),
        "definition": concept.get("definition"),
        "concept_identifier": concept.get("identifier"),
        "in_scheme": concept.get("in_scheme"),
    }


def _convert_variable(variable: dict) -> dict:
    return {
        "pref_label": variable.get("pref_label"),
        "description": variable.get("description"),
        "concept": _convert_concept(variable.get("concept")),
        "universe": _convert_concept(variable.get("universe")),
        "representation": variable.get("representation"),
    }


def _convert_provenance(provenance: dict) -> dict:
    return {
        "title": provenance.get("title"),
        "description": provenance.get("description"),
        "preservation_event": _convert_reference(
            provenance.get("preservation_event")
        ),
        "temporal": _convert_temporal(provenance.get("temporal")),
        "outcome_description": provenance.get("outcome_description"),
        "spatial": _convert_spatial(provenance.get("spatial")),
        "event_outcome": _convert_reference(provenance.get("event_outcome")),
        "lifecycle_event": _convert_reference(
            provenance.get("lifecycle_event")
        ),
        "variables": [
            _convert_variable(var) for var in provenance.get("variable", [])
        ],
        "is_associated_with": [
            _convert_actor(actor)
            for actor in provenance.get("was_associated_with", [])
        ],
    }


def _convert_reference(ref, preferred_label="pref_label"):
    if not ref:
        return None
    return {
        "id": ref.get("id"),
        "url": ref.get("identifier"),
        "in_scheme": ref.get("in_scheme"),
        "pref_label": ref.get(preferred_label),
    }


def _convert_project(project: dict) -> dict:
    val = {
        "title": project.get("name"),
        "project_identifier": project.get("identifier"),
        "participating_organizations": [
            _convert_organization(org)
            for org in project.get("source_organization")
        ],
    }
    funder_type_data = None
    if funder_type := project.get("funder_type"):
        funder_type_data = _convert_reference(funder_type)
    funding_identifier = project.get("has_funder_identifier")
    funding_agencies = project.get("has_funding_agency", [None])
    val["funding"] = [
        {
            "funder": {
                "organization": _convert_organization(org),
                "funder_type": funder_type_data,
            },
            "funding_identifier": funding_identifier,
        }
        for org in funding_agencies
    ]
    return val


def _convert_other_identifier(other_identifier: dict) -> dict:
    return {
        "notation": other_identifier.get("notation"),
        "identifier_type": _convert_reference(other_identifier.get("type")),
    }


def _convert_entity(entity: dict) -> dict:
    return {
        "title": entity.get("title"),
        "description": entity.get("description"),
        "entity_identifier": entity.get("identifier"),
        "type": _convert_reference(entity.get("type")),
    }


def _convert_remote_url(url_data: dict) -> Optional[str]:
    if not url_data:
        return None
    url = url_data.get("identifier")
    if not url:
        return None
    return url


def _convert_relation(relation: dict) -> dict:
    return {
        "entity": _convert_entity(relation.get("entity")),
        "relation_type": _convert_reference(relation.get("relation_type")),
    }


def _convert_checksum_v2_to_v3(
    checksum: dict, value_key="value"
) -> Optional[str]:
    # TODO: Should be asked why this format was chosen for checksum
    if not checksum:
        return None
    algorithm = checksum.get("algorithm", "").lower().replace("-", "")
    value = checksum.get(value_key, "").lower()
    return f"{algorithm}:{value}"


def _convert_remote_resource(resource: dict) -> dict:
    title = None
    if v2_title := resource.get("title"):
        title = {"en": v2_title}

    description = None
    if v2_description := resource.get("description"):
        description = {"en": v2_description}

    use_category = None
    if v2_use_category := resource.get("use_category"):
        use_category = _convert_reference(v2_use_category)

    file_type = None
    if v2_file_type := resource.get("file_type"):
        file_type = _convert_reference(v2_file_type)

    access_url = _convert_remote_url(resource.get("access_url"))
    download_url = _convert_remote_url(resource.get("download_url"))

    return {
        "title": title,
        "description": description,
        "checksum": _convert_checksum_v2_to_v3(
            resource.get("checksum"), value_key="checksum_value"
        ),
        "mediatype": resource.get("mediatype"),
        "use_category": use_category,
        "file_type": file_type,
        "access_url": access_url,
        "download_url": download_url,
    }
