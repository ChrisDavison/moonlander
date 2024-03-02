#!/usr/bin/env python
from pathlib import Path
import sys
import zipfile
import shutil
import subprocess
import argparse
import re

import keys


RE_MOD = re.compile(
    r"SS_(?P<mod>LSFT|LCTL|LALT|RSFT|RCTL|RALT|LGUI|RGUI)\((?P<key>.+)\)"
)
RE_TAP = re.compile(r"SS_TAP\(X_(?P<key>[^()]+)\)")
RE_DELAY = re.compile(r"SS_DELAY\((?P<delay>[0-9]+)\)")
TARGET_DIR = Path(
    "~/code/external/qmk_firmware/keyboards/moonlander/keymaps/cdavison"
).expanduser()
MACRO_DELAY = 10


def move_source():
    SOURCE_DIR = Path("~/syncthing").expanduser()

    # grap the latest zip file
    files = SOURCE_DIR.glob("moonlander*.zip")
    files = sorted(files, key=lambda f: f.stat().st_mtime)
    source = files[-1]

    if not source.exists():
        raise FileNotFoundError(source)
    print("Extracting", source.name)
    print()

    # Extract the zip file
    with zipfile.ZipFile(source, "r") as zip_ref:
        zip_ref.extractall("/tmp/kb_temp")

    # Move all files in the source subdir to the target dir
    sourcedir = [p for p in Path("/tmp/kb_temp").glob("*") if p.is_dir()][0]
    for f in sourcedir.iterdir():
        if (TARGET_DIR / f.name).exists():
            (TARGET_DIR / f.name).unlink()
        shutil.move(f, TARGET_DIR)


def encode_macro(key, delay=10):
    parts = []
    for k in key:
        if k in keys.letters:
            parts.append(keys.letters[k])
        elif k in keys.numbers:
            parts.append(keys.numbers[k])
        elif k in keys.symbols:
            parts.append(keys.symbols[k])
        elif k in keys.punctuation:
            parts.append(keys.punctuation[k])
        elif k in keys.arrows:
            parts.append(keys.arrows[k])
        else:
            print("Unknown key:", k)
    return f" SS_DELAY({delay}) ".join(parts) + " "


def main():
    parser = argparse.ArgumentParser("Extract moonlander zip, fix macros, then compile")
    # parser.add_argument("string", type=str)
    parser.add_argument("--macro-delay", type=int, default=10)
    parser.add_argument("-n", "--skip-macros", action='store_true')
    args = parser.parse_args()

    move_source()

    keymap_c = TARGET_DIR / "keymap.c"
    content = keymap_c.read_text()

    my_macros = {
        "mac1": {"macro": r"\(\)", "left": 2, "re": None},
        "mac2": {"macro": r"::<>()", "left": 3, "re": None},
        "mac3": {"macro": r"Vec<>", "left": 1, "re": None},
        "mac4": {"macro": r"HashMap<>", "left": 1, "re": None},
        "mac5": {"macro": r"HashSet<>", "left": 1, "re": None},
    }

    for k in my_macros:
        macro_find_str = ".*".join([encode_macro(l).strip() for l in k])
        macro_fixed = macro_find_str.replace("(", ".").replace(")", ".")
        my_macros[k]["re"] = re.compile(macro_fixed)

    newlines = []
    replaced_a_macro = False
    for line in content.splitlines():
        if not args.skip_macros:
            for macro_placeholder, content in my_macros.items():
                macro_re = content["re"]
                if macro_re.search(line):
                    repl = content["macro"]
                    n_left = content["left"]
                    print(f"[REPLACED MACRO] {macro_placeholder}  ->  {repl}")
                    lefts = encode_macro(["left"] * n_left, args.macro_delay)
                    macro_encoded = encode_macro(repl, args.macro_delay) + lefts
                    line = macro_re.sub(macro_encoded, line)
                    replaced_a_macro = True
        newlines.append(RE_DELAY.sub(f"SS_DELAY({args.macro_delay})", line))

    if not args.skip_macros and not replaced_a_macro:
        print("No macros replaced")
        sys.exit(-1)
    keymap_c.write_text("\n".join(newlines))

    ret = subprocess.run(
        ["qmk", "compile", "-kb", "moonlander", "-km", "cdavison"],
        cwd=Path("~/code/external/qmk_firmware").expanduser(),
        capture_output=True
    )
    if ret.returncode != 0:
        print()
        print("=" * 80)
        print("=" * 80)
        print()
        # print(ret.stdout.decode())
        print(ret.stderr.decode())
        raise Exception("Compilation failed")
    else:
        print("  ____ ___  __  __ ____ ___ _     _____ ____  ")
        print(" / ___/ _ \\|  \\/  |  _ \\_ _| |   | ____|  _ \\ ")
        print("| |  | | | | |\\/| | |_) | || |   |  _| | | | |")
        print("| |__| |_| | |  | |  __/| || |___| |___| |_| |")
        print(" \\____\\___/|_|  |_|_|  |___|_____|_____|____/ ")
        print("                                              ")
        print("Now flash using keymapp")

    # remove_zip()


if __name__ == "__main__":
    main()
