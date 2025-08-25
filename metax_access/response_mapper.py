"""Mapper for Metax responses."""

from __future__ import annotations
from collections.abc import Iterable

from metax_access.response import (
    MetaxAccessRights,
    MetaxActor,
    MetaxContract,
    MetaxDataFieldBase,
    MetaxDataset,
    MetaxDirectoryFiles,
    MetaxFile,
    MetaxFileCharacteristics,
    MetaxFileDatasetMetadata,
    MetaxFileDatasetMetadataEntry,
    MetaxFileSet,
    MetaxMetadataOwner,
    MetaxMinFile,
    MetaxParentDirectory,
    MetaxPreservation,
    MetaxProvenance,
)


def map_directory_files(
    metax_directory_files: MetaxDirectoryFiles,
) -> MetaxDirectoryFiles:
    """Maps a metax directory file response to a minimum response
    required by the FDPAS services.
    """
    files: list[MetaxMinFile] = [
        {
            "id": file["id"],
            "filename": file["filename"],
            "size": file["size"],
        }
        for file in metax_directory_files["files"]
    ]

    parent_directory: MetaxParentDirectory | None = None
    if (input_directory := metax_directory_files.get("directory")) is not None:
        parent_directory = {"pathname": input_directory["pathname"]}

    return {
        "directory": parent_directory,
        "files": files,
        "directories": [
            {
                "name": directory["name"],
                "size": directory["size"],
                "file_count": directory["file_count"],
                "pathname": directory["pathname"],
            }
            for directory in metax_directory_files.get("directories", [])
        ],
    }


def map_file(metax_file: MetaxFile) -> MetaxFile:
    """Maps a Metax file response to a minimum response
    required by the FDPAS services.
    """

    use_category: MetaxFileDatasetMetadataEntry | None = None

    # dataset metadata field is only included when file is queried
    # related to the dataset. e.g. get dataset files method. Otherwise
    # Metax won't include it to the response.
    if (input_data := metax_file.get("dataset_metadata")) is not None:
        if (input_use := input_data.get("use_category")) is not None:
            use_category = {
                "pref_label": input_use.get("pref_label"),
                "url": input_use.get("url"),
            }

    dataset_metadata: MetaxFileDatasetMetadata = {"use_category": use_category}

    characteristics: MetaxFileCharacteristics = {
        "file_format_version": {
            "file_format": None,
            "format_version": None,
        },
        "encoding": None,
        "csv_delimiter": None,
        "csv_record_separator": None,
        "csv_quoting_char": None,
        "csv_has_header": None,
    }

    if (input_char := metax_file.get("characteristics")) is not None:
        if (input_format := input_char.get("file_format_version")) is not None:
            characteristics["file_format_version"] = {
                "file_format": input_format.get("file_format"),
                "format_version": input_format.get("format_version"),
            }

        for key in [
            "encoding",
            "csv_delimiter",
            "csv_record_separator",
            "csv_quoting_char",
            "csv_has_header",
        ]:
            characteristics[key] = input_char.get(key)

    return {
        "id": metax_file["id"],
        "storage_identifier": metax_file["storage_identifier"],
        "pathname": metax_file["pathname"],
        "filename": metax_file["filename"],
        "size": metax_file["size"],
        "checksum": metax_file["checksum"],
        "csc_project": metax_file["csc_project"],
        "storage_service": metax_file["storage_service"],
        "dataset_metadata": dataset_metadata,
        "characteristics": characteristics,
        "characteristics_extension": metax_file.get(
            "characteristics_extension"
        ),
        "pas_compatible_file": metax_file.get("pas_compatible_file"),
        "non_pas_compatible_file": metax_file.get("non_pas_compatible_file"),
    }


def map_contract(metax_contract: MetaxContract) -> MetaxContract:
    """Maps a Metax contract response to a minimum response
    required by the FDPAS services.
    """
    return {
        "id": metax_contract["id"],
        "title": {"und": (metax_contract["title"].get("und"))},
        "quota": metax_contract["quota"],
        "organization": metax_contract["organization"],
        "contact": metax_contract["contact"],
        "related_service": metax_contract["related_service"],
        "description": (
            {"und": metax_contract["description"].get("und")}
            if metax_contract["description"] is not None
            else {"und": None}
        ),
        "created": metax_contract["created"],
        "validity": metax_contract["validity"],
    }


