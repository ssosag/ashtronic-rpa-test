"""Bot orchestrator — entry point called from `rpa_runner` via `asyncio.to_thread`.

Runs login → navigate → filters → extract. On any error, captures a screenshot tagged
with the failing step and re-raises as a BotError. Always closes the driver in `finally`.
"""
import logging
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver
from app.core.config import get_settings
from app.rpa.driver import create_driver
from app.rpa.errors import BotError
from app.rpa.steps import login as login_step
from app.rpa.steps import navigate as navigate_step
from app.rpa.steps import filters as filters_step
from app.rpa.steps import extract as extract_step

logger = logging.getLogger(__name__)


def run(job_id: int, fecha_inicial: date, fecha_final: date, limit: int) -> list[dict]:
    """Run the full extraction pipeline. Returns a list of record dicts.
    Raises BotError on failure (after attempting to save a screenshot)."""
    driver: Optional[WebDriver] = None
    logger.info(f"job_id={job_id} bot=start")
    try:
        driver = create_driver()
        login_step.login(driver)
        navigate_step.navigate_to_generate_invoice(driver)
        filters_step.apply_filters(driver, fecha_inicial, fecha_final)
        rows = extract_step.extract_rows(driver, limit)
        logger.info(f"job_id={job_id} bot=done rows={len(rows)}")
        return rows

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
