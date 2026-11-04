# status_export_writer_dialect_wire.py - every writer that lands the
# CEO-visible export is proved to ask the dialect law, and both transports are
# proved by a REAL writer call rather than by reading its source.
# Criteria AC-SEWD1..AC-SEWD6 were pre-registered in state/queue/tech.md:516
# (the R2448 seed row) BEFORE this file existed.
#
# Why this exists: the R2448 parameter-resolution law resolved three writers
# that land docs/status-export.json - closeout_export_parity_wire,
# queue_export_gate_wire and queue_floor_export_face - and MEASURED that none
# of them asked the shared payload derivation, so the dialect audit read
# AUDIT-DEBT (routed=7 unrouted=3) for the first time. A document the reader
# opens was being rewritten by whichever writer happened to run, in whichever
# transport that writer felt like.
#
# This wire is the proof that the debt is closed, and it derives its subject
# rather than listing it (AC-SEWD1): the writer set is READ OFF the shipped
# audit's own reading at CALL time, filtered to the rows whose resolved
# destination spells docs/status-export.json. A hardcoded list of three names
# would go stale the moment a fourth writer landed that file, so there is no
# list in this module.
#
# The transport proof (AC-SEWD2/AC-SEWD3) runs the REAL queue-floor writer
# twice over copies of a supplied export: an LF copy must come back byte for
# byte as today's composition, and a CRLF copy must come back CRLF with zero
# lone LF. Nothing is transcribed from the law - the law is asked at the write
# site by the writer itself.
#
# CLI: status_export_writer_dialect_wire.py --check [--root PATH]
#                                              [--sample PATH] [--json]
#   exit 0 = WIRED (every derived writer asks the law and both transports hold)
#   exit 2 = UNROUTED or TRANSPORT-SPLIT (the reading names what failed)
#   exit 3 = EMPTY (the audit derives no writer for this document)
#   exit 5 = the flags are bad
#
# Pure ASCII source, stdlib only, zero network, no clock. The only bytes it
# writes are the two fixture copies inside the directory its caller supplies.

import io
import json
import os
import shutil
import sys
import tempfile

import general_writer_dialect_audit as GWDA
import queue_floor_export_face as QFE

LABEL = "os-status-export-writer-dialect-wire"
TARGET = "docs/status-export.json"

WIRED = "WIRED"
UNROUTED = "UNROUTED"
EMPTY = "EMPTY"
SPLIT = "TRANSPORT-SPLIT"

ROW_KEYS = ("name", "target", "asks")
REPORT_KEYS = ("label", "verdict", "derived", "routed", "unrouted", "rows",
               "transport")

USAGE = (
    "usage: status_export_writer_dialect_wire.py --check [--root PATH] "
    "[--sample PATH] [--json]\n"
    "  --check        derive the export writers from the audit and read them\n"
    "  --root PATH    repository root the audit and the writer read (default .)\n"
    "  --sample PATH  export document to copy for the two transport proofs\n"
    "  --json         emit one machine-readable object\n"
    "  exit 0 = WIRED, 2 = UNROUTED or TRANSPORT-SPLIT, 3 = EMPTY, 5 = bad flags\n"
)


