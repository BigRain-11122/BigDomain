"""Battery suite for the preview page-pair census - AC-PPC1..AC-PPC7 (R3499).

Seven arms were pinned in src/os/backlog.md at R3499 (PIN then PIN+1 for the
freeze face) BEFORE tools/preview_pair_census.py existed. The point of the
suite is the distinction that made this round necessary: an mtime gap proves
two halves were written at different moments, while only committed history can
say the pair never left in one commit - and even that is excused when a freeze
register proves both halves byte for byte.

Nothing here changes a law or rewrites a page: the tool, both landed halves,
the freeze register and state.json are stat-signed before and after the run.
Synthetic worlds live under the system temp directory and are removed.

Source discipline: pure ASCII, stdlib only, no clock read of its own, no
network, no shell. The tool's own git lookups are read-only.
"""

import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
TOOL = os.path.join(TOOLS, "preview_pair_census.py")
PREVIEW = os.path.join(ROOT, "preview")
JSON_HALF = os.path.join(PREVIEW, "preview-pair-census.json")
HTML_HALF = os.path.join(PREVIEW, "preview-pair-census.html")
REGISTER = os.path.join(ROOT, "state", "apimarket-face-freeze.json")
STATE = os.path.join(ROOT, "src", "os", "state.json")
sys.path.insert(0, TOOLS)

import preview_pair_census as PPC  # noqa: E402

FAILS = []
CHECKS = []


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
        print("FAIL %s %s" % (name, detail))
    else:
        print("PASS %s %s" % (name, detail))


def read_bytes(path):
    with io.open(path, "rb") as f:
        return f.read()


def sig(path):
    try:
        data = read_bytes(path)
    except OSError:
        return None
    return (len(data), hashlib.sha256(data).hexdigest()[:16])


