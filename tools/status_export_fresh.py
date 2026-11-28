"""Keep the CEO three-line face in docs/status-export.json tied to the live round.

Measured at R2820 open: the export carried do/ceo_face.current = R2796 while the
state.json log tail carried R2819, and its own export_ts read the current day, so
a fresh timestamp was masking a 23-round-old sentence. This tool derives the
three rows from the live sources and refuses to call a stale file current.

Criteria (pinned in src/os/backlog.md at R2820 BEFORE this file existed):
  AC-SXF1  --check names the newest round from the log tail and fails E_SXF_STALE
           when do or ceo_face.current does not carry it.
  AC-SXF2  --apply writes export_ts/do/ceo_face.current from that narrative line
           verbatim, and latest_artifact from the newest preview/ file on disk.
  AC-SXF3  next_milestone comes from the newest "[R####] next window" backlog row
           and its due hour claim (12h when the row says <=12h, else 48h).
  AC-SXF4  --apply is idempotent with the clock held: a second run over the same
           inputs leaves the file byte-identical (measured R3303: a fixed-clock
           pair produced sha16 c056a4c555cd4945 twice). Across seconds the only
           bytes that move are export_ts/updated_at/census_ts - the apply's own
           moment - so this criterion is a statement about the writer being a
           function of its inputs, not about two wall-clock runs.
  AC-SXF5  fail-closed on no narrative round (rc=5, zero bytes written); output
           stays UTF-8 without BOM and LF only.

Added at R2821 (pinned in src/os/backlog.md BEFORE this code), because the file
read PASS while carrying two provable falsehoods and 89 percent of its bytes in
one unmaintained key:
  AC-SXF6  the top-level "current" is a third synonym of the same sentence and is
           graded exactly like do and ceo_face.current.
  AC-SXF7  state_bytes must equal os.path.getsize(state.json); --apply recomputes
           it rather than the criterion being relaxed.
  AC-SXF8  the live document stays under EXPORT_MAX_BYTES, and a results_archive
           pointer must resolve to a file on disk whose sha256 still matches.
  AC-SXF9  archiving is lossless: the archive carries every entry it took over and
           the live count equals that number.
  AC-SXF10 this tool must be registered in the battery (control, not product).

Added at R2823 (pinned in src/os/backlog.md BEFORE this code), because the CEO
read a mid-sentence fragment as the current line AND the two faces that publish
the same field disagreed on a healthy tree:
  AC-SXF11 the round HEADLINE wins: a skip marker that merely MENTIONS "log
           items" must not demote the headline, and the fold summary must still
           be skipped.
  AC-SXF12 a value carrying the right round tag but not the headline reddens
           E_SXF_FRAGMENT, so a continuation line cannot read PASS again.
  AC-SXF13 latest_artifact excludes meta board pages by IMPORTING the one shipped
           definition (export_round.BOARD_PAGES) instead of repeating the names.

Added at R2824 (pinned in src/os/backlog.md BEFORE this code), because two of the
three rows this document must carry existed TWICE with different values and
neither copy was graded: apply() only ever wrote the 4-space ceo_face copies, so
the top-level latest_artifact and next_milestone had no writer at all and could
only rot, while check() graded do/ceo_face.current/current and nothing else:
  AC-SXF14 the two copies of next_milestone must be equal to each other and to
           the derivation; a landed value that is a strict prefix of the derived
           one is reported as E_SXF_MILESTONE_FRAGMENT instead of merely stale.
  AC-SXF15 the two copies of latest_artifact must be equal to each other and to
           newest_artifact()'s line.
  AC-SXF16 the milestone is never cut mid-word: milestone_text() lands the row
           whole while it fits under MILESTONE_MAX, and otherwise cuts at the
           last clause boundary with an explicit "(truncated)" marker. The writer
           and the grader call that one function.

Added at R3107 (pinned in src/os/backlog.md BEFORE this code), because the CEO
face answered "when is the next milestone due" TWICE and the two answers were
12.7 hours apart on a tree every gate called healthy: export_ts=23:24:44 landed
ceo_face.next_milestone_due=+48.0h while the top-level copy still read +35.34h
from an earlier window, because apply() only ever wrote the ceo_face copy and
_ensure_top covered the other two rows but not this one:
  AC-SXF21 next_milestone_due is a DERIVED row (export_ts + the milestone row's
           own 12/48h claim), published to BOTH copies by --apply and graded on
           both copies against that derivation. Equality alone is not enough: two
           copies carrying the same wrong hour still redden, because agreeing on
           a false hour is not truth.

Added at R3222 (pinned in src/os/backlog.md BEFORE this code), because the two
counts R3221 published into the gate's verdict had no real reader: measured by
an AST census of the whole tree, every `ledger_rows` / `ledger_broken` site was
a test, a probe, or `closeout_gate`'s own definition, while docs/status-export
.json - the one file both the CEO and a machine read - carried no field for
them. A count published where only a test looks is the same complaint as a
count printed only as prose:
  AC-SXF23 the export carries a "chain" block whose rows/broken/path equal the
           live judgement, derived at check time by closeout_gate.check_ledger
           (one definition, no second parser, root read at call time). Absent is
           E_SXF_CHAIN_MISSING; different numbers are E_SXF_CHAIN_STALE.
  AC-SXF24 --apply publishes that block from the same derivation, so a world
           whose adjacent ledger rows do not link lands broken=1 rather than a
           hardcoded 0, and a second --apply leaves the file byte-identical.
  AC-SXF25 publishing is not gating: a broken chain still reads VERDICT PASS.
           The block adds no refusal and moves no PASS token, no evidence byte
           and no ledger byte.

Added at R3228 (pinned in src/os/backlog.md BEFORE this code), because R3227's
`historic=` split was printed only on the closeout's stdout: the export face the
CEO downloads carried 19 keys and no claims reading at all, and the whole-tree
census found no machine consumer of the split. Probed first (qa/probe-R3228.log):
a world with two claims counted 1 captured + 1 contradicted, and publishing the
reading as a JSON block moved NOTHING (delta zero on every counter) while the
same reading written as prose moved claimed 2 -> 3 / uncaptured 0 -> 1. So the
published shape is part of the law, not a detail of it:
  AC-SXF27 the export carries a "claims" block whose contradicted/historic/rows
           /present equal the live census, derived at check time by
           closeout_gate.check_claims (one definition, no second census, root
           read at call time). Absent is E_SXF_CLAIMS_MISSING; different numbers
           are E_SXF_CLAIMS_STALE.
  AC-SXF28 --apply publishes that block from the same derivation, so a world
           carrying a real contradiction lands contradicted=1 rather than a
           carried zero, and a second --apply on a pinned clock leaves the file
           byte-identical.
  AC-SXF29 publishing is not gating and the shape is part of the proof: a world
           with contradicted>0 still reads VERDICT PASS, the published block
           adds ZERO `rows=` tokens to the export text (the census counts those,
           and the block must not feed the number it publishes), and the chain
           block, do/ceo_face.current and next_milestone_due are unchanged.

Added at R3229 (pinned in src/os/backlog.md BEFORE this code), because the four
shipped keys published the contradiction count but not the largest number the
same census already knew - how many handwritten claims have nothing behind them
(uncaptured), and the denominator that makes it readable (claimed/captured).
Probed first (qa/probe-R3229.log): a private world with 1 captured + 1 prose
claim answered the same six counters before and after publishing either shape,
a 7-key block cost +46 bytes and carried no `rows=` token, and a legacy 4-key
block was refused by name (E_SXF_CLAIMS_STALE) rather than silently accepted:
  AC-SXF30 the block carries all seven readings (claimed/captured/contradicted/
           uncaptured/historic/rows/present) and each equals the gate's own
           reading (one census, no second reader, root resolved at call time).
           A missing block is E_SXF_CLAIMS_MISSING; one altered number is
           E_SXF_CLAIMS_STALE; a legacy four-key block is STALE, not accepted.
  AC-SXF31 publication stays invisible to the number it publishes: a world with
           one captured and one uncaptured claim answers the same six counters
           after the block lands, their conservation holds (captured +
           contradicted + uncaptured == claimed), and the landed block carries
           zero `rows=` tokens.
  AC-SXF32 the change is additive: the chain block keeps its four keys, do and
           ceo_face.current stay the derived narrative, next_milestone_due keeps
           its 48h derivation, and a second --apply on a pinned clock is
           byte-identical.

Added at R3520 (pinned in src/os/backlog.md BEFORE this code), because ONE row of
the CEO face was written by the other writer and graded by neither: --apply left
ceo_face.board_pages_skipped exactly as it found it, so the workaround
(src/os/export_round.py) had to run every closeout or the row could silently
drift while this face called the document healthy:
  AC-SXF41 the row is a DERIVED row: ceo_face.board_pages_skipped equals the
           skipped list of the SAME derivation that names latest_artifact
           (export_round.newest_artifact, imported - no second definition).
           Absent is E_SXF_BOARD_SKIP_MISSING; one different element (or a
           non-list) is E_SXF_BOARD_SKIP_STALE.
  AC-SXF42 --apply publishes that list and leaves the rest of the document to
           its existing laws; a second apply on a pinned clock is byte-identical.
  AC-SXF43 the row is not decoration: a world whose newest pair on disk is a
           meta board page derives a NON-EMPTY list, and after that list lands a
           document rewound to [] reddens by name rather than passing.

ASCII source only (repository encoding law). Product text is read from the live
state, never authored here.
"""

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Kept apart from ROOT: ROOT is rebound by the battery suite to a private world,
# but the module that DEFINES "the CEO's latest artifact" always lives in the
# real tree (AC-SXF13 imports it rather than repeating the definition).
REAL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
PREVIEW = os.path.join(ROOT, "preview")
ARCHIVE_DIR = os.path.join(ROOT, "logs")
EXPORT_MAX_BYTES = 60000
# AC-SXF16: the milestone used to be cut at 400 chars mid-word, so the CEO read
# half a sentence ("...695 suites / 5207"). A clause cut carrying an explicit
# marker is the only truncation this face allows.
MILESTONE_MAX = 1200
MILESTONE_MARK = " (truncated)"
LEGACY_KEY = "results"
# AC-SXF41 (R3520): the one row src/os/export_round.py wrote and this face did
# not, so a document refreshed here could carry a stale audit of the board pages
# passed over while every law in this file read green.
BOARD_SKIP_KEY = "board_pages_skipped"

