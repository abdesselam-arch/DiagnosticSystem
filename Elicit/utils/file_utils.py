"""
Diagnostic Collection System - File Utilities

This module provides utility functions for file operations commonly needed
throughout the diagnostic collection system, with consistent error handling
and logging.
"""

import os
import json
import shutil
import tempfile
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, BinaryIO, TextIO

logger = logging.getLogger(__name__)


def ensure_directory(directory_path: str) -> bool:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path (str): Path to the directory to ensure.
        
    Returns:
        bool: True if the directory exists or was created, False otherwise.
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error ensuring directory {directory_path}: {str(e)}")
        return False


def safe_read_json(file_path: str, default_value: Any = None) -> Any:
    """Safely read a JSON file with error handling.
    
    Args:
        file_path (str): Path to the JSON file.
        default_value (Any, optional): Default value to return if reading fails. Defaults to None.
        
    Returns:
        Any: Parsed JSON data, or default_value if reading fails.
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}")
            return default_value
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        return default_value
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return default_value


def safe_write_json(file_path: str, data: Any, indent: int = 2,
                   atomic: bool = True, create_backup: bool = False) -> bool:
    """Safely write data to a JSON file with error handling.
    
    Args:
        file_path (str): Path to write the JSON file.
        data (Any): Data to write (must be JSON serializable).
        indent (int, optional): JSON indentation level. Defaults to 2.
        atomic (bool, optional): Whether to use atomic writing. Defaults to True.
        create_backup (bool, optional): Whether to create a backup of existing file. Defaults to False.
        
    Returns:
        bool: True if writing was successful, False otherwise.
    """
    try:
        # Ensure directory exists
        ensure_directory(os.path.dirname(file_path))
        
        # Create backup if requested
        if create_backup and os.path.exists(file_path):
            create_file_backup(file_path)
        
        if atomic:
            # Write to temporary file first
            temp_file = f"{file_path}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent)
            
            # Replace original file with temporary file
            if os.path.exists(file_path):
                os.replace(temp_file, file_path)
            else:
                os.rename(temp_file, file_path)
        else:
            # Direct write
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent)
        
        return True
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {str(e)}")
        return False


def create_file_backup(file_path: str, backup_dir: str = None) -> Optional[str]:
    """Create a backup of a file.
    
    Args:
        file_path (str): Path to the file to back up.
        backup_dir (str, optional): Directory to store the backup. 
                                   Defaults to None (same directory with timestamp).
        
    Returns:
        str: Path to the backup file, or None if backup failed.
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Cannot back up nonexistent file: {file_path}")
            return None
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_filename = f"{os.path.splitext(filename)[0]}_{timestamp}{os.path.splitext(filename)[1]}"
        
        # Determine backup directory
        if backup_dir:
            ensure_directory(backup_dir)
            backup_path = os.path.join(backup_dir, backup_filename)
        else:
            backup_path = os.path.join(os.path.dirname(file_path), backup_filename)
        
        # Create backup
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup at {backup_path}")
        
        return backup_path
    except Exception as e:
        logger.error(f"Error creating backup of {file_path}: {str(e)}")
        return None


def get_file_extension(file_path: str) -> str:
    """Get the extension of a file.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        str: File extension without the dot, or empty string if no extension.
    """
    _, ext = os.path.splitext(file_path)
    return ext[1:] if ext else ""


def is_json_file(file_path: str) -> bool:
    """Check if a file is a JSON file.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        bool: True if the file is a JSON file, False otherwise.
    """
    ext = get_file_extension(file_path).lower()
    if ext != "json":
        return False
    
    # Check content if the file exists
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except:
            return False
    
    return False


