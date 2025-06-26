"""
This script scrapes real estate listings from the ceresne.sk website.
It uses Selenium for dynamic content and pagination, Requests for detail page fetching,
BeautifulSoup for HTML parsing, and CSV for data storage.
The script extracts all flat detail URLs, parses relevant data fields, and saves the results to a CSV file.
Robust error handling and pagination logic ensure all listings are captured reliably.
"""

import requests
from bs4 import BeautifulSoup
import csv
import re
import time

from webdriver import get_chrome_driver, quit_driver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)


BASE = "https://www.ceresne.sk"
LIST_URL = BASE + "/ponuka-byvania/"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_all_listing_links_with_pagination(driver):
    """
    Extracts all flat detail URLs across all paginated pages using Selenium.

    Parameters:
    driver (selenium.webdriver.Chrome): The initialized Chrome WebDriver object.

    Returns:
    list: A list of unique flat detail URLs.
    """
    print(f"Navigating to {LIST_URL} with Selenium for pagination...")
    driver.get(LIST_URL)

    wait = WebDriverWait(driver, 30)

    all_links = set()

    # Loop indefinitely until explicit break condition is met
    while True:
        # Before scraping, ensure the main content is loaded
        try:
            # Wait for the presence of the listing content
            # Get a reference to one of the listing elements to check for staleness later
            first_listing_element = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "tr[x-on\\:click*='goToFlat']")
                )
            )
            print("Listings content loaded.")
        except TimeoutException:
            print(
                "Timeout waiting for listings to appear on the current page. Exiting pagination loop."
            )
            break
        # Catch other potential WebDriver errors during initial load
        except WebDriverException as e:
            print(
                f"WebDriver error during initial listings load: {e}. Exiting pagination loop."
            )
            break

        # Get the page source *after* content is loaded for BeautifulSoup parsing
        soup = BeautifulSoup(driver.page_source, "lxml")

        # 1. Scrape links from the current page
        print("Extracting links from current page...")
        current_page_links_count = 0
        # Variable to store IDs/identifiers of listings on the current page
        current_page_listing_ids = set()

        # Find all table rows with the specific attribute indicating a listing
        # and extract the onclick value to get the full link
        for tr in soup.find_all("tr", attrs={"x-on:click": True}):
            onclick_value = tr["x-on:click"]
            match = re.search(r"goToFlat\('([^']+)'", onclick_value)
            if match and "/ponuka-bytov/byt/" in match.group(1):
                full_link = match.group(1)
                # Extract a unique identifier from the link for staleness check
                listing_id_match = re.search(
                    r"byt/(\d+)/", full_link
                )  # Assuming ID is in URL like /byt/123/
                if listing_id_match:
                    current_page_listing_ids.add(listing_id_match.group(1))

                if full_link not in all_links:
                    all_links.add(full_link)
                    current_page_links_count += 1

        print(
            f"Found {current_page_links_count} new links on this page. Total unique links found so far: {len(all_links)}"
        )

        # 2. Determine current page number and find the next page button
        pagination_div = None
        try:
            pagination_div = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.pagination"))
                # EC.presence_of_element_located((By.CSS_SELECTOR, "div.pagination.pdt-20"))
            )
            print("Pagination div found.")
        except TimeoutException:
            print(
                "Timeout waiting for pagination div. Assuming single page or end of pagination."
            )
            break
        except NoSuchElementException:
            print(
                "Pagination div not found. Assuming single page or end of pagination."
            )
            break

        all_pagination_buttons_elements = pagination_div.find_elements(
            By.CSS_SELECTOR, "li > button"
        )

        current_active_page_num = 1
        next_page_button_to_click = None

        found_current_active_li = False

        # 3. Identify the current active page number
        for button_el in all_pagination_buttons_elements:
            try:
                parent_li = button_el.find_element(By.XPATH, "..")
                parent_li_class = parent_li.get_attribute("class")

                if "active" in parent_li_class:
                    button_text = button_el.text.strip()
                    if button_text.isdigit():
                        current_active_page_num = int(button_text)
                        found_current_active_li = True
                        print(
                            f"DEBUG: Current active page identified as: {current_active_page_num}"
                        )
                    elif (
                        "pagination-previous" in parent_li_class
                        or "pagination-next" in parent_li_class
                    ):
                        print(
                            "DEBUG: Active class found on 'Previous' or 'Next' button's parent LI."
                        )
                    break
            except (NoSuchElementException, StaleElementReferenceException):
                continue

        if not found_current_active_li:
            print(
                "WARNING: Could not determine the current active page number from 'li.active'. Assuming page 1."
            )

        # 4. Identify the 'Next' button or the next page number button
        try:
            next_li_element = pagination_div.find_element(
                By.CSS_SELECTOR, "li.pagination-next"
            )
            next_button_potential = next_li_element.find_element(By.TAG_NAME, "button")

            onclick_attr = next_button_potential.get_attribute(
                "x-on:click"
            ) or next_button_potential.get_attribute("@click")
            if onclick_attr and "setPage(page + 1)" in onclick_attr:
                if not next_button_potential.get_attribute("disabled"):
                    next_page_button_to_click = next_button_potential
                    print("Identified 'Next' navigation button.")

        except (NoSuchElementException, StaleElementReferenceException):
            print(
                "No 'Next' navigation button (li.pagination-next) found, or it's not clickable/present."
            )

        # If no 'Next' button was found, try to find the next numerical page button
        if not next_page_button_to_click:
            for button_el in all_pagination_buttons_elements:
                button_text = button_el.text.strip()
                if (
                    button_text.isdigit()
                    and int(button_text) == current_active_page_num + 1
                ):
                    try:
                        parent_li = button_el.find_element(By.XPATH, "..")
                        parent_li_class = parent_li.get_attribute("class")
                        if "active" not in parent_li_class:
                            next_page_button_to_click = button_el
                            print(
                                f"Identified numerical button for page {current_active_page_num + 1}."
                            )
                            break
                    except (NoSuchElementException, StaleElementReferenceException):
                        next_page_button_to_click = button_el
                        print(
                            f"DEBUG: Identified numerical button for page {current_active_page_num + 1}, parent LI check failed."
                        )
                        break

        # 5. Click the next page button if available
        if next_page_button_to_click:
            try:
                # Capture an identifier of the first listing *before* the click
                first_listing_link_before_click = ""
                # Attempt to get the onclick value of the first listing `tr`
                first_tr_element_on_page = driver.find_element(
                    By.CSS_SELECTOR, "tr[x-on\\:click*='goToFlat']"
                )
                onclick_value = first_tr_element_on_page.get_attribute("x-on:click")
                match = re.search(r"goToFlat\('([^']+)'", onclick_value)
                if match:
                    first_listing_link_before_click = match.group(1)

                print(
                    f"DEBUG: First listing link before click: {first_listing_link_before_click}"
                )

                driver.execute_script(
                    "arguments[0].click();", next_page_button_to_click
                )
                print(f"Clicked to navigate. Waiting for listings to change...")

                # Wait conditions - robust enough for SPA (Single Page Application) content change:
                # Wait until the first listing element is *stale* (meaning it's been replaced)
                # or wait until the first listing's "onclick" value changes.
                try:
                    # Method 1: Wait for Staleness of the *old* first listing element
                    wait.until(EC.staleness_of(first_tr_element_on_page))
                    print("First listing element from previous page became stale.")
                except TimeoutException:
                    print(
                        "First listing element did not become stale. Trying to detect new content by ID."
                    )
                    # Method 2: If staleness times out (sometimes elements are only updated, not replaced)
                    # Poll for a new listing to appear that is NOT one of the current page's IDs
                    if (
                        current_page_listing_ids
                    ):  # Only if IDs have been actually extracted
                        wait.until(
                            lambda d: any(
                                re.search(
                                    r"byt/(\d+)/", tr.get_attribute("x-on:click")
                                ).group(1)
                                not in current_page_listing_ids
                                for tr in d.find_elements(
                                    By.CSS_SELECTOR, "tr[x-on\\:click*='goToFlat']"
                                )
                                if re.search(
                                    r"byt/(\d+)/", tr.get_attribute("x-on:click")
                                )
                            )
                        )
                        print("New listing content detected.")
                    else:
                        print(
                            "No listing IDs extracted for current page to check for new content. Falling back to active button change."
                        )
                        # As a last resort, wait for the new active button (if the other waits fail)
                        # Note: "current_active_page_num" here refers to the *previous* page's number
                        expected_next_page_num = current_active_page_num + 1
                        wait.until(
                            EC.presence_of_element_located(
                                (
                                    By.XPATH,
                                    f"//div[@class='pagination']//li[contains(@class, 'active')]/button[text()='{expected_next_page_num}']",
                                )
                            )
                            # EC.presence_of_element_located((By.XPATH, f"//div[@class='pagination pdt-20']//li[contains(@class, 'active')]/button[text()='{expected_next_page_num}']"))
                        )
                        print(
                            f"New active page button for page {expected_next_page_num} found (fallback)."
                        )

                print(
                    f"Navigation confirmed. Proceeding to scrape data for current page (now effectively page {current_active_page_num + 1})."
                )
                time.sleep(1)  # Small buffer after confirmation

            except (
                TimeoutException,
                StaleElementReferenceException,
                WebDriverException,
            ) as e:
                print(
                    f"Error during page navigation or waiting for new content after click (expected page {current_active_page_num + 1}): {e}"
                )
                print(
                    "Likely reached the last page or an unexpected state. Exiting pagination loop."
                )
                break
        else:
            print(
                "No suitable pagination button found to click (no next page number or 'Next' button available/non-active). Reached last page."
            )
            break

    print(
        f"\nFinished pagination. Collected {len(all_links)} unique flat listing links."
    )
    return list(all_links)


