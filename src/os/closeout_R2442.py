"""closeout_R2442 - state / backlog / heartbeat closeout for the R2442
product window (matrix_stamp_provenance_line).

Writes the state log through state_io.canon with a byte read-back, prepends
the backlog row, appends the heartbeat row, and refuses any drift. Run with
--execute to write; the default is a dry run.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
BACKLOG = os.path.join(BASE, "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

TICK = 2442
DEC_ROWS = 239

LOG = [
    "2026-11-04 R2442 product window on the debt gate first=yes item "
    "(product-face-R2442, tech head state/queue/tech.md:508 prefix AC-MSPL1 "
    "matrix_stamp_provenance_line, whose AC-MSPL1..AC-MSPL6 were pinned in "
    "that row at R2418 BEFORE any code): the five anchors were re-checked at "
    "HEAD and every hit was prose or state only (closeout_R2418, "
    "closeout_R2441, export_R2418, export_R2441, state.json, the queue row) "
    "with zero executable occupancy, so the criteria were used as written and "
    "none was widened.",

    "2026-11-04 R2442 SHIPPED src/os/matrix_stamp_provenance_line.py: "
    "--stamp-from let a render follow another document's stamp at R2418, but "
    "MEASURED then the artifact could not say so - the generation command "
    "line was a fixed format string naming only --evidence, so a doc rendered "
    "with a borrowed stamp was byte-for-byte indistinguishable from an "
    "ordinary render and doc_evidence_face read only the evidence segment. "
    "ONE law with two directions: segment(labels, source) renders the line an "
    "artifact must carry for a given source, recorded_source(text, labels) "
    "reads that same line back, so writing and parsing cannot drift apart; "
    "the label and its prefix come from suite_matrix_patterns.json (the "
    "module source carries neither) and a patterns file without the label "
    "fails closed E_MSPL_NO_LABEL instead of rendering an unreadable segment.",

    "2026-11-04 R2442 the seam is asked at suite_matrix's own call sites: "
    "render() takes stamp_from and inserts the segment directly under the "
    "command line it qualifies, and --check reads the recorded source out of "
    "the doc it is judging, so a stamp-aligned doc re-renders to itself "
    "instead of reading as drift. MEASURED on REAL renders of the shipped "
    "tool: the ordinary render is 52827B with no provenance line and its "
    "header/label block byte-identical to the shipped doc, the stamp-from "
    "render is 52871B carrying the flag and the source, and --check reads "
    "PASS on the ordinary doc, on the stamp-aligned doc AND on the pre-change "
    "shipped doc - the last one proving an artifact written before this law "
    "still checks green.",

    "2026-11-04 R2442 evidence: SUITE PASS 6/6 twice with an identical "
    "digest plus three adjacent suites green (EVIDENCE CAPTURE round=R2442 "
    "legs=2 identical=True adjacent=3 fails=0, "
    "qa/matrix-stamp-provenance-line-R2442.log, 3787B, single writer utf-8 LF "
    "through the R2261 capture callable), wired "
    "os-matrix-stamp-provenance-line(6) so the registry reads 549 suites / "
    "4270 criteria. docs/sandbox-suite-matrix.md was regenerated "
    "stamp-aligned through --stamp-from to 52994B at 549 suites / 4270 "
    "criteria and --check reads byte-identical; its own generation block now "
    "records the source it borrowed, which is the product of this window "
    "visible inside the artifact.",

    "2026-11-04 R2442 LIVE, not a plan: "
    "qa/matrix-stamp-provenance-line-live-R2442.log (463B, crlf=0) reads the "
    "REAL shipped doc as recorded=docs/sandbox-suite-matrix.md through the "
    "module face and the flag round-trips both as text and as pinned-key "
    "JSON, with the segment face answering the same string the render "
    "writes.",

    "2026-11-04 R2442 board and register: row 508 stamped with a DISCHARGED "
    "block and one REAL measured gap row seeded from this window's own limit "
    "(matrix_stamp_from_liveness, AC-MSFL1..AC-MSFL6 pre-registered) because "
    "recorded_source hands the recorded string back verbatim and nothing asks "
    "whether that source still exists, so a dangling borrow reads exactly "
    "like a live one; the gauge closed FLOOR-MET main 5/5 tech 10/10 explore "
    "10/10 and the head advanced to state/queue/tech.md:510 prefix AC-PICIC1. "
    "Debt: product-face-R2442 closed through the shipped debt_close and "
    "reconcile-battery-R2443 opened first=yes through debt_append at the "
    "pre-registered 549 suites / 4270 criteria, because this window changed "
    "product src bytes and the R2168 mixed-tree rule owes the battery next.",

    "2026-11-04 R2442 honest disclosures: (a) this window claims two product "
    "points for a runnable artifact-level reading, but no CEO-visible "
    "business surface was rebuilt - the artifact that gained the line is the "
    "internal suite matrix; (b) the first AC-MSPL1 draft compared the WHOLE "
    "ordinary render against the shipped doc and went red the moment this "
    "window's own suite joined the registry (549/4270 against the doc's "
    "548/4264), so the check was narrowed to the header/label block, which is "
    "what the criterion is about, and no criterion was widened; (c) two "
    "module defects were found by measurement rather than review - the "
    "--check path first passed the whole patterns dict where recorded_source "
    "expects the labels dict and raised KeyError on the live doc, and an "
    "unused import was carried in the first draft; both were fixed in the "
    "module; (d) a first live capture decoded the child's GBK stdout as utf-8 "
    "and failed, so the capture was re-run with PYTHONIOENCODING=utf-8 and "
    "the file is utf-8 LF with crlf=0; (e) the doc's generation line is "
    "self-referential for exactly one round (it names itself), which is "
    "honest rather than decorative: the next stamp-aligned regeneration will "
    "name whatever source it is actually told to follow; (f) tasks.md was "
    "not touched, it is the P-47 canonical board and carries no row for this "
    "technical window.",
]

TOKENS = ("R2442 tokens: local=~14k api=0 api_reason=product window - one "
          "src/os law with both directions (render and read-back) plus its "
          "six-criteria suite against criteria pinned at R2418, one seam "
          "wired at two suite_matrix call sites, two real renders measured "
          "byte for byte, three --check states proved, a stamp-aligned "
          "regeneration of the shipped artifact, one live capture, one real "
          "gap row seeded, two debt register writes through their shipped "
          "CLIs, and the state/export/backlog/heartbeat closeout; zero cloud "
          "calls and zero external API touches")

SELF_HEAL = ("2026-11-04 R2442 self-heal check: BigDomain-OSLoop still "
             "exists and its Principal.LogonType reads InteractiveToken, "
             "which the 2026-09-29 machine law forbids for every lane task; "
             "src/os/register_loop_task.ps1 passes an explicit S4U principal "
             "and needs an elevated shell while this session is unelevated, "
             "so the definition was left untouched again (two-hundred-and-"
             "ninth consecutive disclosure, carried as the stale row "
             "loop-s4u-reconcile).")

BACKLOG_ROW = (
    "- [x] [done 2026-11-04 R2442] R2442 product window (debt gate first=yes "
    "product-face-R2442, tech head state/queue/tech.md:508 prefix AC-MSPL1, "
    "criteria pinned there at R2418 before any code): SHIPPED "
    "src/os/matrix_stamp_provenance_line.py plus its six-criteria suite - "
    "segment() renders the provenance line an artifact must carry for a "
    "borrowed stamp and recorded_source() reads that same line back, so "
    "--check on a stamp-aligned doc recovers the borrow instead of reporting "
    "drift, the label is owned by suite_matrix_patterns.json, and an ordinary "
    "render keeps today's bytes (52827B, header/label block byte-identical to "
    "the shipped doc) while a stamp-from render is 52871B naming its source. "
    "SUITE PASS 6/6 twice with an identical digest plus three adjacent suites "
    "green (qa/matrix-stamp-provenance-line-R2442.log, 3787B, legs=2 "
    "identical=True adjacent=3 fails=0), wired "
    "os-matrix-stamp-provenance-line(6) so the registry reads 549 suites / "
    "4270 criteria; docs/sandbox-suite-matrix.md regenerated stamp-aligned to "
    "52994B at 549/4270 with --check byte-identical. LIVE "
    "qa/matrix-stamp-provenance-line-live-R2442.log (463B, crlf=0) reads the "
    "shipped doc as recording itself as its borrowed source. Board: row 508 "
    "stamped, one real gap row seeded (matrix_stamp_from_liveness "
    "AC-MSFL1..AC-MSFL6), floor FLOOR-MET 5/5 10/10 10/10, head now "
    "state/queue/tech.md:510 AC-PICIC1. Debt: product-face-R2442 closed and "
    "reconcile-battery-R2443 opened first=yes at the pre-registered 549/4270. "
    "Honest: two product points for an internal artifact-level reading, no "
    "CEO-visible business surface rebuilt.")

HEARTBEAT_ROW = (
    "2026-11-04T20:05:00+08:00 tick=2442 R2442 product window - "
    "matrix_stamp_provenance_line shipped against AC-MSPL1..AC-MSPL6 pinned "
    "at R2418: a render told to borrow another document's stamp now records "
    "that in the artifact and --check reads it back, while an ordinary render "
    "keeps today's bytes; SUITE PASS 6/6 twice, registry 549 suites / 4270 "
    "criteria, shipped matrix regenerated 52994B and --check byte-identical; "
    "one real gap row seeded (matrix_stamp_from_liveness) and the floor reads "
    "FLOOR-MET 5/5 10/10 10/10; next window owes reconcile-battery-R2443 "
    "[via BigDomain-OSLoop]")


def write_bytes_atomic(path, data, prefix):
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=prefix)
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = open(path, "rb").read()
    if back != data:
        raise SystemExit("E_R2442_BACK read-back does not match the write")
    return len(back)


def main(execute):
    if not execute:
        print("DRY RUN tick=%d log_lines=%d" % (TICK, len(LOG) + 2))
        for line in LOG:
            print("  LOG %s" % line[:100])
        return 0

    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2442_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = DEC_ROWS
    payload["log"].extend(LOG)
    payload["log"].append(TOKENS)
    payload["log"].append(SELF_HEAL)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2442_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2442-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d layout_ok=%s crlf=%d bare_lf=%d"
          % (TICK, size, len(payload["log"]), layout["layout_ok"],
             layout["crlf"], layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if "R2442] R2442 product window" in backlog:
        raise SystemExit("E_R2442_BACKLOG row already present")
    write_bytes_atomic(BACKLOG, (BACKLOG_ROW + "\n" + backlog).encode(
        "utf-8"), ".r2442-backlog-")
    print("BACKLOG row prepended")

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if "tick=2442 " in beat:
        raise SystemExit("E_R2442_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    write_bytes_atomic(HEARTBEAT, (beat + HEARTBEAT_ROW + "\n").encode(
        "utf-8"), ".r2442-beat-")
    print("HEARTBEAT row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))