"""Bot orchestrator — entry point called from `rpa_runner` via `asyncio.to_thread`.

Runs login → navigate → filters → extract. On any error, captures a screenshot tagged
with the failing step and re-raises as a BotError. Always closes the driver in `finally`.

Transient failures (timeouts, webdriver glitches) in `login` and `extract` are retried
with exponential backoff via `app.rpa.retry`. Structural errors like
`InvalidCredentialsError` are NOT retried — the portal actively rejected credentials,
retrying is wasteful.
"""
import logging
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Callable, Optional
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver
from app.core.config import get_settings
from app.rpa.driver import create_driver
from app.rpa.errors import BotError, ExtractError, InvalidCredentialsError, LoginError
from app.rpa.retry import retry
from app.rpa.steps import login as login_step
from app.rpa.steps import navigate as navigate_step
from app.rpa.steps import filters as filters_step
from app.rpa.steps import extract as extract_step

logger = logging.getLogger(__name__)

# Only retry on exceptions that can legitimately be transient (portal slow,
# overlay stuck, network glitch). `InvalidCredentialsError` is intentionally
# excluded — the portal actively rejected credentials.
_TRANSIENT_EXCEPTIONS: tuple[type[BaseException], ...] = (
    TimeoutException,
    WebDriverException,
    LoginError,
    ExtractError,
)


def run(
    job_id: int,
    fecha_inicial: date,
    fecha_final: date,
    limit: int,
    stats: Optional[dict] = None,
    on_session_started: Optional[Callable[[], None]] = None,
) -> list[dict]:
    """Run the full extraction pipeline. Returns a list of record dicts.
    Raises BotError on failure (after attempting to save a screenshot).

    If `stats` is provided, it is mutated with `retries` (int) — the number of
    transient retries that occurred across all retried steps. The caller reads
    this after `run()` returns OR raises, to persist it on the Job row.

    If `on_session_started` is provided, it is called once the webdriver
    session is successfully created.
    """
    settings = get_settings()
    attempts = settings.bot_retry_attempts
    backoff = settings.bot_retry_backoff_seconds

    def _bump_retries() -> None:
        if stats is not None:
            stats["retries"] = stats.get("retries", 0) + 1

    driver: Optional[WebDriver] = None
    logger.info(f"job_id={job_id} bot=start")
    try:
        driver = create_driver()
        if on_session_started is not None:
            try:
                on_session_started()
            except Exception as exc:
                logger.warning(
                    f"job_id={job_id} on_session_started callback failed: {exc}"
                )

        retry(
            lambda: login_step.login(driver),
            attempts=attempts,
            backoff_seconds=backoff,
            retry_on=_TRANSIENT_EXCEPTIONS,
            step="login",
            on_retry=_bump_retries,
        )

        navigate_step.navigate_to_generate_invoice(driver)
        filters_step.apply_filters(driver, fecha_inicial, fecha_final)

        rows = retry(
            lambda: extract_step.extract_rows(driver, limit),
            attempts=attempts,
            backoff_seconds=backoff,
            retry_on=_TRANSIENT_EXCEPTIONS,
            step="extract",
            on_retry=_bump_retries,
        )

        logger.info(f"job_id={job_id} bot=done rows={len(rows)}")
        return rows

    except InvalidCredentialsError:
        # Structural: skip screenshot (the /login page is not interesting) and re-raise.
        raise

    except BotError as exc:
        if driver is not None:
            _save_screenshot(driver, job_id, exc.step)
        raise

    except Exception as exc:
        if driver is not None:
            _save_screenshot(driver, job_id, "bot")
        raise BotError(f"unexpected error: {exc}", step="bot") from exc

    finally:
        if driver is not None:
            try:
                driver.quit()
                logger.info(f"job_id={job_id} webdriver=closed")
            except Exception as exc:
                logger.warning(f"job_id={job_id} error closing webdriver: {exc}")


def _save_screenshot(driver: WebDriver, job_id: int, step: str) -> None:
    """Best-effort screenshot capture. Never raises — failures are only logged."""
    settings = get_settings()
    try:
        screenshot_dir = Path(settings.screenshots_dir)
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = screenshot_dir / f"job_{job_id}_{step}_{ts}.png"
        driver.save_screenshot(str(path))
        logger.error(f"job_id={job_id} step={step} screenshot={path}")
    except Exception as exc:
        logger.error(f"job_id={job_id} screenshot_failed error={exc}")