def parse_flat_detail_requests(url):
    """
    Parses flat detail from a URL using requests (assuming static content).

    Parameters:
    url (str): The URL of the flat detail page.

    Returns:
    dict: A dictionary containing parsed flat details.
    Returns None if parsing fails or page is not found.
    """
    print(f"Parsing detail for: {url} with requests...")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching detail page {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    data = {
        "url": url,
        "stage": None,
        "apartment number": None,
        "floor": None,
        "total area": None,
        "rooms": None,
        "internal area": None,
        "external area": None,
        "status": None,
        "price with VAT": None,
        "discounted price": None,
    }

    # Pattern 1: Vertical label–value blocks
    for div in soup.find_all("div"):
        spans = div.find_all("span", recursive=False)
        if len(spans) >= 2:
            label = spans[0].get_text(strip=True)
            value = spans[1].get_text(strip=True)

            if "Etapa" in label:
                data["stage"] = value
            elif "Označenie" in label:
                data["apartment number"] = value
            elif "Podlažie" in label:
                data["floor"] = value
            elif "Celková výmera" in label:
                data["total area"] = value.replace("m²", "").strip()
            elif "Počet izieb" in label:
                data["rooms"] = value

    # Pattern 2: Horizontal rows
    for row in soup.find_all("div"):
        children = row.find_all("div", recursive=False)
        if len(children) != 2:
            continue

        label = children[0].get_text(strip=True)
        value = children[1].get_text(strip=True)

        if "Výmera interiéru" in label:
            data["internal area"] = value.replace("m²", "").strip()
        elif "Výmera exteriéru" in label:
            data["external area"] = value.replace("m²", "").strip()
        elif "Stav" in label:
            data["status"] = value
        elif "Cenníková cena s DPH" in label:
            data["price with VAT"] = value.replace("€", "").replace(" ", "").strip()
        elif "Zvýhodnená cena" in label:
            data["discounted price"] = value.replace("€", "").replace(" ", "").strip()

    return data


def run_scraper():
    """
    Main function to orchestrate the scraping process.
    Uses Selenium to get listing links with pagination and requests to parse details.

    Parameters:
    None

    Returns:
    None
    """
    driver = None
    all_rows = []

    # Ensure the WebDriver is initialized and ready
    try:
        print("Starting WebDriver...")
        driver = get_chrome_driver(headless=True)

        links = get_all_listing_links_with_pagination(driver)

        print("\nParsing detail pages using requests...")
        # ... (inside run_scraper function) ...

        print("\nParsing detail pages using requests...")

        # Loop through all collected links and parse details
        for full_url in links:
            detail_data = parse_flat_detail_requests(full_url)
            if detail_data:
                all_rows.append(detail_data)

        # Check if any rows were collected
        if all_rows:
            print(f"\nSuccessfully scraped {len(all_rows)} flat details.")
            output_filename = "/app/output/ceresne_flats.csv"
            # Save the results to a CSV file
            with open(output_filename, "w", newline="", encoding="utf8") as f:
                fieldnames = [
                    "url",
                    "stage",
                    "apartment number",
                    "floor",
                    "total area",
                    "rooms",
                    "internal area",
                    "external area",
                    "status",
                    "price with VAT",
                    "discounted price",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_rows)
            print(f"Data saved to {output_filename}")
        else:
            print("No data found or scraped.")

    except Exception as e:
        print(f"An unexpected error occurred in run_scraper: {e}")
    finally:
        print("Quitting WebDriver and cleaning up...")
        if driver:
            quit_driver(driver)


if __name__ == "__main__":
    run_scraper()
