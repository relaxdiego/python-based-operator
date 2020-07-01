from dataclasses import dataclass, field, InitVar
import logging

from kubernetes import (
    client,
)
from kubernetes.client import (
    models
)

log = logging.getLogger(__name__)


PROMETHEUS_ADVERTISED_PORT = 9090


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
    annotations: dict = field(default_factory=dict)


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

def create_cluster(pco: PrometheuClusterObject):
    create_or_replace_config_map(pco)
    create_or_replace_headless_service(pco)


def create_or_replace_config_map(pco: PrometheuClusterObject):
    config_map_name = f"{pco.metadata.name}-prometheus-cluster-config"
    log.debug(f"Building ConfigMap {config_map_name}")
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

    # https://github.com/kubernetes-client/python/blob/master/kubernetes/client/models/v1_config_map.py  # NOQA
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
        except client.rest.ApiException:
            log.error(f"Failed to replace ConfigMap {config_map_name} "
                      f"in namespace {pco.metadata.namespace}")
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
        except client.rest.ApiException:
            log.error(f"Failed to create ConfigMap {config_map_name} "
                      f"in namespace {pco.metadata.namespace}")


def create_or_replace_headless_service(pco: PrometheuClusterObject):
    service_name = f"{pco.metadata.name}-prometheus-cluster-pod-addresses"
    log.debug(f"Building headless Service {service_name}")
    core_v1_client = client.CoreV1Api()
    replace = False

    try:
        log.debug(f"Checking for Service named {service_name}")
        core_v1_client.read_namespaced_service(
            name=service_name,
            namespace=pco.metadata.namespace,
        )
        replace = True
    except client.rest.ApiException as err:
        if err.status >= 400 and err.status < 500:
            log.debug(f"Service '{service_name}' not found in "
                      f"namespace '{pco.metadata.namespace}'")

    # https://github.com/kubernetes-client/python/blob/master/kubernetes/client/models/v1_service.py  # NOQA
    service_spec = models.V1Service(
        api_version='v1',
        kind='Service',
        metadata={
            'name': service_name,
        },
        spec={
            'selector': create_pod_template_labels(pco),
            'clusterIP': 'None'
        }
    )

    if replace:
        log.debug(f"Deleting Service {service_name} "
                  f"in namespace '{pco.metadata.namespace}'")
        try:
            # https://raw.githubusercontent.com/kubernetes-client/python/master/kubernetes/client/api/core_v1_api.py  # NOQA
            core_v1_client.delete_namespaced_service(
                name=service_name,
                namespace=pco.metadata.namespace,
            )
            log.debug(f"Deleted headless Service {service_name} "
                      f"in namespace '{pco.metadata.namespace}'")
        except client.rest.ApiException as err:
            log.error(f"Failed to delete Service {service_name} "
                      f"in namespace {pco.metadata.namespace}: "
                      f"{err.body.strip()}")

    log.debug(f"Creating Service {service_name} "
              f"in namespace '{pco.metadata.namespace}'")
    try:
        # https://raw.githubusercontent.com/kubernetes-client/python/master/kubernetes/client/api/core_v1_api.py  # NOQA
        core_v1_client.create_namespaced_service(
            namespace=pco.metadata.namespace,
            body=service_spec,
            field_manager='bare-python-prometheus-operator'
        )
        log.debug(f"Created headless Service {service_name} "
                  f"in namespace '{pco.metadata.namespace}'")
    except client.rest.ApiException as err:
        log.error(f"Failed to create Service {service_name} "
                  f"in namespace {pco.metadata.namespace}: "
                  f"{err.body.strip()}")


def create_or_replace_stateful_set(pco: PrometheuClusterObject):
    #  client: https://github.com/kubernetes-client/python/blob/master/kubernetes/client/api/apps_v1_api.py  # NOQA
    #  StatefulSet: https://github.com/kubernetes-client/python/blob/master/kubernetes/client/models/v1_stateful_set_spec.py  # NOQA
    # spec = models.V1DeploymentSpec(
    #     replicas=pco.spec.replicas,
    #     template=create_template(config=pco.spec.config),
    #     selector={
    #         'app': 'prometheus',
    #         'apiVersion': pco.apiVersion,
    #         'name': pco.metadata.name
    #     },
    # )
    # apps_v1_client = client.AppsV1Api()
    pass


def create_pod_template_labels(pco):
    return {
        'app': pco.metadata.name,
        'apiVersion': pco.apiVersion.split('/')[1]
    }
