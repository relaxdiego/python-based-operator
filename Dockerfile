#
# TESTER STAGE
#

FROM python:3.8.3-alpine3.12 as tester

WORKDIR /prometheus-operator

ADD ./src/ .
ADD .flake8 .

RUN apk update

# Install build essentials and group them as "build-essentials"
# These are needed by kubernetes-asyncio
RUN apk add --virtual build-essentials \
        build-base \
        gcc 

RUN pip install --upgrade pip
RUN pip install -r dev-requirements.txt

# TODO: Run unit tests here

# TODO: Submit test artifacts somewhere

#
# BUILDER STAGE
#

FROM python:3.8.3-alpine3.12 as builder

WORKDIR /prometheus-operator

COPY --from=tester /prometheus-operator/ .

RUN apk update

# Install build essentials and group them as "build-essentials"
# These are needed by kubernetes-asyncio
RUN apk add --virtual build-essentials \
        build-base \
        gcc

# Reference: https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
ENV VIRTUAL_ENV=/prometheus-operator/.venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip
# We are using requirements.txt to constrain the dependency versions to the
# ones that we have tested with so as the lessen the build and deployment
# variables and make our deployments more deterministic.
RUN pip3 install -c requirements.txt .

# Remove files not needed for the final image
RUN rm -rf tests
RUN rm -rf *.egg-info
RUN rm -f *requirements.*
RUN rm -f .flake*

#
# FINAL STAGE
#

FROM python:3.8.3-alpine3.12

WORKDIR /prometheus-operator

COPY --from=builder /prometheus-operator/ .

ENV VIRTUAL_ENV=/prometheus-operator/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENTRYPOINT ["prometheus-operator"]
