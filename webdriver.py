"""
This script uses Selenium library configures
and initializes a Chrome WebDriver instance
for web scraping tasks, particularly in a headless mode
suitable for environments like WSL (Windows Subsystem for Linux).
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeDriverService

# from selenium.webdriver.remote.remote_connection import RemoteConnection
from webdriver_manager.chrome import ChromeDriverManager

import logging

# --- Configuration (Chrome)---
# IMPORTANT: Replace with the actual path to your Chrome executable.
# Author's specific case: Chrome is installed directly in the WSL distribution
CHROME_BINARY_PATH = "/usr/bin/google-chrome"

# Get a logger for the current module. The name will automatically be 'webdriver'
logger = logging.getLogger(__name__)


def get_chrome_driver(headless=True, browser_timeout_seconds=240):
    """
    Initializes and returns a configured Chrome WebDriver instance.

    Parameters:
    headless (bool): If True, runs Chrome in headless mode (no GUI).
                        Defaults to True for performance.
    browser_timeout_seconds (int): Timeout in seconds for page loads and script execution.
                                    Defaults to 240 seconds (4 minutes).

    Returns:
        selenium.webdriver.Chrome: The initialized Chrome WebDriver object.
    """
    logger.info("Setting up Chrome WebDriver...")

    options = ChromeOptions()
    options.binary_location = CHROME_BINARY_PATH

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Options for headless stability below
        options.add_argument(
            "--window-size=1920,1080"
        )  # Specify a window size, sometimes helps
        options.add_argument(
            "--disable-extensions"
        )  # Disable extensions, can reduce overhead
        options.add_argument(
            "--proxy-server='direct://'"
        )  # Bypass proxy if one is configured
        options.add_argument("--proxy-bypass-list=*")  # Bypass proxy for all hosts
        options.add_argument(
            "--start-maximized"
        )  # Start maximized, can help with viewport
        options.add_argument(
            "--disable-setuid-sandbox"
        )  # Redundant with --no-sandbox but safe
        options.add_argument(
            "--disable-web-security"
        )  # Can help with cross-origin issues
        options.add_argument(
            "--allow-running-insecure-content"
        )  # Related to web security
        # options.add_argument("--remote-debugging-port=9222") # Can open a debugging port, useful for manual inspection
        logger.info("Running Chrome in headless mode.")
    else:
        logger.info("Running Chrome with GUI.")

    service = ChromeDriverService(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    logger.info("Chrome WebDriver initialized.")

    return driver


def quit_driver(driver):
    """
    Quits the WebDriver.
    """
    if driver:
        driver.quit()
        logger.info("WebDriver quit successfully.")


# --- Main execution block (for testing webdriver.py directly) ---
if __name__ == "__main__":
    driver = None
    try:
        driver = get_chrome_driver(
            headless=True, browser_timeout_seconds=300
        )  # Test with 5 min timeouts
        driver.get("https://www.google.com")
        logger.info(f"Page Title: {driver.title}")
    except Exception as e:
        logger.critical(f"An error occurred during direct execution: {e}")
    finally:
        quit_driver(driver)
