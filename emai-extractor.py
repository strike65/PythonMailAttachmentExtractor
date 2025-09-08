#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cross-Platform Email Attachment Extractor
Extracts all attachments from IMAP mailboxes and saves them to a specified location
Compatible with Windows, Linux, and macOS
"""

import imaplib
import email
from email import policy
from email.header import decode_header
import os
import sys
import getpass
import re
from datetime import datetime
from pathlib import Path
import argparse
import json
from typing import Dict, List, Optional, Tuple
import ssl
import platform

# Cross-platform colored output
class Colors:
    """Cross-platform color codes for terminal output"""
    
    # Check if we're on Windows
    if platform.system() == 'Windows':
        # Enable ANSI escape sequences on Windows 10+
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass
    
    # ANSI color codes
    RED = '\033[91m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    @staticmethod
    def error(text):
        """Red text for errors"""
        return f"{Colors.RED}{text}{Colors.RESET}"
    
    @staticmethod
    def success(text):
        """Green text for success messages"""
        return f"{Colors.GREEN}{text}{Colors.RESET}"
    
    @staticmethod
    def info(text):
        """Cyan text for information"""
        return f"{Colors.CYAN}{text}{Colors.RESET}"
    
    @staticmethod
    def warning(text):
        """Yellow text for warnings"""
        return f"{Colors.YELLOW}{text}{Colors.RESET}"


class EmailAttachmentExtractor:
    """Class for extracting email attachments via IMAP"""

    KNOWN_PROVIDERS = {
        'gmail':   {'server': 'imap.gmail.com',         'port': 993, 'ssl': True},
        'outlook': {'server': 'outlook.office365.com',  'port': 993, 'ssl': True},
        'icloud':  {'server': 'imap.mail.me.com',       'port': 993, 'ssl': True},
        'yahoo':   {'server': 'imap.mail.yahoo.com',    'port': 993, 'ssl': True},
        'gmx':     {'server': 'imap.gmx.net',           'port': 993, 'ssl': True},
        'web.de':  {'server': 'imap.web.de',            'port': 993, 'ssl': True},
    }

    def __init__(self, server: str, port: int, username: str, password: str, use_ssl: bool = True):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.imap: Optional[imaplib.IMAP4] = None
        self.statistics = {
            'emails_processed': 0,
            'attachments_saved': 0,
            'total_size_mb': 0.0,
            'errors': []
        }

    def connect(self) -> bool:
        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                self.imap = imaplib.IMAP4_SSL(self.server, self.port, ssl_context=context)
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

    def get_mailboxes(self) -> List[str]:
        try:
            status, mailboxes = self.imap.list()
            if status != 'OK' or not mailboxes:
                return []
            
            folders: List[str] = []
            for raw in mailboxes:
                if raw is None:
                    continue
                    
                line = raw.decode(errors='replace')
                
                # Parse IMAP LIST format: (flags) "delimiter" mailbox_name
                match = re.match(r'\([^)]*\)\s+"[^"]*"\s+(.+)', line)
                if match:
                    folder_name = match.group(1).strip('"')
                    folders.append(folder_name)
                        
            return folders
            
        except Exception as e:
            print(Colors.error(f"Error fetching mailboxes: {e}"))
            return []

    def select_mailbox(self, mailbox: str = 'INBOX') -> bool:
        try:
            status, _ = self.imap.select(mailbox, readonly=True)
            if status == 'OK':
                print(Colors.success(f"Mailbox '{mailbox}' selected"))
                return True
            print(Colors.error(f"Could not select mailbox '{mailbox}'"))
            return False
        except Exception as e:
            print(Colors.error(f"Error selecting mailbox: {e}"))
            return False

    @staticmethod
    def decode_mime_string(s: Optional[str]) -> str:
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
            return s

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        # Remove invalid characters for all platforms
        # Windows: < > : " / \ | ? * and ASCII 0-31
        # Unix/Linux/macOS: mainly / and null
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)
        filename = filename.strip().rstrip('.')
        
        # Windows reserved names
        if platform.system() == 'Windows':
            reserved = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1,10)] + [f'LPT{i}' for i in range(1,10)]
            name_without_ext = filename.split('.')[0].upper()
            if name_without_ext in reserved:
                filename = f'_{filename}'
        
        # Maximum filename length (255 for most systems, but be conservative)
        max_length = 200
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length - len(ext)] + ext
            
        return filename or 'unnamed'

    @staticmethod
    def get_unique_filename(directory: str, filename: str) -> str:
        base = os.path.join(directory, filename)
        if not os.path.exists(base):
            return filename
        name, ext = os.path.splitext(filename)
        counter = 1
        while True:
            candidate = f"{name}_{counter}{ext}"
            if not os.path.exists(os.path.join(directory, candidate)):
                return candidate
            counter += 1

    def extract_attachments_from_email(
        self,
        email_id: str,
        msg: email.message.Message,
        save_path: str,
        organize_by_sender: bool = False,
        organize_by_date: bool = False
    ) -> List[Dict]:
        saved_attachments: List[Dict] = []

        sender = self.decode_mime_string(msg.get('From', 'Unknown'))
        subject = self.decode_mime_string(msg.get('Subject', 'No Subject'))
        date_str = msg.get('Date', '')
        
        # Extract Message-ID
        message_id = msg.get('Message-ID', '')
        if message_id:
            message_id = message_id.strip('<>')
            if '@' in message_id:
                message_id = message_id.split('@')[0]
            message_id = re.sub(r'[^a-zA-Z0-9\-_]', '', message_id)[:20]
        else:
            message_id = f"email_{email_id}"

        m = re.search(r'<([^>]+)>', sender)
        sender_email = (m.group(1) if m else sender.split()[:1][0]) if sender and sender != 'Unknown' else 'unknown'

        try:
            email_date = email.utils.parsedate_to_datetime(date_str) if date_str else None
        except Exception:
            email_date = None
        
        date_for_filename = (email_date or datetime.now()).strftime('%Y-%m-%d')
        
        # Prepare base directory (but don't create yet)
        target_dir = save_path
        
        if organize_by_sender:
            target_dir = os.path.join(target_dir, self.sanitize_filename(sender_email))
        
        if organize_by_date:
            target_dir = os.path.join(target_dir, date_for_filename)
        
        # Email-specific folder (but don't create yet)
        subject_short = self.sanitize_filename(subject[:50])
        email_folder_name = f"{date_for_filename}_{message_id}_{subject_short}"
        email_target_dir = os.path.join(target_dir, email_folder_name)
        
        # Collect all attachments first
        attachments_to_save = []
        attachment_counter = 0

        for part in msg.walk():
            disp = part.get_content_disposition()
            filename = part.get_filename()

            is_attachment = (disp == 'attachment') or (filename is not None)
            if not is_attachment:
                continue

            attachment_counter += 1
            original_filename = self.decode_mime_string(filename or f'attachment_{attachment_counter}')
            sanitized_filename = self.sanitize_filename(original_filename)
            
            # Add prefix for better sorting
            new_filename = f"{attachment_counter:02d}_{sanitized_filename}"
            
            attachments_to_save.append({
                'part': part,
                'new_filename': new_filename,
                'original_filename': original_filename,
                'sanitized_filename': sanitized_filename,
                'attachment_number': attachment_counter
            })
        
        # Only create folder and save if attachments were found
        if attachments_to_save:
            os.makedirs(email_target_dir, exist_ok=True)
            
            for att_data in attachments_to_save:
                part = att_data['part']
                new_filename = att_data['new_filename']
                original_filename = att_data['original_filename']
                
                unique_filename = self.get_unique_filename(email_target_dir, new_filename)
                filepath = os.path.join(email_target_dir, unique_filename)

                try:
                    content = part.get_payload(decode=True)
                    if content is None:
                        payload = part.get_payload()
                        if isinstance(payload, str):
                            content = payload.encode(errors='replace')
                    if content is None:
                        raise ValueError("No content in MIME part")

                    with open(filepath, 'wb') as f:
                        f.write(content)

                    size_bytes = os.path.getsize(filepath)
                    size_mb = round(size_bytes / (1024 * 1024), 2)

                    info = {
                        'filename': unique_filename,
                        'original_filename': original_filename,
                        'filepath': filepath,
                        'size_bytes': size_bytes,
                        'size_mb': size_mb,
                        'sender': sender,
                        'subject': subject,
                        'date': (email_date or datetime.now()).isoformat(),
                        'email_id': email_id,
                        'message_id': message_id,
                        'email_folder': email_folder_name,
                        'attachment_number': att_data['attachment_number'],
                    }
                    saved_attachments.append(info)
                    self.statistics['attachments_saved'] += 1
                    self.statistics['total_size_mb'] += size_mb
                    print(Colors.info(f"  Saved: {email_folder_name}/{unique_filename} ({size_mb} MB)"))
                    
                except Exception as e:
                    msg_err = f"Error saving {original_filename}: {e}"
                    print(Colors.error(f"  {msg_err}"))
                    self.statistics['errors'].append(msg_err)
        else:
            print(Colors.warning(f"  No attachments in email from {sender_email[:30]} - {subject[:50]}"))

        return saved_attachments

    def search_emails(self, search_criteria: str = 'ALL', limit: Optional[int] = None) -> List[str]:
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

    def process_mailbox_recursive(
        self,
        mailbox: str,
        save_path: str,
        search_criteria: str = 'ALL',
        organize_by_sender: bool = False,
        organize_by_date: bool = False,
        limit: Optional[int] = None,
        save_metadata: bool = True,
        processed_count: int = 0,
        total_limit: Optional[int] = None
    ) -> Tuple[Dict, int]:
        """Process a mailbox"""
        print(Colors.info(f"\nProcessing mailbox: {mailbox}"))
        print("-" * 40)
        
        if not self.select_mailbox(mailbox):
            print(Colors.warning(f"Skipping {mailbox} - could not select"))
            return self.statistics, processed_count
        
        effective_limit = limit
        if total_limit and processed_count < total_limit:
            remaining = total_limit - processed_count
            if limit:
                effective_limit = min(limit, remaining)
            else:
                effective_limit = remaining
        
        print(Colors.info(f"Searching emails with criteria: {search_criteria}"))
        email_ids = self.search_emails(search_criteria, effective_limit)
        
        if email_ids:
            print(Colors.info(f"{len(email_ids)} email(s) found in {mailbox}"))
            
            # Clean mailbox name for filesystem
            mailbox_clean = mailbox.replace('/', '_').replace('\\', '_').replace(':', '_')
            mailbox_save_path = os.path.join(save_path, mailbox_clean)
            os.makedirs(mailbox_save_path, exist_ok=True)
            
            all_attachments = []
            
            for idx, eid in enumerate(email_ids, 1):
                if total_limit and processed_count >= total_limit:
                    print(Colors.warning(f"Global limit of {total_limit} emails reached"))
                    break
                    
                try:
                    print(Colors.info(f"\nProcessing email {idx}/{len(email_ids)} in {mailbox} (ID {eid})..."))
                    status, data = self.imap.fetch(eid, '(RFC822)')
                    
                    if status != 'OK' or not data:
                        raise RuntimeError("Fetch returned no data")
                    
                    raw_email = None
                    for item in data:
                        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], (bytes, bytearray)):
                            raw_email = item[1]
                            break
                            
                    if raw_email is None:
                        raise RuntimeError("No RFC822 payload found")
                    
                    msg = email.message_from_bytes(raw_email, policy=policy.default)
                    
                    attachments = self.extract_attachments_from_email(
                        eid, msg, mailbox_save_path, organize_by_sender, organize_by_date
                    )
                    all_attachments.extend(attachments)
                    self.statistics['emails_processed'] += 1
                    processed_count += 1
                    
                except Exception as e:
                    err = f"Error processing email {eid} in {mailbox}: {e}"
                    print(Colors.error(err))
                    self.statistics['errors'].append(err)
            
            if save_metadata and all_attachments:
                metadata_file = os.path.join(mailbox_save_path, f'attachments_metadata_{mailbox_clean}.json')
                try:
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'mailbox': mailbox,
                            'extraction_date': datetime.now().isoformat(),
                            'attachments': all_attachments
                        }, f, ensure_ascii=False, indent=2)
                    print(Colors.success(f"Metadata saved for {mailbox}"))
                except Exception as e:
                    print(Colors.error(f"Error saving metadata for {mailbox}: {e}"))
        else:
            print(Colors.warning(f"No emails found in {mailbox}"))
        
        return self.statistics, processed_count

    def process_all_inbox_folders(
        self,
        save_path: str,
        search_criteria: str = 'ALL',
        organize_by_sender: bool = False,
        organize_by_date: bool = False,
        limit_per_folder: Optional[int] = None,
        total_limit: Optional[int] = None,
        save_metadata: bool = True
    ) -> Dict:
        """Process INBOX and all subfolders"""
        all_mailboxes = self.get_mailboxes()
        
        inbox_folders = ['INBOX']
        for mb in all_mailboxes:
            if mb.startswith('INBOX/') and mb not in inbox_folders:
                inbox_folders.append(mb)
        
        print(Colors.info(f"\nFound {len(inbox_folders)} INBOX folder(s):"))
        for folder in inbox_folders:
            print(f"   - {folder}")
        
        processed_count = 0
        
        for folder in inbox_folders:
            if total_limit and processed_count >= total_limit:
                print(Colors.warning(f"\nTotal limit of {total_limit} emails reached"))
                break
                
            self.statistics, processed_count = self.process_mailbox_recursive(
                folder,
                save_path,
                search_criteria,
                organize_by_sender,
                organize_by_date,
                limit_per_folder,
                save_metadata,
                processed_count,
                total_limit
            )
        
        if save_metadata:
            metadata_file = os.path.join(save_path, 'attachments_metadata_total.json')
            try:
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'extraction_date': datetime.now().isoformat(),
                        'processed_folders': inbox_folders,
                        'statistics': self.statistics
                    }, f, ensure_ascii=False, indent=2)
                print(Colors.success(f"\nTotal metadata saved to: {metadata_file}"))
            except Exception as e:
                print(Colors.error(f"Error saving total metadata: {e}"))
        
        return self.statistics

    def process_emails(
        self,
        save_path: str,
        search_criteria: str = 'ALL',
        organize_by_sender: bool = False,
        organize_by_date: bool = False,
        limit: Optional[int] = None,
        save_metadata: bool = True
    ) -> Dict:
        os.makedirs(save_path, exist_ok=True)

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
                status, data = self.imap.fetch(eid, '(RFC822)')
                if status != 'OK' or not data:
                    raise RuntimeError("Fetch returned no data")

                raw_email = None
                for item in data:
                    if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], (bytes, bytearray)):
                        raw_email = item[1]
                        break
                if raw_email is None:
                    raise RuntimeError("No RFC822 payload found")

                msg = email.message_from_bytes(raw_email, policy=policy.default)

                attachments = self.extract_attachments_from_email(
                    eid, msg, save_path, organize_by_sender, organize_by_date
                )
                all_attachments.extend(attachments)
                self.statistics['emails_processed'] += 1

            except Exception as e:
                err = f"Error processing email {eid}: {e}"
                print(Colors.error(err))
                self.statistics['errors'].append(err)

        if save_metadata and all_attachments:
            metadata_file = os.path.join(save_path, 'attachments_metadata.json')
            try:
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'extraction_date': datetime.now().isoformat(),
                        'statistics': self.statistics,
                        'attachments': all_attachments
                    }, f, ensure_ascii=False, indent=2)
                print(Colors.success(f"\nMetadata saved to: {metadata_file}"))
            except Exception as e:
                print(Colors.error(f"Error saving metadata: {e}"))

        return self.statistics

    def disconnect(self):
        if self.imap:
            try:
                self.imap.logout()
                print(Colors.success("Connection closed"))
            except Exception:
                pass


def get_available_drives() -> Optional[str]:
    """Get available drives/volumes based on the operating system"""
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        volumes_path = "/Volumes"
        volumes = []
        try:
            entries = os.listdir(volumes_path)
        except Exception:
            print(Colors.error("No external drives found"))
            return None

        for item in entries:
            p = os.path.join(volumes_path, item)
            if os.path.isdir(p):
                try:
                    stat = os.statvfs(p)
                    free_gb = round((stat.f_bavail * stat.f_frsize) / (1024**3), 2)
                    total_gb = round((stat.f_blocks * stat.f_frsize) / (1024**3), 2)
                except Exception:
                    free_gb = 'N/A'
                    total_gb = 'N/A'
                volumes.append({'name': item, 'path': p, 'free_gb': free_gb, 'total_gb': total_gb})
                
    elif system == 'Windows':
        import string
        volumes = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    import shutil
                    total, used, free = shutil.disk_usage(drive)
                    free_gb = round(free / (1024**3), 2)
                    total_gb = round(total / (1024**3), 2)
                    volumes.append({'name': f"Drive {letter}:", 'path': drive, 'free_gb': free_gb, 'total_gb': total_gb})
                except:
                    volumes.append({'name': f"Drive {letter}:", 'path': drive, 'free_gb': 'N/A', 'total_gb': 'N/A'})
                    
    else:  # Linux and other Unix-like systems
        volumes = []
        # Add home directory
        home = os.path.expanduser("~")
        try:
            stat = os.statvfs(home)
            free_gb = round((stat.f_bavail * stat.f_frsize) / (1024**3), 2)
            total_gb = round((stat.f_blocks * stat.f_frsize) / (1024**3), 2)
            volumes.append({'name': 'Home', 'path': home, 'free_gb': free_gb, 'total_gb': total_gb})
        except:
            volumes.append({'name': 'Home', 'path': home, 'free_gb': 'N/A', 'total_gb': 'N/A'})
        
        # Check for mounted drives in /media and /mnt
        for mount_point in ['/media', '/mnt']:
            if os.path.exists(mount_point):
                try:
                    for item in os.listdir(mount_point):
                        p = os.path.join(mount_point, item)
                        if os.path.ismount(p):
                            stat = os.statvfs(p)
                            free_gb = round((stat.f_bavail * stat.f_frsize) / (1024**3), 2)
                            total_gb = round((stat.f_blocks * stat.f_frsize) / (1024**3), 2)
                            volumes.append({'name': item, 'path': p, 'free_gb': free_gb, 'total_gb': total_gb})
                except:
                    pass

    if not volumes:
        print(Colors.error("No drives found"))
        return None

    print(Colors.info("\nAvailable drives:"))
    print("-" * 60)
    for idx, v in enumerate(volumes, 1):
        if v['free_gb'] != 'N/A':
            print(f"{idx}. {v['name']} - {v['free_gb']} GB free of {v['total_gb']} GB")
        else:
            print(f"{idx}. {v['name']}")

    while True:
        choice = input(Colors.cyan(f"\nSelect a drive (1-{len(volumes)}) or 'q' to quit: ")).strip()
        if choice.lower() == 'q':
            return None
        try:
            i = int(choice) - 1
            if 0 <= i < len(volumes):
                sel = volumes[i]
                sub = input(Colors.cyan(f"\nSubfolder on {sel['name']} (Enter for root): ")).strip()
                full = os.path.join(sel['path'], sub) if sub else sel['path']
                os.makedirs(full, exist_ok=True)
                return full
        except ValueError:
            pass
        print(Colors.error("Invalid selection"))


def load_config(config_file: str) -> Dict:
    """Load configuration from JSON file"""
    try:
        if not os.path.exists(config_file):
            print(Colors.error(f"Configuration file '{config_file}' not found"))
            return None
            
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        required_fields = ['server', 'username']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            print(Colors.error(f"Missing fields in configuration: {', '.join(missing_fields)}"))
            return None
            
        # Set default values for optional fields
        config.setdefault('port', 993)
        config.setdefault('use_ssl', True)
        config.setdefault('mailbox', 'INBOX')
        config.setdefault('search_criteria', 'ALL')
        config.setdefault('organize_by_sender', False)
        config.setdefault('organize_by_date', True)
        config.setdefault('save_metadata', True)
        config.setdefault('save_path', None)
        config.setdefault('limit', None)
        config.setdefault('recursive', False)
        
        print(Colors.success(f"Configuration loaded from: {config_file}"))
        return config
        
    except json.JSONDecodeError as e:
        print(Colors.error(f"Error parsing JSON file: {e}"))
        return None
    except Exception as e:
        print(Colors.error(f"Error loading configuration: {e}"))
        return None


def interactive_setup() -> Dict:
    print("\n" + "="*60)
    print(Colors.info("EMAIL ATTACHMENT EXTRACTOR - SETUP"))
    print("="*60)

    print(Colors.info("\nSelect email provider:"))
    print("-" * 40)
    providers = list(EmailAttachmentExtractor.KNOWN_PROVIDERS.keys()) + ['Other']
    for idx, provider in enumerate(providers, 1):
        print(f"{idx}. {provider}")

    while True:
        try:
            choice = input(Colors.cyan(f"\nSelect your provider (1-{len(providers)}): ")).strip()
            idx = int(choice) - 1
            if 0 <= idx < len(providers):
                selected_provider = providers[idx]
                break
            print(Colors.error("Invalid selection"))
        except ValueError:
            print(Colors.error("Please enter a number"))

    if selected_provider == 'Other':
        server = input(Colors.cyan("IMAP server address: ")).strip()
        port_s = input(Colors.cyan("Port (default 993 for SSL): ")).strip()
        port = int(port_s) if port_s else 993
        use_ssl = input(Colors.cyan("Use SSL? (y/n, default y): ")).strip().lower() != 'n'
    else:
        settings = EmailAttachmentExtractor.KNOWN_PROVIDERS[selected_provider]
        server, port, use_ssl = settings['server'], settings['port'], settings['ssl']
        print(Colors.success(f"\nServer settings loaded for {selected_provider}"))

    print(Colors.info("\nLogin credentials:"))
    print("-" * 40)
    username = input(Colors.cyan("Email address/username: ")).strip()
    password = getpass.getpass(Colors.cyan("Password: "))

    return {'server': server, 'port': port, 'username': username, 'password': password, 'use_ssl': use_ssl}


def main():
    parser = argparse.ArgumentParser(
        description='Cross-Platform Email Attachment Extractor',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Configuration file as primary option
    parser.add_argument('--config', '-c', help='Path to JSON configuration file')
    
    # All other options can override configuration
    parser.add_argument('--server', help='IMAP server address (overrides config)')
    parser.add_argument('--port', type=int, help='IMAP port (overrides config)')
    parser.add_argument('--username', help='Email address/username (overrides config)')
    parser.add_argument('--password', help='Password (overrides config)')
    parser.add_argument('--save-path', help='Save path for attachments (overrides config)')
    parser.add_argument('--mailbox', help='Mailbox/folder (overrides config)')
    parser.add_argument('--search', help='IMAP search criteria (overrides config)')
    parser.add_argument('--organize-by-sender', action='store_true', help='Create folders by sender')
    parser.add_argument('--organize-by-date', action='store_true', help='Create folders by date')
    parser.add_argument('--limit', type=int, help='Maximum number of emails to process')
    parser.add_argument('--no-metadata', action='store_true', help='Do not save metadata JSON')
    parser.add_argument('--recursive', action='store_true', help='Process all INBOX subfolders recursively')
    parser.add_argument('--limit-per-folder', type=int, help='Maximum emails per folder (for recursive)')
    parser.add_argument('--total-limit', type=int, help='Total limit across all folders (for recursive)')

    args = parser.parse_args()

    # Initialize configuration
    config = {}
    
    # Load configuration from file if specified
    if args.config:
        config = load_config(args.config)
        if config is None:
            sys.exit(1)
    
    # Override with command line arguments
    if args.server:
        config['server'] = args.server
    if args.port:
        config['port'] = args.port
    if args.username:
        config['username'] = args.username
    if args.password:
        config['password'] = args.password
    if args.save_path:
        config['save_path'] = args.save_path
    if args.mailbox:
        config['mailbox'] = args.mailbox
    if args.search:
        config['search_criteria'] = args.search
    if args.organize_by_sender:
        config['organize_by_sender'] = True
    if args.organize_by_date:
        config['organize_by_date'] = True
    if args.limit:
        config['limit'] = args.limit
    if args.no_metadata:
        config['save_metadata'] = False
    if args.recursive:
        config['recursive'] = True

    # If no configuration loaded and no server data available, start interactive setup
    if not config.get('server') or not config.get('username'):
        print(Colors.warning("\nNo complete configuration found. Starting interactive setup..."))
        settings = interactive_setup()
        config.update(settings)
    
    # Request password if not in configuration
    if not config.get('password'):
        config['password'] = getpass.getpass(Colors.cyan(f"Password for {config['username']}: "))

    # Initialize extractor
    extractor = EmailAttachmentExtractor(
        config['server'],
        config.get('port', 993),
        config['username'],
        config['password'],
        config.get('use_ssl', True)
    )

    if not extractor.connect():
        print(Colors.error("Connection failed"))
        sys.exit(1)

    # Select mailbox
    mailbox = config.get('mailbox', 'INBOX')
    
    # If no specific mailbox in config, show available
    if mailbox == 'INBOX' and not args.config:
        print(Colors.info("\nAvailable mailboxes:"))
        print("-" * 40)
        mailboxes = extractor.get_mailboxes()
        
        if mailboxes:
            for idx, mb in enumerate(mailboxes, 1):
                print(f"{idx}. {mb}")
            
            choice = input(Colors.cyan(f"\nSelect mailbox (1-{len(mailboxes)}, Enter for INBOX): ")).strip()
            if choice:
                try:
                    i = int(choice) - 1
                    if 0 <= i < len(mailboxes):
                        mailbox = mailboxes[i]
                except ValueError:
                    pass

    if not config.get('recursive', False) and not args.recursive:
        if not extractor.select_mailbox(mailbox):
            print(Colors.error(f"Could not select mailbox '{mailbox}'"))
            sys.exit(1)

    # Determine save path
    save_path = config.get('save_path')
    if not save_path:
        print(Colors.info("\nSelect save location:"))
        print("-" * 40)
        save_path = get_available_drives()
        if not save_path:
            save_path = input(Colors.cyan("\nEnter save path (Enter = current directory): ")).strip()
            if not save_path:
                save_path = os.path.join(os.getcwd(), f"email_attachments_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    print(Colors.info(f"\nSave path: {save_path}"))
    print(Colors.info(f"Search criteria: {config.get('search_criteria', 'ALL')}"))
    print(Colors.info(f"Organize by sender: {'Yes' if config.get('organize_by_sender') else 'No'}"))
    print(Colors.info(f"Organize by date: {'Yes' if config.get('organize_by_date') else 'No'}"))
    if config.get('limit'):
        print(Colors.info(f"Limit: {config['limit']} emails"))

    print("\n" + "="*60)
    print(Colors.info("STARTING PROCESSING"))
    print("="*60)

    try:
        # Check if recursive processing is desired
        if args.recursive or config.get('recursive', False):
            print(Colors.info("\nRecursive processing of all INBOX folders enabled"))
            
            statistics = extractor.process_all_inbox_folders(
                save_path=save_path,
                search_criteria=config.get('search_criteria', 'ALL'),
                organize_by_sender=config.get('organize_by_sender', False),
                organize_by_date=config.get('organize_by_date', True),
                limit_per_folder=args.limit_per_folder or config.get('limit_per_folder'),
                total_limit=args.total_limit or config.get('total_limit') or config.get('limit'),
                save_metadata=config.get('save_metadata', True)
            )
        else:
            # Normal processing of a single mailbox
            statistics = extractor.process_emails(
                save_path=save_path,
                search_criteria=config.get('search_criteria', 'ALL'),
                organize_by_sender=config.get('organize_by_sender', False),
                organize_by_date=config.get('organize_by_date', True),
                limit=config.get('limit'),
                save_metadata=config.get('save_metadata', True)
            )

        print("\n" + "="*60)
        print(Colors.success("PROCESSING COMPLETED"))
        print("="*60)
        print(Colors.info(f"Emails processed: {statistics['emails_processed']}"))
        print(Colors.info(f"Attachments saved: {statistics['attachments_saved']}"))
        print(Colors.info(f"Total size: {statistics['total_size_mb']:.2f} MB"))

        if statistics['errors']:
            print(Colors.warning(f"\n{len(statistics['errors'])} error(s) occurred:"))
            for err in statistics['errors'][:5]:
                print(Colors.error(f"   - {err}"))
            if len(statistics['errors']) > 5:
                print(Colors.warning(f"   ... and {len(statistics['errors']) - 5} more"))

        print(Colors.success(f"\nAttachments saved to: {save_path}"))

    except KeyboardInterrupt:
        print(Colors.warning("\n\nProcessing interrupted by user"))
    except Exception as e:
        print(Colors.error(f"\nUnexpected error: {e}"))
    finally:
        extractor.disconnect()


if __name__ == "__main__":
    main()