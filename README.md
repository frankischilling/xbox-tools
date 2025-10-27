# xbox-tools

Collection of small Python command-line utilities to help when working with Xbox RGH files and archives.

This repository currently contains three focused scripts written in Python:

- `rename.py` — clean and limit filenames for FATX-like targets (e.g. Xbox file systems).
- `unzip_1.py` — recursively extract ZIP and RAR archives in-place, flattening internal paths.
- `flatten_to_root.py` — move all files from subfolders into a single root folder.

## Requirements

- Python 3.10+ (unions and modern annotations used)
- Optional for RAR support:
  - Python package: `rarfile` (`pip install rarfile`)
  - System extraction backend (e.g. `unrar`, `unar`, or `bsdtar`) so `rarfile` can open RAR archives

Make the scripts executable if you prefer:
```bash
chmod +x rename.py unzip_1.py flatten_to_root.py
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
python3 rename.py

# or (if executable)
./rename.py
```

Example
```bash
cd /path/to/roms
python3 rename.py
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
python3 unzip_1.py [ROOT] [-p PASSWORD] [--delete]
```

Options
- ROOT (optional): path to scan (defaults to `.`).
- `-p`, `--password`: password to use for encrypted RARs (optional).
- `--delete`: remove archives after successful extraction.

Examples
```bash
# extract everything in current directory and subfolders
python3 unzip_1.py

# extract a specific folder and delete archives afterwards
python3 unzip_1.py /path/to/collection --delete

# extract and provide RAR password
python3 unzip_1.py /path/to/collection -p "secret"
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
python3 flatten_to_root.py

# or (if executable)
./flatten_to_root.py
```

Example
```bash
cd /path/to/collection
python3 flatten_to_root.py
```

Notes
- This is a destructive reorganization (files are moved). Back up or test on a copy first.

## Safety & recommendations

- Backup: All three scripts rename, move or extract files. Work on a copy or ensure you have backups before running them.
- Dry-run: The scripts do not implement a dry-run mode. If you want to preview actions, copy a small sample of your data into a temp folder and run the scripts there first.
- Version control: Running `git init` in a directory and committing before running destructive scripts can help you revert some changes (only for tracked files).
- Adjust limits: Update `MAX_FILENAME` in `rename.py` to match your target filesystem if 42 is not appropriate.
- Improve: Consider adding `--dry-run` flags or a `--yes` confirmation toggle for destructive behaviors.

## Example workflows

Prepare ROMs for an Xbox-style device:
1. Extract archives into their folders:
```bash
python3 unzip_1.py /path/to/raw_archives
```
2. Flatten nested files into a single folder (if desired):
```bash
cd /path/to/raw_archives
python3 flatten_to_root.py
```
3. Clean filenames for FATX:
```bash
python3 rename.py
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
