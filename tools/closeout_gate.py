"""Closeout precondition gate (R2932, criteria AC-CLG1..AC-CLG9).

WHY: the R2926 commit hook refuses STAGED evidence bytes only. A round that
writes a shell-captured file and never stages it still leaves the file on disk,
where every later reader meets it and no gate has refused it yet. The board
carried this as "decide whether the closeout runs qa_writer_census --check as a
HARD precondition, and pin WHICH of its two faces gates".

THE DECISION, and why it is not a preference:

  * `flags` GATES. It is the census's own drift face - a new non-tee file, or a
    baselined file whose class moved. That is exactly "this round let a
    non-healthy write reach the tree", i.e. the thing a closeout precondition
    exists to refuse.
  * `reader_refused` does NOT gate. It counts BASELINED files that no writer
    family decodes. Those were baselined by name at freeze time, so a refusal
    there would make every closeout red for history the round did not create,
    and the only exit would be a re-freeze that also masks unrelated drift. It
    stays PUBLISHED on the gate line so the debt is visible on every closeout.

  A change to a baselined file's bytes that breaks the dialect moves its class,
  so it already lands on `flags`. Honest boundary: a rewrite that stays inside
  the same class is invisible to both faces (the census has no hashes).

R3093 - the two faces a round could still slip past (AC-CLG6):

Two laws already ship as SUITES but were never asked at closeout, so a round
could read PASS while both were red. Measured at R3092: R3091 closed a round
whose newest block carried no dated labelled main line, and entered the tree
with a registry row that had never been re-pinned; each law was asked only by
its own suite, and the closeout gate asked none of them.

  * round-main - `ledger_lines --round-main` (E_RMS_NO_ROUND / NO_DATE /
    NO_LABEL). The CEO face is composed from the newest dated labelled line;
    a round without one publishes the PREVIOUS round while every check passes.
  * registry census - `registry_counter_census --check`. A registry row that
    was edited without re-pinning moves the census, and nothing at closeout
    refused it.

Both are READ-ONLY and both are cheap (one state read, one registry read).
Both are opt-in through `root`: with `root=None` the gate answers exactly the
question it shipped with, byte for byte, so the eleven shipped call sites and
the five shipped criteria keep their meaning. The CLI passes `root=ROOT`, so a
human closeout asks all three faces in one command.

Ordering is part of the law: `flags` is asked FIRST, because it is the cheapest
face and the only one about bytes this round wrote; a drifted tree is refused
before either root face is read. The root faces then run in cost order:
round-main (one state read), census (one registry read), matrix (the derived
document, measured at 331ms - the most expensive face of the three).

R3094 - the derived document (AC-CLG7):

`docs/sandbox-suite-matrix.md` is derived from the registry, and the law that
the two agree already shipped as `src/os/suite_matrix_reconcile.py --check`.
Measured at R3094: that law was asked only by the battery follow-up sections
(a round that runs no battery leg never asks it) and by human habit - the
round that closes carries its own `--check` in the board text, and nothing
refused a stale document. `check_matrix(root)` now asks it as the third root
face and refuses by name E_CLG_MATRIX; a missing document is E_EDM_NO_DOC,
never a skip. A caller building a fixture world with no document MUST say so:
`matrix=False` is the named opt-out, so "not asked" is always visible in code.

R3104 - the matrix face asked about a world it cannot address (AC-CLG9):

The document law compares a document against THIS module's registry, so `root`
selects only the document and the qa/ pile. Measured on a fixture world that
carried a byte copy of the live document: the face read EVIDENCE-FACE with
rows=735/735 over a world holding no registry at all - it refused, but on the
leg provenance string, while publishing live registry numbers as if they were
the world's. `check_matrix` now applies the same guard as `check_census`: the
registry file the law reads must live under `root`, or the face refuses by
name E_CLG_FOREIGN_REGISTRY face=matrix. The guard sits on root and the
registry, NOT on the document path, so a caller checking a CANDIDATE document
inside this repo (the shipped AC-CLG7c usage) still gets the document verdict.

Honest boundary, disclosed rather than implied: the vehicle `src/os/closeout.py`
asks this gate through `tree_refusal` (R3095), so `evaluate` is reached whenever
a world carries all three inputs the gate reads (`qa/`, its census baseline file
and the derived document); a world missing any of them prints `gate=NOT-ASKED`
with its reason, and that is the one shape still unjudged - printed, never
silently skipped.

R3105 - the same address law spells which face refused:

`check_census`'s refusal carried `registry=... root=...` with no face token,
while `check_matrix` carried `face=matrix`, so a reader holding the census line
could not tell which face had refused. The census line now reads
`E_CLG_FOREIGN_REGISTRY face=census registry=... root=...`. The two faces keep
ONE code on purpose: it is one law (a face may not judge a tree it cannot
address), and the face token - not a second spelling - is what makes the line
actionable. Pinned by AC-CLG9 and by AC-COUT9 (the vehicle now prints it).

R3219 - the replacement ledger (AC-CLG11..13):

`qa_log.py --ledger-check` shipped at R3218 but nothing ran it: measured on
four fixture worlds, a truncated JSON row and a latest row whose `new_sha16`
no longer matched the file on disk both answered the identical
`CLOSEOUT-GATE PASS` with no ledger token. `check_ledger(root)` now asks the
writer's OWN judgement (`qa_log.ledger_report`, one definition) about
`root/state/qa_replacements.jsonl` with the named files judged under
`root/qa`; a bad row or a stale latest row refuses by name E_CLG_LEDGER, an
absent ledger is rows=0 and PASS, and a gone file is counted missing rather
than reddened. It is asked LAST (cheapest read, but it judges bytes a previous
write replaced) and `ledger=False` is the named opt-out. The reading rides
BELOW the verdict so the PASS token shape stays byte-identical.

R3221 - the reading a machine can compare (AC-CLG15..16):

`check_ledger` printed `rows=`/`broken=` on the LEDGER row, but `evaluate`
published only `ledger: "OK"/"RED"` in its verdict dict. Measured on three
fixture worlds (absent ledger, healthy chain, broken chain) the key set was
identical and no count was reachable except by parsing prose - the same
criticism as R3218, moved one layer up. `check_ledger` now accepts a `reading`
dict filled from the report it judged (never re-parsed), and the verdict gains
`ledger_rows` / `ledger_broken` as VALUES; the printed row and the PASS token
shape are unchanged, and a break is still never gated.

Shape: a published line, never a silent pass.

    CLOSEOUT-GATE PASS files=<n> flags=0 reader_refused=<n> gating=flags
    CLOSEOUT-GATE PASS ... gating=flags round_main=OK census=PASS
    CLOSEOUT-GATE PASS ... gating=flags round_main=OK census=PASS matrix=DOC-CURRENT
    CLOSEOUT-GATE REFUSED reason=<E_CLG_*> flags=<n> ... [flag] lines

Exit codes: 0 PASS; 2 REFUSED. Read-only: the gate never writes the tree, the
baseline, or any qa/ file. Stdlib only (plus the shipped census module), no
network, no shell.
"""