def main():
    sig_tool = sig(TOOL)
    sig_json = sig(JSON_HALF)
    sig_html = sig(HTML_HALF)
    sig_reg = sig(REGISTER)
    sig_state = sig(STATE)

    payload = PPC.census()
    rows = payload["pairs"]
    totals = payload["totals"]

    # AC-PPC1: one class per pair, and the classes cover the tree without gaps.
    arms = [
        PPC.classify(60, "aaa", "bbb") == "same-run",
        PPC.classify(PPC.SAME_RUN_SECONDS + 1, "aaa", "aaa") == "same-commit",
        PPC.classify(PPC.SAME_RUN_SECONDS + 1, "aaa", "bbb") == "history-split",
        PPC.classify(PPC.SAME_RUN_SECONDS + 1, "", "bbb") == "untracked",
    ]
    named = [r["verdict"] for r in rows]
    classified = sum(totals[k] for k in ("same-run", "same-commit", "history-split",
                                        "frozen-excused", "untracked", "no-json"))
    ok("AC-PPC1", all(arms) and classified == totals["html"] == len(named)
       and len(set(named)) <= 6, "arms=%s html=%d classified=%d" % (arms, totals["html"], classified))

    # AC-PPC2: the negative control the whole page rests on - the SAME mtime gap
    # answers two different verdicts depending on committed history alone.
    gap = 4 * 3600
    same_batch = PPC.classify(gap, "c0ffee", "c0ffee")
    split_batch = PPC.classify(gap, "c0ffee", "beef01")
    ok("AC-PPC2", same_batch == "same-commit" and split_batch == "history-split",
       "same_gap_4h -> %s vs %s" % (same_batch, split_batch))

    # AC-PPC3: the oldest survivor is named, and it really is the largest gap
    # among history splits (not among all pairs).
    splits = [r for r in rows if r["verdict"] == "history-split"]
    oldest = payload["oldest_split"]
    worst = max(splits, key=lambda r: r["delta_seconds"]) if splits else None
    ok("AC-PPC3", (oldest is None and worst is None)
       or (oldest["name"] == worst["name"]
           and abs(oldest["delta_hours"] - worst["delta_seconds"] / 3600.0) < 0.06),
       "oldest=%s splits=%d" % (oldest and oldest["name"], len(splits)))

    # AC-PPC4: both landed halves are this derivation, and a single changed field
    # is caught - the gate is not a rubber stamp (negative control).
    fresh_json = PPC.dumps(payload).encode("utf-8")
    fresh_html = PPC.html_of(payload).encode("utf-8")
    landed_ok = (PPC.normalized(read_bytes(JSON_HALF)) == PPC.normalized(fresh_json)
                 and PPC.normalized(read_bytes(HTML_HALF)) == PPC.normalized(fresh_html))
    tampered = json.loads(PPC.dumps(payload))
    tampered["totals"]["same-run"] += 1
    caught = PPC.normalized(json.dumps(tampered, indent=2, sort_keys=True,
                                       ensure_ascii=False)) != PPC.normalized(fresh_json)
    stamp_only = json.loads(PPC.dumps(payload))
    stamp_only["generated_at"] = "1999-01-01T00:00:00+08:00"
    stamp_only["round"] = 1
    volatile_ignored = PPC.normalized(json.dumps(stamp_only, indent=2, sort_keys=True,
                                                 ensure_ascii=False)) == PPC.normalized(fresh_json)
    ok("AC-PPC4", landed_ok and caught and volatile_ignored,
       "landed_pair=%s tamper_caught=%s label_and_stamp_ignored=%s"
       % (landed_ok, caught, volatile_ignored))

    # AC-PPC5: the page does not describe itself, so committing it cannot flip
    # its own class and redden --check for a reason that is not a defect.
    ok("AC-PPC5", PPC.LABEL not in [r["name"] for r in rows]
       and payload["self_excluded"] == PPC.LABEL,
       "self_absent=%s" % (PPC.LABEL not in [r["name"] for r in rows]))

    # AC-PPC6: a freeze receipt excuses a split only when BOTH halves still match
    # their registered digest; a half that moved keeps the split and says which.
    work = tempfile.mkdtemp(prefix="ppc3499-")
    try:
        html_path = os.path.join(work, "frozen-face.html")
        json_path = os.path.join(work, "frozen-face.json")
        with io.open(html_path, "wb") as f:
            f.write(b"<html>frozen</html>")
        with io.open(json_path, "wb") as f:
            f.write(b'{"n": 1}')

        both = {"frozen-face.html": {"html": PPC.sha256_hex(html_path),
                                     "json": PPC.sha256_hex(json_path)}}
        row = {"verdict": "history-split", "delta_seconds": 7200}
        PPC.apply_freeze(row, html_path, json_path, both)

        half = {"frozen-face.html": {"html": PPC.sha256_hex(html_path),
                                     "json": "0" * 64}}
        row2 = {"verdict": "history-split", "delta_seconds": 7200}
        PPC.apply_freeze(row2, html_path, json_path, half)

        with io.open(html_path, "ab") as f:
            f.write(b"<!-- moved -->")
        row3 = {"verdict": "history-split", "delta_seconds": 7200}
        PPC.apply_freeze(row3, html_path, json_path, both)

        row4 = {"verdict": "same-run", "delta_seconds": 5}
        PPC.apply_freeze(row4, html_path, json_path, both)

        ok("AC-PPC6", row["verdict"] == "frozen-excused" and row.get("receipt") == "sha256-both"
           and row2["verdict"] == "history-split"
           and row2.get("freeze_bytes_match") == "html-only"
           and row3["verdict"] == "history-split"
           and row3.get("freeze_bytes_match") == "json-only"
           and row4["verdict"] == "same-run",
           "both=%s half=%s moved=%s same_run=%s"
           % (row["verdict"], row2.get("freeze_bytes_match"),
              row3.get("freeze_bytes_match"), row4["verdict"]))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    # AC-PPC7: the suite proved things without changing anything on disk.
    same = (sig(TOOL) == sig_tool and sig(JSON_HALF) == sig_json
            and sig(HTML_HALF) == sig_html and sig(REGISTER) == sig_reg
            and sig(STATE) == sig_state)
    ok("AC-PPC7", same, "repo_untouched=%s" % same)

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
