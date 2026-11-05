"""R2486 closeout: append this window's log items and move the tick. One
atomic replace in the state canon, proved by a read-back. No decision token
moved this window (new=0 against the stored baseline), so the baseline list is
carried unchanged and says so.
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
    "2026-11-06 R2486 CLAIMED the carried tech-queue row the debt gate named (product-face-R2456, state/queue/tech.md:522, prefix AC-PFKC1 pinned at R2446 BEFORE any code), after a five-silence scan that was clean at open: git status empty at HEAD ad13ade2 equal to origin/main with no .git/index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the content-addressed decisions diff reading new=0 against the stored 139-token baseline over 304 lines, the group orders tail unchanged at 2026-11-05 20:22 equal to the stored last_order, and benchmarks refreshed 2026-11-03 inside the seven-day gate. debt_gate --check --round R2486 printed verdict=CLAIM-FIRST item=product-face-R2456 opened=R2455 carried=31 stale=yes open=2 first=1, so this window shipped that row rather than running another battery.",
    "2026-11-06 R2486 SHIPPED src/os/row_key_carrier_scope.py: the shipped row-drift reading (comma_binding_face_row_drift, R2446) compares only the keys EVERY publisher face carries, which MEASURED at 6/7/8-wide row shapes is module/receiver/state/text, so `kind` (from-import and relative, 22 rows over 11 files) and `relative` (relative only, 11 rows) were dropped in silence. The new face asks the shipped row-drift reading at CALL time, keeps that report unchanged inside its own, derives each key's carrier set from the rows that actually publish it (never a fixed list), reads every key across its own carriers on every (path, line) cell, names a two-of-three disagreement ROWS-SPLIT with the key and every carrying face, and reports a one-of-three key SINGLE-FACE with its carrier count instead of silence.",
    "2026-11-06 R2486 MEASURED on the REAL tree: verdict=AGREE cells=11 keys=6 all=4 subset=2 singles=1, with kind carriers=2 (from-import,relative) and relative carriers=1 (relative) - exactly the two keys the R2446 intersection dropped, now published rather than silent; qa/row-key-carrier-scope-live-R2486.log is 579B utf-8 LF crlf=0. The blind spot is proved on FIXTURES and is NOT claimed as a live catch: rewriting one from-import `kind` keeps the shipped row-drift reading at FACES-AGREE rc=0 splits=0 while this face reads ROWS-SPLIT naming kind and both carriers, and the all-face keys stay byte-identical to the R2446 reading on both the clean tree and the drifted probe (AC-PFKC4 asserted by JSON equality against the shipped report, not by eyeball).",
    "2026-11-06 R2486 PROOF: AC-PFKC1..AC-PFKC6 read SUITE PASS 6/6 TWICE with an identical criterion digest plus three adjacent comma suites green through the shipped capture callable at qa/row-key-carrier-scope-R2486.log (3118B, legs=2 identical=True adjacent=3 fails=0). The registry moved 570 -> 571 suites and 4396 -> 4402 criteria by exactly one row os-row-key-carrier-scope(6); docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the last eligible battery evidence qa/reconcile-all-R2485.log to 54827B at 571/4402 with --check reading byte-identical, and its green line honestly reads 570/571 because this window ran no battery. qa_writer_census --check read files=2584 tee=2055 baselined=529 flags=0 verdict DRIFT-CLEAN with its 529-entry baseline untouched.",
    "2026-11-06 R2486 DEBT: this window adds one product module and one six-criteria suite, so the R2168 mixed-tree rule makes the NEXT window run a full battery on the committed tree BEFORE any further product byte. reconcile-battery-R2486 was appended through the shipped debt_append first=no at 125935B -> 126340B with readback ok and the pre-registered target 571 suites / 4402 criteria.",
    "2026-11-06 R2486 honest disclosures: (a) this is an INTERNAL audit face, not a CEO-clickable one - what it buys is that the export-reading family can no longer disagree on a key two of its three faces publish without saying so, and the new reading is published text rather than a claim; (b) the live tree carries NO disagreement today, so ROWS-SPLIT and SINGLE-FACE are proved on fixtures only and are NOT claimed as live catches; (c) my own round-open mistake is disclosed: the first live evidence file was written with the child process's own CRLF endings and the census refused it as class=pwsh-capture (flags=1 DRIFT-FLAG), so the file was rewritten as utf-8 LF through an explicit normalisation and the census then read flags=0 - nothing was baselined or widened to make it pass; (d) Docker is absent on this host, so a containerised bring-up of the six sandbox faces stays unproved and is not claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (f) tasks.md was not touched, it is the P-47 canonical board; (g) no fold was due: src/os/state.json measured 29040B at open against the 78500B waterline with 30 log items.",
    "R2486 tokens: local=~13k api=0 api_reason=tech-face window - one carried queue row shipped against criteria pinned two rounds earlier, one new six-criteria module reading every published key across the faces that carry it, one two-leg capture with three adjacent suites green, one live reading on the real tree, one dialect refusal caught by the census and repaired at the source of the bytes, one registry row and one stamp-aligned matrix restamp proved byte-identical, one debt row appended through its own writer, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-06 R2486 self-heal check: BigDomain-OSLoop exists and reads Ready, but its Principal.LogonType still reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2486
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
          and back["tick"] == 2486
          and back["last_order"] == "2026-11-05 20:22")
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())