import hashlib
import io
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))          # .../tools
ROOT = os.path.dirname(BASE)                                # repo root
sys.path.insert(0, os.path.join(ROOT, "src", "os"))

import qa_writer_census as CENSUS                           # noqa: E402

GATING_FACE = "flags"
# R3103: a face asked about a root it cannot address refuses by name instead of
# judging the tree this module was imported from.
E_CLG_FOREIGN_REGISTRY = "E_CLG_FOREIGN_REGISTRY"
E_CLG_NO_STATE = "E_CLG_NO_STATE"
# R3177: the state carrier's own two pathologies, named so a reader can act.
E_CLG_CARRIER = "E_CLG_CARRIER"
E_CLG_CARRIER_LAYOUT = "E_CLG_CARRIER_LAYOUT"
E_CLG_CARRIER_FOLD = "E_CLG_CARRIER_FOLD"
E_CLG_CARRIER_UNREADABLE = "E_CLG_CARRIER_UNREADABLE"
# R3219: the replacement ledger's two pathologies (a bad row, a latest row
# whose new_sha16 no longer matches the file on disk). Named so a reader can
# act; an absent ledger is rows=0 and never a refusal.
E_CLG_LEDGER = "E_CLG_LEDGER"
INFORMATIONAL_FACES = ("reader_refused", "plain_unusable",
                       "reader_rescued", "flags")


