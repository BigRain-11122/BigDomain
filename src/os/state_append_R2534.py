"""R2534 state append: the verification window on the battery R2533 owed."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-07 R2534 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2533, pre-registered 596 suites / 4552 criteria, and "
    "the target was RE-MEASURED by importing reconcile_all.SUITES before "
    "anything ran - byte for byte the registered number). Opened on a clean "
    "tree at HEAD abac19ca with no index.lock and the debt gate reading "
    "CLAIM-FIRST reconcile-battery-R2533 first=1. RESULT GREEN ON THE FIRST "
    "LEG, measured not quoted: qa/reconcile-all-R2533.log is 931140B as "
    "delivered (1978B follow-up block appended, 933118B on disk), utf-8 "
    "bom=False crlf=0 nul=0, closing RUNNER PASS (596/596 suites green, "
    "reconcile controls 7/7, 1196.3s), ZERO FAIL suite rows, and an independent "
    "recount over the 596 PASS rows summing to EXACTLY 4552 criteria; launched "
    "detached and unfiltered through src/os/battery_stream.py with its stream "
    "and its pid in SEPARATE files this time, because the R2532 window put the "
    "stream into the pid path and that mistake is fixed at the launcher rather "
    "than only disclosed. FOUR FOLLOW-UP SECTIONS in the designed order: the "
    "dry run read matrix FAIL first by design at on-disk 57459B against "
    "regenerated 57453B with NO byte written while fingerprint read CLEAN "
    "domains=5, profile byte-identical and census DRIFT-CLEAN; "
    "docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from THIS "
    "round own green evidence through suite_matrix.py --stamp-from to 57453B "
    "at 596 suites / 4552 criteria with green=596/596 self-describing and "
    "--check byte-identical; the re-run read all four PASS for VERDICT "
    "reconcile-all-R2533 PASS failing=none (APPENDED 1978B eol_ok=True). DEBT: "
    "reconcile-battery-R2533 closed through the shipped debtor at its predicted "
    "163107B -> 163110B (line 264, open 15->14, done 232->233, readback ok), "
    "and product-face-R2534 was appended first=yes (163110B -> 163535B, "
    "readback ok) naming the next window a PRODUCT face on queue head "
    "state/queue/tech.md:571 prefix AC-PCNS1 probe_seam_nested_subscript_scope; "
    "NO successor battery is owed because no product src byte moved this window "
    "and the registry is unmoved at 596 suites / 4552 criteria, re-read by "
    "import. Board, product faces and tasks.md were not touched this window; "
    "queue_floor still reads FLOOR-MET and the head is still line 571.",

    "2026-11-07 R2534 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this window "
    "and none is claimed; the deliverable is a green 596/4552 battery, a matrix "
    "document whose evidence column names THIS round own green leg with "
    "green=596/596 self-describing, and a recounted criteria total rather than "
    "a quoted one; (b) the leg went green so no red leg exists to keep and no "
    "repair was needed, which is a fact of this run and not a claim that the "
    "battery is safe in general; (c) the R2532 launcher mistake was FIXED at "
    "the birth site this window by writing the stream and the pid to different "
    "paths before the launch, so logs/battery-R2533.pid holds only the pid and "
    "logs/battery-R2533.stream.log holds the live stream; (d) the progress "
    "polls repeated the same shape three times before the polling was switched "
    "to a single blocking wait on the evidence file, which is disclosed because "
    "a repeated identical action is a cost even when it returns new numbers; "
    "(e) Docker is absent on this host, the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items, and the S4U lane reconcile "
    "still needs an elevated shell; (f) tasks.md was not touched.",

    "R2534 tokens: local=~5k api=0 api_reason=verification window - one debt "
    "gate read, one tree and HEAD check, one registry target re-measured by "
    "import, one full 596-suite battery through the detached single-writer "
    "streamer with its stream and pid separated at the launcher, one "
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
    state["tick"] = 2534
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
          and back["tick"] == 2534
          and back["log"][-1] == LINES[-1])
    print("state %s tick=%s log=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             os.path.getsize(PATH), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())