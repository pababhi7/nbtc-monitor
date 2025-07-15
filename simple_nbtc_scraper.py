#!/usr/bin/env python3
"""
Simple NBTC Equipment Scraper
Uses only requests and BeautifulSoup - no Selenium required
"""

import requests
import json
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class SimpleNBTCScraper:
    def __init__(self):
        self.base_url = "https://mocheck.nbtc.go.th"
        self.session = requests.Session()
        self.setup_session()
        
        # Target keywords for cellular mobile equipment
        self.cellular_keywords = [
            'cellular mobile', 'gsm', 'wcdma', 'lte', 'nr', '5g',
            'เครื่องโทรคมนาคม', 'cellular', 'mobile', 'phone', 'smartphone',
            'โทรศัพท์', 'มือถือ', 'ระบบเซลลูลาร์', 'ระบบมือถือ'
        ]
    
    def setup_session(self):
        """Setup session with realistic headers and settings"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'th,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(headers)
        
        # Set up session properties
        self.session.max_redirects = 10
        self.session.verify = True
    
    def try_different_endpoints(self):
        """Try different API and page endpoints"""
        endpoints = [
            # Direct API endpoints
            f"{self.base_url}/api/equipments",
            f"{self.base_url}/api/search",
            f"{self.base_url}/api/equipment/search",
            f"{self.base_url}/api/v1/equipments",
            f"{self.base_url}/api/v2/equipments",
            
            # Page endpoints
            f"{self.base_url}/search-equipments",
            f"{self.base_url}/search-equipments/1624970",
            f"{self.base_url}/equipments",
            f"{self.base_url}/equipment",
            f"{self.base_url}/search",
            f"{self.base_url}/en/search-equipments",
            
            # Public endpoints
            f"{self.base_url}/public/equipments",
            f"{self.base_url}/public/search",
            
            # Common paths
            f"{self.base_url}/",
            f"{self.base_url}/index.php",
            f"{self.base_url}/main.php",
        ]
        
        results = []
        
        for endpoint in endpoints:
            print(f"🔍 Trying endpoint: {endpoint}")
            
            try:
                # Try GET request
                response = self.session.get(endpoint, timeout=30)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'application/json' in content_type:
                        # Handle JSON response
                        try:
                            data = response.json()
                            devices = self.extract_from_json(data, endpoint)
                            if devices:
                                print(f"   ✅ Found {len(devices)} devices in JSON!")
                                results.extend(devices)
                        except json.JSONDecodeError:
                            print(f"   ❌ Invalid JSON response")
                    
                    elif 'text/html' in content_type:
                        # Handle HTML response
                        if "Just a moment" in response.text:
                            print(f"   ⚠️  Cloudflare protection detected")
                        else:
                            devices = self.extract_from_html(response.text, endpoint)
                            if devices:
                                print(f"   ✅ Found {len(devices)} devices in HTML!")
                                results.extend(devices)
                    
                elif response.status_code == 403:
                    print(f"   ❌ Access forbidden (Cloudflare)")
                elif response.status_code == 404:
                    print(f"   ❌ Not found")
                else:
                    print(f"   ❓ Unexpected status code")
                
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Request failed: {e}")
            
            # Small delay between requests
            time.sleep(random.uniform(1, 3))
        
        return results
    
    def extract_from_json(self, data, source_url):
        """Extract equipment data from JSON responses"""
        devices = []
        
        def search_json_recursive(obj, path=""):
            """Recursively search JSON for cellular equipment"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check if this key-value pair contains cellular equipment
                    if isinstance(value, str):
                        if any(keyword in value.lower() for keyword in self.cellular_keywords):
                            device = {
                                'source': f'json_{path}',
                                'type': 'json_data',
                                'data': {key: value},
                                'matched_keywords': [kw for kw in self.cellular_keywords if kw in value.lower()],
                                'url': source_url,
                                'timestamp': datetime.now().isoformat(),
                                'json_path': current_path
                            }
                            devices.append(device)
                    
                    # Recurse into nested structures
                    search_json_recursive(value, current_path)
                    
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]" if path else f"[{i}]"
                    search_json_recursive(item, current_path)
        
        search_json_recursive(data)
        return devices
    
    def extract_from_html(self, html_content, source_url):
        """Extract equipment data from HTML responses"""
        devices = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Save HTML for debugging
            timestamp = int(time.time())
            with open(f'simple_scraper_page_{timestamp}.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"   📄 Page title: {soup.title.string if soup.title else 'No title'}")
            print(f"   📄 Content length: {len(html_content)} characters")
            
            # Method 1: Extract from tables
            devices.extend(self.extract_from_tables(soup, source_url))
            
            # Method 2: Extract from forms and select options
            devices.extend(self.extract_from_forms(soup, source_url))
            
            # Method 3: Extract from lists
            devices.extend(self.extract_from_lists(soup, source_url))
            
            # Method 4: Extract from general text content
            devices.extend(self.extract_from_text(soup, source_url))
            
            # Method 5: Extract from script tags (JSON data)
            devices.extend(self.extract_from_scripts(soup, source_url))
            
        except Exception as e:
            print(f"   ❌ Error parsing HTML: {e}")
        
        return devices
    
    def extract_from_tables(self, soup, source_url):
        """Extract equipment from HTML tables"""
        devices = []
        tables = soup.find_all('table')
        
        print(f"      📊 Processing {len(tables)} tables")
        
        for i, table in enumerate(tables):
            try:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                # Get headers
                header_row = rows[0]
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                
                # Process data rows
                for row_idx, row in enumerate(rows[1:], 1):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        
                        row_data = {}
                        for j, cell in enumerate(cells):
                            header = headers[j] if j < len(headers) else f"column_{j}"
                            value = cell.get_text(strip=True)
                            row_data[header] = value
                        
                        # Check if this row contains cellular mobile equipment
                        row_text = ' '.join(row_data.values()).lower()
                        if any(keyword in row_text for keyword in self.cellular_keywords):
                            device = {
                                'source': f'table_{i}_row_{row_idx}',
                                'type': 'table_row',
                                'data': row_data,
                                'matched_keywords': [kw for kw in self.cellular_keywords if kw in row_text],
                                'url': source_url,
                                'timestamp': datetime.now().isoformat(),
                                'raw_text': row_text
                            }
                            devices.append(device)
                            print(f"      ✅ Found cellular device in table {i}, row {row_idx}")
                            
            except Exception as e:
                print(f"      ❌ Error processing table {i}: {e}")
        
        return devices
    
    def extract_from_forms(self, soup, source_url):
        """Extract equipment from forms and select options"""
        devices = []
        forms = soup.find_all('form')
        
        print(f"      📝 Processing {len(forms)} forms")
        
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
                                'url': source_url,
                                'timestamp': datetime.now().isoformat()
                            }
                            devices.append(device)
                            print(f"      ✅ Found cellular device option: {option_text}")
                            
            except Exception as e:
                print(f"      ❌ Error processing form {i}: {e}")
        
        return devices
    
    def extract_from_lists(self, soup, source_url):
        """Extract equipment from HTML lists"""
        devices = []
        lists = soup.find_all(['ul', 'ol'])
        
        print(f"      📋 Processing {len(lists)} lists")
        
        for i, list_elem in enumerate(lists):
            items = list_elem.find_all('li')
            
            for j, item in enumerate(items):
                try:
                    item_text = item.get_text(strip=True)
                    
                    if item_text and any(keyword in item_text.lower() for keyword in self.cellular_keywords):
                        device = {
                            'source': f'list_{i}_item_{j}',
                            'type': 'list_item',
                            'data': {
                                'text': item_text,
                                'html': str(item)
                            },
                            'matched_keywords': [kw for kw in self.cellular_keywords if kw in item_text.lower()],
                            'url': source_url,
                            'timestamp': datetime.now().isoformat()
                        }
                        devices.append(device)
                        print(f"      ✅ Found cellular device in list: {item_text[:50]}...")
                        
                except Exception as e:
                    print(f"      ❌ Error processing list item {i},{j}: {e}")
        
        return devices
    
    def extract_from_text(self, soup, source_url):
        """Extract equipment from general text content"""
        devices = []
        
        # Get all text content
        page_text = soup.get_text()
        
        # Look for patterns that might indicate cellular mobile equipment
        import re
        
        equipment_patterns = [
            r'cellular mobile[\w\s]{10,100}',
            r'gsm[\w\s]{10,50}',
            r'lte[\w\s]{10,50}',
            r'เครื่องโทรคมนาคม[\w\s]{10,100}',
            r'โทรศัพท์[\w\s]{10,50}',
            r'มือถือ[\w\s]{10,50}',
            r'[A-Z]{2,}\s*[0-9]{3,}',  # Model numbers
        ]
        
        for pattern in equipment_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                match_text = match.strip()
                if any(keyword in match_text.lower() for keyword in self.cellular_keywords):
                    device = {
                        'source': 'text_pattern',
                        'type': 'text_match',
                        'data': {
                            'text': match_text,
                            'pattern': pattern
                        },
                        'matched_keywords': [kw for kw in self.cellular_keywords if kw in match_text.lower()],
                        'url': source_url,
                        'timestamp': datetime.now().isoformat()
                    }
                    devices.append(device)
                    print(f"      ✅ Found cellular device in text: {match_text[:50]}...")
        
        return devices
    
    def extract_from_scripts(self, soup, source_url):
        """Extract equipment data from JavaScript variables"""
        devices = []
        scripts = soup.find_all('script')
        
        print(f"      📜 Processing {len(scripts)} script tags")
        
        for i, script in enumerate(scripts):
            try:
                script_content = script.string
                if not script_content:
                    continue
                
                # Look for JSON data or JavaScript arrays
                if any(keyword in script_content.lower() for keyword in ['equipment', 'device', 'cellular']):
                    
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
                                        'url': source_url,
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    devices.append(device)
                                    print(f"      ✅ Found cellular device in script data")
                                    
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                print(f"      ❌ Error processing script {i}: {e}")
        
        return devices
    
    def try_specific_searches(self):
        """Try specific search queries"""
        devices = []
        
        # Specific search URLs to try
        search_urls = [
            f"{self.base_url}/search?q=cellular+mobile",
            f"{self.base_url}/search?q=GSM",
            f"{self.base_url}/search?q=LTE",
            f"{self.base_url}/search?q=เครื่องโทรคมนาคม",
            f"{self.base_url}/search-equipments?type=cellular",
            f"{self.base_url}/search-equipments?category=mobile",
            f"{self.base_url}/api/search?type=cellular",
            f"{self.base_url}/api/equipments?category=cellular",
        ]
        
        for search_url in search_urls:
            print(f"🔍 Trying search: {search_url}")
            
            try:
                response = self.session.get(search_url, timeout=30)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'application/json' in content_type:
                        try:
                            data = response.json()
                            search_devices = self.extract_from_json(data, search_url)
                            devices.extend(search_devices)
                            if search_devices:
                                print(f"   ✅ Found {len(search_devices)} devices!")
                        except json.JSONDecodeError:
                            pass
                    else:
                        search_devices = self.extract_from_html(response.text, search_url)
                        devices.extend(search_devices)
                        if search_devices:
                            print(f"   ✅ Found {len(search_devices)} devices!")
                
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Search failed: {e}")
            
            time.sleep(random.uniform(1, 3))
        
        return devices
    
    def run_simple_search(self):
        """Run the simple search without Chrome"""
        print("🚀 Simple NBTC Equipment Scraper (No Chrome Required)")
        print("=" * 60)
        print("Searching for Cellular Mobile (GSM/WCDMA/LTE/NR) equipment...")
        print()
        
        all_devices = []
        
        # Step 1: Try different endpoints
        print("📡 Step 1: Trying different endpoints...")
        endpoint_devices = self.try_different_endpoints()
        all_devices.extend(endpoint_devices)
        
        print()
        
        # Step 2: Try specific searches
        print("🔍 Step 2: Trying specific searches...")
        search_devices = self.try_specific_searches()
        all_devices.extend(search_devices)
        
        print()
        
        # Step 3: Save results
        if all_devices:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simple_nbtc_devices_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_devices, f, indent=2, ensure_ascii=False)
            
            print(f"🎉 FOUND {len(all_devices)} CELLULAR MOBILE DEVICES!")
            print("=" * 50)
            print(f"📁 Results saved to: {filename}")
            print()
            
            # Show summary
            type_counts = {}
            for device in all_devices:
                device_type = device.get('type', 'unknown')
                type_counts[device_type] = type_counts.get(device_type, 0) + 1
            
            print("📊 Device Summary by Source Type:")
            for device_type, count in type_counts.items():
                print(f"   {device_type}: {count}")
            
            print()
            print("📱 Device Details:")
            for i, device in enumerate(all_devices, 1):
                print(f"\n🔸 Device #{i}:")
                print(f"   Source: {device['source']}")
                print(f"   Type: {device['type']}")
                print(f"   Keywords: {', '.join(device['matched_keywords'])}")
                print(f"   URL: {device['url']}")
                
                if 'data' in device and isinstance(device['data'], dict):
                    for key, value in device['data'].items():
                        if isinstance(value, str) and len(value) <= 100:
                            print(f"   {key}: {value}")
            
        else:
            print("❌ No cellular mobile devices found")
            print()
            print("💡 This could be due to:")
            print("1. Website has strict Cloudflare protection")
            print("2. Equipment data requires authentication")
            print("3. Data is loaded dynamically via AJAX")
            print("4. Website structure has changed")
            print("5. Need to use specific search parameters")
            print()
            print("🔧 Try these alternatives:")
            print("1. Use the targeted scraper: python3 targeted_nbtc_scraper.py")
            print("2. Try manual parsing: python3 manual_parser.py")
            print("3. Install Chrome: sudo bash install_chrome.sh")
        
        return all_devices

def main():
    """Main function"""
    scraper = SimpleNBTCScraper()
    scraper.run_simple_search()

if __name__ == "__main__":
    main()