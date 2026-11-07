"""R2536 state append: tick 2536, the verification window log lines, baseline union.

The shipped state_fold layout reader still does not match the dumped file
(disclosed since R2522), so this appends through a proved load+dump round-trip
instead of reformatting the file.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")

NEW_TOKENS = ["D-20260930-18", "D-20261024-13"]

LINES = [
    "2026-11-07 R2536 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2535, pre-registered 597 suites / 4558 criteria, "
    "re-measured by importing reconcile_all.SUITES and matching byte for "
    "byte). Five-silence scan at open: tree clean at HEAD 428bbdcd with no "
    "index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the "
    "content-addressed decisions diff read TWO tokens over the stored "
    "174-token baseline (D-20260930-18, D-20261024-13) and both are INLINE "
    "REFERENCES inside other rows own prose, cited by rows dated before this "
    "window, so both are ACKNOWLEDGED with no execution face and the baseline "
    "was advanced by union; group orders tail is a fleet audio closeout order "
    "for bm-a/bm-b/bm-c node lanes, not a BigDomain execution face, so it is "
    "noted and not executed; benchmarks 2026-11-03 inside the seven-day gate. "
    "The debt gate read CLAIM-FIRST item=reconcile-battery-R2535 opened=R2535 "
    "first=1 with 16 open rows, so the battery ran before any product byte "
    "per the R2168 mixed-tree rule.",

    "2026-11-07 R2536 BATTERY GREEN ON THE COMMITTED TREE: "
    "qa/reconcile-all-R2536.log 935285B, RUNNER PASS (597/597 suites green, "
    "reconcile controls 7/7, 1448.8s), zero FAIL suite rows, and the runner "
    "own summary line reporting the expected criteria total=4558, so the "
    "registered number and the measured number agree on both axes. The run "
    "launched detached and unfiltered through src/os/battery_stream.py "
    "precisely because the filtering-pipe trap has cost earlier windows their "
    "whole run; the child finished 1448.8s after launch and the evidence was "
    "written once through the single-writer path (bare LF UTF-8). Two FAIL "
    "lines inside the log are FIXTURE expectations (pay-tamper-revokes and "
    "member-tamper both PASS at exit=2 with the FAILS detected and named), and "
    "the R-D2/R-D3 rows are CEO physical-item boundaries, not suite failures.",

    "2026-11-07 R2536 FOLLOW-UP in the designed order: matrix FAILED FIRST on "
    "a stale doc by design (on-disk=57572B regenerated=57573B, no byte "
    "written), then fingerprint PASS verdict CLEAN domains=5, profile PASS "
    "byte-identical, census PASS DRIFT-CLEAN. "
    "docs/sandbox-suite-matrix.md was regenerated stamp-aligned through "
    "src/sandbox/suite_matrix.py --stamp-from to 57573 bytes at 597 suites / "
    "4558 criteria with green honestly 597/597 self-describing from this "
    "round own evidence, --check then read byte-identical, and the four "
    "sections re-ran for VERDICT R2536 PASS failing=none (appended 1950B, "
    "eol_ok=True).",

    "2026-11-07 R2536 DEBT: reconcile-battery-R2535 closed through its "
    "shipped writer (line 267, open 16->15, done 234->235, 164023B -> "
    "164026B, readback ok). NO successor battery is owed because the "
    "registry did not move this window (no module and no suite changed), so "
    "the NEXT window owes a PRODUCT face: product-face-R2536 was appended "
    "first=yes naming the tech head state/queue/tech.md:573 prefix AC-PNKB1 "
    "probe_seam_nested_key_binding_scope, whose six criteria were pinned in "
    "that row at R2535 BEFORE any code (164026B -> 164331B, readback ok).",

    "2026-11-07 R2536 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - this window verified evidence and moved no "
    "product byte, so nothing a CEO could open was built; (b) the battery "
    "was owed and ran to 1448.8s, well past the 25 minute window budget, "
    "because the full battery is the price of a moved registry and the red "
    "leg rule forbids a partial claim; (c) one AUTOMATIC CANCEL was measured: "
    "a silent 5 minute poll loop was cancelled by the shell tool with no "
    "output, and the detached battery was UNAFFECTED because it is a separate "
    "process - the wait was resumed with a heartbeat loop rather than "
    "relaunched, so no duplicate run exists; (d) a first invocation of "
    "battery_followup used --round R2536 and was refused E_BFU_BAD_ARGS "
    "(the flag wants an integer) before any section ran, then the integer "
    "form was used and the sections ran in the designed order; (e) the "
    "registry and criteria counts were RECOMPUTED by import before the launch "
    "rather than trusted from the register; (f) Docker is absent on this host "
    "so no containerised bring-up of the sandbox faces is claimed; (g) the "
    "real 19.9 debit and the real msgSecCheck still wait on CEO physical items "
    "(merchant id, mini-program appid/secret); (h) tasks.md was not touched, "
    "it is the P-47 canonical board; (i) the S4U lane re-registration still "
    "needs an ELEVATED shell and remains a ceo-pending physical item with "
    "zero chase; (j) no fold was due at open (state under the waterline).",

    "R2536 tokens: local=~14k api=0 api_reason=verification window - "
    "five-silence scan, one content-addressed decisions diff read and two "
    "inline references judged knowledge-only, one registry recount by import, "
    "one full battery launched detached through the shipped stream runner "
    "with a single-writer evidence file, seventeen poll cycles with heartbeat "
    "output after one silent-poll cancel, the four follow-up sections run "
    "twice (stale doc first by design, then green), one stamp-aligned matrix "
    "regeneration checked byte-identical, three debt rows moved through their "
    "shipped writers, and the state/export/backlog/heartbeat closeout; zero "
    "cloud calls and zero external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2536
    state["log"].extend(LINES)
    base = list(state.get("last_dec_tokens") or [])
    for token in NEW_TOKENS:
        if token not in base:
            base.append(token)
    state["last_dec_tokens"] = base
    state["last_decision_rows"] = 210
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"])
          and back["tick"] == 2536
          and back["log"][-1] == LINES[-1])
    print("state %s tick=%s log=%d tokens=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             len(back["last_dec_tokens"]), os.path.getsize(PATH),
             "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())