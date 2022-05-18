from metax_access.utils import remove_redundant_dirs


def test_remove_redundant_dirs():
    """
    Test that redundant child directories are removed from the given list
    """
    before = [
        "/foo",
        "/bar",
        "/foo/bar",
        "/foo1",
        "/foo2/foo3",
        "/foo2/foo3/foo4"
    ]

    after = [
        "/bar",
        "/foo",
        "/foo1",
        "/foo2/foo3",
    ]

    assert remove_redundant_dirs(before) == after
