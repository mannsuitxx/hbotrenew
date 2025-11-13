
import os
import time
import argparse
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- Configuration ---
HIDENCLOUD_USERNAME = os.environ.get("HIDENCLOUD_USERNAME")
HIDENCLOUD_PASSWORD = os.environ.get("HIDENCLOUD_PASSWORD")
LOGIN_URL = "https://freepanel.hidencloud.com/server/2870cdbb"

def renew_server():
    """
    Logs into HidenCloud, navigates to the server page, and clicks the renew button,
    using undetected-chromedriver to avoid bot detection.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()

    if not HIDENCLOUD_USERNAME or not HIDENCLOUD_PASSWORD:
        print("Error: Please set the HIDENCLOUD_USERNAME and HIDENCLOUD_PASSWORD environment variables.")
        return

    options = uc.ChromeOptions()

    # Enable headless mode if --headless flag is present or if running in CI
    if args.headless or os.environ.get("CI"):
        print("Running in headless mode.")
        options.add_argument("--headless")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("start-maximized")
    
    # For GitHub Actions, the Chrome binary path is in the CHROME_BIN env var
    chrome_bin = os.environ.get("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin
        print(f"Using Chrome binary from CHROME_BIN: {chrome_bin}")

    driver = uc.Chrome(options=options)
    # ---------------------

    wait = WebDriverWait(driver, 60) # Increased wait time for potential challenges

    try:
        print(f"Navigating to login page: {LOGIN_URL}")
        driver.get(LOGIN_URL)

        # It's possible Cloudflare will present a challenge page.
        # We'll wait for the email field to be visible, which should happen after any challenge.
        print("Waiting for login page to load (this may take a moment due to Cloudflare)...")
        
        try:
            # Try to find elements for Version B (English)
            print("Attempting to find login elements for English version...")
            user_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Username or Email']")))
            pass_field_locator = (By.XPATH, "//input[@placeholder='Password']")
            login_button_locator = (By.XPATH, "//button[text()='Login']")
            print("Found English version elements.")
        except TimeoutException:
            # If that fails, try to find elements for Version A (Localization keys)
            print("English version not found, attempting to find elements for localization key version...")
            user_field = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='login.username-or-email']")))
            pass_field_locator = (By.XPATH, "//input[@placeholder='login.password']")
            login_button_locator = (By.XPATH, "//button[contains(., 'login.login')]")
            print("Found localization key version elements.")

        # Now, use the locators
        print("Login page loaded. Entering credentials...")
        user_field.send_keys(HIDENCLOUD_USERNAME)

        pass_field = wait.until(EC.visibility_of_element_located(pass_field_locator))
        pass_field.send_keys(HIDENCLOUD_PASSWORD)

        # NEW: Handle "Verify you are human" challenge on the login page
        try:
            print("Checking for 'Verify you are human' checkbox on login page...")
            # The checkbox is likely in an iframe. Let's wait for the iframe to be present.
            iframe_wait = WebDriverWait(driver, 15)
            iframe = iframe_wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[starts-with(@id, 'cf-chl-widget')]")))
            driver.switch_to.frame(iframe)
            
            # Now, wait for the checkbox and click it
            checkbox_wait = WebDriverWait(driver, 15)
            checkbox = checkbox_wait.until(EC.element_to_be_clickable((By.XPATH, "//label[@class='cb-lb']/input[@type='checkbox']")))
            checkbox.click()
            print("'Verify you are human' checkbox clicked.")
            
            # Switch back to the main content
            driver.switch_to.default_content()
            
        except TimeoutException:
            print("No 'Verify you are human' checkbox found on login page, proceeding.")
            # If we timed out, we might not need to click it, so we switch back just in case
            driver.switch_to.default_content()

        login_button = wait.until(EC.element_to_be_clickable(login_button_locator))
        driver.execute_script("arguments[0].click();", login_button)

        print("Login successful. Waiting for dashboard...")
        
        # --- NEW: Check server status and restart if needed ---
        try:
            print("Checking server status...")
            # Check for an "Offline" or "Stopped" status indicator. This is a guess.
            # We use find_elements to avoid an error if the element doesn't exist.
            offline_indicator = driver.find_elements(By.XPATH, "//*[contains(text(), 'Offline') or contains(text(), 'Stopped')]")
            
            if offline_indicator:
                print("Server is offline. Attempting to start it...")
                # Find and click the "Start" or "Restart" button. This is also a guess.
                start_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Start') or contains(., 'Restart')]")))
                start_button.click()
                print("Start/Restart button clicked. Waiting a few seconds for the server to initialize...")
                time.sleep(15) # Wait for server to begin starting up
            else:
                print("Server is online.")
        except Exception as e:
            print(f"Could not check server status or start it: {e}")
            # This is not a critical error, so we continue to the renewal step.
        # ----------------------------------------------------

        renew_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Renew')]")))
        print("Found renew button. Clicking it...")
        renew_button.click()

        print("Renew button clicked successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        driver.save_screenshot("error_screenshot.png")
        print("A screenshot 'error_screenshot.png' has been saved for debugging.")

    finally:
        print("Closing the browser.")
        driver.quit()

if __name__ == "__main__":
    renew_server()
