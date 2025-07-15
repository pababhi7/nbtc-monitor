#!/usr/bin/env python3
"""
Management script for NBTC Equipment Scraper
Provides utilities for viewing data, testing notifications, and managing the scraper
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import List

from dotenv import load_dotenv
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
import pandas as pd
from telegram import Bot

# Import our classes
from nbtc_equipment_scraper import Equipment, Base, NBTCEquipmentScraper

load_dotenv()

class ScraperManager:
    def __init__(self):
        db_url = os.getenv('DATABASE_URL', 'sqlite:///equipment_tracker.db')
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Telegram bot
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if self.telegram_token:
            self.bot = Bot(token=self.telegram_token)
        else:
            self.bot = None
    
    def list_equipment(self, limit: int = 20, category_filter: str = None):
        """List equipment from database"""
        query = self.session.query(Equipment).order_by(desc(Equipment.first_seen))
        
        if category_filter:
            query = query.filter(Equipment.subcategory.contains(category_filter))
        
        equipment_list = query.limit(limit).all()
        
        if not equipment_list:
            print("No equipment found in database")
            return
        
        print(f"\n📱 Found {len(equipment_list)} equipment entries:")
        print("=" * 80)
        
        for eq in equipment_list:
            print(f"ID: {eq.equipment_id}")
            print(f"Name: {eq.name or 'N/A'}")
            print(f"Brand: {eq.brand or 'N/A'}")
            print(f"Company: {eq.company or 'N/A'}")
            print(f"Category: {eq.subcategory or 'N/A'}")
            print(f"First Seen: {eq.first_seen}")
            print(f"Notified: {'✅' if eq.notified else '❌'}")
            print(f"URL: {eq.url}")
            print("-" * 80)
    
    def export_to_csv(self, filename: str = None):
        """Export equipment data to CSV"""
        if not filename:
            filename = f"equipment_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        equipment_list = self.session.query(Equipment).all()
        
        if not equipment_list:
            print("No equipment found to export")
            return
        
        # Convert to pandas DataFrame
        data = []
        for eq in equipment_list:
            data.append({
                'equipment_id': eq.equipment_id,
                'name': eq.name,
                'brand': eq.brand,
                'model': eq.model,
                'category': eq.category,
                'subcategory': eq.subcategory,
                'company': eq.company,
                'certification_number': eq.certification_number,
                'certification_date': eq.certification_date,
                'expiry_date': eq.expiry_date,
                'url': eq.url,
                'first_seen': eq.first_seen,
                'notified': eq.notified
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"✅ Exported {len(data)} equipment entries to {filename}")
    
    def stats(self):
        """Show database statistics"""
        total = self.session.query(Equipment).count()
        notified = self.session.query(Equipment).filter_by(notified=True).count()
        cellular = self.session.query(Equipment).filter(
            Equipment.subcategory.contains('Cellular Mobile')
        ).count()
        
        # Recent entries (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent = self.session.query(Equipment).filter(
            Equipment.first_seen >= yesterday
        ).count()
        
        # Weekly entries
        week_ago = datetime.now() - timedelta(days=7)
        weekly = self.session.query(Equipment).filter(
            Equipment.first_seen >= week_ago
        ).count()
        
        print(f"\n📊 Database Statistics:")
        print("=" * 30)
        print(f"Total Equipment: {total}")
        print(f"Cellular Mobile: {cellular}")
        print(f"Notifications Sent: {notified}")
        print(f"Added Last 24h: {recent}")
        print(f"Added Last Week: {weekly}")
        print("=" * 30)
    
    async def test_telegram(self):
        """Test Telegram notification"""
        if not self.bot or not self.telegram_chat_id:
            print("❌ Telegram not configured")
            return
        
        try:
            message = f"""🧪 *Test Notification*

This is a test message from the NBTC Equipment Scraper.

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Status:* ✅ Working correctly"""

            await self.bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            print("✅ Test notification sent successfully")
            
        except Exception as e:
            print(f"❌ Error sending test notification: {e}")
    
    def resend_notifications(self, equipment_id: str = None):
        """Resend notifications for equipment"""
        if equipment_id:
            equipment_list = self.session.query(Equipment).filter_by(equipment_id=equipment_id).all()
        else:
            # Resend for unnotified equipment
            equipment_list = self.session.query(Equipment).filter_by(notified=False).all()
        
        if not equipment_list:
            print("No equipment found for notification")
            return
        
        print(f"Found {len(equipment_list)} equipment for notification")
        
        async def send_notifications():
            scraper = NBTCEquipmentScraper()
            for equipment in equipment_list:
                await scraper.send_telegram_notification(equipment)
                print(f"Sent notification for {equipment.equipment_id}")
        
        asyncio.run(send_notifications())
    
    def reset_notifications(self):
        """Reset notification status for all equipment"""
        count = self.session.query(Equipment).update({'notified': False})
        self.session.commit()
        print(f"✅ Reset notification status for {count} equipment entries")
    
    def delete_equipment(self, equipment_id: str):
        """Delete specific equipment from database"""
        equipment = self.session.query(Equipment).filter_by(equipment_id=equipment_id).first()
        
        if not equipment:
            print(f"Equipment {equipment_id} not found")
            return
        
        self.session.delete(equipment)
        self.session.commit()
        print(f"✅ Deleted equipment {equipment_id}")
    
    def run_single_scrape(self):
        """Run a single scrape cycle"""
        print("Running single scrape cycle...")
        scraper = NBTCEquipmentScraper()
        asyncio.run(scraper.run_scrape_cycle())

def main():
    parser = argparse.ArgumentParser(description='NBTC Equipment Scraper Management')
    parser.add_argument('command', choices=[
        'list', 'export', 'stats', 'test-telegram', 'resend', 'reset-notifications',
        'delete', 'run-once'
    ], help='Command to execute')
    
    parser.add_argument('--limit', type=int, default=20, help='Limit for list command')
    parser.add_argument('--filter', type=str, help='Category filter for list command')
    parser.add_argument('--filename', type=str, help='Filename for export command')
    parser.add_argument('--equipment-id', type=str, help='Equipment ID for specific operations')
    
    args = parser.parse_args()
    
    manager = ScraperManager()
    
    if args.command == 'list':
        manager.list_equipment(limit=args.limit, category_filter=args.filter)
    
    elif args.command == 'export':
        manager.export_to_csv(filename=args.filename)
    
    elif args.command == 'stats':
        manager.stats()
    
    elif args.command == 'test-telegram':
        asyncio.run(manager.test_telegram())
    
    elif args.command == 'resend':
        manager.resend_notifications(equipment_id=args.equipment_id)
    
    elif args.command == 'reset-notifications':
        confirm = input("Reset all notification statuses? (y/N): ")
        if confirm.lower() == 'y':
            manager.reset_notifications()
    
    elif args.command == 'delete':
        if not args.equipment_id:
            print("Equipment ID required for delete command")
            return
        confirm = input(f"Delete equipment {args.equipment_id}? (y/N): ")
        if confirm.lower() == 'y':
            manager.delete_equipment(args.equipment_id)
    
    elif args.command == 'run-once':
        manager.run_single_scrape()

if __name__ == "__main__":
    main()