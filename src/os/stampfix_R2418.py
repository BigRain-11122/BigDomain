"""R2418: give every stand-in matrix doc a REAL stamp line.

The matrix section now refuses a doc with no stamp line (E_MSC_NO_STAMP), so
a fixture that writes a bare b"MATRIX\\n" would only prove the refusal. The
line is taken from the shipped doc through the law, never spelled here.
"""
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

NESTED_DOC_CALL = 'handle.write(b"MATRIX\\n")'

HELPER = '''
REPO_DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")


def stamp_line():
    """R2418: a stand-in doc must carry a real stamp line, taken through the
    law rather than spelled here, because the matrix section now refuses a doc
    with none (E_MSC_NO_STAMP)."""
    verdict, _code, stamp, _detail = MSC.stamp_of(REPO_DOC)
    if verdict != MSC.PASS or not stamp:
        return None
    with io.open(REPO_DOC, "r", encoding="utf-8") as handle:
        for line in handle.read().split("\\n"):
            if stamp in line:
                return line
    return None


STAMP_LINE = stamp_line()
'''

TARGETS = (
    "test_battery_followup_help_wire.py",
    "test_followup_guard_evidence_scope.py",
    "test_matrix_evidence_pile_consistency.py",
)


def patch(name):
    path = os.path.join(BASE, name)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "STAMP_LINE" in text:
        print("%s already carries a stamp line" % name)
        return 0
    if 'DOC_BYTES = b"MATRIX\\n"' in text:
        text = text.replace('DOC_BYTES = b"MATRIX\\n"',
                            'DOC_BYTES = (("%s\\nMATRIX\\n" % STAMP_LINE)\n'
                            '             if STAMP_LINE else "MATRIX\\n")'
                            '.encode("utf-8")', 1)
    elif NESTED_DOC_CALL in text:
        text = text.replace(NESTED_DOC_CALL,
                            'handle.write((("%s\\nMATRIX\\n" % STAMP_LINE)\n'
                            '                  if STAMP_LINE else "MATRIX\\n")'
                            '.encode("utf-8"))', 1)
    else:
        print("%s: no doc fixture anchor" % name)
        return 2
    anchor = "import runner_arg_guard as RAG  # noqa: E402\n"
    if anchor not in text:
        anchor = None
        hits = re.findall(r"(?m)^import \w+ as \w+  # noqa: E402\n", text)
        if not hits:
            print("%s: no import anchor" % name)
            return 2
        anchor = hits[-1]
        text = text.replace(anchor, anchor + "import matrix_stamp_compare as MSC  # noqa: E402\n", 1)
    else:
        text = text.replace(anchor, anchor + "import matrix_stamp_compare as MSC  # noqa: E402\n", 1)
    marker = 'LABEL = "'
    index = text.find(marker)
    end = text.find("\n", index)
    text = text[:end + 1] + HELPER.strip() + "\n\n" + text[end + 1:]
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("%s patched" % name)
    return 0


def main():
    bad = 0
    for name in TARGETS:
        bad |= patch(name)
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main())