"""Sample contract response data."""

BASE = {
    "id": "test_contract_id",
    "title": {"und": "Test Contract Title"},
    "quota": 111205,
    "organization": {
        "name": "Test organization",
        "organization_identifier": "test_org_identifier",
    },
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
    "description": {"und": "Description of unknown length"},
    "created": "test_created_date",
    "validity": {"start_date": "2014-01-17", "end_date": None},
}
