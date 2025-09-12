#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Colors Module
"""

import pytest
import sys
import os
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.colors import Colors, ProgressIndicator


class TestColors:
    """Test Colors class functionality."""
    
    def test_color_codes_exist(self):
        """Test that color codes are defined."""
        assert Colors.RED
        assert Colors.GREEN
        assert Colors.YELLOW
        assert Colors.CYAN
        assert Colors.RESET
    
    @patch('sys.stdout.isatty', return_value=True)
    def test_colorize_with_colors_enabled(self, _):
        """Test colorizing text when colors are enabled."""
        Colors.enable(force_recheck=True)
        text = "Test"
        result = Colors._colorize(text, Colors.RED)
        assert Colors.RED in result
        assert Colors.RESET in result
        assert "Test" in result
    
    def test_colorize_with_colors_disabled(self):
        Colors.disable()
        text = "Test"
        result = Colors._colorize(text, Colors.RED)
        assert result == "Test"  # No color codes
        Colors.enable()  # Re-enable for other tests
    
    def test_error_formatting(self):
        """Test error message formatting."""
        message = "Error occurred"
        result = Colors.error(message)
        assert message in result
        if Colors.is_enabled():
            assert Colors.RED in result
    
    def test_success_formatting(self):
        """Test success message formatting."""
        message = "Operation successful"
        result = Colors.success(message)
        assert message in result
        if Colors.is_enabled():
            assert Colors.GREEN in result
    
    def test_warning_formatting(self):
        """Test warning message formatting."""
        message = "Warning: Check this"
        result = Colors.warning(message)
        assert message in result
        if Colors.is_enabled():
            assert Colors.YELLOW in result
    
    def test_info_formatting(self):
        """Test info message formatting."""
        message = "Information"
        result = Colors.info(message)
        assert message in result
        if Colors.is_enabled():
            assert Colors.CYAN in result
    
    def test_strip_colors(self):
        """Test stripping ANSI color codes."""
        colored_text = f"{Colors.RED}Error{Colors.RESET}"
        stripped = Colors.strip_colors(colored_text)
        assert stripped == "Error"
        assert Colors.RED not in stripped
        assert Colors.RESET not in stripped
    
    def test_custom_color_combination(self):
        """Test custom color combinations."""
        text = "Custom"
        result = Colors.custom(text, fg=Colors.MAGENTA, bg=Colors.BG_YELLOW, style=Colors.BOLD)
        assert "Custom" in result
        if Colors.is_enabled():
            assert Colors.MAGENTA in result
            assert Colors.BG_YELLOW in result
            assert Colors.BOLD in result
    
    @patch('sys.stdout.isatty')
    def test_non_tty_disables_colors(self, mock_isatty):
        """Test that non-TTY output disables colors."""
        mock_isatty.return_value = False
        Colors._initialized = False
        Colors._initialize()
        assert not Colors.is_enabled()
        
        # Reset
        mock_isatty.return_value = True
        Colors._initialized = False
        Colors._initialize()


class TestProgressIndicator:
    """Test ProgressIndicator class."""
    
    def test_progress_indicator_creation(self):
        """Test creating a progress indicator."""
        progress = ProgressIndicator(100, "Processing")
        assert progress.total == 100
        assert progress.prefix == "Processing"
        assert progress.current == 0
    
    def test_progress_update(self):
        """Test updating progress."""
        progress = ProgressIndicator(100, "Test")
        progress.update(50)
        assert progress.current == 50
        
        progress.update(100)
        assert progress.current == 100
    
    def test_progress_increment(self):
        """Test incrementing progress."""
        progress = ProgressIndicator(100, "Test")
        progress.increment()
        assert progress.current == 1
        
        progress.increment()
        assert progress.current == 2
    
    @patch('builtins.print')
    def test_progress_output(self, mock_print):
        """Test progress indicator output."""
        progress = ProgressIndicator(10, "Test", width=10)
        progress.update(5, "halfway")
        
        # Check that print was called
        mock_print.assert_called()
        call_args = str(mock_print.call_args)
        assert "Test" in call_args
        assert "50" in call_args  # 50%
        assert "halfway" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])