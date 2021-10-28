import azure.functions as func
from log_config import get_logger, handle_uncaught_exception
import sys

logger = get_logger(__name__)

sys.excepthook = handle_uncaught_exception

def catch_uncaught(return_value):
    def decorator(function):
        def wrapper(req):
            try:
                return function(req)
            except Exception:
                handle_uncaught_exception(*sys.exc_info())
                return return_value
        return wrapper
    return decorator


@catch_uncaught(func.HttpResponse(status_code=500))
def main(req: func.HttpRequest) -> func.HttpResponse:
    store_id = req.params.get('store_id')

    logger.debug("Debug w/store id payment_token='token'", extra={"store_id": store_id})
    logger.error("no store provided id payment_token='xxxxxxxxx'")
    logger.info("Info w/store id expiry_date='33333333'", extra={"store_id": store_id})
    logger.error("Error w/store id", extra={"store_id": store_id})

    raise TypeError

    return func.HttpResponse(f"Response from {store_id}")
