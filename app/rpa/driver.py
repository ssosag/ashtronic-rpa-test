import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def create_driver() -> webdriver.Remote:
    """Connect to the remote Selenium hub and return a configured WebDriver."""
    settings = get_settings()

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")

    logger.info(f"connecting to selenium hub at {settings.selenium_hub_url}")
    driver = webdriver.Remote(
        command_executor=settings.selenium_hub_url,
        options=options,
    )
    # Explicit waits only — no implicit waits mixing with them
    driver.implicitly_wait(0)
    driver.set_page_load_timeout(settings.selenium_timeout * 2)
    logger.info("webdriver session started")
    return driver
