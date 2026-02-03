import os
from typing import Dict, Any, Tuple
from collections import defaultdict
import utils
import navigation


def count_files(path: str) -> Tuple[bool, int]:
    """
    Recursive counting of all files in the Windows directory.

    Args:
        path (str): The path to the analyzed directory.

    Returns:
        Tuple[bool, int]: Tuple, where:
         - bool: Operation success (True/False)
         - int: Total number of files in the directory and subdirectories.
    """

    path = utils.normalize_windows_path(path)

    try:
        validity, items = navigation.list_directory(path)
        if not validity or not items:
            return False, 0

        count = 0

        for item in items:
            full_path = os.path.join(path, item["name"])

            if item['type'] == 'file':
                count += 1
            elif item['type'] == 'folder' and not item.get('hidden', False):
                success_sub, count_sub = count_files(full_path)
                if success_sub:
                    count += count_sub

        return True, count

    except Exception as e:
        print(f"Ошибка при подсчете файлов в {path}: {e}")
        return False, 0


def count_bytes(path: str) -> Tuple[bool, int]:
    """
    Recursive calculation of the total size of files in the Windows directory.

    Args:
        path (str): The path to the analyzed directory.

    Returns:
        Tuple[bool, int]: Tuple, where:
         - bool: Operation success (True/False)
         - int: The total size of all files in bytes.
    """

    path = utils.normalize_windows_path(path)

    try:
        validity, items = navigation.list_directory(path)
        if not validity:
            return False, 0

        count = 0

        for item in items:
            full_path = os.path.join(path, item["name"])

            if item['type'] == 'file':
                count += item.get('size', 0)
            elif item['type'] == 'folder' and not item.get('hidden', False):
                success_sub, count_sub = count_bytes(full_path)
                if success_sub:
                    count += count_sub

        return True, count

    except Exception as e:
        print(f"Ошибка при подсчете размера в {path}: {e}")
        return False, 0


def analyze_windows_file_types(path: str) -> Tuple[bool,Dict[str, Dict[str, Any]]]:
    """
    Analyzes file types by extensions in the Windows directory.

    Args:
        path (str): The path to the analyzed directory.

    Returns:
        Tuple[bool, Dict[str, Dict[str, Any]]]: Tuple, where:
         - bool: Operation success (True/False)
         - Dict: Extension statistics, where the key is the extension,
           value is a dictionary with keys:
            - 'count': the number of files with this extension
            - 'size': the total size of files with this extension
    """
    path = utils.normalize_windows_path(path)
    statistic = defaultdict(lambda: {"count": 0, "size": 0})

    try:
        validity, items = navigation.list_directory(path)
        if not validity:
            return False, {}

        for item in items:
            full_path = os.path.join(path, item["name"])

            if item["type"] == "folder":
                success, subdir_stats = analyze_windows_file_types(full_path)
                if success:
                    for ext, data in subdir_stats.items():
                        statistic[ext]["count"] += data["count"]
                        statistic[ext]["size"] += data["size"]
                continue

            if item["type"] == "file":
                filename, extension = os.path.splitext(item["name"])
                extension = extension.lower()

                if not extension:
                    extension = ".noext"

                size = item.get("size", 0)

                statistic[extension]["count"] += 1
                statistic[extension]["size"] += size

        return True, dict(statistic)

    except Exception as e:
        print(f"Ошибка анализа типов файлов в {path}: {e}")
        return False, {}


