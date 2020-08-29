from dataclasses import dataclass, field, InitVar
import logging
from pathlib import Path
import shutil
import subprocess
import tempfile
import yaml

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
    annotations: dict

@dataclass
class CustomResourceObject:
    apiVersion: str
    kind: str
    metadata: MetadataField

    def __post_init__(self):
        self.metadata = MetadataField(**self.metadata)


@dataclass
class PrometheusClusterObjectSpecField:
    replicas: int
    config: str


@dataclass()
class PrometheuClusterObject(CustomResourceObject):
    spec: PrometheusClusterObjectSpecField

    def __post_init__(self):
        super().__post_init__()
        self.spec = PrometheusClusterObjectSpecField(**self.spec)

    def __str__(self):
        return f"{self.kind} {self.apiVersion} " \
               f"ns={self.metadata.namespace} name={self.metadata.name}"


# BUSINESS LOGIC

def install(pco: PrometheuClusterObject):
    cluster_name = pco.metadata.name

    with tempfile.TemporaryDirectory(prefix="prometheus-operator-") as tmpdir:
        values_yaml = Path(tmpdir).joinpath("values.yaml")
        values_yaml.write_text(yaml.dump({
            'prometheus': {
                'replicas': pco.spec.replicas,
                'config': pco.spec.config
            }
        }))

        success = \
            _helm([
                "install",
                "--atomic",
                "--wait",
                "--timeout=3m0s",
                "--values", str(values_yaml.resolve()),
                f"--namespace={pco.metadata.namespace}",
                cluster_name,
                Path(__file__).joinpath('..', '..', 'charts', 'prometheus').resolve(),
        ])

    if success:
        log.info(f"Succesfully installed Prometheus Cluster '{cluster_name}' "
                 f"in namespace '{pco.metadata.namespace}'")
    else:
        log.error(f"Failed to install Prometheus cluster '{cluster_name}' "
                  f"in namespace '{pco.metadata.namespace}'")

def uninstall(pco: PrometheuClusterObject):
    cluster_name = pco.metadata.name

    success = _helm([
        "uninstall",
        f"--namespace={pco.metadata.namespace}",
        cluster_name,
    ])

    if success:
        log.info(f"Succesfully uninstalled Prometheus Cluster '{cluster_name}' "
                 f"in namespace '{pco.metadata.namespace}'")
    else:
        log.error(f"Failed to uninstall Prometheus cluster '{cluster_name}' "
                  f"in namespace '{pco.metadata.namespace}'")

def upgrade(pco: PrometheuClusterObject):
    cluster_name = pco.metadata.name

    with tempfile.TemporaryDirectory(prefix="prometheus-operator-") as tmpdir:
        values_yaml = Path(tmpdir).joinpath("values.yaml")
        values_yaml.write_text(yaml.dump({
            'prometheus': {
                'replicas': pco.spec.replicas,
                'config': pco.spec.config
            }
        }))

        success = \
            _helm([
                "upgrade",
                "--atomic",
                "--wait",
                "--timeout=3m0s",
                "--values", str(values_yaml.resolve()),
                f"--namespace={pco.metadata.namespace}",
                cluster_name,
                Path(__file__).joinpath('..', '..', 'charts', 'prometheus').resolve(),
        ])

    if success:
        log.info(f"Succesfully upgraded Prometheus Cluster '{cluster_name}' "
                 f"in namespace '{pco.metadata.namespace}'")
    else:
        log.error(f"Failed to upgrade Prometheus cluster '{cluster_name}' "
                  f"in namespace '{pco.metadata.namespace}'")

# HELPERS

def _helm(args_list):
    cmd = [shutil.which('helm')] + [str(arg) for arg in args_list]
    log.debug(f"Running: {' '.join(cmd)}")
    output = subprocess.run(cmd, capture_output=True)
    log.debug(output)
    return output.returncode == 0

# Add a representer to format literal block strings properly when dumping
# Reference: https://stackoverflow.com/a/50519774/402145
def _selective_representer(dumper, data):
    return dumper.represent_scalar(u"tag:yaml.org,2002:str", data,
                                   style="|" if "\n" in data else None)

yaml.add_representer(str, _selective_representer)
