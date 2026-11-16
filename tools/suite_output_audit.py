"""Output-level audit: which registered suites ACTUALLY emit the battery row?

The census (tools/suite_closing_row_census.py) reads format literals in SOURCE,
so it can be wrong in both directions: a suite that builds its closing row in a
helper module reads as non_law, and a suite that carries a law literal on a
branch that never runs reads as law. This audit answers the same question from
BEHAVIOUR: it runs a bounded slice through the runner's own invocation and
classifies each suite by the row it really printed.

Two single authorities, neither copied:
  * the law is tools/battery_shard.py SUITE_LINE (imported, never re-written);
  * the family label is tools/suite_closing_row_census.py classify() (the
    census stays the classification authority; this tool only re-asks it at
    output level).
The suite invocation is battery_shard.run_one(), so the audit runs a suite the
same way a leg does (same cwd, same env, same per-suite cap and overrides).

Read-only: it writes nothing except the optional evidence file, which goes
through the runner's own write_evidence. stdlib only, no network, no clock
literal.

Usage:
  python tools/suite_output_audit.py --family no_status --per-family-limit 20
  python tools/suite_output_audit.py --family no_status --family no_numbers \
      --family other --per-family-limit 20 --evidence closing-row-audit-R2845.log
"""
import argparse
import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAMILIES = ("law_direct", "law_status", "law_split", "law_numeric",
            "law_numeric_slot", "suspect_status", "no_status",
            "legacy_paren", "legacy_label", "legacy_status_colon",
            "no_numbers", "legacy_lower", "other", "no_row")
ROW_RE = re.compile(r"(?m)^SUITE\b.*$")


def load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


def shipped(root):
    """Runner and census, imported from the tree under audit."""
    runner = load(os.path.join(root, "tools", "battery_shard.py"), "_soa_runner")
    census = load(os.path.join(root, "tools", "suite_closing_row_census.py"),
                  "_soa_census")
    return runner, census


def closing_row(runner, out):
    """The real SUITE line this suite printed, or None. Law, not a copy.

    The law is the runner's own reader: parse_suite_row, which accepts an
    explicit verdict word and derives one from a numbers-only row. Asking
    SUITE_LINE alone would report a row the runner honours as debt.
    """
    m = runner.SUITE_LINE.search(out or "")
    if m:
        return m.group(0).strip()
    rows = runner.SUITE_LINE_NUM.findall(out or "")
    if rows:
        return ("SUITE " + rows[-1][0] + "/" + rows[-1][1]).strip()
    tail = [ln.strip() for ln in (out or "").splitlines() if ROW_RE.match(ln.strip())]
    return tail[-1] if tail else "none"


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--family", action="append", default=[])
    ap.add_argument("--per-family-limit", type=int, default=0)
    ap.add_argument("--evidence", default="")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    runner, census = shipped(root)
    if args.evidence:
        runner.evidence_name(args.evidence)

    families = args.family or ["no_status", "no_numbers", "other"]
    bad = [f for f in families if f not in FAMILIES]
    if bad:
        print("E_SOA_BAD_FAMILY %s known=%s" % (bad[0], "|".join(FAMILIES)))
        return 2

    rows, base, cap, overrides = runner.registry()
    by_family = {}
    for label, rel, crit in rows:
        path = os.path.join(root, "src", "sandbox", rel)
        if not os.path.isfile(path):
            by_family.setdefault("missing_file", []).append((label, rel, crit))
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            fam = census.classify(fh.read())
        by_family.setdefault(fam, []).append((label, rel, crit))

    lines = []
    print("AUDIT note=OUTPUT-LEVEL registry=%d cap=%ds families=%s"
          % (len(rows), cap, ",".join(families)))
    total_sel = total_law = total_red = 0
    for fam in families:
        picked = by_family.get(fam, [])
        if args.per_family_limit:
            picked = picked[:args.per_family_limit]
        law_emit = red = 0
        for label, rel, crit in picked:
            code, out, secs = runner.run_one(base, label, rel, cap, overrides)
            row = closing_row(runner, out)
            is_law = runner.parse_suite_row(out or "") is not None
            law_emit += 1 if is_law else 0
            red += 1 if code != 0 else 0
            line = ("AUDIT row label=%s family=%s rc=%d law=%s row=%s crit=%d %.1fs"
                    % (label, fam, code, "yes" if is_law else "no", row, crit, secs))
            print(line)
            lines.append(line)
        non_law = len(picked) - law_emit
        head = ("AUDIT family=%s total=%d selected=%d law_emit=%d non_law=%d red=%d"
                % (fam, len(by_family.get(fam, [])), len(picked), law_emit,
                   non_law, red))
        print(head)
        lines.append(head)
        total_sel += len(picked)
        total_law += law_emit
        total_red += red

    closing = ("AUDIT TOTAL selected=%d law_emit=%d non_law=%d red=%d families=%d"
               % (total_sel, total_law, total_sel - total_law, total_red,
                  len(families)))
    print(closing)
    lines.append(closing)
    if args.evidence:
        proof = runner.write_evidence(runner.evidence_name(args.evidence),
                                      "\n".join(lines) + "\n")
        print("AUDIT evidence name=%s bytes=%d lines=%d sha256=%s dialect=utf-8/lf"
              % (runner.evidence_name(args.evidence), proof["bytes"],
                 proof["lines"], proof["sha256"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
