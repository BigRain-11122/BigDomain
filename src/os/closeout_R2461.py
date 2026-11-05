"""closeout_R2461 - append this window's evidence to src/os/state.json.

Same shape as the R2460 template: seed the dialect from the bytes read (this
file is CRLF-canon), bump tick, append the log (append-only), land one atomic
replace and read the result back. This round also records the one decision
token the content-addressed scan judged and rejected, so the same prose
artifact does not re-read as a fresh dispatch next window.
"""

import json
import os
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

JUDGED_TOKENS = ["D-20261105-0"]

LINES = [
    "2026-11-05 R2461 VERIFICATION window, opened on the debt the two product "
    "windows left behind rather than on a new business face. Five-silence scan "
    "at open: git status empty at HEAD 2a9fed3f with no .git/index.lock (that "
    "HEAD is the R2460 closeout note, one commit past the pushed 06ca68ee), the "
    "evolution ledger carries zero @BigDomain rows, the content-addressed "
    "decisions diff read 198 rows with new=1 and that single token was the "
    "prose artifact D-20261105-0 out of the sentence 'D-20261105-0x 7 tiao' on "
    "decisions.md line 259, i.e. zero real dispatches, the group orders tail "
    "max_ts is 2026-11-05 00:36 equal to the stored last_order, and benchmarks "
    "were refreshed 2026-11-03 inside the seven-day gate. The queue head read "
    "state/queue/tech.md:522 prefix AC-PFKC1 with claimable=11 and the floor "
    "MET. The debt gate named CLAIM-FIRST item=product-face-R2456, but the "
    "register ALSO carried two open battery rows owed by the R2459 and R2460 "
    "src edits, and the R2168 mixed-tree rule says the battery runs first, so "
    "this window is a verification window and product-face-R2456 is CARRIED, "
    "not dropped.",

    "2026-11-05 R2461 BATTERY GREEN on the committed tree 2a9fed3f with an "
    "empty git status before the run: RUNNER PASS 558/558 suites green plus "
    "reconcile controls 7/7 in 1002.1s with criteria total 4324 EXACTLY as "
    "pre-registered in the debt register at R2460 (556->558 suites and "
    "4312->4324 criteria being this station own R2459 checkout-demo and R2460 "
    "lobby-page suites), birth-site TMP RECLAIM candidates=932 removed=932 "
    "busy=0 failed=0 reclaimed 326.59 MiB. Evidence qa/reconcile-all-R2461.log "
    "(857490B at the green leg, 861329B with both follow-up legs) written by "
    "ONE utf-8 LF single writer through src/os/battery_stream.py, never a shell "
    "redirection: crlf=0 lone_cr_absent bom=False. The battery was launched "
    "detached and unfiltered, so the R2211/R2268/R2289/R2348/R2453/R2458 "
    "filtering-pipe trap was not re-paid, and no red leg exists because none "
    "was produced.",

    "2026-11-05 R2461 the four follow-up sections produced the designed order: "
    "LEG 1 read SECTION matrix FAIL matrix mismatch on-disk=53731B "
    "regenerated=53887B with no byte written, and fingerprint PASS CLEAN "
    "domains=5, profile PASS byte-identical, census PASS DRIFT-CLEAN; then "
    "src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from "
    "THIS round own eligible green evidence through --stamp-from and printed "
    "'PASS generated ... 53887 bytes ... registry suites=558 criteria=4324 "
    "evidence=qa/reconcile-all-R2461.log green=558/558', with --check reading "
    "byte-identical at 53887B / 558 suites / 4324 criteria. LEG 2 then read all "
    "four sections PASS - matrix byte-identical 53887B, fingerprint CLEAN "
    "domains=5, profile byte-identical, census DRIFT-CLEAN - for VERDICT R2461 "
    "PASS failing=none. Both legs stay in the evidence tail (1889B FAIL then "
    "1950B PASS) and the matrix is self-describing this round: its own green "
    "line reads 558/558 because it names this round own battery rather than a "
    "borrowed older leg, which also un-stales the document R2460 had to "
    "disclose as stale.",

    "2026-11-05 R2461 debt register closed through its own writers: "
    "reconcile-battery-R2460 closed at 120102B -> 120106B (line=194, open 4->3, "
    "done 172->173, readback=ok) and reconcile-battery-R2461 closed at 120106B "
    "-> 120110B (line=195, open 3->2, done 173->174, readback=ok), both after a "
    "dry run that predicted exactly those deltas. NO successor battery was "
    "registered because this window changed no product src byte and the suite "
    "registry is unmoved at 558 suites / 4324 criteria. The gate now reads "
    "verdict=CLAIM-FIRST item=product-face-R2456 opened=R2455 carried=6 "
    "stale=yes open=2 first=1, naming the tech head "
    "state/queue/tech.md:522 prefix AC-PFKC1 row_key_carrier_scope, whose "
    "AC-PFKC1..AC-PFKC6 were pinned in that row at R2446 BEFORE any code.",

    "2026-11-05 R2461 honest disclosures: (a) this is a ZERO product-point "
    "verification window - nothing a CEO could open was rebuilt, no P-47 "
    "business surface was touched, and every P-47 item beyond the shipped "
    "sandbox faces remains blocked on CEO physical pieces; what the window "
    "bought is a proven registry (558 suites, 4324 criteria) on the exact tree "
    "the two business windows committed, and the sandbox faces R2456/R2457/"
    "R2459/R2460 shipped are now PROVED rather than merely shipped; (b) the "
    "scan one new token was a prose artifact and the baseline is widened here "
    "by that judged token (D-20261105-0) so the same false positive cannot "
    "re-appear as a phantom dispatch; (c) one poll command was auto-cancelled "
    "by the shell five-minute no-output gate while the battery kept running as "
    "a separate detached process - the cancellation touched no evidence byte "
    "and the run was verified alive by process id afterwards, so no second "
    "launch happened; (d) Docker is absent on this host, so the compose "
    "bring-up of the sandbox faces stays unproved and is not claimed; (e) the "
    "real 19.9 debit and the real msgSecCheck still wait on CEO physical items "
    "(merchant id, mini-program appid/secret); (f) READ-ONLY observation "
    "outside this repo: the group file FluxGroup/docs/orders.md still carries "
    "its leftover empty conflict markers in the group worktree, which this "
    "station may not write and which is already reported in HQ-FEEDBACK.md; "
    "(g) the window ran past its 25-minute budget on a 1002.1s battery plus "
    "two poll rounds and the two follow-up legs, named rather than hidden; "
    "(h) tasks.md was not touched, it is the P-47 canonical board.",

    "2026-11-05 R2461 self-heal check: BigDomain-OSLoop still exists and its "
    "Principal.LogonType reads Interactive, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 needs an "
    "elevated shell while this session is unelevated, so the definition was "
    "left untouched again (carried as the stale row loop-s4u-reconcile).",

    "R2461 tokens: local=~9k api=0 api_reason=verification window - one full "
    "reconcile battery on the committed tree (558/558 suites, controls 7/7, "
    "4324 criteria exactly as pre-registered, 1002.1s), one designed matrix "
    "FAIL followed by a stamp-aligned regeneration from this round own green "
    "evidence and a byte-identical --check, four follow-up sections PASS for "
    "VERDICT R2461 PASS, two battery rows closed through their shipped CLI, "
    "and the state/export/backlog/heartbeat closeout; zero cloud calls and "
    "zero external API touches",
]


def main():
    with open(STATE, "rb") as handle:
        raw = handle.read()
    crlf = b"\r\n" in raw
    obj = json.loads(raw.decode("utf-8"))
    before = len(obj.get("log") or [])
    obj["tick"] = int(obj.get("tick", 0)) + 1
    obj.setdefault("log", []).extend(LINES)
    tokens = obj.get("last_dec_tokens")
    if isinstance(tokens, list):
        added = 0
        for token in JUDGED_TOKENS:
            if token not in tokens:
                tokens.append(token)
                added += 1
    else:
        added = 0
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
    print("STATE CLOSEOUT tick=%d log=%d->%d tokens_added=%d crlf=%s lone_lf=%d "
          "bytes=%d readback=%s"
          % (check["tick"], before, len(check["log"]), added, crlf,
             back.count(b"\n") - back.count(b"\r\n"), len(back),
             "ok" if len(check["log"]) == before + len(LINES) else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())