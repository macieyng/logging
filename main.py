from log_config.log_config import logger
from module import log_in_module


def main():
    logger.error("redacted payment_token='tkoane'")

    store_id = 3
    logger.error("redacted with store id payment_token='tkoane'")


if __name__ == "__main__":
    store_id = 2
    main()
    log_in_module.main()

    raise Exception
