from dataclasses import dataclass, InitVar
import logging

from kubernetes import (
    client,
)
from kubernetes.client import (
    models
)

log = logging.getLogger(__name__)


# MODELS

@dataclass
class MetadataField:
    creationTimestamp: str
    generation: int
    managedFields: list
    name: str
    namespace: str
    resourceVersion: str
    selfLink: str
    uid: str


@dataclass
class CustomResourceObject:
    apiVersion: str
    kind: str
    metadata: InitVar[dict] = None

    def __post_init__(self, metadata_dict):
        self._metadata = MetadataField(**metadata_dict)

    @property
    def metadata(self):
        return self._metadata


@dataclass
class PrometheusClusterObjectSpecField:
    replicas: int
    config: str


@dataclass
class PrometheuClusterObject(CustomResourceObject):
    spec: InitVar[dict] = None

    def __post_init__(self, metadata_dict, spec_dict):
        if metadata_dict and isinstance(metadata_dict, dict):
            super().__post_init__(metadata_dict)

        if spec_dict and isinstance(spec_dict, dict):
            self._spec = PrometheusClusterObjectSpecField(**spec_dict)

    @property
    def spec(self):
        return self._spec

    def __str__(self):
        return f"{self.kind} {self.apiVersion} " \
               f"ns={self.metadata.namespace} name={self.metadata.name}"


# BUSINESS LOGIC

# References
#  client: https://github.com/kubernetes-client/python/blob/master/kubernetes/client/api/apps_v1_api.py  # NOQA
#  StatefulSet: https://github.com/kubernetes-client/python/blob/master/kubernetes/client/models/v1_stateful_set_spec.py  # NOQA

#  Deployment: https://github.com/kubernetes-client/python/blob/master/kubernetes/client/models/v1_deployment_spec.py  # NOQA

def create_cluster(pco: PrometheuClusterObject):
    log.debug("Building the prometheus configuration ConfigMap")
    config_map_name = f"{pco.metadata.name}-prometheus-cluster-config"
    core_v1_client = client.CoreV1Api()
    replace_config_map = False

    try:
        log.debug(f"Checking for ConfigMap named {config_map_name}")
        core_v1_client.read_namespaced_config_map(
            name=config_map_name,
            namespace=pco.metadata.namespace,
        )
        replace_config_map = True
    except client.rest.ApiException as err:
        if err.status >= 400 and err.status < 500:
            log.debug(f"ConfigMap '{config_map_name}' not found in "
                      f"namespace '{pco.metadata.namespace}'")

    config_map_spec = models.V1ConfigMap(
        api_version='v1',
        kind='ConfigMap',
        data={
            'prometheus.yml': pco.spec.config,
        },
        metadata={
            'name': config_map_name
        }
    )

    if replace_config_map:
        log.debug(f"Replacing existing ConfigMap {config_map_name} "
                  f"in namespace '{pco.metadata.namespace}'")
        try:
            core_v1_client.replace_namespaced_config_map(
                name=config_map_name,
                namespace=pco.metadata.namespace,
                body=config_map_spec,
                field_manager='bare-python-prometheus-operator'
            )
            log.debug(f"ConfigMap {config_map_name} "
                      f"in namespace '{pco.metadata.namespace}' "
                      "replaced succesfully")
        except client.rest.ApiException as err:
            log.error(err)
    else:
        log.debug(f"Creating ConfigMap {config_map_name} "
                  f"in namespace '{pco.metadata.namespace}'")
        try:
            core_v1_client.create_namespaced_config_map(
                namespace=pco.metadata.namespace,
                body=config_map_spec,
                field_manager='bare-python-prometheus-operator'
            )
            log.debug(f"ConfigMap {config_map_name} "
                      f"in namespace '{pco.metadata.namespace}' "
                      "created succesfully")
        except client.rest.ApiException as err:
            log.error(err)
