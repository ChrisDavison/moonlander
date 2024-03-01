#!/usr/bin/env python
from pathlib import Path
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
TARGET_DIR = Path("~/code/external/qmk_firmware/keyboards/moonlander/keymaps/cdavison").expanduser()
MACRO_DELAY = 10


def move_source():
    SOURCE_DIR = Path("~/syncthing").expanduser()

    # grap the latest zip file
    files = SOURCE_DIR.glob("moonlander*.zip")
    files = sorted(files, key=lambda f: f.stat().st_mtime)
    source = files[-1]

    if not source.exists():
        raise FileNotFoundError(source)
    print("Extracting", source, "to", TARGET_DIR)

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Extract moonlander zip, fix macros, then compile")
    # parser.add_argument("string", type=str)
    parser.add_argument("--macro-delay", type=int, default=10)
    args = parser.parse_args()

    # move_source()

    keymap_c = TARGET_DIR / "keymap.c"
    content = keymap_c.read_text()

    my_macros = [
        ("mac1", [r'\(\)', 2]),
        ("mac2", [r'::<>()', 3]),
        ("mac3", [r'Vec<>', 1]),
        ("mac4", [r'HashMap<>', 1]),
        ("mac5", [r'HashSet<>', 1]),
    ]

    # replace macros
    for (to_find, (repl, n_left)) in my_macros:
        lefts = encode_macro(["left"] * n_left, args.macro_delay)
        macro_encoded = encode_macro(repl, args.macro_delay) + lefts

        macro_find_str = ".*".join([encode_macro(l).strip() for l in to_find]) 
        RE_MACRO = re.compile(macro_find_str.replace('(', r'\(').replace(')', r'\)'))
        print("FIND", macro_find_str)
        content = RE_MACRO.sub(macro_encoded, content)

    # shorten the delay
    # content = RE_DELAY.sub(f"SS_DELAY({args.macro_delay})", content)

    print(content)

    keymap_c.write_text(content)

    # # subprocess.run(["qmk", "compile", "-kb", "moonlander", "-km", "cdavison"])
