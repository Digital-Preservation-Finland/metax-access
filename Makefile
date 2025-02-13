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
	${PYTHON} -m pytest tests/unit_tests -svvv --junitxml=junit.xml

coverage:
	${PYTHON} -m pytest tests --cov=metax_access --cov-fail-under=70 --cov-report=html
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

.PHONY: doc
doc:
	PYTHONPATH="../" make -C doc html
