Metax access library
====================
Library for accessing Metax.

Installation
------------
Clone this repository and install with pip::

   pip install ./metax-access/

Usage
-----
A simple commandline interface can be used for posting, retrieving, or deleting metadata. For example to view metadata of dataset::

   metax_access --host https://metax-test.csc.fi -u tpas -p password get dataset 1

Alternatively ``host``, ``user``, and ``password`` may be to configuration file ``/home/vagrant/metax.cfg``::

   [metax]
   host=https://metax-test.csc.fi
   user=tpas
   password=password


which can be used wifh ``-c`` flag ::

   metax_access -c /home/vagrant/metax.cfg get dataset 1

For more information see::

   metax_access -h



Testing
-------

Create and activate virtualenv::

   virtualenv venv
   source venv/bin/activate

Upgrade pip::

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

Documentation for modules is automatically generated from docstrings using `Sphinx <https://www.sphinx-doc.org/en/master/>`_::

   make doc
