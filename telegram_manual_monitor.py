#!/usr/bin/env python3
"""
Telegram Manual Monitor for NBTC Equipment
Sends regular reminders to manually check the NBTC website
"""

import asyncio
import schedule
import time
from datetime import datetime
from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

class TelegramManualMonitor:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            print("❌ Missing Telegram credentials!")
            print("Please update .env file with:")
            print("TELEGRAM_BOT_TOKEN=your_bot_token")
            print("TELEGRAM_CHAT_ID=your_chat_id")
            return
        
        self.bot = Bot(token=self.bot_token)
    
    async def send_check_reminder(self):
        """Send reminder to manually check NBTC website"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            message = f"""🔔 **NBTC Equipment Check Reminder**
📅 Time: {current_time}

🌐 **Website to Check:**
https://mocheck.nbtc.go.th/search-equipments/1624970

🔍 **Look for:**
• ประเภทย่อยเครื่องโทรคมนาคม
• **Cellular Mobile (GSM/WCDMA/LTE/NR)**
• New devices in this category

📱 **Search Terms:**
• "cellular mobile"
• "GSM"
• "WCDMA" 
• "LTE"
• "NR"
• "5G"
• "เครื่องโทรศัพท์มือถือ"

✅ **If you find new devices:**
Reply with device details to this chat

⏰ **Next reminder:** In 2 hours"""

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            print(f"✅ Reminder sent at {current_time}")
            
        except Exception as e:
            print(f"❌ Error sending reminder: {e}")
    
    def send_reminder_sync(self):
        """Synchronous wrapper for async function"""
        try:
            asyncio.run(self.send_check_reminder())
        except Exception as e:
            print(f"❌ Error in sync wrapper: {e}")
    
    async def test_notification(self):
        """Test the notification system"""
        try:
            test_message = """🧪 **NBTC Monitor Test**

✅ Telegram bot is working!
🔗 Connected to NBTC monitoring system
⏰ Regular reminders will be sent every 2 hours

Ready to monitor for:
📱 Cellular Mobile (GSM/WCDMA/LTE/NR) equipment"""

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=test_message,
                parse_mode='Markdown'
            )
            
            print("✅ Test notification sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Test notification failed: {e}")
            return False
    
    def setup_schedule(self):
        """Setup the monitoring schedule"""
        # Send reminder every 2 hours
        schedule.every(2).hours.do(self.send_reminder_sync)
        
        # Additional reminders at specific times (Thai timezone)
        schedule.every().day.at("09:00").do(self.send_reminder_sync)  # Morning
        schedule.every().day.at("14:00").do(self.send_reminder_sync)  # Afternoon  
        schedule.every().day.at("18:00").do(self.send_reminder_sync)  # Evening
        
        print("📅 Schedule configured:")
        print("   • Every 2 hours")
        print("   • Daily at 09:00, 14:00, 18:00 (Thai time)")
    
    def run_monitor(self):
        """Run the monitoring system"""
        if not self.bot_token or not self.chat_id:
            return
        
        print("🚀 Starting NBTC Manual Monitor...")
        print("=" * 50)
        
        # Test notification first
        test_result = asyncio.run(self.test_notification())
        if not test_result:
            print("❌ Cannot send test notification. Check your credentials.")
            return
        
        # Setup schedule
        self.setup_schedule()
        
        # Send initial reminder
        print("📤 Sending initial reminder...")
        self.send_reminder_sync()
        
        print("\n✅ Monitor is running!")
        print("Press Ctrl+C to stop...")
        
        # Run the scheduler
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\n⏹️ Monitor stopped by user")

def main():
    """Main function"""
    print("📱 NBTC Telegram Manual Monitor")
    print("=" * 40)
    
    monitor = TelegramManualMonitor()
    
    # Check if we want to just test or run the monitor
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🧪 Testing notification...")
        result = asyncio.run(monitor.test_notification())
        if result:
            print("✅ Test successful! Your Telegram bot is configured correctly.")
        else:
            print("❌ Test failed! Check your .env configuration.")
    else:
        monitor.run_monitor()

if __name__ == "__main__":
    main()