#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Additional tests for EmailProcessor helper methods and summary.
"""

import sys
import os
import tempfile
from email.message import EmailMessage

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.email_processor import EmailProcessor


def test_decode_mime_string_and_sender_extraction():
    # Encoded UTF-8 header
    s = '=?utf-8?q?Hello_=C3=84?='
    assert EmailProcessor._decode_mime_string(s) == 'Hello Ä'

    assert EmailProcessor._extract_sender_email('John <john@example.com>') == 'john@example.com'
    assert EmailProcessor._extract_sender_email('plain@example.com') == 'plain@example.com'
    assert EmailProcessor._extract_sender_email(None) == 'unknown'


def test_extract_message_id_and_date_parsing():
    assert EmailProcessor._extract_message_id('<abc123@domain.com>', '42') == 'abc123'
    # Fallback uses email_id
    assert EmailProcessor._extract_message_id('', '42') == 'email_42'

    assert EmailProcessor._parse_email_date('Fri, 21 Nov 1997 09:55:06 -0600') is not None
    assert EmailProcessor._parse_email_date('not-a-date') is None


def test_get_email_summary_and_attachment_saving(tmp_path):
    # Prepare an email with 2 attachments
    msg = EmailMessage()
    msg['From'] = 'Alice <alice@example.com>'
    msg['Subject'] = 'Report'
    msg['Date'] = 'Fri, 21 Nov 1997 09:55:06 -0600'
    msg.set_content('Body here')

    msg.add_attachment(b'PDFDATA', maintype='application', subtype='pdf', filename='report.pdf')
    msg.add_attachment(b'EXEDATA', maintype='application', subtype='octet-stream', filename='virus.exe')

    proc = EmailProcessor()

    summary = proc.get_email_summary(msg)
    assert summary['sender'].startswith('Alice') or 'alice@example.com' in summary['sender']
    assert summary['attachment_count'] == 2
    assert 'report.pdf' in summary['attachment_names']

    # Now test extract_attachments with filtering: allow pdf, exclude exe
    saved = proc.extract_attachments(
        email_id='1',
        msg=msg,
        save_path=str(tmp_path),
        organize_by_sender=False,
        organize_by_date=False,
        allowed_extensions=['*.pdf'],
        excluded_extensions=['*.exe'],
        pattern_matcher=None,
    )
    # Only PDF should be saved
    assert len(saved) == 1
    assert saved[0]['filename'].startswith('01_')
    assert saved[0]['original_filename'] == 'report.pdf'
    assert os.path.exists(saved[0]['filepath'])