class GateRowError(Exception):
    """The census row did not carry a field the gate needs."""


def _token(lines, name):
    """Read `name=<digits>` through the census's OWN scanner (R2933).

    The token scanner moved into the census module because the commit-side
    tree face reads the same row: two private scanners could drift and let
    one gate accept a row the other refuses. Absent or malformed ->
    GateRowError (a gate that cannot read its own input must refuse).
    """
    try:
        return CENSUS.published_int(lines, name)
    except ValueError as exc:
        raise GateRowError(str(exc))


def _src_os(root):
    """The repo's src/os on sys.path, importing lazily (R3093).

    Imported inside the root faces so that `root=None` keeps the gate's
    import surface at exactly what R2932 shipped: a closeout that does not
    ask the two new questions does not load their modules either.
    """
    path = os.path.join(root, "src", "os")
    if path not in sys.path:
        sys.path.insert(0, path)
    return path


def _timed(box, key, fn, *args, **kwargs):
    """Call fn, publishing its wall time into box[key].

    R3097: the dry run grew to ~8s and nothing said which face owned the
    seconds - one total is not a name. The reading is a DIAGNOSTIC and never
    enters a verdict token or the PASS line, so no gate decision can move with
    a machine's speed; a slow face is still PASS, it is only visible.
    """
    start = time.perf_counter()
    try:
        return fn(*args, **kwargs)
    finally:
        box[key] = round((time.perf_counter() - start) * 1000.0, 1)


def check_round_main(root):
    """Ask the round-main shape law of the live log. Returns (ok, line).

    R3103: a root with no log is refused BY NAME. Before this, asking the face
    of a fixture world raised a bare FileNotFoundError, which the vehicle
    turned into UNREADABLE - a refusal, but not one a reader could act on.
    """
    path = _src_os(root)
    if not os.path.isfile(os.path.join(path, "state.json")):
        return False, "%s src/os/state.json" % E_CLG_NO_STATE
    import ledger_lines as LEDGER
    log = LEDGER.load_state_log(os.path.join(path, "state.json"))
    report = LEDGER.check_round_main_shape(log)
    return bool(report["ok"]), LEDGER.format_round_main(report)


def check_carrier(root):
    """Ask the state carrier's waterline and canonical layout (AC-WLG1..6).

    WHY (R3177, measured at R3176): state.json read 92329B against the 78500B
    gate with bare_lf=453, so the shipped fold door refused E_STATE_LAYOUT and
    the breach could not be paid down - yet this gate read neither the gauge
    nor the layout, so the debt accumulated for dozens of rounds with every
    closeout green. The laws asked here already ship in `logs_toolkit`
    (`GATE`, `eol_profile`, `load_state`); this face re-reads them and adds no
    second definition of either number.

    Two pathologies refuse, and only these two (pre-registered R3177):
      * a NON-CANONICAL layout - the fold door cannot read it, so any debt is
        unpayable by construction;
      * OVER the line with no window to fold (`log_items < 2`).
    An over-line carrier that is canonical and foldable is NOT refused: it is
    published as `fold_needed=true` on the CARRIER row so the debt is visible
    at every closeout without turning an honest mid-round state into a red.

    Read-only; returns (ok, line) where `line` is the CARRIER row either way.
    """
    path = _src_os(root)
    state = os.path.join(path, "state.json")
    if not os.path.isfile(state):
        return False, "%s src/os/state.json" % E_CLG_NO_STATE
    import logs_toolkit as LT
    try:
        _path, raw, payload = LT.load_state(root)
        prof = LT.eol_profile(raw)
        items = len(payload.get("log") or [])
    except (IOError, OSError, ValueError, UnicodeDecodeError) as exc:
        return False, "%s %s: %s" % (E_CLG_CARRIER_UNREADABLE,
                                     type(exc).__name__, exc)
    disk = os.path.getsize(state)
    margin = LT.GATE - disk
    fold_needed = disk > LT.GATE
    canonical = bool(prof["layout_ok"] and prof["indent_ok"])
    row = ("CARRIER bytes=%d gate=%d margin=%d fold_needed=%s layout_ok=%s "
           "crlf=%d bare_lf=%d indent_anomaly=%d log_items=%d"
           % (disk, LT.GATE, margin,
              "true" if fold_needed else "false",
              "true" if canonical else "false",
              prof["crlf"], prof["bare_lf"], prof["indent_anomaly"], items))
    if not canonical:
        return False, "CARRIER FAIL %s %s" % (E_CLG_CARRIER_LAYOUT, row)
    if fold_needed and items < 2:
        return False, "CARRIER FAIL %s %s" % (E_CLG_CARRIER_FOLD, row)
    return True, row


