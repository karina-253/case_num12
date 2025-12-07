import os
from typing import Dict, Any, List, Tuple
from collections import defaultdict
import ctypes
import utils
import navigation

def is_junction_points(path: str) -> bool:
    """Определение junction point через WinAPI."""
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            return False
        return bool(attrs & 0x400)
    except Exception:
        return False


def count_files(path: str) -> Tuple[bool, int]:
    """Рекурсивный подсчет файлов в Windows каталоге"""
    try:
        validity, items = navigation.list_directory(path)
        if not validity:
            return False, 0
        count = 0

        for item in items:
            full_path = os.path.join(path, item["name"])

            if os.path.islink(full_path) or is_junction_points(full_path):
                continue

            if item["type"] == "folder":
                success, subdir_count = count_files(full_path)
                if success:
                    count += subdir_count
                continue

            if item["type"] == "file":
                count += 1
        return True, count

    except Exception:
        return False, 0


def count_bytes(path: str) -> Tuple[bool, int]:
    """Рекурсивный подсчет размера файлов в Windows"""
    try:
        validity, items = navigation.list_directory(path)
        if not validity:
            return False, 0

        count_size = 0

        for item in items:
            full_path = os.path.join(path, item["name"])

            if os.path.islink(full_path) or is_junction_points(full_path):
                continue

            if item["type"] == "folder":
                success, subdir_count = count_bytes(full_path)
                if success:
                    count_size += subdir_count
                continue

            if item["type"] == "file":
                try:
                    count_size += item.get("size", os.path.getsize(full_path))
                except Exception:
                    pass

        return True, count_size

    except Exception:
        return False, 0


def analyze_windows_file_types(path: str) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    """Анализ типов файлов с учетом Windows расширений"""

    statistic = defaultdict(lambda: {"count": 0, "size": 0})

    try:
        validity, items = navigation.list_directory(path)
        if not validity:
            return False, {}

        for item in items:
            full_path = os.path.join(path, item["name"])

            if os.path.islink(full_path) or is_junction_points(full_path):
                continue

            if item["type"] == "folder":
                success, subdir_stats = analyze_windows_file_types(full_path)
                if success:
                    # Слияние словарей
                    for ext, data in subdir_stats.items():
                        statistic[ext]["count"] += data["count"]
                        statistic[ext]["size"] += data["size"]
                continue

            if item["type"] == "file":
                filename, extension = os.path.splitext(item["name"])
                extension = extension.lower()
                size = item.get("size", 0)

                statistic[extension]["count"] += 1
                statistic[extension]["size"] += size

        return True, statistic

    except Exception:
        return False, {}


def is_system_file(path: str) -> bool:
    """Проверка является ли файл системным в Windows"""
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            return False
        return bool(attrs & 0x4)
    except Exception:
        return False


def get_windows_file_attributes_stats(path: str) -> Dict[str, int]:
    """Статистика по атрибутам файлов Windows"""

    statistic = {"hidden": 0, "system": 0, "readonly": 0}

    try:
        success, items = navigation.list_directory(path)
        if not success:
            return statistic

        for item in items:
            full_path = os.path.join(path, item["name"])

            if os.path.islink(full_path) or is_junction_points(full_path):
                continue

            # hidden
            if item["type"] == "file":
                if utils.is_hidden_windows_file(full_path):
                    statistic["hidden"] += 1

                if not os.access(full_path, os.W_OK):
                    statistic["readonly"] += 1

                if is_system_file(full_path):
                    statistic["system"] += 1

            if item["type"] == "folder":
                subdir_stats = get_windows_file_attributes_stats(full_path)
                for key in statistic:
                    statistic[key] += subdir_stats.get(key, 0)
        return statistic

    except Exception:
        return statistic


def show_windows_directory_stats(path: str) -> bool:
    """Комплексный вывод статистики Windows каталога"""

    print(f"\n{'='*60}")
    print(f"Статистика каталога: {path}")
    print(f"{'='*60}\n")

    print("\nПодсчет общего количества файлов")
    success_files, total_files = count_files(path)
    if not success_files:
        print("Ошибка при подсчёте файлов")
        return False
    print(f"Файлов всего: {total_files}")

    print("\nПодсчет общего размера")
    success_size, total_bytes = count_bytes(path)
    if not success_size:
        print("Ошибка при подсчёте размеров")
        return False
    print(f"Общий размер: {utils.format_size(total_bytes)}")

    print("\nСтатистика по расширениям:")
    success_types, ext_stats = analyze_windows_file_types(path)
    if not success_types:
        print("Ошибка при анализе расширений")
        return False

    print("\nТипы файлов:")
    for extension, data in sorted(ext_stats.items(), key=lambda x: -x[1]["count"]):
        print(f"  {extension:10}  {data['count']:5} файлов, {utils.format_size(data['size'])}")

    attrs = get_windows_file_attributes_stats(path)
    print("\nАтрибуты:")
    print(f"Скрытые:            {attrs['hidden']:,}")
    print(f"Системные:          {attrs['system']:,}")
    print(f"Только для чтения:  {attrs['readonly']:}")

    print("\nКрупнейшие файлы:")
    success, items = navigation.list_directory(path)
    if success:
        files = [
            (item["name"], item["size"])
            for item in items
            if item["type"] == "file"
        ]
        top = sorted(files, key=lambda x: -x[1])[:5]
        for name, size in top:
            print(f"  {name:40} {utils.format_size(size)}")
    else:
        print("Недоступно")

    print("\nГотово.\n")
    return True
