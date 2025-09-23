# HyperLiquid Copy Trader

> **Professional copy trading solution for HyperLiquid DEX with intelligent position management and automated execution.**

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 Overview

HyperLiquid Copy Trader is a sophisticated copy trading application designed for the HyperLiquid decentralized exchange. It provides automated position and order replication with intelligent entry strategies, proportional sizing, and comprehensive risk management features.

### ✨ Key Features

- **🎯 Dual Trading Modes**: Position-based and order-based copy trading strategies
- **📊 Intelligent Position Sizing**: Automatic scaling based on account values and leverage
- **⚡ Price-Aware Entry**: Smart entry timing for optimal position entries
- **🔒 Secure Credential Management**: Encrypted storage using system keyring
- **📱 Professional GUI**: Intuitive interface with real-time monitoring
- **🛡️ Risk Management**: Configurable trade limits and position controls
- **📈 Real-time Monitoring**: Live position tracking and detailed logging

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Trading Modes](#-trading-modes)
- [Configuration](#-configuration)
- [Building](#-building)
- [Security](#-security)
- [API Reference](#-api-reference)
- [Contributing](#-contributing)
- [License](#-license)

## 🛠️ Installation

### Prerequisites

- **Python 3.8+** - [Download Python](https://python.org/downloads/)
- **Linux VPS** with SSH access for bot deployment
- **Node.js** and **npm** for PM2 process management
- **HyperLiquid Account** with API access

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lucyCooked/hyperliquid-copytrader.git
   cd hyperliquid-copytrader
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

### Binary Downloads

Pre-built binaries are available for major platforms:

- **macOS**: [Download Latest Release](https://github.com/lucyCooked/hyperliquid-copytrader/releases)
- **Windows**: [Download Latest Release](https://github.com/lucyCooked/hyperliquid-copytrader/releases)
- **Linux**: Use source installation or build from source

## 🚀 Quick Start

1. **Launch the Application**
   ```bash
   python main.py
   ```

2. **Configure Server Connection**
   - Enter your VPS server details
   - Provide SSH credentials
   - Test connection

3. **Setup Trading Configuration**
   - Input the wallet address to copy
   - Set your trading wallet address
   - Configure your HyperLiquid API private key
   - Set position multiplier/leverage

4. **Start Trading**
   - Click "Start Trading" to begin copy trading
   - Monitor positions and orders in real-time
   - Review logs for detailed execution history

## 🎯 Trading Modes

### 📊 Position Bot

**Intelligent position-based copy trading with strategic entry timing**

- **Smart Entry Strategy**: Only enters positions when price is favorable relative to the target's entry price
- **Dynamic Position Sizing**: Automatically scales positions based on account value ratios
- **Delayed Execution**: Queues unfavorable entries for better price execution
- **Comprehensive Monitoring**: Real-time position tracking with detailed reporting

**Ideal for**: Long-term position mirroring with optimized entry points

### 📋 Order Bot

**Real-time order replication with precision execution**

- **Instant Order Mirroring**: Copies limit orders in real-time with proportional sizing
- **Order Lifecycle Management**: Handles placement, updates, and cancellations automatically
- **Reduce-Only Support**: Maintains order types including reduce-only orders
- **High-Frequency Updates**: 500ms polling for minimal latency

**Ideal for**: Active trading strategies requiring immediate order execution

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in your deployment directory:

```env
# Trading Configuration
PRIVATE_KEY_API=your_hyperliquid_api_private_key
ACCOUNT_TO_COPY=0x1234567890abcdef1234567890abcdef12345678
TRADING_ADDRESS=0xabcdef1234567890abcdef1234567890abcdef12
LEVERAGE=1.5

# Optional Settings
TRADE_LIMIT=10.0              # Minimum trade size in USD
MINI_ALLOC_OF_PF=0           # Minimum portfolio allocation %
```

### Security Configuration

The application uses the system keyring for secure credential storage:

- **SSH passwords** are encrypted using system keyring
- **API private keys** are stored securely and never logged
- **Configuration files** contain only non-sensitive data

### Server Requirements

Your VPS should have:
- **Ubuntu 20.04+** or similar Linux distribution
- **Python 3.8+** and pip
- **Node.js 16+** and npm
- **PM2** for process management
- **SSH access** enabled

## 🔧 Building

### macOS Application

```bash
python scripts/build_macos.py
```

Output: `dist/HyperLiquidCopyTrader.app`

### Windows Executable

```bash
python scripts/build_windows.py
```

Output: `dist/HyperLiquidCopyTrader/`

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run code formatting
black src/

# Run type checking
mypy src/

# Run tests
pytest tests/
```

## 🛡️ Security

### Best Practices

- **🔐 Never share private keys** or store them in plain text
- **🌐 Use secure SSH connections** with key-based authentication when possible
- **🔒 Enable 2FA** on all exchange accounts
- **💾 Regular backups** of configuration and logs
- **🔍 Monitor positions** regularly for unexpected behavior

### API Permissions

Ensure your HyperLiquid API key has only necessary permissions:
- ✅ **Trading** - Required for order placement
- ✅ **Account Reading** - Required for position monitoring
- ❌ **Withdrawal** - Not required, should be disabled

### Network Security

- Use VPS providers with strong security practices
- Keep your server updated with security patches
- Consider using a VPN for additional security
- Monitor server logs for unauthorized access attempts

## 📚 API Reference

### Core Classes

#### `OrderBot`
Handles real-time order copying and management.

```python
from src.bots import OrderBot

bot = OrderBot()
await bot.run()
```

#### `PositionBot`
Manages position-based copy trading with intelligent entry strategies.

```python
from src.bots import PositionBot

bot = PositionBot()
await bot.run()
```

#### `TradingBotApp`
Main GUI application for bot management and monitoring.

```python
from src.gui import TradingBotApp
import tkinter as tk

root = tk.Tk()
app = TradingBotApp(root)
root.mainloop()
```

### Configuration Options

| Parameter | Description | Default | Range |
|-----------|-------------|---------|--------|
| `LEVERAGE` | Position size multiplier | 1.0 | 0.1 - 50.0 |
| `TRADE_LIMIT` | Minimum trade size (USD) | 10.0 | 1.0 - 1000.0 |
| `MINI_ALLOC_OF_PF` | Minimum portfolio allocation (%) | 0.0 | 0.0 - 100.0 |

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Development Process

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with proper testing
4. **Follow code style**: Run `black src/` for formatting
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Code Standards

- Follow [PEP 8](https://pep8.org/) style guidelines
- Add type hints for all functions
- Include docstrings for public methods
- Write unit tests for new features
- Update documentation as needed

### Reporting Issues

When reporting issues, please include:
- Detailed description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- System information (OS, Python version)
- Relevant log outputs (sanitized)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**Trading cryptocurrencies involves substantial risk and may not be suitable for all investors. Past performance does not guarantee future results. This software is provided "as is" without warranties of any kind. Users are responsible for their own trading decisions and should understand the risks involved.**

- This software is for educational and research purposes
- Always test with small amounts first
- Never risk more than you can afford to lose
- Understand the risks of automated trading
- Be aware of potential bugs or market conditions that could cause losses

## 🙏 Acknowledgments

- **HyperLiquid Team** for building an innovative DEX platform
- **Python Community** for excellent libraries and tools
- **Contributors** who help improve this project
- **Users** who provide valuable feedback and bug reports

---

<div align="center">

**Built with ❤️ for the DeFi community**

[⭐ Star this repo](https://github.com/lucyCooked/hyperliquid-copytrader) if you find it helpful!

</div>