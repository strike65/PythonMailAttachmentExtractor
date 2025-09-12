#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Pattern Matcher Module
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.pattern_matcher import PatternMatcher, PatternCollection


class TestPatternMatcher:
    """Test PatternMatcher class functionality."""
    
    def test_simple_extension_matching(self):
        """Test matching simple extensions without wildcards."""
        assert PatternMatcher.matches_pattern("document.pdf", ["pdf"])
        assert PatternMatcher.matches_pattern("document.pdf", [".pdf"])
        assert not PatternMatcher.matches_pattern("document.doc", ["pdf"])
        assert PatternMatcher.matches_pattern("IMAGE.JPG", ["jpg"])  # Case insensitive
    
    def test_wildcard_all_matching(self):
        """Test the special '*' pattern that matches everything."""
        patterns = ["*"]
        assert PatternMatcher.matches_pattern("anything.pdf", patterns)
        assert PatternMatcher.matches_pattern("test.exe", patterns)
        assert PatternMatcher.matches_pattern("no_extension", patterns)
    
    def test_wildcard_extension_matching(self):
        """Test wildcard patterns for extensions."""
        # *.extension patterns
        assert PatternMatcher.matches_pattern("file.pdf", ["*.pdf"])
        assert PatternMatcher.matches_pattern("document.docx", ["*.doc*"])
        assert PatternMatcher.matches_pattern("spreadsheet.xlsx", ["*.xls*"])
        assert not PatternMatcher.matches_pattern("image.jpg", ["*.pdf"])
    
    def test_complex_wildcard_patterns(self):
        """Test complex wildcard patterns."""
        # Prefix patterns
        assert PatternMatcher.matches_pattern("report_2024.pdf", ["report_*"])
        assert PatternMatcher.matches_pattern("IMG_1234.jpg", ["IMG_*.jpg"])
        assert not PatternMatcher.matches_pattern("DOC_1234.jpg", ["IMG_*.jpg"])
        
        # Year patterns
        assert PatternMatcher.matches_pattern("backup_2023.zip", ["backup_20??.zip"])
        assert not PatternMatcher.matches_pattern("backup_1999.zip", ["backup_20??.zip"])
    
    def test_character_set_patterns(self):
        """Test [seq] and [!seq] patterns."""
        # Character sets
        assert PatternMatcher.matches_pattern("file1.txt", ["file[123].txt"])
        assert PatternMatcher.matches_pattern("file2.txt", ["file[123].txt"])
        assert not PatternMatcher.matches_pattern("file4.txt", ["file[123].txt"])
        
        # Negated sets
        assert PatternMatcher.matches_pattern("fileA.txt", ["file[!0-9].txt"])
        assert not PatternMatcher.matches_pattern("file1.txt", ["file[!0-9].txt"])
    
    def test_filter_files(self):
        """Test filtering a list of files."""
        files = [
            "document.pdf",
            "report.docx",
            "script.exe",
            "image.jpg",
            "data.xlsx",
            "virus.bat"
        ]
        
        # Allow only documents
        result = PatternMatcher.filter_files(
            files,
            allowed_patterns=["*.pdf", "*.doc*", "*.xls*"],
            excluded_patterns=None
        )
        assert set(result) == {"document.pdf", "report.docx", "data.xlsx"}
        
        # Allow all except dangerous
        result = PatternMatcher.filter_files(
            files,
            allowed_patterns=None,
            excluded_patterns=["*.exe", "*.bat"]
        )
        assert set(result) == {"document.pdf", "report.docx", "image.jpg", "data.xlsx"}
        
        # Combined: documents except those starting with 'report'
        result = PatternMatcher.filter_files(
            files,
            allowed_patterns=["*.pdf", "*.doc*"],
            excluded_patterns=["report*"]
        )
        assert set(result) == {"document.pdf"}
    
    def test_should_include_file(self):
        """Test should_include_file with reason messages."""
        # Excluded file
        should_include, reason = PatternMatcher.should_include_file(
            "virus.exe",
            allowed_patterns=["*"],
            excluded_patterns=["*.exe"]
        )
        assert not should_include
        assert "exclusion" in reason.lower()
        
        # Allowed file
        should_include, reason = PatternMatcher.should_include_file(
            "document.pdf",
            allowed_patterns=["*.pdf"],
            excluded_patterns=None
        )
        assert should_include
        assert "allowed" in reason.lower()
        
        # Not in allowed list
        should_include, reason = PatternMatcher.should_include_file(
            "image.jpg",
            allowed_patterns=["*.pdf"],
            excluded_patterns=None
        )
        assert not should_include
        assert "doesn't match" in reason.lower()
    
    def test_validate_patterns(self):
        """Test pattern validation and categorization."""
        patterns = ["pdf", "*.doc*", "*", "report_*", "", None]
        result = PatternMatcher.validate_patterns(patterns)
        
        assert "pdf" in result['simple_extensions']
        assert "*.doc*" in result['wildcard_patterns']
        assert "*" in result['match_all']
        assert "report_*" in result['wildcard_patterns']
        assert "" in result['invalid']
        assert None in result['invalid']
    
    def test_expand_pattern(self):
        """Test expanding patterns to show matches."""
        files = [
            "report_2023.pdf",
            "report_2024.pdf",
            "invoice_2024.pdf",
            "image.jpg"
        ]
        
        matches = PatternMatcher.expand_pattern("report_*.pdf", files)
        assert set(matches) == {"report_2023.pdf", "report_2024.pdf"}
        
        matches = PatternMatcher.expand_pattern("*.pdf", files)
        assert len(matches) == 3
        assert "image.jpg" not in matches
    
    def test_pattern_info(self):
        """Test getting pattern information."""
        # Match all
        info = PatternMatcher.get_pattern_info("*")
        assert info['type'] == 'match_all'
        assert info['matches_all'] is True
        
        # Simple extension
        info = PatternMatcher.get_pattern_info("pdf")
        assert info['type'] == 'simple_extension'
        assert info['is_extension'] is True
        
        # Wildcard pattern
        info = PatternMatcher.get_pattern_info("*.pdf")
        assert info['type'] == 'wildcard'
        assert info['has_wildcards'] is True
    
    def test_suggest_patterns(self):
        """Test pattern suggestions based on filenames."""
        filenames = [
            "report_2023.pdf",
            "report_2024.pdf",
            "invoice_001.pdf",
            "invoice_002.pdf",
            "data_2023.xlsx",
            "data_2024.xlsx"
        ]
        
        suggestions = PatternMatcher.suggest_patterns(filenames)
        
        # Should suggest common extensions
        assert any('.pdf' in ext for ext in suggestions['extensions'])
        assert any('.xlsx' in ext for ext in suggestions['extensions'])
        
        # Should suggest common prefixes
        assert any('report' in prefix for prefix in suggestions['prefixes'])
        assert any('invoice' in prefix for prefix in suggestions['prefixes'])
        
        # Should suggest year pattern
        assert '*20??*' in suggestions['patterns']
    
    def test_empty_and_none_patterns(self):
        """Test handling of empty and None pattern lists."""
        # Empty list
        assert not PatternMatcher.matches_pattern("file.pdf", [])
        
        # None patterns in list
        assert PatternMatcher.matches_pattern("file.pdf", [None, "pdf", None])
        assert not PatternMatcher.matches_pattern("file.pdf", [None, None])
    
    def test_special_characters_in_filenames(self):
        """Test handling of special characters in filenames."""
        # Spaces
        assert PatternMatcher.matches_pattern("my document.pdf", ["*.pdf"])
        
        # Parentheses
        assert PatternMatcher.matches_pattern("file(1).pdf", ["*.pdf"])
        
        # Brackets
        assert PatternMatcher.matches_pattern("file[backup].pdf", ["*.pdf"])


class TestPatternCollection:
    """Test PatternCollection predefined patterns."""
    
    def test_documents_collection(self):
        """Test DOCUMENTS pattern collection."""
        patterns = PatternCollection.DOCUMENTS
        assert "*.pdf" in patterns
        assert "*.doc*" in patterns
        assert "*.xls*" in patterns
    
    def test_images_collection(self):
        """Test IMAGES pattern collection."""
        patterns = PatternCollection.IMAGES
        assert "*.jpg" in patterns
        assert "*.png" in patterns
        assert "*.gif" in patterns
    
    def test_dangerous_collection(self):
        """Test DANGEROUS pattern collection."""
        patterns = PatternCollection.DANGEROUS
        assert "*.exe" in patterns
        assert "*.bat" in patterns
        assert "*.dll" in patterns
    
    def test_get_collection(self):
        """Test getting collections by name."""
        docs = PatternCollection.get_collection('documents')
        assert "*.pdf" in docs
        
        images = PatternCollection.get_collection('IMAGES')  # Case insensitive
        assert "*.jpg" in images
        
        unknown = PatternCollection.get_collection('unknown')
        assert unknown == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])