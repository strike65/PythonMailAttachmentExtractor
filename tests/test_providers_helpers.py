#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Additional tests for providers helper methods.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.providers.email_providers import EmailProviders, get_provider_config, detect_provider


def test_is_provider_supported_and_wrappers():
    assert EmailProviders.is_provider_supported('imap.gmail.com') is True
    assert EmailProviders.is_provider_supported('imap.unknown.example') is False

    cfg = get_provider_config('gmail')
    assert cfg is not None and cfg['server'] == 'imap.gmail.com'

    assert detect_provider('user@gmail.com') == 'gmail'
    assert detect_provider('user@unknown.example') is None


def test_provider_notes_and_help_url():
    assert isinstance(EmailProviders.get_provider_notes('icloud'), str)
    assert 'http' in (EmailProviders.get_provider_help_url('gmail') or '')


def test_print_provider_info(capsys):
    EmailProviders.print_provider_info('gmail')
    out = capsys.readouterr().out
    assert 'Gmail Configuration' in out
    assert 'Server:' in out

