"""
Test cases for trading bots
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import os
from src.bots.order_bot import OrderBot
from src.bots.position_bot import PositionBot


class TestOrderBot:
    """Test cases for OrderBot"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock environment variables
        self.env_vars = {
            'PRIVATE_KEY_API': 'test_private_key',
            'ACCOUNT_TO_COPY': '0x1234567890abcdef1234567890abcdef12345678',
            'TRADING_ADDRESS': '0xabcdef1234567890abcdef1234567890abcdef12',
            'LEVERAGE': '2.0',
            'TRADE_LIMIT': '10.0'
        }
        
    @patch.dict(os.environ, {'PRIVATE_KEY_API': 'test_key', 'ACCOUNT_TO_COPY': '0x123', 'TRADING_ADDRESS': '0xabc'})
    @patch('src.bots.order_bot.eth_account')
    @patch('src.bots.order_bot.Exchange')
    @patch('src.bots.order_bot.Info')
    def test_order_bot_initialization(self, mock_info, mock_exchange, mock_eth_account):
        """Test OrderBot initialization"""
        # Mock the account creation
        mock_account = Mock()
        mock_eth_account.Account.from_key.return_value = mock_account
        
        # Mock the info.meta() call
        mock_info_instance = Mock()
        mock_info_instance.meta.return_value = {
            "universe": [
                {"name": "BTC", "szDecimals": 4},
                {"name": "ETH", "szDecimals": 3}
            ]
        }
        mock_info.return_value = mock_info_instance
        
        # Initialize bot
        bot = OrderBot()
        
        # Assertions
        assert bot.ACCOUNT_TO_COPY == '0x123'
        assert bot.TRADING_ADDRESS == '0xabc'
        assert bot.LEVERAGE == 1.0  # default value
        assert 'BTC' in bot.sz_decimals
        assert bot.sz_decimals['BTC'] == 4
        
    @patch.dict(os.environ, {'PRIVATE_KEY_API': 'test_key', 'ACCOUNT_TO_COPY': '0x123', 'TRADING_ADDRESS': '0xabc'})
    @patch('src.bots.order_bot.eth_account')
    @patch('src.bots.order_bot.Exchange')
    @patch('src.bots.order_bot.Info')
    @patch('src.bots.order_bot.requests')
    async def test_get_account_value(self, mock_requests, mock_info, mock_exchange, mock_eth_account):
        """Test account value retrieval"""
        # Setup mocks
        mock_account = Mock()
        mock_eth_account.Account.from_key.return_value = mock_account
        
        mock_info_instance = Mock()
        mock_info_instance.meta.return_value = {"universe": []}
        mock_info.return_value = mock_info_instance
        
        # Mock requests response
        mock_response = Mock()
        mock_response.json.return_value = {
            'crossMarginSummary': {'accountValue': '1000.50'}
        }
        mock_requests.post.return_value = mock_response
        
        # Initialize bot and test
        bot = OrderBot()
        result = await bot.get_account_value('0x123')
        
        assert result == 1000.50
        
    async def test_get_account_value_error(self):
        """Test account value retrieval with error"""
        with patch.dict(os.environ, {'PRIVATE_KEY_API': 'test_key', 'ACCOUNT_TO_COPY': '0x123', 'TRADING_ADDRESS': '0xabc'}):
            with patch('src.bots.order_bot.eth_account'):
                with patch('src.bots.order_bot.Exchange'):
                    with patch('src.bots.order_bot.Info') as mock_info:
                        mock_info_instance = Mock()
                        mock_info_instance.meta.return_value = {"universe": []}
                        mock_info.return_value = mock_info_instance
                        
                        with patch('src.bots.order_bot.requests') as mock_requests:
                            mock_requests.post.side_effect = Exception("Network error")
                            
                            bot = OrderBot()
                            result = await bot.get_account_value('0x123')
                            
                            assert result == 0


class TestPositionBot:
    """Test cases for PositionBot"""
    
    @patch.dict(os.environ, {'PRIVATE_KEY_API': 'test_key', 'ACCOUNT_TO_COPY': '0x123', 'TRADING_ADDRESS': '0xabc'})
    @patch('src.bots.position_bot.eth_account')
    @patch('src.bots.position_bot.Exchange')
    @patch('src.bots.position_bot.Info')
    def test_position_bot_initialization(self, mock_info, mock_exchange, mock_eth_account):
        """Test PositionBot initialization"""
        # Mock the account creation
        mock_account = Mock()
        mock_eth_account.Account.from_key.return_value = mock_account
        
        # Mock the info.meta() call
        mock_info_instance = Mock()
        mock_info_instance.meta.return_value = {
            "universe": [
                {"name": "BTC", "szDecimals": 4},
                {"name": "ETH", "szDecimals": 3}
            ]
        }
        mock_info.return_value = mock_info_instance
        
        # Initialize bot
        bot = PositionBot()
        
        # Assertions
        assert bot.ACCOUNT_TO_COPY == '0x123'
        assert bot.TRADING_ADDRESS == '0xabc'
        assert bot.LEVERAGE == 1.0  # default value
        assert 'BTC' in bot.sz_decimals
        assert bot.sz_decimals['BTC'] == 4
        assert bot.pending_changes == {}
        assert bot.previous_positions == {}


class TestBotIntegration:
    """Integration tests for bot functionality"""
    
    @pytest.mark.asyncio
    async def test_bot_error_handling(self):
        """Test that bots handle errors gracefully"""
        with patch.dict(os.environ, {'PRIVATE_KEY_API': 'invalid_key'}):
            with pytest.raises(ValueError):
                OrderBot()


if __name__ == "__main__":
    pytest.main([__file__])
