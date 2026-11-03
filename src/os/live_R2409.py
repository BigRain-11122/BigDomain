# live_R2409.py - read-only live capture for R2409.
# Reads the REAL tree through the sweep, then proves the CRLF half on a COPY of
# the real declaration (the real file is never written by this script), and
# proves this window's module did not move while it ran.
# Stdlib only, ASCII source, zero network, no clock.

import hashlib
import io
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import gate_decl_append as GDA  # noqa: E402
import library_declaration_dialect_sweep as LDS  # noqa: E402
import machine_gate as MG  # noqa: E402


def sha16(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


def main():
    module = os.path.join(HERE, "library_declaration_dialect_sweep.py")
    before = sha16(module)
    reading = LDS.report(ROOT)
    print(LDS.one_line(reading), flush=True)
    for name in reading["offenders"]:
        print("  DEBT %s" % name, flush=True)

    copy = tempfile.mkdtemp(prefix="ldws-live-")
    try:
        rel = MG.DEFAULT_DECLARATION
        target = os.path.join(copy, rel)
        os.makedirs(os.path.dirname(target))
        real = os.path.join(ROOT, rel)
        with io.open(real, "rb") as handle:
            raw = handle.read()
        lf = raw.replace(b"\r\n", b"\n")
        crlf = lf.replace(b"\n", b"\r\n")
        with io.open(target, "wb") as handle:
            handle.write(crlf)
        got = GDA.append_gate(copy, "-#LDSLIVE", "battery",
                              "live crlf proof", "R2409", execute=True)
        landed = io.open(target, "rb").read()
        lone = landed.replace(b"\r\n", b"")
        print("  CRLF COPY dialect-before=CRLF entries-before=%d entries-after=%d"
              % (got["declarations_before"], got["declarations_after"]),
              flush=True)
        print("  CRLF COPY kept=%s lone_lf=%d lone_cr=%d read_back=%s"
              % (b"\r\n" in landed, lone.count(b"\n"), lone.count(b"\r"),
                 got["read_back_ok"]), flush=True)
    finally:
        shutil.rmtree(copy, ignore_errors=True)

    after = sha16(module)
    print("  MODULE digest %s unchanged=%s" % (after, before == after),
          flush=True)
    return 0 if before == after and reading["unrouted"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())