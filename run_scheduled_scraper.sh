#!/bin/bash

# --- Configuration ---
# ABSOLUTE PATH to your project directory on the host machine.
# IMPORTANT: Replace /home/other_animal/test_scraper with your actual absolute path!
PROJECT_PATH="/home/other_animal/test_scraper" 

# Your Docker image name
IMAGE_NAME="test-scraper"

# A unique name for your container instance when scheduled
CONTAINER_NAME="my-scheduled-scraper-instance"

# Absolute path for a log file where this script's stdout/stderr will go
# This is useful for debugging the cron job itself.
SCRIPT_LOG_FILE="${PROJECT_PATH}/cron_script_output.log"

# --- Script Logic ---

# Redirect all stdout and stderr of this script to the log file
exec >> "${SCRIPT_LOG_FILE}" 2>&1

echo "--- $(date): Starting scheduled scraper run ---"

# Stop and remove any previous instance of the container
# This ensures a clean run every time and prevents "name already in use" errors.
# `2>/dev/null || true` prevents errors if the container doesn't exist or isn't running.
echo "$(date): Checking for and stopping/removing existing container '${CONTAINER_NAME}'..."
docker stop "${CONTAINER_NAME}" 2>/dev/null || true
docker rm "${CONTAINER_NAME}" 2>/dev/null || true
echo "$(date): Cleaned up old container (if any)."

# Run the Docker container in detached mode (-d)
# Use absolute paths for volume mounts for cron compatibility.
echo "$(date): Starting new container '${CONTAINER_NAME}'..."
docker run -d \
  --name "${CONTAINER_NAME}" \
  -e LOG_LEVEL=INFO \
  -v "${PROJECT_PATH}/logs:/app/logs" \
  -v "${PROJECT_PATH}/output:/app/output" \
  "${IMAGE_NAME}"

# Optional: Add a short delay to allow the container to start and log its initial status
sleep 5

# Check if the container started successfully
echo "--- $(date): Scheduled scraper run initiated. Check docker logs ${CONTAINER_NAME} ---"