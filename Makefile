# Makefile: build issueHistory.py
# Uses python virtualenv, see also:
# http://docs.python-guide.org/en/latest/dev/virtualenvs/

MODULES = qjira

all:
	@echo "Run from virtualenv"
	@echo "$$ source bin/activate"
	@echo "$$ make init"
	@echo "$$ make test"
	@echo "$$ deactivate"

_py27:
	virtualenv --python=python2.7 _py27
	cd _py27 && ln -s ../Makefile ../setup.py ../qjira ../tests .

_py3:
	virtualenv --python=python3 _py3
	cd _py3 && ln -s ../Makefile ../setup.py ../qjira ../tests .

init: 
	python setup.py develop

build:
	python setup.py build

clean:
	python setup.py clean
	for dir in $(MODULES); do \
		$(MAKE) -C $$dir $@; \
	done
	rm -fr build qjira.egg-info

clean-all: clean
	rm -fr _py27
	rm -fr _py3

test:
	python setup.py build test

test-all: _py27 _py3
	pushd _py27 && source bin/activate && $(MAKE) test && deactivate && popd
	pushd _py3  && source bin/activate && $(MAKE) test && deactivate && popd

dist:
	python setup.py bdist

dist-all:
	python setup.py sdist

install:
	@echo run setuptools


.PHONY: all init build clean clean-all test test-all install dist dist-all
