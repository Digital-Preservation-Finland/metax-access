"""Install metax-access package."""
from setuptools import setup, find_packages

from version import get_version


def main():
    """Install metax-access."""
    setup(
        name='metax-access',
        packages=find_packages(exclude=['tests', 'tests.*']),
        include_package_data=True,
        version=get_version(),
        data_files=[('etc', ['include/etc/metax.cfg'])],
        install_requires=[
            "requests",
            "lxml",
            "argcomplete"
        ],
        entry_points={
            'console_scripts': [
                'metax_access = metax_access.__main__:main'
            ]
        }
    )


if __name__ == '__main__':
    main()
