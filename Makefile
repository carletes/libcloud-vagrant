all:
	pip install -r requirements-devel.txt
	pyflakes libcloudvagrant

TESTS=${:libcloudvagrant}

# XXX Consider ``--processes=-1``
check: all
	py.test \
		--showlocals \
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
