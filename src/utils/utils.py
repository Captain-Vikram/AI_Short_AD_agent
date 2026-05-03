import time
import random
import functools
from typing import Any, Callable, List, Optional, Type, Union

from logger import get_logger

def retry_with_backoff(
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 60.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception,
    status_codes: Optional[List[int]] = None,
    logger_name: str = "utils",
    log_file: Optional[str] = None,
):
    """
    Retry a function with exponential backoff and optional jitter.
    
    Args:
        max_retries: Maximum number of retries.
        initial_backoff: Initial backoff time.
        max_backoff: Maximum backoff time.
        jitter: Whether to add random jitter to the backoff.
        exceptions: Exception(s) to catch and retry on.
        status_codes: HTTP status codes to retry on (if the exception has a status_code or response.status_code attribute).
        logger_name: Name for the logger.
        log_file: Path to the log file.
    """
    if isinstance(exceptions, list):
        exceptions = tuple(exceptions)

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name, log_file=log_file)
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if x >= max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries. Final error: {e}")
                        raise

                    # Check for HTTP status codes if provided
                    if status_codes:
                        actual_status = None
                        if hasattr(e, "response") and hasattr(e.response, "status_code"):
                            actual_status = e.response.status_code
                        elif hasattr(e, "status_code"):
                            actual_status = e.status_code
                        
                        if actual_status and actual_status not in status_codes:
                            logger.error(f"Function {func.__name__} failed with status code {actual_status}, which is not in retryable list {status_codes}.")
                            raise

                    # Calculate wait time
                    wait = (initial_backoff * 2**x)
                    if jitter:
                        wait += random.uniform(0, 1)
                    wait = min(wait, max_backoff)

                    logger.warning(
                        f"Function {func.__name__} failed with {type(e).__name__}: {e}. "
                        f"Retrying in {wait:.2f} seconds... (Attempt {x+1}/{max_retries})"
                    )
                    time.sleep(wait)
                    x += 1

        return wrapper

    return decorator