def map_dataset(metax_dataset: MetaxDataset) -> MetaxDataset:
    """Maps a Metax dataset response to a minimum response
    required by the FDPAS services.
    """

    fileset: MetaxFileSet = (
        {
            "total_files_size": metax_dataset["fileset"]["total_files_size"],
            "csc_project": metax_dataset["fileset"]["csc_project"],
            "total_files_count": metax_dataset["fileset"]["total_files_count"],
        }
        if metax_dataset["fileset"]
        else {
            "total_files_size": 0,
            "csc_project": None,
            "total_files_count": 0,
        }
    )

    preservation: MetaxPreservation = {
        "state": -1,
        "description": None,
        "reason_description": None,
        "dataset_version": {
            "id": None,
            "persistent_identifier": None,
            "preservation_state": None,
        },
        "contract": None,
    }

    if (input_pres := metax_dataset["preservation"]) is not None:
        preservation["state"] = input_pres["state"]
        preservation["description"] = input_pres["description"]
        preservation["reason_description"] = input_pres["reason_description"]
        preservation["contract"] = input_pres["contract"]

        if (dataset_ver := input_pres.get("dataset_version")) is not None:
            preservation["dataset_version"] = {
                "id": dataset_ver["id"],
                "persistent_identifier": dataset_ver["persistent_identifier"],
                "preservation_state": dataset_ver["preservation_state"],
            }

    access_rights: MetaxAccessRights | None = None

    if metax_dataset["access_rights"] is not None:
        access_rights = {
            "license": [
                {
                    "url": license["url"] or "",
                    "pref_label": license["pref_label"],
                }
                for license in metax_dataset["access_rights"]["license"]
            ]
        }

    def _map_provenance(member: MetaxProvenance) -> MetaxProvenance:
        p: MetaxProvenance = {
            "title": member["title"],
            "description": member["description"],
            "outcome_description": member["outcome_description"],
            "temporal": None,
            "event_outcome": None,
            "lifecycle_event": None,
        }

        if (temp := member.get("temporal")) is not None:
            p["temporal"] = {"start_date": temp["start_date"]}

        if (outcome := member.get("event_outcome")) is not None:
            p["event_outcome"] = {
                "pref_label": outcome["pref_label"],
                "url": outcome["url"],
            }

        if (event := member.get("lifecycle_event")) is not None:
            p["lifecycle_event"] = {"pref_label": event["pref_label"]}

        return p

    provenance: list[MetaxProvenance] = [
        _map_provenance(member) for member in metax_dataset["provenance"]
    ]

    metadata_owner: MetaxMetadataOwner = {
        # TODO: `metadata_owner.user` and
        # `metadata_owner.organization` might be hidden in some
        # datasets, so they then set to `None`. Does it make
        # sense fetch those datasets? Can it be avoided?
        "organization": (metax_dataset["metadata_owner"].get("organization")),
        "user": metax_dataset["metadata_owner"].get("user"),
    }

    return {
        "id": metax_dataset["id"],
        "created": metax_dataset["created"],
        "title": metax_dataset["title"],
        "description": metax_dataset["description"],
        "modified": metax_dataset["modified"],
        "fileset": fileset,
        "preservation": preservation,
        "access_rights": access_rights,
        "version": metax_dataset["version"],
        "language": [
            {"url": language["url"]} for language in metax_dataset["language"]
        ],
        "persistent_identifier": metax_dataset["persistent_identifier"],
        "issued": metax_dataset["issued"],
        "actors": _map_actors(metax_dataset["actors"]),
        "keyword": metax_dataset["keyword"],
        "theme": [
            {"pref_label": theme["pref_label"]}
            for theme in metax_dataset["theme"]
        ],
        "spatial": [
            {"geographic_name": location["geographic_name"]}
            for location in metax_dataset["spatial"]
        ],
        "field_of_science": [
            {"pref_label": field["pref_label"]}
            for field in metax_dataset["field_of_science"]
        ],
        "provenance": provenance,
        "metadata_owner": metadata_owner,
        "data_catalog": metax_dataset["data_catalog"],
    }


def _map_actors(actors: Iterable[MetaxActor]) -> list[MetaxActor]:
    """A helper method for mapping actors in a dataset."""

    def _map_actor(actor: MetaxActor) -> MetaxActor:
        act: MetaxActor = {
            "roles": actor.get("roles", []),
            "person": None,
            "organization": None,
        }

        if (person := actor.get("person")) is not None:
            act["person"] = {
                "name": person["name"],
                "external_identifier": person["external_identifier"],
                # TODO: `email` might be hidden in some datasets, so
                # it is then set to `None`. Does it make sense fetch
                # those datasets? Can it be avoided?
                "email": person.get("email"),
            }

        if (org := actor.get("organization")) is not None:
            parent: MetaxDataFieldBase | None = None
            if org["parent"] is not None:
                parent = {"pref_label": org["parent"]["pref_label"]}

            act["organization"] = {
                "pref_label": org["pref_label"],
                "url": org["url"],
                "external_identifier": org["external_identifier"],
                "parent": parent,
            }

        return act

    return [_map_actor(actor) for actor in actors]
