# closeout_export_parity_text_binding.py - the wire finally binds the text it lands
# Criteria AC-CEPM1..AC-CEPM6 were pre-registered in state/queue/tech.md:535
# (the R2454 seed row) BEFORE this file existed.
#
# Why this exists: closeout_export_parity_wire.publish accepts the text its
# caller hands in and proves it against the parity, but the parity recomposes
# the STAGED bytes - it never asks whether those bytes are what the document
# being replaced composes to. MEASURED at R2454: publishing a composition made
# from document A over document B read WRITTEN/AGREES and silently wrote A's
# content into B (self_drive.tick 9 became 1). One document's content landed
# under another document's name and no face named it.
#
# This module is that binding. Before any byte is staged it asks the shipped
# composition (closeout_export_parity_wire.compose, which is
# export_closeout_gate_parity.closeout_style - the ONE owner of the closeout
# byte shape) what THIS document composes to at CALL time, and compares that
# with the text the caller handed in. Same content publishes exactly as today;
# different content refuses with E_CEPM_BINDING naming the first differing
# field from the shipped difference law (export_closeout_gate_parity
# .first_difference) and leaves the target byte-identical with no residue.
#
# The comparison normalises line endings only. Transport is the target's own
# business (GWDA.payload_for renders it on the write path, exactly as before),
# so a caller handing in the same content in either transport still publishes
# and the document keeps the bytes it has today.
#
# CLI: closeout_export_parity_text_binding.py --publish
#          [--text-from PATH] [--root PATH] [--export PATH] [--json]
#   --publish        bind the text to the target document, then publish it
#   --text-from PATH  read the text to publish from PATH (default: compose
#                     the target document itself)
#   exit 0 = WRITTEN (bound, published), 2 = REFUSED (binding or parity),
#   3 = a file is missing or unreadable, 5 = the flags are bad
#
# Pure ASCII source, stdlib only, zero network, no clock.

import io
import json
import os
import sys

import closeout_export_parity_wire as CEPW
import export_closeout_gate_parity as ECGP

LABEL = "os-closeout-export-parity-text-binding"
DEFAULT_EXPORT = os.path.join("docs", "status-export.json")

# The wire's seven reading keys keep their names AND their positions; the
# binding reading is strictly additional (AC-CEPM5).
REPORT_KEYS = tuple(CEPW.REPORT_KEYS) + ("binding", "differs")

USAGE = (
    "usage: closeout_export_parity_text_binding.py --publish "
    "[--text-from PATH] [--root PATH] [--export PATH] [--json]\n"
    "  --publish         bind the text to the target document, then publish\n"
    "  --text-from PATH  read the text to publish from PATH "
    "(default: compose the target)\n"
    "  --root PATH       repository root to read the queues from (default .)\n"
    "  --export PATH     export document to publish "
    "(default docs/status-export.json)\n"
    "  --json            emit one machine-readable object\n"
    "  exit 0 = WRITTEN, 2 = REFUSED, 3 = missing file, 5 = bad flags\n"
)


class CloseoutExportParityTextBindingError(Exception):
    """Refusal with a stable code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def compose(root, path):
    """The bytes this document composes to, from the wire's one owner."""
    try:
        return CEPW.compose(root, path)
    except CEPW.CloseoutExportParityWireError as exc:
        raise CloseoutExportParityTextBindingError(exc.code, exc.detail)


def bind(root, path, text):
    """Compare handed text with the target's own composition.

    Returns (difference, composed). `difference` is "" when the handed text
    carries the same content as the document's own composition, otherwise it
    names the first differing field from the shipped difference law.
    """
    composed = compose(root, path)
    left = _normalise(composed)
    right = _normalise(text)
    if left == right:
        return "", composed
    difference = ECGP.first_difference(left, right) or "bytes"
    return difference, composed


def publish(root, path, text=None):
    """Bind first, then publish through the shipped wire (AC-CEPM1/2/3)."""
    if text is None:
        text = compose(root, path)
    difference, _composed = bind(root, path, text)
    if difference:
        return _refused(path, difference), 2
    result, code = CEPW.publish(root, path, text)
    published = dict(result)
    published["binding"] = "BOUND"
    published["differs"] = ""
    return published, code


def _normalise(text):
    """Transport only: the comparison is about content, never line endings."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _refused(path, difference):
    """The refusal report: the wire's seven keys, plus the binding reading."""
    return {
        "label": CEPW.LABEL,
        "verdict": "REFUSED",
        "path": path,
        "gate": None,
        "reading": None,
        "bytes": 0,
        "residue": "(none)",
        "binding": "REFUSED",
        "differs": difference,
    }


def _text_from(path):
    try:
        with io.open(path, "r", encoding="utf-8-sig", newline="") as handle:
            return handle.read()
    except (IOError, OSError):
        raise CloseoutExportParityTextBindingError("E_CEPM_TEXT_UNREADABLE", path)


def _check_flags(argv):
    if not argv or "--help" in argv or "-h" in argv:
        return None, None, None, None, True
    root = "."
    export = DEFAULT_EXPORT
    text_from = None
    as_json = False
    saw_publish = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--publish":
            saw_publish = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--export", "--text-from"):
            index += 1
            if index >= len(argv):
                raise CloseoutExportParityTextBindingError(
                    "E_CEPM_BAD_FLAGS", "missing value for %s" % arg)
            if arg == "--root":
                root = argv[index]
            elif arg == "--export":
                export = argv[index]
            else:
                text_from = argv[index]
        else:
            raise CloseoutExportParityTextBindingError(
                "E_CEPM_BAD_FLAGS", "unknown argument %s" % arg)
        index += 1
    if not saw_publish:
        raise CloseoutExportParityTextBindingError("E_CEPM_BAD_FLAGS",
                                                   "--publish is required")
    return root, export, text_from, as_json, False


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        root, export, text_from, as_json, help_wanted = _check_flags(argv)
    except CloseoutExportParityTextBindingError as exc:
        sys.stderr.write("%s\n" % exc)
        return 5
    if help_wanted:
        sys.stdout.write(USAGE)
        return 0

    try:
        text = None if text_from is None else _text_from(text_from)
        result, code = publish(root, export, text)
    except CloseoutExportParityTextBindingError as exc:
        sys.stderr.write("%s\n" % exc)
        return 3

    if as_json:
        payload = {}
        for key in REPORT_KEYS:
            payload[key] = result[key]
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(
            "TEXT BINDING %s verdict=%s path=%s binding=%s differs=%s "
            "gate=%s reading=%s bytes=%d residue=%s\n"
            % (result["label"], result["verdict"], result["path"],
               result["binding"], result["differs"] or "(none)",
               result["gate"], result["reading"], result["bytes"],
               result["residue"]))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))