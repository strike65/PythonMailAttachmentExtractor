#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Additional tests for filesystem helpers: safe_move, safe_copy, and OS-specific discovery helpers.
"""

import sys
import os
import shutil

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.filesystem import (
    safe_move,
    safe_copy,
    _get_macos_volumes,
    _get_windows_drives,
    _get_linux_mounts,
)


def test_safe_move_and_copy_file(tmp_path):
    src = tmp_path / 'file.txt'
    src.write_text('hello')
    dest_dir = tmp_path / 'dest'
    dest_dir.mkdir()

    # Copy file
    dest_file = dest_dir / 'file.txt'
    assert safe_copy(str(src), str(dest_file)) is True
    assert dest_file.exists()
    assert src.exists()  # copy does not remove source

    # Move file
    moved_dir = tmp_path / 'moved'
    moved_dir.mkdir()
    assert safe_move(str(src), str(moved_dir)) is True
    assert (moved_dir / 'file.txt').exists()
    assert not src.exists()


def test_safe_copy_directory(tmp_path):
    src_dir = tmp_path / 'folder'
    src_dir.mkdir()
    (src_dir / 'a.txt').write_text('a')
    dest_dir = tmp_path / 'folder_copy'
    assert safe_copy(str(src_dir), str(dest_dir)) is True
    assert dest_dir.is_dir()
    assert (dest_dir / 'a.txt').exists()


def test_safe_copy_and_move_nonexistent(tmp_path):
    missing = tmp_path / 'missing.txt'
    assert safe_copy(str(missing), str(tmp_path / 'out.txt')) is False
    assert safe_move(str(missing), str(tmp_path / 'out_dir')) is False


def test_get_macos_volumes_monkeypatched(monkeypatch):
    # Simulate a volume on /Volumes
    monkeypatch.setattr('os.listdir', lambda p: ['MyDrive'] if p == '/Volumes' else [])
    monkeypatch.setattr('os.path.isdir', lambda p: p == '/Volumes/MyDrive')
    # statvfs likely fails for fake path; function will catch and mark N/A
    vols = _get_macos_volumes()
    assert any(v['name'] == 'MyDrive' for v in vols)


def test_get_windows_drives_monkeypatched(monkeypatch):
    # Only C:\ exists
    def exists(path):
        return path == 'C:\\'
    monkeypatch.setattr('os.path.exists', exists)

    class DU:
        def __init__(self):
            self.total = 1024 * 1024 * 1024
            self.used = 512 * 1024 * 1024
            self.free = self.total - self.used

    monkeypatch.setattr('shutil.disk_usage', lambda p: DU())
    vols = _get_windows_drives()
    assert any('Drive C:' in v['name'] for v in vols)


def test_get_linux_mounts_home_only(monkeypatch, tmp_path):
    # Force home to tmp_path
    monkeypatch.setattr('os.path.expanduser', lambda s: str(tmp_path) if s == '~' else s)
    vols = _get_linux_mounts()
    assert any(v['name'] == 'Home' and v['path'] == str(tmp_path) for v in vols)

