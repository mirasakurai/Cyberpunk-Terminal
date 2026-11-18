from enum import Enum

# tab names used throughout the app
class Tab(str, Enum):
    MESSAGES = "messages"
    FILES = "files"
    NET = "net"
    CONSOLE = "console"