import logging
import re
import rollbar
from rollbar.logger import RollbarHandler
import sys

DEFAULT_FORMAT = (
    "%(name)s %(levelname)s [STORE:%(store_id)s] %(message)s"
)
# ROLLBAR_FORMAT = "[STORE: %(store_id)s] %(message)s"

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


class StoreFormatter(logging.Formatter):
    def __init__(self, patterns = SENSITIVE_INFO_PATTERNS, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._patterns = patterns

    def format(self, record):
        if "store_id" in self._fmt:
            record = self.format_store(record)
        msg = super().format(record)
        return msg

    def formatMessage(self, record):
        msg = super().formatMessage(record)
        msg = self.format_pattern(msg)
        return msg

    def get_formatting_no_store_id(self):
        format_parts = self._fmt.split(" ")
        format_parts = format_parts[:-2] + [format_parts[-1]]
        return " ".join(format_parts)

    def format_store(self, record):
        if not hasattr(record, "store_id"):
            self._style._fmt = self.get_formatting_no_store_id()
        else:
            self._style._fmt = self._fmt
        return record

    def format_pattern(self, msg):
        for pattern in self._patterns:
            msg = re.sub(pattern, "REDACTED", msg)
        return msg


def get_logger(name = __name__):

    logger = logging.getLogger(name)
    logger.setLevel(level=logging.DEBUG)

    formatter = StoreFormatter(patterns=SENSITIVE_INFO_PATTERNS, fmt=DEFAULT_FORMAT)

    rollbar_handler = RollbarHandler(
        "", environment=""
    )
    rollbar_handler.setLevel(logging.ERROR)
    logger.addHandler(rollbar_handler)

    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    logger.addHandler(stderr_handler)
    
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)

    for handler in logger.handlers:
        handler.setFormatter(formatter)

    return logger

def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    print("handling uncaught exception")
    logger = get_logger()
    logger.error(
        "Uncaught exception. Value %s",
        exc_value,
        exc_info=(exc_type, exc_value, exc_traceback),
    )

sys.excepthook = handle_uncaught_exception