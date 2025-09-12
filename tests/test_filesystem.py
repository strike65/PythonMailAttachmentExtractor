#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Filesystem Utilities Module
"""

import pytest
import sys
import os
import tempfile
import platform
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.filesystem import (
    sanitize_filename,
    get_unique_filename,
    create_directory,
    get_file_size_readable,
    check_disk_space,
    list_files_with_pattern,
    get_directory_stats
)


class TestSanitizeFilename:
    """Test filename sanitization."""
    
    def test_remove_invalid_characters(self):
        """Test removal of invalid characters."""
        assert sanitize_filename('file<>:"/\\|?*.txt') == 'file________.txt'
        assert sanitize_filename('normal_file.pdf') == 'normal_file.pdf'
    
    def test_remove_control_characters(self):
        """Test removal of control characters."""
        filename = 'file\x00\x01\x02.txt'
        result = sanitize_filename(filename)
        assert '\x00' not in result
        assert '\x01' not in result
    
    def test_trim_spaces_and_dots(self):
        """Test trimming of leading/trailing spaces and dots."""
        assert sanitize_filename('  file.txt  ') == 'file.txt'
        assert sanitize_filename('file...') == 'file'
        assert sanitize_filename('...file...') == 'file'
    
    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific test")
    def test_windows_reserved_names(self):
        """Test handling of Windows reserved names."""
        assert sanitize_filename('CON') == '_CON'
        assert sanitize_filename('PRN.txt') == '_PRN.txt'
        assert sanitize_filename('AUX.doc') == '_AUX.doc'
        assert sanitize_filename('COM1') == '_COM1'
        assert sanitize_filename('LPT1.pdf') == '_LPT1.pdf'
    
    def test_filename_length_limit(self):
        """Test filename length limiting."""
        long_name = 'a' * 300 + '.txt'
        result = sanitize_filename(long_name)
        assert len(result) <= 204  # 200 + extension
        assert result.endswith('.txt')
    
    def test_empty_filename(self):
        """Test handling of empty filename."""
        assert sanitize_filename('') == 'unnamed'
        assert sanitize_filename(None) == 'unnamed'
    
    def test_case_preservation(self):
        """Test that case is preserved."""
        assert sanitize_filename('MyFile.PDF') == 'MyFile.PDF'
        assert sanitize_filename('CamelCase.docx') == 'CamelCase.docx'


class TestGetUniqueFilename:
    """Test unique filename generation."""
    
    def test_unique_filename_no_conflict(self):
        """Test when filename doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = get_unique_filename(tmpdir, 'test.txt')
            assert filename == 'test.txt'
    
    def test_unique_filename_with_conflict(self):
        """Test when filename already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing file
            Path(tmpdir, 'test.txt').touch()
            
            # Get unique name
            filename = get_unique_filename(tmpdir, 'test.txt')
            assert filename == 'test_1.txt'
            
            # Create that too
            Path(tmpdir, 'test_1.txt').touch()
            filename = get_unique_filename(tmpdir, 'test.txt')
            assert filename == 'test_2.txt'
    
    def test_unique_filename_preserves_extension(self):
        """Test that file extension is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, 'document.pdf').touch()
            filename = get_unique_filename(tmpdir, 'document.pdf')
            assert filename.endswith('.pdf')
            assert filename == 'document_1.pdf'


