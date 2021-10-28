import logging
import re
from typing import Iterable, Mapping
from rollbar.logger import RollbarHandler
import sys
from opencensus.ext.azure.log_exporter import AzureLogHandler

DEFAULT_FORMAT = (
    "%(name)s %(message)s"
)

SENSITIVE_INFO_PATTERNS = [
    r"(?<=('|\")AdditionalResponse('|\"): ('|\"))[^('|\")]+(?=('|\"))",
    r"(?<=('|\")ExpiryDate('|\"): ('|\"))[^('|\")]+(?=('|\"))",
    r"(?<=('|\")additional_response('|\"): ('|\"))[^('|\")]+(?=('|\"))",
    r"(?<=('|\")expiry_date('|\"): ('|\"))[^('|\")]+(?=('|\"))",
    r"(?<=('|\")payment_token('|\"): ('|\"))[^('|\")]+(?=('|\"))",
    r"(?<=additional_response=')[^']+(?=')",
    r"(?<=expiry_date=')[^']+(?=')",
    r"(?<=card_expiry_date=')[^']+(?=')",
    r"(?<=payment_token=')[^']+(?=')",
]


class StoreAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra: Mapping[str, object] = {}, patterns: Iterable[str] = SENSITIVE_INFO_PATTERNS) -> None:
        super().__init__(logger, extra)
        self._patterns = patterns

    def process(self, msg, kwargs):
        for pattern in self._patterns:
            msg = re.sub(pattern, "REDACTED", msg)

        try:
            store_id = kwargs['extra']['store_id']
            return "[STORE: %s] %s" % (store_id, msg), kwargs
        except KeyError:
            return super().process(msg, kwargs)


def get_logger(name = __name__):
    logging.basicConfig(format=DEFAULT_FORMAT)
    logger = logging.getLogger(name)
    logger.setLevel(level=logging.DEBUG)

    rollbar_handler = RollbarHandler(
        "token", environment="env"
    )
    rollbar_handler.setLevel(logging.ERROR)
    logger.addHandler(rollbar_handler)

    return StoreAdapter(logger)

def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    print("handling uncaught exception")
    logger = get_logger()
    logger.error(
        "Uncaught exception. Value %s",
        exc_value,
        exc_info=(exc_type, exc_value, exc_traceback),
    )

sys.excepthook = handle_uncaught_exception