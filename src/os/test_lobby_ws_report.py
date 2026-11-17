"""lobby WebSocket report face suite (R2876; criteria AC-LWR1..AC-LWR7 were
pinned before the code: AC-LWR1..AC-LWR6 in state/queue/tech.md as the R2840
seed row, AC-LWR7 in src/os/backlog.md as the R2879 pin).

What this proves: tools/lobby_ws_report.py prints eight readings and, until
R2876, nothing re-derived them, so a wrong face read exactly like a right one.
This suite re-derives the rendered face from the evidence the tool itself
carries, drives the shipped --check gate through its own fail-closed branches,
EXECUTES the shipped socket walk once under the guard so the eight readings are
measured on the wire rather than only recomputed, and leaves the tracked
preview pair byte- and mtime-identical (the tool re-publishes a tracked pair,
which is the production consumer tree_snapshot was shipped for in R2875).

Stdlib plus the tool's own `websockets` dependency, ASCII source, loopback
only. Exit 0 = all green.
"""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import time

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
TOOL = os.path.join(REPO, "tools", "lobby_ws_report.py")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-lobby-ws-report-face"
EXPECTED_CRITERIA = 7

sys.path.insert(0, BASE)
import tree_snapshot as TS  # noqa: E402

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def sig(path):
    """Bytes plus mtime as the guard would record them."""
    if not os.path.exists(path):
        return ("absent", 0)
    with open(path, "rb") as handle:
        value = hashlib.sha256(handle.read()).hexdigest()
    return (value, os.stat(path).st_mtime_ns)


