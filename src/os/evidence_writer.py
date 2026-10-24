#!/usr/bin/env python3
"""evidence_writer.py - single-writer evidence log helper (LF law).

Any function returning with a non-ASCII body of text is out of scope:
this module is plain stdlib, ASCII source, zero network imports.

Product law (AC-EVD1..AC-EVD8, pre-registered in state/queue/tech.md
BEFORE this code, R2072 claim):
  * AC-EVD1  write_evidence lands utf-8 no-BOM bytes with crlf == 0
             (still LF on Windows default-text environments) and
             exactly one trailing newline; the writer census reads
             the fresh file back as class "tee".
  * AC-EVD2  input CRLF / CR / mixed newlines are normalised to LF
             line-for-line (content unchanged, only EOL).
  * AC-EVD3  atomic replace: same-directory tempfile + os.replace;
             encoding/type errors raise BEFORE any disk touch, so a
             failure can never leave a half-written evidence file.
  * AC-EVD4  post-write self-check: the fresh file is classified and
             a non-tee dialect raises EvidenceDialectError - a broken
             dialect is never written silently.
  * AC-EVD5  check_file is read-only: it returns the census row and
             never rewrites bytes or mtime; a missing file raises.
  * AC-EVD6  a real CRLF file (default text-mode writer) is FLAGGED;
             fix_file normalises it to tee with content equal on the
             newline axis only, and refuses non utf-8 bytes.
  * AC-EVD7  the census stays read-only over a fixture directory
             (bytes and mtime of every file are unchanged).
  * AC-EVD8  CLI: --check exits 0 tee / 2 non-tee / 3 missing;
             --fix rewrites then prints the post class.

Usage:
    python src/os/evidence_writer.py --check qa/<evidence>.log
    python src/os/evidence_writer.py --fix qa/<evidence>.log
In-process:
    from evidence_writer import write_evidence
    write_evidence("qa/foo.log", "line one\r\nline two")
"""

import argparse
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import qa_writer_census as CENSUS  # classify_file single source

TEE = "tee"
EXIT_TEE = 0
EXIT_FLAG = 2
EXIT_MISSING = 3


class EvidenceDialectError(Exception):
    """Raised when an evidence file cannot be proven to be tee."""


def normalize_lf(text):
    """Return text with every EOL form collapsed to a bare LF."""
    if not isinstance(text, str):
        raise TypeError("evidence text must be str, got %r"
                        % type(text).__name__)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _payload(text):
    """Encode to the canonical evidence byte shape (fail-closed)."""
    body = normalize_lf(text)
    if body:
        body = body.rstrip("\n") + "\n"
    return body.encode("utf-8")


def _post_check(path, enabled=True):
    row = check_file(path)
    if enabled and row["class"] != TEE:
        raise EvidenceDialectError(
            "evidence dialect=%s bytes=%d crlf=%d"
            % (row["class"], row["bytes"], row["crlf"]))
    return row


def write_evidence(path, text, check=True):
    """Write one evidence file through the single LF writer.

    Returns the post-write census row (class is always "tee" unless
    check=False was requested on purpose).
    """
    data = _payload(text)  # encode first: a bad input touches nothing
    target = os.path.abspath(path)
    parent = os.path.dirname(target)
    os.makedirs(parent, exist_ok=True)
    handle, tmp = tempfile.mkstemp(prefix=".evd-", suffix=".tmp",
                                   dir=parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
        os.replace(tmp, target)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    return _post_check(target, enabled=check)


def check_file(path):
    """Read-only dialect check (AC-EVD5). Zero writes, zero repair."""
    if not os.path.isfile(path):
        raise EvidenceDialectError("evidence file missing: %s" % path)
    return CENSUS.classify_file(path)


def fix_file(path):
    """Normalise an existing evidence file to the tee dialect.

    Only the EOL axis is rewritten; the line content is preserved.
    Non utf-8 bytes are refused fail-closed (AC-EVD6) - never guess
    an encoding for an evidence file.
    """
    row = check_file(path)
    if row["class"] == TEE:
        return row
    with open(path, "rb") as stream:
        raw = stream.read()
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise EvidenceDialectError(
            "cannot normalise non utf-8 evidence: %s" % exc.__class__.__name__)
    return write_evidence(path, text)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="single-writer evidence log helper (LF law)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", metavar="PATH",
                       help="classify one evidence file (read-only)")
    group.add_argument("--fix", metavar="PATH",
                       help="normalise one evidence file to LF/utf-8")
    args = parser.parse_args(argv)

    if args.check:
        try:
            row = check_file(args.check)
        except EvidenceDialectError:
            print("MISSING %s" % args.check)
            return EXIT_MISSING
        print("check class=%s bytes=%d crlf=%d bare_lf=%d utf8=%s %s"
              % (row["class"], row["bytes"], row["crlf"],
                 row["bare_lf"], row["utf8"], args.check))
        return EXIT_TEE if row["class"] == TEE else EXIT_FLAG

    try:
        row = fix_file(args.fix)
    except EvidenceDialectError as exc:
        print("REFUSED %s: %s" % (args.fix, exc))
        return EXIT_FLAG
    print("fix class=%s bytes=%d crlf=%d %s"
          % (row["class"], row["bytes"], row["crlf"], args.fix))
    return EXIT_TEE


if __name__ == "__main__":
    sys.exit(main())