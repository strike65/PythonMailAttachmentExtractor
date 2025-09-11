#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pattern Matcher Module

Handles wildcard pattern matching for file filtering.
Supports Unix-style wildcards: *, ?, [seq], [!seq]
"""

import fnmatch
from typing import List, Optional, Dict, Tuple
from pathlib import Path


class PatternMatcher:
    """
    Pattern matching utility for filtering filenames based on wildcards.
    
    Supports:
    - Simple extensions (pdf, docx)
    - Wildcard patterns (*.pdf, report_*.doc)
    - Complex patterns (backup_20??.*, [!~]*)
    """
    
    @staticmethod
    def matches_pattern(filename: str, patterns: List[str]) -> bool:
        """
        Check if a filename matches any of the given patterns.
        
        Args:
            filename: The filename to check
            patterns: List of patterns (can be extensions or wildcards)
            
        Returns:
            True if filename matches at least one pattern
            
        Examples:
            >>> PatternMatcher.matches_pattern("report.pdf", ["*.pdf"])
            True
            >>> PatternMatcher.matches_pattern("file.doc", ["*.pdf", "*.doc"])
            True
            >>> PatternMatcher.matches_pattern("test.exe", ["*"])
            True
        """
        if not patterns:
            return False
            
        filename_lower = filename.lower()
        
        for pattern in patterns:
            if pattern is None:
                continue
                
            pattern_lower = pattern.lower().strip()
            
            # Special case: "*" matches everything
            if pattern_lower == '*':
                return True
            
            # Case 1: Simple extension without wildcards (e.g., "pdf", ".pdf")
            if not any(c in pattern_lower for c in ['*', '?', '[', ']']):
                # Normalize extension
                if not pattern_lower.startswith('.'):
                    ext_pattern = '.' + pattern_lower
                else:
                    ext_pattern = pattern_lower
                    
                # Check if filename ends with this extension
                if filename_lower.endswith(ext_pattern):
                    return True
            
            # Case 2: Pattern contains wildcards - use fnmatch
            else:
                if fnmatch.fnmatch(filename_lower, pattern_lower):
                    return True
                    
        return False
    
    @staticmethod
    def filter_files(
        filenames: List[str],
        allowed_patterns: Optional[List[str]] = None,
        excluded_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """
        Filter a list of filenames based on allowed and excluded patterns.
        
        Exclusions always have priority over allowed patterns.
        
        Args:
            filenames: List of filenames to filter
            allowed_patterns: Patterns for allowed files (None = allow all)
            excluded_patterns: Patterns for excluded files (None = exclude none)
            
        Returns:
            Filtered list of filenames
            
        Examples:
            >>> files = ["doc.pdf", "image.jpg", "script.exe"]
            >>> PatternMatcher.filter_files(files, ["*.pdf", "*.jpg"], ["*.exe"])
            ["doc.pdf", "image.jpg"]
        """
        filtered = []
        
        for filename in filenames:
            # First check exclusions (they have priority)
            if excluded_patterns and PatternMatcher.matches_pattern(filename, excluded_patterns):
                continue
                
            # Then check allowed patterns
            if allowed_patterns:
                if PatternMatcher.matches_pattern(filename, allowed_patterns):
                    filtered.append(filename)
            else:
                # No allowed patterns means everything is allowed (except excluded)
                filtered.append(filename)
                
        return filtered
    
    @staticmethod
    def should_include_file(
        filename: str,
        allowed_patterns: Optional[List[str]] = None,
        excluded_patterns: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        Determine if a file should be included based on patterns.
        
        Args:
            filename: The filename to check
            allowed_patterns: Patterns for allowed files
            excluded_patterns: Patterns for excluded files
            
        Returns:
            Tuple of (should_include, reason_message)
            
        Examples:
            >>> PatternMatcher.should_include_file("test.exe", ["*"], ["*.exe"])
            (False, "Matches exclusion pattern")
        """
        # Check exclusions first (priority)
        if excluded_patterns and PatternMatcher.matches_pattern(filename, excluded_patterns):
            return False, "Matches exclusion pattern"
        
        # Check allowed patterns
        if allowed_patterns:
            if PatternMatcher.matches_pattern(filename, allowed_patterns):
                return True, "Matches allowed pattern"
            else:
                return False, "Doesn't match allowed patterns"
        
        # No restrictions
        return True, "No restrictions"
    
    @staticmethod
    def validate_patterns(patterns: List[str]) -> Dict[str, List[str]]:
        """
        Validate and categorize patterns.
        
        Args:
            patterns: List of patterns to validate
            
        Returns:
            Dictionary with categorized patterns
            
        Examples:
            >>> PatternMatcher.validate_patterns(["pdf", "*.doc*", "*", "report_*"])
            {
                'simple_extensions': ['pdf'],
                'wildcard_patterns': ['*.doc*', 'report_*'],
                'match_all': ['*'],
                'invalid': []
            }
        """
        result = {
            'simple_extensions': [],
            'wildcard_patterns': [],
            'match_all': [],
            'invalid': []
        }
        
        for pattern in patterns:
            if pattern is None or pattern.strip() == '':
                result['invalid'].append(pattern)
                continue
                
            pattern = pattern.strip()
            
            # Match all pattern
            if pattern == '*':
                result['match_all'].append(pattern)
            # Simple extension (no wildcards)
            elif not any(c in pattern for c in ['*', '?', '[', ']']):
                result['simple_extensions'].append(pattern)
            # Wildcard pattern
            else:
                result['wildcard_patterns'].append(pattern)
                
        return result
    
    @staticmethod
    def expand_pattern(pattern: str, available_files: List[str]) -> List[str]:
        """
        Expand a pattern to show which files it would match.
        
        Useful for debugging and testing patterns.
        
        Args:
            pattern: The pattern to expand
            available_files: List of files to test against
            
        Returns:
            List of matching filenames
            
        Examples:
            >>> files = ["report_2023.pdf", "report_2024.pdf", "image.jpg"]
            >>> PatternMatcher.expand_pattern("report_*.pdf", files)
            ["report_2023.pdf", "report_2024.pdf"]
        """
        return [f for f in available_files if PatternMatcher.matches_pattern(f, [pattern])]
    
    @staticmethod
    def get_pattern_info(pattern: str) -> Dict[str, any]:
        """
        Get information about a pattern.
        
        Args:
            pattern: The pattern to analyze
            
        Returns:
            Dictionary with pattern information
        """
        info = {
            'pattern': pattern,
            'type': 'unknown',
            'has_wildcards': False,
            'is_extension': False,
            'matches_all': False,
            'description': ''
        }
        
        if pattern == '*':
            info['type'] = 'match_all'
            info['matches_all'] = True
            info['description'] = 'Matches all files'
            
        elif not any(c in pattern for c in ['*', '?', '[', ']']):
            info['type'] = 'simple_extension'
            info['is_extension'] = True
            ext = pattern if pattern.startswith('.') else f'.{pattern}'
            info['description'] = f'Files ending with {ext}'
            
        else:
            info['type'] = 'wildcard'
            info['has_wildcards'] = True
            
            # Provide human-readable descriptions for common patterns
            if pattern.startswith('*.'):
                ext = pattern[2:]
                info['description'] = f'All files with .{ext} extension'
            elif pattern.endswith('*'):
                prefix = pattern[:-1]
                info['description'] = f'Files starting with "{prefix}"'
            elif '*' in pattern:
                info['description'] = f'Files matching pattern "{pattern}"'
            else:
                info['description'] = f'Complex pattern: {pattern}'
                
        return info
    
    @staticmethod
    def suggest_patterns(filenames: List[str]) -> Dict[str, List[str]]:
        """
        Suggest patterns based on a list of filenames.
        
        Analyzes filenames to suggest useful patterns.
        
        Args:
            filenames: List of filenames to analyze
            
        Returns:
            Dictionary with suggested patterns by category
        """
        from collections import Counter
        import os
        
        suggestions = {
            'extensions': [],
            'prefixes': [],
            'patterns': []
        }
        
        # Collect extensions
        extensions = Counter()
        prefixes = Counter()
        
        for filename in filenames:
            # Get extension
            _, ext = os.path.splitext(filename)
            if ext:
                extensions[ext.lower()] += 1
            
            # Get common prefixes (first word before _ or -)
            for delimiter in ['_', '-']:
                if delimiter in filename:
                    prefix = filename.split(delimiter)[0]
                    if len(prefix) > 2:  # Meaningful prefix
                        prefixes[prefix.lower()] += 1
                    break
        
        # Suggest extension patterns
        for ext, count in extensions.most_common(5):
            if count > 1:  # Only if appears multiple times
                suggestions['extensions'].append(f'*{ext}')
        
        # Suggest prefix patterns
        for prefix, count in prefixes.most_common(5):
            if count > 1:
                suggestions['prefixes'].append(f'{prefix}*')
        
        # Suggest year-based patterns if applicable
        import re
        year_pattern = re.compile(r'20\d{2}')
        years_found = set()
        
        for filename in filenames:
            matches = year_pattern.findall(filename)
            years_found.update(matches)
        
        if len(years_found) > 1:
            suggestions['patterns'].append('*20??*')  # Files containing years 2000-2099
            
        return suggestions


