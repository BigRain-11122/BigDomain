"""Split every post-pin FOLD-CARRY gap into REPAIRABLE and FROZEN (R3494).

Why this exists: the FOLD-CARRY law reddens one shape - a round whose
narrative sits in an archived window while no ledger presence line for that
round is found in the archives. R3493 measured six such entries on the
shipped tree and could not say whether they were an archival accounting
artefact, a reading artefact, or real holes.

R3494 measured them read-only and found a THIRD class: three rounds
(R3436, R3458, R3459) whose narratives are complete but whose budget lines
exist nowhere - not in the archives, not in the live ring - and never
entered the repository's committed history at all. The law's own comment
names the defect it pins as 'a narrative archived while its ledger line
stayed behind in the LIVE log', which is repairable by re-folding. A line
that exists nowhere is not repairable: the archives are frozen history no
later round may rewrite.

So the census publishes the two classes apart, without changing the law's
verdict:
  left_behind - ledger presence line still in the live ring: the law's
                true target, gated by this tool (exit 2).
  nowhere     - no ledger line in archives or live ring: a frozen hole,
                published by name so a reader can see exactly what the
                law reddens and why it cannot be repaired in place.
  exempted    - a round the named table excuses with both halves re-proved
                from the tree (ledger_lines.FOLD_CARRY_EXEMPT).

Stdlib only, ASCII source, zero network, no child process.
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
sys.path.insert(0, os.path.join(REPO, "src", "os"))

import ledger_lines as LL  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
PAGE = os.path.join(REPO, "preview", "fold-carry-census.json")
EVIDENCE_PAGE = os.path.join(REPO, "preview", "fold-carry-evidence.json")
LABEL = "fold-carry-census"

# R3495: a fold summary that enumerates a block part by part is a receipt
# written verbatim into the archive at fold time. If the enumeration has no
# budget part while every other part of the round is named, the block had no
# budget line when it was folded - evidence a reader can re-check from disk,
# without git and without trusting this tool's own gap reading. The negative
# shape is the same sentence WITH a budget part (measured: the R3437 receipt
# lists tokens), which must never be admitted.
# R3496: the reader itself moved to the law module so the exemption and this
# census share one definition; this name is kept for its callers.
LOSS_RE = re.compile(r"refuses\s+by\s+name\s+\(E_ROUND_LOST\)")


def receipt_index(paths):
    """Every block-part receipt in the archives, keyed by round."""
    return LL.block_receipts(paths)


def budget_line_bounds(paths, live_lines):
    """Earliest surviving budget-line round, and the E_ROUND_LOST round."""
    earliest = None
    for line in live_lines:
        hit = LL.LEDGER_PRESENCE_RE.match(line)
        if hit is not None:
            round_no = int(hit.group(1))
            earliest = round_no if earliest is None else min(earliest, round_no)
    lost_at = None
    for path in paths:
        handle = io.open(path, "r", encoding="utf-8")
        try:
            for raw in handle:
                text = raw.rstrip("\n").rstrip("\r")
                hit = LL.LEDGER_PRESENCE_RE.match(text)
                if hit is not None:
                    round_no = int(hit.group(1))
                    earliest = (round_no if earliest is None
                                else min(earliest, round_no))
                if not LOSS_RE.search(text):
                    continue
                hit = LL.NARRATIVE_RE.match(text)
                if hit is None:
                    continue
                round_no = int(hit.group(1))
                lost_at = round_no if lost_at is None else min(lost_at, round_no)
        finally:
            handle.close()
    return earliest, lost_at


def _archive_walk(paths):
    """Every archive window, materialised once per file (AC-FCW1, R3634).

    The census and the evidence face used to walk the archives separately, so
    one `--evidence` run read the same 27944 archive lines twice (measured:
    six walks over three files). Nothing about the data differs between the
    two, so the walk is built here - the one call site - and handed in.
    """
    return [(path, list(LL.load_archive_windows(path))) for path in paths]


def evidence(min_round=None, _walk=None):
    """Answer both decision questions from disk alone (R3495).

    A: does a named exemption need git? No - a fold summary written at fold
       time enumerates the block and its missing budget part is readable.
    B: can narrowing the range heal the red? Only if a candidate boundary
       sits after the holes; the scope starts at the boundary, so a hole
       BELOW the boundary is released. Both measured boundaries are older
       than every hole, so nothing is released.
    """
    paths = LL.archive_files(LL.default_logs_dir(STATE))
    walk = _archive_walk(paths) if _walk is None else _walk
    report = census(min_round, _walk=walk)
    live = LL.load_state_log(STATE)
    receipts = receipt_index(paths)
    earliest, lost_at = budget_line_bounds(paths, live)
    # R3633: the law's own kind is asked of the law's own vocabulary. Without
    # it this page spoke two receipt kinds while the table carried four, so
    # R3458 (inline payload) and R3610 (tree absence) were published as "no
    # receipt" beside a law that excuses both by name.
    live_rounds = LL.tree_presence_rounds(live)
    archive_rounds = set()
    narratives = {}
    for path, file_windows in walk:
        for window in file_windows:
            for line in window["lines"]:
                presence = LL.LEDGER_PRESENCE_RE.match(line)
                if presence is not None:
                    archive_rounds.add(int(presence.group(1)))
                if window["round"] < report["since"]:
                    continue
                if LL.classify(line) == "round":
                    narratives.setdefault(
                        int(LL.NARRATIVE_RE.match(line).group(1)),
                        []).append(line)
    rows = []
    for round_no in report["nowhere_rounds"]:
        found = [item for item in receipts.get(round_no, [])
                 if item["omits_budget"]]
        # Strongest receipt first: the enumeration that names the most parts.
        found.sort(key=lambda item: -len(item["parts"]))
        # Same arguments the census hands the law, so the two faces cannot
        # disagree about whether a hole is excused.
        law_ok, law_why = LL.fold_carry_exemption(
            round_no, narratives.get(round_no, []),
            archive_rounds | live_rounds, receipts, live_rounds=live_rounds)
        rows.append({
            "round": round_no,
            "class": "block-receipt" if found else "no-receipt",
            "receipt": found[0] if found else None,
            "receipts_total": len(receipts.get(round_no, [])),
            "law_ok": law_ok,
            "law_kind": LL.exemption_kind(round_no),
            "law_why": law_why,
        })
    holes = list(report["nowhere_rounds"])
    boundaries = {}
    for name, value in (("earliest_budget", earliest), ("e_round_lost", lost_at)):
        if value is None:
            boundaries[name] = {"round": None, "releases": None}
            continue
        boundaries[name] = {
            "round": value,
            "releases": len([item for item in holes if item < value]),
        }
    refused = sorted(set(
        round_no for round_no, items in receipts.items()
        for item in items if not item["omits_budget"]))
    return {
        "tool": LABEL + "-evidence",
        "since": report["since"],
        "frozen_rounds": holes,
        "rows": rows,
        "block_receipt": len([row for row in rows
                              if row["class"] == "block-receipt"]),
        "no_receipt": len([row for row in rows
                           if row["class"] == "no-receipt"]),
        "boundaries": boundaries,
        "narrowing_releases": sum(
            item["releases"] or 0 for item in boundaries.values()),
        "receipts_refused": refused,
        "left_behind": len(report["left_behind"]),
        # R3633: the law's reading beside the receipt reading, so a hole the
        # law excuses by name never reads the same as one nothing explains.
        "law_excused": len([row for row in rows if row["law_ok"]]),
        "unexplained": len([row for row in rows if not row["law_ok"]]),
        "clean": report["clean"] and len(rows) == len(holes),
    }


def evidence_line(report):
    """One ASCII line: what the receipts say and what narrowing would do."""
    return ("FOLD-CARRY-EVIDENCE since=%d frozen=%d block_receipt=%d "
            "no_receipt=%d earliest_budget=%s e_round_lost=%s "
            "narrowing_releases=%d refused=%d left_behind=%d "
            "law_excused=%d unexplained=%d"
            % (report["since"], len(report["frozen_rounds"]),
               report["block_receipt"], report["no_receipt"],
               report["boundaries"]["earliest_budget"]["round"],
               report["boundaries"]["e_round_lost"]["round"],
               report["narrowing_releases"], len(report["receipts_refused"]),
               report["left_behind"], report["law_excused"],
               report["unexplained"]))


def presence_rounds(lines):
    """Rounds that carry a ledger PRESENCE line in the given lines."""
    out = set()
    for line in lines:
        hit = LL.LEDGER_PRESENCE_RE.match(line)
        if hit is not None:
            out.add(int(hit.group(1)))
    return out


def classify_round(round_no, archive_rounds, live_rounds, narratives):
    """One round's FOLD-CARRY class: None when clean (R3495, R3496).

    R3496: the class is a MEASUREMENT, never a gate decision. Whether the law
    excuses a frozen hole by name is asked separately, so this page can keep
    publishing the holes while the law reads OK - otherwise the excuse table
    would empty the very reading that justified it.
    """
    if round_no in archive_rounds:
        return None
    if LL.exemption_kind(round_no) == LL.FOLD_CARRY_NOT_A_HOLE_KIND:
        # The round's own words prove it was never a work round, so it is not
        # a hole at all - the pre-R3496 class, unchanged, now asked of the
        # law's named constant instead of this tool's own copy of the string.
        verdict, _why = LL.fold_carry_exemption(round_no, narratives,
                                                archive_rounds)
        if verdict:
            return "exempted"
    if round_no in live_rounds:
        return "left_behind"
    return "nowhere"


def census(min_round=None, _walk=None):
    """Measure the shipped tree and answer the two-class split."""
    since = LL.FOLD_CARRY_PIN if min_round is None else min_round
    paths = LL.archive_files(LL.default_logs_dir(STATE))
    walk = _archive_walk(paths) if _walk is None else _walk
    live = LL.load_state_log(STATE)
    live_rounds = presence_rounds(live)
    archive_rounds = set()
    examined = []
    windows = 0
    rounds = 0
    rows = []
    round_narrative = {}
    # Two passes, borrowed from audit_fold_carry: the archive ledger set must
    # be complete before ANY window is judged, or a round whose ledger line
    # sits in a later file reads as a hole. Measured while writing this: a
    # one-pass draft reported 22 holes over 19 rounds where the audit reports
    # 6 over 3 - the whole difference was file order.
    for path, file_windows in walk:
        for window in file_windows:
            for line in window["lines"]:
                hit = LL.LEDGER_PRESENCE_RE.match(line)
                if hit is not None:
                    archive_rounds.add(int(hit.group(1)))
            if window["round"] >= since:
                examined.append(window)
    for window in examined:
        windows += 1
        narratives = {}
        for line in window["lines"]:
            if LL.classify(line) == "round":
                round_no = int(LL.NARRATIVE_RE.match(line).group(1))
                narratives.setdefault(round_no, []).append(line)
                round_narrative.setdefault(round_no, []).append(line)
        for round_no in sorted(narratives):
            rounds += 1
            kind = classify_round(round_no, archive_rounds, live_rounds,
                                  narratives[round_no])
            if kind is None:
                continue
            rows.append({
                "class": kind,
                "round": round_no,
                "window": window["round"],
                "narrative_lines": len(narratives[round_no]),
                "why": ("ledger line still in the live ring" if kind
                        == "left_behind" else
                        "no ledger line in the archives or the live ring"),
                "file": os.path.basename(window["path"]),
                "file_ordinal": window["ordinal"],
                "line": window["line"],
            })
    left = [row for row in rows if row["class"] == "left_behind"]
    nowhere = [row for row in rows if row["class"] == "nowhere"]
    # R3496: the law's excuse is a SECOND reading over the same holes, asked
    # with the receipts this page just read, so the page can say both "three
    # frozen holes" and "the law excuses all three by name" without either
    # number swallowing the other.
    receipts = LL.block_receipts(paths)
    exempted = []
    for row in nowhere:
        verdict, why = LL.fold_carry_exemption(
            row["round"], round_narrative.get(row["round"], []),
            archive_rounds | live_rounds, receipts,
            live_rounds=live_rounds)
        if verdict:
            exempted.append({"round": row["round"],
                             "window": row["window"],
                             "why": why})
    return {
        "tool": LABEL,
        "since": since,
        "windows": windows,
        "rounds": rounds,
        "archive_ledger_rounds": len(archive_rounds),
        "live_ledger_rounds": len(live_rounds),
        "left_behind": left,
        "nowhere": nowhere,
        "exempted": exempted,
        "nowhere_rounds": sorted(set(row["round"] for row in nowhere)),
        "clean": not left,
    }


def verdict_line(report):
    """One ASCII line: the classes apart, the repairable count as the gate."""
    return ("FOLD-CARRY-CENSUS since=%d windows=%d rounds=%d "
            "left_behind=%d nowhere=%d(rounds=%d entries=%d) "
            "law_excused=%d(%s)"
            % (report["since"], report["windows"], report["rounds"],
               len(report["left_behind"]), len(report["nowhere_rounds"]),
               len(report["nowhere_rounds"]), len(report["nowhere"]),
               len(set(item["round"] for item in report["exempted"])),
               ",".join("R%d" % item for item in sorted(set(
                   item["round"] for item in report["exempted"]))) or "-"))


def render():
    text = json.dumps(census(), indent=2, sort_keys=True) + "\n"
    return text.encode("utf-8")


def landed(path):
    # Line endings are not part of the claim: the repository normalises text
    # on checkout (measured: this page lands with CRLF on a re-checkout), and
    # a pair gate that reddens on the checkout filter would be measuring the
    # filter rather than the derivation.
    try:
        raw = io.open(path, "rb").read().decode("utf-8", "replace")
    except (IOError, OSError):
        return None
    return raw.replace("\r\n", "\n")


def main(argv):
    write = "--write" in argv
    check = "--check" in argv
    want_evidence = "--evidence" in argv
    allowed = {"--write", "--check", "--evidence"}
    unknown = [item for item in argv if item.startswith("--")
               and item not in allowed]
    if unknown:
        sys.stderr.write("E_FCC_ARGS unknown %s\n" % unknown[0])
        return 3
    page = EVIDENCE_PAGE if want_evidence else PAGE
    if want_evidence:
        report = evidence()
        print(evidence_line(report))
        for row in report["rows"]:
            receipt = row["receipt"]
            if row["law_ok"]:
                law = "law=%s" % (row["law_kind"] or "(kind-unnamed)")
            else:
                law = "law=refused:%s" % row["law_why"]
            if receipt is None:
                print("  NO-RECEIPT R%d (enumerations seen: %d) %s"
                      % (row["round"], row["receipts_total"], law))
                continue
            print("  BLOCK-RECEIPT R%d at %s:%d parts=%d omits_budget=%s %s"
                  % (row["round"], receipt["file"], receipt["line"],
                     len(receipt["parts"]), receipt["omits_budget"], law))
        for name in sorted(report["boundaries"]):
            item = report["boundaries"][name]
            print("  BOUNDARY %s round=%s releases=%s"
                  % (name, item["round"], item["releases"]))
        if report["receipts_refused"]:
            print("  REFUSED-WITH-BUDGET %s"
                  % ",".join("R%d" % item
                             for item in report["receipts_refused"]))
    else:
        report = census()
        print(verdict_line(report))
        for row in report["left_behind"]:
            print("  LEFT-BEHIND R%d in window R%d at %s:%d:%d"
                  % (row["round"], row["window"], row["file"],
                     row["file_ordinal"], row["line"]))
        for row in report["nowhere"]:
            print("  NOWHERE R%d in window R%d at %s:%d:%d (%d narrative lines)"
                  % (row["round"], row["window"], row["file"],
                     row["file_ordinal"], row["line"], row["narrative_lines"]))
    fresh = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if write:
        with io.open(page, "wb") as handle:
            handle.write(fresh.encode("utf-8"))
        print("WROTE %s %dB" % (os.path.relpath(page, REPO),
                                len(fresh.encode("utf-8"))))
    if check:
        tag = "FCE-CHECK" if want_evidence else "FCC-CHECK"
        was = landed(page)
        if was is None:
            print("%s VERDICT MISSING" % tag)
            return 2
        if was != fresh:
            print("%s VERDICT STALE" % tag)
            return 2
        print("%s VERDICT PASS read_only=True" % tag)
    return 2 if report["left_behind"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
