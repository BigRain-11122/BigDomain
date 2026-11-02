"""followup_section_foreign_wire (R2370; criteria AC-FSFW1..AC-FSFW6 were pinned
inside the R2357 seed row of state/queue/tech.md BEFORE this code existed).

followup_section_foreign (R2357) reads the evidence pile and says whether any
round reported a SECTION name the ritual does not own. Nothing consumed it:
battery_followup's matrix section regenerated the matrix doc over whatever the
pile contained, so a future ritual RENAME would have regenerated the matrix
over foreign sections in silence while the reader stayed a manual call.
Measured at R2357: the reader read VOCABULARY-CLEAN over 454 rounds and no code
path asked it.

This module is the WIRE - the follow-up matrix section asks the reader FIRST:

  - FOREIGN-SECTION   the section REFUSES before any matrix byte is rendered
                      and names the rounds and the foreign names
                      (E_FSFW_FOREIGN_SECTION);
  - VOCABULARY-CLEAN  the section runs exactly as it did before this wire, and
                      the matrix doc it compares is byte-identical (AC-FSFW3);
  - a census disagreement (a foreign name seen, or a vocabulary name never
    seen) is REPORTED on the section's one-line detail even when every round
    is clean, so a rename is never silent (AC-FSFW4).

Two authorities are kept apart on purpose: followup_section_foreign owns the
reading (this file parses no log) and battery_followup owns the matrix core
(this file renders no matrix), so each law still has exactly one owner.

A pile the reader cannot speak about at all (no evidence name it recognises, an
unreadable log, a duplicate round) is NOT a refusal: the matrix section runs as
before and the guard's own code is carried on the detail, because a guard must
never invent a refusal for a pile it could not read.

It writes nothing, reads no clock, opens no network connection. Pure stdlib,
pure-ASCII source.
"""

import json
import sys

import followup_section_foreign as FSF

READING_CLEAN = "VOCABULARY-CLEAN"
READING_FOREIGN = "FOREIGN-SECTION"
READING_UNREADABLE = "UNREADABLE"

E_FSFW_BAD_ARGS = "E_FSFW_BAD_ARGS"
E_FSFW_FOREIGN_SECTION = "E_FSFW_FOREIGN_SECTION"

GUARD_KEYS = ("dir", "verdict", "rounds", "rounds_foreign", "foreign",
              "census", "code")
CENSUS_KEYS = ("vocabulary", "foreign", "missing")
SECTION_NAME = "matrix"

USAGE = ("usage: followup_section_foreign_wire.py --check [DIR] "
         "[--root PATH] [--json]\n"
         "  DIR defaults to qa\n"
         "  exit 0 = VOCABULARY-CLEAN, the matrix section may run\n"
         "  exit 2 = FOREIGN-SECTION, the matrix section refuses\n"
         "  exit 3 = the pile cannot be read at all\n"
         "  exit 5 = bad flags\n")


def guard(root, directory="qa"):
    """AC-FSFW1: the reading is followup_section_foreign's; this file adds none."""
    try:
        report = FSF.reading(root, directory)
    except FSF.FollowupSectionForeignError as exc:
        empty = {"vocabulary": [], "foreign": [], "missing": []}
        return {"dir": directory, "verdict": READING_UNREADABLE, "rounds": 0,
                "rounds_foreign": [], "foreign": [], "census": empty,
                "code": exc.code}
    rounds_foreign = []
    names = []
    for item in report["rounds"]:
        if item["reading"] == FSF.READING_FOREIGN:
            rounds_foreign.append(item["round"])
            for name in item["foreign"]:
                if name not in names:
                    names.append(name)
    return {"dir": report["dir"], "verdict": report["verdict"],
            "rounds": report["counts"]["rounds"],
            "rounds_foreign": rounds_foreign,
            "foreign": sorted(names),
            "census": dict(report["census"]),
            "code": ""}


def census_note(reading):
    """AC-FSFW4: a rename is reported even when every round reads clean."""
    census = reading["census"]
    parts = []
    seen_foreign = census.get("foreign") or []
    seen_missing = census.get("missing") or []
    if seen_foreign:
        parts.append("foreign=" + ",".join(seen_foreign))
    if seen_missing:
        parts.append("missing=" + ",".join(seen_missing))
    return ("census " + " ".join(parts)) if parts else ""


def refusal_detail(reading):
    """AC-FSFW2: the refusal names the rounds AND the foreign names."""
    return ("%s round=%s names=%s"
            % (E_FSFW_FOREIGN_SECTION,
               ",".join(reading["rounds_foreign"]) or "-",
               ",".join(reading["foreign"]) or "-"))


def matrix_section(root, evidence, call, directory="qa"):
    """The guarded matrix section: reader first, refusal before any byte."""
    reading = guard(root, directory)
    if reading["verdict"] == FSF.VERDICT_FOREIGN:
        return {"section": SECTION_NAME, "verdict": "FAIL",
                "detail": refusal_detail(reading)}, ""
    import battery_followup as BF
    entry, body = BF.matrix_core(root, evidence, call)
    tail = []
    if reading["verdict"] == READING_UNREADABLE:
        tail.append("guard=%s" % reading["code"])
    note = census_note(reading)
    if note:
        tail.append(note)
    if tail:
        return {"section": entry["section"], "verdict": entry["verdict"],
                "detail": entry["detail"] + " " + " ".join(tail)}, body
    return entry, body


def render(reading):
    """One line, the census, then the verdict - ASCII, one trailing LF."""
    census = reading["census"]
    out = ["FOLLOWUP SECTION GUARD dir=%s rounds=%d foreign_rounds=%d "
           "verdict=%s"
           % (reading["dir"], reading["rounds"],
              len(reading["rounds_foreign"]), reading["verdict"])]
    out.append("  foreign=%s" % (",".join(reading["foreign"]) or "none"))
    out.append("census foreign=%s missing=%s"
               % (",".join(census.get("foreign") or []) or "none",
                  ",".join(census.get("missing") or []) or "none"))
    if reading["code"]:
        out.append("code=%s" % reading["code"])
    return "\n".join(out)


def to_json(reading):
    """AC-FSFW5: the pinned GUARD_KEYS order, ASCII, one trailing LF."""
    ordered = {}
    for key in GUARD_KEYS:
        if key == "census":
            census = {}
            for name in CENSUS_KEYS:
                census[name] = reading["census"].get(name) or []
            ordered["census"] = census
        else:
            ordered[key] = reading[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def main(argv):
    operation = False
    as_json = False
    root = "."
    directory = "qa"
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_FSFW_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_FSFW_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            directory = arg
        index += 1
    if not operation:
        sys.stdout.write("E_FSFW_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    reading = guard(root, directory)
    if as_json:
        sys.stdout.write(to_json(reading))
    else:
        sys.stdout.write(render(reading) + "\n")
    if reading["verdict"] == FSF.VERDICT_FOREIGN:
        return 2
    if reading["verdict"] == READING_UNREADABLE:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))