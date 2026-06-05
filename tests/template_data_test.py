"""Tests for template_data module."""
from metax_access.response_mapper import map_contract, map_dataset, map_file
from metax_access.template_data import CONTRACT, DATASET, FILE


def test_contract_is_valid():
    """Test that template contract metadata contains correct data."""
    # The template contract metadata should contain enough data, so that
    # metax_access does not have to add any default values. It should
    # not contain any extra data which metax_access would ignore.
    # Therefore, the result from map_contract should be exactly same as
    # the original metadata.
    assert map_contract(CONTRACT) == CONTRACT


def test_dataset_is_valid():
    """Test that template dataset metadata contains correct data."""
    # The template dataset metadata should contain enough data, so that
    # metax_access does not have to add any default values. It should
    # not contain any extra data which metax_access would ignore.
    # Therefore, the result from map_dataset should be exactly same as
    # the original metadata.
    assert map_dataset(DATASET) == DATASET


def test_file_is_valid():
    """Test that template file metadata contains correct data."""
    # The template file metadata should contain enough data, so that
    # metax_access does not have to add any default values. It should
    # not contain any extra data which metax_access would ignore.
    # Therefore, the result from map_file should be exactly same as the
    # original metadata.
    assert map_file(FILE) == FILE