def check_ledger(root, reading=None):
    """Ask the replacement ledger of THIS world (R3219, AC-CLG11..13).

    WHY (measured at R3218): `qa_log.py --ledger-check` shipped a read face and
    nothing ran it - a ledger with a truncated JSON line or with a latest row
    whose `new_sha16` no longer matches the file on disk answered the identical
    `CLOSEOUT-GATE PASS` as a healthy one, so a rewrite-recorded-then-changed
    evidence file could close green.

    Read-only. The judgement is the writer's OWN (qa_log.ledger_report), so the
    gate cannot drift from `--ledger-check`; this face only decides the verdict
    against THIS world: the ledger is `root/state/qa_replacements.jsonl` and
    the files it names are judged under `root/qa`. An absent ledger is rows=0
    and PASS - no rewrite has happened yet, which is not a defect. A gone file
    is counted `missing`, not reddened: a deletion is another event and the
    ledger never claimed the file would stay.

    Returns (ok, lines) where lines[0] is the LEDGER row and the rest are one
    detail line per defect.

    R3220 (AC-CLG14): the row also prints `broken=`, the count of names whose
    adjacent records do not link (the later row's old_sha16 must be the earlier
    row's new_sha16). It is published, never gated: a break is either a lost
    record or a lawful deletion-then-recreate / external write, and this face
    cannot tell them apart, so refusing would accuse the lawful case.

    R3221 (AC-CLG15): the same counts were reachable ONLY by reading the row
    text - measured on three fixture worlds (absent / healthy chain / broken
    chain) the verdict dict answered the identical `ledger='OK'` and carried no
    count at all, so a machine consumer had to parse prose. A caller may now
    pass a `reading` dict; it is filled from the SAME report this face judged
    (never re-parsed), so the value and the printed row cannot disagree.

    R3224 (AC-SXF26): the reading also carries `present`, whether the ledger
    file exists. Measured this window: absent and empty ledgers answered the
    identical row AND the identical reading, so a downstream face published
    rows=0 for both - "nothing to measure" read as "measured empty". The row
    text is unchanged on purpose (an absent ledger is still OK rows=0); only
    the machine-readable reading gains the existence bit.
    """
    _src_os(root)
    import qa_log as QL
    path = os.path.join(root, "state", QL.LEDGER_NAME)
    report = QL.ledger_report(path, evidence_dir=os.path.join(root, "qa"))
    if reading is not None:
        reading.update({"present": report["present"],
                        "rows": report["rows"], "names": report["names"],
                        "bad": len(report["bad"]),
                        "stale": len(report["stale"]),
                        "missing": len(report["missing"]),
                        "broken": len(report["broken"])})
    lines = ["LEDGER %s rows=%d names=%d bad=%d stale=%d missing=%d broken=%d "
             "path=%s"
             % (report["verdict"], report["rows"], report["names"],
                len(report["bad"]), len(report["stale"]),
                len(report["missing"]), len(report["broken"]),
                os.path.relpath(path, root).replace("\\", "/"))]
    for number, reason in report["bad"]:
        lines.append("LEDGER detail bad line=%d reason=%s" % (number, reason))
    for name, disk, wanted in report["stale"]:
        lines.append("LEDGER detail stale name=%s disk_sha16=%s ledger_sha16=%s"
                     % (name, disk, wanted))
    for name in report["missing"]:
        lines.append("LEDGER detail missing name=%s" % name)
    for name, prev_line, line, prev_sha, old_sha in report["broken"]:
        lines.append("LEDGER detail chain name=%s prev_line=%d line=%d "
                     "prev_new_sha16=%s old_sha16=%s"
                     % (name, prev_line, line, prev_sha, old_sha))
    return report["verdict"] == "OK", lines


