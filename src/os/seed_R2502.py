"""R2502 seed: one measured gap, pinned with criteria, inserted under the
just-closed AC-PLR1 row so the tech floor is back at ten claimable."""

import io
import sys

P = "state/queue/tech.md"
AFTER = "- [x] [done 2026-11-07 R2502] P2 tech seed (R2494,"
SEED = (
    "- [ ] P2 tech seed (R2502, from this window own measured limit): "
    "`src/os/patterns_label_readability_render_consumer.py` - MEASURED this "
    "window while shipping the readability face: `src/sandbox/"
    "suite_matrix.py::load_patterns` reads suite_matrix_patterns.json with "
    "`json.load` and `render()` interpolates every label straight into "
    "docs/sandbox-suite-matrix.md, so the operator's own render command never "
    "asks whether a label is readable - the gate this window shipped only "
    "protects callers that CHOOSE to route through publish(). A patterns file "
    "with one mis-encoded label still renders into the CEO-visible artifact "
    "when the shipped tool is run directly. Product: the render path asks the "
    "shipped readability gate before it composes, refuses with the gate's own "
    "code and the offending label key when a label is suspect, and leaves "
    "every byte of a clean render exactly as today. Criteria AC-PLRC1..AC-PLRC6 "
    "pre-registered HERE BEFORE any code: AC-PLRC1 the refusal comes from the "
    "SHIPPED gate asked at CALL time, proved by patching the gate and watching "
    "the render refuse, never by a second classifier in suite_matrix; "
    "AC-PLRC2 a suspect patterns file refuses 'python src/sandbox/"
    "suite_matrix.py' with the gate's code naming the label key and writes "
    "NO artifact byte (target byte-identical, no residue); AC-PLRC3 a clean "
    "patterns file renders byte-identically to today, proved against the "
    "committed docs/sandbox-suite-matrix.md at its recorded evidence; AC-PLRC4 "
    "--check keeps today's semantics on a clean tree and reports the refusal "
    "distinctly (not as drift) on a suspect one; AC-PLRC5 the label strings "
    "are never rewritten and the patterns digest is unchanged after any run; "
    "AC-PLRC6 pure ASCII, stdlib only, no clock, zero network, own reconcile "
    "label and own suite. Five anchors to re-check zero-occupancy at HEAD "
    "before any code: patterns_label_readability_render_consumer, AC-PLRC, "
    "E_PLRC, os-patterns-label-readability-render-consumer, "
    "test_patterns_label_readability_render_consumer.\n"
)


def main():
    text = io.open(P, encoding="utf-8", newline="").read()
    newline = "\r\n" if "\r\n" in text[:200] else "\n"
    lines = text.split(newline)
    hits = [i for i, row in enumerate(lines) if row.startswith(AFTER)]
    if len(hits) != 1:
        print("FAIL anchor hits=%d" % len(hits))
        return 2
    at = hits[0] + 2  # directly under the row and its DISCHARGED note
    lines.insert(at, SEED.rstrip("\n"))
    payload = newline.join(lines)
    io.open(P, "w", encoding="utf-8", newline="").write(payload)
    back = io.open(P, encoding="utf-8", newline="").read().split(newline)
    ok = back[at].startswith("- [ ] P2 tech seed (R2502,")
    print("seeded_at=%d read_back=%s bytes=%d"
          % (at + 1, ok, len(payload.encode("utf-8"))))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())