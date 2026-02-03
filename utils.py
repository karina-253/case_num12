import os
import platform
from pathlib import Path
from typing import Union, List, Tuple
import re
import local as lcl

PathString = Union[str, Path]


def is_windows_os() -> bool:
    """Checks whether current OS is Windows.

    Args:
        None

    Returns:
        bool: True if the OS is Windows, False otherwise
    """

    return platform.system() == "Windows"


def validate_windows_path(path: PathString) -> Tuple[bool, str]:
    """Validates a Windows file system path according to Windows rules.
    Performs checks for:
    - Empty paths
    - Drive format
    - UNC paths
    - Forbidden characters
    - Reserved device names
    - Trailing spaces or dots
    - Path length limits
    - Mixed or duplicate separators
    - NTFS discouraged characters

    Args:
        path (str | Path): Path to validate.

    Returns:
        tuple:
            bool: True if path is valid.
            str: Validation result message.
    """

    p_str = str(path)

    if not p_str.strip():
        return False, "Путь не может быть пустым"

    disk_match = re.match(r'^([A-Za-z]):', p_str)
    remaining_path = p_str

    if disk_match:
        disk_prefix = disk_match.group(0)
        remaining_path = p_str[len(disk_prefix):]

        if not re.match(r'^[A-Za-z]:$', disk_prefix):
            return False, f"{lcl.INCORRECT1}: {disk_prefix}"

    elif p_str.startswith('\\'):
        if p_str.startswith('\\\\'):
            if len(p_str) < 4 or '\\' not in p_str[2:]:
                return False, f'{lcl.INCORRECT2}'


    forbidden_chars = ['<', '>', ':', '"', '|', '?', '*']

    colon_count = p_str.count(':')
    if colon_count > 1:
        return False, f'{lcl.COLON1}'

    if colon_count == 1 and not disk_match:
        return False, f'{lcl.COLON2}'
    for char in forbidden_chars:
        if char in remaining_path:
            return False, f" f'{lcl.SYMBOL}' : '{char}'"

    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]

    path_parts = [part for part in re.split(r'[\\/]+', remaining_path) if part]

    for part in path_parts:
        name_without_ext = os.path.splitext(part)[0].upper()
        if name_without_ext in reserved_names:
            return False, f"f'{lcl.NAME1}' : {part}"

        if part.endswith('.'):
            return False, f'{lcl.NAME2}'
        if part.endswith(' '):
            return False, f'{lcl.NAME3}'
        if part.startswith(' '):
            return False, f'{lcl.NAME4}'

    if p_str.startswith('\\\\?\\'):
        if len(p_str) > 32767:
            return False, (f'{lcl.PATH1}' + f"{len(p_str)}" + f'{lcl.PATH2}')
    else:
        if len(p_str) > 260:
            return False, f'{lcl.PATH3}' + f"{len(p_str)}" + f'{lcl.PATH4}'

    if '\\' in p_str and '/' in p_str:
        return False, f'{lcl.SEPARATOR1}'

    if p_str.startswith('\\\\?\\'):
        path_after_prefix = p_str[4:]
        if re.search(r'[\\/]{2,}', path_after_prefix):
            return False, f'{lcl.SEPARATOR2}'
    elif p_str.startswith('\\\\'):
        match = re.match(r'^(\\\\[^\\/]+[\\/])(.*)', p_str)
        if match:
            prefix, rest = match.groups()
            if re.search(r'[\\/]{2,}', rest):
                return False, f'{lcl.SEPARATOR3}'
    else:
        if re.search(r'[\\/]{2,}', p_str):
            return False, f'{lcl.SEPARATOR2}'

    not_recommended_chars = ['$', '%', '&', "'", '+', ',', ';', '=',
                             '@','[', ']', '^', '`', '{', '}', '~']
    found_not_recommended = []
    for char in not_recommended_chars:
        if char in remaining_path:
            found_not_recommended.append(char)

    if found_not_recommended:
        warning = (f'{lcl.SYMBOLS}', f"{', '.join(found_not_recommended)})")
        return True, f'{lcl.VALID}' + f"{warning}"

    return True, f'{lcl.VALID}'


