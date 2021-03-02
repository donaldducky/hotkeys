import re
import signal
import sys
import yaml
import applescript
from time import sleep
from AppKit import NSWorkspace

CLEAR_SCREEN = '\033[2J'
TOP_LEFT = '\033[1;1H'
SHOW_CURSOR = '\033[?25h'
HIDE_CURSOR = '\033[?25l'


def sigint_handler(sig, frame):
    print('%s' % SHOW_CURSOR)
    sys.exit(0)


def on_context_change(context):
    print(f"{CLEAR_SCREEN}{TOP_LEFT}Current app → {context['app_name']} ({context['app_path']})\n")
    try:
        path = f"hotkeys/{context['id']}.yaml"
        with open(path, "r") as stream:
            y = yaml.safe_load(stream)
            hotkeys = y["hotkeys"]
            max_key_size = len(max(hotkeys.keys(), key=len))
            for k, v in hotkeys.items():
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

    return {
            'id': context,
            'app_name': name,
            'app_path': app['NSApplicationPath']
            }


signal.signal(signal.SIGINT, sigint_handler)
print('%s', HIDE_CURSOR)
last_active_id = None
while True:
    active_app = NSWorkspace.sharedWorkspace().activeApplication()
    context = get_context(active_app)
    if context['id'] != last_active_id:
        last_active_id = context['id']
        on_context_change(context)
    sleep(1)
