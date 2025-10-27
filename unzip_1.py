#!/usr/bin/env python3
"""
Extract .zip and .rar archives in place (into the same folder as each archive).
- Recurses subfolders
- For multi-part RAR sets, extracts only from the first volume
- Flattens internal archive paths (files land beside the archive)
- Never overwrites: adds _1, _2, ... if needed
- Optional: delete archive after success

Usage:
  python3 extract_in_place.py /path/to/roms           # extract everything
  python3 extract_in_place.py /path/to/roms --delete  # delete archives after
"""

import argparse
import os
import re
import sys
import zipfile

try:
    import rarfile  # pip install rarfile  (requires system unrar/unar/bsdtar)
except Exception:
    rarfile = None


def is_first_rar_volume(filename: str) -> bool:
    """Return True if filename looks like the FIRST volume of a RAR set."""
    f = filename.lower()
    # .part01.rar / .part1.rar is first
    if re.search(r"\.part0*1\.rar$", f):
        return True
    # .partXX.rar where XX > 1 is not first
    if re.search(r"\.part\d+\.rar$", f):
        return False
    # old style: .rar is first, .r00/.r01... are subsequent
    if re.search(r"\.r\d{2}$", f):
        return False
    return f.endswith(".rar")


def unique_path(dirpath: str, filename: str) -> str:
    """Return a path that doesn't exist by appending _N if needed."""
    path = os.path.join(dirpath, filename)
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(filename)
    i = 1
    while True:
        path = os.path.join(dirpath, f"{base}_{i}{ext}")
        if not os.path.exists(path):
            return path
        i += 1


def ensure_parent(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def extract_zip(zip_path: str, dest_dir: str) -> int:
    """Extract ZIP contents into dest_dir, flattening internal paths."""
    n = 0
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = os.path.basename(info.filename) or "file"
            out_path = unique_path(dest_dir, name)
            ensure_parent(out_path)
            with zf.open(info) as src, open(out_path, "wb") as dst:
                dst.write(src.read())
            n += 1
    return n


def extract_rar(rar_path: str, dest_dir: str, password: str | None = None) -> int:
    """Extract RAR contents into dest_dir, flattening internal paths."""
    if rarfile is None:
        raise RuntimeError("rarfile module not available. Install with: pip install rarfile")
    n = 0
    with rarfile.RarFile(rar_path) as rf:
        for info in rf.infolist():
            if info.isdir():
                continue
            name = os.path.basename(info.filename) or "file"
            out_path = unique_path(dest_dir, name)
            ensure_parent(out_path)
            with rf.open(info, pwd=password) as src, open(out_path, "wb") as dst:
                # Read/write in chunks to support big files
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="Extract .zip/.rar in place (recursive, flatten paths).")
    ap.add_argument("root", nargs="?", default=".", help="Root folder to scan (default: current dir)")
    ap.add_argument("-p", "--password", default=None, help="Password for encrypted RARs (optional)")
    ap.add_argument("--delete", action="store_true", help="Delete archives after successful extraction")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    total_archives = total_files = errors = 0

    # Small helper: print warning if rar backend missing
    if rarfile is None:
        print("Note: RAR support disabled (install `pip install rarfile` and `unrar`).", file=sys.stderr)

    for dirpath, _, files in os.walk(root):
        for fname in sorted(files):
            low = fname.lower()
            full = os.path.join(dirpath, fname)

            try:
                if low.endswith(".zip"):
                    total_archives += 1
                    print(f"\nZIP: {full}")
                    extracted = extract_zip(full, dirpath)
                    print(f"  -> extracted {extracted} file(s) into {dirpath}")
                    total_files += extracted
                    if args.delete:
                        os.remove(full)
                        print("  (deleted archive)")
                elif (low.endswith(".rar") or re.search(r"\.r\d{2}$", low)) and rarfile is not None:
                    # Skip non-first volumes
                    if not is_first_rar_volume(fname):
                        continue
                    total_archives += 1
                    print(f"\nRAR: {full}")
                    extracted = extract_rar(full, dirpath, password=args.password)
                    print(f"  -> extracted {extracted} file(s) into {dirpath}")
                    total_files += extracted
                    if args.delete:
                        try:
                            os.remove(full)
                            print("  (deleted first volume)")
                        except Exception as e:
                            print(f"  (could not delete first volume: {e})")
                else:
                    continue
            except Exception as e:
                errors += 1
                print(f"  ERROR: {e}")

    print(f"\nSummary: archives processed={total_archives}, files extracted={total_files}, errors={errors}")


if __name__ == "__main__":
    main()
