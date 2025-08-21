#!/usr/bin/env python3
"""
Screenshot capture script for KanardiaCloud documentation
"""
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """Set up Chrome driver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--headless')  # Enable headless mode for stability
    
    # Set the binary location to chromium
    chrome_options.binary_location = '/usr/bin/chromium-browser'
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Failed to create Chrome driver: {e}")
        print("Please make sure Chromium and chromedriver are installed")
        return None

def login_to_app(driver, base_url="http://localhost:5000"):
    """Login to the KanardiaCloud application"""
    try:
        driver.get(f"{base_url}/auth/login")
        time.sleep(3)
        
        print("Attempting to login...")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Try different ways to find email field
        email_field = None
        email_selectors = [
            ("name", "email"),
            ("id", "email"),
            ("type", "email"),
            ("css", "input[type='email']"),
            ("css", "#email")
        ]
        
        for selector_type, selector_value in email_selectors:
            try:
                if selector_type == "name":
                    email_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.NAME, selector_value))
                    )
                elif selector_type == "id":
                    email_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, selector_value))
                    )
                elif selector_type == "type":
                    email_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f"input[type='{selector_value}']"))
                    )
                elif selector_type == "css":
                    email_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector_value))
                    )
                
                if email_field:
                    print(f"Found email field using {selector_type}: {selector_value}")
                    break
            except TimeoutException:
                continue
        
        if not email_field:
            print("Could not find email field, trying manual approach...")
            # Print page source for debugging
            print("Available input fields:")
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for i, inp in enumerate(inputs):
                print(f"  Input {i}: type={inp.get_attribute('type')}, name={inp.get_attribute('name')}, id={inp.get_attribute('id')}")
            
            # Try to find any input field
            inputs = driver.find_elements(By.TAG_NAME, "input")
            if inputs:
                email_field = inputs[0]  # Use first input field
        
        if email_field:
            email_field.clear()
            email_field.send_keys("demo@kanardia.com")
            print("✓ Entered email")
            
            # Find password field
            password_field = None
            password_selectors = [
                ("name", "password"),
                ("id", "password"),
                ("type", "password"),
                ("css", "input[type='password']")
            ]
            
            for selector_type, selector_value in password_selectors:
                try:
                    if selector_type == "name":
                        password_field = driver.find_element(By.NAME, selector_value)
                    elif selector_type == "id":
                        password_field = driver.find_element(By.ID, selector_value)
                    elif selector_type == "type":
                        password_field = driver.find_element(By.CSS_SELECTOR, f"input[type='{selector_value}']")
                    elif selector_type == "css":
                        password_field = driver.find_element(By.CSS_SELECTOR, selector_value)
                    
                    if password_field:
                        print(f"Found password field using {selector_type}: {selector_value}")
                        break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                # Try second input field if available
                inputs = driver.find_elements(By.TAG_NAME, "input")
                if len(inputs) > 1:
                    password_field = inputs[1]
            
            if password_field:
                password_field.clear()
                password_field.send_keys("demo123")
                print("✓ Entered password")
                
                # Find submit button
                submit_button = None
                submit_selectors = [
                    ("css", "button[type='submit']"),
                    ("css", "input[type='submit']"),
                    ("css", ".btn-primary"),
                    ("css", ".btn"),
                    ("tag", "button")
                ]
                
                for selector_type, selector_value in submit_selectors:
                    try:
                        if selector_type == "css":
                            submit_button = driver.find_element(By.CSS_SELECTOR, selector_value)
                        elif selector_type == "tag":
                            buttons = driver.find_elements(By.TAG_NAME, selector_value)
                            if buttons:
                                submit_button = buttons[0]
                        
                        if submit_button:
                            print(f"Found submit button using {selector_type}: {selector_value}")
                            break
                    except NoSuchElementException:
                        continue
                
                if submit_button:
                    submit_button.click()
                    print("✓ Clicked submit button")
                    
                    # Wait for redirect (with longer timeout)
                    try:
                        WebDriverWait(driver, 15).until(
                            lambda d: "/login" not in d.current_url or "/dashboard" in d.current_url
                        )
                        print("✓ Successfully logged in")
                        return True
                    except TimeoutException:
                        print("Timeout waiting for redirect after login")
                        print(f"Current URL: {driver.current_url}")
                else:
                    print("Could not find submit button")
            else:
                print("Could not find password field")
        else:
            print("Could not find email field")
            
        return False
        
    except Exception as e:
        print(f"Login failed with error: {e}")
        print(f"Current URL: {driver.current_url}")
        return False

def capture_screenshot(driver, filename, description=""):
    """Capture a screenshot and save it"""
    try:
        time.sleep(2)  # Wait for page to fully load
        screenshot_path = f"/home/rok/src/Cloud-1/tex/screenshots/{filename}"
        driver.save_screenshot(screenshot_path)
        print(f"✓ Captured: {filename} - {description}")
        return True
    except Exception as e:
        print(f"Failed to capture {filename}: {e}")
        return False

def capture_dashboard_screenshots(driver):
    """Capture main dashboard screenshots"""
    base_url = "http://localhost:5000"
    
    print("\n=== Capturing Dashboard Screenshots ===")
    
    # Main dashboard
    driver.get(f"{base_url}/dashboard")
    capture_screenshot(driver, "main_dashboard.png", "Main dashboard overview")
    
    # Dashboard overview (same as main for now)
    capture_screenshot(driver, "dashboard_overview.png", "Dashboard overview with navigation")

def capture_checklist_screenshots(driver):
    """Capture checklist-related screenshots"""
    base_url = "http://localhost:5000"
    
    print("\n=== Capturing Checklist Screenshots ===")
    
    # Checklist dashboard
    try:
        driver.get(f"{base_url}/dashboard/checklists")
        capture_screenshot(driver, "checklist_dashboard.png", "Checklist management dashboard")
        
        # Try to capture create checklist form
        try:
            driver.get(f"{base_url}/dashboard/checklists/add")
            capture_screenshot(driver, "create_checklist_form.png", "Create new checklist form")
        except Exception as e:
            print(f"Could not capture create checklist form: {e}")
        
        # Try to capture import form
        try:
            driver.get(f"{base_url}/dashboard/checklists/import")
            capture_screenshot(driver, "checklist_import.png", "Checklist import functionality")
        except Exception as e:
            print(f"Could not capture checklist import: {e}")
            
        # Go back to checklist list and try to capture print views
        try:
            driver.get(f"{base_url}/dashboard/checklists")
            # Look for a checklist to view print options
            checklist_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/checklists/']")
            if checklist_links:
                # Get first checklist ID from href
                href = checklist_links[0].get_attribute('href')
                checklist_id = href.split('/')[-1]
                
                # Try to capture print views
                driver.get(f"{base_url}/dashboard/checklists/{checklist_id}/print")
                capture_screenshot(driver, "checklist_print_standard.png", "Standard checklist print view")
                
                # Try minimal print view if available (might need URL parameter)
                driver.get(f"{base_url}/dashboard/checklists/{checklist_id}/print?style=minimal")
                capture_screenshot(driver, "checklist_print_minimal.png", "Minimal checklist print view")
        except Exception as e:
            print(f"Could not capture print views: {e}")
            
    except Exception as e:
        print(f"Error capturing checklist screenshots: {e}")

def capture_device_screenshots(driver):
    """Capture device management screenshots"""
    base_url = "http://localhost:5000"
    
    print("\n=== Capturing Device Screenshots ===")
    
    try:
        driver.get(f"{base_url}/dashboard/devices")
        capture_screenshot(driver, "device_management.png", "Device management interface")
    except Exception as e:
        print(f"Error capturing device screenshots: {e}")

def capture_logbook_screenshots(driver):
    """Capture logbook screenshots"""
    base_url = "http://localhost:5000"
    
    print("\n=== Capturing Logbook Screenshots ===")
    
    try:
        # Try to find a device with logbook entries
        driver.get(f"{base_url}/dashboard/devices")
        device_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/logbook']")
        if device_links:
            device_links[0].click()
            time.sleep(3)
            capture_screenshot(driver, "logbook_overview.png", "Logbook overview")
        else:
            print("No device logbook links found")
    except Exception as e:
        print(f"Error capturing logbook screenshots: {e}")

def capture_login_screenshots(driver):
    """Capture login/registration screenshots"""
    base_url = "http://localhost:5000"
    
    print("\n=== Capturing Authentication Screenshots ===")
    
    try:
        # Capture login page
        driver.get(f"{base_url}/auth/login")
        capture_screenshot(driver, "login_form.png", "Login page")
        
        # Capture registration page if available
        try:
            driver.get(f"{base_url}/auth/register")
            capture_screenshot(driver, "registration_form.png", "User registration form")
        except:
            print("Could not access registration page")
                
    except Exception as e:
        print(f"Error capturing authentication screenshots: {e}")

def main():
    """Main screenshot capture process"""
    print("KanardiaCloud Screenshot Capture Tool")
    print("=====================================")
    
    # Create screenshots directory if it doesn't exist
    screenshots_dir = "/home/rok/src/Cloud-1/tex/screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    print(f"Screenshots will be saved to: {screenshots_dir}")
    
    # Setup Chrome driver
    driver = setup_driver()
    if not driver:
        return
    
    try:
        # Capture login/registration screenshots first
        capture_login_screenshots(driver)
        
        # Login to the application
        if login_to_app(driver):
            # Capture various sections
            capture_dashboard_screenshots(driver)
            capture_checklist_screenshots(driver)
            capture_logbook_screenshots(driver) 
            capture_device_screenshots(driver)
            
            print("\n=== Screenshot capture completed ===")
            print("Screenshots saved to: /home/rok/src/Cloud-1/tex/screenshots/")
            print("\nTo replace placeholder images in the manual:")
            print("1. Review the captured screenshots")
            print("2. Copy relevant ones to tex/images/ directory")  
            print("3. Update filenames in the LaTeX files if needed")
            print("4. Rebuild the PDF with: cd tex && make")
            
        else:
            print("Failed to login, skipping authenticated sections")
            
    except Exception as e:
        print(f"Error during screenshot capture: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