def load_tool():
    spec = importlib.util.spec_from_file_location("lobby_ws_report_probe", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evidence_for(lob, flags):
    """Build the evidence dict FROM the tool own CRITERIA, not a copy."""
    return {cid: {"pass": flag, "measured": "synthetic row for %s" % cid}
            for (cid, _intent), flag in zip(lob.CRITERIA, flags)}


def facts_for(lob):
    return {
        "uri": "ws://127.0.0.1:0/ws",
        "risk_text": "stand-in risk text",
        "hello": {"payload": {"v": 1, "rooms": ["lobby"]}},
        "risk": {"payload": {"text": "stand-in risk text"}},
        "broadcast": {"type": "chat.broadcast"},
        "census": {"id": "c1", "served": ["name"], "whitelist": ["name", "tier"]},
        "shipped_sha": {},
    }


def run_main(lob, argv):
    """Call the shipped main with stdout captured, returning (code, text)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = lob.main(argv)
    return code, buf.getvalue()


def main():
    tracked = [lob_path for lob_path in (
        os.path.join(REPO, "preview", "lobby-ws-report.html"),
        os.path.join(REPO, "preview", "lobby-ws-report.json"),
    )]
    before = {path: sig(path) for path in tracked}

    lob = load_tool()
    n = len(lob.CRITERIA)

    # AC-LWR1 contract: one list, eight pinned ids, and the rendered face is
    # DERIVED from that list rather than carrying a second copy.
    ids = [cid for cid, _intent in lob.CRITERIA]
    intents_ok = all(isinstance(text, str) and text.strip() for _c, text in lob.CRITERIA)
    expected = ["AC-LWS%d" % index for index in range(1, 9)]
    ev_all = evidence_for(lob, [True] * n)
    _doc, data = lob.render(ev_all, facts_for(lob))
    derived_ids = [row["id"] for row in data["criteria"]]
    # the derivation is proved by shrinking the one list and re-rendering
    original = lob.CRITERIA
    try:
        lob.CRITERIA = original[:2]
        _doc2, data2 = lob.render(evidence_for(lob, [True, True]), facts_for(lob))
        shrunk = len(data2["criteria"])
    finally:
        lob.CRITERIA = original
    check(
        ids == expected and intents_ok and derived_ids == ids and shrunk == 2
        and data["artifact"] == "lobby-ws-report"
        and n == 8,
        "AC-LWR1 contract: %d ids %s, intents non-empty, rendered ids derived from the one list "
        "(shrink->%d), artifact name pinned" % (n, ids == expected, shrunk),
    )

    # AC-LWR2 independent recount: the verdict is a FUNCTION of the evidence
    # flags, recomputed here, so a wrong face cannot read like a right one.
    passed_all = sum(1 for row in ev_all.values() if row["pass"])
    flipped = evidence_for(lob, [True] * (n - 1) + [False])
    passed_flip = sum(1 for row in flipped.values() if row["pass"])
    _d1, all_data = lob.render(ev_all, facts_for(lob))
    _d2, flip_data = lob.render(flipped, facts_for(lob))
    check(
        all_data["passed"] == passed_all == n
        and all_data["verdict"] == "PASS"
        and all_data["total"] == n
        and flip_data["passed"] == passed_flip == n - 1
        and flip_data["verdict"] == "FAIL"
        and [row["pass"] for row in flip_data["criteria"]] == [True] * (n - 1) + [False],
        "AC-LWR2 recount: recomputed %d==%d PASS and one flipped flag reads %d/%d FAIL "
        "(verdict is a function of evidence)" % (passed_all, all_data["passed"],
                                                 passed_flip, flip_data["total"]),
    )

    # AC-LWR3 honest zero: an all-red face renders 0/8 FAIL and stays readable;
    # a face with NO evidence at all is refused rather than rendered green 0/0.
    _doc3, zero_data = lob.render(evidence_for(lob, [False] * n), facts_for(lob))
    empty_refused = False
    try:
        lob.render({}, facts_for(lob))
    except KeyError:
        empty_refused = True
    check(
        zero_data["passed"] == 0 and zero_data["verdict"] == "FAIL"
        and len(zero_data["criteria"]) == n and empty_refused,
        "AC-LWR3 honest zero: all-red reads 0/%d FAIL with %d rows, absent evidence refused "
        "(KeyError) rather than 0/0 PASS" % (n, len(zero_data["criteria"])),
    )

    # AC-LWR4 bad-input fail-closed: the shipped --check gate refuses a missing
    # pair and a tampered fingerprint, and only passes a pair it just published.
    world = tempfile.mkdtemp(prefix="bigdomain-lwr-")
    html_path = os.path.join(world, "face.html")
    json_path = os.path.join(world, "face.json")
    saved = (lob.HTML_PATH, lob.JSON_PATH, lob.PREVIEW, lob.build_evidence)
    try:
        lob.HTML_PATH = html_path
        lob.JSON_PATH = json_path
        lob.PREVIEW = world
        lob.build_evidence = lambda: (ev_all, facts_for(lob))
        missing_code, missing_text = run_main(lob, ["--check"])
        published_code, published_text = run_main(lob, [])
        live_code, live_text = run_main(lob, ["--check"])
        with open(json_path, encoding="utf-8") as handle:
            landed = json.load(handle)
        landed["fingerprint"] = "0000000000000000"
        with open(json_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(landed, ensure_ascii=False, indent=1) + "\n")
        tampered_code, tampered_text = run_main(lob, ["--check"])
    finally:
        lob.HTML_PATH, lob.JSON_PATH, lob.PREVIEW, lob.build_evidence = saved
    check(
        missing_code == 2 and "VERDICT FAIL" in missing_text
        and published_code == 0 and "VERDICT PASS" in published_text
        and live_code == 0 and "VERDICT PASS" in live_text
        and tampered_code == 2 and "VERDICT FAIL" in tampered_text,
        "AC-LWR4 fail-closed: absent pair rc=%d FAIL, fresh publish rc=%d PASS, "
        "re-check rc=%d PASS, tampered fingerprint rc=%d FAIL"
        % (missing_code, published_code, live_code, tampered_code),
    )

    # AC-LWR5 purity at the real pair: the tool re-publishes a TRACKED pair, so
    # the suite must leave it byte- and mtime-identical, and the re-rendering
    # body is exercised under the shipped guard (tree_snapshot first consumer
    # outside its own test).
    guarded_html = os.path.join(world, "tracked.html")
    guarded_json = os.path.join(world, "tracked.json")
    for path in (guarded_html, guarded_json):
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("original body\n")
    guarded_before = {path: sig(path) for path in (guarded_html, guarded_json)}
    with TS.Snapshot([guarded_html, guarded_json]):
        for path in (guarded_html, guarded_json):
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write("re-rendered body\n")
            os.utime(path, (1234567890, 1234567890))
    guarded_after = {path: sig(path) for path in (guarded_html, guarded_json)}
    after = {path: sig(path) for path in tracked}
    check(
        after == before and guarded_after == guarded_before,
        "AC-LWR5 purity: tracked pair unchanged (2 files, bytes+mtime), guarded re-render "
        "restores the tmp pair it rewrote" % (),
    )

    # AC-LWR7 the live walk, measured ON THE WIRE instead of re-derived: the
    # R2876 suite proved the verdict is a function of the evidence but never
    # executed the walk, so the eight readings stayed unmeasured for three
    # windows. Here the shipped build_evidence() runs exactly once under the
    # guard, and the criterion demands all eight flags true, the rendered
    # fingerprint equal to the LANDED one, and the tracked pair untouched.
    # A walk that raises (including a missing `websockets`) is a named red.
    live_error = ""
    live_flags = []
    live_data = {}
    walk_before = {path: sig(path) for path in tracked}
    started = time.time()
    try:
        with TS.Snapshot(tracked):
            live_ev, live_facts = lob.build_evidence()
            _live_doc, live_data = lob.render(live_ev, live_facts)
        live_flags = [live_ev[cid]["pass"] for cid, _intent in lob.CRITERIA]
    except Exception as exc:  # a refused walk is a named red, not a skip
        live_error = "%s: %s" % (type(exc).__name__, exc)
    elapsed = time.time() - started
    walk_after = {path: sig(path) for path in tracked}
    landed_pair = {}
    landed_json = os.path.join(REPO, "preview", "lobby-ws-report.json")
    if os.path.exists(landed_json):
        with open(landed_json, encoding="utf-8") as handle:
            landed_pair = json.load(handle)
    live_green = sum(1 for flag in live_flags if flag)
    check(
        not live_error
        and len(live_flags) == n
        and live_green == n
        and live_data.get("passed") == n
        and live_data.get("fingerprint") == landed_pair.get("fingerprint")
        and landed_pair.get("verdict") == "PASS"
        and walk_after == walk_before,
        "AC-LWR7 live walk: %d/%d flags on the wire, fingerprint %s vs landed %s, "
        "tracked pair unchanged=%s, %.1fs%s"
        % (live_green, n, live_data.get("fingerprint"), landed_pair.get("fingerprint"),
           walk_after == walk_before, elapsed,
           (" error=" + live_error) if live_error else ""),
    )

    # AC-LWR6 wiring: the suite is registered in the battery and the matrix
    # names it, so this face cannot lose its guard without a red leg.
    wired = False
    with open(RUNNER, encoding="utf-8", errors="replace") as handle:
        wired = ('"test_lobby_ws_report.py"), %d),' % EXPECTED_CRITERIA) in handle.read()
    in_matrix = False
    if os.path.exists(MATRIX):
        with open(MATRIX, encoding="utf-8", errors="replace") as handle:
            in_matrix = LABEL in handle.read()
    check(wired and in_matrix,
          "AC-LWR6 wiring: %s registered with %d criteria in the battery and named in the matrix"
          % (LABEL, EXPECTED_CRITERIA))

    print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL", PASSES, PASSES + FAILS),
          flush=True)
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
