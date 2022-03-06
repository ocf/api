DOCKER_REVISION ?= testing-$(USER)
DOCKER_TAG = docker-push.ocf.berkeley.edu/ocfapi:$(DOCKER_REVISION)

.PHONY: cook-image
cook-image:
	docker build --pull -t $(DOCKER_TAG) .

.PHONY: push-image
push-image:
	docker push $(DOCKER_TAG)

.PHONY: dev
dev:
	chmod u+x venv/bin/activate && . venv/bin/activate && python -m uvicorn app.main:app --reload
