#!/usr/bin/env python3
"""
IoTeX Price Alert Bot for Telegram

This bot monitors IoTeX (IOTX) price changes and sends alerts to a Telegram channel
every 5 minutes with current price information and percentage changes.

Author: David Nitty
"""

import requests
import time
import json
import logging
from datetime import datetime
from typing import Dict, Optional

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("iotx-bot")

class IoTeXPriceBot:
    def __init__(self, bot_token: str, channel_id: str):
        """
        Initialize the IoTeX Price Bot
        
        Args:
            bot_token (str): Telegram bot token from BotFather
            channel_id (str): Telegram channel ID where alerts will be sent
        """
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}"
        self.previous_price = None
        self.price_history = []
        
        # API endpoints for IoTeX price data
        self.coingecko_api = "https://api.coingecko.com/api/v3/simple/price"
        self.coinmarketcap_api = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        
    def get_iotex_price_coingecko(self ) -> Optional[Dict]:
        """
        Fetch IoTeX price data from CoinGecko API
        
        Returns:
            Dict containing price data or None if failed
        """
        try:
            params = {
                \\'ids\\': \\'iotex\\',
                \\'vs_currencies\\': \\'usd\\',
                \\'include_market_cap\\': \\'true\\',
                \\'include_24hr_vol\\': \\'true\\',
                \\'include_24hr_change\\': \\'true\\',
                \\'include_last_updated_at\\': \\'true\\'
            }
            
            response = requests.get(self.coingecko_api, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if \\'iotex\\': in data:
                iotex_data = data[\\'iotex\\']
                return {
                    \\'price\\': iotex_data.get(\\'usd\\', 0),
                    \\'market_cap\\': iotex_data.get(\\'usd_market_cap\\', 0),
                    \\'volume_24h\\': iotex_data.get(\\'usd_24h_vol\\', 0),
                    \\'change_24h\\': iotex_data.get(\\'usd_24h_change\\', 0),
                    \\'last_updated\\': iotex_data.get(\\'last_updated_at\\', 0),
                    \\'source\\': \\'CoinGecko\\'
                }
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching price from CoinGecko: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing CoinGecko response: {e}")
            return None
    
    def get_iotex_price_dia(self) -> Optional[Dict]:
        """
        Fetch IoTeX price data from DIA API as backup
        
        Returns:
            Dict containing price data or None if failed
        """
        try:
            dia_url = "https://api.diadata.org/v1/assetQuotation/Ethereum/0x6fB3e0A217407EFFf7Ca062D46c26E5d60a14d69"
            
            response = requests.get(dia_url, timeout=10 )
            response.raise_for_status()
            
            data = response.json()
            if \\'Price\\': in data:
                return {
                    \\'price\\': data.get(\\'Price\\', 0),
                    \\'market_cap\\': 0,  # DIA doesn\\':t provide market cap
                    \\'volume_24h\\': data.get(\\'VolumeYesterdayUSD\\', 0),
                    \\'change_24h\\': 0,  # Calculate manually if needed
                    \\'last_updated\\': int(time.time()),
                    \\'source\\': \\'DIA\\'
                }
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching price from DIA: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing DIA response: {e}")
            return None
    
    def get_current_price(self) -> Optional[Dict]:
        """
        Get current IoTeX price from available APIs with fallback
        
        Returns:
            Dict containing price data or None if all APIs fail
        """
        # Try CoinGecko first (more comprehensive data)
        price_data = self.get_iotex_price_coingecko()
        if price_data:
            return price_data
        
        # Fallback to DIA API
        logger.warning("CoinGecko API failed, trying DIA API")
        price_data = self.get_iotex_price_dia()
        if price_data:
            return price_data
        
        logger.error("All price APIs failed")
        return None
    
    def calculate_price_change(self, current_price: float) -> Dict:
        """
        Calculate price change since last check
        
        Args:
            current_price (float): Current price
            
        Returns:
            Dict containing change information
        """
        if self.previous_price is None:
            return {
                \\'change_amount\\': 0,
                \\'change_percentage\\': 0,
                \\'trend\\': \\'neutral\\'
            }
        
        change_amount = current_price - self.previous_price
        change_percentage = (change_amount / self.previous_price) * 100 if self.previous_price > 0 else 0
        
        if change_amount > 0:
            trend = \\'up\\'
        elif change_amount < 0:
            trend = \\'down\\'
        else:
            trend = \\'neutral\\'
        
        return {
            \\'change_amount\\': change_amount,
            \\'change_percentage\\': change_percentage,
            \\'trend\\': trend
        }
    
    def format_price_message(self, price_data: Dict, change_data: Dict) -> str:
        """
        Format the price alert message for Telegram
        
        Args:
            price_data (Dict): Current price data
            change_data (Dict): Price change data
            
        Returns:
            Formatted message string
        """
        current_price = price_data[\\'price\\']
        market_cap = price_data.get(\\'market_cap\\', 0)
        volume_24h = price_data.get(\\'volume_24h\\', 0)
        change_24h = price_data.get(\\'change_24h\\', 0)
        source = price_data.get(\\'source\\', \\'Unknown\\')
        
        # Trend emoji
        trend_emoji = {
            \\'up\\': \\'📈\\',
            \\'down\\': \\'📉\\',
            \\'neutral\\': \\'➡️\\'
        }
        
        # 24h change emoji
        change_24h_emoji = \\'🟢\\' if change_24h >= 0 else \\'🔴\\'
        
        # 5-minute change emoji
        change_5min_emoji = trend_emoji.get(change_data[\\'trend\\'], \\'➡️\\')
        
        message = f"""
${current_price:.6f}
        """.strip()
        
        return message
    
    def send_telegram_message(self, message: str) -> bool:
        """
        Send message to Telegram channel
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            url = f"{self.telegram_api_url}/sendMessage"
            payload = {
                \\'chat_id\\': self.channel_id,
                \\'text\\': message,
                \\'parse_mode\\': \\'Markdown\\',
                \\'disable_web_page_preview\\': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get(\\'ok\\'):
                logger.info("Message sent successfully to Telegram")
                return True
            else:
                logger.error(f"Telegram API error: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Telegram response: {e}")
            return False
    
    def run_price_check(self) -> bool:
        """
        Run a single price check and send alert if successful
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Checking IoTeX price...")
        
        # Get current price data
        price_data = self.get_current_price()
        if not price_data:
            logger.error("Failed to fetch price data")
            return False
        
        current_price = price_data[\\'price\\']
        logger.info(f"Current IoTeX price: ${current_price:.6f}")
        
        # Calculate price change
        change_data = self.calculate_price_change(current_price)
        
        # Format and send message
        message = self.format_price_message(price_data, change_data)
        success = self.send_telegram_message(message)
        
        if success:
            # Update price history
            self.previous_price = current_price
            self.price_history.append({
                \\'timestamp\\': datetime.now().isoformat(),
                \\'price\\': current_price,
                \\'source\\': price_data.get(\\'source\\', \\'Unknown\\')
            })
            
            # Keep only last 100 price points
            if len(self.price_history) > 100:
                self.price_history = self.price_history[-100:]
        
        return success
    
    def run_continuous(self, interval_minutes: int = 5):
        """
        Run the bot continuously with specified interval
        
        Args:
            interval_minutes (int): Interval between price checks in minutes
        """
        logger.info(f"Starting IoTeX Price Bot with {interval_minutes}-minute intervals")
        logger.info(f"Bot Token: {self.bot_token[:10]}...")
        logger.info(f"Channel ID: {self.channel_id}")
        
        interval_seconds = interval_minutes * 60
        
        while True:
            try:
                self.run_price_check()
                logger.info(f"Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.info("Continuing after error...")
                time.sleep(60)  # Wait 1 minute before retrying

def main():
    """
    Main function to run the bot
    """
    # Configuration - Replace with your actual values
    BOT_TOKEN = "7774279278:AAGyElsfJXHcJied7GTrzAGzmSAEDYnPy4Q"  # Replace with your bot token from BotFather
    CHANNEL_ID = "-1002633018195"  # Replace with your channel ID (e.g., -1001234567890)
    
    # ---- SINGLE-RUN ENTRYPOINT (for Railway Cron) ------------------------------
import os

def main():
    # Read secrets from environment (Railway → Variables)
    BOT_TOKEN  = os.environ["TG_TOKEN"]
    CHANNEL_ID = os.environ["TG_CHAT_ID"]

    # Create bot and send ONE price update, then exit
    bot = IoTeXPriceBot(BOT_TOKEN, CHANNEL_ID)

    try:
        ok = bot.run_price_check()   # <-- runs once and posts
        if not ok:
            logger.error("Price check failed; exiting with error.")
            raise SystemExit(1)
        logger.info("Price check sent successfully; exiting.")
    except Exception as e:
        logger.exception("Unhandled error while sending price update: %s", e)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
# ---------------------------------------------------------------------------

