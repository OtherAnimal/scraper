import requests
from bs4 import BeautifulSoup
import csv
import re
import time # Added for potential delays if needed

# Import the WebDriver functions from your updated webdriver.py
from webdriver_chrome import get_chrome_driver, quit_driver # Will now import the Chrome functions

BASE = "https://www.ceresne.sk"
LIST_URL = BASE + "/ponuka-byvania/"
HEADERS = {"User-Agent": "Mozilla/5.0"} # Still useful for requests.get()

def get_listing_links_selenium(driver):
    """
    Extracts flat detail URLs using Selenium for dynamic content.
    """
    print(f"Navigating to {LIST_URL} with Selenium...")
    driver.get(LIST_URL)
    # Give the page some time to load dynamic content.
    # In a real scenario, use WebDriverWait and expected_conditions
    # to wait for specific elements to appear.
    time.sleep(5) # Adjust as needed, or replace with explicit waits

    # Get the page source after dynamic content has loaded
    soup = BeautifulSoup(driver.page_source, "lxml")

    links = []
    print("Extracting links from Selenium-rendered page...")
    for tr in soup.find_all("tr", attrs={"x-on:click": True}):
        onclick_value = tr["x-on:click"]
        # The regex needs to account for the full URL and the ', event)' part
        match = re.search(r"goToFlat\('([^']+)'", onclick_value)
        if match and "/ponuka-bytov/byt/" in match.group(1):
            links.append(match.group(1))
            print(f"Found Link: {match.group(1)}") # Uncomment for debugging

    # Remove duplicates
    unique_links = list(set(links))
    print(f"Found {len(unique_links)} unique listing links.")
    return unique_links


def parse_flat_detail_requests(url):
    """
    Parses flat detail from a URL using requests (assuming static content).
    """
    print(f"Parsing detail for: {url} with requests...")
    resp = requests.get(url, headers=HEADERS)
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
    Uses Selenium to get listing links and requests to parse details.
    """
    driver = None # Initialize driver to None
    all_rows = []
    try:
        print("Starting WebDriver...")
        driver = get_chrome_driver(headless=True) # This will now call your Chrome setup

        # Use Selenium to get the initial list of links
        links = get_listing_links_selenium(driver)

        # Now, iterate through the links and parse details using requests
        # (assuming detail pages don't require JavaScript)
        print("Parsing detail pages using requests...")
        for url in links:
            detail_data = parse_flat_detail_requests(BASE + url) # Prepend BASE to relative URLs
            all_rows.append(detail_data)

        if all_rows:
            print(f"Successfully scraped {len(all_rows)} flat details.")
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
        print(f"An error occurred in run_scraper: {e}")
    finally:
        # Ensure the driver is quit and profile cleaned up, even if errors occur
        print("Quitting WebDriver and cleaning up...")
        quit_driver(driver)

if __name__ == "__main__":
    run_scraper()