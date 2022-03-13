DOCKER_REVISION ?= testing-$(USER)
DOCKER_TAG = docker-push.ocf.berkeley.edu/ocfapi:$(DOCKER_REVISION)
HOST=127.0.0.1
PORT=8000

.PHONY: cook-image
cook-image:
	docker build --pull -t $(DOCKER_TAG) .

.PHONY: push-image
push-image:
	docker push $(DOCKER_TAG)

venv: requirements.txt requirements-dev.txt
	python3 -m venv venv && \
	. venv/bin/activate && \
	pip install --upgrade "pip>=20.3" && \
	pip install -r requirements.txt -r requirements-dev.txt

.PHONY: dev
dev:
	chmod u+x venv/bin/activate && \
	. venv/bin/activate && \
	cd app && \
	python -m uvicorn main:app --reload --host $(HOST) --port $(PORT)

.PHONY: test
test: venv unit-test

.PHONY: unit-test
unit-test:
	chmod u+x venv/bin/activate && \
	. venv/bin/activate && \
	cd app && \
	python -m pytest

.PHONY: update-requirements
update-requirements: venv
	$(BIN)/upgrade-requirements
	sed -i 's/^ocflib==.*/ocflib/' requirements.txt
