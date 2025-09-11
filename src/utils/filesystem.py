#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filesystem Utilities Module

Cross-platform filesystem operations for the email attachment extractor.
"""

import os
import re
import platform
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime

from .colors import Colors


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe use across all platforms.
    
    Removes or replaces characters that are invalid on Windows/Unix/macOS.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for all platforms
    """
    if not filename:
        return 'unnamed'
    
    # Remove invalid characters for all platforms
    # Windows: < > : " / \ | ? * and ASCII 0-31
    # Unix/Linux/macOS: mainly / and null
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip().rstrip('.')
    
    # Handle Windows reserved names
    if platform.system() == 'Windows':
        reserved = ['CON', 'PRN', 'AUX', 'NUL']
        reserved += [f'COM{i}' for i in range(1, 10)]
        reserved += [f'LPT{i}' for i in range(1, 10)]
        
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in reserved:
            filename = f'_{filename}'
    
    # Limit filename length (255 for most systems, but be conservative)
    max_length = 200
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    # Ensure filename is not empty after sanitization
    return filename or 'unnamed'


def get_unique_filename(directory: str, filename: str) -> str:
    """
    Generate a unique filename if the file already exists.
    
    Args:
        directory: Directory where file will be saved
        filename: Desired filename
        
    Returns:
        Unique filename (original or with number suffix)
    """
    filepath = os.path.join(directory, filename)
    
    if not os.path.exists(filepath):
        return filename
    
    # Split name and extension
    name, ext = os.path.splitext(filename)
    counter = 1
    
    while True:
        candidate = f"{name}_{counter}{ext}"
        candidate_path = os.path.join(directory, candidate)
        if not os.path.exists(candidate_path):
            return candidate
        counter += 1
        
        # Safety check to avoid infinite loop
        if counter > 9999:
            # Use timestamp as last resort
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"{name}_{timestamp}{ext}"


def create_directory(path: str) -> bool:
    """
    Create a directory if it doesn't exist.
    
    Args:
        path: Directory path to create
        
    Returns:
        True if successful or already exists, False on error
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(Colors.error(f"Error creating directory {path}: {e}"))
        return False


def get_file_size_readable(size_bytes: int) -> str:
    """
    Convert file size to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_available_drives() -> Optional[str]:
    """
    Get available drives/volumes based on the operating system.
    
    Returns:
        Selected drive path or None if cancelled
    """
    system = platform.system()
    volumes = []
    
    if system == 'Darwin':  # macOS
        volumes = _get_macos_volumes()
    elif system == 'Windows':
        volumes = _get_windows_drives()
    else:  # Linux and other Unix-like systems
        volumes = _get_linux_mounts()
    
    if not volumes:
        print(Colors.error("No drives found"))
        return None
    
    # Display available drives
    print(Colors.info("\nAvailable drives:"))
    print("-" * 60)
    
    for idx, vol in enumerate(volumes, 1):
        if vol.get('free_gb', 'N/A') != 'N/A':
            print(f"{idx}. {vol['name']} - {vol['free_gb']:.2f} GB free of {vol['total_gb']:.2f} GB")
        else:
            print(f"{idx}. {vol['name']}")
    
    # Let user select
    while True:
        choice = input(Colors.cyan(f"\nSelect a drive (1-{len(volumes)}) or 'q' to quit: ")).strip()
        
        if choice.lower() == 'q':
            return None
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(volumes):
                selected = volumes[idx]
                
                # Ask for subdirectory
                subdir = input(Colors.cyan(f"\nSubfolder on {selected['name']} (Enter for root): ")).strip()
                
                if subdir:
                    full_path = os.path.join(selected['path'], subdir)
                else:
                    full_path = selected['path']
                
                # Create directory if it doesn't exist
                create_directory(full_path)
                return full_path
                
        except ValueError:
            pass
            
        print(Colors.error("Invalid selection"))


def _get_macos_volumes() -> List[Dict]:
    """Get available volumes on macOS."""
    volumes = []
    volumes_path = "/Volumes"
    
    try:
        entries = os.listdir(volumes_path)
    except Exception:
        return volumes
    
    for item in entries:
        path = os.path.join(volumes_path, item)
        if os.path.isdir(path):
            try:
                stat = os.statvfs(path)
                free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
                total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
                volumes.append({
                    'name': item,
                    'path': path,
                    'free_gb': free_gb,
                    'total_gb': total_gb
                })
            except Exception:
                volumes.append({
                    'name': item,
                    'path': path,
                    'free_gb': 'N/A',
                    'total_gb': 'N/A'
                })
    
    return volumes


