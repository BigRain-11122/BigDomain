# closeout_R2406.py - the R2406 product closeout: the re-pin dialect window
# shipped, its suite captured twice, the live face re-derived from the real
# tree, the board stamped, the debt successor opened and the ledger line
# landed THROUGH ledger_line_shape_guard's own door.
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import state_io  # noqa: E402
import ledger_line_shape_guard as LLSG  # noqa: E402
import queue_floor_export_face as QFEF  # noqa: E402
import check_export_consistency as CEC  # noqa: E402

STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
HEART = os.path.join(REPO, "heartbeat.txt")
BACKLOG = os.path.join(BASE, "backlog.md")

STAMP = "2026-11-03T06:40:00+08:00"
DO = ("R2406 product: the re-pin now lands in the declaration's own dialect "
      "(CRLF stays CRLF, LF keeps today's bytes, MIXED refuses E_RDPL_MIXED) "
      "and the window repaired the live residue drift it exposed")
ART = ("src/os/repin_dialect_preservation.py + qa/"
       "repin-dialect-preservation-R2406.log + qa/"
       "repin-dialect-preservation-live-R2406.log")
NEXT = ("run the carried battery on this committed tree (target 531 suites / "
        "4162 criteria), then claim state/queue/tech.md AC-LDWS1")

DECISIONS = ["D-20261103-07", "D-20261103-08", "D-20261103-09",
             "D-20261103-10", "D-20261103-11"]

LEDGER = (
    "R2406 tokens: local=~34k api=0 api_reason=product window - one payload "
    "derivation module and its six-criteria suite written to criteria pinned "
    "eight rounds earlier, the re-pin writer rerouted through it in BINARY "
    "mode while keeping its ONE os.replace, one MIXED refusal added with every "
    "pre-existing refusal proved byte-identical against the HEAD module, one "
    "two-leg evidence capture with three adjacent suites plus six adjacent "
    "suites re-run directly, one live capture over the real declaration, one "
    "live drift repaired through the shipped CLI at its predicted "
    "70256->70344 bytes, one board stamp with one measured gap row seeded, "
    "the debt successor opened at 531/4162, and the state/export/backlog/"
    "heartbeat closeout; zero cloud calls and zero external API touches")

