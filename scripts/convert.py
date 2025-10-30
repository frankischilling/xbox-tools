#!/usr/bin/env python3
"""
to_wav_xboxsafe.py — Recursively convert all audio to Xbox 360–compatible WAV
(PCM 16-bit LE, mono, 44100 Hz, no metadata). If the source is already .wav,
it is normalized IN-PLACE via a temporary .wav file to avoid ffmpeg "same as input" errors.

Usage:
  python3 to_wav_xboxsafe.py /path --overwrite
  python3 to_wav_xboxsafe.py /path --dry-run
  python3 to_wav_xboxsafe.py . --keep
"""

import argparse
import os
import shutil
import subprocess
from pathlib import Path

SUPPORTED_EXTS = {
    ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma", ".wv",
    ".aif", ".aiff", ".aifc", ".mp2", ".ac3", ".mka", ".mkv", ".mp4", ".m4b", ".wav"
}

def have_tool(name: str) -> bool:
    return shutil.which(name) is not None

def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def ffmpeg_xboxsafe_cmd(src: Path, dst: Path, overwrite: bool) -> list[str]:
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-i", str(src),
        "-acodec", "pcm_s16le",  # 16-bit PCM LE
        "-ac", "1",              # mono
        "-ar", "44100",          # 44.1 kHz
        "-map_metadata", "-1",   # strip all metadata
        "-f", "wav",             # force WAV muxer (works for temp files)
        "-y" if overwrite else "-n",
        str(dst),
    ]

def convert_other_to_wav(src: Path, dst: Path, overwrite: bool) -> tuple[bool, str]:
    p = run(ffmpeg_xboxsafe_cmd(src, dst, overwrite))
    ok = (p.returncode == 0) and dst.exists()
    return ok, p.stderr.strip()

def normalize_wav_inplace(src: Path) -> tuple[bool, str]:
    # Write to a .wav temp, then atomically replace the original
    tmp = src.with_name(src.name + ".x360tmp.wav")
    try:
        if tmp.exists():
            tmp.unlink()
        p = run(ffmpeg_xboxsafe_cmd(src, tmp, True))  # allow overwrite of tmp
        if p.returncode != 0 or not tmp.exists():
            if tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass
            return False, p.stderr.strip()
        os.replace(tmp, src)  # atomic replace
        return True, ""
    except Exception as e:
        try:
            tmp.unlink()
        except Exception:
            pass
        return False, str(e)

def main():
    ap = argparse.ArgumentParser(description="Convert audio to Xbox-safe WAV (16-bit, mono, 44.1 kHz, no metadata).")
    ap.add_argument("root", nargs="?", default=".", help="Root directory to scan")
    ap.add_argument("--keep", action="store_true", help="Keep originals (for non-wav sources)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite/normalize existing .wav files in place")
    ap.add_argument("--dry-run", action="store_true", help="Preview actions; make no changes")
    args = ap.parse_args()

    if not have_tool("ffmpeg"):
        print("ERROR: 'ffmpeg' not found in PATH. Install ffmpeg.")
        return

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: Path not found: {root}")
        return

    to_process: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            to_process.append(p)

    print(f"Scanning: {root}")
    print(f"Found {len(to_process)} audio file(s).")

    converted = deleted = skipped = errors = 0

    for src in to_process:
        ext = src.suffix.lower()

        if ext == ".wav":
            if not args.overwrite:
                print(f"[skip] {src} exists (use --overwrite to normalize in place)")
                skipped += 1
                continue

            print(f"[normalize] {src} (mono/44.1k/16-bit/no-metadata)")
            if args.dry_run:
                converted += 1
                continue

            ok, err = normalize_wav_inplace(src)
            if not ok:
                print(f"[error] {src}: {err}")
                errors += 1
            else:
                converted += 1
            continue

        # Non-WAV → convert to WAV (Xbox-safe)
        dst = src.with_suffix(".wav")
        if dst.exists() and not args.overwrite:
            print(f"[skip] {dst} exists (use --overwrite to replace)")
            skipped += 1
            continue

        print(f"[convert] {src} → {dst}")
        if args.dry_run:
            converted += 1
            if not args.keep:
                deleted += 1
            continue

        ok, err = convert_other_to_wav(src, dst, True)  # allow overwrite for the target
        if not ok:
            print(f"[error] {src}: {err}")
            errors += 1
            continue

        converted += 1
        if not args.keep:
            try:
                src.unlink()
                deleted += 1
                print(f"[delete] {src}")
            except Exception as e:
                print(f"[error] Couldn’t delete {src}: {e}")
                errors += 1

    print("\n=== Summary ===")
    print(f"Converted/normalized: {converted}")
    print(f"Deleted originals:    {deleted}")
    print(f"Skipped:              {skipped}")
    print(f"Errors:               {errors}")

if __name__ == "__main__":
    main()
