"""Apply the mandatory filters of the 'Generar facturas' screen.

The form uses `bootstrap-select` (jQuery plugin) on top of native <select> elements.
We drive it through its JS API (`.selectpicker('val', …)`) instead of clicking through
the custom dropdown UI — it is the official API of the plugin, atomic, and robust
against visual variations. Every interaction is followed by an explicit wait to verify
the cascading effect (next select enabled/populated).
"""
import logging
from datetime import date
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
from app.rpa import waits
from app.rpa.errors import FilterError

logger = logging.getLogger(__name__)

CONVENIO_LABEL = "Savia Salud Subsidiado"
CONTRATO_NEEDLE = "savia salud subsidiado"  # case-insensitive match in contract options
MODALIDAD = "US"


def _find_option_value(driver: WebDriver, select_id: str, exact_text: str) -> str:
    """Find the value of a <select> option by exact visible text (case-insensitive, trimmed)."""
    script = """
        const select = document.getElementById(arguments[0]);
        if (!select) return null;
        const needle = arguments[1].trim().toLowerCase();
        for (const opt of select.options) {
            if (opt.textContent.trim().toLowerCase() === needle) return opt.value;
        }
        return null;
    """
    value = driver.execute_script(script, select_id, exact_text)
    if not value:
        raise FilterError(f"option '{exact_text}' not found in select #{select_id}")
    return value


def _find_option_value_contains(driver: WebDriver, select_id: str, needle: str) -> str:
    """Find the value of the first option whose text contains the needle (case-insensitive)."""
    script = """
        const select = document.getElementById(arguments[0]);
        if (!select) return null;
        const needle = arguments[1].trim().toLowerCase();
        for (const opt of select.options) {
            if (opt.textContent.trim().toLowerCase().includes(needle)) return opt.value;
        }
        return null;
    """
    value = driver.execute_script(script, select_id, needle)
    if not value:
        raise FilterError(f"no option containing '{needle}' found in select #{select_id}")
    return value


def _selectpicker_val(driver: WebDriver, select_id: str, value) -> None:
    """Set a bootstrap-select value via its JS API."""
    driver.execute_script(
        "$('#' + arguments[0]).selectpicker('val', arguments[1]).trigger('change');",
        select_id,
        value,
    )


def _selectpicker_select_all(driver: WebDriver, select_id: str) -> None:
    driver.execute_script(
        "$('#' + arguments[0]).selectpicker('selectAll').trigger('change');",
        select_id,
    )


def _set_date_input(driver: WebDriver, input_id: str, value: date) -> None:
    """Fill a jQuery-UI datepicker input via JS (format yyyy-mm-dd, confirmed by user)."""
    iso = value.isoformat()
    driver.execute_script(
        "$('#' + arguments[0]).val(arguments[1]).trigger('change').trigger('blur');",
        input_id,
        iso,
    )


def apply_filters(driver: WebDriver, fecha_inicial: date, fecha_final: date) -> None:
    """Apply Convenio, Contrato, Sedes, Modalidad and date filters."""
    try:
        logger.info(f"step=filters action=set_dates inicial={fecha_inicial} final={fecha_final}")
        _set_date_input(driver, "dateInit", fecha_inicial)
        _set_date_input(driver, "dateEnd", fecha_final)

        logger.info(f"step=filters action=set_convenio value={CONVENIO_LABEL!r}")
        convenio_value = _find_option_value(driver, "convenios_facturas", CONVENIO_LABEL)
        _selectpicker_val(driver, "convenios_facturas", convenio_value)

        logger.info("step=filters action=wait_contrato_enabled")
        waits.wait_not_disabled(driver, "#contratos_facturas")
        waits.wait_select_populated(driver, "contratos_facturas")

        logger.info(f"step=filters action=set_contrato needle={CONTRATO_NEEDLE!r}")
        contrato_value = _find_option_value_contains(driver, "contratos_facturas", CONTRATO_NEEDLE)
        _selectpicker_val(driver, "contratos_facturas", contrato_value)

        logger.info("step=filters action=wait_sedes_enabled")
        waits.wait_not_disabled(driver, "#sedes_facturas")
        waits.wait_select_populated(driver, "sedes_facturas")

        logger.info("step=filters action=select_all_sedes")
        _selectpicker_select_all(driver, "sedes_facturas")

        logger.info(f"step=filters action=set_modalidad value={MODALIDAD!r}")
        _selectpicker_val(driver, "modalidades", [MODALIDAD])

        logger.info("step=filters action=success")
    except FilterError:
        raise
    except WebDriverException as exc:
        raise FilterError(f"unexpected error applying filters: {exc}") from exc
