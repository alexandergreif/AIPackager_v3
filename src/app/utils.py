# src/app/utils.py
import time
from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def retry_with_backoff(
    retries: int = 3, backoff_in_seconds: float = 1
) -> Callable[[F], F]:
    def rwb(f: F) -> F:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _retries, _backoff = retries, backoff_in_seconds
            while _retries > 1:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    print(f"Error: {e}. Retrying in {_backoff} seconds...")
                    time.sleep(_backoff)
                    _retries -= 1
                    _backoff *= 2
            return f(*args, **kwargs)

        return wrapper  # type: ignore

    return rwb
