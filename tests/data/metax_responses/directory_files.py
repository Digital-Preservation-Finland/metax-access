"""Sample directory files data."""

FULL = {
    "directory": {
        "storage_service": "test_storage_service",
        "csc_project": "test_project",
        "name": "Test_Name",
        "pathname": "/testdata/Test_Name/",
        "file_count": 13,
        "size": 23040,
        "created": "test_created_date",
        "modified": "test_modified_date",
        "dataset_metadata": None,
        "parent_url": "https://url_to/testdata/",
    },
    "directories": [
        {
            "storage_service": "test_storage_service",
            "csc_project": "test_project",
            "name": "baseline",
            "pathname": "/testdata/Test_Name/baseline/",
            "file_count": 6,
            "size": 11297,
            "created": "test_created_date",
            "modified": "test_modified_date",
            "dataset_metadata": None,
            "url": "https://url_to/testdata/baseline/",
        }
    ],
    "files": [
        {
            "id": "68d4bcea-a020-446d-b20d-3bf3e022b7ba",
            "storage_identifier": "683e4452104ea364728696f2244",
            "pathname": "/testdata/Test_Name/zero_size_file",
            "filename": "zero_size_file",
            "size": 0,
            "storage_service": "test_storage_service",
            "csc_project": "test_project",
            "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "frozen": "2025-06-03T00:39:46Z",
            "modified": "test_modified_date",
            "removed": None,
            "published": "2025-06-03T09:34:30Z",
            "user": "fd_test_fairdata_user",
            "dataset_metadata": None,
            "characteristics": None,
            "characteristics_extension": None,
            "pas_process_running": False,
            "pas_compatible_file": None,
            "non_pas_compatible_file": None,
        }
    ],
}

BASE = {
    "directory": {
        "storage_service": "test_storage_service",
        "csc_project": "test_project",
        "name": "Test_Name",
        "pathname": "/",
        "file_count": 0,
        "size": 0,
        "created": "test_created_date",
        "modified": "test_modified_date",
        "dataset_metadata": None,
        "parent_url": None,
    },
    "files": [],
    "directories": [],
}
