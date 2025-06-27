# Use a lightweight Python base image
FROM python:3.9-slim-buster

# Install system dependencies required for Chrome and Chromedriver
# These typically include libraries for fonts, graphics, and system utilities.
RUN apt-get update && apt-get install -y \
    # Core browser dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxshmfence1 \
    libxcb1 \
    libxrender1 \
    libfontconfig1 \
    libfreetype6 \
    libglib2.0-0 \
    libharfbuzz0b \
    libpng16-16 \
    libwebp6 \
    libxml2 \
    libxslt1.1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    # Additional common dependencies for headless Chrome on Debian
    libappindicator3-1 \
    libasound2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libu2f-udev \
    libvulkan1 \
    # Utilities
    gnupg \
    # For unzip and wget
    unzip \
    wget \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
# The exact version can be pinned, but this usually gets a stable version
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update && apt-get install -y google-chrome-stable

# Install Chromedriver - IMPORTANT: Match this version to your installed Chrome version!
# You'll need to check the exact Chrome version that `google-chrome-stable` installs
# (e.g., by running `google-chrome --version` in a temporary container).
# Then find the corresponding Chromedriver from: https://googlechromelabs.github.io/chrome-for-testing/
ARG CHROMEDRIVER_VERSION="138.0.7204.49" # <--- **UPDATE THIS VERSION**
RUN wget -q https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/local/bin/ \
    && rm chromedriver-linux64.zip \
    && chmod +x /usr/local/bin/chromedriver

# Set the working directory inside the container
WORKDIR /app

# Copy your requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your scraper code into the container
COPY . .

# Ensure CSV output can be accessed outside the container using a volume
# Define a volume where the CSV will be saved inside the container
VOLUME /app/output

# Command to run your scraper when the container starts
# -u flag makes output unbuffered for immediate logging
CMD ["python", "-u", "run_scraper.py"]