LOG = [
    ("2026-11-03 R2406 product window (five-silence scan at open: empty git "
     "status at HEAD a8435b6f, no .git/index.lock; LEDGER atbd_lines=0 "
     "unreplied_groups=0; DEC rows=148 tokens=97 new=5 - D-20261103-07..11 "
     "read in full and NONE dispatches this company: they name a four-company "
     "feedback silence audit, an orders.md merge-conflict repair, the P-09/"
     "P-10 ledger judgement, the LINE-REGISTRY sidecar and a value-line "
     "registration, all @HQ; the group orders tail stays the 2026-11-02 11:04 "
     "model-policy baseline already acknowledged as non-execution; benchmarks "
     "refreshed 2026-11-02 inside the seven-day gate; floor FLOOR-MET main 5/5 "
     "tech 10/10 explore 10/10). The debt gate named reconcile-battery-R2405 "
     "and its own note recorded that the battery ran GREEN on this very tree "
     "at R2405 with no product change after it, so a re-run would measure "
     "nothing new: the product-first law took the window and the successor "
     "row carries the battery. PRODUCT: claimed state/queue/tech.md:478 prefix "
     "AC-RDPL1 (repin_dialect_preservation), whose AC-RDPL1..AC-RDPL6 were "
     "pinned INSIDE that row at R2398 BEFORE any code, after a fresh anchor "
     "check at HEAD (all five anchors hit only prose and state files: "
     "closeout_R2398.py, closeout_R2404.py, closeout_R2405.py, state.json - "
     "zero executable occupancy)."),
    ("2026-11-03 R2406 product face, what shipped: SHIPPED "
     "src/os/repin_dialect_preservation.py plus "
     "src/os/test_repin_dialect_preservation.py. R2398 closed the transport "
     "for the four SPLICE writers and left the re-render out on purpose, so a "
     "re-pin of a CRLF declaration still converted every line of it to LF - "
     "measured in the shipped source, build composes json.dumps(...) + LF and "
     "plan wrote it with newline=LF. ONE seam now answers what bytes a "
     "re-render must land: it asks declaration_writer_dialect_preservation "
     "for the payload at CALL time, so the dialect is still the shared law's "
     "answer and patching it moves this writer (AC-RDPL5); an LF declaration "
     "gets exactly today's bytes (AC-RDPL2); a CRLF declaration is re-rendered "
     "as CRLF (AC-RDPL1); and a MIXED declaration refuses E_RDPL_MIXED before "
     "any byte instead of having one transport chosen for it. The re-pin "
     "writer keeps its ONE os.replace and its own temp, and only the payload "
     "is derived elsewhere, which is exactly what the shipped AC-RNP5 "
     "criterion pins."),
    ("2026-11-03 R2406 evidence and board: SUITE PASS 6/6 twice with an "
     "identical criterion digest plus three adjacent suites green "
     "(qa/repin-dialect-preservation-R2406.log, 1298B, legs=2 identical=True "
     "adjacent=3 fails=0, one utf-8 LF writer through src/os/evidence_capture.py), "
     "and six adjacent suites were re-run directly and all green "
     "(os-residue-triage-repin, os-repin-noop-parity, "
     "os-residue-triage-repin-idempotent, os-repin-noop-eol-dialect, "
     "os-declaration-writer-dialect-preservation, "
     "os-declaration-writer-noop-parity), wired "
     "os-repin-dialect-preservation(6) so the registry reads 531 suites / "
     "4162 criteria. LIVE, not a plan: "
     "qa/repin-dialect-preservation-live-R2406.log (one utf-8 LF writer, "
     "src/os/live_R2406.py) reads the REAL 70344B declaration as dialect=LF "
     "with payload=70344 equal_to_file=True, the real re-pin CLI as NOOP at "
     "70344->70344, a CRLF copy of it resolving to CRLF with 1749 pairs and "
     "ZERO lone LF, and a MIXED copy refused E_RDPL_MIXED - so the repair is "
     "proved prospective on this tree and the CRLF half is proved on a "
     "fixture, not claimed as a live catch. Tech row 478 stamped [done "
     "2026-11-03 R2406] and one REAL measured gap row seeded "
     "(library_declaration_dialect_sweep, AC-LDWS1..AC-LDWS6 pre-registered in "
     "that row): MEASURED this window over every non-test src/os/*.py, five "
     "LIBRARY writers of a JSON declaration (gate_decl_append, "
     "gate_decl_retire, orphan_promotion_ledger, retire_accept, retire_apply) "
     "still compose with json.dumps and land through one os.replace without "
     "ever asking the dialect, beside 116 one-off round scripts that are "
     "historical rather than debt."),
    ("2026-11-03 R2406 live drift measured and repaired at its birth site: "
     "residue_triage read RESIDUE with R2393 untriaged and R2402 no longer "
     "live, because the R2405 closeout fold moved log items out from under the "
     "declaration while its stamp stayed live. The repair ran through the "
     "shipped CLI this window had just changed - a dry run predicted "
     "70256->70344 with dropped=1, the execute landed at exactly that size, "
     "and residue_triage then read TRIAGED 249/249 with untriaged=0 "
     "unmatched=0, which also turned os-residue-triage from 5/6 back to 6/6 "
     "with no criterion touched. That is the new binary write path dogfooded "
     "on the real 70344B declaration, not on a fixture."),
    ("2026-11-03 R2406 honest disclosures: (a) this window own first draft put "
     "the atomic write inside the new module, and TWO shipped suites went RED "
     "for a real reason - AC-RNP5 pins ONE os.replace in the shipped re-pin "
     "module and one_writer counted zero once the write moved, and AC-RTRP4 "
     "likewise counts writes == 1 - so the write went back to the shipped "
     "writer and only the PAYLOAD derivation stayed in the new seam. No "
     "criterion was widened and no test was edited to match. (b) AC-RTRP6 "
     "restricts the module's TOP-LEVEL imports to json/os/sys/residue_triage, "
     "so the new seam is imported INSIDE build() and main(), which is the same "
     "call-time idiom the NOOP law already used there. (c) The first MIXED "
     "fixture crashed at exit 1 instead of refusing: RepinDialectError was not "
     "caught by the CLI, and the fix was the missing except clause in the "
     "module, never the assertion. (d) The live capture is read-only by "
     "construction and writes only its own qa file; the real declaration was "
     "written once, by the shipped CLI, at its predicted bytes. (e) NO battery "
     "ran this window, so 531 suites / 4162 criteria is a WIRING count (530/4156 "
     "measured at R2405 plus this window +1 suite / +6 criteria); the register "
     "row reconcile-battery-R2406 is OPEN with that measured target."),
    ("2026-11-03 R2406 self-heal check: BigDomain-OSLoop is still registered "
     "with LogonType=InteractiveToken, which the 2026-09-29 machine law "
     "forbids for every lane task; src/os/register_loop_task.ps1 already "
     "passes an explicit S4U principal but needs an elevated shell, and this "
     "session is unelevated, so the task definition was left untouched "
     "(hundred-and-sixty-first consecutive disclosure, carried as the stale "
     "row loop-s4u-reconcile in state/debt.md)."),
]