def check_census(root, registry=None, pin=None):
    """Ask the registry counter census against its own pin. (ok, line).

    `registry`/`pin` exist so a fixture world can inject its own frozen
    registry and pin; the live call passes neither and reads the shipped
    constants of the census module itself.
    """
    _src_os(root)
    import registry_counter_census as RC
    registry = registry or RC.REGISTRY
    pin = pin or RC.PIN
    # R3103: the two constants are bound to THIS module's import-time root, so
    # a face asked about another root used to answer for this one - measured
    # on a battery_followup fixture world: ok=True "VERDICT PASS pinned=735"
    # at 161.9ms while the world carried no registry at all. A face that cannot
    # address the world it was given now refuses by name instead of judging a
    # tree nobody asked about.
    base = os.path.normcase(os.path.abspath(root)) + os.sep
    for name, path in (("registry", registry), ("pin", pin)):
        if os.path.normcase(os.path.abspath(path)).startswith(base):
            continue
        # R3105: the same address law is spelled by two faces, so the line
        # names WHICH face refused. Without the token a reader holding
        # `E_CLG_FOREIGN_REGISTRY registry=...` could not tell the census
        # refusal from the matrix one, which already carried face=matrix.
        return False, ("%s face=census %s=%s root=%s"
                       % (E_CLG_FOREIGN_REGISTRY, name, path,
                          os.path.abspath(root)))
    # R3098: the live registry may use the shipped content-addressed cache, but
    # the gate only READS it (cache_write=False) - a gate that writes the tree
    # it is judging is not a gate. A fixture registry never touches the live
    # cache file, so no private world can be served another world's classes.
    cache = None
    if os.path.normcase(os.path.abspath(registry)) == \
            os.path.normcase(os.path.abspath(RC.REGISTRY)):
        cache = RC.CACHE
    try:
        report = RC.census(registry=registry, cache_path=cache,
                           cache_write=False)
    except RC.CensusError as exc:
        return False, "%s %s" % (exc.code, exc.detail)
    try:
        with io.open(pin, encoding="utf-8") as fh:
            pinned = json.load(fh)
    except (IOError, OSError, ValueError) as exc:
        return False, "E_RCC_NO_PIN %s" % exc
    fails = RC.compare(report, pinned)
    if fails:
        return False, "VERDICT FAIL %s" % " ".join(fails)
    return True, "VERDICT PASS pinned=%d" % sum(
        len(v) for v in pinned.values())


def check_matrix(root, doc=None, qa_dir=None):
    """Ask the suite-matrix doc law shipped at R3086/R3089 (AC-CLG7).

    The document is DERIVED from the registry, so a round can move a registry
    row and leave the doc behind while every other closeout face reads green.
    The law itself already ships (`suite_matrix_reconcile.report`, measured at
    331ms on the live tree and DOC-CURRENT); before R3094 only a battery leg or
    a human habit asked it. Returns (ok, line), never a silent pass: a missing
    document is a refusal by name, not a skip.
    """
    # R3104: the law compares a document against THIS module's registry
    # (`suite_matrix_reconcile.registry_counts()` reads reconcile_all.SUITES of
    # the repo it was imported from). Asked about another root it therefore
    # published LIVE registry numbers about a world - measured on a fixture
    # world carrying a byte copy of the live document: EVIDENCE-FACE rows=735/735
    # over a world with no registry at all. The refusal came from the leg
    # provenance string, not from addressability, so a reader could not tell
    # which tree those numbers described. Same guard, same name as
    # check_census: a face asked about a registry it cannot address refuses.
    registry = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
    base = os.path.normcase(os.path.abspath(root)) + os.sep
    if not os.path.normcase(os.path.abspath(registry)).startswith(base):
        return False, ("%s face=matrix registry=%s root=%s"
                       % (E_CLG_FOREIGN_REGISTRY, registry,
                          os.path.abspath(root)))
    path = _src_os(root)
    import suite_matrix_reconcile as SMR
    doc = doc or os.path.join(root, "docs", "sandbox-suite-matrix.md")
    qa_dir = qa_dir or os.path.join(root, "qa")
    if not os.path.isfile(doc):
        return False, "E_EDM_NO_DOC %s" % os.path.basename(doc)
    try:
        report = SMR.report(doc, None, qa_dir)
    except (IOError, OSError, ValueError) as exc:
        return False, "E_EDM_UNREADABLE %s: %s" % (type(exc).__name__, exc)
    verdict = report.get("verdict")
    return (verdict == SMR.WORD_CURRENT,
            "%s %s rows=%s/%s" % (verdict, SMR.rel(doc),
                                  report.get("doc_rows"),
                                  report.get("registry_rows")))


