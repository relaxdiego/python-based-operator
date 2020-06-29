.PHONY: clean clean-all image operator dev-operator dependencies
.DEFAULT_GOAL := dependencies

CHART_RELEASE_NAME := dev-9095562

ns ?= default
namespace ?= $(ns)


clean:
	@if microk8s.helm3 status --namespace=$(namespace) ${CHART_RELEASE_NAME} 1>/dev/null 2>&1 ; then microk8s.helm3 uninstall --namespace=$(namespace) ${CHART_RELEASE_NAME}; else echo 'Operator is not running in the $(namespace) namespace. Ignoring.'; exit 1; fi
	rm -f .last-helm-install .last-make-operator-run

clean-all: clean
	rm -f .last-*

image: .last-docker-push

dev-operator: dependencies
	@if [ -f '.last-make-operator-run' ]; then echo; echo "Operator already running. Run 'make clean' first to uninstall"; echo; exit 1; fi
	microk8s.helm3 install --atomic --set dev=true --namespace=$(namespace) ${CHART_RELEASE_NAME} helm/ 2>&1 | tee .last-helm-install
	@# If .last-helm-install does not contain "Error:", create .last-make-operator-run
	@grep "Error:" .last-helm-install 1>/dev/null || touch .last-make-operator-run
	@# If .last-helm-install contains "Error:", delete .last-helm-install and .last-make-operator-run
	@grep -v "Error:" .last-helm-install 1>/dev/null || rm .last-helm-install .last-make-operator-run

operator: .last-helm-install
	@if [ -f '.last-make-operator-run' ]; then echo; echo "Operator already running. Run 'make clean' first to uninstall"; echo; exit 1; fi
	@# If .last-helm-install does not contain "Error:", create .last-make-operator-run
	@grep "Error:" .last-helm-install 1>/dev/null || touch .last-make-operator-run
	@# If .last-helm-install contains "Error:", delete .last-helm-install and .last-make-operator-run
	@grep -v "Error:" .last-helm-install 1>/dev/null || rm .last-helm-install .last-make-operator-run

.last-helm-install: .last-docker-push
	@if [ -z $(tag) ]; then echo; echo "tag argument is missing. See README for guidance"; echo; exit 1; fi
	microk8s.helm3 install --atomic --set dev=$(dev) --set image.repository=$(tag) --namespace=$(namespace) ${CHART_RELEASE_NAME} helm/ 2>&1 | tee .last-helm-install

.last-docker-push: .last-docker-build
	docker push $(tag) | tee .last-docker-push

.last-docker-build: Dockerfile LICENSE prometheus_operator/* requirements.txt dev-requirements.txt
	@if [ -z $(tag) ]; then echo; echo "tag argument is missing. See README for guidance"; echo; exit 1; fi
	docker build -t $(tag) . | tee .last-docker-build

dependencies: dev-requirements.txt .last-dependencies-installation

dev-requirements.txt: dev-requirements.in requirements.txt
	pip-compile dev-requirements.in

requirements.txt: setup.py
	pip-compile

.last-dependencies-installation: dev-requirements.txt requirements.txt
	pip-sync dev-requirements.txt requirements.txt | tee .last-dependencies-installation
