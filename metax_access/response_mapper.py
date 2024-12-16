"""Mapper for Metax responses."""

def map_file(metax_file):
     return {
          "id": metax_file['id'],
          "pathname": metax_file['pathname'],
          "filename": metax_file['filename'],
          "size": metax_file['size'],
          "checksum": metax_file['checksum'],
          "csc_project": metax_file['csc_project'],
          "storage_service": metax_file["storage_service"],
          # as of now 17.12.-24, the structure pf the dataset_metadata is not documented anywhere in V3
          # so this is a guess.
          "dataset_metadata": {
               "use_category": {
                    "identifier": metax_file["dataset_metadata"]["use_category"]["identifier"],
                    "pref_label": metax_file["dataset_metadata"]["use_category"]["pref_label"]
                    if "pref_label" in metax_file["dataset_metadata"]["use_category"].keys()
                    else None
               } if metax_file["dataset_metadata"]["use_category"] is not None else None
          } if metax_file["dataset_metadata"] is not None else None,
          "characteristics": {
               # if something breaks (e.g. in the e2e tests) this field used to contain pref_label
               # field. It was not needed in the UTs so it is not included anymore.
               "file_format_version": {
                    "file_format": metax_file['characteristics']['file_format_version']['file_format'],
                    "format_version": metax_file['characteristics']['file_format_version']['format_version'],
               } if metax_file['characteristics']['file_format_version'] is not None else None,
               "encoding": metax_file['characteristics']['encoding'],
               "csv_delimiter": metax_file['characteristics']['csv_delimiter'],
               "csv_record_separator": metax_file['characteristics']['csv_record_separator'],
               "csv_quoting_char": metax_file['characteristics']['csv_quoting_char'],
               "csv_has_header": metax_file["characteristics"]['csv_has_header'],
               "file_created": metax_file["characteristics"]['file_created']
          } if metax_file['characteristics'] is not None else None,
          "characteristics_extension": metax_file["characteristics_extension"]
     }

def map_contract(metax_contract):
        """TODO: Documentation. Has pretty much a 1-1
        mapping to the original contract.
        """
        return {
             'contract_identifier': metax_contract['contract_identifier'],
        'title': {
             'und': metax_contract['title']['und']
        },
        'quota': metax_contract['quota'],
        'organization': metax_contract["organization"],
        'contact': metax_contract["contact"],
        'related_service': metax_contract["related_service"],
        'description': {
             'und': metax_contract['description']['und']
        },
        'created': metax_contract['created'],
        'validity': metax_contract['validity'],
        }

def map_dataset(metax_dataset):
    """TODO: Documentation"""
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
            }
            if metax_dataset["fileset"]
            else None
        ),
        "preservation": {
            "state": metax_dataset["preservation"]["state"],
            "description": metax_dataset["preservation"]["description"],
            "reason_description": metax_dataset["preservation"][
                "reason_description"
            ],
            "dataset_version": {
                "id": metax_dataset["preservation"]["dataset_version"]["id"],
                "persistent_identifier": metax_dataset["preservation"][
                    "dataset_version"
                ]["persistent_identifier"],
                "preservation_state": metax_dataset["preservation"][
                    "dataset_version"
                ]["preservation_state"],
            },
            "contract": metax_dataset["preservation"]["contract"],
            "id": metax_dataset["preservation"]["id"],
        },
        "access_rights": {
            "license": (
                (
                    [
                        {"url": license["url"], "title": license["title"]}
                        for license in metax_dataset["access_rights"][
                            "license"
                        ]
                    ]
                )
                if metax_dataset["access_rights"] is not None
                else None
            )
        },
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
                        "temporal_coverage": p["temporal"][
                            "temporal_coverage"
                        ],
                        "start_date": p["temporal"]["start_date"],
                        "end_date": p["temporal"]["end_date"],
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
                "is_associated_with": _map_actors(p["is_associated_with"]),
                "preservation_event": (
                    {"pref_label": p["preservation_event"]["pref_label"]}
                    if p["preservation_event"] is not None
                    else None
                ),
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
                "organization": metax_dataset["metadata_owner"][
                    "organization"
                ],
                "user": metax_dataset["metadata_owner"]["user"],
            }
            if metax_dataset["metadata_owner"] is not None
            else None
        ),
        "data_catalog": metax_dataset["data_catalog"],
    }


def _map_actors(actors):
    # TODO: Not working nicely with Nones/nulls.
    # Something wrong with the normalization.
    if actors == []:
        return []
    return [
        {
            "roles": actor["roles"] if actor.get("roles") else [],
            "person": (
                {
                    "name": actor["person"]["name"],
                    "external_identifier": actor["person"][
                        "external_identifier"
                    ],
                    "email": actor["person"]["email"],
                }
                if actor.get("person")
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
                if actor.get("organization")
                else None
            ),
        }
        for actor in actors
    ]
