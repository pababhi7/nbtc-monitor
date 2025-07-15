# NBTC Equipment Scraper

A comprehensive web scraper for monitoring the Thai National Broadcasting and Telecommunications Commission (NBTC) equipment database, specifically designed to track **Cellular Mobile (GSM/WCDMA/LTE/NR)** equipment and send real-time Telegram notifications.

## ⚠️ **Important: Cloudflare Protection Issue**

**Status:** The NBTC website has very strict Cloudflare protection (HTTP 403) that blocks automated requests.

**Quick Solutions Available:**
- 🟢 **Manual Parser**: Works immediately - `python3 manual_parser.py`
- 🟡 **Enhanced Scraper**: Requires Chrome installation - `sudo bash install_chrome.sh`
- 🔴 **Original Scraper**: Needs Chrome + additional configuration

See [SOLUTION_GUIDE.md](SOLUTION_GUIDE.md) for detailed troubleshooting.

## Features

🔍 **Smart Web Scraping**
- Multiple Cloudflare bypass strategies
- Enhanced browser automation with anti-detection
- Manual HTML parsing as fallback
- Robust retry mechanisms with exponential backoff

📱 **Telegram Integration**
- Real-time notifications for new equipment
- Markdown-formatted messages with detailed information
- Test notification functionality

🗄️ **Database Management**
- SQLite database for efficient data storage
- Duplicate detection to avoid redundant notifications
- Comprehensive equipment tracking with timestamps

📊 **Monitoring & Analytics**
- Database statistics and reporting
- CSV export functionality
- Equipment listing with filtering options

⚙️ **Automation**
- Configurable scraping intervals
- Systemd service support for automatic startup
- Continuous monitoring with scheduling

## Target Equipment Category

The scraper specifically monitors for equipment classified as:
**ประเภทย่อยเครื่องโทรคมนาคม Cellular Mobile (GSM/WCDMA/LTE/NR)**

This includes:
- GSM mobile devices
- WCDMA/3G equipment
- LTE/4G devices
- NR/5G equipment
- Cellular modems and routers

## Installation

### Prerequisites

- Linux system (Ubuntu/Debian recommended)
- Python 3.8 or higher
- Google Chrome browser
- Internet connection

