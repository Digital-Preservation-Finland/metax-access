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

Copyright
---------
Copyright (C) 2019 CSC - IT Center for Science Ltd.

This program is free software: you can redistribute it and/or modify it under the terms
of the GNU Lesser General Public License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with
this program.  If not, see <https://www.gnu.org/licenses/>.
