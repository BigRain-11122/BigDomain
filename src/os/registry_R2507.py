"""R2507 registry writer: wire the new suite row into reconcile_all.SUITES.

One read, one atomic replace, read-back. ASCII source, stdlib only.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
RUNNER = os.path.join(REPO, "src", "sandbox", "reconcile_all.py")

OLD = (
    '    ("os-patterns-non-label-text-readability",\n'
    '     os.path.join("..", "os",\n'
    '                  "test_patterns_non_label_text_readability.py"), 6),\n'
)

NEW = OLD + (
    "    # R2507 (AC-ADTR1..AC-ADTR6, criteria pinned in state/queue/tech.md as\n"
    "    # the R2507 claim row BEFORE the code): both gates above read the\n"
    "    # PATTERNS DOCUMENT, while render also interpolates the registry labels\n"
    "    # and paths and every string billable_faces reads out of each product\n"
    "    # config.json - a registry label carrying U+FFFD rendered straight into\n"
    "    # the CEO-visible artifact while the shipped gate read publishable=True.\n"
    "    # The render now asks ONE reading over that disk-sourced set, derived\n"
    "    # from what the render actually reads, through the same shipped\n"
    "    # per-codepoint law, and refuses at exit 4 naming the SOURCE and the\n"
    "    # field with no artifact byte written.\n"
    '    ("os-artifact-disk-text-readability",\n'
    '     os.path.join("..", "os",\n'
    '                  "test_artifact_disk_text_readability.py"), 6),\n'
)


def main():
    text = io.open(RUNNER, encoding="utf-8").read()
    before = len(text.encode("utf-8"))
    if "os-artifact-disk-text-readability" in text:
        print("NOOP already wired")
        return 0
    if text.count(OLD) != 1:
        print("FAIL anchor: %d matches" % text.count(OLD))
        return 2
    payload = text.replace(OLD, NEW)
    with io.open(RUNNER, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = io.open(RUNNER, encoding="utf-8").read()
    ok = ('"os-artifact-disk-text-readability",' in back
          and 'test_artifact_disk_text_readability.py"), 6),' in back)
    print("runner %s predicted=%d measured=%d delta=%d"
          % ("OK" if ok else "FAIL", len(payload.encode("utf-8")),
             len(back.encode("utf-8")),
             len(back.encode("utf-8")) - before))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())