#!/usr/bin/env python3
"""
PDF Fake Duplex Interleaver

Takes a single-sided scan where the first half contains one side of pages
(e.g., fronts) and the second half contains the other side (e.g., backs),
possibly in reverse order. Produces a correctly interleaved PDF.

Requires: pypdf (pip install pypdf)
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional, Tuple, Union

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf._page import PageObject  # type: ignore
except Exception as e:  # pragma: no cover - import-time guidance
    print(
        "Error: Missing dependency 'pypdf'.\n"
        "Install it with: pip install pypdf",
        file=sys.stderr,
    )
    raise


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Interleave a scan where the first half are one side of pages and the "
            "second half are the other side (possibly reversed)."
        )
    )
    parser.add_argument(
        "input",
        help="Input PDF file (single-sided scan: first half one side, second half other)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output PDF path (default: <input>.interleaved.pdf)",
    )
    parser.add_argument(
        "-s",
        "--split",
        type=int,
        default=None,
        help=(
            "Index (1-based) where second half starts. Default: half of pages. "
            "Use to handle odd pages or trailing blanks."
        ),
    )
    parser.add_argument(
        "-r",
        "--reverse-second",
        action="store_true",
        help=(
            "Reverse the second half before interleaving (typical when flipping the stack)."
        ),
    )
    parser.add_argument(
        "--no-reverse-second",
        action="store_true",
        help="Force not reversing the second half (explicit).",
    )
    parser.add_argument(
        "--pad-blank",
        action="store_true",
        help=(
            "Pad the shorter half with blank pages to align pairs (uses first page size)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write output; print the page mapping instead.",
    )
    return parser.parse_args(argv)


def determine_output_path(input_path: str, output_arg: Optional[str]) -> str:
    if output_arg:
        return output_arg
    base, ext = os.path.splitext(input_path)
    return f"{base}.interleaved.pdf"


def split_halves(reader: PdfReader, split_at: Optional[int]) -> Tuple[List[PageObject], List[PageObject]]:
    total = len(reader.pages)
    if total == 0:
        raise ValueError("Input PDF has no pages")

    if split_at is None:
        split_idx = total // 2
    else:
        if split_at < 1:
            raise ValueError("--split must be >= 1 (1-based index)")
        # convert 1-based to 0-based index for slicing; cap to total
        split_idx = max(0, min(total, split_at - 1))

    first = [reader.pages[i] for i in range(0, split_idx)]
    second = [reader.pages[i] for i in range(split_idx, total)]
    return first, second


def interleave_pages(
    first: List[PageObject],
    second: List[PageObject],
    reverse_second: bool,
    pad_blank: bool,
) -> List[Union[PageObject, None]]:
    # Optionally reverse second half (typical scenario)
    if reverse_second:
        second = list(reversed(second))

    # Optionally pad the shorter half with blanks (represented as None)
    if pad_blank and len(first) != len(second):
        diff = abs(len(first) - len(second))
        if len(first) < len(second):
            first = first + [None] * diff  # type: ignore
        else:
            second = second + [None] * diff  # type: ignore

    interleaved: List[Union[PageObject, None]] = []
    max_len = max(len(first), len(second))
    for i in range(max_len):
        if i < len(first):
            interleaved.append(first[i])
        if i < len(second):
            interleaved.append(second[i])
    return interleaved


def write_output(
    reader: PdfReader,
    interleaved: List[Union[PageObject, None]],
    output_path: str,
) -> None:
    writer = PdfWriter()

    # Determine base page size for blanks (from the first page)
    base_width = None
    base_height = None
    if len(reader.pages) > 0:
        media_box = reader.pages[0].mediabox
        base_width = float(media_box.width)
        base_height = float(media_box.height)

    for idx, page in enumerate(interleaved):
        if page is None:
            if base_width is None or base_height is None:
                raise ValueError("Cannot add blank page: unknown page size")
            writer.add_blank_page(width=base_width, height=base_height)
        else:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)


def plan_mapping(
    first_len: int,
    second_len: int,
    reverse_second: bool,
    pad_blank: bool,
) -> List[Tuple[Optional[int], Optional[int]]]:
    """
    Build a plan of (first_half_index, second_half_index) pairs per output step.
    Indices are 0-based within their respective halves; None indicates a blank.
    """
    # Create index lists (with None for padded blanks)
    first_idx = list(range(first_len))
    second_idx = list(range(second_len))
    if reverse_second:
        second_idx = list(reversed(second_idx))

    if pad_blank and len(first_idx) != len(second_idx):
        diff = abs(len(first_idx) - len(second_idx))
        if len(first_idx) < len(second_idx):
            first_idx += [None] * diff  # type: ignore
        else:
            second_idx += [None] * diff  # type: ignore

    mapping: List[Tuple[Optional[int], Optional[int]]] = []
    max_len = max(len(first_idx), len(second_idx))
    for i in range(max_len):
        a = first_idx[i] if i < len(first_idx) else None
        b = second_idx[i] if i < len(second_idx) else None
        mapping.append((a, b))
    return mapping


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    input_path = args.input
    if not os.path.isfile(input_path):
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 2

    # Decide reverse preference: default to reversing the second half (common case)
    if args.reverse_second and args.no_reverse_second:
        print(
            "Error: Use only one of --reverse-second or --no-reverse-second",
            file=sys.stderr,
        )
        return 2
    reverse_second = True
    if args.reverse_second:
        reverse_second = True
    if args.no_reverse_second:
        reverse_second = False

    try:
        reader = PdfReader(input_path)
    except Exception as e:
        print(f"Error reading PDF: {e}", file=sys.stderr)
        return 1

    try:
        first, second = split_halves(reader, args.split)
    except Exception as e:
        print(f"Error preparing halves: {e}", file=sys.stderr)
        return 2

    if args.dry_run:
        mapping = plan_mapping(len(first), len(second), reverse_second, args.pad_blank)
        print(
            f"Input pages: {len(reader.pages)} | first_half: {len(first)} | second_half: {len(second)}"
        )
        print(
            "Order (pairs show [first_half_index, second_half_index] in output sequence):"
        )
        out_index = 0
        for a, b in mapping:
            if a is not None:
                print(f"{out_index:4d}: first[{a}] -> output")
                out_index += 1
            if b is not None:
                print(f"{out_index:4d}: second[{b}] -> output")
                out_index += 1
        return 0

    interleaved = interleave_pages(first, second, reverse_second, args.pad_blank)
    output_path = determine_output_path(input_path, args.output)

    try:
        write_output(reader, interleaved, output_path)
    except Exception as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        return 1

    print(f"Wrote interleaved PDF: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
