import logging
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from app.core.config import get_settings
from app.rpa import waits
from app.rpa.errors import InvalidCredentialsError, LoginError

logger = logging.getLogger(__name__)


def login(driver: WebDriver) -> None:
    """Log into the Hiruko Prodiagnóstico portal using credentials from settings."""
    settings = get_settings()
    login_url = f"{settings.portal_url.rstrip('/')}/login"

    logger.info(f"step=login action=navigate url={login_url}")
    driver.get(login_url)

    try:
        username_input = waits.wait_visible(driver, By.ID, "username")
        password_input = driver.find_element(By.ID, "password")
        submit_button = driver.find_element(By.ID, "_submit")
    except TimeoutException as exc:
        raise LoginError(f"login form did not render: {exc}") from exc

    logger.info("step=login action=fill_credentials")
    username_input.clear()
    username_input.send_keys(settings.portal_user)
    password_input.clear()
    password_input.send_keys(settings.portal_password)

    logger.info("step=login action=submit")
    submit_button.click()

    # Success criterion: URL no longer contains `/login` AND the main menu appears
    try:
        waits.wait_present(driver, By.ID, "menuPrincipal")
    except TimeoutException as exc:
        current_url = driver.current_url
        # Still on /login after submit → portal rejected credentials. Not retryable.
        if "/login" in current_url:
            raise InvalidCredentialsError(
                f"portal rejected credentials (still at {current_url})"
            ) from exc
        # Not on /login but menu missing → possibly transient (slow render, network glitch).
        raise LoginError(
            f"main menu not found after submit (current_url={current_url})"
        ) from exc

    logger.info(f"step=login action=success current_url={driver.current_url}")
