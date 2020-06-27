import logging

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

    log.debug("Loading kube config")
    config.load_incluster_config()

    v1 = client.CoreV1Api()

    while True:
        w = watch.Watch()

        log.debug("Watching pod events in all namespaces")
        for event in w.stream(v1.list_pod_for_all_namespaces, timeout_seconds=10):
            log.debug("Event: %s %s %s" % (
                event['type'],
                event['object'].kind,
                event['object'].metadata.name)
            )
        log.debug("Finished pod stream. Retrying")


if __name__ == "__main__":
    main()
