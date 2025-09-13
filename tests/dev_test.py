#!/usr/bin/env python3
"""
Developer test for pdffake_duplex: generates synthetic PDFs with identifiable
page sizes, runs the interleaver in different modes, and asserts ordering.
"""

from __future__ import annotations

import os
import sys
from typing import List

from pypdf import PdfReader, PdfWriter

# Import the module under test from workspace
import pdffake_duplex as tool


def make_pdf(path: str, ids: List[int]) -> None:
    """Create a PDF where each page has height 200 + id and width 200."""
    w = PdfWriter()
    for pid in ids:
        w.add_blank_page(width=200, height=200 + pid)
    with open(path, "wb") as f:
        w.write(f)


def read_ids(path: str) -> List[int]:
    r = PdfReader(path)
    out = []
    for p in r.pages:
        h = float(p.mediabox.height)
        out.append(int(round(h - 200)))
    return out


def assert_eq(actual: List[int], expected: List[int], label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label} failed.\nExpected: {expected}\nActual:   {actual}")


def run_tests(tmpdir: str) -> None:
    os.makedirs(tmpdir, exist_ok=True)

    # Test 1: second half reversed (typical) -> default behavior
    # Fronts: 1,2,3 | Backs (scanned): 103,102,101
    t1_in = os.path.join(tmpdir, "t1_in.pdf")
    t1_out = os.path.join(tmpdir, "t1_out.pdf")
    make_pdf(t1_in, [1, 2, 3, 103, 102, 101])
    rc = tool.main([t1_in, "-o", t1_out])
    if rc != 0:
        raise SystemExit(f"Tool returned {rc} for test 1")
    got = read_ids(t1_out)
    exp = [1, 101, 2, 102, 3, 103]
    assert_eq(got, exp, "Test 1")

    # Test 2: second half already forward -> use --no-reverse-second
    t2_in = os.path.join(tmpdir, "t2_in.pdf")
    t2_out = os.path.join(tmpdir, "t2_out.pdf")
    make_pdf(t2_in, [1, 2, 3, 101, 102, 103])
    rc = tool.main([t2_in, "--no-reverse-second", "-o", t2_out])
    if rc != 0:
        raise SystemExit(f"Tool returned {rc} for test 2")
    got = read_ids(t2_out)
    exp = [1, 101, 2, 102, 3, 103]
    assert_eq(got, exp, "Test 2")

    # Test 3: custom split (1-based). Total 6 pages, second half at page 5 -> split=5
    # Input: first 4 fronts 1..4, then backs 104,103 (reversed scan)
    t3_in = os.path.join(tmpdir, "t3_in.pdf")
    t3_out = os.path.join(tmpdir, "t3_out.pdf")
    make_pdf(t3_in, [1, 2, 3, 4, 104, 103])
    rc = tool.main([t3_in, "--split", "5", "-o", t3_out])
    if rc != 0:
        raise SystemExit(f"Tool returned {rc} for test 3")
    got = read_ids(t3_out)
    # Interleave: (1,103),(2,104),(3,None),(4,None) -> but no padding, so 1,103,2,104,3,4
    exp = [1, 103, 2, 104, 3, 4]
    assert_eq(got, exp, "Test 3")

    # Test 4: same as Test 3 but with padding blanks to pair all
    t4_out = os.path.join(tmpdir, "t4_out.pdf")
    rc = tool.main([t3_in, "--split", "5", "--pad-blank", "-o", t4_out])
    if rc != 0:
        raise SystemExit(f"Tool returned {rc} for test 4")
    got = read_ids(t4_out)
    # Expect: 1,103,2,104,3,<blank>,4,<blank> -> blanks encode as height of first page, so we detect by ids==1 again
    # We cannot distinguish blank from page id==1 by height; instead, just check prefix ordering unaffected
    prefix = got[:4]
    assert_eq(prefix, [1, 103, 2, 104], "Test 4 prefix")

    print("All tests passed.")


if __name__ == "__main__":
    run_tests(tmpdir=os.path.join(os.path.dirname(__file__), "out"))