def _get_windows_drives() -> List[Dict]:
    """Get available drives on Windows."""
    import string
    volumes = []
    
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            try:
                total, used, free = shutil.disk_usage(drive)
                volumes.append({
                    'name': f"Drive {letter}:",
                    'path': drive,
                    'free_gb': free / (1024**3),
                    'total_gb': total / (1024**3)
                })
            except:
                volumes.append({
                    'name': f"Drive {letter}:",
                    'path': drive,
                    'free_gb': 'N/A',
                    'total_gb': 'N/A'
                })
    
    return volumes


def _get_linux_mounts() -> List[Dict]:
    """Get available mount points on Linux."""
    volumes = []
    
    # Add home directory
    home = os.path.expanduser("~")
    try:
        stat = os.statvfs(home)
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
        volumes.append({
            'name': 'Home',
            'path': home,
            'free_gb': free_gb,
            'total_gb': total_gb
        })
    except:
        volumes.append({
            'name': 'Home',
            'path': home,
            'free_gb': 'N/A',
            'total_gb': 'N/A'
        })
    
    # Check for mounted drives in common locations
    mount_points = ['/media', '/mnt']
    
    for mount_base in mount_points:
        if os.path.exists(mount_base):
            try:
                for item in os.listdir(mount_base):
                    path = os.path.join(mount_base, item)
                    if os.path.ismount(path) or os.path.isdir(path):
                        try:
                            stat = os.statvfs(path)
                            free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
                            total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
                            volumes.append({
                                'name': item,
                                'path': path,
                                'free_gb': free_gb,
                                'total_gb': total_gb
                            })
                        except:
                            pass
            except:
                pass
    
    return volumes


def check_disk_space(path: str, required_mb: float = 100) -> Tuple[bool, str]:
    """
    Check if there's enough disk space available.
    
    Args:
        path: Path to check
        required_mb: Required space in MB
        
    Returns:
        Tuple of (has_enough_space, message)
    """
    try:
        stat = shutil.disk_usage(path)
        free_mb = stat.free / (1024 * 1024)
        
        if free_mb >= required_mb:
            return True, f"Available space: {free_mb:.2f} MB"
        else:
            return False, f"Insufficient space: {free_mb:.2f} MB available, {required_mb:.2f} MB required"
            
    except Exception as e:
        return False, f"Error checking disk space: {e}"


def list_files_with_pattern(directory: str, pattern: str = "*") -> List[str]:
    """
    List files in directory matching a pattern.
    
    Args:
        directory: Directory to search
        pattern: Glob pattern (default: "*" for all files)
        
    Returns:
        List of matching file paths
    """
    try:
        path = Path(directory)
        if not path.exists():
            return []
            
        files = []
        for file_path in path.glob(pattern):
            if file_path.is_file():
                files.append(str(file_path))
                
        return sorted(files)
        
    except Exception as e:
        print(Colors.error(f"Error listing files: {e}"))
        return []


def get_directory_stats(directory: str) -> Dict:
    """
    Get statistics about a directory.
    
    Args:
        directory: Directory path
        
    Returns:
        Dictionary with directory statistics
    """
    stats = {
        'exists': False,
        'total_files': 0,
        'total_size_bytes': 0,
        'total_size_readable': '0 B',
        'file_types': {},
        'largest_file': None,
        'newest_file': None
    }
    
    try:
        path = Path(directory)
        if not path.exists():
            return stats
            
        stats['exists'] = True
        newest_time = 0
        largest_size = 0
        
        for file_path in path.rglob('*'):
            if file_path.is_file():
                stats['total_files'] += 1
                
                # File size
                size = file_path.stat().st_size
                stats['total_size_bytes'] += size
                
                # Track largest file
                if size > largest_size:
                    largest_size = size
                    stats['largest_file'] = {
                        'path': str(file_path),
                        'size': get_file_size_readable(size)
                    }
                
                # Track newest file
                mtime = file_path.stat().st_mtime
                if mtime > newest_time:
                    newest_time = mtime
                    stats['newest_file'] = {
                        'path': str(file_path),
                        'modified': datetime.fromtimestamp(mtime).isoformat()
                    }
                
                # Count file types
                ext = file_path.suffix.lower()
                if ext:
                    stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
        
        stats['total_size_readable'] = get_file_size_readable(stats['total_size_bytes'])
        
    except Exception as e:
        print(Colors.error(f"Error getting directory stats: {e}"))
    
    return stats


def safe_move(source: str, destination: str) -> bool:
    """
    Safely move a file or directory.
    
    Args:
        source: Source path
        destination: Destination path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        shutil.move(source, destination)
        return True
    except Exception as e:
        print(Colors.error(f"Error moving {source} to {destination}: {e}"))
        return False


def safe_copy(source: str, destination: str) -> bool:
    """
    Safely copy a file or directory.
    
    Args:
        source: Source path
        destination: Destination path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        return True
    except Exception as e:
        print(Colors.error(f"Error copying {source} to {destination}: {e}"))
        return False