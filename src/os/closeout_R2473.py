"""R2473 closeout: state tick and log lines, backlog row flip, heartbeat row."""
import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
BACKLOG = os.path.join(SRC, "backlog.md")
BEAT = os.path.join(ROOT, "heartbeat.txt")

TICK = 2473

LINES = [
    "2026-11-05 R2473 BUSINESS window, taken on the CEO standing order "
    "OB-20261105-003656-879 (real output only) and SUPERSEDING the carried "
    "internal audit row product-face-R2456 by name - that row stays open and "
    "claimable at state/queue/tech.md:522 prefix AC-PFKC1 and is CARRIED, never "
    "dropped. Five-silence scan at open: git status empty at HEAD f9f83a3f equal "
    "to origin/main with no .git/index.lock, zero @BigDomain rows in the evolution "
    "ledger, the content-addressed decisions diff new=0 against the 135-token / "
    "211-row baseline, the group orders tail unchanged at 2026-11-05 00:36 equal "
    "to the stored last_order, benchmarks refreshed 2026-11-03 inside the "
    "seven-day gate. FINDING before any code: the P-47-3b UGC pipeline "
    "(src/sandbox/ugc/pipeline.py, store.py, wordlist.py, review.py, twenty-odd "
    "suites) exists and is proved, but it could only be driven from a terminal - "
    "a person could not submit a sentence, could not see whether it landed as "
    "pass / review / risky, could not watch a gray-zone case wait for a human "
    "verdict, and could not see the pool move. AC-UGW1..AC-UGW6 were written into "
    "src/os/backlog.md BEFORE the page, the module and the suite existed.",

    "2026-11-05 R2473 SHIPPED src/sandbox/ugc/ugc_console.html (8816B "
    "self-contained console: actor field, one sentence box, the receipt the "
    "pipeline really returned, a suspended-review list with pass/risky buttons, "
    "and a pool block with per-line counts; zero external references, the live "
    "config AI label and the non-advice disclaimer verbatim, and a mock statement "
    "on screen) plus src/sandbox/ugc/ugc_page.py (pure ASCII stdlib face: GET /ugc "
    "and /ugc/ serve the page bytes from disk; GET /ugc/api/state publishes the "
    "suspended rows read from the SHIPPED review table, the SHIPPED pool_query "
    "items and per-line counts derived from them, plus the standing notices read "
    "from config.json at call time; POST /ugc/api/submit grants the MOCK entrance "
    "through the SHIPPED grant_entrance_sandbox and returns the pipeline receipt "
    "unchanged; POST /ugc/api/verdict drives the SHIPPED review_verdict; unknown "
    "404, POST on the state route 405, blank 400, over-length 413) plus one "
    "reconcile_all.py registry row ugc-console(6). Bring-up: python "
    "src/sandbox/ugc/ugc_page.py --port 8098 then open http://127.0.0.1:8098/ugc/.",

    "2026-11-05 R2473 EVIDENCE, measured rather than asserted: "
    "src/sandbox/ugc/test_ugc_console.py reads SUITE PASS 6/6 TWICE with an "
    "identical criterion digest E8C2DB4ACF5DAFC0 through the shipped capture "
    "callable (EVIDENCE CAPTURE round=R2473 legs=2 identical=True fails=0, "
    "qa/ugc-console-R2473.log 1665B, one utf-8 LF writer), with three adjacent "
    "suites re-run green inside the same capture (ugc 37/37 criteria, "
    "water-journal 7/7, reviewdesk-persist 7/7). Every criterion is read off a "
    "REAL server on an OS-assigned port over a private temp world: the page is "
    "8816B identical to disk on both slash forms and offline; an empty world reads "
    "an empty review list and an empty pool with notices equal to the live config; "
    "a clean sentence returns received=True gate=pass with the shipped 16-hex "
    "content address and appears in the pool while a blank body is 400 and an "
    "over-length body is 413 and neither stores an item; a LIVE forbidden word is "
    "refused 422 E_CONTENT_REJECTED with nothing stored and a LIVE gray word lands "
    "gate=review suspended=True as exactly one suspended row, with no configured "
    "word appearing as a module literal; the pass verdict routes the case into the "
    "pool and drops it from the suspended list, a second verdict is refused 409 "
    "E_REVIEW_DONE, a risky verdict answers 422 E_CONTENT_REJECTED while the queue "
    "row keeps its trace, and an unknown case is 404 E_UGW_UNKNOWN_CASE; hygiene "
    "reads unknown 404, POST on the state route 405, PUT 405, module pure ASCII "
    "with no clock import, page BOM-free and CRLF-free, registry row present.",

    "2026-11-05 R2473 LIVE, not a plan: src/os/live_R2473.py starts the real "
    "process the way a person would (python src/sandbox/ugc/ugc_page.py --port "
    "<free> --db <temp>) and writes qa/ugc-console-live-R2473.log itself as ONE "
    "utf-8 LF single writer - state 200 review=0 pool=0 max_len=2000, page 200 at "
    "8816 bytes, submit 200 gate=pass received=True evt=a5ec6389e4b055ed, gray "
    "submit 200 gate=review suspended=True, verdict 200, after 200 review=0 "
    "pool=2, VERDICT PASS, child_pid=96396 child_alive=False. The log measures "
    "282B with crlf=0 and bom=False.",

    "2026-11-05 R2473 TWO OWN DEFECTS CAUGHT BY RUNNING, and the fix direction "
    "named honestly: (a) my pre-registered AC-UGW3 said the evt_id is 32 hex while "
    "the SHIPPED compute_evt_id returns a 16-hex content address - that is a "
    "pre-registration measurement error, so the CRITERION was corrected to the "
    "measured width and the correction is disclosed here rather than hidden; (b) "
    "POST on the read route answered 404 where the pre-registered criterion asks "
    "405, which is a real module defect, so ugc_page.py was FIXED to answer 405 on "
    "the state route and the criterion was left as written - the module moved, not "
    "the law.",

    "2026-11-05 R2473 matrix and debt register: docs/sandbox-suite-matrix.md was "
    "regenerated stamp-aligned from the last eligible green evidence "
    "(qa/reconcile-all-R2472-retry.log) through src/sandbox/suite_matrix.py "
    "--evidence plus --stamp-from and now reads 54354B at registry suites=564 "
    "criteria=4360, with --check byte-identical and its green line honestly "
    "reading 563/564 because no battery log carries the new suite yet. "
    "reconcile-battery-R2473 was opened first=no through the shipped debt_append "
    "at 122269B -> 122765B (readback=ok) because product src bytes changed and the "
    "registry moved 563->564 suites / 4354->4360 criteria, so the R2168 "
    "mixed-tree rule puts the battery first in the next window at the "
    "pre-registered 564 suites / 4360 criteria. qa_writer_census re-read flags=0 "
    "DRIFT-CLEAN with its 529-entry baseline untouched.",

    "2026-11-05 R2473 honest disclosures: (a) this window claims two product "
    "points for a flow a person can click through - submit, watch the gate decide, "
    "take a gray case to a verdict, and watch the pool move; (b) it is a sandbox "
    "face on the SHIPPED pipeline and it says so on screen: the entrance "
    "credential is mock, nothing is chargeable, and the real msgSecCheck still "
    "waits on the CEO physical item (mini-program appid/secret), so what a reader "
    "sees is the sandbox stub deciding, not the production gate; (c) the module "
    "carries one new read (the suspended list behind the shipped review table) "
    "because no list reader existed - it goes through the store own handle and "
    "adds no second law, and the pool block is the SHIPPED pool_query unchanged; "
    "(d) Docker is absent on this host, so a containerised bring-up stays unproved "
    "and is not claimed; (e) the console is its own process and is NOT yet listed "
    "in the lobby hub payload - that wiring is named here and left to a later "
    "window rather than smuggled into this one; (f) tasks.md was not touched, it "
    "is the P-47 canonical board; (g) READ-ONLY observation outside this repo: "
    "FluxGroup/docs/orders.md still carries its leftover empty conflict markers, "
    "already reported in HQ-FEEDBACK.md.",

    "R2473 tokens: local=~12k api=0 api_reason=business window - one operable "
    "console page, one pure-ASCII serving module over the shipped pipeline / store "
    "/ wordlist / review with four routes and no second law, one six-criteria "
    "suite proved twice with an identical digest plus three adjacent suites re-run "
    "green, one real-process live capture written by a single utf-8 LF writer, one "
    "registry row, one stamp-aligned matrix regeneration with a byte-identical "
    "check, one battery debt row appended through its shipped CLI, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero external "
    "API touches",
]

