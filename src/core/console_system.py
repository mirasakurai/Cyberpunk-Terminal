import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import base64
import codecs

ROOT = Path(__file__).parent.parent.parent
CONSOLE_ROOT = ROOT / "data" / "console"


class VirtualFilesystem:

    def __init__(self):
        self.current_path = "/home/operator"
        self.root_path = CONSOLE_ROOT
        self.virtual_root = "/home"

    def _virtual_to_real(self, virtual_path: str) -> Path:
        if virtual_path.startswith("/home"):
            rel_path = virtual_path[5:].lstrip("/")
        else:
            rel_path = virtual_path.lstrip("/")

        return self.root_path / "home" / rel_path

    def _normalize_path(self, path: str) -> str:
        parts = []
        for part in path.split("/"):
            if part == "..":
                if parts and parts[-1] != "home":
                    parts.pop()
            elif part and part != ".":
                parts.append(part)

        result = "/" + "/".join(parts)
        if not result.startswith("/home"):
            result = "/home"

        return result

    def resolve_path(self, path: str) -> str:
        if path == "~":
            return "/home/operator"
        if path.startswith("/"):
            return self._normalize_path(path)
        if path == "..":
            return self._normalize_path(self.current_path + "/..")
        if path == ".":
            return self.current_path

        return self._normalize_path(f"{self.current_path}/{path}")

    def exists(self, virtual_path: str) -> bool:
        real_path = self._virtual_to_real(virtual_path)
        return real_path.exists()

    def is_dir(self, virtual_path: str) -> bool:
        real_path = self._virtual_to_real(virtual_path)
        return real_path.is_dir()

    def is_file(self, virtual_path: str) -> bool:
        real_path = self._virtual_to_real(virtual_path)
        return real_path.is_file()

    def list_dir(self, virtual_path: str, show_hidden: bool = False) -> List[Dict]:
        real_path = self._virtual_to_real(virtual_path)

        if not real_path.is_dir():
            return []

        items = []
        try:
            for item in real_path.iterdir():
                name = item.name
                if not show_hidden and name.startswith("."):
                    continue

                items.append({
                    "name": name,
                    "type": "dir" if item.is_dir() else "file"
                })
        except PermissionError:
            pass

        return sorted(items, key=lambda x: (x["type"] != "dir", x["name"]))

    def read_file(self, virtual_path: str) -> Optional[str]:
        real_path = self._virtual_to_real(virtual_path)

        if not real_path.is_file():
            return None

        try:
            with open(real_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return None

    def get_file_info(self, virtual_path: str) -> Optional[Dict]:
        real_path = self._virtual_to_real(virtual_path)

        if not real_path.exists():
            return None

        ext = real_path.suffix.lower()
        is_image = ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        is_audio = ext in ['.mp3', '.wav', '.ogg', '.flac', '.m4a']

        return {
            "name": real_path.name,
            "is_dir": real_path.is_dir(),
            "is_image": is_image,
            "is_audio": is_audio,
            "real_path": str(real_path),
            "extension": ext
        }


class ConsoleSystem:
    def __init__(self):
        self.config = self._load_config()
        self.filesystem = VirtualFilesystem()
        self.access_denied = False
        self.has_sudo = False

        self.password_mode = None  # None, 'sudo', 'file'
        self.pending_command = None
        self.pending_file = None

        self.command_history: List[str] = []
        self.max_history = 5

        # Файлы, защищённые паролем (виртуальный путь -> пароль)
        self.protected_files = self.config.get("protected_files", {})

        # Файлы, требующие sudo
        self.sudo_files = self.config.get("sudo_files", [])

    def _load_config(self) -> Dict:
        config_path = ROOT / "data" / "console_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                "correct_password": "1234",
                "sudo_password": "sudo123",
                "username": "user",
                "hostname": "system",
                "home_directory": "/home/user",
                "startup_message": "System ready."
            }

    def add_to_history(self, cmd: str):
        if cmd.strip() and (not self.command_history or self.command_history[-1] != cmd):
            self.command_history.append(cmd)
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)

    def get_history(self, index: int) -> str:
        if 0 <= index < len(self.command_history):
            return self.command_history[-(index + 1)]
        return ""

    def get_prompt(self) -> str:
        if self.password_mode:
            return "[sudo] password: "

        user = "root" if self.has_sudo else self.config.get("username", "user")
        host = self.config.get("hostname", "system")
        path = self.filesystem.current_path
        symbol = "#" if self.has_sudo else "$"
        return f"{user}@{host}:{path}{symbol} "

    def execute_command(self, cmd: str) -> str:
        if self.access_denied:
            return "ACCESS DENIED - System locked"

        cmd = cmd.strip()
        if not cmd:
            return ""

        if self.password_mode == 'sudo':
            return self._handle_sudo_password(cmd)
        elif self.password_mode == 'file':
            return self._handle_file_password(cmd)

        # Добавляем в историю
        self.add_to_history(cmd)

        parts = cmd.split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        if command == "help":
            return self._cmd_help()
        elif command == "pwd":
            return self._cmd_pwd()
        elif command == "ip":
            return self._cmd_ip(args)
        elif command == "ls":
            show_hidden = "-a" in args
            target_args = [a for a in args if not a.startswith("-")]
            target = target_args[0] if target_args else "."
            return self._cmd_ls(target, show_hidden)
        elif command == "cd":
            return self._cmd_cd(args[0] if args else "~")
        elif command == "cat":
            if not args:
                return "cat: missing filename"
            return self._cmd_cat(" ".join(args))
        elif command == "decode":
            if len(args) < 2:
                return "decode: usage: decode <type> <string>"
            return self._cmd_decode(args[0], " ".join(args[1:]))
        elif command == "sudo":
            return self._cmd_sudo(args)
        elif command == "clear":
            return "__CLEAR__"
        elif command == "cowsay":
            if not args:
                return "cowsay: missing message"
            return self._cmd_cowsay(" ".join(args))
        else:
            return f"command not found: {command}"

    def _handle_sudo_password(self, password: str) -> str:
        self.password_mode = None

        if password == self.config.get("sudo_password"):
            self.has_sudo = True
            if self.pending_command:
                cmd = self.pending_command
                self.pending_command = None
                return self.execute_command(cmd)
            return ""
        else:
            self.pending_command = None
            return "sudo: incorrect password"

    def _handle_file_password(self, password: str) -> str:
        self.password_mode = None
        filename = self.pending_file
        self.pending_file = None

        if not filename:
            return "error: no file pending"

        path = self.filesystem.resolve_path(filename)
        expected_password = self.protected_files.get(path)

        if expected_password and password == expected_password:
            content = self.filesystem.read_file(path)
            return content if content else "error reading file"
        else:
            return "access denied"

    def _cmd_help(self) -> str:
        return """Available commands:
  help                    Show this message
  pwd                     Print working directory
  ls [DIR]                List directory contents
  ls -a [DIR]             List all files (including hidden)
  cd [DIR]                Change directory
  cat FILE                Display file contents
  decode TYPE STRING      Decode string (base64, hex, rot13)
  ip a                    Show network interfaces
  sudo COMMAND            Run command with elevated privileges
  clear                   Clear terminal
  cowsay MESSAGE          Make a cow say something
"""

    def _cmd_pwd(self) -> str:
        return self.filesystem.current_path

    def _cmd_ip(self, args: list) -> str:
        if not args or args[0] != "a":
            return "Usage: ip a"

        interfaces = self.config.get("network_interfaces", [
            {"name": "lo", "ip": "127.0.0.1", "mask": "255.0.0.0", "status": "UP"},
            {"name": "eth0", "ip": "192.168.1.100", "mask": "255.255.255.0", "status": "UP"},
        ])

        output = []
        for i, iface in enumerate(interfaces, 1):
            name = iface.get("name", f"eth{i}")
            ip = iface.get("ip", "0.0.0.0")
            mask = iface.get("mask", "255.255.255.0")
            status = iface.get("status", "UP")
            mac = iface.get("mac", f"00:1A:2B:3C:4D:{i:02X}")

            output.append(f"{i}: {name}: <BROADCAST,MULTICAST,{status}> mtu 1500")
            output.append(f"    link/ether {mac}")
            output.append(f"    inet {ip}/{self._mask_to_cidr(mask)} scope global {name}")

        return "\n".join(output)

    def _mask_to_cidr(self, mask: str) -> int:
        try:
            parts = [int(x) for x in mask.split('.')]
            binary = ''.join(format(x, '08b') for x in parts)
            return binary.count('1')
        except:
            return 24

    def _cmd_ls(self, target: str, show_hidden: bool) -> str:
        path = self.filesystem.resolve_path(target)

        if not self.filesystem.exists(path):
            return f"ls: cannot access '{target}': No such file or directory"

        if not self.filesystem.is_dir(path):
            return f"ls: cannot access '{target}': Not a directory"

        items = self.filesystem.list_dir(path, show_hidden)
        if not items:
            return ""

        result = []
        for item in items:
            name = item["name"]
            if item["type"] == "dir":
                name = f"{name}/"
            result.append(name)

        return "  ".join(result)

    def _cmd_cd(self, target: str) -> str:
        path = self.filesystem.resolve_path(target)

        if not self.filesystem.exists(path):
            return f"cd: {target}: No such directory"

        if not self.filesystem.is_dir(path):
            return f"cd: {target}: Not a directory"
        if not path.startswith("/home"):
            return "cd: Permission denied"

        self.filesystem.current_path = path
        return ""

    def _cmd_cat(self, filename: str) -> str:
        path = self.filesystem.resolve_path(filename)

        if not self.filesystem.exists(path):
            return f"cat: {filename}: No such file or directory"

        if self.filesystem.is_dir(path):
            return f"cat: {filename}: Is a directory"
        if path in self.sudo_files and not self.has_sudo:
            return "sudo required"

        if path in self.protected_files:
            self.password_mode = 'file'
            self.pending_file = filename
            return "password required:"

        # Проверяем тип файла
        file_info = self.filesystem.get_file_info(path)
        if file_info:
            if file_info["is_image"]:
                return f"[IMAGE: {file_info['real_path']}]"
            if file_info["is_audio"]:
                return f"[AUDIO: {file_info['real_path']}]"

        content = self.filesystem.read_file(path)
        if content is None:
            return f"cat: {filename}: Cannot read file"

        return content.rstrip()

    def _cmd_decode(self, decode_type: str, data: str) -> str:
        try:
            if decode_type.lower() == "base64":
                return base64.b64decode(data).decode('utf-8', errors='ignore')
            elif decode_type.lower() == "hex":
                return bytes.fromhex(data).decode('utf-8', errors='ignore')
            elif decode_type.lower() == "rot13":
                return codecs.encode(data, 'rot_13')
            else:
                return f"decode: unknown type '{decode_type}'"
        except Exception as e:
            return f"decode error: {str(e)}"

    def _cmd_sudo(self, args: list) -> str:
        if not args:
            return "sudo: no command specified"

        if self.has_sudo:
            return self.execute_command(" ".join(args))

        self.password_mode = 'sudo'
        self.pending_command = " ".join(args)
        return ""

    def _cmd_cowsay(self, message: str) -> str:
        max_width = 40
        words = message.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_width:
                current_line = f"{current_line} {word}" if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        if not lines:
            lines = [message]
        width = max(len(line) for line in lines)
        border_top = " " + "_" * (width + 2)
        border_bottom = " " + "-" * (width + 2)

        bubble = [border_top]
        if len(lines) == 1:
            bubble.append(f"< {lines[0].ljust(width)} >")
        else:
            bubble.append(f"/ {lines[0].ljust(width)} \\")
            for line in lines[1:-1]:
                bubble.append(f"| {line.ljust(width)} |")
            bubble.append(f"\\ {lines[-1].ljust(width)} /")
        bubble.append(border_bottom)

        # Корова
        cow = r"""        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||"""

        return "\n".join(bubble) + "\n" + cow

    def verify_password(self, password: str, file_path: Optional[str] = None) -> bool:
        if file_path:
            path = self.filesystem.resolve_path(file_path)
            expected = self.protected_files.get(path)
            if expected:
                return password == expected

        return password == self.config.get("sudo_password")
