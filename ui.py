# Justin DeGuzman
# justicd1@uci.edu
# 72329664

from shlex import split
from pathlib import Path
from typing import Optional
from command_processor import CommandProcessor
from Profile import Profile, Post, DsuFileError, DsuProfileError

import ds_client


class UI:
    def __init__(self) -> None:
        self.processor = CommandProcessor()
        self.current_path: Optional[str] = None
        self.current_profile: Optional[Profile] = None
        self.in_admin_mode: bool = False

    @staticmethod
    def _get_option_value(options: list[str], flag: str) -> Optional[str]:
        if flag not in options:
            return None
        i = options.index(flag)
        if i + 1 >= len(options):
            return None
        return options[i + 1]

    @staticmethod
    def _valid_userpass(value: str) -> bool:
        if value.strip() == "":
            return False
        return not any(ch.isspace() for ch in value)

    def _build_dsu_path(self, directory: str, name: str) -> Optional[str]:
        d = Path(directory)
        if not d.exists() or not d.is_dir():
            return None

        filename = name
        if not filename.endswith(".dsu"):
            filename += ".dsu"

        return str((d / filename).resolve())

    def _collect_profile_info(self) -> Optional[Profile]:
        try:
            print("username:")
            username = input().strip()

            print("password:")
            password = input().strip()

            print("bio:")
            bio = input().strip()

            print("server:")
            dsuserver = input().strip()
        except EOFError:
            return None

        if not self._valid_userpass(username):
            return None
        if not self._valid_userpass(password):
            return None
        if bio.strip() == "":
            return None
        if dsuserver.strip() == "":
            return None

        prof = Profile()
        prof.username = username
        prof.password = password
        prof.bio = bio
        prof.dsuserver = dsuserver
        return prof

    @staticmethod
    def _touch_empty_file(path: str) -> bool:
        p = Path(path)
        if p.exists():
            return False
        try:
            p.touch()
            return True
        except Exception:
            return False

    @staticmethod
    def _safe_delete(path: str) -> None:
        try:
            p = Path(path)
            if p.exists():
                p.unlink()
        except Exception:
            pass

    @staticmethod
    def _split_path_and_options(tokens: list[str]) -> tuple[Optional[str], list[str]]:
        if not tokens:
            return None, []

        path_tokens: list[str] = []
        i = 0
        while i < len(tokens) and not tokens[i].startswith("-"):
            path_tokens.append(tokens[i])
            i += 1

        if not path_tokens:
            return None, []

        path = " ".join(path_tokens)
        options = tokens[i:]
        return path, options

    #
    # Open DSU Command
    #
    def _open_dsu(self, path: str) -> None:
        resolved = str(Path(path).resolve())

        prof = Profile()

        try:
            prof.load_profile(resolved)
        except (DsuFileError, DsuProfileError):
            print("ERROR")
            return

        self.current_profile = prof
        self.current_path = resolved
        print(f"LOADED {resolved}")

    #
    # Create or Load Command
    #
    def _create_dsu(self, directory: str, options: list[str]) -> None:
        name = self._get_option_value(options, "-n")
        if name is None:
            print("ERROR")
            return

        full_path = self._build_dsu_path(directory, name)
        if full_path is None:
            print("ERROR")
            return

        if Path(full_path).exists():
            self._open_dsu(full_path)
            return

        prof = self._collect_profile_info()
        if prof is None:
            print("ERROR")
            return

        if not self._touch_empty_file(full_path):
            print("ERROR")
            return

        try:
            prof.save_profile(full_path)
        except DsuFileError:
            self._safe_delete(full_path)
            print("ERROR")
            return

        self.current_profile = prof
        self.current_path = full_path
        print(f"LOADED {full_path}")

    #
    # Print Command
    #
    def _print_profile(self, options: list[str]) -> None:
        prof = self.current_profile
        if prof is None:
            print("ERROR")
            return

        if not options:
            print("ERROR")
            return

        i = 0
        while i < len(options):
            opt = options[i]

            if opt == "-usr":
                print(prof.username)
                i += 1

            elif opt == "-pwd":
                print(prof.password)
                i += 1

            elif opt == "-bio":
                print(prof.bio)
                i += 1

            elif opt == "-posts":
                posts = prof.get_posts()
                for idx, post in enumerate(posts, start=1):
                    print(f"{idx}: {post.entry}")
                i += 1

            elif opt == "-post":
                if i + 1 >= len(options):
                    print("ERROR")
                    return
                try:
                    idx = int(options[i + 1]) - 1
                except ValueError:
                    print("ERROR")
                    return

                posts = prof.get_posts()
                if idx < 0 or idx >= len(posts):
                    print("ERROR")
                    return

                print(posts[idx].entry)
                i += 2

            elif opt == "-all":
                print(prof.username)
                print(prof.password)
                print(prof.bio)
                posts = prof.get_posts()
                for idx, post in enumerate(posts, start=1):
                    print(f"{idx}: {post.entry}")
                i += 1

            else:
                print("ERROR")
                return

    #
    # Publish Post
    #
    def _publish_post(self, index: int) -> None:
        prof = self.current_profile

        if prof is None:
            print("ERROR")
            return

        if prof.dsuserver is None or prof.dsuserver.strip() == "":
            print("ERROR")
            return

        posts = prof.get_posts()
        if index < 0 or index >= len(posts):
            print("ERROR")
            return

        post = posts[index]

        # no empty/whitespace posts
        if post.entry is None or post.entry.strip() == "":
            print("ERROR")
            return

        ok = ds_client.send(
            prof.dsuserver,
            2021,
            prof.username,
            prof.password,
            prof.entry,
            prof.bio
        )

        if ok:
            print("PUBLISHED")
        else:
            print("ERROR")

    #
    # Core Command Processing
    #
    def _process_line(self, line: str) -> bool:
        line = line.strip()

        if line == "Q":
            return False

        if line == "":
            print("ERROR")
            return True

        try:
            parts = split(line)
        except ValueError:
            print("ERROR")
            return True

        cmd = parts[0].upper()

        path_commands = {"L", "C", "D", "R", "O"}
        no_path_commands = {"E", "P", "PUB"}

        if cmd in path_commands:
            if len(parts) < 2:
                print("ERROR")
                return True

            path, options = self._split_path_and_options(parts[1:])
            if path is None:
                print("ERROR")
                return True

            if cmd == "O":
                self._open_dsu(path)
                return True

            if cmd == "C":
                self._create_dsu(path, options)
                return True

            self.processor.handle(cmd, path, options)
            return True

        if cmd in no_path_commands:
            if self.current_profile is None or self.current_path is None:
                print("ERROR")
                return True

            if cmd == "PUB":
                if len(parts) != 2:
                    print("ERROR")
                    return True

                try:
                    idx = int(parts[1]) - 1
                except ValueError:
                    print("ERROR")
                    return True

                self._publish_post(idx)
                return True

            options = parts[1:]

            if cmd == "P":
                self._print_profile(options)
                return True

            if cmd == "E":
                self._edit_profile(options)
                return True

        print("ERROR")
        return True

    #
    # Admin / Friendly Loop
    #
    def run_friendly(self, first_choice: str = "") -> None:
        self.in_admin_mode = False

        if first_choice.strip() != "":
            if not self._process_line(first_choice):
                return

        while True:
            try:
                line = input("> ")
            except EOFError:
                break

            if not self._process_line(line):
                break

    def run_admin(self) -> None:
        self.in_admin_mode = True

        while True:
            try:
                line = input()
            except EOFError:
                break

            if not self._process_line(line):
                break

    #
    # Edit Option
    #
    def _edit_profile(self, options: list[str]) -> None:
        prof = self.current_profile
        path = self.current_path
        if prof is None or path is None:
            print("ERROR")
            return

        if not options:
            print("ERROR")
            return

        # if save fails
        old_username = prof.username
        old_password = prof.password
        old_bio = prof.bio
        old_posts = [(p.entry, p.timestamp) for p in prof.get_posts()]

        plan: list[tuple[str, object]] = []

        shadow_posts = list(prof.get_posts())

        i = 0
        while i < len(options):
            opt = options[i]

            if opt in {"-usr", "-pwd", "-bio", "-addpost", "-delpost"}:
                if i + 1 >= len(options):
                    print("ERROR")
                    return
                val = options[i + 1]

                if opt == "-usr":
                    if not self._valid_userpass(val):
                        print("ERROR")
                        return
                    plan.append(("usr", val))

                elif opt == "-pwd":
                    if not self._valid_userpass(val):
                        print("ERROR")
                        return
                    plan.append(("pwd", val))

                elif opt == "-bio":
                    if val.strip() == "":
                        print("ERROR")
                        return
                    plan.append(("bio", val))

                elif opt == "-addpost":
                    if val.strip() == "":
                        print("ERROR")
                        return
                    plan.append(("addpost", val))
                    shadow_posts.append(Post(val))

                elif opt == "-delpost":
                    try:
                        idx = int(val) - 1
                    except ValueError:
                        print("ERROR")
                        return
                    if idx < 0 or idx >= len(shadow_posts):
                        print("ERROR")
                        return
                    plan.append(("delpost", idx))
                    del shadow_posts[idx]

                i += 2
            else:
                print("ERROR")
                return

        for op, val in plan:
            if op == "usr":
                prof.username = str(val)
            elif op == "pwd":
                prof.password = str(val)
            elif op == "bio":
                prof.bio = str(val)
            elif op == "addpost":
                prof.add_post(Post(str(val)))
            elif op == "delpost":
                ok = prof.del_post(int(val))
                if not ok:
                    print("ERROR")
                    return
        try:
            prof.save_profile(path)
        except DsuFileError:
            prof.username = old_username
            prof.password = old_password
            prof.bio = old_bio

            prof.get_posts().clear()
            for entry, ts in old_posts:
                prof.add_post(Post(entry, ts))

            print("ERROR")
            return
