"""Mapper for Metax responses."""


def map_directory_files(metax_directory_files):
    """Maps a metax directory file response to a minimum response
    required by the FDPAS services.
    """
    return {
        "directory": (
            {"pathname": metax_directory_files["directory"]["pathname"]}
            if metax_directory_files["directory"] is not None
            else None
        ),
        "files": [
            {
                "id": file["id"],
                "filename": file["filename"],
                "size": file["size"],
            }
            for file in metax_directory_files["files"]
        ],
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


def map_file(metax_file):
    """Maps a Metax file response to a minimum response
    required by the FDPAS services.
    """
    return {
        "id": metax_file["id"],
        "storage_identifier": metax_file["storage_identifier"],
        "pathname": metax_file["pathname"],
        "filename": metax_file["filename"],
        "size": metax_file["size"],
        "checksum": metax_file["checksum"],
        "csc_project": metax_file["csc_project"],
        "storage_service": metax_file["storage_service"],
        # dataset metadata field is only included when file is queried
        # related to the dataset. e.g. get dataset files method. Otherwise
        # Metax won't include it to the response.
        "dataset_metadata": (
            {
                "use_category": (
                    {
                        "pref_label": (
                            metax_file["dataset_metadata"]["use_category"][
                                "pref_label"
                            ]
                        ),
                        "url": metax_file["dataset_metadata"]["use_category"][
                            "url"
                        ],
                    }
                    if metax_file.get("dataset_metadata", {}).get(
                        "use_category"
                    )
                    is not None
                    else None
                )
            }
            if metax_file.get("dataset_metadata") is not None
            else {"use_category": None}
        ),
        "characteristics": (
            {
                "file_format_version": (
                    {
                        "file_format": metax_file["characteristics"][
                            "file_format_version"
                        ]["file_format"],
                        "format_version": metax_file["characteristics"][
                            "file_format_version"
                        ]["format_version"],
                    }
                    if metax_file["characteristics"]["file_format_version"]
                    is not None
                    else None
                ),
                "encoding": metax_file["characteristics"]["encoding"],
                "csv_delimiter": metax_file["characteristics"][
                    "csv_delimiter"
                ],
                "csv_record_separator": metax_file["characteristics"][
                    "csv_record_separator"
                ],
                "csv_quoting_char": metax_file["characteristics"][
                    "csv_quoting_char"
                ],
                "csv_has_header": metax_file["characteristics"][
                    "csv_has_header"
                ],
            }
            if metax_file["characteristics"] is not None
            else None
        ),
        "characteristics_extension": metax_file["characteristics_extension"],
        "pas_compatible_file": metax_file["pas_compatible_file"],
        "non_pas_compatible_file": metax_file["non_pas_compatible_file"],
    }


def map_contract(metax_contract):
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


def map_dataset(metax_dataset):
    """Maps a Metax dataset response to a minimum response
    required by the FDPAS services.
    """
    return {
        "id": metax_dataset["id"],
        "created": metax_dataset["created"],
        "title": metax_dataset["title"],
        "description": metax_dataset["description"],
        "modified": metax_dataset["modified"],
        "fileset": (
            {
                "total_files_size": metax_dataset["fileset"][
                    "total_files_size"
                ],
                "csc_project": metax_dataset["fileset"]["csc_project"],
                "total_files_count": metax_dataset["fileset"][
                    "total_files_count"
                ],
            }
            if metax_dataset["fileset"]
            else {
                "total_files_size": 0,
                "csc_project": None,
                "total_files_count": 0,
            }
        ),
        "preservation": (
            {
                "state": metax_dataset["preservation"]["state"],
                "description": metax_dataset["preservation"]["description"],
                "reason_description": metax_dataset["preservation"][
                    "reason_description"
                ],
                # This field is created when a dataset is preserved
                "dataset_version": (
                    {
                        "id": metax_dataset["preservation"]["dataset_version"][
                            "id"
                        ],
                        "persistent_identifier": metax_dataset["preservation"][
                            "dataset_version"
                        ]["persistent_identifier"],
                        "preservation_state": metax_dataset["preservation"][
                            "dataset_version"
                        ]["preservation_state"],
                    }
                    if "dataset_version" in metax_dataset["preservation"]
                    and metax_dataset["preservation"]["dataset_version"]
                    is not None
                    else {
                        "id": None,
                        "persistent_identifier": None,
                        "preservation_state": None,
                    }
                ),
                "contract": metax_dataset["preservation"]["contract"],
            }
            if metax_dataset["preservation"] is not None
            else {
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
        ),
        "access_rights": (
            {
                "license": [
                    {
                        "url": license["url"] or "",
                        "pref_label": license["pref_label"],
                    }
                    for license in metax_dataset["access_rights"]["license"]
                ]
            }
            if metax_dataset["access_rights"] is not None
            else None
        ),
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
        "provenance": [
            {
                "title": p["title"],
                "temporal": (
                    {
                        "start_date": p["temporal"]["start_date"]
                    }
                    if p["temporal"] is not None
                    else None
                ),
                "description": p["description"],
                "event_outcome": (
                    {
                        "pref_label": p["event_outcome"]["pref_label"],
                        "url": p["event_outcome"]["url"],
                    }
                    if p["event_outcome"] is not None
                    else None
                ),
                "outcome_description": p["outcome_description"],
                "lifecycle_event": (
                    {"pref_label": p["lifecycle_event"]["pref_label"]}
                    if p["lifecycle_event"] is not None
                    else None
                ),
            }
            for p in metax_dataset["provenance"]
        ],
        "metadata_owner": (
            {
                # TODO: `metadata_owner.user` and
                # `metadata_owner.organization` might be hidden in some
                # datasets, so they then set to `None`. Does it make
                # sense fetch those datasets? Can it be avoided?
                "organization": (
                    metax_dataset["metadata_owner"].get("organization")
                ),
                "user": metax_dataset["metadata_owner"].get("user"),
            }
        ),
        "data_catalog": metax_dataset["data_catalog"],
    }


def _map_actors(actors):
    """A helper method for mapping actors in a dataset."""
    return [
        {
            "roles": actor["roles"] if actor.get("roles") else [],
            "person": (
                {
                    "name": actor["person"]["name"],
                    "external_identifier": actor["person"][
                        "external_identifier"
                    ],
                    # TODO: `email` might be hidden in some datasets, so
                    # it is then set to `None`. Does it make sense fetch
                    # those datasets? Can it be avoided?
                    "email": actor["person"].get("email"),
                }
                if actor.get("person") is not None
                else None
            ),
            "organization": (
                {
                    "pref_label": actor["organization"]["pref_label"],
                    "url": actor["organization"]["url"],
                    "external_identifier": actor["organization"][
                        "external_identifier"
                    ],
                    "parent": (
                        {
                            "pref_label": actor["organization"]["parent"][
                                "pref_label"
                            ]
                        }
                        if actor["organization"]["parent"] is not None
                        else None
                    ),
                }
                if actor.get("organization") is not None
                else None
            ),
        }
        for actor in actors
    ]
