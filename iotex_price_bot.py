#!/usr/bin/env python3
"""
IoTeX Simple Price Alert Bot for Telegram

This bot monitors IoTeX (IOTX) price and sends simple price alerts to a Telegram channel
every 5 minutes - showing only the current price.

Author: David Nitty
"""

import requests
import time
import logging
import os
from datetime import datetime
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# CoinGecko API URL (no API key required!)
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

class IoTeXPriceBot:
    def __init__(self):
        self.last_price = None
        self.last_check_time = None
        
    def get_iotx_price(self) -> Optional[float]:
        """Fetch IoTeX price data from CoinGecko"""
        try:
            # CoinGecko parameters - only get price
            params = {
                'ids': 'iotex',
                'vs_currencies': 'usd'
            }
            
            response = requests.get(COINGECKO_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'iotex' in data and 'usd' in data['iotex']:
                return data['iotex']['usd']
            return None
            
        except requests.RequestException as e:
            logging.error(f"Error fetching price data: {e}")
            return None
        except KeyError as e:
            logging.error(f"Error parsing price data: {e}")
            return None

    def format_price_message(self, price: float) -> str:
        """Format price into a simple message - just the price"""
        # Format price with 6 decimal places for small values, 4 for larger
        if price < 1:
            price_str = f"${price:.6f}"
        else:
            price_str = f"${price:.4f}"
        
        # Simple message - just the price
        return price_str

    def send_telegram_message(self, message: str) -> bool:
        """Send message to Telegram channel"""
        try:
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message
            }
            
            response = requests.post(TELEGRAM_URL, json=payload, timeout=30)
            response.raise_for_status()
            
            logging.info("Message sent successfully to Telegram")
            return True
            
        except requests.RequestException as e:
            logging.error(f"Error sending Telegram message: {e}")
            return False

    def run_price_check(self):
        """Run a single price check and send alert"""
        logging.info("Checking IoTeX price from CoinGecko...")
        
        # Get price data
        price = self.get_iotx_price()
        if not price:
            logging.error("Failed to get price data from CoinGecko")
            return
        
        # Format simple message
        message = self.format_price_message(price)
        success = self.send_telegram_message(message)
        
        if success:
            self.last_price = price
            self.last_check_time = datetime.now()
            logging.info(f"Price alert sent successfully. Current price: ${price:.6f}")
        else:
            logging.error("Failed to send price alert")

    def run(self):
        """Main bot loop - runs continuously and checks every 5 minutes"""
        logging.info("🚀 IoTeX Simple Price Alert Bot Started!")
        logging.info("📊 Using CoinGecko API (free tier)")
        logging.info("⏰ Sending simple price alerts every 5 minutes...")
        
        # Send initial alert
        self.run_price_check()
        
        # Main loop - check every 5 minutes (300 seconds)
        while True:
            try:
                logging.info("⏳ Waiting 5 minutes until next check...")
                time.sleep(300)  # Wait 5 minutes
                self.run_price_check()
                
            except KeyboardInterrupt:
                logging.info("Bot stopped by user")
                break
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                logging.info("🔄 Retrying in 1 minute...")
                time.sleep(60)  # Wait 1 minute before retrying

def main():
    # Check if required environment variables are set
    required_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logging.error("Please set: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return
    
    logging.info("✅ Environment variables configured")
    logging.info("📡 CoinGecko API - No API key required!")
    
    # Create and run bot
    bot = IoTeXPriceBot()
    bot.run()

if __name__ == "__main__":
    main()
