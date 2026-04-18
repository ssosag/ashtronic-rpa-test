"""Extract rows from the DataTables results table after clicking 'Buscar'.

Strategy:
1. Click 'Buscar'.
2. Wait for the .blockUI overlay (jQuery blockUI) to disappear.
3. Wait for `#detalle_consulta tbody` to appear — it is rendered dynamically after
   the first search.
4. Bypass DataTables pagination: `$('#...').DataTable().page.len(limit).draw()` renders
   `limit` rows in a single page, avoiding next/previous clicks.
5. Read all <th> headers (including hidden columns — they live in the DOM).
6. For each <tr> in tbody: map cells by header name, fill the structured fields and
   keep the whole row in `raw_row_json` for traceability (D13).
"""
import logging
from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from app.rpa import waits
from app.rpa.errors import ExtractError
from app.rpa.steps.filters import CONVENIO_LABEL

logger = logging.getLogger(__name__)

TABLE_ID = "detalle_consulta"
INFO_ID = "detalle_consulta_info"
SEARCH_BUTTON_ID = "buscar"
TBODY_SELECTOR = f"#{TABLE_ID} tbody"


def _read_info_text_safe(driver: WebDriver) -> Optional[str]:
    """Read the DataTables info line if present. Returns None if the element does not exist
    (DataTables may create it only after the first search)."""
    try:
        return driver.find_element(By.ID, INFO_ID).text.strip()
    except NoSuchElementException:
        return None


def _read_headers(driver: WebDriver) -> list[str]:
    """Return all <th> header labels in order, including hidden columns."""
    return driver.execute_script(
        f"""
        return Array.from(document.querySelectorAll('#{TABLE_ID} thead th'))
            .map(t => t.textContent.trim());
        """
    )


def _set_datatable_page_length(driver: WebDriver, length: int) -> None:
    """Ask DataTables to render `length` rows on a single page (client-side)."""
    driver.execute_script(
        f"$('#{TABLE_ID}').DataTable().page.len(arguments[0]).draw();",
        length,
    )


def _row_is_empty_placeholder(row: WebElement) -> bool:
    """DataTables renders a single <td class='dataTables_empty'> row when no results exist."""
    cells = row.find_elements(By.TAG_NAME, "td")
    if len(cells) != 1:
        return False
    classes = cells[0].get_attribute("class") or ""
    return "dataTables_empty" in classes


def _extract_row(row: WebElement, headers: list[str]) -> dict:
    cells = row.find_elements(By.TAG_NAME, "td")
    raw: dict[str, str] = {}
    for idx, header in enumerate(headers):
        if idx < len(cells):
            raw[header] = cells[idx].text.strip()

    def by(header: str) -> Optional[str]:
        value = raw.get(header, "").strip()
        return value or None

    return {
        "external_row_id": by("No. Orden"),
        "patient_name": by("Nombres"),
        "patient_document": by("Documento"),
        "date_service": by("Fecha cita"),
        "sede": by("Sede"),
        "contrato": CONVENIO_LABEL,
        "raw_row_json": raw,
    }


def extract_rows(driver: WebDriver, limit: int) -> list[dict]:
    """Click 'Buscar', wait for the table to refresh, and extract up to `limit` rows."""
    try:
        logger.info("step=extract action=click_buscar")
        driver.find_element(By.ID, SEARCH_BUTTON_ID).click()

        logger.info("step=extract action=wait_overlay_gone")
        waits.wait_overlay_gone(driver)

        logger.info("step=extract action=wait_table_rendered")
        waits.wait_present(driver, By.CSS_SELECTOR, TBODY_SELECTOR)

        info = _read_info_text_safe(driver)
        if info:
            logger.info(f"step=extract action=table_refreshed info={info!r}")

        logger.info(f"step=extract action=set_page_length length={limit}")
        try:
            _set_datatable_page_length(driver, limit)
            waits.wait_overlay_gone(driver)
        except WebDriverException as exc:
            logger.warning(f"step=extract datatables_page_len_failed error={exc}")

        headers = _read_headers(driver)
        logger.info(f"step=extract action=read_rows headers={len(headers)}")

        row_elements = driver.find_elements(By.CSS_SELECTOR, f"{TBODY_SELECTOR} tr")

        if len(row_elements) == 1 and _row_is_empty_placeholder(row_elements[0]):
            logger.info("step=extract action=no_results")
            return []

        rows: list[dict] = []
        for row in row_elements[:limit]:
            if _row_is_empty_placeholder(row):
                continue
            rows.append(_extract_row(row, headers))

        logger.info(f"step=extract action=success rows={len(rows)}")
        return rows

    except ExtractError:
        raise
    except TimeoutException as exc:
        raise ExtractError(f"timeout waiting for table to refresh: {exc}") from exc
    except WebDriverException as exc:
        raise ExtractError(f"webdriver error during extraction: {exc}") from exc
    except Exception as exc:
        raise ExtractError(f"unexpected error: {exc}") from exc
