"""R2423 closeout: state tick, log lines, layout canon, waterline fold (one-off)."""
import io
import json
import os
import re
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
GATE = 78500
RESERVE = 6000
BLOCK_END = re.compile(r"^R\d+ tokens:")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

LINES = [
    "2026-11-04 R2423 verification window (five-silence scan clean at open: git status empty at HEAD d96003ec with no .git/index.lock; the evolution ledger carries zero @BigDomain rows; the content-addressed decisions diff read 157 rows and 105 tokens with new=0 against the stored baseline; group orders max_ts is the 2026-11-04 00:46 bm-c de-AI line already acknowledged at R2421, so nothing dispatches this company; benchmarks refreshed 2026-11-03 inside the seven-day gate; queue floor FLOOR-MET main 5/5 tech 10/10 explore 10/10 with tech head line 489 prefix AC-PICB1). The debt gate named CLAIM-FIRST item=reconcile-battery-R2422 with a pre-registered target of 539 suites / 4210 criteria, so the battery ran FIRST on the committed tree with zero product edits.",
    "2026-11-04 R2423 the battery came back RED ON EVIDENCE, NOT CODE, and the red named its own files: RUNNER FAIL 538/539 suites with the criteria total 4210 EXACTLY as pre-registered (953.9s, qa/reconcile-all-R2423.log kept as the red leg), the only red suite being reconcile-daily-census at exit 2. qa_writer_census --check named the cause - qa/plain-import-alias-gate-R2422.log and qa/plain-import-alias-gate-live-R2422.log were captured through a PowerShell redirect, so both landed as ps-utf16 by BOM (class=ps-utf16) inside a pile the census reads as one utf-8 LF dialect.",
    "2026-11-04 R2423 repair at the BIRTH SITE, never by widening the baseline: src/os/repair_R2423.py decodes utf-16, asks the shipped run_identity.normalize for the allowed normalisation, writes utf-8 LF through one atomic replace and proves the line set identical on both sides before the write (2094B -> 1032B and 274B -> 135B, crlf=0 lone_cr=0, read-back equal). The census then reads files=2473 tee=1944 baselined=529 disappeared=0 flags=0 verdict=DRIFT-CLEAN with the baseline untouched, and the repair was committed ALONE as f0271477 before any further byte changed.",
    "2026-11-04 R2423 the retry leg then ran on the committed repair tree: python src/os/battery_stream.py --evidence qa/reconcile-all-R2423-retry.log read RUNNER PASS (539/539 suites green, reconcile controls 7/7, 907.8s) with a measured criteria total of 4210 - the pre-registered number to the unit - plus TMP RECLAIM removed=932 busy=0 failed=0 reclaimed=326.59 MiB; the evidence file is 841118B. The four follow-up sections produced the designed first FAIL (matrix on-disk 51905B against regenerated 51924B, no rewrite), docs/sandbox-suite-matrix.md was regenerated to 51924B at 539 suites / 4210 criteria with --check byte-identical, and the re-run read VERDICT R2423 PASS failing=none (matrix byte-identical 51924B, fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN). Both legs stay appended in the evidence file (1889B FAIL then 1950B PASS, eol_ok=True).",
    "2026-11-04 R2423 debt register after this window: open=2 done=136. reconcile-battery-R2422 was closed through the shipped debt_close at its predicted 102964B -> 102967B (measured exactly, readback=ok) and ONE leader row product-face-R2424 was appended first=yes through the shipped debt_append at its predicted 102967B -> 103429B (readback=ok), naming the next window a product face on the tech head state/queue/tech.md line 489 prefix AC-PICB1 whose criteria were pinned at R2422 before any code. Remaining open: loop-s4u-reconcile and stale-suite-matrix-copy, neither discharged here.",
    "2026-11-04 R2423 honest disclosures: (a) this window shipped ZERO product code and scores 0 product points, deliberately - the R2168 mixed-tree rule makes a product edit inside a verification window invalidate the very measurement the window exists to produce; (b) the red is a transport defect two windows old that the whole battery caught and nothing else did, so the census station earned its keep; (c) MEASURED and named rather than smoothed - the R2422 note recorded qa/plain-import-alias-gate-R2422.log at 1516B while the file on disk before this repair was 2094B of utf-16 that decodes to 1032B of utf-8, so that byte count was itself wrong and is corrected here; (d) the window ran far past its 25-minute budget - the red battery alone cost 953.9s and the retry 907.8s - named rather than hidden; (e) tasks.md was not touched, it is the P-47 canonical board and carries no row for this verification window; (f) the two stale rows loop-s4u-reconcile and stale-suite-matrix-copy were NOT discharged here.",
    "R2423 tokens: local=~26k api=0 api_reason=verification window - one full battery on the committed tree at a pre-registered target (539 suites / 4210 criteria, measured exactly), one red traced to two shell-captured evidence logs and repaired at the birth site through the shipped normalisation law with the payload proved, one repair committed alone, one retry battery to RUNNER PASS, four follow-up sections with one intended matrix FAIL and one green verdict after regenerating the doc, one debt row closed and one leader registered through their shipped CLIs, and the state/export/backlog/heartbeat closeout; zero product code shipped, zero cloud calls and zero external API touches",
    "2026-11-04 R2423 self-heal check: BigDomain-OSLoop exists and is Ready, and its Principal.LogonType still reads Interactive, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 passes an explicit S4U principal and needs an elevated shell while this session is unelevated, so the definition was left untouched again (hundred-and-ninety-third consecutive disclosure, carried as the stale row loop-s4u-reconcile).",
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
    before = state["tick"]
    state["tick"] = before + 1
    state["last_order"] = "2026-11-04 00:46"
    state["last_decision_rows"] = 157
    state["log"].extend(LINES)
    size = write_state(state)
    print("tick %d -> %d lines=%d bytes=%d" % (before, state["tick"],
                                               len(state["log"]), size))
    if size <= GATE - RESERVE:
        print("fold not due gate=%d reserve=%d" % (GATE, RESERVE))
        return
    import state_fold
    ends = [i + 1 for i, item in enumerate(state["log"])
            if BLOCK_END.match(str(item).strip())]
    chosen = None
    for end in ends:
        if end < 2:
            continue
        window = state["log"][1:end]
        if state_fold.round_split(window, state["log"][end:]):
            continue
        with io.open(PATH, "rb") as handle:
            raw = handle.read()
        summary = ("Fold R2423: log items 2..%d moved verbatim to the monthly "
                   "archive at a true round-block boundary." % end)
        plan, _ = state_fold.plan_fold(raw, state, 2, end, summary,
                                       reserve=RESERVE, gate=GATE)
        if plan.get("gate_ok") and not plan.get("tokens_missing"):
            chosen = (end, summary)
            break
    if not chosen:
        print("NO CLEAN FOLD WINDOW - state kept at %dB" % size)
        return
    end, summary = chosen
    result = state_fold.fold(ROOT, "R2423", 651, 2, end, summary,
                             reserve=RESERVE, gate=GATE, execute=True)
    print("fold end=%d post=%s missing=%s"
          % (end, result.get("post_disk_bytes"),
             result.get("token_missing")))


if __name__ == "__main__":
    main()