"""R2418: the evidence capture was re-run after five adjacent suites needed a
real stamp line in their stand-in docs, so every face that quoted the first
capture (legs=2 adjacent=1) is corrected to the final one (adjacent=5), and the
ripple is named rather than left to be discovered next window.
"""
import io
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
OLD = "legs=2 identical=True adjacent=1 fails=0"
NEW = "legs=2 identical=True adjacent=5 fails=0"

FILES = [
    os.path.join(ROOT, "src", "os", "state.json"),
    os.path.join(ROOT, "state", "queue", "tech.md"),
    os.path.join(ROOT, "docs", "status-export.json"),
    os.path.join(ROOT, "src", "os", "backlog.md"),
]

RIPPLE = (
    " Five further stand-in docs across the tree also had to carry a real"
    " stamp line (battery_followup_help_wire, followup_guard_evidence_scope,"
    " matrix_evidence_pile_consistency, followup_section_foreign_wire and the"
    " battery_followup suite itself) - measured, not guessed: each one read"
    " E_MSC_NO_STAMP through the new refusal until its fixture asked the"
    " shipped doc for the line, and all five then read SUITE PASS 6/6.")


def main():
    for path in FILES:
        with io.open(path, "r", encoding="utf-8", newline="") as handle:
            text = handle.read()
        hits = text.count(OLD)
        if not hits:
            print("%s: no anchor" % os.path.basename(path))
            continue
        text = text.replace(OLD, NEW)
        if path.endswith("state.json"):
            anchor = NEW + "),"
            if anchor in text:
                text = text.replace(anchor, NEW + "." + RIPPLE + "\"),", 1)
        with io.open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        print("%s: %d corrected" % (os.path.basename(path), hits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())