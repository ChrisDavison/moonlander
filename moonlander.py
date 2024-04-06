#!/usr/bin/env python
from pathlib import Path
import sys
import zipfile
import shutil
import subprocess
import re
import click

import keys
from macros import my_macros


RE_DELAY = re.compile(r"SS_DELAY\((?P<delay>[0-9]+)\)")
QMK_DIR = Path("~/code/EXTERNAL/qmk_firmware").expanduser()
TARGET_DIR = (QMK_DIR / "keyboards/moonlander/keymaps/cdavison")


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


@click.command(help="Extract moonlander zip, fix macros, then compile")
@click.option("--macro-delay", type=int, default=10)
@click.option("-n", "--skip-macros", is_flag=True)
def main(macro_delay, skip_macros):
    move_source()

    keymap_c = TARGET_DIR / "keymap.c"
    content = keymap_c.read_text()

    for k in my_macros:
        macro_find_str = ".*".join([encode_macro(l).strip() for l in k])
        macro_fixed = macro_find_str.replace("(", ".").replace(")", ".")
        my_macros[k]["re"] = re.compile(macro_fixed)

    newlines = []
    replaced_a_macro = False
    for line in content.splitlines():
        if not skip_macros:
            for macro_placeholder, content in my_macros.items():
                macro_re = content["re"]
                if macro_re.search(line):
                    repl = content["macro"]
                    n_left = content["left"]
                    print(f"[REPLACED MACRO] {macro_placeholder}  ->  {repl}")
                    lefts = encode_macro(["left"] * n_left, macro_delay)
                    macro_encoded = encode_macro(repl, macro_delay) + lefts
                    line = macro_re.sub(macro_encoded, line)
                    replaced_a_macro = True
        newlines.append(RE_DELAY.sub(f"SS_DELAY({macro_delay})", line))

    if not skip_macros and not replaced_a_macro:
        print("No macros replaced")
    keymap_c.write_text("\n".join(newlines))

    ret = subprocess.run(
        ["qmk", "compile", "-kb", "moonlander", "-km", "cdavison"],
        cwd=QMK_DIR,
        capture_output=True,
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
        # print(ret.stdout.decode())
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
