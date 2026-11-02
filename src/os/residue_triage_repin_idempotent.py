"""residue_triage_repin_idempotent - the re-pin finally has a NOOP (R2372).

`residue_triage_repin` composes a fresh declaration and writes it, but it
cannot tell "there is nothing to do" from "I rewrote the declaration". R2363
measured the seam at its own live write: a second plan composed bytes
IDENTICAL to the file on disk (predicted 62266 == on_disk 62266) and still
read PLANNED, so --execute would rewrite the same 62266 bytes and report
PINNED, and every ledger-style reader would see a write where there was none.

This is that reading added, and it adds nothing else:

  * the composition is `residue_triage_repin.build` and the writer is
    `residue_triage_repin.plan`; neither the document shape nor the atomic
    replace is re-implemented here (a patched build moves this reading, a
    patched plan moves the executed path);
  * the reading is NOOP exactly when the composed document's bytes equal the
    bytes on disk, and it is decided by BYTES - this module never looks at the
    declaration's head round, so a declaration whose content already IS the
    composition of the requested round reads NOOP however old that round is;
  * a NOOP returns before the writer is entered at all, so no temp file is
    created and the single atomic write path is not doubled;
  * every non-NOOP path is the shipped writer's own report, printed through
    the shipped renderer and serialiser, so the CLI exit codes and the pinned
    --json key order are byte-identical to `residue_triage_repin`.

Pure stdlib, pure ASCII source, zero network, no clock of its own. Criteria
AC-RTRI1..AC-RTRI6 were pinned inside the R2363 seed row of state/queue/tech.md
BEFORE this code existed.
"""

import os
import sys

import residue_triage_repin as RTR

REPORT_KEYS = RTR.PLAN_KEYS

NOOP = "NOOP"

USAGE = ("usage: residue_triage_repin_idempotent.py --round R<n> "
         "--until R<n> --reason TEXT [--drop-unmatched] [--execute] "
         "[--root PATH] [--json]\n"
         "  dry run is the default and writes no byte\n"
         "  exit 0 = PLANNED (dry run), PINNED (--execute) or NOOP "
         "(the file already IS the composition)\n"
         "  exit 2 = refused over live state (DISAGREES, UNMATCHED, "
         "NOT-TRIAGED)\n"
         "  exit 3 = the declaration is missing (UNPINNED) or unreadable\n"
         "  exit 5 = bad flags (including an --until before the round)\n")


def on_disk_bytes(path):
    """The declaration's bytes, or None when there is no file to compare."""
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except (IOError, OSError):
        return None


def decide(root, round_text, until_text, reason, allow_drop=False,
           execute=False):
    """Compose first, then compare BYTES with the file: NOOP or the writer.

    The composition is the shipped one (`build`), so the refusal surface is
    unchanged: every reason a re-pin refuses is raised here before the
    comparison is ever made. The NOOP branch returns before `plan` is called,
    which is what keeps the write path singular.
    """
    report = RTR.build(root, round_text, until_text, reason, allow_drop)
    composed = report["_text"].encode("utf-8")
    current = on_disk_bytes(report["_path"])
    if current is not None and current == composed:
        report["verdict"] = NOOP
        report["executed"] = False
        return report
    return RTR.plan(root, round_text, until_text, reason, allow_drop, execute)


def one_line(report):
    """The shipped line, with the agreement named when nothing was written."""
    line = RTR.one_line(report)
    if report["verdict"] == NOOP:
        line += " noop_at=%s" % report["round"]
    return line


def render(report):
    """The shipped body plus one explicit line on the NOOP reading."""
    body = RTR.render(report)
    if report["verdict"] == NOOP:
        body += ("\n  NOOP the composed declaration equals the file on disk "
                 "at %s - nothing to write" % report["round"])
    return body


def to_json(report):
    """The shipped serialiser, so the pinned key order cannot drift."""
    return RTR.to_json(report)


def main(argv):
    as_json = False
    execute = False
    allow_drop = False
    round_text = None
    until_text = None
    reason = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            as_json = True
        elif arg == "--execute":
            execute = True
        elif arg == "--drop-unmatched":
            allow_drop = True
        elif arg in ("--round", "--until", "--reason", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RTRP_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            if arg == "--round":
                round_text = argv[index]
            elif arg == "--until":
                until_text = argv[index]
            elif arg == "--reason":
                reason = argv[index]
            else:
                root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RTRP_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if round_text is None or until_text is None or reason is None:
        sys.stdout.write("E_RTRP_BAD_ARGS: --round, --until and --reason are "
                         "required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = decide(root, round_text, until_text, reason, allow_drop,
                        execute)
    except RTR.RT.ResidueTriageError as exc:
        # the refusals belong to residue_triage, and so do their exit codes
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code in ("E_RTR_UNREADABLE", "E_RTR_BAD_SHAPE",
                        "E_RTR_BAD_STATE", "E_RTR_BAD_STATUS",
                        "E_RTR_DUPLICATE"):
            return 3
        return 2
    except RTR.RepinError as exc:
        # the writer's own refusals, mapped exactly as residue_triage_repin
        # maps them, so a caller cannot tell the two CLIs apart
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        if exc.code in ("E_RTRP_UNPINNED", "E_RTRP_SIZE"):
            return 3
        if exc.code in ("E_RTRP_BAD_REASON", "E_RTRP_UNTIL_PREDATES"):
            return 5
        return 2
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))