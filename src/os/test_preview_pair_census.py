"""Battery suite for the preview page-pair census - AC-PPC1..AC-PPC9 (R3499, R3508, R3511)
and AC-PPA1..AC-PPA5 (R3522, the replay-receipt admissibility face).

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

import glob
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
RECEIPT = os.path.join(PREVIEW, "face-pair-receipt.json")
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
    sig_admit_json = sig(PPC.ADMIT_OUT)
    sig_admit_html = sig(PPC.ADMIT_HTML)
    sig_receipt = sig(RECEIPT)

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
    # R3508 repair, recorded rather than folded in silently: R3500 added the
    # channel-receipt class to the census but this closure arm kept the R3499
    # tuple, so it counted 103 of 106 rows and the arm had been red since that
    # round without anyone re-running this suite. The invariant is unchanged -
    # every row carries exactly one class and the classes cover the tree.
    classes = ("same-run", "same-commit", "history-split", "channel-receipt",
               "frozen-excused", "untracked", "no-json")
    classified = sum(totals[k] for k in classes)
    ok("AC-PPC1", all(arms) and classified == totals["html"] == len(named)
       and len(set(named)) <= len(classes), "arms=%s html=%d classified=%d" % (arms, totals["html"], classified))

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
    # R3508: the html half prints its own round label, so it went red the moment
    # the tick moved past its derivation. The label is excluded and the
    # exclusion is proved narrow - one changed count still reads drift.
    fresh_html_text = PPC.html_of(payload)
    html_stamp_only = fresh_html_text.replace("Tick %d" % payload["round"], "Tick 1")
    marked = ">%d html<" % totals["html"]
    html_tampered = fresh_html_text.replace(marked, ">%d html<" % (totals["html"] + 1), 1)
    html_label_ignored = (html_stamp_only != fresh_html_text
                          and PPC.normalized(html_stamp_only) == PPC.normalized(fresh_html_text))
    html_digit_caught = (html_tampered != fresh_html_text
                         and PPC.normalized(html_tampered) != PPC.normalized(fresh_html_text))
    ok("AC-PPC4", landed_ok and caught and volatile_ignored
       and html_label_ignored and html_digit_caught,
       "landed_pair=%s tamper_caught=%s label_and_stamp_ignored=%s html_label=%s html_digit=%s"
       % (landed_ok, caught, volatile_ignored, html_label_ignored, html_digit_caught))

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

    # AC-PPC8: a landed face that prints this page's own byte count is a READING,
    # not a measurement - its clocks, digests and last-commit labels are dropped
    # so the census and the entry index can no longer redden each other, while
    # its class stays compared (negative controls on detection and on the reading).
    mirrors = [r for r in rows if r.get("mirror")]
    mirror_names = sorted(r["name"] for r in mirrors)
    names_page = []
    for path in sorted(glob.glob(os.path.join(PREVIEW, "*.html"))):
        stem = os.path.basename(path)[:-5]
        if stem == PPC.LABEL:
            continue
        try:
            text = read_bytes(path).decode("utf-8", "replace")
        except OSError:
            continue
        if PPC.LABEL in text:
            names_page.append(stem)
    names_page.sort()
    measured_keys = ("bytes", "sha", "mtime", "mtime_epoch")
    mirror_drops_measurement = all(
        not any(k in (r.get("html") or {}) for k in measured_keys)
        and not any(k in (r.get("json") or {}) for k in measured_keys)
        and "delta_seconds" not in r
        for r in mirrors)
    narrow = all("bytes" in r["html"] for r in rows if not r.get("mirror"))
    work2 = tempfile.mkdtemp(prefix="ppc3508-")
    try:
        quiet = os.path.join(work2, "quiet.html")
        loud = os.path.join(work2, "loud.html")
        with io.open(quiet, "wb") as f:
            f.write(b"<html><body>no sizes here</body></html>")
        with io.open(loud, "wb") as f:
            f.write(("<html><body>%s.json &middot; 52722B</body></html>" % PPC.LABEL).encode("utf-8"))
        detect = (not PPC.prints_this_page(quiet)) and PPC.prints_this_page(loud)
    finally:
        shutil.rmtree(work2, ignore_errors=True)
    reading_compared = True
    if mirrors:
        moved = json.loads(PPC.dumps(payload))
        for row in moved["pairs"]:
            if row.get("mirror"):
                row["verdict"] = "history-split"
                break
        reading_compared = (PPC.normalized(json.dumps(moved, indent=2, sort_keys=True,
                                                      ensure_ascii=False))
                            != PPC.normalized(read_bytes(JSON_HALF)))
    ok("AC-PPC8", mirror_names == names_page and bool(names_page)
       and mirror_drops_measurement and narrow and detect and reading_compared,
       "mirrors=%s named_in_html=%s no_measurement=%s narrow=%s detect=%s reading_compared=%s"
       % (mirror_names, names_page, mirror_drops_measurement, narrow, detect, reading_compared))

    # AC-PPC9: a mirror row carries no clock at all, so a page that embeds this
    # page's own size can no longer redden the pair by being re-derived - while
    # the exclusion stays narrow: a normal pair's commits are still compared and
    # one changed commit still reads drift.
    mirror_rows_have_no_clock = all(
        "commit" not in (r.get("html") or {}) and "commit" not in (r.get("json") or {})
        for r in mirrors)
    paired = [r for r in rows if not r.get("mirror")
              and isinstance(r.get("html"), dict) and isinstance(r.get("json"), dict)
              and "commit" in r["html"] and "commit" in r["json"]]
    if paired:
        shifted = json.loads(PPC.dumps(payload))
        for row in shifted["pairs"]:
            if row["name"] == paired[0]["name"]:
                row["html"]["commit"] = "deadbee"
                break
        commit_still_compared = (PPC.normalized(json.dumps(shifted, indent=2, sort_keys=True,
                                                           ensure_ascii=False))
                                 != PPC.normalized(fresh_json))
    else:
        commit_still_compared = False
    ok("AC-PPC9", bool(mirrors) and mirror_rows_have_no_clock and commit_still_compared,
       "mirror_without_clock=%s paired_rows=%d commit_still_compared=%s"
       % (mirror_rows_have_no_clock, len(paired), commit_still_compared))

    # AC-PPA1: the admissibility face covers exactly the splits the law counts
    # and its arithmetic is its own - admitted plus blocked is the whole face,
    # and the shipped totals are declared untouched rather than quietly moved.
    face = PPC.admissibility(payload)
    f_rows = face["rows"]
    admitted_rows = [r for r in f_rows if r["would_be_admitted"]]
    ok("AC-PPA1", face["splits"] == totals["history-split"] == len(f_rows)
       and face["admitted"] == len(admitted_rows)
       and face["if_admitted"]["history_split_before"] == face["splits"]
       and face["if_admitted"]["history_split_after"] == face["splits"] - face["admitted"]
       and face["if_admitted"]["shipped_totals_unchanged"] is True
       and face["checks"] == 5 and "never excuses" in face["law_now"],
       "splits=%d admitted=%d after=%d"
       % (face["splits"], face["admitted"], face["if_admitted"]["history_split_after"]))

    # AC-PPA2: every admitted row is re-derived here, from its own bytes read by
    # this suite, not from the face's own digest - and a row the face refuses
    # must name why, so a refusal is never a silent zero.
    def live12(name):
        try:
            return hashlib.sha256(read_bytes(os.path.join(PREVIEW, name + ".html"))).hexdigest()[:12]
        except OSError:
            return ""

    recount = all(live12(r["name"]) == r["live_sha256_12"] for r in admitted_rows)
    bound = all(r["receipt_verdict"] == "version-drift" and r["historical_commit"]
                and r["recorded_sha256_12"] == r["live_sha256_12"]
                and not r["blocked_by"] for r in admitted_rows)
    named = all(r["blocked_by"] for r in f_rows if not r["would_be_admitted"])
    ok("AC-PPA2", bool(admitted_rows) and recount and bound and named,
       "admitted=%d recount=%s bound=%s blocked_rows_named=%s"
       % (len(admitted_rows), recount, bound, named))

    # AC-PPA3: the three controls sit on the real records and each moved field
    # has to be load-bearing - the exact single reason is pinned, so a control
    # that answered False for the wrong reason cannot pass.
    cons = dict((c["control"], c) for c in face["negative_controls"])
    expect = {"binding-digest-moved-one-hex": "receipt-not-bound-to-landed-bytes",
              "json-claim-dropped": "json-not-byte-identical",
              "no-receipt-at-all": "no-receipt"}
    controls_ok = (set(cons) == set(expect)
                   and all(cons[k]["ok"] is True and cons[k]["answer"] == [v]
                           for k, v in expect.items()))
    ok("AC-PPA3", controls_ok, "controls=%s" % sorted(cons))

    # AC-PPA4: the page is one derivation with two halves; a changed measurement
    # reddens it while the clock and the window label do not, which is what lets
    # a decision read it whole after the tick has moved on.
    fresh_adj_json = PPC.admit_dumps(face).encode("utf-8")
    fresh_adj_html = PPC.admit_html_of(face).encode("utf-8")
    adj_landed = (os.path.exists(PPC.ADMIT_OUT) and os.path.exists(PPC.ADMIT_HTML)
                  and PPC.admit_normalized(read_bytes(PPC.ADMIT_OUT))
                  == PPC.admit_normalized(fresh_adj_json)
                  and PPC.admit_normalized(read_bytes(PPC.ADMIT_HTML))
                  == PPC.admit_normalized(fresh_adj_html))
    tampered_adj = json.loads(PPC.admit_dumps(face))
    tampered_adj["rows"][0]["would_be_admitted"] = not tampered_adj["rows"][0]["would_be_admitted"]
    adj_caught = (PPC.admit_normalized(json.dumps(tampered_adj, indent=2, sort_keys=True,
                                                  ensure_ascii=False))
                  != PPC.admit_normalized(fresh_adj_json))
    stamp_adj = json.loads(PPC.admit_dumps(face))
    stamp_adj["generated_at"] = "1999-01-01T00:00:00+08:00"
    stamp_adj["round"] = 1
    adj_stamp_ignored = (PPC.admit_normalized(json.dumps(stamp_adj, indent=2, sort_keys=True,
                                                         ensure_ascii=False))
                         == PPC.admit_normalized(fresh_adj_json))
    ok("AC-PPA4", adj_landed and adj_caught and adj_stamp_ignored,
       "landed_pair=%s tamper_caught=%s label_ignored=%s"
       % (adj_landed, adj_caught, adj_stamp_ignored))

    # AC-PPA5: the staleness gate is the point of the page - a landed row whose
    # live bytes moved must be named, a clean pair must read clean, and a
    # missing half must be named rather than skipped.
    work3 = tempfile.mkdtemp(prefix="ppa3522-")
    try:
        good_json = os.path.join(work3, "good.json")
        good_html = os.path.join(work3, "good.html")
        bad_json = os.path.join(work3, "bad.json")
        with io.open(good_json, "wb") as f:
            f.write(PPC.admit_dumps(face).encode("utf-8"))
        with io.open(good_html, "wb") as f:
            f.write(PPC.admit_html_of(face).encode("utf-8"))
        clean = PPC.admit_check(payload, face, good_json, good_html)
        stale_doc = json.loads(PPC.admit_dumps(face))
        moved_name = ""
        for row in stale_doc["rows"]:
            if row["would_be_admitted"]:
                row["live_sha256_12"] = "0" * 12
                moved_name = row["name"]
                break
        with io.open(bad_json, "wb") as f:
            f.write((json.dumps(stale_doc, indent=2, sort_keys=True,
                                ensure_ascii=False) + "\n").encode("utf-8"))
        stale = PPC.admit_check(payload, face, bad_json, good_html)
        missing = PPC.admit_check(payload, face, os.path.join(work3, "absent.json"), good_html)
    finally:
        shutil.rmtree(work3, ignore_errors=True)
    ok("AC-PPA5", clean == [] and any("live bytes moved" in p and moved_name in p for p in stale)
       and any("missing half" in p for p in missing),
       "clean=%d stale_named=%s missing_named=%s"
       % (len(clean), any("live bytes moved" in p for p in stale),
          any("missing half" in p for p in missing)))

    # AC-PPC7: the suite proved things without changing anything on disk.
    same = (sig(TOOL) == sig_tool and sig(JSON_HALF) == sig_json
            and sig(HTML_HALF) == sig_html and sig(REGISTER) == sig_reg
            and sig(STATE) == sig_state
            and sig(PPC.ADMIT_OUT) == sig_admit_json
            and sig(PPC.ADMIT_HTML) == sig_admit_html
            and sig(RECEIPT) == sig_receipt)
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
