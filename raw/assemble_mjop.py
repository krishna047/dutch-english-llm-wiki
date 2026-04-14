#!/usr/bin/env python3
"""
Assembles the corrected MJOP markdown by replacing ### Tables sections
with OCR-extracted table content for specified pages.
"""

import re
import os

INPUT_FILE = "/Users/senn1/Documents/vve/raw/783-punt-7c-mjop.md"
OUTPUT_FILE = "/Users/senn1/Documents/vve/raw/783-punt-7c-mjop-corrected.md"
OCR_DIR = "/Users/senn1/Documents/vve/raw/ocr-tables"

PAGES_TO_REPLACE = [
    16,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    30,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
]


def load_ocr_table(page_num):
    path = os.path.join(OCR_DIR, f"page-{page_num}.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().rstrip("\n")


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    total_lines = len(lines)

    # Build a map: page_num -> line index of "<!-- Page N -->"
    page_line = {}
    for i, line in enumerate(lines):
        m = re.match(r"<!-- Page (\d+) -->", line.strip())
        if m:
            page_line[int(m.group(1))] = i

    # For each page we want to replace, find the ### Tables line and the
    # closing --- (end of that page section), then replace.
    # We work on a mutable list of lines.
    result_lines = lines[:]

    # We need to process pages in REVERSE order so that line number shifts
    # from earlier replacements don't affect later ones.
    for page_num in sorted(PAGES_TO_REPLACE, reverse=True):
        if page_num not in page_line:
            print(f"WARNING: <!-- Page {page_num} --> not found, skipping.")
            continue

        start_search = page_line[page_num]

        # Find ### Tables line after the page marker
        tables_line_idx = None
        for i in range(start_search, total_lines):
            if result_lines[i].strip() == "### Tables":
                tables_line_idx = i
                break
            # Stop if we hit the next page marker
            if i > start_search and re.match(
                r"<!-- Page \d+ -->", result_lines[i].strip()
            ):
                break

        if tables_line_idx is None:
            print(f"WARNING: ### Tables not found for page {page_num}, skipping.")
            continue

        # Find the closing --- after ### Tables
        end_line_idx = None
        for i in range(tables_line_idx + 1, total_lines):
            if result_lines[i].strip() == "---":
                end_line_idx = i
                break
            # Safety: stop at next page marker
            if re.match(r"<!-- Page \d+ -->", result_lines[i].strip()):
                # The --- wasn't found before next page — take the line before
                end_line_idx = i - 1
                break

        if end_line_idx is None:
            # End of file
            end_line_idx = total_lines - 1

        # Load the OCR replacement table
        try:
            ocr_content = load_ocr_table(page_num)
        except FileNotFoundError:
            print(f"WARNING: OCR file for page {page_num} not found, skipping.")
            continue

        # Replace from ### Tables line up to (but NOT including) the --- line
        # New content: "### Tables", blank line, ocr table, blank line
        replacement = ["### Tables", "", ocr_content, ""]

        result_lines[tables_line_idx:end_line_idx] = replacement

        # Update total_lines after replacement
        total_lines = len(result_lines)

        # Rebuild page_line map (we're going reverse, so we only need to update
        # pages already processed - but since we go reverse this isn't needed)
        print(f"  Page {page_num}: replaced lines {tables_line_idx}–{end_line_idx - 1}")

    output = "\n".join(result_lines)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\nDone. Written to: {OUTPUT_FILE}")
    print(f"Original: {len(lines)} lines")
    print(f"Result:   {len(result_lines)} lines")


if __name__ == "__main__":
    main()
