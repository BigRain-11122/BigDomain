"""live_R2406 - the read-only live capture for the repin dialect window.

It measures the REAL tree and writes nothing there: the declaration's own
dialect, the shipped re-pin CLI's dry run over that same declaration, a CRLF
copy of it resolved through the new seam, and a MIXED copy refused by the
shipped CLI. Every line lands in one utf-8 LF file through one writer.

ASCII source, stdlib only, no clock, no network.
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import repin_dialect_preservation as RDPL  # noqa: E402
import repin_noop_eol_dialect as RNP  # noqa: E402

DECL = os.path.join(REPO, "state", "residue_triage.json")
OUT = os.path.join(REPO, "qa", "repin-dialect-preservation-live-R2406.log")

REASON = ("R2406 re-pin: the fold at R2405 left R2393 live in the residue "
          "and R2402 no longer live, so the declaration is re-read from the "
          "live stamp reading")


def emit(lines):
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    lines = []
    with open(DECL, "rb") as handle:
        raw = handle.read()
    text = raw.decode("utf-8")
    lines.append("LIVE REPIN DIALECT R2406 declaration_bytes=%d dialect=%s"
                 % (len(raw), RNP.dialect_of(raw)))

    reading = RDPL.report(DECL, text)
    lines.append("READING %s" % RDPL.one_line(reading))
    same_name, same_payload = RDPL.resolve(raw, text)
    lines.append("SAME-TEXT resolve dialect=%s payload=%d equal_to_file=%s"
                 % (same_name, len(same_payload), same_payload == raw))

    crlf_raw = raw.replace(b"\n", b"\r\n")
    crlf_name, crlf_payload = RDPL.resolve(crlf_raw, text)
    lines.append("CRLF-COPY resolve dialect=%s payload=%d crlf_pairs=%d "
                 "lone_lf=%d"
                 % (crlf_name, len(crlf_payload),
                    crlf_payload.count(b"\r\n"),
                    crlf_payload.count(b"\n") - crlf_payload.count(b"\r\n")))

    proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "residue_triage_repin.py"),
         "--round", "R2406", "--until", "R2416", "--reason", REASON,
         "--root", REPO],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _err = proc.communicate()
    first = out.decode("utf-8", "replace").splitlines()
    lines.append("REAL-CLI rc=%d %s" % (proc.returncode,
                                        first[0] if first else "-"))

    mixed_raw = raw.replace(b"\n", b"\r\n", 3)
    mixed_name = None
    mixed_code = None
    try:
        mixed_name, _payload = RDPL.resolve(mixed_raw, text)
        mixed_name = "NO-REFUSAL"
    except RDPL.RepinDialectError as exc:
        mixed_code = exc.code
    lines.append("MIXED-COPY resolve=%s code=%s refused=%s"
                 % (mixed_name, mixed_code, mixed_code is not None))

    lines.append("VERDICT dialect=%s crlf_kept=%s mixed_refused=%s "
                 "real_noop=%s"
                 % (RNP.dialect_of(raw), crlf_name == "CRLF",
                    mixed_code == "E_RDPL_MIXED",
                    (first[0].split()[2] if first and len(first[0].split()) > 2
                     else "-")))
    emit(lines)
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())