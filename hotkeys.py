import re
import signal
import subprocess
import sys
import yaml
import applescript
from os.path import basename
from time import sleep
from AppKit import NSWorkspace

CLEAR_SCREEN = '\033[2J'
TOP_LEFT = '\033[1;1H'
SHOW_CURSOR = '\033[?25h'
HIDE_CURSOR = '\033[?25l'
UNDERLINE_ON = '\033[4m'
UNDERLINE_OFF = '\033[24m'


def sigint_handler(sig, frame):
    print('%s' % SHOW_CURSOR)
    sys.exit(0)


def on_context_change(context):
    print(f"{CLEAR_SCREEN}{TOP_LEFT}{context['id']} ({context['app_path']})\n")
    try:
        path = f"hotkeys/{context['id']}.yaml"
        with open(path, "r") as stream:
            y = yaml.safe_load(stream)
            hotkeys = y["hotkeys"]
            max_key_size = len(max(hotkeys.keys(), key=len))
            for k, v in hotkeys.items():
                if isinstance(v, dict):
                    print(f"{UNDERLINE_ON}{k}{UNDERLINE_OFF}")
                    max_key_size2 = len(max(v.keys(), key=len))
                    for k2, v2 in v.items():
                        print(f"{k2:{max_key_size2}}\t{v2}")
                    print("")
                else:
                    print(f"{k:{max_key_size}}\t{v}")
    except yaml.YAMLError as e:
        print(e)
    except FileNotFoundError:
        print(f"No hotkeys file found at: {path}")


def get_context(app):
    name = app['NSApplicationName']
    context = name
    if name == "Google Chrome":
        result = applescript.tell.app("Google Chrome", "return URL of active tab of front window")
        if re.match("https://(gist.)?github.com", result.out):
            context += "-github"
        else:
            context += "-unknown"
    elif name == "iTerm2":
        result = applescript.tell.app("iTerm2", "return tty of current session of current tab of front window")
        tty = basename(result.out)
        cmd = ["ps", "-t", tty, "-opid=,stat=,command="]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        out, err = proc.communicate()
        context = "🤷🏻‍♂️"
        if proc.returncode == 0:
            processes = out.split("\n")
            processes = [p for p in processes if "S+" in p]
            if len(processes) == 1:
                match = re.match(r'(?P<pid>\d+) (?P<status>[\w+]+) +(?P<cmd>.*)', processes[0])
                if match is None:
                    print(f"Could not parse process string: {processes[0]}")
                else:
                    cmd = match['cmd'].split()[0]
                    context = basename(cmd)

    return {
            'id': context,
            'app_name': name,
            'app_path': app['NSApplicationPath']
            }


signal.signal(signal.SIGINT, sigint_handler)
print(f'{HIDE_CURSOR}')
last_active_id = None
while True:
    active_app = NSWorkspace.sharedWorkspace().activeApplication()
    context = get_context(active_app)
    if context['id'] != last_active_id:
        last_active_id = context['id']
        on_context_change(context)
    sleep(1)
