.PHONY: dependencies image deploy deploy-common deploy-dev reset uninstall
.DEFAULT_GOAL := image

tag ?= ""

export IMAGE_TAG = ${tag}
export SERVICEACCOUNT_NAME = "python-based-operator-serviceaccount"

dependencies: .last-pip-tools-install src/requirements-dev.txt .last-pip-sync

image: .last-docker-build
	@echo -n

deploy: deploy-common .last-docker-build .last-docker-push
	@scripts/render templates/operator.yml > .tmp/yml/operator.yml || exit 1
	@kubectl apply -f .tmp/yml/

deploy-common:
	@rm -rf .tmp/yml && mkdir -p .tmp/yml
	@scripts/render templates/crd.yml  > .tmp/yml/crd.yml  || exit 1
	@scripts/render templates/ns.yml   > .tmp/yml/ns.yml   || exit 1
	@scripts/render templates/rbac.yml > .tmp/yml/rbac.yml || exit 1

deploy-dev: deploy-common .last-pip-sync
	@kubectl apply -f .tmp/yml/
	@rm -rf .tmp/serviceaccount && mkdir -p .tmp/serviceaccount
	@kubectl config view --minify | grep server | cut -f 2- -d ":" | tr -d " " \
		| xargs printf "export server_addr=%s\n" > .tmp/serviceaccount/generate_dev_kubeconfig.sh
	@kubectl get serviceaccount python-based-operator-serviceaccount -n python-based-operator -o go-template='{{ (index .secrets 0).name }}' \
		| xargs -n1 kubectl get secret -n python-based-operator -o go-template='{{ (index .data "token") }}' \
		| base64 --decode \
		| xargs printf "export token=%s\n" >> .tmp/serviceaccount/generate_dev_kubeconfig.sh
	@kubectl get serviceaccount python-based-operator-serviceaccount -n python-based-operator -o go-template='{{ (index .secrets 0).name }}' \
		| xargs -n1 kubectl get secret -n python-based-operator -o go-template='{{ (index .data "namespace") }}' \
		| base64 --decode \
		| xargs printf "export namespace=%s\n" >> .tmp/serviceaccount/generate_dev_kubeconfig.sh
	@kubectl get serviceaccount python-based-operator-serviceaccount -n python-based-operator -o go-template='{{ (index .secrets 0).name }}' \
		| xargs -n1 kubectl get secret -n python-based-operator -o go-template='{{ (index .data "ca.crt") }}' \
		| xargs -n1 printf "export ca_crt=%s\n" >> .tmp/serviceaccount/generate_dev_kubeconfig.sh
	@echo "scripts/render templates/dev_kubeconfig.yml" >> .tmp/serviceaccount/generate_dev_kubeconfig.sh
	@chmod +x .tmp/serviceaccount/generate_dev_kubeconfig.sh
	@.tmp/serviceaccount/generate_dev_kubeconfig.sh > .tmp/serviceaccount/dev_kubeconfig.yml
	@python-based-operator

reset: uninstall
	@rm -v -f .last-*

uninstall:
	@kubectl delete -f .tmp/yml/ || true

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
	(pyenv -v && pyenv rehash) || true

.last-pip-tools-install:
	@(pip-compile --version 1>/dev/null 2>&1 || pip --disable-pip-version-check install "pip-tools>=5.3.0,<5.4" || echo "pip-tools install error") | tee .last-pip-tools-install
	@(grep "pip-tools install error" .last-pip-tools-install 1>/dev/null 2>&1 && rm -f .last-pip-tools-install && exit 1) || true
	(pyenv -v && pyenv rehash) || true

src/requirements-dev.txt: .last-pip-tools-install src/requirements-dev.in src/requirements.txt
	cd src && CUSTOM_COMPILE_COMMAND="make dependencies" pip-compile requirements-dev.in

src/requirements.txt: .last-pip-tools-install src/setup.py
	cd src && CUSTOM_COMPILE_COMMAND="make dependencies" pip-compile
