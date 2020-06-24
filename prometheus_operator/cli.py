import time
import logging

from prometheus_operator import (
    logs
)


def main():
    logs.configure()
    log = logging.getLogger(__name__)
    while True:
        log.info("Main!")
        time.sleep(5)


if __name__ == "__main__":
    main()
