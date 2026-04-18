"""Retry helper for bot steps with transient failures.

Only retries on a whitelist of exception types (typically `TimeoutException` and
`WebDriverException`). Structural errors — like `LoginError` raised because the
post-submit URL is still `/login` (credentials are invalid) — are **not** retried:
re-running them is wasteful and just delays the job's failure.
"""
import logging
import time
from typing import Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry(
    fn: Callable[[], T],
    *,
    attempts: int,
    backoff_seconds: float,
    retry_on: tuple[type[BaseException], ...],
    step: str,
    on_retry: Optional[Callable[[], None]] = None,
) -> T:
    """Call `fn`; if it raises one of `retry_on`, wait and retry up to `attempts` times total.

    `attempts` counts the first call (e.g. attempts=3 → 1 original + 2 retries).
    Backoff is exponential: `backoff_seconds * 2**(attempt - 1)`.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except retry_on as exc:
            last_exc = exc
            if attempt == attempts:
                logger.error(
                    f"step={step} retry=exhausted attempts={attempts} error={exc!r}"
                )
                raise
            delay = backoff_seconds * (2 ** (attempt - 1))
            logger.warning(
                f"step={step} retry=transient attempt={attempt}/{attempts} "
                f"delay={delay:.1f}s error={exc!r}"
            )
            if on_retry is not None:
                try:
                    on_retry()
                except Exception as cb_exc:
                    logger.warning(f"step={step} retry on_retry callback failed: {cb_exc}")
            time.sleep(delay)

    # Unreachable: the loop either returns or raises.
    assert last_exc is not None
    raise last_exc
