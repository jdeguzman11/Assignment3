# Justin DeGuzman
# justicd1@uci.edu
# 72329664

# command_processor.py

from pathlib import Path
import sys


class CommandProcessor:

    # defining function that handles what command function to call
    def handle(self, command: str, path: str, options: list[str] | None) -> None:
        if options is None:
            options = []

        if command == "L":
            self._list(path, options)
        elif command == "C":
            self._create(path, options)
        elif command == "D":
            self._delete(path)
        elif command == "R":
            self._read(path)
        else:
            print("ERROR")

    # defining function for L (list) command
    def _list(self, path: str, options: list[str]) -> None:
        path_obj = Path(path)

        if not path_obj.exists() or not path_obj.is_dir():
            print("ERROR")
            return

        try:
            items = list(path_obj.iterdir())
        except Exception:
            print("ERROR")
            return

        files = sorted(p for p in items if p.is_file())
        dirs = sorted(p for p in items if p.is_dir())

        if "-s" in options:
            self._list_search(files, dirs, options)
            return

        if "-e" in options:
            self._list_extension(files, dirs, options)
            return

        for f in files:
            print(str(f))

        for d in dirs:
            if "-f" not in options:
                print(str(d))
            if "-r" in options:
                self._list(str(d), options)

    # defining function for -s option
    def _list_search(self, files: list[Path], dirs: list[Path], options: list[str]) -> None:
        try:
            name = options[options.index("-s") + 1]
        except (ValueError, IndexError):
            print("ERROR")
            return

        for f in files:
            if f.name == name:
                print(str(f))

        if "-r" in options:
            for d in dirs:
                self._list(str(d), options)

    # defining function for -e option
    def _list_extension(self, files: list[Path], dirs: list[Path], options: list[str]) -> None:
        try:
            ext = options[options.index("-e") + 1]
        except (ValueError, IndexError):
            print("ERROR")
            return

        for f in files:
            if f.suffix == f".{ext}":
                print(str(f))

        if "-r" in options:
            for d in dirs:
                self._list(str(d), options)

    # defining function for C (create) command
    def _create(self, path: str, options: list[str]) -> None:
        if "-n" not in options:
            print("ERROR")
            return

        try:
            name = options[options.index("-n") + 1]
        except (ValueError, IndexError):
            print("ERROR")
            return

        directory = Path(path)

        if not directory.exists() or not directory.is_dir():
            print("ERROR")
            return

        if not name.endswith(".dsu"):
            name += ".dsu"

        full_path = directory / name

        if full_path.exists():
            print("ERROR")
            return

        try:
            full_path.touch()
            print(str(full_path.resolve()))
        except Exception:
            print("ERROR")

    # defining function for D (delete) command
    def _delete(self, path: str) -> None:
        path_obj = Path(path)

        if not path_obj.exists() or not path_obj.is_file() or path_obj.suffix != ".dsu":
            print("ERROR")
            return

        try:
            resolved = str(path_obj.resolve())
            path_obj.unlink()
            print(f"{resolved} DELETED")
        except Exception:
            print("ERROR")

    # defining function for R (read) command
    def _read(self, path: str) -> None:
        path_obj = Path(path)

        if not path_obj.exists() or not path_obj.is_file() or path_obj.suffix != ".dsu":
            print("ERROR")
            return

        if path_obj.stat().st_size == 0:
            sys.stdout.write("EMPTY")
            return

        try:
            with open(path_obj, "r") as f:
                sys.stdout.write(f.read())
        except Exception:
            print("ERROR")
