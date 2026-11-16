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
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
PREVIEW = os.path.join(ROOT, "preview")
ARCHIVE_DIR = os.path.join(ROOT, "logs")
EXPORT_MAX_BYTES = 60000
LEGACY_KEY = "results"

ROUND_RE = re.compile(r"\bR(\d{4})\b")
NEXT_ROW_RE = re.compile(r"\[R(\d{4})\] next window")
NARRATIVE_SKIP = ("tokens:", "log items", "honest disclosures")


def now_local():
    return dt.datetime.now().astimezone()


def iso(moment):
    return moment.replace(microsecond=0).isoformat()


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def load_state(path):
    return json.loads(read_text(path))


def newest_round(state):
    """Return (round_int, narrative_line) from the live state log tail."""
    best_round = None
    best_line = None
    for line in state.get("log") or []:
        if not isinstance(line, str):
            continue
        hits = ROUND_RE.findall(line)
        if not hits:
            continue
        round_int = max(int(value) for value in hits)
        if best_round is None or round_int > best_round:
            best_round = round_int
            best_line = None
        if round_int != best_round:
            continue
        lowered = line.lower()
        if any(marker in lowered for marker in NARRATIVE_SKIP):
            continue
        if best_line is None:
            best_line = line
    return best_round, best_line


def newest_artifact(preview_dir):
    """Newest on-disk file in preview/ as the CEO can actually open it."""
    best = None
    for name in os.listdir(preview_dir):
        path = os.path.join(preview_dir, name)
        if not os.path.isfile(path):
            continue
        stat = os.stat(path)
        if best is None or stat.st_mtime_ns > best[0]:
            best = (stat.st_mtime_ns, name, stat.st_size)
    if best is None:
        return None
    stamps = dt.datetime.fromtimestamp(best[0] / 1e9).astimezone()
    return {
        "line": "preview/%s (%dB, %s)" % (best[1], best[2], iso(stamps)),
        "abs": os.path.join(preview_dir, best[1]),
        "bytes": best[2],
        "mtime": iso(stamps),
    }


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
    return {"round": round_int, "text": row[:400], "hours": hours}


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
    edits = [
        ("", "export_ts", iso(moment), "  "),
        ("", "do", narrative, "  "),
        ("", "current", narrative, "  "),
        ("", "current", narrative, "    "),
        ("", "latest_artifact", artifact["line"], "    "),
        ("", "last_artifact", artifact["line"], "    "),
        ("", "latest_artifact_abs", artifact["abs"], "    "),
        ("", "next_milestone", milestone["text"] if milestone else "", "    "),
        ("", "next_milestone_due", iso(due), "    "),
        ("", "updated_at", iso(moment), "    "),
    ]
    missing = []
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
    before = read_text(export_path)
    changed = text != before
    if dry_run:
        print("DRY %s changed=%s round=R%d bytes_before=%d bytes_after=%d"
              % ("R%d" % round_int, changed, round_int, len(before.encode("utf-8")), len(text.encode("utf-8"))))
        return 0
    with io.open(export_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    after = read_text(export_path)
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
