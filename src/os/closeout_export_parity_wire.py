# closeout_export_parity_wire.py - the parity finally runs on the write path
# Criteria AC-CEPW1..AC-CEPW6 were pre-registered in state/queue/tech.md:424
# (the R2377 seed row) BEFORE this file existed.
#
# Why this exists: R2377 shipped export_closeout_gate_parity, which measures
# whether the closeout recipe and queue_export_gate_wire publish the same
# bytes - but nothing calls it. The closeout scripts (closeout_R2375.py,
# closeout_R2376.py, closeout_R2377.py) read the document, call QFE.apply,
# dump it and write it themselves, so a closeout can still publish a block
# that nobody proved, and the parity only ever speaks when a human types the
# CLI. git grep -l export_closeout_gate_parity at HEAD listed only the
# module, its suite and the registry.
#
# This wire is the caller. It stages the bytes it is about to publish beside
# the real export, asks export_closeout_gate_parity.check over that staged
# document, and only replaces the export when the reading is AGREES. The
# check is asked as an attribute at call time, so patching it moves what gets
# published (AC-CEPW1); a refusal removes the staged file and leaves the
# export byte-identical with no residue (AC-CEPW2); an AGREES reading writes
# the staged bytes and proves them by reading back (AC-CEPW3); the wire
# writes nothing when it refuses and reads no clock (AC-CEPW4).
#
# compose() is export_closeout_gate_parity.closeout_style - the one owner of
# the closeout byte shape - so this file carries no json.dump, no QFE import
# and no second formatter. A caller that already composed its document (the
# closeout, after its own field mutations) hands the text in, which is the
# honest route: the wire proves the bytes it publishes rather than rebuilding
# them.
#
# CLI: closeout_export_parity_wire.py --publish [--root PATH] [--export PATH]
#                                      [--json]
#   exit 0 = WRITTEN (the parity agreed, the export was replaced)
#   exit 2 = REFUSED (the reading is named), export untouched
#   exit 3 = the export file is missing or unreadable
#   exit 5 = the flags are bad
#
# Pure ASCII source, stdlib only, zero network, no clock.

import io
import json
import os
import sys

import export_closeout_gate_parity as ECGP

LABEL = "os-closeout-export-parity-wire"
DEFAULT_EXPORT = os.path.join("docs", "status-export.json")

REPORT_KEYS = ("label", "verdict", "path", "gate", "reading", "bytes",
               "residue")

USAGE = (
    "usage: closeout_export_parity_wire.py --publish [--root PATH] "
    "[--export PATH] [--json]\n"
    "  --publish      prove the blocked bytes with the parity, then replace\n"
    "  --root PATH    repository root to read the queues from (default .)\n"
    "  --export PATH  export document to publish "
    "(default docs/status-export.json)\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = WRITTEN, 2 = REFUSED, 3 = missing file, 5 = bad flags\n"
)


class CloseoutExportParityWireError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def compose(root, path):
    """The closeout byte shape for this document, from its one owner."""
    try:
        return ECGP.closeout_style(root, path)
    except ECGP.ExportCloseoutGateParityError as exc:
        raise CloseoutExportParityWireError(exc.code, exc.detail)


def publish(root, path, text=None):
    """Stage, prove with the parity, and only then replace the export."""
    if text is None:
        text = compose(root, path)
    stage = path + ".parity-stage"
    report, code = _stage_and_check(root, path, stage, text)
    if code != 0:
        return {
            "label": LABEL,
            "verdict": "REFUSED",
            "path": path,
            "gate": report.get("gate"),
            "reading": report.get("verdict"),
            "bytes": 0,
            "residue": "(none)",
        }, 2
    os.replace(stage, path)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    if back != text:
        raise CloseoutExportParityWireError("E_CEPW_READBACK", path)
    return {
        "label": LABEL,
        "verdict": "WRITTEN",
        "path": path,
        "gate": report.get("gate"),
        "reading": "AGREES",
        "bytes": len(back.encode("utf-8")),
        "residue": "(none)",
    }, 0


def _stage_and_check(root, path, stage, text):
    """Write the staged bytes, ask the parity, and leave no residue on refusal.

    The staged file SURVIVES a passing reading on purpose: the caller replaces
    the export with it, so removing it here would publish nothing.
    """
    try:
        with io.open(stage, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    except (IOError, OSError):
        _drop(stage)
        raise CloseoutExportParityWireError("E_CEPW_STAGE", path)
    try:
        report, code = ECGP.check(root, stage)
    except ECGP.ExportCloseoutGateParityError as exc:
        _drop(stage)
        raise CloseoutExportParityWireError(exc.code, exc.detail)
    if code != 0:
        _drop(stage)
    return report, code


def _drop(path):
    """Remove a staged file if it exists; never raise."""
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def _check_flags(argv):
    if not argv or "--help" in argv or "-h" in argv:
        return None, None, None, True
    root = "."
    export = DEFAULT_EXPORT
    as_json = False
    saw_publish = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--publish":
            saw_publish = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--export"):
            index += 1
            if index >= len(argv):
                raise CloseoutExportParityWireError("E_CEPW_BAD_FLAGS",
                                                    "missing value for %s" % arg)
            if arg == "--root":
                root = argv[index]
            else:
                export = argv[index]
        else:
            raise CloseoutExportParityWireError("E_CEPW_BAD_FLAGS",
                                                "unknown argument %s" % arg)
        index += 1
    if not saw_publish:
        raise CloseoutExportParityWireError("E_CEPW_BAD_FLAGS",
                                            "--publish is required")
    return root, export, as_json, False


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        root, export, as_json, help_wanted = _check_flags(argv)
    except CloseoutExportParityWireError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5
    if help_wanted:
        sys.stdout.write(USAGE)
        return 0

    try:
        result, code = publish(root, export)
    except CloseoutExportParityWireError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        payload = {}
        for key in REPORT_KEYS:
            payload[key] = result[key]
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "CLOSEOUT EXPORT PARITY %s verdict=%s path=%s gate=%s "
            "reading=%s bytes=%d residue=%s\n"
            % (result["label"], result["verdict"], result["path"],
               result["gate"], result["reading"], result["bytes"],
               result["residue"]))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))