# -*- coding: utf-8 -*-
"""R1868 closeout driver (continuation of the interrupted 17:1x window).
Adopts the dead window's verified artifacts (claim note 17:17, suite
file + apidev.py window surgery + sibling signature syncs +
reconcile_all registration, kvw1/kvw2 double-run captures 17:19) with
zero code change; the dead window's RUNNER log died mid-run (71
suites, no verdict, 17:29) so the full regression is REBURNED fresh
(qa/reconcile-all-R1868-2.log) rather than reused - unlike the R1867
precedent whose dead RUNNER had completed. Fold R499 (R1867
carry-forward deferral) executes before this closeout. Byte-surgery
closeout per closeout_R1866/R1867.py (R1710 discipline).
Faces:
  1. evidence file qa/apidev-keyviewwin-R1868.log (LF, utf-8, no
     BOM, tee dialect) - runs 1/2/3 + census + matrix + RUNNER tail
  2. state/queue/tech.md - flip claim row + done note + reseed
  3. src/os/state.json - tick 1867->1868, gord 307->305, +2 log
     lines (post-fold 10-line state)
  4. heartbeat.txt - +1 row
  5. docs/status-export.json - recompute flush
Chinese payload: src/os/closeout_payload_R1868.json (data file).
Pure stdlib, zero network, pure ASCII source."""
import datetime as _dt
import hashlib
import io
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_PAYLOAD = os.path.join(BASE, "closeout_payload_R1868.json")
P_STATE = os.path.join(BASE, "state.json")
P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_HB = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_EVID = os.path.join(ROOT, "qa", "apidev-keyviewwin-R1868.log")
P_RUNNER = os.path.join(ROOT, "qa", "reconcile-all-R1868-2.log")
P_RUNNER_DEAD = os.path.join(ROOT, "qa", "reconcile-all-R1868.log")
P_SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                      "test_apidev_keyviewwin.py")
TMP = os.path.join(ROOT, ".codely-cli", "tmp")
PY = sys.executable


def detect_eol(text):
    return "\r\n" if "\r\n" in text else "\n"


def norm(b):
    if b[:2] == b"\xff\xfe" or b[:2] == b"\xfe\xff":
        t = b.decode("utf-16")
    else:
        t = b.decode("utf-8-sig", errors="replace")
    return t.replace("\r\n", "\n").replace("\r", "\n")


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    return r.returncode, r.stdout, r.stderr