def write_atomic(path, text):
    temp = path + ".tmp-co2406"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temp, path)


def fix_debt():
    text = io.open(DEBT, encoding="utf-8").read()
    open_part = text.split("## Closed")[0]
    present = "reconcile-battery-R2406" in open_part
    sys.stdout.write("DEBT read successor row present=%r bytes=%d\n"
                     % (present, os.path.getsize(DEBT)))
    return 0 if present else 2


DEBT = os.path.join(REPO, "state", "debt.md")

BACKLOG_ROW = (
    "- [x] R2406 product window: repin_dialect_preservation - R2398 closed "
    "the transport for the four SPLICE writers and deliberately left the "
    "RE-RENDER out, so a re-pin of a CRLF declaration still converted every "
    "line of it to LF (measured in the shipped source: build composes "
    "json.dumps + LF and plan wrote it with newline=LF). SHIPPED "
    "src/os/repin_dialect_preservation.py plus its six-criteria suite: ONE "
    "seam answers what bytes a re-render must land, asking "
    "declaration_writer_dialect_preservation for the payload at CALL time, so "
    "an LF declaration keeps exactly today's bytes, a CRLF declaration stays "
    "CRLF with zero lone LF, and a MIXED declaration refuses E_RDPL_MIXED "
    "before any byte. The re-pin writer keeps its ONE os.replace and its own "
    "temp and only the payload is derived elsewhere - two shipped suites "
    "(AC-RNP5, AC-RTRP4) caught the first draft that moved the write, so the "
    "write went back. SUITE PASS 6/6 twice with an identical digest plus "
    "three adjacent suites green (qa/repin-dialect-preservation-R2406.log, "
    "1298B, legs=2 identical=True adjacent=3 fails=0) and six adjacent suites "
    "green when re-run directly, wired os-repin-dialect-preservation(6) so "
    "the registry reads 531/4162. LIVE: "
    "qa/repin-dialect-preservation-live-R2406.log reads the REAL 70344B "
    "declaration as LF/payload-equal, the real CLI as NOOP, a CRLF copy as "
    "CRLF with zero lone LF, and a MIXED copy refused. The window also "
    "repaired a live residue drift the same writer exposed (R2393 untriaged, "
    "R2402 no longer live) through the shipped CLI at its predicted "
    "70256->70344 bytes, after which residue_triage reads TRIAGED 249/249. "
    "Board: row 478 stamped and one measured gap row seeded "
    "(library_declaration_dialect_sweep, five library JSON writers still "
    "unrouted), floor FLOOR-MET 5/5 10/10 10/10. No battery ran: "
    "reconcile-battery-R2406 stays OPEN at 531/4162.\n")


