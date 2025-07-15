#!/usr/bin/env python3
"""
Test script to verify that the NBTC Equipment Scraper setup is working correctly
"""

import sys
import os

def test_imports():
    """Test that all required packages can be imported"""
    print("Testing imports...")
    
    try:
        import selenium
        print(f"✅ Selenium: {selenium.__version__}")
    except ImportError as e:
        print(f"❌ Selenium import failed: {e}")
        return False
    
    try:
        import requests
        print(f"✅ Requests: {requests.__version__}")
    except ImportError as e:
        print(f"❌ Requests import failed: {e}")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print(f"✅ BeautifulSoup4: Available")
    except ImportError as e:
        print(f"❌ BeautifulSoup4 import failed: {e}")
        return False
    
    try:
        import telegram
        print(f"✅ Python Telegram Bot: {telegram.__version__}")
    except ImportError as e:
        print(f"❌ Python Telegram Bot import failed: {e}")
        return False
    
    try:
        import schedule
        print(f"✅ Schedule: Available")
    except ImportError as e:
        print(f"❌ Schedule import failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print(f"✅ Python Dotenv: Available")
    except ImportError as e:
        print(f"❌ Python Dotenv import failed: {e}")
        return False
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print(f"✅ WebDriver Manager: Available")
    except ImportError as e:
        print(f"❌ WebDriver Manager import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print(f"✅ Pandas: {pd.__version__}")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    return True

def test_chrome_driver():
    """Test Chrome driver installation"""
    print("\nTesting Chrome WebDriver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Try to install and setup driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Test basic functionality
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        print(f"✅ Chrome WebDriver: Working (Test page title: {title})")
        return True
        
    except Exception as e:
        print(f"❌ Chrome WebDriver failed: {e}")
        return False

def test_environment_file():
    """Test .env file configuration"""
    print("\nTesting environment configuration...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("Please create .env file with your Telegram configuration")
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not telegram_token or telegram_token == 'your_telegram_bot_token_here':
            print("❌ TELEGRAM_BOT_TOKEN not configured")
            return False
        
        if not chat_id or chat_id == 'your_chat_id_here':
            print("❌ TELEGRAM_CHAT_ID not configured")
            return False
        
        print("✅ Environment configuration: Ready")
        return True
        
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\nTesting database...")
    
    try:
        from sqlalchemy import create_engine
        from nbtc_equipment_scraper import Base, Equipment
        
        # Create test database
        engine = create_engine('sqlite:///test_equipment.db')
        Base.metadata.create_all(engine)
        
        print("✅ Database: Schema created successfully")
        
        # Clean up test database
        os.remove('test_equipment.db')
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 NBTC Equipment Scraper - Setup Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 4
    
    # Test imports
    if test_imports():
        tests_passed += 1
    
    # Test Chrome driver
    if test_chrome_driver():
        tests_passed += 1
    
    # Test environment
    if test_environment_file():
        tests_passed += 1
    
    # Test database
    if test_database():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Setup is complete.")
        print("\nNext steps:")
        print("1. Configure your .env file with Telegram credentials")
        print("2. Test with: python3 manage_scraper.py test-telegram")
        print("3. Run single scrape: python3 manage_scraper.py run-once")
        print("4. Start continuous monitoring: python3 nbtc_equipment_scraper.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("- Make sure all dependencies are installed")
        print("- Check your .env file configuration")
        print("- Install Chrome browser if WebDriver test failed")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)