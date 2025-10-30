#!/usr/bin/env python3
"""
to_wav.py — Recursively convert all audio files under a path to WAV
(PCM 16-bit), then delete originals *only if* conversion succeeds.

Usage:
  python3 to_wav.py /path/to/root
  python3 to_wav.py . --overwrite
  python3 to_wav.py /music --keep --sample-rate 48000

Flags:
  --keep           Keep originals (do not delete after conversion)
  --overwrite      Overwrite existing .wav files if present
  --dry-run        Show what would happen, make no changes
  --sample-rate N  Resample to N Hz (omit to preserve original)
  --channels N     Force N channels (default 2)
"""

import argparse
import shutil
import subprocess
from pathlib import Path

SUPPORTED_EXTS = {
    ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma", ".wv",
    ".aif", ".aiff", ".aifc", ".mp2", ".ac3", ".mka", ".mkv", ".mp4", ".m4b"
}
# We skip .wav inputs by default.
SKIP_EXTS = {".wav"}

def have_tool(name: str) -> bool:
    return shutil.which(name) is not None

def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def get_duration_seconds(path: Path) -> float | None:
    # Returns float seconds or None if unknown
    p = run(["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             str(path)])
    if p.returncode != 0:
        return None
    try:
        return float(p.stdout.strip())
    except (ValueError, AttributeError):
        return None

def convert_to_wav(src: Path, dst: Path, sample_rate: int | None, channels: int, overwrite: bool) -> tuple[bool, str]:
    # Build ffmpeg command
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin"]
    if not overwrite:
        cmd += ["-n"]   # don't overwrite
    else:
        cmd += ["-y"]   # overwrite
    cmd += ["-i", str(src), "-vn"]  # ensure audio only

    # Force PCM 16-bit LE WAV
    cmd += ["-acodec", "pcm_s16le", "-ac", str(channels)]
    if sample_rate:
        cmd += ["-ar", str(sample_rate)]

    cmd += [str(dst)]

    p = run(cmd)
    ok = (p.returncode == 0) and dst.exists()
    return ok, p.stderr.strip()

def main():
    ap = argparse.ArgumentParser(description="Recursively convert audio to WAV and delete originals on success.")
    ap.add_argument("root", nargs="?", default=".", help="Root directory to scan")
    ap.add_argument("--keep", action="store_true", help="Keep originals (do not delete)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing .wav files")
    ap.add_argument("--dry-run", action="store_true", help="Preview actions; make no changes")
    ap.add_argument("--sample-rate", type=int, default=None, help="Resample to N Hz (e.g., 44100, 48000)")
    ap.add_argument("--channels", type=int, default=2, help="Number of output channels (default: 2)")
    args = ap.parse_args()

    # Tool checks
    for tool in ("ffmpeg", "ffprobe"):
        if not have_tool(tool):
            print(f"ERROR: '{tool}' not found in PATH. Install ffmpeg package and try again.")
            return

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: Path not found: {root}")
        return

    to_process: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        if suf in SKIP_EXTS:
            continue
        if suf in SUPPORTED_EXTS:
            to_process.append(p)

    converted = 0
    deleted = 0
    skipped = 0
    errors = 0

    print(f"Scanning: {root}")
    print(f"Found {len(to_process)} candidate audio file(s).")

    for src in to_process:
        dst = src.with_suffix(".wav")

        if dst.exists() and not args.overwrite:
            print(f"[skip] WAV exists: {dst}")
            skipped += 1
            continue

        # Safety: measure input duration if available
        in_dur = get_duration_seconds(src)

        print(f"[convert] {src} -> {dst}")
        if args.dry_run:
            converted += 1
            if not args.keep:
                deleted += 1
            continue

        ok, err = convert_to_wav(src, dst, args.sample_rate, args.channels, args.overwrite)
        if not ok:
            print(f"[error] Conversion failed: {src}\n        {err}")
            errors += 1
            continue

        # Verify output duration roughly matches input (if both known)
        out_dur = get_duration_seconds(dst)
        if in_dur is not None and out_dur is not None:
            # allow a small tolerance (1.0s) for container/rounding differences
            if abs(in_dur - out_dur) > 1.0 and out_dur > 0.0:
                print(f"[warn] Duration mismatch (in={in_dur:.2f}s, out={out_dur:.2f}s). Keeping original for safety: {src}")
                skipped += 1
                continue

        converted += 1

        if not args.keep:
            try:
                src.unlink()
                deleted += 1
                print(f"[delete] Original removed: {src}")
            except Exception as e:
                print(f"[error] Could not delete original: {src} ({e})")
                errors += 1

    print("\n=== Summary ===")
    print(f"Converted: {converted}")
    print(f"Deleted originals: {deleted}{' (dry-run)' if args.dry_run and not args.keep else ''}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")

if __name__ == "__main__":
    main()
