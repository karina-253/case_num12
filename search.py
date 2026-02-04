import os
import re
from typing import List, Dict, Any
import utils
import navigation
import analysis
import fnmatch
import local as lcl

def contains_forbidden_chars(name: str) -> bool:
    """
    Check if the filename or path contains forbidden characters.

    Args:
        name (str): The filename or path.

    Returns:
        bool: True if forbidden characters are found, False otherwise.
    """
    forbidden_chars = r'[\/:*?"<>|]'
    return re.search(forbidden_chars, name) is not None

def is_path_too_long(path_str: str) -> bool:
    """
    Determine if the path exceeds Windows maximum length.

    Args:
        path_str (str): The path string.

    Returns:
        bool: True if length exceeds 260 characters, False otherwise.
    """
    return len(path_str) > 260

def is_hidden_by_dot(name: str) -> bool:
    """
    Check if the file is hidden based on its name starting with a dot.

    Args:
        name (str): The filename.

    Returns:
        bool: True if filename starts with '.', False otherwise.
    """
    return name.startswith('.')


def is_junction_points(path: str) -> bool:
    """
        Check if the given path is a junction point.

        Args:
            path (str): The filesystem path.

        Returns:
            bool: True if it is a junction point, False otherwise.
    """
    return os.path.islink(path)

def find_files_windows(
    pattern: str,
    path: str,
    case_sensitive: bool = False,
    current_path: str = None,
    matched_files: List[str] = None
) -> List[str]:
    """
    Recursively search for files matching a pattern.

    Args:
        pattern (str): The filename pattern.
        path (str): The root directory to start search.
        case_sensitive (bool): Match case sensitivity.
        current_path (str): Current directory in recursion.
        matched_files (List[str]): Accumulated list of matched files.

    Returns:
        List[str]: List of matched file paths.
    """
    if matched_files is None:
        matched_files = []
    if current_path is None:
        current_path = path

    if case_sensitive:
        def match_func(name: str, pattern_str: str) -> bool:
            return fnmatch.fnmatchcase(name, pattern_str)
    else:
        def match_func(name: str, pattern_str: str) -> bool:
            return fnmatch.fnmatchcase(name.lower(), pattern_str.lower())

    try:
        validity, items = navigation.list_directory(current_path)
        if not validity:
            return matched_files

        for item in items:
            item_path = os.path.join(current_path, item["name"])

            if contains_forbidden_chars(item["name"]) or is_path_too_long(item_path):
                continue

            if os.path.islink(item_path) or is_junction_points(item_path):
                continue

            if item["type"] == "folder":
                find_files_windows(pattern, path, case_sensitive, item_path, matched_files)
            elif item["type"] == "file":
                if match_func(item["name"], pattern):
                    if not is_path_too_long(item_path):
                        matched_files.append(item_path)
    except:
        pass
    return matched_files

def find_by_windows_extension(
    extensions: List[str],
    path: str
) -> List[str]:
    """
    Search files by extensions.

    Args:
        extensions (List[str]): List of extensions.
        path (str): Directory to search in.

    Returns:
        List[str]: List of matched files.
    """
    if not os.path.exists(path) or not os.path.isdir(path):
        return []

    normalized_exts = []
    for ext in extensions:
        ext = ext.strip().lower()
        if not ext.startswith('.'):
            ext = '.' + ext
        normalized_exts.append(ext)

    success, stats = analysis.analyze_windows_file_types(path)
    if not success:
        return []

    relevant_exts = [ext for ext in normalized_exts if ext in stats and stats[ext]['count'] > 0]
    if not relevant_exts:
        return []

    matched_files: List[str] = []

    def recursive_scan(current_dir: str) -> None:
        try:
            validity, items = navigation.list_directory(current_dir)
            if not validity:
                return
            for item in items:
                full_path = os.path.join(current_dir, item["name"])

                if contains_forbidden_chars(item["name"]) or is_path_too_long(full_path):
                    continue

                if os.path.islink(full_path) or is_junction_points(full_path):
                    continue

                if item["type"] == "folder":
                    recursive_scan(full_path)
                elif item["type"] == "file":
                    _, ext = os.path.splitext(item["name"])
                    if ext.lower() in relevant_exts:
                        if not is_path_too_long(full_path):
                            matched_files.append(full_path)
        except:
            pass

    recursive_scan(path)
    return matched_files

def find_large_files_windows(
    min_size_mb: float,
    path: str
) -> List[Dict[str, Any]]:
    """
    Find large files exceeding a size threshold.

    Args:
        min_size_mb (float): Minimum size in megabytes.
        path (str): Directory to search.

    Returns:
        List[Dict[str, Any]]: List of dictionaries with file info.
    """
    min_size_bytes = min_size_mb * 1024 * 1024
    large_files: List[Dict[str, Any]] = []

    def scan_directory(dir_path: str) -> None:
        try:
            validity, items = navigation.list_directory(dir_path)
            if not validity:
                return
            for item in items:
                full_path = os.path.join(dir_path, item["name"])

                if contains_forbidden_chars(item["name"]) or is_path_too_long(full_path):
                    continue
                if os.path.islink(full_path) or is_junction_points(full_path):
                    continue

                if item["type"] == "file":
                    try:
                        size_success, size_bytes = analysis.count_bytes(full_path)
                        if size_success and size_bytes >= min_size_bytes:
                            large_files.append({
                                'path': full_path,
                                'size_mb': size_bytes / (1024 * 1024),
                                'size_bytes': size_bytes,
                                'name': os.path.basename(full_path),
                                'type': os.path.splitext(full_path)[1]
                            })
                    except:
                        pass
                elif item["type"] == "folder":
                    scan_directory(full_path)
        except:
            pass

    scan_directory(path)
    return large_files

