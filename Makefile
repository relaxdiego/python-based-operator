.PHONY: debug dependencies history image install reset rollback status uninstall upgrade
.DEFAULT_GOAL := install

ifndef dev
	override DEV_OPTION =
	override IN_DEV_MODE = "\b"
else
	override DEV_OPTION = --set dev=true
	override IN_DEV_MODE = "IN DEV MODE"
endif

OPERATOR_RELEASE_NAME := test
CRD_RELEASE_NAME := prometheus-cluster-crd
ns ?= prometheus-operator
tag ?= ""
rev ?=

debug:
	helm install --debug --dry-run prometheus-cluster-crd charts/prometheus-cluster-crd/ 2>&1
	@echo "--------------------"
	helm install --debug --dry-run ${OPERATOR_RELEASE_NAME} charts/prometheus-operator/ 2>&1

dependencies: src/dev-requirements.txt .last-pip-sync

history:
	@helm history ${CRD_RELEASE_NAME}
	@helm history ${OPERATOR_RELEASE_NAME} --namespace=${ns}

image: .last-docker-build
	@echo -n

install: .last-docker-push
	@(test -n ${tag} && echo "Using image: ${tag}") || \
	 (echo "The tag argument is missing. See README for guidance" && exit 1)
	@(helm status ${CRD_RELEASE_NAME} 1>/dev/null 2>&1 && \
		echo "${CRD_RELEASE_NAME} already installed. Try 'make upgrade' instead") || \
	 (echo "Installing ${CRD_RELEASE_NAME}" && \
		 helm install --atomic ${CRD_RELEASE_NAME} charts/prometheus-cluster-crd/)
	@(helm status ${OPERATOR_RELEASE_NAME} --namespace=${ns} 1>/dev/null 2>&1 && \
		echo "'${OPERATOR_RELEASE_NAME}' Prometheus Operator already installed in the '${ns}' namespace. Try 'make upgrade' instead") || \
	 (echo "Installing '${OPERATOR_RELEASE_NAME}' Prometheus Operator in the '${ns}' namespace" ${IN_DEV_MODE} "\b. If the namespace does not exist, it will be created"; \
		helm install --atomic ${DEV_OPTION} --set image.repository=${tag} --namespace=${ns} --create-namespace ${OPERATOR_RELEASE_NAME} charts/prometheus-operator/)

reset: uninstall
	@rm -v -f .last-*

rollback:
	@(helm status ${CRD_RELEASE_NAME} 1>/dev/null 2>&1 && \
		echo "Rolling back ${CRD_RELEASE_NAME}" && \
		helm rollback --wait ${CRD_RELEASE_NAME} ${rev})
	@(helm status ${OPERATOR_RELEASE_NAME} --namespace=${ns} 1>/dev/null 2>&1 && \
		echo "Rolling back '${OPERATOR_RELEASE_NAME}' Prometheus Operator in the '${ns}' namespace." && \
		helm rollback --wait --namespace=${ns} ${OPERATOR_RELEASE_NAME} ${rev})

status:
	@helm status ${CRD_RELEASE_NAME}
	@helm status ${OPERATOR_RELEASE_NAME} --namespace=${ns}

uninstall:
	@(helm status ${CRD_RELEASE_NAME} 1>/dev/null 2>&1 && \
		echo "Uninstalling ${CRD_RELEASE_NAME}" && \
		helm uninstall ${CRD_RELEASE_NAME}) || \
	 (echo "${CRD_RELEASE_NAME} not installed. Skipping.")
	@(helm status ${OPERATOR_RELEASE_NAME} --namespace=${ns} 1>/dev/null 2>&1 && \
		echo "Uninstalling '${OPERATOR_RELEASE_NAME}' Prometheus Operator from the '${ns}' namespace. The namespace will be left alone." && \
		helm uninstall ${OPERATOR_RELEASE_NAME} --namespace=${ns}) || \
	 (echo "'${OPERATOR_RELEASE_NAME}' Prometheus Operator not installed in the '${ns}' namespace. Skipping.")

upgrade: .last-docker-push
	@(test -n ${tag} && echo "Using image: ${tag}") || \
	 (echo "The tag argument is missing. See README for guidance" && exit 1)
	@(helm status ${CRD_RELEASE_NAME} 1>/dev/null 2>&1 && \
		echo "Upgrading ${CRD_RELEASE_NAME}" && \
		helm upgrade --atomic ${CRD_RELEASE_NAME} charts/prometheus-cluster-crd) || \
	 (echo "${CRD_RELEASE_NAME} not installed. Run 'make install' first." && exit 1)
	@(helm status ${OPERATOR_RELEASE_NAME} --namespace=${ns} 1>/dev/null 2>&1 && \
		echo "Upgrading '${OPERATOR_RELEASE_NAME}' Prometheus Operator in the '${ns}' namespace" ${IN_DEV_MODE} "\b." && \
		helm upgrade --atomic ${DEV_OPTION} --set image.repository=${tag} --namespace=${ns} ${OPERATOR_RELEASE_NAME} charts/prometheus-operator/) || \
	 (echo "'${OPERATOR_RELEASE_NAME}' Prometheus Operator not installed in the '${ns}' namespace. Run make 'make install' first." && exit 1)

.last-pip-sync: src/dev-requirements.txt src/requirements.txt
	cd src && pip-sync dev-requirements.txt requirements.txt | tee ../.last-pip-sync

ifndef dev
.last-docker-build: Dockerfile LICENSE src/**/* src/requirements.txt src/dev-requirements.txt
	docker build -t ${tag} . 2>&1 | tee .last-docker-build
	@(grep -E "(Error response from daemon|returned a non-zero code)" .last-docker-build 1>/dev/null && rm -f .last-docker-build && echo "Error building container image" && exit 1) || exit 0

.last-docker-push: .last-docker-build
	@(test -n ${tag} && echo "Using image: ${tag}") || \
	 (echo "The tag argument is missing. See README for guidance" && exit 1)
	@test -f .last-docker-build || (echo "Last container image build was unsuccessful. Exiting." && exit 1)
	docker push ${tag} | tee .last-docker-push
else
.last-docker-build:
.last-docker-push:
endif

src/dev-requirements.txt: src/dev-requirements.in src/requirements.txt
	cd src && pip-compile dev-requirements.in

src/requirements.txt: src/setup.py
	cd src && pip-compile
