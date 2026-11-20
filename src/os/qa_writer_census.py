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
  * no BOM + any NUL byte present    -> nul-bytes   (BOM-less UTF-16:
                                                    endianness cannot
                                                    be verified, and
                                                    the NUL padding
                                                    decodes as valid
                                                    utf-8, so this
                                                    branch must run
                                                    BEFORE the EOL
                                                    branches - R2808)
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
the target dir, --baseline overridable) carries ONLY the five non-tee
class name lists {cmd-raw, pwsh-capture, ps-utf16, nul-bytes, other}
sorted; tee files are deliberately NOT baselined because the runner
Tee is the healthy dialect - a NEW tee file is a normal evidence
product and must never flag (the zero-tee-key baseline IS that
mechanism). nul-bytes joined this set at R2808 as a KNOWN-DEBT
class: the 115 BOM-less UTF-16 evidence logs already on disk are
baselined by name (so the debt is counted every run instead of
passing as healthy) while any NEW nul-bytes file still flags.
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

Debt-headline measurement (R2929, AC-WCB8..AC-WCB10): the check face
also publishes `plain_unusable=`, `reader_rescued=` and
`reader_refused=` over the baselined set. The debt is defined by
BYTES, not by the class name: `plain_unusable` counts the baselined
files a plain utf-8 consumer would lose (a decode that raises OR that
"succeeds" into NUL-riddled text), `reader_rescued` counts those of
them the shipped reader (`evidence_dialect.read_text`) gets back, and
a file no writer family decodes is counted in `reader_refused` and
NAMED on its own `[refuse-read]` line - so "rescued" can never mean
"read as mojibake". Measured on the shipped tree at R2929:
baselined=590, plain_unusable=151, reader_rescued=151,
reader_refused=0.

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
import time

BASE = os.path.dirname(os.path.abspath(__file__))   # .../src/os
SRC = os.path.dirname(BASE)                          # .../src
ROOT = os.path.dirname(SRC)                          # repo root
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, SANDBOX)
sys.path.insert(0, BASE)

import qa_decode_probe as QDP       # BOM face, single source
import evidence_dialect as ED       # dialect law, single source (R2926)
import reconcile_all as RA          # SHELL_CAPTURE_LABEL, single source

NET_IMPORTS = ("urllib", "requests", "socket", "http", "ftplib",
               "xmlrpc", "smtplib", "asyncio")
QA_DIR = os.path.join(ROOT, "qa")
LABEL = RA.SHELL_CAPTURE_LABEL
CLASSES = ("tee", "cmd-raw", "pwsh-capture", "ps-utf16", "nul-bytes",
           "other")
BASELINE_CLASSES = ("cmd-raw", "pwsh-capture", "ps-utf16", "nul-bytes",
                    "other")
BASELINE_NAME = "writer-census-baseline.json"


def classify_file(path, counts=True):
    """Read-only writer-signature census of one file. Returns a row
    dict; every number is measured or honestly absent - zero
    fabrication.

    R2926 (AC-EVB4): the dialect rule itself moved to
    src/os/evidence_dialect.py (ONE source, delegated here) because the
    commit gate needs the same answer without loading this module's
    reconcile_all import. The row shape is unchanged.

    R3099 (AC-WCB11): `counts=False` is passed straight to the leaf, so a
    caller that only needs the class (the name lists) does not pay the two
    whole-blob count passes; `crlf`/`bare_lf` then read -1 (not measured).
    """
    row = {"name": os.path.basename(path), "bytes": -1, "bom": "?",
           "crlf": 0, "bare_lf": 0, "utf8": False, "label": False,
           "class": "other", "err": ""}
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        row["err"] = "OSError:%s" % exc.__class__.__name__
        return row
    measured = ED.classify_bytes(raw, LABEL.encode("ascii"), counts=counts)
    row.update(measured)
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
        row = classify_file(os.path.join(target, name), counts=False)
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


