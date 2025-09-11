#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Attachment Extractor - Main Extractor Class

This module contains the main EmailAttachmentExtractor class that handles
IMAP connections, mailbox navigation, and orchestrates the extraction process.
"""

import imaplib
# imaplib.Debug = 4
import ssl
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from ..utils.colors import Colors, ProgressIndicator
from ..utils.filesystem import create_directory
from .email_processor import EmailProcessor
from .pattern_matcher import PatternMatcher


class EmailAttachmentExtractor:
    """
    Main class for extracting email attachments via IMAP.
    
    Handles connection management, mailbox selection, and orchestrates
    the email processing workflow.
    """
    
    def __init__(
        self,
        server: str,
        port: int,
        username: str,
        password: str,
        use_ssl: bool = True
    ):
        """
        Initialize the EmailAttachmentExtractor.
        
        Args:
            server: IMAP server address
            port: IMAP server port
            username: Email username/address
            password: Email password
            use_ssl: Whether to use SSL/TLS connection
        """
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.imap: Optional[imaplib.IMAP4] = None
        
        # Initialize processors
        self.email_processor = EmailProcessor()
        self.pattern_matcher = PatternMatcher()
        
        # Statistics tracking
        self.statistics = {
            'emails_processed': 0,
            'attachments_saved': 0,
            'total_size_mb': 0.0,
            'errors': []
        }
        
    def connect(self) -> bool:
        """
        Establish connection to the IMAP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                self.imap = imaplib.IMAP4_SSL(
                    self.server, 
                    self.port, 
                    ssl_context=context
                )
            else:
                self.imap = imaplib.IMAP4(self.server, self.port)
                
            self.imap.login(self.username, self.password)
            print(Colors.success(f"Successfully connected to {self.server}"))
            return True
            
        except imaplib.IMAP4.error as e:
            print(Colors.error(f"IMAP error: {e}"))
            return False
        except Exception as e:
            print(Colors.error(f"Connection error: {e}"))
            return False
    
    def disconnect(self):
        """Close the IMAP connection."""
        if self.imap:
            try:
                self.imap.logout()
                print(Colors.success("Connection closed"))
            except Exception:
                pass
    
    def get_mailboxes(self) -> List[str]:
        """
        Get list of available mailboxes/folders.
        
        Returns:
            List of mailbox names
        """
        try:
            status, mailboxes = self.imap.list()
            if status != 'OK' or not mailboxes:
                return []
            
            folders: List[str] = []
            for raw in mailboxes:
                if raw is None:
                    continue
                    
                # Parse IMAP LIST response
                folder_name = self._parse_mailbox_name(raw)
                if folder_name:
                    folders.append(folder_name)
                    
            return folders
            
        except Exception as e:
            print(Colors.error(f"Error fetching mailboxes: {e}"))
            return []
    
    def select_mailbox(self, mailbox: str = 'INBOX') -> bool:
        """
        Select a mailbox for processing.
        
        Args:
            mailbox: Name of the mailbox to select
            
        Returns:
            True if selection successful, False otherwise
        """
        try:
            # Special handling for iCloud
            if 'imap.mail.me.com' in self.server:
                status, _ = self.imap.select(mailbox, readonly=False)
            else:
                status, _ = self.imap.select(mailbox, readonly=True)
                
            if status == 'OK':
                print(Colors.success(f"Mailbox '{mailbox}' selected"))
                return True
                
            print(Colors.error(f"Could not select mailbox '{mailbox}'"))
            return False
            
        except Exception as e:
            print(Colors.error(f"Error selecting mailbox: {e}"))
            return False
    
    def search_emails(
        self, 
        search_criteria: str = 'ALL', 
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Search for emails matching criteria.
        
        Args:
            search_criteria: IMAP search criteria
            limit: Maximum number of emails to return
            
        Returns:
            List of email IDs
        """
        try:
            status, data = self.imap.search(None, search_criteria)
            if status != 'OK' or not data or not data[0]:
                return []
                
            raw_ids = data[0].split()
            ids = [i.decode('ascii', errors='ignore') for i in raw_ids if i]
            
            if limit is not None:
                ids = ids[:max(0, int(limit))]
                
            return ids
            
        except Exception as e:
            print(Colors.error(f"Error searching emails: {e}"))
            return []
    
    def process_emails(
        self,
        save_path: str,
        search_criteria: str = 'ALL',
        organize_by_sender: bool = False,
        organize_by_date: bool = False,
        limit: Optional[int] = None,
        save_metadata: bool = True,
        allowed_extensions: Optional[List[str]] = None,
        excluded_extensions: Optional[List[str]] = None
    ) -> Dict:
        """
        Process emails and extract attachments.
        
        Args:
            save_path: Directory to save attachments
            search_criteria: IMAP search criteria
            organize_by_sender: Create folders by sender
            organize_by_date: Create folders by date
            limit: Maximum number of emails to process
            save_metadata: Whether to save metadata JSON
            allowed_extensions: List of allowed file patterns
            excluded_extensions: List of excluded file patterns
            
        Returns:
            Statistics dictionary
        """
        # Create save directory
        create_directory(save_path)
        
        print(Colors.info(f"\nSearching emails with criteria: {search_criteria}"))
        email_ids = self.search_emails(search_criteria, limit)
        
        if not email_ids:
            print(Colors.warning("No emails found"))
            return self.statistics
        
        print(Colors.info(f"{len(email_ids)} email(s) found"))
        
        all_attachments: List[Dict] = []
        
        for idx, eid in enumerate(email_ids, 1):
            try:
                print(Colors.info(f"\nProcessing email {idx}/{len(email_ids)} (ID {eid})..."))
                
                # Fetch email
                raw_email = self._fetch_email(eid)
                if not raw_email:
                    continue
                
                # Parse and process email
                msg = self.email_processor.parse_email(raw_email, self.server)
                
                # Extract attachments
                attachments = self.email_processor.extract_attachments(
                    email_id=eid,
                    msg=msg,
                    save_path=save_path,
                    organize_by_sender=organize_by_sender,
                    organize_by_date=organize_by_date,
                    allowed_extensions=allowed_extensions,
                    excluded_extensions=excluded_extensions,
                    pattern_matcher=self.pattern_matcher
                )
                
                all_attachments.extend(attachments)
                self.statistics['emails_processed'] += 1
                self.statistics['attachments_saved'] += len(attachments)
                self.statistics['total_size_mb'] += sum(a['size_mb'] for a in attachments)
                
            except Exception as e:
                err = f"Error processing email {eid}: {e}"
                print(Colors.error(err))
                self.statistics['errors'].append(err)
        
        # Save metadata if requested
        if save_metadata and all_attachments:
            self._save_metadata(save_path, all_attachments)
        
        return self.statistics
    
    def process_all_inbox_folders(
        self,
        save_path: str,
        search_criteria: str = 'ALL',
        organize_by_sender: bool = False,
        organize_by_date: bool = False,
        limit_per_folder: Optional[int] = None,
        total_limit: Optional[int] = None,
        save_metadata: bool = True,
        allowed_extensions: Optional[List[str]] = None,
        excluded_extensions: Optional[List[str]] = None
    ) -> Dict:
        """
        Process INBOX and all subfolders recursively.
        
        Args:
            save_path: Directory to save attachments
            search_criteria: IMAP search criteria
            organize_by_sender: Create folders by sender
            organize_by_date: Create folders by date
            limit_per_folder: Max emails per folder
            total_limit: Total limit across all folders
            save_metadata: Whether to save metadata
            allowed_extensions: Allowed file patterns
            excluded_extensions: Excluded file patterns
            
        Returns:
            Statistics dictionary
        """
        # Get all INBOX folders
        all_mailboxes = self.get_mailboxes()
        inbox_folders = self._filter_inbox_folders(all_mailboxes)
        
        print(Colors.info(f"\nFound {len(inbox_folders)} INBOX folder(s):"))
        for folder in inbox_folders:
            print(f"   - {folder}")
        
        processed_count = 0
        
        for folder in inbox_folders:
            if total_limit and processed_count >= total_limit:
                print(Colors.warning(f"\nTotal limit of {total_limit} emails reached"))
                break
            
            # Calculate effective limit for this folder
            effective_limit = self._calculate_effective_limit(
                limit_per_folder, 
                total_limit, 
                processed_count
            )
            
            # Process folder
            processed_count = self._process_mailbox(
                mailbox=folder,
                save_path=save_path,
                search_criteria=search_criteria,
                organize_by_sender=organize_by_sender,
                organize_by_date=organize_by_date,
                limit=effective_limit,
                save_metadata=save_metadata,
                processed_count=processed_count,
                allowed_extensions=allowed_extensions,
                excluded_extensions=excluded_extensions
            )
        
        # Save overall metadata
        if save_metadata:
            self._save_total_metadata(save_path, inbox_folders)
        
        return self.statistics
    
    # ========== Private Helper Methods ==========
    
    def _parse_mailbox_name(self, raw: bytes) -> Optional[str]:
        """Parse mailbox name from IMAP LIST response."""
        try:
            line = raw.decode(errors='replace')
            # Parse format: (flags) "delimiter" mailbox_name
            import re
            match = re.match(r'\([^)]*\)\s+"[^"]*"\s+(.+)', line)
            if match:
                return match.group(1).strip('"')
            return None
        except Exception:
            return None
    
    def _fetch_email(self, email_id: str) -> Optional[bytes]:
        """Fetch raw email data."""
        try:
            # Special handling for iCloud
            if 'imap.mail.me.com' in self.server:
                status, data = self.imap.fetch(email_id, '(BODY[])')
            else:
                status, data = self.imap.fetch(email_id, '(RFC822)')
            
            if status != 'OK' or not data:
                return None
            
            # Extract raw email from response
            for item in data:
                if isinstance(item, tuple) and len(item) >= 2:
                    if isinstance(item[1], (bytes, bytearray)):
                        return item[1]
                elif isinstance(item, bytes):
                    return item
                    
            return None
            
        except Exception as e:
            print(Colors.error(f"Error fetching email {email_id}: {e}"))
            return None
    
    def _filter_inbox_folders(self, mailboxes: List[str]) -> List[str]:
        """Filter for INBOX and subfolders."""
        inbox_folders = ['INBOX']
        for mb in mailboxes:
            if mb.startswith('INBOX/') and mb not in inbox_folders:
                inbox_folders.append(mb)
        return inbox_folders
    
    def _calculate_effective_limit(
        self, 
        limit_per_folder: Optional[int],
        total_limit: Optional[int],
        processed_count: int
    ) -> Optional[int]:
        """Calculate effective limit for current folder."""
        if total_limit and processed_count < total_limit:
            remaining = total_limit - processed_count
            if limit_per_folder:
                return min(limit_per_folder, remaining)
            return remaining
        return limit_per_folder
    
    def _process_mailbox(
        self,
        mailbox: str,
        save_path: str,
        processed_count: int,
        **kwargs
    ) -> int:
        """Process a single mailbox and return updated count."""
        print(Colors.info(f"\nProcessing mailbox: {mailbox}"))
        print("-" * 40)
        
        if not self.select_mailbox(mailbox):
            print(Colors.warning(f"Skipping {mailbox} - could not select"))
            return processed_count
        
        # Clean mailbox name for filesystem
        mailbox_clean = mailbox.replace('/', '_').replace('\\', '_').replace(':', '_')
        mailbox_save_path = os.path.join(save_path, mailbox_clean)
        
        # Process emails in this mailbox
        stats = self.process_emails(
            save_path=mailbox_save_path,
            **kwargs
        )
        
        return processed_count + stats.get('emails_processed', 0)
    
    def _save_metadata(self, save_path: str, attachments: List[Dict]):
        """Save metadata to JSON file."""
        metadata_file = os.path.join(save_path, 'attachments_metadata.json')
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'extraction_date': datetime.now().isoformat(),
                    'statistics': self.statistics,
                    'attachments': attachments
                }, f, ensure_ascii=False, indent=2)
            print(Colors.success(f"\nMetadata saved to: {metadata_file}"))
        except Exception as e:
            print(Colors.error(f"Error saving metadata: {e}"))
    
    def _save_total_metadata(self, save_path: str, folders: List[str]):
        """Save total metadata for all processed folders."""
        metadata_file = os.path.join(save_path, 'attachments_metadata_total.json')
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'extraction_date': datetime.now().isoformat(),
                    'processed_folders': folders,
                    'statistics': self.statistics
                }, f, ensure_ascii=False, indent=2)
            print(Colors.success(f"\nTotal metadata saved to: {metadata_file}"))
        except Exception as e:
            print(Colors.error(f"Error saving total metadata: {e}"))
    
    def print_statistics(self):
        """Print extraction statistics."""
        print("\n" + "="*60)
        print(Colors.success("PROCESSING COMPLETED"))
        print("="*60)
        print(Colors.info(f"Emails processed: {self.statistics['emails_processed']}"))
        print(Colors.info(f"Attachments saved: {self.statistics['attachments_saved']}"))
        print(Colors.info(f"Total size: {self.statistics['total_size_mb']:.2f} MB"))
        
        if self.statistics['errors']:
            print(Colors.warning(f"\n{len(self.statistics['errors'])} error(s) occurred:"))
            for err in self.statistics['errors'][:5]:
                print(Colors.error(f"   - {err}"))
            if len(self.statistics['errors']) > 5:
                print(Colors.warning(f"   ... and {len(self.statistics['errors']) - 5} more"))