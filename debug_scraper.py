#!/usr/bin/env python3
"""
Debug script to test NBTC website scraping without Selenium
"""

import requests
from bs4 import BeautifulSoup
import json
import time

def test_website_access():
    """Test basic access to the NBTC website"""
    print("🔍 Testing NBTC Website Access...")
    
    # Test the main website
    urls_to_test = [
        "https://mocheck.nbtc.go.th",
        "https://mocheck.nbtc.go.th/search-equipments",
        "https://mocheck.nbtc.go.th/search-equipments/1624970",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    for url in urls_to_test:
        print(f"\n📡 Testing: {url}")
        try:
            response = session.get(url, timeout=30)
            print(f"Status Code: {response.status_code}")
            print(f"Content Length: {len(response.content)} bytes")
            
            # Check for Cloudflare
            if "cloudflare" in response.text.lower() or "just a moment" in response.text.lower():
                print("⚠️  Cloudflare protection detected")
            
            # Check for equipment content
            if "equipment" in response.text.lower() or "เครื่อง" in response.text:
                print("✅ Equipment-related content found")
            else:
                print("❌ No equipment content found")
            
            # Save response for debugging
            filename = f"debug_{url.split('/')[-1] or 'home'}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"💾 Response saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(2)

def test_search_api():
    """Test if there's an API endpoint for equipment search"""
    print("\n🔍 Testing potential API endpoints...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
    }
    
    api_endpoints = [
        "https://mocheck.nbtc.go.th/api/equipment",
        "https://mocheck.nbtc.go.th/api/search",
        "https://mocheck.nbtc.go.th/equipment/search",
        "https://mocheck.nbtc.go.th/search",
    ]
    
    session = requests.Session()
    session.headers.update(headers)
    
    for endpoint in api_endpoints:
        print(f"\n📡 Testing API: {endpoint}")
        try:
            response = session.get(endpoint, timeout=15)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ JSON response received: {len(str(data))} chars")
                    print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                except:
                    print(f"📄 Text response: {len(response.text)} chars")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def analyze_page_structure():
    """Analyze the structure of a known equipment page"""
    print("\n🔍 Analyzing page structure...")
    
    test_url = "https://mocheck.nbtc.go.th/search-equipments/1624970"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        response = requests.get(test_url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for common elements
        print("\n📋 Page Analysis:")
        print(f"Title: {soup.title.string if soup.title else 'No title'}")
        
        # Check for forms
        forms = soup.find_all('form')
        print(f"Forms found: {len(forms)}")
        
        # Check for tables
        tables = soup.find_all('table')
        print(f"Tables found: {len(tables)}")
        
        # Check for links
        links = soup.find_all('a')
        equipment_links = [link for link in links if 'equipment' in str(link.get('href', '')).lower()]
        print(f"Equipment links: {len(equipment_links)}")
        
        # Look for cellular mobile text
        page_text = soup.get_text()
        cellular_keywords = ['cellular mobile', 'gsm', 'wcdma', 'lte', 'nr', 'เครื่องโทรคมนาคม']
        found_keywords = [kw for kw in cellular_keywords if kw.lower() in page_text.lower()]
        print(f"Cellular keywords found: {found_keywords}")
        
        # Check for pagination
        pagination = soup.find_all(['nav', 'div'], class_=lambda x: x and ('page' in x.lower() or 'pagination' in x.lower()))
        print(f"Pagination elements: {len(pagination)}")
        
        # Save the parsed content
        with open('debug_page_structure.txt', 'w', encoding='utf-8') as f:
            f.write(f"Title: {soup.title.string if soup.title else 'No title'}\n\n")
            f.write(f"Page text preview (first 1000 chars):\n{page_text[:1000]}\n\n")
            f.write(f"Forms: {len(forms)}\n")
            f.write(f"Tables: {len(tables)}\n")
            f.write(f"Links: {len(links)}\n")
            f.write(f"Equipment links: {len(equipment_links)}\n")
            if equipment_links:
                f.write("Equipment links:\n")
                for link in equipment_links[:10]:  # First 10
                    f.write(f"  - {link.get('href')}: {link.get_text(strip=True)[:50]}\n")
        
        print("💾 Page analysis saved to debug_page_structure.txt")
        
    except Exception as e:
        print(f"❌ Error analyzing page: {e}")

def main():
    """Run all debug tests"""
    print("🧪 NBTC Website Debug Tool")
    print("=" * 50)
    
    # Test basic website access
    test_website_access()
    
    # Test API endpoints
    test_search_api()
    
    # Analyze page structure
    analyze_page_structure()
    
    print("\n" + "=" * 50)
    print("✅ Debug complete! Check the generated files:")
    print("- debug_*.html - Raw responses")
    print("- debug_page_structure.txt - Analysis results")

if __name__ == "__main__":
    main()