const https = require('https');
const fs = require('fs');
const { spawn } = require('child_process');

// Configuration
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;
const DATA_FILE = 'devices.json';

// Target categories for cellular devices
const TARGET_CATEGORIES = [
  'cellular mobile',
  'gsm',
  'wcdma',
  'lte',
  'nr',
  '5g',
  'umts',
  'mobile phone',
  'smartphone'
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

// Fetch CSV data using curl command
function fetchCSVData() {
  return new Promise((resolve, reject) => {
    console.log('Fetching CSV data using curl...');
    
    const curl = spawn('curl', [
      '-s',
      '-L',
      '-k',
      '--max-time', '180',
      '--retry', '5',
      '--retry-delay', '3',
      '--connect-timeout', '30',
      '--user-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
      '--header', 'Accept: text/csv,application/csv,text/plain,*/*',
      '--header', 'Accept-Language: en-US,en;q=0.9',
      '--header', 'Cache-Control: no-cache',
      'https://hub.nbtc.go.th/download/certification.csv'
    ]);
    
    let data = '';
    let errorData = '';
    
    curl.stdout.on('data', (chunk) => {
      data += chunk;
    });
    
    curl.stderr.on('data', (chunk) => {
      errorData += chunk;
    });
    
    curl.on('close', (code) => {
      if (code === 0) {
        if (data.length > 500) {
          console.log(`Successfully fetched ${data.length} bytes of CSV data`);
          resolve(data);
        } else {
          console.error('Data too small:', data.substring(0, 200));
          reject(new Error('Fetched data appears to be too small or empty'));
        }
      } else {
        console.error('Curl error:', errorData);
        reject(new Error(`Curl failed with exit code ${code}: ${errorData}`));
      }
    });
    
    curl.on('error', (error) => {
      console.error('Curl spawn error:', error);
      reject(new Error(`Failed to spawn curl: ${error.message}`));
    });
  });
}

// Parse CSV data
function parseCSV(csvData) {
  try {
    console.log('Parsing CSV data...');
    
    const lines = csvData.trim().split('\n');
    console.log(`Total lines: ${lines.length}`);
    
    if (lines.length < 2) {
      throw new Error('CSV data appears to be empty or invalid');
    }
    
    // Detect separator
    const firstLine = lines[0];
    let separator = ',';
    if (firstLine.split(',').length < firstLine.split(';').length) {
      separator = ';';
    }
    if (firstLine.split(separator).length < firstLine.split('\t').length) {
      separator = '\t';
    }
    
    console.log(`Using separator: '${separator}'`);
    
    const headers = lines[0].split(separator).map(h => h.replace(/"/g, '').trim().toLowerCase());
    console.log(`Headers found: ${headers.slice(0, 5).join(', ')}...`);
    
    const devices = [];
    
    for (let i = 1; i < lines.length; i++) {
      try {
        const values = lines[i].split(separator).map(v => v.replace(/"/g, '').trim());
        
        if (values.length >= 3) {
          const device = {};
          headers.forEach((header, index) => {
            device[header] = values[index] || '';
          });
          
          // Find device type field
          const deviceType = device.device_type || device.devicetype || device.type || 
                           device.category || device.equipment_type || device.equipmenttype || '';
          
          // Check if it's a cellular device
          const isCellular = TARGET_CATEGORIES.some(keyword => 
            deviceType.toLowerCase().includes(keyword)
          );
          
          if (isCellular) {
            // Find certificate number
            const certNo = device.cert_no || device.certno || device.certificate_no || 
                          device.certificateno || device.id || device.certificate || '';
            
            // Find product name
            const tradeName = device.trade_name || device.tradename || device.name || 
                            device.product_name || device.productname || device.product || '';
            
            // Find model
            const modelCode = device.model_code || device.modelcode || device.model || 
                            device.model_name || device.modelname || '';
            
            // Find company
            const clientName = device.clntname || device.clientname || device.company || 
                             device.manufacturer || device.applicant || '';
            
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
      } catch (lineError) {
        // Skip problematic lines
        continue;
      }
    }
    
    console.log(`Found ${devices.length} cellular devices`);
    return devices;
    
  } catch (error) {
    console.error('Error parsing CSV:', error);
    throw error;
  }
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
      res.on('data', (chunk) => response += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve(JSON.parse(response));
        } else {
          reject(new Error(`Telegram API error: ${res.statusCode} ${response}`));
        }
      });
    });
    
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// Format notification message
function formatMessage(device) {
  return `🔔 <b>New NBTC Device Certified!</b>

📱 <b>Device:</b> ${device.tradeName}
🏷️ <b>Model:</b> ${device.modelCode || 'N/A'}
📄 <b>Certificate:</b> ${device.certificateNumber}
🏢 <b>Company:</b> ${device.clientName || 'N/A'}
📂 <b>Type:</b> ${device.deviceType}

⏰ <b>Time:</b> ${new Date().toLocaleString('en-US', { 
  timeZone: 'Asia/Kolkata',
  dateStyle: 'medium',
  timeStyle: 'short'
})} IST`;
}

// Check if this is first run
function isFirstRun() {
  return !fs.existsSync(DATA_FILE);
}

// Main monitoring function
async function monitorDevices() {
  try {
    console.log('🔍 Starting NBTC device monitoring...');
    
    // Validate environment variables
    if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) {
      throw new Error('Missing required environment variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID');
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
    
    // Check first run
    const firstRun = isFirstRun();
    console.log(`First run: ${firstRun}`);
    
    // Load existing devices
    const existingDevices = loadExistingDevices();
    const existingIds = new Set(existingDevices.map(d => d.id));
    console.log(`Found ${existingDevices.length} existing devices`);
    
    // Fetch and parse data
    const csvData = await fetchCSVData();
    const currentDevices = parseCSV(csvData);
    
    if (firstRun) {
      // First run: Set baseline
      saveDevices(currentDevices);
      
      const initMessage = `📝 <b>NBTC Monitor Initialized</b>

📊 <b>Baseline set:</b> ${currentDevices.length} devices
🔔 <b>Notifications:</b> Will start from next run
⏰ <b>Next check:</b> Monitoring active

System ready to detect new certifications!`;
      
      await sendTelegramMessage(initMessage);
      console.log('✅ Baseline set successfully');
      
    } else {
      // Regular run: Check for new devices
      const newDevices = currentDevices.filter(device => !existingIds.has(device.id));
      
      if (newDevices.length > 0) {
        console.log(`🆕 Found ${newDevices.length} new devices!`);
        
        // Send notifications for new devices
        for (const device of newDevices) {
          try {
            const message = formatMessage(device);
            await sendTelegramMessage(message);
            console.log(`✅ Notified: ${device.tradeName}`);
            
            // Delay between messages
            await new Promise(resolve => setTimeout(resolve, 1000));
          } catch (error) {
            console.error(`❌ Failed to notify ${device.tradeName}:`, error.message);
          }
        }
        
        // Update device list
        saveDevices(currentDevices);
        
        // Send summary
        const summaryMessage = `📊 <b>NBTC Monitoring Summary</b>

🆕 <b>New devices:</b> ${newDevices.length}
📋 <b>Total tracked:</b> ${currentDevices.length}
⏰ <b>Last check:</b> ${new Date().toLocaleString('en-US', { 
  timeZone: 'Asia/Kolkata',
  dateStyle: 'medium',
  timeStyle: 'short'
})} IST

✅ All notifications sent!`;
        
        await sendTelegramMessage(summaryMessage);
        
      } else {
        console.log('ℹ️ No new devices found');
        
        // Send status update for morning checks
        const now = new Date();
        const istTime = new Date(now.getTime() + (5.5 * 60 * 60 * 1000));
        const istHour = istTime.getHours();
        
        if (istHour === 5 || istHour === 6) {
          const statusMessage = `✅ <b>NBTC Monitor Status</b>

📊 <b>Devices tracked:</b> ${currentDevices.length}
🔍 <b>Status:</b> Active monitoring
⏰ <b>Check time:</b> ${now.toLocaleString('en-US', { 
  timeZone: 'Asia/Kolkata',
  dateStyle: 'medium',
  timeStyle: 'short'
})} IST

No new devices found.`;
          
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
})} IST`;
      
      await sendTelegramMessage(errorMessage);
    } catch (notificationError) {
      console.error('Failed to send error notification:', notificationError);
    }
    
    process.exit(1);
  }
}

// Run the monitor
monitorDevices();
