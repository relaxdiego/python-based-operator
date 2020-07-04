#
# TESTER STAGE
#

FROM python:3.8.3-alpine3.12 as tester

WORKDIR /prometheus-operator-src

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

WORKDIR /prometheus-operator-src

COPY --from=tester /prometheus-operator-src/ .

RUN apk update

# Install build essentials and group them as "build-essentials"
# These are needed by kubernetes-asyncio
RUN apk add --virtual build-essentials \
        build-base \
        gcc \
        wget

# Reference: https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
ENV VIRTUAL_ENV=/prometheus-operator
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip
# We are using requirements.txt to constrain the dependency versions to the
# ones that we have tested with so as the lessen the build and deployment
# variables and make our deployments more deterministic.
RUN pip3 install -c requirements.txt .

# Install
RUN wget https://get.helm.sh/helm-v3.2.4-linux-amd64.tar.gz -O /tmp/helm.tar.gz 2>&1
RUN mkdir -p /tmp/helm
RUN tar -xvf /tmp/helm.tar.gz -C /tmp/helm
RUN cp /tmp/helm/linux-amd64/helm $VIRTUAL_ENV/bin

#
# FINAL STAGE
#

FROM python:3.8.3-alpine3.12

# Copy the virtual environment only since it has all that we need and
# none of the cruft.
WORKDIR /prometheus-operator

COPY --from=builder /prometheus-operator/ .

ENV VIRTUAL_ENV=/prometheus-operator
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENTRYPOINT ["prometheus-operator"]