def check_against_baseline(target, path, stats=None, shape=None, now=None):
    """AC-WCB2..WCB5 drift-detector face. Read-only against the target
    dir AND the baseline file. Three verdict faces: new-dialect FLAG,
    class-migrated FLAG, disappeared info. Deterministic output.

    R3101 (AC-WCB13): the corpus this face re-reads every round is
    507.8MB and nothing published how much of it is fresh. Measured over
    the live tree, 92.6% of those bytes are older than seven days and the
    recent mass grows ~6.75MB/day, so the face will slow down on a
    schedule no reading named. The same directory enumeration that names
    the corpus now also carries each file's size and mtime for free
    (scandir+stat=9.5ms for 4119 entries vs 8.5ms for listdir alone), and
    the growth split is published through a SECOND out-parameter so the
    `stats` three-key contract (AC-WCB12-R1) and every returned line stay
    byte-identical. `now` is injectable because the recency boundary must
    be testable without a clock.

    R3100 (AC-WCB12): the same single pass that feeds the class lists now
    also counts the corpus it read (files and bytes). The count is DERIVED
    from the bytes actually read and published only through the optional
    `stats` out-parameter, so the returned lines stay byte-identical for
    every existing caller (AC-WCB11-R5 pins them). The CLI gate prints it
    as a guard reading: the round's elapsed_ms paired with the corpus size
    is what makes "the face did not get slower" checkable instead of
    assumed.

    R3099 (AC-WCB11): ONE read per file. Measured at R3099 over the live
    tree, the shipped face read every baselined file THREE times - once in
    census_names, once for the label column, once for the debt split - and
    that repetition was 1618.9ms of its 1626.4ms (the baseline comparison
    itself costs 0.0ms). The bytes of a single read now feed all three
    answers, classified with the leaf's `counts=False` cut of the same law,
    which decides the class by short-circuit membership and leaves the two
    count columns at -1 (not measured). The printed lines are unchanged.
    """
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
    # R3101 (AC-WCB13): one enumeration names the corpus AND carries the
    # size/mtime the growth split needs (Windows serves both from the
    # directory read). The name set is identical to the shipped listdir
    # version, which AC-WCB13-g pins on a private world.
    names = []
    meta = {}
    try:
        with os.scandir(target) as it:
            for entry in it:
                if not entry.name.endswith(".log"):
                    continue
                names.append(entry.name)
                try:
                    st = entry.stat()
                    meta[entry.name] = (st.st_size, st.st_mtime)
                except OSError:
                    meta[entry.name] = None
    except OSError:
        names = []
        meta = {}
    names.sort()
    if not names:
        lines.append("no *.log candidates under target dir (refusal)")
        return lines, 3
    base_of = {}
    for c in BASELINE_CLASSES:
        for n in base[c]:
            base_of[n] = c
    # the single read pass: class lists, the label column for baselined
    # files, and the debt split all come out of these same bytes
    if shape is not None:
        # R3101: seven days is a READING boundary, not a law - no gate
        # grades these numbers, and nothing is excluded from the scan.
        cut = (time.time() if now is None else now) - 7 * 86400.0
        shape.update({"files": len(names), "recent7d_files": 0,
                      "recent7d_bytes": 0, "older_files": 0,
                      "older_bytes": 0, "unmeasured": 0})
    lists = dict((c, []) for c in CLASSES)
    rows = []
    unusable = 0
    rescued = 0
    refused = []
    label_bytes = LABEL.encode("ascii")
    corpus_bytes = 0
    corpus_readable = 0
    for name in names:
        fpath = os.path.join(target, name)
        if shape is not None:
            # counted before the read so an unreadable file still lands
            # on one side of the split instead of vanishing from the sum
            m = meta.get(name)
            if m is None:
                shape["unmeasured"] += 1
            elif m[1] >= cut:
                shape["recent7d_files"] += 1
                shape["recent7d_bytes"] += m[0]
            else:
                shape["older_files"] += 1
                shape["older_bytes"] += m[0]
        try:
            with open(fpath, "rb") as handle:
                raw = handle.read()
        except OSError as exc:
            # unreadable file: the shipped census counted it in the
            # honest other bucket, and it never reaches the debt split
            lists["other"].append(name)
            continue
        corpus_bytes += len(raw)
        corpus_readable += 1
        row = ED.classify_bytes(raw, label_bytes, counts=False)
        lists[row["class"]].append(name)
        if name not in base_of or not os.path.isfile(fpath):
            continue
        rows.append((name, row))
        # R2929 (AC-WCB8..AC-WCB10): the debt headline is a MEASUREMENT,
        # not the class name. A plain utf-8 consumer loses only the files
        # the leaf's plain_unusable() names, and the shipped reader is
        # asked to read exactly those - so "rescued" can never be a count
        # of files that decode into mojibake (that is AC-WCB9's arm).
        if not ED.plain_unusable(raw):
            continue
        unusable += 1
        try:
            ED.read_text(raw)
            rescued += 1
        except ED.EvidenceDecodeError as exc:
            refused.append((name, str(exc)))
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
    split = ED.label_coverage(rows)
    lines.append("labeled_baselined=%d unlabeled_baselined=%d"
                 % (split["labeled"], split["unlabeled"]))
    lines.append("plain_unusable=%d reader_rescued=%d reader_refused=%d"
                 % (unusable, rescued, len(refused)))
    for name, reason in refused:
        lines.append("[refuse-read] %s: %s" % (name, reason))
    # R2808: the known-debt face is counted on EVERY run. Baselined
    # nul-bytes files never flag (they are recorded by name), so
    # without this line the debt would be invisible again - the very
    # defect this class exists to name.
    lines.append("nul_bytes=%d" % len(lists["nul-bytes"]))
    lines.append("disappeared=%d" % len(gone))
    lines.append("flags=%d" % flags)
    lines.append("verdict: %s" % ("DRIFT-CLEAN" if flags == 0
                                 else "DRIFT-FLAG"))
    if stats is not None:
        # AC-WCB12: published through an out-parameter, never through
        # `lines`, because the returned lines are pinned line-for-line by
        # AC-WCB11-R5 and a gate reading that moved would be a law change.
        stats["files"] = len(names)
        stats["readable"] = corpus_readable
        stats["bytes"] = corpus_bytes
    return lines, (0 if flags == 0 else 2)


