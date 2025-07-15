#!/usr/bin/env python3
"""
Manual HTML Parser for NBTC Equipment Data
Use this when automated scraping is blocked by Cloudflare
"""

import os
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

class ManualNBTCParser:
    def __init__(self):
        self.target_keywords = [
            'cellular mobile', 'gsm', 'wcdma', 'lte', 'nr', '5g',
            'เครื่องโทรคมนาคม', 'โทรศัพท์', 'มือถือ'
        ]
    
    def parse_html_file(self, html_file: str) -> List[Dict]:
        """Parse a saved HTML file for equipment data"""
        print(f"📄 Parsing HTML file: {html_file}")
        
        if not os.path.exists(html_file):
            print(f"❌ File not found: {html_file}")
            return []
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Analysis
            print(f"📊 Page Analysis:")
            print(f"   Title: {soup.title.string if soup.title else 'No title'}")
            print(f"   Content Length: {len(html_content)} characters")
            
            # Check if this is a Cloudflare page
            if "Just a moment" in html_content or "cloudflare" in html_content.lower():
                print("⚠️  This appears to be a Cloudflare challenge page")
                print("   Please save the HTML AFTER the page loads completely")
                return []
            
            equipment_data = []
            
            # Extract equipment information
            equipment_data.extend(self.extract_from_tables(soup))
            equipment_data.extend(self.extract_from_lists(soup))
            equipment_data.extend(self.extract_from_cards(soup))
            equipment_data.extend(self.extract_from_text(soup))
            
            # Filter for cellular mobile equipment
            cellular_equipment = self.filter_cellular_equipment(equipment_data)
            
            print(f"✅ Found {len(equipment_data)} total equipment entries")
            print(f"📱 Found {len(cellular_equipment)} cellular mobile entries")
            
            return cellular_equipment
            
        except Exception as e:
            print(f"❌ Error parsing HTML file: {e}")
            return []
    
    def extract_from_tables(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract equipment data from tables"""
        equipment = []
        tables = soup.find_all('table')
        
        print(f"🔍 Analyzing {len(tables)} tables...")
        
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            headers = []
            
            # Try to find headers
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            for row in rows[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    row_data = {}
                    
                    for j, cell in enumerate(cells):
                        header = headers[j] if j < len(headers) else f"column_{j}"
                        value = cell.get_text(strip=True)
                        row_data[header] = value
                    
                    # Look for equipment-related data
                    row_text = ' '.join(row_data.values()).lower()
                    if any(keyword in row_text for keyword in ['equipment', 'device', 'เครื่อง', 'อุปกรณ์']):
                        equipment.append({
                            'source': f'table_{i}',
                            'type': 'table_row',
                            'data': row_data,
                            'raw_text': row_text
                        })
        
        return equipment
    
    def extract_from_lists(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract equipment data from lists"""
        equipment = []
        lists = soup.find_all(['ul', 'ol'])
        
        print(f"🔍 Analyzing {len(lists)} lists...")
        
        for i, list_elem in enumerate(lists):
            items = list_elem.find_all('li')
            
            for j, item in enumerate(items):
                text = item.get_text(strip=True)
                
                # Look for equipment-related items
                if any(keyword in text.lower() for keyword in ['equipment', 'device', 'เครื่อง', 'อุปกรณ์']):
                    equipment.append({
                        'source': f'list_{i}_item_{j}',
                        'type': 'list_item',
                        'text': text,
                        'html': str(item)
                    })
        
        return equipment
    
    def extract_from_cards(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract equipment data from card-like structures"""
        equipment = []
        
        # Look for common card patterns
        card_selectors = [
            'div[class*="card"]',
            'div[class*="item"]',
            'div[class*="product"]',
            'div[class*="equipment"]',
            'div[class*="device"]'
        ]
        
        for selector in card_selectors:
            cards = soup.select(selector)
            print(f"🔍 Found {len(cards)} elements matching '{selector}'")
            
            for i, card in enumerate(cards):
                text = card.get_text(strip=True)
                
                if text and len(text) > 10:  # Ignore empty or very short cards
                    equipment.append({
                        'source': f'card_{selector}_{i}',
                        'type': 'card',
                        'text': text,
                        'html': str(card)
                    })
        
        return equipment
    
    def extract_from_text(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract equipment data from general text content"""
        equipment = []
        
        # Get all text content
        page_text = soup.get_text()
        
        # Look for patterns that might indicate equipment
        equipment_patterns = [
            r'เครื่อง[\w\s]{10,50}',  # Thai equipment descriptions
            r'อุปกรณ์[\w\s]{10,50}',  # Thai device descriptions
            r'[A-Z]{2,}\s*[0-9]{2,}',  # Model numbers
            r'GSM|WCDMA|LTE|NR|5G',   # Technology keywords
        ]
        
        for pattern in equipment_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                equipment.append({
                    'source': 'text_pattern',
                    'type': 'pattern_match',
                    'pattern': pattern,
                    'text': match.strip()
                })
        
        return equipment
    
    def filter_cellular_equipment(self, equipment_data: List[Dict]) -> List[Dict]:
        """Filter equipment for cellular mobile devices"""
        cellular_equipment = []
        
        for item in equipment_data:
            # Get all text from the item
            item_text = ""
            if 'text' in item:
                item_text += item['text']
            if 'raw_text' in item:
                item_text += item['raw_text']
            if 'data' in item:
                item_text += ' '.join(str(v) for v in item['data'].values())
            
            item_text = item_text.lower()
            
            # Check for cellular mobile keywords
            if any(keyword in item_text for keyword in self.target_keywords):
                item['is_cellular'] = True
                item['matched_keywords'] = [kw for kw in self.target_keywords if kw in item_text]
                cellular_equipment.append(item)
        
        return cellular_equipment
    
    def save_results(self, equipment_data: List[Dict], output_file: str = None):
        """Save extracted equipment data to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"extracted_equipment_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(equipment_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Results saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
    
    def create_report(self, equipment_data: List[Dict]):
        """Create a human-readable report"""
        if not equipment_data:
            print("📄 No equipment data to report")
            return
        
        print("\n" + "="*60)
        print("📱 CELLULAR MOBILE EQUIPMENT REPORT")
        print("="*60)
        
        for i, item in enumerate(equipment_data, 1):
            print(f"\n🔸 Equipment #{i}")
            print(f"   Source: {item.get('source', 'Unknown')}")
            print(f"   Type: {item.get('type', 'Unknown')}")
            
            if 'matched_keywords' in item:
                print(f"   Keywords: {', '.join(item['matched_keywords'])}")
            
            if 'text' in item:
                print(f"   Text: {item['text'][:100]}...")
            
            if 'data' in item:
                print("   Data:")
                for key, value in item['data'].items():
                    if value and len(str(value)) > 2:
                        print(f"     {key}: {value}")

def main():
    """Main function to demonstrate usage"""
    parser = ManualNBTCParser()
    
    print("🔧 Manual NBTC Equipment Parser")
    print("=" * 50)
    print("Instructions:")
    print("1. Open https://mocheck.nbtc.go.th/search-equipments in your browser")
    print("2. Wait for the page to load completely (past Cloudflare)")
    print("3. Right-click → View Page Source")
    print("4. Save the source as 'nbtc_page.html' in this directory")
    print("5. Run this script again")
    print()
    
    # Look for HTML files in current directory
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    
    if not html_files:
        print("❌ No HTML files found in current directory")
        print("💡 Please save the website's HTML source and try again")
        return
    
    print(f"📁 Found HTML files: {', '.join(html_files)}")
    
    # Process each HTML file
    all_equipment = []
    for html_file in html_files:
        equipment_data = parser.parse_html_file(html_file)
        all_equipment.extend(equipment_data)
    
    if all_equipment:
        # Create report
        parser.create_report(all_equipment)
        
        # Save results
        parser.save_results(all_equipment)
        
        print(f"\n🎉 Processing complete!")
        print(f"📱 Found {len(all_equipment)} cellular mobile equipment entries")
    else:
        print("\n❌ No cellular mobile equipment found")
        print("💡 Make sure you saved the HTML after the page loaded completely")

if __name__ == "__main__":
    main()