### Quick Setup

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd nbtc-equipment-scraper
   chmod +x setup.py
   python3 setup.py
   ```

2. **Configure Telegram**
   
   Create a Telegram bot:
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot` and follow instructions
   - Copy the bot token
   
   Get your chat ID:
   - Message [@userinfobot](https://t.me/userinfobot) on Telegram
   - Copy your chat ID

3. **Update Configuration**
   ```bash
   nano .env
   ```
   
   Replace the placeholder values:
   ```env
   TELEGRAM_BOT_TOKEN=your_actual_bot_token
   TELEGRAM_CHAT_ID=your_actual_chat_id
   ```

### Manual Installation

If the automatic setup fails:

1. **Install Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Install Chrome**
   ```bash
   sudo apt update
   sudo apt install google-chrome-stable
   ```

## Usage

### Running the Scraper

#### One-time Scan
```bash
python3 manage_scraper.py run-once
```

#### Continuous Monitoring
```bash
python3 nbtc_equipment_scraper.py
```

#### As System Service
```bash
sudo cp nbtc-scraper.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nbtc-scraper
sudo systemctl start nbtc-scraper
```

### Management Commands

#### View Equipment Database
```bash
# List recent equipment
python3 manage_scraper.py list

# List with filters
python3 manage_scraper.py list --filter "Cellular Mobile" --limit 50

# Show statistics
python3 manage_scraper.py stats
```

#### Export Data
```bash
# Export all equipment to CSV
python3 manage_scraper.py export

# Export with custom filename
python3 manage_scraper.py export --filename my_equipment_data.csv
```

#### Test Telegram Notifications
```bash
python3 manage_scraper.py test-telegram
```

#### Manage Notifications
```bash
# Resend notifications for unnotified equipment
python3 manage_scraper.py resend

# Reset all notification statuses
python3 manage_scraper.py reset-notifications

# Delete specific equipment
python3 manage_scraper.py delete --equipment-id 1624970
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Required |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | Required |
| `SCRAPE_INTERVAL_MINUTES` | Minutes between scrape cycles | 30 |
| `MAX_PAGES_TO_SCRAPE` | Maximum pages to scrape per cycle | 50 |
| `DATABASE_URL` | Database connection string | `sqlite:///equipment_tracker.db` |

### Example .env File
```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Scraping Settings
SCRAPE_INTERVAL_MINUTES=30
MAX_PAGES_TO_SCRAPE=100

# Database
DATABASE_URL=sqlite:///equipment_tracker.db
```

## System Service Configuration

To run the scraper as a system service that starts automatically:

1. **Install Service**
   ```bash
   sudo cp nbtc-scraper.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable nbtc-scraper
   ```

2. **Start Service**
   ```bash
   sudo systemctl start nbtc-scraper
   ```

3. **Check Status**
   ```bash
   sudo systemctl status nbtc-scraper
   ```

4. **View Logs**
   ```bash
   sudo journalctl -u nbtc-scraper -f
   ```

## Sample Telegram Notification

When new Cellular Mobile equipment is found, you'll receive a notification like:

```
🔥 New Cellular Mobile Equipment Found!

📱 Name: iPhone 15 Pro Max
🏷️ Brand: Apple
📋 Model: A2849
🏢 Company: Apple Thailand Co., Ltd.
📄 Cert #: NBTC-2024-001234
🔗 URL: https://mocheck.nbtc.go.th/search-equipments/1624970

Category: Cellular Mobile (GSM/WCDMA/LTE/NR)

Found at: 2024-01-15 14:30:25
```

## Database Schema

The SQLite database stores the following information:

| Field | Type | Description |
|-------|------|-------------|
| `equipment_id` | String | Unique equipment identifier |
| `name` | String | Equipment name/model |
| `brand` | String | Manufacturer brand |
| `company` | String | Importing/distributing company |
| `category` | String | Equipment category |
| `subcategory` | String | Equipment subcategory |
| `certification_number` | String | NBTC certification number |
| `certification_date` | String | Date of certification |
| `expiry_date` | String | Certification expiry date |
| `url` | String | Source URL |
| `first_seen` | DateTime | When first discovered |
| `notified` | Boolean | Whether notification was sent |

## Troubleshooting

### Common Issues

#### 1. Cloudflare Protection
```
Error: Cloudflare challenge timeout
```
**Solution:** The scraper includes automatic Cloudflare handling, but if issues persist:
- Increase timeout in the script
- Try running with `--headless=false` for debugging
- Check your IP isn't blocked

#### 2. Chrome Driver Issues
```
Error: Unable to locate the Chrome binary
```
**Solution:**
```bash
sudo apt update
sudo apt install google-chrome-stable
```

#### 3. Telegram Errors
```
Error: Unauthorized
```
**Solution:**
- Verify your bot token is correct
- Ensure the bot has permission to send messages
- Check your chat ID is accurate

#### 4. Permission Errors
```
Error: Permission denied
```
**Solution:**
```bash
chmod +x *.py
sudo chown -R $USER:$USER .
```

### Debug Mode

For detailed debugging, modify the logging level in the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Service Debugging

If the service fails to start:
```bash
sudo journalctl -u nbtc-scraper --no-pager
```

## Performance Considerations

- **Rate Limiting:** The scraper includes delays between requests to be respectful to the server
- **Memory Usage:** SQLite database grows over time; consider periodic cleanup
- **CPU Usage:** Chrome browser instances can be resource-intensive
- **Network:** Adjust scraping intervals based on your connection and needs

## Security Notes

- Store sensitive tokens in `.env` file, not in the code
- The `.env` file is ignored by git to prevent accidental commits
- Consider using a dedicated Telegram bot for notifications
- Monitor logs for any unauthorized access attempts

## Legal Disclaimer

This tool is for educational and monitoring purposes only. Users are responsible for:
- Complying with the website's terms of service
- Respecting rate limits and server resources
- Using scraped data ethically and legally
- Following all applicable laws and regulations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. Please use responsibly and in accordance with applicable laws and the target website's terms of service.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs in `equipment_scraper.log`
3. Test individual components using the management script
4. Create an issue with detailed error information

---

**Happy Monitoring! 📱🔔**