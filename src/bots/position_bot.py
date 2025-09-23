"""
HyperLiquid Position Copy Bot

Monitors and copies positions from a target account with intelligent
position sizing and price-aware entry strategies.
"""

import asyncio
import os
import datetime
import math
import time
from typing import Dict, List, Optional, Tuple, Any
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


class PositionBot:
    """
    HyperLiquid Position Copy Bot
    
    This bot monitors and copies positions from a target account with
    intelligent position sizing and price-aware entry strategies.
    """
    
    def __init__(self):
        """Initialize the PositionBot with environment configuration."""
        load_dotenv()
        
        # Initialize HyperLiquid API
        self._init_hyperliquid()
        
        # Load configuration
        self._load_config()
        
        # Initialize metadata
        self._init_metadata()
        
        # Bot state
        self.pending_changes = {}
        self.previous_positions = {}
        
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
            logger.info("Position Bot restarted")
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            raise

    async def get_position(self, account: str) -> Dict[str, Any]:
        """
        Get position data for a given account.
        
        Args:
            account: The wallet address to query
            
        Returns:
            Position data including account value and asset positions
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/json',
                'Origin': 'https://app.hyperliquid.xyz',
                'Referer': 'https://app.hyperliquid.xyz/',
            }
            
            response = requests.post(
                'https://api.hyperliquid.xyz/info',
                json={"type": "clearinghouseState", "user": account},
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if not data:
                raise ValueError("Empty response received")
                
            return {
                "address": account,
                "accountValue": data["crossMarginSummary"]["accountValue"],
                "assetPositions": data["assetPositions"]
            }
        except Exception as e:
            logger.error(f"Error in get_position for {account}: {e}")
            raise

    async def get_allocations(self, account: str) -> Dict[str, Dict[str, float]]:
        """
        Get position allocations for an account.
        
        Args:
            account: The wallet address to query
            
        Returns:
            Dictionary mapping coin names to position data
        """
        try:
            position_data = await self.get_position(account)
            total_account_value = float(position_data["accountValue"])
            positions = {}
            
            for pos in position_data["assetPositions"]:
                coin = pos["position"]["coin"]
                entry_px = float(pos["position"]["entryPx"])
                szi = float(pos["position"]["szi"])
                position_value = float(pos["position"]["positionValue"])
                
                if szi < 0:
                    position_value = -position_value
                    
                if coin in positions:
                    positions[coin]["positionValue"] += position_value
                    positions[coin]["szi"] += szi
                    positions[coin]["entryPxTotal"] += entry_px
                else:
                    positions[coin] = {
                        "positionValue": position_value,
                        "szi": szi,
                        "entryPxTotal": entry_px
                    }

            # Calculate percentages and round values
            for coin in positions:
                positions[coin]["positionValue"] = round(
                    (positions[coin]["positionValue"] / total_account_value) * 100, 2
                )
                positions[coin]["szi"] = round(positions[coin]["szi"], 5)

            return dict(sorted(
                positions.items(), 
                key=lambda x: abs(x[1]["positionValue"]), 
                reverse=True
            ))
        except Exception as e:
            logger.error(f"Error getting allocations for {account}: {e}")
            return {}

    async def get_perpetuals_price(self) -> Dict[str, str]:
        """
        Get current market prices for all perpetuals.
        
        Returns:
            Dictionary mapping coin names to current prices
        """
        try:
            response = requests.post(
                'https://api.hyperliquid.xyz/info',
                json={"type": "allMids"},
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Content-Type': 'application/json',
                    'Origin': 'https://app.hyperliquid.xyz',
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting perpetuals prices: {e}")
            raise

    async def execute_trade(
        self, 
        market: str, 
        order_type: str, 
        position_type: str, 
        size: float
    ) -> Tuple[bool, str]:
        """
        Execute a trade on the specified market.
        
        Args:
            market: The trading pair
            order_type: "buy" or "sell"
            position_type: Position type for logging
            size: Trade size
            
        Returns:
            Tuple of (success, message)
        """
        try:
            size = round(float(size), self.sz_decimals[market])
            prices = await self.get_perpetuals_price()
            market_price = float(prices[market])
            is_buy = order_type == "buy"
            
            order_result = self.exchange.market_open(market, is_buy, size, market_price, 0.01)
            
            if order_result["status"] == "ok":
                for status in order_result["response"]["data"]["statuses"]:
                    if "filled" in status:
                        filled = status["filled"]
                        action = "Buy" if is_buy else "Sell"
                        return True, f"{action} {filled['totalSz']} {market} @ ${float(filled['avgPx']):.2f}"
                    else:
                        return False, f"Trade Error: {status.get('error', 'Unknown error')}"
            return False, "Order failed"
        except Exception as e:
            return False, f"Error executing trade: {e}"

    async def get_balance(self, address: str) -> str:
        """
        Get account balance for the specified address.
        
        Args:
            address: The wallet address to query
            
        Returns:
            Account balance as string
        """
        try:
            response = requests.post(
                'https://api.hyperliquid.xyz/info',
                json={"type": "clearinghouseState", "user": address},
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Content-Type': 'application/json',
                    'Origin': 'https://app.hyperliquid.xyz',
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data or "crossMarginSummary" not in data:
                raise ValueError("Invalid response format")
                
            return data["crossMarginSummary"]["accountValue"]
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {e}")
            raise

    def print_position_summary(self, positions: Dict[str, Dict], title: str) -> None:
        """
        Print a summary of positions.
        
        Args:
            positions: Dictionary of position data
            title: Title for the summary
        """
        if not positions:
            logger.info(f"{title}: No open positions")
            return
            
        logger.info(f"\n{title}:")
        total_value = 0
        
        for coin, pos in positions.items():
            direction = "Long" if pos["szi"] > 0 else "Short"
            size = abs(pos["szi"])
            entry_price = pos["entryPxTotal"]
            value = abs(pos["positionValue"])
            total_value += value
            
            logger.info(f"  {coin}: {direction} {size:.4f} @ ${entry_price:.2f} ({value:.2f}%)")
        
        logger.info(f"Total Position Value: {total_value:.2f}%")

    async def update_positions(
        self, 
        my_positions: Dict[str, Dict], 
        copy_positions: Dict[str, Dict], 
        prices: Dict[str, str]
    ) -> List[str]:
        """
        Update positions based on copy account positions.
        
        Args:
            my_positions: My current positions
            copy_positions: Positions from copy account
            prices: Current market prices
            
        Returns:
            List of actions taken
        """
        actions = []
        try:
            copy_account_value = float(await self.get_balance(self.ACCOUNT_TO_COPY))
            my_account_value = float(await self.get_balance(self.TRADING_ADDRESS)) * self.LEVERAGE
            
            # Process each position in copy account
            for coin, copy_pos in copy_positions.items():
                price = float(prices[coin])
                entry_price = copy_pos["entryPxTotal"]
                
                copy_position_value = abs(copy_pos["szi"] * price)
                target_size = (copy_position_value / copy_account_value) * my_account_value / price
                my_pos = my_positions.get(coin)
                
                # Open new position if not exists and meets criteria
                if not my_pos and copy_position_value > self.TRADE_LIMIT:
                    # Only enter if price is favorable
                    if ((copy_pos["szi"] > 0 and price < entry_price) or 
                        (copy_pos["szi"] < 0 and price > entry_price)):
                        
                        success, msg = await self.execute_trade(
                            coin,
                            "buy" if copy_pos["szi"] > 0 else "sell",
                            "long" if copy_pos["szi"] > 0 else "short",
                            abs(target_size)
                        )
                        if success:
                            actions.append(f"Opened new position: {msg}")
                
                # Update existing position
                elif my_pos:
                    current_size = abs(my_pos["szi"])
                    size_diff = abs(target_size - current_size)
                    size_diff_value = size_diff * price
                    
                    if size_diff_value > self.TRADE_LIMIT:
                        is_size_up = target_size > current_size
                        
                        # For size increases, check if price is favorable
                        if is_size_up:
                            is_favorable = ((my_pos["szi"] > 0 and price < entry_price) or 
                                          (my_pos["szi"] < 0 and price > entry_price))
                            
                            if not is_favorable:
                                # Queue for later execution when price is better
                                self.pending_changes[coin] = {
                                    "timestamp": time.time(),
                                    "targetSize": target_size,
                                    "direction": "long" if my_pos["szi"] > 0 else "short",
                                    "entryPrice": entry_price
                                }
                                continue
                        
                        # Execute the trade
                        success, msg = await self.execute_trade(
                            coin,
                            "buy" if (my_pos["szi"] > 0) == is_size_up else "sell",
                            "long" if my_pos["szi"] > 0 else "short",
                            size_diff
                        )
                        if success:
                            actions.append(f"Adjusted position: {msg}")
            
            # Close positions no longer in copy account
            for coin, pos in my_positions.items():
                if coin not in copy_positions:
                    success, msg = await self.execute_trade(
                        coin,
                        "buy" if pos["szi"] < 0 else "sell",
                        "flat",
                        abs(pos["szi"])
                    )
                    if success:
                        actions.append(f"Closed position: {msg}")
                    
            return actions
            
        except Exception as e:
            logger.error(f"Error in update_positions: {e}")
            return actions

    async def process_positions(self) -> None:
        """Main position processing loop."""
        try:
            while True:
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                
                # Get account values
                copy_account_value = float(await self.get_balance(self.ACCOUNT_TO_COPY))
                my_account_value = float(await self.get_balance(self.TRADING_ADDRESS)) * self.LEVERAGE
                
                logger.info(f"\n=== Position Update {current_time} ===")
                logger.info(f"Master Account: ${copy_account_value:,.2f}")
                logger.info(f"Copy Account: ${my_account_value:,.2f} (with {self.LEVERAGE}x leverage)")
                
                # Get current market prices
                prices = await self.get_perpetuals_price()
                pending_actions = []
                
                # Get and display positions
                my_positions = await self.get_allocations(self.TRADING_ADDRESS)
                copy_positions = await self.get_allocations(self.ACCOUNT_TO_COPY)
                
                self.print_position_summary(copy_positions, "Master Account Positions")
                self.print_position_summary(my_positions, "Copy Account Positions")

                # Process pending changes
                if self.pending_changes:
                    for market, change in list(self.pending_changes.items()):
                        current_price = float(prices[market])
                        is_price_favorable = (
                            (change["direction"] == "long" and current_price < change["entryPrice"]) or
                            (change["direction"] == "short" and current_price > change["entryPrice"])
                        )
                        
                        if is_price_favorable:
                            success, msg = await self.execute_trade(
                                market,
                                "buy" if change["direction"] == "long" else "sell",
                                change["direction"],
                                abs(change["targetSize"])
                            )
                            if success:
                                pending_actions.append(f"Executed delayed trade: {msg}")
                            del self.pending_changes[market]

                # Process position updates
                updates = await self.update_positions(my_positions, copy_positions, prices)
                pending_actions.extend(updates)

                # Print updates if any changes were made
                if pending_actions:
                    logger.info("\nPosition Updates:")
                    for action in pending_actions:
                        logger.info(f"• {action}")
                
                await asyncio.sleep(30)  # Check every 30 seconds

        except Exception as e:
            logger.error(f"Error in process_positions: {e}")
            await asyncio.sleep(5)
            await self.process_positions()

    async def run(self) -> None:
        """Main bot execution entry point."""
        logger.info("Starting HyperLiquid Position Copy Bot...")
        logger.info(f"Copying from: {self.ACCOUNT_TO_COPY}")
        logger.info(f"Trading with: {self.TRADING_ADDRESS}")
        logger.info(f"Leverage: {self.LEVERAGE}x")
        logger.info(f"Minimum trade size: ${self.TRADE_LIMIT}")
        
        await self.process_positions()


async def main():
    """Main entry point for the position bot."""
    bot = PositionBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping bot...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Position Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
