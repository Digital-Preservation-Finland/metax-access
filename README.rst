Metax access library
====================
Library for accessing Metax.

Installation
------------

Installation and usage requires Python 3.6 or newer.
The software is tested with Python 3.6 on Centos 7.x release.

Create a virtual environment::

   python3 -m venv venv

Run the following to activate the virtual environment::

   source venv/bin/activate

Install the required software with commands::

   pip install --upgrade pip setuptools
   pip install -r requirements_dev.txt
   pip install .

To deactivate the virtual environment, run ``deactivate``. To reactivate it, run the ``source`` command above.


Usage
-----
A simple commandline interface can be used for posting, retrieving, or deleting metadata. For example to view metadata of dataset::

   metax_access --url metax-test.csc.fi -u tpas -p password get dataset 1

Alternatively ``host``, ``user``, and ``password`` may be to configuration file ``~/.metax.cfg``::

   [metax]
   url=https://metax-test.csc.fi
   user=tpas
   password=password


which can be used wifh ``-c`` flag ::

   metax_access -c ~/.metax.cfg get dataset 1

For more information see::

   metax_access -h

Testing
-------

Run tests with::

   python3 -m pytest tests/

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
