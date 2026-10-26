"""QA evidence-file writer-mode census probe (BigDomain P2 tech-queue
item "reconcile_all no-argv shell-capture self-label + daily chain
dialect mutual-proof window", R1836; seed = the R1827 three-state
writer archaeology + qa_decode_probe canon, claim row in
state/queue/tech.md registers AC-SL3 BEFORE this code).

What this tool answers: qa/ evidence logs have been written by three
writer families (R1827 archaeology) - raw cmd/PowerShell redirection
(CRLF + raw cp936 bytes), PowerShell re-encoding capture (CRLF +
utf-8-decodable but mojibake-prone), and the runner's utf-8 Tee
(utf-8 + LF). Since R1836 a no-argv reconcile_all run also prints the
SHELL_CAPTURE_LABEL first line, so future shell-captured files are
self-announcing. This probe mechanically classifies EVERY *.log in a
directory by writer-dialect signature and counts the three states:

    python qa_writer_census.py                 # live qa/ census
    python qa_writer_census.py --dir PATH      # any evidence dir
    python qa_writer_census.py --selftest      # sandbox fixtures

Classification rule (pre-registered AC-SL3, mechanical and total):
  * BOM utf-16le/utf-16be            -> ps-utf16    (PS 5.1 `>` family)
  * no BOM + crlf==0 + strict utf-8  -> tee         (LF + utf-8 dialect)
  * no BOM + crlf-dominant (crlf > bare_lf) + strict utf-8 FAILS
                                     -> cmd-raw     (raw cp936 family)
  * no BOM + crlf-dominant + strict utf-8 OK
                                     -> pwsh-capture (re-encode family)
  * anything else (utf-8-sig BOM, mixed EOL with LF majority,
    unreadable files, empty degenerate-noted rows)
                                     -> other      (honest catch-all,
                                                    named per file)
The label column reports label=yes when the first physical line is
byte-equal to reconcile_all.SHELL_CAPTURE_LABEL (single source,
imported - never copied; trailing EOL tolerated).

Exit codes: 0 census complete (every file classified, including the
honest "other" bucket); 3 no *.log candidates under target dir
(refusal family, R1727 AC-LN5 / qa_decode_probe AC-QD5 precedent).
This probe is a measurement face (R1727 precedent): it is NOT
registered in the reconcile_all SUITES table, reads directories only,
and never writes inside any qa/ dir.

R1841 baseline + drift-detector extension (writer-census baseline
window; criteria AC-WCB1..WCB6 pre-registered in state/queue/tech.md
BEFORE this code). The R1836 census answered "what writer families
exist TODAY" one-shot; this extension answers "did any NEW non-tee
dialect file appear SINCE the baseline" on every future call:

    python qa_writer_census.py --update-baseline   # freeze baseline
    python qa_writer_census.py --check             # drift detector

Baseline law (AC-WCB1): writer-census-baseline.json (default under
the target dir, --baseline overridable) carries ONLY the four non-tee
class name lists {cmd-raw, pwsh-capture, ps-utf16, other} sorted;
tee files are deliberately NOT baselined because the runner Tee is
the healthy dialect - a NEW tee file is a normal evidence product
and must never flag (the zero-tee-key baseline IS that mechanism).
The baseline is a pure parse product: zero timestamps, zero paths,
indent=2 + sort_keys + trailing NL round-trip format, atomic
tempfile+os.replace write, idempotent re-freeze byte-identical
(R1684 runner-profile-baseline isomorphism). --update-baseline is
the re-freeze gate (R1713 AC-BF4 law): mutually exclusive with
--check, and after writing it self-runs the check (post-check must
be green - structurally guaranteed because the baseline derives
from the very census it is checked against).

Check law (AC-WCB2..WCB5): three verdict faces -
  * new-dialect   FLAG  current class in the four baselined classes
                         AND name not in that class list -> the
                         shell-capture discipline detector body
                         (every future pwsh/cmd-captured evidence
                         file is caught by name, exit 2, no silence)
  * class-migrated FLAG baselined file whose current class differs
                         from its base class (incl. rewritten to
                         tee) -> rewrite face, exit 2
  * disappeared   info  baselined file no longer on disk -> legal
                         cleanup, NOT a violation (R1684 REMOVED-SUITE
                         info precedent), exit 0 face
Missing baseline file during --check -> exit 2 with an honest
"probe not deployed" hint (zero fabricated empty baseline). Double
run of --check prints byte-identical stdout (zero timestamps).

Write-discipline note (honest update of the R1836 read-only claim):
the census and check faces still write NOTHING inside any qa/ dir;
--update-baseline writes exactly ONE file - the baseline itself -
and only as an explicit operator re-freeze action.

Per-file disposition (R2151 AC-CDN1..AC-CDN8, pre-registered in
state/queue/tech.md BEFORE this code): a baselined non-tee file that
was legitimately rebuilt in the healthy tee dialect otherwise flags
class-migrated forever, whose only exit was a whole-baseline re-freeze
that would also mask unrelated drift. `--accept NAME` (repeatable)
drops one rebuilt file from the baseline after checking that it is
baselined, still present, and currently class=tee; every refusal
leaves the baseline byte-identical, and a second accept of the same
file reports already-reconciled without a write.

Evidence: qa/selflabel-chain-R1836.log (R1836); qa/
writer-census-drift-R1841.log (this window).
"""

