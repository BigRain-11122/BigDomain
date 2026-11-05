"""R2489 closeout: append this window's log items and move the tick.

One atomic replace in the state canon, proved by a read-back. Four new group
decision tokens (D-20261106-01..04) were judged KNOWLEDGE-ONLY this window and
are widened into the stored baseline so they cannot re-read as dispatches.
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

NEW_TOKENS = ["D-20261106-01", "D-20261106-02", "D-20261106-03",
              "D-20261106-04"]

LINES = [
    "2026-11-06 R2489 BUSINESS window (CEO standing order OB-20261105-003656-879, real output only). CLAIM: R2487 shipped the membership page - the side of the 19.9 entrance that answers 'what do I hold now' - and disclosed its own unfinished half in the same breath: the face was reachable by command only, because the hub payload never listed it and the control panel could not start it, and its suite was never wired into the runner registry (that closeout said the registry was unmoved at 571/4402). So a person who opened the ONE door could not see or reach the membership surface at all. Five-silence scan at open: git status empty at HEAD 90a245d3 equal to origin/main with no .git/index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the content-addressed decisions diff naming FOUR new tokens D-20261106-01..04, the group orders tail unchanged at 2026-11-05 20:22 equal to the stored last_order, and benchmarks refreshed 2026-11-03 inside the seven-day gate.",
    "2026-11-06 R2489 the four new decision rows were READ IN FULL and all four judged KNOWLEDGE-ONLY with the baseline widened by exactly them: D-20261106-01 is a decisions.md volume split (archive pointer), D-20261106-02 renames the bm-a branch-divergence posture, D-20261106-03 puts BigCompute-LaneTaskGuard on the expected-disabled whitelist, and D-20261106-04 is the collection batch that records all five subsidiaries' mtimes and zero new requests; none dispatches a BigDomain task, so nothing was executed, nothing was rejected, and no work was invented to look busy.",
    "2026-11-06 R2489 SHIPPED the sixth-to-seventh face into the one door and taught the panel to start it: src/sandbox/lobby/hub_page.py gains MEMBER_CMD/MEMBER_NOTE plus member_port (default 8096) in build_faces and in face_ports, src/sandbox/lobby/hub.html gains the member card id=link-member with its data-face=member live marker (seven markers now, zero external references, subtitle corrected from six faces to seven and the footer naming both the flag and the page command), src/sandbox/lobby/server.py advertises --member-port (default 8096) and passes member_port=args.member_port to build_faces, src/sandbox/panel.py gains MEMBER in FACE_MODULES and member in FACE_IDS so a click starts it, src/sandbox/panel.html's footer was rewritten to the five-face truth, and src/sandbox/member/member_page.py's own --port default moved 8095 -> 8096 because 8095 is the hub's customary port and a default run of both would have collided (a real defect found by wiring, fixed at its birth site rather than worked around).",
    "2026-11-06 R2489 PROOF, measured not quoted: AC-HMB1..AC-HMB6 were pinned in src/os/backlog.md BEFORE any of those edits and read SUITE PASS 6/6 TWICE with identical verdicts through the shipped capture callable (qa/hub-member-R2489.log, 1321B, legs=2 identical=True, three adjacent suites green, fails=0). The LIVE leg qa/hub-member-live-R2489.log started the REAL lobby server with a real hub port and the REAL member page on an OS-assigned port: the hub payload published member=http://127.0.0.1:58297/member/ with live[member]=False BEFORE the start, live[member]=True after it with no unrelated face flipped, that published URL answered 200 at 8752B byte-identical to member.html on disk, and both ports refused a connect after teardown. AC-HMB5 is not a table assertion: the panel's own start() spawned the real member page, the published URL served the real bytes, the state read reported live=true at that port, and stop closed it.",
    "2026-11-06 R2489 three neighbouring pinned criteria were amended OPENLY where the product legitimately moved them, none by loosening an assertion: test_hub_panel AC-HPN1 and test_hub_ugc AC-HUG1 both pinned an exact face_ports map, so each gained member=8096 and kept its equality law; test_panel AC-PAN2 and test_panel_lobby AC-LBY1 both pinned an exact startable list, so each gained 'member' and stayed an exact list rather than becoming a subset check (the R2482/R2475 shape). One criterion was REPLACED with its intent preserved and that is disclosed: test_start_all AC-STL6 asserted 'git diff --quiet HEAD' over the hub bytes, which can only hold on the round that wrote it - R2484 already added a hub card and R2489 adds another, so the launcher suite went red for a change the launcher did not make; it now measures that the hub still publishes a URL for every face the launcher plans, and its registry assertion is unchanged.",
    "2026-11-06 R2489 registry, matrix and debt: the registry moved 571 -> 573 suites and 4402 -> 4414 criteria by exactly two rows - lobby-hub-member(6) for this window and member-face(6) for the R2487 suite that had never been wired, which closes a hole this window did not create. docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the last eligible battery evidence qa/reconcile-all-R2488.log to 54983B at 573/4414 with --check reading byte-identical, and its green line honestly reads 571/573 because this window ran no battery. qa_writer_census --check read files=2588 tee=2059 baselined=529 flags=0 verdict DRIFT-CLEAN with its 529-entry baseline untouched. Debt: reconcile-battery-R2489 was appended through the shipped debt_append first=no at 126827B -> 127367B with readback ok and the pre-registered target 573 suites / 4414 criteria, so the NEXT window owes the battery on the committed tree BEFORE any further product byte.",
    "2026-11-06 R2489 honest disclosures: (a) this is a PRODUCT window worth 2 points on the Executive Protocol scale - the membership surface is now one click from the entry page and one click from the control panel, where before it was a command nobody had been told about; (b) what it does NOT do and does not claim: the panel starts member on one port and does not start it together with the lobby, the hub still cannot start anything itself, the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret), and the member page's data directory is still a throwaway temp world per run; (c) the panel.html footer sentence carries an adjacent warning from the page's own encoding - the file is not pure ASCII and one character in the older sentence renders as replacement characters in this session's console, which is a display artefact of the console rather than a byte this window wrote, and it is named rather than silently left; (d) Docker is absent on this host, so a containerised bring-up stays unproved and is not claimed; (e) tasks.md was not touched, it is the P-47 canonical board; (f) no fold was due: src/os/state.json measured 45294B at open against the 78500B waterline with 51 log items.",
    "R2489 tokens: local=~15k api=0 api_reason=business window - one hub payload extension, one page card, one operator flag, one panel face row, one member_page default-port fix, one six-criteria suite proved twice identical plus three adjacent suites green after four open amendments, one live end-to-end leg that started the real lobby server and the real member page and read the published URL back byte-identical, two registry rows wired (one of them closing the R2487 unregistered suite), one stamp-aligned matrix restamp with a byte-identical --check, one debt row appended through its own writer, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-06 R2489 self-heal check: BigDomain-OSLoop exists and reads Ready, but its Principal.LogonType still reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2489
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
          and back["tick"] == 2489
          and back["last_order"] == "2026-11-05 20:22")
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))


if __name__ == "__main__":
    main()