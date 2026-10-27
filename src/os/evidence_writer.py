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

Directory batch face (AC-EVDB1..AC-EVDB8, pre-registered in
state/queue/tech.md R2172 claim BEFORE this code):
  * AC-EVDB1  check_dir returns the six-key envelope {dir, file_count,
              tee_count, flagged_count, skipped_count, rows} with the
              six-key census rows {name, class, bytes, crlf, bare_lf,
              utf8}; candidates are the directory's direct regular,
              non-symlink, exactly suffix ".log" files, in name order
              (no recursion).
  * AC-EVDB2  check_dir is read-only (bytes and mtime unchanged) and
              raises on a missing path.
  * AC-EVDB3  fix_dir rewrites only files classified non-tee; healthy
              candidates are not touched at all.
  * AC-EVDB4  fix_dir rows report before/after bytes and lines, both
              measured from bytes read back off disk; the line table
              outside the newline axis is preserved.
  * AC-EVDB5  an unfixable candidate (non utf-8) fails the whole batch
              BEFORE any write.
  * AC-EVDB6  a write failure mid-batch restores every already-written
              candidate byte for byte (no temp residue).
  * AC-EVDB7  CLI --check-dir exits 0/2/3 and prints per-file plus a
              summary line; --fix-dir is idempotent.
  * AC-EVDB8  ASCII stdlib source, no wall clock, wired into the
              reconcile battery as os-evidence-writer-dir(8).

Usage:
    python src/os/evidence_writer.py --check qa/<evidence>.log
    python src/os/evidence_writer.py --fix qa/<evidence>.log
    python src/os/evidence_writer.py --check-dir qa
    python src/os/evidence_writer.py --fix-dir qa
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


LOG_SUFFIX = ".log"


def _dir_entries(path):
    """Return (candidate names, skipped entry count) for one directory.

    Only direct, regular, non-symlink files whose name ends with the
    lowercase ".log" suffix are candidates (AC-EVDB1). No recursion.
    """
    if not os.path.isdir(path):
        raise EvidenceDialectError("evidence directory missing: %s" % path)
    names = []
    skipped = 0
    for name in sorted(os.listdir(path)):
        full = os.path.join(path, name)
        if (name.endswith(LOG_SUFFIX) and not os.path.islink(full)
                and os.path.isfile(full)):
            names.append(name)
        else:
            skipped += 1
    return names, skipped


def check_dir(path):
    """Read-only dialect census over one directory (AC-EVDB1/EVD2)."""
    names, skipped = _dir_entries(path)
    rows = []
    for name in names:
        row = check_file(os.path.join(path, name))
        rows.append({"name": name, "class": row["class"],
                     "bytes": row["bytes"], "crlf": row["crlf"],
                     "bare_lf": row["bare_lf"], "utf8": row["utf8"]})
    tee = len([row for row in rows if row["class"] == TEE])
    return {"dir": os.path.abspath(path), "file_count": len(rows),
            "tee_count": tee, "flagged_count": len(rows) - tee,
            "skipped_count": skipped, "rows": rows}


def _read_raw(path):
    with open(path, "rb") as stream:
        return stream.read()


def _raw_lines(raw):
    """Decode strictly and count lines; a bad byte fails the batch."""
    try:
        return raw.decode("utf-8", "strict").splitlines()
    except UnicodeDecodeError as exc:
        raise EvidenceDialectError(
            "cannot normalise non utf-8 evidence: %s"
            % exc.__class__.__name__)


def _restore(path, raw):
    """Put the original bytes back atomically (rollback leg, AC-EVDB6)."""
    parent = os.path.dirname(os.path.abspath(path))
    handle, tmp = tempfile.mkstemp(prefix=".evd-", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(raw)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def fix_dir(path):
    """Normalise every flagged candidate, reporting before/after (AC-EVDB3..6).

    Validation (classification and strict utf-8 decode) completes for the
    whole batch before the first byte is written; a write failure restores
    every already-written file to its original bytes.
    """
    names, skipped = _dir_entries(path)
    plan = []
    for name in names:
        full = os.path.join(path, name)
        row = check_file(full)
        raw = _read_raw(full)
        plan.append({"name": name, "path": full, "raw": raw,
                     "class_before": row["class"],
                     "before_bytes": len(raw),
                     "lines": _raw_lines(raw)})
    written = []
    try:
        for item in plan:
            if item["class_before"] == TEE:
                continue
            write_evidence(item["path"], item["raw"].decode("utf-8"))
            written.append(item)
    except BaseException:
        for item in written:
            _restore(item["path"], item["raw"])
        raise
    rows = []
    for item in plan:
        after = _read_raw(item["path"])
        after_rows = _raw_lines(after)
        if after_rows != item["lines"]:
            if item["path"] in [w["path"] for w in written]:
                _restore(item["path"], item["raw"])
            raise EvidenceDialectError(
                "line content changed by normalisation: %s" % item["name"])
        rows.append({"name": item["name"],
                     "before_bytes": item["before_bytes"],
                     "before_lines": len(item["lines"]),
                     "after_bytes": len(after),
                     "after_lines": len(after_rows),
                     "class_before": item["class_before"],
                     "class_after": check_file(item["path"])["class"],
                     "changed": item["class_before"] != TEE})
    fixed = len(written)
    return {"dir": os.path.abspath(path), "file_count": len(rows),
            "fixed_count": fixed, "skipped_count": skipped, "rows": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="single-writer evidence log helper (LF law)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", metavar="PATH",
                       help="classify one evidence file (read-only)")
    group.add_argument("--fix", metavar="PATH",
                       help="normalise one evidence file to LF/utf-8")
    group.add_argument("--check-dir", metavar="DIR", dest="check_dir",
                       help="classify every *.log in one directory (read-only)")
    group.add_argument("--fix-dir", metavar="DIR", dest="fix_dir",
                       help="normalise every flagged *.log in one directory")
    args = parser.parse_args(argv)

    if args.check_dir:
        try:
            envelope = check_dir(args.check_dir)
        except EvidenceDialectError:
            print("MISSING %s" % args.check_dir)
            return EXIT_MISSING
        for row in envelope["rows"]:
            print("check-dir name=%s class=%s bytes=%d crlf=%d"
                  % (row["name"], row["class"], row["bytes"], row["crlf"]))
        print("dir files=%d tee=%d flagged=%d"
              % (envelope["file_count"], envelope["tee_count"],
                 envelope["flagged_count"]))
        return EXIT_TEE if envelope["flagged_count"] == 0 else EXIT_FLAG

    if args.fix_dir:
        try:
            envelope = fix_dir(args.fix_dir)
        except EvidenceDialectError as exc:
            print("REFUSED %s: %s" % (args.fix_dir, exc))
            return EXIT_FLAG
        for row in envelope["rows"]:
            print("fix-dir name=%s class=%s->%s bytes=%d->%d lines=%d->%d"
                  % (row["name"], row["class_before"], row["class_after"],
                     row["before_bytes"], row["after_bytes"],
                     row["before_lines"], row["after_lines"]))
        print("dir fixed=%d skipped=%d"
              % (envelope["fixed_count"], envelope["skipped_count"]))
        return EXIT_TEE

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