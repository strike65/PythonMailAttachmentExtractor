#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for CLI argument validation behavior.
"""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli.argparser import create_parser, validate_arguments


def test_validate_with_config_short_circuits():
    parser = create_parser()
    args = parser.parse_args(['--config', 'config.json'])
    assert validate_arguments(args) is True


def test_validate_interactive_when_no_args():
    parser = create_parser()
    # No args provided at all: should be considered interactive and thus valid
    args = parser.parse_args([])
    assert validate_arguments(args) is True


def test_validate_requires_server_and_username_when_partial(capsys):
    parser = create_parser()
    # Provide only server, missing username
    args = parser.parse_args(['--server', 'imap.gmail.com'])
    assert validate_arguments(args) is False
    out = capsys.readouterr().out
    assert 'both --server and --username are required' in out

