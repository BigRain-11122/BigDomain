"""R2539 live leg: the real tree plus the SAME fixture on BOTH readers."""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(os.path.dirname(BASE), "sandbox"))

import probe_seam_name_binding_scope_awareness as P  # noqa: E402
import probe_seam_nested_key_binding_scope as B  # noqa: E402
import suite_matrix as SM  # noqa: E402

FIXTURE = (
    'D = {"a": {"b": ("pnsb_live_helper",)}}\n'
    '\n'
    'def first():\n'
    '    KEY = "b"\n'
    '    for name in D["a"][KEY]:\n'
    '        pass\n'
    '\n'
    'def second():\n'
    '    KEY = "zzz"\n'
    '    for name in D["a"][KEY]:\n'
    '        pass\n'
)


def main():
    report = P.reading(BASE, SM)
    covered = [row for row in report["probes"] if row["verdict"] == "COVERED"]
    loops = sum(len(row["scope_loops"]) for row in report["probes"])
    mine = P.scope_report(FIXTURE)["loops"]
    base = B.nested_report(FIXTURE)
    lines = [
        "tool=%s" % report["tool"],
        "base_tool=%s" % report.get("base_tool"),
        "verdict=%s" % report["verdict"],
        "counts=%s" % json.dumps(report["counts"], sort_keys=True),
        "covered_probes=%d scope_loop_rows=%d probes=%d"
        % (len(covered), loops, len(report["probes"])),
        "MINE=%s" % json.dumps(mine, sort_keys=True),
        "BASE_refused=%s" % json.dumps(base.get("refused"), sort_keys=True),
        "BASE_followed=%s" % json.dumps(base.get("followed"), sort_keys=True),
    ]
    repo = os.path.dirname(os.path.dirname(BASE))
    path = os.path.join(repo, "qa",
                        "probe-seam-name-binding-scope-awareness-live-R2539.log")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if report["verdict"] == P.SEAMS_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())