class WireError(Exception):
    """A refusal carrying its own code, never a traceback."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code if not detail else "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def spell(target):
    """One slash form for a resolved destination, so the filter is literal."""
    text = (target or "").replace("\\", "/").strip()
    if text.startswith("./"):
        text = text[2:]
    return text


def derived(root):
    """The KEEPS writers whose own destination is the CEO-visible export.

    The audit is asked at CALL time (AC-SEWD1), so patching its reading moves
    this set, and a writer that lands the same file tomorrow joins it without
    an edit here.
    """
    try:
        reading = GWDA.report(root)
    except GWDA.AuditError as exc:
        raise WireError(exc.code, exc.detail)
    rows = [row for row in reading["rows"]
            if row["kind"] == "KEEPS" and spell(row["target"]) == TARGET]
    return reading, rows


def transport(folder, sample):
    """Run the REAL queue-floor writer over an LF copy and a CRLF copy."""
    with io.open(sample, "rb") as handle:
        raw = handle.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise WireError("E_SEWD_SAMPLE_NOT_UTF8", sample)
    lf_path = os.path.join(folder, "lf.json")
    crlf_path = os.path.join(folder, "crlf.json")
    body = text.replace("\r\n", "\n")
    if not body.endswith("\n"):
        body += "\n"
    with io.open(lf_path, "wb") as handle:
        handle.write(body.encode("utf-8"))
    composed = QFE.compose(".", lf_path)
    QFE.write(".", lf_path)
    with io.open(lf_path, "rb") as handle:
        lf_back = handle.read()
    lf_ok = lf_back == composed.encode("utf-8")

    with io.open(crlf_path, "wb") as handle:
        handle.write(body.replace("\n", "\r\n").encode("utf-8"))
    QFE.write(".", crlf_path)
    with io.open(crlf_path, "rb") as handle:
        crlf_back = handle.read()
    lone = crlf_back.replace(b"\r\n", b"").count(b"\n")
    crlf_ok = (lone == 0 and b"\r\n" in crlf_back
               and crlf_back.replace(b"\r\n", b"\n") == composed.encode("utf-8"))

    return {
        "lf_bytes": len(lf_back),
        "lf_today_exact": lf_ok,
        "crlf_bytes": len(crlf_back),
        "crlf_lone_lf": lone,
        "crlf_kept": crlf_ok,
    }


def check(root, sample=None):
    """The one reading this wire publishes."""
    reading, rows = derived(root)
    keeps = [row for row in reading["rows"] if row["kind"] == "KEEPS"]
    routed = [row for row in rows if row["asks"]]
    unrouted = [row["name"] for row in rows if not row["asks"]]
    transport_row = None
    if sample is not None:
        if not os.path.exists(sample):
            raise WireError("E_SEWD_SAMPLE_MISSING", sample)
        folder = tempfile.mkdtemp(prefix="sewd-")
        try:
            transport_row = transport(folder, sample)
        finally:
            shutil.rmtree(folder, ignore_errors=True)
    if not rows:
        verdict = EMPTY
    elif unrouted:
        verdict = UNROUTED
    elif transport_row is not None and not (
            transport_row["lf_today_exact"] and transport_row["crlf_kept"]):
        verdict = SPLIT
    else:
        verdict = WIRED
    return {
        "label": LABEL,
        "verdict": verdict,
        "derived": len(rows),
        "routed": len(routed),
        "unrouted": list(unrouted),
        "rows": [{"name": row["name"], "target": row["target"],
                  "asks": row["asks"]} for row in rows],
        "transport": transport_row,
        "audit_keeps": len(keeps),
        "audit_routed": reading["routed"],
        "audit_verdict": reading["verdict"],
    }


def one_line(reading):
    transport_row = reading["transport"]
    shown = "-" if transport_row is None else "%s/%s" % (
        "LF" if transport_row["lf_today_exact"] else "LF-MOVED",
        "CRLF" if transport_row["crlf_kept"] else "CRLF-BROKEN")
    return ("STATUS EXPORT WRITERS derived=%d routed=%d unrouted=%d "
            "transport=%s audit=%s verdict=%s"
            % (reading["derived"], reading["routed"],
               len(reading["unrouted"]), shown, reading["audit_verdict"],
               reading["verdict"]))


def render(reading):
    out = [one_line(reading)]
    for row in reading["rows"]:
        out.append("  WRITER %s target=%s asks=%s"
                   % (row["name"], row["target"],
                      "yes" if row["asks"] else "no"))
    if reading["unrouted"]:
        out.append("  UNROUTED %s" % ", ".join(reading["unrouted"]))
    transport_row = reading["transport"]
    if transport_row is not None:
        out.append("  TRANSPORT lf=%dB today-exact=%s crlf=%dB lone-lf=%d "
                   "crlf-kept=%s"
                   % (transport_row["lf_bytes"],
                      transport_row["lf_today_exact"],
                      transport_row["crlf_bytes"],
                      transport_row["crlf_lone_lf"],
                      transport_row["crlf_kept"]))
    return "\n".join(out)


def parse(argv):
    opts = {"root": ".", "sample": None, "json": False, "check": False}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--check",):
            opts["check"] = True
        elif arg == "--json":
            opts["json"] = True
        elif arg in ("--root", "--sample"):
            if index + 1 >= len(argv):
                raise WireError("E_SEWD_BAD_FLAGS", "%s needs a value" % arg)
            opts[arg[2:]] = argv[index + 1]
            index += 1
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            raise SystemExit(0)
        else:
            raise WireError("E_SEWD_BAD_FLAGS", "unknown argument %s" % arg)
        index += 1
    if not opts["check"]:
        raise WireError("E_SEWD_BAD_FLAGS", "--check is required")
    if not os.path.isdir(opts["root"]):
        raise WireError("E_SEWD_BAD_FLAGS", "--root is not a directory")
    return opts


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        opts = parse(argv)
        reading = check(opts["root"], opts["sample"])
    except WireError as exc:
        sys.stdout.write("%s\n" % exc)
        if exc.code == "E_SEWD_BAD_FLAGS":
            sys.stdout.write(USAGE)
            return 5
        return 3 if exc.code.endswith("SAMPLE_MISSING") else 2
    if opts["json"]:
        sys.stdout.write(json.dumps(reading, ensure_ascii=True, indent=2) + "\n")
    else:
        sys.stdout.write(render(reading) + "\n")
    if reading["verdict"] == WIRED:
        return 0
    if reading["verdict"] == EMPTY:
        return 3
    return 2


if __name__ == "__main__":
    sys.exit(main())