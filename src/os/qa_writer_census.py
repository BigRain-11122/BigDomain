"""QA evidence-file writer-mode census probe (BigDomain P2 tech-queue
item "reconcile_all no-argv shell-capture self-label + daily chain
dialect mutual-proof window", R1836; seed = the R1827 three-state
writer archaeology + qa_decode_probe canon, claim row in
state/queue/tech.md registers AC-SL3 BEFORE this code).

What this tool answers: qa/ evidence logs have been written by three
writer families (R1827 archaeology) - raw cmd/PowerShell redirection
(CRLF + raw cp936 bytes), PowerShell re-encoding capture (CRLF +
utf-8-decodable but mojibake-prone), and the runner's utf-8 Tee
(utf-8 + LF). Since R1836 a no-argv reconcile_all run also prints the
SHELL_CAPTURE_LABEL first line, so future shell-captured files are
self-announcing. This probe mechanically classifies EVERY *.log in a
directory by writer-dialect signature and counts the three states:

    python qa_writer_census.py                 # live qa/ census
    python qa_writer_census.py --dir PATH      # any evidence dir
    python qa_writer_census.py --selftest      # sandbox fixtures

Classification rule (pre-registered AC-SL3, mechanical and total):
  * BOM utf-16le/utf-16be            -> ps-utf16    (PS 5.1 `>` family)
  * no BOM + crlf==0 + strict utf-8  -> tee         (LF + utf-8 dialect)
  * no BOM + crlf-dominant (crlf > bare_lf) + strict utf-8 FAILS
                                     -> cmd-raw     (raw cp936 family)
  * no BOM + crlf-dominant + strict utf-8 OK
                                     -> pwsh-capture (re-encode family)
  * anything else (utf-8-sig BOM, mixed EOL with LF majority,
    unreadable files, empty degenerate-noted rows)
                                     -> other      (honest catch-all,
                                                    named per file)
The label column reports label=yes when the first physical line is
byte-equal to reconcile_all.SHELL_CAPTURE_LABEL (single source,
imported - never copied; trailing EOL tolerated).

Exit codes: 0 census complete (every file classified, including the
honest "other" bucket); 3 no *.log candidates under target dir
(refusal family, R1727 AC-LN5 / qa_decode_probe AC-QD5 precedent).
This probe is a measurement face (R1727 precedent): it is NOT
registered in the reconcile_all SUITES table, reads directories only,
and never writes inside any qa/ dir.

Evidence: qa/selflabel-chain-R1836.log (selftest + live sections).
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
sys.path.insert(0, BASE)

import qa_decode_probe as QDP       # BOM face, single source
import reconcile_all as RA          # SHELL_CAPTURE_LABEL, single source

NET_IMPORTS = ("urllib", "requests", "socket", "http", "ftplib",
               "xmlrpc", "smtplib", "asyncio")
QA_DIR = os.path.join(ROOT, "qa")
LABEL = RA.SHELL_CAPTURE_LABEL
CLASSES = ("tee", "cmd-raw", "pwsh-capture", "ps-utf16", "other")


def classify_file(path):
    """Read-only writer-signature census of one file. Returns a row
    dict; every number is measured or honestly absent - zero
    fabrication."""
    row = {"name": os.path.basename(path), "bytes": -1, "bom": "?",
           "crlf": 0, "bare_lf": 0, "utf8": False, "label": False,
           "class": "other", "err": ""}
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        row["err"] = "OSError:%s" % exc.__class__.__name__
        return row
    row["bytes"] = len(raw)
    row["bom"] = QDP._bom_of(raw)
    row["crlf"] = raw.count(b"\r\n")
    row["bare_lf"] = raw.count(b"\n") - row["crlf"]
    try:
        raw.decode("utf-8", "strict")
        row["utf8"] = True
    except UnicodeDecodeError:
        row["utf8"] = False
    # label column: first physical line, trailing EOL tolerated
    first = raw.split(b"\n", 1)[0]
    if first.endswith(b"\r"):
        first = first[:-1]
    row["label"] = (first == LABEL.encode("ascii"))
    # classification rule (pre-registered; mechanical and total)
    if row["err"]:
        row["class"] = "other"
    elif row["bom"] in ("utf-16le", "utf-16be"):
        row["class"] = "ps-utf16"
    elif row["bom"] == "utf-8-sig":
        row["class"] = "other"
    elif row["crlf"] == 0:
        row["class"] = "tee" if row["utf8"] else "other"
    elif row["crlf"] > row["bare_lf"]:
        # CRLF-dominant: re-encoding capture vs raw redirect
        row["class"] = "pwsh-capture" if row["utf8"] else "cmd-raw"
    else:
        row["class"] = "other"   # mixed EOL without CRLF majority
    return row


def probe_dir(target):
    """Read-only writer census of one directory. Returns (lines,
    exit_code, summary). Zero writes, zero fabrication."""
    names = sorted(n for n in os.listdir(target) if n.endswith(".log"))
    lines = []
    if not names:
        lines.append("no *.log candidates under target dir (refusal)")
        return lines, 3, {"file_count": 0,
                          "counts": dict((c, 0) for c in CLASSES)}
    lines.append("file_count=%d" % len(names))
    counts = dict((c, 0) for c in CLASSES)
    labeled = 0
    for name in names:
        row = classify_file(os.path.join(target, name))
        counts[row["class"]] += 1
        if row["label"]:
            labeled += 1
        if row["err"]:
            lines.append("[err] %s bytes=%d reason=%s"
                         % (name, row["bytes"], row["err"]))
        else:
            lines.append("[%s] %s bytes=%d bom=%s crlf=%d bare_lf=%d "
                         "utf8=%s label=%s"
                         % (row["class"], name, row["bytes"], row["bom"],
                            row["crlf"], row["bare_lf"],
                            "yes" if row["utf8"] else "no",
                            "yes" if row["label"] else "no"))
    lines.append("counts: " + " ".join("%s=%d" % (c, counts[c])
                                        for c in CLASSES))
    lines.append("labeled_selfannounced=%d" % labeled)
    lines.append("total=%d" % len(names))
    lines.append("verdict: CENSUS-COMPLETE (all %d files classified, "
                 "other=%d honest bucket)" % (len(names), counts["other"]))
    return lines, 0, {"file_count": len(names), "counts": counts,
                      "labeled": labeled}


def _hygiene_lines():
    out = []
    with io.open(os.path.abspath(__file__), "r", encoding="ascii",
                 errors="strict") as handle:
        src = handle.read()
    out.append("self-ascii: PASS (%d bytes)" % len(src.encode("ascii")))
    bad_imports = [mod for mod in NET_IMPORTS
                   if any(line.strip().startswith("import %s" % mod)
                          or (line.strip().startswith("from")
                              and mod in line)
                          for line in src.splitlines())]
    out.append("self-net-imports: %s" % ("NONE (PASS)" if not bad_imports
                                         else "FAIL %s" % bad_imports))
    return out, (0 if not bad_imports else 2)


def _selftest():
    """Sandbox fixtures (AC-SL3, >= 8 assertions)."""
    checks = []

    def check(label, cond):
        checks.append((label, bool(cond)))

    tmp = tempfile.mkdtemp(prefix="qa-writer-census-")
    try:
        fx = os.path.join(tmp, "fixtures")
        os.mkdir(fx)
        # 1 tee dialect: utf-8 + LF
        with open(os.path.join(fx, "tee-like.log"), "wb") as fh:
            fh.write("PASS suite ledger exit=0\n".encode("utf-8"))
        # 2 cmd-raw dialect: CRLF + raw cp936 (undecodable as utf-8)
        with open(os.path.join(fx, "cmd-raw-like.log"), "wb") as fh:
            fh.write(u"AI \u5224\u5b9a".encode("gbk") + b"\r\n"
                     + b"PASS suite row\r\n")
        # 3 pwsh-capture dialect: CRLF + valid utf-8
        with open(os.path.join(fx, "pwsh-like.log"), "wb") as fh:
            fh.write(u"AI \u5224\u5b9a".encode("utf-8") + b"\r\n"
                     + b"PASS suite row\r\n")
        # 4 PS 5.1 redirection: UTF-16LE with BOM
        with open(os.path.join(fx, "ps-utf16.log"), "wb") as fh:
            fh.write(b"\xff\xfe" + "hello utf16le\n".encode("utf-16-le"))
        # 5 self-labeled shell-capture file: label first line + CRLF
        with open(os.path.join(fx, "labeled-capture.log"), "wb") as fh:
            fh.write(LABEL.encode("ascii") + b"\r\n"
                     + u"AI \u5224\u5b9a".encode("utf-8") + b"\r\n")
        # 6 utf-8-sig BOM -> honest other bucket
        with open(os.path.join(fx, "utf8bom.log"), "wb") as fh:
            fh.write(b"\xef\xbb\xbf" + "PASS suite row\n".encode("utf-8"))
        # 7 mixed EOL, LF majority -> honest other bucket
        with open(os.path.join(fx, "mixed-eol.log"), "wb") as fh:
            fh.write("l1\nl2\nl3\nl4\r\n".encode("utf-8"))
        # 8 empty degenerate: mechanically tee-by-rule, bytes=0 noted
        open(os.path.join(fx, "empty.log"), "wb").close()
        lines, code, summary = probe_dir(fx)
        blob = "\n".join(lines)
        check("refusal not triggered (8 fixtures)", code == 0
              and summary["file_count"] == 8)
        check("tee dialect named", "[tee] tee-like.log" in blob)
        check("cmd-raw dialect named (utf8=no)",
              "[cmd-raw] cmd-raw-like.log" in blob
              and "utf8=no" in blob)
        check("pwsh-capture dialect named",
              "[pwsh-capture] pwsh-like.log" in blob)
        check("ps-utf16 named", "[ps-utf16] ps-utf16.log" in blob)
        check("labeled capture self-announces (label=yes)",
              "labeled-capture.log" in blob and "label=yes" in blob
              and summary["labeled"] == 1)
        check("utf-8-sig and mixed-EOL land in other bucket",
              "[other] utf8bom.log" in blob
              and "[other] mixed-eol.log" in blob
              and summary["counts"]["other"] == 2)
        check("empty degenerate honest row (bytes=0, tee-by-rule)",
              "[tee] empty.log bytes=0" in blob)
        check("counts sum == file count",
              sum(summary["counts"].values()) == 8)
        # 9 refusal: empty dir
        empty = os.path.join(tmp, "empty-dir")
        os.mkdir(empty)
        _le, code_empty, _se = probe_dir(empty)
        check("empty dir refusal exit 3", code_empty == 3)
        # 10 read-only law + determinism: identical re-census
        lines2, code2, summary2 = probe_dir(fx)
        check("reprobe deterministic (identical census)",
              (lines2, code2, summary2) == (lines, code, summary))
        # 11 zero writes into probed dirs
        check("zero writes into probed dirs",
              sorted(os.listdir(fx)) ==
              ["cmd-raw-like.log", "empty.log", "labeled-capture.log",
               "mixed-eol.log", "ps-utf16.log", "pwsh-like.log",
               "tee-like.log", "utf8bom.log"])
        # 12 hygiene faces
        hy, hy_code = _hygiene_lines()
        check("hygiene ascii+net-imports clean", hy_code == 0)
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
    return (0 if ok == len(checks) else 2), checks


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="qa evidence writer-mode census (R1836 AC-SL3)")
    parser.add_argument("--dir", default=QA_DIR,
                        help="target evidence dir (default live qa/)")
    parser.add_argument("--selftest", action="store_true",
                        help="run sandbox fixtures")
    args = parser.parse_args(argv)
    print("probe: qa writer-mode census (BigDomain R1836 AC-SL3)")
    if args.selftest:
        code, _checks = _selftest()
        hy, hy_code = _hygiene_lines()
        for line in hy:
            print(line)
        return code or hy_code
    target = os.path.abspath(args.dir)
    print("dir: %s" % target)
    lines, code, _summary = probe_dir(target)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