ROUND_RE = re.compile(r"\bR(\d{4})\b")
NEXT_ROW_RE = re.compile(r"\[R(\d{4})\] next window")
NARRATIVE_SKIP = ("tokens:", "log items", "honest disclosures")


_LEDGER_MODULE = None


def _ledger_lines_module():
    """The shipped law module, loaded once and shared by every borrowed shape."""
    global _LEDGER_MODULE
    if _LEDGER_MODULE is None:
        import importlib.util

        path = os.path.join(REAL_ROOT, "src", "os", "ledger_lines.py")
        spec = importlib.util.spec_from_file_location("ledger_lines_shared",
                                                      path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _LEDGER_MODULE = module
    return _LEDGER_MODULE


_CEC_MODULE = None


def _cec_module():
    """The shipped consistency checker, loaded once (AC-SXF36).

    R3360 measured that this face graded neither the self_drive counts nor the
    tick row, so the staleness R3358 had to chase live was visible to
    check_export_consistency alone. The DERIVATION stays single-sourced: this
    loads that module from the real tree and asks its recompute() instead of
    recounting the log here a second time.
    """
    global _CEC_MODULE
    if _CEC_MODULE is None:
        import importlib.util

        path = os.path.join(REAL_ROOT, "src", "os",
                            "check_export_consistency.py")
        spec = importlib.util.spec_from_file_location("cec_shared", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _CEC_MODULE = module
    return _CEC_MODULE


# The two counts R3358 watched go stale on the live face. The window bounds are
# already graded through the chain/claims blocks, so only the live counts are
# borrowed here rather than the whole derived dict.
SELF_DRIVE_ROWS = ("log_lines_in_window", "substantive_non_idle_mention_lines")


def self_drive_problems(landed_sd, derived, tick, results, label):
    """The three rows this face used to leave ungraded (AC-SXF36, R3360).

    Pure on purpose: every argument is handed in, so each arm can be driven
    without touching the live tree. `derived` is the shipped checker's own
    recount - one derivation, two readers - and is never recomputed here.
    """
    problems = []
    derived = derived or {}
    if not isinstance(landed_sd, dict):
        problems.append(("E_SXF_SELF_DRIVE_MISSING",
                         "self_drive is not an object, so its counts cannot be "
                         "compared with the shipped recount"))
    else:
        for key in SELF_DRIVE_ROWS:
            got = landed_sd.get(key, "<missing>")
            want = derived.get(key)
            if got != want:
                problems.append(("E_SXF_SELF_DRIVE_STALE",
                                 "self_drive.%s stored=%r recomputed=%r"
                                 % (key, got, want)))
    rows = results if isinstance(results, list) else []
    stamped = [row for row in rows
               if isinstance(row, list) and len(row) >= 2 and label
               and row[1] == label]
    if len(stamped) != 1:
        problems.append(("E_SXF_TICK_ROW_SHAPE",
                         "results carries %d row(s) labelled %r, expected exactly 1"
                         % (len(stamped), label)))
    elif str(stamped[0][0]) != str(tick):
        problems.append(("E_SXF_TICK_ROW_STALE",
                         "results tick row stored=%r tick=%r"
                         % (stamped[0][0], tick)))
    return problems


def _round_label_src():
    """The UPPERCASE-label shape, borrowed from the shipped write gate (R2874).

    AC-RLBL3: this face, src/os/export_round.py and src/os/ledger_lines.py must
    answer the SAME question about what a headline is. Reading the constant out
    of that module instead of retyping it is what makes a gate that refuses a
    label and a reader that skips one impossible to drift apart. The module
    lives in the real tree and is stdlib-only; if it cannot be loaded the
    grader refuses loudly rather than grading against a private opinion.
    """
    return _ledger_lines_module().ROUND_LABEL_SRC


def _round_meta_re():
    """The meta-label shape (R3310 AC-EXPW21), same single definition.

    A meta headline is the round's own observation scan, not its artifact; both
    readers prefer a non-meta headline of the newest round and this face must
    expect the SAME line src/os/export_round.py publishes, or the export gate
    would call a correctly published face stale.
    """
    return _ledger_lines_module().ROUND_META_RE


# AC-SXF11: a line that opens "R#### <UPPERCASE>" IS a round headline, whatever
# it goes on to discuss. This is the detector src/os/export_round.py already
# ships as ROUND_HEAD_RE; the label half is the write gate's own string.
HEADLINE_RE = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2} )?R(\d{4}) " + _round_label_src())
META_RE = _round_meta_re()
FOLD_MARK = "fold of log items"


def now_local():
    return dt.datetime.now().astimezone()


def iso(moment):
    return moment.replace(microsecond=0).isoformat()


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def lf_text(path):
    """R3303: one dialect on the way in, because every anchor here is a line.

    The reader (json.loads) tolerates CRLF, so the face was classified as a
    tolerant carrier at R3209 - but _set_line/_set_number/_ensure_top match
    ^<indent>"key": ...(,?)$ and `$` does not match before a CR. On a worktree
    materialised by core.autocrlf=true the writer therefore answered
    E_SXF_NO_KEY for all fourteen keys while --check graded what it could
    still parse. Normalising here repairs an existing CRLF checkout; the pin
    in .gitattributes stops a new one from appearing.
    """
    return read_text(path).replace("\r\n", "\n").replace("\r", "\n")


def load_state(path):
    return json.loads(read_text(path))


def round_of(line):
    """Newest round number a line mentions, or None."""
    hits = ROUND_RE.findall(line or "")
    return max(int(value) for value in hits) if hits else None


def is_headline(line):
    """True when the line opens as a round headline (AC-SXF11)."""
    return bool(HEADLINE_RE.match(line or ""))


def is_fold_summary(line):
    """True for a fold summary, which is never a round narrative.

    The phrase alone is not enough to identify one: R2822's own HEADLINE says
    "the round-aligned fold ... finally ran" and mentions "log items" while
    describing the budget, and the old substring skip demoted that headline to
    a mid-sentence continuation line - which is exactly the fragment the CEO
    then had to read. Structure decides: a summary carries the phrase and does
    NOT open with the headline shape.
    """
    text = line or ""
    if FOLD_MARK not in text.lower():
        return False
    return not is_headline(text)


def headline_body(narrative):
    """The headline with its round label stripped, for cross-writer comparison."""
    return re.sub(r"^(?:\d{4}-\d{2}-\d{2} )?R\d{4}\s+", "", narrative or "")[:80]


