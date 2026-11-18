Cyberpunk Terminal

A fake terminal in a cyberpunk style. It's meant to be used as a prop for a game: players poke around in someone else's computer, read their chats, open files, browse a few "websites", play music and, if they're lucky, get into the console.

Everything you see in the terminal comes from plain JSON, HTML and media files, so you can fill it with your own story without touching the code (well, almost: see the notes about paths below).

Installation

You'll need Python 3.

bash
cd Cyberpunk_Terminal
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py


Basic settings

The main config lives in data/config.json:

json
{
  "enable_console": true,
  "current_date": "06.08.2045",
  "current_date_ru": "вт 06.08.2045"
}
enable_console: shows or hides the CONSOLE tab. Set it to false if you don't want players to have the console at all (or not yet).
current_date: the in-game "today", in DD.MM.YYYY format. The terminal uses it wherever it needs to show the current date.
current_date_ru: the same date with the day of the week, for the places where the interface shows it in Russian.

Messages

The MESSAGES tab shows chat conversations between characters.

Adding a chat group
Go to data/messages/.
Create a folder for the group, e.g. data/messages/MyGroup/. Every folder here becomes its own chat group in the interface.
Put the conversations inside as JSON files: msg_001.json, msg_002.json and so on.
Open datapools.py and point MSG_DIR at your folder.
What a conversation file looks like

data/messages/MyGroup/msg_001.json:

json
{
  "id": "msg_001",
  "subject": "conversation topic",
  "participants": ["nick1", "nick2"],
  "date": "2045-07-19",
  "thread": [
    {
      "sender": "nick1",
      "timestamp": "2045-07-19 13:02",
      "text": "message text"
    },
    {
      "sender": "nick2",
      "timestamp": "2045-07-19 13:05",
      "text": "reply",
      "image": "photo.jpg"
    },
    {
      "sender": "nick1",
      "timestamp": "2045-07-19 13:10",
      "text": "more text",
      "video": "clip.mp4"
    }
  ]
}

What each field does:

id: the conversation's ID. Chats are sorted by it from top to bottom, so msg_001 will be above msg_002.
subject: the title you see in the chat list.
participants: who's in the chat.
date: when the conversation started.
thread: the messages themselves, in the order they were sent. Each message has:
sender: the nickname of whoever wrote it
timestamp: when it was sent
text: the message itself
image / video (optional): an attached picture or video

To attach media, drop the file into the same folder as the JSON and write its name (or a path relative to that folder) in image or video.

Giving each character a color

Every participant can have their own color in the chat. The colors are set in ui.py, in self.colors:

python
self.colors = {
    'shtanga': ACCENT_CYAN,
    'sh0v': "#004D00",
    'rjjavii': "#310000",
    'in3y': "#003441",
    'pr4vyi': "#4B2900",
    'lev4y4': "#440044",
    'k0styashhhhka': "#473333",
    're_ey': "#8AC57E",
    'tiktik': "#0B2E11",
}

Files

The FILES tab is the victim's documents: notes, photos, videos, audio recordings.

Adding a collection
Go to data/files/.
Create a folder, e.g. data/files/MyCollection/.
Add a JSON file for each document: file_001.json, file_002.json...
Open datapools.py and point the files path at your folder.
What a file looks like

data/files/MyCollection/file_001.json:

json
{
  "id": "file_001",
  "name": "filename.txt",
  "type": "text",
  "size": "2.4 MB",
  "date": "2045-08-06 14:20",
  "content": "file text content"
}
name: the file name shown in the list.
type: what kind of file it is.
size: purely cosmetic, write whatever looks believable.
date: when the file was "modified".
content: the text you see when you open it.

If the file should be a picture, a video or a recording, add the matching field with a relative path:

json
"image": "photo.jpg",
"video": "clip.mp4",
"audio": "voice_note.mp3"

Music

The music player sits on the right side of the terminal.

Go to data/music/.
Create a folder for the playlist, e.g. data/music/MyPlaylist/.
Drop the MP3 or WAV files straight into it.
Open right_panel.py and point MUSIC_DIR at that folder.

Websites

Honest disclaimer: I generated all the websites with AI. I tried building them by hand and gave up, sorry :)

