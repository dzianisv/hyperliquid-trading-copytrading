"""
Windows Build Script for HyperLiquid Copy Trader

This script builds a Windows executable using PyInstaller
with all necessary dependencies and resources.
"""

import os
import shutil
from pathlib import Path
import sys

def build_windows_app():
    """Build Windows executable using PyInstaller."""
    # Get current directory
    current_dir = Path().absolute()
    print(f"Building from directory: {current_dir}")
    
    # Create resources directory if it doesn't exist
    resources_dir = current_dir / "resources"
    resources_dir.mkdir(exist_ok=True)
    print(f"Resources directory: {resources_dir}")

    # Remove any existing files in resources
    for existing_file in resources_dir.glob('*'):
        if existing_file.is_file():
            existing_file.unlink()
    
    # Copy bot files to resources
    src_bots_dir = current_dir / "src" / "bots"
    bot_files = ["position_bot.py", "order_bot.py"]
    
    for bot_file in bot_files:
        source = src_bots_dir / bot_file
        destination = resources_dir / bot_file
        if source.exists():
            shutil.copy2(source, destination)
            print(f"Copied {bot_file} to resources")
        else:
            raise FileNotFoundError(f"Required file {bot_file} not found in {src_bots_dir}!")

    # Check if main app file exists
    main_app = current_dir / "main.py"
    if not main_app.exists():
        print("Creating main.py entry point...")
        with open(main_app, 'w') as f:
            f.write("""#!/usr/bin/env python3
\"\"\"
Main entry point for HyperLiquid Copy Trader
\"\"\"

from src.gui.trading_app import main

if __name__ == "__main__":
    main()
""")

    # Define PyInstaller configuration
    try:
        import PyInstaller.__main__
        
        pyinstaller_args = [
            str(main_app),
            '--windowed',
            '--name=HyperLiquidCopyTrader',
            '--add-data=resources;.',
            '--add-data=src;src',
            '--clean',
            '--noconfirm',
            '--icon=assets/icon.ico' if (current_dir / "assets" / "icon.ico").exists() else None,
            '--hidden-import=tkinter',
            '--hidden-import=paramiko',
            '--hidden-import=eth_account',
            '--hidden-import=dotenv',
            '--hidden-import=hyperliquid',
            '--hidden-import=cryptography',
            '--hidden-import=requests',
            '--hidden-import=asyncio',
            '--hidden-import=eth_account.signers.local',
            '--hidden-import=hyperliquid.exchange',
            '--hidden-import=hyperliquid.info',
            '--hidden-import=hyperliquid.utils',
            '--hidden-import=keyring',
            '--hidden-import=keyring.backends',
            '--hidden-import=keyring.backends.Windows',
            '--collect-all=keyring',
            '--onedir',
        ]
        
        # Remove None values (icon if not found)
        pyinstaller_args = [arg for arg in pyinstaller_args if arg is not None]
        
        print("Starting PyInstaller build...")
        PyInstaller.__main__.run(pyinstaller_args)
        print("Build completed successfully!")
        print("Application can be found in the 'dist' directory")
        
    except ImportError:
        print("PyInstaller not found. Please install it with: pip install pyinstaller")
        sys.exit(1)
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_windows_app()
