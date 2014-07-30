all:
	pip install -r requirements-devel.txt
	pyflakes libcloudvagrant

TESTS=${:libcloudvagrant}

check: all
	nosetests \
		--detailed-errors \
		--processes=-1 \
		--process-timeout=1200 \
		--stop \
		$(TESTS)

cover: all
	nosetests \
		--detailed-errors \
		--with-coverage \
		--cover-branches \
		--cover-erase \
		--cover-html \
		--cover-inclusive \
		--cover-package=libcloudvagrant \
		--cover-tests \
		$(TESTS)

lint: all
	pylint libcloudvagrant

clean:
	-git clean -dfx

dist: clean
	python setup.py sdist

distcheck: dist
	sh distcheck.sh

PYPI=${:https://testpypi.python.org/pypi}

upload: dist
	python setup.py sdist upload -r $(PYPI)
