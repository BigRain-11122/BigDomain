"""R2532 state append: the verification window on the battery R2531 owed."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-07 R2532 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2531, pre-registered 595 suites / 4546 criteria, and "
    "the target was RE-MEASURED by importing reconcile_all.SUITES before "
    "anything ran - byte for byte the registered number, after R2531 moved the "
    "registry by exactly one row os-probe-seam-for-container-name(6)). Five-"
    "silence state at open: the tree was CLEAN at HEAD f6ec7fd6 with no "
    "index.lock; the debt gate read CLAIM-FIRST reconcile-battery-R2531 "
    "first=1; the content-addressed decisions scan read new=0 over the stored "
    "baseline (the five D-20261107-18..22 tokens R2531 judged were already "
    "absorbed); zero unreplied @BigDomain rows in cph4/evolution-ledger.md; "
    "and the group orders tail moved to 2026-11-07 18:01 - read and judged NOT "
    "this company execution face (OB-20261107-180106-609 is a fleet role "
    "dispatch naming bm-a/bm-b/bm-c machine lanes and an audio BGM fill "
    "receipt, so this window KNOWS of it and acts on none of it, with the "
    "number referenced here as the delivery law requires); benchmarks "
    "2026-11-03 inside the seven-day gate. RESULT GREEN ON THE FIRST LEG, "
    "measured not quoted: qa/reconcile-all-R2532.log is 926711B as delivered "
    "(1978B follow-up block appended to a 926711B green leg, 928689B on disk), "
    "utf-8 bom=False crlf=0 nul=0 lone_cr=0, closing RUNNER PASS (595/595 "
    "suites green, reconcile controls 7/7, 1212.5s), ZERO FAIL suite rows, and "
    "an independent recount over the 595 PASS rows summing to EXACTLY 4546 "
    "criteria; launched detached and unfiltered through src/os/battery_stream.py "
    "so the evidence is one single-writer utf-8 LF artifact and not a shell "
    "redirection dialect. FOUR FOLLOW-UP SECTIONS in the designed order: the "
    "dry run read matrix FAIL first by design at on-disk 57362B against "
    "regenerated 57334B with NO byte written while fingerprint read CLEAN "
    "domains=5, profile byte-identical and census DRIFT-CLEAN; "
    "docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from THIS "
    "round own green evidence through suite_matrix.py --stamp-from to 57334B "
    "at 595 suites / 4546 criteria with green=595/595 self-describing, --check "
    "byte-identical; and the re-run read all four PASS for VERDICT "
    "reconcile-all-R2532 PASS failing=none (APPENDED 1978B eol_ok=True). DEBT: "
    "reconcile-battery-R2531 closed through the shipped debtor at its predicted "
    "161675B -> 161678B (line 261, open 14->13, done 230->231, readback ok), "
    "and product-face-R2532 was appended first=yes (161678B -> 162181B, "
    "readback ok) naming the next window a PRODUCT face on queue head "
    "state/queue/tech.md:569 prefix AC-PCSC1 probe_seam_subscript_container_scope; "
    "NO successor battery is owed because no product src byte moved this window "
    "and the registry is unmoved at 595 suites / 4546 criteria, re-read by "
    "import. BOARD and PRODUCT faces were not touched this window; queue_floor "
    "still reads FLOOR-MET and the head is still line 569.",

    "2026-11-07 R2532 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this window "
    "and none is claimed; the deliverable is a green 595/4546 battery, a matrix "
    "document whose evidence column names THIS round own green leg, and a "
    "measured recount rather than a quoted number; (b) a LAUNCHER MISTAKE of "
    "mine was measured and is disclosed rather than hidden: the detached "
    "launcher redirected the battery own streaming stdout into "
    "logs/battery-R2532.pid, the same path I then wrote the pid into, so the "
    "pid file became the live stream (547KB -> 933KB) and the pid was "
    "overwritten; the battery itself was unaffected because the evidence is "
    "written once at the end by battery_stream.py, verified by pid AND by a "
    "child reconcile_all process both alive during the run, and the stream was "
    "preserved as logs/battery-R2532.stream.log instead of being thrown away; "
    "(c) the first leg went green so no red leg exists to keep, and no repair "
    "was needed - stated as a fact of this run, not as a claim that the "
    "battery is safe in general; (d) the group orders tail had moved since "
    "R2531 and was judged a fleet dispatch, which is a judgement recorded with "
    "its number rather than a silent skip; (e) Docker is absent on this host, "
    "the real 19.9 debit and the real msgSecCheck still wait on CEO physical "
    "items, the S4U lane reconcile still needs an elevated shell, and "
    "tasks.md was not touched.",

    "R2532 tokens: local=~6k api=0 api_reason=verification window - one debt "
    "gate read, one zero-occupancy tree and HEAD check, one content-addressed "
    "decisions scan reading new=0, one group orders tail read judged not this "
    "company face, one registry target re-measured by import, one full "
    "595-suite battery through the detached single-writer streamer with an "
    "independent criteria recount, one designed matrix FAIL with no byte "
    "written, one stamp-aligned matrix regeneration checked byte-identical, one "
    "four-section follow-up appended to the same evidence file, two debt rows "
    "moved through their shipped writers, and the state/export/backlog/"
    "heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2532
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
          and back["tick"] == 2532
          and back["log"][-1] == LINES[-1])
    print("state %s tick=%s log=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             os.path.getsize(PATH), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())