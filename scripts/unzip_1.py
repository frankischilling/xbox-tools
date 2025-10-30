#!/usr/bin/env python3
"""
Extract .zip, .rar, .7z, .tar, .gz, .bz2, .xz archives in place (into the same folder as each archive).
- Recurses subfolders
- Flattens internal archive paths (files land beside the archive)
- Never overwrites: adds _1, _2, ... if needed
- Optional: delete archive after success

Requires:
  sudo apt install p7zip-full p7zip-rar unrar unzip tar gzip bzip2 xz-utils
  pip install patool rarfile py7zr
"""

import argparse
import os
import re
import sys
import zipfile
import shutil
import subprocess

# Optional backends
try:
    import rarfile
except Exception:
    rarfile = None

try:
    import patoolib
    patoolib.util.PATOOLEXECUTABLES['7z'] = '7z'
    patoolib.util.PATOOLEXECUTABLES['7za'] = '7z'
    patoolib.util.PATOOLEXECUTABLES['7zr'] = '7z'
except Exception:
    patoolib = None


def is_first_rar_volume(filename: str, dirpath: str = ".") -> bool:
    """Return True if filename looks like the FIRST volume of a RAR set."""
    f = filename.lower()
    if re.search(r"\.part0*1\.rar$", f):
        base = re.sub(r"\.part0*1\.rar$", "", f)
        next_part = os.path.join(dirpath, base + ".part2.rar")
        if not os.path.exists(next_part):
            print(f"  ⚠ missing next part: {next_part}")
        return True
    if re.search(r"\.part\d+\.rar$", f):
        return False
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


def safe_copy(src, dst, chunk_size=1024 * 1024):
    """Copy data from src to dst in chunks; tolerate short reads."""
    while True:
        chunk = src.read(chunk_size)
        if not chunk:
            break
        dst.write(chunk)


def extract_zip(zip_path: str, dest_dir: str) -> int:
    n = 0
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = os.path.basename(info.filename) or "file"
            out_path = unique_path(dest_dir, name)
            ensure_parent(out_path)
            with zf.open(info) as src, open(out_path, "wb") as dst:
                safe_copy(src, dst)
            n += 1
    return n


def extract_rar(rar_path: str, dest_dir: str, password: str | None = None) -> int:
    """Extract RAR contents into dest_dir, with integrity test and unrar fallback."""
    if rarfile is None:
        raise RuntimeError("rarfile not available. Install with: pip install rarfile")
    n = 0
    try:
        with rarfile.RarFile(rar_path) as rf:
            try:
                rf.testrar()
            except rarfile.Error as e:
                print(f"  ⚠ integrity test failed: {e}")

            for info in rf.infolist():
                if info.isdir():
                    continue
                name = os.path.basename(info.filename) or "file"
                out_path = unique_path(dest_dir, name)
                ensure_parent(out_path)
                with rf.open(info, pwd=password) as src, open(out_path, "wb") as dst:
                    safe_copy(src, dst)
                n += 1
    except Exception as e:
        print(f"  ⚠ rarfile failed, trying system unrar: {e}")
        subprocess.run(["unrar", "x", "-o+", rar_path, dest_dir], check=False)
    return n


def extract_any(archive_path: str, dest_dir: str):
    """Fallback: use py7zr or patool for .7z, .tar, .gz, .xz, etc."""
    ext = archive_path.lower()
    if ext.endswith(".7z"):
        try:
            import py7zr
            with py7zr.SevenZipFile(archive_path, mode="r") as z:
                z.extractall(path=dest_dir)
            return
        except Exception as e:
            print(f"  py7zr failed: {e}")
    if patoolib is None:
        raise RuntimeError("patool not installed. Run: pip install patool py7zr rarfile")
    patoolib.extract_archive(archive_path, outdir=dest_dir, verbosity=-1)


def main():
    ap = argparse.ArgumentParser(description="Extract archives in place (recursive, flatten paths).")
    ap.add_argument("root", nargs="?", default=".", help="Root folder to scan (default: current dir)")
    ap.add_argument("-p", "--password", default=None, help="Password for encrypted RARs (optional)")
    ap.add_argument("--delete", action="store_true", help="Delete archives after successful extraction")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    total_archives = total_files = errors = 0

    for dirpath, _, files in os.walk(root):
        for fname in sorted(files):
            low = fname.lower()
            full = os.path.join(dirpath, fname)

            try:
                if low.endswith(".zip"):
                    total_archives += 1
                    print(f"\nZIP: {full}")
                    extracted = extract_zip(full, dirpath)
                    print(f"  -> extracted {extracted} file(s)")
                    total_files += extracted
                    if args.delete:
                        os.remove(full)
                        print("  (deleted archive)")

                elif (low.endswith(".rar") or re.search(r"\.r\d{2}$", low)) and rarfile is not None:
                    if not is_first_rar_volume(fname, dirpath):
                        continue
                    total_archives += 1
                    print(f"\nRAR: {full}")
                    extracted = extract_rar(full, dirpath, password=args.password)
                    print(f"  -> extracted {extracted} file(s)")
                    total_files += extracted
                    if args.delete:
                        os.remove(full)
                        print("  (deleted archive)")

                elif re.search(r"\.(7z|tar|gz|bz2|xz)$", low):
                    total_archives += 1
                    print(f"\nOTHER: {full}")
                    extract_any(full, dirpath)
                    total_files += 1
                    if args.delete:
                        os.remove(full)
                        print("  (deleted archive)")

            except Exception as e:
                errors += 1
                print(f"  ERROR: {e}")

    print(f"\nSummary: archives processed={total_archives}, files extracted≈{total_files}, errors={errors}")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
