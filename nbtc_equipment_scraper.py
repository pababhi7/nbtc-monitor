#!/usr/bin/env python3
"""
NBTC Equipment Scraper
Scrapes Thai telecommunications equipment database for Cellular Mobile equipment
and sends Telegram notifications for new findings.
"""

import os
import asyncio
import logging
import time
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import telegram
from telegram import Bot
from dotenv import load_dotenv
import schedule
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('equipment_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()

class Equipment(Base):
    __tablename__ = 'equipment'
    
    id = Column(Integer, primary_key=True)
    equipment_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(500))
    category = Column(String(200))
    subcategory = Column(String(200))
    brand = Column(String(200))
    model = Column(String(200))
    certification_number = Column(String(200))
    certification_date = Column(String(100))
    expiry_date = Column(String(100))
    company = Column(String(500))
    url = Column(String(1000))
    details = Column(Text)
    first_seen = Column(DateTime, default=datetime.now)
    notified = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Equipment(id={self.equipment_id}, name={self.name})>"

@dataclass
class EquipmentData:
    equipment_id: str
    name: str
    category: str
    subcategory: str
    brand: str
    model: str
    certification_number: str
    certification_date: str
    expiry_date: str
    company: str
    url: str
    details: str

class NBTCEquipmentScraper:
    def __init__(self):
        self.base_url = "https://mocheck.nbtc.go.th"
        self.search_url = "https://mocheck.nbtc.go.th/search-equipments"
        self.target_category = "Cellular Mobile (GSM/WCDMA/LTE/NR)"
        
        # Configuration from environment
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.max_pages = int(os.getenv('MAX_PAGES_TO_SCRAPE', 50))
        
        # Database setup
        db_url = os.getenv('DATABASE_URL', 'sqlite:///equipment_tracker.db')
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Telegram bot
        if self.telegram_token:
            self.bot = Bot(token=self.telegram_token)
        else:
            self.bot = None
            logger.warning("No Telegram bot token provided")
        
        # Selenium driver
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options for scraping"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Anti-detection measures
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to avoid detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def close_driver(self):
        """Close the selenium driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def wait_for_cloudflare(self, timeout=60):
        """Wait for Cloudflare challenge to be solved"""
        logger.info("Waiting for Cloudflare challenge...")
        
        try:
            # Wait for either the main content to load or timeout
            WebDriverWait(self.driver, timeout).until(
                lambda driver: "Just a moment..." not in driver.page_source
                and "Enable JavaScript and cookies" not in driver.page_source
            )
            logger.info("Cloudflare challenge passed")
            time.sleep(3)  # Additional wait for page to fully load
            return True
        except TimeoutException:
            logger.error("Cloudflare challenge timeout")
            return False
    
    def get_page_with_retry(self, url: str, max_retries: int = 3) -> bool:
        """Get page with retry logic for Cloudflare protection"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to load {url} (attempt {attempt + 1})")
                self.driver.get(url)
                
                if self.wait_for_cloudflare():
                    return True
                    
                logger.warning(f"Failed to load page on attempt {attempt + 1}")
                time.sleep(5 * (attempt + 1))  # Exponential backoff
                
            except Exception as e:
                logger.error(f"Error loading page: {e}")
                time.sleep(5)
                
        return False
    
    def search_equipment(self) -> List[str]:
        """Search for equipment and return list of equipment URLs"""
        equipment_urls = []
        
        if not self.get_page_with_retry(self.search_url):
            logger.error("Failed to load search page")
            return equipment_urls
        
        try:
            # Look for search forms or navigation elements
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find equipment links - this will need to be adjusted based on actual page structure
            # Look for links that might lead to equipment details
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                if href and ('equipment' in href or 'detail' in href):
                    full_url = urljoin(self.base_url, href)
                    if full_url not in equipment_urls:
                        equipment_urls.append(full_url)
            
            # Try to find pagination and navigate through pages
            page_num = 1
            while page_num <= self.max_pages:
                logger.info(f"Searching page {page_num}")
                
                # Look for next page button or pagination
                try:
                    next_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Next') or contains(text(), 'ถัดไป') or contains(@class, 'next')]")
                    
                    if next_buttons:
                        next_buttons[0].click()
                        time.sleep(3)
                        
                        # Parse new page for equipment links
                        page_source = self.driver.page_source
                        soup = BeautifulSoup(page_source, 'html.parser')
                        links = soup.find_all('a', href=True)
                        
                        for link in links:
                            href = link.get('href')
                            if href and ('equipment' in href or 'detail' in href):
                                full_url = urljoin(self.base_url, href)
                                if full_url not in equipment_urls:
                                    equipment_urls.append(full_url)
                    else:
                        break
                        
                except NoSuchElementException:
                    break
                    
                page_num += 1
                
        except Exception as e:
            logger.error(f"Error during search: {e}")
            
        logger.info(f"Found {len(equipment_urls)} equipment URLs")
        return equipment_urls
    
    def scrape_equipment_details(self, url: str) -> Optional[EquipmentData]:
        """Scrape detailed information from an equipment page"""
        try:
            if not self.get_page_with_retry(url):
                logger.error(f"Failed to load equipment page: {url}")
                return None
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract equipment details - this will need to be adjusted based on actual page structure
            equipment_data = {
                'equipment_id': '',
                'name': '',
                'category': '',
                'subcategory': '',
                'brand': '',
                'model': '',
                'certification_number': '',
                'certification_date': '',
                'expiry_date': '',
                'company': '',
                'url': url,
                'details': ''
            }
            
            # Look for text containing our target category
            page_text = soup.get_text()
            
            # Extract equipment ID from URL
            if '/equipments/' in url:
                equipment_data['equipment_id'] = url.split('/equipments/')[-1].split('/')[0]
            elif 'search-equipments/' in url:
                equipment_data['equipment_id'] = url.split('search-equipments/')[-1].split('/')[0]
            
            # Look for Thai text patterns
            thai_patterns = [
                'ประเภทย่อยเครื่องโทรคมนาคม',
                'Cellular Mobile',
                'GSM', 'WCDMA', 'LTE', 'NR',
                'เครื่องโทรศัพท์', 'โทรคมนาคม'
            ]
            
            contains_target = any(pattern in page_text for pattern in thai_patterns)
            
            if contains_target:
                # Try to extract structured data
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            key = cells[0].get_text(strip=True)
                            value = cells[1].get_text(strip=True)
                            
                            # Map Thai/English keys to our data structure
                            if any(word in key.lower() for word in ['name', 'ชื่อ', 'model']):
                                equipment_data['name'] = value
                            elif any(word in key.lower() for word in ['brand', 'ยี่ห้อ', 'manufacturer']):
                                equipment_data['brand'] = value
                            elif any(word in key.lower() for word in ['category', 'ประเภท']):
                                equipment_data['category'] = value
                            elif any(word in key.lower() for word in ['subcategory', 'ประเภทย่อย']):
                                equipment_data['subcategory'] = value
                            elif any(word in key.lower() for word in ['company', 'บริษัท']):
                                equipment_data['company'] = value
                            elif any(word in key.lower() for word in ['certification', 'เลขที่', 'หนังสือรับรอง']):
                                equipment_data['certification_number'] = value
                
                # Check if this is the target category
                if self.target_category.lower() in page_text.lower() or \
                   'cellular mobile' in page_text.lower() or \
                   any(tech in page_text.upper() for tech in ['GSM', 'WCDMA', 'LTE', 'NR']):
                    
                    equipment_data['subcategory'] = self.target_category
                    equipment_data['details'] = page_text[:1000]  # Store first 1000 chars
                    
                    return EquipmentData(**equipment_data)
            
        except Exception as e:
            logger.error(f"Error scraping equipment details from {url}: {e}")
            
        return None
    
    def is_new_equipment(self, equipment_id: str) -> bool:
        """Check if equipment is new (not in database)"""
        existing = self.session.query(Equipment).filter_by(equipment_id=equipment_id).first()
        return existing is None
    
    def save_equipment(self, equipment_data: EquipmentData) -> Equipment:
        """Save equipment to database"""
        equipment = Equipment(
            equipment_id=equipment_data.equipment_id,
            name=equipment_data.name,
            category=equipment_data.category,
            subcategory=equipment_data.subcategory,
            brand=equipment_data.brand,
            model=equipment_data.model,
            certification_number=equipment_data.certification_number,
            certification_date=equipment_data.certification_date,
            expiry_date=equipment_data.expiry_date,
            company=equipment_data.company,
            url=equipment_data.url,
            details=equipment_data.details
        )
        
        self.session.add(equipment)
        self.session.commit()
        return equipment
    
    async def send_telegram_notification(self, equipment: Equipment):
        """Send Telegram notification for new equipment"""
        if not self.bot or not self.telegram_chat_id:
            logger.warning("Telegram not configured, skipping notification")
            return
        
        try:
            message = f"""🔥 *New Cellular Mobile Equipment Found!*

📱 *Name:* {equipment.name or 'N/A'}
🏷️ *Brand:* {equipment.brand or 'N/A'}
📋 *Model:* {equipment.model or 'N/A'}
🏢 *Company:* {equipment.company or 'N/A'}
📄 *Cert #:* {equipment.certification_number or 'N/A'}
🔗 *URL:* {equipment.url}

*Category:* {equipment.subcategory}

*Found at:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            await self.bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            # Mark as notified
            equipment.notified = True
            self.session.commit()
            
            logger.info(f"Telegram notification sent for equipment {equipment.equipment_id}")
            
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
    
    async def run_scrape_cycle(self):
        """Run a complete scrape cycle"""
        logger.info("Starting scrape cycle...")
        
        try:
            self.setup_driver()
            
            # Search for equipment URLs
            equipment_urls = self.search_equipment()
            
            if not equipment_urls:
                logger.warning("No equipment URLs found")
                return
            
            new_equipment_count = 0
            cellular_equipment_count = 0
            
            for url in equipment_urls:
                try:
                    # Add delay between requests
                    time.sleep(2)
                    
                    # Scrape equipment details
                    equipment_data = self.scrape_equipment_details(url)
                    
                    if equipment_data and self.target_category.lower() in equipment_data.subcategory.lower():
                        cellular_equipment_count += 1
                        
                        if self.is_new_equipment(equipment_data.equipment_id):
                            # Save new equipment
                            equipment = self.save_equipment(equipment_data)
                            new_equipment_count += 1
                            
                            # Send notification
                            await self.send_telegram_notification(equipment)
                            
                            logger.info(f"New cellular mobile equipment found: {equipment.name}")
                        else:
                            logger.debug(f"Equipment already exists: {equipment_data.equipment_id}")
                
                except Exception as e:
                    logger.error(f"Error processing URL {url}: {e}")
                    continue
            
            logger.info(f"Scrape cycle completed. Found {cellular_equipment_count} cellular equipment, {new_equipment_count} new")
            
        except Exception as e:
            logger.error(f"Error in scrape cycle: {e}")
        finally:
            self.close_driver()
    
    def run_continuous(self):
        """Run scraper continuously on schedule"""
        interval = int(os.getenv('SCRAPE_INTERVAL_MINUTES', 30))
        
        # Run initial scrape
        asyncio.run(self.run_scrape_cycle())
        
        # Schedule periodic scrapes
        schedule.every(interval).minutes.do(lambda: asyncio.run(self.run_scrape_cycle()))
        
        logger.info(f"Scraper scheduled to run every {interval} minutes")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    """Main function"""
    scraper = NBTCEquipmentScraper()
    
    try:
        scraper.run_continuous()
    except KeyboardInterrupt:
        logger.info("Scraper stopped by user")
    except Exception as e:
        logger.error(f"Scraper error: {e}")
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    main()