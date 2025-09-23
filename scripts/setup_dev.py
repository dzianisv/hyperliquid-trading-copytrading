#!/usr/bin/env python3
"""
Development Environment Setup Script

This script sets up a complete development environment for HyperLiquid Copy Trader
including dependencies, pre-commit hooks, and development tools.
"""

import subprocess
import sys
import os
from pathlib import Path
import venv


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def setup_virtual_environment():
    """Set up a virtual environment."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("📦 Virtual environment already exists")
        return True
    
    print("📦 Creating virtual environment...")
    try:
        venv.create("venv", with_pip=True)
        print("✅ Virtual environment created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False


def get_pip_command():
    """Get the appropriate pip command for the current platform."""
    if os.name == 'nt':  # Windows
        return "venv\\Scripts\\pip"
    else:  # Unix-like
        return "venv/bin/pip"


def get_python_command():
    """Get the appropriate python command for the current platform."""
    if os.name == 'nt':  # Windows
        return "venv\\Scripts\\python"
    else:  # Unix-like
        return "venv/bin/python"


def install_dependencies():
    """Install project dependencies."""
    pip_cmd = get_pip_command()
    
    commands = [
        (f"{pip_cmd} install --upgrade pip", "Upgrading pip"),
        (f"{pip_cmd} install -r requirements.txt", "Installing main dependencies"),
        (f"{pip_cmd} install -e .", "Installing project in development mode"),
        (f"{pip_cmd} install pytest pytest-cov black flake8 mypy pre-commit", "Installing development tools"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True


def setup_pre_commit():
    """Set up pre-commit hooks."""
    python_cmd = get_python_command()
    
    # Create pre-commit config
    pre_commit_config = """
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.8
        
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]
        
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        args: [--ignore-missing-imports]
        additional_dependencies: [types-requests]
        
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: check-added-large-files
"""
    
    with open(".pre-commit-config.yaml", "w") as f:
        f.write(pre_commit_config.strip())
    
    return run_command(f"{python_cmd} -m pre_commit install", "Setting up pre-commit hooks")


def run_initial_tests():
    """Run initial tests to verify setup."""
    python_cmd = get_python_command()
    
    commands = [
        (f"{python_cmd} -m black --check src/", "Checking code formatting"),
        (f"{python_cmd} -m flake8 src/", "Running linting"),
        (f"{python_cmd} -m pytest tests/ -v", "Running tests"),
    ]
    
    for command, description in commands:
        run_command(command, description)


def create_example_env():
    """Create an example .env file."""
    env_example = """# HyperLiquid Copy Trader Configuration
# Copy this file to .env and fill in your actual values

# Trading Configuration
PRIVATE_KEY_API=your_hyperliquid_api_private_key_here
ACCOUNT_TO_COPY=0x1234567890abcdef1234567890abcdef12345678
TRADING_ADDRESS=0xabcdef1234567890abcdef1234567890abcdef12
LEVERAGE=1.5

# Optional Settings
TRADE_LIMIT=10.0
MINI_ALLOC_OF_PF=0.0

# Development Settings (optional)
LOG_LEVEL=INFO
DEBUG=False
"""
    
    with open(".env.example", "w") as f:
        f.write(env_example)
    
    print("📝 Created .env.example file")


def main():
    """Main setup function."""
    print("🚀 Setting up HyperLiquid Copy Trader development environment...\n")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Setup steps
    steps = [
        (setup_virtual_environment, "Virtual Environment Setup"),
        (install_dependencies, "Dependency Installation"),
        (setup_pre_commit, "Pre-commit Hooks Setup"),
        (create_example_env, "Example Configuration"),
        (run_initial_tests, "Initial Testing"),
    ]
    
    success_count = 0
    for step_func, step_name in steps:
        print(f"\n🔄 {step_name}")
        print("-" * 50)
        
        if step_func():
            success_count += 1
        else:
            print(f"⚠️  {step_name} had issues, but continuing...")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"🎉 Setup completed! {success_count}/{len(steps)} steps successful")
    print("=" * 60)
    
    if success_count == len(steps):
        print("✅ Development environment is ready!")
    else:
        print("⚠️  Some steps had issues. Please check the output above.")
    
    print("\n📋 Next steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("2. Copy .env.example to .env and configure your settings")
    print("3. Run the application: python main.py")
    print("4. Start developing! 🚀")


if __name__ == "__main__":
    main()
