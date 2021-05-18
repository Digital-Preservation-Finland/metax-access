DESTDIR ?= /
ETC = ${DESTDIR}/etc
PREFIX ?= /usr
PYTHON ?= python3

install:
	# Cleanup temporary files
	rm -f INSTALLED_FILES

	# Copy config file to /etc
	mkdir -p "${ETC}"
	cp include/etc/metax.cfg ${ETC}/

	# Use Python setuptools
	python3 ./setup.py install -O1 --prefix="${PREFIX}" --root="${DESTDIR}" --record=INSTALLED_FILES

github:
	python3 -mvenv venv; \
	    source venv/bin/activate; \
	    pip install --upgrade pip setuptools; \
	    pip install -r requirements_dev.txt; \
	    pip install .; \
	    if [ ! -f ~/.metax.cfg ]; then \
	    	cp include/etc/metax.cfg ~/.metax.cfg; \
	    fi

test:
	${PYTHON} -m pytest -svvvv \
	    --junitprefix=dpres-siptools-research --junitxml=junit.xml \
	    tests/unit_tests

coverage:
	${PYTHON} -m pytest tests --cov=metax_access --cov-report=html
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

rpm3: clean
	create-archive.sh
	preprocess-spec-m4-macros.sh include/rhel8
	build-rpm.sh

.PHONY: doc
doc:
	PYTHONPATH="../" make -C doc html
