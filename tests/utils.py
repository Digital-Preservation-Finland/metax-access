import copy
import contextlib
from tests.metax_data.contracts import CONTRACT_RESPONSE
from tests.metax_data.datasets import BASE_DATASET_RESPONSE
from tests.metax_data.files import BASE_FILE_RESPONSE
from tests.metax_data.directory_files import BASE_DIRECTORY_FILES_RESPONSE

def _create_merged_dict(data, **kwargs):
    """
    Create a new dict with fields merged from the given keyword arguments

    '__' can be used to separate nested dicts as with Metax API. For example,
    parameter
    `preservation__state="foo"`
    will be equivalent to `data['preservation']['state'] = "foo"`.
    """
    data = copy.deepcopy(data)

    # Use '__' as separator for nested dicts.
    # For example, 'preservation__state="foo"' will be equivalent to
    # `dataset["preservation"]["state"] = "foo"`
    for key, value in kwargs.items():
        fields = key.split("__")
        field = None
        field_dict = data

        while len(fields) > 1:
            field = fields.pop(0)
            with contextlib.suppress(ValueError):
                # Cast to integer in case one was provided; this allows
                # modifying lists
                field = int(field)

            field_dict = field_dict[field]

        last_field = fields.pop()

        # Ensure that the field we're trying to set actually exists.
        # We can do this as we deal with complete responses in Metax V3.
        assert last_field in field_dict, f"Field {key} does not exist!"

        field_dict[last_field] = value

    return data


def create_test_file(**kwargs):
    return _create_merged_dict(BASE_FILE_RESPONSE, **kwargs)


def create_test_dataset(**kwargs):
    return _create_merged_dict(BASE_DATASET_RESPONSE, **kwargs)


def create_test_contract(**kwargs):
    return _create_merged_dict(CONTRACT_RESPONSE, **kwargs)

def create_test_directory_files(**kwargs):
    return _create_merged_dict(BASE_DIRECTORY_FILES_RESPONSE, **kwargs)