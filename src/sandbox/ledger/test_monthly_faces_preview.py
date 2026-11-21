"""Acceptance suite for the R3193 monthly market faces preview page.

Product under proof: src/sandbox/ledger/monthly_faces_preview.py, the R3193
generator that renders five shipped market monthly read faces into one
self-contained offline page plus one JSON payload from a deterministic demo
world. Until this window the page was guarded only by the generator own
--verify flag, so the battery, the matrix, the census and the closeout gate
could not see it at all.

Criteria AC-MFRW1..AC-MFRW8 were registered in src/os/backlog.md (R3194 PIN
row) BEFORE this file existed - honesty law. The AC-MFRW prefix, this module
name, the ledger-monthly-faces-preview runner label and the declared count
were git-grep -F zero-occupancy anchored 2026-11-21 (the label text exists in
the board and export prose only, with no reconcile_all row).

Criteria:
  AC-MFRW1 contract and reuse: the generator exports the ten names this
    suite drives, this module defines none of the renderer functions in its
    own namespace (so the renderer is reused rather than copied), and the
    shipped CLI writing to temp paths exits 0 with bytes equal to the
    in-process render.
  AC-MFRW2 determinism: two independent demo worlds render byte-identical
    HTML and JSON (equal sha16 on each).
  AC-MFRW3 conservation: the generator own check_identity reports zero
    problems and this suite recomputes every IDENTITY pair sum against the
    envelope, with ascending month grids, on its own.
  AC-MFRW4 honest empty states: every face with zero months keeps its named
    empty copy on the page and the face itself stays visible.
  AC-MFRW5 standing compliance: the page carries the AIGC label and the
    non-advisory disclaimer, no external reference and no script tag, and
    the generator source stays pure ASCII.
  AC-MFRW6 zero write: the shipped preview/apimarket.db size and sha16 are
    unchanged across the whole run and so are the two shipped page files.
  AC-MFRW7 hygiene: this source is ASCII, its imports are stdlib only (no
    socket, urllib, http.client or requests) plus the generator itself, and
    every write lands in a private temp dir removed on exit.
  AC-MFRW8 runner wiring (recorded last so it can weight the count against
    this suite own records): reconcile_all.py carries the label exactly
    once, names this file and declares the same number of criteria this
    suite actually records.

Usage: python test_monthly_faces_preview.py
"""

import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
LEDGER = os.path.join(BASE, "src", "sandbox", "ledger")
if LEDGER not in sys.path:
    sys.path.insert(0, LEDGER)

import monthly_faces_preview as M  # noqa: E402

RESULTS = []
SUITE_FILE = os.path.abspath(__file__)
RECONCILE = os.path.join(BASE, "src", "sandbox", "reconcile_all.py")
MODULE = os.path.join(LEDGER, "monthly_faces_preview.py")
LABEL = "ledger-monthly-faces-preview"
DECLARED = 8
TEMPS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok), evidence))
    print("%s %s %s" % ("PASS" if ok else "FAIL", ac, evidence))


def sha16_bytes(data):
    return hashlib.sha256(data).hexdigest()[:16]


def sha16_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def temp_root(tag):
    path = tempfile.mkdtemp(prefix="monthly-faces-gate-" + tag + "-")
    TEMPS.append(path)
    return path


def shipped_marks():
    """Snapshot identity of everything this suite must not touch."""
    return (
        os.path.getsize(M.SNAPSHOT),
        sha16_file(M.SNAPSHOT),
        os.path.isfile(M.OUT_HTML),
        sha16_file(M.OUT_HTML) if os.path.isfile(M.OUT_HTML) else None,
        os.path.isfile(M.OUT_JSON),
        sha16_file(M.OUT_JSON) if os.path.isfile(M.OUT_JSON) else None,
    )


def check_contract():
    names = ("collect", "render_html", "render_json", "check_identity",
             "load_copy", "FACES", "IDENTITY", "SNAPSHOT", "OUT_HTML",
             "OUT_JSON")
    missing = [name for name in names if not hasattr(M, name)]
    # Ask this module own namespace instead of scanning its text: a text
    # scan for markup or function names matches the scan literals
    # themselves (this arm went red twice on exactly that self-match).
    own = dir(sys.modules[__name__])
    copied = [name for name in ("collect", "render_html", "render_json",
                                "check_identity") if name in own]
    copy = M.load_copy()
    faces = M.collect(temp_root("contract"))
    html_in = M.render_html(copy, faces)
    json_in = M.render_json(faces)
    out_dir = temp_root("contract-cli")
    out_html = os.path.join(out_dir, "page.html")
    out_json = os.path.join(out_dir, "page.json")
    proc = subprocess.run([sys.executable, MODULE, "--out", out_html,
                           "--json-out", out_json], capture_output=True)
    same = False
    if proc.returncode == 0 and os.path.isfile(out_html) \
            and os.path.isfile(out_json):
        with open(out_html, "rb") as fh:
            cli_html = fh.read()
        with open(out_json, "rb") as fh:
            cli_json = fh.read()
        same = (cli_html == html_in.encode("utf-8")
                and cli_json == json_in.encode("utf-8"))
    record("AC-MFRW1", not missing and not copied and same,
           "exports=%d/%d own_copies=%s cli_exit=%d cli_equal=%s"
           % (len(names) - len(missing), len(names),
              ",".join(copied) or "none", proc.returncode, same))