def list_files_with_extension(directory: str, extension: str) -> List[str]:
    """List all files in a directory with a specific extension.
    
    Args:
        directory (str): Directory to search.
        extension (str): File extension to filter by (without the dot).
        
    Returns:
        list: List of file paths.
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return []
    
    # Ensure extension doesn't have a leading dot
    if extension.startswith('.'):
        extension = extension[1:]
    
    # Find matching files
    matching_files = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(f".{extension.lower()}"):
            matching_files.append(os.path.join(directory, filename))
            
    return matching_files


def get_newest_file(directory: str, extension: str = None) -> Optional[str]:
    """Get the newest file in a directory, optionally filtered by extension.
    
    Args:
        directory (str): Directory to search.
        extension (str, optional): File extension to filter by. Defaults to None.
        
    Returns:
        str: Path to the newest file, or None if no files found.
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return None
    
    # Get list of files
    if extension:
        files = list_files_with_extension(directory, extension)
    else:
        files = [os.path.join(directory, f) for f in os.listdir(directory) 
                if os.path.isfile(os.path.join(directory, f))]
    
    if not files:
        return None
    
    # Find newest file
    return max(files, key=os.path.getmtime)


def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get information about a file.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        dict: Dictionary with file information.
    """
    info = {
        "exists": False,
        "is_file": False,
        "is_dir": False,
        "size": 0,
        "modified": None,
        "created": None,
        "extension": "",
        "filename": os.path.basename(file_path),
        "path": os.path.abspath(file_path)
    }
    
    if os.path.exists(file_path):
        info["exists"] = True
        info["is_file"] = os.path.isfile(file_path)
        info["is_dir"] = os.path.isdir(file_path)
        
        if info["is_file"]:
            info["size"] = os.path.getsize(file_path)
            info["modified"] = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            info["created"] = datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
            info["extension"] = get_file_extension(file_path)
    
    return info


def safe_delete_file(file_path: str, create_backup: bool = False) -> bool:
    """Safely delete a file with optional backup.
    
    Args:
        file_path (str): Path to the file to delete.
        create_backup (bool, optional): Whether to create a backup before deleting. Defaults to False.
        
    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Cannot delete nonexistent file: {file_path}")
            return False
        
        # Create backup if requested
        if create_backup:
            create_file_backup(file_path)
        
        # Delete file
        os.remove(file_path)
        logger.info(f"Deleted file: {file_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        return False


def create_temp_copy(file_path: str) -> Optional[str]:
    """Create a temporary copy of a file.
    
    Args:
        file_path (str): Path to the file to copy.
        
    Returns:
        str: Path to the temporary copy, or None if copying failed.
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Cannot copy nonexistent file: {file_path}")
            return None
        
        # Create temp file
        ext = get_file_extension(file_path)
        fd, temp_path = tempfile.mkstemp(suffix=f".{ext}")
        os.close(fd)
        
        # Copy content
        shutil.copy2(file_path, temp_path)
        
        return temp_path
    except Exception as e:
        logger.error(f"Error creating temp copy of {file_path}: {str(e)}")
        return None


def safe_move_file(source_path: str, dest_path: str, overwrite: bool = False) -> bool:
    """Safely move a file with error handling.
    
    Args:
        source_path (str): Path to the source file.
        dest_path (str): Destination path.
        overwrite (bool, optional): Whether to overwrite existing destination. Defaults to False.
        
    Returns:
        bool: True if the move was successful, False otherwise.
    """
    try:
        if not os.path.exists(source_path):
            logger.warning(f"Cannot move nonexistent file: {source_path}")
            return False
        
        # Check if destination exists
        if os.path.exists(dest_path) and not overwrite:
            logger.warning(f"Destination file exists and overwrite is False: {dest_path}")
            return False
        
        # Ensure destination directory exists
        ensure_directory(os.path.dirname(dest_path))
        
        # Move file
        shutil.move(source_path, dest_path)
        logger.info(f"Moved file from {source_path} to {dest_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error moving file from {source_path} to {dest_path}: {str(e)}")
        return False


def read_text_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """Read text from a file with error handling.
    
    Args:
        file_path (str): Path to the text file.
        encoding (str, optional): File encoding. Defaults to 'utf-8'.
        
    Returns:
        str: File content, or None if reading failed.
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}")
            return None
        
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None


