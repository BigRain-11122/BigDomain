"""R2388 closeout: state tick, four log lines, the export face, heartbeat.

One writer, one read-back. The export's derived block is left to
check_export_consistency's own recompute (self_drive counters and the queue
counts did not move: one tech row closed, one measured seed added, so tech
stays 11 open / 10 claimable).
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_DECISIONS = os.path.join(os.path.dirname(os.path.dirname(ROOT)), "docs",
                           "decisions.md")

WINDOW = (
    "R2388 product window: state/queue/tech.md:442 prefix AC-RNED1 "
    "(repin_noop_eol_dialect), criteria pinned in that row at R2382 BEFORE "
    "any code, anchors re-checked at HEAD (only the row's own board helper "
    "and state prose mentioned the names). SHIPPED "
    "src/os/repin_noop_eol_dialect.py plus src/os/test_repin_noop_eol_dialect"
    ".py: the NOOP comparison owned BYTES, which is right about content and "
    "wrong about transport - a CRLF declaration carrying the composition read "
    "PLANNED and --execute rewrote it to LF, so an unchanged declaration was "
    "written and no reader could tell that from a real re-pin. ONE "
    "normalisation now lives in that module (CRLF and a lone CR to LF, "
    "content never touched), is_noop answers the one question both writer "
    "faces ask, and repin_noop_parity.is_noop plus "
    "residue_triage_repin_idempotent.decide call it AT CALL time so the "
    "literal byte comparison that used to live in the wire is gone rather "
    "than duplicated; the wire's dead on_disk_bytes helper went with it. "
    "SUITE PASS 6/6 twice with an identical criterion digest plus three "
    "adjacent suites green (qa/repin-noop-eol-dialect-R2388.log, 2402B, "
    "legs=2 identical=True adjacent=3 fails=0), wired "
    "os-repin-noop-eol-dialect(6) so the registry reads 515 suites / 4066 "
    "criteria and docs/sandbox-suite-matrix.md was regenerated to match "
    "(49422B, green=513/515 because the two newest suites are not in the "
    "R2387 battery evidence). LIVE: qa/repin-noop-eol-dialect-live-R2388.log "
    "reads the REAL 67603B declaration as dialect=LF, a CRLF copy of the REAL "
    "declaration as verdict=NOOP raw_equal=no dialect=CRLF with its digest "
    "unchanged and no temp beside it, and the REAL tree dry re-pin at R2388 "
    "as PLANNED with shipped and wire printing the same line - so the "
    "normalisation is content-safe and not a blanket green. Row 442 stamped "
    "and one REAL measured gap seeded (declaration_writer_noop_parity, "
    "AC-DWNP1..AC-DWNP6 pre-registered in that row, five anchors "
    "zero-occupancy): the three sibling declaration writers hold is_noop ZERO "
    "times, so the law reaches one of four writers."
)

DISCLOSURES = (
    "R2388 honest disclosures: (a) AC-RNED5 was RED on its first run and the "
    "red was this window own counter, never the module: it scanned every .py "
    "under src/os for 'def normalise_bytes' and counted the suite file "
    "itself, so the reading was 3 instead of 1; the counter now skips test_ "
    "files and the module was not touched. (b) The refactor removed the "
    "adjacent suite's pinned source literal: AC-RTRI2 asserted 'current == "
    "composed' and 'on_disk_bytes(' inside the wire, both of which this "
    "window legitimately deleted by routing the comparison to the one law. "
    "Its anchor now follows the delegation ('RNP.is_noop(' present, "
    "'on_disk_bytes' absent) while its two behavioural legs (older=NOOP, "
    "newer=PLANNED) were neither touched nor widened - disclosed because a "
    "changed adjacent assertion is never silent here. (c) The CRLF NOOP path "
    "is proved on a fixture world and on a CRLF copy of the REAL declaration; "
    "the real declaration itself is LF, so the live log does not imply a live "
    "CRLF catch. (d) A board edit was mis-anchored on its first attempt and "
    "clobbered the R2387 discharge opening; tech.md was restored from HEAD "
    "with git checkout and both edits were redone against a verified unique "
    "anchor, then read back (DISCHARGED R2387 present once, DISCHARGED R2388 "
    "present once, one new seed row). (e) No battery ran this window: the "
    "register target is 515 suites / 4066 criteria, the carried battery row "
    "stays open, and the suite matrix therefore reports green=513/515 rather "
    "than claiming the new suites are covered. (f) tasks.md was left "
    "untouched: it is the P-47 canonical board and carries no row for this "
    "tech slice. (g) The window ran past its 25-minute budget; the product "
    "face was shipped rather than deferred because the tree was clean at open "
    "and every evidence file was written by one utf-8 LF writer."
)

SELF_HEAL = (
    "R2388 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an "
    "explicit S4U principal but needs an elevated shell, and this session is "
    "unelevated, so the task definition was left untouched (hundred-and-"
    "forty-third consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

TOKENS = (
    "R2388 tokens: local=~30k api=0 api_reason=product window - one module "
    "and its six-criteria suite written to criteria pinned six rounds "
    "earlier, two call sites rerouted through the one law with the dead "
    "helper removed, one adjacent source anchor re-followed, one registry "
    "wiring line, one two-leg evidence capture with three adjacent suites, "
    "one three-leg live capture on the real declaration, one board stamp and "
    "one measured gap row seeded, one suite matrix regeneration, and the "
    "state/export/heartbeat closeout; zero cloud calls and zero external API "
    "touches"
)

DO = (
    "R2388 product window: the re-pin NOOP comparison now owns the line-"
    "ending dialect, so a declaration whose content is already the "
    "composition is no longer rewritten just because it carries CRLF; one "
    "normalisation serves the shipped CLI and the wire, the adjacent source "
    "anchor follows it, and the three sibling declaration writers were "
    "measured to have no NOOP comparison at all and are seeded as the next "
    "slice."
)

LATEST = (
    "src/os/repin_noop_eol_dialect.py plus its six-criteria suite "
    "(qa/repin-noop-eol-dialect-R2388.log, qa/repin-noop-eol-dialect-live-"
    "R2388.log)"
)

NEXT = (
    "run the carried full battery at 515 suites / 4066 criteria on the "
    "committed R2388 tree, then ask the same one law in "
    "residue_triage_append / _head_renew / _entry_retire (AC-DWNP1..6 "
    "already pinned in state/queue/tech.md)"
)


def main():
    with io.open(P_STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    if state.get("tick") != 2387:
        sys.stdout.write("REFUSE: tick is %r, expected 2387\n"
                         % (state.get("tick"),))
        return 1
    log = state.setdefault("log", [])
    for line in (WINDOW, DISCLOSURES, SELF_HEAL, TOKENS):
        log.append(line)
    state["tick"] = 2388

    text = io.open(P_DECISIONS, encoding="utf-8").read()
    tokens = sorted(set(re.findall(r"[DC]-\d{8}-\d+", text)))
    state["last_dec_tokens"] = tokens
    state["last_decision_rows"] = len(
        io.open(P_DECISIONS, encoding="utf-8").read().splitlines())

    payload = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    temp = P_STATE + ".tmp-r2388"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    os.replace(temp, P_STATE)
    with io.open(P_STATE, encoding="utf-8") as handle:
        back = json.load(handle)
    if back.get("tick") != 2388 or len(back.get("log", [])) != len(log):
        sys.stdout.write("REFUSE: state read-back mismatch\n")
        return 1

    with io.open(P_EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    export["export_ts"] = "2026-11-02T21:10:00+08:00"
    export["do"] = DO
    export["ceo_face"]["current"] = DO
    export["ceo_face"]["latest_artifact"] = LATEST
    export["ceo_face"]["next_milestone"] = NEXT
    for row in export.get("results", []):
        if row and row[0] == "2387":
            row[0] = "2388"
            break
    export["results"].insert(0, ["2388", WINDOW])
    outs = export.setdefault("outs", [])
    outs.insert(0, [LATEST,
                    "on",
                    "R2388: the NOOP comparison owns the EOL dialect - a CRLF "
                    "declaration carrying the composition reads NOOP and is "
                    "not rewritten; one normalisation serves the shipped CLI "
                    "and the wire."])
    export_payload = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    temp = P_EXPORT + ".tmp-r2388"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(export_payload)
    os.replace(temp, P_EXPORT)
    with io.open(P_EXPORT, encoding="utf-8") as handle:
        back_export = json.load(handle)
    if back_export.get("export_ts") != export["export_ts"]:
        sys.stdout.write("REFUSE: export read-back mismatch\n")
        return 1

    with io.open(P_HEART, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("R2388 ok %s\n"
                     % ("repin_noop_eol_dialect NOOP owns the EOL dialect"))

    with io.open(P_STATE, "rb") as handle:
        size = len(handle.read())
    sys.stdout.write("CLOSEOUT R2388 tick=2388 log=%d tokens=%d state=%dB\n"
                     % (len(back["log"]), len(tokens), size))
    return 0


if __name__ == "__main__":
    sys.exit(main())