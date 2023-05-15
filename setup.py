"""Install metax-access package."""
from setuptools import setup, find_packages


def main():
    """Install metax-access."""
    setup(
        name='metax-access',
        packages=find_packages(exclude=['tests', 'tests.*']),
        include_package_data=True,
        python_requires='>=3.6',
        setup_requires=['setuptools_scm'],
        use_scm_version=True,
        install_requires=[
            "requests",
            "lxml",
            "click"
        ],
        entry_points={
            'console_scripts': [
                'metax_access = metax_access.__main__:main'
            ]
        }
    )


if __name__ == '__main__':
    main()
