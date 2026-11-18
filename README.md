
# Cyberpunk Terminal

[Installation](#-installation) •
[Settings](#%EF%B8%8F-basic-settings) •
[Messages](#-messages) •
[Files](#-files) •
[Music](#-music) •
[Websites](#-websites) •
[Console](#-console)


<img width="5119" height="1236" alt="image" src="https://github.com/user-attachments/assets/c1fe8689-0f03-4b60-8eba-0171161a4c25" />
<img width="5101" height="1235" alt="image" src="https://github.com/user-attachments/assets/31da4ab7-0ea5-45af-8b7b-99a34364d0f5" />

---

## Why and wat

Players poke around in someone else's computer: they read chats, open files, browse a few "websites", play music and, if they're lucky, get into the console.

Everything you see in the terminal comes from plain JSON, HTML and media files* so you can fill it with your own story without touching the code (well, almost: see the notes about paths below).

| Tab | Why |
|---|---|
|Messages| Chat conversations between characters, with photos and videos |
|Files | The victim's documents: notes, images, videos, audio |
|Music| A player on the right side of the screen |
|Websites| Fake sites that open in an overlay |
|Console| A hacker console with its own file system, passwords and sudo |

---

## Installation

> [!NOTE]
> You'll need **Python 3**.

```bash
cd Cyberpunk_Terminal
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

---

## Basic settings

The main config lives in `data/config.json`:

| Field | What it does |
|---|---|
| `enable_console` | Shows or hides the **CONSOLE** tab. Set it to `false` if you don't want players to have the console at all (or not yet) |
| `current_date` | The in-game "today", in `DD.MM.YYYY` format. The terminal uses it wherever it needs to show the current date |
| `current_date_ru` | The same date with the day of the week, for the places where the interface shows it in Russian |

---

## Messages

The **MESSAGES** tab shows chat conversations between characters.
<img width="1289" height="1145" alt="image" src="https://github.com/user-attachments/assets/05124975-a955-45d5-abcb-02993863d83d" />

### Adding a chat group

1. Go to `data/messages/`
2. Create a folder for the group, e.g. `data/messages/MyGroup/`. Every folder here becomes its own chat group in the interface
3. Put the conversations inside as JSON files: `msg_001.json`, `msg_002.json` and so on
4. Open `datapools.py` and point `MSG_DIR` at your folder

### What a conversation file looks like

| Field | What it does |
|---|---|
| `id` | The conversation's ID. Chats are sorted by it from top to bottom, so `msg_001` will be above `msg_002` |
| `subject` | The title you see in the chat list |
| `participants` | Who's in the chat |
| `date` | When the conversation started |
| `thread` | The messages themselves, in the order they were sent |
| `sender` | The nickname of whoever wrote it |
| `timestamp` | When it was sent |
| `text` | The message itself |
| `image` / `video` | *Optional.* An attached picture or video |

> [!TIP]
> To attach media, drop the file into the same folder as the JSON and write its name (or a path relative to that folder) in `image` or `video`.

### Giving each character a color

Every participant can have their own color in the chat. The colors are set in `ui.py`, in `self.colors`:

```python
self.colors = {
    'shtanga': ACCENT_CYAN,
    'sh0v': "#004D00",
    'rjjavii': "#310000"
}
```

---

## Files

The **FILES** tab is the victim's documents: notes, photos, videos, audio recordings.
<img width="2473" height="1167" alt="image" src="https://github.com/user-attachments/assets/be848ef9-91a1-4115-a558-0e9daeb1457e" />

### Adding a collection

1. Go to `data/files/`
2. Create a folder, e.g. `data/files/MyCollection/`
3. Add a JSON file for each document: `file_001.json`, `file_002.json`...
4. Open `datapools.py` and point the files path at your folder

### What a file looks like

| Field | What it does |
|---|---|
| `name` | The file name shown in the list |
| `type` | What kind of file it is |
| `size` | Purely cosmetic, write whatever looks believable |
| `date` | When the file was "modified" |
| `content` | The text you see when you open it |

If the file should be a picture, a video or a recording, add the matching field with a relative path:

```json
"image": "photo.jpg",
"video": "clip.mp4",
"audio": "voice_note.mp3"
```

---

## Music

The music player sits on the right side of the terminal.

1. Go to `data/music/`
2. Create a folder for the playlist, e.g. `data/music/MyPlaylist/`
3. Drop the **MP3** or **WAV** files straight into it
4. Open `right_panel.py` and point `MUSIC_DIR` at that folder

---

## Websites

> [!NOTE]
> Honest disclaimer: I generated all the websites with AI. I tried building them by hand and gave up, sorry :)

<img width="1388" height="979" alt="image" src="https://github.com/user-attachments/assets/8b9f68fd-f847-4c52-8f93-0fff82444b37" />


Each site is a separate HTML file. When a player clicks one, it opens in an overlay on top of the terminal. Since they're just regular HTML, you can edit them however you want.

To add a site, put a new HTML file into `data/sites/`, e.g. `data/sites/my_website.html`.

---

## Console

The console is the most "hacker" part of the terminal. Players can walk through the victim's file system, read files, decode strings and check network info. You can turn it off entirely in `data/config.json`.

### How you get into the console

The console doesn't open right away. You get in in a few stages:

| Stage | What happens |
|---|---|
| **LOCKED** | This is where the console starts. Players don't type a password by hand: instead they do a skill check in the game. If they pass, the game master presses the green button; if not, the red one. *(Later this will be done through a Telegram bot command instead of buttons.)* |
| **ANIMATING** | Right after the button, the password "gets cracked" on screen. If the check passed, the animation ends on the real password from `console_config.json`. If it failed, it's just random digits |
| **AWAITING_CONFIRMATION** | When the animation finishes, the terminal waits for someone to press `>`.<br>✅ If the password is right, you are inside<br>❌ If it's wrong, an "access denied" message appears |
| **AUTHORIZED** | The console is open and you can run commands. It stays unlocked for the rest of the session |

> [!WARNING]
> If the password is wrong, the console stays locked **until the end of the session**. One try, no second chances.
<img width="930" height="721" alt="image" src="https://github.com/user-attachments/assets/e92babef-d2e6-4005-ba3a-b3c66d84c98d" />

###Console settings

Everything about the console is configured in `data/console_config.json`:

| Field | What it does |
|---|---|
| `correct_password` | The password that shows up at the end of the animation when the check passes |
| `sudo_password` | The password for the `sudo` command. Players won't get it automatically, so hide it somewhere in the story (in a chat, a file, a website...) |
| `username`, `hostname` | Shown in the prompt as `username@hostname:path$` |
| `startup_message` | The first line players see after getting in |
| `network_interfaces` | What the `ip a` command prints. Each interface has a name (`lo`, `eth0`...), an IP, a subnet mask, a status (`UP`/`DOWN`) and a MAC address |
| `protected_files` | Files that ask for their own password. Format: `"path": "password"` |
| `sudo_files` | Files that can only be read with `sudo` |

### Commands

These work once the console is unlocked:

| Command | What it does |
|---|---|
| `help` | Lists all commands |
| `pwd` | Shows which folder you're in |
| `ls [DIR]` | Lists a folder's contents |
| `ls -a [DIR]` | Same, but also shows hidden files |
| `cd [DIR]` | Moves to a folder: `cd /home/operator`, `cd ..`, `cd ~` |
| `cat FILE` | Shows a file's contents (unless it's password-protected or needs sudo) |
| `ip a` | Shows network interfaces |
| `sudo COMMAND` | Runs a command as admin (asks for the sudo password) |
| `decode TYPE STRING` | Decodes a string from `base64`, `hex` or `rot13` |
| `clear` | Clears the screen |
| `cowsay MESSAGE` | An ASCII cow says your message. Just because 🐄 |

`decode` examples:

```console
kryss@DANGER-PC:~$ decode base64 SGVsbG8gV29ybGQ=
kryss@DANGER-PC:~$ decode hex 48656C6C6F
kryss@DANGER-PC:~$ decode rot13 Uryyb
```

<img width="4255" height="1351" alt="image" src="https://github.com/user-attachments/assets/30a7cb87-92c2-49c8-9a48-8107ebd25598" />