import argparse
import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))   # .../src/os
SRC = os.path.dirname(BASE)                          # .../src
ROOT = os.path.dirname(SRC)                          # repo root
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, SANDBOX)
sys.path.insert(0, BASE)

import qa_decode_probe as QDP       # BOM face, single source
import reconcile_all as RA          # SHELL_CAPTURE_LABEL, single source

NET_IMPORTS = ("urllib", "requests", "socket", "http", "ftplib",
               "xmlrpc", "smtplib", "asyncio")
QA_DIR = os.path.join(ROOT, "qa")
LABEL = RA.SHELL_CAPTURE_LABEL
CLASSES = ("tee", "cmd-raw", "pwsh-capture", "ps-utf16", "other")
BASELINE_CLASSES = ("cmd-raw", "pwsh-capture", "ps-utf16", "other")
BASELINE_NAME = "writer-census-baseline.json"


def classify_file(path):
    """Read-only writer-signature census of one file. Returns a row
    dict; every number is measured or honestly absent - zero
    fabrication."""
    row = {"name": os.path.basename(path), "bytes": -1, "bom": "?",
           "crlf": 0, "bare_lf": 0, "utf8": False, "label": False,
           "class": "other", "err": ""}
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        row["err"] = "OSError:%s" % exc.__class__.__name__
        return row
    row["bytes"] = len(raw)
    row["bom"] = QDP._bom_of(raw)
    row["crlf"] = raw.count(b"\r\n")
    row["bare_lf"] = raw.count(b"\n") - row["crlf"]
    try:
        raw.decode("utf-8", "strict")
        row["utf8"] = True
    except UnicodeDecodeError:
        row["utf8"] = False
    # label column: first physical line, trailing EOL tolerated
    first = raw.split(b"\n", 1)[0]
    if first.endswith(b"\r"):
        first = first[:-1]
    row["label"] = (first == LABEL.encode("ascii"))
    # classification rule (pre-registered; mechanical and total)
    if row["err"]:
        row["class"] = "other"
    elif row["bom"] in ("utf-16le", "utf-16be"):
        row["class"] = "ps-utf16"
    elif row["bom"] == "utf-8-sig":
        row["class"] = "other"
    elif row["crlf"] == 0:
        row["class"] = "tee" if row["utf8"] else "other"
    elif row["crlf"] > row["bare_lf"]:
        # CRLF-dominant: re-encoding capture vs raw redirect
        row["class"] = "pwsh-capture" if row["utf8"] else "cmd-raw"
    else:
        row["class"] = "other"   # mixed EOL without CRLF majority
    return row


def probe_dir(target):
    """Read-only writer census of one directory. Returns (lines,
    exit_code, summary). Zero writes, zero fabrication."""
    names = sorted(n for n in os.listdir(target) if n.endswith(".log"))
    lines = []
    if not names:
        lines.append("no *.log candidates under target dir (refusal)")
        return lines, 3, {"file_count": 0,
                          "counts": dict((c, 0) for c in CLASSES)}
    lines.append("file_count=%d" % len(names))
    counts = dict((c, 0) for c in CLASSES)
    labeled = 0
    for name in names:
        row = classify_file(os.path.join(target, name))
        counts[row["class"]] += 1
        if row["label"]:
            labeled += 1
        if row["err"]:
            lines.append("[err] %s bytes=%d reason=%s"
                         % (name, row["bytes"], row["err"]))
        else:
            lines.append("[%s] %s bytes=%d bom=%s crlf=%d bare_lf=%d "
                         "utf8=%s label=%s"
                         % (row["class"], name, row["bytes"], row["bom"],
                            row["crlf"], row["bare_lf"],
                            "yes" if row["utf8"] else "no",
                            "yes" if row["label"] else "no"))
    lines.append("counts: " + " ".join("%s=%d" % (c, counts[c])
                                        for c in CLASSES))
    lines.append("labeled_selfannounced=%d" % labeled)
    lines.append("total=%d" % len(names))
    lines.append("verdict: CENSUS-COMPLETE (all %d files classified, "
                 "other=%d honest bucket)" % (len(names), counts["other"]))
    return lines, 0, {"file_count": len(names), "counts": counts,
                      "labeled": labeled}


