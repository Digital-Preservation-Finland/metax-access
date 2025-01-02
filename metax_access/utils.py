import copy


def remove_none(json):
    """Removes ``None`` values from the converted fields.
    If a fields gets a `Ǹone`` value it was not defined in source and is
    removed from the output.
    :param dict json:
    :returns: dict without ``None`` values.
    """
    processed_json = {k: v for k, v in json.items() if v is not None}
    for k, v in processed_json.items():
        if type(v) is dict:
            processed_json[k] = remove_none(v)
        elif type(v) is list:
            processed_json[k] = [
                remove_none(item) if type(item) is dict else item for item in v
            ]
        else:
            processed_json[k] = v
    return {k: v for k, v in processed_json.items() if v != {}}


def update_nested_dict(original, update):
    """Update nested dictionary.

    The keys of update dictionary are appended to
    original dictionary. If original already contains the key, it will be
    overwritten. If key value is dictionary, the original value is updated with
    the value from update dictionary.

    :param original: Original dictionary
    :param update: Dictionary that contains only key/value pairs to be updated
    :returns: Updated dictionary
    """
    updated_dict = copy.deepcopy(original)

    if original is None:
        return update

    for key in update:
        if key in original and isinstance(update[key], dict):
            updated_dict[key] = update_nested_dict(original[key], update[key])
        else:
            updated_dict[key] = update[key]

    return updated_dict
