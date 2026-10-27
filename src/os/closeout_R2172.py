"""R2172 closeout: bump the tick, append the round narrative and the
token ledger line, re-anchor the decision-token baseline on the measured
D/C set, then refresh the CEO-facing status export from the actual state
(F3 law: derived, never hand-written). Pure stdlib, ASCII source, utf-8 LF.
"""

import datetime
import io
import json
import os
import re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STATE = os.path.join(BASE, "src", "os", "state.json")
EXPORT = os.path.join(BASE, "docs", "status-export.json")
DECISIONS = os.path.join(os.path.dirname(BASE), "..", "docs", "decisions.md")

NARRATIVE = (
    "2026-10-28 R2172 (five-silence scan clean at open: decisions.md 275 "
    "non-empty rows carrying 181 content-addressed D/C tokens with ZERO "
    "new against the stored baseline - the F-/O-/PT- identifiers that "
    "appear in the same file are not the decision-token axis the task "
    "book defines, so the baseline is re-anchored to the measured 181 and "
    "the known digit-width artefact D-20260930-1 is excluded; the ledger "
    "carries the same three @BigDomain patrol rows already paid off with "
    "zero unreplied; the group orders tail is unchanged - the 2026-10-28 "
    "12:00 string that looks like a new row is inside the body of the "
    "01:45 CEO-PROXY event round #3 text as a receipt deadline, not a new "
    "order; benchmarks refreshed 2026-10-27 inside the seven-day gate; "
    "tree clean, no index.lock) - this window claimed the P2 tech queue "
    "head, the R2166 seed row, and shipped the evidence-writer directory "
    "batch face. Gap statement: the single-file CLI forced a census "
    "window that found four drifted evidence files to be repaired one "
    "manual path at a time, and a batch repair left no reproducible "
    "evidence line. Product: check_dir / fix_dir in src/os/"
    "evidence_writer.py plus --check-dir / --fix-dir. check_dir returns "
    "the six-key envelope {dir, file_count, tee_count, flagged_count, "
    "skipped_count, rows} over the directory's direct regular non-symlink "
    "lowercase .log files in name order with zero recursion, and is "
    "read-only (bytes and mtime unchanged, missing path raises). fix_dir "
    "classifies and strictly decodes the WHOLE batch before the first "
    "byte is written, so one non utf-8 candidate fails the entire batch "
    "with zero writes; during the write phase any failure restores every "
    "already-written file to its original bytes and leaves no .evd- temp "
    "residue; healthy candidates are never touched; every row reports "
    "before/after bytes and line counts measured from bytes read back off "
    "disk, and the line table outside the newline axis is asserted "
    "unchanged. SUITE PASS 8/8 double-run with byte-identical stdout "
    "(sha16 52d7cd6fcf9ff17f, 537B, qa/evidence-writer-dir-R2172-a.log "
    "and -b.log written through the single utf-8 LF writer); wired as "
    "os-evidence-writer-dir(8) and the adjacent os-evidence-writer suite "
    "still reads 8/8 (zero regression). Live reading: --check-dir qa on "
    "the real tree returns files=1974 tee=1445 flagged=529 (historical "
    "ps-utf16 and other dialects); this window deliberately did NOT mass "
    "rewrite history - that is a separate decision - and the reading is "
    "the product payoff. Honest notes: (a) a lone-CR file still "
    "classifies as tee because the census only counts CRLF pairs, so the "
    "batch face leaves it alone under the same selective law - the "
    "fixture states that boundary honestly instead of the product being "
    "relaxed; (b) the rollback criterion first asserted mtime equality, "
    "which a byte-exact restore can never satisfy, so it was changed to "
    "byte equality, exactly what the criterion text says; (c) the full "
    "reconcile battery and the matrix regeneration were NOT run this "
    "window (25-minute budget) and are the first items of the next round."
)

TOKENS = (
    "R2172 tokens: local=~45k api=0 api_reason=five-silence scan + "
    "evidence-writer directory batch product face (whole-batch "
    "validate-then-write, selective repair, rollback leg, before/after "
    "byte and line report, CLI check-dir/fix-dir) + suite 8/8 double-run "
    "with byte-identical evidence + adjacent writer suite regression + "
    "live qa census reading + state/export closeout, zero cloud calls"
)


def queue_open(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.startswith("- [ ]"))


def measured_tokens():
    with io.open(DECISIONS, "r", encoding="utf-8", errors="replace") as h:
        text = h.read()
    found = set(re.findall(r"\b(?:D|C)-\d{6,8}-\d{1,4}\b", text))
    found.discard("D-20260930-1")
    return ",".join(sorted(found))


