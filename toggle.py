#!/usr/bin/env python3
"""
Read a text file containing one fixed-width hexadecimal number per line
(no “0x” prefix required).  
Verify that every line has the *same* number of hex digits, collect **all**
bit positions that are set to 1 (LSB = index 0) across the whole file, and
print the sorted list of unique indices once at the end.
"""

from pathlib import Path
import argparse
import sys


def bits_set(n: int) -> list[int]:
    """Return indices of bits that are 1 in *n* (LSB = 0)."""
    idx, out = 0, []
    while n:
        if n & 1:
            out.append(idx)
        n >>= 1
        idx += 1
    return out


def collect_unique_indices(path: Path) -> None:
    expected_len: int | None = None
    all_indices: set[int] = set()

    with path.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            text = raw.strip()
            if not text:
                continue                        # skip blank lines

            # Strip optional 0x/0X prefix
            if text.lower().startswith("0x"):
                text = text[2:]

            # Ensure constant width
            if expected_len is None:
                expected_len = len(text)
            elif len(text) != expected_len:
                print(
                    f"Line {lineno}: width {len(text)} ≠ expected {expected_len}",
                    file=sys.stderr,
                )
                continue

            try:
                value = int(text, 16)
            except ValueError:
                print(f"Line {lineno}: invalid hex → {text!r}", file=sys.stderr)
                continue

            all_indices.update(bits_set(value))

    # Print consolidated result
    for idx in sorted(all_indices):
      print(idx)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Collect unique bit indices set to 1 in fixed-width "
                    "hex numbers from a file."
    )
    ap.add_argument("file", help="Path to input file")
    args = ap.parse_args()

    collect_unique_indices(Path(args.file))


if __name__ == "__main__":
    main()

