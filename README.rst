Metax access library
===================================================
Library for accessing Metax.

Installation
------------
On Centos 7 metax-access can be installed from `DPres RPM repository <https://dpres-rpms.csc.fi/>`_::

   yum install metax-acess

Usage
-----

Testing
-------
Install required RPM packages::

   yum install libxslt-devel libxml2-devel openssl-devel gcc

Create and activate virtualenv::

   virtualenv venv
   source venv/bin/activate

Luigi will not install with old versions of pip, so upgrade pip::

   pip install --upgrade pip

Install required python packages for testing::

   pip install -r requirements_dev.txt

Run tests::

   make test


Building
--------
Build RPM::

   make rpm

Generating documentation
------------------------
Documentation for modules is automatically generated from docstrings using Sphinx (`https://wiki.csc.fi/KDK/PythonKoodinDokumentointi <https://wiki.csc.fi/KDK/PythonKoodinDokumentointi>`_)::

   cd doc/
   make html
