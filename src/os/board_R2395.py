"""Close the claimed tech row and re-target the carried battery (R2395).

Text edits only, each proven by an exact occurrence count and a predicted
byte delta, so a wrong anchor refuses instead of corrupting a board. ASCII
source, stdlib only, no clock, no network.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))

TECH = os.path.join(REPO, "state", "queue", "tech.md")
DEBT = os.path.join(REPO, "state", "debt.md")

ROW_HEAD = ("- [ ] P2 tech seed (R2393, from this window own measured seam): "
            "`src/os/runner_suite_timeout_headroom.py`")

DISCHARGED = (
    "  DISCHARGED R2395 (line 462, AC-RTH1..AC-RTH6): "
    "src/os/runner_suite_timeout_headroom.py plus its suite shipped against "
    "the criteria pinned at R2393. The reading derives every registered "
    "suite's own slowest measured leg from the runner's own PASS/FAIL suite "
    "lines - the `PASS suites 520/520 green` summary line is deliberately "
    "not a suite line, so the field order is pinned rather than a loose word "
    "match - and the registered labels come from an AST read of the runner's "
    "SUITES table, never an import of a 5000-line battery driver. Headroom is "
    "cap minus that measured leg, a suite at or above the band (default 60% "
    "of the cap) is named with verdict BAND-HIT, a registered suite with no "
    "measured leg reads NO-MEASURE rather than comfortable, and the CLI keeps "
    "0/2/3/5 with a byte-stable --json over pinned keys. SUITE PASS 6/6, two "
    "legs identical digest CB10BFECDEC50D24, three adjacent suites green "
    "(owner_table_parity, export_publish_wire_identity, "
    "declaration_writer_noop_parity), wired "
    "os-runner-suite-timeout-headroom(6). LIVE on the real pile: 521 "
    "registered suites, 520 measured, 3 inside the band - "
    "ledger-apimarket-refundregister 268.1s (headroom 31.9s), "
    "ledger-apimarket-reportclaims 246.8s (53.2s), "
    "ledger-apimarket-buyerhistory 232.2s (67.8s) - and "
    "os-runner-suite-timeout-headroom itself reading NO-MEASURE because no "
    "battery has run since it was wired "
    "(qa/runner-suite-timeout-headroom-live-R2395.log). DISCLOSED: the "
    "SUITES table is not literal - every path is an os.path.join call - so "
    "the first reader answered E_RTH_NO_REGISTRY on the real tree and the "
    "label extraction was rebuilt on the AST instead of evaluating the "
    "table.")

SEED = (
    "- [ ] P2 tech seed (R2395, from this window own measured gap): "
    "`src/os/runner_abort_face.py` - the headroom reading only knows suites "
    "that some leg FINISHED, so the very suite that killed a battery is the "
    "one line the pile does not carry: R2393 leg 3 died on "
    "ledger/test_apimarket_report_claims.py after exactly 300s and no suite "
    "line was ever written for it, which is why the same suite reads 246.8s "
    "today and looks merely slow. Product: a reading that names the aborted "
    "suite from the runner's own captured body (the last echoed child line "
    "before the abort plus the missing suite line the registry expects), so a "
    "dead battery yields a named suite instead of silence. Criteria "
    "AC-RAF1..AC-RAF6 pre-registered HERE BEFORE any code: AC-RAF1 the "
    "aborted suite is derived from the registry minus the suite lines the "
    "body carries, never from a hard-coded label; AC-RAF2 a body that ends "
    "with a complete verdict writes no abort reading; AC-RAF3 the verdict "
    "reads ABORTED with the suite named while a complete body reads "
    "COMPLETE at exit 0; AC-RAF4 an unparseable body reads UNREADABLE rather "
    "than claiming an abort; AC-RAF5 CLI exits 0/2/3/5 with a byte-stable "
    "--json over pinned keys; AC-RAF6 pure ASCII, stdlib only, no clock, no "
    "network, read-only, plus its own reconcile label. Anchors "
    "zero-occupancy at HEAD 2026-11-03: runner_abort_face, AC-RAF, E_RAF, "
    "os-runner-abort-face, test_runner_abort_face.")

BATTERY_TAIL = ("runs FIRST next window on the committed tree with zero "
                "product edits; carried target 520/4096 until a product "
                "window adds a suite")

BATTERY_NOTE = (
    " | note_appended_R2395: not run this window - the product face took the "
    "window and this row stays OPEN with its target re-measured against the "
    "tree it must walk: 521 suites / 4102 criteria (520/4096 plus this "
    "window's os-runner-suite-timeout-headroom suite, +1 suite / +6 "
    "criteria). The live reading this window wrote is the reason the row "
    "matters: three ledger-apimarket suites now sit at 232.2s..268.1s "
    "against the 300s cap, so a loaded machine will abort this battery "
    "again with no code defect.")


def edit(path, pairs):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    before = len(text.encode("utf-8"))
    for needle, replacement in pairs:
        count = text.count(needle)
        if count != 1:
            raise SystemExit("REFUSED: %r appears %d times in %s"
                             % (needle[:60], count, os.path.basename(path)))
        text = text.replace(needle, replacement, 1)
    after = len(text.encode("utf-8"))
    print("%s %d -> %d bytes (delta %+d)"
          % (os.path.basename(path), before, after, after - before),
          flush=True)
    temp = path + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temp, path)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return len(handle.read().encode("utf-8")) == after


def main(argv):
    dry = "--execute" not in argv
    if dry:
        print("DRY: tech row stamp + discharged line + one seed; "
              "battery row note appended")
        return 0
    with io.open(TECH, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if text.count(ROW_HEAD) != 1:
        raise SystemExit("REFUSED: the claimed row head is not unique")
    text = text.replace(ROW_HEAD,
                        "- [x] [done 2026-11-03 R2395] "
                        + ROW_HEAD[len("- [ ] "):], 1)
    lines = text.split("\n")
    index = [i for i, line in enumerate(lines)
             if line.startswith("- [x] [done 2026-11-03 R2395]")
             and "runner_suite_timeout_headroom" in line]
    if len(index) != 1:
        raise SystemExit("REFUSED: the stamped row is not unique")
    lines.insert(index[0] + 1, DISCHARGED)
    while lines and not lines[-1].strip():
        lines.pop()
    lines.append("")
    lines.append(SEED)
    lines.append("")
    body = "\n".join(lines)
    with io.open(TECH, "w", encoding="utf-8", newline="") as handle:
        handle.write(body)
    print("tech.md written %d bytes" % len(body.encode("utf-8")), flush=True)
    ok_debt = edit(DEBT, [(BATTERY_TAIL, BATTERY_TAIL + BATTERY_NOTE)])
    print("debt.md verified=%s" % ok_debt, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))