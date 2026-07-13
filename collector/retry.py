import time
from functools import wraps

from utils.logger import logger


def retry(max_attempts=3, delay=2):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            attempt = 1

            while attempt <= max_attempts:

                try:

                    return func(*args, **kwargs)

                except Exception as e:

                    logger.warning(
                        f"Attempt {attempt} failed : {e}"
                    )

                    if attempt == max_attempts:

                        logger.error("Maximum retry reached.")

                        raise

                    time.sleep(delay)

                    attempt += 1

        return wrapper

    return decorator