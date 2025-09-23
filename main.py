#!/usr/bin/env python3
"""
Main entry point for HyperLiquid Copy Trader

A professional copy trading application for the HyperLiquid decentralized exchange.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from gui.trading_app import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Application error: {e}")
    sys.exit(1)
