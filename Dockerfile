FROM python:3.8.3-alpine3.12

ADD . /prometheus-operator
RUN pip3 install -r /prometheus-operator/requirements.txt
RUN pip3 install /prometheus-operator

ENTRYPOINT ["prometheus_operator"]