def published_int(lines, name):
    """Read `name=<digits>` out of a published census line (R2933).

    ONE scanner for every gate that grades this census. The closeout gate
    (tools/closeout_gate.py) and the commit-side tree face
    (tools/hooks/pre_commit_gate.py) both read `flags=` and `reader_refused=`
    out of the same rows; two private scanners that drifted would let one gate
    accept a row the other refuses, which is the two-places defect this repo
    has deleted before.

    Searched as a TOKEN, not a line prefix, because the census prints
    `plain_unusable=151 reader_rescued=151 reader_refused=0` on one line.
    Raises ValueError when the token is absent or malformed: a gate that
    cannot read its own input must refuse, never pass.
    """
    prefix = name + "="
    for line in lines:
        start = line.find(prefix)
        if start < 0:
            continue
        pos = start + len(prefix)
        end = pos
        while end < len(line) and line[end].isdigit():
            end += 1
        if end == pos:
            raise ValueError("%s= is not a number (%r)" % (name, line))
        return int(line[pos:end])
    raise ValueError("census did not publish %s=" % name)


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


def baseline_add(target, path, name):
    """Narrow additive disposition face (R2712 AC-WCB7-1..AC-WCB7-6).

    The shipped disposition face is one-directional: --accept DROPS a
    baselined file that was legitimately rebuilt in the tee dialect,
    so a genuine one-off evidence file that stays in a non-tee dialect
    flags new-dialect forever, and its only exit was --update-baseline
    - a whole-baseline re-freeze that would also mask unrelated drift.
    This face adds EXACTLY ONE named file to the baseline list of the
    class it currently measures, so the drift gate keeps its teeth for
    every other file. Refusals never touch the baseline file, and the
    post-check is reported rather than assumed. Returns (lines, code).
    """
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
    if (not name or name in (".", "..")
            or os.path.basename(name) != name
            or (os.altsep and os.altsep in name)):
        lines.append("refused: %r is not a bare file name inside the "
                     "target dir (no path, no parent)" % name)
        return lines, 2
    fpath = os.path.join(target, name)
    if not os.path.isfile(fpath):
        lines.append("refused: %s not on disk (the add face needs a "
                     "measured file, not a promise)" % name)
        return lines, 2
    row = classify_file(fpath)
    cls = row["class"]
    if cls == "tee":
        lines.append("refused: %s is class=tee (healthy dialect files "
                     "are never baselined - a new tee file must never "
                     "flag)" % name)
        return lines, 2
    if name in base_of:
        total = sum(len(base[c]) for c in BASELINE_CLASSES)
        lines.append("already-baselined: %s (class=%s)"
                     % (name, base_of[name]))
        lines.append("baseline: %s" % os.path.abspath(path))
        lines.append("baselined=%d" % total)
        return lines, 0
    base[cls] = sorted(base[cls] + [name])
    clean = dict((c, sorted(base[c])) for c in BASELINE_CLASSES)
    _write_baseline_json(path, clean)
    lines.append("added: %s (class=%s)" % (name, cls))
    lines.append("baseline: %s" % os.path.abspath(path))
    lines.append("baselined=%d"
                 % sum(len(clean[c]) for c in BASELINE_CLASSES))
    post, post_code = check_against_baseline(target, path)
    lines.append("--- post-check (self-run after add) ---")
    lines.extend(post)
    lines.append("post-check exit=%d" % post_code)
    return lines, (0 if post_code == 0 else 2)


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
        # --- AC-WCB8..WCB10 debt headline is a measurement (R2929) ---
        rw = os.path.join(tmp, "read-world")
        os.mkdir(rw)
        with open(os.path.join(rw, "r-tee.log"), "wb") as fh:
            fh.write("PASS suite row\n".encode("utf-8"))
        rpath = os.path.join(rw, BASELINE_NAME)
        write_baseline(rw, rpath)
        qlines, qcode = check_against_baseline(rw, rpath)
        qblob = "\n".join(qlines)
        check("AC-WCB8 tee-only world reads plain_unusable=0 "
              "reader_rescued=0",
              qcode == 0
              and "plain_unusable=0 reader_rescued=0 reader_refused=0"
              in qblob)
        # one BOM utf-16le baselined file: a plain reader loses it, the
        # shipped reader gets it back
        with open(os.path.join(rw, "r-utf16.log"), "wb") as fh:
            fh.write(b"\xff\xfe" + "SUITE PASS 1/1\n".encode("utf-16-le"))
        write_baseline(rw, rpath)
        ulines, ucode = check_against_baseline(rw, rpath)
        ublob = "\n".join(ulines)
        check("AC-WCB8 utf-16 world reads plain_unusable=1 "
              "reader_rescued=1 reader_refused=0",
              ucode == 0
              and "plain_unusable=1 reader_rescued=1 reader_refused=0"
              in ublob)
        # a blob no family decodes: unusable, REFUSED BY NAME, never
        # counted as rescued (the mojibake trap)
        with open(os.path.join(rw, "r-bad.log"), "wb") as fh:
            fh.write(b"\x80\xff\x80")
        write_baseline(rw, rpath)
        blines, _bcode = check_against_baseline(rw, rpath)
        bblob = "\n".join(blines)
        check("AC-WCB9 undecodable blob: unusable=2 rescued=1 "
              "refused=1 and named",
              "plain_unusable=2 reader_rescued=1 reader_refused=1"
              in bblob
              and "[refuse-read] r-bad.log: no known family decodes this "
              "blob" in bblob)
        # the column moves with the bytes: a one-byte change to the
        # undecodable file can make it readable, and the count follows
        with open(os.path.join(rw, "r-bad.log"), "wb") as fh:
            fh.write(b"A")
        mlines2, _mcode2 = check_against_baseline(rw, rpath)
        check("AC-WCB8 column moves with the bytes (bad->ascii: "
              "unusable=1 refused=0)",
              "plain_unusable=1 reader_rescued=1 reader_refused=0"
              in "\n".join(mlines2))
        # AC-WCB10: an independent re-count over the same world agrees
        names = sorted(n for n in os.listdir(rw) if n.endswith(".log"))
        rec_u = rec_r = 0
        for name in names:
            with open(os.path.join(rw, name), "rb") as fh:
                body = fh.read()
            if ED.plain_unusable(body):
                rec_u += 1
                try:
                    ED.read_text(body)
                    rec_r += 1
                except ED.EvidenceDecodeError:
                    pass
        check("AC-WCB10 independent re-count agrees (%d/%d)"
              % (rec_u, rec_r),
              ("plain_unusable=%d reader_rescued=%d" % (rec_u, rec_r))
              in "\n".join(mlines2))
        # --- AC-WCB11: one read per file, counts measured only if asked ---
        # a: the counts=False cut of the law decides the SAME class on every
        # fixture blob and publishes -1 rather than a zero it never read
        lab = LABEL.encode("ascii")
        lean_shapes = [
            ("tee", b"PASS suite row\n"),
            ("pwsh-capture", u"AI \u5224\u5b9a".encode("utf-8") + b"\r\n"),
            ("cmd-raw", u"AI \u5224\u5b9a".encode("gbk") + b"\r\n"),
            ("ps-utf16", b"\xff\xfe" + "hi\n".encode("utf-16-le")),
            ("nul-bytes", b"a\x00b\x00"),
            ("other", b"\xef\xbb\xbf" + "x\n".encode("utf-8")),
        ]
        lean_ok = True
        lean_marks = True
        for want, blob in lean_shapes:
            full = ED.classify_bytes(blob, lab)
            lean = ED.classify_bytes(blob, lab, counts=False)
            lean_ok = lean_ok and full["class"] == want == lean["class"]
            lean_marks = (lean_marks and lean["crlf"] == -1
                          and lean["bare_lf"] == -1
                          and full["crlf"] >= 0 and full["bare_lf"] >= 0)
        check("AC-WCB11-R1 counts=False decides the same six classes and "
              "publishes crlf=bare_lf=-1", lean_ok and lean_marks)
        # b: the full row is unchanged - pinned literally, no drift
        pinned = ED.classify_bytes(u"AI \u5224\u5b9a".encode("gbk") + b"\r\n",
                                   lab)
        check("AC-WCB11-R2 counts=True row pinned exactly",
              pinned == {"bytes": 9, "bom": "utf-8", "crlf": 1,
                         "bare_lf": 0, "utf8": False, "label": False,
                         "class": "cmd-raw"})
        # one private world touching all five published counter faces
        lw = os.path.join(tmp, "one-read-world")
        os.mkdir(lw)
        with open(os.path.join(lw, "l-tee.log"), "wb") as fh:
            fh.write(b"PASS suite row\n")
        with open(os.path.join(lw, "l-pwsh.log"), "wb") as fh:
            fh.write(u"AI \u5224\u5b9a".encode("utf-8") + b"\r\n")
        with open(os.path.join(lw, "l-cmdraw.log"), "wb") as fh:
            fh.write(u"AI \u5224\u5b9a".encode("gbk") + b"\r\n")
        with open(os.path.join(lw, "l-utf16.log"), "wb") as fh:
            fh.write(b"\xff\xfe" + "SUITE\n".encode("utf-16-le"))
        with open(os.path.join(lw, "l-bad.log"), "wb") as fh:
            fh.write(b"\x80\xff\x80")
        lbase = os.path.join(lw, BASELINE_NAME)
        write_baseline(lw, lbase)
        import builtins
        real_open = builtins.open
        seen_opens = {}

        def counting_open(handle, mode="r", *args, **kwargs):
            if "rb" in str(mode):
                key = os.path.basename(str(handle))
                seen_opens[key] = seen_opens.get(key, 0) + 1
            return real_open(handle, mode, *args, **kwargs)

        builtins.open = counting_open
        try:
            ww, wcode = check_against_baseline(lw, lbase)
        finally:
            builtins.open = real_open
        # c: the counters come out of one pass and agree with the bytes
        check("AC-WCB11-R3 counters from one pass: files=5 tee=1 "
              "baselined=4 unusable=3 rescued=2 refused=1",
              wcode == 0
              and "census: files=5 tee=1 baselined=4" in "\n".join(ww)
              and "plain_unusable=3 reader_rescued=2 reader_refused=1"
              in "\n".join(ww))
        # d: every evidence file is opened exactly ONCE by the check face
        logs = dict((k, v) for k, v in seen_opens.items()
                    if k.endswith(".log"))
        check("AC-WCB11-R4 every file read once (opens=%s)"
              % sorted(logs.items()),
              len(logs) == 5 and set(logs.values()) == set([1]))
        # e: the printed line order is pinned, so a refactor cannot move it
        check("AC-WCB11-R5 published lines pinned in order",
              ww == ["census: files=5 tee=1 baselined=4",
                     "labeled_baselined=0 unlabeled_baselined=4",
                     "plain_unusable=3 reader_rescued=2 reader_refused=1",
                     "[refuse-read] l-bad.log: no known family decodes "
                     "this blob",
                     "nul_bytes=0", "disappeared=0", "flags=0",
                     "verdict: DRIFT-CLEAN"])
        # f: the printed census face still measures its counts
        plines, _pcode, _psum = probe_dir(lw)
        pblob = "\n".join(plines)
        check("AC-WCB11-R6 probe_dir still measures crlf/bare_lf "
              "(no -1 leaks into the printed census)",
              "crlf=1" in pblob and "crlf=-1" not in pblob)
        # --- AC-WCB12: the corpus reading is derived, not declared ---
        # a: the out-parameter carries the bytes actually read; the arm
        # recomputes the sum from disk so a hardcoded number cannot pass
        disk_bytes = sum(os.path.getsize(os.path.join(lw, n))
                         for n in os.listdir(lw) if n.endswith(".log"))
        cst = {}
        cw, cwcode = check_against_baseline(lw, lbase, cst)
        check("AC-WCB12-R1 stats out-param is the bytes on disk "
              "(files=%d bytes=%d)" % (cst.get("files", -1),
                                       cst.get("bytes", -1)),
              cwcode == 0 and cst == {"files": 5, "readable": 5,
                                      "bytes": disk_bytes})
        # b: passing the out-parameter must not move the published face
        check("AC-WCB12-R2 returned lines byte-identical with and "
              "without stats",
              cw == ww)
        # c: the CLI gate face prints the same derived number and the
        # verdict/exit code are untouched by the new line
        grab = io.StringIO()
        keep = sys.stdout
        sys.stdout = grab
        try:
            cli_code = main(["--dir", lw, "--check"])
        finally:
            sys.stdout = keep
        cli_out = grab.getvalue()
        check("AC-WCB12-R3 CLI --check prints corpus files=5 bytes=%d "
              "rc=%d" % (disk_bytes, cli_code),
              cli_code == 0
              and ("corpus files=5 readable=5 bytes=%d" % disk_bytes)
              in cli_out
              and "verdict: DRIFT-CLEAN" in cli_out)
        # --- AC-WCB13 (R3101): the corpus growth reading ---
        # a: asking for no shape leaves the shipped face untouched
        plain_lines, plain_code = check_against_baseline(lw, lbase)
        pst = {}
        plain2, _pcode2 = check_against_baseline(lw, lbase, pst)
        check("AC-WCB13-a shape absent: lines and the stats three-key "
              "dict unchanged",
              plain_code == 0 and plain_lines == ww and plain2 == ww
              and sorted(pst) == ["bytes", "files", "readable"])
        # one world with mtimes this arm controls (no clock dependence)
        gw = os.path.join(tmp, "growth-world")
        os.mkdir(gw)
        # offsets are relative to this instant, so the +/-1h boundary
        # files stay exact whether an arm injects `now` or the CLI reads
        # the wall clock (main() has no --now flag on purpose)
        NOW = time.time()
        DAY = 86400.0
        ages = {"g-new.log": 60.0,
                "g-old.log": 10 * DAY,
                "g-bound-new.log": 7 * DAY - 3600.0,
                "g-bound-old.log": 7 * DAY + 3600.0}
        for gname, age in ages.items():
            gpath = os.path.join(gw, gname)
            with open(gpath, "wb") as fh:
                fh.write(b"PASS suite row\n")
            os.utime(gpath, (NOW - age, NOW - age))
        with open(os.path.join(gw, "g-notlog.txt"), "wb") as fh:
            fh.write(b"ignore me\n")
        gbase = os.path.join(gw, BASELINE_NAME)
        write_baseline(gw, gbase)
        gst, gsh = {}, {}
        glines, gcode = check_against_baseline(gw, gbase, gst, gsh,
                                               now=NOW)
        # b: the split is recomputed from disk here, so a typed number
        #    cannot pass, and the three buckets still sum to files
        gcut = NOW - 7 * DAY
        rec_f = rec_b = old_f = old_b = 0
        for gname in sorted(os.listdir(gw)):
            if not gname.endswith(".log"):
                continue
            gsize = os.path.getsize(os.path.join(gw, gname))
            if os.path.getmtime(os.path.join(gw, gname)) >= gcut:
                rec_f += 1
                rec_b += gsize
            else:
                old_f += 1
                old_b += gsize
        check("AC-WCB13-b disk recompute agrees (recent=%d/%dB older=%d/%dB)"
              % (rec_f, rec_b, old_f, old_b),
              gsh.get("recent7d_files") == rec_f
              and gsh.get("recent7d_bytes") == rec_b
              and gsh.get("older_files") == old_f
              and gsh.get("older_bytes") == old_b
              and gsh.get("unmeasured") == 0
              and (gsh.get("recent7d_files", 0) + gsh.get("older_files", 0)
                   + gsh.get("unmeasured", 0)) == gsh.get("files"))
        # c: the boundary is one comparison, not an intuition - a file
        #    an hour inside the seven days is recent, an hour outside is not
        check("AC-WCB13-c seven-day boundary: 2 recent / 2 older",
              gsh.get("recent7d_files") == 2
              and gsh.get("older_files") == 2)
        # d: the *.log law survives the scandir rewrite - a non-.log and
        #    an uppercase extension are neither counted nor read
        with open(os.path.join(gw, "G-UPPER.LOG"), "wb") as fh:
            fh.write(u"AI \u5224\u5b9a".encode("gbk") + b"\r\n")
        gst2, gsh2 = {}, {}
        glines2, _gcode2 = check_against_baseline(gw, gbase, gst2, gsh2,
                                                 now=NOW)
        check("AC-WCB13-d non-.log and uppercase .LOG stay outside "
              "the corpus (files=4)",
              gsh2.get("files") == 4 and gst2.get("files") == 4
              and "G-UPPER.LOG" not in "\n".join(glines2)
              and "g-notlog.txt" not in "\n".join(glines2))
        # e: the two out-parameters do not leak into each other
        check("AC-WCB13-e stats stays three keys and lines stay pinned "
              "while shape is asked",
              sorted(gst) == ["bytes", "files", "readable"]
              and glines == check_against_baseline(gw, gbase)[0])
        # f: the CLI publishes the growth line; verdict and rc untouched
        ggrab = io.StringIO()
        gkeep = sys.stdout
        sys.stdout = ggrab
        try:
            gcli = main(["--dir", gw, "--check"])
        finally:
            sys.stdout = gkeep
        gout = ggrab.getvalue()
        check("AC-WCB13-f CLI prints corpus_growth and keeps the "
              "R3100 substring (rc=%d)" % gcli,
              gcli == 0 and "verdict: DRIFT-CLEAN" in gout
              and ("corpus files=4 readable=4 bytes=%d" % (rec_b + old_b))
              in gout
              and ("corpus_growth recent7d_files=2 recent7d_bytes=%d"
                   % rec_b) in gout)
        # g: the scandir enumeration publishes exactly what listdir did
        real_scandir = os.scandir

        class _Entry(object):
            def __init__(self, name, st):
                self.name = name
                self._st = st

            def stat(self, follow_symlinks=True):
                if self._st is None:
                    raise OSError("unstatable in this arm")
                return self._st

        class _Scan(object):
            def __init__(self, path):
                rows = []
                for nm in os.listdir(path):
                    try:
                        rows.append(_Entry(nm, os.stat(
                            os.path.join(path, nm))))
                    except OSError:
                        rows.append(_Entry(nm, None))
                self._rows = rows

            def __enter__(self):
                return iter(self._rows)

            def __exit__(self, *exc):
                return False

        os.scandir = _Scan
        try:
            sst, ssh = {}, {}
            slines, _scode = check_against_baseline(gw, gbase, sst, ssh,
                                                    now=NOW)
        finally:
            os.scandir = real_scandir
        check("AC-WCB13-g scandir face is byte-identical to the listdir "
              "face it replaced",
              slines == glines and sst == gst and ssh == gsh)
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
    parser.add_argument("--baseline-add", action="append", default=None,
                        metavar="NAME",
                        help="per-file disposition: add ONE named "
                             "non-tee file to the baseline so a genuine "
                             "one-off evidence file stops flagging "
                             "without re-freezing the whole baseline "
                             "(repeatable, R2712)")
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
    if args.baseline_add and (args.check or args.update_baseline
                              or args.accept):
        parser.error("--baseline-add is a disposition face of its own; "
                     "do not combine it with --check, --update-baseline "
                     "or --accept")
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
        t0 = time.perf_counter()
        cstats = {}
        cshape = {}
        lines, code = check_against_baseline(target, bpath, cstats, cshape)
        print("elapsed_ms=%.1f" % ((time.perf_counter() - t0) * 1000.0))
        # AC-WCB12 guard reading: the corpus the face read, derived from the
        # same pass, so "did it get slower" is answerable without a probe.
        print("corpus files=%d readable=%d bytes=%d"
              % (cstats.get("files", 0), cstats.get("readable", 0),
                 cstats.get("bytes", 0)))
        # AC-WCB13 growth reading (R3101): how much of that corpus is fresh
        # and how much is frozen history. No threshold: this is the number
        # that tells a reader whether the face is on a slower schedule.
        print("corpus_growth recent7d_files=%d recent7d_bytes=%d "
              "older_files=%d older_bytes=%d unmeasured=%d"
              % (cshape.get("recent7d_files", 0),
                 cshape.get("recent7d_bytes", 0),
                 cshape.get("older_files", 0),
                 cshape.get("older_bytes", 0),
                 cshape.get("unmeasured", 0)))
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
    if args.baseline_add:
        print("mode: baseline-add (per-file disposition)")
        print("dir: %s" % target)
        print("baseline: %s" % bpath)
        code = 0
        for name in args.baseline_add:
            lines, sub = baseline_add(target, bpath, name)
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
