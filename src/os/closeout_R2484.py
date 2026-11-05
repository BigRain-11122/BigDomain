"""R2484 closeout: fold at a true round-block boundary, then append this
window's log items and move the tick. One atomic replace in the state canon,
proved by a read-back.

The fold window is lines 1..78, i.e. the whole R2474..R2482 blocks plus the
previous fold summary; line 79 opens R2483, so the cut is a real round-block
boundary rather than merely a tokens line. Every AC- token in the folded
window is carried into the summary, which state_fold.plan_fold refuses to let
us skip.
"""
import io
import json
import os
import re
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
ARCHIVE = os.path.join(ROOT, "logs", "state-log-archive-2026-11.md")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

import state_fold  # noqa: E402
import state_io  # noqa: E402

TOKEN_RE = state_fold.PAT

LINES = [
    "2026-11-06 R2484 BUSINESS window DELIVERED (CEO standing order OB-20261105-003656-879, real output only; it SUPERSEDES the carried internal audit row product-face-R2456 by name, which stays open and claimable at state/queue/tech.md:522 prefix AC-PFKC1). Five-silence scan at open: git status empty at HEAD 54205c74 equal to origin/main with no .git/index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the content-addressed decisions diff reading new=0 against the stored 142-token baseline, the group orders tail unchanged at 2026-11-05 20:22 equal to the stored last_order, benchmarks refreshed 2026-11-03 inside the seven-day gate, and the queue head AC-PFKC1 with claimable=12 so no idle declaration was available. CLAIM: R2481 shipped the panel and R2482 taught it to start the lobby, and BOTH windows disclosed the same unfinished half - the hub entry page never linked to the panel, so a person who opens the ONE door never learns a click-to-start surface exists and the hub own live map could not report it.",
    "2026-11-06 R2484 SHIPPED the sixth face into the one door: src/sandbox/lobby/hub_page.py gains PANEL_CMD/PANEL_NOTE plus panel_port (default 8099) in build_faces and in face_ports, src/sandbox/lobby/hub.html gains the panel card id=link-panel with its data-face=panel live marker (six markers now, zero external references, the subtitle corrected from five faces to six and the footer naming both the server flag and the panel command), and src/sandbox/lobby/server.py advertises --panel-port (default 8099) and passes panel_port=args.panel_port to build_faces so the published URL is the port the operator chose; src/sandbox/lobby/test_hub_panel.py wires AC-HPN1..AC-HPN6 into the registry as lobby-hub-panel(6).",
    "2026-11-06 R2484 PROOF: AC-HPN1..AC-HPN6 were pinned in src/os/backlog.md BEFORE the code, the suite read SUITE PASS 6/6 TWICE with identical verdicts through the shipped capture callable at qa/hub-panel-R2484.log (1163B, utf-8, crlf=0, bom=False), and the LIVE leg qa/hub-panel-live-R2484.log started the REAL lobby server and the REAL panel on OS-assigned ports: hub page 200 at 7853B byte-identical to disk, the payload published panel=http://127.0.0.1:65087/panel/ with live[panel]=True, that published URL answered 200 at 7738B byte-identical to panel.html on disk, /panel/api/state answered 200 with startable=checkout,ledger,ugc,lobby, and the panel port refused a connect after teardown.",
    "2026-11-06 R2484 one neighbouring pinned criterion was amended OPENLY where the product legitimately moved it, never by loosening an assertion: src/sandbox/lobby/test_hub_ugc.py AC-HUG1 compared face_ports to an exact six-key map, so the first run of this window own suite read AC-HPN5 FAIL solely because that neighbour refused the seventh key (the R2475 shape again). The map gained panel=8099 and keeps its equality law rather than being weakened to a subset, with the reason written into the suite beside it; no other assertion and no other criterion text was touched, and all three adjacent suites now read SUITE PASS 6/6.",
    "2026-11-06 R2484 registry, matrix and debt: the registry moved 569 -> 570 suites and 4390 -> 4396 criteria by exactly one row lobby-hub-panel(6); docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the last eligible green battery to 54765B with its green line honestly reading 569/570 because this window ran no battery, and --check reads byte-identical at 54765B / 570 suites / 4396 criteria; qa_writer_census --check read flags=0 verdict DRIFT-CLEAN with its 529-entry baseline untouched. Debt: reconcile-battery-R2484 was appended first=no through the shipped debt_append at 125395B -> 125931B with readback ok and the pre-registered target 570 suites / 4396 criteria, so the NEXT window owes the battery on the committed tree BEFORE any further product byte (the R2168 mixed-tree rule).",
    "2026-11-06 R2484 honest disclosures: (a) this is a PRODUCT window worth 2 points on the Executive Protocol scale - the hub, which is the one URL a person opens, finally leads to the control panel and marks whether that panel is really listening; (b) what it does NOT do and does not claim: the hub itself still cannot START anything (that remains the panel own job, one click further), and the poll is a 0.35s TCP connect rather than a health contract, so a process that holds the port without serving reads alive - the limitation is stated rather than hidden; (c) the round re-paid one small self-inflicted cost and says so: debt_append requires --opened, which this window omitted at first, so it printed its usage instead of writing and nothing was appended twice; (d) Docker is absent on this host, so a containerised bring-up of the six faces stays unproved and is not claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (f) tasks.md was not touched, it is the P-47 canonical board; (g) a fold was DUE and ran: src/os/state.json measured 78345B at open, only 155B under the 78500B waterline, so log items 1..78 (the whole R2474..R2482 blocks) were moved verbatim into logs/state-log-archive-2026-11.md at a true round-block boundary BEFORE this append, with every AC- token in that window carried into the fold summary.",
    "R2484 tokens: local=~9k api=0 api_reason=business window - one hub payload extension, one page card, one operator flag, one six-criteria suite proved twice with identical verdicts through the shipped capture callable, one live end-to-end leg that started the real lobby server and the real panel and read the published URL back byte-identical, one open amendment in a neighbour suite pinned exact rather than loosened, one stamp-aligned matrix restamp with a byte-identical --check, one debt row appended through its own writer, one waterline fold at a true round-block boundary, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-06 R2484 self-heal check: BigDomain-OSLoop exists and reads Running, but its Principal.LogonType still reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    with io.open(PATH, "rb") as handle:
        raw = handle.read()
    state = json.loads(raw.decode("utf-8"))
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0

    start, end = 1, 78
    window = state["log"][start - 1:end]
    tokens = sorted(set(TOKEN_RE.findall("\n".join(window))))
    summary = ("Fold R2484: log items %d..%d moved verbatim into the monthly "
               "archive at a true round-block boundary (the whole R2474..R2482 "
               "blocks plus the previous fold summary); tokens covered %s"
               % (start, end, ",".join(tokens)))
    plan, folded_text = state_fold.plan_fold(raw, state, start, end, summary,
                                            reserve=6000)
    print("FOLD PLAN window=%d:%d lines=%d split=%r tokens=%d missing=%d "
          "predicted=%dB margin=%d gate_ok=%s"
          % (plan["window_start"], plan["window_end"], plan["window_lines"],
             plan["round_split"], plan["tokens_total"],
             len(plan["tokens_missing"]), plan["predicted_bytes"],
             plan["margin"], plan["gate_ok"]))
    if plan["round_split"] or not plan["gate_ok"] or not plan["token_ok"]:
        print("FOLD REFUSED split=%r gate_ok=%s token_ok=%s"
              % (plan["round_split"], plan["gate_ok"], plan["token_ok"]))
        return 3
    header = "# --- Fold R2484 (2026-11-06) log items %d..%d ---" % (start, end)
    state_fold.append_archive(ARCHIVE, header, window, allow_create=True)

    folded = json.loads(folded_text)
    folded["tick"] = 2484
    folded["log"].extend(LINES)
    text = json.dumps(folded, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(folded["log"])
          and back["tick"] == 2484
          and back["log"][-1] == LINES[-1])
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())