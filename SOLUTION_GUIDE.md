# 🔧 NBTC Scraper Issue & Solutions

## 🚨 **The Problem**

The NBTC website (mocheck.nbtc.go.th) has **very strict Cloudflare protection** that:

- Returns HTTP 403 (Forbidden) to all requests
- Shows "Just a moment..." challenge page
- Requires JavaScript execution to solve challenges
- Blocks both simple requests and basic Selenium automation

## 📊 **Test Results**

```
Status Code: 403 (All endpoints)
Protection: Advanced Cloudflare with JavaScript challenges
Response: "Just a moment..." page
Success Rate: 0% with basic methods
```

## 🛠️ **Solution Options**

### **Option 1: Install Chrome & Enhanced Selenium** ⭐ **RECOMMENDED**

1. **Install Chrome Browser:**
   ```bash
   # Ubuntu/Debian
   wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
   echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
   sudo apt update
   sudo apt install google-chrome-stable
   
   # Or download directly
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
   sudo dpkg -i google-chrome-stable_current_amd64.deb
   sudo apt-get install -f
   ```

2. **Test Enhanced Scraper:**
   ```bash
   python3 improved_scraper.py
   ```

### **Option 2: Use Different Network/VPN** 🌐

The website might be geo-blocking or IP-blocking:

```bash
# Try with VPN or different IP
# Or use proxy settings in the scraper
```

### **Option 3: Manual Browser with Automation** 🖱️

1. **Open browser manually** to solve Cloudflare
2. **Get cookies** and session data
3. **Use them in the scraper**

### **Option 4: Alternative Data Sources** 📊

Look for alternative sources:
- Mobile app APIs
- Official NBTC APIs
- Mirror websites
- RSS feeds

### **Option 5: Scheduled Browser Sessions** ⏰

Set up automated browser sessions that:
1. Open browser at regular intervals
2. Solve Cloudflare manually once
3. Use the session for multiple requests

## 🔍 **Debugging Steps**

### Step 1: Test Chrome Installation
```bash
google-chrome --version
```

### Step 2: Test Basic Access
```bash
python3 debug_scraper.py
```

### Step 3: Check Generated Files
- `debug_*.html` - Raw responses
- `debug_page_structure.txt` - Analysis

### Step 4: Monitor Logs
```bash
tail -f equipment_scraper.log
```

## 🚀 **Quick Fix Implementation**

If you want immediate results, here's a working approach:

### **Manual Browser Method:**

1. **Open the website manually** in your browser
2. **Wait for Cloudflare to load** the real page
3. **Copy the HTML source** of the working page
4. **Save it as a file** for the scraper to parse

```python
# Use this with manual HTML
with open('manual_page_source.html', 'r') as f:
    html_content = f.read()
    
soup = BeautifulSoup(html_content, 'html.parser')
# Process the data
```

## 📱 **Alternative: Check for Mobile API**

Many websites have mobile APIs that are less protected:

```bash
curl -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)" \
     https://mocheck.nbtc.go.th/api/mobile/equipment
```

## 🔄 **Advanced Solutions**

### **Use Selenium Wire (Intercept Requests)**
```bash
pip install selenium-wire
```

### **Use Undetected Chrome Driver**
```bash
pip install undetected-chromedriver
```

### **Use Playwright Instead**
```bash
pip install playwright
playwright install chromium
```

## ⚡ **Immediate Working Solution**

Since the protection is very strict, here's what you can do **right now**:

1. **Manual Method:**
   - Open https://mocheck.nbtc.go.th/search-equipments in your browser
   - Wait for it to load completely
   - Right-click → View Page Source
   - Save as `working_page.html`
   - Run our parser on this file

2. **Scheduled Check:**
   - Set up the scraper to run at different times
   - Some protections are time-based
   - Try running at off-peak hours

3. **Use Mobile Browser:**
   - Open the site on mobile
   - Mobile versions often have less protection
   - Check if there's a mobile API

## 🎯 **Success Indicators**

You'll know it's working when:
- ✅ Status code changes from 403 to 200
- ✅ Page title is NOT "Just a moment..."
- ✅ You see actual equipment data
- ✅ Tables/forms are present in the HTML

## 📞 **Support Strategy**

If all technical solutions fail:
1. **Contact NBTC** for official API access
2. **Check NBTC documentation** for developer APIs
3. **Look for official data exports**
4. **Use NBTC mobile app** if available

## 🔧 **Next Steps**

1. **Install Chrome browser**
2. **Run the enhanced scraper**
3. **Check debug output**
4. **Try alternative methods if needed**

The scraper code is solid - the issue is purely the website's protection level!