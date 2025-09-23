"""
HyperLiquid Copy Trader GUI Application

A professional GUI application for managing HyperLiquid copy trading bots
with SSH connection management and secure credential storage.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import paramiko
import threading
import json
from pathlib import Path
import time
from datetime import datetime
import keyring
from typing import Optional, Callable, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CollapsibleFrame(ttk.Frame):
    """A collapsible frame widget for organizing UI elements."""
    
    def __init__(self, parent, text="", *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)

        # Configure style for the frame
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Helvetica', '12', 'bold'))
        style.configure('Logs.TFrame', background='white')

        # Initialize the toggle functionality
        self.show = tk.BooleanVar(value=False)
        
        # Main container
        self.main_container = ttk.Frame(self, style='Logs.TFrame', padding="2")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Header frame
        self.header_frame = ttk.Frame(self.main_container, style='Logs.TFrame')
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        
        # Toggle button/label
        self.toggle_button = ttk.Label(
            self.header_frame, 
            text="▼ " + text, 
            style='Header.TLabel',
            padding=(5, 5)
        )
        self.toggle_button.grid(row=0, column=0, sticky="w")
        
        # Content frame with fixed height
        self.content_frame = ttk.Frame(self.main_container, padding="5", height=200)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=2, pady=(0, 2))
        self.content_frame.grid_propagate(False)
        
        # Create log text widget
        self.log_text = scrolledtext.ScrolledText(
            self.content_frame,
            height=10,
            width=80,
            background='white',
            font=('Consolas', '10'),
            wrap=tk.WORD,
            undo=False,
            maxundo=0,
            setgrid=True
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Log buffer for batching updates
        self.log_buffer = []
        self.max_lines = 1000
        
        # Configure tags for different message types
        self.log_text.tag_configure('timestamp', foreground='#666666')
        self.log_text.tag_configure('error', foreground='#ff0000')
        self.log_text.tag_configure('warning', foreground='#ffa500')
        self.log_text.tag_configure('success', foreground='#008000')
        self.log_text.tag_configure('info', foreground='#000000')
        
        # Configure weights for proper expansion
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(1, weight=0)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=0)
        
        # Define toggle method
        def toggle(event=None):
            if self.show.get():
                self.content_frame.grid_remove()
                self.toggle_button.configure(text="▶ " + self.toggle_button.cget("text")[2:])
            else:
                self.content_frame.grid()
                self.toggle_button.configure(text="▼ " + self.toggle_button.cget("text")[2:])
            self.show.set(not self.show.get())
        
        # Store the toggle method
        self.toggle = toggle
        
        # Bind click event
        self.toggle_button.bind('<Button-1>', self.toggle)
        self.header_frame.bind('<Button-1>', self.toggle)

        # Schedule periodic updates
        self._schedule_update()

    def _schedule_update(self):
        if hasattr(self, 'content_frame'):
            self.content_frame.after(100, self._process_buffer)

    def _process_buffer(self):
        try:
            if self.log_buffer:
                self.log_text.configure(state='normal')
                
                # Process all buffered messages
                for timestamp, message, log_type in self.log_buffer:
                    self.log_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
                    self.log_text.insert(tk.END, f"{message}\n", log_type)
                
                # Clear buffer
                self.log_buffer.clear()
                
                # Limit number of lines
                self._limit_lines()
                
                self.log_text.configure(state='disabled')
                self.log_text.see(tk.END)
        finally:
            self._schedule_update()

    def _limit_lines(self):
        """Limit the number of lines to prevent memory issues."""
        line_count = int(self.log_text.index('end-1c').split('.')[0])
        if line_count > self.max_lines:
            self.log_text.delete('1.0', f'{line_count - self.max_lines}.0')

    def append_log(self, message: str, log_type: str = 'info'):
        """Add log message to buffer."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_buffer.append((timestamp, message, log_type))

    def get_all_logs(self) -> str:
        """Get all logs."""
        return self.log_text.get("1.0", tk.END)

    def clear_logs(self):
        """Clear all logs."""
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state='disabled')
        self.log_buffer.clear()
        
    def set_logs(self, logs: str):
        """Set log content."""
        self.clear_logs()
        if logs:
            self.log_text.configure(state='normal')
            self.log_text.insert(tk.END, logs)
            self.log_text.configure(state='disabled')
            self.log_text.see(tk.END)


