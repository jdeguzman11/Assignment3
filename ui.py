# Justin DeGuzman
# justicd1@uci.edu
# 72329664

# ui.py

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

    def _ask_yes_no(self, prompt: str, default: str = "n") -> bool:
        try:
            suffix = " [Y/n]: " if default.lower() == "y" else " [y/N]: "
            ans = input(prompt + suffix).strip().lower()
        except EOFError:
            return False
        if ans == "":
            ans = default.lower()
        return ans in {"y", "yes"}

    def _prompt_nonempty(self, label: str) -> Optional[str]:
        while True:
            try:
                val = input(label).strip()
            except EOFError:
                return None
            if val != "":
                return val
            print("Please enter a value (cannot be blank).")

    def _edit_publish_settings_flow(self) -> bool:
        prof = self.current_profile
        path = self.current_path

        if prof is None or path is None:
            print("ERROR")
            return False

        server = getattr(prof, "dsusever", "")

        print()
        print("Before publishing, confirm these settings:")
        print(f"  Username: {prof.username}")
        print(f"  Password: {'*' * len(prof.password) if prof.password else '(none)'}")
        print(f"  Bio:      {prof.bio}")
        print(f"  Server:   {server if server else '(missing)'}")
        print()

        if not self._ask_yes_no("Do you want to edit any of these before publishing?", default="n"):
            return True

        # username
        if self._ask_yes_no("Edit username?", default="n"):
            u = self._prompt_nonempty("New username: ")
            if u is None:
                return False
            self._edit_profile(["-usr", u])

        # password
        if self._ask_yes_no("Edit password?", default="n"):
            p = self._prompt_nonempty("New password: ")
            if p is None:
                return False
            self._edit_profile(["-pwd", p])

        # bio
        if self._ask_yes_no("Edit bio?", default="n"):
            b = self._prompt_nonempty("New bio: ")
            if b is None:
                return False
            self._edit_profile(["-bio", b])

        # server
        if self._ask_yes_no("Edit server?", default="n"):
            s = self._prompt_nonempty("New server: ")
            if s is None:
                return False
            prof.dsuserver = s
            try:
                prof.save_profile(path)
                print("UPDATED server.")
            except DsuFileError:
                print("ERROR")
                return False

        return True

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
    def _split_path_and_options(tokens: list[str]) -> \
            tuple[Optional[str], list[str]]:
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
            post.entry,
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

                if not self.in_admin_mode:
                    if not self._edit_publish_settings_flow():
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
    # User Mode UI
    #
    def _user_banner(self) -> None:
        print()
        print("----DSU Profile Manager----")
        if self.current_path:
            print(f"Loaded: {self.current_path}")
        else:
            print("Loaded: (none)")
        print("Type a command or choose an option below.")
        print()

    def _user_menu(self) -> None:
        loaded = (self.current_profile is not None
                  and self.current_path is not None)

        print("Commands Available at Anytime:")
        print(
            "  L <dir> [-f] [-r] [-s <name>] [-e <ext>]  List Directory "
            "Contents (recursively with -r)"
        )
        print(
            "  C <dir> -n <name>"
            "                         Create/Load DSU Profile")
        print("  O <path_to_dsu>                           Open DSU Profile ")
        print("  D <path_to_dsu>                           Delete DSU Profile")
        print(
            "  R <path_to_dsu>                           "
            "Read/Print a .dsu File")
        print("  Q                                         Quit")
        print()

        if not loaded:
            print("Quick Actions:")
            print("  Create Profile (C <directory> -n <name>)")
            print("  Open Profile   (O <path_to_dsu>)")
            print("  List Directory (L <dir> ...)")
            print("  Quit           (Q)")
            print()

        else:
            print("Profile Commands (requires a loaded profile):")
            print("  P -usr | -pwd | -bio | -posts | -post <#> | -all")
            print(
                "  E -usr <u> -pwd <p> -bio <b> -addpost \"...\" "
                "  -delpost <#>")
            print("  PUB <#>")
            print()

            print("Quick Actions:")
            print("  View All Profile Info      (P -all)")
            print("  View Posts List            (P -posts)")
            print("  View One Post              (P -post <#>)")
            print("  Add a Post                 (E -addpost \"...\")")
            print("  Delete a Post              (E -delpost <#>)")
            print("  Publish a Post             (PUB <#>)")
            print("  List Directory             (L <dir> ...)")
            print("  Delete a DSU file          (D <path_to_dsu>)")
            print("  Read a DSU file            (R <path_to_dsu>)")
            print("  Open Another Profile       (O <path_to_dsu>)")
            print("  Quit                       (Q)")
            print()

    def _user_choice_to_command(self, choice: str) -> str:
        c = choice.strip()
        loaded = (self.current_profile is not None and
                  self.current_path is not None)

        if not loaded:
            if c == "1":
                try:
                    directory = input("Directory: ").strip()
                    name = input("Name (without .dsu allowed): ").strip()
                except EOFError:
                    return ""
                if directory == "" or name == "":
                    return ""
                return f'C {directory} -n {name}'

            if c == "2":
                try:
                    path = input("Path to .dsu: ").strip()
                except EOFError:
                    return ""
                if path == "":
                    return ""
                return f'O {path}'

            if c == "3":
                try:
                    directory = input("Directory to list: ").strip()
                    opts = input("Options: ").strip()
                except EOFError:
                    return ""
                if directory == "":
                    return ""
                return f'L {directory} {opts}'.strip()

            if c == "4":
                return "Q"

            return choice

        if c == "1":
            return "P -all"

        if c == "2":
            return "P -posts"

        if c == "3":
            try:
                num = input("Post number: ").strip()
            except EOFError:
                return ""
            if num == "":
                return ""
            return f'P -post {num}'

        if c == "4":
            try:
                text = input("Post text: ").strip()
            except EOFError:
                return ""
            if text == "":
                return ""
            return f'E -addpost {text}'

        if c == "5":
            try:
                num = input("Post number to delete: ").strip()
            except EOFError:
                return ""
            if num == "":
                return ""
            return f'E -delpost {num}'

        if c == "6":
            try:
                num = input("Post number to publish: ").strip()
            except EOFError:
                return ""
            if num == "":
                return ""
            return f'PUB {num}'

        if c == "7":
            try:
                directory = input("Directory to list: ").strip()
                opts = input("Options: ").strip()
            except EOFError:
                return ""
            if directory == "":
                return ""
            return f'L {directory} {opts}'.strip()

        if c == "8":
            try:
                path = input("Path to .dsu to delete: ").strip()
            except EOFError:
                return ""
            if path == "":
                return ""
            return f"D {path}"

        if c == "9":
            try:
                path = input("Path to .dsu to read: ").strip()
            except EOFError:
                return ""
            if path == "":
                return ""
            return f"R {path}"

        if c == "10":
            try:
                path = input("Path to .dsu: ").strip()
            except EOFError:
                return ""
            if path == "":
                return ""
            return f"O {path}"

        if c == "11":
            return "Q"

        return choice

    #
    # Admin / Friendly Loop
    #
    def run_friendly(self, first_choice: str = "") -> None:
        self.in_admin_mode = False

        if first_choice.strip() != "":
            if not self._process_line(first_choice):
                return

        while True:
            self._user_banner()
            self._user_menu()

            try:
                line = input("> ")
            except EOFError:
                break

            if line.strip() == "":
                continue

            cmd_line = self._user_choice_to_command(line)
            if cmd_line.strip() == "":
                continue

            if not self._process_line(cmd_line):
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
