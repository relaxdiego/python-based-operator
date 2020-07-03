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
    ensure_config_map(pco)
    ensure_service(pco, headless=True)
    ensure_service(pco, headless=False)
    ensure_stateful_set(pco)


def ensure_config_map(pco: PrometheuClusterObject):
    config_map_name = create_configmap_name(pco)
    log.debug(f"Ensuring ConfigMap {config_map_name}")
    core_v1_client = client.CoreV1Api()
    patch = False

    try:
        log.debug(f"Checking for ConfigMap named {config_map_name}")
        core_v1_client.read_namespaced_config_map(
            name=config_map_name,
            namespace=pco.metadata.namespace,
        )
        patch = True
    except client.rest.ApiException as err:
        if err.status >= 400 and err.status < 500:
            log.debug(f"ConfigMap '{config_map_name}' not found in "
                      f"namespace '{pco.metadata.namespace}'")

    # https://github.com/kubernetes-client/python/blob/master/kubernetes/client/models/v1_config_map.py  # NOQA
    config_map_def = models.V1ConfigMap(
        api_version='v1',
        kind='ConfigMap',
        data={
            'prometheus.yml': pco.spec.config,
        },
        metadata={
            'name': config_map_name
        }
    )

    if patch:
        log.debug(f"Updating existing ConfigMap {config_map_name} "
                  f"in namespace '{pco.metadata.namespace}'")
        try:
            # https://raw.githubusercontent.com/kubernetes-client/python/master/kubernetes/client/api/core_v1_api.py  # NOQA
            core_v1_client.replace_namespaced_config_map(
                name=config_map_name,
                namespace=pco.metadata.namespace,
                body=config_map_def,
                field_manager='bare-python-prometheus-operator'
            )
            log.debug(f"Updated ConfigMap {config_map_name} "
                      f"in namespace '{pco.metadata.namespace}'")
        except client.rest.ApiException:
            log.error(f"Failed to update ConfigMap {config_map_name} "
                      f"in namespace {pco.metadata.namespace}")
    else:
        log.debug(f"Creating ConfigMap {config_map_name} "
                  f"in namespace '{pco.metadata.namespace}'")
        try:
            core_v1_client.create_namespaced_config_map(
                namespace=pco.metadata.namespace,
                body=config_map_def,
                field_manager='bare-python-prometheus-operator'
            )
            log.debug(f"Created ConfigMap {config_map_name} "
                      f"in namespace '{pco.metadata.namespace}'")
        except client.rest.ApiException:
            log.error(f"Failed to create ConfigMap {config_map_name} "
                      f"in namespace {pco.metadata.namespace}")


def ensure_service(pco: PrometheuClusterObject, headless: bool):
    service_name = create_service_name(pco, headless)
    service_type_str = f"{headless and 'Headless' or ''} Service"
    log.debug(f"Ensuring  "
              f"{service_name}")
    core_v1_client = client.CoreV1Api()
    patch = False

    try:
        log.debug(f"Checking for {service_type_str} named {service_name}")
        core_v1_client.read_namespaced_service(
            name=service_name,
            namespace=pco.metadata.namespace,
        )
        patch = True
    except client.rest.ApiException as err:
        if err.status >= 400 and err.status < 500:
            log.debug(f"{service_type_str} '{service_name}' not found in "
                      f"namespace '{pco.metadata.namespace}'")

    # https://github.com/kubernetes-client/python/blob/master/kubernetes/client/models/v1_service.py  # NOQA
    service_def_dict = dict(
        api_version='v1',
        kind='Service',
        metadata={
            'name': service_name,
        },
        spec={
            'selector': create_pod_template_labels(pco),
        }
    )

    if headless:
        service_def_dict['spec']['clusterIP'] = 'None'
    else:
        service_def_dict['spec']['ports'] = [
            {
                'protocol': 'TCP',
                'port': PROMETHEUS_ADVERTISED_PORT,
                'containerPort': PROMETHEUS_ADVERTISED_PORT
            }
        ]

    service_def = models.V1Service(**service_def_dict)

    if patch:
        log.debug(f"Patching {service_type_str} {service_name} "
                  f"in namespace '{pco.metadata.namespace}'")
        try:
            # https://raw.githubusercontent.com/kubernetes-client/python/master/kubernetes/client/api/core_v1_api.py  # NOQA
            core_v1_client.patch_namespaced_service(
                name=service_name,
                namespace=pco.metadata.namespace,
                body=service_def,
            )
            log.debug(f"Patched {service_type_str} {service_name} "
                      f"in namespace '{pco.metadata.namespace}'")
        except client.rest.ApiException as err:
            log.error(f"Failed to patch {service_type_str} {service_name} "
                      f"in namespace {pco.metadata.namespace}: "
                      f"{err.body.strip()}")
    else:
        log.debug(f"Creating {service_type_str} {service_name} "
                  f"in namespace '{pco.metadata.namespace}'")
        try:
            # https://raw.githubusercontent.com/kubernetes-client/python/master/kubernetes/client/api/core_v1_api.py  # NOQA
            core_v1_client.create_namespaced_service(
                namespace=pco.metadata.namespace,
                body=service_def,
                field_manager='bare-python-prometheus-operator'
            )
            log.debug(f"Created {service_type_str} {service_name} "
                      f"in namespace '{pco.metadata.namespace}'")
        except client.rest.ApiException as err:
            log.error(f"Failed to create {service_type_str} {service_name} "
                      f"in namespace {pco.metadata.namespace}: "
                      f"{err.body.strip()}")


