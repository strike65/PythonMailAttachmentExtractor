#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Tests for Email Attachment Extractor
"""

import pytest
import sys
import os
import tempfile
import json
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.extractor import EmailAttachmentExtractor
from src.core.email_processor import EmailProcessor
from src.cli.argparser import parse_arguments, create_parser
from src.providers.email_providers import EmailProviders


class TestEmailProviders:
    """Test email provider configurations."""
    
    def test_get_provider_config(self):
        """Test getting provider configuration."""
        config = EmailProviders.get_provider_config('gmail')
        assert config is not None
        assert config['server'] == 'imap.gmail.com'
        assert config['port'] == 993
        assert config['use_ssl'] is True
    
    def test_get_provider_list(self):
        """Test getting list of providers."""
        providers = EmailProviders.get_provider_list()
        assert 'Gmail' in providers
        assert 'Outlook/Office 365' in providers
        assert 'iCloud' in providers
    
    def test_detect_provider_from_email(self):
        """Test provider detection from email address."""
        assert EmailProviders.detect_provider_from_email('user@gmail.com') == 'gmail'
        assert EmailProviders.detect_provider_from_email('user@outlook.com') == 'outlook'
        assert EmailProviders.detect_provider_from_email('user@icloud.com') == 'icloud'
        assert EmailProviders.detect_provider_from_email('user@unknown.com') is None
    
    def test_needs_special_handling(self):
        """Test special handling detection."""
        assert EmailProviders.needs_special_handling('imap.mail.me.com') is True
        assert EmailProviders.needs_special_handling('imap.gmail.com') is False


class TestArgumentParser:
    """Test command-line argument parsing."""
    
    def test_parse_basic_arguments(self):
        """Test parsing basic arguments."""
        parser = create_parser()
        args = parser.parse_args([
            '--server', 'imap.gmail.com',
            '--username', 'test@gmail.com',
            '--save-path', './attachments'
        ])
        assert args.server == 'imap.gmail.com'
        assert args.username == 'test@gmail.com'
        assert args.save_path == './attachments'
    
    def test_parse_file_types(self):
        """Test parsing file type arguments."""
        parser = create_parser()
        args = parser.parse_args([
            '--file-types', 'pdf', '*.doc*', 'image_*.jpg'
        ])
        assert args.file_types == ['pdf', '*.doc*', 'image_*.jpg']
    
    def test_parse_boolean_flags(self):
        """Test parsing boolean flags."""
        parser = create_parser()
        args = parser.parse_args([
            '--organize-by-sender',
            '--organize-by-date',
            '--recursive',
            '--no-metadata'
        ])
        assert args.organize_by_sender is True
        assert args.organize_by_date is True
        assert args.recursive is True
        assert args.no_metadata is True


class TestEmailProcessorIntegration:
    """Test EmailProcessor integration."""
    
    @patch('email.message_from_bytes')
    def test_parse_email_standard(self, mock_parse):
        """Test standard email parsing."""
        processor = EmailProcessor()
        mock_msg = Mock()
        mock_parse.return_value = mock_msg
        
        raw_email = b"From: test@example.com\r\nSubject: Test\r\n\r\nBody"
        result = processor.parse_email(raw_email, "imap.gmail.com")
        
        assert result == mock_msg
        mock_parse.assert_called_once()
    
    @patch('email.message_from_bytes')
    @patch('email.message_from_string')
    def test_parse_email_icloud(self, mock_parse_string, mock_parse_bytes):
        """Test iCloud-specific email parsing."""
        processor = EmailProcessor()
        mock_msg = Mock()
        mock_parse_bytes.return_value = mock_msg
        
        raw_email = b"From: test@icloud.com\r\nSubject: Test\r\n\r\nBody"
        result = processor.parse_email(raw_email, "imap.mail.me.com")
        
        assert result == mock_msg


class TestExtractorIntegration:
    """Test EmailAttachmentExtractor integration."""
    
    @patch('imaplib.IMAP4_SSL')
    def test_connect_ssl(self, mock_imap):
        """Test SSL connection."""
        mock_connection = Mock()
        mock_imap.return_value = mock_connection
        mock_connection.login.return_value = ('OK', [])
        
        extractor = EmailAttachmentExtractor(
            server='imap.gmail.com',
            port=993,
            username='test@gmail.com',
            password='password',
            use_ssl=True
        )
        
        result = extractor.connect()
        assert result is True
        mock_imap.assert_called_once()
        mock_connection.login.assert_called_with('test@gmail.com', 'password')
    
    @patch('imaplib.IMAP4_SSL')
    def test_select_mailbox(self, mock_imap):
        """Test mailbox selection."""
        mock_connection = Mock()
        mock_imap.return_value = mock_connection
        mock_connection.login.return_value = ('OK', [])
        mock_connection.select.return_value = ('OK', [])
        
        extractor = EmailAttachmentExtractor(
            server='imap.gmail.com',
            port=993,
            username='test@gmail.com',
            password='password'
        )
        extractor.connect()
        
        result = extractor.select_mailbox('INBOX')
        assert result is True
        mock_connection.select.assert_called_with('INBOX', readonly=True)
    
    @patch('imaplib.IMAP4_SSL')
    def test_select_mailbox_icloud(self, mock_imap):
        """Test iCloud mailbox selection (readonly=False)."""
        mock_connection = Mock()
        mock_imap.return_value = mock_connection
        mock_connection.login.return_value = ('OK', [])
        mock_connection.select.return_value = ('OK', [])
        
        extractor = EmailAttachmentExtractor(
            server='imap.mail.me.com',  # iCloud server
            port=993,
            username='test@icloud.com',
            password='password'
        )
        extractor.connect()
        
        result = extractor.select_mailbox('INBOX')
        assert result is True
        # iCloud should use readonly=False
        mock_connection.select.assert_called_with('INBOX', readonly=False)


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_config_file_creation(self):
        """Test creating and loading a config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'config.json')
            
            config = {
                "server": "imap.gmail.com",
                "username": "test@gmail.com",
                "port": 993,
                "allowed_extensions": ["pdf", "*.doc*"],
                "excluded_extensions": ["exe", "bat"]
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            # Verify file was created
            assert os.path.exists(config_path)
            
            # Load and verify
            with open(config_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded['server'] == "imap.gmail.com"
            assert loaded['allowed_extensions'] == ["pdf", "*.doc*"]


# pytest.ini configuration
PYTEST_INI = """[pytest]
# pytest configuration

# Test discovery patterns
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test paths
testpaths = tests

# Output options
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings

# Markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    
# Coverage options (when running with pytest-cov)
# Run with: pytest --cov=src --cov-report=html
"""

# conftest.py for shared fixtures
CONFTEST_PY = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared pytest fixtures and configuration
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_config():
    """Provide a sample configuration dictionary."""
    return {
        "server": "imap.gmail.com",
        "port": 993,
        "username": "test@gmail.com",
        "password": "testpass",
        "use_ssl": True,
        "mailbox": "INBOX",
        "search_criteria": "ALL",
        "organize_by_date": True,
        "save_metadata": True,
        "allowed_extensions": ["pdf", "*.doc*"],
        "excluded_extensions": ["exe", "bat"]
    }


@pytest.fixture
def mock_email_message():
    """Create a mock email message."""
    from unittest.mock import Mock
    
    msg = Mock()
    msg.get.return_value = "test@example.com"
    msg.walk.return_value = []
    
    return msg
'''

if __name__ == "__main__":
    # Save pytest.ini
    with open('pytest.ini', 'w') as f:
        f.write(PYTEST_INI)
    print("Created pytest.ini")
    
    # Save conftest.py
    with open('tests/conftest.py', 'w') as f:
        f.write(CONFTEST_PY)
    print("Created tests/conftest.py")
    
    # Run tests
    pytest.main(['-v'])