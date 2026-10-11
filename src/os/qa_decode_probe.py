"""QA evidence-file decodability probe (BigDomain P2 tech-queue item
"qa evidence-file decodability probe window", R1781; seed = R1774
bad-file skip-gate widening to the ValueError family, claim row in
state/queue/tech.md registers AC-QD1..AC-QD7 BEFORE this code).

What this tool answers: qa/ evidence logs carry two writer dialects
(runner utf-8 tee vs PowerShell 5.1 UTF-16LE redirection, R1683). A
mixed-dialect file (UTF-16LE base with appended non-UTF16 sections)
cannot be decoded; the suite_matrix discovery face skips it as not
evidence-eligible (fail-closed, R1774 widening). This probe makes
the decodability census mechanically re-runnable on ANY directory:

    python qa_decode_probe.py                 # live qa/ census
    python qa_decode_probe.py --dir PATH      # any evidence dir
    python qa_decode_probe.py --selftest      # sandbox fixtures

The decode/eligibility faces are imported live from src/sandbox/
suite_matrix.py (single source of truth, reference never copy); this
probe only reads directories and never writes inside any qa/ dir.

Pre-registered decision rule (AC-QD5):
  * zero *.log in target dir -> NO-ELIGIBLE refusal exit 3
    (R1727 AC-LN5 family);
  * every file decodable -> ALL-DECODABLE exit 0;
  * undecodable files present -> UNDECODABLE-NAMED exit 0 ONLY IF
    every undecodable file is ALSO gate-skipped (SM._evidence_eligible
    == False, i.e. skip = cannot serve as evidence); any undecodable
    file that comes back eligible is a discovery-gate gap -> FAIL
    exit 2 (fail-closed).
Exit codes: 0 all assertions pass; 2 assertion/gate failure; 3 no
eligible target files (refusal, not a failure).

Evidence: qa/qa-decode-probe-R1781.log (selftest + live sections).
"""

import argparse
import io
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))   # .../src/os
SRC = os.path.dirname(BASE)                          # .../src
ROOT = os.path.dirname(SRC)                          # repo root
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, SANDBOX)
import suite_matrix as SM  # decode/eligibility, single source of truth

NET_IMPORTS = ("urllib", "requests", "socket", "http", "ftplib",
               "xmlrpc", "smtplib", "asyncio")
QA_DIR = os.path.join(ROOT, "qa")


def _bom_of(raw):
    """BOM dialect census (display face only; the decode face stays
    inside suite_matrix.read_text - single source of truth)."""
    if raw.startswith(b"\xff\xfe"):
        return "utf-16le"
    if raw.startswith(b"\xfe\xff"):
        return "utf-16be"
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    return "utf-8"  # presumed (no BOM on disk)


