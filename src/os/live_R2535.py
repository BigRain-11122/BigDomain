"""Live leg for R2535: read the REAL tree, then one fixture on BOTH readers.

Writes utf-8 with LF only through one writer, then reads the bytes back.
Nothing is imported or run from the probed tree; every reading is AST only.
"""

import hashlib
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_nested_subscript_scope as PCNS
import probe_seam_subscript_container_scope as PCSC
import suite_matrix as SM

LIVE = os.path.join(os.path.dirname(SRC), "qa",
                    "probe-seam-nested-subscript-scope-live-R2535.log")

FIXTURE = ('import importlib\n'
           '\n'
           'D = {"a": {"b": ("pcns_live_helper",)}}\n'
           '\n'
           'for name in D["a"]["b"]:\n'
           '    importlib.import_module(name)\n')


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main():
    module_digest = digest(os.path.join(BASE,
                                        "probe_seam_nested_subscript_scope.py"))
    base_digest = digest(os.path.join(
        BASE, "probe_seam_subscript_container_scope.py"))
    render_digest = digest(os.path.join(SANDBOX, "suite_matrix.py"))
    report = PCNS.audit(BASE, SM)
    counts = report["counts"]
    lines = []
    lines.append("PROBE SEAM NESTED SUBSCRIPT LIVE round=R2535")
    lines.append("  verdict=%s probes=%d covered=%d out_of_scope=%d "
                 "missing=%d unreadable=%d historical=%d"
                 % (report["verdict"], len(report["probes"]),
                    counts[PCNS.COVERED], counts[PCNS.OUT_OF_SCOPE],
                    counts[PCNS.MISSING_SEAM], counts[PCNS.UNREADABLE],
                    counts[PCNS.HISTORICAL]))
    lines.append("  read_only=True tree=%s" % BASE)
    world = tempfile.mkdtemp(prefix="pcns-live-")
    try:
        with open(os.path.join(world, "pcns_live_helper.py"), "w",
                  encoding="ascii", newline="\n") as handle:
            handle.write("QUIETED = ()\n")
        with open(os.path.join(world, "pcns_live_probe.py"), "w",
                  encoding="ascii", newline="\n") as handle:
            handle.write(FIXTURE)
        mine = PCNS.nested_report(FIXTURE, world)
        other = PCSC.subscript_report(FIXTURE, world)
        lines.append("  FIXTURE two-key chain: this face followed=%s"
                     % (mine["followed"].get("name"),))
        lines.append("  FIXTURE two-key chain: this face refused=%s"
                     % (mine["refused"].get("name"),))
        lines.append("  FIXTURE two-key chain: shipped subscript face "
                     "followed=%s refused=%s"
                     % (other["followed"].get("name"),
                        other["refused"].get("name"),))
        got = PCNS.audit(world, SM)
        row = [item for item in got["probes"]
               if item["file"] == "pcns_live_probe.py"]
        lines.append("  FIXTURE world verdict=%s probe=%s"
                     % (got["verdict"], row[0]["verdict"] if row else "-"))
    finally:
        for entry in sorted(os.listdir(world)):
            os.remove(os.path.join(world, entry))
        os.rmdir(world)
    lines.append("  digest module=%s base=%s render=%s"
                 % (module_digest[:16], base_digest[:16],
                    render_digest[:16]))
    lines.append("  digest_after module=%s base=%s render=%s"
                 % (digest(os.path.join(
                     BASE, "probe_seam_nested_subscript_scope.py"))[:16],
                    digest(os.path.join(
                        BASE, "probe_seam_subscript_container_scope.py"))[:16],
                    digest(os.path.join(SANDBOX, "suite_matrix.py"))[:16]))
    text = "\n".join(lines) + "\n"
    with open(LIVE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with open(LIVE, "rb") as handle:
        raw = handle.read()
    print(text, end="")
    print("  bytes=%d crlf=%d bom=%s"
          % (len(raw), raw.count(b"\r\n"), raw.startswith(b"\xef\xbb\xbf")))
    return 0


if __name__ == "__main__":
    sys.exit(main())