# Test Scrapper

A robust and automated web scraper designed to extract real estate listings from `ceresne.sk`, now complemented by an interactive Streamlit dashboard for data visualization.

## Table of Contents

-   [What This Program Does](#what-this-program-does)
-   [What This Program Doesn't Do (Limitations)](#what-this-program-doesnt-do-limitations)
-   [Prerequisites](#prerequisites)
-   [Project Structure](#project-structure)
-   [Setup & Installation (Scraper)](#setup--installation-scraper)
-   [Usage (Scraper)](#usage-scraper)
    -   [Manual Run](#manual-run)
    -   [Configuration (Logging Level)](#configuration-logging-level)
-   [Scheduled Execution (Automation with Cron)](#scheduled-execution-automation-with-cron)
-   [Streamlit Dashboard](#streamlit-dashboard)
    -   [Setup & Installation (Dashboard)](#setup--installation-dashboard)
    -   [Usage (Dashboard)](#usage-dashboard)
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
    * Rooms
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
* **Interactive Streamlit Dashboard:** Visualizes the scraped data with interactive charts, providing insights into price distribution, area vs. price relationships, and other key metrics.

## What This Program Doesn't Do (Limitations)

This scraper and dashboard are designed for a specific task and have the following limitations:

* **No CAPTCHA/Bot Detection Bypassing:** It does not include logic for bypassing CAPTCHAs, IP rate limiting, or advanced bot detection mechanisms.
* **No Proxy Rotation:** It does not use proxies, meaning all requests originate from the same IP address (your host's or your Docker container's external IP).
* **No Database Integration:** Scraped data is only saved to a CSV file; there's no direct integration with a database for either the scraper or the dashboard.
* **No Advanced Error Recovery:** While it logs unexpected errors, it doesn't have sophisticated retry mechanisms for network failures or broken element selectors beyond what's inherent in Python/Selenium.
* **Site Structure Changes:** It relies on the current HTML structure of `ceresne.sk`. Significant changes to the website's layout or element IDs/classes may break the scraper.
* **Rate Limiting:** Does not implement explicit delays between requests, relying on implicit page load times. This might be an issue if the target site implements aggressive rate limiting.
* **Dashboard Live Refresh:** The Streamlit dashboard loads data from the CSV at startup; it does not automatically refresh when the underlying CSV file changes unless the app is restarted.
* **Limited Dashboard Interactivity:** While charts are interactive, the dashboard does not include advanced user controls for filtering or custom analysis beyond basic chart interactions.

## Prerequisites

Before you can run this project, you need to have the following installed on your system:

* **Git:** For cloning the repository.
    * [Download Git](https://git-scm.com/downloads)
* **Docker:** The platform used to build and run the containerized scraper.
    * [Install Docker Engine](https://docs.docker.com/engine/install/)
* **Python 3.8+:** For running the Streamlit dashboard and managing its dependencies.
    * [Download Python](https://www.python.org/downloads/)
    * **Recommended:** Use a **Linux environment** (e.g., via WSL on Windows) for seamless integration with Docker and cron scheduling.

## Project Structure

```

.
├── Dockerfile                  \# Defines the Docker image for the scraper
├── scraper.py                  \# The main Python script for scraping
├── webdriver.py                \# Utilities for configuring and initializing a Selenium Chrome WebDriver
├── requirements.txt            \# Python dependencies for the *scraper* (inside Docker)
├── run\_scheduled\_scraper.sh    \# Shell script for cron scheduling
├── dashboard\_app.py            \# The Streamlit application script for data visualization
├── requirements-dashboard.txt  \# Python dependencies for the *Streamlit dashboard*
└── utils/
└── logging\_config.py       \# Centralized logging configuration
└── logs/                       \# Directory for scraper logs (created by setup)
└── output/                     \# Directory for scraped CSV data (created by setup)

````

## Setup & Installation (Scraper)

Follow these steps to get the scraper running on your system:

1.  **Clone the Repository:**
    First, clone this repository to your local machine.

    ```bash
    git clone [https://github.com/OtherAnimal/scraper.git](https://github.com/OtherAnimal/scraper.git)
    cd scraper
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

## Usage (Scraper)

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
    # m h  dom mon dow   command
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

## Streamlit Dashboard

This project includes an interactive Streamlit dashboard to visualize the data collected by the scraper.

### Setup & Installation (Dashboard)

The Streamlit dashboard runs directly on your host machine (within a Python virtual environment), not inside Docker.

1.  **Navigate to your Project Directory:**

    ```bash
    cd /home/other_animal/test_scraper/
    ```

2.  **Create a Python Virtual Environment:**
    It's highly recommended to use a virtual environment to manage dashboard dependencies separately.

    ```bash
    python3 -m venv ./.venv
    ```

3.  **Activate the Virtual Environment:**

    ```bash
    source ./.venv/bin/activate
    ```

    Your terminal prompt should show `(.venv)` (or `(venv)`) indicating the environment is active.

4.  **Generate and Install Dashboard Dependencies:**
    First, ensure you have a `requirements-dashboard.txt` file listing all the Python libraries for the Streamlit app. This project uses `streamlit`, `pandas`, and `plotly`. If you don't have this file, create it by running `pip freeze > requirements-dashboard.txt` (after installing these libraries, if not already present).

    ```bash
    pip install -r requirements-dashboard.txt
    ```

### Usage (Dashboard)

1.  **Ensure Scraped Data is Available:**
    Run the scraper at least once to generate the `ceresne_flats.csv` file in the `./output/` directory, as the dashboard relies on this data.

2.  **Navigate to your Project Directory and Activate Virtual Environment:**

    ```bash
    cd /home/other_animal/test_scraper/
    source ./.venv/bin/activate
    ```

3.  **Run the Streamlit App:**

    ```bash
    streamlit run dashboard_app.py
    ```

4.  **Access the Dashboard:**
    Once the command runs, Streamlit will typically open a new tab in your web browser with the dashboard, usually at `http://localhost:8501`. If it doesn't open automatically, copy and paste the provided URL into your browser.

## Output Files

All output files will be saved directly to your host machine due to the volume mounts.

  * **Scraped Data (Consumed by Dashboard):**
      * `./output/ceresne_flats.csv`
  * **Application Logs (from scraper inside Docker):**
      * `./logs/scraper.log`
  * **Cron Job Script Logs (for debugging the cron job itself):**
      * `./cron_script_output.log`

## Troubleshooting & Checking Logs

If your scraper or dashboard isn't performing as expected:

1.  **Check Scraper Execution:**

      * **Cron Job Execution:**
          * Inspect the script's output log to see if the `docker run` command itself executed correctly:
            ```bash
            tail -f ./cron_script_output.log
            ```
      * **Scraper Application Logs:**
          * Review the detailed logs from your scraper for errors, warnings, or unexpected behavior:
            ```bash
            tail -f ./logs/scraper.log
            ```
          * If the container is still running, you can also use `docker logs my-scheduled-scraper-instance` to see its `stdout`.
      * **Run Manually with `DEBUG` Logging:**
          * Execute the `docker run` command with `-e LOG_LEVEL=DEBUG` to get more verbose output for debugging.

2.  **Check Streamlit Dashboard:**

      * **Python Environment:** Ensure your virtual environment is activated (`(.venv)` in your prompt) and `streamlit` is running from within it.
      * **Dependencies:** Verify all dashboard dependencies are installed via `pip list` within the active virtual environment.
      * **File Paths:** Confirm `dashboard_app.py` can correctly find `output/ceresne_flats.csv`.
      * **Browser Console:** Check your browser's developer console (F12) for any JavaScript errors related to the Streamlit app or Plotly charts.

## Future Improvements

  * Implement proper error handling and retry mechanisms for network issues or failed page loads.
  * Add proxy rotation to avoid IP blocking.
  * Integrate with a database (e.g., PostgreSQL, SQLite) for storing scraped data instead of just CSV.
  * Use a more sophisticated scheduler (e.g., Apache Airflow, Docker Compose with custom entrypoints) for more complex workflows.
  * Implement data validation and cleaning steps.
  * Build a notification system (e.g., email, Slack) for critical errors or successful runs.
  * **Dashboard Enhancements:**
      * Add more interactive filters and widgets (e.g., date range, price range sliders).
      * Implement user authentication or access control if deployed publicly.
      * Explore live data refreshing without manual app restarts.
      * Add more diverse chart types or analytical views.

## License

MIT License

-----

## Contact

Natalia Egorova - [GitHub Profile Link](https://github.com/OtherAnimal)

-----
