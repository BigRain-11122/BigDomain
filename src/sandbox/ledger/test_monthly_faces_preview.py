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
  AC-MFRW8 runner wiring: reconcile_all.py carries the label exactly
    once and names this file, and the count it declares equals the
    DECLARED law below. (Until R3195 this arm also proved that count
    against its own position; the positional half moved to AC-MFPC6
    when this suite grew from eight criteria to fourteen - recorded as
    JUDGED-CHANGED, no sentence relaxed.)

R3195 copy-key contract criteria (pre-registered in the same board as a
PIN row BEFORE this code existed):

  AC-MFPC1 the key law self-proves: REQUIRED_COPY_KEYS equals the set of
    distinct top-level keys the generator source really reads through
    copy["..."] (this suite scans the GENERATOR source only, never its
    own text, so no scan literal can match itself), and equals the key
    set of the shipped copy file.
  AC-MFPC2 every required key is refused when missing: dropping any one
    of the thirteen keys makes load_copy raise CopyError with code
    E_MFP_COPY and the key named in the detail, while the untouched
    shipped copy loads clean.
  AC-MFPC3 the refusal writes nothing: a CLI run with a short copy file
    exits 2 with one stdout line naming E_MFP_COPY and the missing key,
    zero stderr bytes, and neither --out nor --json-out on disk; the
    --verify --log path refuses identically and creates no log.
  AC-MFPC4 the healthy bytes do not move: the shipped copy renders the
    shipped page and JSON byte for byte (6834B / 13015B) in process, and
    the CLI writing to temp paths produces those same bytes at rc=0.
  AC-MFPC5 shape and hygiene: a JSON list as the whole copy file is
    refused by name with the type in the detail, an extra unread key is
    tolerated (forward compatibility), the module source stays ASCII,
    and CopyError publishes code, detail and face().
  AC-MFPC6 wiring and self-count (recorded last so it can weigh the
    count against this suite own records): reconcile_all.py carries the
    label once and this file once, the registry count equals DECLARED,
    and DECLARED equals the number of criteria actually recorded here.

R3196 read-entry criteria (pre-registered in the same board as a PIN row
BEFORE this code existed):

  AC-MFPR1 three read failures are refused by name: a missing path,
    invalid UTF-8 and malformed JSON each make load_copy raise
    CopyError with code E_MFP_COPY and a detail that starts with the
    underlying reader type, while the shipped copy still loads clean.
  AC-MFPR2 the CLI reads as one line and writes nothing: each fixture
    exits 2 with exactly one stdout line naming E_MFP_COPY and the
    reader type, zero stderr bytes and neither output file on disk; the
    --verify --log path refuses identically and creates no log.
  AC-MFPR3 the healthy bytes do not move: the shipped copy renders the
    shipped page and JSON byte for byte in process and through the CLI
    at rc=0, and a byte-identical copy at another path loads to an
    equal mapping.
  AC-MFPR4 the older shape laws survive the wrapper: a JSON list at the
    top level is still refused with the type in the detail, an extra
    unread key is still tolerated, and dropping a required key is still
    refused with the key named.
  AC-MFPR5 hygiene and wiring self-count (recorded last): the module
    source stays ASCII, the read entry is one definition plus one call
    site, reconcile_all.py carries the label and this file once, and
    the registry count equals DECLARED. (Until R3197 this arm also
    weighed DECLARED against what this run recorded; that positional
    half moved to AC-MFPW6 when the suite grew from nineteen criteria
    to twenty-five - JUDGED-CHANGED, no sentence relaxed.)

R3197 write-face criteria (pre-registered in the same board as a PIN
row BEFORE this code existed):

  AC-MFPW1 a render-time failure writes nothing: injecting an exception
    into render_html or render_json, in a world where the targets
    already hold content and in a world where they do not, leaves the
    old bytes identical or the targets absent, and no .mfp-write-*
    temp file behind.
  AC-MFPW2 two outputs cannot half-write: when the second _stage fails,
    the first target is not swapped (both texts are staged before any
    replace), so its previous bytes survive exactly.
  AC-MFPW3 a replace failure does not truncate the target: with
    os.replace raising once, the target keeps its previous bytes and
    the staged temp file is removed.
  AC-MFPW4 the healthy bytes do not move: in process and through the
    CLI the page and JSON match the shipped 6834B/13015B byte for byte.
  AC-MFPW5 the CLI face is named (R3198 rewrote this arm): an injected
    render, stage or replace failure exits 2 with exactly one stdout
    line carrying E_MFP_WRITE and the stage, zero stderr bytes, and the
    target keeps its previous bytes. (Until R3197 this arm pinned the
    opposite - rc=1 with a traceback - because that window only moved
    what lands on disk; the sentence changed with the new face, recorded
    as JUDGED-CHANGED.)
  AC-MFPW6 hygiene and wiring self-count (recorded last): the module
    source stays ASCII, os.replace appears exactly once, both render
    calls happen inside write_outputs before the first _stage, three
    raise WriteError sites carry the three stages, main catches
    WriteError once, reconcile_all.py carries the label and this file
    once, and the registry count equals DECLARED equals what this run
    recorded.

R3198 named write-face criteria (pre-registered in the same board as a
PIN row BEFORE this code existed):

  AC-MFPX1 three stages, one named family: injecting a failure into
    render_html, render_json, _stage or os.replace makes write_outputs
    raise WriteError with code E_MFP_WRITE, stage render/render/stage/
    replace, the injected exception type first in the detail, and the
    original exception reachable as __cause__; a healthy world raises
    nothing.
  AC-MFPX2 the CLI names the stage, not the traceback: four real
    subprocess runs exit 2 with exactly one stdout line carrying
    E_MFP_WRITE and the matching stage, zero stderr bytes, the previous
    bytes untouched and no .mfp-write-* temp file left behind.

