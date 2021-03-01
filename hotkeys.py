import signal
import sys
import yaml
from time import sleep
from AppKit import NSWorkspace

CLEAR_SCREEN = '\033[2J'
TOP_LEFT = '\033[1;1H'
SHOW_CURSOR = '\033[?25h'
HIDE_CURSOR = '\033[?25l'


def sigint_handler(sig, frame):
    print('%s' % SHOW_CURSOR)
    sys.exit(0)


def on_app_change(active_app):
    name = active_app['NSApplicationName']
    app_path = active_app['NSApplicationPath']
    print(f"{CLEAR_SCREEN}{TOP_LEFT}Current app → {name} ({app_path})\n")
    try:
        path = f"hotkeys/{name}.yaml"
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


signal.signal(signal.SIGINT, sigint_handler)
print('%s', HIDE_CURSOR)
last_active_name = None
while True:
    active_app = NSWorkspace.sharedWorkspace().activeApplication()
    if active_app['NSApplicationName'] != last_active_name:
        last_active_name = active_app['NSApplicationName']
        on_app_change(active_app)
    sleep(1)
