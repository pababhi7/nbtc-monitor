#!/usr/bin/env python3
"""
Targeted NBTC Equipment Scraper
Specifically designed to find and extract cellular mobile equipment data from mocheck.nbtc.go.th
"""

import os
import time
import json
import logging
import random
from datetime import datetime
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TargetedNBTCScraper:
    def __init__(self):
        self.base_url = "https://mocheck.nbtc.go.th"
        self.driver = None
        self.found_devices = []
        self.session = requests.Session()
        self.setup_session()
        
        # Target keywords for cellular mobile equipment
        self.cellular_keywords = [
            'cellular mobile', 'gsm', 'wcdma', 'lte', 'nr', '5g',
            'เครื่องโทรคมนาคม', 'cellular', 'mobile', 'phone', 'smartphone',
            'โทรศัพท์', 'มือถือ', 'ระบบเซลลูลาร์', 'ระบบมือถือ'
        ]
        
        # Common search paths and parameters
        self.search_paths = [
            "/search-equipments",
            "/search-equipments/1624970",  # Known equipment category
            "/equipments",
            "/equipment/search",
            "/search",
            "/api/equipments",
            "/api/search"
        ]
    
    def setup_session(self):
        """Setup requests session with realistic headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'th,en-US;q=0.9,en;q=0.8',
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
        """Setup Chrome driver with enhanced settings"""
        chrome_options = Options()
        
        # Basic headless settings
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Performance
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        
        # User agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Anti-detection script
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Enhanced Chrome driver setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup enhanced driver: {e}")
            return False
    
    def wait_for_page_load(self, timeout=30):
        """Wait for page to load completely"""
        try:
            # Wait for body to be present
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for JavaScript to complete
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            time.sleep(2)  # Additional wait for dynamic content
            return True
            
        except TimeoutException:
            logger.warning("Page load timeout")
            return False
    
    def bypass_cloudflare(self, max_attempts=3):
        """Enhanced Cloudflare bypass"""
        for attempt in range(max_attempts):
            logger.info(f"Cloudflare bypass attempt {attempt + 1}/{max_attempts}")
            
            try:
                page_source = self.driver.page_source
                
                # Check if we're past Cloudflare
                if ("Just a moment" not in page_source and 
                    "cloudflare" not in page_source.lower() and
                    self.driver.title != "Just a moment..." and
                    len(page_source) > 1000):
                    
                    logger.info("Successfully bypassed Cloudflare!")
                    return True
                
                # Wait with random intervals
                wait_time = random.uniform(5, 15)
                logger.info(f"Waiting {wait_time:.1f} seconds for Cloudflare...")
                time.sleep(wait_time)
                
                # Try scrolling to simulate human behavior
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(random.uniform(1, 3))
                    self.driver.execute_script("window.scrollTo(0, 0);")
                except:
                    pass
                    
            except Exception as e:
                logger.warning(f"Error during Cloudflare bypass: {e}")
                time.sleep(5)
        
        logger.error("Failed to bypass Cloudflare")
        return False
    
    def try_different_urls(self):
        """Try different URL approaches to access equipment data"""
        urls_to_try = [
            f"{self.base_url}/search-equipments",
            f"{self.base_url}/search-equipments/1624970",
            f"{self.base_url}/search-equipments/category/cellular",
            f"{self.base_url}/search-equipments/type/mobile",
            f"{self.base_url}/equipments/search",
            f"{self.base_url}/equipment",
            f"{self.base_url}/search",
            f"{self.base_url}/",
            f"{self.base_url}/api/equipments",
            f"{self.base_url}/public/equipments",
            f"{self.base_url}/en/search-equipments",
        ]
        
        for url in urls_to_try:
            logger.info(f"Trying URL: {url}")
            
            try:
                self.driver.get(url)
                self.wait_for_page_load()
                
                if self.bypass_cloudflare():
                    # Check if this page has equipment data
                    if self.check_for_equipment_data():
                        logger.info(f"Found equipment data at: {url}")
                        return url
                    else:
                        logger.info(f"No equipment data found at: {url}")
                        
            except Exception as e:
                logger.error(f"Error accessing {url}: {e}")
                
            time.sleep(random.uniform(3, 7))
        
        return None
    
    def check_for_equipment_data(self):
        """Check if current page contains equipment data"""
        try:
            page_source = self.driver.page_source.lower()
            page_text = BeautifulSoup(self.driver.page_source, 'html.parser').get_text().lower()
            
            # Check for equipment-related content
            equipment_indicators = [
                'equipment', 'device', 'เครื่อง', 'อุปกรณ์', 'ประเภท', 'รุ่น', 'model',
                'cellular', 'mobile', 'gsm', 'lte', 'wcdma', 'nr', '5g',
                'โทรศัพท์', 'มือถือ', 'โทรคมนาคม', 'search', 'ค้นหา'
            ]
            
            found_indicators = [indicator for indicator in equipment_indicators if indicator in page_text]
            
            if found_indicators:
                logger.info(f"Found indicators: {found_indicators}")
                
                # Look for tables, forms, or lists that might contain equipment
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                tables = soup.find_all('table')
                forms = soup.find_all('form')
                lists = soup.find_all(['ul', 'ol'])
                divs = soup.find_all('div', class_=lambda x: x and any(word in x.lower() for word in ['equipment', 'device', 'search', 'result']))
                
                logger.info(f"Found {len(tables)} tables, {len(forms)} forms, {len(lists)} lists, {len(divs)} equipment divs")
                
                if tables or forms or lists or divs:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for equipment data: {e}")
            return False
    
    def extract_equipment_from_page(self):
        """Extract equipment data from current page"""
        devices = []
        
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            current_url = self.driver.current_url
            
            logger.info(f"Extracting from: {current_url}")
            logger.info(f"Page title: {self.driver.title}")
            
            # Save page for debugging
            timestamp = int(time.time())
            with open(f'extracted_page_{timestamp}.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # Method 1: Extract from tables
            devices.extend(self.extract_from_tables(soup))
            
            # Method 2: Extract from forms and search results
            devices.extend(self.extract_from_forms(soup))
            
            # Method 3: Extract from lists
            devices.extend(self.extract_from_lists(soup))
            
            # Method 4: Extract from card/grid layouts
            devices.extend(self.extract_from_cards(soup))
            
            # Method 5: Look for JSON data in script tags
            devices.extend(self.extract_from_scripts(soup))
            
            # Method 6: Extract from specific div patterns
            devices.extend(self.extract_from_divs(soup))
            
            logger.info(f"Extracted {len(devices)} devices from current page")
            
        except Exception as e:
            logger.error(f"Error extracting equipment from page: {e}")
            
        return devices
    
    def extract_from_tables(self, soup):
        """Extract equipment from HTML tables"""
        devices = []
        tables = soup.find_all('table')
        
        logger.info(f"Processing {len(tables)} tables")
        
        for i, table in enumerate(tables):
            try:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                # Get headers
                header_row = rows[0]
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                
                logger.info(f"Table {i} headers: {headers}")
                
                # Process data rows
                for row_idx, row in enumerate(rows[1:], 1):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        
                        row_data = {}
                        for j, cell in enumerate(cells):
                            header = headers[j] if j < len(headers) else f"column_{j}"
                            value = cell.get_text(strip=True)
                            
                            # Also get any links or images
                            links = cell.find_all('a')
                            images = cell.find_all('img')
                            
                            if links:
                                row_data[f"{header}_links"] = [link.get('href') for link in links if link.get('href')]
                            if images:
                                row_data[f"{header}_images"] = [img.get('src') for img in images if img.get('src')]
                            
                            row_data[header] = value
                        
                        # Check if this row contains cellular mobile equipment
                        row_text = ' '.join(row_data.values()).lower()
                        if any(keyword in row_text for keyword in self.cellular_keywords):
                            device = {
                                'source': f'table_{i}_row_{row_idx}',
                                'type': 'table_row',
                                'data': row_data,
                                'matched_keywords': [kw for kw in self.cellular_keywords if kw in row_text],
                                'url': self.driver.current_url,
                                'timestamp': datetime.now().isoformat(),
                                'raw_text': row_text
                            }
                            devices.append(device)
                            logger.info(f"Found cellular device in table {i}, row {row_idx}")
                            
            except Exception as e:
                logger.error(f"Error processing table {i}: {e}")
        
        return devices
    
    def extract_from_forms(self, soup):
        """Extract equipment from forms and search interfaces"""
        devices = []
        forms = soup.find_all('form')
        
        logger.info(f"Processing {len(forms)} forms")
        
        for i, form in enumerate(forms):
            try:
                # Look for select options that might contain equipment types
                selects = form.find_all('select')
                
                for j, select in enumerate(selects):
                    options = select.find_all('option')
                    
                    for option in options:
                        option_text = option.get_text(strip=True)
                        option_value = option.get('value', '')
                        
                        if option_text and any(keyword in option_text.lower() for keyword in self.cellular_keywords):
                            device = {
                                'source': f'form_{i}_select_{j}',
                                'type': 'form_option',
                                'data': {
                                    'text': option_text,
                                    'value': option_value,
                                    'form_action': form.get('action', ''),
                                    'form_method': form.get('method', 'GET')
                                },
                                'matched_keywords': [kw for kw in self.cellular_keywords if kw in option_text.lower()],
                                'url': self.driver.current_url,
                                'timestamp': datetime.now().isoformat()
                            }
                            devices.append(device)
                            logger.info(f"Found cellular device option: {option_text}")
                            
            except Exception as e:
                logger.error(f"Error processing form {i}: {e}")
        
        return devices
    
    def extract_from_lists(self, soup):
        """Extract equipment from HTML lists"""
        devices = []
        lists = soup.find_all(['ul', 'ol'])
        
        logger.info(f"Processing {len(lists)} lists")
        
        for i, list_elem in enumerate(lists):
            items = list_elem.find_all('li')
            
            for j, item in enumerate(items):
                try:
                    item_text = item.get_text(strip=True)
                    
                    if item_text and any(keyword in item_text.lower() for keyword in self.cellular_keywords):
                        # Get any links in the item
                        links = item.find_all('a')
                        
                        device = {
                            'source': f'list_{i}_item_{j}',
                            'type': 'list_item',
                            'data': {
                                'text': item_text,
                                'html': str(item),
                                'links': [link.get('href') for link in links if link.get('href')]
                            },
                            'matched_keywords': [kw for kw in self.cellular_keywords if kw in item_text.lower()],
                            'url': self.driver.current_url,
                            'timestamp': datetime.now().isoformat()
                        }
                        devices.append(device)
                        logger.info(f"Found cellular device in list: {item_text[:50]}...")
                        
                except Exception as e:
                    logger.error(f"Error processing list item {i},{j}: {e}")
        
        return devices
    
    def extract_from_cards(self, soup):
        """Extract equipment from card/grid layouts"""
        devices = []
        
        # Look for common card patterns
        card_selectors = [
            'div[class*="card"]',
            'div[class*="item"]',
            'div[class*="product"]',
            'div[class*="equipment"]',
            'div[class*="device"]',
            'div[class*="result"]',
            'div[class*="entry"]',
            '.equipment-card',
            '.device-card',
            '.search-result'
        ]
        
        for selector in card_selectors:
            try:
                elements = soup.select(selector)
                logger.info(f"Found {len(elements)} elements for selector: {selector}")
                
                for i, element in enumerate(elements):
                    element_text = element.get_text(strip=True)
                    
                    if element_text and any(keyword in element_text.lower() for keyword in self.cellular_keywords):
                        # Get additional data
                        links = element.find_all('a')
                        images = element.find_all('img')
                        
                        device = {
                            'source': f'card_{selector}_{i}',
                            'type': 'card_element',
                            'data': {
                                'text': element_text,
                                'html': str(element)[:500],  # Limit HTML size
                                'links': [link.get('href') for link in links if link.get('href')],
                                'images': [img.get('src') for img in images if img.get('src')]
                            },
                            'matched_keywords': [kw for kw in self.cellular_keywords if kw in element_text.lower()],
                            'url': self.driver.current_url,
                            'timestamp': datetime.now().isoformat()
                        }
                        devices.append(device)
                        logger.info(f"Found cellular device in card: {element_text[:50]}...")
                        
            except Exception as e:
                logger.error(f"Error processing cards with selector {selector}: {e}")
        
        return devices
    
    def extract_from_scripts(self, soup):
        """Extract equipment data from JavaScript variables"""
        devices = []
        scripts = soup.find_all('script')
        
        logger.info(f"Processing {len(scripts)} script tags")
        
        for i, script in enumerate(scripts):
            try:
                script_content = script.string
                if not script_content:
                    continue
                
                # Look for JSON data or JavaScript arrays
                if ('equipment' in script_content.lower() or 
                    'device' in script_content.lower() or
                    'cellular' in script_content.lower()):
                    
                    # Try to extract JSON objects
                    import re
                    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                    matches = re.findall(json_pattern, script_content)
                    
                    for match in matches:
                        try:
                            data = json.loads(match)
                            if isinstance(data, dict):
                                data_str = json.dumps(data).lower()
                                
                                if any(keyword in data_str for keyword in self.cellular_keywords):
                                    device = {
                                        'source': f'script_{i}',
                                        'type': 'javascript_data',
                                        'data': data,
                                        'matched_keywords': [kw for kw in self.cellular_keywords if kw in data_str],
                                        'url': self.driver.current_url,
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    devices.append(device)
                                    logger.info(f"Found cellular device in script data")
                                    
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"Error processing script {i}: {e}")
        
        return devices
    
    def extract_from_divs(self, soup):
        """Extract equipment from div elements with specific patterns"""
        devices = []
        
        # Look for divs that might contain equipment info
        div_patterns = [
            {'class': lambda x: x and 'equipment' in ' '.join(x).lower()},
            {'class': lambda x: x and 'device' in ' '.join(x).lower()},
            {'class': lambda x: x and 'result' in ' '.join(x).lower()},
            {'class': lambda x: x and 'item' in ' '.join(x).lower()},
            {'id': lambda x: x and any(word in x.lower() for word in ['equipment', 'device', 'search', 'result'])}
        ]
        
        for pattern in div_patterns:
            try:
                divs = soup.find_all('div', pattern)
                logger.info(f"Found {len(divs)} divs matching pattern: {pattern}")
                
                for i, div in enumerate(divs):
                    div_text = div.get_text(strip=True)
                    
                    if div_text and any(keyword in div_text.lower() for keyword in self.cellular_keywords):
                        device = {
                            'source': f'div_pattern_{i}',
                            'type': 'div_element',
                            'data': {
                                'text': div_text,
                                'class': div.get('class', []),
                                'id': div.get('id', ''),
                                'html': str(div)[:500]
                            },
                            'matched_keywords': [kw for kw in self.cellular_keywords if kw in div_text.lower()],
                            'url': self.driver.current_url,
                            'timestamp': datetime.now().isoformat()
                        }
                        devices.append(device)
                        logger.info(f"Found cellular device in div: {div_text[:50]}...")
                        
            except Exception as e:
                logger.error(f"Error processing divs with pattern {pattern}: {e}")
        
        return devices
    
    def try_search_functionality(self):
        """Try to use search functionality on the website"""
        devices = []
        
        try:
            # Look for search forms
            search_forms = self.driver.find_elements(By.TAG_NAME, "form")
            
            for form in search_forms:
                try:
                    # Look for search inputs
                    search_inputs = form.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='search'], input[name*='search'], textarea")
                    
                    for search_input in search_inputs:
                        # Try searching for cellular mobile equipment
                        search_terms = ['cellular mobile', 'GSM', 'LTE', 'mobile phone', 'เครื่องโทรคมนาคม']
                        
                        for term in search_terms:
                            try:
                                logger.info(f"Searching for: {term}")
                                
                                search_input.clear()
                                search_input.send_keys(term)
                                
                                # Look for submit button
                                submit_buttons = form.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], button")
                                
                                if submit_buttons:
                                    submit_buttons[0].click()
                                    
                                    # Wait for results
                                    time.sleep(3)
                                    self.wait_for_page_load()
                                    
                                    # Extract results
                                    search_results = self.extract_equipment_from_page()
                                    devices.extend(search_results)
                                    
                                    if search_results:
                                        logger.info(f"Found {len(search_results)} devices for search term: {term}")
                                    
                                    # Go back to try next term
                                    self.driver.back()
                                    self.wait_for_page_load()
                                    
                                    # Break to try next form
                                    break
                                    
                            except Exception as e:
                                logger.error(f"Error searching for {term}: {e}")
                                
                except Exception as e:
                    logger.error(f"Error processing search form: {e}")
                    
        except Exception as e:
            logger.error(f"Error trying search functionality: {e}")
        
        return devices
    
    def save_results(self, devices, filename=None):
        """Save extracted devices to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nbtc_devices_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(devices, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(devices)} devices to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def run_comprehensive_search(self):
        """Run comprehensive search for cellular mobile equipment"""
        logger.info("Starting comprehensive NBTC equipment search...")
        
        if not self.setup_enhanced_driver():
            logger.error("Failed to setup driver")
            return []
        
        all_devices = []
        
        try:
            # Step 1: Try different URLs to find equipment pages
            working_url = self.try_different_urls()
            
            if working_url:
                logger.info(f"Found working URL: {working_url}")
                
                # Step 2: Extract equipment from current page
                devices = self.extract_equipment_from_page()
                all_devices.extend(devices)
                
                # Step 3: Try search functionality
                search_devices = self.try_search_functionality()
                all_devices.extend(search_devices)
                
                # Step 4: Look for pagination and follow links
                # This would be expanded to handle pagination
                
            else:
                logger.warning("No working URL found - website may be heavily protected")
                
                # Try to get any available content anyway
                self.driver.get(f"{self.base_url}/search-equipments")
                self.wait_for_page_load()
                time.sleep(10)  # Wait longer for any content
                
                devices = self.extract_equipment_from_page()
                all_devices.extend(devices)
            
            # Step 5: Save results
            if all_devices:
                self.save_results(all_devices)
                
                # Print summary
                print(f"\n🎉 FOUND {len(all_devices)} CELLULAR MOBILE DEVICES!")
                print("=" * 50)
                
                for i, device in enumerate(all_devices, 1):
                    print(f"\n📱 Device #{i}:")
                    print(f"   Source: {device['source']}")
                    print(f"   Type: {device['type']}")
                    print(f"   Keywords: {', '.join(device['matched_keywords'])}")
                    
                    if 'data' in device and isinstance(device['data'], dict):
                        for key, value in device['data'].items():
                            if isinstance(value, str) and len(value) <= 100:
                                print(f"   {key}: {value}")
                    
                    print(f"   URL: {device['url']}")
                
            else:
                logger.warning("No cellular mobile devices found")
                print("\n❌ No cellular mobile devices found")
                print("This could be due to:")
                print("1. Website requires login/authentication")
                print("2. Search parameters need to be adjusted")
                print("3. Data is loaded dynamically via AJAX")
                print("4. Website structure has changed")
                
        except Exception as e:
            logger.error(f"Error during comprehensive search: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
        
        return all_devices

def main():
    """Main function"""
    scraper = TargetedNBTCScraper()
    
    print("🚀 Targeted NBTC Equipment Scraper")
    print("=" * 50)
    print("Searching for Cellular Mobile (GSM/WCDMA/LTE/NR) equipment...")
    
    devices = scraper.run_comprehensive_search()
    
    if devices:
        print(f"\n✅ Successfully found {len(devices)} devices!")
        print(f"📁 Results saved to JSON file")
        
        # Show summary by type
        type_counts = {}
        for device in devices:
            device_type = device.get('type', 'unknown')
            type_counts[device_type] = type_counts.get(device_type, 0) + 1
        
        print(f"\n📊 Device Summary by Source Type:")
        for device_type, count in type_counts.items():
            print(f"   {device_type}: {count}")
    else:
        print("\n❌ No devices found")
        print("\n💡 Next steps to try:")
        print("1. Install Chrome browser: sudo bash install_chrome.sh")
        print("2. Try manual parsing: python3 manual_parser.py")
        print("3. Use VPN or different network")
        print("4. Check if website requires specific authentication")

if __name__ == "__main__":
    main()