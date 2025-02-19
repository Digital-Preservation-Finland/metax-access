import copy


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


def extended_result(url, metax, params={}):
    """Handles paged queries by calling the next url.

    :param str url: The URL to make the query.
    :param obj metax: Metax instance to handle the queries.
    :param dict params: URL parameters for the query
    """
    result = []
    while url is not None:
        response = metax.get(url, params=params).json()
        url = response["next"]
        result.extend(response["results"])
    return result
