import json
from pathlib import Path

from core.Console import Console
from core import datapools
from core import events
from core.console_auth import AcessControl, ConsoleAuth
from core.state import AppState
from core.tabs import Tab

ROOT = Path(__file__).parent.parent
CONFIG = ROOT / "data" / "config.json"
NET = ROOT / "data" / "net.json"

# main engine that handles everything
class Engine:
    def __init__(self):
        self.state = AppState()
        self.access = AcessControl()
        self.console = Console()
        self.events = events.Events()
        self._setup_commands()
        self._load_cfg()

    def _load_cfg(self):
        # read config.json
        if not CONFIG.exists():
            return
        try:
            with open(CONFIG, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except:
            return
        # show console if enabled
        if cfg.get("enable_console"):
            self.state.enable_tab(Tab.CONSOLE)

    # navigation
    def navigate(self, name):
        # go to tab by name
        try:
            t = Tab(name)
        except ValueError:
            return f"Unknown tab: {name}"
        if not self.state.is_tab_enabled(t):
            return f"tab disabled: {t.value}"
        self.state.navigate(t)
        return self.state.current_tab.value

    def get_tabs(self):
        return [t.value for t in Tab if self.state.is_tab_enabled(t)]

    def get_messages(self):
        return datapools.load_all_messages()

    def get_files(self):
        return datapools.load_all_files()

    def get_net_sites(self):
        with open(NET, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_site_content(self, sid):
        for s in self.get_net_sites():
            if s["id"] == sid:
                return s.get("content", "")
        return None

    # console auth
    def start_console_animating(self):
        # start password animation
        self.state.set_console_stage(ConsoleAuth.ANIMATING)
        pwd = self.access.get_console_password()
        self.events.emit("console_auth_animation", {"password": pwd, "will_succeed": True})

    def console_denied(self, wrong="********"):
        # show failed password animation
        self.state.set_console_stage(ConsoleAuth.ANIMATING)
        self.events.emit("console_auth_animation", {"password": wrong, "will_succeed": False})

    def finish_unlock_animation_success(self):
        # password was right, wait for user to click ok
        if self.state.console_stage != ConsoleAuth.ANIMATING:
            return
        self.state.set_console_stage(ConsoleAuth.AWAITING_CONFIRMATION)
        self.events.emit("console_auth_awaiting_confirmation", None)

    def confirm_console_acess(self):
        # user clicked ok, grant access
        if self.state.console_stage != ConsoleAuth.AWAITING_CONFIRMATION:
            return "not ready"
        self.state.set_console_stage(ConsoleAuth.AUTHORIZED)
        self.events.emit("console_authorized", None)
        return "authorized"

    def finish_unlock_animation_denied(self):
        # password was wrong
        if self.state.console_stage != ConsoleAuth.ANIMATING:
            return
        self.state.set_console_stage(ConsoleAuth.DENIED)
        self.events.emit("console_auth_denied", None)

    def reset_console_after_denial(self):
        # lock console again after failed attempt
        if self.state.console_stage == ConsoleAuth.DENIED:
            self.state.set_console_stage(ConsoleAuth.LOCKED)

    # commands
    def run_console_command(self, inp):
        if not self.state.is_tab_enabled(Tab.CONSOLE):
            return "console unavailable"
        if not self.state.is_console_authorized():
            return "access denied: locked"
        return self.console.execute(inp)

    def _setup_commands(self):
        self.console.register("ls", self._cmd_ls)
        self.console.register("cat", self._cmd_cat)
        self.console.register("unlock", self._cmd_unlock)

    def _cmd_ls(self, args):
        out = []
        for f in self._files_flat():
            m = "[LOCKED]" if f.get("locked") else "[OPEN]"
            out.append(f"{m} {f['name']}")
        return "\n".join(out)

    def _cmd_cat(self, args):
        if not args:
            return "usage: cat <filename>"
        for f in self._files_flat():
            if f["name"] == args[0]:
                if f.get("locked"):
                    return f"access denied: {f['name']} is locked"
                return f["content"]
        return f"no such file: {args[0]}"

    def _cmd_unlock(self, args):
        if len(args) < 2:
            return "usage: unlock <id> <password>"
        tid, pwd = args[0], args[1]
        if self.access.check(tid, pwd):
            f = self.get_files().get(tid)
            return f["content"] if f else "???"
        return "access denied"

    def _files_flat(self):
        res = []
        for fid, data in self.get_files().items():
            if isinstance(data, dict):
                res.append(data)
            else:
                res.append({"id": fid, "content": data})
        return res
