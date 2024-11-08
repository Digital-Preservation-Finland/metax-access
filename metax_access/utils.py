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
                remove_none(item) if type(item) is dict else item
                for item in v
            ]
        else:
            processed_json[k] = v
    return {k: v for k, v in processed_json.items() if v != {}}