class TradingBotApp:
    """Main application class for the HyperLiquid Copy Trader GUI."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("HyperLiquid Copy Trader")
        self.root.geometry("600x300")

        # Create app data directory for storing credentials and logs
        self.app_data_dir = Path.home() / '.hyperliquid_copytrader'
        self.app_data_dir.mkdir(exist_ok=True)
        self.log_file = self.app_data_dir / 'bot_logs.txt'
        self.config_file = self.app_data_dir / 'config.json'
        
        # Initialize UI variables
        self._init_variables()
        
        # Load saved configuration
        self.load_saved_config()
        
        # Setup UI
        self.setup_ui()
        
        # Initialize connection state
        self.ssh: Optional[paramiko.SSHClient] = None
        self.connected = False
        self.bots_running = False

        # Load previous logs
        self.load_logs()

        # Add timer for batched log saving
        self.last_log_save = time.time()
        self.log_save_interval = 5
        
        # Schedule periodic log saving
        self.root.after(5000, self.periodic_save_logs)

        # Set up closing handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Initially show only server connection tab
        self.notebook.select(0)
        self.notebook.hide(1)

    def _init_variables(self):
        """Initialize tkinter variables."""
        self.server_var = tk.StringVar(value="your-server.com")
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.copy_account_var = tk.StringVar()
        self.trading_address_var = tk.StringVar()
        self.private_key_var = tk.StringVar()
        self.leverage_var = tk.StringVar(value="1")

    def setup_ui(self):
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Top container for tabs
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), pady=5)
        
        # Create and configure style for notebook
        style = ttk.Style()
        style.layout('CustomNotebook.TNotebook.Tab', [])
        style.configure('CustomNotebook.TNotebook', tabposition='n')
        style.configure('CustomNotebook.TNotebook.Tab', 
                    padding=[10, 5],
                    font=('Helvetica', '12', 'bold'),
                    borderwidth=0,
                    background='white'
        )
        
        # Configure tab strip to be borderless
        style.layout('CustomNotebook', [('Notebook.client', {'sticky': 'nswe'})])
        
        # Create notebook with custom style
        self.notebook = ttk.Notebook(top_frame, style='CustomNotebook.TNotebook')
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Setup connection and trading frames
        self._setup_connection_frame()
        self._setup_trading_frame()
        
        # Bottom container for logs
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.S), pady=5)
        
        # Log frame
        self.log_frame = CollapsibleFrame(bottom_frame, text="Logs")
        self.log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        self.log_frame.toggle()  # Collapse the logs frame on startup
        
        # Configure grid weights
        self._configure_grid_weights(main_frame, top_frame, bottom_frame)

    def _setup_connection_frame(self):
        """Set up the server connection frame."""
        connection_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(connection_frame, text="Server Connection")
        
        # Connection UI elements
        ttk.Label(connection_frame, text="Server:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(connection_frame, textvariable=self.server_var).grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(connection_frame, text="Username:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(connection_frame, textvariable=self.username_var).grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(connection_frame, text="Password:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(connection_frame, textvariable=self.password_var, show="*").grid(row=2, column=1, sticky=(tk.W, tk.E))
        
        self.connect_button = ttk.Button(connection_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Add status indicator
        status_frame = ttk.Frame(connection_frame)
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5,0))
        
        self.status_label = ttk.Label(
            status_frame, 
            text="Not Connected",
            foreground='red'
        )
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        connection_frame.columnconfigure(1, weight=1)

    def _setup_trading_frame(self):
        """Set up the trading configuration frame."""
        config_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(config_frame, text="Trading Configuration")
        
        # Account to Copy
        ttk.Label(config_frame, text="Address to Copytrade:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.copy_account_var).grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Trading Address
        ttk.Label(config_frame, text="Web3 Wallet Address:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.trading_address_var).grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        # API Private Key
        ttk.Label(config_frame, text="Private Key from API:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.private_key_var, show="*").grid(row=2, column=1, sticky=(tk.W, tk.E))
        ttk.Label(config_frame, justify=tk.LEFT).grid(row=2, column=2, sticky=tk.W, padx=5)
        
        # Multiplier
        ttk.Label(config_frame, text="Position Multiplier:").grid(row=3, column=0, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.leverage_var).grid(row=3, column=1, sticky=(tk.W, tk.E))
        ttk.Label(config_frame, justify=tk.LEFT).grid(row=3, column=2, sticky=tk.W, padx=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(config_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=5)
        
        self.start_button = ttk.Button(buttons_frame, text="Start Trading", command=self.start_trading, state=tk.DISABLED)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="Stop Trading", command=self.stop_trading, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        config_frame.columnconfigure(1, weight=1)

    def _configure_grid_weights(self, main_frame, top_frame, bottom_frame):
        """Configure grid weights for proper resizing."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=0)
        main_frame.rowconfigure(1, weight=1)
        
        top_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(0, weight=1)

    def update_connection_status(self, connected: bool):
        """Update the connection status indicator."""
        if connected:
            self.status_label.configure(
                text="Connected",
                foreground='green'
            )
        else:
            self.status_label.configure(
                text="Not Connected",
                foreground='red'
            )

    def load_saved_config(self):
        """Load saved configuration from files and keyring."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                    # Load non-sensitive data
                    self.server_var.set(config.get('server', ''))
                    self.username_var.set(config.get('username', ''))
                    self.copy_account_var.set(config.get('copy_account', ''))
                    self.trading_address_var.set(config.get('trading_address', ''))
                    self.leverage_var.set(config.get('leverage', '1'))
                    
                    # Load sensitive data from keyring
                    if config.get('username'):
                        password = keyring.get_password(
                            'hyperliquid_copytrader',
                            f"{config.get('username')}@{config.get('server')}_password"
                        )
                        if password:
                            self.password_var.set(password)
                            
                    if config.get('trading_address'):
                        private_key = keyring.get_password(
                            'hyperliquid_copytrader',
                            f"{config.get('trading_address')}_private_key"
                        )
                        if private_key:
                            self.private_key_var.set(private_key)
                            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    def save_config(self):
        """Save configuration securely."""
        try:
            # Save non-sensitive data
            config = {
                'server': self.server_var.get(),
                'username': self.username_var.get(),
                'copy_account': self.copy_account_var.get(),
                'trading_address': self.trading_address_var.get(),
                'leverage': self.leverage_var.get()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            
            # Save sensitive data securely
            if self.password_var.get():
                keyring.set_password(
                    'hyperliquid_copytrader',
                    f"{self.username_var.get()}@{self.server_var.get()}_password",
                    self.password_var.get()
                )
            
            if self.private_key_var.get():
                keyring.set_password(
                    'hyperliquid_copytrader',
                    f"{self.trading_address_var.get()}_private_key",
                    self.private_key_var.get()
                )
            
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def periodic_save_logs(self):
        """Periodically save logs to file."""
        try:
            current_time = time.time()
            if current_time - self.last_log_save >= self.log_save_interval:
                self.save_logs()
                self.last_log_save = current_time
        finally:
            self.root.after(5000, self.periodic_save_logs)

    def save_logs(self):
        """Save logs to file."""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(self.log_frame.get_all_logs())
        except Exception as e:
            logger.error(f"Error saving logs: {e}")

    def load_logs(self):
        """Load previous logs."""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = f.read()
                    if logs:
                        self.log_frame.set_logs(logs)
        except Exception as e:
            logger.error(f"Error loading logs: {e}")

    def log(self, message: str, log_type: str = 'info'):
        """Add log message with appropriate styling."""
        try:
            self.log_frame.append_log(message, log_type)
        except Exception as e:
            logger.error(f"Error logging message: {e}")
            logger.info(f"[{datetime.now()}] {message}")

    def handle_successful_connection(self):
        """Handle UI updates after successful connection."""
        self.update_connection_status(True)
        
        # Show trading configuration tab
        self.notebook.select(1)
        self.notebook.hide(0)
        
        # Reset connect button
        self.connect_button.configure(
            state=tk.NORMAL,
            text="Connect"
        )

    def connect_to_server(self):
        """Initiate connection to SSH server."""
        self.connect_button.configure(state=tk.DISABLED, text="Connecting...")

        def connect_thread():
            try:
                self.log("Connecting to server...", 'info')
                
                # Create SSH client with keepalive
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connect to server with timeout
                try:
                    self.ssh.connect(
                        self.server_var.get(),
                        username=self.username_var.get(),
                        password=self.password_var.get(),
                        timeout=10
                    )
                except (paramiko.SSHException, TimeoutError) as e:
                    raise Exception(f"Failed to connect: {str(e)}")
                
                # Enable keepalive to prevent timeouts
                self.ssh.get_transport().set_keepalive(60)
                
                self.log("Connected successfully!", 'success')
                self.log("Setting up environment...")

                # Setup environment
                await self._setup_environment()
                
                self.log("Environment setup complete!")
                self.connected = True
                self.root.after(0, self.handle_successful_connection)
                
            except Exception as e:
                self.log(f"Connection error: {str(e)}", 'error')
                messagebox.showerror("Connection Error", str(e))
                self.root.after(0, lambda: self.connect_button.configure(
                    state=tk.NORMAL,
                    text="Connect"
                ))
                return
            finally:
                if not self.connected:
                    self.root.after(0, lambda: self.connect_button.configure(
                        state=tk.NORMAL,
                        text="Connect"
                    ))
        
        # Start connection thread
        thread = threading.Thread(target=connect_thread)
        thread.daemon = True
        thread.start()

    async def _setup_environment(self):
        """Set up the remote environment for trading bots."""
        # Environment setup logic would go here
        # This is a placeholder for the original environment setup code
        pass

    def execute_ssh_command(self, command: str, check_exit: bool = True) -> tuple[bool, str]:
        """Execute SSH command with optimized handling."""
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            if check_exit:
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    error = stderr.read().decode().strip()
                    if error:
                        return False, error
            return True, stdout.read().decode().strip()
        except Exception as e:
            return False, str(e)

    def start_trading(self):
        """Start the trading bots."""
        if not all([self.copy_account_var.get(), self.trading_address_var.get(), self.private_key_var.get()]):
            messagebox.showerror("Error", "Please fill in all trading configuration fields")
            return
                
        def start_thread():
            try:
                self.start_button.configure(state=tk.DISABLED)
                self.bots_running = True
                
                # Create .env file
                env_content = f"""PRIVATE_KEY_API={self.private_key_var.get()}
