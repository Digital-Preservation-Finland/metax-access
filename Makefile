DESTDIR ?= /
ETC = ${DESTDIR}/etc
PREFIX ?= /usr
PYTHON ?= python3

install:
	# Cleanup temporary files
	rm -f INSTALLED_FILES

	# Use Python setuptools
	python3 ./setup.py install -O1 --prefix="${PREFIX}" --root="${DESTDIR}" --record=INSTALLED_FILES

github:
	python3 -mvenv venv; \
	    source venv/bin/activate; \
	    pip install --upgrade pip setuptools; \
	    pip install -r requirements_dev.txt; \
	    pip install .; \

clean: clean-rpm
	find . -iname '*.pyc' -type f -delete
	find . -iname '__pycache__' -exec rm -rf '{}' \; | true
	rm -rf coverage.xml htmlcov junit.xml .coverage

clean-rpm:
	rm -rf rpmbuild
	rm -rf doc/build doc/source/modules

.PHONY: doc
doc:
	PYTHONPATH="../" make -C doc html
