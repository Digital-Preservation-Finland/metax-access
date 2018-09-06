"""Install siptools-research package"""
from setuptools import setup, find_packages

from version import get_version


def main():
    """Install metax-access"""
    setup(
        name='metax-access',
        packages=find_packages(exclude=['tests', 'tests.*']),
        version=get_version(),
        install_requires=[
            "requests",
            "lxml",
            "scandir",
            "jsonschema",
            "wand",
            "iso-639"
        ],
        entry_points={
            'console_scripts': [
                'metax_access = metax_access.__main__:main'
            ]
        }
    )


if __name__ == '__main__':
    main()