ACCOUNT_TO_COPY={self.copy_account_var.get()}
TRADING_ADDRESS={self.trading_address_var.get()}
LEVERAGE={self.leverage_var.get()}"""

                with self.ssh.open_sftp() as sftp:
                    with sftp.file("/root/trading_bots/.env", 'w') as f:
                        f.write(env_content)
                
                # Start bots
                success, output = self.execute_ssh_command(
                    "cd /root/trading_bots && "
                    "pm2 start position_bot.py --name position_bot --interpreter python3 && "
                    "pm2 start order_bot.py --name order_bot --interpreter python3"
                )
                
                if not success:
                    self.log(f"Error starting bots: {output}", 'error')
                    return
                
                self.log("Trading bots started successfully!", 'success')
                self.stop_button.configure(state=tk.NORMAL)
                
                # Start log monitoring
                self.monitor_logs()
                
            except Exception as e:
                self.log(f"Error starting trading: {str(e)}", 'error')
                messagebox.showerror("Error", f"Failed to start trading: {str(e)}")
                self.start_button.configure(state=tk.NORMAL)
        
        thread = threading.Thread(target=start_thread)
        thread.start()

    def stop_trading(self):
        """Stop the trading bots."""
        def stop_thread():
            try:
                self.log("Stopping trading bots...")
                self.bots_running = False
                
                # Stop PM2 processes
                stop_commands = [
                    "pm2 stop position_bot",
                    "pm2 stop order_bot",
                    "pm2 delete position_bot",
                    "pm2 delete order_bot"
                ]
                
                for cmd in stop_commands:
                    stdin, stdout, stderr = self.ssh.exec_command(cmd)
                    exit_status = stdout.channel.recv_exit_status()
                    
                    if exit_status != 0:
                        error = stderr.read().decode()
                        self.log(f"Warning during bot shutdown: {error}")
                
                self.log("Trading bots stopped successfully")
                self.stop_button.configure(state=tk.DISABLED)
                self.start_button.configure(state=tk.NORMAL)
                
            except Exception as e:
                self.log(f"Error stopping trading bots: {str(e)}")
                messagebox.showerror("Error", f"Failed to stop trading bots: {str(e)}")
        
        thread = threading.Thread(target=stop_thread)
        thread.start()

    def monitor_logs(self):
        """Monitor bot logs from the remote server."""
        def monitor_thread():
            last_log_time = {}
            
            while self.connected and self.bots_running:
                try:
                    # Monitor logic would go here
                    # This is a placeholder for the original log monitoring code
                    time.sleep(5)
                except Exception as e:
                    self.log(f"Error monitoring logs: {str(e)}", 'error')
                    time.sleep(5)
                        
        thread = threading.Thread(target=monitor_thread)
        thread.daemon = True
        thread.start()

    def on_closing(self):
        """Handle application closing."""
        try:
            if self.bots_running:
                if messagebox.askyesno("Quit", "Trading bots are running. Stop them before closing?"):
                    self.stop_trading()
                    self.root.after(1000, self.on_closing)
                    return
                    
            if self.ssh and self.connected:
                self.ssh.close()
                self.connected = False
                self.update_connection_status(False)
            
            self.save_config()
            self.save_logs()
            self.root.destroy()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            self.root.destroy()


def main():
    """Main entry point for the GUI application."""
    root = tk.Tk()
    app = TradingBotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
