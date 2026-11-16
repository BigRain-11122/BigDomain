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

ASCII source only (repository encoding law). Product text is read from the live
state, never authored here.
"""

import argparse
import datetime as dt
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


def check(export_path, state_path):
    state = load_state(state_path)
    round_int, narrative = newest_round(state)
    if round_int is None or not narrative:
        print("E_SXF_NO_ROUND: state.json log carries no narrative round line")
        return 5
    doc = json.loads(read_text(export_path))
    tag = "R%d" % round_int
    current = doc.get("do") or ""
    face = (doc.get("ceo_face") or {}).get("current") or ""
    problems = []
    # The LEADING round tag is what "current" means. A mere mention is not enough:
    # the first negative control measured PASS because the narrative names its own
    # round twice, so rewinding the leading tag left a second mention behind.
    for label, value in (("do", current), ("ceo_face.current", face)):
        match = ROUND_RE.search(value)
        leading = "R" + match.group(1) if match else "none"
        if leading != tag:
            problems.append("%s leads with %s, expected %s" % (label, leading, tag))
    if problems:
        print("VERDICT %s FAIL" % tag)
        for problem in problems:
            print("E_SXF_STALE: " + problem)
        return 2
    print("VERDICT %s PASS: do and ceo_face.current both name %s" % (tag, tag))
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
            missing.append(key)
    if missing:
        print("E_SXF_NO_KEY: export has no line-anchored key for %s" % ",".join(missing))
        return 6
    parsed = json.loads(text)
    if parsed.get("do") != narrative or (parsed.get("ceo_face") or {}).get("current") != narrative:
        print("E_SXF_WRITE: parsed values moved away from the derived narrative")
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


def main(argv):
    parser = argparse.ArgumentParser(description="Tie the CEO three-line face to the live round.")
    parser.add_argument("--check", action="store_true", help="fail when the export lags the live round")
    parser.add_argument("--apply", action="store_true", help="write derived rows into the export")
    parser.add_argument("--dry-run", action="store_true", help="report what --apply would change")
    args = parser.parse_args(argv)
    if args.check and args.apply:
        print("E_SXF_USAGE: choose --check or --apply")
        return 64
    if args.check:
        return check(EXPORT, STATE)
    if args.apply:
        return apply(EXPORT, STATE, BACKLOG, PREVIEW, dry_run=args.dry_run)
    parser.print_help()
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
