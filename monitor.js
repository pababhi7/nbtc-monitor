const https = require('https');
const http = require('http');
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

// Fetch CSV data with retry logic and proper error handling
function fetchCSVData(retries = 3) {
  return new Promise((resolve, reject) => {
    console.log(`Attempting to fetch CSV data (${4 - retries}/3)...`);
    
    // Try alternative URL if original fails
    const urls = [
      'https://hub.nbtc.go.th/download/certification.csv',
      'https://mocheck.nbtc.go.th/download/certification.csv',
      'https://www.nbtc.go.th/download/certification.csv'
    ];
    
    const currentUrl = urls[Math.min(3 - retries, urls.length - 1)];
    const urlObj = new URL(currentUrl);
    
    const options = {
      hostname: urlObj.hostname,
      port: 443,
      path: urlObj.pathname,
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; NBTC-Monitor/1.0; +https://github.com/monitor)',
        'Accept': 'text/csv,application/csv,text/plain,*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'identity',
        'Connection': 'close',
        'Cache-Control': 'no-cache'
      },
      timeout: 90000,
      rejectUnauthorized: false,
      secureProtocol: 'TLSv1_2_method'
    };

    console.log(`Trying URL: ${currentUrl}`);
    
    const requestModule = urlObj.protocol === 'https:' ? https : http;
    
    const request = requestModule.request(options, (response) => {
      let data = '';
      
      console.log(`HTTP Status: ${response.statusCode}`);
      console.log(`Content-Type: ${response.headers['content-type']}`);
      
      response.on('data', (chunk) => {
        data += chunk;
      });
      
      response.on('end', () => {
        if (response.statusCode === 200) {
          console.log(`Successfully fetched ${data.length} bytes of CSV data`);
          if (data.length > 100 && (data.includes('cert_no') || data.includes('certificate') || data.includes('device'))) {
            resolve(data);
          } else {
            reject(new Error('Data appears to be invalid or empty'));
          }
        } else if (response.statusCode === 301 || response.statusCode === 302) {
          const redirectUrl = response.headers.location;
          console.log(`Redirecting to: ${redirectUrl}`);
          
          if (redirectUrl) {
            const redirectUrlObj = new URL(redirectUrl);
            const redirectModule = redirectUrlObj.protocol === 'https:' ? https : http;
            
            redirectModule.get(redirectUrl, (redirectResponse) => {
              let redirectData = '';
              redirectResponse.on('data', (chunk) => {
                redirectData += chunk;
              });
              redirectResponse.on('end', () => {
                if (redirectData.length > 100) {
                  resolve(redirectData);
                } else {
                  reject(new Error('Redirect data appears to be invalid'));
                }
              });
            }).on('error', reject);
          } else {
            reject(new Error('Redirect location not found'));
          }
        } else {
          reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
        }
      });
      
      response.on('error', (error) => {
        console.error('Response error:', error);
        reject(error);
      });
    });

    request.on('timeout', () => {
      console.error('Request timeout');
      request.destroy();
      reject(new Error('Request timeout after 90 seconds'));
    });

    request.on('error', (error) => {
      console.error('Request error:', error);
      if (retries > 0) {
        console.log(`Retrying with different URL... (${retries} attempts left)`);
        setTimeout(() => {
          fetchCSVData(retries - 1).then(resolve).catch(reject);
        }, 3000);
      } else {
        reject(error);
      }
    });

    request.setTimeout(90000, () => {
      console.error('Request timeout');
      request.destroy();
    });

    request.end();
  });
}

// Fallback fetch method using spawn process
async function fetchWithCurl() {
  const { spawn } = require('child_process');
  
  return new Promise((resolve, reject) => {
    const curl = spawn('curl', [
      '-s',
      '-L',
      '-k',
      '--max-time', '120',
      '--retry', '3',
      '--retry-delay', '2',
      '--user-agent', 'Mozilla/5.0 (compatible; NBTC-Monitor/1.0)',
      'https://hub.nbtc.go.th/download/certification.csv'
    ]);
    
    let data = '';
    let error = '';
    
    curl.stdout.on('data', (chunk) => {
      data += chunk;
    });
    
    curl.stderr.on('data', (chunk) => {
      error += chunk;
    });
    
    curl.on('close', (code) => {
      if (code === 0 && data.length > 100) {
        console.log(`Curl fetched ${data.length} bytes successfully`);
        resolve(data);
      } else {
        reject(new Error(`Curl failed with code ${code}: ${error}`));
      }
    });
    
    curl.on('error', (err) => {
      reject(new Error(`Curl spawn error: ${err.message}`));
    });
  });
}

