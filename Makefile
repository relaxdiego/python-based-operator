.PHONY: dependencies image deploy reset uninstall
.DEFAULT_GOAL := image

tag ?= ""

dependencies: .last-pip-tools-install src/requirements-dev.txt .last-pip-sync

image: .last-docker-build
	@echo -n

deploy: .last-docker-build .last-docker-push
	@mkdir -p .tmp
	@IMAGE_TAG=${tag} \
		scripts/render templates/python-based-operator.yml > .tmp/python-based-operator.yml || exit 1
	@kubectl apply -f .tmp/python-based-operator.yml

reset: uninstall
	@rm -v -f .last-*

uninstall:
	@test -f .tmp/python-based-operator.yml && kubectl delete -f .tmp/python-based-operator.yml || true

.last-docker-build: Dockerfile LICENSE src/MANIFEST.in src/**/* src/requirements.txt src/requirements-dev.txt
	docker build -t ${tag} . 2>&1 | tee .last-docker-build
	@(grep -E "(Error response from daemon|returned a non-zero code)" .last-docker-build 1>/dev/null && rm -f .last-docker-build && echo "Error building image" && exit 1) || exit 0

.last-docker-push: .last-docker-build
	@(test -n ${tag} && echo "Using image: ${tag}") || \
	 (echo "The tag argument is missing. See README for guidance" && exit 1)
	@test -f .last-docker-build || (echo "Last container image build was unsuccessful. Exiting." && exit 1)
	 docker push ${tag} | tee .last-docker-push

.last-pip-sync: .last-pip-tools-install src/requirements-dev.txt src/requirements.txt
	cd src && pip-sync requirements-dev.txt requirements.txt | tee ../.last-pip-sync

.last-pip-tools-install:
	@(pip-compile --version 1>/dev/null 2>&1 || pip --disable-pip-version-check install "pip-tools>=5.3.0,<5.4" || echo "pip-tools install error") | tee .last-pip-tools-install
	@(grep "pip-tools install error" .last-pip-tools-install 1>/dev/null 2>&1 && rm -f .last-pip-tools-install && exit 1) || true
	@pyenv rehash

src/requirements-dev.txt: .last-pip-tools-install src/requirements-dev.in src/requirements.txt
	cd src && CUSTOM_COMPILE_COMMAND="make dependencies" pip-compile requirements-dev.in

src/requirements.txt: .last-pip-tools-install src/setup.py
	cd src && CUSTOM_COMPILE_COMMAND="make dependencies" pip-compile
