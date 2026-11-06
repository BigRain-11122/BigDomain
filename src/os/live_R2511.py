"""R2511 live leg: the real tree reads CLEAN, a doctored value is refused."""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SANDBOX = os.path.join(ROOT, "src", "sandbox")
sys.path.insert(0, HERE)
sys.path.insert(0, SANDBOX)

import stamp_text_coverage as STPT  # noqa: E402
import suite_matrix as SM  # noqa: E402

PATTERNS = os.path.join(SANDBOX, "suite_matrix_patterns.json")
DOC = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
OUT = os.path.join(ROOT, "qa", "stamp-text-coverage-live-R2511.log")
BREAK = "\ufffd"


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


document = json.loads(read_text(PATTERNS))
text = read_text(DOC)
stamp = SM.doc_stamp(text, document)
source = SM.MSPL.recorded_source(text, document["labels"])
before = [digest(PATTERNS), digest(DOC)]

lines = ["LIVE round=R2511 stamp=%r borrow=%r" % (stamp, source)]
clean = STPT.reading(document, stamp, source)
lines.append("CLEAN leg: %s" % STPT.render(clean).replace("\n", " | "))
doctored = STPT.reading(document, stamp[:4] + BREAK + stamp[4:], source)
lines.append("DOCTORED stamp leg: %s" % STPT.render(doctored).replace("\n",
                                                                     " | "))
doctored2 = STPT.reading(document, stamp,
                         str(source)[:-4] + BREAK + ".log")
lines.append("DOCTORED stamp_from leg: %s"
             % STPT.render(doctored2).replace("\n", " | "))
after = [digest(PATTERNS), digest(DOC)]
lines.append("digests_unchanged=%s clean=%s refused=%s other_refused=%s"
             % (before == after, clean["publishable"],
                not doctored["publishable"], not doctored2["publishable"]))
payload = "\n".join(lines) + "\n"
io.open(OUT, "w", encoding="utf-8", newline="\n").write(payload)
print(payload)