def probe_dir(target):
    """Read-only decodability census of one directory. Returns
    (report_lines, exit_code, summary). Zero writes, zero
    fabrication: every number is measured or honestly absent."""
    names = sorted(n for n in os.listdir(target) if n.endswith(".log"))
    lines = []
    if not names:
        lines.append("no *.log candidates under target dir (refusal)")
        return lines, 3, {"file_count": 0, "decodable": 0,
                          "undecodable": 0}
    lines.append("file_count=%d" % len(names))
    bad = []
    decodable = 0
    for name in names:
        path = os.path.join(target, name)
        try:
            with open(path, "rb") as handle:
                raw = handle.read()
            bom = _bom_of(raw)
            reason = ""
            brk = None
            try:
                SM.read_text(path)
                ok = True
                decodable += 1
            except UnicodeDecodeError as exc:
                ok = False
                reason = "UnicodeDecodeError:%s" % exc.reason
                brk = exc.start
            except OSError as exc:
                ok = False
                reason = "OSError:%s" % exc.__class__.__name__
            size = len(raw)
        except OSError as exc:
            ok = False
            bom = "?"
            reason = "OSError:%s" % exc.__class__.__name__
            brk = None
            size = -1
        if ok:
            lines.append("[ok] %s bytes=%d bom=%s decodable=yes"
                         % (name, size, bom))
        else:
            lines.append("[BAD] %s bytes=%d bom=%s decodable=no"
                         " reason=%s break_offset=%s"
                         % (name, size, bom, reason,
                            brk if brk is not None else "n/a"))
            bad.append((name, path, reason, brk))
    summary = {"file_count": len(names), "decodable": decodable,
               "undecodable": len(bad)}
    lines.append("decodable=%d undecodable=%d"
                 % (decodable, len(bad)))
    if not bad:
        lines.append("verdict: ALL-DECODABLE")
        return lines, 0, summary
    # gate cross-verification: every undecodable file must be
    # evidence-ineligible (skip = cannot serve as evidence)
    gap = False
    for name, path, reason, brk in bad:
        try:
            eligible = bool(SM._evidence_eligible(path))
        except Exception as exc:  # gate itself crashing = gap face
            eligible = True
            reason += " gate-crashed:%s" % exc.__class__.__name__
        if eligible:
            gap = True
            lines.append("GATE-GAP %s undecodable BUT eligible"
                         " (discovery face would use a file that"
                         " cannot decode)" % name)
        else:
            lines.append("gate-cross %s eligible=False"
                         " (skipped, not evidence)" % name)
        if name.startswith("suite-matrix-"):
            lines.append("note %s outside default-face candidate"
                         " set (self-evidence prefix skip)" % name)
    if gap:
        lines.append("verdict: FAIL gate-gap (see GATE-GAP rows)")
        return lines, 2, summary
    lines.append("verdict: UNDECODABLE-NAMED (%d bad, all"
                 " gate-skipped)" % len(bad))
    return lines, 0, summary


def _hygiene_lines():
    out = []
    with io.open(os.path.abspath(__file__), "r", encoding="ascii",
                 errors="strict") as handle:
        src = handle.read()
    out.append("self-ascii: PASS (%d bytes)" % len(src.encode("ascii")))
    bad_imports = [mod for mod in NET_IMPORTS
                   if any(line.strip().startswith("import %s" % mod)
                          or ("import" in line and mod in line
                              and line.strip().startswith("from"))
                          for line in src.splitlines())]
    out.append("self-net-imports: %s" % ("NONE (PASS)" if not bad_imports
                                         else "FAIL %s" % bad_imports))
    return out, (0 if not bad_imports else 2)


