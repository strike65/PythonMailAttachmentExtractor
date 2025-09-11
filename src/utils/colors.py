#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Terminal Colors Module

Provides cross-platform colored terminal output using ANSI escape codes.
Automatically handles Windows terminal compatibility.
"""

import platform
import sys
import os
from typing import Optional, Any


class Colors:
    """
    Cross-platform color codes for terminal output.
    
    Provides methods for colored text output that work on
    Windows, Linux, and macOS terminals.
    """
    
    # ANSI Color Codes
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Regular colors (less bright)
    DARK_RED = '\033[31m'
    DARK_GREEN = '\033[32m'
    DARK_YELLOW = '\033[33m'
    DARK_BLUE = '\033[34m'
    DARK_MAGENTA = '\033[35m'
    DARK_CYAN = '\033[36m'
    GRAY = '\033[90m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # Text styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    STRIKETHROUGH = '\033[9m'
    
    # Reset
    RESET = '\033[0m'
    
    # Class variable to track if colors are enabled
    _enabled = True
    _initialized = False
    
    @classmethod
    def _initialize(cls):
        """
        Initialize color support based on the platform and environment.
        Called automatically on first use.
        """
        if cls._initialized:
            return
            
        cls._initialized = True
        
        # Check if output is redirected (not a terminal)
        if not sys.stdout.isatty():
            cls._enabled = False
            return
        
        # Check for NO_COLOR environment variable
        if os.environ.get('NO_COLOR'):
            cls._enabled = False
            return
        
        # Platform-specific initialization
        if platform.system() == 'Windows':
            cls._initialize_windows()
        
        # Check for TERM environment variable on Unix-like systems
        elif platform.system() in ['Linux', 'Darwin']:
            term = os.environ.get('TERM', '')
            if term == 'dumb':
                cls._enabled = False
    
    @classmethod
    def _initialize_windows(cls):
        """
        Enable ANSI escape sequences on Windows 10+.
        """
        try:
            # Try to enable ANSI support on Windows 10+
            import ctypes
            kernel32 = ctypes.windll.kernel32
            
            # Get current console mode
            STD_OUTPUT_HANDLE = -11
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            
            # Enable ANSI escape sequence processing
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(handle, mode)
            
        except Exception:
            # If we can't enable ANSI on Windows, try colorama as fallback
            try:
                import colorama
                colorama.init()
            except ImportError:
                # No color support available
                cls._enabled = False
    
    @classmethod
    def disable(cls):
        """Disable colored output."""
        cls._enabled = False
    
    @classmethod
    def enable(cls):
        """Enable colored output."""
        cls._enabled = True
        cls._initialize()
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if colored output is enabled."""
        if not cls._initialized:
            cls._initialize()
        return cls._enabled
    
    # ========== Convenience Methods ==========
    
    @classmethod
    def _colorize(cls, text: Any, *codes: str) -> str:
        """
        Apply color codes to text if colors are enabled.
        
        Args:
            text: Text to colorize
            *codes: Color/style codes to apply
            
        Returns:
            Colorized string or original text
        """
        if not cls._initialized:
            cls._initialize()
            
        text = str(text)
        
        if not cls._enabled or not codes:
            return text
            
        return ''.join(codes) + text + cls.RESET
    
    @classmethod
    def error(cls, text: Any) -> str:
        """
        Format text as an error (red).
        
        Args:
            text: Text to format
            
        Returns:
            Red colored text
        """
        return cls._colorize(text, cls.RED, cls.BOLD)
    
    @classmethod
    def success(cls, text: Any) -> str:
        """
        Format text as success (green).
        
        Args:
            text: Text to format
            
        Returns:
            Green colored text
        """
        return cls._colorize(text, cls.GREEN)
    
    @classmethod
    def warning(cls, text: Any) -> str:
        """
        Format text as warning (yellow).
        
        Args:
            text: Text to format
            
        Returns:
            Yellow colored text
        """
        return cls._colorize(text, cls.YELLOW)
    
    @classmethod
    def info(cls, text: Any) -> str:
        """
        Format text as info (cyan).
        
        Args:
            text: Text to format
            
        Returns:
            Cyan colored text
        """
        return cls._colorize(text, cls.CYAN)
    
    @classmethod
    def debug(cls, text: Any) -> str:
        """
        Format text as debug (gray/dim).
        
        Args:
            text: Text to format
            
        Returns:
            Gray colored text
        """
        return cls._colorize(text, cls.GRAY, cls.DIM)
    
    @classmethod
    def bold(cls, text: Any) -> str:
        """
        Format text as bold.
        
        Args:
            text: Text to format
            
        Returns:
            Bold text
        """
        return cls._colorize(text, cls.BOLD)
    
    @classmethod
    def underline(cls, text: Any) -> str:
        """
        Format text with underline.
        
        Args:
            text: Text to format
            
        Returns:
            Underlined text
        """
        return cls._colorize(text, cls.UNDERLINE)
    
    @classmethod
    def cyan(cls, text: Any) -> str:
        """
        Format text in cyan color.
        
        Args:
            text: Text to format
            
        Returns:
            Cyan colored text
        """
        return cls._colorize(text, cls.CYAN)
    
    @classmethod
    def custom(cls, text: Any, fg: Optional[str] = None, 
               bg: Optional[str] = None, style: Optional[str] = None) -> str:
        """
        Apply custom color combination.
        
        Args:
            text: Text to format
            fg: Foreground color code
            bg: Background color code
            style: Style code (bold, underline, etc.)
            
        Returns:
            Formatted text
        """
        codes = []
        if style:
            codes.append(style)
        if fg:
            codes.append(fg)
        if bg:
            codes.append(bg)
            
        return cls._colorize(text, *codes)
    
    @classmethod
    def strip_colors(cls, text: str) -> str:
        """
        Remove all ANSI color codes from text.
        
        Args:
            text: Text with potential color codes
            
        Returns:
            Plain text without color codes
        """
        import re
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_escape.sub('', text)
    
    @classmethod
    def print_colored(cls, text: Any, color_func: callable = None):
        """
        Print colored text directly.
        
        Args:
            text: Text to print
            color_func: Color function to apply (e.g., cls.error)
        """
        if color_func:
            print(color_func(text))
        else:
            print(text)


