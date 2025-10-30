#!/usr/bin/env python3
import os
import re

# ---- SETTINGS ----
MAX_FILENAME = 42           # FATX filename limit (includes extension)
BASE_DIR = os.getcwd()      # work in the folder you run the script from

# Remove ANY [ ... ] tag (GoodTools-style)
BRACKETS = re.compile(r"\s*\[[^\]]*\]")

# Remove ( ... ) when it contains any of these tokens (region/lang/rev/etc.)
PARENS_WITH_TAGS = re.compile(
    r"""
    \s*\(
        [^)]*
        (?:USA|Japan|World|Europe|PAL|NTSC|
           JPN|U|E|
           Eng(?:lish)?|En|Fr|De|Es|It|Nl|Pt|Sv|No|Ja|
           Rev(?:\s*\d+|[A-Z])?|
           Proto|Beta|Unl|Arcade|Demo|Sample|Alt\s*\d+|
           v\d+(?:\.\d+)?|
           (?:[A-Z]{2})(?:,[A-Z]{2})+   # En,Fr,De style lists
        )
        [^)]*
    \)
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Characters allowed for safety on FATX: letters, digits, space, hyphen, underscore, dot
SAFE_CHARS = re.compile(r"[^A-Za-z0-9 ._-]+")

def tidy_base(name: str) -> str:
    # Drop bracket & taggy parentheses
    name = BRACKETS.sub("", name)
    name = PARENS_WITH_TAGS.sub("", name)
    # Remove now-empty () or []
    name = re.sub(r"\(\s*\)|\[\s*\]", "", name)
    # Replace forbidden chars with space
    name = SAFE_CHARS.sub(" ", name)
    # Normalize punctuation/spacing
    name = re.sub(r"[,/]+", " ", name)
    name = re.sub(r"[-_]{2,}", " ", name)
    name = re.sub(r"\s{2,}", " ", name)
    # Trim edges
    name = name.strip(" .-_")
    # Fallback if empty
    return name or "ROM"

def enforce_length(base: str, ext: str) -> str:
    # Ensure len(base + ext) <= MAX_FILENAME
    allowed = max(1, MAX_FILENAME - len(ext))
    if len(base) <= allowed:
        return base
    # Prefer cutting at a word boundary near the limit
    trimmed = base[:allowed]
    if " " in trimmed:
        trimmed = trimmed[:trimmed.rfind(" ")].rstrip(" .-_")
        if not trimmed:
            trimmed = base[:allowed].rstrip(" .-_")
    else:
        trimmed = trimmed.rstrip(" .-_")
    return trimmed or "ROM"

def unique_path(dirpath: str, base: str, ext: str) -> str:
    # Avoid collisions; keep within the MAX_FILENAME limit
    candidate = os.path.join(dirpath, base + ext)
    if not os.path.exists(candidate):
        return candidate
    i = 1
    while True:
        suffix = f"_{i}"
        allowed = max(1, MAX_FILENAME - len(ext) - len(suffix))
        b2 = (base[:allowed]).rstrip(" .-_") or "ROM"
        candidate = os.path.join(dirpath, f"{b2}{suffix}{ext}")
        if not os.path.exists(candidate):
            return candidate
        i += 1

count = 0
for root, _, files in os.walk(BASE_DIR):
    for fname in files:
        base, ext = os.path.splitext(fname)
        new_base = tidy_base(base)
        new_base = enforce_length(new_base, ext)
        # Final tidy in case trimming exposed odd endings
        new_base = new_base.strip(" .-_") or "ROM"
        old_path = os.path.join(root, fname)
        new_path = unique_path(root, new_base, ext)
        if old_path != new_path:
            try:
                os.rename(old_path, new_path)
                print(f"Renamed: {fname} -> {os.path.basename(new_path)}")
                count += 1
            except Exception as e:
                print(f"Error renaming {fname}: {e}")

print(f"\n✅ Done! {count} filenames cleaned and limited to ≤ {MAX_FILENAME} chars.")
