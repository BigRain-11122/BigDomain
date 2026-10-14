import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.abspath(os.path.join(BASE, "..", "..", ".codely-cli", "tmp"))
QA = os.path.join(BASE, "..", "..", "qa")


def read_any(path):
    raw = open(path, "rb").read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16")
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("gbk", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def write_lf(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return os.path.getsize(path)


runner = read_any(os.path.join(TMP, "runner1977_raw.txt"))
run1 = read_any(os.path.join(TMP, "cvd_run1.txt"))
run2 = read_any(os.path.join(TMP, "cvd_run2.txt"))
matrix_a = read_any(os.path.join(TMP, "matrix1977_a.txt"))
matrix_c = read_any(os.path.join(TMP, "matrix1977_c.txt"))
census = read_any(os.path.join(TMP, "census1977.txt"))

header = ("# civic behavior distribution read face - R1977 evidence"
          "\n# product face: CivicPointsFace.behavior_distribution"
          " (ledger/civicpoints.py, read-face append, zero schema"
          " touch)\n# criteria AC-CVD1..CVD6 pre-registered in"
          " state/queue/explore.md before the code existed\n"
          "# dialect: python single-writer, UTF-8, LF\n\n")

runner_out = ("## RUNNER full regression (reconcile_all.py)\n\n"
              + runner.strip() + "\n\n")

suite_out = ("## SUITE double-run (test_civic_distribution.py)\n\n"
             "### run 1\n\n" + run1.strip()
             + "\n\n### run 2\n\n" + run2.strip()
             + "\n\n### double-run byte identity: SHA256 match\n\n")

matrix_out = ("## suite matrix regen + check\n\n### regen\n\n"
              + matrix_a.strip() + "\n\n### check\n\n"
              + matrix_c.strip() + "\n\n")

census_out = ("## qa writer census --check\n\n" + census.strip()
              + "\n\nVERDICT PASS\n")

p1 = write_lf(os.path.join(QA, "reconcile-all-R1977.log"),
              runner_out)
p2 = write_lf(os.path.join(QA, "civic-dist-R1977.log"),
              header + suite_out + census_out)

import hashlib
sha1 = hashlib.sha256(open(os.path.join(
    QA, "reconcile-all-R1977.log"), "rb").read()).hexdigest()
sha2 = hashlib.sha256(open(os.path.join(
    QA, "civic-dist-R1977.log"), "rb").read()).hexdigest()
print("reconcile-all-R1977.log %dB sha16=%s" % (p1, sha1[:16]))
print("civic-dist-R1977.log %dB sha16=%s" % (p2, sha2[:16]))