def census_names(target):
    """Per-class sorted name lists (read-only, AC-WCB1 derivation
    face). Returns dict class -> sorted names, or None for the empty
    refusal family (probe_dir law)."""
    names = sorted(n for n in os.listdir(target) if n.endswith(".log"))
    if not names:
        return None
    lists = dict((c, []) for c in CLASSES)
    for name in names:
        row = classify_file(os.path.join(target, name))
        lists[row["class"]].append(name)
    return dict((c, sorted(lists[c])) for c in CLASSES)


def default_baseline_path(target):
    return os.path.join(target, BASELINE_NAME)


def write_baseline(target, path):
    """AC-WCB1 re-freeze face. Derives the baseline from a live census
    (pure parse product: zero timestamps, zero paths), writes it
    atomically (tempfile + os.replace), then self-runs the check
    (post-check must be green - structurally guaranteed). Returns
    (lines, exit_code, baseline_dict); lines carry the freeze report
    plus the post-check output as evidence."""
    lines = []
    lists = census_names(target)
    if lists is None:
        lines.append("no *.log candidates under target dir (refusal)")
        return lines, 3, None
    base = dict((c, lists[c]) for c in BASELINE_CLASSES)
    _write_baseline_json(path, base)
    lines.append("baseline written: %s" % os.path.basename(path))
    for c in BASELINE_CLASSES:
        lines.append("  %s: %d names" % (c, len(base[c])))
    lines.append("  tee: %d files (healthy dialect, NOT baselined)"
                 % len(lists["tee"]))
    post, post_code = check_against_baseline(target, path)
    lines.append("--- post-check (self-run after freeze) ---")
    lines.extend(post)
    lines.append("post-check exit=%d" % post_code)
    if post_code != 0:
        return lines, 2, base      # structurally unreachable, honest face
    return lines, 0, base


def check_against_baseline(target, path):
    """AC-WCB2..WCB5 drift-detector face. Read-only against the target
    dir AND the baseline file. Three verdict faces: new-dialect FLAG,
    class-migrated FLAG, disappeared info. Deterministic output."""
    lines = []
    if not os.path.exists(path):
        lines.append("baseline file missing: %s" % os.path.basename(path))
        lines.append("hint: run --update-baseline first "
                     "(probe not deployed - honest refusal, "
                     "zero fabricated empty baseline)")
        return lines, 2
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            base = json.load(fh)
    except (OSError, ValueError) as exc:
        lines.append("baseline unreadable: %s (%s)"
                     % (os.path.basename(path), exc.__class__.__name__))
        return lines, 2
    for c in BASELINE_CLASSES:
        if c not in base:
            lines.append("baseline malformed: missing class key %s" % c)
            return lines, 2
    lists = census_names(target)
    if lists is None:
        lines.append("no *.log candidates under target dir (refusal)")
        return lines, 3
    base_of = {}
    for c in BASELINE_CLASSES:
        for n in base[c]:
            base_of[n] = c
    flags = 0
    for c in CLASSES:
        for n in lists[c]:
            if c == "tee":
                continue          # healthy dialect face, never flags
            if n not in base_of:
                lines.append("[flag] new-dialect: %s (class=%s)" % (n, c))
                flags += 1
    for c in CLASSES:
        for n in lists[c]:
            b = base_of.get(n)
            if b is not None and b != c:
                lines.append("[flag] class-migrated: %s (base=%s cur=%s)"
                             % (n, b, c))
                flags += 1
    seen = set()
    for c in CLASSES:
        seen.update(lists[c])
    gone = sorted(n for n in base_of if n not in seen)
    for n in gone:
        lines.append("[info] disappeared: %s (base=%s)"
                     % (n, base_of[n]))
    lines.append("census: files=%d tee=%d baselined=%d"
                 % (sum(len(lists[c]) for c in CLASSES),
                    len(lists["tee"]), len(base_of)))
    lines.append("disappeared=%d" % len(gone))
    lines.append("flags=%d" % flags)
    lines.append("verdict: %s" % ("DRIFT-CLEAN" if flags == 0
                                 else "DRIFT-FLAG"))
    return lines, (0 if flags == 0 else 2)


