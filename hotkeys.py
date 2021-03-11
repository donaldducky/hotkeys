import re
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


def on_context_change(context):
    print(f"{CLEAR_SCREEN}{TOP_LEFT}{context['id']} ({context['app_path']}) {context['cwd']}\n")
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
    cwd = ''
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
        out = subprocess.run(cmd, capture_output=True, universal_newlines=True, check=True).stdout
        context = "🤷🏻‍♂️"
        process_lines = out.split("\n")
        # S+ or R+
        # TODO parse the process line, then check for the flag
        processes = [p for p in process_lines if "S+" in p]
        if not processes:
            processes = [p for p in process_lines if "R+" in p]

        if len(processes) == 1:
            match = re.search(r'(?P<pid>\d+)\s+(?P<status>[\w+]+)\s+(?P<cmd>.*)', processes[0])
            if match is None:
                print(f"Could not parse process string: {processes[0]}")
            else:
                if re.search(r'python hotkeys.py', match['cmd']) is not None:
                    context = 'hotkeys'
                else:
                    lsof_cmd = ["lsof", "-a", "-p", match['pid'], "-d", "cwd", "-F", "n"]
                    out = subprocess.run(lsof_cmd, capture_output=True, universal_newlines=True, check=True).stdout
                    try:
                        cwd = [c for c in out.split("\n") if c.startswith("n")][0][1:]
                    except IndexError:
                        print(f"Could not find cwd from {out}")

                    cmd = match['cmd'].split()[0]
                    context = basename(cmd)
        else:
            print(f"Found an unexpected number of processes {processes}")

    return {
            'id': context,
            'app_name': name,
            'app_path': app['NSApplicationPath'],
            'cwd': cwd
            }

def main_loop():
    print(f'{HIDE_CURSOR}')
    # TODO better handle context change
    last_active_id = None
    last_cwd = ''
    while True:
        try:
            active_app = NSWorkspace.sharedWorkspace().activeApplication()
            context = get_context(active_app)
            if context['id'] != 'hotkeys' and (context['id'] != last_active_id or context['cwd'] != last_cwd):
                last_active_id = context['id']
                last_cwd = context['cwd']
                on_context_change(context)
            sleep(1)
        except KeyboardInterrupt:
            print(f'{SHOW_CURSOR}')
            sys.exit(0)


main_loop()