// Parse CSV data with better error handling
function parseCSV(csvData) {
  try {
    console.log('Starting CSV parsing...');
    
    if (!csvData || csvData.length < 100) {
      throw new Error('CSV data appears to be empty or too small');
    }
    
    const lines = csvData.trim().split('\n');
    console.log(`Total lines in CSV: ${lines.length}`);
    
    if (lines.length < 2) {
      throw new Error('CSV data appears to be empty or invalid');
    }
    
    // Handle different CSV formats (comma, semicolon, tab-separated)
    const firstLine = lines[0];
    let separator = ',';
    if (firstLine.includes(';')) separator = ';';
    if (firstLine.includes('\t')) separator = '\t';
    
    console.log(`Using separator: '${separator}'`);
    
    const headers = lines[0].split(separator).map(h => h.replace(/"/g, '').trim());
    console.log(`Found ${headers.length} headers:`, headers.slice(0, 10));
    
    const devices = [];
    let processedCount = 0;
    
    for (let i = 1; i < lines.length; i++) {
      try {
        const values = lines[i].split(separator).map(v => v.replace(/"/g, '').trim());
        
        if (values.length >= 3) {
          const device = {};
          headers.forEach((header, index) => {
            device[header] = values[index] || '';
          });
          
          // More flexible device type detection
          const deviceType = device.device_type || device.DeviceType || device.type || 
                           device.category || device.Category || device.equipment_type || '';
          
          // Check if it's a cellular device
          const isCellular = deviceType && (
            TARGET_CATEGORIES.some(cat => deviceType.includes(cat)) ||
            deviceType.toLowerCase().includes('cellular') || 
            deviceType.toLowerCase().includes('mobile') ||
            deviceType.toLowerCase().includes('gsm') ||
            deviceType.toLowerCase().includes('lte') ||
            deviceType.toLowerCase().includes('wcdma') ||
            deviceType.toLowerCase().includes('umts') ||
            deviceType.toLowerCase().includes('5g') ||
            deviceType.toLowerCase().includes('nr')
          );
          
          if (isCellular) {
            const certNo = device.cert_no || device.CertNo || device.certificate_no || 
                          device.CertificateNo || device.id || '';
            const tradeName = device.trade_name || device.TradeName || device.name || 
                            device.product_name || device.ProductName || '';
            const modelCode = device.model_code || device.ModelCode || device.model || 
                            device.Model || device.model_name || '';
            const clientName = device.clntname || device.ClientName || device.company || 
                             device.Company || device.applicant || '';
            
            if (certNo && tradeName) {
              devices.push({
                id: certNo,
                certificateNumber: certNo,
                tradeName: tradeName,
                modelCode: modelCode,
                deviceType: deviceType,
                clientName: clientName,
                discoveredAt: new Date().toISOString()
              });
            }
          }
        }
        
        processedCount++;
        if (processedCount % 1000 === 0) {
          console.log(`Processed ${processedCount} lines...`);
        }
        
      } catch (lineError) {
        console.warn(`Error parsing line ${i}: ${lineError.message}`);
      }
    }
    
    console.log(`Successfully parsed ${devices.length} cellular devices from ${processedCount} total records`);
    return devices;
    
  } catch (error) {
    console.error('Error parsing CSV:', error);
    throw error;
  }
}

// Send Telegram notification with retry logic
function sendTelegramMessage(message, retries = 3) {
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
      },
      timeout: 30000
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
          const error = new Error(`HTTP ${res.statusCode}: ${response}`);
          if (retries > 0) {
            console.log(`Retrying Telegram message... (${retries} attempts left)`);
            setTimeout(() => {
              sendTelegramMessage(message, retries - 1).then(resolve).catch(reject);
            }, 2000);
          } else {
            reject(error);
          }
        }
      });
    });
    
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Telegram request timeout'));
    });
    
    req.on('error', (error) => {
      if (retries > 0) {
        console.log(`Retrying Telegram message... (${retries} attempts left)`);
        setTimeout(() => {
          sendTelegramMessage(message, retries - 1).then(resolve).catch(reject);
        }, 2000);
      } else {
        reject(error);
      }
    });
    
    req.write(data);
    req.end();
  });
}