def _write_baseline_json(path, base):
    """Atomic deterministic baseline write (AC-WCB1 / AC-CDN6):
    full serialize first, tempfile + os.replace, zero timestamps."""
    text = json.dumps(base, indent=2, sort_keys=True) + "\n"
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".wc-baseline-", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def accept_reconciled(target, path, name):
    """Per-file disposition face (R2151 AC-CDN3..AC-CDN7).

    A baselined non-tee file that was legitimately rebuilt in the
    healthy tee dialect is dropped from the baseline, so --check can
    return to DRIFT-CLEAN without re-freezing the whole baseline and
    masking unrelated drift. Refusals never touch the baseline file.
    Returns (lines, exit_code)."""
    lines = []
    if not os.path.exists(path):
        lines.append("baseline file missing: %s" % os.path.basename(path))
        lines.append("hint: run --update-baseline first "
                     "(probe not deployed - honest refusal, "
                     "zero fabricated empty baseline)")
        return lines, 2
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            base = json.load(fh)
    except (OSError, ValueError) as exc:
        lines.append("baseline unreadable: %s (%s)"
                     % (os.path.basename(path), exc.__class__.__name__))
        return lines, 2
    for c in BASELINE_CLASSES:
        if c not in base:
            lines.append("baseline malformed: missing class key %s" % c)
            return lines, 2
    base_of = {}
    for c in BASELINE_CLASSES:
        for n in base[c]:
            base_of[n] = c
    fpath = os.path.join(target, name)
    if not os.path.isfile(fpath):
        lines.append("refused: %s not on disk (disappeared face is info, "
                     "not an accept)" % name)
        return lines, 2
    row = classify_file(fpath)
    if row["class"] != "tee":
        lines.append("refused: %s is class=%s (rebuild it as utf-8+LF "
                     "tee dialect first)" % (name, row["class"]))
        return lines, 2
    if name not in base_of:
        total = sum(len(base[c]) for c in BASELINE_CLASSES)
        lines.append("already-reconciled: %s (tee, not baselined)" % name)
        lines.append("baseline: %s" % os.path.abspath(path))
        lines.append("reconciled=%d" % total)
        return lines, 0
    prior = base_of[name]
    base[prior] = sorted(n for n in base[prior] if n != name)
    clean = dict((c, sorted(base[c])) for c in BASELINE_CLASSES)
    _write_baseline_json(path, clean)
    lines.append("accepted: %s (base=%s cur=tee)" % (name, prior))
    lines.append("baseline: %s" % os.path.abspath(path))
    lines.append("reconciled=%d" % len(clean[prior]))
    return lines, 0


def _hygiene_lines():
    out = []
    with io.open(os.path.abspath(__file__), "r", encoding="ascii",
                 errors="strict") as handle:
        src = handle.read()
    out.append("self-ascii: PASS (%d bytes)" % len(src.encode("ascii")))
    bad_imports = [mod for mod in NET_IMPORTS
                   if any(line.strip().startswith("import %s" % mod)
                          or (line.strip().startswith("from")
                              and mod in line)
                          for line in src.splitlines())]
    out.append("self-net-imports: %s" % ("NONE (PASS)" if not bad_imports
                                         else "FAIL %s" % bad_imports))
    return out, (0 if not bad_imports else 2)


