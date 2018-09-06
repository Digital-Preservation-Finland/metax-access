DESTDIR ?= /
PREFIX ?= /usr
ETC=${DESTDIR}/etc
SHAREDIR=${DESTDIR}${PREFIX}/share/metax_access
VAR=${DESTDIR}/var

LOGDIR=${VAR}/log/metax_access
PROCESSINGDIR=${VAR}/spool/metax_access

TESTER=blahblah

install:
	# Cleanup temporary files
	rm -f INSTALLED_FILES

	# Create log, share and processing directories
	mkdir -p "${LOGDIR}"
	mkdir -p "${PROCESSINGDIR}"
	mkdir -p "${SHAREDIR}"
	mkdir -p "${ETC}"

	# Use Python setuptools
	python ./setup.py install -O1 --prefix="${PREFIX}" --root="${DESTDIR}" --record=INSTALLED_FILES
	cat INSTALLED_FILES | sed 's/^/\//g' >> INSTALLED_FILES

testa:
	echo $(TESTER)

test:
	py.test -svvvv --junitprefix=dpres-siptools-research --junitxml=junit.xml tests/unit_tests

coverage:
	py.test tests --cov=metax_access --cov-report=html --ignore tests/integration_tests/ --ignore tests/workflow/report_preservation_status_test.py
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