def main():
    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if not backlog.startswith("- [x] R2405"):
        sys.stdout.write("NOTE backlog head is not the R2405 row, not "
                         "prepending\n")
    else:
        write_atomic(BACKLOG, BACKLOG_ROW + backlog)
        sys.stdout.write("BACKLOG row prepended\n")

    before = io.open(STATE, encoding="utf-8", newline="").read()
    state = json.loads(before)
    already = LOG[0] in state.get("log", [])
    if already:
        sys.stdout.write("NOTE state already carries this window's items, not "
                         "appending again\n")
    else:
        state["tick"] = int(state.get("tick", 0)) + 1
        for item in LOG:
            if item in state["log"]:
                sys.stdout.write("E_STATE duplicate item\n")
                return 2
            state["log"].append(item)
    tokens = list(state.get("last_dec_tokens") or [])
    for token in DECISIONS:
        if token not in tokens:
            tokens.append(token)
    state["last_dec_tokens"] = tokens
    state["last_decision_rows"] = 148
    text = state_io.canon(json.dumps(state, ensure_ascii=False, indent=2)
                          + "\n")
    raw = text.encode("utf-8")
    write_atomic(STATE, text)
    if open(STATE, "rb").read() != raw:
        sys.stdout.write("E_STATE read-back differs\n")
        return 2
    readback = json.load(io.open(STATE, encoding="utf-8"))
    sys.stdout.write("STATE tick=%d log_items=%d tokens=%d bytes=%d -> %d\n"
                     % (readback["tick"], len(readback["log"]), len(tokens),
                        len(before.encode("utf-8")), len(raw)))

    if fix_debt() != 0:
        return 2

    verdict = LLSG.append_ledger_line(STATE, LEDGER, execute=True)
    sys.stdout.write("LEDGER door verdict=%s predicted=%s wrote=%s\n"
                     % (verdict["verdict"], verdict.get("predicted_bytes"),
                        verdict.get("wrote")))
    if verdict["verdict"] != "ACCEPTED" or verdict.get("wrote") != "yes":
        return 2
    final = json.load(io.open(STATE, encoding="utf-8"))
    sys.stdout.write("STATE after ledger tick=%d log_items=%d bytes=%d\n"
                     % (final["tick"], len(final["log"]),
                        os.path.getsize(STATE)))

    data = json.load(io.open(EXPORT, encoding="utf-8"))
    QFEF.apply(data, REPO)
    derived = CEC.recompute()[0]
    for key, value in derived.items():
        if key in data.get("self_drive", {}):
            data["self_drive"][key] = value
        else:
            sys.stdout.write("NOTE derived key not in export: %s\n" % key)
    data["export_ts"] = STAMP
    data["do"] = DO
    outs = data.get("outs") or []
    if not outs or outs[0] != ART:
        data["outs"] = [ART] + outs
    rows = data.get("results") or []
    if not rows or rows[0][0] != "2406":
        data["results"] = [["2406", DO]] + rows
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ART
    face["last_artifact"] = ART
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = "2026-11-04T23:00:00+08:00"
    face["updated_at"] = STAMP
    write_atomic(EXPORT, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.write("EXPORT refreshed bytes=%d\n" % os.path.getsize(EXPORT))

    heart = io.open(HEART, encoding="utf-8", newline="").read()
    if not heart.endswith("\n"):
        heart += "\n"
    heart += ("%s tick=%d R2406 product window - the re-pin lands in the "
              "declaration's own dialect; live residue drift repaired through "
              "the same CLI\n" % (STAMP, final["tick"]))
    write_atomic(HEART, heart)
    sys.stdout.write("HEARTBEAT appended\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())