DESTDIR ?= /
PREFIX ?= /usr

install:
	# Cleanup temporary files
	rm -f INSTALLED_FILES

	# Use Python setuptools
	python ./setup.py install -O1 --prefix="${PREFIX}" --root="${DESTDIR}" --record=INSTALLED_FILES
	cat INSTALLED_FILES | sed 's/^/\//g' >> INSTALLED_FILES

test:
	py.test -svvvv --junitprefix=dpres-siptools-research --junitxml=junit.xml tests/unit_tests

coverage:
	py.test tests --cov=metax_access --cov-report=html
	coverage report -m
	coverage html
	coverage xml

clean: clean-rpm
	find . -iname '*.pyc' -type f -delete
	find . -iname '__pycache__' -exec rm -rf '{}' \; | true
	rm -rf coverage.xml htmlcov junit.xml .coverage

clean-rpm:
	rm -rf rpmbuild

rpm: clean
	create-archive.sh
	preprocess-spec-m4-macros.sh include/rhel7
	build-rpm.sh

.PHONY: doc
doc:
	make -C doc html
