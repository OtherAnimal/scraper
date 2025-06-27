# Test Scrapper

A robust and automated web scraper designed to extract real estate listings from `ceresne.sk`.

## Table of Contents

-   [What This Program Does](#what-this-program-does)
-   [What This Program Doesn't Do (Limitations)](#what-this-program-doesnt-do-limitations)
-   [Prerequisites](#prerequisites)
-   [Project Structure](#project-structure)
-   [Setup & Installation](#setup--installation)
-   [Usage](#usage)
    -   [Manual Run](#manual-run)
    -   [Configuration (Logging Level)](#configuration-logging-level)
-   [Scheduled Execution (Automation with Cron)](#scheduled-execution-automation-with-cron)
-   [Output Files](#output-files)
-   [Troubleshooting & Checking Logs](#troubleshooting--checking-logs)
-   [Future Improvements](#future-improvements)
-   [License](#license)
-   [Contact](#contact)

---

## What This Program Does

This program automates the extraction of real estate listing data from the [ceresne website](https://www.ceresne.sk/ponuka-byvania/).

Key features include:

* **Full Pagination Scraping:** Navigates through all available pagination pages to collect every listing URL.
* **Detailed Listing Data Extraction:** For each listing, it visits the product detail page to extract comprehensive information, including:
    * URL
    * Stage
    * Apartment Number
    * Floor
    * Total Area
    * Number of Rooms
    * Internal Area
    * External Area
    * Status
    * Price with VAT
    * Discounted Price
* **Headless Browser Automation:** Utilizes Selenium with a headless Chrome browser (running inside Docker) for efficient and robust interaction with dynamic web content.
* **Automated Scheduling:** Designed to work repeatedly via a scheduled Docker run command using `cron`, ensuring daily data collection (configured for 3:00 AM daily by default).
* **Containerized Execution:** Runs entirely within a Docker container, providing an isolated, consistent, and easily deployable environment.
* **Robust Logging:** Implements structured logging to track scraper progress, information, warnings, and errors, with output directed to both the console and a persistent log file.
* **CSV Output:** Saves all scraped data into a structured CSV file for easy analysis and import into databases or spreadsheets.

## What This Program Doesn't Do (Limitations)

This scraper is designed for a specific task and has the following limitations:

* **No CAPTCHA/Bot Detection Bypassing:** It does not include logic for bypassing CAPTCHAs, IP rate limiting, or advanced bot detection mechanisms.
* **No Proxy Rotation:** It does not use proxies, meaning all requests originate from the same IP address (your host's or your Docker container's external IP).
* **No Database Integration:** Scraped data is only saved to a CSV file; there's no direct integration with a database.
* **No Advanced Error Recovery:** While it logs unexpected errors, it doesn't have sophisticated retry mechanisms for network failures or broken element selectors beyond what's inherent in Python/Selenium.
* **Site Structure Changes:** It relies on the current HTML structure of `ceresne.sk`. Significant changes to the website's layout or element IDs/classes may break the scraper.
* **Rate Limiting:** Does not implement explicit delays between requests, relying on implicit page load times. This might be an issue if the target site implements aggressive rate limiting.

## Prerequisites

Before you can run this scraper, you need to have the following installed on your system:

* **Git:** For cloning the repository.
    * [Download Git](https://git-scm.com/downloads)
* **Docker:** The platform used to build and run the containerized scraper.
    * [Install Docker Engine](https://docs.docker.com/engine/install/)

## Project Structure

```

.
├── Dockerfile                  \# Defines the Docker image for the scraper
├── scraper.py                  \# The main Python script for scraping
|── webdriver.py                \# Utilities for configuring and initializing a Selenium Chrome WebDriver
├── requirements.txt            \# Python dependencies for the scraper
├── run\_scheduled\_scraper.sh    \# Shell script for cron scheduling
└── utils/
└──── logging\_config.py       \# Centralized logging configuration

````

## Setup & Installation

Follow these steps to get the scraper running on your system:

1.  **Clone the Repository:**
    First, clone this repository to your local machine. Replace `your-username` and `your-repo-name` with your actual GitHub username and the name you gave your repository.

    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```
    *Example:* If your username is `johndoe` and your repository is named `ceresne-scraper`, the commands would be:
    ```bash
    git clone [https://github.com/johndoe/ceresne-scraper.git](https://github.com/johndoe/ceresne-scraper.git)
    cd ceresne-scraper
    ```

2.  **Build the Docker Image:**
    This command reads the `Dockerfile` and creates a Docker image named `test-scraper`.
    ```bash
    docker build -t test-scraper .
    ```
    *Note: If you encounter issues with Chromedriver, ensure the `CHROMEDRIVER_VERSION` in your Dockerfile matches the `google-chrome-stable` version installed.*

3.  **Create Output and Log Directories on Host:**
    These directories will be mounted into the Docker container to persist your scraped data and application logs.
    ```bash
    mkdir -p ./logs ./output
    ```

## Usage

### Manual Run

You can run the scraper manually in Docker for testing or a one-off execution.

```bash
docker run \
  -e LOG_LEVEL=INFO \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/output:/app/output" \
  test-scraper
````

  * `-e LOG_LEVEL=INFO`: Sets the minimum logging level that will appear on the console (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). File logs capture `DEBUG` level by default.
  * `-v "$(pwd)/logs:/app/logs"`: Mounts your host's `./logs` directory to `/app/logs` inside the container for persistent application logs.
  * `-v "$(pwd)/output:/app/output"`: Mounts your host's `./output` directory to `/app/output` inside the container for persistent CSV output.

The scraper will execute, save data to `ceresne_flats.csv` in your host's `./output` directory, and write logs to your host's `./logs` directory. The container will exit once the scraping is complete.

### Configuration (Logging Level)

You can control the verbosity of console output using the `LOG_LEVEL` environment variable:

  * `INFO` (default): Standard progress messages.
  * `DEBUG`: Highly detailed messages, useful for debugging.
  * `WARNING`: Potentially problematic events.
  * `ERROR`: Errors that prevent normal operation.
  * `CRITICAL`: Severe errors that may lead to program termination.

Example for `DEBUG` level console output:

```bash
docker run -e LOG_LEVEL=DEBUG -v "$(pwd)/logs:/app/logs" -v "$(pwd)/output:/app/output" test-scraper
```

## Scheduled Execution (Automation with Cron)

The scraper can be scheduled to run automatically using `cron` (on Linux/macOS).

1.  **Ensure `run_scheduled_scraper.sh` is Executable:**

    ```bash
    chmod +x run_scheduled_scraper.sh
    ```

2.  **Edit the `run_scheduled_scraper.sh` Script:**
    Open `run_scheduled_scraper.sh` in a text editor and **set the `PROJECT_PATH` variable** to the absolute path of your project directory on your host machine.
    Example: `PROJECT_PATH="/home/your_username/your_project_name"`

3.  **Open your Crontab for Editing:**

    ```bash
    crontab -e
    ```

    (If prompted, choose a text editor like `nano`.)

4.  **Add a new line to schedule the script:**
    To run the scraper every day at 3:00 AM (local server time):

    ```cron
    # m h  dom mon dow   command
    0 3 * * * /home/other_animal/test_scraper/run_scheduled_scraper.sh
    ```

      * **Explanation:**
          * `0`: Minute (0)
          * `3`: Hour (3 AM)
          * `*`: Every day of the month
          * `*`: Every month
          * `*`: Every day of the week
          * `/home/other_animal/test_scraper/run_scheduled_scraper.sh`: The absolute path to your script.

5.  **Save and Exit:**

      * For `nano`: Press `Ctrl+O`, then `Enter`, then `Ctrl+X`.
      * You should see `crontab: installing new crontab`.

Your scraper will now automatically run according to the schedule.

## Output Files

All output files will be saved directly to your host machine due to the volume mounts.

  * **Scraped Data:**
      * `./output/ceresne_flats.csv`
  * **Application Logs (from scraper inside Docker):**
      * `./logs/scraper.log`
  * **Cron Job Script Logs (for debugging the cron job itself):**
      * `./cron_script_output.log`

## Troubleshooting & Checking Logs

If your scraper isn't performing as expected:

1.  **Check Cron Job Execution:**
      * Inspect the script's output log to see if the `docker run` command itself executed correctly:
        ```bash
        tail -f ./cron_script_output.log
        ```
2.  **Check Scraper Application Logs:**
      * Review the detailed logs from your scraper for errors, warnings, or unexpected behavior:
        ```bash
        tail -f ./logs/scraper.log
        ```
      * If the container is still running, you can also use `docker logs my-scheduled-scraper-instance` to see its `stdout`.
3.  **Run Manually with `DEBUG` Logging:**
      * Execute the `docker run` command with `-e LOG_LEVEL=DEBUG` to get more verbose output for debugging.

## Future Improvements

  * Implement proper error handling and retry mechanisms for network issues or failed page loads.
  * Add proxy rotation to avoid IP blocking.
  * Integrate with a database (e.g., PostgreSQL, SQLite) for storing scraped data instead of just CSV.
  * Use a more sophisticated scheduler (e.g., Apache Airflow, Docker Compose with custom entrypoints) for more complex workflows.
  * Implement data validation and cleaning steps.
  * Build a notification system (e.g., email, Slack) for critical errors or successful runs.

## License

MIT License

-----

## Contact

Natalia Egorova - [GitHub Profile Link](https://github.com/OtherAnimal)

-----
