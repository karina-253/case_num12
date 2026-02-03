import os
import sys
from typing import NoReturn
import utils
import navigation
import analysis
import search
import local as lcl


def check_windows_environment() -> bool:
    """Checks that the program is running on Windows.

        Prints an error message if executed on a non-Windows system.

        Args:
            None

        Returns:
            bool: True if running on Windows, False otherwise.
        """

    if not utils.is_windows_os():
        print("=" * 60)
        print(f'{lcl.SYSTEM1}')
        print(f'{lcl.SYSTEM2}' f"{sys.platform}")
        print("=" * 60)
        return False
    return True


def display_windows_banner() -> None:
    """Displays startup banner with Windows system information.

    Shows:
    - Current drive
    - Available drives
    - Current working directory
    - Windows special folders

    Args:
        None

    Returns:
        None
    """

    print("=" * 70)
    print(" " * 20 + f'{lcl.TITLE}')
    print("=" * 70)

    current_drive = navigation.get_current_drive()
    print(f'{lcl.DISK1}' f"{current_drive}")

    drives = navigation.list_available_drives()
    print(f'{lcl.DISK2}' f"{', '.join(drives)}")

    current_path = os.getcwd()
    print(f'{lcl.PATH5}' f"{current_path}")

    print(f'\n{lcl.FOLDERS}')
    special_folders = navigation.get_windows_special_folders()
    for name, path in special_folders.items():
        if os.path.exists(path):
            print(f"  {name}: {path}")

    print("=" * 70)
    print()


def display_main_menu(current_path: str) -> None:
    """Displays main command menu.

    Args:
        current_path (str): Current working directory.

    Returns:
        None
    """

    print(f'\n{lcl.DIRECTORY}' f"{current_path}")
    print("-" * 70)
    print(f'{lcl.COMMANDS}')
    print(f'{lcl.FIRST}')
    print(f'{lcl.SECOND}')
    print(f'{lcl.THIRD}')
    print(f'{lcl.FORTH}')
    print(f'{lcl.FIFTH}')
    print(f'{lcl.SIXTH}')
    print(f'{lcl.SEVENTH}')
    print(f'{lcl.EIGHTTH}')
    print(f'{lcl.ZERO}')
    print("-" * 70)


def handle_windows_navigation(command: str, current_path: str) -> str:
    """Handles Windows navigation commands.

    Args:
        command (str): User command.
        current_path (str): Current working directory.

    Returns:
        str: Updated path after navigation.
    """

    if command == "5":
        new_path = navigation.move_up(current_path)
        print(f'{lcl.CHANGE}' f"{new_path}")
        return new_path

    elif command == "6":
        dir_name = input(f'{lcl.CATALOG}').strip()
        if dir_name:
            success, new_path = navigation.move_down(current_path, dir_name)
            if success:
                print(f'{lcl.CHANGE}' f"{new_path}")
                return new_path
            else:
                print(f'{lcl.FAILED}' f"{dir_name}")

    elif command == "7":
        drives = navigation.list_available_drives()
        print(f'{lcl.DISK2}')
        for i, drive in enumerate(drives, 1):
            print(f"  {i}. {drive}")

        try:
            choice = int(input(f'{lcl.DISK3}'))
            if 1 <= choice <= len(drives):
                new_drive = drives[choice - 1]
                new_path = new_drive + "\\"
                valid, msg = utils.validate_windows_path(new_path)
                if valid:
                    os.chdir(new_path)
                    print(f'{lcl.DISK4}' f"{new_drive}")
                    return os.getcwd()
                else:
                    print(f'{lcl.ERROR}' f"{msg}")
            else:
                print(f'{lcl.DISK5}')
        except ValueError:
            print(f'{lcl.DISK3}')

    elif command == "8":
        special_folders = navigation.get_windows_special_folders()
        print(f'{lcl.FOLDERS}')
        folders_list = list(special_folders.items())
        for i, (name, path) in enumerate(folders_list, 1):
            if os.path.exists(path):
                print(f"  {i}. {name} ({path})")

        try:
            choice = int(input(f'{lcl.FOLDERS1}'))
            if 1 <= choice <= len(folders_list):
                name, path = folders_list[choice - 1]
                if os.path.exists(path):
                    os.chdir(path)
                    print(f'{lcl.FOLDERS2}' f"{name}")
                    return os.getcwd()
                else:
                    print(f'{lcl.FOLDER}' f"{name}" f'{lcl.FOLDER1}')
            else:
                print(f'{lcl.FOLDER2}')
        except ValueError:
            print(f'{lcl.FOLDER3}')

    return current_path


def handle_windows_analysis(command: str, current_path: str) -> None:
    """Handles Windows filesystem analysis commands.

        Args:
            command (str): User command.
            current_path (str): Current working directory.

        Returns:
            None
        """

    if command == "2":
        print(f'\n{lcl.ANALYS}' f"{current_path}")
        analysis.show_windows_directory_stats(current_path)

    elif command == "4":
        print(f'\n{lcl.ANALYS1}' f"{current_path}")
        success, stats = analysis.analyze_windows_file_types(current_path)
        if success:
            print(f'\n{lcl.STATISTIC}')
            print("-" * 50)
            for ext, data in sorted(stats.items(), key=lambda x: -x[1]["size"]):
                if ext:
                    print(f"{ext:10} : {data['count']:4}" f'{lcl.FILE}', f"{utils.format_size(data['size'])}")
            print("-" * 50)
        else:
            print(f'{lcl.ERROR1}')


def handle_windows_search(command: str, current_path: str) -> None:
    """Handles file search commands.

    Args:
        command (str): User command.
        current_path (str): Current working directory.

    Returns:
        None
    """

    if command == "3":
        search.search_menu_handler(current_path)


def run_windows_command(command: str, current_path: str) -> str:
    """Main Windows command dispatcher.

        Args:
            command (str): User command.
            current_path (str): Current working directory.

        Returns:
            str: Updated working directory.
    """

    new_path = current_path

    match command:
        case "1":
            print(f'\n{lcl.DIRECTORY1}' f"{current_path}")
            success, items = navigation.list_directory(current_path)
            if success:
                navigation.format_directory_output(items)
            else:
                print(f'{lcl.DIRECTORY_ERROR}')

        case "2" | "4":
            handle_windows_analysis(command, current_path)

        case "3":
            handle_windows_search(command, current_path)

        case "5" | "6" | "7" | "8":
            new_path = handle_windows_navigation(command, current_path)

        case "0":
            print(f'{lcl.EXIT}')
            sys.exit(0)

        case _:
            print(f'{lcl.NO_COMMAND}')

    return new_path


def main() -> NoReturn:
    """Main entry point of Windows File Manager.

    Args:
        None

    Returns:
        NoReturn
    """

    if not check_windows_environment():
        print(f'\n{lcl.CANCELED}')
        sys.exit(1)

    display_windows_banner()

    current_path = os.getcwd()

    while True:
        try:
            display_main_menu(current_path)

            command = input(f'\n{lcl.COMMAND}').strip()

            current_path = run_windows_command(command, current_path)

        except KeyboardInterrupt:
            print(f'\n\n{lcl.COMMAND}')
            break
        except SystemExit:
            raise
        except Exception as e:
            print(f'\n{lcl.EXPECT_ERROR}' f"{e}")
            print(f'{lcl.CONTINUE}')

    print(f'\n{lcl.THANKS}')
    sys.exit(0)


if __name__ == "__main__":
    main()