// Format notification message
function formatMessage(device) {
  return `🔔 <b>New NBTC Device Certified!</b>

📱 <b>Device:</b> ${device.tradeName || 'Unknown'}
🏷️ <b>Model:</b> ${device.modelCode || 'Unknown'}
📄 <b>Certificate:</b> ${device.certificateNumber || 'Unknown'}
🏢 <b>Company:</b> ${device.clientName || 'Unknown'}
📂 <b>Type:</b> ${device.deviceType || 'Unknown'}

⏰ <b>Discovered:</b> ${new Date(device.discoveredAt).toLocaleString('en-US', { 
  timeZone: 'Asia/Kolkata',
  dateStyle: 'medium',
  timeStyle: 'short'
})} IST`;
}

// Check if this is first run (initialization)
function isFirstRun() {
  return !fs.existsSync(DATA_FILE);
}

// Main monitoring function
async function monitorDevices() {
  try {
    console.log('🔍 Starting NBTC device monitoring...');
    
    // Validate environment variables
    if (!TELEGRAM_BOT_TOKEN) {
      throw new Error('TELEGRAM_BOT_TOKEN environment variable is required');
    }
    if (!TELEGRAM_CHAT_ID) {
      throw new Error('TELEGRAM_CHAT_ID environment variable is required');
    }
    
    // Send startup notification
    const startupMessage = `🚀 <b>NBTC Monitor Started</b>

🔍 <b>Status:</b> Scraper initiated
⏰ <b>Time:</b> ${new Date().toLocaleString('en-US', { 
  timeZone: 'Asia/Kolkata',
  dateStyle: 'medium',
  timeStyle: 'short'
})} IST

Monitoring for new cellular device certifications...`;
    
    await sendTelegramMessage(startupMessage);
    console.log('✅ Startup notification sent');
    
    // Check if this is the first run
    const firstRun = isFirstRun();
    console.log(`First run: ${firstRun}`);
    
    // Load existing devices
    const existingDevices = loadExistingDevices();
    const existingIds = new Set(existingDevices.map(d => d.id));
    
    console.log(`📋 Found ${existingDevices.length} existing devices`);
    
    // Fetch latest data
    console.log('📥 Fetching latest certification data...');
    let csvData;
    
    try {
      csvData = await fetchCSVData();
    } catch (error) {
      console.error('Primary fetch failed, trying alternative method:', error.message);
      
      // Fallback: Try with curl-like approach
      try {
        csvData = await fetchWithCurl();
      } catch (curlError) {
        console.error('Curl fallback also failed:', curlError.message);
        throw new Error(`All fetch methods failed. Original: ${error.message}, Curl: ${curlError.message}`);
      }
    }
    
    // Parse devices
    const currentDevices = parseCSV(csvData);
    console.log(`📊 Found ${currentDevices.length} cellular devices in database`);
    
    if (firstRun) {
      // First run: Save all current devices as baseline, no notifications
      saveDevices(currentDevices);
      
      const initMessage = `📝 <b>NBTC Monitor Initialized</b>

📊 <b>Baseline set:</b> ${currentDevices.length} devices
🔔 <b>Notifications:</b> Will start from next run onwards
⏰ <b>Next check:</b> Monitoring active for new devices

System is now ready to detect new certifications!`;
      
      await sendTelegramMessage(initMessage);
      console.log('✅ Initial baseline set. Future runs will detect new devices.');
      
    } else {
      // Regular run: Check for new devices
      const newDevices = currentDevices.filter(device => !existingIds.has(device.id));
      
      if (newDevices.length > 0) {
        console.log(`🆕 Found ${newDevices.length} new devices!`);
        
        // Send notifications for new devices only
        for (const device of newDevices) {
          try {
            const message = formatMessage(device);
            await sendTelegramMessage(message);
            console.log(`✅ Sent notification for: ${device.tradeName}`);
            
            // Small delay between messages
            await new Promise(resolve => setTimeout(resolve, 2000));
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
})} IST

✅ All notifications sent successfully!`;
        
        await sendTelegramMessage(summaryMessage);
        
      } else {
        console.log('ℹ️ No new devices found');
        
        // Send status update (only for morning check)
        const now = new Date();
        const istTime = new Date(now.getTime() + (5.5 * 60 * 60 * 1000)); // Convert to IST
        const istHour = istTime.getHours();
        
        if (istHour === 5 || istHour === 6) { // 5 AM or 6 AM IST check
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
