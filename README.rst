Metax access library
===================================================
Library for accessing Metax.

Installation
------------
On Centos 7 siptools_research can be installed from `DPres RPM repository <https://dpres-rpms.csc.fi/>`_::

   yum install metax-acess

Usage
-----

Testing
-------
Install required RPM packages::

   yum install libxslt-devel libxml2-devel openssl-devel mongodb-server gcc ImageMagick dpres-xml-schemas

Create and activate virtualenv::

   virtualenv venv
   source venv/bin/activate

Luigi will not install with old versions of pip, so upgrade pip::

   pip install --upgrade pip

Install required python packages for testing::

   pip install -r requirements_dev.txt

Run tests::

   make test

or run one of the integration tests::

   py.test -v tests/integration_tests/metax_integration_test.py


Building
--------
Build RPM::

   make rpm

Generating documentation
------------------------
Documentation for modules is automatically generated from docstrings using Sphinx (`https://wiki.csc.fi/KDK/PythonKoodinDokumentointi <https://wiki.csc.fi/KDK/PythonKoodinDokumentointi>`_)::

   cd doc/
   make html