def main():
    report = []
    with io.open(P_PAYLOAD, encoding="utf-8") as fh:
        payload = json.load(fh)

    # ---------- A. runs identity + fresh live run3 ----------
    with io.open(os.path.join(TMP, "kvw1.txt"), "rb") as h:
        raw1 = h.read()
    with io.open(os.path.join(TMP, "kvw2.txt"), "rb") as h:
        raw2 = h.read()
    with io.open(os.path.join(TMP, "kvw3.txt"), "rb") as h:
        raw3 = h.read()
    r1, r2, r3 = norm(raw1), norm(raw2), norm(raw3)
    sha16 = hashlib.sha256(r1.encode("utf-8")).hexdigest()[:16].upper()
    assert raw1 == raw2 and r1 == r2, "dead-window run1/run2 disagree"
    assert raw1 == raw3 and r1 == r3, "fresh run3 != dead-window run1"
    assert r3.rstrip("\n").endswith("SUITE PASS: 7/7 criteria"), \
        "run3 suite verdict line missing"
    report.append("runs ok: dead 17:19 run1==run2 raw+norm; fresh run3 "
                  "byte-identical; sha16=%s" % sha16)

    # ---------- B. evidence file sections ----------
    with io.open(P_RUNNER, "rb") as h:
        runner_text = h.read().decode("utf-8", errors="replace")
    runner_lines = [ln for ln in runner_text.splitlines()
                    if ln.startswith("PASS suite ledger-apidev-"
                                    "keyviewwin")
                    or ln.startswith("RUNNER PASS")
                    or ln.startswith("PASS suites ")]
    assert any("124/124" in ln for ln in runner_lines), \
        "RUNNER PASS 124/124 line missing from fresh runner log"
    dead_suites = 0
    if os.path.exists(P_RUNNER_DEAD):
        with io.open(P_RUNNER_DEAD, "rb") as h:
            dead_text = norm(h.read())
        dead_suites = len([ln for ln in dead_text.splitlines()
                           if ln.startswith("PASS suite ")])
    parts = []
    parts.append("=== R1868 apidev key_view explicit-history-window "
                 "suite evidence (AC-KVW1..KVW7 pre-registered in "
                 "tech.md claim line by the 17:17 dead window, before "
                 "execution; closeout per R1730/R1675/R1864/R1867 "
                 "interrupted-window precedent - dead-window artifacts "
                 "adopted with zero code change. Deviation from the "
                 "R1867 precedent, honestly noted: the dead window's "
                 "RUNNER log died mid-run at 17:29 (%d suites, no "
                 "verdict, no keyviewwin suite line) so its evidence "
                 "is NOT reusable - the full regression was reburned "
                 "fresh into qa/reconcile-all-R1868-2.log; the dead "
                 "log stays on disk as the honest record) ==="
                 % dead_suites)
    parts.append("--- run 1 verbatim (dead window 17:19, normalized "
                 "EOL) ---")
    parts.append(r1.rstrip("\n"))
    parts.append("--- run 2 determinism (dead window 17:19) ---")
    parts.append("run2 raw bytes == run1 raw bytes: %s" % (raw1 == raw2))
    parts.append("run2 sha256(normalized)=%s"
                 % hashlib.sha256(r2.encode("utf-8")).hexdigest())
    parts.append("--- run 3 live continuation verification (this "
                 "window, PS-capture dialect, byte-identical to "
                 "run1) ---")
    parts.append("run3 raw bytes == run1 raw bytes: %s" % (raw1 == raw3))
    parts.append("--- registration ---")
    parts.append("reconcile_all SUITES row: ledger-apidev-keyviewwin "
                 "criteria=7 (registered by the dead window before "
                 "its 17:26 runner attempt)")
    parts.append("--- dead-window RUNNER forensics (honest record) ---")
    parts.append("dead log qa/reconcile-all-R1868.log: %d PASS-suite "
                 "lines, no RUNNER verdict, no keyviewwin line - "
                 "runner died mid-run; not adopted as regression "
                 "evidence" % dead_suites)
    with io.open(P_EVID, "w", encoding="utf-8", newline="\n") as h:
        h.write("\n".join(parts) + "\n")
    report.append("evidence sections 1-5 written (%d bytes)"
                  % os.path.getsize(P_EVID))

    # ---------- C. census (pre-evidence-complete face) ----------
    rc_c, out_c, err_c = run([PY, os.path.join(BASE,
                             "qa_writer_census.py"), "--check"])
    cens = norm(out_c)
    assert rc_c == 0, "census rc=%d out=%s" % (rc_c, cens[-300:])
    assert "DRIFT-CLEAN" in cens and "flags=0" in cens, \
        "census drift or flags: %s" % cens[-300:]
    cens_verdict = [ln for ln in cens.splitlines()
                    if "verdict" in ln and "DRIFT" in ln]
    cparts = ["--- census qa-writer-census --check (pre-evidence "
              "face) ---", "census exit=0", cens_verdict[-1]]
    with io.open(P_EVID, "a", encoding="utf-8", newline="\n") as h:
        h.write("\n".join(cparts) + "\n")
    report.append("census ok: DRIFT-CLEAN flags=0")

    # ---------- D. matrix regen + check x2 ----------
    mx = [PY, os.path.join(ROOT, "src", "sandbox", "suite_matrix.py"),
          "--evidence", "qa/reconcile-all-R1868-2.log"]
    rc_m, out_m, err_m = run(mx)
    mgen = norm(out_m)
    assert rc_m == 0, "matrix gen rc=%d %s" % (rc_m, mgen[-300:])
    assert "suites=124" in mgen and "criteria=1139" in mgen, \
        "matrix gen counts drift: %s" % mgen[-300:]
    rc_m2, out_m2, _ = run(mx + ["--check"])
    mchk1 = norm(out_m2)
    assert rc_m2 == 0 and "PASS" in mchk1, \
        "matrix check#1 failed: %s" % mchk1[-300:]
    rc_m3, out_m3, _ = run(mx + ["--check"])
    mchk2 = norm(out_m3)
    assert rc_m3 == 0 and "PASS" in mchk2, \
        "matrix check#2 failed: %s" % mchk2[-300:]
    gen_line = [ln for ln in mgen.splitlines()
                if ln.startswith("PASS generated")][0]
    mx_path = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
    mx_bytes = os.path.getsize(mx_path)
    dparts = []
    dparts.append("--- matrix regen + check x2 ---")
    dparts.append(gen_line)
    dparts.append("matrix check#1: rc=0 PASS (byte-identical, %d bytes, "
                  "124 suites, 1139 criteria)" % mx_bytes)
    dparts.append("matrix check#2: rc=0 PASS (byte-identical)")
    dparts.append("--- RUNNER tail (fresh full reburn, this window) ---")
    dparts.extend(runner_lines)
    dparts.append("")
    with io.open(P_EVID, "a", encoding="utf-8", newline="\n") as h:
        h.write("\n".join(dparts) + "\n")
    report.append("matrix ok: gen %d bytes, check x2 PASS identical"
                  % mx_bytes)

    # ---------- E. tech.md flip + done note + reseed ----------
    with io.open(P_TECH, "rb") as fh:
        tech_text = fh.read().decode("utf-8")
    eol = detect_eol(tech_text)
    tech_lines = tech_text.split(eol)
    hits = [i for i, l in enumerate(tech_lines)
            if l.startswith(payload["tech"]["claim_prefix"])]
    assert len(hits) == 1, "claim row hits=%d" % len(hits)
    idx = hits[0]
    assert "R1868 " in tech_lines[idx], "R1868 claim note missing"
    assert "AC-KVW1" in tech_lines[idx] and "AC-KVW7" in tech_lines[idx], \
        "pre-registered criteria block missing"
    done_note = payload["tech"]["done_note"].replace("{SHA16}", sha16)
    assert done_note not in tech_lines[idx], "done note dup"
    tech_lines[idx] = ("- [x] "
                       + tech_lines[idx][len("- [ ] "):] + done_note)
    reseed = payload["tech"]["reseed_line"]
    assert reseed.startswith("- [ ] "), "reseed must be open-checkbox"
    assert reseed not in tech_text, "reseed dup"
    while tech_lines and tech_lines[-1] == "":
        tech_lines.pop()
    tech_lines.append(reseed)
    with io.open(P_TECH, "wb") as fh:
        fh.write((eol.join(tech_lines) + eol).encode("utf-8"))
    open_after = sum(1 for l in tech_lines if l.startswith("- [ ] "))
    assert open_after == 10, "queue_tech_open=%d (expect 10)" % open_after
    report.append("tech.md ok: [x] flip + done note + reseed; open=%d "
                  "eol=%r" % (open_after, eol))

    # ---------- F. state.json CRLF byte surgery (post-fold state) ----------
    with io.open(P_STATE, "rb") as fh:
        raw = fh.read()
    assert raw[:3] != b"\xef\xbb\xbf", "unexpected BOM"
    text = raw.decode("utf-8")
    assert text.count("\n") == text.count("\r\n"), "bare LF in state.json"
    lines = text.split("\r\n")
    assert len(json.loads(text)["log"]) == 10, \
        "expected 10-line post-fold state"
    assert json.loads(text)["tick"] == 1867, "pre-closeout tick drift"

    def replace_once(old, new):
        h2 = [i for i, l in enumerate(lines) if old in l]
        assert len(h2) == 1, "field %r hits=%d" % (old, len(h2))
        lines[h2[0]] = lines[h2[0]].replace(old, new)

    replace_once('"tick": 1867,', '"tick": 1868,')
    replace_once('"last_gord_tbl_rows": 307,',
                 '"last_gord_tbl_rows": %d,'
                 % payload["baselines"]["last_gord_tbl_rows"])
    tick_idx = [i for i, l in enumerate(lines) if '"tick": 1868,' in l]
    assert len(tick_idx) == 1, "tick line not found after bump"
    close_idx = None
    for i in range(tick_idx[0] + 1, len(lines)):
        if lines[i].strip() == "]":
            close_idx = i
            break
    assert close_idx is not None, "log close not found"
    last_item = lines[close_idx - 1]
    assert last_item.startswith(" " * 16), "log indent drift"
    stripped = last_item.rstrip()
    assert stripped.endswith('"') and not stripped.endswith(","), \
        "last item layout drift"
    lines[close_idx - 1] = stripped + ","
    new_lines = [l.replace("{SHA16}", sha16)
                 for l in payload["log_lines"]]
    assert len(new_lines) == 2, "expected 2 log lines"
    items = []
    for i, l in enumerate(new_lines):
        assert "\n" not in l and "\r" not in l, "embedded newline"
        items.append(" " * 16 + json.dumps(l, ensure_ascii=False)
                     + ("," if i < len(new_lines) - 1 else ""))
    lines[close_idx:close_idx] = items
    out_text = "\r\n".join(lines)
    obj = json.loads(out_text)
    assert obj["tick"] == 1868, "tick drift after surgery"
    assert obj["last_gord_tbl_rows"] == 305, "gord baseline drift"
    assert obj["log"][-2].startswith("2026-10-12 R1868 "), \
        "round line prefix drift"
    assert obj["log"][-1].startswith("2026-10-12 R1868 tokens: "), \
        "tokens line prefix drift"
    assert obj["log"][-3].startswith(
        "2026-10-12"), "fold line missing before round lines"
    assert "O-20261012-1710" in obj["log"][-2], \
        "gord full-number reference missing (delivery law)"
    assert "fold R499" in obj["log"][-2], "fold reference missing"
    with io.open(P_STATE, "wb") as fh:
        fh.write(out_text.encode("utf-8"))
    report.append("state.json ok: tick=1868 gord=305 log_items=%d "
                  "bytes=%d" % (len(obj["log"]),
                                len(out_text.encode("utf-8"))))

    # ---------- G. heartbeat ----------
    with io.open(P_HB, "rb") as fh:
        hb_text = fh.read().decode("utf-8")
    hb_eol = detect_eol(hb_text)
    hb_lines = hb_text.split(hb_eol)
    while hb_lines and hb_lines[-1] == "":
        hb_lines.pop()
    assert "tick 1868" not in hb_text, "hb dup"
    ts = _dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M") \
        + " +08:00"
    hb_lines.append("%s | BigDomain OSLoop alive | tick 1868 | %s"
                    % (ts, payload["hb_body"]))
    with io.open(P_HB, "wb") as fh:
        fh.write((hb_eol.join(hb_lines) + hb_eol).encode("utf-8"))
    report.append("heartbeat ok: +1 row (R1868)")

    # ---------- H. export flush ----------
    sys.path.insert(0, BASE)
    import check_export_consistency as cec
    derived, state_obj, export_obj, pat = cec.recompute()
    tick = state_obj["tick"]
    assert tick == 1868, "recompute saw stale tick %s" % tick
    ex = payload["export"]
    export_obj["export_ts"] = _dt.datetime.now().astimezone().isoformat(
        timespec="seconds")
    export_obj["ceo_face"]["current"] = ex["ceo_current"]
    export_obj["ceo_face"]["latest_artifact"] = ex["ceo_artifact"]
    export_obj["ceo_face"]["next_milestone"] = ex["ceo_milestone"]
    sd = dict(derived)
    sd["method"] = ex["self_drive_method"]
    export_obj["self_drive"] = sd
    results = export_obj["results"]
    label = pat["tick_row_label"]
    tick_rows = [r for r in results if isinstance(r, list)
                 and len(r) >= 2 and r[1] == label]
    assert len(tick_rows) == 1, "tick row hits=%d" % len(tick_rows)
    tick_rows[0][0] = str(tick)
    row = ex["result_row"]
    assert isinstance(row, list) and len(row) == 2, "result row shape"
    results.insert(0, row)
    with io.open(P_EXPORT, "wb") as fh:
        fh.write((json.dumps(export_obj, indent=1,
                            ensure_ascii=False) + "\n").encode("utf-8"))
    report.append("export ok: +1 result row results=%d tick_row=%s "
                  "self_drive W=%d sub=%d queues=%d/%d/%d"
                  % (len(results), tick,
                     derived["log_lines_in_window"],
                     derived["substantive_non_idle_mention_lines"],
                     derived["queue_main_open"],
                     derived["queue_tech_open"],
                     derived["queue_explore_open"]))

    for line in report:
        print(line)
    print("closeout complete: 5 faces ok, sha16=%s" % sha16)


if __name__ == "__main__":
    main()
