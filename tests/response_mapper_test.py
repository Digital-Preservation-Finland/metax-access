import pytest
from metax_access.response_mapper import (
    map_dataset,
    map_contract,
    map_file,
    map_directory_files,
)

from tests.data.metax_access_responses import (
    files as metax_access_file,
    datasets as metax_access_dataset,
    directory_files as metax_access_directory_files,
    contracts as metax_access_contract
)
from tests.data.metax_responses import (
    files as metax_file,
    directory_files as metax_directory_files,
    contracts as metax_contract,
    datasets as metax_dataset
)


@pytest.mark.parametrize(
    ("input", "output"),
    [
        (metax_dataset.BASE, metax_access_dataset.BASE),
        (metax_dataset.FULL, metax_access_dataset.FULL),
    ],
)
def test_map_dataset(input, output):
    assert output == map_dataset(input)


@pytest.mark.parametrize(
    ("input", "output"),
    [
        (metax_contract.BASE, metax_access_contract.BASE),
    ],
)
def test_map_contract(input, output):
    assert output == map_contract(input)


@pytest.mark.parametrize(
    ("input", "output"),
    [
        (metax_file.BASE, metax_access_file.BASE),
        (metax_file.FULL, metax_access_file.FULL),
        (
            metax_file.MINIMAL_CHARACTERISTICS_FIELD,
            metax_access_file.MINIMAL_CHARACTERISTICS_FIELD,
        ),
    ],
)
def test_map_file(input, output):
    assert output == map_file(input)


@pytest.mark.parametrize(
    ("input", "output"),
    [
        (metax_directory_files.BASE, metax_access_directory_files.BASE),
        (metax_directory_files.FULL, metax_access_directory_files.FULL),
    ],
)
def test_map_directory_files(input, output):
    assert output == map_directory_files(input)
