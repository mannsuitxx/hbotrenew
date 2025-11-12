#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing Google Chrome..."

# 1. Install dependencies
apt-get update
apt-get install -y wget unzip

# 2. Download and Install Google Chrome
# We still need the browser itself installed on the system.
CHROME_VERSION="117.0.5938.149"
wget -q https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip
unzip chrome-linux64.zip
mv chrome-linux64 /opt/chrome
ln -s /opt/chrome/chrome /usr/local/bin/google-chrome

# 3. Install Python dependencies
# This will install selenium, selenium-stealth, and webdriver-manager.
# When the script runs, webdriver-manager will automatically download the correct chromedriver.
pip install -r requirements.txt

echo "Build script finished."
