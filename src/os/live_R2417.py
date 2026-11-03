# live_R2417.py - one read-only live capture, one utf-8 LF writer.
# Ages every ABORTED body in the REAL evidence pile through
# runner_abort_history: SUPERSEDED / LIVE-ABORT / ORPHAN-ABORT, so a
# historical abort can be told apart from live debt where the abort face
# alone reported both as ABORTED. Writes exactly one file.
import hashlib
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import runner_abort_face as RAF  # noqa: E402
import runner_abort_history as RAH  # noqa: E402

OUT = os.path.join(ROOT, "qa", "runner-abort-history-live-R2417.log")
MODULE = os.path.join(BASE, "runner_abort_history.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
QA = os.path.join(ROOT, "qa")


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


def write(lines):
    body = "\n".join(lines) + "\n"
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return len(body.encode("utf-8"))


def main():
    before = digest(MODULE)
    names = sorted(name for name in os.listdir(QA) if name.endswith(".log"))
    faces = {"COMPLETE": 0, "ABORTED": 0, "UNREADABLE": 0}
    rows = []
    for name in names:
        path = os.path.join(QA, name)
        try:
            face = RAF.check(path, RUNNER)
        except RAF.AbortError:
            continue
        faces[face["verdict"]] += 1
        if face["verdict"] != "ABORTED":
            continue
        try:
            row = RAH.history(path, RUNNER)
        except RAH.HistoryError as exc:
            rows.append((name, "REFUSED", exc.code, "-", 0))
            continue
        rows.append((name, row["verdict"],
                     "-" if row["round"] is None else "R%d" % (row["round"],),
                     row["green_leg"], len(row["family"])))
    counts = {"SUPERSEDED": 0, "LIVE-ABORT": 0, "ORPHAN-ABORT": 0,
              "REFUSED": 0}
    lines = ["EVIDENCE CAPTURE round=R2417 live=runner-abort-history "
             "module_sha16_before=%s" % (before,),
             "PILE logs=%d COMPLETE=%d ABORTED=%d UNREADABLE=%d"
             % (len(names), faces["COMPLETE"], faces["ABORTED"],
                faces["UNREADABLE"])]
    for name, verdict, round_label, green, family_count in rows:
        counts[verdict] = counts.get(verdict, 0) + 1
        lines.append("AGE %s verdict=%s round=%s family=%d green=%s"
                     % (name, verdict, round_label, family_count, green))
    lines.append("AGES aborted=%d SUPERSEDED=%d LIVE-ABORT=%d "
                 "ORPHAN-ABORT=%d REFUSED=%d"
                 % (len(rows), counts["SUPERSEDED"], counts["LIVE-ABORT"],
                    counts["ORPHAN-ABORT"], counts["REFUSED"]))
    after = digest(MODULE)
    lines.append("MODULE sha16_after=%s unchanged=%s"
                 % (after, before == after))
    size = write(lines)
    print("\n".join(lines), flush=True)
    print("WROTE %s bytes=%d" % (os.path.relpath(OUT, ROOT), size), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())