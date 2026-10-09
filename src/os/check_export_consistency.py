#!/usr/bin/env python3
"""Export derived-face consistency checker (F3 zero-canned enforcement tool).

O-20261009-1246 dispatch-a item. Seeds: C-20261009-02 two-caliber gap lesson,
R1254 export flush-drift fix precedent, R1037 tick-row drift precedent.

CANONICAL CALIBER (single source of truth, codified here -- the closeout
flush must recompute self_drive with THIS caliber so flush and check share
one caliber; that closes the two-caliber gap):

  window          = [max_log_date - 6 days, max_log_date]  (7-day daily roll,
                    R1509/R1619 precedent), where max_log_date is the max
                    ^YYYY-MM-DD prefix across ALL state.json#log lines.
  W               = count of log lines whose date prefix falls in window.
  idle            = window lines containing "idle-fast" (path abolished per
                    P-2026-09-28-02, expected 0).
  nop             = window lines containing "no-pullable" (mention-line
                    caliber, roll-line embeds included; matches the R1672
                    flush semantics).
  sub             = window lines matching ^<date> R<num> (round-anchored main,
                    paren/roll summaries excluded) AND not a tokens line
                    AND not containing "no-pullable" (any mention, so a
                    substantive line merely quoting the phrase is also
                    excluded -- matches R1672 flush semantics) AND not
                    containing the declaration-close marker loaded from the
                    patterns file (declaration/waiting one-line closeout
                    rounds are exempt protection-state, not substantive).
  proposals_total = docs/proposals.md lines matching "^### BD-PROP-".
  proposals_open  = those header lines containing the open-status marker
                    (loaded from export_consistency_patterns.json).
  queue_*_open    = state/queue/{main,tech,explore}.md lines matching
                    "^- [ ]".
  tick row        = the unique docs/status-export.json#results row whose
                    second element equals the tick-row label (loaded from
                    export_consistency_patterns.json); its first element
                    must equal str(state.tick). Zero or many rows = FAIL.

Checks (fail-closed): every self_drive numeric/window field, the tick row,
ceo_face three lines non-empty, do/depts/outs/results containers non-empty,
export_ts ISO8601-parseable, and this source file pure ASCII.

Reads only; writes only the evidence log given via --out.
Exit 0 = all fields PASS. Exit 2 = any drift or missing field.
Pure stdlib, zero network, zero new external API surface.
"""

import argparse
import datetime as _dt
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_PROPOSALS = os.path.join(ROOT, "docs", "proposals.md")
P_QUEUES = {
    "queue_main_open": os.path.join(ROOT, "state", "queue", "main.md"),
    "queue_tech_open": os.path.join(ROOT, "state", "queue", "tech.md"),
    "queue_explore_open": os.path.join(ROOT, "state", "queue", "explore.md"),
}
P_PATTERNS = os.path.join(ROOT, "src", "os", "export_consistency_patterns.json")
P_SELF = os.path.abspath(__file__)

RE_DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})")
RE_ROUND_MAIN = re.compile(r"^\d{4}-\d{2}-\d{2} R\d+ ")
RE_PROPOSAL_HEADER = re.compile(r"^### BD-PROP-")
RE_QUEUE_OPEN = re.compile(r"^- \[ \]")

MARKER_IDLE = "idle-fast"
MARKER_NOP = "no-pullable"
TOKENS_LINE = " tokens: "