def ensure_stateful_set(pco: PrometheuClusterObject):
    stateful_set_name = f"{pco.metadata.name}-prometheus"
    log.debug(f"Ensuring ice {stateful_set_name}")

    # https://github.com/kubernetes-client/python/blob/master/kubernetes/client/api/apps_v1_api.py  # NOQA
    apps_v1_client = client.AppsV1Api()
    patch = False

    try:
        log.debug(f"Checking for StatefulSet named {stateful_set_name}")
        apps_v1_client.read_namespaced_stateful_set(
            name=stateful_set_name,
            namespace=pco.metadata.namespace,
        )
        patch = True
    except client.rest.ApiException as err:
        if err.status >= 400 and err.status < 500:
            log.debug(f"StatefulSet '{stateful_set_name}' not found in "
                      f"namespace '{pco.metadata.namespace}'")


    # https://github.com/kubernetes-client/python/blob/master/kubernetes/client/models/v1_stateful_set.py  # NOQA
    stateful_set_def = models.V1StatefulSet(
        api_version='apps/v1',
        kind='StatefulSet',
        metadata={
            'name': stateful_set_name,
        },
        # https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#statefulsetspec-v1-apps
        spec={
            'selector': {
                'matchLabels': create_pod_template_labels(pco),
            },
            'serviceName': create_service_name(pco, headless=True),
            'replicas': int(pco.spec.replicas),
            'template': {
                'metadata': {
                    'labels': create_pod_template_labels(pco)
                },
                'spec': {
                    'terminationGracePeriod': 10,
                    'volumes': [
                        {
                            'name': 'prometheus-config',
                            'configMap': {
                                'name': create_configmap_name(pco),
                                'items': [
                                    {
                                        'key': 'prometheus.yml',
                                        'path': 'prometheus.yml'
                                    }
                                ]
                            }
                        }
                    ],
                    'containers': [
                        {
                            'name': 'prometheus',
                            # TODO: Make this customizable via the
                            #       PromethusCluster's spec
                            'image': 'prom/prometheus:v2.19.2',
                            'ports': [
                                {
                                    'containerPort': PROMETHEUS_ADVERTISED_PORT,
                                    'name': 'web',
                                }
                            ],
                            'volumeMounts': [
                                {
                                    'name': 'data',
                                    'mountPath': '/prometheus',
                                },
                                {
                                    'name': 'prometheus-config',
                                    'mountPath': '/etc/prometheus',
                                }
                            ]
                        }
                    ]
                }
            },
            'volumeClaimTemplates': [
                {
                    'metadata': {
                        'name': 'data',
                    },
                    'spec': {
                        'accessModes': [
                            'ReadWriteOnce',
                        ],
                        'resources': {
                            'requests': {
                                'storage': '1Gi',
                            }
                        }
                    }
                }
            ]
        }
    )

    if patch:
        log.debug(f"Patching StatefulSet {stateful_set_name} "
                  f"in namespace '{pco.metadata.namespace}'")
        try:
            # https://github.com/kubernetes-client/python/blob/e60d9212c6a451a8617e2116fe49589213fad73b/kubernetes/client/api/apps_v1_api.py#L4571-L4597  # NOQA
            apps_v1_client.patch_namespaced_stateful_set(
                name=stateful_set_name,
                namespace=pco.metadata.namespace,
                body=stateful_set_def,
            )
            log.debug(f"Patched StatefulSet {stateful_set_name} "
                      f"in namespace '{pco.metadata.namespace}'")
        except client.rest.ApiException as err:
            log.error(f"Failed to patch StatefulSet {stateful_set_name} "
                      f"in namespace {pco.metadata.namespace}: "
                      f"{err.body.strip()}")
    else:
        log.debug(f"Creating StatefulSet {stateful_set_name} "
                  f"in namespace '{pco.metadata.namespace}'")
        try:
            # https://github.com/kubernetes-client/python/blob/e60d9212c6a451a8617e2116fe49589213fad73b/kubernetes/client/api/apps_v1_api.py#L499-L523  # NOQA
            apps_v1_client.create_namespaced_stateful_set(
                namespace=pco.metadata.namespace,
                body=stateful_set_def,
                field_manager='bare-python-prometheus-operator'
            )
            log.debug(f"Created StatefulSet {stateful_set_name} "
                      f"in namespace '{pco.metadata.namespace}'")
        except client.rest.ApiException as err:
            log.error(f"Failed to create StatefulSet {stateful_set_name} "
                      f"in namespace {pco.metadata.namespace}: "
                      f"{err.body.strip()}")


def create_configmap_name(pco):
    return f"{pco.metadata.name}-prometheus-cluster"


def create_service_name(pco, headless):
    return f"{pco.metadata.name}-prometheus-cluster" \
           f"{headless and '-pod-addresses' or ''}"


def create_pod_template_labels(pco):
    return {
        'app': f"{pco.metadata.name}-prometheus-cluster",
        'apiVersion': pco.apiVersion.split('/')[1]
    }
