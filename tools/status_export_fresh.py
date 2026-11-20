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
  AC-SXF4  --apply is idempotent: a second run leaves the file byte-identical.
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

ROUND_RE = re.compile(r"\bR(\d{4})\b")
NEXT_ROW_RE = re.compile(r"\[R(\d{4})\] next window")
NARRATIVE_SKIP = ("tokens:", "log items", "honest disclosures")


def _round_label_src():
    """The UPPERCASE-label shape, borrowed from the shipped write gate (R2874).

    AC-RLBL3: this face, src/os/export_round.py and src/os/ledger_lines.py must
    answer the SAME question about what a headline is. Reading the constant out
    of that module instead of retyping it is what makes a gate that refuses a
    label and a reader that skips one impossible to drift apart. The module
    lives in the real tree and is stdlib-only; if it cannot be loaded the
    grader refuses loudly rather than grading against a private opinion.
    """
    import importlib.util

    path = os.path.join(REAL_ROOT, "src", "os", "ledger_lines.py")
    spec = importlib.util.spec_from_file_location("ledger_lines_shared", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ROUND_LABEL_SRC


# AC-SXF11: a line that opens "R#### <UPPERCASE>" IS a round headline, whatever
# it goes on to discuss. This is the detector src/os/export_round.py already
# ships as ROUND_HEAD_RE; the label half is the write gate's own string.
HEADLINE_RE = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2} )?R(\d{4}) " + _round_label_src())
FOLD_MARK = "fold of log items"


def now_local():
    return dt.datetime.now().astimezone()


def iso(moment):
    return moment.replace(microsecond=0).isoformat()


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


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


def leading_tag(value):
    match = ROUND_RE.search(value or "")
    return "R" + match.group(1) if match else "none"


def check(export_path, state_path):
    state = load_state(state_path)
    round_int, narrative = newest_round(state)
    if round_int is None or not narrative:
        print("E_SXF_NO_ROUND: state.json log carries no narrative round line")
        return 5
    doc = json.loads(read_text(export_path))
    tag = "R%d" % round_int
    problems = []
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

    text = read_text(export_path)
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
    # AC-SXF7: the byte count is recomputed from the file, never carried forward.
    text, ok = _set_number(text, "state_bytes", os.path.getsize(state_path), "  ")
    if not ok:
        missing.append("state_bytes")
    if missing:
        print("E_SXF_NO_KEY: export has no line-anchored key for %s" % ",".join(missing))
        return 6
    parsed = json.loads(text)
    if parsed.get("do") != narrative or (parsed.get("ceo_face") or {}).get("current") != narrative:
        print("E_SXF_WRITE: parsed values moved away from the derived narrative")
        return 7
    if parsed.get("current") != narrative:
        print("E_SXF_WRITE: top-level current is not the derived narrative")
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
    before = read_text(export_path)
    changed = text != before
    if dry_run:
        print("DRY %s changed=%s round=R%d bytes_before=%d bytes_after=%d"
              % ("R%d" % round_int, changed, round_int, len(before.encode("utf-8")), len(text.encode("utf-8"))))
        return 0
    with io.open(export_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    after = read_text(export_path)
    # AC-EXPR3 (R3117): this tool composes AND lands the face with its own
    # io.open, so it is a birth site of its own - R3117 measured that it named
    # the judgeability gate zero times. It now self-proves once after landing:
    # a face this tool wrote that the CEO gate cannot read is named here rather
    # than discovered later on the card.
    os_dir = os.path.join(REAL_ROOT, "src", "os")
    if os_dir not in sys.path:
        sys.path.insert(0, os_dir)
    judge_code, _judge_report = export_round_module().face_judgeable(export_path)
    if judge_code:
        print("E_SXF_UNPROVEN face=WRITTEN code=%s" % judge_code)
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
    if not os.path.isdir(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
    with io.open(abs_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    digest = sha256_file(abs_path)
    # AC-SXF9: prove the archive carries exactly what the live document held.
    archived = json.loads(read_text(abs_path)).get(LEGACY_KEY) or []
    if archived != legacy:
        print("E_SXF_ARCHIVE_LOSS: archived %d entries do not equal live %d"
              % (len(archived), len(legacy)))
        return 8
    rewritten = dict(doc)
    rewritten.pop(LEGACY_KEY, None)
    rewritten["results_archive"] = {
        "path": rel,
        "sha256": digest,
        "count": len(legacy),
        "bytes": os.path.getsize(abs_path),
    }
    text = json.dumps(rewritten, ensure_ascii=False, indent=2) + "\n"
    with io.open(export_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
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