Each site is a separate HTML file. When a player clicks one, it opens in an overlay on top of the terminal. Since they're just regular HTML, you can edit them however you want.

To add a site, put a new HTML file into data/sites/, e.g. data/sites/my_website.html.

Console

The console is the most "hacker" part of the terminal. Players can walk through the victim's file system, read files, decode strings and check network info. You can turn it off entirely in data/config.json.

How you get into the console

The console doesn't open right away. You get in in a few stages:

LOCKED. This is where the console starts. Players don't type a password by hand: instead they do a skill check in the game. If they pass, the game master presses the green button; if not, the red one. (Later this will be done through a Telegram bot command instead of buttons.)
ANIMATING. Right after the button, the password "gets cracked" on screen. If the check passed, the animation ends on the real password from console_config.json. If it failed, it's just random digits.
AWAITING_CONFIRMATION. When the animation finishes, the terminal waits for someone to press >.
✅ If the password is right, you are inside
❌ If it's wrong, an "access denied" message appears, and the console stays locked until the end of the session.

AUTHORIZED. The console is open and you can run commands. It stays unlocked for the rest of the session.

Console settings

Everything about the console is configured in data/console_config.json:

json
{
  "correct_password": "492754",
  "sudo_password": "N3bul0sa",
  "username": "kryss",
  "hostname": "DANGER-PC",
  "startup_message": "Welcome to NOX. Type 'help' for available commands.",
  "network_interfaces": [
    {
      "name": "lo",
      "ip": "127.0.0.1",
      "mask": "255.0.0.0",
      "status": "UP",
      "mac": "00:00:00:00:00:00"
    },
    {
      "name": "eth0",
      "ip": "10.42.0.15",
      "mask": "255.255.0.0",
      "status": "UP",
      "mac": "4A:7E:2C:91:F3:08"
    }
  ],
  "protected_files": {
    "/home/operator/secret.txt": "shadow42"
  },
  "sudo_files": [
    "/home/operator/cameras.feed"
  ]
}
correct_password: the password that shows up at the end of the animation when the check passes.
sudo_password: the password for the sudo command. Players won't get it automatically, so hide it somewhere in the story (in a chat, a file, a website...).
username and hostname: shown in the prompt as username@hostname:path$.
startup_message: the first line players see after getting in.
network_interfaces: what the ip a command prints. Each interface has a name (lo, eth0...), an IP, a subnet mask, a status (UP/DOWN) and a MAC address.
protected_files: files that ask for their own password. Format: "path": "password".
sudo_files: files that can only be read with sudo.

Commands

These work once the console is unlocked:

Command	What it does
help	Lists all commands
pwd	Shows which folder you're in
ls [DIR]	Lists a folder's contents
ls -a [DIR]	Same, but also shows hidden files
cd [DIR]	Moves to a folder: cd /home/operator, cd .., cd ~
cat FILE	Shows a file's contents (unless it's password-protected or needs sudo)
ip a	Shows network interfaces
sudo COMMAND	Runs a command as admin (asks for the sudo password)
decode TYPE STRING	Decodes a string from base64, hex or rot13
clear	Clears the screen
cowsay MESSAGE	An ASCII cow says your message. Just because

decode examples:

decode base64 SGVsbG8gV29ybGQ=
decode hex 48656C6C6F
decode rot13 Uryyb


Locked files

There are two ways to lock a file, and you can use them as different levels of difficulty.

Password-protected files (protected_files):

When you cat one, the console asks password required:.
The right password shows the file; a wrong one gives access denied.
Each file has its own password, so you can hide them all over the story.

Sudo files (sudo_files):

A plain cat returns sudo required.
You need sudo cat /path/to/file, and then the sudo_password.


The console's file system

The console doesn't touch your real disk. Its file system is fake and lives in data/console/:

In the console, paths start with /home, e.g. /home/operator/.
On disk, those files are in data/console/home/. So /home/operator/secret.txt in the console is data/console/home/operator/secret.txt on disk.
Relative paths work: ., .., ~ (the home folder).
You can't get out above /home, so players can't wander into your real files.

To fill the console with content, just create folders and files in data/console/home/, and they'll show up in ls.