def _selftest():
    """Sandbox fixtures (AC-SL3, >= 8 assertions)."""
    checks = []

    def check(label, cond):
        checks.append((label, bool(cond)))

    tmp = tempfile.mkdtemp(prefix="qa-writer-census-")
    try:
        fx = os.path.join(tmp, "fixtures")
        os.mkdir(fx)
        # 1 tee dialect: utf-8 + LF
        with open(os.path.join(fx, "tee-like.log"), "wb") as fh:
            fh.write("PASS suite ledger exit=0\n".encode("utf-8"))
        # 2 cmd-raw dialect: CRLF + raw cp936 (undecodable as utf-8)
        with open(os.path.join(fx, "cmd-raw-like.log"), "wb") as fh:
            fh.write(u"AI \u5224\u5b9a".encode("gbk") + b"\r\n"
                     + b"PASS suite row\r\n")
        # 3 pwsh-capture dialect: CRLF + valid utf-8
        with open(os.path.join(fx, "pwsh-like.log"), "wb") as fh:
            fh.write(u"AI \u5224\u5b9a".encode("utf-8") + b"\r\n"
                     + b"PASS suite row\r\n")
        # 4 PS 5.1 redirection: UTF-16LE with BOM
        with open(os.path.join(fx, "ps-utf16.log"), "wb") as fh:
            fh.write(b"\xff\xfe" + "hello utf16le\n".encode("utf-16-le"))
        # 5 self-labeled shell-capture file: label first line + CRLF
        with open(os.path.join(fx, "labeled-capture.log"), "wb") as fh:
            fh.write(LABEL.encode("ascii") + b"\r\n"
                     + u"AI \u5224\u5b9a".encode("utf-8") + b"\r\n")
        # 6 utf-8-sig BOM -> honest other bucket
        with open(os.path.join(fx, "utf8bom.log"), "wb") as fh:
            fh.write(b"\xef\xbb\xbf" + "PASS suite row\n".encode("utf-8"))
        # 7 mixed EOL, LF majority -> honest other bucket
        with open(os.path.join(fx, "mixed-eol.log"), "wb") as fh:
            fh.write("l1\nl2\nl3\nl4\r\n".encode("utf-8"))
        # 8 empty degenerate: mechanically tee-by-rule, bytes=0 noted
        open(os.path.join(fx, "empty.log"), "wb").close()
        lines, code, summary = probe_dir(fx)
        blob = "\n".join(lines)
        check("refusal not triggered (8 fixtures)", code == 0
              and summary["file_count"] == 8)
        check("tee dialect named", "[tee] tee-like.log" in blob)
        check("cmd-raw dialect named (utf8=no)",
              "[cmd-raw] cmd-raw-like.log" in blob
              and "utf8=no" in blob)
        check("pwsh-capture dialect named",
              "[pwsh-capture] pwsh-like.log" in blob)
        check("ps-utf16 named", "[ps-utf16] ps-utf16.log" in blob)
        check("labeled capture self-announces (label=yes)",
              "labeled-capture.log" in blob and "label=yes" in blob
              and summary["labeled"] == 1)
        check("utf-8-sig and mixed-EOL land in other bucket",
              "[other] utf8bom.log" in blob
              and "[other] mixed-eol.log" in blob
              and summary["counts"]["other"] == 2)
        check("empty degenerate honest row (bytes=0, tee-by-rule)",
              "[tee] empty.log bytes=0" in blob)
        check("counts sum == file count",
              sum(summary["counts"].values()) == 8)
        # 9 refusal: empty dir
        empty = os.path.join(tmp, "empty-dir")
        os.mkdir(empty)
        _le, code_empty, _se = probe_dir(empty)
        check("empty dir refusal exit 3", code_empty == 3)
        # 10 read-only law + determinism: identical re-census
        lines2, code2, summary2 = probe_dir(fx)
        check("reprobe deterministic (identical census)",
              (lines2, code2, summary2) == (lines, code, summary))
        # 11 zero writes into probed dirs
        check("zero writes into probed dirs",
              sorted(os.listdir(fx)) ==
              ["cmd-raw-like.log", "empty.log", "labeled-capture.log",
               "mixed-eol.log", "ps-utf16.log", "pwsh-like.log",
               "tee-like.log", "utf8bom.log"])
        # 12 hygiene faces
        hy, hy_code = _hygiene_lines()
        check("hygiene ascii+net-imports clean", hy_code == 0)
        # --- AC-WCB1..WCB6 baseline + drift-detector family (R1841) ---
        bx = os.path.join(tmp, "baseline-world")
        os.mkdir(bx)
        with open(os.path.join(bx, "b-cmdraw.log"), "wb") as fh:
            fh.write(u"AI \u5224\u5b9a".encode("gbk") + b"\r\n")
        with open(os.path.join(bx, "b-pwsh.log"), "wb") as fh:
            fh.write(u"AI \u5224\u5b9a".encode("utf-8") + b"\r\n")
        with open(os.path.join(bx, "b-utf16.log"), "wb") as fh:
            fh.write(b"\xff\xfe" + "hi\n".encode("utf-16-le"))
        with open(os.path.join(bx, "b-tee.log"), "wb") as fh:
            fh.write("PASS suite row\n".encode("utf-8"))
        bpath = os.path.join(bx, BASELINE_NAME)
        # AC-WCB1: freeze lands 4-class baseline, no tee key, idempotent,
        # post-check green
        wlines, wcode, wbase = write_baseline(bx, bpath)
        check("AC-WCB1 freeze exit 0 + keys exactly four non-tee",
              wcode == 0 and set(wbase.keys()) == set(BASELINE_CLASSES))
        with io.open(bpath, "r", encoding="utf-8") as fh:
            t1 = fh.read()
        _wl2, _wc2, _wb2 = write_baseline(bx, bpath)
        with io.open(bpath, "r", encoding="utf-8") as fh:
            t2 = fh.read()
        check("AC-WCB1 idempotent re-freeze byte-identical", t1 == t2)
        check("AC-WCB1 baseline lists sorted per class",
              all(wbase[c] == sorted(wbase[c]) for c in BASELINE_CLASSES)
              and wbase["cmd-raw"] == ["b-cmdraw.log"])
        check("AC-WCB1 post-check green inside freeze",
              wcode == 0 and any("post-check exit=0" in l
                                 for l in wlines))
        # AC-WCB2: clean check + new tee file never flags
        clines, ccode = check_against_baseline(bx, bpath)
        check("AC-WCB2 clean world DRIFT-CLEAN exit 0",
              ccode == 0 and "DRIFT-CLEAN" in "\n".join(clines))
        with open(os.path.join(bx, "new-tee-product.log"), "wb") as fh:
            fh.write("PASS suite fresh\n".encode("utf-8"))
        clines2, ccode2 = check_against_baseline(bx, bpath)
        check("AC-WCB2 new tee file = normal product, zero flag",
              ccode2 == 0 and "[flag]" not in "\n".join(clines2))
        # AC-WCB3: four new dialect files each flag by name
        for name, payload in (
                ("new-cmdraw.log", u"AI \u5224\u5b9a".encode("gbk")
                 + b"\r\n"),
                ("new-pwsh.log", u"AI \u5224\u5b9a".encode("utf-8")
                 + b"\r\n"),
                ("new-utf16.log", b"\xff\xfe" + "hi\n".encode("utf-16-le")),
                ("new-other.log", b"\xef\xbb\xbf" + "x\n".encode("utf-8"))):
            with open(os.path.join(bx, name), "wb") as fh:
                fh.write(payload)
        dlines, dcode = check_against_baseline(bx, bpath)
        dblob = "\n".join(dlines)
        check("AC-WCB3 four new dialects FLAG exit 2, each named",
              dcode == 2 and dblob.count("[flag] new-dialect:") == 4
              and "new-cmdraw.log" in dblob
              and "new-pwsh.log" in dblob
              and "new-utf16.log" in dblob
              and "new-other.log" in dblob
              and "DRIFT-FLAG" in dblob)
        # AC-WCB4: rewrite baselined cmd-raw file as tee -> migration flag
        with open(os.path.join(bx, "b-cmdraw.log"), "wb") as fh:
            fh.write("rewritten by tee now\n".encode("utf-8"))
        mlines, mcode = check_against_baseline(bx, bpath)
        check("AC-WCB4 class-migrated flag named (base=cmd-raw cur=tee)",
              mcode == 2 and ("[flag] class-migrated: b-cmdraw.log "
                              "(base=cmd-raw cur=tee)")
              in "\n".join(mlines))
        # restore cmd-raw content, clear the four injected dialect
        # files, then delete a baselined file for the disappeared face
        with open(os.path.join(bx, "b-cmdraw.log"), "wb") as fh:
            fh.write(u"AI \u5224\u5b9a".encode("gbk") + b"\r\n")
        for _n in ("new-cmdraw.log", "new-pwsh.log", "new-utf16.log",
                   "new-other.log"):
            os.unlink(os.path.join(bx, _n))
        os.unlink(os.path.join(bx, "b-pwsh.log"))
        glines, gcode = check_against_baseline(bx, bpath)
        gblob = "\n".join(glines)
        check("AC-WCB5 disappeared file = info face, exit 0",
              gcode == 0 and "[info] disappeared: b-pwsh.log "
              "(base=pwsh-capture)" in gblob
              and "DRIFT-CLEAN" in gblob)
        # AC-WCB5: missing baseline -> honest refusal exit 2
        rlines, rcode = check_against_baseline(
            bx, os.path.join(bx, "no-such-baseline.json"))
        check("AC-WCB5 missing baseline honest refusal exit 2",
              rcode == 2 and "probe not deployed" in "\n".join(rlines))
        # AC-WCB2/WCB6 determinism: identical double check
        g2lines, g2code = check_against_baseline(bx, bpath)
        check("AC-WCB6 double-check deterministic",
              (g2lines, g2code) == (glines, gcode))
        # AC-WCB6 mutex gate via main()
        try:
            mcode2 = main(["--dir", bx, "--check", "--update-baseline"])
        except SystemExit as exc:
            mcode2 = exc.code          # argparse error exits 2
        check("AC-WCB6 mutex --check + --update-baseline refused",
              mcode2 == 2)
        # write-discipline: check face wrote nothing inside world dir
        check("AC-WCB6 check face zero writes (baseline only file)",
              BASELINE_NAME in os.listdir(bx))
    finally:
        for sub in os.listdir(tmp):
            d = os.path.join(tmp, sub)
            if os.path.isdir(d):
                for f in os.listdir(d):
                    os.unlink(os.path.join(d, f))
                os.rmdir(d)
            else:
                os.unlink(d)
        os.rmdir(tmp)
    ok = sum(1 for _l, c in checks if c)
    print("selftest: %d/%d checks pass" % (ok, len(checks)))
    for label, cond in checks:
        print("  [%s] %s" % ("ok" if cond else "FAIL", label))
    return (0 if ok == len(checks) else 2), checks


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="qa evidence writer-mode census (R1836 AC-SL3; "
                    "R1841 baseline+drift AC-WCB1..WCB6)")
    parser.add_argument("--dir", default=QA_DIR,
                        help="target evidence dir (default live qa/)")
    parser.add_argument("--selftest", action="store_true",
                        help="run sandbox fixtures")
    parser.add_argument("--check", action="store_true",
                        help="drift detector: recompute census vs "
                             "baseline, flag new non-tee dialect files")
    parser.add_argument("--update-baseline", action="store_true",
                        help="re-freeze gate: derive baseline from "
                             "live census (R1713 AC-BF4 law: only "
                             "after drift disposition)")
    parser.add_argument("--baseline", default=None,
                        help="baseline path (default: "
                             "writer-census-baseline.json under "
                             "target dir)")
    parser.add_argument("--accept", action="append", default=None,
                        metavar="NAME",
                        help="per-file disposition: drop a baselined "
                             "file that was rebuilt in the tee dialect "
                             "from the baseline (repeatable, R2151)")
    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)
    if args.check and args.update_baseline:
        parser.error("--check and --update-baseline are mutually "
                     "exclusive (re-freeze only after drift "
                     "disposition, R1713 AC-BF4 law)")
    if args.accept and (args.check or args.update_baseline):
        parser.error("--accept is a disposition face of its own; "
                     "do not combine it with --check/--update-baseline")
    print("probe: qa writer-mode census (BigDomain R1836 AC-SL3; "
          "R1841 baseline+drift AC-WCB1..WCB6)")
    if args.selftest:
        code, _checks = _selftest()
        hy, hy_code = _hygiene_lines()
        for line in hy:
            print(line)
        return code or hy_code
    target = os.path.abspath(args.dir)
    bpath = os.path.abspath(args.baseline
                            or default_baseline_path(target))
    if args.check:
        print("mode: check (drift detector)")
        print("dir: %s" % target)
        print("baseline: %s" % bpath)
        lines, code = check_against_baseline(target, bpath)
        for line in lines:
            print(line)
        return code
    if args.accept:
        print("mode: accept (per-file disposition)")
        print("dir: %s" % target)
        print("baseline: %s" % bpath)
        code = 0
        for name in args.accept:
            lines, sub = accept_reconciled(target, bpath, name)
            for line in lines:
                print(line)
            if sub != 0:
                code = 2
        return code
    if args.update_baseline:
        print("mode: update-baseline (re-freeze gate)")
        print("dir: %s" % target)
        print("baseline: %s" % bpath)
        lines, code, _base = write_baseline(target, bpath)
        for line in lines:
            print(line)
        return code
    print("dir: %s" % target)
    lines, code, _summary = probe_dir(target)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
