FROM python:3.8.3-alpine3.12 as tester

WORKDIR /prometheus-operator

ADD ./src/ .
ADD .flake8 .

RUN pip3 install -r dev-requirements.txt

# TODO: Run unit tests here

# TODO: Submit test artifacts somewhere

# Remove files not needed for the final image
RUN rm -rf tests
RUN rm -rf *.egg-info
RUN rm -f dev-requirements.*
RUN rm -f .flake*

#
# FINAL IMAGE
#

FROM python:3.8.3-alpine3.12

WORKDIR /prometheus-operator

COPY --from=tester /prometheus-operator/ .

# We are using requirements.txt to constrain the dependency versions to the
# ones that we have tested with so as the lessen the build and deployment
# variables and make our deployments more deterministic.
RUN pip3 install -c requirements.txt .

ENTRYPOINT ["prometheus-operator"]
