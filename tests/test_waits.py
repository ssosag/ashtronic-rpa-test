"""Unit tests for rpa/waits.py using mock WebDriver objects."""
from unittest.mock import MagicMock

import pytest
from selenium.common.exceptions import TimeoutException

from app.rpa import waits


def _mk_driver(elements_by_selector: dict) -> MagicMock:
    driver = MagicMock()

    def _find(by, selector):
        return elements_by_selector.get(selector, [])

    driver.find_elements.side_effect = _find
    return driver


def _mk_el(displayed: bool) -> MagicMock:
    el = MagicMock()
    el.is_displayed.return_value = displayed
    return el


def test_wait_overlay_gone_returns_immediately_when_no_overlays():
    driver = _mk_driver({})
    waits.wait_overlay_gone(driver, timeout=1)


def test_wait_overlay_gone_returns_when_overlay_hidden():
    driver = _mk_driver({".blockUI": [_mk_el(False)]})
    waits.wait_overlay_gone(driver, timeout=1)


def test_wait_overlay_gone_raises_timeout_when_overlay_visible():
    driver = _mk_driver({".blockUI": [_mk_el(True)]})
    with pytest.raises(TimeoutException):
        waits.wait_overlay_gone(driver, timeout=1)


def test_wait_overlay_gone_raises_for_non_timeout_errors():
    driver = MagicMock()
    driver.find_elements.side_effect = RuntimeError("boom")
    try:
        waits.wait_overlay_gone(driver, timeout=1)
    except RuntimeError as e:
        assert "boom" in str(e)
    else:
        raise AssertionError("Expected RuntimeError to propagate")
