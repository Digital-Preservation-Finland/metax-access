"""Payload converter from Metax v3 to Metax v2."""
from metax_access.v2_to_v3_converter import \
    FILE_STORAGE_V2_TO_STORAGE_SERVICE_V3

# Invert the `storage_service` <-> `file_storage_identifier` dict
STORAGE_SERVICE_V3_TO_FILE_STORAGE_V2 = {
    value: key for key, value in FILE_STORAGE_V2_TO_STORAGE_SERVICE_V3.items()
}


def convert_contract(json):
    """Converts Metax V3 contract to Metax V2 contract.

    :param dict json: Metax V3 contract as a JSON.
    :returns: Metax V2 contract as a dictionary
    """
    return remove_none(
        {
            "date_modified": json.get("modified"),
            "date_created": json.get("created"),
            "service_created": json.get("service"),
            "removed": json.get("removed"),
            "contract_json": {
                "quota": json.get("quota"),
                "title": json.get("title", {}).get("und"),
                "contact": json.get("contact"),
                "created": json.get("created"),
                "modified": json.get("modified"),
                "validity": json.get("validity"),
                "identifier": json.get("contract_identifier"),
                "description": json.get("description", {}).get("und"),
                "organization": json.get("organization"),
                "related_service": json.get("related_service"),
            },
        }
    )


def convert_dataset(json):
    """Converts V3 type dataset to V2 dataset.
    Only contract id of the dataset is updated by the services so
    this method only converts that to V2 format.
    Other fields are not converted.

    :param dict json: Metax V3 dataset as a JSON.
    :returns: Metax V2 dataset as a dictionary
    """
    return {
        "contract": {
            "identifier": json.get('preservation', {}).get('contract')
        }
    }


def convert_file(json):
    """
    Convert Metax file from V3 to V2. This is necessary for data submission
    (eg. POST and PATCH) to Metax during the transition period
    """
    checksum = None
    if json.get("checksum"):
        checksum = {
            "algorithm": json.get("checksum", "")
            .split(":")[0]
            .upper(),
            "value": json.get("checksum", "").split(":")[-1],
            # 'checked' field does not exist in Metax V3. Just spitball
            # a valid timestamp here.
            "checked": json.get("modified")
        }

    return {"identifier": json.get("id"),
            "file_storage": {
                "identifier": STORAGE_SERVICE_V3_TO_FILE_STORAGE_V2.get(
                    json.get("storage_service")
                )
            },
            "file_path": json.get("pathname"),
            "file_name": json.get("filename"),
            "byte_size": json.get("size"),
            "checksum": checksum,
            # Assume the service who created the Metax file metadata is the
            # same as the service. The only exception appears to be Metax's own
            # test data, which shouldn't matter here.
            "service_created": (
                "tpas" if json.get("storage_service") == "pas"
                else json.get("storage_service")
            ),
            "project_identifier": json.get("csc_project"),
            "file_frozen": json.get("frozen"),
            "file_modified": json.get("modified"),
            "removed": json.get("removed"),
            "date_created": json.get("published"),
            "file_format": json.get("file_format"),
            "file_characteristics": {
                "encoding": json.get("characteristics", {}).get(
                    "encoding"
                ),
                "csv_has_header": json.get("characteristics", {}).get(
                    "csv_has_header"
                ),
                "csv_quoting_char": json.get("characteristics", {}).get(
                    "csv_quoting_char"
                ),
                "csv_delimiter": json.get("characteristics", {}).get(
                    "csv_delimiter"
                ),
                "csv_record_separator": json.get(
                    "characteristics", {}
                ).get("csv_record_separator"),
                "title": json.get("characteristics", {})
                .get("file_format_version", {})
                .get("pref_label"),
                "file_format": json.get("characteristics", {})
                .get("file_format_version", {})
                .get("file_format"),
                "format_version": json.get("characteristics", {})
                .get("file_format_version", {})
                .get("format_version"),
            },
            "file_characteristics_extension": json.get(
                "characteristics_extension"
            ),
            # TODO: File creation date field does not exist in Metax V3.
            # '_file_created' field is used during transition period and should
            # be removed after the migration is complete.
            "file_uploaded": json.get("_file_uploaded")
        }
