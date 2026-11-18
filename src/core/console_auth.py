import json
from pathlib import Path
from enum import Enum

# auth states: locked -> animating -> confirm/denied -> authorized/locked
class ConsoleAuth(str, Enum):
    LOCKED = "locked"
    ANIMATING = "animating"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AUTHORIZED = "authorized"
    DENIED = "denied"


ROOT = Path(__file__).parent.parent.parent
ACCESS_FILE = ROOT / "data" / "access_graph.json"

class AcessControl:
    # password checker for console and files
    def __init__(self, path=ACCESS_FILE):
        self.path = path

    def _load(self):
        if not self.path.exists():
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def check(self, target_id, pwd):
        g = self._load()
        t = g.get("targets", {}).get(target_id)
        if not t:
            return False
        return t["password"] == pwd

    def get_console_password(self):
        return self._load().get("console_password", "")

    def check_console_password(self, pwd):
        return pwd == self.get_console_password()
