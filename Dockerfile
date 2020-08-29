#
# TESTER STAGE
#

FROM python:3.8.3-alpine3.12 as tester

WORKDIR /operator-src

ADD ./src/ .
ADD .flake8 .

RUN apk update
RUN pip install --upgrade pip
RUN pip install -r requirements-dev.txt

# TODO: Run unit tests here

# TODO: Submit test artifacts somewhere

#
# BUILDER STAGE
#

FROM python:3.8.3-alpine3.12 as builder

WORKDIR /operator-src

COPY --from=tester /operator-src/ .

RUN apk update
# Reference: https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
ENV VIRTUAL_ENV=/operator
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip
# We are using requirements.txt to constrain the dependency versions to the
# ones that we have tested with so as the lessen the build and deployment
# variables and make our deployments more deterministic.
RUN pip install -c requirements.txt .

# Install Helm 3
RUN apk add wget
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
WORKDIR /operator

COPY --from=builder /operator/ .

ENV VIRTUAL_ENV=/operator
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# This is based on the package name declared in src/setup.py
ENTRYPOINT ["python-based-operator"]