ROW_OLD = "- [ ] R2473 BUSINESS window (CEO standing order OB-20261105-003656-879, real output only; supersedes the carried internal audit row product-face-R2456 by name, which stays open and claimable at state/queue/tech.md:522 prefix AC-PFKC1)."
ROW_NEW = "- [x] [done 2026-11-05 R2473] R2473 BUSINESS window (CEO standing order OB-20261105-003656-879, real output only; supersedes the carried internal audit row product-face-R2456 by name, which stays open and claimable at state/queue/tech.md:522 prefix AC-PFKC1). SHIPPED src/sandbox/ugc/ugc_console.html (8816B, offline, live-config notices) + src/sandbox/ugc/ugc_page.py (pure ASCII; /ugc + /ugc/ page, /ugc/api/state derived, /ugc/api/submit through grant_entrance_sandbox + submit, /ugc/api/verdict through review_verdict; unknown 404, POST-on-state 405, blank 400, over-length 413) + one registry row ugc-console(6). AC-UGW1..AC-UGW6 pre-registered BEFORE the code read SUITE PASS 6/6 twice with identical digest E8C2DB4ACF5DAFC0 (qa/ugc-console-R2473.log, 1665B, one utf-8 LF writer) plus three adjacent suites green (ugc 37/37, water-journal 7/7, reviewdesk-persist 7/7) and LIVE PASS (qa/ugc-console-live-R2473.log: state 200, page 8816B, submit pass, gray suspended, verdict 200, pool 2, review 0, child dead). Matrix restamped 54354B at 564/4360 with --check byte-identical (green honestly 563/564); reconcile-battery-R2473 opened first=no at 122269B -> 122765B. Two own defects caught by running: the pre-registered 32-hex evt_id was a measurement error corrected to the shipped 16-hex width, and POST on the read route was a real module defect fixed to 405 (module moved, criterion not loosened). Honest: sandbox face on the shipped pipeline with a mock entrance, real msgSecCheck still blocked on CEO physical items, Docker absent, console not yet in the hub payload. CLAIM-DETAILS AS WRITTEN BELOW: the claim row and the six criteria stand exactly as pre-registered in this board entry, with the AC-UGW3 width correction disclosed above."