R3199 world/log criteria (pre-registered in the same board as a PIN row
BEFORE this code existed):

  AC-MFPX3 a demo world that cannot be built is one named code: an
    injected collect() failure makes build_world raise WorldError with
    code E_MFP_WORLD, the injected type first in the detail and the
    original reachable as __cause__; a healthy world builds all five
    faces and raises nothing.
  AC-MFPX4 the log is swapped in and never costs the answer: a healthy
    subprocess run writes a log whose lines equal stdout's and whose
    bytes carry no CR (the canonical utf-8/lf dialect); when the --log
    path is a directory the same text is printed in full, one E_MFP_LOG
    refusal line follows, rc=2, stderr is empty, the directory is still
    a directory and no .mfp-write-* temp is left; a missing log
    directory is created and the log lands.
  AC-MFPX5 a failed verify still leaves its evidence: with --log set and
    collect() failing, the log file exists, carries VERIFY FAIL
    problems=1 and the E_MFP_WORLD line, equals what was printed, and
    the run exits 2 (before R3199 the file did not exist at all).

Usage: python test_monthly_faces_preview.py
"""

import hashlib
import io
import json
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
DECLARED = 31
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
    allowed = ("hashlib", "io", "json", "os", "shutil", "subprocess", "sys",
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


def registry_declared(text):
    """The count reconcile_all.py declares beside this suite label."""
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
    return declared


def check_wiring():
    with io.open(RECONCILE, "r", encoding="utf-8") as fh:
        text = fh.read()
    label_hits = text.count('"%s"' % LABEL)
    file_hits = text.count("test_monthly_faces_preview.py")
    declared = registry_declared(text)
    ok = (label_hits == 1 and file_hits == 1 and declared == DECLARED)
    record("AC-MFRW8", ok,
           "label_hits=%d file_hits=%d declared=%d law=%d"
           % (label_hits, file_hits, declared, DECLARED))


def keys_read_by_generator():
    """Distinct top-level copy keys the GENERATOR source reads. This suite
    own text is never scanned, so no scan literal can match itself."""
    with io.open(MODULE, "r", encoding="utf-8") as fh:
        source = fh.read()
    keys = []
    marker = 'copy["'
    index = 0
    while True:
        index = source.find(marker, index)
        if index < 0:
            break
        end = source.find('"]', index + len(marker))
        if end < 0:
            break
        name = source[index + len(marker):end]
        if name not in keys:
            keys.append(name)
        index = end + 2
    return keys


def check_copy_keys():
    law = list(getattr(M, "REQUIRED_COPY_KEYS", ()))
    read = keys_read_by_generator()
    shipped = sorted(M.load_copy().keys())
    ok = (bool(law) and sorted(law) == sorted(read)
          and sorted(law) == shipped)
    record("AC-MFPC1", ok,
           "law=%d read=%d shipped=%d same_law_read=%s same_law_shipped=%s"
           % (len(law), len(read), len(shipped),
              sorted(law) == sorted(read), sorted(law) == shipped))


def write_copy_variant(payload, tag):
    path = os.path.join(temp_root("copy-" + tag), "copy.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return path


def check_copy_refusal():
    copy = M.load_copy()
    law = list(M.REQUIRED_COPY_KEYS)
    failures = []
    for key in law:
        mutated = dict(copy)
        del mutated[key]
        path = write_copy_variant(mutated, "miss-" + key)
        try:
            M.load_copy(path)
            failures.append(key + ".accepted")
            continue
        except M.CopyError as exc:
            if exc.code != "E_MFP_COPY":
                failures.append(key + ".code=" + exc.code)
            if key not in exc.detail:
                failures.append(key + ".unnamed")
        except Exception as exc:  # noqa: BLE001 - any other type is a failure
            failures.append(key + "." + type(exc).__name__)
    try:
        M.load_copy(M.COPY_PATH)
        control = True
    except Exception:  # noqa: BLE001 - the shipped file must load
        control = False
    record("AC-MFPC2", control and not failures,
           "keys=%d refused=%d failures=%s control=%s"
           % (len(law), len(law) - len([f for f in failures
                                        if f.endswith(".accepted")]),
              ",".join(failures) or "none", control))


def check_copy_cli():
    copy = M.load_copy()
    mutated = dict(copy)
    del mutated["src_line"]
    path = write_copy_variant(mutated, "cli")
    out_dir = temp_root("copy-cli-out")
    out_html = os.path.join(out_dir, "page.html")
    out_json = os.path.join(out_dir, "page.json")
    proc = subprocess.run([sys.executable, MODULE, "--copy", path,
                           "--out", out_html, "--json-out", out_json],
                          capture_output=True)
    stdout = proc.stdout.decode("utf-8", "replace")
    ok_line = (stdout.count("\n") == 1
               and "E_MFP_COPY" in stdout and "src_line" in stdout)
    ok_none = not os.path.isfile(out_html) and not os.path.isfile(out_json)
    log_path = os.path.join(temp_root("copy-cli-log"), "verify.log")
    vproc = subprocess.run([sys.executable, MODULE, "--copy", path,
                            "--verify", "--log", log_path],
                           capture_output=True)
    ok_verify = (vproc.returncode == 2 and not os.path.isfile(log_path)
                 and vproc.stderr == b"")
    record("AC-MFPC3",
           proc.returncode == 2 and proc.stderr == b"" and ok_line
           and ok_none and ok_verify,
           "cli_rc=%d stderr_bytes=%d one_line=%s no_outputs=%s "
           "verify_rc=%d verify_log=%s verify_stderr_bytes=%d"
           % (proc.returncode, len(proc.stderr), ok_line, ok_none,
              vproc.returncode, os.path.isfile(log_path),
              len(vproc.stderr)))


def check_copy_bytes():
    copy = M.load_copy()
    faces = M.collect(temp_root("copy-bytes"))
    html_now = M.render_html(copy, faces).encode("utf-8")
    json_now = M.render_json(faces).encode("utf-8")
    with open(M.OUT_HTML, "rb") as fh:
        html_shipped = fh.read()
    with open(M.OUT_JSON, "rb") as fh:
        json_shipped = fh.read()
    out_dir = temp_root("copy-bytes-cli")
    out_html = os.path.join(out_dir, "page.html")
    out_json = os.path.join(out_dir, "page.json")
    proc = subprocess.run([sys.executable, MODULE, "--out", out_html,
                           "--json-out", out_json], capture_output=True)
    cli_equal = False
    if proc.returncode == 0:
        with open(out_html, "rb") as fh:
            cli_html = fh.read()
        with open(out_json, "rb") as fh:
            cli_json = fh.read()
        cli_equal = cli_html == html_shipped and cli_json == json_shipped
    record("AC-MFPC4",
           html_now == html_shipped and json_now == json_shipped
           and proc.returncode == 0 and cli_equal,
           "html_bytes=%d json_bytes=%d inproc_equal=%s cli_equal=%s"
           % (len(html_shipped), len(json_shipped),
              html_now == html_shipped and json_now == json_shipped,
              cli_equal))


def check_copy_shape():
    path = write_copy_variant([{"title": "x"}], "list")
    detail = ""
    code = ""
    named = False
    try:
        M.load_copy(path)
    except M.CopyError as exc:
        code, detail = exc.code, exc.detail
    except Exception:  # noqa: BLE001 - a bare crash is not a named refusal
        pass
    named = code == "E_MFP_COPY" and "list" in detail
    copy = dict(M.load_copy())
    copy["r3195_unread_key"] = "tolerated"
    tolerated = True
    try:
        M.load_copy(write_copy_variant(copy, "extra"))
    except Exception:  # noqa: BLE001 - an extra key must not be refused
        tolerated = False
    with open(MODULE, "rb") as fh:
        raw = fh.read()
    try:
        raw.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        ascii_ok = False
    face_ok = (getattr(M.CopyError, "code", "") == "E_MFP_COPY"
               and hasattr(M.CopyError("x"), "detail")
               and M.CopyError("x").face().startswith("E_MFP_COPY "))
    record("AC-MFPC5", named and tolerated and ascii_ok and face_ok,
           "list_refused=%s detail=%r extra_tolerated=%s module_ascii=%s "
           "face_ok=%s"
           % (named, detail[:40], tolerated, ascii_ok, face_ok))


def check_copy_wiring():
    with io.open(RECONCILE, "r", encoding="utf-8") as fh:
        text = fh.read()
    label_hits = text.count('"%s"' % LABEL)
    file_hits = text.count("test_monthly_faces_preview.py")
    declared = registry_declared(text)
    total_after = len(RESULTS) + 1
    ok = (label_hits == 1 and file_hits == 1 and declared == DECLARED)
    record("AC-MFPC6", ok,
           "label_hits=%d file_hits=%d declared=%d recorded=%d law=%d"
           % (label_hits, file_hits, declared, total_after, DECLARED))


def read_failure_fixtures(tag):
    """Three unreadable copy files: missing path, bad UTF-8, bad JSON."""
    root = temp_root("read-" + tag)
    missing = os.path.join(root, "no-such-copy.json")
    bad_utf8 = os.path.join(root, "bad-utf8.json")
    with open(bad_utf8, "wb") as fh:
        fh.write(b'{"title": "\xff\xfe"}')
    bad_json = os.path.join(root, "bad-json.json")
    with open(bad_json, "wb") as fh:
        fh.write(b'{"title": ')
    return (("missing", missing, "FileNotFoundError"),
            ("badutf8", bad_utf8, "UnicodeDecodeError"),
            ("badjson", bad_json, "JSONDecodeError"))


def check_read_refusal():
    failures = []
    fixtures = read_failure_fixtures("refusal")
    for tag, path, want in fixtures:
        try:
            M.load_copy(path)
            failures.append(tag + ".accepted")
        except M.CopyError as exc:
            if exc.code != "E_MFP_COPY":
                failures.append(tag + ".code=" + exc.code)
            if not exc.detail.startswith(want + ":"):
                failures.append(tag + ".detail=" + exc.detail[:30])
        except Exception as exc:  # noqa: BLE001 - a bare crash is a failure
            failures.append(tag + "." + type(exc).__name__)
    try:
        M.load_copy(M.COPY_PATH)
        control = True
    except Exception:  # noqa: BLE001 - the shipped file must load
        control = False
    record("AC-MFPR1", control and not failures,
           "fixtures=%d refused=%d failures=%s control=%s"
           % (len(fixtures), len(fixtures) - len([f for f in failures
                                                  if f.endswith(".accepted")]),
              ",".join(failures) or "none", control))


def check_read_cli():
    problems = []
    fixtures = read_failure_fixtures("cli")
    for tag, path, want in fixtures:
        out_dir = temp_root("read-cli-" + tag)
        out_html = os.path.join(out_dir, "page.html")
        out_json = os.path.join(out_dir, "page.json")
        proc = subprocess.run([sys.executable, MODULE, "--copy", path,
                               "--out", out_html, "--json-out", out_json],
                              capture_output=True)
        stdout = proc.stdout.decode("utf-8", "replace")
        if proc.returncode != 2:
            problems.append(tag + ".rc=%d" % proc.returncode)
        if stdout.count("\n") != 1 or "E_MFP_COPY" not in stdout \
                or want not in stdout:
            problems.append(tag + ".stdout=%r" % stdout[:40])
        if proc.stderr != b"":
            problems.append(tag + ".stderr=%d" % len(proc.stderr))
        if os.path.isfile(out_html) or os.path.isfile(out_json):
            problems.append(tag + ".wrote")
        log_path = os.path.join(temp_root("read-cli-log-" + tag),
                                "verify.log")
        vproc = subprocess.run([sys.executable, MODULE, "--copy", path,
                                "--verify", "--log", log_path],
                               capture_output=True)
        if vproc.returncode != 2 or os.path.isfile(log_path) \
                or vproc.stderr != b"":
            problems.append(tag + ".verify")
    record("AC-MFPR2", not problems,
           "fixtures=%d problems=%s"
           % (len(fixtures), ",".join(problems) or "none"))


def check_read_bytes():
    copy = M.load_copy()
    faces = M.collect(temp_root("read-bytes"))
    html_now = M.render_html(copy, faces).encode("utf-8")
    json_now = M.render_json(faces).encode("utf-8")
    with open(M.OUT_HTML, "rb") as fh:
        html_shipped = fh.read()
    with open(M.OUT_JSON, "rb") as fh:
        json_shipped = fh.read()
    root = temp_root("read-bytes-copy")
    twin = os.path.join(root, "copy.json")
    shutil.copyfile(M.COPY_PATH, twin)
    same_dict = M.load_copy(twin) == copy
    out_dir = temp_root("read-bytes-cli")
    out_html = os.path.join(out_dir, "page.html")
    out_json = os.path.join(out_dir, "page.json")
    proc = subprocess.run([sys.executable, MODULE, "--out", out_html,
                           "--json-out", out_json], capture_output=True)
    cli_equal = False
    if proc.returncode == 0:
        with open(out_html, "rb") as fh:
            cli_html = fh.read()
        with open(out_json, "rb") as fh:
            cli_json = fh.read()
        cli_equal = cli_html == html_shipped and cli_json == json_shipped
    record("AC-MFPR3",
           html_now == html_shipped and json_now == json_shipped
           and same_dict and proc.returncode == 0 and cli_equal,
           "html_bytes=%d json_bytes=%d inproc_equal=%s twin_dict=%s "
           "cli_equal=%s"
           % (len(html_shipped), len(json_shipped),
              html_now == html_shipped and json_now == json_shipped,
              same_dict, cli_equal))


def check_read_shape_kept():
    detail = ""
    code = ""
    try:
        M.load_copy(write_copy_variant([{"title": "x"}], "read-list"))
    except M.CopyError as exc:
        code, detail = exc.code, exc.detail
    except Exception:  # noqa: BLE001 - a bare crash is not a named refusal
        pass
    list_ok = code == "E_MFP_COPY" and "list" in detail
    copy = dict(M.load_copy())
    copy["r3196_unread_key"] = "tolerated"
    tolerated = True
    try:
        M.load_copy(write_copy_variant(copy, "read-extra"))
    except Exception:  # noqa: BLE001 - an extra key must not be refused
        tolerated = False
    dropped = dict(M.load_copy())
    del dropped["footer_note"]
    key_named = False
    try:
        M.load_copy(write_copy_variant(dropped, "read-drop"))
    except M.CopyError as exc:
        key_named = exc.code == "E_MFP_COPY" and "footer_note" in exc.detail
    except Exception:  # noqa: BLE001 - the key law must still refuse
        pass
    record("AC-MFPR4", list_ok and tolerated and key_named,
           "list_refused=%s extra_tolerated=%s key_named=%s"
           % (list_ok, tolerated, key_named))


def check_read_wiring():
    with open(MODULE, "rb") as fh:
        raw = fh.read()
    try:
        raw.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        ascii_ok = False
    with io.open(MODULE, "r", encoding="utf-8") as fh:
        source = fh.read()
    read_sites = source.count("read_copy_file(")
    with io.open(RECONCILE, "r", encoding="utf-8") as fh:
        text = fh.read()
    label_hits = text.count('"%s"' % LABEL)
    file_hits = text.count("test_monthly_faces_preview.py")
    declared = registry_declared(text)
    total_after = len(RESULTS) + 1
    ok = (ascii_ok and read_sites == 2 and label_hits == 1
          and file_hits == 1 and declared == DECLARED)
    record("AC-MFPR5", ok,
           "module_ascii=%s read_sites=%d label_hits=%d file_hits=%d "
           "declared=%d recorded=%d law=%d"
           % (ascii_ok, read_sites, label_hits, file_hits, declared,
              total_after, DECLARED))


def _boom_factory(name):
    def boom(*_args, **_kwargs):
        raise RuntimeError("injected %s failure" % name)
    return boom


def _leftovers(directory):
    return sorted(name for name in os.listdir(directory)
                  if name.startswith(".mfp-write-"))


def _write_target(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def check_write_render_failure():
    """AC-MFPW1: a render-time failure leaves the delivered files alone."""
    faces = M.collect(temp_root("write-render-world"))
    copy = M.load_copy()
    problems = []
    for attr in ("render_html", "render_json"):
        for world in ("stale", "fresh"):
            root = temp_root("write-render-%s-%s" % (attr, world))
            out_html = os.path.join(root, "page.html")
            out_json = os.path.join(root, "page.json")
            stale = ("OLD PAGE " * 100, '{"old": true}\n')
            if world == "stale":
                _write_target(out_html, stale[0])
                _write_target(out_json, stale[1])
            original = getattr(M, attr)
            setattr(M, attr, _boom_factory(attr))
            raised = True
            caught = None
            try:
                M.write_outputs(faces, copy, out_html, out_json)
                raised = False
            except M.WriteError as exc:
                caught = exc
            except Exception as exc:  # noqa: BLE001 - wrong type is a bug
                problems.append("%s.%s.raised=%s"
                                % (attr, world, type(exc).__name__))
                raised = True
            finally:
                setattr(M, attr, original)
            if not raised:
                problems.append("%s.%s.no-exception" % (attr, world))
            if caught is not None:
                if caught.stage != "render":
                    problems.append("%s.%s.stage=%s"
                                    % (attr, world, caught.stage))
                if not caught.detail.startswith("RuntimeError:"):
                    problems.append("%s.%s.detail=%s"
                                    % (attr, world, caught.detail[:24]))
            if world == "stale":
                for target, text in ((out_html, stale[0]),
                                     (out_json, stale[1])):
                    with io.open(target, "r", encoding="utf-8") as fh:
                        now = fh.read()
                    if now != text:
                        problems.append("%s.%s.truncated=%d"
                                        % (attr, world, len(now)))
            else:
                for target in (out_html, out_json):
                    if os.path.exists(target):
                        problems.append("%s.%s.stray" % (attr, world))
            if _leftovers(root):
                problems.append("%s.%s.temp=%s"
                                % (attr, world, ",".join(_leftovers(root))))
    record("AC-MFPW1", not problems,
           "cases=4 problems=%s" % (",".join(problems) or "none"))


def check_write_no_half():
    """AC-MFPW2: a failure at the second stage does not swap the first."""
    faces = M.collect(temp_root("write-half-world"))
    copy = M.load_copy()
    root = temp_root("write-half")
    out_html = os.path.join(root, "page.html")
    out_json = os.path.join(root, "page.json")
    _write_target(out_html, "OLD PAGE " * 100)
    _write_target(out_json, '{"old": true}\n')
    with open(out_html, "rb") as fh:
        html_before = fh.read()
    with open(out_json, "rb") as fh:
        json_before = fh.read()
    original = M._stage
    calls = {"n": 0}

    def flaky(path, text):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("injected second stage failure")
        return original(path, text)

    M._stage = flaky
    raised = True
    caught = None
    try:
        M.write_outputs(faces, copy, out_html, out_json)
        raised = False
    except M.WriteError as exc:
        caught = exc
    finally:
        M._stage = original
    with open(out_html, "rb") as fh:
        html_after = fh.read()
    with open(out_json, "rb") as fh:
        json_after = fh.read()
    stage_ok = caught is not None and caught.stage == "stage"
    record("AC-MFPW2",
           raised and stage_ok
           and html_after == html_before and json_after == json_before
           and not _leftovers(root),
           "raised=%s stage=%s html_kept=%s json_kept=%s temps=%d stages=%d"
           % (raised, caught.stage if caught is not None else "-",
              html_after == html_before,
              json_after == json_before, len(_leftovers(root)),
              calls["n"]))


def check_write_replace_failure():
    """AC-MFPW3: a replace failure keeps the target bytes and cleans temps."""
    faces = M.collect(temp_root("write-replace-world"))
    copy = M.load_copy()
    root = temp_root("write-replace")
    out_html = os.path.join(root, "page.html")
    out_json = os.path.join(root, "page.json")
    _write_target(out_html, "OLD PAGE " * 100)
    _write_target(out_json, '{"old": true}\n')
    with open(out_html, "rb") as fh:
        html_before = fh.read()
    with open(out_json, "rb") as fh:
        json_before = fh.read()
    original = os.replace

    def refuse(_src, _dst):
        raise OSError("injected replace failure")

    os.replace = refuse
    raised = True
    caught = None
    try:
        M.write_outputs(faces, copy, out_html, out_json)
        raised = False
    except M.WriteError as exc:
        caught = exc
    finally:
        os.replace = original
    with open(out_html, "rb") as fh:
        html_after = fh.read()
    with open(out_json, "rb") as fh:
        json_after = fh.read()
    stage_ok = caught is not None and caught.stage == "replace"
    record("AC-MFPW3",
           raised and stage_ok
           and html_after == html_before and json_after == json_before
           and not _leftovers(root),
           "raised=%s stage=%s html_kept=%s json_kept=%s temps=%d"
           % (raised, caught.stage if caught is not None else "-",
              html_after == html_before, json_after == json_before,
              len(_leftovers(root))))


def check_write_bytes():
    """AC-MFPW4: the healthy bytes do not move, in process or through the CLI."""
    faces = M.collect(temp_root("write-bytes-world"))
    copy = M.load_copy()
    root = temp_root("write-bytes")
    out_html = os.path.join(root, "page.html")
    out_json = os.path.join(root, "page.json")
    M.write_outputs(faces, copy, out_html, out_json)
    with open(M.OUT_HTML, "rb") as fh:
        html_shipped = fh.read()
    with open(M.OUT_JSON, "rb") as fh:
        json_shipped = fh.read()
    with open(out_html, "rb") as fh:
        html_now = fh.read()
    with open(out_json, "rb") as fh:
        json_now = fh.read()
    cli_root = temp_root("write-bytes-cli")
    cli_html = os.path.join(cli_root, "page.html")
    cli_json = os.path.join(cli_root, "page.json")
    proc = subprocess.run([sys.executable, MODULE, "--out", cli_html,
                           "--json-out", cli_json], capture_output=True)
    cli_equal = False
    if proc.returncode == 0:
        with open(cli_html, "rb") as fh:
            cli_html_bytes = fh.read()
        with open(cli_json, "rb") as fh:
            cli_json_bytes = fh.read()
        cli_equal = (cli_html_bytes == html_shipped
                     and cli_json_bytes == json_shipped)
    record("AC-MFPW4",
           html_now == html_shipped and json_now == json_shipped
           and proc.returncode == 0 and cli_equal,
           "html_bytes=%d json_bytes=%d inproc_equal=%s cli_equal=%s"
           % (len(html_shipped), len(json_shipped),
              html_now == html_shipped and json_now == json_shipped,
              cli_equal))


WRITE_DRIVER = '''import os, sys
BASE = sys.argv[1]
sys.path.insert(0, os.path.join(BASE, "src", "sandbox", "ledger"))
import monthly_faces_preview as M
which = sys.argv[2]
def boom(name):
    def inner(*_a, **_k):
        raise RuntimeError("injected %s failure" % name)
    return inner
if which == "html":
    M.render_html = boom("render_html")
elif which == "json":
    M.render_json = boom("render_json")
elif which == "stage":
    M._stage = boom("_stage")
else:
    def refuse(_src, _dst):
        raise OSError("injected replace failure")
    M.os.replace = refuse
raise SystemExit(M.main(["--out", sys.argv[3], "--json-out", sys.argv[4]]))
'''

WRITE_CASES = ("html", "json", "stage", "replace")


def _run_write_case(which, tag):
    """Run one failing stage through the CLI in a world with old bytes.

    Returns (returncode, stdout_bytes, stderr_bytes, kept, leftovers,
    html_before, html_after)."""
    root = temp_root(tag)
    driver = os.path.join(root, "driver.py")
    _write_target(driver, WRITE_DRIVER)
    world = temp_root(tag + "-world")
    out_html = os.path.join(world, "page.html")
    out_json = os.path.join(world, "page.json")
    _write_target(out_html, "OLD PAGE " * 50)
    _write_target(out_json, '{"old": true}\n')
    with open(out_html, "rb") as fh:
        html_before = fh.read()
    with open(out_json, "rb") as fh:
        json_before = fh.read()
    proc = subprocess.run([sys.executable, driver, BASE, which,
                           out_html, out_json], capture_output=True)
    with open(out_html, "rb") as fh:
        html_after = fh.read()
    with open(out_json, "rb") as fh:
        json_after = fh.read()
    return (proc.returncode, proc.stdout, proc.stderr,
            html_after == html_before and json_after == json_before,
            _leftovers(world))


def check_write_cli_face():
    """AC-MFPW5: the CLI answers a refused write in one named line."""
    problems = []
    for which in WRITE_CASES:
        rc, stdout, stderr, kept, temps = _run_write_case(
            which, "write-cli-face-" + which)
        if rc != 2:
            problems.append("%s.rc=%d" % (which, rc))
        lines = stdout.splitlines()
        if len(lines) != 1:
            problems.append("%s.stdout_lines=%d" % (which, len(lines)))
        elif b"E_MFP_WRITE" not in lines[0]:
            problems.append("%s.no-code" % which)
        if stderr != b"":
            problems.append("%s.stderr=%d" % (which, len(stderr)))
        if not kept:
            problems.append("%s.bytes-moved" % which)
        if temps:
            problems.append("%s.temp" % which)
    record("AC-MFPW5", not problems,
           "cases=%d problems=%s"
           % (len(WRITE_CASES), ",".join(problems) or "none"))


def check_write_named():
    """AC-MFPX1: render, stage and swap failures are one named family."""
    faces = M.collect(temp_root("write-named-world"))
    copy = M.load_copy()
    problems = []
    cases = (("render_html", "render", "RuntimeError"),
             ("render_json", "render", "RuntimeError"),
             ("_stage", "stage", "RuntimeError"),
             ("os.replace", "replace", "OSError"))
    for attr, stage, kind in cases:
        root = temp_root("write-named-" + attr.strip("_").replace(".", "-"))
        out_html = os.path.join(root, "page.html")
        out_json = os.path.join(root, "page.json")
        if attr == "os.replace":
            original = os.replace

            def refuse(_src, _dst):
                raise OSError("injected replace failure")

            os.replace = refuse
        else:
            original = getattr(M, attr)
            setattr(M, attr, _boom_factory(attr))
        caught = None
        other = None
        try:
            M.write_outputs(faces, copy, out_html, out_json)
        except M.WriteError as exc:
            caught = exc
        except Exception as exc:  # noqa: BLE001 - wrong type is a bug
            other = type(exc).__name__
        finally:
            if attr == "os.replace":
                os.replace = original
            else:
                setattr(M, attr, original)
        label = attr.replace(".", "-")
        if other is not None:
            problems.append("%s.raised=%s" % (label, other))
            continue
        if caught is None:
            problems.append("%s.no-exception" % label)
            continue
        if caught.code != "E_MFP_WRITE":
            problems.append("%s.code=%s" % (label, caught.code))
        if caught.stage != stage:
            problems.append("%s.stage=%s" % (label, caught.stage))
        if not caught.detail.startswith(kind + ":"):
            problems.append("%s.detail=%s" % (label, caught.detail[:24]))
        if caught.__cause__ is None:
            problems.append("%s.no-cause" % label)
        elif type(caught.__cause__).__name__ != kind:
            problems.append("%s.cause=%s"
                            % (label, type(caught.__cause__).__name__))
        if _leftovers(root):
            problems.append("%s.temp" % label)
    control = temp_root("write-named-control")
    control_html = os.path.join(control, "page.html")
    control_json = os.path.join(control, "page.json")
    try:
        M.write_outputs(faces, copy, control_html, control_json)
        healthy_ok = (os.path.isfile(control_html)
                      and os.path.isfile(control_json)
                      and not _leftovers(control))
    except Exception as exc:  # noqa: BLE001 - a healthy world must not raise
        healthy_ok = False
        problems.append("control.raised=%s" % type(exc).__name__)
    record("AC-MFPX1", not problems,
           "cases=%d control=%s problems=%s"
           % (len(cases), healthy_ok, ",".join(problems) or "none"))


def check_write_named_cli():
    """AC-MFPX2: each CLI refusal names the stage that actually failed."""
    expected = {"html": "render", "json": "render",
                "stage": "stage", "replace": "replace"}
    problems = []
    for which in WRITE_CASES:
        rc, stdout, stderr, _kept, _temps = _run_write_case(
            which, "write-named-cli-" + which)
        line = stdout.decode("utf-8", "replace").strip()
        want = "stage=%s" % expected[which]
        if rc != 2:
            problems.append("%s.rc=%d" % (which, rc))
        if want not in line:
            problems.append("%s.line=%s" % (which, line[:60] or "-"))
        if stderr != b"":
            problems.append("%s.stderr=%d" % (which, len(stderr)))
    record("AC-MFPX2", not problems,
           "cases=%d problems=%s"
           % (len(WRITE_CASES), ",".join(problems) or "none"))


def check_write_wiring():
    with open(MODULE, "rb") as fh:
        raw = fh.read()
    try:
        raw.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        ascii_ok = False
    with io.open(MODULE, "r", encoding="utf-8") as fh:
        source = fh.read()
    replace_sites = source.count("os.replace(")
    named_sites = source.count("_write_error(")
    caught_sites = source.count("except WriteError as exc:")
    world_sites = source.count("raise WorldError(")
    world_caught = source.count("except WorldError as exc:")
    stage_sites = tuple(source.count('_write_error("%s",' % stage)
                        for stage in ("render", "stage", "replace"))
    body_start = source.find("def write_outputs(")
    body = source[body_start:] if body_start >= 0 else ""
    log_start = source.find("def write_log(")
    log_body = (source[log_start:body_start]
                if 0 <= log_start < body_start else "")
    replace_in_outputs = body.count("os.replace(")
    replace_in_log = log_body.count("os.replace(")
    render_at = body.find("render_html(")
    json_at = body.find("render_json(")
    stage_at = body.find("_stage(")
    ordered = (body_start >= 0 and render_at >= 0 and json_at >= 0
               and stage_at >= 0 and render_at < stage_at
               and json_at < stage_at)
    with io.open(RECONCILE, "r", encoding="utf-8") as fh:
        text = fh.read()
    label_hits = text.count('"%s"' % LABEL)
    file_hits = text.count("test_monthly_faces_preview.py")
    declared = registry_declared(text)
    total_after = len(RESULTS) + 1
    ok = (ascii_ok and replace_sites == 2 and ordered
          and replace_in_outputs == 1 and replace_in_log == 1
          and named_sites == 4 and caught_sites == 2
          and world_sites == 1 and world_caught == 2
          and stage_sites == (1, 1, 1)
          and label_hits == 1 and file_hits == 1 and declared == DECLARED
          and total_after == DECLARED)
    record("AC-MFPW6", ok,
           "module_ascii=%s replace_sites=%d swaps=%d+%d "
           "render_before_stage=%s named_sites=%d caught=%d "
           "world=%d/%d stages=%s "
           "label_hits=%d file_hits=%d declared=%d recorded=%d law=%d"
           % (ascii_ok, replace_sites, replace_in_outputs, replace_in_log,
              ordered, named_sites, caught_sites, world_sites, world_caught,
              ",".join(str(n) for n in stage_sites),
              label_hits, file_hits, declared, total_after, DECLARED))


def _call_main(argv):
    """Call M.main with stdout captured; returns (rc, text)."""
    buf = io.StringIO()
    real = sys.stdout
    sys.stdout = buf
    try:
        rc = M.main(argv)
    finally:
        sys.stdout = real
    return rc, buf.getvalue()


def check_world_named():
    """AC-MFPX3: a demo world that cannot be built is one named code."""
    problems = []
    original = M.collect

    def boom(_tmp):
        raise RuntimeError("injected build failure")

    M.collect = boom
    caught = None
    other = None
    try:
        M.build_world(temp_root("world-named"))
    except M.WorldError as exc:
        caught = exc
    except Exception as exc:  # noqa: BLE001 - a wrong type is a bug
        other = type(exc).__name__
    finally:
        M.collect = original
    if other is not None:
        problems.append("raised=%s" % other)
    elif caught is None:
        problems.append("no-exception")
    else:
        if caught.code != "E_MFP_WORLD":
            problems.append("code=%s" % caught.code)
        if not caught.detail.startswith("RuntimeError:"):
            problems.append("detail=%s" % caught.detail[:24])
        if caught.__cause__ is None:
            problems.append("no-cause")
        elif type(caught.__cause__).__name__ != "RuntimeError":
            problems.append("cause=%s" % type(caught.__cause__).__name__)
    control_ok = False
    try:
        control = M.build_world(temp_root("world-named-control"))
        control_ok = isinstance(control, list) and len(control) == len(M.FACES)
    except Exception as exc:  # noqa: BLE001 - a healthy world must not raise
        problems.append("control.raised=%s" % type(exc).__name__)
    record("AC-MFPX3", not problems,
           "cases=1 control=%s problems=%s"
           % (control_ok, ",".join(problems) or "none"))


def check_log_atomic_cli():
    """AC-MFPX4: the log is swapped in, and a bad path still hands over
    the whole verify text instead of throwing it away."""
    problems = []
    root = temp_root("log-atomic-healthy")
    healthy_log = os.path.join(root, "verify.log")
    proc = subprocess.run(
        [sys.executable, MODULE, "--verify", "--log", healthy_log],
        capture_output=True, cwd=BASE)
    healthy = proc.stdout
    healthy_ok = (proc.returncode == 0 and proc.stderr == b"" and healthy != b""
                  and os.path.isfile(healthy_log))
    if healthy_ok:
        with open(healthy_log, "rb") as fh:
            logged = fh.read()
        # stdout goes through the Windows newline translation, the file is
        # written in the canonical utf-8/lf dialect qa_log.py --check reads.
        healthy_ok = (logged.splitlines() == healthy.splitlines()
                      and b"\r" not in logged)
    if not healthy_ok:
        problems.append("healthy")
    if _leftovers(root):
        problems.append("healthy.temp")

    bad_root = temp_root("log-atomic-dir")
    logdir = os.path.join(bad_root, "logdir")
    os.mkdir(logdir)
    proc = subprocess.run(
        [sys.executable, MODULE, "--verify", "--log", logdir],
        capture_output=True, cwd=BASE)
    tail = proc.stdout[len(healthy):]
    if proc.returncode != 2:
        problems.append("dir.rc=%d" % proc.returncode)
    if healthy != b"" and not proc.stdout.startswith(healthy):
        problems.append("dir.text-lost")
    if tail.count(b"\n") != 1 or b"E_MFP_LOG" not in tail:
        problems.append("dir.refusal=%r" % tail[:48])
    if proc.stderr != b"":
        problems.append("dir.stderr=%d" % len(proc.stderr))
    if not os.path.isdir(logdir):
        problems.append("dir.moved")
    if _leftovers(bad_root):
        problems.append("dir.temp")

    miss_root = temp_root("log-atomic-missing")
    miss_log = os.path.join(miss_root, "nodir", "verify.log")
    proc = subprocess.run(
        [sys.executable, MODULE, "--verify", "--log", miss_log],
        capture_output=True, cwd=BASE)
    if proc.returncode != 0:
        problems.append("missing.rc=%d" % proc.returncode)
    if not os.path.isfile(miss_log):
        problems.append("missing.no-log")
    else:
        with open(miss_log, "rb") as fh:
            logged = fh.read()
        if logged.splitlines() != proc.stdout.splitlines():
            problems.append("missing.log!=stdout")
    record("AC-MFPX4", not problems,
           "healthy=%s cases=3 problems=%s"
           % (healthy_ok, ",".join(problems) or "none"))


def check_verify_evidence():
    """AC-MFPX5: a --verify that cannot build its world still leaves the
    evidence file it was asked for, carrying the named refusal."""
    problems = []
    root = temp_root("verify-evidence")
    log = os.path.join(root, "verify.log")
    original = M.collect

    def boom(_tmp):
        raise RuntimeError("injected build failure")

    M.collect = boom
    try:
        rc, text = _call_main(["--verify", "--log", log])
    finally:
        M.collect = original
    exists = os.path.isfile(log)
    body = io.open(log, encoding="utf-8").read() if exists else ""
    if rc != 2:
        problems.append("rc=%r" % (rc,))
    if not exists:
        problems.append("log-missing")
    if "VERIFY FAIL problems=1" not in body:
        problems.append("no-fail-line")
    if "E_MFP_WORLD" not in body:
        problems.append("no-code")
    if body != text:
        problems.append("log!=stdout")
    if _leftovers(root):
        problems.append("temp")
    record("AC-MFPX5", not problems,
           "rc=%r exists=%s bytes=%d problems=%s"
           % (rc, exists, len(body.encode("utf-8")),
              ",".join(problems) or "none"))


def check_log_readback():
    """AC-MFPX6: the swapped-in log proves itself by reading back."""
    problems = []
    text = "VERIFY PASS criteria=AC-MFR1..AC-MFR8 (probe)\nsecond line\n"
    want = text.encode("utf-8")

    def land(which, only):
        real = os.replace

        def shim(src, dst):
            if os.path.abspath(dst) != os.path.abspath(only):
                return real(src, dst)
            with io.open(src, "rb") as fh:
                payload = fh.read()
            if which == "truncated":
                payload = payload[: max(1, len(payload) // 2)]
            elif which == "crlf":
                payload = payload.replace(b"\n", b"\r\n")
            with io.open(dst, "wb") as fh:
                fh.write(payload)
            try:
                os.remove(src)
            except OSError:
                pass

        return shim

    root = temp_root("readback-healthy")
    target = os.path.join(root, "verify.log")
    proof = M.write_log(target, text)
    landed = io.open(target, "rb").read()
    if landed != want:
        problems.append("healthy.bytes=%d" % len(landed))
    if (proof.get("bytes") != len(want)
            or proof.get("sha256") != sha16_bytes(want)
            or proof.get("lines") != 2):
        problems.append("healthy.proof=%r" % (proof,))
    if _leftovers(root):
        problems.append("healthy.temp")

    shapes = {}
    kept = {}
    for which in ("truncated", "crlf"):
        root = temp_root("readback-%s" % which)
        target = os.path.join(root, "verify.log")
        real = os.replace
        os.replace = land(which, target)
        caught = None
        try:
            M.write_log(target, text)
        except M.LogError as exc:
            caught = exc
        except Exception as exc:  # noqa: BLE001 - a wrong type is a bug
            shapes[which] = "raised=%s" % type(exc).__name__
            continue
        finally:
            os.replace = real
        on_disk = io.open(target, "rb").read() if os.path.isfile(target) else b""
        kept[which] = len(on_disk)
        if caught is None:
            shapes[which] = "no-refusal"
            continue
        detail = caught.detail
        ok = (caught.code == "E_MFP_LOG" and caught.stage == "read-back"
              and "landed" in detail and "intended" in detail
              and ("landed %d bytes" % len(on_disk)) in detail
              and isinstance(caught.__cause__, ValueError))
        if not ok:
            shapes[which] = "code=%s stage=%s detail=%s" % (
                caught.code, caught.stage, detail[:64])
        if on_disk == want:
            shapes[which] = "disk-matches"
        if not os.path.isfile(target):
            shapes[which] = "disk-missing"
    if shapes:
        problems.append("shapes=%s" % json.dumps(shapes, sort_keys=True))

    root = temp_root("readback-cli")
    target = os.path.join(root, "verify.log")
    rc0, text0 = _call_main(["--verify", "--log", target])
    if rc0 != 0 or not text0:
        problems.append("cli.control=%r/%d" % (rc0, len(text0)))
    real = os.replace
    os.replace = land("truncated", target)
    try:
        rc, printed = _call_main(["--verify", "--log", target])
    finally:
        os.replace = real
    if rc != 2:
        problems.append("cli.rc=%r" % (rc,))
    if printed.count("E_MFP_LOG stage=read-back") != 1:
        problems.append("cli.refusals=%d" % printed.count("E_MFP_LOG"))
    if text0 and not printed.startswith(text0):
        problems.append("cli.text-lost")
    cli_disk = io.open(target, "rb").read() if os.path.isfile(target) else b""
    if cli_disk == printed.encode("utf-8"):
        problems.append("cli.disk-matches")

    root = temp_root("readback-census")
    target = os.path.join(root, "preview-monthly-faces-R9999.log")
    M.write_log(target, text)
    proc = subprocess.run([sys.executable,
                           os.path.join(BASE, "src", "os",
                                        "qa_writer_census.py"),
                           "--dir", root],
                          capture_output=True, cwd=BASE)
    census = proc.stdout.decode("utf-8", "replace")
    if proc.returncode != 0 or "[tee]" not in census:
        problems.append("census.rc=%d tee=%s"
                        % (proc.returncode, "[tee]" in census))

    with open(MODULE, "rb") as fh:
        raw = fh.read()
    try:
        raw.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        ascii_ok = False
    with io.open(MODULE, "r", encoding="utf-8") as fh:
        source = fh.read()
    log_start = source.find("def verify_log(")
    log_end = source.find("def write_log(")
    proof_body = source[log_start:log_end] if 0 <= log_start < log_end else ""
    site_ok = (proof_body.count('io.open(path, "rb")') == 1
               and source.count('_log_error("read-back", exc)') == 1)
    if not (ascii_ok and site_ok):
        problems.append("hygiene=ascii:%s sites:%s" % (ascii_ok, site_ok))
    record("AC-MFPX6", not problems,
           "kept=%s cli_disk=%d census_tee=%s ascii=%s sites=%s "
           "problems=%s"
           % (json.dumps(kept, sort_keys=True), len(cli_disk),
              "[tee]" in census, ascii_ok, site_ok,
              ",".join(problems) or "none"))


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
        check_copy_keys()
        check_copy_refusal()
        check_copy_cli()
        check_copy_bytes()
        check_copy_shape()
        check_copy_wiring()
        check_read_refusal()
        check_read_cli()
        check_read_bytes()
        check_read_shape_kept()
        check_read_wiring()
        check_write_render_failure()
        check_write_no_half()
        check_write_replace_failure()
        check_write_bytes()
        check_write_cli_face()
        check_write_named()
        check_write_named_cli()
        check_world_named()
        check_log_atomic_cli()
        check_verify_evidence()
        check_log_readback()
        check_write_wiring()
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
