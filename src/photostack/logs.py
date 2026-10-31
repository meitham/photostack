import logging
import sys


def configure(verbosity=1):
    """Configure logging based on verbosity level.

    verbosity=1: WARNING
    verbosity=2: INFO
    verbosity=3+: DEBUG
    """
    levels = {
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }
    level = levels.get(verbosity, logging.DEBUG)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr,
    )

    return logging.getLogger('photostack')
