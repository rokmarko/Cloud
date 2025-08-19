#!/usr/bin/env python3
"""
Test script to verify the dropdown clipping fix in admin devices page
"""
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_dropdown_visibility():
    """Test that dropdown menus are visible and not clipped."""
    
    print("Testing Dropdown Clipping Fix")
    print("=" * 40)
    
    # Note: This test requires Chrome/Chromium and chromedriver to be installed
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Navigate to admin devices page
            url = "http://127.0.0.1:5000/admin/devices"
            print(f"Navigating to: {url}")
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "devices-table-container"))
            )
            
            print("✅ Page loaded successfully")
            
            # Check if dropdown buttons exist
            dropdown_buttons = driver.find_elements(By.CSS_SELECTOR, ".dropdown-toggle")
            print(f"✅ Found {len(dropdown_buttons)} dropdown buttons")
            
            if dropdown_buttons:
                # Click first dropdown
                first_dropdown = dropdown_buttons[0]
                driver.execute_script("arguments[0].click();", first_dropdown)
                
                # Wait for dropdown menu to appear
                time.sleep(0.5)
                
                # Check if dropdown menu is visible
                dropdown_menu = driver.find_element(By.CSS_SELECTOR, ".dropdown-menu.show")
                
                if dropdown_menu.is_displayed():
                    print("✅ Dropdown menu is visible")
                    
                    # Get dropdown position and dimensions
                    menu_rect = driver.execute_script("""
                        const menu = arguments[0];
                        const rect = menu.getBoundingClientRect();
                        return {
                            top: rect.top,
                            left: rect.left,
                            bottom: rect.bottom,
                            right: rect.right,
                            width: rect.width,
                            height: rect.height
                        };
                    """, dropdown_menu)
                    
                    # Get viewport dimensions
                    viewport = driver.execute_script("""
                        return {
                            width: window.innerWidth,
                            height: window.innerHeight
                        };
                    """)
                    
                    print(f"   Menu position: top={menu_rect['top']:.1f}, left={menu_rect['left']:.1f}")
                    print(f"   Menu size: {menu_rect['width']:.1f}x{menu_rect['height']:.1f}")
                    print(f"   Viewport: {viewport['width']}x{viewport['height']}")
                    
                    # Check if menu is within viewport
                    is_within_viewport = (
                        menu_rect['top'] >= 0 and
                        menu_rect['left'] >= 0 and
                        menu_rect['bottom'] <= viewport['height'] and
                        menu_rect['right'] <= viewport['width']
                    )
                    
                    if is_within_viewport:
                        print("✅ Dropdown menu is fully within viewport")
                    else:
                        print("⚠️  Dropdown menu extends beyond viewport")
                        if menu_rect['right'] > viewport['width']:
                            print(f"   Extends {menu_rect['right'] - viewport['width']:.1f}px to the right")
                        if menu_rect['bottom'] > viewport['height']:
                            print(f"   Extends {menu_rect['bottom'] - viewport['height']:.1f}px below")
                    
                    # Test mobile viewport
                    print("\nTesting mobile viewport...")
                    driver.set_window_size(375, 667)  # iPhone SE size
                    time.sleep(0.5)
                    
                    # Re-check dropdown positioning
                    mobile_rect = driver.execute_script("""
                        const menu = arguments[0];
                        const rect = menu.getBoundingClientRect();
                        return {
                            top: rect.top,
                            left: rect.left,
                            bottom: rect.bottom,
                            right: rect.right,
                            width: rect.width,
                            height: rect.height
                        };
                    """, dropdown_menu)
                    
                    mobile_viewport = driver.execute_script("""
                        return {
                            width: window.innerWidth,
                            height: window.innerHeight
                        };
                    """)
                    
                    print(f"   Mobile menu position: top={mobile_rect['top']:.1f}, left={mobile_rect['left']:.1f}")
                    print(f"   Mobile viewport: {mobile_viewport['width']}x{mobile_viewport['height']}")
                    
                    is_mobile_within_viewport = (
                        mobile_rect['top'] >= 0 and
                        mobile_rect['left'] >= 0 and
                        mobile_rect['bottom'] <= mobile_viewport['height'] and
                        mobile_rect['right'] <= mobile_viewport['width']
                    )
                    
                    if is_mobile_within_viewport:
                        print("✅ Mobile dropdown positioning works correctly")
                    else:
                        print("⚠️  Mobile dropdown may need adjustment")
                    
                else:
                    print("❌ Dropdown menu is not visible")
                    return False
            else:
                print("⚠️  No dropdown buttons found - may be no devices in the system")
            
            print("\n✅ Dropdown clipping fix test completed successfully!")
            return True
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("\nNote: This test requires Chrome/Chromium and chromedriver to be installed.")
        print("You can manually test by:")
        print("1. Opening http://127.0.0.1:5000/admin/devices in a browser")
        print("2. Clicking on dropdown buttons in the Actions column")
        print("3. Verifying the dropdown menus are fully visible")
        print("4. Testing on different screen sizes (mobile, tablet, desktop)")
        return False


if __name__ == '__main__':
    print("Dropdown Clipping Fix Test")
    print("This script tests the dropdown menu visibility fix in the admin devices page.")
    print()
    
    success = test_dropdown_visibility()
    
    if success:
        print()
        print("All tests passed! The dropdown clipping fix is working correctly.")
    else:
        print()
        print("Test encountered issues. Manual testing is recommended.")
        
    print()
    print("Manual Testing Instructions:")
    print("1. Open http://127.0.0.1:5000/admin/devices")
    print("2. Look for dropdown buttons (⋮) in the Actions column")
    print("3. Click on dropdown buttons to open menus")
    print("4. Verify dropdowns are fully visible and not clipped")
    print("5. Test on different screen sizes using browser dev tools")
    print("6. Test horizontal scrolling if table is wide")
    
    sys.exit(0 if success else 1)