class TestCreateDirectory:
    """Test directory creation."""
    
    def test_create_new_directory(self):
        """Test creating a new directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, 'new_folder')
            assert create_directory(new_dir) is True
            assert os.path.exists(new_dir)
    
    def test_create_nested_directories(self):
        """Test creating nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = os.path.join(tmpdir, 'level1', 'level2', 'level3')
            assert create_directory(nested_dir) is True
            assert os.path.exists(nested_dir)
    
    def test_create_existing_directory(self):
        """Test creating a directory that already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Should return True and not raise error
            assert create_directory(tmpdir) is True


class TestGetFileSizeReadable:
    """Test human-readable file size conversion."""
    
    def test_bytes(self):
        """Test byte sizes."""
        assert get_file_size_readable(0) == "0.00 B"
        assert get_file_size_readable(500) == "500.00 B"
        assert get_file_size_readable(1023) == "1023.00 B"
    
    def test_kilobytes(self):
        """Test kilobyte sizes."""
        assert get_file_size_readable(1024) == "1.00 KB"
        assert get_file_size_readable(1536) == "1.50 KB"
        assert get_file_size_readable(1024 * 1023) == "1023.00 KB"
    
    def test_megabytes(self):
        """Test megabyte sizes."""
        assert get_file_size_readable(1024 * 1024) == "1.00 MB"
        assert get_file_size_readable(1024 * 1024 * 5.5) == "5.50 MB"
    
    def test_gigabytes(self):
        """Test gigabyte sizes."""
        assert get_file_size_readable(1024 ** 3) == "1.00 GB"
        assert get_file_size_readable(1024 ** 3 * 2.5) == "2.50 GB"
    
    def test_terabytes(self):
        """Test terabyte sizes."""
        assert get_file_size_readable(1024 ** 4) == "1.00 TB"


class TestCheckDiskSpace:
    """Test disk space checking."""
    
    def test_check_existing_path(self):
        """Test checking disk space for existing path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            has_space, message = check_disk_space(tmpdir, required_mb=1)
            assert has_space is True
            assert "Available space" in message
    
    def test_check_insufficient_space(self):
        """Test when insufficient space."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Request impossible amount
            has_space, message = check_disk_space(tmpdir, required_mb=1000000000)
            assert has_space is False
            assert "Insufficient space" in message
    
    def test_check_invalid_path(self):
        """Test checking non-existent path."""
        has_space, message = check_disk_space("/invalid/path/that/doesnt/exist", 100)
        assert has_space is False
        assert "Error" in message


class TestListFilesWithPattern:
    """Test listing files with pattern."""
    
    def test_list_all_files(self):
        """Test listing all files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, 'file1.txt').touch()
            Path(tmpdir, 'file2.pdf').touch()
            Path(tmpdir, 'file3.doc').touch()
            
            files = list_files_with_pattern(tmpdir, "*")
            assert len(files) == 3
    
    def test_list_specific_extension(self):
        """Test listing files with specific extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, 'file1.txt').touch()
            Path(tmpdir, 'file2.txt').touch()
            Path(tmpdir, 'file3.pdf').touch()
            
            files = list_files_with_pattern(tmpdir, "*.txt")
            assert len(files) == 2
            assert all(f.endswith('.txt') for f in files)
    
    def test_list_nonexistent_directory(self):
        """Test listing files from non-existent directory."""
        files = list_files_with_pattern("/nonexistent/path", "*")
        assert files == []
    
    def test_list_files_sorted(self):
        """Test that files are returned sorted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files in random order
            Path(tmpdir, 'zebra.txt').touch()
            Path(tmpdir, 'apple.txt').touch()
            Path(tmpdir, 'banana.txt').touch()
            
            files = list_files_with_pattern(tmpdir, "*.txt")
            basenames = [os.path.basename(f) for f in files]
            assert basenames == ['apple.txt', 'banana.txt', 'zebra.txt']


class TestGetDirectoryStats:
    """Test directory statistics."""
    
    def test_stats_for_empty_directory(self):
        """Test stats for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats = get_directory_stats(tmpdir)
            assert stats['exists'] is True
            assert stats['total_files'] == 0
            assert stats['total_size_bytes'] == 0
    
    def test_stats_for_directory_with_files(self):
        """Test stats for directory with files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files with content
            file1 = Path(tmpdir, 'file1.txt')
            file1.write_text('Hello World')
            
            file2 = Path(tmpdir, 'file2.pdf')
            file2.write_bytes(b'PDF content here')
            
            stats = get_directory_stats(tmpdir)
            assert stats['exists'] is True
            assert stats['total_files'] == 2
            assert stats['total_size_bytes'] > 0
            assert '.txt' in stats['file_types']
            assert '.pdf' in stats['file_types']
            assert stats['file_types']['.txt'] == 1
            assert stats['file_types']['.pdf'] == 1
    
    def test_stats_for_nonexistent_directory(self):
        """Test stats for non-existent directory."""
        stats = get_directory_stats("/nonexistent/path")
        assert stats['exists'] is False
        assert stats['total_files'] == 0
    
    def test_stats_for_nested_structure(self):
        """Test stats for nested directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            subdir = Path(tmpdir, 'subdir')
            subdir.mkdir()
            
            Path(tmpdir, 'file1.txt').write_text('root file')
            Path(subdir, 'file2.txt').write_text('nested file')
            
            stats = get_directory_stats(tmpdir)
            assert stats['total_files'] == 2  # Should count recursively


if __name__ == "__main__":
    pytest.main([__file__, "-v"])