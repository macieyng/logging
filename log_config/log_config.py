import logging
import re
import rollbar
from rollbar.logger import RollbarHandler
import sys

DEFAULT_FORMAT = (
    "%(module)s.%(filename)s.%(funcName)s %(levelname)s [STORE: %(store_id)s] %(message)s"
)
ROLLBAR_FORMAT = "[STORE: %(store_id)s] %(message)s"

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


class CustomRollbarHandler(RollbarHandler):
    def emit(self, record):
        # If the record came from Rollbar's own logger don't report it
        # to Rollbar
        if record.name == rollbar.__log_name__:
            return

        level = record.levelname.lower()

        if level not in self.SUPPORTED_LEVELS:
            return

        exc_info = record.exc_info

        extra_data = {
            "args": record.args,
            "record": {
                "created": record.created,
                "funcName": record.funcName,
                "lineno": record.lineno,
                "module": record.module,
                "name": record.name,
                "pathname": record.pathname,
                "process": record.process,
                "processName": record.processName,
                "relativeCreated": record.relativeCreated,
                "thread": record.thread,
                "threadName": record.threadName,
            },
        }

        extra_data.update(getattr(record, "extra_data", {}))

        payload_data = getattr(record, "payload_data", {})

        self._add_history(record, payload_data)

        # after we've added the history data, check to see if the
        # notify level is satisfied
        if record.levelno < self.notify_level:
            return

        # Wait until we know we're going to send a report before trying to
        # load the request
        request = getattr(record, "request", None) or rollbar.get_request()

        uuid = None
        try:
            # when not in an exception handler, exc_info == (None, None, None)
            if exc_info and exc_info[0]:
                if record.msg:
                    message_template = {
                        "body": {
                            "trace": {
                                "exception": {
                                    "description": self.format(record),
                                }
                            }
                        }
                    }
                    payload_data = rollbar.dict_merge(
                        payload_data, message_template, silence_errors=True
                    )

                uuid = rollbar.report_exc_info(
                    exc_info,
                    level=level,
                    request=request,
                    extra_data=extra_data,
                    payload_data=payload_data,
                )
            else:
                uuid = rollbar.report_message(
                    self.format(
                        record
                    ),  # w oryginale record.getMessage() przez co wiadomość nie jest sformatowana
                    level=level,
                    request=request,
                    extra_data=extra_data,
                    payload_data=payload_data,
                )
        except:
            self.handleError(record)
        else:
            if uuid:
                record.rollbar_uuid = uuid


class StoreFormatter(logging.Formatter):
    def __init__(self, *args, patterns, **kwargs):
        super().__init__(*args, **kwargs)
        self._patterns = patterns

    def format(self, record):
        record = self.format_store(record)
        msg = super().format(record)
        msg = self.format_pattern(msg)
        return msg

    def format_store(self, record):
        if not hasattr(record, "store_id"):
            setattr(record, "store_id", None)
        return record

    def format_pattern(self, msg):
        for pattern in self._patterns:
            msg = re.sub(pattern, "REDACTED", msg)
        return msg


logger = logging.getLogger()

rollbar_handler = CustomRollbarHandler(
    "token", environment="maciek_logs"
)
rollbar_handler.setLevel(logging.ERROR)
logger.addHandler(rollbar_handler)

formatter = StoreFormatter(fmt=DEFAULT_FORMAT, patterns=SENSITIVE_INFO_PATTERNS)
rollbar_formatter = StoreFormatter(fmt=ROLLBAR_FORMAT, patterns=SENSITIVE_INFO_PATTERNS)
for handler in logger.handlers:
    if isinstance(handler, CustomRollbarHandler):
        handler.setFormatter(rollbar_formatter)
    else:
        handler.setFormatter(formatter)


def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error(
        "Uncaught exception. Value %s",
        exc_value,
        exc_info=(exc_type, exc_value, exc_traceback),
    )

sys.excepthook = handle_exception
