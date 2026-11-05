"""closeout_R2463 - append this window's evidence to src/os/state.json.

Same atomic-replace + read-back shape as the R2462 template.
"""

import json
import os
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-05 R2463 VERIFICATION window on the debt the R2462 business "
    "window left behind, not on a new face: the R2168 mixed-tree rule owed the "
    "battery because R2462 changed product src bytes and moved the registry "
    "558->559 suites / 4324->4330 criteria. Five-silence scan at open: git "
    "status empty at HEAD 1883f995 with no .git/index.lock, the evolution "
    "ledger carries zero @BigDomain rows, the content-addressed decisions diff "
    "read 129 tokens with new=0 against the stored 130-token baseline (the one "
    "gone token is the known prose artifact D-20261105-0), the group orders "
    "tail max_ts is 2026-11-05 00:36 equal to the stored last_order, "
    "benchmarks were refreshed 2026-11-03 inside the seven-day gate, and the "
    "queue head read state/queue/tech.md:522 prefix AC-PFKC1. The debt gate "
    "named CLAIM-FIRST item=product-face-R2456, but the register ALSO carried "
    "the open reconcile-battery-R2463 row, and the mixed-tree rule says the "
    "battery runs first, so product-face-R2456 is CARRIED, not dropped.",

    "2026-11-05 R2463 BATTERY GREEN on the committed tree 1883f995 with an "
    "empty git status before the run: RUNNER PASS 559/559 suites green plus "
    "reconcile controls 7/7 in 990.3s (991.1s wall) with the last summary line "
    "reading 'PASS suites 559/559 green, expected criteria total=4330', i.e. "
    "exactly the total pre-registered in the debt register at R2462; birth-site "
    "TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed 326.59 "
    "MiB. Evidence qa/reconcile-all-R2463.log (858063B at the green leg, "
    "860481B with both follow-up legs) written by ONE utf-8 LF single writer "
    "through src/os/battery_stream.py, never a shell redirection: crlf=0 "
    "lone_cr=0 bom=False, re-measured byte-wise after the run. The battery was "
    "launched detached and unfiltered, so the R2211/R2268/R2289/R2348/R2453/"
    "R2458/R2461 filtering-pipe trap was not re-paid, and no red leg exists "
    "because none was produced.",

    "2026-11-05 R2463 the four follow-up sections produced the designed order: "
    "LEG 1 read SECTION matrix FAIL matrix mismatch on-disk=53959B "
    "regenerated=53952B with no byte written, fingerprint PASS CLEAN domains=5, "
    "profile PASS byte-identical, census PASS DRIFT-CLEAN; then "
    "src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from "
    "THIS round own eligible green evidence through --stamp-from and printed "
    "'PASS generated ... 53952 bytes ... registry suites=559 criteria=4330 "
    "evidence=qa/reconcile-all-R2463.log green=559/559', with --check reading "
    "byte-identical at 53952B / 559 suites / 4330 criteria. LEG 2 then read all "
    "four sections PASS - matrix byte-identical 53952B, fingerprint CLEAN "
    "domains=5, profile byte-identical, census DRIFT-CLEAN - for VERDICT "
    "reconcile-all-R2463 PASS failing=none. Both legs stay in the evidence tail "
    "(1917B FAIL then 1978B PASS) and the matrix is self-describing this round: "
    "its own green line reads 559/559 because it names this round own battery "
    "rather than a borrowed older leg.",

    "2026-11-05 R2463 debt register closed through its own writer: "
    "reconcile-battery-R2463 closed at 120598B -> 120602B (line=196, open 3->2, "
    "done 174->175, readback=ok) after a dry run that predicted exactly those "
    "deltas. NO successor battery was registered because this window changed no "
    "product src byte and the registry is unmoved at 559 suites / 4330 "
    "criteria. The gate now reads verdict=CLAIM-FIRST item=product-face-R2456 "
    "opened=R2455 carried=8 stale=yes open=2 first=1, naming the tech head "
    "state/queue/tech.md:522 prefix AC-PFKC1 row_key_carrier_scope, whose "
    "AC-PFKC1..AC-PFKC6 were pinned in that row at R2446 BEFORE any code.",

    "2026-11-05 R2463 honest disclosures: (a) this is a ZERO product-point "
    "verification window - nothing a CEO could open was rebuilt, no P-47 "
    "business surface was touched, and every P-47 item beyond the shipped "
    "sandbox faces remains blocked on CEO physical items; what the window "
    "bought is a proven registry (559 suites, 4330 criteria) on the exact tree "
    "R2462 committed, so the entry page shipped there is now PROVED rather than "
    "merely shipped; (b) the debt gate leader is still the internal audit row "
    "product-face-R2456, now eight windows carried and stale, while the CEO "
    "standing order OB-20261105-003656-879 asks for real output, so the next "
    "window should ship a BUSINESS face and say plainly that it supersedes the "
    "audit row rather than serving the gate blindly; (c) the battery_stream "
    "call still lets the inner reconcile_all print 'no evidence path: "
    "shell-capture mode' as its first line, which is the runner own banner and "
    "NOT the dialect of the file - the file dialect was measured byte-wise "
    "above, and this note exists so the next reader does not mistake the banner "
    "for the R2458 shell-capture defect; (d) Docker is absent on this host, so "
    "the compose bring-up of the sandbox faces stays unproved and is not "
    "claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on "
    "CEO physical items (merchant id, mini-program appid/secret); (f) READ-ONLY "
    "observation outside this repo: FluxGroup/docs/orders.md still carries its "
    "leftover empty conflict markers, already reported in HQ-FEEDBACK.md; (g) "
    "the window ran past its 25-minute budget on a 991.1s battery plus two "
    "follow-up legs, named rather than hidden; (h) tasks.md was not touched, it "
    "is the P-47 canonical board; (i) no fold was due: state.json measured "
    "72320B before the closeout against the 78500B waterline.",

    "R2463 tokens: local=~8k api=0 api_reason=verification window - one full "
    "reconcile battery on the committed tree (559/559 suites, controls 7/7, "
    "4330 criteria exactly as pre-registered, 990.3s), one detached launch "
    "through the single-writer stream, one designed matrix FAIL followed by a "
    "stamp-aligned regeneration from this round own green evidence and a "
    "byte-identical --check, four follow-up sections PASS for VERDICT R2463 "
    "PASS, one battery row closed through its shipped CLI, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
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
             "ok" if len(check["log"]) == before + len(LINES) else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())