def _selftest():
    """Sandbox fixtures, >= 10 assertions (AC-QD6)."""
    checks = []

    def check(label, cond):
        checks.append((label, bool(cond)))

    tmp = tempfile.mkdtemp(prefix="qa-decode-probe-")
    try:
        # fixture dialects
        healthy = os.path.join(tmp, "healthy")
        os.mkdir(healthy)
        with open(os.path.join(healthy, "utf8-clean.log"), "wb") as fh:
            fh.write("PASS runner ok\nsuite rows here\n".encode("utf-8"))
        with open(os.path.join(healthy, "utf8bom.log"), "wb") as fh:
            fh.write(b"\xef\xbb\xbf" +
                     "PASS runner ok\nsuite rows here\n".encode("utf-8"))
        with open(os.path.join(healthy, "u16le-clean.log"), "wb") as fh:
            fh.write(b"\xff\xfe" +
                     "hello utf16le world\n".encode("utf-16-le"))
        mixed = os.path.join(tmp, "mixed")
        os.mkdir(mixed)
        base = b"\xff\xfe" + "healthy base text\n".encode("utf-16-le")
        with open(os.path.join(mixed, "utf8-clean.log"), "wb") as fh:
            fh.write("PASS runner ok\n".encode("utf-8"))
        with open(os.path.join(mixed, "mixed-dialect.log"), "wb") as fh:
            # odd-byte tail after an even UTF-16LE base = the real
            # mixed-dialect failure mode (live anchor: lobby-roomboard
            # -R1773.log, 7077 bytes, truncated at 7076)
            fh.write(base + b"appended-utf8")
        # 1-3: three healthy dialects decodable with BOM census
        lines1, code1, s1 = probe_dir(healthy)
        check("three healthy dialects ALL-DECODABLE",
              code1 == 0 and "ALL-DECODABLE" in "\n".join(lines1))
        check("census counts all files (3/3)",
              s1["file_count"] == 3 and s1["decodable"] == 3)
        check("bom census utf-16le named",
              "bom=utf-16le" in "\n".join(lines1)
              and "bom=utf-8-sig" in "\n".join(lines1)
              and "bom=utf-8" in "\n".join(lines1))
        # 4-5: mixed dialect undecodable + break offset
        lines2, code2, s2 = probe_dir(mixed)
        blob2 = "\n".join(lines2)
        check("mixed dir UNDECODABLE-NAMED",
              code2 == 0 and "UNDECODABLE-NAMED" in blob2)
        check("mixed-dialect file named with break offset",
              "[BAD] mixed-dialect.log" in blob2
              and "break_offset=" in blob2
              and "UnicodeDecodeError" in blob2)
        bad_row = [l for l in lines2 if l.startswith("[BAD]")
                   and "mixed-dialect" in l][0]
        brk = int(bad_row.split("break_offset=")[1].split()[0])
        check("break offset lands at/after base section",
              brk >= len(base))
        check("gate cross: undecodable file skipped",
              "gate-cross mixed-dialect.log eligible=False" in blob2)
        # 6: gate-gap negative path (patched eligibility bypass)
        real_elig = SM._evidence_eligible
        SM._evidence_eligible = lambda path: True
        try:
            lines3, code3, _s3 = probe_dir(mixed)
            check("gate-gap negative path caught (FAIL exit 2)",
                  code3 == 2 and "GATE-GAP" in "\n".join(lines3))
        finally:
            SM._evidence_eligible = real_elig
        # 7: empty dir refusal
        empty = os.path.join(tmp, "empty")
        os.mkdir(empty)
        _le, code_empty, _se = probe_dir(empty)
        check("empty dir refusal exit 3", code_empty == 3)
        # 8: read-only law - fixture dir census identical after reprobe
        lines4, code4, s4 = probe_dir(mixed)
        check("reprobe deterministic (identical census)",
              (lines4, code4, s4) == (lines2, code2, s2))
        # 9: hygiene faces
        hy, hy_code = _hygiene_lines()
        check("hygiene ascii+net-imports clean", hy_code == 0)
        # 10: probe never wrote inside target dirs (fixture dirs
        # still hold exactly the files we created)
        check("zero writes into probed dirs",
              sorted(os.listdir(mixed)) ==
              ["mixed-dialect.log", "utf8-clean.log"])
    finally:
        for sub in os.listdir(tmp):
            d = os.path.join(tmp, sub)
            if os.path.isdir(d):
                for f in os.listdir(d):
                    os.unlink(os.path.join(d, f))
                os.rmdir(d)
            else:
                os.unlink(d)
        os.rmdir(tmp)
    ok = sum(1 for _l, c in checks if c)
    print("selftest: %d/%d checks pass" % (ok, len(checks)))
    for label, cond in checks:
        print("  [%s] %s" % ("ok" if cond else "FAIL", label))
    return 0 if ok == len(checks) else 2, checks


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="qa evidence-file decodability probe (R1781)")
    parser.add_argument("--dir", default=QA_DIR,
                        help="target evidence dir (default live qa/)")
    parser.add_argument("--selftest", action="store_true",
                        help="run sandbox fixtures")
    args = parser.parse_args(argv)
    print("probe: qa decode census (BigDomain R1781 AC-QD)")
    if args.selftest:
        code, _checks = _selftest()
        hy, hy_code = _hygiene_lines()
        for line in hy:
            print(line)
        return code or hy_code
    target = os.path.abspath(args.dir)
    print("dir: %s" % target)
    lines, code, summary = probe_dir(target)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
