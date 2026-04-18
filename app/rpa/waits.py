"""Explicit-wait helpers for the bot. All waits use WebDriverWait + expected_conditions —
no time.sleep as a primary mechanism (D15)."""
import logging
from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.core.config import get_settings

logger = logging.getLogger(__name__)


_MIN_DEFAULT_TIMEOUT_SECONDS = 5
_MAX_DEFAULT_TIMEOUT_SECONDS = 300


def _timeout(override: Optional[int]) -> int:
    if override is not None:
        return max(1, override)

    configured = get_settings().selenium_timeout
    return max(
        _MIN_DEFAULT_TIMEOUT_SECONDS, min(_MAX_DEFAULT_TIMEOUT_SECONDS, configured)
    )


def wait_present(driver: WebDriver, by: str, selector: str, timeout: Optional[int] = None) -> WebElement:
    return WebDriverWait(driver, _timeout(timeout)).until(
        EC.presence_of_element_located((by, selector))
    )


def wait_visible(driver: WebDriver, by: str, selector: str, timeout: Optional[int] = None) -> WebElement:
    return WebDriverWait(driver, _timeout(timeout)).until(
        EC.visibility_of_element_located((by, selector))
    )


def wait_clickable(driver: WebDriver, by: str, selector: str, timeout: Optional[int] = None) -> WebElement:
    return WebDriverWait(driver, _timeout(timeout)).until(
        EC.element_to_be_clickable((by, selector))
    )


def wait_not_disabled(driver: WebDriver, css_selector: str, timeout: Optional[int] = None) -> None:
    """Wait until the element no longer has the `disabled` attribute.
    bootstrap-select enables dependent selects (e.g. contratos after convenio) by removing
    the disabled attribute on the underlying <select>."""
    def _check(drv: WebDriver) -> bool:
        elems = drv.find_elements(By.CSS_SELECTOR, css_selector)
        return bool(elems) and not elems[0].get_attribute("disabled")
    WebDriverWait(driver, _timeout(timeout)).until(_check)


def wait_select_populated(driver: WebDriver, select_id: str, timeout: Optional[int] = None) -> None:
    """Wait until a <select id="..."> has at least one real option (beyond the placeholder
    carrying the `bs-title-option` class)."""
    script = (
        "return document.querySelectorAll("
        f"  '#{select_id} option:not(.bs-title-option)'"
        ").length > 0;"
    )
    WebDriverWait(driver, _timeout(timeout)).until(lambda d: d.execute_script(script))


def wait_overlay_gone(driver: WebDriver, timeout: Optional[int] = None) -> None:
    """Wait for known loading overlays/spinners to disappear.

    Checks a list of common selectors (DataTables processing overlay + generic spinners).
    Returns successfully when none of them are visible in the DOM."""
    selectors = [
        ".blockUI",              # jQuery blockUI plugin used by the Hiruko portal
        ".dataTables_processing",
        ".loading-overlay",
        ".loader",
        ".spinner-overlay",
        "#loading",
    ]
    def _all_gone(drv: WebDriver) -> bool:
        for sel in selectors:
            for el in drv.find_elements(By.CSS_SELECTOR, sel):
                if el.is_displayed():
                    return False
        return True
    WebDriverWait(driver, _timeout(timeout)).until(_all_gone)
