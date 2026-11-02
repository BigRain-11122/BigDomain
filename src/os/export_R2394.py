"""Sync the exported face with the live tree (R2394).

Every derived field comes from check_export_consistency.recompute() - nothing
is hand-counted here (F3). The export's own serialisation is proven first by a
round trip, so a rewrite keeps its format byte for byte.

Stdlib only, ASCII source, no network.
"""

import datetime
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import check_export_consistency as C  # noqa: E402

EXPORT = os.path.join(REPO, "docs", "status-export.json")

CURRENT = ("R2394: the carried reconcile battery is green on the committed "
           "tree (520/520 suites, controls 7/7, 1007.7s, criteria 4096 as "
           "registered), and the single red it found was a real untriaged "
           "residue round now repaired in the declaration.")
ARTIFACT = ("qa/reconcile-all-R2394-retry.log (RUNNER PASS 520/520) and "
            "docs/sandbox-suite-matrix.md regenerated to 520 suites / 4096 "
            "criteria; state/residue_triage.json repaired at the predicted "
            "+184 bytes")
NEXT = ("a product window on the two rows whose criteria were pre-registered "
        "at R2393: runner_suite_timeout_headroom (AC-RTH1..6) and "
        "ledger_line_shape_guard (AC-LLSG1..6)")
DUE = "2026-11-05T23:00:00+08:00"


def main(argv):
    dry = "--execute" not in argv
    with io.open(EXPORT, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    doc = json.loads(raw)
    if json.dumps(doc, ensure_ascii=False, indent=2) + "\n" != raw:
        raise SystemExit("REFUSED: the export does not round-trip in its own "
                         "format, so a rewrite could reflow it")
    derived, state, _exp, pat = C.recompute()
    changes = []
    for key, value in derived.items():
        if doc["self_drive"].get(key) != value:
            changes.append("%s %r -> %r" % (key, doc["self_drive"].get(key),
                                            value))
        doc["self_drive"][key] = value
    label = pat["tick_row_label"]
    for row in doc["results"]:
        if isinstance(row, list) and len(row) >= 2 and row[1] == label:
            if row[0] != str(state.get("tick")):
                changes.append("tick_row %r -> %r" % (row[0],
                                                      state.get("tick")))
            row[0] = str(state.get("tick"))
    ceo = doc["ceo_face"]
    ceo["current"] = CURRENT
    ceo["latest_artifact"] = ARTIFACT
    ceo["next_milestone"] = NEXT
    ceo["next_milestone_due"] = DUE
    ceo["last_artifact"] = ARTIFACT
    now = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))).replace(microsecond=0)
    doc["export_ts"] = now.isoformat()
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    print("export changes: %d field(s)" % len(changes), flush=True)
    for line in changes:
        print("  %s" % line, flush=True)
    print("export_ts %s bytes %d -> %d"
          % (doc["export_ts"], len(raw.encode("utf-8")),
             len(text.encode("utf-8"))), flush=True)
    if dry:
        print("DRY: no byte written", flush=True)
        return 0
    temp = EXPORT + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temp, EXPORT)
    with io.open(EXPORT, "r", encoding="utf-8", newline="") as handle:
        written = handle.read()
    if json.loads(written) != doc:
        raise SystemExit("REFUSED: the write moved the payload")
    print("verified bytes %d temp_left=%s"
          % (len(written.encode("utf-8")), os.path.exists(temp)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))