class PatternCollection:
    """
    A collection of commonly used pattern sets.
    
    Provides pre-defined pattern sets for common use cases.
    """
    
    # Document patterns
    DOCUMENTS = [
        "*.pdf",
        "*.doc*",  # doc, docx, docm
        "*.xls*",  # xls, xlsx, xlsm
        "*.ppt*",  # ppt, pptx
        "*.txt",
        "*.rtf",
        "*.odt",
        "*.ods",
        "*.odp"
    ]
    
    # Image patterns
    IMAGES = [
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.gif",
        "*.bmp",
        "*.svg",
        "*.tiff",
        "*.tif",
        "*.webp",
        "*.ico"
    ]
    
    # Archive patterns
    ARCHIVES = [
        "*.zip",
        "*.rar",
        "*.7z",
        "*.tar",
        "*.gz",
        "*.bz2",
        "*.xz"
    ]
    
    # Executable/dangerous patterns
    DANGEROUS = [
        "*.exe",
        "*.bat",
        "*.cmd",
        "*.sh",
        "*.dll",
        "*.scr",
        "*.vbs",
        "*.js",
        "*.jar",
        "*.app",
        "*.msi",
        "*.com"
    ]
    
    # Temporary/backup patterns
    TEMPORARY = [
        "*.tmp",
        "*.temp",
        "*.cache",
        "*.bak",
        "*.backup",
        "~*",        # Unix backup files
        "*.swp",     # Vim swap files
        ".DS_Store", # macOS
        "Thumbs.db"  # Windows
    ]
    
    @classmethod
    def get_collection(cls, name: str) -> List[str]:
        """
        Get a predefined pattern collection by name.
        
        Args:
            name: Name of the collection (documents, images, archives, dangerous, temporary)
            
        Returns:
            List of patterns or empty list if not found
        """
        collections = {
            'documents': cls.DOCUMENTS,
            'images': cls.IMAGES,
            'archives': cls.ARCHIVES,
            'dangerous': cls.DANGEROUS,
            'temporary': cls.TEMPORARY
        }
        return collections.get(name.lower(), [])