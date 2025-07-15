#!/bin/bash

echo "🚀 Chrome Browser Installation Script for NBTC Scraper"
echo "======================================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script needs to be run with sudo"
    echo "💡 Usage: sudo bash install_chrome.sh"
    exit 1
fi

echo "📋 Installing Chrome Browser..."

# Update package list
echo "1️⃣ Updating package list..."
apt update

# Install required packages
echo "2️⃣ Installing required packages..."
apt install -y wget gnupg

# Add Google signing key
echo "3️⃣ Adding Google signing key..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -

# Add Google Chrome repository
echo "4️⃣ Adding Chrome repository..."
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Update package list again
echo "5️⃣ Updating package list with Chrome repository..."
apt update

# Install Google Chrome
echo "6️⃣ Installing Google Chrome..."
apt install -y google-chrome-stable

# Verify installation
echo "7️⃣ Verifying installation..."
if command -v google-chrome &> /dev/null; then
    CHROME_VERSION=$(google-chrome --version)
    echo "✅ Chrome installed successfully: $CHROME_VERSION"
else
    echo "❌ Chrome installation failed"
    exit 1
fi

# Install additional dependencies for headless mode
echo "8️⃣ Installing additional dependencies..."
apt install -y libnss3-dev libgconf-2-4 libxss1 libappindicator1 libindicator7 xvfb

echo ""
echo "🎉 Installation Complete!"
echo "========================================"
echo "✅ Google Chrome installed successfully"
echo "✅ Additional dependencies installed"
echo ""
echo "🔧 Next Steps:"
echo "1. Test the scraper: python3 improved_scraper.py"
echo "2. Or run the original: python3 nbtc_equipment_scraper.py"
echo ""
echo "💡 If you still get errors, try:"
echo "   - Using VPN or different network"
echo "   - Running at different times"
echo "   - Using the manual parser: python3 manual_parser.py"