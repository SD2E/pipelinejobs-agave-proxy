CONTAINER_IMAGE=$(shell bash scripts/container_image.sh)
PYTHON ?= "python3"
PYTEST_OPTS ?= "-s"
PYTEST_DIR ?= "tests"
ABACO_DEPLOY_OPTS ?= "-p"
SCRIPT_DIR ?= "scripts"
PREF_SHELL ?= "bash"
ACTOR_ID ?=
NOCLEANUP ?= 0
GITREF=$(shell git rev-parse --short HEAD)
MESSAGEFILE ?=

.PHONY: tests container tests-local tests-reactor tests-deployed
.SILENT: tests container tests-local tests-reactor tests-deployed shell

all: image

image:
	abaco deploy -R -t $(GITREF) $(ABACO_DEPLOY_OPTS)

shell:
	bash $(SCRIPT_DIR)/run_container_process.sh bash

tests: tests-pytest tests-local

tests-pytest:
	bash $(SCRIPT_DIR)/run_container_process.sh $(PYTHON) -m "pytest" $(PYTEST_DIR) $(PYTEST_OPTS)

tests-local: tests-local-message01

tests-local-message01:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/message01.json

tests-deployed:
	bash $(SCRIPT_DIR)/run_abaco_message.sh tests/data/message02.json

tests-deployed-message:
	bash $(SCRIPT_DIR)/run_abaco_message.sh tests/data/$(MESSAGEFILE)

clean: clean-image clean-tests

clean-image:
	docker rmi -f $(CONTAINER_IMAGE)

clean-tests:
	rm -rf .hypothesis .pytest_cache __pycache__ */__pycache__ tmp.* *junit.xml

deploy:
	abaco deploy -t $(GITREF) $(ABACO_DEPLOY_OPTS) -U $(ACTOR_ID)

postdeploy:
	bash scripts/run_after_deploy.sh

nonce:
	bash scripts/nonces-new.sh

nonces:
	bash scripts/nonces-list.sh
