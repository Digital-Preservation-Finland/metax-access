import pytest
from metax_access.response_mapper import (
    map_dataset,
    map_contract,
    map_file,
    map_directory_files,
)

from tests.metax_data.files import (
    BASE_FILE,
    BASE_FILE_RESPONSE,
    FILE_WITH_MINIMAL_CHARACTERISTICS_FIELD,
    FILE_WITH_MINIMAL_CHARACTERISTICS_FIELD_RESPONSE,
    FULL_FILE,
    FULL_FILE_RESPONSE,
)

from tests.metax_data.datasets import (
    BASE_DATASET,
    BASE_DATASET_RESPONSE,
    FULL_DATASET,
    FULL_DATASET_RESPONSE,
)

from tests.metax_data.contracts import CONTRACT, CONTRACT_RESPONSE

from tests.metax_data.directory_files import (
    BASE_DIRECTORY_FILES,
    BASE_DIRECTORY_FILES_RESPONSE,
    DIRECTORY_FILES,
    DIRECTORY_FILES_RESPONSE,
)


@pytest.mark.parametrize(
    ("input", "output"),
    [
        (BASE_DATASET, BASE_DATASET_RESPONSE),
        (FULL_DATASET, FULL_DATASET_RESPONSE),
    ],
)
def test_map_dataset(input, output):
    assert output == map_dataset(input)


@pytest.mark.parametrize(
    ("input", "output"),
    [
        (CONTRACT, CONTRACT_RESPONSE),
    ],
)
def test_map_contract(input, output):
    assert output == map_contract(input)


@pytest.mark.parametrize(
    ("input", "output"),
    [
        (BASE_FILE, BASE_FILE_RESPONSE),
        (FULL_FILE, FULL_FILE_RESPONSE),
        (
            FILE_WITH_MINIMAL_CHARACTERISTICS_FIELD,
            FILE_WITH_MINIMAL_CHARACTERISTICS_FIELD_RESPONSE,
        ),
    ],
)
def test_map_file(input, output):
    assert output == map_file(input)


@pytest.mark.parametrize(
    ("input", "output"),
    [
        (DIRECTORY_FILES, DIRECTORY_FILES_RESPONSE),
        (BASE_DIRECTORY_FILES, BASE_DIRECTORY_FILES_RESPONSE),
    ],
)
def test_map_directory_files(input, output):
    assert output == map_directory_files(input)
