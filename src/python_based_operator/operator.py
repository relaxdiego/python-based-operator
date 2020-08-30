import logging
import os
from pathlib import Path
import sys

from kubernetes import (
    client,
    config,
    watch,
)

from python_based_operator import (
    logs,
)
from python_based_operator.provisioners import (
    v1alpha1,
)

logs.configure()
log = logging.getLogger(__name__)


def main():
    load_kube_credentials()
    api_version = os.environ.get('PROMETHEUS_CLUSTER_CRD_VERSION_TO_WATCH', 'v1alpha1')
    watch_prometheusclusters(api_version=api_version)


def load_kube_credentials():
    log.debug("Looking for credentials...")
    user_kubeconfig = Path(os.path.expanduser("~")).joinpath('.kube', 'config')
    dev_kubeconfig = Path(__file__).joinpath('..', '..', '..',
                                             '.tmp', 'serviceaccount',
                                             'dev_kubeconfig.yml').resolve()

    if dev_kubeconfig.exists():
        log.debug("Loading from dev kube config")
        config.load_kube_config(config_file=str(dev_kubeconfig))
    elif user_kubeconfig.exists():
        log.debug("Loading user kube config")
        config.load_kube_config()
    else:
        log.debug("Loading in-cluster kube config")
        try:
            config.load_incluster_config()
        except config.ConfigException:
            log.error("Unable to load in-cluster config file. Exiting.")
            sys.exit(1)


def watch_prometheusclusters(api_version):
    log = logging.getLogger(__name__)
    log.debug("Loading CustomObjectsApi client")
    # https://github.com/kubernetes-client/python/blob/v11.0.0/kubernetes/client/api/custom_objects_api.py
    coa_client = client.CustomObjectsApi()

    api_group = 'relaxdiego.com'
    crd_name = 'prometheusclusters'

    log.info(f"Watching {crd_name}.{api_group}/{api_version} events")
    # References:
    # 1. Watchable methods:
    #      https://raw.githubusercontent.com/kubernetes-client/python/v11.0.0/kubernetes/client/api/core_v1_api.py
    #      https://github.com/kubernetes-client/python/blob/master/kubernetes/client/api/apiextensions_v1_api.py
    #
    # 2. The Watch#stream() method
    #      https://github.com/kubernetes-client/python-base/blob/d30f1e6fd4e2725aae04fa2f4982a4cfec7c682b/watch/watch.py#L107-L157
    for event in watch.Watch().stream(coa_client.list_cluster_custom_object,
                                      group=api_group,
                                      plural=crd_name,
                                      version=api_version):
        custom_obj = event['raw_object']
        log.debug(f"Received: {custom_obj}")
        event_type = event['type']

        if api_version == 'v1alpha1':
            provisioner = v1alpha1

        pco = provisioner.PrometheuClusterObject(**custom_obj)
        log.info(f"{event_type} {pco}")

        if event_type == "ADDED":
            provisioner.install(pco)
        elif event_type == "DELETED":
            provisioner.uninstall(pco)
        elif event_type == "MODIFIED":
            provisioner.upgrade(pco)
        else:
            log.info(f"Unhandled event type '{event_type}'")


if __name__ == "__main__":
    main()