def newest_round(state):
    """Return (round_int, narrative_line) from the live state log tail.

    AC-SXF11: the round HEADLINE wins outright. The previous rule skipped any
    line carrying the substring "log items", which was meant to drop the fold
    summary but also dropped every headline that merely mentioned the phrase -
    so the rounds that ran a fold (the ones that matter most) published a
    mid-sentence fragment instead of what the round did.
    """
    log = [line for line in (state.get("log") or []) if isinstance(line, str)]
    # R2835: the window is the round the newest HEADLINE labels, not the largest
    # number any sentence happens to contain. Measured on the real tree: a round
    # narrative that named a private-world fixture round (R9101) rewrote the
    # expected round for every copy of the face, and a healthy closeout then read
    # E_SXF_STALE three times over. A headline's own label is its first token, so
    # it is read from HEADLINE_RE's capture rather than from the maximum mention
    # inside the line, which a body may also inflate.
    label_round = None
    for line in log:
        match = HEADLINE_RE.match(line)
        if not match or is_fold_summary(line):
            continue
        value = int(match.group(1))
        if label_round is None or value > label_round:
            label_round = value
    best_round = label_round
    if best_round is None:
        # No headline at all: fall back to the mention rule so a window that
        # wrote only sub-lines is still anchored somewhere rather than silently
        # reading "no round".
        for line in log:
            value = round_of(line)
            if value is None:
                continue
            if best_round is None or value > best_round:
                best_round = value
    if best_round is None:
        return None, None
    candidates = [line for line in log if round_of(line) == best_round]
    # R2969: a line that merely MENTIONS the round is not that round's
    # narrative. Measured on the real tree: one round's closeout row ended with
    # "the new R2969 board row", so it became a candidate for R2969 and - being
    # earlier in the log - was published as the CEO's sentence while a real
    # R2969 headline sat below it; a healthy closeout then wrote do=old and the
    # gate it must satisfy read stale. The headline's own label is its round
    # (the AC-SXF11/R2835 rule), so the label tier comes first and the mention
    # tiers below are unchanged.
    # R3310 AC-EXPW21: a meta headline is the round's observation scan, never
    # its artifact - prefer the first non-meta headline of the newest round and
    # fall back to position below when the round wrote nothing else. The pattern
    # is src/os/ledger_lines.py's single definition, shared with the writer.
    for line in candidates:
        match = HEADLINE_RE.match(line or "")
        if not match or is_fold_summary(line):
            continue
        if int(match.group(1)) == best_round and not META_RE.match(line or ""):
            return best_round, line
    for line in candidates:
        match = HEADLINE_RE.match(line or "")
        if not match or is_fold_summary(line):
            continue
        if int(match.group(1)) == best_round:
            return best_round, line
    for line in candidates:
        if is_headline(line) and not is_fold_summary(line):
            return best_round, line
    for line in candidates:
        if is_headline(line):
            return best_round, line
    for line in candidates:
        lowered = line.lower()
        if any(marker in lowered for marker in NARRATIVE_SKIP):
            continue
        return best_round, line
    return best_round, (candidates[0] if candidates else None)


def export_round_module():
    """The shipped module that owns what counts as the CEO's latest artifact."""
    import importlib.util

    path = os.path.join(REAL_ROOT, "src", "os", "export_round.py")
    spec = importlib.util.spec_from_file_location("export_round_shared", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def newest_artifact(preview_dir):
    """Newest on-disk file in preview/ as the CEO can actually open it.

    AC-SXF13: the previous version took the newest file of ANY kind, so it named
    meta census boards as the CEO's latest artifact while `src/os/export_round.py`
    excluded them - the two faces graded the same field against different rules
    and disagreed on a healthy tree. The exclusion and the published format are
    now IMPORTED from that one shipped definition instead of repeated here, and
    the boards passed over are named rather than dropped silently.
    """
    shared = export_round_module()
    root = os.path.dirname(os.path.abspath(preview_dir))
    pair, skipped, newest_is_board = shared.newest_artifact(root)
    if pair is None:
        return None
    # R2898 AC-EXPD7: the shared row carries a sixth field (the clock the stamp
    # came from); the fields this face publishes are the first five, and the
    # line itself is still formatted by the one shipped formatter below.
    mtime, html_rel, json_rel, html_bytes, json_bytes = pair[:5]
    html_abs = os.path.join(root, html_rel.replace("/", os.sep))
    stamps = dt.datetime.fromtimestamp(mtime).astimezone()
    return {
        # R2896 AC-EXPD1: the line is formatted by the ONE shipped formatter, so
        # the pair's own date is published by both faces from the same bytes and
        # AC-SXF15 can no longer be satisfied by two formaters that happen to
        # agree today.
        "line": shared.fmt_pair(pair),
        "abs": html_abs,
        "bytes": html_bytes,
        "mtime": iso(stamps),
        "skipped": list(skipped),
        "newest_is_board": bool(newest_is_board),
    }


def milestone_text(row):
    """AC-SXF16: the one definition of what the milestone row publishes.

    A whole row is published verbatim. Only a row that overflows MILESTONE_MAX is
    cut, and it is cut at a clause boundary with an explicit marker, so the CEO
    never reads a sentence that stops mid-word.
    """
    row = (row or "").strip()
    if len(row) <= MILESTONE_MAX:
        return row
    window = row[:MILESTONE_MAX]
    cut = window.rfind("; ")
    if cut <= 0:
        cut = window.rfind(". ")
    if cut <= 0:
        cut = window.rfind(" ")
    if cut <= 0:
        cut = MILESTONE_MAX
    return row[:cut].rstrip() + MILESTONE_MARK


def next_milestone(backlog_path):
    """Newest declared next-window row, verbatim, with its own hour claim."""
    text = read_text(backlog_path)
    rows = []
    for match in NEXT_ROW_RE.finditer(text):
        rows.append((int(match.group(1)), match.start()))
    if not rows:
        return None
    round_int, start = max(rows)
    end = text.find("\n", start)
    row = text[start:end if end != -1 else len(text)].strip()
    hours = 12 if "<=12h" in row else 48
    return {"round": round_int, "row": row, "text": milestone_text(row), "hours": hours}


def sha256_file(path):
    digest = hashlib.sha256()
    with io.open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 16), b""):
            digest.update(block)
    return digest.hexdigest()


# AC-SXF22 (R3118): every write of the live face goes through a same-directory
# stage that the judgeability gate reads BEFORE os.replace, so a refused face
# leaves the live name byte-identical and no residue behind.
STAGE_SUFFIX = ".sxf-stage"


def _stage_path(target):
    return target + STAGE_SUFFIX


def leading_tag(value):
    match = ROUND_RE.search(value or "")
    return "R" + match.group(1) if match else "none"