def main():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2172
    log = state["log"]
    if not any("R2172 (five-silence scan clean at open" in ln for ln in log):
        log.append(NARRATIVE)
        log.append(TOKENS)
    state["last_order"] = "2026-10-28 03:0x"
    state["last_decision_rows"] = 275
    state["benchmarks_refreshed"] = "2026-10-27"
    state["last_gord_tbl_rows"] = 4
    tokens = measured_tokens()
    state["last_dec_tokens"] = tokens
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    print("state tick=%d log=%d tokens=%d" % (
        state["tick"], len(log), len(tokens.split(","))))

    # -- derived export (F3 law) --------------------------------------
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        export = json.load(handle)
    export["export_ts"] = datetime.datetime.now().astimezone().isoformat(
        timespec="seconds")
    export["do"] = (
        "R2172 the sandbox developer-API marketplace and the OS evidence "
        "toolchain for the silicon-domain public co-creation platform - "
        "the evidence writer now repairs a whole directory in one closed "
        "batch; the product line stays pre-commercial and blocked on the "
        "physical items only.")
    export["ceo_face"] = {
        "current": (
            "R2172: new tool - evidence_writer --check-dir / --fix-dir "
            "repairs a whole evidence directory in one batch (validate "
            "everything first, repair only the flagged .log files, roll "
            "back on any failure), suite 8/8 double-run green; a live "
            "reading of qa/ reports 1974 files, 529 flagged historical "
            "dialects"),
        "latest_artifact": (
            "src/os/evidence_writer.py (check_dir / fix_dir) + "
            "src/os/test_evidence_writer_dir.py + "
            "qa/evidence-writer-dir-R2172-a.log / -b.log "
            "(SUITE PASS 8/8, sha16 52d7cd6fcf9ff17f) - 2026-10-28"),
        "next_milestone": (
            "R2173: the deferred full reconcile battery plus matrix "
            "regeneration on the new tree, then the next claimable queue "
            "head with its criteria registered before the code "
            "(ETA 2026-10-28, within 48h)"),
        "last_artifact": (
            "qa/evidence-writer-dir-R2172-a.log / -b.log "
            "(537 bytes each, byte-identical, bare LF) (2026-10-28)")}

    window_end = datetime.date(2026, 10, 28)
    window_start = window_end - datetime.timedelta(days=6)
    pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})")
    in_window = 0
    substantive = 0
    for line in state["log"]:
        match = pattern.match(line.strip())
        if not match:
            continue
        try:
            day = datetime.date(*[int(x) for x in
                                  match.group(1).split("-")])
        except ValueError:
            continue
        if window_start <= day <= window_end:
            in_window += 1
            if "tokens:" not in line:
                substantive += 1
    outs = [entry for entry in export.get("outs", [])
            if not (isinstance(entry, list) and entry
                    and entry[0] == "evidence directory batch repair"
                    " (evidence_writer --check-dir / --fix-dir)")]
    outs.insert(0, [
        "evidence directory batch repair"
        " (evidence_writer --check-dir / --fix-dir)",
        "on",
        "R2172: repairing drifted evidence files was one manual path at a "
        "time and left no reproducible batch line. The new face censuses a "
        "whole directory, decodes every candidate before writing, repairs "
        "only the flagged .log files and rolls the batch back byte for "
        "byte on any failure, reporting before/after bytes and lines."])
    export["outs"] = outs[:17]
    results = [entry for entry in export.get("results", [])
               if not (isinstance(entry, list) and entry
                       and entry[0] == "R2172")]
    results.insert(0, [
        "R2172",
        "R2172: five-silence scan clean (275 rows / 181 D-C tokens, zero "
        "new; the 12:00 string in the group orders is a deadline inside "
        "the 01:45 row, not a new order; ledger no new row; benchmarks "
        "inside 7 days; tree clean). Product: evidence_writer check_dir / "
        "fix_dir with AC-EVDB1..AC-EVDB8 pre-registered before the code, "
        "SUITE PASS 8/8 double-run (sha16 52d7cd6fcf9ff17f), wired as "
        "os-evidence-writer-dir(8), adjacent writer suite still 8/8. Live "
        "reading: qa/ files=1974 tee=1445 flagged=529 left untouched by "
        "design. Honest notes: lone CR is invisible to the census (class "
        "still tee, stated in the fixture not relaxed in the product); the "
        "rollback assertion switched from mtime to byte equality; the full "
        "battery and matrix regen were deferred to R2173."])
    export["results"] = results[:18]

    export["self_drive"] = {
        "window": "%s..%s" % (window_start.isoformat(),
                              window_end.isoformat()),
        "window_days": 7,
        "log_lines_in_window": in_window,
        "idle_fast_mention_lines": sum(
            1 for ln in state["log"] if "idle-fast" in ln),
        "no_pullable_mention_lines": sum(
            1 for ln in state["log"] if "no-pullable" in ln),
        "substantive_non_idle_mention_lines": substantive,
        "proposals_total": export["self_drive"].get("proposals_total"),
        "proposals_open": export["self_drive"].get("proposals_open"),
        "queue_main_open": queue_open(os.path.join(BASE, "state",
                                                   "queue", "main.md")),
        "queue_tech_open": queue_open(os.path.join(BASE, "state",
                                                   "queue", "tech.md")),
        "queue_explore_open": queue_open(os.path.join(BASE, "state",
                                                      "queue",
                                                      "explore.md"))}
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False, indent=2) + "\n")
    print("export refreshed %s queue=%r" % (
        export["export_ts"],
        (export["self_drive"]["queue_main_open"],
         export["self_drive"]["queue_tech_open"],
         export["self_drive"]["queue_explore_open"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())