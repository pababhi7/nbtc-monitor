const https = require('https');
const fs = require('fs');
const path = require('path');

// Configuration
const CSV_URL = 'https://hub.nbtc.go.th/download/certification.csv';
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;
const DATA_FILE = 'devices.json';

// Target categories for cellular devices
const TARGET_CATEGORIES = [
  'Cellular Mobile (GSM/WCDMA/LTE/NR)',
  'Cellular Mobile (GSM/WCDMA/LTE)',
  'Cellular Mobile (GSM/WCDMA)',
  'Cellular Mobile (GSM)',
  'Cellular Mobile'
];

// Load existing devices
function loadExistingDevices() {
  try {
    if (fs.existsSync(DATA_FILE)) {
      const data = fs.readFileSync(DATA_FILE, 'utf8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('Error loading existing devices:', error);
  }
  return [];
}

// Save devices to file
function saveDevices(devices) {
  try {
    fs.writeFileSync(DATA_FILE, JSON.stringify(devices, null, 2));
    console.log(`Saved ${devices.length} devices to file`);
  } catch (error) {
    console.error('Error saving devices:', error);
  }
}

// Fetch CSV data
function fetchCSVData() {
  return new Promise((resolve, reject) => {
    https.get(CSV_URL, (response) => {
      let data = '';
      
      response.on('data', (chunk) => {
        data += chunk;
      });
      
      response.on('end', () => {
        resolve(data);
      });
      
      response.on('error', (error) => {
        reject(error);
      });
    }).on('error', (error) => {
      reject(error);
    });
  });
}

// Parse CSV data
function parseCSV(csvData) {
  const lines = csvData.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.replace(/"/g, ''));
  
  const devices = [];
  
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.replace(/"/g, ''));
    
    if (values.length >= headers.length) {
      const device = {};
      headers.forEach((header, index) => {
        device[header] = values[index] || '';
      });
      
      // Filter for cellular devices
      if (TARGET_CATEGORIES.some(cat => device.device_type?.includes(cat))) {
        devices.push({
          id: device.cert_no || device.id,
          certificateNumber: device.cert_no,
          tradeName: device.trade_name,
          modelCode: device.model_code,
          deviceType: device.device_type,
          clientName: device.clntname,
          discoveredAt: new Date().toISOString()
        });
      }
    }
  }
  
  return devices;
}

// Send Telegram notification
function sendTelegramMessage(message) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      chat_id: TELEGRAM_CHAT_ID,
      text: message,
      parse_mode: 'HTML'
    });
    
    const options = {
      hostname: 'api.telegram.org',
      port: 443,
      path: `/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
      }
    };
    
    const req = https.request(options, (res) => {
      let response = '';
      
      res.on('data', (chunk) => {
        response += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve(JSON.parse(response));
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${response}`));
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    req.write(data);
    req.end();
  });
}

// Format notification message
function formatMessage(device) {
  return `🔔 <b>New NBTC Device Certified!</b>

📱 <b>Device:</b> ${device.tradeName}
🏷️ <b>Model:</b> ${device.modelCode}
📄 <b>Certificate:</b> ${device.certificateNumber}
🏢 <b>Company:</b> ${device.clientName}
📂 <b>Type:</b> ${device.deviceType}

⏰ <b>Discovered:</b> ${new Date(device.discoveredAt).toLocaleString('en-US', { 
  timeZone: 'Asia/Kolkata',
  dateStyle: 'medium',
  timeStyle: 'short'
})} IST`;
}

// Main monitoring function
async function monitorDevices() {
  try {
    console.log('🔍 Starting NBTC device monitoring...');
    
    // Load existing devices
    const existingDevices = loadExistingDevices();
    const existingIds = new Set(existingDevices.map(d => d.id));
    
    console.log(`📋 Found ${existingDevices.length} existing devices`);
    
    // Fetch latest data
    console.log('📥 Fetching latest certification data...');
    const csvData = await fetchCSVData();
    
    // Parse devices
    const currentDevices = parseCSV(csvData);
    console.log(`📊 Found ${currentDevices.length} cellular devices in database`);
    
    // Find new devices
    const newDevices = currentDevices.filter(device => !existingIds.has(device.id));
    
    if (newDevices.length > 0) {
      console.log(`🆕 Found ${newDevices.length} new devices!`);
      
      // Send notifications for new devices
      for (const device of newDevices) {
        try {
          const message = formatMessage(device);
          await sendTelegramMessage(message);
          console.log(`✅ Sent notification for: ${device.tradeName}`);
          
          // Small delay between messages
          await new Promise(resolve => setTimeout(resolve, 1000));
        } catch (error) {
          console.error(`❌ Failed to send notification for ${device.tradeName}:`, error);
        }
      }
      
      // Save updated device list
      saveDevices(currentDevices);
      
      // Send summary message
      const summaryMessage = `📊 <b>NBTC Monitoring Summary</b>

🆕 <b>New devices found:</b> ${newDevices.length}
📋 <b>Total devices tracked:</b> ${currentDevices.length}
⏰ <b>Last check:</b> ${new Date().toLocaleString('en-US', { 
  timeZone: 'Asia/Kolkata',
  dateStyle: 'medium',
  timeStyle: 'short'
})} IST`;
      
      await sendTelegramMessage(summaryMessage);
      
    } else {
      console.log('ℹ️ No new devices found');
      
      // Send status update (only for morning check)
      const now = new Date();
      const istHour = (now.getUTCHours() + 5) % 24 + (now.getUTCMinutes() >= 30 ? 1 : 0);
      
      if (istHour === 5) { // 5 AM IST check
        const statusMessage = `✅ <b>NBTC Monitor Status</b>

📊 <b>Total devices tracked:</b> ${currentDevices.length}
🔍 <b>Status:</b> Active monitoring
⏰ <b>Last check:</b> ${now.toLocaleString('en-US', { 
  timeZone: 'Asia/Kolkata',
  dateStyle: 'medium',
  timeStyle: 'short'
})} IST

No new devices found in this check.`;
        
        await sendTelegramMessage(statusMessage);
      }
    }
    
    console.log('✅ Monitoring completed successfully');
    
  } catch (error) {
    console.error('❌ Error during monitoring:', error);
    
    // Send error notification
    try {
      const errorMessage = `🚨 <b>NBTC Monitor Error</b>

❌ <b>Error:</b> ${error.message}
⏰ <b>Time:</b> ${new Date().toLocaleString('en-US', { 
  timeZone: 'Asia/Kolkata',
  dateStyle: 'medium',
  timeStyle: 'short'
})} IST

Please check the system logs for more details.`;
      
      await sendTelegramMessage(errorMessage);
    } catch (notificationError) {
      console.error('Failed to send error notification:', notificationError);
    }
    
    process.exit(1);
  }
}

// Run the monitor
monitorDevices();