def _baseline_identity(baseline, root):
    """Which baseline the census face just judged, read off that file (R3109).

    Measured: the PASS line says `census=PASS` and never names the file it
    compared against - the name is a module constant bound at import time, so
    a reader holding the line could not verify which baseline was judged, how
    big it was, or when it was written. Every value below is derived from the
    same file the face was handed (the SHA-256 is of those exact bytes); a
    window that re-types instead of reading fails AC-CLG10.
    """
    try:
        with io.open(baseline, "rb") as handle:
            raw = handle.read()
        base = json.loads(raw.decode("utf-8"))
        written = os.stat(baseline).st_mtime
    except (IOError, OSError, ValueError, UnicodeDecodeError):
        return ""
    if not isinstance(base, dict):
        return ""
    rows = 0
    for value in base.values():
        if isinstance(value, list):
            rows += len(value)
    name = os.path.relpath(baseline, root).replace("\\", "/")
    return ("CENSUS-BASELINE name=%s bytes=%d rows=%d sha256=%s written=%s"
            % (name, len(raw), rows, hashlib.sha256(raw).hexdigest()[:12],
               time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(written))))


def _ledger_values(verdict, reading):
    """Publish the ledger's two machine-readable counts (R3221, AC-CLG15).

    The values come from `check_ledger`'s `reading` out-parameter, which that
    face fills from the report it judged - so the verdict and the printed
    LEDGER row are two renderings of ONE report and cannot disagree. A world
    where the face produced no reading (it refused before reading, or the
    caller said `ledger=False`) publishes neither key: absent means "not
    read", which is not the same claim as rows=0.
    """
    for source, target in (("rows", "ledger_rows"), ("broken", "ledger_broken")):
        if source in reading:
            verdict[target] = reading[source]
    return verdict


