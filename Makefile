PROJECT=benchmarkweb

PYHOME=.venv/bin
NOSE=$(PYHOME)/nosetests
FLAKE8=$(PYHOME)/flake8
PYTHON=$(PYHOME)/python


all: lint test

.PHONY: clean npm
clean:
	rm -rf $(PROJECT)/static/react/node_modules
	rm -rf MANIFEST dist/* $(PROJECT).egg-info .coverage
	find . -name '*.pyc' -delete
	rm -rf .venv

test: .venv
	@echo Starting tests...
	@$(NOSE) --with-coverage --cover-package $(PROJECT)

lint: .venv
	@$(FLAKE8) $(PROJECT) --ignore E501 && echo OK

.venv:
	sudo apt-get install -qy python-virtualenv libpq-dev python-dev libyaml-dev
	virtualenv .venv
	$(PYHOME)/pip install --upgrade setuptools
	$(PYTHON) setup.py develop

npm:
	cd $(PROJECT)/static/react; npm install

serve: .venv
	.venv/bin/pserve development.ini

release: clean
	tar --exclude-vcs -cvzf ../benchmark-web.tar.gz *
