#!/usr/bin/env python3
"""
Bot runner for Kubernetes deployment
Runs either position_bot or order_bot based on BOT_TYPE environment variable
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for bot runner."""
    bot_type = os.getenv("BOT_TYPE", "position").lower()

    logger.info(f"Starting HyperLiquid Copy Trading Bot (Type: {bot_type})")

    try:
        if bot_type == "position":
            from bots.position_bot import PositionBot
            bot = PositionBot()
            await bot.run()
        elif bot_type == "order":
            from bots.order_bot import OrderBot
            bot = OrderBot()
            await bot.run()
        else:
            logger.error(f"Invalid BOT_TYPE: {bot_type}. Must be 'position' or 'order'")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping bot...")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
