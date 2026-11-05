"""R2467 closeout: state tick and log lines (one-off)."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
GATE = 78500

if SRC not in sys.path:
    sys.path.insert(0, SRC)

LINES = [
    "2026-11-05 R2467 BUSINESS window, taken on the CEO standing order OB-20261105-003656-879 (real output only) over the carried audit row product-face-R2456 (still open, still claimable, carried rather than dropped). The five-silence scan at open found a DIRTY tree, and that was the first finding: R2466 had finished its work but never committed it - state.json, backlog, export, heartbeat, debt register, residue declaration, matrix and two src/os scripts sat uncommitted at HEAD f7728805 with three untracked evidence logs, origin/main at 06f4473d. The closeout was measured rather than assumed (check_export_consistency pass=21 fail=0 at tick 2466, state 60618B under the 78500B waterline) and committed as 96f24160, so this window started on a clean tree.",

    "2026-11-05 R2467 SHIPPED src/sandbox/lobby/gate.html + src/sandbox/lobby/gate_page.py + one --gate-port flag on server.py: the content gate, which BLUEPRINT section five makes a life-or-death surface, is now a face a person can USE. Until today the shipped msgSecCheck stub could only be driven from a terminal, so nobody could see what the gate decides. The console serves GET /gate and /gate/ from the page bytes on disk, GET /gate/api/contract publishes the endpoint the real WeChat msgSecCheck v2 must satisfy, and POST /gate/api/check runs the SHIPPED stub over the submitted text and returns its own response object unchanged plus one DERIVED key http_decision taken from the stub own is_risky / needs_review helpers, so the suggest-to-action mapping still has exactly one owner and no second wordlist exists. Bring-up: python src/sandbox/lobby/server.py --gate-port 8096 then open http://127.0.0.1:8096/gate/. The face is also listed in the hub payload, so the entry page can reach it.",

    "2026-11-05 R2467 EVIDENCE, measured rather than asserted: AC-GC1..AC-GC6 were written into src/os/backlog.md BEFORE the module, the page or the suite existed (the ordering law honoured this window, and the R2460 lapse is not repeated), and src/sandbox/lobby/test_gate_console.py reads SUITE PASS 6/6 twice with an identical criterion digest (qa/content-gate-console-R2467.log, 1436B, one utf-8 LF writer through src/os/live_R2467.py). Every criterion is read off a REAL server process: the page is 7157B identical to disk and offline; all three standing surfaces plus the CEO-physical-item statement ride in the served page; the contract equals msgsec_stub.contract() asked at call time including provider_prod, endpoint, suggest_values, request_keys, response_keys and result_keys, with blocked_on naming the appid; plain text reads pass/100/SERVE, a word taken from the LIVE config forbidden list reads risky/20001/REFUSE, a word from the LIVE advisory list reads review/20002/REVIEW, every response carries a 32-char trace_id with mock=true billable=false provider=stub, and no configured word appears as a literal in the serving module; the slash forms agree, unknown paths 404 for GET and POST, GET and PUT on the check route 405, blank content 400 E_GC_BAD_CONTENT and an over-length body 413 E_GC_TOO_LONG without reaching the gate. Registry moved exactly one row to 561 suites / 4342 criteria, and four adjacent suites stayed green (hub 6/6, lobby page 6/6, room picker 6/6, checkout demo 6/6 with its digest unchanged at 46654133EC75D89438D1B6C4547C79CE).",

    "2026-11-05 R2467 LIVE, not a plan: qa/content-gate-console-live-R2467.log is a real server started the way a person would start it - the banner carries gate=http://127.0.0.1:<bound port>/gate/ max_len=2000 and hub=http://127.0.0.1:<bound port>/hub/ faces=14, GET /gate/ answered 200 at 7157 bytes with all four notices present, GET /gate/api/contract answered the WeChat endpoint with blocked_on=CEO physical item: mini-program appid/secret, and the three probes read SERVE / REFUSE / REVIEW with mock=True billable=False while a blank body answered 400 E_GC_BAD_CONTENT; the process was terminated with zero survivors, and the hub payload published the same gate URL.",

    "2026-11-05 R2467 matrix and debt register: docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the only eligible green evidence face (qa/reconcile-all-R2466-retry2.log) through src/sandbox/suite_matrix.py and now reads 54146B, registry suites=561 criteria=4342, with --check byte-identical and its green line honestly reading 560/561 because no battery log carries the new suite yet. reconcile-battery-R2467 was opened first=no through debt_append at 121071B -> 121381B (readback=ok) because product src bytes changed and the registry moved, so the R2168 mixed-tree rule owes the battery next at the pre-registered 561 suites / 4342 criteria.",

    "2026-11-05 R2467 honest disclosures: (a) the window claimed two product points for a face a person can click and read; (b) two birth defects of my own were caught by RUNNING rather than by reading - a wrong replace removed the lobby_page bring-up line inside main() (syntax-invisible, caught on the first suite run and restored in the same edit that wired the gate console), and src/os/live_R2467.py first computed the repo root one level too shallow so every subprocess call died with WinError 267 (fixed in the capture script, not in a criterion); (c) the suite is a real-server suite, so its six criteria are only true while a process can bind a loopback port - the same limitation every shipped sandbox face carries and it is not claimed beyond that; (d) Docker is absent on this host, so a containerised bring-up of this face stays unproved and is not claimed; (e) the real msgSecCheck and the real 19.9 debit still wait on CEO physical items (mini-program appid/secret, merchant id), and the page says so on screen instead of pretending to be the production gate; (f) tasks.md was not touched, it is the P-47 canonical board; (g) READ-ONLY observation outside this repo: FluxGroup/docs/orders.md still carries its leftover empty conflict markers, already reported in HQ-FEEDBACK.md.",

    "R2467 tokens: local=~13k api=0 api_reason=business window - one content-gate console (page plus read face plus contract route plus a check route that reuses the shipped stub), one server flag and one hub face, one six-criteria suite proved twice with an identical digest plus four adjacent suites re-run green, one real-process live capture, one registry row, one stamp-aligned matrix regeneration with a byte-identical check, one battery debt row appended through its shipped CLI, the adoption and commit of the R2466 closeout that a dead window left uncommitted, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
]


def write_state(state):
    import state_io
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    if back["tick"] != state["tick"] or len(back["log"]) != len(state["log"]):
        raise SystemExit("E_CLOSEOUT_READBACK")
    return os.path.getsize(PATH)


def main():
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("log already carries this window")
        size = os.path.getsize(PATH)
    else:
        state["tick"] = state["tick"] + 1
        state["log"].extend(LINES)
        size = write_state(state)
    print("tick %d lines=%d bytes=%d" % (state["tick"], len(state["log"]), size))
    print("fold due=%s gate=%d" % (size > GATE, GATE))


if __name__ == "__main__":
    main()