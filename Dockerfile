FROM python:3.8.3-alpine3.12

ADD . /prometheus-operator

# We are using requirements.txt to constrain the dependency versions to the
# once that we have tested with so as the lessen the build and deployment
# variables and make our deployments more deterministic.
RUN pip3 install -c /prometheus-operator/requirements.txt /prometheus-operator

ENTRYPOINT ["prometheus_operator"]