def evaluate(target, baseline, root=None, registry=None, census_pin=None,
             matrix=None, ledger=None):
    """Run the census check and return (lines, exit_code, verdict dict).

    `root=None` -> the pre-R3093 question, byte for byte.
    `root` given -> after a green `flags` face, also ask round-main and the
    registry census; either red refuses the closeout by name.
    `ledger=False` -> the named opt-out for the R3219 replacement-ledger face,
    so a world that keeps no ledger says so in code instead of being skipped.
    """
    face_ms = {}
    # R3124: measured on the live tree, this face's 1186.3ms is BYTES, not
    # names - enumeration cost 13.7ms (1.2%) while the whole-blob read cost
    # 831.6ms (69.9%, 582.6MB/s) and the classification sweep 337.0ms (28.3%)
    # over 4211 files / 484.5MB. The census already derives files/readable/
    # bytes through its own `stats` out-parameter, so the corpus the reading
    # paid for is published through the verdict (never the PASS line, whose
    # token shape is pinned) instead of being re-counted here.
    corpus = {}
    census_lines, census_rc = _timed(face_ms, "flags",
                                     CENSUS.check_against_baseline,
                                     target, baseline, stats=corpus)

    def _pub(verdict):
        # R3097: the per-face readings ride in the verdict, never on the line.
        verdict["face_ms"] = dict(face_ms)
        if corpus:
            verdict["corpus"] = dict(corpus)
        return verdict
    out = []
    if census_lines and census_lines[0].startswith("baseline file missing"):
        out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_NO_BASELINE "
                   "baseline=%s" % os.path.basename(baseline))
        out.extend(census_lines)
        return out, 2, {"verdict": "REFUSED",
                        "reason": "E_CLG_NO_BASELINE"}
    if census_rc == 3:
        out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_EMPTY target=%s"
                   % os.path.abspath(target))
        out.extend(census_lines)
        return out, 2, {"verdict": "REFUSED", "reason": "E_CLG_EMPTY"}
    try:
        flags = _token(census_lines, GATING_FACE)
        refused = _token(census_lines, "reader_refused")
        count = 0
        for line in census_lines:
            if line.startswith("census: files="):
                count = _token([line], "files")
                break
        if count == 0:
            raise GateRowError("census did not publish its file count")
    except GateRowError as exc:
        out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_ROW detail=%s" % exc)
        out.extend(census_lines)
        return out, 2, {"verdict": "REFUSED", "reason": "E_CLG_ROW"}

    if flags == 0:
        verdict = {"verdict": "PASS", "files": count, "flags": flags,
                   "reader_refused": refused, "gating": GATING_FACE}
        tail = ""
        carrier_row = ""
        ledger_row = ""
        if root is not None:
            # R3177: the carrier is the cheapest root face (one state read)
            # and the one every later face reads through, so it is asked
            # first. An unpayable breach or a non-canonical layout refuses by
            # name; a canonical over-line carrier passes and publishes its
            # debt on the CARRIER row below the verdict.
            try:
                cr_ok, cr_line = _timed(face_ms, "carrier",
                                        check_carrier, root)
            except (IOError, OSError, ValueError, UnicodeDecodeError) as exc:
                cr_ok = False
                cr_line = "%s %s" % (E_CLG_CARRIER_UNREADABLE, exc)
            if not cr_ok:
                out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_CARRIER "
                           "files=%d flags=%d carrier=FAIL"
                           % (count, flags))
                out.append(cr_line)
                verdict = {"verdict": "REFUSED", "reason": "E_CLG_CARRIER",
                           "files": count, "flags": flags,
                           "carrier": "FAIL"}
                return out, 2, _pub(verdict)
            carrier_row = cr_line
            # R3093: the two laws a round could slip past. Read-only, cheap,
            # and asked only after the byte-drift face is green.
            try:
                rm_ok, rm_line = _timed(face_ms, "round_main",
                                        check_round_main, root)
            except (IOError, OSError, ValueError) as exc:
                out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_ROUND_MAIN "
                           "files=%d flags=%d round_main=UNREADABLE"
                           % (count, flags))
                out.append("E_RMS_UNREADABLE %s" % exc)
                verdict = {"verdict": "REFUSED",
                           "reason": "E_CLG_ROUND_MAIN", "files": count,
                           "flags": flags, "round_main": "UNREADABLE"}
                return out, 2, _pub(verdict)
            if not rm_ok:
                out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_ROUND_MAIN "
                           "files=%d flags=%d round_main=FAIL" % (count, flags))
                out.append(rm_line)
                verdict = {"verdict": "REFUSED",
                           "reason": "E_CLG_ROUND_MAIN", "files": count,
                           "flags": flags, "round_main": "FAIL"}
                return out, 2, _pub(verdict)
            try:
                cen_ok, cen_line = _timed(face_ms, "census", check_census,
                                          root, registry=registry,
                                          pin=census_pin)
            except (IOError, OSError, ValueError) as exc:
                out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_CENSUS "
                           "files=%d flags=%d census=UNREADABLE"
                           % (count, flags))
                out.append("E_RCC_UNREADABLE %s" % exc)
                verdict = {"verdict": "REFUSED", "reason": "E_CLG_CENSUS",
                           "files": count, "flags": flags,
                           "round_main": "OK", "census": "UNREADABLE"}
                return out, 2, _pub(verdict)
            if not cen_ok:
                out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_CENSUS "
                           "files=%d flags=%d round_main=OK census=FAIL"
                           % (count, flags))
                out.append(cen_line)
                verdict = {"verdict": "REFUSED", "reason": "E_CLG_CENSUS",
                           "files": count, "flags": flags,
                           "round_main": "OK", "census": "FAIL"}
                return out, 2, _pub(verdict)
            if matrix is not False:
                # R3094: the derived document is asked LAST, after every face
                # that reads this round's own bytes. `matrix=False` is the
                # caller's named opt-out for a fixture world that constructs no
                # document, so an unasked face can never happen silently.
                doc = matrix if matrix else None
                try:
                    mx_ok, mx_line = _timed(face_ms, "matrix", check_matrix,
                                            root, doc=doc)
                except (IOError, OSError, ValueError) as exc:
                    face_ms.setdefault("matrix", 0.0)
                    mx_ok, mx_line = False, "E_EDM_UNREADABLE %s" % exc
                if not mx_ok:
                    out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_MATRIX "
                               "files=%d flags=%d round_main=OK census=PASS "
                               "matrix=FAIL" % (count, flags))
                    out.append(mx_line)
                    verdict = {"verdict": "REFUSED", "reason": "E_CLG_MATRIX",
                               "files": count, "flags": flags,
                               "round_main": "OK", "census": "PASS",
                               "matrix": "FAIL"}
                    return out, 2, _pub(verdict)
                verdict["matrix"] = "DOC-CURRENT"
                tail_matrix = " matrix=DOC-CURRENT"
            else:
                # A named opt-out still publishes a reading, so a reader can
                # see that the face was skipped rather than slow.
                face_ms["matrix"] = 0.0
                tail_matrix = ""
            if ledger is not False:
                # R3219: the replacement ledger is asked LAST - it is the
                # cheapest read of the five (one small file) but it judges
                # bytes a previous write replaced, so it must not be the face
                # that explains a red that the drift face already owns.
                # R3221: the counts ride into the verdict as VALUES, filled by
                # the same report the row is rendered from, so no consumer has
                # to parse the prose (and none can disagree with it).
                ledger_reading = {}
                try:
                    lg_ok, lg_lines = _timed(face_ms, "ledger",
                                             check_ledger, root,
                                             reading=ledger_reading)
                except (IOError, OSError, ValueError,
                        UnicodeDecodeError) as exc:
                    lg_ok = False
                    lg_lines = ["%s %s" % (E_CLG_LEDGER, exc)]
                if not lg_ok:
                    out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_LEDGER "
                               "files=%d flags=%d round_main=OK census=PASS"
                               % (count, flags))
                    out.extend(lg_lines)
                    verdict = {"verdict": "REFUSED", "reason": E_CLG_LEDGER,
                               "files": count, "flags": flags,
                               "round_main": "OK", "census": "PASS",
                               "ledger": "RED"}
                    _ledger_values(verdict, ledger_reading)
                    return out, 2, _pub(verdict)
                ledger_row = lg_lines[0]
                verdict["ledger"] = "OK"
                _ledger_values(verdict, ledger_reading)
            else:
                face_ms["ledger"] = 0.0
                ledger_row = ""
            verdict["round_main"] = "OK"
            verdict["census"] = "PASS"
            verdict["carrier"] = "OK"
            tail = " round_main=OK census=PASS" + tail_matrix
        out.append("CLOSEOUT-GATE PASS files=%d flags=%d "
                   "reader_refused=%d gating=%s%s"
                   % (count, flags, refused, GATING_FACE, tail))
        if root is not None:
            # R3177: the carrier reading rides BELOW the verdict so the pinned
            # PASS token shape stays byte-identical (same law as R3109 below).
            if carrier_row:
                out.append(carrier_row)
            # R3219: the ledger reading rides BELOW the verdict for the same
            # reason - the pinned PASS token shape stays byte-identical.
            if ledger_row:
                out.append(ledger_row)
            # R3109: a PASS that does not name the baseline it judged cannot
            # be re-checked by the reader who quotes it. The identity row is a
            # READING (no threshold, no gate) and rides below the verdict so
            # the shipped PASS token shape stays byte-identical.
            ident = _baseline_identity(baseline, root)
            if ident:
                out.append(ident)
        # The informational debt is never silent: a baselined file no family
        # decodes is still named on every closeout, it just does not refuse.
        out.extend(line for line in census_lines
                   if line.startswith("[refuse-read]"))
        return out, 0, (_pub(verdict) if root is not None else verdict)

    out.append("CLOSEOUT-GATE REFUSED reason=E_CLG_DRIFT files=%d flags=%d "
               "reader_refused=%d gating=%s"
               % (count, flags, refused, GATING_FACE))
    for line in census_lines:
        if line.startswith("[flag]") or line.startswith("[refuse-read]"):
            out.append(line)
    drift = {"verdict": "REFUSED", "reason": "E_CLG_DRIFT",
             "files": count, "flags": flags,
             "reader_refused": refused, "gating": GATING_FACE}
    return out, 2, (_pub(drift) if root is not None else drift)


def main(argv=None):
    target = os.path.join(ROOT, "qa")
    lines, code, _verdict = evaluate(
        target, os.path.join(target, CENSUS.BASELINE_NAME), root=ROOT)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