class ProgressIndicator:
    """
    Simple progress indicator for terminal output.
    """
    
    def __init__(self, total: int, prefix: str = "Progress", 
                 width: int = 50, color: bool = True):
        """
        Initialize progress indicator.
        
        Args:
            total: Total number of items
            prefix: Prefix text
            width: Width of progress bar
            color: Whether to use colors
        """
        self.total = total
        self.prefix = prefix
        self.width = width
        self.current = 0
        self.use_color = color and Colors.is_enabled()
    
    def update(self, current: int, suffix: str = ""):
        """
        Update progress indicator.
        
        Args:
            current: Current item number
            suffix: Optional suffix text
        """
        self.current = current
        percent = 100 * (current / float(self.total))
        filled = int(self.width * current // self.total)
        
        # Create progress bar
        bar = '█' * filled + '-' * (self.width - filled)
        
        # Format output
        if self.use_color:
            if percent < 33:
                bar_colored = Colors.red(bar)
            elif percent < 66:
                bar_colored = Colors.yellow(bar)
            else:
                bar_colored = Colors.green(bar)
                
            output = f'\r{self.prefix}: |{bar_colored}| {percent:.1f}% {suffix}'
        else:
            output = f'\r{self.prefix}: |{bar}| {percent:.1f}% {suffix}'
        
        # Print with carriage return
        print(output, end='\r')
        
        # Print newline when complete
        if current >= self.total:
            print()
    
    def increment(self, suffix: str = ""):
        """Increment progress by one."""
        self.update(self.current + 1, suffix)


def test_colors():
    """
    Test color output on the current terminal.
    """
    print("Testing terminal color support...\n")
    
    # Test basic colors
    print(Colors.error("This is an error message"))
    print(Colors.success("This is a success message"))
    print(Colors.warning("This is a warning message"))
    print(Colors.info("This is an info message"))
    print(Colors.debug("This is a debug message"))
    
    print("\nStyles:")
    print(Colors.bold("Bold text"))
    print(Colors.underline("Underlined text"))
    print(Colors.custom("Custom colored text", fg=Colors.MAGENTA, style=Colors.BOLD))
    
    print("\nAll foreground colors:")
    colors = [
        ('Black', Colors.BLACK),
        ('Red', Colors.RED),
        ('Green', Colors.GREEN),
        ('Yellow', Colors.YELLOW),
        ('Blue', Colors.BLUE),
        ('Magenta', Colors.MAGENTA),
        ('Cyan', Colors.CYAN),
        ('White', Colors.WHITE),
    ]
    
    for name, color in colors:
        print(Colors._colorize(f"  {name} text", color))
    
    print("\nColors enabled:", Colors.is_enabled())
    print("Platform:", platform.system())
    
    # Test progress indicator
    print("\nTesting progress indicator:")
    progress = ProgressIndicator(50, "Processing")
    import time
    for i in range(51):
        progress.update(i, f"Item {i}")
        time.sleep(0.02)


if __name__ == "__main__":
    test_colors()