def _read_text(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    return raw.decode("utf-8-sig")


def _load_patterns():
    pat = json.loads(_read_text(P_PATTERNS))
    for key in ("tick_row_label", "proposal_open_marker", "declaration_close_marker"):
        if key not in pat or not isinstance(pat[key], str) or not pat[key]:
            raise KeyError("patterns file missing key: %s" % key)
    return pat


def recompute():
    """Return (derived dict, state dict, export dict, info list). Canonical caliber."""
    pat = _load_patterns()
    state = json.loads(_read_text(P_STATE))
    export = json.loads(_read_text(P_EXPORT))
    log = state.get("log", [])
    if not isinstance(log, list) or not log:
        raise ValueError("state.json log missing/empty")

    dates = []
    for ln in log:
        m = RE_DATE_PREFIX.match(ln)
        if m:
            dates.append(_dt.date.fromisoformat(m.group(1)))
    if not dates:
        raise ValueError("no date prefixes found in state log")
    d_max = max(dates)
    d_min = d_max - _dt.timedelta(days=6)

    win_lines = []
    for ln in log:
        m = RE_DATE_PREFIX.match(ln)
        if m and d_min <= _dt.date.fromisoformat(m.group(1)) <= d_max:
            win_lines.append(ln)

    idle = sum(1 for ln in win_lines if MARKER_IDLE in ln)
    nop = sum(1 for ln in win_lines if MARKER_NOP in ln)
    decl = pat["declaration_close_marker"]
    sub = 0
    for ln in win_lines:
        if not RE_ROUND_MAIN.match(ln):
            continue
        if TOKENS_LINE in ln:
            continue
        if MARKER_NOP in ln or decl in ln:
            continue
        sub += 1

    prop_lines = [ln for ln in _read_text(P_PROPOSALS).splitlines()
                  if RE_PROPOSAL_HEADER.match(ln)]
    proposals_total = len(prop_lines)
    proposals_open = sum(1 for ln in prop_lines if pat["proposal_open_marker"] in ln)

    queues = {}
    for key, path in P_QUEUES.items():
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8-sig")
        queues[key] = sum(1 for ln in text.splitlines() if RE_QUEUE_OPEN.match(ln))

    derived = {
        "window": "%s..%s" % (d_min.isoformat(), d_max.isoformat()),
        "window_days": (d_max - d_min).days + 1,
        "log_lines_in_window": len(win_lines),
        "idle_fast_mention_lines": idle,
        "no_pullable_mention_lines": nop,
        "substantive_non_idle_mention_lines": sub,
        "proposals_total": proposals_total,
        "proposals_open": proposals_open,
    }
    derived.update(queues)
    return derived, state, export, pat


def check():
    """Return (report lines, n_pass, n_fail). Exit-code semantics per AC-EC3."""
    out = []
    n_pass = 0
    n_fail = 0

    def emit(field, ok, stored, recomputed):
        nonlocal n_pass, n_fail
        if ok:
            n_pass += 1
            out.append("PASS %s stored=%r" % (field, stored))
        else:
            n_fail += 1
            out.append("FAIL %s stored=%r recomputed=%r" % (field, stored, recomputed))

    derived, state, export, pat = recompute()
    sd = export.get("self_drive")
    if not isinstance(sd, dict):
        out.append("FAIL self_drive missing (not an object)")
        return out, n_pass, 1

    for key, want in sorted(derived.items()):
        got = sd.get(key, "<missing>")
        emit("self_drive.%s" % key, got == want, got, want)

    tick = state.get("tick")
    results = export.get("results")
    label = pat["tick_row_label"]
    if not isinstance(results, list) or not results:
        out.append("FAIL results container missing/empty")
        n_fail += 1
    else:
        rows = [r for r in results if isinstance(r, list) and len(r) >= 2 and r[1] == label]
        if len(rows) != 1:
            out.append("FAIL results.tick_row expected exactly 1 row with label %r, found %d"
                       % (label, len(rows)))
            n_fail += 1
        else:
            emit("results.tick_row", str(tick) == str(rows[0][0]), rows[0][0], tick)

    ceo = export.get("ceo_face")
    if not isinstance(ceo, dict):
        out.append("FAIL ceo_face missing (not an object)")
        n_fail += 1
    else:
        for key in ("current", "latest_artifact", "next_milestone"):
            val = ceo.get(key)
            ok = isinstance(val, str) and bool(val.strip())
            emit("ceo_face.%s non-empty" % key, ok, ("<empty>" if not ok else "present"), None)

    for key in ("do", "depts", "outs", "results"):
        val = export.get(key)
        ok = (isinstance(val, str) and bool(val.strip())) or (isinstance(val, list) and val)
        emit("container %s non-empty" % key, ok, ("<empty>" if not ok else "present"), None)

    ts = export.get("export_ts")
    try:
        _dt.datetime.fromisoformat(ts)
        age_h = None
        m = RE_DATE_PREFIX.match(ts or "")
        if m:
            age_h = (_dt.datetime.now(_dt.timezone.utc)
                     - _dt.datetime.fromisoformat(ts)).total_seconds() / 3600.0
        out.append("INFO export_ts parseable %r (age %.1fh)" % (ts, age_h if age_h is not None else -1))
        n_pass += 1
    except (TypeError, ValueError):
        out.append("FAIL export_ts not ISO8601-parseable: %r" % (ts,))
        n_fail += 1

    with open(P_SELF, "rb") as fh:
        src = fh.read()
    bad = [b for b in src if b >= 128]
    emit("checker source pure ASCII", not bad, ("%d non-ascii bytes" % len(bad)) if bad else "0", 0)

    out.append("SUMMARY pass=%d fail=%d state_tick=%s window=%s W=%d idle=%d nop=%d sub=%d "
               "proposals=%d/%d queues=%d/%d/%d"
               % (n_pass, n_fail, tick, derived["window"], derived["log_lines_in_window"],
                  derived["idle_fast_mention_lines"], derived["no_pullable_mention_lines"],
                  derived["substantive_non_idle_mention_lines"], derived["proposals_total"],
                  derived["proposals_open"], derived["queue_main_open"],
                  derived["queue_tech_open"], derived["queue_explore_open"]))
    return out, n_pass, n_fail


def main():
    ap = argparse.ArgumentParser(description="status-export derived-face consistency checker")
    ap.add_argument("--out", default=None, help="write report to this file instead of stdout")
    args = ap.parse_args()
    try:
        lines, n_pass, n_fail = check()
    except Exception as exc:  # fail-closed on any unreadable/malformed input
        lines = ["FATAL %s: %s" % (type(exc).__name__, exc)]
        n_fail = 1
        n_pass = 0
    lines.append("VERDICT " + ("PASS" if n_fail == 0 else "FAIL exit 2"))
    report = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(report)
    else:
        sys.stdout.write(report)
    return 0 if n_fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
