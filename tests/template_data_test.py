import pytest

from metax_access.template_data import (CONTRACT,
                                        DATASET,
                                        FILE)
from metax_access.response_mapper import (map_contract,
                                          map_dataset,
                                          map_file)

def test_CONTRACT_is_valid():
    try:
        map_contract(CONTRACT)
    except KeyError:
        pytest.fail("Template contract must contain all keys.")
    
def test_DATASET_is_valid():
    try:
        map_dataset(DATASET)
    except KeyError:
        pytest.fail("Template dataset must contain all keys.")

def test_FILE_is_valid():
    try:
        map_file(FILE)
    except KeyError:
        pytest.fail("Template file must contain all keys.")
    
