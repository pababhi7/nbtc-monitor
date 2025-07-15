#!/usr/bin/env python3
"""
Setup script for NBTC Equipment Scraper
"""

import os
import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False
    return True

def install_chrome():
    """Install Chrome browser (for Linux)"""
    print("Checking Chrome installation...")
    try:
        # Check if Chrome is already installed
        subprocess.run(["google-chrome", "--version"], capture_output=True, check=True)
        print("✅ Chrome is already installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Chrome not found. Installing...")
        
        try:
            # Update package list
            subprocess.run(["sudo", "apt", "update"], check=True)
            
            # Install wget if not present
            subprocess.run(["sudo", "apt", "install", "-y", "wget"], check=True)
            
            # Download Chrome
            subprocess.run([
                "wget", "-q", "-O", "-", 
                "https://dl.google.com/linux/linux_signing_key.pub"
            ], stdout=subprocess.PIPE, check=True)
            
            # Add Chrome repository
            subprocess.run([
                "sudo", "sh", "-c", 
                "echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google-chrome.list"
            ], check=True)
            
            # Update and install Chrome
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "google-chrome-stable"], check=True)
            
            print("✅ Chrome installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing Chrome: {e}")
            print("Please install Chrome manually:")
            print("1. Download from https://www.google.com/chrome/")
            print("2. Or use: sudo apt install google-chrome-stable")
            return False

def create_config():
    """Create configuration files"""
    print("Setting up configuration...")
    
    # Check if .env exists
    if not Path(".env").exists():
        print("❌ .env file not found")
        print("Please create .env file with your Telegram bot configuration:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("TELEGRAM_CHAT_ID=your_chat_id_here")
        return False
    
    # Load .env to check if tokens are set
    with open(".env", "r") as f:
        env_content = f.read()
    
    if "your_telegram_bot_token_here" in env_content:
        print("❌ Please update your Telegram bot token in .env file")
        return False
    
    if "your_chat_id_here" in env_content:
        print("❌ Please update your Telegram chat ID in .env file")
        return False
    
    print("✅ Configuration looks good")
    return True

def create_systemd_service():
    """Create systemd service file for automatic startup"""
    service_content = f"""[Unit]
Description=NBTC Equipment Scraper
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={os.getcwd()}
ExecStart={sys.executable} {os.path.join(os.getcwd(), 'nbtc_equipment_scraper.py')}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_path = "/etc/systemd/system/nbtc-scraper.service"
    
    try:
        print("Creating systemd service...")
        with open("nbtc-scraper.service", "w") as f:
            f.write(service_content)
        
        print(f"Service file created. To install as system service, run:")
        print(f"sudo cp nbtc-scraper.service {service_path}")
        print("sudo systemctl daemon-reload")
        print("sudo systemctl enable nbtc-scraper")
        print("sudo systemctl start nbtc-scraper")
        
    except Exception as e:
        print(f"❌ Error creating service file: {e}")

def main():
    """Main setup function"""
    print("🚀 Setting up NBTC Equipment Scraper...")
    print("=" * 50)
    
    success = True
    
    # Install requirements
    if not install_requirements():
        success = False
    
    # Install Chrome
    if not install_chrome():
        success = False
    
    # Check configuration
    if not create_config():
        success = False
    
    # Create service file
    create_systemd_service()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update .env file with your Telegram bot token and chat ID")
        print("2. Test the scraper: python3 nbtc_equipment_scraper.py")
        print("3. Install as system service (optional, see above)")
    else:
        print("❌ Setup completed with errors. Please fix the issues above.")
    
    print("\nTo get your Telegram bot token:")
    print("1. Message @BotFather on Telegram")
    print("2. Create a new bot with /newbot")
    print("3. Copy the token to .env file")
    print("\nTo get your chat ID:")
    print("1. Message @userinfobot on Telegram")
    print("2. Copy the ID to .env file")

if __name__ == "__main__":
    main()