"""Append the R2481 round log to src/os/state.json (one utf-8 LF writer).

Written as a one-off script so the round's own narrative lands through a single
atomic replace with a byte read-back, the same shape every recent round used.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

TICK = 2481

LOG = [
    "2026-11-06 R2481 BUSINESS window DELIVERED (CEO standing order "
    "OB-20261105-003656-879, real output only; it SUPERSEDES the carried "
    "internal audit row product-face-R2456 by name, which stays open and "
    "claimable at state/queue/tech.md:522 prefix AC-PFKC1). Five-silence scan "
    "at open: git status empty at HEAD 600756dc equal to origin/main with no "
    ".git/index.lock, zero @BigDomain rows in the cph4/evolution-ledger.md, "
    "the content-addressed decisions diff reading new=0 against the stored "
    "token baseline (141 tokens present, none unseen), the group orders tail "
    "unchanged at 2026-11-05 20:22 equal to the stored last_order, benchmarks "
    "refreshed 2026-11-03 inside the seven-day gate, and the queue head still "
    "AC-PFKC1 with claimable rows so no idle declaration was available. CLAIM: "
    "R2477 gave the sandbox one terminal command that starts all six faces and "
    "disclosed the other half as unmet - the hub page is read-only, POST on "
    "/hub/api/faces is pinned 405 by AC-HLL3, so a person in a browser can "
    "never start a face and every card ends in 'start this yourself'. AC-PAN1.."
    "AC-PAN6 were pinned in src/os/backlog.md BEFORE panel.py, panel.html or "
    "test_panel.py existed.",

    "2026-11-06 R2481 SHIPPED src/sandbox/panel.py (pure ASCII, stdlib only) "
    "plus src/sandbox/panel.html (7590B, zero external references) plus one "
    "registry row panel(6): GET /panel and /panel/ serve the page bytes from "
    "disk, GET /panel/api/state publishes the three independently startable "
    "shipped faces (checkout, ledger, ugc) with a live flag measured by a real "
    "TCP connect at call time, POST /panel/api/start really spawns the shipped "
    "entry module through an argv vector led by sys.executable with "
    "CREATE_NO_WINDOW, waits until that socket accepts, and only then hands "
    "back the URL it measured, and POST /panel/api/stop terminates the child "
    "it started and reports the port it saw go quiet. The lobby server is "
    "deliberately NOT startable here because it owns five sockets in one "
    "process and a panel that claimed to start it would be lying; the page "
    "says so in its footer.",

    "2026-11-06 R2481 PROOF: AC-PAN1..AC-PAN6 read SUITE PASS 6/6 TWICE with "
    "identical criterion bodies (digest CEB6D522A66597E5) through the shipped "
    "capture callable at qa/panel-R2481.log (1381B), with two adjacent suites "
    "green in the same capture (ledger/test_ledger_page.py and "
    "lobby/test_hub_page.py). LIVE leg qa/panel-live-R2481.log (362B, crlf=0, "
    "bom=False, one utf-8 LF writer) drove the REAL module over HTTP: page 200 "
    "at 7590B, state 200 naming checkout,ledger,ugc, start 200 spawning ledger "
    "on OS-assigned port 53571 with live=True, the published URL answering 200 "
    "with bytes byte-identical to the shipped ledger.html (7977B), stop 200, "
    "and the port refusing a connect afterwards (still_open=False).",

    "2026-11-06 R2481 one real defect found by running, repaired at its BIRTH "
    "SITE before the battery, never by loosening a criterion: the suite's "
    "report() printed 'AC-PAN1 ... PASS' instead of a PASS/FAIL-prefixed line, "
    "so the first capture digested to E3B0C44298FC1C14 - the sha256 of nothing "
    "- and the shipped battery's ^PASS counter would have read zero criterion "
    "lines for a six-criteria suite. The prefix was corrected in test_panel.py "
    "(with a comment naming why the contract exists), the stale evidence file "
    "was deleted rather than kept, and the capture was re-taken, now reading "
    "digest CEB6D522A66597E5 with legs identical.",

    "2026-11-06 R2481 criterion amendment disclosed rather than hidden: AC-PAN6 "
    "was first drafted with the copied 'imports no clock module' ban the "
    "page-serving suites use, which is impossible for a module whose whole job "
    "is waiting until a spawned socket accepts. The ban was dropped in the "
    "backlog row BEFORE the suite existed and BEFORE any PASS was claimed, with "
    "the reason written into the criterion itself; the wait remains bounded by "
    "an explicit 25s timeout and the teardown by a 3s one, so nothing was "
    "silently weakened.",

    "2026-11-06 R2481 registry, matrix and debt: the registry moved 567 -> 568 "
    "suites and 4378 -> 4384 criteria by exactly one row panel(6), and "
    "docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the last "
    "eligible green battery with 'green=567/568' (honest, because this window "
    "ran no battery) at 54605B, with --check reading byte-identical at 54605B / "
    "568 suites / 4384 criteria. Debt: reconcile-battery-R2481 was appended "
    "first=no through the shipped debt_append at its predicted 124975B -> "
    "125178B with readback ok and the pre-registered target 568 suites / 4384 "
    "criteria, so the NEXT window owes the battery on the committed tree "
    "BEFORE any further product byte (the R2168 mixed-tree rule).",

    "2026-11-06 R2481 honest disclosures: (a) this is a PRODUCT window worth 2 "
    "points on the Executive Protocol scale - a person can now open one page "
    "and start a shipped face with a click, and the proof is a live run against "
    "the real module rather than a plan; (b) what it does NOT do and does not "
    "claim: the panel starts three faces, not the lobby server, because that "
    "process owns ws/city/gate/web/hub together - the terminal launcher "
    "src/sandbox/start_all.py remains the way to bring all six up at once; (c) "
    "the panel is not wired into the hub payload, so the hub page still does "
    "not link to it, and that is the next obvious step rather than a claim of "
    "this one; (d) Docker is absent on this host, so a containerised bring-up "
    "of these faces stays unproved and is not claimed; (e) the real 19.9 debit "
    "and the real msgSecCheck still wait on CEO physical items (merchant id, "
    "mini-program appid/secret); (f) tasks.md was not touched, it is the P-47 "
    "canonical board; (g) no fold was due: src/os/state.json measured 64842B at "
    "open against the 78500B waterline, leaving room for this append but the "
    "next verification window should check the margin before it writes.",

    "R2481 tokens: local=~10k api=0 api_reason=business window - one panel "
    "module with a real spawn/prove/stop lifecycle, one self-contained page, "
    "one six-criteria suite proved twice with a real digest plus two adjacent "
    "suites green in the same capture, one live end-to-end leg against the real "
    "module over HTTP, one process defect (a non-PASS-prefixed report line) "
    "caught and re-taken, one criterion amendment disclosed, one stamp-aligned "
    "matrix restamp with a byte-identical --check, one debt row appended "
    "through its own writer, and the state/export/backlog/heartbeat closeout; "
    "zero cloud calls and zero external API touches",

    "2026-11-06 R2481 self-heal check: BigDomain-OSLoop exists and reads "
    "Running, but its Principal.LogonType still reads InteractiveToken, which "
    "the 2026-09-29 machine law forbids for every lane task; "
    "src/os/register_loop_task.ps1 needs an elevated shell while this session "
    "is unelevated, so the definition was left untouched again (carried as the "
    "stale row loop-s4u-reconcile).",
]


def main():
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    before = os.path.getsize(STATE)
    state["tick"] = TICK
    state.setdefault("log", []).extend(LOG)
    data = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=False)
    tmp = STATE + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(data + "\n")
    os.replace(tmp, STATE)
    with io.open(STATE, encoding="utf-8") as handle:
        back = json.load(handle)
    after = os.path.getsize(STATE)
    print("STATE tick=%d log=%d before=%dB after=%dB readback=%s"
          % (back["tick"], len(back["log"]), before, after,
             "ok" if back["tick"] == TICK else "BAD"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())