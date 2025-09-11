#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Setup Module

Provides interactive configuration setup for the email attachment extractor.
"""

import getpass
from typing import Dict, Optional, List
import os

from ..utils.colors import Colors
from ..providers.email_providers import EmailProviders


def interactive_setup() -> Optional[Dict]:
    """
    Run interactive setup wizard.
    
    Returns:
        Configuration dictionary or None if cancelled
    """
    print("\n" + "="*60)
    print(Colors.info("EMAIL ATTACHMENT EXTRACTOR - INTERACTIVE SETUP"))
    print("="*60)
    
    config = {}
    
    # Select email provider
    provider_config = select_email_provider()
    if not provider_config:
        return None
    
    config.update(provider_config)
    
    # Get credentials
    credentials = get_credentials_interactive()
    if not credentials:
        return None
    
    config.update(credentials)
    
    # Get processing options
    options = get_processing_options()
    config.update(options)
    
    # Get file filtering options
    filters = get_file_filters()
    config.update(filters)
    
    return config


def select_email_provider() -> Optional[Dict]:
    """
    Interactively select email provider.
    
    Returns:
        Provider configuration or None if cancelled
    """
    print(Colors.info("\nSelect your email provider:"))
    print("-" * 40)
    
    providers = EmailProviders.get_provider_list()
    providers.append('Other (Custom IMAP)')
    
    for idx, provider in enumerate(providers, 1):
        print(f"{idx}. {provider}")
    
    while True:
        try:
            choice = input(Colors.cyan(f"\nSelect provider (1-{len(providers)}) or 'q' to quit: ")).strip()
            
            if choice.lower() == 'q':
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(providers):
                selected = providers[idx]
                break
                
            print(Colors.error("Invalid selection"))
            
        except ValueError:
            print(Colors.error("Please enter a number"))
    
    # Get provider configuration
    if selected == 'Other (Custom IMAP)':
        return get_custom_server_config()
    else:
        config = EmailProviders.get_provider_config(selected)
        if config:
            print(Colors.success(f"\nServer settings loaded for {selected}"))
            return config
        else:
            print(Colors.error(f"Error loading settings for {selected}"))
            return None


def get_custom_server_config() -> Dict:
    """
    Get custom IMAP server configuration.
    
    Returns:
        Server configuration dictionary
    """
    print(Colors.info("\nCustom IMAP Server Configuration:"))
    print("-" * 40)
    
    config = {}
    
    # Server address
    while True:
        server = input(Colors.cyan("IMAP server address: ")).strip()
        if server:
            config['server'] = server
            break
        print(Colors.error("Server address is required"))
    
    # Port
    port_str = input(Colors.cyan("Port (default 993 for SSL): ")).strip()
    config['port'] = int(port_str) if port_str else 993
    
    # SSL
    use_ssl = input(Colors.cyan("Use SSL/TLS? (y/n, default y): ")).strip().lower()
    config['use_ssl'] = use_ssl != 'n'
    
    return config


def get_credentials_interactive() -> Optional[Dict]:
    """
    Get email credentials interactively.
    
    Returns:
        Credentials dictionary or None if cancelled
    """
    print(Colors.info("\nLogin Credentials:"))
    print("-" * 40)
    
    credentials = {}
    
    # Username
    while True:
        username = input(Colors.cyan("Email address/username: ")).strip()
        if username:
            credentials['username'] = username
            break
        print(Colors.error("Username is required"))
    
    # Password
    password = getpass.getpass(Colors.cyan("Password: "))
    if not password:
        print(Colors.warning("No password provided"))
        confirm = input(Colors.cyan("Continue without password? (y/n): ")).strip().lower()
        if confirm != 'y':
            return None
    else:
        credentials['password'] = password
    
    return credentials


def get_processing_options() -> Dict:
    """
    Get email processing options interactively.
    
    Returns:
        Processing options dictionary
    """
    print(Colors.info("\nProcessing Options:"))
    print("-" * 40)
    
    options = {}
    
    # Mailbox
    mailbox = input(Colors.cyan("Mailbox to process (default: INBOX): ")).strip()
    options['mailbox'] = mailbox if mailbox else 'INBOX'
    
    # Search criteria
    print("\nCommon search criteria:")
    print("  ALL         - All messages (default)")
    print("  UNSEEN      - Unread messages only")
    print("  SINCE date  - Messages since date (e.g., SINCE 01-Jan-2024)")
    print("  FROM email  - Messages from specific sender")
    
    criteria = input(Colors.cyan("Search criteria (default: ALL): ")).strip()
    options['search_criteria'] = criteria if criteria else 'ALL'
    
    # Organization
    organize_sender = input(Colors.cyan("Organize by sender? (y/n, default n): ")).strip().lower()
    options['organize_by_sender'] = organize_sender == 'y'
    
    organize_date = input(Colors.cyan("Organize by date? (y/n, default y): ")).strip().lower()
    options['organize_by_date'] = organize_date != 'n'
    
    # Limits
    limit_str = input(Colors.cyan("Maximum emails to process (Enter for no limit): ")).strip()
    if limit_str:
        try:
            options['limit'] = int(limit_str)
        except ValueError:
            print(Colors.warning("Invalid limit, ignoring"))
    
    # Recursive
    recursive = input(Colors.cyan("Process all INBOX subfolders? (y/n, default n): ")).strip().lower()
    options['recursive'] = recursive == 'y'
    
    # Metadata
    save_meta = input(Colors.cyan("Save metadata JSON? (y/n, default y): ")).strip().lower()
    options['save_metadata'] = save_meta != 'n'
    
    return options


def get_file_filters() -> Dict:
    """
    Get file filtering options interactively.
    
    Returns:
        File filter configuration
    """
    print(Colors.info("\nFile Filtering Options:"))
    print("-" * 40)
    
    filters = {}
    
    print("\nYou can use patterns like:")
    print("  pdf          - PDF files")
    print("  *.doc*       - All Word documents")
    print("  report_*.pdf - PDFs starting with 'report_'")
    print("  *            - All files")
    
    # Allowed extensions
    allowed = input(Colors.cyan("Allowed file patterns (space-separated, Enter for all): ")).strip()
    if allowed:
        filters['allowed_extensions'] = allowed.split()
    else:
        filters['allowed_extensions'] = None
    
    # Excluded extensions
    excluded = input(Colors.cyan("Excluded file patterns (space-separated, Enter for none): ")).strip()
    if excluded:
        filters['excluded_extensions'] = excluded.split()
    else:
        filters['excluded_extensions'] = None
    
    return filters


def select_mailbox_interactive(mailboxes: List[str]) -> Optional[str]:
    """
    Interactively select a mailbox from list.
    
    Args:
        mailboxes: List of available mailboxes
        
    Returns:
        Selected mailbox name or None
    """
    if not mailboxes:
        print(Colors.warning("No mailboxes available"))
        return None
    
    print(Colors.info("\nAvailable mailboxes:"))
    print("-" * 40)
    
    for idx, mailbox in enumerate(mailboxes, 1):
        print(f"{idx}. {mailbox}")
    
    choice = input(Colors.cyan(f"\nSelect mailbox (1-{len(mailboxes)}, Enter for INBOX): ")).strip()
    
    if not choice:
        return 'INBOX'
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(mailboxes):
            return mailboxes[idx]
    except ValueError:
        pass
    
    print(Colors.warning("Invalid selection, using INBOX"))
    return 'INBOX'


def confirm_settings(config: Dict) -> bool:
    """
    Display settings and get confirmation.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if confirmed, False otherwise
    """
    print(Colors.info("\nConfiguration Summary:"))
    print("="*60)
    
    # Connection settings
    print(Colors.bold("Connection:"))
    print(f"  Server: {config.get('server', 'Not set')}")
    print(f"  Port: {config.get('port', 993)}")
    print(f"  SSL: {'Yes' if config.get('use_ssl', True) else 'No'}")
    print(f"  Username: {config.get('username', 'Not set')}")
    print(f"  Password: {'***Set***' if config.get('password') else 'Not set'}")
    
    # Processing settings
    print(Colors.bold("\nProcessing:"))
    print(f"  Mailbox: {config.get('mailbox', 'INBOX')}")
    print(f"  Search: {config.get('search_criteria', 'ALL')}")
    print(f"  Organize by sender: {'Yes' if config.get('organize_by_sender') else 'No'}")
    print(f"  Organize by date: {'Yes' if config.get('organize_by_date') else 'No'}")
    print(f"  Recursive: {'Yes' if config.get('recursive') else 'No'}")
    
    # Filtering
    if config.get('allowed_extensions'):
        print(f"  Allowed patterns: {', '.join(config['allowed_extensions'])}")
    if config.get('excluded_extensions'):
        print(f"  Excluded patterns: {', '.join(config['excluded_extensions'])}")
    
    print("="*60)
    
    confirm = input(Colors.cyan("\nProceed with these settings? (y/n): ")).strip().lower()
    return confirm == 'y'


def get_save_path_interactive() -> Optional[str]:
    """
    Get save path interactively.
    
    Returns:
        Save path or None if cancelled
    """
    print(Colors.info("\nWhere to save attachments:"))
    print("-" * 40)
    print("1. Current directory")
    print("2. Select drive/volume")
    print("3. Enter custom path")
    
    choice = input(Colors.cyan("Select option (1-3): ")).strip()
    
    if choice == '1':
        from datetime import datetime
        dirname = f"email_attachments_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return os.path.join(os.getcwd(), dirname)
        
    elif choice == '2':
        from ..utils.filesystem import get_available_drives
        return get_available_drives()
        
    elif choice == '3':
        path = input(Colors.cyan("Enter path: ")).strip()
        if path:
            return os.path.expanduser(path)
    
    return None