BEAT_LINE = (
    "tick=2473 R2473 business: UGC pipeline console shipped (page + submit + "
    "suspended review + verdict + pool over the shipped pipeline), SUITE 6/6 twice "
    "identical digest E8C2DB4ACF5DAFC0, three adjacent suites green, live PASS, "
    "matrix restamped 54354B at 564/4360 | reconcile-battery-R2473 owed first next "
    "window (564/4360) | supersedes audit row product-face-R2456 by name"
)


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
    else:
        state["tick"] = TICK
        state["log"].extend(LINES)
        size = write_state(state)
        print("state tick %d, log +%d, bytes=%d" % (TICK, len(LINES), size))

    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if ROW_OLD in text:
        text = text.replace(ROW_OLD, ROW_NEW, 1)
        tmp = BACKLOG + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp, BACKLOG)
        print("backlog row flipped to done")
    else:
        print("backlog row already flipped")

    with io.open(BEAT, "r", encoding="utf-8", newline="") as handle:
        beat = handle.read()
    if BEAT_LINE not in beat:
        newline = "\r\n" if "\r\n" in beat else "\n"
        if not beat.endswith(("\n", "\r")):
            beat += newline
        beat += BEAT_LINE + newline
        tmp = BEAT + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
            handle.write(beat)
        os.replace(tmp, BEAT)
        print("heartbeat row appended")
    else:
        print("heartbeat row already present")


if __name__ == "__main__":
    main()