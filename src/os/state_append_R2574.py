import io
import json
import os

STATE = os.path.join("src", "os", "state.json")

LINES = [
    "2026-11-08 R2574 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2573, pre-registered 616 suites / 4672 criteria at "
    "R2573 because that window moved the registry by one row and shipped a "
    "document). Five-silence at open: git status EMPTY at HEAD 14e5b91a equal "
    "to origin/main with no index.lock, zero @BigDomain rows in "
    "cph4/evolution-ledger.md, the content-addressed decisions scan read "
    "rows=284 tokens=169 new=0 over the stored baseline, the group orders tail "
    "held last_tok=2026-11-08 18:03 (OB-20261108-180341-868, an @BigMoney "
    "re-dispatch, knowledge-only for this company; the scanner max_ts "
    "2026-11-09 belongs to a due date INSIDE that row and is named rather than "
    "smoothed), benchmarks 2026-11-03 inside the seven-day gate. The debt gate "
    "read CLAIM-FIRST item=reconcile-battery-R2573 first=1 open=30 with "
    "stale=no, and queue_head named tech line 609 prefix AC-PNDCI1 "
    "claimable=11 with the floor MET at 5/5 11/10 10/10. The target was "
    "RE-MEASURED by importing reconcile_all.SUITES BEFORE the launch: 616 "
    "suites, 4672 criteria, 616 unique names, 616 unique paths.",
    "2026-11-08 R2574 LEG 1 RED AND KEPT (qa/reconcile-all-R2573.log, "
    "1038744B): written by the shipped single writer through "
    "src/os/battery_stream.py launched detached and unfiltered with its stream "
    "and pid in separate files, utf-8 bom=False crlf=0 lone_cr=0 nul=0, "
    "615/616 suites green at exactly 4672 criteria in 1550.7s, 616 unique "
    "suite names, ONE red suite os-residue-triage 5/6 on AC-RTR6 because the "
    "live residue carried 324 rounds with only 321 declared and the set "
    "difference named THREE product rounds shipped and committed with no "
    "declaration row (R2563, R2565, R2567). BIRTH SITE REPAIRED ALONE before "
    "any retry: each of the three was measured on its own live status through "
    "residue_batch_status_face (DELIVERED, DELIVERED, DELIVERED) rather than "
    "typed, the shipped batch writer was dry-run first at its prediction "
    "324->327 entries / 88023B -> 88677B delta 654, then executed at exactly "
    "that prediction with readback TRIAGED 324/324 untriaged=0 and three "
    "inherited UNMATCHED entries (R2569, R2571, R2573) named rather than "
    "hidden; the red suite then re-read SUITE PASS 6/6 alone. The red leg and "
    "that repair were committed ALONE as e3a17556 so the retry ran on a "
    "committed tree.",
    "2026-11-08 R2574 RETRY GREEN measured not quoted "
    "(qa/reconcile-all-R2573-retry.log): 1038554B at delivery and 1040505B "
    "after the follow-up block appended its own 1951B, utf-8 bom=False crlf=0 "
    "lone_cr=0 nul=0, closing line RUNNER PASS (616/616 suites green, "
    "reconcile controls 7/7, 1658.5s), ZERO FAIL suite rows, 616 unique suite "
    "names with no duplicates, and an INDEPENDENT recount over their own "
    "criteria fields summing to EXACTLY 4672 - the pre-registered total "
    "matched by measurement on both axes, with the registry re-read by import "
    "matching at 616 / 4672. The leg went green so no second red leg exists to "
    "keep, which is a fact of this run and not a claim that the battery is safe "
    "in general.",
    "2026-11-08 R2574 FOLLOW-UP in the designed order: the dry run read "
    "SECTION matrix FAIL first BY DESIGN at on-disk 60718B against regenerated "
    "60737B with NO byte written while fingerprint read PASS CLEAN domains=5, "
    "profile read PASS byte-identical and census read PASS DRIFT-CLEAN for "
    "VERDICT R2574 FAIL failing=matrix; docs/sandbox-suite-matrix.md was then "
    "regenerated stamp-aligned from THIS round own green evidence through "
    "src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R2573-retry.log "
    "--stamp-from docs/sandbox-suite-matrix.md to 60737 bytes at 616 suites / "
    "4672 criteria with its green line honestly self-describing 616/616, "
    "--check read byte-identical at rc=0, and the four sections re-ran to "
    "VERDICT R2574 PASS failing=none (APPENDED 1951B eol_ok=True). The census "
    "was additionally re-read BEFORE the retry as files=2740 tee=2211 "
    "baselined=529 flags=0 DRIFT-CLEAN so no capture dialect could cost the "
    "second leg.",
    "2026-11-08 R2574 DEBT AND BOARD: reconcile-battery-R2573 was closed "
    "through the shipped debtor at its predicted and measured 180591B -> "
    "180594B (line 320, open 30->29, done 273->274, readback ok), and "
    "product-face-R2574 was appended first=yes through the shipped appender at "
    "its predicted 180594B -> 181055B (readback ok) naming the next window a "
    "PRODUCT face on the queue head state/queue/tech.md:609 prefix AC-PNDCI1, "
    "whose AC-PNDCI1..AC-PNDCI6 were pinned in that row at R2573 BEFORE any "
    "code. NO successor battery is owed: this window moved no product src byte "
    "and the registry is unmoved at 616 suites / 4672 criteria, which is "
    "exactly what the green leg measured, and the count was re-read by import "
    "rather than trusted. queue_head re-read line 609 claimable=11 and "
    "queue_floor read FLOOR-MET main=5/5 tech=11/10 explore=10/10; no queue "
    "row was opened or closed, because a verification window writes no board "
    "row.",
    "2026-11-08 R2574 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this window "
    "and none is claimed; the deliverable is a green 616/4672 battery, a matrix "
    "document whose evidence column names THIS round own green leg, and a "
    "declaration repair that closes a repeating birth site; (b) the red was a "
    "real birth site and not load noise: the three rounds were each measured on "
    "their own live status before they were declared, and the declaration is "
    "the third recorded instance of product rounds shipping without a residue "
    "row, so the writer is still not wired into the product closeout - named "
    "plainly rather than dressed up; (c) three INHERITED UNMATCHED entries "
    "(R2569, R2571, R2573 declared DELIVERED, live=-) remain in the "
    "declaration and were NOT repaired by hand here, which is the same "
    "inherited drift earlier windows dropped through the repin tool; (d) state "
    "read 43419B against the 78500B waterline so state_fold --check read "
    "FOLD-CLEAR margin=35081 at 33 log lines and no fold was owed this window; "
    "this append used a PROVED indent=1 no-trailing-newline round-trip checked "
    "byte for byte before mutation; (e) last_decision_rows was left at 284 and "
    "the content-addressed token set was unchanged because the scan read new=0; "
    "(f) Docker is absent on this host so no containerised bring-up of the "
    "sandbox faces is claimed; (g) the real 19.9 debit and the real msgSecCheck "
    "still wait on CEO physical items (merchant id, mini-program "
    "appid/secret); (h) tasks.md was not touched, it is the P-47 canonical "
    "board; (i) the S4U lane re-registration still needs an ELEVATED shell and "
    "D-20261107-14 has classified it as a ceo-pending physical item with zero "
    "chase.",
    "R2574 tokens: local=~9k api=0 api_reason=verification window - five-"
    "silence scan with the decisions and orders faces actually read, one "
    "registry target re-measured by import on both axes, one full 616-suite "
    "leg kept red with its single birth site named, three rounds measured on "
    "their own live status and declared through the shipped batch writer with "
    "a dry-run prediction hit exactly, one red suite re-run alone to 6/6, one "
    "commit carrying the red leg plus the repair and nothing else, one "
    "pre-retry census check, one green retry at the pre-registered 4672 "
    "criteria with an independent recount, one designed matrix FAIL, one "
    "stamp-aligned regeneration checked byte-identical, one four-section "
    "follow-up to a PASS verdict, one debt row closed and one opened through "
    "their shipped writers, and the state/export/heartbeat closeout; zero "
    "cloud calls and zero external API touches",
]


def main():
    raw = io.open(STATE, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    roundtrip = json.dumps(data, indent=1, ensure_ascii=False)
    if roundtrip.encode("utf-8") != raw:
        print("REFUSED E_STATE_ROUNDTRIP: json round-trip is not byte-identical")
        return 3
    before = len(raw)
    data["tick"] = int(data["tick"]) + 1
    for line in LINES:
        data["log"].append(line)
    payload = json.dumps(data, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(STATE, encoding="utf-8").read()
    got = json.loads(back)
    ok = (got["tick"] == 2574 and len(got["log"]) == len(data["log"])
          and got["log"][-1].startswith("R2574 tokens:"))
    print("state tick=%s log=%d before=%dB after=%dB ok=%r"
          % (got["tick"], len(got["log"]), before, len(back.encode("utf-8")),
             ok))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())