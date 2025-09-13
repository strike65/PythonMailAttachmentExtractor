#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for extractor helper methods that were not covered.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.extractor import EmailAttachmentExtractor


def make_extractor():
    return EmailAttachmentExtractor(
        server='imap.example.com', port=993, username='u', password='p', use_ssl=True
    )


def test_parse_mailbox_name_from_imap_list():
    ext = make_extractor()
    raw = b'(\\HasNoChildren) "/" "INBOX/Subfolder"'
    assert ext._parse_mailbox_name(raw) == 'INBOX/Subfolder'

    raw2 = b'(\\HasNoChildren) "/" INBOX'
    # Unquoted name should still parse to something or None; ensure no crash
    name = ext._parse_mailbox_name(raw2)
    assert name in (None, 'INBOX')


def test_filter_inbox_folders():
    ext = make_extractor()
    folders = ['INBOX', 'Sent', 'INBOX/Sub', 'INBOX/Another', 'Drafts']
    filtered = ext._filter_inbox_folders(folders)
    assert filtered[0] == 'INBOX'
    assert 'INBOX/Sub' in filtered and 'INBOX/Another' in filtered
    assert 'Sent' not in filtered


def test_calculate_effective_limit():
    ext = make_extractor()
    # No limits
    assert ext._calculate_effective_limit(None, None, 0) is None
    # Total limit remaining
    assert ext._calculate_effective_limit(None, 10, 3) == 7
    # Per-folder smaller than remaining total
    assert ext._calculate_effective_limit(4, 10, 3) == 4
    # Remaining total smaller than per-folder
    assert ext._calculate_effective_limit(4, 10, 9) == 1

