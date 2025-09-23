"""
HyperLiquid Copy Trader

A professional trading application for copying trades on the HyperLiquid
decentralized exchange with intelligent position and order management.
"""

__version__ = "2.0.0"
__author__ = "HyperLiquid Copy Trader Team"
__description__ = "Professional copy trading solution for HyperLiquid DEX"

from src.gui.trading_app import TradingBotApp, main
from src.bots.order_bot import OrderBot
from src.bots.position_bot import PositionBot

__all__ = [
    "TradingBotApp",
    "OrderBot", 
    "PositionBot",
    "main"
]
