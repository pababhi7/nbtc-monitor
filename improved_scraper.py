#!/usr/bin/env python3
"""
Improved NBTC Equipment Scraper with enhanced Cloudflare bypass
"""

import os
import time
import logging
import random
from datetime import datetime
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedNBTCScraper:
    def __init__(self):
        self.base_url = "https://mocheck.nbtc.go.th"
        self.driver = None
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """Setup requests session with headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(headers)
    
    def setup_enhanced_driver(self):
        """Setup Chrome driver with enhanced anti-detection settings"""
        chrome_options = Options()
        
        # Basic options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Faster loading
        chrome_options.add_argument('--disable-javascript')  # Try without JS first
        
        # Anti-detection measures
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("detach", True)
        
        # Realistic browser settings
        chrome_options.add_argument('--window-size=1366,768')
        chrome_options.add_argument('--start-maximized')
        
        # Custom user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Performance optimizations
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-iframes')
        
        # Proxy settings (if needed)
        # chrome_options.add_argument('--proxy-server=your-proxy:port')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            
            logger.info("Enhanced Chrome driver setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup enhanced driver: {e}")
            return False
    
    def wait_for_cloudflare_bypass(self, timeout=120):
        """Enhanced Cloudflare bypass waiting"""
        logger.info("Waiting for Cloudflare challenge to complete...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                current_url = self.driver.current_url
                page_source = self.driver.page_source
                
                # Check if we're past Cloudflare
                if ("Just a moment" not in page_source and 
                    "cloudflare" not in page_source.lower() and
                    self.driver.title != "Just a moment..."):
                    
                    logger.info("Successfully bypassed Cloudflare!")
                    return True
                
                # Check for error pages
                if "403" in page_source or "Access denied" in page_source:
                    logger.warning("Access denied detected")
                    return False
                
                # Random wait to appear human-like
                time.sleep(random.uniform(1, 3))
                
                # Occasionally move mouse or scroll (simulate human activity)
                if random.random() < 0.3:
                    try:
                        self.driver.execute_script("window.scrollBy(0, 100);")
                    except:
                        pass
                
            except Exception as e:
                logger.warning(f"Error during Cloudflare wait: {e}")
                time.sleep(2)
        
        logger.error("Cloudflare bypass timeout")
        return False
    
    def try_alternative_access_methods(self):
        """Try different methods to access the website"""
        
        methods = [
            {"name": "Main Search Page", "url": "https://mocheck.nbtc.go.th/search-equipments"},
            {"name": "Direct Equipment Page", "url": "https://mocheck.nbtc.go.th/search-equipments/1624970"},
            {"name": "Home Page First", "url": "https://mocheck.nbtc.go.th"},
        ]
        
        for method in methods:
            logger.info(f"Trying method: {method['name']}")
            
            try:
                self.driver.get(method['url'])
                
                # Wait for page to load
                time.sleep(random.uniform(3, 7))
                
                # Try to bypass Cloudflare
                if self.wait_for_cloudflare_bypass():
                    logger.info(f"Success with method: {method['name']}")
                    return True
                else:
                    logger.warning(f"Failed with method: {method['name']}")
                    
            except Exception as e:
                logger.error(f"Error with method {method['name']}: {e}")
                
            # Wait between attempts
            time.sleep(random.uniform(5, 10))
        
        return False
    
    def search_for_equipment(self):
        """Search for equipment on the website"""
        logger.info("Starting equipment search...")
        
        if not self.setup_enhanced_driver():
            logger.error("Failed to setup driver")
            return []
        
        try:
            # Try different access methods
            if not self.try_alternative_access_methods():
                logger.error("All access methods failed")
                return []
            
            # Now try to extract equipment data
            equipment_data = self.extract_equipment_data()
            return equipment_data
            
        except Exception as e:
            logger.error(f"Error during equipment search: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
    
    def extract_equipment_data(self):
        """Extract equipment data from the current page"""
        logger.info("Extracting equipment data...")
        
        try:
            # Get page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Save current page for debugging
            with open(f'debug_current_page_{int(time.time())}.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            logger.info(f"Current URL: {self.driver.current_url}")
            logger.info(f"Page title: {self.driver.title}")
            logger.info(f"Page length: {len(page_source)} characters")
            
            # Look for equipment data
            equipment_found = []
            
            # Check for tables
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} tables")
            
            # Check for forms
            forms = soup.find_all('form')
            logger.info(f"Found {len(forms)} forms")
            
            # Check for links
            links = soup.find_all('a', href=True)
            equipment_links = [link for link in links if 'equipment' in str(link.get('href', '')).lower()]
            logger.info(f"Found {len(equipment_links)} equipment links")
            
            # Look for cellular mobile keywords
            page_text = soup.get_text()
            cellular_keywords = ['cellular mobile', 'gsm', 'wcdma', 'lte', 'nr', 'เครื่องโทรคมนาคม', 'โทรศัพท์']
            found_keywords = [kw for kw in cellular_keywords if kw.lower() in page_text.lower()]
            logger.info(f"Found cellular keywords: {found_keywords}")
            
            # Try to find specific equipment entries
            # This would need to be customized based on the actual page structure
            equipment_entries = soup.find_all(['div', 'tr', 'li'], class_=lambda x: x and ('equipment' in x.lower() if x else False))
            logger.info(f"Found {len(equipment_entries)} potential equipment entries")
            
            # Look for any data that might contain device information
            if 'cellular' in page_text.lower() or 'mobile' in page_text.lower():
                logger.info("Found cellular/mobile content in page")
                equipment_found.append({
                    'url': self.driver.current_url,
                    'title': self.driver.title,
                    'content_preview': page_text[:500],
                    'found_keywords': found_keywords,
                    'timestamp': datetime.now().isoformat()
                })
            
            return equipment_found
            
        except Exception as e:
            logger.error(f"Error extracting equipment data: {e}")
            return []
    
    def test_simplified_access(self):
        """Test with a simplified approach"""
        logger.info("Testing simplified access...")
        
        # Try with just requests first (though we know it will fail)
        try:
            response = self.session.get(f"{self.base_url}/search-equipments", timeout=30)
            logger.info(f"Requests method - Status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("Success with requests method!")
                soup = BeautifulSoup(response.content, 'html.parser')
                # Process the content
                return True
            else:
                logger.warning("Requests method blocked by Cloudflare")
                
        except Exception as e:
            logger.error(f"Requests method failed: {e}")
        
        return False

def main():
    """Main function to test the improved scraper"""
    scraper = ImprovedNBTCScraper()
    
    print("🚀 Testing Improved NBTC Scraper...")
    print("=" * 50)
    
    # Test simplified access first
    if scraper.test_simplified_access():
        print("✅ Simplified access worked!")
        return
    
    # Try full Selenium approach
    print("📋 Trying full Selenium approach...")
    equipment_data = scraper.search_for_equipment()
    
    if equipment_data:
        print(f"✅ Found {len(equipment_data)} equipment entries!")
        for item in equipment_data:
            print(f"- {item.get('title', 'Unknown')}: {item.get('url', 'No URL')}")
    else:
        print("❌ No equipment data found")
        print("\nTroubleshooting suggestions:")
        print("1. Check if Chrome browser is installed")
        print("2. Try running without headless mode")
        print("3. The website may have very strict protection")
        print("4. Consider using a VPN or different IP address")

if __name__ == "__main__":
    main()