def format_size(size_bytes: int) -> str:
    """Converts a file size in bytes to a human-readable Windows-style format.

    Args:
        size_bytes (int): File size in bytes.

    Returns:
        str: Formatted size string (b, kb, mb, gb, tb)
    """

    if size_bytes < 1024:
        return f"{size_bytes} B"

    kb = 1024
    mb = kb * 1024
    gb = mb * 1024
    tb = gb * 1024

    if size_bytes < mb:
        return f"{size_bytes / kb:.1f} KB"
    elif size_bytes < gb:
        return f"{size_bytes / mb:.1f} MB"
    elif size_bytes < tb:
        return f"{size_bytes / gb:.1f} GB"
    else:
        return f"{size_bytes / tb:.1f} TB"


def get_parent_path(path: PathString) -> str:
    """Returns the parent directory of a path with Windows root handling.
    Ensures drive roots end with backslash (C:\\).

    Args:
        path (str | Path): Input path.

    Returns:
        str: Parent directory path.
    """

    p_str = str(path)
    parent = os.path.dirname(p_str)

    if platform.system() == "Windows":
        if re.match(r'^[A-Za-z]:$', parent):
            parent = parent + '\\'
        elif re.match(r'^[A-Za-z]:\\$', parent):
            pass
    elif os.path.splitdrive(parent)[1] == "":
        parent = os.path.join(parent, "")

    return parent


def safe_windows_listdir(path: PathString) -> List[str]:
    """Safely lists directory contents on Windows.

    Handles PermissionError, FileNotFoundError and OS errors silently.

    Args:
        path (str | Path): Directory path.

    Returns:
        list: List of file and folder names, or empty list on failure.
    """

    try:
        p_str = str(path)
        return os.listdir(p_str)
    except (PermissionError, FileNotFoundError, OSError):
        return []


def is_hidden_windows_file(path: PathString) -> bool:
    """Determines whether a file is hidden.

    On Windows uses WinAPI FILE_ATTRIBUTE_HIDDEN.
    On Unix-like systems checks for leading dot.

    Args:
        path (str | Path): File path.

    Returns:
        bool: True if file is hidden, otherwise False.
    """

    p_str = str(path)

    if not Path(p_str).exists():
        return False

    if platform.system() == "Windows":
        try:
            import ctypes
            from ctypes import wintypes

            file_attribute_hidden = 0x02

            GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
            GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
            GetFileAttributesW.restype = wintypes.DWORD

            attrs = GetFileAttributesW(p_str)

            if attrs == 0xFFFFFFFF:
                last_error = ctypes.windll.kernel32.GetLastError()
                error_access_denied = 5

                if last_error == error_access_denied:
                    return True
                return False

            return bool(attrs & file_attribute_hidden)

        except Exception:
            pass

    return os.path.basename(p_str).startswith('.')


def get_windows_reserved_names() -> List[str]:
    """Returns the list of Windows reserved device names.

    Includes CON, PRN, AUX, NUL, COM1–COM9, LPT1–LPT9.

    Args:
        None

    Returns:
        list: Reserved Windows filenames.
    """

    return [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]


def normalize_windows_path(path: str) -> str:
    """Normalizes a Windows path.

    - Converts forward slashes to backslashes
    - Removes duplicate separators
    - Removes trailing backslash unless path is drive root

    Args:
        path (str): Input path.

    Returns:
        str: Normalized Windows path.
    """

    path = path.replace('/', '\\')

    path = re.sub(r'\\\\+', '\\', path)

    if path.endswith('\\') and not re.match(r'^[A-Za-z]:\\$', path):
        path = path.rstrip('\\')

    return path
