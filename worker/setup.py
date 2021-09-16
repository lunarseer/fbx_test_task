import logging


logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s - %(asctime)s - [%(levelname)s] - %(message)s",
)

log = logging.getLogger('APP')
