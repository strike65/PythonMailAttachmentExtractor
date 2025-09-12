#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Configuration Loader Module
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config_loader import ConfigLoader, load_config, prepare_config


class TestConfigLoader:
    """Test ConfigLoader class."""
    
    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "server": "imap.gmail.com",
                "username": "test@gmail.com",
                "port": 993
            }
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = ConfigLoader.load_config(temp_file)
            assert config is not None
        finally:
            os.unlink(temp_file)
    
    def test_validate_config_required_fields(self):
        """Test validation of required fields."""
        # Missing required fields
        config = {"port": 993}
        assert ConfigLoader.validate_config(config) is False
        
        # Has required fields
        config = {"server": "imap.gmail.com", "username": "test@gmail.com"}
        assert ConfigLoader.validate_config(config) is True
    
    def test_validate_config_port(self):
        """Test port validation."""
        # Invalid port
        config = {"server": "test", "username": "user", "port": 99999}
        assert ConfigLoader.validate_config(config) is False
        
        # Valid port
        config = {"server": "test", "username": "user", "port": 993}
        assert ConfigLoader.validate_config(config) is True
    
    def test_validate_config_extensions(self):
        """Test extension list validation."""
        # Valid extensions
        config = {
            "server": "test",
            "username": "user",
            "allowed_extensions": ["pdf", "*.doc*"],
            "excluded_extensions": ["exe", "bat"]
        }
        assert ConfigLoader.validate_config(config) is True
        
        # Invalid - not a list
        config = {
            "server": "test",
            "username": "user",
            "allowed_extensions": "pdf"
        }
        assert ConfigLoader.validate_config(config) is False
    
    def test_apply_defaults(self):
        """Test applying default values."""
        config = {"server": "test", "username": "user"}
        config = ConfigLoader.apply_defaults(config)
        
        assert config['port'] == 993
        assert config['use_ssl'] is True
        assert config['mailbox'] == 'INBOX'
        assert config['search_criteria'] == 'ALL'
        assert config['organize_by_date'] is True
        assert config['save_metadata'] is True
    
    def test_merge_with_args(self):
        """Test merging config with command-line arguments."""
        config = {
            "server": "imap.gmail.com",
            "username": "test@gmail.com",
            "port": 993
        }
        
        # Mock args
        args = Mock()
        args.server = "imap.yahoo.com"  # Override
        args.port = None  # Don't override
        args.organize_by_sender = True
        args.no_metadata = True
        args.file_types = ["pdf", "docx"]
        
        merged = ConfigLoader.merge_with_args(config, args)
        
        assert merged['server'] == "imap.yahoo.com"  # Overridden
        assert merged['port'] == 993  # Original kept
        assert merged['organize_by_sender'] is True
        assert merged['save_metadata'] is False  # no_metadata flag
        assert merged['allowed_extensions'] == ["pdf", "docx"]
    
    @patch('getpass.getpass')
    def test_prompt_for_password(self, mock_getpass):
        """Test password prompting."""
        mock_getpass.return_value = "secret123"
        
        config = {"username": "test@gmail.com"}
        config = ConfigLoader.prompt_for_password(config)
        
        assert config['password'] == "secret123"
        mock_getpass.assert_called_once()
    
    def test_save_config_with_password(self):
        """Test saving configuration with password."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config = {
                "server": "imap.gmail.com",
                "username": "test@gmail.com",
                "password": "secret123"
            }
            
            # Save with password
            assert ConfigLoader.save_config(config, config_path, include_password=True)
            
            # Load and check
            with open(config_path, 'r') as f:
                saved = json.load(f)
            assert saved['password'] == "secret123"
    
    def test_save_config_without_password(self):
        """Test saving configuration without password."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config = {
                "server": "imap.gmail.com",
                "username": "test@gmail.com",
                "password": "secret123"
            }
            
            # Save without password
            assert ConfigLoader.save_config(config, config_path, include_password=False)
            
            # Load and check
            with open(config_path, 'r') as f:
                saved = json.load(f)
            assert saved['password'] is None
    
    def test_create_example_config(self):
        """Test creating example configuration."""
        config = ConfigLoader.create_example_config()
        
        assert 'server' in config
        assert 'username' in config
        assert 'port' in config
        assert config['port'] == 993
        assert config['use_ssl'] is True
        assert isinstance(config['allowed_extensions'], list)


class TestHelperFunctions:
    """Test standalone helper functions."""
    
    def test_load_config_function(self):
        """Test the standalone load_config function."""
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                config_data = {
                    "server": "imap.gmail.com",
                    "username": "test@gmail.com"
                }
                json.dump(config_data, f)
                temp_file = f.name
            
            config = load_config(temp_file)
            assert config is not None
            assert config['server'] == "imap.gmail.com"
            # Should have defaults applied
            assert config['port'] == 993
        finally:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
    
    @patch('src.utils.config_loader.ConfigLoader.prompt_for_password')
    def test_prepare_config_with_file(self, mock_prompt):
        """Test prepare_config with config file."""
        mock_prompt.side_effect = lambda x: x  # Return config unchanged
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "server": "imap.gmail.com",
                "username": "test@gmail.com"
            }
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            args = Mock(spec=['config','server','port','username','password','ssl'])
            args.config = temp_file
            args.server = None
            args.port = None
            args.username = None
            args.password = None
            args.ssl = None
            
            config = prepare_config(args)
            assert config is not None
            assert config['server'] == "imap.gmail.com"
        finally:
            os.unlink(temp_file)
    
    def test_prepare_config_with_args_only(self):
        """Test prepare_config with command-line args only."""
        args = Mock()
        args.config = None
        args.server = "imap.yahoo.com"
        args.username = "test@yahoo.com"
        args.port = 993
        args.password = "secret"
        args.organize_by_sender = False
        args.organize_by_date = False
        args.no_metadata = False
        
        config = prepare_config(args)
        assert config is not None
        assert config['server'] == "imap.yahoo.com"
        assert config['username'] == "test@yahoo.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])