"""Payload converter from Metax v3 to Metax v2."""


def convert_contract(json):
    """Converts Metax V3 contract to Metax V2 contract.

    :param dict json: Metax V3 contract as a JSON.
    :returns: Metax V2 contract as a dictionary
    """
    return {
        "date_modified": json.get("modified"),
        "date_created": json.get("created"),
        "service_created": json.get("service"),
        "removed": json.get("removed"),
        'contract_json': {
            "quota": json.get('quota'),
            "title": json.get('title', {}).get('und'),
            "contact": json.get('contact'),
            "created": json.get('created'),
            "modified": json.get('modified'),
            "validity": json.get('validity'),
            "identifier": json.get('contract_identifier'),
            "description": json.get('description', {}).get('und'),
            "organization": json.get('organization'),
            "related_service": json.get('related_service')
        }
    }


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
