PROJECT=benchmarkweb

PYHOME=.venv/bin
NOSE=$(PYHOME)/nosetests
FLAKE8=$(PYHOME)/flake8
PYTHON=$(PYHOME)/python

all: lint test

.PHONY: clean
clean:
	rm -rf MANIFEST dist/* $(PROJECT).egg-info .coverage
	find . -name '*.pyc' -delete
	rm -rf .venv

test: .venv
	@echo Starting tests...
	@$(NOSE) --with-coverage --cover-package $(PROJECT)

lint: .venv
	@$(FLAKE8) $(PROJECT) --ignore E501 && echo OK

.venv:
	sudo apt-get install -qy python-virtualenv
	virtualenv .venv
	$(PYTHON) setup.py develop

serve:
	.venv/bin/python serve.py

release: clean
	tar --exclude-vcs -cvzf ../benchmkark-gui.tar.gz *

