"""R2388 live capture: the real declaration, measured through the new law.

Three legs, each printed as one line, written through ONE utf-8 LF writer:

  A the REAL declaration's dialect, read by the module CLI;
  B a CRLF copy of the REAL declaration compared with its own LF
    normalisation - NOOP with raw_equal=no, the copy byte-identical after the
    reading and no temp file beside it (before R2388 a byte comparison would
    have said PLANNED and a writer would have rewritten the whole file);
  C the REAL tree's dry re-pin at R2388 through the shipped CLI, which must
    stay PLANNED because the content really differs - the normalisation is
    content-safe, not a blanket answer.
"""

import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import repin_noop_eol_dialect as RNED  # noqa: E402

DECLARATION = os.path.join(ROOT, "state", "residue_triage.json")
EVIDENCE = os.path.join(ROOT, "qa", "repin-noop-eol-dialect-live-R2388.log")
MODULE = os.path.join(BASE, "repin_noop_eol_dialect.py")
SHIPPED = os.path.join(BASE, "residue_triage_repin.py")
WIRE = os.path.join(BASE, "residue_triage_repin_idempotent.py")


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def run(argv):
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace").strip(), \
        err.decode("utf-8", "replace").strip()


def main():
    lines = []
    data = RNED.read_bytes(DECLARATION)
    if data is None:
        sys.stdout.write("E_LIVE_NO_DECLARATION\n")
        return 3

    code, out, _ = run([sys.executable, MODULE, "--dialect", DECLARATION])
    lines.append("LEG-A dialect=%s rc=%d out=%s"
                 % (RNED.dialect_of(data), code, out.replace("\n", " | ")))

    work = tempfile.mkdtemp(prefix="rned-live-")
    try:
        crlf_path = os.path.join(work, "residue_triage.json")
        with io.open(crlf_path, "wb") as handle:
            handle.write(data if b"\r" in data
                         else data.replace(b"\n", b"\r\n"))
        composed = os.path.join(work, "composition.txt")
        with io.open(composed, "wb") as handle:
            handle.write(RNED.normalise_bytes(data))
        before = digest(crlf_path)
        code, out, _ = run([sys.executable, MODULE, "--compare", crlf_path,
                            "--composed", composed])
        after = digest(crlf_path)
        temps = sorted(name for name in os.listdir(work)
                       if name.endswith(".tmp") or "tmp-" in name)
        lines.append("LEG-B rc=%d unchanged=%s temps=%r out=%s"
                     % (code, "yes" if before == after else "no", temps,
                        out.replace("\n", " | ")))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    args = ["--round", "R2388", "--until", "R2404",
            "--reason", "live reading at R2388, dry run"]
    shipped = run([sys.executable, SHIPPED] + args)
    wire = run([sys.executable, WIRE] + args)
    lines.append("LEG-C shipped_rc=%d wire_rc=%d same_stdout=%s shipped=%s"
                 % (shipped[0], wire[0],
                    "yes" if shipped[1] == wire[1] else "no",
                    shipped[1].split("\n")[0]))

    body = "R2388 repin_noop_eol_dialect live capture\n" + "\n".join(lines) + "\n"
    with io.open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())