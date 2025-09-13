#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for interactive CLI flows using input/getpass monkeypatching.
"""

import sys
import os

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli import interactive as cli_interactive


def test_get_custom_server_config_flow(monkeypatch):
    # Inputs in order:
    # server, port(blank->993), use_ssl('n'->False), mailbox, search,
    # organize_by_sender('y'), organize_by_date('n'), limit('100'), save_metadata('n')
    inputs = iter([
        'imap.example.com',
        '',
        'n',
        'INBOX',
        'ALL',
        'y',
        'n',
        '100',
        'n',
    ])
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: next(inputs))

    cfg = cli_interactive.get_custom_server_config()
    assert cfg['server'] == 'imap.example.com'
    assert cfg['port'] == 993
    assert cfg['use_ssl'] is False


def test_get_credentials_interactive_password(monkeypatch):
    inputs = iter(['user@example.com'])
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: next(inputs))
    monkeypatch.setattr('getpass.getpass', lambda *args, **kwargs: 'secret')

    creds = cli_interactive.get_credentials_interactive()
    assert creds['username'] == 'user@example.com'
    assert creds['password'] == 'secret'


def test_get_credentials_interactive_no_password_decline(monkeypatch):
    inputs = iter(['user@example.com', 'n'])
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: next(inputs))
    monkeypatch.setattr('getpass.getpass', lambda *args, **kwargs: '')

    creds = cli_interactive.get_credentials_interactive()
    assert creds is None


def test_get_processing_options(monkeypatch):
    inputs = iter([
        'MYBOX',       # mailbox
        'UNSEEN',      # search
        'y',           # organize sender
        'n',           # organize date
        '10',          # limit
        'y',           # recursive
        'n',           # save metadata
    ])
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: next(inputs))

    opts = cli_interactive.get_processing_options()
    assert opts['mailbox'] == 'MYBOX'
    assert opts['search_criteria'] == 'UNSEEN'
    assert opts['organize_by_sender'] is True
    assert opts['organize_by_date'] is False
    assert opts['limit'] == 10
    assert opts['recursive'] is True
    assert opts['save_metadata'] is False


def test_select_email_provider_custom(monkeypatch):
    # Force list and pick custom option
    monkeypatch.setattr('src.cli.interactive.EmailProviders.get_provider_list', lambda: ['Gmail', 'Other (Custom IMAP)'])
    inputs = iter(['2'])
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: next(inputs))
    monkeypatch.setattr('src.cli.interactive.get_custom_server_config', lambda: {'server': 's', 'port': 993, 'use_ssl': True})
    cfg = cli_interactive.select_email_provider()
    assert cfg['server'] == 's'


def test_select_email_provider_known(monkeypatch):
    monkeypatch.setattr('src.cli.interactive.EmailProviders.get_provider_list', lambda: ['Gmail'])
    inputs = iter(['1'])
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: next(inputs))
    monkeypatch.setattr('src.cli.interactive.EmailProviders.get_provider_config', lambda name: {'server': 'imap.gmail.com', 'port': 993, 'use_ssl': True})
    cfg = cli_interactive.select_email_provider()
    assert cfg['server'] == 'imap.gmail.com'


def test_get_file_filters(monkeypatch):
    inputs = iter(['pdf *.doc*', 'exe bat'])
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: next(inputs))
    filters = cli_interactive.get_file_filters()
    assert filters['allowed_extensions'] == ['pdf', '*.doc*']
    assert filters['excluded_extensions'] == ['exe', 'bat']

    # Empty inputs -> None
    inputs2 = iter(['', ''])
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: next(inputs2))
    filters2 = cli_interactive.get_file_filters()
    assert filters2['allowed_extensions'] is None
    assert filters2['excluded_extensions'] is None


def test_select_mailbox_interactive(monkeypatch):
    # Valid selection
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: '2')
    assert cli_interactive.select_mailbox_interactive(['INBOX', 'Sent']) == 'Sent'

    # Invalid -> INBOX
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: 'x')
    assert cli_interactive.select_mailbox_interactive(['INBOX', 'Sent']) == 'INBOX'

    # Empty -> INBOX
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: '')
    assert cli_interactive.select_mailbox_interactive(['INBOX', 'Sent']) == 'INBOX'

    # No mailboxes
    assert cli_interactive.select_mailbox_interactive([]) is None


def test_confirm_settings(monkeypatch):
    cfg = {
        'server': 'imap.gmail.com',
        'port': 993,
        'use_ssl': True,
        'username': 'user@example.com',
        'password': 'secret',
        'mailbox': 'INBOX',
        'search_criteria': 'ALL',
        'organize_by_sender': False,
        'organize_by_date': True,
        'recursive': False,
        'allowed_extensions': ['*.pdf'],
        'excluded_extensions': ['*.exe'],
    }
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: 'y')
    assert cli_interactive.confirm_settings(cfg) is True
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: 'n')
    assert cli_interactive.confirm_settings(cfg) is False


def test_get_save_path_interactive_option1(monkeypatch, tmp_path):
    # Work in a temp cwd
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: '1')
    path = cli_interactive.get_save_path_interactive()
    assert os.path.dirname(path) == str(tmp_path)
    assert os.path.basename(path).startswith('email_attachments_')


def test_get_save_path_interactive_option3(monkeypatch, tmp_path):
    # Provide option '3' then the custom path
    inputs = iter(['3', str(tmp_path / 'custom')])
    monkeypatch.setattr('builtins.input', lambda *args, **kwargs: next(inputs))
    path = cli_interactive.get_save_path_interactive()
    assert path.endswith('custom')
