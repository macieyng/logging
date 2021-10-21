from log_config.log_config import logger
from module import log_in_module


def main():
    logger.error("error from main.py payment_token='tkoane'", extra={"store": 2})


if __name__ == "__main__":
    main()
    log_in_module.main()
