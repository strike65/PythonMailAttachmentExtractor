#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Argument Parser Module

Command-line argument parsing for the email attachment extractor.
"""

import argparse
from typing import Optional


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog='email-attachment-extractor',
        description='Cross-Platform Email Attachment Extractor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  %(prog)s
  
  # Use configuration file
  %(prog)s --config config.json
  
  # Command-line with specific options
  %(prog)s --server imap.gmail.com --username user@gmail.com --file-types pdf docx
  
  # Recursive processing with limits
  %(prog)s --config config.json --recursive --limit-per-folder 100
  
  # Extract only images, organize by date
  %(prog)s --config config.json --file-types jpg png gif --organize-by-date
        """
    )
    
    # Configuration file (primary option)
    parser.add_argument(
        '--config', '-c',
        metavar='FILE',
        help='Path to JSON configuration file'
    )
    
    # Connection settings
    connection_group = parser.add_argument_group('Connection Settings')
    connection_group.add_argument(
        '--server',
        help='IMAP server address (e.g., imap.gmail.com)'
    )
    connection_group.add_argument(
        '--port',
        type=int,
        help='IMAP port (default: 993 for SSL)'
    )
    connection_group.add_argument(
        '--username',
        help='Email address or username'
    )
    connection_group.add_argument(
        '--password',
        help='Password (will prompt if not provided)'
    )
    connection_group.add_argument(
        '--no-ssl',
        action='store_false',
        dest='use_ssl',
        help='Disable SSL/TLS connection'
    )
    
    # Mailbox settings
    mailbox_group = parser.add_argument_group('Mailbox Settings')
    mailbox_group.add_argument(
        '--mailbox',
        help='Mailbox/folder to process (default: INBOX)'
    )
    mailbox_group.add_argument(
        '--search',
        dest='search_criteria',
        help='IMAP search criteria (default: ALL)'
    )
    mailbox_group.add_argument(
        '--recursive',
        action='store_true',
        help='Process all INBOX subfolders recursively'
    )
    
    # Output settings
    output_group = parser.add_argument_group('Output Settings')
    output_group.add_argument(
        '--save-path',
        help='Directory to save attachments'
    )
    output_group.add_argument(
        '--organize-by-sender',
        action='store_true',
        help='Create folders organized by sender email'
    )
    output_group.add_argument(
        '--organize-by-date',
        action='store_true',
        help='Create folders organized by date'
    )
    output_group.add_argument(
        '--no-metadata',
        action='store_true',
        help='Do not save metadata JSON files'
    )
    
    # Processing limits
    limit_group = parser.add_argument_group('Processing Limits')
    limit_group.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Maximum number of emails to process'
    )
    limit_group.add_argument(
        '--limit-per-folder',
        type=int,
        metavar='N',
        help='Maximum emails per folder (for recursive mode)'
    )
    limit_group.add_argument(
        '--total-limit',
        type=int,
        metavar='N',
        help='Total limit across all folders (for recursive mode)'
    )
    
    # File filtering
    filter_group = parser.add_argument_group('File Filtering')
    filter_group.add_argument(
        '--file-types', '--extensions',
        nargs='+',
        dest='file_types',
        metavar='PATTERN',
        help='Allowed file extensions/patterns (e.g., pdf "*.doc*" "report_*.pdf")'
    )
    filter_group.add_argument(
        '--exclude-types',
        nargs='+',
        dest='exclude_types',
        metavar='PATTERN',
        help='Excluded file extensions/patterns (e.g., exe bat "*.tmp")'
    )
    
    # Verbosity and debugging
    debug_group = parser.add_argument_group('Debug Options')
    debug_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    debug_group.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with detailed IMAP output'
    )
    debug_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Test run without saving attachments'
    )
    
    # Help and version
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 2.0.0'
    )
    
    return parser


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = create_parser()
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> bool:
    """
    Validate parsed arguments.
    
    Args:
        args: Parsed arguments
        
    Returns:
        True if valid, False otherwise
    """
    # If config file is provided, most validation will happen there
    if args.config:
        return True
    
    # If no config, we need at least server and username
    if not args.server or not args.username:
        if not any([args.server, args.username, args.save_path]):
            # No arguments provided at all - likely interactive mode
            return True
        else:
            # Partial arguments provided
            print("Error: When not using --config, both --server and --username are required")
            return False
    
    return True