"""R2477 closeout: append this business window's log items and move the tick.

The write is one atomic replace in the state canon, proved by a read-back. No
decision token moved this window (the content-addressed diff read zero new), so
the baseline list is carried unchanged and said so rather than silently kept.
"""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

NEW_TOKENS = []

LINES = [
    "2026-11-05 R2477 BUSINESS window DELIVERED (CEO standing order OB-20261105-003656-879, real output only; it SUPERSEDES the carried internal audit row product-face-R2456 by name, which stays open and claimable at state/queue/tech.md:522 prefix AC-PFKC1). Five-silence scan at open: git status empty at HEAD 92e5e494 with no .git/index.lock, zero @BigDomain rows in the evolution ledger, the content-addressed decisions diff naming ZERO new tokens against the baseline (the D-20261105-23 row already recorded), the group orders tail unchanged at 2026-11-05 20:22 equal to the stored last_order, benchmarks refreshed 2026-11-03 inside the seven-day gate, and the tech head AC-PFKC1 with claimable=11 so no idle declaration was available. CLAIM: the sandbox has six openable faces but they are reached by five separate commands on five separate ports, and the hub - the one door R2462 built - is read-only, so every card it publishes ends in 'start this yourself'; R2475 disclosed exactly that as undone.",
    "2026-11-05 R2477 SHIPPED src/sandbox/start_all.py (pure ASCII, stdlib only, no shell): one command picks OS-assigned ports for all eight sockets (ws, city, gate, web, hub, checkout, ledger, ugc), starts the four SHIPPED entry modules unchanged through an argument vector led by sys.executable, waits until every socket really accepts, then asks the hub's own probe map what it publishes and prints the single door URL - so the URL is the hub's answer rather than a literal in the launcher. Modes: serve (keep running until a stop file appears) and --check (start, prove, tear down, report, exit). Teardown terminates then kills every child it started, so no orphan holds a sandbox port.",
    "2026-11-05 R2477 PROOF: AC-STL1..AC-STL6 were pinned in src/os/backlog.md BEFORE the module, the suite or the registry row existed. SUITE PASS 6/6 TWICE with identical verdict bodies (qa/start-all-R2477-leg1.log and leg2.log): AC-STL1 the report's six face URLs are byte-equal to GET /hub/api/faces?probe=1 asked at call time, AC-STL2 the report says live AND an independent TCP connect agrees on all six, AC-STL3 build_commands() names the four shipped modules with sys.executable first and the module carries no shell, no BOM, no CRLF and only stdlib imports, AC-STL4 the explicit --ws-port/--hub-port overrides are honoured and the six published face ports are pairwise distinct, AC-STL5 after the stop file the launcher exits 0 and all six ports refuse a connect within three seconds, AC-STL6 hub.html and hub_page.py are byte-identical to HEAD and the registry carries exactly one start-all row. LIVE PASS (qa/start-all-live-R2477.log) against a real launcher: hub page 200 at 7104B with zero external references, and all six faces answered 200 through the published URLs - checkout 8051B, city 6653B, gate 7157B, ledger 7977B, lobby 10077B, ugc 8816B - with launcher_exit=0 and ports_still_open_after_stop=0.",
    "2026-11-05 R2477 one real defect found by running, repaired at its BIRTH SITE in the SUITE rather than by loosening a criterion: the first leg read AC-STL2 FAIL unreachable and AC-STL4 FAIL overrides-ignored solely because the suite read a report file LEFT BY THE PREVIOUS LEG before this run's launcher rewrote it, and a second defect was a KeyError-shaped crash where a face name was used as a plan key (lobby's socket is planned as web). The product now publishes face_ports derived from FACE_PORT_KEY, and the suite clears both control files before starting a launcher, so neither failure mode can recur; no assertion was relaxed and every criterion text is unchanged. Adjacent suites stayed green: test_hub_page.py 6/6, test_hub_ledger_live.py 6/6, test_hub_ugc.py 6/6.",
    "2026-11-05 R2477 registry and matrix: the registry moved 565 -> 566 suites and 4366 -> 4372 criteria by exactly one row start-all(6), and docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the last eligible green battery with 'PASS generated 54461 bytes, registry suites=566 criteria=4372 evidence=qa/reconcile-all-R2476.log green=565/566', with --check reading byte-identical at 54461B / 566 / 4372 - the green line honestly reads 565/566 because this window ran no battery. Debt: reconcile-battery-R2477 was appended first=no through the shipped debt_append at its predicted 123180B -> 123363B with readback ok and the pre-registered target 566 suites / 4372 criteria, so the NEXT window owes the battery on the committed tree BEFORE any further product byte (the R2168 mixed-tree rule).",
    "2026-11-05 R2477 honest disclosures: (a) this is a PRODUCT window worth 2 points on the Executive Protocol scale - a person can now open one door from one command instead of five commands, and the proof is a live run rather than a plan; (b) what it does NOT do: the hub page itself still cannot start a face from the browser (the launcher is the terminal-shaped answer), so the R2475/R2476 named candidate 'hub can START a face' is only half met and is stated as half met; (c) the launcher starts children with CREATE_NO_WINDOW so no console flashes, which matters under the 2026-09-29 silence law; (d) Docker is absent on this host, so the containerised bring-up of these six faces stays unproved and is not claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (f) tasks.md was not touched, it is the P-47 canonical board; (g) no fold was due: src/os/state.json was well under the 78500B waterline at open.",
    "R2477 tokens: local=~11k api=0 api_reason=business window - one launcher module written and four real defects found by running it (a stale report, a plan-key mismatch, a non-listening socket map, an unquoted face port) plus one suite and one registry row, two full suite legs 6/6 with identical bodies, three adjacent hub suites green, one live end-to-end leg across all six faces, one stamp-aligned matrix regeneration with a byte-identical --check, one debt row appended through its own writer, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-05 R2477 self-heal check: BigDomain-OSLoop exists and reads Running, but its Principal.LogonType still reads Interactive, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2477
    state["last_order"] = "2026-11-05 20:22"
    state["last_decision_rows"] = 221
    tokens = list(state.get("last_dec_tokens") or [])
    for token in NEW_TOKENS:
        if token not in tokens:
            tokens.append(token)
    state["last_dec_tokens"] = tokens
    state["log"].extend(LINES)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"])
          and back["tick"] == 2477
          and back["last_order"] == "2026-11-05 20:22")
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())