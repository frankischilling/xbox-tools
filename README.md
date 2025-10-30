# xbox-tools

Collection of small Python command-line utilities to help when working with Xbox RGH files and archives.

This repository currently contains three focused scripts written in Python:

- `scripts/rename.py` — clean and limit filenames for FATX-like targets (e.g. Xbox file systems).
- `scripts/unzip_1.py` — recursively extract ZIP and RAR archives in-place, flattening internal paths.
- `scripts/flatten_to_root.py` — move all files from subfolders into a single root folder.
- `scripts/convert.py` — recursively convert various audio files to Xbox-compatible 16-bit PCM WAV format.

## Requirements

- Python 3.10+ (unions and modern annotations used)
- Optional for RAR support:
  - Python package: `rarfile` (`pip install rarfile`)
  - System extraction backend (e.g. `unrar`, `unar`, or `bsdtar`) so `rarfile` can open RAR archives

Make the scripts executable if you prefer:
```bash
chmod +x scripts/rename.py scripts/unzip_1.py scripts/flatten_to_root.py scripts/convert.py
```

## Installation

Clone the repo:

```bash
git clone https://github.com/frankischilling/xbox-tools.git
cd xbox-tools
```

Install optional RAR support (if you need it):

```bash
python3 -m pip install rarfile
# ensure `unrar` or `unar` is available on your system
```

## Scripts

Each script is a single-file utility. They operate on the current working directory by default (unless the script accepts a root path argument).

---

### rename.py

Purpose
- Clean filenames and enforce a maximum filename length suitable for FATX-like targets (default MAX_FILENAME = 42).
- Useful when preparing ROMs or files for Xbox file systems that have filename length/character restrictions.

Behavior
- Recursively walks the working directory.
- Removes GoodTools-style bracket tags, removes parentheses that contain region/lang/revision tokens (e.g., (USA), (Japan), (Rev A)), replaces unsafe characters, normalizes spacing and punctuation.
- Ensures filename length (base + extension) is <= MAX_FILENAME; trims at word boundaries where possible.
- Avoids collisions by appending `_1`, `_2`, ... while respecting the length limit.

Config
- Edit `MAX_FILENAME` in the script if you need a different filename length limit.
- Script uses `BASE_DIR = os.getcwd()` — run it from the folder you want processed.

Usage
```bash
# run from the directory you want to process
python3 scripts/rename.py

# or (if executable)
./scripts/rename.py
```

Example
```bash
cd /path/to/roms
python3 scripts/rename.py
```

Notes
- The script performs in-place renames. Backup important data before running.
- The script prints each rename and a final summary with the count of changes.

---

### unzip_1.py

Purpose
- Recursively locate and extract `.zip` and `.rar` archives into the folder containing each archive.
- Flatten internal archive paths so files land beside the archive instead of nested subfolders.
- Avoid overwriting: the script appends `_1`, `_2`, ... when a filename collision would occur.
- Optionally delete archives after successful extraction.

Behavior and features
- Walks the given root (default: current directory).
- For RAR archives, only extracts from the first volume (detects `.part01.rar`, `.rar`, and `.r00`-style sets).
- Skips extraction of subsequent rar volumes.
- Prints per-archive progress and a final summary (archives processed, files extracted, errors).

Usage
```bash
python3 scripts/unzip_1.py [ROOT] [-p PASSWORD] [--delete]
```

Options
- ROOT (optional): path to scan (defaults to `.`).
- `-p`, `--password`: password to use for encrypted RARs (optional).
- `--delete`: remove archives after successful extraction.

Examples
```bash
# extract everything in current directory and subfolders
python3 scripts/unzip_1.py

# extract a specific folder and delete archives afterwards
python3 scripts/unzip_1.py /path/to/collection --delete

# extract and provide RAR password
python3 scripts/unzip_1.py /path/to/collection -p "secret"
```

Notes
- If `rarfile` is not installed or the system RAR backend is missing, the script will extract ZIPs only and print a notice.
- The docstring in the file references `extract_in_place.py`, but the repository file is named `unzip_1.py`. Use the displayed filename when invoking.

---

### flatten_to_root.py

