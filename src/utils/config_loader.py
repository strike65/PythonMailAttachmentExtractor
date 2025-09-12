#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Loader Module

Handles loading, validation, and merging of configuration from JSON files
and command-line arguments.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import getpass

from .colors import Colors


class ConfigLoader:
    """
    Loads and validates configuration for the email attachment extractor.
    """
    
    # Default configuration values
    DEFAULTS = {
        'port': 993,
        'use_ssl': True,
        'mailbox': 'INBOX',
        'search_criteria': 'ALL',
        'organize_by_sender': False,
        'organize_by_date': True,
        'save_metadata': True,
        'save_path': None,
        'limit': None,
        'recursive': False,
        'limit_per_folder': None,
        'total_limit': None,
        'allowed_extensions': None,
        'excluded_extensions': None
    }
    
    # Required fields that must be present
    REQUIRED_FIELDS = ['server', 'username']
    
    @classmethod
    def load_config(cls, config_file: str) -> Optional[Dict]:
        """
        Load configuration from JSON file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Configuration dictionary or None if failed
        """
        try:
            if not os.path.exists(config_file):
                print(Colors.error(f"Configuration file '{config_file}' not found"))
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(Colors.success(f"Configuration loaded from: {config_file}"))
            return config
            
        except json.JSONDecodeError as e:
            print(Colors.error(f"Error parsing JSON file: {e}"))
            return None
        except Exception as e:
            print(Colors.error(f"Error loading configuration: {e}"))
            return None
    
    @classmethod
    def validate_config(cls, config: Dict) -> bool:
        """
        Validate configuration dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        missing_fields = [field for field in cls.REQUIRED_FIELDS 
                         if field not in config or config[field] is None]
        
        if missing_fields:
            print(Colors.error(f"Missing required fields: {', '.join(missing_fields)}"))
            return False
        
        # Validate port number
        if 'port' in config:
            port = config.get('port')
            if not isinstance(port, int) or port < 1 or port > 65535:
                print(Colors.error(f"Invalid port number: {port}"))
                return False
        
        # Validate boolean fields
        bool_fields = ['use_ssl', 'organize_by_sender', 'organize_by_date', 
                      'save_metadata', 'recursive']
        for field in bool_fields:
            if field in config and not isinstance(config[field], bool):
                print(Colors.warning(f"Field '{field}' should be boolean, converting..."))
                config[field] = bool(config[field])
        
        # Validate integer fields
        int_fields = ['limit', 'limit_per_folder', 'total_limit']
        for field in int_fields:
            if field in config and config[field] is not None:
                if not isinstance(config[field], int) or config[field] < 1:
                    print(Colors.error(f"Invalid {field}: must be positive integer"))
                    return False
        
        # Validate extension lists
        for field in ['allowed_extensions', 'excluded_extensions']:
            if field in config and config[field] is not None:
                if not isinstance(config[field], list):
                    print(Colors.error(f"'{field}' must be a list"))
                    return False
                # Filter out None values
                config[field] = [ext for ext in config[field] if ext is not None]
        
        return True
    
    @classmethod
    def apply_defaults(cls, config: Dict) -> Dict:
        """
        Apply default values to configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with defaults applied
        """
        for key, default_value in cls.DEFAULTS.items():
            if key not in config:
                config[key] = default_value
        
        return config
    
    @classmethod
    def merge_with_args(cls, config: Dict, args) -> Dict:
        """
        Merge configuration with command-line arguments.
        
        Command-line arguments override configuration file values.
        
        Args:
            config: Configuration dictionary
            args: Parsed command-line arguments
            
        Returns:
            Merged configuration
        """
        # Direct field mappings
        field_mappings = {
            'server': 'server',
            'port': 'port',
            'username': 'username',
            'password': 'password',
            'save_path': 'save_path',
            'mailbox': 'mailbox',
            'search_criteria': 'search_criteria',
            'limit': 'limit',
            'recursive': 'recursive',
            'limit_per_folder': 'limit_per_folder',
            'total_limit': 'total_limit'
        }
        
        for arg_name, config_name in field_mappings.items():
            if hasattr(args, arg_name) and getattr(args, arg_name) is not None:
                config[config_name] = getattr(args, arg_name)
        
        # Boolean flags
        if hasattr(args, 'organize_by_sender') and args.organize_by_sender:
            config['organize_by_sender'] = True
        if hasattr(args, 'organize_by_date') and args.organize_by_date:
            config['organize_by_date'] = True
        if hasattr(args, 'no_metadata') and args.no_metadata:
            config['save_metadata'] = False
        
        # File types (extensions)
        if hasattr(args, 'file_types') and args.file_types:
            config['allowed_extensions'] = args.file_types
        if hasattr(args, 'exclude_types') and args.exclude_types:
            config['excluded_extensions'] = args.exclude_types
        
        return config
    
    @classmethod
    def prompt_for_password(cls, config: Dict) -> Dict:
        """
        Prompt for password if not in configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with password
        """
        if not config.get('password'):
            username = config.get('username', 'user')
            config['password'] = getpass.getpass(
                Colors.cyan(f"Password for {username}: ")
            )
        
        return config
    
    @classmethod
    def save_config(cls, config: Dict, filepath: str, 
                   include_password: bool = False) -> bool:
        """
        Save configuration to JSON file.
        
        Args:
            config: Configuration dictionary
            filepath: Path to save configuration
            include_password: Whether to include password in saved config
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a copy for saving
            save_config = config.copy()
            
            # Remove password if requested
            if not include_password and 'password' in save_config:
                save_config['password'] = None
                print(Colors.warning("Password not saved for security"))
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_config, f, indent=2, ensure_ascii=False)
            
            print(Colors.success(f"Configuration saved to: {filepath}"))
            return True
            
        except Exception as e:
            print(Colors.error(f"Error saving configuration: {e}"))
            return False
    
    @classmethod
    def create_example_config(cls) -> Dict:
        """
        Create an example configuration.
        
        Returns:
            Example configuration dictionary
        """
        return {
            "server": "imap.gmail.com",
            "port": 993,
            "username": "your.email@gmail.com",
            "password": None,
            "use_ssl": True,
            "mailbox": "INBOX",
            "search_criteria": "ALL",
            "organize_by_sender": False,
            "organize_by_date": True,
            "save_path": "./attachments",
            "limit": 100,
            "save_metadata": True,
            "allowed_extensions": ["pdf", "*.doc*", "*.xls*"],
            "excluded_extensions": ["exe", "bat", "*.tmp"],
            "recursive": False,
            "limit_per_folder": None,
            "total_limit": None
        }
    
    @classmethod
    def print_config(cls, config: Dict, hide_password: bool = True):
        """
        Print configuration in a readable format.
        
        Args:
            config: Configuration dictionary
            hide_password: Whether to hide password
        """
        print(Colors.info("\nCurrent Configuration:"))
        print("-" * 40)
        
        for key, value in config.items():
            if key == 'password' and hide_password and value:
                display_value = '***hidden***'
            elif value is None:
                display_value = 'Not set'
            elif isinstance(value, list):
                if not value:
                    display_value = '[]'
                else:
                    display_value = ', '.join(str(v) for v in value)
            else:
                display_value = str(value)
            
            print(f"{key:20s}: {display_value}")


def load_config(config_file: str) -> Optional[Dict]:
    """
    Convenience function to load and validate configuration.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Valid configuration dictionary or None
    """
    loader = ConfigLoader()
    
    # Load configuration
    config = loader.load_config(config_file)
    if not config:
        return None
    
    # Apply defaults
    config = loader.apply_defaults(config)
    
    # Validate
    if not loader.validate_config(config):
        return None
    
    return config


def validate_config(config: Dict) -> bool:
    """
    Convenience function to validate configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid, False otherwise
    """
    return ConfigLoader.validate_config(config)


def prepare_config(args) -> Optional[Dict]:
    """
    Prepare configuration from file and/or command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Complete configuration dictionary or None
    """
    loader = ConfigLoader()
    config = {}
    
    # Load from file if specified
    if hasattr(args, 'config') and args.config:
        config = loader.load_config(args.config)
        if not config:
            return None
    
    # Merge with command-line arguments
    config = loader.merge_with_args(config, args)
    
    # Apply defaults
    config = loader.apply_defaults(config)
    
    # Validate
    if not loader.validate_config(config):
        return None
    
    # Prompt for password if needed
    config = loader.prompt_for_password(config)
    
    return config