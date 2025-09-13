#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Processor Module

Handles email parsing, attachment extraction, and email metadata processing.
"""

import email
from email import policy
from email.header import decode_header
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import email.utils

from ..utils.colors import Colors
from ..utils.debug import dprint
from ..utils.filesystem import sanitize_filename, get_unique_filename, create_directory
from .pattern_matcher import PatternMatcher


class EmailProcessor:
    """
    Processes email messages and extracts attachments.
    
    Handles email parsing, MIME decoding, attachment extraction,
    and organization of saved files.
    """
    
    def __init__(self):
        """Initialize the EmailProcessor."""
        self.current_email_info = {}
        
    def parse_email(self, raw_email: bytes, server: str = "") -> email.message.Message:
        """
        Parse raw email bytes into a Message object.
        
        Args:
            raw_email: Raw email data as bytes
            server: Server name for special handling (e.g., iCloud)
            
        Returns:
            Parsed email Message object
        """
        # Special handling for iCloud
        if 'imap.mail.me.com' in server:
            try:
                # Try UTF-8 first
                msg = email.message_from_bytes(raw_email)
            except:
                # Fallback to Latin-1
                msg = email.message_from_string(
                    raw_email.decode('latin-1', errors='replace')
                )
        else:
            # Standard parsing with policy
            msg = email.message_from_bytes(raw_email, policy=policy.default)
            
        return msg
    
    def extract_attachments(
        self,
        email_id: str,
        msg: email.message.Message,
        save_path: str,
        organize_by_sender: bool = False,
        organize_by_date: bool = False,
        allowed_extensions: Optional[List[str]] = None,
        excluded_extensions: Optional[List[str]] = None,
        pattern_matcher: Optional[PatternMatcher] = None
    ) -> List[Dict]:
        """
        Extract and save attachments from an email message.
        
        Behavior:
        - Filenames are sanitized before matching and saving.
        - A numeric prefix (01_, 02_, ...) is added to preserve order.
        - Existing files are not overwritten; a unique name is chosen.
        - Allowed/excluded patterns are applied via PatternMatcher.
        
        Args:
            email_id: Unique identifier for the email (for metadata)
            msg: Parsed email message
            save_path: Base directory to save attachments
            organize_by_sender: Create subdirectories by sender
            organize_by_date: Create subdirectories by date
            allowed_extensions: List of allowed file patterns
            excluded_extensions: List of excluded file patterns
            pattern_matcher: PatternMatcher instance for filtering
            
        Returns:
            List of dictionaries containing attachment information
        """
        if pattern_matcher is None:
            pattern_matcher = PatternMatcher()
            
        saved_attachments: List[Dict] = []
        
        # Extract email metadata
        email_info = self._extract_email_metadata(msg, email_id)
        self.current_email_info = email_info
        dprint(
            f"Email id={email_id} from='{email_info.get('sender_email','')}' subject='{email_info.get('subject','')[:80]}' date='{email_info.get('date_str','')}'",
            tag="MAIL",
        )
        
        # Prepare target directory structure
        target_dir = self._prepare_directory_structure(
            save_path,
            email_info,
            organize_by_sender,
            organize_by_date
        )
        dprint(f"Target directory: {target_dir}", tag="MAIL")
        
        # Collect attachments from email
        attachments_to_save = self._collect_attachments(
            msg,
            allowed_extensions,
            excluded_extensions,
            pattern_matcher
        )
        
        # Save attachments if any were found
        if attachments_to_save:
            create_directory(target_dir)
            
            for att_data in attachments_to_save:
                saved_info = self._save_attachment(
                    att_data,
                    target_dir,
                    email_info
                )
                if saved_info:
                    saved_attachments.append(saved_info)
        else:
            sender_short = email_info['sender_email'][:30]
            subject_short = email_info['subject'][:50]
            print(Colors.warning(
                f"  No attachments to save from {sender_short} - {subject_short}"
            ))
        dprint(f"Saved {len(saved_attachments)} attachment(s)", tag="MAIL")
        
        return saved_attachments
    
    def _extract_email_metadata(
        self, 
        msg: email.message.Message, 
        email_id: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from email message.
        
        Args:
            msg: Email message object
            email_id: Email identifier
            
        Returns:
            Dictionary containing email metadata
        """
        # Decode headers
        sender = self._decode_mime_string(msg.get('From', 'Unknown'))
        subject = self._decode_mime_string(msg.get('Subject', 'No Subject'))
        date_str = msg.get('Date', '')
        
        # Extract Message-ID
        message_id = self._extract_message_id(msg.get('Message-ID', ''), email_id)
        
        # Extract sender email
        sender_email = self._extract_sender_email(sender)
        
        # Parse date
        email_date = self._parse_email_date(date_str)
        date_for_filename = (email_date or datetime.now()).strftime('%Y-%m-%d')
        
        # Create email folder name
        subject_short = sanitize_filename(subject[:50])
        email_folder_name = f"{date_for_filename}_{message_id}_{subject_short}"
        
        return {
            'sender': sender,
            'sender_email': sender_email,
            'subject': subject,
            'date_str': date_str,
            'email_date': email_date,
            'date_for_filename': date_for_filename,
            'message_id': message_id,
            'email_id': email_id,
            'email_folder_name': email_folder_name
        }
    
    def _prepare_directory_structure(
        self,
        base_path: str,
        email_info: Dict,
        organize_by_sender: bool,
        organize_by_date: bool
    ) -> str:
        """
        Prepare the directory structure for saving attachments.
        
        Args:
            base_path: Base save directory
            email_info: Email metadata
            organize_by_sender: Whether to organize by sender
            organize_by_date: Whether to organize by date
            
        Returns:
            Full path to the target directory
        """
        target_dir = base_path
        
        if organize_by_sender:
            sender_dir = sanitize_filename(email_info['sender_email'])
            target_dir = os.path.join(target_dir, sender_dir)
        
        if organize_by_date:
            target_dir = os.path.join(target_dir, email_info['date_for_filename'])
        
        # Email-specific folder
        target_dir = os.path.join(target_dir, email_info['email_folder_name'])
        
        return target_dir
    
    def _collect_attachments(
        self,
        msg: email.message.Message,
        allowed_extensions: Optional[List[str]],
        excluded_extensions: Optional[List[str]],
        pattern_matcher: PatternMatcher
    ) -> List[Dict]:
        """
        Collect all attachments from email message.
        
        Args:
            msg: Email message object
            allowed_extensions: Allowed file patterns
            excluded_extensions: Excluded file patterns
            pattern_matcher: PatternMatcher instance
            
        Returns:
            List of attachment data dictionaries
        """
        attachments_to_save = []
        attachment_counter = 0
        
        # Debug output for patterns
        if allowed_extensions:
            print(Colors.info(f"  Allowed patterns: {allowed_extensions}"))
        if excluded_extensions:
            print(Colors.info(f"  Excluded patterns: {excluded_extensions}"))
        
        for part in msg.walk():
            # Check if this part is an attachment
            if not self._is_attachment(part):
                continue
            
            # Get filename
            filename = part.get_filename()
            original_filename = self._decode_mime_string(
                filename or f'attachment_{attachment_counter}'
            )
            sanitized_filename = sanitize_filename(original_filename)
            
            # Check if file should be included
            should_include, reason = pattern_matcher.should_include_file(
                sanitized_filename,
                allowed_extensions,
                excluded_extensions
            )
            
            if should_include:
                attachment_counter += 1
                print(Colors.info(f"  Including: {original_filename} ({reason})"))
                
                # Add numbered prefix for better sorting
                new_filename = f"{attachment_counter:02d}_{sanitized_filename}"
                
                attachments_to_save.append({
                    'part': part,
                    'new_filename': new_filename,
                    'original_filename': original_filename,
                    'sanitized_filename': sanitized_filename,
                    'attachment_number': attachment_counter
                })
            else:
                print(Colors.warning(f"  Skipping: {original_filename} ({reason})"))
        
        return attachments_to_save
    
    def _save_attachment(
        self,
        att_data: Dict,
        target_dir: str,
        email_info: Dict
    ) -> Optional[Dict]:
        """
        Save a single attachment to disk.
        
        Args:
            att_data: Attachment data dictionary
            target_dir: Target directory for saving
            email_info: Email metadata
            
        Returns:
            Dictionary with saved attachment information or None if failed
        """
        part = att_data['part']
        new_filename = att_data['new_filename']
        original_filename = att_data['original_filename']
        
        # Get unique filename if file already exists
        unique_filename = get_unique_filename(target_dir, new_filename)
        filepath = os.path.join(target_dir, unique_filename)
        
        try:
            # Extract attachment content
            content = self._extract_attachment_content(part)
            
            if content is None:
                raise ValueError("No content in MIME part")
            
            # Save to file
            with open(filepath, 'wb') as f:
                f.write(content)
            
            # Get file size
            size_bytes = os.path.getsize(filepath)
            size_mb = round(size_bytes / (1024 * 1024), 2)
            
            # Prepare attachment info
            info = {
                'filename': unique_filename,
                'original_filename': original_filename,
                'filepath': filepath,
                'size_bytes': size_bytes,
                'size_mb': size_mb,
                'sender': email_info['sender'],
                'subject': email_info['subject'],
                'date': (email_info['email_date'] or datetime.now()).isoformat(),
                'email_id': email_info['email_id'],
                'message_id': email_info['message_id'],
                'email_folder': email_info['email_folder_name'],
                'attachment_number': att_data['attachment_number'],
            }
            
            print(Colors.success(
                f"  Saved: {email_info['email_folder_name']}/{unique_filename} ({size_mb} MB)"
            ))
            dprint(f"Saved to path: {filepath}", tag="FILE")
            
            return info
            
        except Exception as e:
            error_msg = f"Error saving {original_filename}: {e}"
            print(Colors.error(f"  {error_msg}"))
            return None
    
    # ========== Helper Methods ==========
    
    @staticmethod
    def _decode_mime_string(s: Optional[str]) -> str:
        """
        Decode MIME-encoded string.
        
        Args:
            s: MIME-encoded string or None
            
        Returns:
            Decoded string
        """
        if not s:
            return ''
            
        try:
            decoded_parts = decode_header(s)
            out = []
            for part, enc in decoded_parts:
                if isinstance(part, bytes):
                    out.append(part.decode(enc or 'utf-8', errors='replace'))
                else:
                    out.append(str(part))
            return ''.join(out)
        except Exception:
            return str(s)
    
    @staticmethod
    def _extract_message_id(message_id: str, email_id: str) -> str:
        """
        Extract and clean Message-ID.
        
        Args:
            message_id: Raw Message-ID header
            email_id: Fallback email ID
            
        Returns:
            Cleaned message ID
        """
        if message_id:
            message_id = message_id.strip('<>')
            if '@' in message_id:
                message_id = message_id.split('@')[0]
            message_id = re.sub(r'[^a-zA-Z0-9\-_]', '', message_id)[:20]
        else:
            message_id = f"email_{email_id}"
            
        return message_id
    
    @staticmethod
    def _extract_sender_email(sender: str) -> str:
        """
        Extract email address from sender field.
        
        Args:
            sender: Raw sender field
            
        Returns:
            Extracted email address
        """
        if not sender or sender == 'Unknown':
            return 'unknown'
            
        # Try to extract email from format: "Name <email@domain.com>"
        match = re.search(r'<([^>]+)>', sender)
        if match:
            return match.group(1)
            
        # Fallback: use first word
        return sender.split()[0] if sender.split() else 'unknown'
    
    @staticmethod
    def _parse_email_date(date_str: str) -> Optional[datetime]:
        """
        Parse email date string.
        
        Args:
            date_str: Date string from email header
            
        Returns:
            Parsed datetime or None
        """
        if not date_str:
            return None
            
        try:
            return email.utils.parsedate_to_datetime(date_str)
        except Exception:
            return None
    
    @staticmethod
    def _is_attachment(part: email.message.Message) -> bool:
        """
        Check if a message part is an attachment.
        
        Args:
            part: Email message part
            
        Returns:
            True if part is an attachment
        """
        disposition = part.get_content_disposition()
        filename = part.get_filename()
        
        # Consider it an attachment if:
        # 1. It has 'attachment' disposition, OR
        # 2. It has a filename (even with 'inline' disposition)
        return disposition == 'attachment' or filename is not None
    
    @staticmethod
    def _extract_attachment_content(part: email.message.Message) -> Optional[bytes]:
        """
        Extract content from an attachment part.
        
        Tries `get_payload(decode=True)` first, then falls back to the raw
        string payload (encoded to bytes) when necessary.
        
        Args:
            part: Email message part containing attachment
            
        Returns:
            Attachment content as bytes or None
        """
        content = part.get_payload(decode=True)
        
        if content is None:
            # Try to get payload as string and encode it
            payload = part.get_payload()
            if isinstance(payload, str):
                content = payload.encode(errors='replace')
                
        return content
    
    def get_email_summary(self, msg: email.message.Message) -> Dict[str, Any]:
        """
        Get a summary of an email without saving attachments.
        
        Useful for previews/listing; counts attachments and collects their
        names (best-effort) and a rough byte-size estimate from payloads.
        
        Args:
            msg: Email message object
            
        Returns:
            Dictionary with email summary
        """
        # Extract basic info
        sender = self._decode_mime_string(msg.get('From', 'Unknown'))
        subject = self._decode_mime_string(msg.get('Subject', 'No Subject'))
        date_str = msg.get('Date', '')
        
        # Count attachments
        attachment_count = 0
        total_size = 0
        attachment_names = []
        
        for part in msg.walk():
            if self._is_attachment(part):
                attachment_count += 1
                filename = part.get_filename()
                if filename:
                    attachment_names.append(self._decode_mime_string(filename))
                    
                # Try to estimate size
                payload = part.get_payload(decode=False)
                if isinstance(payload, str):
                    total_size += len(payload)
        
        return {
            'sender': sender,
            'subject': subject,
            'date': date_str,
            'attachment_count': attachment_count,
            'attachment_names': attachment_names,
            'estimated_size_bytes': total_size
        }
