#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E-Mail Anhänge Extraktor für macOS
Extrahiert alle Anhänge aus einer IMAP-Mailbox und speichert sie auf einer externen Festplatte
"""

import imaplib
# imaplib.Debug = 4
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
from typing import Dict, List, Optional
import ssl

class EmailAttachmentExtractor:
    """Klasse zum Extrahieren von E-Mail-Anhängen über IMAP"""

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
            print(f"✅ Erfolgreich mit {self.server} verbunden")
            return True
        except imaplib.IMAP4.error as e:
            print(f"❌ IMAP-Fehler: {e}")
            return False
        except Exception as e:
            print(f"❌ Verbindungsfehler: {e}")
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
            
              # Teile die Zeile in drei Teile: (flags) "delimiter" name
                # Verwende Regex um das zu extrahieren
                match = re.match(r'\([^)]*\)\s+"[^"]*"\s+(.+)', line)
                if match:
                    folder_name = match.group(1).strip('"')
                    folders.append(folder_name)
                        
            return folders
        except Exception as e:
            print(f"❌ Fehler beim Abrufen der Mailboxen: {e}")
            return []    
    
    def select_mailbox(self, mailbox: str = 'INBOX') -> bool:
        try:
            status, _ = self.imap.select(mailbox, readonly=True)
            if status == 'OK':
                print(f"✅ Mailbox '{mailbox}' ausgewählt")
                return True
            print(f"❌ Konnte Mailbox '{mailbox}' nicht auswählen")
            return False
        except Exception as e:
            print(f"❌ Fehler beim Auswählen der Mailbox: {e}")
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
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)
        filename = filename.strip().rstrip('.')
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255 - len(ext)] + ext
        return filename or 'unnamed'

    @staticmethod
    def get_unique_filename(directory: str, filename: str) -> str:
        base = os.path.join(directory, filename)
        if not os.path.exists(base):
            return filename
        
        # Bei Duplikaten: füge Zähler vor der Dateiendung ein
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

        sender = self.decode_mime_string(msg.get('From', 'Unbekannt'))
        subject = self.decode_mime_string(msg.get('Subject', 'Kein Betreff'))
        date_str = msg.get('Date', '')
        
        # Message-ID extrahieren
        message_id = msg.get('Message-ID', '')
        if message_id:
            message_id = message_id.strip('<>')
            if '@' in message_id:
                message_id = message_id.split('@')[0]
            message_id = re.sub(r'[^a-zA-Z0-9\-_]', '', message_id)[:20]
        else:
            message_id = f"email_{email_id}"

        m = re.search(r'<([^>]+)>', sender)
        sender_email = (m.group(1) if m else sender.split()[:1][0]) if sender and sender != 'Unbekannt' else 'unbekannt'

        try:
            email_date = email.utils.parsedate_to_datetime(date_str) if date_str else None
        except Exception:
            email_date = None
        
        date_for_filename = (email_date or datetime.now()).strftime('%Y-%m-%d')
        
        # Basis-Verzeichnis vorbereiten (aber noch NICHT erstellen)
        target_dir = save_path
        
        if organize_by_sender:
            target_dir = os.path.join(target_dir, self.sanitize_filename(sender_email))
        
        if organize_by_date:
            target_dir = os.path.join(target_dir, date_for_filename)
        
        # E-Mail spezifischer Ordner vorbereiten (aber noch NICHT erstellen)
        subject_short = self.sanitize_filename(subject[:50])
        email_folder_name = f"{date_for_filename}_{message_id}_{subject_short}"
        email_target_dir = os.path.join(target_dir, email_folder_name)
        
        # WICHTIG: Erst alle Anhänge sammeln, BEVOR Ordner erstellt werden
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
            
            # Dateiname mit Präfix für bessere Sortierung
            new_filename = f"{attachment_counter:02d}_{sanitized_filename}"
            
            # Sammle Attachment-Daten
            attachments_to_save.append({
                'part': part,
                'new_filename': new_filename,
                'original_filename': original_filename,
                'sanitized_filename': sanitized_filename,
                'attachment_number': attachment_counter
            })
        
        # NUR wenn Anhänge gefunden wurden, erstelle Ordner und speichere
        if attachments_to_save:
            # JETZT erst Ordner erstellen
            os.makedirs(email_target_dir, exist_ok=True)
            
            # Anhänge speichern
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
                        raise ValueError("kein Inhalt im MIME-Part")

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
                    print(f"  📎 Gespeichert: {email_folder_name}/{unique_filename} ({size_mb} MB)")
                    
                except Exception as e:
                    msg_err = f"Fehler beim Speichern von {original_filename}: {e}"
                    print(f"  ❌ {msg_err}")
                    self.statistics['errors'].append(msg_err)
        else:
            # Keine Anhänge gefunden - Info ausgeben aber keinen Ordner erstellen
            print(f"  ℹ️  Keine Anhänge in E-Mail von {sender_email[:30]} - {subject[:50]}")

        return saved_attachments

    def search_emails(self, search_criteria: str = 'ALL', limit: Optional[int] = None) -> List[str]:
        try:
            status, data = self.imap.search(None, search_criteria)
            if status != 'OK' or not data or not data[0]:
                return []
            raw_ids = data[0].split()  # bytes IDs
            ids = [i.decode('ascii', errors='ignore') for i in raw_ids if i]
            if limit is not None:
                ids = ids[:max(0, int(limit))]
            return ids
        except Exception as e:
            print(f"❌ Fehler bei der E-Mail-Suche: {e}")
            return []

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

        print(f"\n🔍 Suche E-Mails mit Kriterium: {search_criteria}")
        email_ids = self.search_emails(search_criteria, limit)
        if not email_ids:
            print("Keine E-Mails gefunden")
            return self.statistics

        print(f"📧 {len(email_ids)} E-Mail(s) gefunden")

        all_attachments: List[Dict] = []

        for idx, eid in enumerate(email_ids, 1):
            try:
                print(f"\nVerarbeite E-Mail {idx}/{len(email_ids)} (ID {eid})...")
                status, data = self.imap.fetch(eid, '(RFC822)')
                if status != 'OK' or not data:
                    raise RuntimeError("Fetch lieferte keine Daten")

                # Daten können mehrteilig sein; suche die Nutzlast
                raw_email = None
                for item in data:
                    if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], (bytes, bytearray)):
                        raw_email = item[1]
                        break
                if raw_email is None:
                    raise RuntimeError("Keine RFC822-Payload gefunden")

                msg = email.message_from_bytes(raw_email, policy=policy.default)

                attachments = self.extract_attachments_from_email(
                    eid, msg, save_path, organize_by_sender, organize_by_date
                )
                all_attachments.extend(attachments)
                self.statistics['emails_processed'] += 1

            except Exception as e:
                err = f"Fehler bei E-Mail {eid}: {e}"
                print(f"❌ {err}")
                self.statistics['errors'].append(err)

        if save_metadata and all_attachments:
            metadata_file = os.path.join(save_path, 'anhaenge_metadaten.json')
            try:
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'extraction_date': datetime.now().isoformat(),
                        'statistics': self.statistics,
                        'attachments': all_attachments
                    }, f, ensure_ascii=False, indent=2)
                print(f"\n📊 Metadaten gespeichert in: {metadata_file}")
            except Exception as e:
                print(f"❌ Fehler beim Speichern der Metadaten: {e}")

        return self.statistics

    def disconnect(self):
        if self.imap:
            try:
                self.imap.logout()
                print("✅ Verbindung getrennt")
            except Exception:
                pass
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
    ) -> tuple[Dict, int]:
        """
        Verarbeitet eine Mailbox und alle ihre Unterordner rekursiv
        
        Args:
            mailbox: Name der zu verarbeitenden Mailbox
            save_path: Basis-Speicherpfad
            search_criteria: IMAP-Suchkriterien
            organize_by_sender: Nach Absender organisieren
            organize_by_date: Nach Datum organisieren
            limit: Limit pro Mailbox
            save_metadata: Metadaten speichern
            processed_count: Anzahl bereits verarbeiteter E-Mails (für globales Limit)
            total_limit: Globales Limit über alle Mailboxen
            
        Returns:
            Tuple aus (Statistiken, Anzahl verarbeiteter E-Mails)
        """
        print(f"\n📁 Verarbeite Mailbox: {mailbox}")
        print("-" * 40)
        
        # Wähle Mailbox aus
        if not self.select_mailbox(mailbox):
            print(f"⚠️  Überspringe {mailbox} - konnte nicht ausgewählt werden")
            return self.statistics, processed_count
        
        # Berechne effektives Limit für diese Mailbox
        effective_limit = limit
        if total_limit and processed_count < total_limit:
            remaining = total_limit - processed_count
            if limit:
                effective_limit = min(limit, remaining)
            else:
                effective_limit = remaining
        
        # Verarbeite E-Mails in dieser Mailbox
        print(f"🔍 Suche E-Mails mit Kriterium: {search_criteria}")
        email_ids = self.search_emails(search_criteria, effective_limit)
        
        if email_ids:
            print(f"📧 {len(email_ids)} E-Mail(s) in {mailbox} gefunden")
            
            # Erstelle Unterordner für diese Mailbox im Speicherpfad
            mailbox_clean = mailbox.replace('/', '_').replace('\\', '_')
            mailbox_save_path = os.path.join(save_path, mailbox_clean)
            os.makedirs(mailbox_save_path, exist_ok=True)
            
            all_attachments = []
            
            for idx, eid in enumerate(email_ids, 1):
                if total_limit and processed_count >= total_limit:
                    print(f"⚠️  Globales Limit von {total_limit} E-Mails erreicht")
                    break
                    
                try:
                    print(f"\nVerarbeite E-Mail {idx}/{len(email_ids)} in {mailbox} (ID {eid})...")
                    status, data = self.imap.fetch(eid, '(RFC822)')
                    
                    if status != 'OK' or not data:
                        raise RuntimeError("Fetch lieferte keine Daten")
                    
                    raw_email = None
                    for item in data:
                        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], (bytes, bytearray)):
                            raw_email = item[1]
                            break
                            
                    if raw_email is None:
                        raise RuntimeError("Keine RFC822-Payload gefunden")
                    
                    msg = email.message_from_bytes(raw_email, policy=policy.default)
                    
                    attachments = self.extract_attachments_from_email(
                        eid, msg, mailbox_save_path, organize_by_sender, organize_by_date
                    )
                    all_attachments.extend(attachments)
                    self.statistics['emails_processed'] += 1
                    processed_count += 1
                    
                except Exception as e:
                    err = f"Fehler bei E-Mail {eid} in {mailbox}: {e}"
                    print(f"❌ {err}")
                    self.statistics['errors'].append(err)
            
            # Speichere Metadaten für diese Mailbox
            if save_metadata and all_attachments:
                metadata_file = os.path.join(mailbox_save_path, f'anhaenge_metadaten_{mailbox_clean}.json')
                try:
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'mailbox': mailbox,
                            'extraction_date': datetime.now().isoformat(),
                            'attachments': all_attachments
                        }, f, ensure_ascii=False, indent=2)
                    print(f"📊 Metadaten für {mailbox} gespeichert")
                except Exception as e:
                    print(f"❌ Fehler beim Speichern der Metadaten für {mailbox}: {e}")
        else:
            print(f"ℹ️  Keine E-Mails in {mailbox} gefunden")
        
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
        """
        Verarbeitet INBOX und alle Unterordner
        
        Args:
            save_path: Basis-Speicherpfad
            search_criteria: IMAP-Suchkriterien
            organize_by_sender: Nach Absender organisieren
            organize_by_date: Nach Datum organisieren
            limit_per_folder: Limit pro Ordner
            total_limit: Gesamtlimit über alle Ordner
            save_metadata: Metadaten speichern
            
        Returns:
            Gesamtstatistiken
        """
        # Hole alle Mailboxen
        all_mailboxes = self.get_mailboxes()
        
        # Filtere nur INBOX und INBOX/* Ordner
        inbox_folders = ['INBOX']  # INBOX selbst immer zuerst
        for mb in all_mailboxes:
            if mb.startswith('INBOX/') and mb not in inbox_folders:
                inbox_folders.append(mb)
        
        print(f"\n🗂️  Gefundene INBOX-Ordner: {len(inbox_folders)}")
        for folder in inbox_folders:
            print(f"   - {folder}")
        
        processed_count = 0
        
        # Verarbeite jeden Ordner
        for folder in inbox_folders:
            if total_limit and processed_count >= total_limit:
                print(f"\n⚠️  Gesamtlimit von {total_limit} E-Mails erreicht")
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
        
        # Speichere Gesamt-Metadaten
        if save_metadata:
            metadata_file = os.path.join(save_path, 'anhaenge_metadaten_gesamt.json')
            try:
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'extraction_date': datetime.now().isoformat(),
                        'processed_folders': inbox_folders,
                        'statistics': self.statistics
                    }, f, ensure_ascii=False, indent=2)
                print(f"\n📊 Gesamt-Metadaten gespeichert in: {metadata_file}")
            except Exception as e:
                print(f"❌ Fehler beim Speichern der Gesamt-Metadaten: {e}")
        
        return self.statistics


def select_external_drive() -> Optional[str]:
    volumes_path = "/Volumes"
    volumes = []
    try:
        entries = os.listdir(volumes_path)
    except Exception:
        print("❌ Keine externen Laufwerke gefunden")
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

    if not volumes:
        print("❌ Keine externen Laufwerke gefunden")
        return None

    print("\n📁 Verfügbare Laufwerke:")
    print("-" * 60)
    for idx, v in enumerate(volumes, 1):
        if v['free_gb'] != 'N/A':
            print(f"{idx}. {v['name']} - {v['free_gb']} GB frei von {v['total_gb']} GB")
        else:
            print(f"{idx}. {v['name']}")

    while True:
        choice = input(f"\nWählen Sie ein Laufwerk (1-{len(volumes)}) oder 'q' zum Beenden: ").strip()
        if choice.lower() == 'q':
            return None
        try:
            i = int(choice) - 1
            if 0 <= i < len(volumes):
                sel = volumes[i]
                sub = input(f"\nUnterordner auf {sel['name']} (Enter für Hauptverzeichnis): ").strip()
                full = os.path.join(sel['path'], sub) if sub else sel['path']
                os.makedirs(full, exist_ok=True)
                return full
        except ValueError:
            pass
        print("❌ Ungültige Auswahl")

def interactive_setup() -> Dict:
    print("\n" + "="*60)
    print("📧 E-MAIL ANHÄNGE EXTRAKTOR - EINRICHTUNG")
    print("="*60)

    print("\n🏢 E-Mail-Provider auswählen:")
    print("-" * 40)
    providers = list(EmailAttachmentExtractor.KNOWN_PROVIDERS.keys()) + ['Andere']
    for idx, provider in enumerate(providers, 1):
        print(f"{idx}. {provider}")

    while True:
        try:
            choice = input(f"\nWählen Sie Ihren Provider (1-{len(providers)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(providers):
                selected_provider = providers[idx]
                break
            print("❌ Ungültige Auswahl")
        except ValueError:
            print("❌ Bitte geben Sie eine Zahl ein")

    if selected_provider == 'Andere':
        server = input("IMAP-Server-Adresse: ").strip()
        port_s = input("Port (Standard 993 für SSL): ").strip()
        port = int(port_s) if port_s else 993
        use_ssl = input("SSL verwenden? (j/n, Standard j): ").strip().lower() != 'n'
    else:
        settings = EmailAttachmentExtractor.KNOWN_PROVIDERS[selected_provider]
        server, port, use_ssl = settings['server'], settings['port'], settings['ssl']
        print(f"\n✅ Server-Einstellungen für {selected_provider} geladen")

    print("\n🔐 Anmeldedaten:")
    print("-" * 40)
    username = input("E-Mail-Adresse/Benutzername: ").strip()
    password = getpass.getpass("Passwort: ")

    return {'server': server, 'port': port, 'username': username, 'password': password, 'use_ssl': use_ssl}


def load_config(config_file: str) -> Dict:
    """
    Lädt die Konfiguration aus einer JSON-Datei
    
    Args:
        config_file: Pfad zur Konfigurationsdatei
        
    Returns:
        Dictionary mit Konfigurationseinstellungen
    """
    try:
        config_path = Path(config_file)
        if not config_path.exists():
            print(f"❌ Konfigurationsdatei '{config_file}' nicht gefunden")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Validiere erforderliche Felder
        required_fields = ['server', 'username', 'password']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            print(f"❌ Fehlende Felder in Konfiguration: {', '.join(missing_fields)}")
            return None
            
        # Setze Standardwerte für optionale Felder
        config.setdefault('port', 993)
        config.setdefault('use_ssl', True)
        config.setdefault('mailbox', 'INBOX')
        config.setdefault('search_criteria', 'ALL')
        config.setdefault('organize_by_sender', False)
        config.setdefault('organize_by_date', True)
        config.setdefault('save_metadata', True)
        config.setdefault('save_path', None)
        config.setdefault('limit', None)
        
        print(f"✅ Konfiguration geladen aus: {config_file}")
        return config
        
    except json.JSONDecodeError as e:
        print(f"❌ Fehler beim Parsen der JSON-Datei: {e}")
        return None
    except Exception as e:
        print(f"❌ Fehler beim Laden der Konfiguration: {e}")
        return None
def main():
    parser = argparse.ArgumentParser(
        description='E-Mail Anhänge Extraktor für macOS',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Konfigurationsdatei als primäre Option
    parser.add_argument('--config', '-c', help='Pfad zur JSON-Konfigurationsdatei')
    
    # Alle anderen Optionen können die Konfiguration überschreiben
    parser.add_argument('--server', help='IMAP-Server-Adresse (überschreibt config)')
    parser.add_argument('--port', type=int, help='IMAP-Port (überschreibt config)')
    parser.add_argument('--username', help='E-Mail-Adresse/Benutzername (überschreibt config)')
    parser.add_argument('--password', help='Passwort (überschreibt config)')
    parser.add_argument('--save-path', help='Speicherpfad für Anhänge (überschreibt config)')
    parser.add_argument('--mailbox', help='Mailbox/Ordner (überschreibt config)')
    parser.add_argument('--search', help='IMAP-Suchkriterium (überschreibt config)')
    parser.add_argument('--organize-by-sender', action='store_true', help='Ordner nach Absender erstellen')
    parser.add_argument('--organize-by-date', action='store_true', help='Ordner nach Datum erstellen')
    parser.add_argument('--limit', type=int, help='Maximale Anzahl zu verarbeitender E-Mails')
    parser.add_argument('--no-metadata', action='store_true', help='Keine Metadaten-JSON speichern')
    parser.add_argument('--recursive', action='store_true', help='Alle INBOX-Unterordner rekursiv verarbeiten')
    parser.add_argument('--limit-per-folder', type=int, help='Maximale Anzahl E-Mails pro Ordner (bei rekursiv)')
    parser.add_argument('--total-limit', type=int, help='Gesamtlimit über alle Ordner (bei rekursiv)')

    args = parser.parse_args()

    # Initialisiere Konfiguration
    config = {}
    
    # Lade Konfiguration aus Datei wenn angegeben
    if args.config:
        config = load_config(args.config)
        if config is None:
            sys.exit(1)
    
    # Überschreibe mit Kommandozeilen-Argumenten
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

    # Falls keine Konfiguration geladen wurde und keine Server-Daten vorhanden sind, 
    # starte interaktive Einrichtung
    if not config.get('server') or not config.get('username'):
        print("\n⚠️  Keine vollständige Konfiguration gefunden. Starte interaktive Einrichtung...")
        settings = interactive_setup()
        config.update(settings)
    
    # Passwort abfragen falls nicht in Konfiguration
    if not config.get('password'):
        config['password'] = getpass.getpass(f"Passwort für {config['username']}: ")

    # Extractor initialisieren
    extractor = EmailAttachmentExtractor(
        config['server'],
        config.get('port', 993),
        config['username'],
        config['password'],
        config.get('use_ssl', True)
    )

    if not extractor.connect():
        print("❌ Verbindung fehlgeschlagen")
        sys.exit(1)

    # Mailbox auswählen
    mailbox = config.get('mailbox', 'INBOX')
    
    # Wenn keine spezifische Mailbox in config, zeige verfügbare an
    if mailbox == 'INBOX' and not args.config:
        print("\n📬 Verfügbare Mailboxen:")
        print("-" * 40)
        mailboxes = extractor.get_mailboxes()
        
        if mailboxes:
            for idx, mb in enumerate(mailboxes, 1):
                print(f"{idx}. {mb}")
            
            choice = input(f"\nMailbox wählen (1-{len(mailboxes)}, Enter für INBOX): ").strip()
            if choice:
                try:
                    i = int(choice) - 1
                    if 0 <= i < len(mailboxes):
                        mailbox = mailboxes[i]
                except ValueError:
                    pass

    if not extractor.select_mailbox(mailbox):
        print(f"❌ Mailbox '{mailbox}' konnte nicht ausgewählt werden")
        sys.exit(1)

    # Speicherpfad bestimmen
    save_path = config.get('save_path')
    if not save_path:
        print("\n💾 Speicherort wählen:")
        print("-" * 40)
        save_path = select_external_drive()
        if not save_path:
            save_path = input("\nSpeicherpfad eingeben (Enter = aktuelles Verzeichnis): ").strip()
            if not save_path:
                save_path = os.path.join(os.getcwd(), f"email_anhaenge_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    print(f"\n📂 Speicherpfad: {save_path}")
    print(f"📧 Suchkriterium: {config.get('search_criteria', 'ALL')}")
    print(f"📁 Nach Absender organisieren: {'Ja' if config.get('organize_by_sender') else 'Nein'}")
    print(f"📅 Nach Datum organisieren: {'Ja' if config.get('organize_by_date') else 'Nein'}")
    if config.get('limit'):
        print(f"🔢 Limit: {config['limit']} E-Mails")

    print("\n" + "="*60)
    print("🚀 STARTE VERARBEITUNG")
    print("\n" + "="*60)
    print("🚀 STARTE VERARBEITUNG")
    print("="*60)

    try:
        # Prüfe ob rekursive Verarbeitung gewünscht ist
        if args.recursive or config.get('recursive', False):
            print("\n🔄 Rekursive Verarbeitung aller INBOX-Ordner aktiviert")
            
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
            # Normale Verarbeitung einer einzelnen Mailbox
            statistics = extractor.process_emails(
                save_path=save_path,
                search_criteria=config.get('search_criteria', 'ALL'),
                organize_by_sender=config.get('organize_by_sender', False),
                organize_by_date=config.get('organize_by_date', True),
                limit=config.get('limit'),
                save_metadata=config.get('save_metadata', True)
            )
        print("\n" + "="*60)
        print("✅ VERARBEITUNG ABGESCHLOSSEN")
        print("="*60)
        print(f"📧 E-Mails verarbeitet: {statistics['emails_processed']}")
        print(f"📎 Anhänge gespeichert: {statistics['attachments_saved']}")
        print(f"💾 Gesamtgröße: {statistics['total_size_mb']:.2f} MB")

        if statistics['errors']:
            print(f"\n⚠️  {len(statistics['errors'])} Fehler aufgetreten:")
            for err in statistics['errors'][:5]:
                print(f"   - {err}")
            if len(statistics['errors']) > 5:
                print(f"   ... und {len(statistics['errors']) - 5} weitere")

        print(f"\n📂 Anhänge gespeichert in: {save_path}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Verarbeitung abgebrochen")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
    finally:
        extractor.disconnect()
        
if __name__ == "__main__":
    main()

