"""Closeout for the R2458 verification window.

Writes the state log, the backlog row and the heartbeat row for the window
that discharged the battery the R2457 product edit owed. Every number below
was measured this window.

Run with --execute to write; the default is a dry run that prints the payload
and touches nothing. The export is refreshed by its own shipped writer AFTER
every state append (the R2449 ordering law), never from inside this script.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402
import declaration_writer_dialect_preservation as DDP  # noqa: E402

STATE = os.path.join(BASE, "state.json")
BACKLOG = os.path.join(BASE, "backlog.md")
HEARTBEAT = os.path.join(os.path.dirname(os.path.dirname(BASE)),
                         "heartbeat.txt")

ROUND = 2458
DEC_ROWS = 199
ORDER_TS = "2026-11-05 00:36"

LINES = [
    "2026-11-05 R2458 verification window, and the battery was ADOPTED rather "
    "than launched: the five-silence scan found git status carrying exactly one "
    "untracked path - qa/reconcile-all-R2458.log, 856250B, mtime 06:57 - and "
    "nothing else dirty at HEAD 5f970de8 with no .git/index.lock, zero "
    "@BigDomain rows in the evolution ledger, the content-addressed decisions "
    "diff new=0 against the stored 199-row baseline, the group orders tail "
    "max_ts 2026-11-05 00:36 equal to the stored last_order and benchmarks "
    "refreshed 2026-11-03 inside the seven-day gate. The debt gate named "
    "CLAIM-FIRST item=product-face-R2456 and the carried battery row "
    "reconcile-battery-R2458 was open, so the R2168 mixed-tree rule owed the "
    "battery first; a prior attempt had already run it on this committed tree, "
    "so per the R2437 precedent the evidence was RE-MEASURED here instead of "
    "being re-run: 556 suite rows, criteria summed to 4312 EXACTLY as "
    "pre-registered at R2457, fails=0, one RUNNER PASS line at 1337.6s.",

    "2026-11-05 R2458 battery provenance, disclosed rather than dressed up: the "
    "log first line reads 'no evidence path: shell-capture mode, evidence "
    "dialect follows the caller', so that attempt was a shell capture and NOT "
    "the src/os/battery_stream.py single writer the house law asks for. The "
    "bytes were kept rather than rewritten (they are the battery own output) "
    "and the dialect was measured: 856250B, crlf=0, lone_lf=6240, bom=False, so "
    "the body is a clean utf-8 LF capture; reconcile-daily-census reads "
    "DRIFT-CLEAN flags=0 over it in the follow-up leg below. The lesson is "
    "restated as a habit: launch through battery_stream with --evidence so the "
    "evidence file is single-writer from birth.",

    "2026-11-05 R2458 the four follow-up sections produced the designed order "
    "on the adopted evidence: LEG 1 read SECTION matrix FAIL matrix mismatch "
    "on-disk=53657B regenerated=53731B (no rewrite) with fingerprint PASS "
    "verdict CLEAN domains=5, profile PASS byte-identical and census PASS "
    "verdict DRIFT-CLEAN; then src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md from THIS round own evidence through "
    "--stamp-from in one shipped call and printed 'PASS generated ... 53731 "
    "bytes ... registry suites=556 criteria=4312 evidence=qa/reconcile-all-"
    "R2458.log green=556/556', and --check read byte-identical at 53731B / 556 "
    "suites / 4312 criteria; LEG 2 then read matrix PASS byte-identical 53731B, "
    "fingerprint PASS CLEAN domains=5, profile PASS and census PASS "
    "DRIFT-CLEAN, VERDICT R2458 PASS failing=none. Both legs were appended by "
    "the shipped writer, so the evidence moved 856250B -> 860089B with the "
    "closing line 'VERDICT R2458: PASS eol crlf=0 bare_cr=0 bom=False', and the "
    "matrix is self-describing this round: its own green line reads 556/556.",

    "2026-11-05 R2458 debt register closed through its own writers: "
    "reconcile-battery-R2458 closed at 119464B -> 119468B (line=193, open "
    "3->2, done 171->172, readback=ok). NO successor battery was registered "
    "because this window changed no product src byte and the registry is "
    "unmoved at 556 suites and 4312 criteria, so no table moved and no battery "
    "is owed. The gate now reads open=2 done=172 first=product-face-R2456 "
    "stale=2 carried=227 verdict=DEBT-STALE: product-face-R2456 (tech head "
    "state/queue/tech.md:522 prefix AC-PFKC1) is now three windows stale and is "
    "carried rather than dropped, and loop-s4u-reconcile stays open for the "
    "known unelevated-session reason.",

    "2026-11-05 R2458 honest disclosures: (a) ZERO product points - nothing a "
    "CEO could open was rebuilt this window, no P-47 business surface was "
    "touched, and every P-47 item remains blocked on CEO physical pieces; what "
    "the window bought is a proven registry (556 suites, 4312 criteria) on the "
    "exact tree R2457 committed; (b) the battery was not launched by this "
    "session and its provenance is a shell capture, both stated above rather "
    "than implicit; (c) the unsupported-flag trap was paid once more and is "
    "recorded rather than swept: probing reconcile_all.py with --list started a "
    "real battery, the truncating pipe cut it, and a 5-byte file literally "
    "named --list was left in the repo root - deleted before any commit, zero "
    "surviving processes checked by command line; (d) the debt gate leader is "
    "still an internal audit face while the standing CEO order asks for real "
    "output, so the next window should either ship product-face-R2456 or "
    "supersede it with a business face and say which; (e) READ-ONLY observation "
    "outside this repo: FluxGroup/docs/orders.md still carries its leftover "
    "empty conflict markers, already reported in HQ-FEEDBACK.md; (f) tasks.md "
    "was not touched, it is the P-47 canonical board; (g) the window stayed "
    "inside its 25-minute budget only because the 1337.6s battery was not "
    "re-paid - the re-measurement and the two follow-up legs took about "
    "fifteen minutes.",

    "R2458 tokens: local=~7k api=0 api_reason=verification window - one "
    "adopted battery re-measured (556 suites, 4312 criteria exactly as "
    "pre-registered, zero fails) rather than re-run, one designed matrix FAIL "
    "followed by a stamp-aligned regeneration and a byte-identical --check, two "
    "follow-up legs appended by the shipped writer for VERDICT R2458 PASS, one "
    "battery row closed through its shipped CLI, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]

BACKLOG_ITEM = (
    "- [x] [done 2026-11-05 R2458] R2458 verification window on the carried "
    "row reconcile-battery-R2458 (owed by R2457, pre-registered 556 suites / "
    "4312 criteria): zero product src bytes changed, the R2168 mixed-tree rule "
    "honoured. The battery had ALREADY been run on this committed tree "
    "(5f970de8) by a prior attempt and left as one untracked evidence file, so "
    "it was ADOPTED and re-measured rather than re-run: 556 suite rows, "
    "criteria summed to 4312 EXACTLY as pre-registered, fails=0, RUNNER PASS at "
    "1337.6s (qa/reconcile-all-R2458.log, 856250B -> 860089B with both "
    "follow-up legs). PROVENANCE DISCLOSED: the body is a shell capture (its "
    "first line reads 'no evidence path: shell-capture mode'), not the "
    "battery_stream single writer, and it measures crlf=0 lone_lf=6240 "
    "bom=False. Four follow-up sections in the designed order: matrix FAIL at "
    "on-disk=53657B against regenerated=53731B with no byte written, "
    "suite_matrix regenerated docs/sandbox-suite-matrix.md through --stamp-from "
    "to 53731B at 556 suites / 4312 criteria green=556/556, --check "
    "byte-identical, then LEG 2 read all four sections PASS (fingerprint CLEAN "
    "domains=5, profile byte-identical, census DRIFT-CLEAN) for VERDICT R2458 "
    "PASS failing=none. Debt: reconcile-battery-R2458 closed at 119464B -> "
    "119468B (line=193, open 3->2, done 171->172, readback ok); no successor "
    "battery owed because no product src byte and no registry count moved; the "
    "gate now reads open=2 first=product-face-R2456 (stale, carried=3). Zero "
    "product points claimed; no P-47 business surface rebuilt and every P-47 "
    "item remains blocked on CEO physical pieces.\n"
)


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write_atomic(path, text):
    """Land the composed text in the dialect the document already carries.

    R2458 birth-site repair: the first draft hardcoded newline="\\n" and so
    converted a CRLF working document; the transport is now asked of the
    shipped dialect law against the current bytes and written as bytes.
    """
    if os.path.exists(path):
        name, payload = DDP.encode(open(path, "rb").read(), text)
    else:
        name, payload = "NEW", text.encode("utf-8")
    tmp = path + ".tmp-r2458"
    with open(tmp, "wb") as fh:
        fh.write(payload)
    os.replace(tmp, path)
    with open(path, "rb") as fh:
        back = fh.read()
    if back != payload:
        raise SystemExit("E_CLOSE_R2458_READBACK " + path)
    return name


def main(argv):
    execute = "--execute" in argv
    raw = load(STATE)
    data = json.loads(raw)
    plan = {"tick": ROUND, "log_lines": len(LINES),
            "last_decision_rows": DEC_ROWS,
            "last_order": ORDER_TS, "backlog": "prepend done row",
            "heartbeat": "append tick=%d" % ROUND}
    if not execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        print("DRY RUN - nothing written")
        return 0

    data["tick"] = ROUND
    log = data.setdefault("log", [])
    for line in LINES:
        if line not in log:
            log.append(line)
    data["last_decision_rows"] = DEC_ROWS
    data["last_order"] = ORDER_TS
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    canon = state_io.canon(body)
    write_atomic(STATE, canon)

    bl = load(BACKLOG)
    if "R2458 verification window on the carried row" not in bl:
        write_atomic(BACKLOG, BACKLOG_ITEM + bl)

    hb = load(HEARTBEAT)
    if not hb.endswith("\n"):
        hb += "\n"
    hb += ("tick=%d %s\n" % (ROUND, "2026-11-05T R2458 verification: adopted "
                                     "the R2457-owed battery evidence, 556/556 "
                                     "suites at 4312 criteria, matrix "
                                     "regenerated, VERDICT PASS"))
    write_atomic(HEARTBEAT, hb)

    print("CLOSEOUT R2458 tick=%d log_added=%d bytes=%d layout=%s"
          % (ROUND, len(LINES), os.path.getsize(STATE),
             state_io.layout(open(STATE, "rb").read().decode("utf-8"))
             .get("layout_ok")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))