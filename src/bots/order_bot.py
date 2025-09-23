"""
HyperLiquid Order Copy Bot

Monitors and copies orders from a target account with proportional sizing
based on account values and leverage settings.
"""

import asyncio
import os
import datetime
from typing import Dict, List, Optional, Tuple
import logging
from hyperliquid.info import Info
import requests
import eth_account
from eth_account.signers.local import LocalAccount
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrderBot:
    """
    HyperLiquid Order Copy Bot
    
    This bot monitors and copies orders from a target account, maintaining
    proportional position sizes based on account values and leverage settings.
    """
    
    def __init__(self):
        """Initialize the OrderBot with environment configuration."""
        self.should_run = True
        load_dotenv()
        
        # Initialize HyperLiquid API
        self._init_hyperliquid()
        
        # Load configuration
        self._load_config()
        
        # Initialize metadata
        self._init_metadata()
        
    def _init_hyperliquid(self) -> None:
        """Initialize HyperLiquid API components."""
        try:
            private_key = os.getenv("PRIVATE_KEY_API")
            if not private_key:
                raise ValueError("PRIVATE_KEY_API not found in environment")
                
            self.account: LocalAccount = eth_account.Account.from_key(private_key)
            self.exchange = Exchange(self.account, constants.MAINNET_API_URL)
            self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
            
            logger.info("HyperLiquid API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize HyperLiquid API: {e}")
            raise
            
    def _load_config(self) -> None:
        """Load configuration from environment variables."""
        self.ACCOUNT_TO_COPY = os.getenv("ACCOUNT_TO_COPY")
        self.TRADING_ADDRESS = os.getenv("TRADING_ADDRESS")
        self.LEVERAGE = float(os.getenv("LEVERAGE", "1"))
        self.TRADE_LIMIT = float(os.getenv("TRADE_LIMIT", "10"))
        self.MINI_ALLOC_OF_PF = float(os.getenv("MINI_ALLOC_OF_PF", "0"))
        
        if not all([self.ACCOUNT_TO_COPY, self.TRADING_ADDRESS]):
            raise ValueError("Missing required environment variables")
            
        logger.info(f"Configuration loaded - Copying from: {self.ACCOUNT_TO_COPY}")
        
    def _init_metadata(self) -> None:
        """Initialize exchange metadata and size decimals mapping."""
        try:
            meta = self.info.meta()
            self.sz_decimals = {}
            
            for asset_info in meta["universe"]:
                self.sz_decimals[asset_info["name"]] = asset_info["szDecimals"]
                
            logger.info(f"Loaded metadata for {len(self.sz_decimals)} assets")
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            raise

    async def get_account_value(self, address: str) -> float:
        """
        Get account value for a given address.
        
        Args:
            address: The wallet address to query
            
        Returns:
            Account value in USD
        """
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    'https://api.hyperliquid.xyz/info',
                    json={"type": "clearinghouseState", "user": address},
                    timeout=10
                )
            )
            data = response.json()
            return float(data['crossMarginSummary']['accountValue'])
        except Exception as e:
            logger.error(f"Error fetching account value for {address}: {e}")
            return 0

    async def get_open_orders(self, address: str) -> List[Dict]:
        """
        Get open orders for a given address.
        
        Args:
            address: The wallet address to query
            
        Returns:
            List of open orders
        """
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    'https://api.hyperliquid.xyz/info',
                    json={"type": "openOrders", "user": address},
                    timeout=10
                )
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching open orders for {address}: {e}")
            return []

    async def cancel_order(self, coin: str, oid: str) -> bool:
        """
        Cancel a specific order.
        
        Args:
            coin: The trading pair
            oid: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cancel_result = self.exchange.cancel(coin, oid)
            if cancel_result["status"] == "ok":
                return True
            logger.warning(f"Failed to cancel order {oid}: {cancel_result}")
            return False
        except Exception as e:
            logger.error(f"Error cancelling order {oid}: {e}")
            return False

    async def place_limit_order(
        self, 
        coin: str, 
        is_buy: bool, 
        size: float, 
        price: float, 
        reduce_only: bool = False
    ) -> bool:
        """
        Place a limit order.
        
        Args:
            coin: The trading pair
            is_buy: True for buy order, False for sell
            size: Order size
            price: Limit price
            reduce_only: Whether this is a reduce-only order
            
        Returns:
            True if successful, False otherwise
        """
        try:
            order_result = self.exchange.order(
                coin,
                is_buy,
                size,
                price,
                {"limit": {"tif": "Gtc"}},
                reduce_only=reduce_only
            )
            
            if order_result["status"] == "ok":
                status = order_result["response"]["data"]["statuses"][0]
                if "error" in status:
                    logger.error(f"Order error: {status['error']}")
                    return False
                return True
                
            logger.error(f"Error placing limit order: {order_result}")
            return False
        except Exception as e:
            logger.error(f"Exception in place_limit_order: {e}")
            return False

    def print_order_summary(self, orders: List[Dict], title: str) -> None:
        """
        Print a summary of orders.
        
        Args:
            orders: List of order dictionaries
            title: Title for the summary
        """
        if not orders:
            logger.info(f"{title}: No active orders")
            return
            
        logger.info(f"\n{title}:")
        order_summary = {}
        total_value = 0
        
        for order in orders:
            coin = order['coin']
            if coin not in order_summary:
                order_summary[coin] = []
                
            order_value = float(order['sz']) * float(order['limitPx'])
            total_value += abs(order_value)
            
            order_summary[coin].append({
                'side': 'Buy' if order['side'] == 'B' else 'Sell',
                'price': float(order['limitPx']),
                'size': float(order['sz']),
                'value': order_value,
                'reduceOnly': order.get('reduceOnly', False)
            })
            
        for coin, coin_orders in order_summary.items():
            logger.info(f"  {coin}:")
            for order in coin_orders:
                logger.info(f"    {order['side']} {order['size']:.4f} @ ${order['price']:.2f}")

    async def check_and_copy_orders(self) -> None:
        """Main order copying logic."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Checking orders at {timestamp}")
            
            # Get account values
            copy_trade_account_value = await self.get_account_value(self.ACCOUNT_TO_COPY)
            my_account_value = (await self.get_account_value(self.TRADING_ADDRESS)) * self.LEVERAGE
            
            if copy_trade_account_value == 0 or my_account_value == 0:
                logger.warning("Failed to get account values, skipping iteration")
                return
            
            logger.info(f"Copy account value: ${copy_trade_account_value:,.2f}")
            logger.info(f"My account value (with {self.LEVERAGE}x leverage): ${my_account_value:,.2f}")
            
            # Get orders
            copy_trade_orders = await self.get_open_orders(self.ACCOUNT_TO_COPY)
            my_orders = await self.get_open_orders(self.TRADING_ADDRESS)
            
            self.print_order_summary(copy_trade_orders, "Copy Trade Account Orders")
            self.print_order_summary(my_orders, "My Open Orders")
            
            # Process order synchronization
            await self._sync_orders(
                copy_trade_orders, 
                my_orders, 
                copy_trade_account_value, 
                my_account_value
            )
            
        except asyncio.CancelledError:
            logger.info("Order check cancelled, shutting down gracefully...")
            self.should_run = False
        except Exception as e:
            logger.error(f"Error in check_and_copy_orders: {e}")

    async def _sync_orders(
        self, 
        copy_orders: List[Dict], 
        my_orders: List[Dict],
        copy_account_value: float,
        my_account_value: float
    ) -> None:
        """
        Synchronize orders between copy account and my account.
        
        Args:
            copy_orders: Orders from the account being copied
            my_orders: My current orders
            copy_account_value: Value of the copy account
            my_account_value: Value of my account (with leverage)
        """
        # Create order maps for efficient lookup
        my_order_map = {}
        copy_trade_map = {}
        
        for order in my_orders:
            key = f"{order['coin']}-{order['side']}-{order['limitPx']}"
            my_order_map[key] = order
            
        for order in copy_orders:
            key = f"{order['coin']}-{order['side']}-{order['limitPx']}"
            copy_trade_map[key] = order

        # Cancel unmatched orders
        cancelled_orders = 0
        for my_order in my_orders:
            key = f"{my_order['coin']}-{my_order['side']}-{my_order['limitPx']}"
            if key not in copy_trade_map:
                if await self.cancel_order(my_order['coin'], my_order['oid']):
                    cancelled_orders += 1
                    my_order_map.pop(key, None)

        # Process copy trade orders
        processed_orders = 0
        for order in copy_orders:
            try:
                key = f"{order['coin']}-{order['side']}-{order['limitPx']}"
                existing_order = my_order_map.get(key)
                
                # Calculate scaled size
                order_size = float(order['sz'])
                scaled_size = (order_size * my_account_value) / copy_account_value
                scaled_size = round(scaled_size, self.sz_decimals[order['coin']])
                
                if scaled_size == 0:
                    min_size = 1 / (10 ** self.sz_decimals[order['coin']])
                    scaled_size = min_size
                    
                reduce_only = order.get('reduceOnly', False)

                if not existing_order:
                    # Place new order
                    success = await self.place_limit_order(
                        order['coin'],
                        order['side'] == 'B',
                        scaled_size,
                        float(order['limitPx']),
                        reduce_only=reduce_only
                    )
                    if success:
                        processed_orders += 1
                else:
                    # Update existing order if size differs significantly
                    current_size = float(existing_order['sz'])
                    size_diff = abs(current_size - scaled_size)
                    
                    if size_diff / current_size > 0.01:  # 1% threshold
                        if await self.cancel_order(existing_order['coin'], existing_order['oid']):
                            success = await self.place_limit_order(
                                order['coin'],
                                order['side'] == 'B',
                                scaled_size,
                                float(order['limitPx']),
                                reduce_only=reduce_only
                            )
                            if success:
                                processed_orders += 1

            except Exception as e:
                logger.error(f"Error processing order: {e}")
                continue

        logger.info(f"Order sync summary:")
        logger.info(f"Copy trade orders: {len(copy_orders)}")
        logger.info(f"My orders: {len(my_orders)}")
        logger.info(f"Orders processed: {processed_orders}")
        logger.info(f"Orders cancelled: {cancelled_orders}")

    async def run(self) -> None:
        """Main bot execution loop."""
        logger.info("Starting HyperLiquid Order Copy Bot...")
        logger.info(f"Copying from: {self.ACCOUNT_TO_COPY}")
        logger.info(f"Trading with: {self.TRADING_ADDRESS}")
        logger.info(f"Leverage: {self.LEVERAGE}x")
        logger.info(f"Minimum trade size: ${self.TRADE_LIMIT}")
        
        while self.should_run:
            try:
                await self.check_and_copy_orders()
                await asyncio.sleep(0.5)  # Check every 500ms
            except asyncio.CancelledError:
                logger.info("Bot operation cancelled, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying


async def main():
    """Main entry point for the order bot."""
    bot = OrderBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping bot...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Order Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
