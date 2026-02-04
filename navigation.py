import os
from datetime import datetime
from typing import Any, Dict, List, Tuple
import utils
import local as lcl


def get_current_drive() -> str:
    """
    Get the current Windows drive.

    Returns:
        str: The current drive letter (e.g. "C:").
             If the drive cannot be determined, returns "C:" by default.
    """
    current_path = os.getcwd()
    drive, _ = os.path.splitdrive(current_path)

    if drive:
        return drive

    # Fallback to default Windows drive
    return "C:"


def list_available_drives() -> List[str]:
    """
    Get a list of available drives in Windows.

    Returns:
        List[str]: A list of available drive letters (e.g. ["C:", "D:"]).
                   If the operation fails, returns ["C:"] as a fallback.
    """
    if not utils.is_windows_os():
        return ["/"]

    try:
        from ctypes import wintypes
        import ctypes

        get_logical_drives = ctypes.windll.kernel32.GetLogicalDrives
        get_logical_drives.restype = wintypes.DWORD

        drives_bitmask = get_logical_drives()

        if drives_bitmask == 0:
            last_error = ctypes.windll.kernel32.GetLastError()
            print(f"Windows API error GetLogicalDrives: {lcl.CODE} {last_error}")
            return ["C:"]

        drives = []

        for i in range(26):
            if drives_bitmask & (1 << i):
                drive_letter = f"{chr(65 + i)}:"
                drive_path = drive_letter + "\\"

                try:
                    if os.path.exists(drive_path):
                        drives.append(drive_letter)
                except (PermissionError, OSError):
                    continue

        return drives if drives else ["C:"]

    except AttributeError:
        print("Windows API is not available")
        return ["C:"]
    except OSError as exc:
        print(f"Windows API error: {exc}")
        return ["C:"]
    except Exception as exc:
        print(f"Unexpected error getting drives: {exc}")
        return ["C:"]


def list_directory(path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    List the contents of a directory in Windows.

    Args:
        path (str): Path to the directory.

    Returns:
        Tuple[bool, List[Dict[str, Any]]]: Tuple, where:
         - bool: Operation success (True/False)
         - List[Dict]: List of directory entries with metadata:
           - name (str)
           - type ("file" or "folder")
           - size (int)
           - modified (str, YYYY-MM-DD)
           - hidden (bool)
    """
    entries: List[Dict[str, Any]] = []

    try:
        items = utils.safe_windows_listdir(path)

        for item in items:
            full_path = os.path.join(path, item)

            is_dir = os.path.isdir(full_path)
            is_hidden = utils.is_hidden_windows_file(full_path)

            size = 0 if is_dir else os.path.getsize(full_path)
            modified_time = datetime.fromtimestamp(
                os.path.getmtime(full_path)
            ).strftime("%Y-%m-%d")

            entries.append(
                {
                    "name": item,
                    "type": "folder" if is_dir else "file",
                    "size": size,
                    "modified": modified_time,
                    "hidden": is_hidden,
                }
            )

        return True, entries

    except Exception:
        return False, []


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable form.

    Args:
        size_bytes (int): File size in bytes.

    Returns:
        str: Formatted size (e.g. "10 MB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes} {unit}"
        size_bytes /= 1024

    return f"{size_bytes:.2f} PB"


def format_directory_output(items: List[Dict[str, Any]]) -> None:
    """
    Print formatted directory contents to the console.

nastya, [04.02.2026 0:21]
Args:
        items (List[Dict[str, Any]]): Directory entries returned
                                      by list_directory().
    """
    if not items:
        print(f"{lcl.EMPTY_DIRECTORY}")
        return

    for item in items:
        name = item["name"]
        type_icon = "[D]" if item["type"] == "folder" else "[F]"
        size_str = (
            format_size(item["size"])
            if item["type"] == "file"
            else ""
        )
        hidden_marker = f"{lcl.HIDDEN}" if item["hidden"] else ""

        print(f"{type_icon} {name} {size_str} {hidden_marker}")


def move_up(current_path: str) -> str:
    """
    Move to the parent directory in Windows.

    Args:
        current_path (str): Current directory path.

    Returns:
        str: Parent directory path if valid,
             otherwise the original path.
    """
    parent_path = utils.get_parent_path(current_path)
    valid, msg = utils.validate_windows_path(parent_path)

    if valid:
        return parent_path

    print(f"{lcl.FAILED_NAV_PARENT_D} {msg}")
    return current_path


def move_down(current_path: str, target_dir: str) -> Tuple[bool, str]:
    """
    Move to a subdirectory in Windows.

    Args:
        current_path (str): Current directory path.
        target_dir (str): Name of the target subdirectory.

    Returns:
        Tuple[bool, str]: Tuple, where:
         - bool: Operation success (True/False)
         - str: New path or original path on failure
    """
    new_path = os.path.join(current_path, target_dir)
    valid, msg = utils.validate_windows_path(new_path)

    if valid:
        return True, new_path

    print(f"{lcl.ERROR_DURING_TRANSITION} {msg}")
    return False, current_path


def get_windows_special_folders() -> Dict[str, str]:
    """
    Get paths to common user folders.

    Returns:
        Dict[str, str]: Dictionary with paths to:
         - Desktop
         - Documents
         - Downloads
    """
    if not utils.is_windows_os():
        home_dir = os.path.expanduser("~")
        return {
            "Desktop": os.path.join(home_dir, "Desktop"),
            "Documents": os.path.join(home_dir, "Documents"),
            "Downloads": os.path.join(home_dir, "Downloads"),
        }

    user_profile = os.environ.get("USERPROFILE", "")
    return {
        "Desktop": os.path.join(user_profile, "Desktop"),
        "Documents": os.path.join(user_profile, "Documents"),
        "Downloads": os.path.join(user_profile, "Downloads"),
    }
    