def write_text_file(file_path: str, content: str, encoding: str = 'utf-8',
                   atomic: bool = True, create_backup: bool = False) -> bool:
    """Write text to a file with error handling.
    
    Args:
        file_path (str): Path to write the text file.
        content (str): Content to write.
        encoding (str, optional): File encoding. Defaults to 'utf-8'.
        atomic (bool, optional): Whether to use atomic writing. Defaults to True.
        create_backup (bool, optional): Whether to create a backup of existing file. Defaults to False.
        
    Returns:
        bool: True if writing was successful, False otherwise.
    """
    try:
        # Ensure directory exists
        ensure_directory(os.path.dirname(file_path))
        
        # Create backup if requested
        if create_backup and os.path.exists(file_path):
            create_file_backup(file_path)
        
        if atomic:
            # Write to temporary file first
            temp_file = f"{file_path}.tmp"
            with open(temp_file, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Replace original file with temporary file
            if os.path.exists(file_path):
                os.replace(temp_file, file_path)
            else:
                os.rename(temp_file, file_path)
        else:
            # Direct write
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
        
        return True
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {str(e)}")
        return False


def find_files_by_content(directory: str, search_text: str, 
                         extension: str = None, recursive: bool = False) -> List[str]:
    """Find files containing specific text.
    
    Args:
        directory (str): Directory to search.
        search_text (str): Text to search for.
        extension (str, optional): File extension to filter by. Defaults to None.
        recursive (bool, optional): Whether to search subdirectories. Defaults to False.
        
    Returns:
        list: List of file paths containing the search text.
    """
    matching_files = []
    
    try:
        # Walk directory
        for root, dirs, files in os.walk(directory):
            # Process files in current directory
            for filename in files:
                # Check extension if specified
                if extension and not filename.lower().endswith(f".{extension.lower()}"):
                    continue
                
                # Check file content
                file_path = os.path.join(root, filename)
                try:
                    # Read file content (assume text file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # Check if search text is in content
                    if search_text in content:
                        matching_files.append(file_path)
                except:
                    # Skip files that can't be read as text
                    continue
            
            # Stop if not recursive
            if not recursive:
                break
    except Exception as e:
        logger.error(f"Error searching files in {directory}: {str(e)}")
    
    return matching_files


def rotate_files(directory: str, pattern: str, max_files: int = 10) -> int:
    """Rotate files matching a pattern, keeping only the newest ones.
    
    Args:
        directory (str): Directory containing files.
        pattern (str): Pattern to match filenames (e.g., "backup_*.json").
        max_files (int, optional): Maximum number of files to keep. Defaults to 10.
        
    Returns:
        int: Number of files deleted.
    """
    try:
        import glob
        
        # Find matching files
        file_pattern = os.path.join(directory, pattern)
        files = glob.glob(file_pattern)
        
        # Sort by modification time (oldest first)
        files.sort(key=os.path.getmtime)
        
        # Delete oldest files if there are too many
        files_to_delete = files[:-max_files] if len(files) > max_files else []
        
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                logger.info(f"Rotated out old file: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file during rotation: {file_path}: {str(e)}")
        
        return len(files_to_delete)
    except Exception as e:
        logger.error(f"Error rotating files in {directory}: {str(e)}")
        return 0


def get_directory_size(directory: str) -> int:
    """Get the total size of a directory in bytes.
    
    Args:
        directory (str): Directory to measure.
        
    Returns:
        int: Total size in bytes.
    """
    total_size = 0
    
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                total_size += os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error calculating directory size for {directory}: {str(e)}")
    
    return total_size


def is_path_safe(path: str, allowed_dirs: List[str] = None) -> bool:
    """Check if a file path is safe (not escaping allowed directories).
    
    Args:
        path (str): Path to check.
        allowed_dirs (list, optional): List of allowed directories. Defaults to None.
        
    Returns:
        bool: True if the path is safe, False otherwise.
    """
    # Normalize path to absolute path
    abs_path = os.path.abspath(path)
    
    # If allowed_dirs is provided, check if path is within any of them
    if allowed_dirs:
        return any(os.path.commonpath([abs_path, allowed_dir]) == allowed_dir 
                 for allowed_dir in [os.path.abspath(d) for d in allowed_dirs])
    
    # Basic safety checks
    if os.path.islink(abs_path):
        return False  # Don't allow symlinks
    
    # Check for suspicious patterns
    suspicious_patterns = ['../', '..\\', '~', '$', '|', ';', '&', '*', '?', '<', '>', '{', '}']
    return not any(pattern in path for pattern in suspicious_patterns)