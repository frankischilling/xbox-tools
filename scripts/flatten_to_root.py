#!/usr/bin/env python3
"""
Move all files from subfolders into the root directory recursively.
- Skips venv/ and hidden folders
- Adds _1, _2, ... if duplicate names exist
- Prints a summary at the end
"""

import os
import shutil

def unique_path(dest_dir, filename):
    """Return a unique path by appending _1, _2, etc. if needed."""
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(dest_dir, filename)
    i = 1
    while os.path.exists(candidate):
        candidate = os.path.join(dest_dir, f"{base}_{i}{ext}")
        i += 1
    return candidate

def flatten_to_root(root):
    total = 0
    root = os.path.abspath(root)
    script_name = os.path.basename(__file__)

    for dirpath, _, files in os.walk(root):
        # Skip root dir and venv
        if dirpath == root or "venv" in dirpath:
            continue
        for file in files:
            if file.startswith(".") or file == script_name:
                continue
            src = os.path.join(dirpath, file)
            dest = unique_path(root, file)
            try:
                shutil.move(src, dest)
                print(f"Moved: {src} → {dest}")
                total += 1
            except Exception as e:
                print(f"Error moving {src}: {e}")

    print(f"\n✅ Done! {total} files moved to {root}")

if __name__ == "__main__":
    flatten_to_root(".")
