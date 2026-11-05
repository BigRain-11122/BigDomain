"""closeout_R2465 - append this window's evidence to src/os/state.json."""

import json
import os
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-05 R2465 VERIFICATION window on the battery the R2464 src edits "
    "owed (reconcile-battery-R2465, pre-registered at 560 suites / 4336 "
    "criteria). Five-silence scan at open: git status empty at HEAD 6d6fa062 "
    "with no .git/index.lock, zero @BigDomain rows in the evolution ledger, the "
    "group orders tail unchanged at 2026-11-05 00:36, benchmarks refreshed "
    "2026-11-03 inside the seven-day gate, queue head AC-PFKC1 with the floor "
    "MET. The mixed-tree rule therefore owed the battery first and "
    "product-face-R2456 is CARRIED, never dropped.",

    "2026-11-05 R2465 BATTERY LEG 1 RED, and the cause is named rather than "
    "swept: RUNNER FAIL (2 failed assertions) in 1062.1s with the single "
    "failing suite os-residue-triage 5/6, whose AC-RTR6 read residue=282 "
    "triaged=281 untriaged=1. The untriaged row was resolved by reading the "
    "live reader, not by guessing: stamp_residue reports 282 live rounds while "
    "state/residue_triage.json carried 281 declarations, and the set "
    "difference named exactly one round, R2452 (DELIVERED, hits=1, closed=1 "
    "over state/queue/tech.md:518). This was a missing declaration, not an "
    "open work item.",

    "2026-11-05 R2465 FIX AT THE BIRTH SITE: the declaration was appended "
    "through the shipped writer residue_triage_append.py (dry run first, then "
    "--append round=R2452 status=DELIVERED by=R2465 until=R2470, 281->282 "
    "entries, 78508B -> 78896B, readback TRIAGED), and the suite re-ran green "
    "SUITE PASS 6/6 with AC-RTR6 reading live residue fully triaged. No "
    "criterion was loosened to obtain that green. The repair and the red "
    "evidence were committed together as 9f0e5a57 so the re-run below started "
    "on a clean tree.",

    "2026-11-05 R2465 BATTERY LEG 2 RED on the cleaned tree in 1071.8s: the "
    "residue failure was gone, and a DIFFERENT single suite failed - "
    "os-lobby-checkout-demo ran 0.7s, printed zero criterion lines and died on "
    "the first request with ConnectionAbortedError [WinError 10053]. Run "
    "standalone it reads SUITE PASS 6/6 with the byte-identical digest "
    "46654133EC75D89438D1B6C4547C79CE, twice in a row, so this is a "
    "load-sensitive transport race in the suite own HTTP helper rather than a "
    "product defect.",

    "2026-11-05 R2465 the second defect was repaired at its birth site too: "
    "the suite http() helper now retries TRANSPORT failures only "
    "(TRANSPORT_RETRIES=3, 0.1s linear backoff) and prints every retry it "
    "used, while an HTTP status is never retried and no status, byte or count "
    "assertion was touched; AC-CKD6 scans the MODULE for 'import time', not "
    "this suite, so the stdlib clock ban on the product module still holds. "
    "Two consecutive standalone runs read SUITE PASS 6/6 with the unchanged "
    "digest.",

    "2026-11-05 R2465 debt register, stated honestly rather than closed: "
    "reconcile-battery-R2465 stays OPEN because no green full battery exists "
    "for this window - two legs ran and both were red for two different, "
    "named, repaired causes. The next window owes the battery FIRST on the "
    "committed tree at the unchanged pre-registered 560 suites / 4336 "
    "criteria, and this row is the leader it must close. No successor row was "
    "appended: the debt is this one battery, not a second one.",

    "2026-11-05 R2465 honest disclosures: (a) ZERO product points and no "
    "product byte changed - nothing a CEO can open was rebuilt, every P-47 "
    "item remains blocked on CEO physical pieces, and the only src edit this "
    "window is a test-harness robustness fix; (b) the battery was run TWICE, "
    "about 36 minutes of wall clock, and the window therefore ran far past its "
    "25-minute budget - named rather than hidden; (c) the two legs were "
    "launched detached and unfiltered through src/os/battery_stream.py, so the "
    "R2211/R2268/R2289/R2348/R2453/R2458/R2461 filtering-pipe trap was not "
    "re-paid; (d) no matrix regeneration ran this window because neither leg "
    "was green - docs/sandbox-suite-matrix.md is untouched and still carries "
    "its R2464 reading, which is disclosed instead of being refreshed from a "
    "red leg; (e) Docker is absent on this host and the real 19.9 debit plus "
    "the real msgSecCheck still wait on CEO physical items; (f) tasks.md was "
    "not touched, it is the P-47 canonical board.",

    "R2465 tokens: local=~9k api=0 api_reason=verification window - two full "
    "reconcile batteries launched detached through the single-writer stream "
    "(both red, two different named causes), one residue declaration appended "
    "through its shipped writer and re-proved green, one test-harness "
    "transport retry landed at the birth site and proved twice, one repair "
    "commit, and the state/export/backlog/heartbeat closeout; zero cloud calls "
    "and zero external API touches",
]


def main():
    with open(STATE, "rb") as handle:
        raw = handle.read()
    crlf = b"\r\n" in raw
    obj = json.loads(raw.decode("utf-8"))
    before = len(obj.get("log") or [])
    obj["tick"] = int(obj.get("tick", 0)) + 1
    obj.setdefault("log", []).extend(LINES)
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    if crlf:
        text = text.replace("\n", "\r\n")
    data = text.encode("utf-8")
    fd, path = tempfile.mkstemp(dir=BASE, prefix=".state-", suffix=".tmp")
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    os.replace(path, STATE)
    with open(STATE, "rb") as handle:
        back = handle.read()
    check = json.loads(back.decode("utf-8"))
    print("STATE CLOSEOUT tick=%d log=%d->%d crlf=%s bytes=%d readback=%s"
          % (check["tick"], before, len(check["log"]), crlf, len(back),
             "ok" if check["log"][-1] == LINES[-1] else "MISMATCH"))


if __name__ == "__main__":
    main()