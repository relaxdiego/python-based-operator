import logging.config
import textwrap
import yaml


def configure(verbosity=1):
    config_dict = yaml.safe_load(textwrap.dedent("""
        version: 1
        disable_existing_loggers: False

        formatters:
          simple:
            format: '%(asctime)s %(name)-25s %(levelname)-7s %(message)s'

        handlers:
            stdout:
                class: logging.StreamHandler
                formatter: simple

        root:
            level: INFO
            handlers:
                - stdout"""))

    if verbosity > 0:
        config_dict['root']['level'] = 'DEBUG'
    else:
        config_dict['root']['level'] = 'INFO'

    logging.config.dictConfig(config_dict)
