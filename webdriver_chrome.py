import os
import tempfile # Still imported, though not directly used for Chrome profiles here
import shutil # Still imported, though not directly used for Chrome profiles here
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeDriverService
# from selenium.webdriver.remote.remote_connection import RemoteConnection # Not directly needed for this fix
from webdriver_manager.chrome import ChromeDriverManager


# --- Configuration (Chrome)---
# IMPORTANT: Replace with the actual path to your Chrome executable.
# Common paths for Chrome/Chromium on WSL/Linux:
# "/usr/bin/google-chrome"
# "/usr/bin/chromium-browser"
# On Windows, it would be something like "C:/Program Files/Google/Chrome/Application/chrome.exe"
# If running on WSL and Chrome is installed on Windows:
CHROME_BINARY_PATH = "/usr/bin/google-chrome" # Google Chrome in WSL
# OR if Chrome is installed directly in your WSL distribution:
# CHROME_BINARY_PATH = "/usr/bin/google-chrome"


def get_chrome_driver(headless=True, browser_timeout_seconds=240): # Renamed timeout for clarity
    """
    Initializes and returns a configured Chrome WebDriver instance.

    Args:
        headless (bool): If True, runs Chrome in headless mode (no GUI).
                         Defaults to True for performance.
        browser_timeout_seconds (int): Timeout in seconds for page loads and script execution.
                                       Defaults to 240 seconds (4 minutes).

    Returns:
        selenium.webdriver.Chrome: The initialized Chrome WebDriver object.
    """
    print("Setting up Chrome WebDriver...")

    options = ChromeOptions()
    options.binary_location = CHROME_BINARY_PATH

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # --- ADD THESE ADDITIONAL OPTIONS FOR HEADLESS STABILITY ---
        options.add_argument("--window-size=1920,1080") # Specify a window size, sometimes helps
        options.add_argument("--disable-extensions") # Disable extensions, can reduce overhead
        options.add_argument("--proxy-server='direct://'") # Bypass proxy if one is configured
        options.add_argument("--proxy-bypass-list=*") # Bypass proxy for all hosts
        options.add_argument("--start-maximized") # Start maximized, can help with viewport
        options.add_argument("--disable-setuid-sandbox") # Redundant with --no-sandbox but safe
        options.add_argument("--disable-web-security") # Can help with cross-origin issues
        options.add_argument("--allow-running-insecure-content") # Related to web security
        # options.add_argument("--remote-debugging-port=9222") # Can open a debugging port, useful for manual inspection
        # --------------------------------------------------------
        print("Running Chrome in headless mode.")
    else:
        print("Running Chrome with GUI.")

    service = ChromeDriverService(ChromeDriverManager().install())

    # --- REMOVE THIS LINE: service.command_executor.set_timeout(connection_timeout) ---
    # This line was causing the AttributeError.

    driver = webdriver.Chrome(service=service, options=options)
    print("Chrome WebDriver initialized.")

    # --- ADD these lines to set timeouts on the driver instance AFTER it's created ---
    # These timeouts apply to subsequent operations, not the initial connection.
    # Set the page load timeout (how long to wait for a page to load)
    driver.set_page_load_timeout(browser_timeout_seconds)
    # Set the script timeout (how long an asynchronous script can run)
    driver.set_script_timeout(browser_timeout_seconds)
    # You can also set implicit waits if needed:
    # driver.implicitly_wait(10) # waits up to 10 seconds for elements to appear

    return driver

def quit_driver(driver):
    """
    Quits the WebDriver.
    """
    if driver:
        driver.quit()
        print("WebDriver quit successfully.")


# --- Main execution block (for testing webdriver.py directly) ---
if __name__ == "__main__":
    driver = None
    try:
        driver = get_chrome_driver(headless=True, browser_timeout_seconds=300) # Test with 5 min timeouts
        driver.get("https://www.google.com")
        print(f"Page Title: {driver.title}")
    except Exception as e:
        print(f"An error occurred during direct execution: {e}")
    finally:
        quit_driver(driver)