def find_windows_system_files(path: str) -> List[str]:
    """
    Get system files in Windows directories.

    Args:
        path (str): Directory path.

    Returns:
        List[str]: List of system files.
    """
    system_files: List[str] = []

    special_dirs = navigation.get_windows_special_folders()
    search_dirs = [
        special_dirs.get('Desktop', ''),
        special_dirs.get('Documents', ''),
        special_dirs.get('Downloads', ''),
        path
    ]

    sys_extensions = ['.exe', '.dll', '.sys']
    for dir_path in search_dirs:
        if not dir_path or not os.path.exists(dir_path):
            continue
        try:
            with os.scandir(dir_path) as entries:
                for entry in entries:
                    full_path = os.path.join(dir_path, entry.name)

                    if contains_forbidden_chars(entry.name) or is_path_too_long(full_path):
                        continue
                    if os.path.islink(full_path) or is_junction_points(full_path):
                        continue

                    if entry.is_file():
                        ext = os.path.splitext(entry.name)[1].lower()
                        if ext in sys_extensions:
                            system_files.append(full_path)
        except:
            pass

    return system_files


def search_menu_handler(current_path: str) -> bool:
    """
    Display interactive search menu.

    Args:
        current_path (str): Current directory.

    Returns:
        bool: False when user exits menu.
    """
    while True:
        print("\n" + "="*70)
        print(f'{lcl.NOT_MENU}')
        print("="*70)
        print(f'{lcl.ACTION}')
        print(f'{lcl.LARGE_FILES}')
        print(f'{lcl.SISTEM_FILES}')
        print(f'{lcl.STATISTIC_FOLDER}')
        print(f'{lcl.FIND_FOLDER_1}')
        print(f'{lcl.FIND_FOLDER_2}')
        print(f'{lcl.END_MENU}')
        choice = input(f'{lcl.NUMBER_MENU}').strip()

        match choice:
            case '1':
                try:
                    size_mb = float(input(f'{lcl.MIN_FOLDER}'))
                except:
                    print(f'{lcl.CORRECT_NUMER}')
                    continue
                files = find_large_files_windows(size_mb, current_path)
                print(f"\n{lcl.FIND} {len(files)} {lcl.FILES_MORE} {size_mb} {lcl.M_B}")
                if files:
                    print(f"{f'{lcl.FILE_NAME}':<40} {f'{lcl.SIZE}':<12} {f'{lcl.TYPE}':<10}")
                    print("-" * 70)
                    for f in files:
                        print(f"{f['name']:<40} {f['size_mb']:<12.2f} {f['type']:<10}")
                else:
                    print(f'{lcl.NOT_FILES}')
            case '2':
                sys_files = find_windows_system_files(current_path)
                print(f"\n{lcl.SYSTEM_FILES} {len(sys_files)}")
                for f in sys_files:
                    print(f"  {os.path.basename(f)} - {f}")
            case '3':
                print(f"\n{lcl.SHOW_STATISTIC}")
                analysis.show_windows_directory_stats(current_path)
            case '4':
                exts_input = input(f'{lcl.EX_INPUT}').strip()
                if exts_input:
                    extensions = [ext.strip() for ext in exts_input.split(',')]
                    files = find_by_windows_extension(extensions, current_path)
                    print(f"\n{lcl.FIND} {len(files)} {lcl.FILES_SIZE} {extensions}:")
                    for f in files:
                        print(f"  {os.path.basename(f)} - {f}")
                else:
                    print(f'{lcl.NOT_SIZE}')
            case '5':
                pattern = input(f'{lcl.SAMPLE}').strip()
                if pattern:
                    case_sensitive = input(f'{lcl.REG_SENS}').strip().lower()
                    is_case_sensitive = case_sensitive in [f'{lcl.YES}', f'{lcl.LETTER}', 'yes', 'y']
                    files = find_files_windows(pattern, current_path, is_case_sensitive)
                    print(f"\n{lcl.FIND} {len(files)} f'{lcl.FILES_SAMPLE}' '{pattern}':")
                    for f in files:
                        print(f"  {os.path.basename(f)} - {f}")
                else:
                    print(f'{lcl.NOT_SAMPLE}')
            case '6':
                print(f"\n{lcl.END_SEARCH}")
                return False
            case _:
                print(f'{lcl.INCOR_INPUT}')
        cont = input(f"\n{lcl.CONTINUE_SEARCH}").strip().lower()
        if cont not in [f'{lcl.YES}', f'{lcl.LETTER}', 'yes', 'y']:
            print(f'{lcl.GOODBYE}')
            return False

    return True
def format_windows_search_results(results: List[Dict[str, Any]],
                                  search_type: str) -> None:
    """
    Print formatted search results.

    Args:
        results (List[Dict[str, Any]]): Search results.
        search_type (str): Search description.
    """
    print("\n" + "=" * 80)
    print(f"{lcl.RESULT_TYPE}' {search_type}")
    print("=" * 80)

    if not results:
        print(f'{lcl.NOT_RESULT}')
        return

    print(f"{f'{lcl.FILE_NAME}':<40} {f'{lcl.SIZE}':<15} {f'{lcl.P}':<30}")
    print("-" * 80)

    for item in results:
        name = item.get('name', f'{lcl.NOT_NAME }')
        size_bytes = item.get('size_bytes', item.get('size', 0))
        path = item.get('path', '')

        size_str = utils.format_size(size_bytes)  # форматируем размер через utils

        print(f"{name:<40} {size_str:<15} {path:<30}")

    print("=" * 80)
    print(f"{lcl.ALL_FIND} {len(results)} {lcl.FILES_2}\n")
