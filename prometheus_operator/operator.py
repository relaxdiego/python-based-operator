import logging
import os
from pathlib import Path
import sys
import time

from kubernetes import (
    client,
    config,
    watch,
)

from prometheus_operator import (
    logs,
)


def main():
    logs.configure()
    log = logging.getLogger(__name__)

    user_kubeconfig = Path(os.path.expanduser("~")).joinpath('.kube', 'config')

    if user_kubeconfig.exists():
        log.debug("Loading user kube config")
        config.load_kube_config()
    else:
        log.debug("Loading in-cluster kube config")
        try:
            config.load_incluster_config()
        except config.ConfigException:
            log.error("Unable to load in-cluster config file. Exiting.")
            sys.exit(1)

    log.debug("Loading CustomObjectsApi client")
    # https://github.com/kubernetes-client/python/blob/master/kubernetes/client/api/apiextensions_v1_api.py
    coa_client = client.CustomObjectsApi()

    while True:
        api_group = 'relaxdiego.com'
        crd_name = 'prometheusclusters'
        api_version = 'v1alpha1'

        log.info(f"Watching {crd_name}.{api_group}/{api_version} events")
        try:
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

                log.info(f"{event['type']} {custom_obj['kind']} "
                         f"ns: {custom_obj['metadata']['namespace']}, "
                         f"name: {custom_obj['metadata']['name']}")
        except client.rest.ApiException as err:
            log.error(f"{err.status} {err.reason}")
            wait_in_seconds = 5
            log.error(f"Unable to watch {crd_name}.{api_group}/{api_version} "
                      f"events. Retrying in {wait_in_seconds} secdons")
            time.sleep(wait_in_seconds)
        else:
            log.warning("Watch stream ended unexpectedly. Retrying...")


if __name__ == "__main__":
    main()