def get_windows_file_attributes_stats(path: str) -> Dict[str, int]:
    """
    Collects statistics on attributes of Windows files in a directory.

    Args:
        path (str): The path to the analyzed directory.

    Returns:
        Dict[str, int]: Dictionary with statistics on attributes:
            - 'hidden': the number of hidden files
            - 'system': number of system files
            - 'readonly': number of read-only files
    """
    path = utils.normalize_windows_path(path)
    statistic = {"hidden": 0, "system": 0, "readonly": 0}

    try:
        success, items = navigation.list_directory(path)
        if not success or not items:
            return statistic

        for item in items:
            full_path = os.path.join(path, item["name"])

            if item["type"] == "file":
                if item.get("hidden", False):
                    statistic["hidden"] += 1

                try:
                    if not os.access(full_path, os.W_OK):
                        statistic["readonly"] += 1
                except (PermissionError, OSError):
                    pass

                filename_lower = item["name"].lower()
                if filename_lower.endswith('.sys') or filename_lower in [
                    'pagefile.sys', 'hiberfil.sys', 'swapfile.sys'
                ]:
                    statistic["system"] += 1

            elif item["type"] == "folder" and not item.get("hidden", False):
                subdir_stats = get_windows_file_attributes_stats(full_path)
                for key in statistic:
                    statistic[key] += subdir_stats.get(key, 0)

        return statistic

    except Exception as e:
        print(f"Ошибка при анализе атрибутов в {path}: {e}")
        return statistic


def show_windows_directory_stats(path: str) -> bool:
    """
    Comprehensive analysis and output of Windows catalog statistics.

    Args:
        path (str): The path to the analyzed directory.

    Returns:
        bool: The overall success of the analysis (True if all the basic operations are completed).

    Prints:
        Outputs to the console:
        1. General information (number of files, total size)
        2. Statistics on file types (extensions)
        3. Statistics on file attributes
        4. List of the largest files in the current directory
    """
    path = utils.normalize_windows_path(path)

    print(f"\n{'='*60}")
    print(f"Статистика каталога: {path}")
    print(f"{'='*60}\n")


    print("\n1. ОБЩАЯ ИНФОРМАЦИЯ:")
    print("-" * 40)

    success_files, total_files = count_files(path)
    if success_files:
        print(f"Файлов всего: {total_files:,}")
    else:
        print("Ошибка при подсчёте файлов")

    success_size, total_bytes = count_bytes(path)
    if success_size:
        print(f"Общий размер: {utils.format_size(total_bytes)}")
    else:
        print("Ошибка при подсчёте размеров")


    print("\n2. ТИПЫ ФАЙЛОВ:")
    print("-" * 40)

    success_types, ext_stats = analyze_windows_file_types(path)
    if success_types and ext_stats:
        print(f" Найдено {len(ext_stats)} различных расширений:")
        print()

        for extension, data in sorted(
                ext_stats.items(),
                key=lambda x: -x[1]["count"]):
            print(f"  {extension:10}  {data['count']:5} файлов,"
                  f" {utils.format_size(data['size'])}")
    else:
        print("Ошибка при анализе расширений")


    print("\n3. АТРИБУТЫ ФАЙЛОВ:")
    print("-" * 40)

    attrs = get_windows_file_attributes_stats(path)
    print(f"Скрытые:            {attrs['hidden']:,}")
    print(f"Системные:          {attrs['system']:,}")
    print(f"Только для чтения:  {attrs['readonly']:}")


    print("\n4. КРУПНЕЙШИЕ ФАЙЛЫ:")
    print("-" * 40)

    success, items = navigation.list_directory(path)
    if success and items:
        files = []
        for item in items:
            if item["type"] == "file":
                files.append((item["name"], item.get("size", 0)))

        if files:
            files.sort(key=lambda x: x[1], reverse=True)
            top_files = files[:10]

            print(f"Найдено {len(files)} файлов, топ {len(top_files)} по размеру:\n")

            for i, (name, size) in enumerate(top_files, 1):
                display_name = name
                if len(name) > 35:
                    display_name = name[:32] + "..."

                print(f"{i:2}. {display_name:35} {utils.format_size(size):>10}")
        else:
            print(" В этой папке нет файлов")
    else:
        print(" Не удалось получить список файлов")

    print("\n" + "=" * 60)
    print(" Анализ завершен")
    print("=" * 60)

    return success_files and success_size and success_types
    
