.PHONY: clean image operator

clean:
	@rm .last-helm-install .last-operator-install
	microk8s.helm3 uninstall dev

image: .last-docker-push

operator: .last-helm-install
	@if [ -f '.last-helm-install' ] && [ -f '.last-operator-install' ]; then echo; echo "Operator already running. Run make clean first to uninstall"; echo; exit 1; fi
	@touch .last-operator-install

.last-docker-push: .last-docker-build
	docker push $(tag) | tee .last-docker-push

.last-docker-build: Dockerfile prometheus_operator/*
	@if [ -z $(tag) ]; then echo; echo "tag argument is missing"; echo; exit 1; fi
	docker build -t $(tag) . | tee .last-docker-build

.last-helm-install: .last-docker-push
	microk8s.helm3 install --atomic --set image.repository=$(tag) dev helm/ | tee .last-helm-install