Purpose
- Move all non-hidden files from subfolders into the root directory (the directory you run the script in), consolidating scattered files into one folder.
- Skips `venv` paths and hidden files/folders.
- Avoids overwriting by appending `_1`, `_2`, ... for duplicate filenames.

Behavior
- Recursively walks the root directory.
- Skips the root itself and any path containing `venv`.
- Skips hidden files (names starting with `.`) and the script file itself.
- Moves files (shutil.move) — this changes filesystem layout.

Usage
```bash
# run in the folder you want to flatten
python3 scripts/flatten_to_root.py

# or (if executable)
./scripts/flatten_to_root.py
```

Example
```bash
cd /path/to/collection
python3 scripts/flatten_to_root.py
```

Notes
- This is a destructive reorganization (files are moved). Back up or test on a copy first.

---

### convert.py

Purpose
- Recursively convert audio files (e.g. MP3, FLAC, AAC, M4A, OGG, WMA, and more) to 16-bit PCM WAV format, compatible with Xbox tools and devices.
- Optionally delete the original file only after successful conversion and matching duration.
- Intended for batch-prepping audio assets for Xbox modding and homebrew.

Features
- Converts a wide range of common formats to `.wav` using `ffmpeg` and `ffprobe` (`.wav` inputs are skipped).
- Option to keep original files (`--keep`), preview without making changes (`--dry-run`), or overwrite existing `.wav` files (`--overwrite`).
- Supports custom sample rate (`--sample-rate N`) and number of channels (`--channels N`, default 2).
- Compares in/out durations (if available) for safety before deleting the original.
- Prints a summary (converted, skipped, deleted, errors).

Requirements
- Requires `ffmpeg` and `ffprobe` in your PATH.

Usage
```bash
python3 scripts/convert.py /path/to/audio [--keep] [--dry-run] [--overwrite] [--sample-rate N] [--channels N]
```

Examples
```bash
# Convert all supported audio files recursively inside ./music to WAV, delete originals if successful
python3 scripts/convert.py ./music

# Convert, but keep original files
python3 scripts/convert.py ./music --keep

# Resample to 48000 Hz and force stereo output
python3 scripts/convert.py ./music --sample-rate 48000 --channels 2

# Only preview what would be done
python3 scripts/convert.py ./music --dry-run
```

Notes
- Only originals with successful and duration-matching conversions are deleted (unless --keep is used).
- Backup your data before bulk converting/moving audio files.
- This script modifies files in-place. Use --dry-run to preview actions safely.
- Useful for preparing soundtrack or audio sets for emulators, custom dashboards, or homebrew running on Xbox hardware.

## Safety & recommendations

- Backup: All three scripts rename, move or extract files. Work on a copy or ensure you have backups before running them.
- Dry-run: The scripts do not implement a dry-run mode. If you want to preview actions, copy a small sample of your data into a temp folder and run the scripts there first.
- Version control: Running `git init` in a directory and committing before running destructive scripts can help you revert some changes (only for tracked files).
- Adjust limits: Update `MAX_FILENAME` in `rename.py` to match your target filesystem if 42 is not appropriate.
- Improve: Consider adding `--dry-run` flags or a `--yes` confirmation toggle for destructive behaviors.

## Example workflows

Prepare ROMs or audio for an Xbox-style device:
1. Extract archives into their folders:
```bash
python3 scripts/unzip_1.py /path/to/raw_archives
```
2. Flatten nested files into a single folder (if desired):
```bash
cd /path/to/raw_archives
python3 scripts/flatten_to_root.py
```
3. Convert audio files to WAV format for Xbox:
```bash
python3 scripts/convert.py /path/to/your/audio
```
4. Clean filenames for FATX:
```bash
python3 scripts/rename.py
```

## Development & contributions

- These are single-file utilities; keep changes small and focused.
- Good enhancements: add a `--dry-run` flag, add CLI options to `flatten_to_root.py` to accept a root path, add tests, add logging levels.
- To contribute: fork the repo, propose changes in a branch, open a PR. Use issues for discussion.

## License

This repository includes a LICENSE file: GNU Affero General Public License v3 (AGPL-3.0). See LICENSE for full terms.

## Contact

For questions, feature requests or bug reports, open an issue or a pull request on the repository:
https://github.com/frankischilling/xbox-tools
