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
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
sys.path.insert(0, os.path.join(REPO, "src", "os"))

import ledger_lines as LL  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
PAGE = os.path.join(REPO, "preview", "fold-carry-census.json")
LABEL = "fold-carry-census"


def presence_rounds(lines):
    """Rounds that carry a ledger PRESENCE line in the given lines."""
    out = set()
    for line in lines:
        hit = LL.LEDGER_PRESENCE_RE.match(line)
        if hit is not None:
            out.add(int(hit.group(1)))
    return out


def census(min_round=None):
    """Measure the shipped tree and answer the two-class split."""
    since = LL.FOLD_CARRY_PIN if min_round is None else min_round
    paths = LL.archive_files(LL.default_logs_dir(STATE))
    live = LL.load_state_log(STATE)
    live_rounds = presence_rounds(live)
    archive_rounds = set()
    examined = []
    windows = 0
    rounds = 0
    rows = []
    # Two passes, borrowed from audit_fold_carry: the archive ledger set must
    # be complete before ANY window is judged, or a round whose ledger line
    # sits in a later file reads as a hole. Measured while writing this: a
    # one-pass draft reported 22 holes over 19 rounds where the audit reports
    # 6 over 3 - the whole difference was file order.
    for path in paths:
        for window in LL.load_archive_windows(path):
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
        for round_no in sorted(narratives):
            rounds += 1
            if round_no in archive_rounds:
                continue
            verdict, why = LL.fold_carry_exemption(
                round_no, narratives[round_no], archive_rounds)
            if verdict:
                kind = "exempted"
            elif round_no in live_rounds:
                kind = "left_behind"
            else:
                kind = "nowhere"
            rows.append({
                "class": kind,
                "round": round_no,
                "window": window["round"],
                "narrative_lines": len(narratives[round_no]),
                "why": why,
                "file": os.path.basename(window["path"]),
                "file_ordinal": window["ordinal"],
                "line": window["line"],
            })
    left = [row for row in rows if row["class"] == "left_behind"]
    nowhere = [row for row in rows if row["class"] == "nowhere"]
    exempted = [row for row in rows if row["class"] == "exempted"]
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
            "left_behind=%d nowhere=%d(rounds=%d entries=%d) exempt=%d"
            % (report["since"], report["windows"], report["rounds"],
               len(report["left_behind"]), len(report["nowhere_rounds"]),
               len(report["nowhere_rounds"]), len(report["nowhere"]),
               len(report["exempted"])))


def render():
    text = json.dumps(census(), indent=2, sort_keys=True) + "\n"
    return text.encode("utf-8")


def landed(path):
    try:
        return io.open(path, "rb").read()
    except (IOError, OSError):
        return None


def main(argv):
    write = "--write" in argv
    check = "--check" in argv
    allowed = {"--write", "--check"}
    unknown = [item for item in argv if item.startswith("--")
               and item not in allowed]
    if unknown:
        sys.stderr.write("E_FCC_ARGS unknown %s\n" % unknown[0])
        return 3
    report = census()
    fresh = json.dumps(report, indent=2, sort_keys=True) + "\n"
    print(verdict_line(report))
    for row in report["left_behind"]:
        print("  LEFT-BEHIND R%d in window R%d at %s:%d:%d"
              % (row["round"], row["window"], row["file"],
                 row["file_ordinal"], row["line"]))
    for row in report["nowhere"]:
        print("  NOWHERE R%d in window R%d at %s:%d:%d (%d narrative lines)"
              % (row["round"], row["window"], row["file"],
                 row["file_ordinal"], row["line"], row["narrative_lines"]))
    if write:
        with io.open(PAGE, "wb") as handle:
            handle.write(fresh.encode("utf-8"))
        print("WROTE %s %dB" % (os.path.relpath(PAGE, REPO),
                                len(fresh.encode("utf-8"))))
    if check:
        was = landed(PAGE)
        if was is None:
            print("FCC-CHECK VERDICT MISSING")
            return 2
        if was.decode("utf-8", "replace") != fresh:
            print("FCC-CHECK VERDICT STALE")
            return 2
        print("FCC-CHECK VERDICT PASS read_only=True")
    return 2 if report["left_behind"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
