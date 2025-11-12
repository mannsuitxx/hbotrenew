
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

# --- Configuration ---
HIDENCLOUD_USERNAME = os.environ.get("HIDENCLOUD_USERNAME")
HIDENCLOUD_PASSWORD = os.environ.get("HIDENCLOUD_PASSWORD")
LOGIN_URL = "https://freepanel.hidencloud.com/server/2870cdbb"

def renew_server():
    """
    Logs into HidenCloud, navigates to the server page, and clicks the renew button,
    using selenium-stealth to avoid bot detection.
    """
    if not HIDENCLOUD_USERNAME or not HIDENCLOUD_PASSWORD:
        print("Error: Please set the HIDENCLOUD_USERNAME and HIDENCLOUD_PASSWORD environment variables.")
        return

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # In the GitHub Actions environment, browser-actions/setup-chrome adds chromedriver to the PATH.
    # We can initialize the driver directly.
    driver = webdriver.Chrome(options=options)

    # --- Apply Stealth ---
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    # ---------------------

    wait = WebDriverWait(driver, 30) # Increased wait time for potential challenges

    try:
        print(f"Navigating to login page: {LOGIN_URL}")
        driver.get(LOGIN_URL)

        # It's possible Cloudflare will present a challenge page.
        # We'll give it some time to resolve before looking for the login fields.
        print("Waiting for potential Cloudflare challenge to resolve...")
        time.sleep(10) # Wait for 10 seconds

        print("Entering credentials...")
        user_field = wait.until(EC.visibility_of_element_located((By.NAME, "email")))
        user_field.send_keys(HIDENCLOUD_USERNAME)

        pass_field = wait.until(EC.visibility_of_element_located((By.NAME, "password")))
        pass_field.send_keys(HIDENCLOUD_PASSWORD)

        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_button.click()

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
