"""Sample Metax contract data."""

# TODO: This is almost identical to metax_access.template_data.CONTRACT.
# The requirement for two almost identical test data cases should be 
# revisited at least in TPASPKT-1529.
BASE = {
    "id": "test_contract_id",
    "title": {"und": "Test Contract Title", "en": "Test Contract Title"},
    "description": {"und": "Description of unknown length"},
    "quota": 111205,
    "created": "test_created_date",
    "modified": "test_modified_date",
    "organization": {
        "name": "Test organization",
        "organization_identifier": "test_org_identifier",
    },
    "validity": {"start_date": "2014-01-17", "end_date": None},
    "contact": [
        {
            "name": "Contact Name",
            "email": "contact.email@csc.fi",
            "phone": "+358501231234",
        }
    ],
    "related_service": [
        {"identifier": "local:service:id", "name": "Name of Service"}
    ],
    "removed": None,
}