def check(export_path, state_path):
    state = load_state(state_path)
    round_int, narrative = newest_round(state)
    if round_int is None or not narrative:
        print("E_SXF_NO_ROUND: state.json log carries no narrative round line")
        return 5
    raw = read_text(export_path)
    doc = json.loads(raw)
    tag = "R%d" % round_int
    problems = []
    # AC-SXF34 (R3303): this document is the CEO's download and the only shipped
    # writer splices it through line anchors, so one dialect is a property of the
    # face, not a preference - a CR here is what made every anchor miss.
    if "\r" in raw:
        problems.append(("E_SXF_EOL",
                         "the face carries %d CR; AC-SXF34 requires LF only because "
                         "this writer's anchors are line based" % raw.count("\r")))
    # The LEADING round tag is what "current" means. A mere mention is not enough:
    # the first negative control measured PASS because the narrative names its own
    # round twice, so rewinding the leading tag left a second mention behind.
    # AC-SXF6: the top-level "current" is the third synonym and had no grader at all.
    for label, value in (("do", doc.get("do") or ""),
                         ("ceo_face.current", (doc.get("ceo_face") or {}).get("current") or ""),
                         ("current", doc.get("current") or "")):
        found = leading_tag(value)
        if found != tag:
            problems.append(("E_SXF_STALE",
                             "%s leads with %s, expected %s" % (label, found, tag)))
            continue
        # AC-SXF12: carrying the right round tag is not enough. A mid-sentence
        # continuation also leads with the round number, which is how the CEO
        # came to read "how the change was held to its own criteria" as the
        # current line. The published value must carry the round's HEADLINE.
        body = headline_body(narrative)
        if body and body[:60] not in value:
            problems.append(("E_SXF_FRAGMENT",
                             "%s does not carry the round headline (expected %r, got %r)"
                             % (label, body[:60], value[:60])))
    # AC-SXF7: a field that claims to be derived must agree with its source.
    real_bytes = os.path.getsize(state_path)
    if doc.get("state_bytes") != real_bytes:
        problems.append(("E_SXF_STATE_BYTES",
                         "doc state_bytes=%s real=%d" % (doc.get("state_bytes"), real_bytes)))
    # AC-SXF8: the pointer may not outlive what it points at, and the live file
    # that the CEO actually downloads must stay small enough to be worth opening.
    live_bytes = os.path.getsize(export_path)
    if live_bytes > EXPORT_MAX_BYTES:
        problems.append(("E_SXF_TOO_BIG",
                         "export %dB over waterline %dB" % (live_bytes, EXPORT_MAX_BYTES)))
    archive = doc.get("results_archive")
    if isinstance(archive, dict):
        rel = archive.get("path") or ""
        abs_path = os.path.join(ROOT, rel.replace("/", os.sep)) if rel else ""
        if not rel or not os.path.isfile(abs_path):
            problems.append(("E_SXF_ARCHIVE",
                             "results_archive.path=%r is not on disk" % rel))
        else:
            actual = sha256_file(abs_path)
            if actual != (archive.get("sha256") or ""):
                problems.append(("E_SXF_ARCHIVE",
                                 "archive sha256 %s != disk %s"
                                 % (archive.get("sha256"), actual)))
    # AC-SXF14/15: two of the three rows this document must carry existed TWICE
    # with different values, because apply() only ever wrote the ceo_face copies.
    # A document that answers "what is the latest artifact" twice is not truthful
    # even when one of the answers is stale and the other is current, so both
    # copies must equal each other AND the derivation.
    milestone = next_milestone(BACKLOG)
    derived_milestone = milestone["text"] if milestone else ""
    artifact = newest_artifact(PREVIEW)
    derived_artifact = artifact["line"] if artifact else ""
    face = doc.get("ceo_face") or {}
    # AC-SXF41 (R3520): the row the other writer owned and this face ignored.
    derived_skip = list(artifact.get("skipped") or []) if artifact else []
    landed_skip = face.get(BOARD_SKIP_KEY)
    if not isinstance(landed_skip, list):
        problems.append(("E_SXF_BOARD_SKIP_MISSING",
                         "ceo_face.%s is %r, derived=%r"
                         % (BOARD_SKIP_KEY, landed_skip, derived_skip)))
    elif [str(entry) for entry in landed_skip] != derived_skip:
        problems.append(("E_SXF_BOARD_SKIP_STALE",
                         "ceo_face.%s landed=%r derived=%r"
                         % (BOARD_SKIP_KEY, landed_skip, derived_skip)))
    # AC-SXF21: the due row is a DERIVED row, not a free text. When the backlog
    # carries a next-window row, the only truthful due is export_ts + that row's
    # own hour claim, so both copies are graded against the derivation rather
    # than against each other (two copies agreeing on a wrong hour is not truth).
    pairs = [
        ("next_milestone", doc.get("next_milestone"), face.get("next_milestone"),
         derived_milestone),
        ("latest_artifact", doc.get("latest_artifact"), face.get("latest_artifact"),
         derived_artifact),
    ]
    if milestone:
        try:
            stamp = dt.datetime.fromisoformat(doc.get("export_ts") or "")
        except ValueError:
            problems.append(("E_SXF_DUE_STALE",
                             "export_ts=%r is not an ISO timestamp, so the due row "
                             "cannot be derived" % (doc.get("export_ts"),)))
            stamp = None
        if stamp is not None:
            pairs.append(("next_milestone_due", doc.get("next_milestone_due"),
                          face.get("next_milestone_due"),
                          iso(stamp + dt.timedelta(hours=milestone["hours"]))))
    for label, top, inner, derived in pairs:
        tops = top or ""
        inners = inner or ""
        if tops == derived and inners == derived:
            continue
        code = ("E_SXF_MILESTONE_STALE" if label == "next_milestone"
                else "E_SXF_DUE_STALE" if label == "next_milestone_due"
                else "E_SXF_ARTIFACT_STALE")
        # AC-SXF14 second half: a landed value that is a strict prefix of the
        # derivation was cut rather than left behind, and that is the same
        # complaint the CEO made about the headline fragment at R2823.
        if (label == "next_milestone" and derived and tops
                and derived.startswith(tops) and tops != derived):
            code = "E_SXF_MILESTONE_FRAGMENT"
        problems.append((code, "%s top=%r ceo_face=%r derived=%r"
                         % (label, tops[:60], inners[:60], derived[:60])))
    # AC-SXF23 (R3222): the counts a machine can compare, published on the face
    # a machine reads. Derived here, at check time, so a rewritten ledger cannot
    # leave a stale field green.
    derived_chain = chain_face(ROOT)
    landed_chain = doc.get(CHAIN_KEY)
    if not isinstance(landed_chain, dict):
        problems.append(("E_SXF_CHAIN_MISSING",
                         "%s absent; derived=%s"
                         % (CHAIN_KEY, json.dumps(derived_chain, sort_keys=True))))
    elif landed_chain != derived_chain:
        problems.append(("E_SXF_CHAIN_STALE",
                         "landed=%s derived=%s"
                         % (json.dumps(landed_chain, sort_keys=True),
                            json.dumps(derived_chain, sort_keys=True))))
    # AC-SXF27 (R3228): the same law for the census reading. Published as a
    # reading, never a verdict - a contradicted count of 1 still reads PASS.
    derived_claims = claims_face(ROOT)
    # AC-SXF35 (R3236): the reading is graded against itself, not only against
    # the landed block. A block that equals a non-conserving census is STALE-
    # clean by construction, so the arithmetic needs its own verdict or the
    # defect is silent (measured, qa/probe-R3236.log: rc=0 PASS with 99 claims
    # unaccounted for).
    for violation in claims_arith(derived_claims):
        problems.append(("E_SXF_CLAIMS_ARITH", violation))
    landed_claims = doc.get(CLAIMS_KEY)
    if not isinstance(landed_claims, dict):
        problems.append(("E_SXF_CLAIMS_MISSING",
                         "%s absent; derived=%s"
                         % (CLAIMS_KEY, json.dumps(derived_claims, sort_keys=True))))
    else:
        landed_reading = {key: value for key, value in landed_claims.items()
                          if key != CLAIMS_TS_KEY}
        if landed_reading != derived_claims:
            # AC-SXFB39/AC-SXFB40 (R3383): the block must be the census of the
            # DOCUMENT IT IS WRITTEN IN - the prose rows it sits beside carry
            # `rows=` tokens, so a block derived from an earlier draft reddens
            # here rather than reading clean by construction.
            problems.append(("E_SXF_CLAIMS_STALE",
                             "landed=%s derived=%s (the block must be the census "
                             "of the document it is written in)"
                             % (json.dumps(landed_reading, sort_keys=True),
                                json.dumps(derived_claims, sort_keys=True))))
        # AC-SXF33 (R3231): a reading that cannot state its own age is a defect,
        # and a reading whose age is not this apply's own moment is a DIFFERENT
        # defect - so "no stamp / unusable stamp" and "stamp from another apply"
        # are named separately instead of collapsing into one refusal.
        stamp = landed_claims.get(CLAIMS_TS_KEY)
        if not isinstance(stamp, str) or not stamp:
            problems.append(("E_SXF_CLAIMS_AGE",
                             "%s carries no %s; the reading cannot state its own "
                             "age" % (CLAIMS_KEY, CLAIMS_TS_KEY)))
        else:
            try:
                dt.datetime.fromisoformat(stamp)
            except ValueError:
                problems.append(("E_SXF_CLAIMS_AGE",
                                 "%s=%r is not an ISO timestamp"
                                 % (CLAIMS_TS_KEY, stamp)))
            else:
                if stamp != (doc.get("export_ts") or ""):
                    problems.append(("E_SXF_CLAIMS_AGE_SPLIT",
                                     "%s=%s but export_ts=%s: the reading and the "
                                     "face were not written by one apply"
                                     % (CLAIMS_TS_KEY, stamp,
                                        doc.get("export_ts"))))
    # AC-SXF36 (R3360): three rows this face could not see. R3358 chased a
    # self_drive block whose two counts and tick row were stale while --check
    # read PASS, because only check_export_consistency compared them. The
    # boundary is the shipped writer's own (src/os/export_round.py refreshes
    # self_drive for the real tree only), so a private world prints a NAMED
    # skip line rather than passing silently.
    cec = _cec_module()
    if os.path.abspath(state_path) != os.path.abspath(cec.P_STATE):
        print("self_drive graded=0 skipped=private-world: %s is not the real "
              "tree state, so the shipped recount does not describe it"
              % state_path)
    else:
        try:
            derived_sd, cec_state, _cec_export, cec_pat = cec.recompute()
        except (ValueError, KeyError, OSError) as exc:
            problems.append(("E_SXF_SELF_DRIVE_UNREADABLE",
                             "the shipped recount refused the live tree: %s: %s"
                             % (type(exc).__name__, exc)))
        else:
            problems.extend(self_drive_problems(
                doc.get("self_drive"), derived_sd, cec_state.get("tick"),
                doc.get(LEGACY_KEY), cec_pat.get("tick_row_label")))
    # AC-SXF37 (R3459): one document, one verdict. R3458 measured this tool
    # answering PASS over a docs/status-export.json that
    # `src/os/export_round.py --check` called FAIL 4 on a clean tree - two
    # shipped graders contradicting each other about one file, and the CEO reads
    # whichever he opens. This face may ADD laws (the AC-SXF* family) but it can
    # no longer certify a document the export grader refuses: that grader is
    # imported, never re-implemented.
    live_export = os.path.join(REAL_ROOT, "docs", "status-export.json")
    if os.path.abspath(export_path) == os.path.abspath(live_export):
        try:
            outside = export_round_module().check(REAL_ROOT)
        except (ValueError, KeyError, OSError) as exc:
            problems.append(("E_SXF_EXPORT_ROUND",
                             "the export grader refused to read the live tree: "
                             "%s: %s" % (type(exc).__name__, exc)))
        else:
            for one in outside:
                problems.append(("E_SXF_EXPORT_ROUND", one))
    else:
        print("export_round graded=0 skipped=private-world: %s is not the live "
              "docs/status-export.json" % export_path)
    if problems:
        print("VERDICT %s FAIL" % tag)
        for code, problem in problems:
            print("%s: %s" % (code, problem))
        return 2
    print("VERDICT %s PASS: do, ceo_face.current and current all name %s" % (tag, tag))
    print("state_bytes=%d export_bytes=%d archive=%s"
          % (real_bytes, live_bytes,
             (doc.get("results_archive") or {}).get("path") or "none"))
    print("export_ts=%s" % (doc.get("export_ts") or ""))
    print("chain rows=%d broken=%d path=%s"
          % (derived_chain["rows"], derived_chain["broken"], derived_chain["path"]))
    print("claims claimed=%d captured=%d uncaptured=%d contradicted=%d "
          "historic=%d rows=%d present=%s"
          % (derived_claims["claimed"], derived_claims["captured"],
             derived_claims["uncaptured"], derived_claims["contradicted"],
             derived_claims["historic"], derived_claims["rows"],
             "true" if derived_claims["present"] else "false"))
    print("claims age=%s (pinned to export_ts by AC-SXF33)"
          % (landed_claims.get(CLAIMS_TS_KEY) or "unknown"))
    return 0


