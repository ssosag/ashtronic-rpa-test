import logging
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from app.core.config import get_settings
from app.rpa import waits
from app.rpa.errors import NavigationError

logger = logging.getLogger(__name__)

# Direct URL to "Facturación → Generar facturas". Found via inspection of the
# jQuery UI menu (see docs/ARCHITECTURE.md § Bot flow). Navigating directly
# avoids fragile menu-hover/click interactions.
GENERATE_INVOICE_PATH = "/facturacion/facturacion/consulta_ordenes_facturar"


def navigate_to_generate_invoice(driver: WebDriver) -> None:
    """Open the 'Facturación → Generar facturas' page. Assumes the user is already logged in."""
    settings = get_settings()
    target_url = f"{settings.portal_url.rstrip('/')}{GENERATE_INVOICE_PATH}"

    logger.info(f"step=navigate action=goto url={target_url}")
    driver.get(target_url)

    # Success criterion: the convenio select is present in the DOM.
    try:
        waits.wait_present(driver, By.ID, "convenios_facturas")
    except TimeoutException as exc:
        raise NavigationError(
            f"generate-invoice page did not load (did not find #convenios_facturas at {driver.current_url})"
        ) from exc

    logger.info("step=navigate action=success")
