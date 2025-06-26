import requests
from bs4 import BeautifulSoup
import csv
import re
import time 

from webdriver_chrome import get_chrome_driver, quit_driver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException


BASE = "https://www.ceresne.sk"
LIST_URL = BASE + "/ponuka-byvania/"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_all_listing_links_with_pagination(driver):
    """
    Extracts all flat detail URLs across all paginated pages using Selenium.
    """
    print(f"Navigating to {LIST_URL} with Selenium for pagination...")
    driver.get(LIST_URL)

    wait = WebDriverWait(driver, 20)

    all_links = set()
    current_page_num = 1

    while True:
        print(f"\n--- Scraping Page {current_page_num} ---")

        try:
            # Wait for the main content (e.g., the first 'tr' with x-on:click) to be present
            # CSS Selector is good for attributes with colons
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr[x-on\\:click*='goToFlat']")))
            print("Listings content loaded.")
        except TimeoutException:
            print("Timeout waiting for listings to appear. Exiting pagination loop.")
            break

        soup = BeautifulSoup(driver.page_source, "lxml")

        print("Extracting links from current page...")
        for tr in soup.find_all("tr", attrs={"x-on:click": True}):
            onclick_value = tr["x-on:click"]
            match = re.search(r"goToFlat\('([^']+)'", onclick_value)
            if match and "/ponuka-bytov/byt/" in match.group(1):
                full_link = match.group(1)
                all_links.add(full_link)

        print(f"Total unique links found so far: {len(all_links)}")

        # 2. Find pagination buttons
        # Change 1: Use local-name() for x-on:click attribute in XPath, or CSS Selector
        try:
            # Option A: Using local-name() in XPath (more robust for varied attribute names)
            # This selects button elements that are children of li, and have an attribute
            # whose local name is 'click' and its value contains 'setPage('.
            pagination_buttons = wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//li/button[contains(./@*[local-name()='click'], 'setPage(')]"))
            )
            # Option B: Using CSS Selector (often simpler for attributes with colons)
            # pagination_buttons = wait.until(
            #    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li > button[x-on\\:click*='setPage']"))
            # )
            
            print(f"Found {len(pagination_buttons)} pagination buttons.")
        except TimeoutException:
            print("No pagination buttons found on the page. Assuming single page or end of pagination.")
            break

        next_page_button = None
        
        # We need to re-find elements after each page load because of StaleElementReferenceException.
        # So we get all buttons again and iterate to find the one we need.

        # Re-find pagination buttons to avoid StaleElementReferenceException
        # Use the same locator as above
        pagination_buttons_current_dom = driver.find_elements(By.XPATH, "//li/button[contains(./@*[local-name()='click'], 'setPage(')]")
        # OR:
        # pagination_buttons_current_dom = driver.find_elements(By.CSS_SELECTOR, "li > button[x-on\\:click*='setPage']")


        # Try to find the button for the next sequential page number (current_page_num + 1)
        for button in pagination_buttons_current_dom:
            button_text = button.text.strip()
            if button_text.isdigit() and int(button_text) == current_page_num + 1:
                # Check if this button's parent <li> is NOT active
                try:
                    parent_li_class = button.find_element(By.XPATH, "..").get_attribute("class")
                    if "active" not in parent_li_class:
                        next_page_button = button
                        print(f"Found button for page {current_page_num + 1}.")
                        break # Found the next page number button, exit inner loop
                    else:
                        print(f"Page {current_page_num + 1} button is active, likely reached end.")
                except NoSuchElementException:
                    # Parent li not found, might be an unexpected structure, but continue
                    next_page_button = button # Assume it's the right one
                    print(f"Found button for page {current_page_num + 1}, parent LI not found.")
                    break

        # If no specific next page number button was found, look for a "Next" button
        if not next_page_button:
            for button in pagination_buttons_current_dom:
                button_text = button.text.strip().lower()
                if button_text == "next":
                    try:
                        parent_li_class = button.find_element(By.XPATH, "..").get_attribute("class")
                        if "active" not in parent_li_class:
                            next_page_button = button
                            print("Found 'Next' button.")
                            break # Found the Next button, exit inner loop
                        else:
                            print("Found 'Next' button but it's on an active (current) page. Assuming end of pagination.")
                    except NoSuchElementException:
                        next_page_button = button # Assume it's the right one
                        print("Found 'Next' button, parent LI not found.")
                        break

        if next_page_button:
            try:
                driver.execute_script("arguments[0].click();", next_page_button)
                current_page_num += 1
                print(f"Clicked to navigate to page {current_page_num}. Waiting for content to load...")
                
                # IMPORTANT WAIT: Wait for the new page's active button to appear
                wait.until(
                    EC.presence_of_element_located((By.XPATH, f"//li[contains(@class, 'active')]/button[text()='{current_page_num}']"))
                )
                print(f"Page {current_page_num} loaded successfully.")
                time.sleep(1) # Small buffer
                
            except (TimeoutException, StaleElementReferenceException) as e:
                print(f"Error during page navigation or waiting for new content: {e}")
                print("Likely reached the last page or an unexpected state. Exiting pagination loop.")
                break
        else:
            print("No more pagination buttons to click. Reached last page.")
            break

    print(f"\nFinished pagination. Collected {len(all_links)} unique flat listing links.")
    return list(all_links)


def parse_flat_detail_requests(url):
    """
    Parses flat detail from a URL using requests (assuming static content).
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
    """
    driver = None
    all_rows = []
    try:
        print("Starting WebDriver...")
        driver = get_chrome_driver(headless=True)

        links = get_all_listing_links_with_pagination(driver)

        print("\nParsing detail pages using requests...")
        for url_suffix in links:
            full_url = BASE + url_suffix
            detail_data = parse_flat_detail_requests(full_url)
            if detail_data:
                all_rows.append(detail_data)

        if all_rows:
            print(f"\nSuccessfully scraped {len(all_rows)} flat details.")
            output_filename = "ceresne_flats.csv"
            with open(output_filename, "w", newline="", encoding="utf8") as f:
                fieldnames = [
                    "url", "stage", "apartment number", "floor", "total area",
                    "rooms", "internal area", "external area", "status",
                    "price with VAT", "discounted price"
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