def _set_line(text, key, value, indent):
    """Replace one line-anchored JSON string value, preserving all other bytes."""
    pattern = re.compile(r'^%s"%s": ".*?"(,?)$' % (re.escape(indent), re.escape(key)), re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return text, False
    payload = json.dumps(value, ensure_ascii=False)
    replacement = "%s\"%s\": %s%s" % (indent, key, payload, match.group(1))
    return text[:match.start()] + replacement + text[match.end():], True


def _set_number(text, key, value, indent):
    """Replace one line-anchored JSON integer value, preserving all other bytes."""
    pattern = re.compile(r'^%s"%s": -?\d+(,?)$' % (re.escape(indent), re.escape(key)), re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return text, False
    replacement = "%s\"%s\": %d%s" % (indent, key, value, match.group(1))
    return text[:match.start()] + replacement + text[match.end():], True


def _ensure_top(text, key, value, indent="  "):
    """AC-SXF14/15: publish a top-level row, inserting it when no writer ever did.

    Two writers over one file is how the two copies came to disagree; rather than
    deleting a copy an unknown consumer may read, the writer makes BOTH copies
    carry the same derived value and the gate refuses any document where they
    differ. When the key is absent the row is inserted after "current", so a
    document produced by the other writer is repaired instead of refused.
    """
    text, ok = _set_line(text, key, value, indent)
    if ok:
        return text, True
    anchor = re.compile(r'^%s"current": .*?,(?=\n)' % re.escape(indent), re.MULTILINE)
    match = anchor.search(text)
    if not match:
        return text, False
    row = "\n%s\"%s\": %s," % (indent, key, json.dumps(value, ensure_ascii=False))
    return text[:match.end()] + row + text[match.end():], True


CHAIN_KEY = "chain"
ADJUDICATION_KEY = "adjudication"


def adjudication_face(reading):
    """R3619 (AC-EXA2/AC-EXA3): the break QUALIFICATION, rendered where it is counted.

    `broken` is a count and, by the ledger's own law (AC-QALB34), never says
    what a break IS: five broken links can be five lost records or five lawful
    progress-partials. The count station learned that last window (R3618); the
    CEO face still published only the count, so `broken=5` read as five lost
    records on the one face a reader is asked to believe.

    `qa_log.chain_reading` is the shipped helper that asks the owner of that
    judgement (`qa_chain_diagnose`) in process. This face renders its answer:
    no second link law, no second kind vocabulary, no local arithmetic.

    `reading is None` means asked and got nothing; that is published as
    UNADJUDICATED with null numbers, never defaulted to OK/0.

    R3648 (AC-EXV1): a classification is not a verification. R3647 taught the
    adjudicator to compare every break's last row with the evidence file on
    disk, and this face still published only the kind, so a reader could not
    tell five breaks whose files are present from five whose files were
    silently rewritten. `landed_ok`, `landed_missing` and `rewritten` are
    passed through from the same reading - counted there, never here.
    """
    if reading is None:
        return {"partial": None, "declared": None, "unexplained": None,
                "adjudication": "UNADJUDICATED", "landed_ok": None,
                "landed_missing": None, "rewritten": None}
    return {"partial": reading["partial"],
            "declared": reading["declared"],
            "unexplained": reading["unexplained"],
            "adjudication": reading["verdict"],
            "landed_ok": reading.get("landed_ok"),
            "landed_missing": reading.get("landed_missing"),
            "rewritten": reading.get("rewritten")}


def chain_face(root):
    """AC-SXF23 (R3222): the ledger counts, read by the gate's OWN face.

    The values come from `closeout_gate.check_ledger(root, reading)`, which fills
    the reading from the same `qa_log.ledger_report` it renders - so the export,
    the gate's verdict and the printed LEDGER row are three renderings of ONE
    report. `root` is a parameter and is resolved at call time: an import-time
    default would keep aiming at the live tree once a suite rebinds ROOT.

    R3224 (AC-SXF26): the block also carries `present`. Measured this window:
    an absent ledger and an empty one published the identical `rows=0`, so the
    CEO face could not tell "no ledger exists" from "the ledger was measured
    and holds nothing". `present` is passed through from the same reading (no
    second stat, no second parser); `None` rather than `False` if the reading
    ever stops carrying it, because inventing a `False` would be a claim this
    face did not measure.

    R3619 (AC-EXA1..AC-EXA5): the block also carries the QUALIFICATION of its
    own break count - `partial`, `declared`, `unexplained` and `adjudication` -
    read in this same place from `qa_log.chain_reading(<this world's ledger>)`,
    which asks `qa_chain_diagnose` in process. The four existing keys keep
    their values and their order; the new ones are appended.
    """
    for path in (os.path.join(REAL_ROOT, "tools"),
                 os.path.join(REAL_ROOT, "src", "os")):
        if path not in sys.path:
            sys.path.insert(0, path)
    import closeout_gate as CG
    import qa_log as QL
    reading = {}
    CG.check_ledger(root, reading)
    block = {"present": reading.get("present"),
             "rows": reading.get("rows", 0),
             "broken": reading.get("broken", 0),
             "path": "state/" + QL.LEDGER_NAME}
    # R3619 (AC-EXA1): the qualification is asked of the same helper the
    # command-line station asks, against THIS world's ledger - a second count
    # here would let the two faces disagree about the same bytes.
    block.update(adjudication_face(
        QL.chain_reading(os.path.join(root, "state", QL.LEDGER_NAME))))
    # R3621 (AC-EXE2): `broken` counts the links that are still unexplained by
    # the count station, while the adjudicator counts every unlinked row - the
    # difference is exactly the rows that station excuses on their own later
    # declaration. Published from the SAME check_ledger report above, so the
    # block can be reconciled: broken + excused == partial + declared +
    # unexplained. `None` if that reading ever stops carrying it, because
    # inventing a 0 would name a row that was never measured.
    block["excused"] = reading.get("excused")
    return block


CLAIMS_KEY = "claims"
# AC-SXF33 (R3231): the reading states its OWN age. Probed this window
# (qa/probe-R3231.log): the census moved (uncaptured 0 -> 1) while the stamp
# stayed behind and check() still answered rc=0, because every criterion
# compared the block to the census and none compared it to a moment.
CLAIMS_TS_KEY = "census_ts"


def claims_face(root, export_text=None):
    """AC-SXF27 (R3228): the census readings, read by the gate's OWN face.

    The values come from `closeout_gate.check_claims(root, reading)`, which fills
    the reading from the same `claim_census.census` it renders - so the export,
    the gate's CLAIMS row and the verdict's `claims` key are three renderings of
    ONE census.

    Published as a JSON object on purpose (measured, qa/probe-R3228.log): the
    census counts `rows=<n>` tokens, and a JSON `"rows": 4` is not one of them,
    so publishing this reading moves no counter (delta zero on every field),
    while the same reading written as prose moved claimed 2 -> 3 and uncaptured
    0 -> 1. The shape is what keeps the mirror from feeding the number it
    mirrors - no exclusion law is needed and none was added.
    R3229 (AC-SXF30..32): all seven readings ship, not only the four that were
    published at R3228. Measured (qa/probe-R3229.log): the same census counted
    1 captured and 1 uncaptured claim while the export carried neither, so the
    CEO face showed the contradiction count and hid the larger number - claims
    with nothing behind them. `claimed` is published beside them because
    `uncaptured=187` alone names no denominator; the conservation
    (captured + contradicted + uncaptured == claimed) is what makes the number
    checkable by a reader instead of trusted.
    """
    for path in (os.path.join(REAL_ROOT, "tools"),
                 os.path.join(REAL_ROOT, "src", "os")):
        if path not in sys.path:
            sys.path.insert(0, path)
    import closeout_gate as CG
    reading = {}
    CG.check_claims(root, reading, export_text=export_text)
    return {"claimed": reading.get("claimed", 0),
            "captured": reading.get("captured", 0),
            "contradicted": reading.get("contradicted", 0),
            "uncaptured": reading.get("uncaptured", 0),
            "historic": reading.get("historic", 0),
            "rows": reading.get("rows", 0),
            "present": reading.get("present")}


def claims_block(root, moment, export_text=None):
    """The published block: the census reading PLUS the moment it was taken.

    AC-SXF33 (R3231). `claims_face` stays a pure reading with no clock in it, so
    a grader can ask it at any time and get the same answer; the age rides
    beside it and `check` pins it to `export_ts`. The two are written from the
    same `moment` in `apply`, which is what makes "one apply" a fact a machine
    can verify instead of a convention a reader has to trust.

    `export_text` (AC-SXFB39, R3383) asks the census about a CANDIDATE document
    - the one this apply is about to land - instead of the one on disk.
    """
    block = claims_face(root, export_text=export_text)
    block[CLAIMS_TS_KEY] = iso(moment)
    return block


READING_KEYS = ("claimed", "captured", "contradicted", "uncaptured", "historic",
                "rows", "present")


def _reading(block):
    """The six readings a block carries, without its own age stamp."""
    return {key: (block or {}).get(key) for key in READING_KEYS}


def settle_claims(text, moment, root=None, limit=3):
    """Write the census block until the DOCUMENT IT LANDS reads back the same.

    AC-SXFB39 (R3383). Measured at R3382: `export_round` landed claimed=40 /
    uncaptured=33 and `--check` derived 41/34 from the very document it had just
    written, reddening `E_SXF_CLAIMS_STALE` on every run. The cause is not
    arithmetic - the export face carries `rows=` tokens inside its own prose
    rows (`latest_artifact`, `next_milestone`), so a block derived from the
    document as it stood BEFORE this apply's prose edits is stale the moment it
    lands. The writer must ask the census about the text it is about to land.

    Publishing the block itself adds no `rows=` token (it is JSON), so one pass
    normally settles; the loop proves that rather than assuming it, and refuses
    by name when the document will not hold still. Returns
    `(text, block, settled)`; `block` is None only when the document has no
    line-anchored claims row.
    """
    moment_root = ROOT if root is None else root
    block = None
    for _pass in range(max(1, limit)):
        candidate = claims_block(moment_root, moment, export_text=text)
        new_text, ok = _ensure_block(text, CLAIMS_KEY, candidate, "  ")
        if not ok:
            return text, None, False
        text = new_text
        block = candidate
        if _reading(claims_face(moment_root, export_text=text)) == _reading(block):
            return text, block, True
    return text, block, False


CLAIMS_ARITH_KEYS = ("claimed", "captured", "contradicted", "uncaptured",
                     "historic", "rows")


def claims_arith(reading):
    """AC-SXF35 (R3236): named violations of the reading's own arithmetic.

    The six readings are only readable if they add up. Probed
    (qa/probe-R3236.log): a world whose landed block EQUALED a census reading of
    claimed=100 / captured=1 / contradicted=0 / uncaptured=0 answered
    `--check` rc=0 VERDICT PASS - every criterion compared the block to the
    census, so 99 claims with nothing behind them were invisible. The HTTP card
    printed a `class=fail` sentence about it, which is a rendering a reader may
    miss, not a gate.

    Violations are returned one per line so a red print names the law that
    broke instead of collapsing three defects into one refusal. An unusable
    reading (non-integer or negative counter) is reported first and short
    circuits, because a sum over it would be a second guess.
    """
    bad = []
    for key in CLAIMS_ARITH_KEYS:
        value = reading.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            bad.append("%s=%r is not a non-negative integer" % (key, value))
    if bad:
        return bad
    total = (reading["captured"] + reading["contradicted"]
             + reading["uncaptured"])
    if total != reading["claimed"]:
        bad.append("captured + contradicted + uncaptured = %d but claimed = %d"
                   % (total, reading["claimed"]))
    if reading["historic"] > reading["contradicted"]:
        bad.append("historic = %d exceeds contradicted = %d (historic is a "
                   "sub-count, never a reclassification)"
                   % (reading["historic"], reading["contradicted"]))
    return bad


def _ensure_block(text, key, mapping, indent="  "):
    """Publish a derived one-line object, replacing whatever shape is on disk.

    A landed block may be one line (this writer) or spread over several by
    json.dumps (a fixture world, or a future writer), so the replacement walks
    brace depth to its closing line instead of assuming a single line. The
    payload is our own dict of two integers and one relative path, so brace
    counting is safe here; a value carrying braces would need a real parse.
    """
    payload = json.dumps(mapping, ensure_ascii=False)
    prefix = "%s\"%s\": " % (indent, key)
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        end = index
        rest = line[len(prefix):]
        if "{" in rest:
            depth = rest.count("{") - rest.count("}")
            while depth > 0 and end + 1 < len(lines):
                end += 1
                depth += lines[end].count("{") - lines[end].count("}")
        comma = "," if lines[end].rstrip().endswith(",") else ""
        lines[index:end + 1] = [prefix + payload + comma]
        return "\n".join(lines), True
    anchor = "%s\"current\": " % indent
    for index, line in enumerate(lines):
        if line.startswith(anchor) and line.rstrip().endswith(","):
            lines[index + 1:index + 1] = [prefix + payload + ","]
            return "\n".join(lines), True
    return text, False


def _ensure_json_list(text, key, rows, indent="  "):
    """Publish a derived list value, replacing whatever shape is on disk.

    The same seam as `_ensure_block`, one bracket type wider: the tick row lives
    inside `results`, which a landed face may keep on one line (this writer) or
    spread over several (a fixture), so the replacement walks bracket depth to
    its closing line instead of assuming a single line.
    """
    payload = json.dumps(rows, ensure_ascii=False)
    prefix = "%s\"%s\": " % (indent, key)
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        end = index
        rest = line[len(prefix):]
        if "[" in rest:
            depth = rest.count("[") - rest.count("]")
            while depth > 0 and end + 1 < len(lines):
                end += 1
                depth += lines[end].count("[") - lines[end].count("]")
        comma = "," if lines[end].rstrip().endswith(",") else ""
        lines[index:end + 1] = [prefix + payload + comma]
        return "\n".join(lines), True
    return text, False


def publish_self_drive(text, derived, tick, results, label):
    """AC-SXF38 (R3460): the rows this writer used to leave for the round hand.

    R3459 carried the debt by name: `--apply` republished the clock, the
    narrative, the artifact, the milestone, the chain and the census, yet a
    freshly applied face still answered `E_SXF_SELF_DRIVE_STALE` and
    `E_SXF_TICK_ROW_STALE`, so every window typed those numbers in by hand - and
    a hand-typed number is exactly what this face exists to stop.

    The derivation is the shipped checker's own `recompute`, asked through the
    loader the gate uses, because publishing from a second recount would create
    the second authority AC-SXF36 removed. The tick row is REFRESHED, never
    invented: a document with zero or two labelled rows is graded
    `E_SXF_TICK_ROW_SHAPE` at check time, and minting one here would decide a
    shape question this writer cannot see.
    """
    notes = []
    tick_published = False
    text, ok = _ensure_block(text, "self_drive", derived, "  ")
    if not ok:
        notes.append("self_drive")
    if isinstance(results, list):
        stamped = [row for row in results
                   if isinstance(row, list) and len(row) >= 2 and row[1] == label]
        if len(stamped) == 1:
            fresh = json.loads(json.dumps(results))
            for row in fresh:
                if isinstance(row, list) and len(row) >= 2 and row[1] == label:
                    row[0] = str(tick)
            text, ok = _ensure_json_list(text, "results", fresh, "  ")
            if not ok:
                notes.append("results")
            else:
                tick_published = True
    return text, notes, tick_published


def apply(export_path, state_path, backlog_path, preview_dir, dry_run=False):
    state = load_state(state_path)
    round_int, narrative = newest_round(state)
    if round_int is None or not narrative:
        print("E_SXF_NO_ROUND: state.json log carries no narrative round line")
        return 5
    artifact = newest_artifact(preview_dir)
    if artifact is None:
        print("E_SXF_NO_ARTIFACT: preview/ carries no file to name")
        return 5
    milestone = next_milestone(backlog_path)
    moment = now_local()
    due = moment + dt.timedelta(hours=milestone["hours"] if milestone else 48)

    text = lf_text(export_path)
    milestone_line = milestone["text"] if milestone else ""
    edits = [
        ("", "export_ts", iso(moment), "  "),
        ("", "do", narrative, "  "),
        ("", "current", narrative, "  "),
        ("", "current", narrative, "    "),
        ("", "latest_artifact", artifact["line"], "    "),
        ("", "last_artifact", artifact["line"], "    "),
        ("", "latest_artifact_abs", artifact["abs"], "    "),
        ("", "next_milestone", milestone_line, "    "),
        ("", "next_milestone_due", iso(due), "    "),
        ("", "updated_at", iso(moment), "    "),
    ]
    missing = []
    # AC-SXF14/15: the top-level copies are published by the same derivation, so
    # the file the CEO downloads can no longer answer these two questions twice.
    for key, value in (("latest_artifact", artifact["line"]),
                       ("next_milestone", milestone_line),
                       ("next_milestone_due", iso(due))):
        text, ok = _ensure_top(text, key, value, "  ")
        if not ok:
            missing.append(key + "@top")
    for _, key, value, indent in edits:
        text, ok = _set_line(text, key, value, indent)
        if not ok:
            missing.append(key + "@" + indent.strip())
    # AC-SXF24 (R3222): the block is published from the same derivation the
    # grader uses, so a broken chain lands broken=1 instead of a carried zero.
    chain = chain_face(ROOT)
    text, ok = _ensure_block(text, CHAIN_KEY, chain, "  ")
    if not ok:
        missing.append(CHAIN_KEY)
    # AC-SXF42 (R3520): the board-page audit is published from the derivation
    # that already named latest_artifact, so both writers of this document now
    # carry the same answer instead of one writing and one skipping the row.
    derived_skip = list(artifact.get("skipped") or [])
    text, ok = _ensure_json_list(text, BOARD_SKIP_KEY, derived_skip, "    ")
    if not ok:
        missing.append(BOARD_SKIP_KEY + "@ceo_face")
    # AC-SXF38 (R3460): the two rows the round hand used to patch are published
    # from the shipped checker's recount, before the census settles (the
    # self_drive block carries no `rows=` token, so it cannot move that census).
    derived_sd = None
    sd_tick = None
    sd_label = None
    tick_published = False
    try:
        derived_sd, sd_state, _sd_export, sd_pat = _cec_module().recompute(ROOT)
        sd_tick = sd_state.get("tick")
        sd_label = sd_pat["tick_row_label"]
        text, sd_notes, tick_published = publish_self_drive(
            text, derived_sd, sd_tick, json.loads(text).get("results"), sd_label)
    except Exception as exc:  # the derivation is graded by check(), not invented here
        print("E_SXF_SELF_DRIVE_UNDERIVED: %s" % (exc,))
        derived_sd = None
        sd_notes = []
    if sd_notes:
        print("E_SXF_NO_KEY: export has no line-anchored key for %s@self_drive"
              % ",".join(sd_notes))
        return 6
    # AC-SXF28 (R3228): the census reading is published from the same derivation
    # the grader uses. Landing it adds zero `rows=` tokens (JSON shape), so the
    # value it publishes is not moved by publishing it - the second --apply is
    # byte-identical for that reason, not by luck.
    # AC-SXFB39 (R3383): the derivation is asked about THIS document, after every
    # prose edit above - the milestone and artifact rows carry `rows=` tokens, so
    # a block taken from the pre-edit text is stale the moment it lands (R3382
    # measured the writer landing 40/33 while its own verifier derived 41/34).
    text, claims, settled = settle_claims(text, moment, root=ROOT)
    if claims is None:
        missing.append(CLAIMS_KEY)
    elif not settled:
        print("E_SXF_CLAIMS_FIXPOINT: the census does not settle on the document "
              "this apply would land (block=%s derived=%s)"
              % (json.dumps(_reading(claims), sort_keys=True),
                 json.dumps(_reading(claims_face(ROOT, export_text=text)),
                            sort_keys=True)))
        return 9
    # AC-SXF7: the byte count is recomputed from the file, never carried forward.
    text, ok = _set_number(text, "state_bytes", os.path.getsize(state_path), "  ")
    if not ok:
        missing.append("state_bytes")
    if missing:
        print("E_SXF_NO_KEY: export has no line-anchored key for %s" % ",".join(missing))
        return 6
    parsed = json.loads(text)
    # AC-SXF38 (R3460): the rows just published are graded here the way check()
    # will grade them a moment later - one derivation, two callers, so the writer
    # cannot land a face its own gate refuses.
    if derived_sd is not None:
        if parsed.get("self_drive") != derived_sd:
            print("E_SXF_WRITE: self_drive block is not the derived recount "
                  "(landed=%r derived=%r)"
                  % (json.dumps(parsed.get("self_drive"), sort_keys=True),
                     json.dumps(derived_sd, sort_keys=True)))
            return 7
        if tick_published:
            rows = [row for row in (parsed.get("results") or [])
                    if isinstance(row, list) and len(row) >= 2 and row[1] == sd_label]
            if len(rows) != 1 or str(rows[0][0]) != str(sd_tick):
                print("E_SXF_WRITE: results tick row did not land the derived "
                      "round (rows=%r tick=%r)" % (len(rows), sd_tick))
                return 7
    if parsed.get("do") != narrative or (parsed.get("ceo_face") or {}).get("current") != narrative:
        print("E_SXF_WRITE: parsed values moved away from the derived narrative")
        return 7
    if parsed.get("current") != narrative:
        print("E_SXF_WRITE: top-level current is not the derived narrative")
        return 7
    if parsed.get(CHAIN_KEY) != chain:
        print("E_SXF_WRITE: chain block is not the derived judgement (landed=%r derived=%r)"
              % (parsed.get(CHAIN_KEY), chain))
        return 7
    if parsed.get(CLAIMS_KEY) != claims:
        print("E_SXF_WRITE: claims block is not the derived census (landed=%r derived=%r)"
              % (parsed.get(CLAIMS_KEY), claims))
        return 7
    # AC-SXF14/15: the write is only complete when BOTH copies carry the derived
    # value, so a document that leaves one of them behind cannot be published.
    landed_face = parsed.get("ceo_face") or {}
    for key, derived in (("latest_artifact", artifact["line"]),
                         ("next_milestone", milestone_line),
                         ("next_milestone_due", iso(due))):
        pair = (parsed.get(key), landed_face.get(key))
        if pair != (derived, derived):
            print("E_SXF_WRITE: %s copies are not both the derived value (top=%r ceo_face=%r)"
                  % (key, (pair[0] or "")[:40], (pair[1] or "")[:40]))
            return 7
    # AC-SXF42 second half: the audit row landed as the derivation, not as prose.
    landed_skip = landed_face.get(BOARD_SKIP_KEY)
    if not isinstance(landed_skip, list) or [str(e) for e in landed_skip] != derived_skip:
        print("E_SXF_WRITE: ceo_face.%s is not the derived audit (landed=%r derived=%r)"
              % (BOARD_SKIP_KEY, landed_skip, derived_skip))
        return 7
    before = lf_text(export_path)
    changed = text != before
    if dry_run:
        print("DRY %s changed=%s round=R%d bytes_before=%d bytes_after=%d"
              % ("R%d" % round_int, changed, round_int, len(before.encode("utf-8")), len(text.encode("utf-8"))))
        return 0
    # AC-SXF22 (R3118): the R3117 proof ran AFTER the bytes were on disk under
    # the live name, so a refused face was still the face the CEO downloaded -
    # measured on a private world with a naive clock: rc=8 and the live name grew
    # 1173->1149 bytes carrying export_ts without an offset. The stage is judged
    # FIRST, so "refused" and "did not land" are now the same fact.
    stage = _stage_path(export_path)
    with io.open(stage, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os_dir = os.path.join(REAL_ROOT, "src", "os")
    if os_dir not in sys.path:
        sys.path.insert(0, os_dir)
    judge_code, _judge_report = export_round_module().face_judgeable(stage)
    if judge_code:
        os.remove(stage)
        print("E_SXF_UNPROVEN face=STAGED code=%s" % judge_code)
        return 8
    os.replace(stage, export_path)
    after = read_text(export_path)
    # AC-SXF35 (R3303): the applied line used to PRINT lf_only and land anyway.
    # A face that still carries a CR is one this writer cannot repar, so it is
    # refused here rather than left for the next window to discover.
    if "\r" in after:
        print("E_SXF_EOL: applied face still carries %d CR (AC-SXF35)" % after.count("\r"))
        return 9
    # The re-read is a live-name reading, not a second refusal surface: after
    # os.replace the landed bytes ARE the judged bytes, so a code here would mean
    # the judge or the disk moved between the two calls.
    live_code, _live_report = export_round_module().face_judgeable(export_path)
    if live_code:
        print("E_SXF_UNPROVEN face=WRITTEN code=%s" % live_code)
        return 8
    print("APPLIED R%d changed=%s bytes=%d lf_only=%s bom=%s"
          % (round_int, changed, len(after.encode("utf-8")),
             "\r" not in after, after.startswith("\ufeff")))
    print("do->%s" % narrative[:160])
    print("latest_artifact->%s" % artifact["line"])
    if milestone:
        print("next_milestone->R%d %s... due=%s" % (milestone["round"], milestone["text"][:80], iso(due)))
    return 0


def _archive_name(month, index):
    if index == 0:
        return "status-export-legacy-%s.json" % month
    return "status-export-legacy-%s-%d.json" % (month, index)


def archive_legacy(export_path, confirm=False, dry_run=False):
    """Move the unmaintained results block out of the file the CEO downloads.

    Lossless by construction: the archive keeps every entry, and when this month's
    archive already exists the entries are merged rather than overwritten, so two
    windows in one month cannot destroy each other's history.
    """
    doc = json.loads(read_text(export_path))
    legacy = doc.get(LEGACY_KEY)
    if not isinstance(legacy, list):
        existing = doc.get("results_archive")
        if isinstance(existing, dict):
            print("ARCHIVE-SKIP: %s already archived to %s count=%s"
                  % (LEGACY_KEY, existing.get("path"), existing.get("count")))
            return 0
        print("E_SXF_NO_RESULTS: export carries no %s list to archive" % LEGACY_KEY)
        return 5
    month = now_local().strftime("%Y-%m")
    index = 0
    rel = ""
    while True:
        candidate = _archive_name(month, index)
        if not os.path.isfile(os.path.join(ARCHIVE_DIR, candidate)):
            rel = "logs/" + candidate
            break
        index += 1
    abs_path = os.path.join(ARCHIVE_DIR, os.path.basename(rel))
    record = {
        "archived_ts": iso(now_local()),
        "source": "docs/status-export.json",
        "key": LEGACY_KEY,
        "note": "Frozen per-round narratives moved out of the CEO three-line face; "
                "no round maintains them and no gate checked them.",
        "results": legacy,
    }
    body = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    before_bytes = len(read_text(export_path).encode("utf-8"))
    if dry_run or not confirm:
        print("DRY archive=%s entries=%d live_bytes_before=%d payload_bytes=%d"
              % (rel, len(legacy), before_bytes, len(body.encode("utf-8"))))
        if not confirm:
            print("E_SXF_CONFIRM: pass --confirm to write the archive")
            return 64
        return 0
    # AC-SXF22 (R3118): this function rewrites the live face by hand and was
    # judged by nobody (R3118 measured zero production callers, so it had never
    # been exercised outside its own suite). The export rewrite is staged and
    # proven FIRST - before the archive payload is created - so a refusal leaves
    # both the face and logs/ untouched. The pointer digest is computed from the
    # payload bytes, so it can be published before the archive is written, and
    # the equality check below proves the two agree.
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    rewritten = dict(doc)
    rewritten.pop(LEGACY_KEY, None)
    rewritten["results_archive"] = {
        "path": rel,
        "sha256": digest,
        "count": len(legacy),
        "bytes": len(body.encode("utf-8")),
    }
    text = json.dumps(rewritten, ensure_ascii=False, indent=2) + "\n"
    os_dir = os.path.join(REAL_ROOT, "src", "os")
    if os_dir not in sys.path:
        sys.path.insert(0, os_dir)
    stage = _stage_path(export_path)
    with io.open(stage, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    judge_code, _judge_report = export_round_module().face_judgeable(stage)
    if judge_code:
        os.remove(stage)
        print("E_SXF_UNPROVEN face=STAGED code=%s" % judge_code)
        return 8
    if not os.path.isdir(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
    archive_stage = _stage_path(abs_path)
    with io.open(archive_stage, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    # AC-SXF9: prove the archive carries exactly what the live document held.
    archived = json.loads(read_text(archive_stage)).get(LEGACY_KEY) or []
    if archived != legacy or sha256_file(archive_stage) != digest:
        os.remove(archive_stage)
        os.remove(stage)
        print("E_SXF_ARCHIVE_LOSS: staged archive %d entries do not equal live %d"
              % (len(archived), len(legacy)))
        return 8
    os.replace(archive_stage, abs_path)
    os.replace(stage, export_path)
    # Every key other than the moved one must survive untouched.
    after = json.loads(read_text(export_path))
    drift = [key for key in doc if key != LEGACY_KEY and doc[key] != after.get(key)]
    after_bytes = os.path.getsize(export_path)
    print("ARCHIVED %s %d entries %dB sha256=%s"
          % (rel, len(legacy), os.path.getsize(abs_path), digest[:16]))
    print("live %d -> %dB keys_drift=%s archive=%s"
          % (before_bytes, after_bytes, drift or "none", rel))
    return 0 if not drift else 8


def main(argv):
    parser = argparse.ArgumentParser(description="Tie the CEO three-line face to the live round.")
    parser.add_argument("--check", action="store_true", help="fail when the export lags the live round")
    parser.add_argument("--apply", action="store_true", help="write derived rows into the export")
    parser.add_argument("--dry-run", action="store_true", help="report what --apply would change")
    parser.add_argument("--archive-legacy", action="store_true",
                        help="move the frozen results block into logs/ and leave a pointer")
    parser.add_argument("--confirm", action="store_true", help="really write the archive")
    args = parser.parse_args(argv)
    if sum([bool(args.check), bool(args.apply), bool(args.archive_legacy)]) > 1:
        print("E_SXF_USAGE: choose one of --check, --apply, --archive-legacy")
        return 64
    if args.check:
        return check(EXPORT, STATE)
    if args.apply:
        return apply(EXPORT, STATE, BACKLOG, PREVIEW, dry_run=args.dry_run)
    if args.archive_legacy:
        return archive_legacy(EXPORT, confirm=args.confirm, dry_run=args.dry_run)
    parser.print_help()
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
