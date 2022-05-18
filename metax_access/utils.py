"""Various utility functions"""
from pathlib import PurePath


def remove_redundant_dirs(paths):
    """
    Remove redundant directories from a list of paths.

    This means that child directories will be removed if a parent directory
    already exists in the list.
    """
    # Sort the directories. Parent directories will be listed first before
    # their children, meaning elimination becomes simple by comparing each
    # directory against the previous one.
    all_paths = sorted(paths)

    new_paths = []

    last_dir = None
    for path in all_paths:
        if last_dir is not None:
            try:
                PurePath(path).relative_to(last_dir)
                # Last path was a parent, skip this one
                continue
            except ValueError:
                new_paths.append(path)
        else:
            new_paths.append(path)

        last_dir = path

    return new_paths
