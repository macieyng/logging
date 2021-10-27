from sys import exc_info
from log_config.log_config import get_logger

logger = get_logger()
def main():
    logger.error("error")
    store_id = 1
    logger.error("error with store id")
    dict = {}
    try:
        hello = dict["hello"]
    except KeyError as e:
        logger.error("wrong key", exc_info=e)
