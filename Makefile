DOCKER_REVISION ?= testing-$(USER)
DOCKER_TAG = docker-push.ocf.berkeley.edu/ocfapi:$(DOCKER_REVISION)
HOST = 127.0.0.1
PORT = 8001

.PHONY: cook-image
cook-image:
	docker build --pull -t $(DOCKER_TAG) .

.PHONY: push-image
push-image:
	docker push $(DOCKER_TAG)

venv: | venv/pyvenv.cfg

venv/pyvenv.cfg: requirements.txt requirements-dev.txt
	python3 -m venv venv && \
	chmod u+x venv/bin/activate && \
	. venv/bin/activate && \
	pip install --upgrade "pip>=20.3" && \
	pip install -r requirements.txt -r requirements-dev.txt && \
	pre-commit install

.PHONY: dev
dev: venv
	@. venv/bin/activate && \
	cd app && \
	python -m uvicorn main:app --reload --host $(HOST) --port $(PORT)

.PHONY: test
test: venv
	@. venv/bin/activate && \
	cd app && \
	python -m pytest && \
	cd .. && \
	venv/bin/check-requirements

.PHONY: update-requirements
update-requirements: venv
	@venv/bin/upgrade-requirements
	@sed -i 's/^ocflib==.*/ocflib/' requirements.txt
	@make venv
