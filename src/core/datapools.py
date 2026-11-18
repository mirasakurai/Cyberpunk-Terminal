import json
from pathlib import Path

# find data dirs
ROOT = Path(__file__).parent.parent.parent
MSG_DIR = ROOT / "data" / "messages" / "Fists"
FILES_DIR = ROOT / "data" / "files" / "Fists"


def load_all_messages():
    # load all message json files
    if not MSG_DIR.exists():
        return {}
    msgs = {}
    files = sorted(MSG_DIR.glob("msg_*.json"))
    # sort by number in filename
    files.sort(key=lambda f: int(f.stem.split('_')[1]))
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                txt = f.read().strip()
                if not txt:
                    continue
                data = json.loads(txt)
                mid = data.get("id", fp.stem)
                msgs[mid] = data
        except:
            # skip broken files
            continue
    return msgs


def load_all_files():
    # load all file json files
    if not FILES_DIR.exists():
        return {}
    out = {}
    files = sorted(FILES_DIR.glob("file_*.json"))
    # sort by number in filename
    files.sort(key=lambda f: int(f.stem.split('_')[1]))
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                txt = f.read().strip()
                if not txt:
                    continue
                data = json.loads(txt)
                fid = data.get("id", fp.stem)
                out[fid] = data
        except:
            # skip broken files
            continue
    return out