def check_determinism():
    copy = M.load_copy()
    marks = []
    for tag in ("det-a", "det-b"):
        faces = M.collect(temp_root(tag))
        marks.append((
            sha16_bytes(M.render_html(copy, faces).encode("utf-8")),
            sha16_bytes(M.render_json(faces).encode("utf-8")),
        ))
    record("AC-MFRW2", marks[0] == marks[1],
           "html %s/%s json %s/%s"
           % (marks[0][0], marks[1][0], marks[0][1], marks[1][1]))


def check_conservation():
    faces = M.collect(temp_root("identity"))
    problems = []
    M.check_identity(faces, problems)
    detail = []
    for face in faces:
        months = face["months"]
        for row_key, env_key in M.IDENTITY.get(face["fn"], []):
            total = sum((row.get(row_key) or 0) for row in months)
            if total != face["envelope"].get(env_key):
                problems.append("%s.%s" % (face["fn"], row_key))
        if months:
            stamps = [row["month"] for row in months]
            if stamps != sorted(stamps):
                problems.append("%s.grid" % face["fn"])
        detail.append("%s:%d" % (face["fn"], len(months)))
    record("AC-MFRW3", not problems,
           "problems=%d/%s faces=%s"
           % (len(problems), ",".join(problems) or "none",
              ",".join(detail)))


def check_empty():
    copy = M.load_copy()
    faces = M.collect(temp_root("empty"))
    page = M.render_html(copy, faces)
    empties = [face["fn"] for face in faces if not face["months"]]
    missing = []
    for fn in empties:
        text = copy["empty"].get(fn)
        if not text or text not in page:
            missing.append(fn + ".copy")
        if copy["faces"].get(fn, fn) not in page:
            missing.append(fn + ".label")
    record("AC-MFRW4", bool(empties) and not missing,
           "empty_faces=%s missing=%s"
           % (",".join(empties) or "none", ",".join(missing) or "none"))


def check_compliance():
    copy = M.load_copy()
    faces = M.collect(temp_root("compliance"))
    page = M.render_html(copy, faces)
    aigc = copy["aigc_label"] in page
    dis = copy["disclaimer"] in page
    external = ("http://" in page) or ("https://" in page)
    script = "<script" in page.lower()
    with open(MODULE, "rb") as fh:
        raw = fh.read()
    try:
        raw.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        ascii_ok = False
    record("AC-MFRW5",
           aigc and dis and not external and not script and ascii_ok,
           "aigc=%s disclaimer=%s external=%s script=%s module_ascii=%s"
           % (aigc, dis, external, script, ascii_ok))


def check_zero_write(before):
    after = shipped_marks()
    record("AC-MFRW6", before == after,
           "snapshot size=%d sha16=%s pages=%s unchanged=%s"
           % (after[0], after[1], after[4] and after[2], before == after))


def check_hygiene():
    with io.open(SUITE_FILE, "r", encoding="utf-8") as fh:
        source = fh.read()
    try:
        source.encode("ascii")
        ascii_ok = True
    except UnicodeEncodeError:
        ascii_ok = False
    imports = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            imports.append(stripped)
    banned = [line for line in imports
              if ("socket" in line or "urllib" in line
                  or "http.client" in line or "requests" in line)]
    allowed = ("hashlib", "io", "os", "shutil", "subprocess", "sys",
               "tempfile", "monthly_faces_preview")
    stray = []
    for line in imports:
        parts = line.replace(",", " ").split()
        for index, part in enumerate(parts):
            if part in ("import", "from"):
                name = parts[index + 1].split(".")[0]
                if name not in allowed:
                    stray.append(name)
                break
    record("AC-MFRW7", ascii_ok and not banned and not stray,
           "ascii=%s banned=%s stray=%s imports=%d"
           % (ascii_ok, ",".join(banned) or "none",
              ",".join(stray) or "none", len(imports)))


def check_wiring():
    with io.open(RECONCILE, "r", encoding="utf-8") as fh:
        text = fh.read()
    label_hits = text.count('"%s"' % LABEL)
    file_hits = text.count("test_monthly_faces_preview.py")
    declared = -1
    marker = text.find('"%s"' % LABEL)
    if marker >= 0:
        window = text[marker:marker + 400]
        cut = window.find("), ")
        if cut >= 0:
            digits = ""
            for char in window[cut + 3:]:
                if char.isdigit():
                    digits += char
                else:
                    break
            if digits:
                declared = int(digits)
    total_after = len(RESULTS) + 1
    ok = (label_hits == 1 and file_hits == 1 and declared == DECLARED
          and total_after == DECLARED)
    record("AC-MFRW8", ok,
           "label_hits=%d file_hits=%d declared=%d recorded=%d expected=%d"
           % (label_hits, file_hits, declared, total_after, DECLARED))


def main():
    before = shipped_marks()
    try:
        check_contract()
        check_determinism()
        check_conservation()
        check_empty()
        check_compliance()
        check_zero_write(before)
        check_hygiene()
        check_wiring()
    finally:
        for path in TEMPS:
            shutil.rmtree(path, ignore_errors=True)

    passed = sum(1 for _ac, ok, _ev in RESULTS if ok)
    print("\nSUITE %s %d/%d"
          % ("PASS" if passed == len(RESULTS) else "FAIL",
             passed, len(RESULTS)))
    payload = "%s|%s" % (
        "".join("%s=%d;" % (ac, 1 if ok else 0) for ac, ok, _ev in RESULTS),
        len(RESULTS))
    print("SUITE-SHA16 %s" % sha16_bytes(payload.encode("utf-8")))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
