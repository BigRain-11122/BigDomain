# closeout_export_parity_dialect_wire.py - the closeout publish path in the
# document's OWN transport
# Criteria AC-CEPD1..AC-CEPD6 were pre-registered in state/queue/tech.md:520
# (the R2452 seed row) BEFORE this file existed.
#
# Why this exists: MEASURED at R2452 the closeout wire cannot publish a
# CRLF-dialect export at all - closeout_export_parity_wire reads REFUSED at
# exit 2 with the document byte-identical and the parity reading
# DISAGREES/bytes, while its LF leg writes normally. The cause was the parity
# itself: closeout_style() composed LF text while queue_export_gate_wire (the
# other recipe) kept the target's own dialect, so the two recipes disagreed on
# line endings and the refusal was transport-only, not content drift.
#
# This file is the publish path that asks the shipped dialect law (through the
# parity's own composition, which now lands the target transport at CALL time)
# and then reports what it actually landed. Nothing is re-derived here: the
# composition comes from export_closeout_gate_parity.closeout_style, the write
# and its parity proof come from closeout_export_parity_wire.publish, and the
# transport name comes from declaration_writer_dialect_preservation.dialect.
#
# What it adds is the operator reading the other wires do not publish: the
# document's own transport, and the number of LONE LF bytes left in the landed
# file (a CRLF document must read zero). A refusal is carried through with the
# parity's own gate and reading, and the document is left byte-identical.
#
# CLI: closeout_export_parity_dialect_wire.py --publish [--root PATH]
#                                              [--export PATH] [--json]
#   exit 0 = WRITTEN (the parity agreed and the target transport was landed)
#   exit 2 = REFUSED (the parity's reading is named), export untouched
#   exit 3 = the export file is missing or unreadable
#   exit 5 = the flags are bad
#
# Pure ASCII source, stdlib only, zero network, no clock.

import io
import json
import os
import sys

import closeout_export_parity_wire as CEPW
import declaration_writer_dialect_preservation as DWDP
import export_closeout_gate_parity as ECGP

LABEL = "os-closeout-export-parity-dialect-wire"
DEFAULT_EXPORT = os.path.join("docs", "status-export.json")

REPORT_KEYS = ("label", "verdict", "path", "transport", "gate", "reading",
               "bytes", "lone_lf", "residue")

USAGE = (
    "usage: closeout_export_parity_dialect_wire.py --publish [--root PATH] "
    "[--export PATH] [--json]\n"
    "  --publish      compose in the target's own transport, prove with the\n"
    "                 parity, then replace the export\n"
    "  --root PATH    repository root to read the queues from (default .)\n"
    "  --export PATH  export document to publish "
    "(default docs/status-export.json)\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = WRITTEN, 2 = REFUSED, 3 = missing file, 5 = bad flags\n"
)


class DialectWireError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def transport(path):
    """The document's own dialect, from the shipped law (never a guess)."""
    try:
        with io.open(path, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError):
        raise DialectWireError("E_CEPD_EXPORT_MISSING", path)
    return DWDP.dialect(raw)


def compose(root, path):
    """The bytes the closeout recipe publishes, in the target transport."""
    try:
        return ECGP.closeout_style(root, path)
    except ECGP.ExportCloseoutGateParityError as exc:
        raise DialectWireError(exc.code, exc.detail)


def _lone_lf(back):
    """Count the LF bytes that are NOT part of a CRLF pair."""
    return back.replace(b"\r\n", b"").count(b"\n")


def publish(root, path, text=None):
    """Compose, prove, replace - then report the transport actually landed."""
    if text is None:
        text = compose(root, path)
    own = transport(path)
    try:
        base, code = CEPW.publish(root, path, text)
    except CEPW.CloseoutExportParityWireError as exc:
        raise DialectWireError(exc.code, exc.detail)
    if code != 0:
        return {
            "label": LABEL,
            "verdict": "REFUSED",
            "path": path,
            "transport": own,
            "gate": base.get("gate"),
            "reading": base.get("reading"),
            "bytes": 0,
            "lone_lf": 0,
            "residue": base.get("residue"),
        }, 2
    try:
        with io.open(path, "rb") as handle:
            back = handle.read()
    except (IOError, OSError):
        raise DialectWireError("E_CEPD_READBACK", path)
    return {
        "label": LABEL,
        "verdict": "WRITTEN",
        "path": path,
        "transport": own,
        "gate": base.get("gate"),
        "reading": base.get("reading"),
        "bytes": len(back),
        "lone_lf": _lone_lf(back),
        "residue": base.get("residue"),
    }, 0


def one_line(result):
    return ("CLOSEOUT EXPORT PARITY DIALECT %s verdict=%s path=%s "
            "transport=%s gate=%s reading=%s bytes=%d lone_lf=%d residue=%s"
            % (result["label"], result["verdict"], result["path"],
               result["transport"], result["gate"], result["reading"],
               result["bytes"], result["lone_lf"], result["residue"]))


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
                raise DialectWireError("E_CEPD_BAD_FLAGS",
                                       "missing value for %s" % arg)
            if arg == "--root":
                root = argv[index]
            else:
                export = argv[index]
        else:
            raise DialectWireError("E_CEPD_BAD_FLAGS",
                                   "unknown argument %s" % arg)
        index += 1
    if not saw_publish:
        raise DialectWireError("E_CEPD_BAD_FLAGS", "--publish is required")
    return root, export, as_json, False


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        root, export, as_json, help_wanted = _check_flags(argv)
    except DialectWireError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5
    if help_wanted:
        sys.stdout.write(USAGE)
        return 0

    try:
        result, code = publish(root, export)
    except DialectWireError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        payload = {}
        for key in REPORT_KEYS:
            payload[key] = result[key]
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(one_line(result) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))