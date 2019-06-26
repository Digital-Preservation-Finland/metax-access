DESTDIR ?= /
ETC=${DESTDIR}/etc
PREFIX ?= /usr

install:
	# Cleanup temporary files
	rm -f INSTALLED_FILES

	# Copy config file to /etc
	mkdir -p "${ETC}"
	cp include/etc/metax.cfg ${ETC}/

	# Use Python setuptools
	python ./setup.py install -O1 --prefix="${PREFIX}" --root="${DESTDIR}" --record=INSTALLED_FILES

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
	rm -rf doc/build doc/source/modules

rpm: clean
	create-archive.sh
	preprocess-spec-m4-macros.sh include/rhel7
	build-rpm.sh

.PHONY: doc
doc:
	PYTHONPATH="../" make -C doc html
