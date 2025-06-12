"""Sample metax_access directory files response data."""

FULL = {
    "directory": {"pathname": "/testdata/Test_Name/"},
    "files": [
        {
            "id": "68d4bcea-a020-446d-b20d-3bf3e022b7ba",
            "filename": "zero_size_file",
            "size": 0,
        },
    ],
    "directories": [
        {
            "name": "baseline",
            "size": 11297,
            "file_count": 6,
            "pathname": "/testdata/Test_Name/baseline/",
        }
    ],
}

BASE = {
    "directory": {"pathname": "/"},
    "files": [],
    "directories": [],
}
