#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Providers Module

Pre-configured settings for common email providers.
"""

from typing import Dict, List, Optional


class EmailProviders:
    """
    Email provider configurations and helper methods.
    """
    
    # Known email provider configurations
    PROVIDERS = {
        'gmail': {
            'name': 'Gmail',
            'server': 'imap.gmail.com',
            'port': 993,
            'use_ssl': True,
            'notes': 'Requires app-specific password. Enable 2FA and generate app password.',
            'help_url': 'https://support.google.com/mail/answer/185833'
        },
        'outlook': {
            'name': 'Outlook/Office 365',
            'server': 'outlook.office365.com',
            'port': 993,
            'use_ssl': True,
            'notes': 'May require app password if 2FA is enabled.',
            'help_url': 'https://support.microsoft.com/en-us/account-billing/using-app-passwords-with-apps-that-don-t-support-two-step-verification-5896ed9b-4263-e681-128a-a6f2979a7944'
        },
        'icloud': {
            'name': 'iCloud',
            'server': 'imap.mail.me.com',
            'port': 993,
            'use_ssl': True,
            'notes': 'Requires app-specific password. Generate from Apple ID settings.',
            'help_url': 'https://support.apple.com/en-us/HT204397',
            'special_handling': True
        },
        'yahoo': {
            'name': 'Yahoo Mail',
            'server': 'imap.mail.yahoo.com',
            'port': 993,
            'use_ssl': True,
            'notes': 'May require app password. Enable in Account Security settings.',
            'help_url': 'https://help.yahoo.com/kb/SLN15241.html'
        },
        'gmx': {
            'name': 'GMX',
            'server': 'imap.gmx.net',
            'port': 993,
            'use_ssl': True,
            'notes': 'Enable IMAP access in email settings.'
        },
        'web.de': {
            'name': 'Web.de',
            'server': 'imap.web.de',
            'port': 993,
            'use_ssl': True,
            'notes': 'Enable IMAP access in email settings.'
        },
        'aol': {
            'name': 'AOL',
            'server': 'imap.aol.com',
            'port': 993,
            'use_ssl': True,
            'notes': 'May require app password.'
        },
        'mail.com': {
            'name': 'Mail.com',
            'server': 'imap.mail.com',
            'port': 993,
            'use_ssl': True,
            'notes': 'Enable IMAP in settings.'
        },
        'zoho': {
            'name': 'Zoho Mail',
            'server': 'imap.zoho.com',
            'port': 993,
            'use_ssl': True,
            'notes': 'Enable IMAP access and may need app-specific password.'
        },
        'protonmail': {
            'name': 'ProtonMail',
            'server': '127.0.0.1',
            'port': 1143,
            'use_ssl': False,
            'notes': 'Requires ProtonMail Bridge application running locally.',
            'help_url': 'https://protonmail.com/bridge'
        },
        'fastmail': {
            'name': 'FastMail',
            'server': 'imap.fastmail.com',
            'port': 993,
            'use_ssl': True,
            'notes': 'Supports app passwords for better security.'
        },
        'mailbox.org': {
            'name': 'Mailbox.org',
            'server': 'imap.mailbox.org',
            'port': 993,
            'use_ssl': True,
            'notes': 'Privacy-focused email provider.'
        },
        'yandex': {
            'name': 'Yandex Mail',
            'server': 'imap.yandex.com',
            'port': 993,
            'use_ssl': True,
            'notes': 'Enable IMAP in settings. May need app password.'
        },
        'exchange': {
            'name': 'Exchange Server (Generic)',
            'server': None,  # User must provide
            'port': 993,
            'use_ssl': True,
            'notes': 'Contact your IT administrator for server details.'
        }
    }
    
    @classmethod
    def get_provider_config(cls, provider_name: str) -> Optional[Dict]:
        """
        Get configuration for a specific provider.
        
        Args:
            provider_name: Name of the provider (case-insensitive)
            
        Returns:
            Provider configuration dictionary or None if not found
        """
        # Try exact match first
        provider_lower = provider_name.lower()
        if provider_lower in cls.PROVIDERS:
            config = cls.PROVIDERS[provider_lower].copy()
            # Remove metadata fields not needed for connection
            config.pop('name', None)
            config.pop('notes', None)
            config.pop('help_url', None)
            config.pop('special_handling', None)
            return config
        
        # Try to find by provider display name
        for key, provider in cls.PROVIDERS.items():
            if provider['name'].lower() == provider_lower:
                config = provider.copy()
                config.pop('name', None)
                config.pop('notes', None)
                config.pop('help_url', None)
                config.pop('special_handling', None)
                return config
        
        return None
    
    @classmethod
    def get_provider_list(cls) -> List[str]:
        """
        Get list of available provider names.
        
        Returns:
            List of provider display names
        """
        return [provider['name'] for provider in cls.PROVIDERS.values()]
    
    @classmethod
    def is_provider_supported(cls, server: str) -> bool:
        """
        Check if a server is a known provider.
        
        Args:
            server: IMAP server address
            
        Returns:
            True if server is known
        """
        for provider in cls.PROVIDERS.values():
            if provider.get('server') == server:
                return True
        return False
    
    @classmethod
    def get_provider_notes(cls, provider_name: str) -> Optional[str]:
        """
        Get setup notes for a provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Setup notes or None
        """
        provider_lower = provider_name.lower()
        if provider_lower in cls.PROVIDERS:
            return cls.PROVIDERS[provider_lower].get('notes')
        return None
    
    @classmethod
    def get_provider_help_url(cls, provider_name: str) -> Optional[str]:
        """
        Get help URL for a provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Help URL or None
        """
        provider_lower = provider_name.lower()
        if provider_lower in cls.PROVIDERS:
            return cls.PROVIDERS[provider_lower].get('help_url')
        return None
    
    @classmethod
    def needs_special_handling(cls, server: str) -> bool:
        """
        Check if a server needs special handling.
        
        Args:
            server: IMAP server address
            
        Returns:
            True if special handling is needed
        """
        for provider in cls.PROVIDERS.values():
            if provider.get('server') == server:
                return provider.get('special_handling', False)
        return False
    
    @classmethod
    def detect_provider_from_email(cls, email: str) -> Optional[str]:
        """
        Try to detect provider from email address.
        
        Args:
            email: Email address
            
        Returns:
            Provider name or None
        """
        if not email or '@' not in email:
            return None
        
        domain = email.split('@')[1].lower()
        
        # Common domain mappings
        domain_mappings = {
            'gmail.com': 'gmail',
            'googlemail.com': 'gmail',
            'outlook.com': 'outlook',
            'hotmail.com': 'outlook',
            'live.com': 'outlook',
            'msn.com': 'outlook',
            'icloud.com': 'icloud',
            'me.com': 'icloud',
            'mac.com': 'icloud',
            'yahoo.com': 'yahoo',
            'yahoo.co.uk': 'yahoo',
            'yahoo.fr': 'yahoo',
            'yahoo.de': 'yahoo',
            'gmx.net': 'gmx',
            'gmx.de': 'gmx',
            'gmx.com': 'gmx',
            'web.de': 'web.de',
            'aol.com': 'aol',
            'mail.com': 'mail.com',
            'zoho.com': 'zoho',
            'protonmail.com': 'protonmail',
            'proton.me': 'protonmail',
            'pm.me': 'protonmail',
            'fastmail.com': 'fastmail',
            'fastmail.fm': 'fastmail',
            'mailbox.org': 'mailbox.org',
            'yandex.com': 'yandex',
            'yandex.ru': 'yandex'
        }
        
        return domain_mappings.get(domain)
    
    @classmethod
    def print_provider_info(cls, provider_name: str):
        """
        Print detailed information about a provider.
        
        Args:
            provider_name: Name of the provider
        """
        provider_lower = provider_name.lower()
        if provider_lower not in cls.PROVIDERS:
            print(f"Provider '{provider_name}' not found")
            return
        
        provider = cls.PROVIDERS[provider_lower]
        print(f"\n{provider['name']} Configuration:")
        print("-" * 40)
        print(f"Server: {provider.get('server', 'User must provide')}")
        print(f"Port: {provider['port']}")
        print(f"SSL: {'Yes' if provider['use_ssl'] else 'No'}")
        
        if provider.get('notes'):
            print(f"\nNotes: {provider['notes']}")
        
        if provider.get('help_url'):
            print(f"Help: {provider['help_url']}")


def get_provider_config(provider_name: str) -> Optional[Dict]:
    """
    Convenience function to get provider configuration.
    
    Args:
        provider_name: Name of the provider
        
    Returns:
        Provider configuration or None
    """
    return EmailProviders.get_provider_config(provider_name)


def detect_provider(email: str) -> Optional[str]:
    """
    Convenience function to detect provider from email.
    
    Args:
        email: Email address
        
    Returns:
        Provider name or None
    """
    return EmailProviders.detect_provider_from_email(email)