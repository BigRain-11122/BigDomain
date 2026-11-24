"""Suite for the claims census: the numbers this company writes get a reader.

TEN criteria. AC-CLAIM1..3 were pre-registered in the R3225 backlog PIN row,
AC-CLAIM4..6 in the R3226 PIN row, AC-CLAIM7..9 in the R3227 PIN row, and
AC-CLAIM10 in the R3359 PIN row - every group before the code it grades.

R3224 measured the hole: the board wrote `LEDGER OK rows=2` while the ledger as
that round's own commit recorded it held one row, and nothing read the number
back - the probe for R3225 counted 307 `rows=<n>` tokens on the three faces and
found five of seven round-tagged claims disagreeing with their own commit.

AC-CLAIM1 grades the classification on a private world: a claim is captured
only when a landed file its own line names carries the same token, contradicted
when that citation carries the same shape with a different number or when the
line speaks about the live ledger and the number is not the ledger's, and
uncaptured when the line names nothing that could speak for it (prose, named,
never deleted and never counted as a measurement).

AC-CLAIM2 grades that the reader reads only: no writes to the three faces or the
ledger, the counts add up to the claims, one ledger parser (`qa_log`), and the
module stays ASCII.

AC-CLAIM3 grades the consumer: the closeout gate prints one CLAIMS row, carries
the counts as values, publishes them on a seventh named face, and still passes a
world whose prose contradicts itself - a written sentence is not a gate.

Usage: python test_claim_census.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TOOLS = os.path.join(REPO, "tools")
MODULE = os.path.join(TOOLS, "claim_census.py")
GATE = os.path.join(TOOLS, "closeout_gate.py")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
ROW = "claim-census"

sys.path.insert(0, TOOLS)
import claim_census as CC  # noqa: E402
import closeout_gate as CG  # noqa: E402

RESULTS = []

LEDGER_ROW = {"event": "REPLACED", "name": "inner.log", "new_bytes": 12,
              "new_sha16": "0123456789abcdef", "old_bytes": 3,
              "old_sha16": "fedcba9876543210", "ts": "2026-11-22T00:00:00Z"}


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def write(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def world(root, board_lines, ledger_rows=1, cited=()):
    """A private world: three faces, a ledger and the qa files it may name."""
    write(os.path.join(root, "src", "os", "backlog.md"), "\n".join(board_lines))
    write(os.path.join(root, "src", "os", "state.json"), '{"log": []}\n')
    write(os.path.join(root, "docs", "status-export.json"), '{"chain": {}}\n')
    rows = [dict(LEDGER_ROW) for _ in range(ledger_rows)]
    write(os.path.join(root, "state", "qa_replacements.jsonl"),
          "".join(json.dumps(row) + "\n" for row in rows))
    for name, text in cited:
        write(os.path.join(root, "qa", name), text)


def statuses(root, board_lines):
    found = []
    for line in board_lines:
        found.extend(CC.classify(root, line, ledger_rows_of(root)))
    return found


def ledger_rows_of(root):
    import qa_log as QL
    return QL.ledger_report(os.path.join(root, "state", QL.LEDGER_NAME),
                            evidence_dir=os.path.join(root, "qa"))["rows"]


def main():
    root = tempfile.mkdtemp(prefix="claims-")
    try:
        # ---- AC-CLAIM1: the five shapes of a written number. --------------
        bad1 = []
        cited_hit = ("inner.log",
                     "LEDGER OK rows=3 names=3 bad=0 stale=0 missing=0 broken=0\n")
        cited_off = ("other.log",
                     "LEDGER OK rows=2 names=2 bad=0 stale=0 missing=0 broken=0\n")
        citations = (cited_hit, cited_off, ("silent.log", "SUITE PASS 2/2\n"))
        board = [
            # a: names the live ledger and agrees with it -> captured
            "- live agrees LEDGER OK rows=1 names=1 bad=0 path=state/qa_replacements.jsonl",
            # b: names the live ledger and disagrees -> contradicted
            "- live lies LEDGER OK rows=9 names=9 bad=0 path=state/qa_replacements.jsonl",
            # c: cites a landed file that carries the same token -> captured
            "- cited twice LEDGER OK rows=3 bad=0 (qa/inner.log)",
            # d: cites a landed file carrying the same shape, other number
            "- cited wrong LEDGER OK rows=4 bad=0 (qa/other.log)",
            # e: bare prose, nothing to speak for it -> uncaptured
            "- prose only rows=7 in a sentence nobody can check",
            # f: cites a landed file with no rows shape at all -> uncaptured
            "- cites silence rows=5 (qa/silent.log)",
        ]
        world(root, board, ledger_rows=1, cited=citations)
        got = statuses(root, board)
        want = ["captured", "contradicted", "captured", "contradicted",
                "uncaptured", "uncaptured"]
        if [item["status"] for item in got] != want:
            bad1.append("statuses=%s" % [item["status"] for item in got])
        # The citation that does not exist must not be trusted either.
        ghost = ["- ghost citation LEDGER OK rows=3 bad=0 (qa/never-written.log)"]
        if [item["status"] for item in statuses(root, ghost)] != ["uncaptured"]:
            bad1.append("unlanded-citation-counted")
        # Derived, not declared: changing the ledger moves the live reading.
        world(root, board, ledger_rows=9, cited=citations)
        if [i["status"] for i in statuses(root, board)][:2] != ["contradicted",
                                                              "captured"]:
            bad1.append("live-count-not-derived")
        report("AC-CLAIM1", bool(bad1), ",".join(bad1))

        # ---- AC-CLAIM2: reads only, one parser, and the counts add up. ----
        bad2 = []
        world(root, board, ledger_rows=1, cited=citations)
        watched = [os.path.join(root, "src", "os", "backlog.md"),
                   os.path.join(root, "src", "os", "state.json"),
                   os.path.join(root, "docs", "status-export.json"),
                   os.path.join(root, "state", "qa_replacements.jsonl")]
        before = [(os.path.getsize(p), os.path.getmtime(p)) for p in watched]
        result = CC.census(root)
        after = [(os.path.getsize(p), os.path.getmtime(p)) for p in watched]
        if before != after:
            bad2.append("wrote-what-it-read")
        if result["claimed"] != (result["captured"] + result["contradicted"]
                                 + result["uncaptured"]):
            bad2.append("counts-do-not-add-up-%s" % result["claimed"])
        if result["claimed"] != len(board):
            bad2.append("claims=%d expected=%d" % (result["claimed"], len(board)))
        raw = io.open(MODULE, "rb").read()
        if any(byte > 126 or byte == 13 for byte in raw):
            bad2.append("not-ascii-lf")
        text = raw.decode("ascii")
        if text.count("ledger_report(") != 1:
            bad2.append("second-parser-%d" % text.count("ledger_report("))
        if "read_ledger(" in text or "json.loads" in text:
            bad2.append("own-parser")
        if CC.census_row(result).count("rows=") != 1:
            bad2.append("row-shape")
        report("AC-CLAIM2", bool(bad2), ",".join(bad2))

        # ---- AC-CLAIM3: the consumer reads, prints and never refuses. -----
        bad3 = []
        world(root, board, ledger_rows=1, cited=citations)
        reading = {}
        ok, row = CG.check_claims(root, reading=reading)
        if ok is not True:
            bad3.append("face-refused")
        if not row.startswith("CLAIMS "):
            bad3.append("row-prefix")
        census = CC.census(root)
        for key in ("claimed", "captured", "contradicted", "uncaptured", "rows"):
            if reading.get(key) != census[key]:
                bad3.append("reading-%s-%r" % (key, reading.get(key)))
        if "contradicted=0" in row:
            bad3.append("fixture-did-not-contradict")
        gate_text = io.open(GATE, encoding="utf-8").read()
        if gate_text.count('_timed(face_ms, "claims", check_claims') != 1:
            bad3.append("wiring")
        if gate_text.count('verdict["claims"] = dict(claims_reading)') != 1:
            bad3.append("publish")
        if '"claims"' not in gate_text.split("INFORMATIONAL_FACES")[1][:120]:
            bad3.append("not-named-informational")
        with io.open(REGISTRY, encoding="utf-8") as handle:
            reg = handle.read()
        found = re.search(r'test_claim_census\.py"\)\s*,\s*(\d+)', reg)
        if not found or int(found.group(1)) != 10:
            bad3.append("registry-count-%s" % (found.group(1) if found else "-"))
        if len(RESULTS) != 2:
            bad3.append("results-before-this-arm-%d" % len(RESULTS))
        report("AC-CLAIM3", bool(bad3), ",".join(bad3))

        # ---- AC-CLAIM4: every contradicted claim gets an address. ---------
        bad4 = []
        named_board = [
            "- [R3210] old snapshot LEDGER OK rows=0 path=state/qa_replacements.jsonl",
            "- [R3230] about now LEDGER OK rows=9 path=state/qa_replacements.jsonl",
            "- [R3230] cited wrong LEDGER OK rows=4 bad=0 (qa/other.log)",
            "- [R3230] cited right LEDGER OK rows=2 bad=0 (qa/other.log)",
            "- [R3230] prose only rows=7 nobody can check",
        ]
        world(root, named_board, ledger_rows=4, cited=citations)
        named = []
        result4 = CC.census(root, detail=named)
        if len(named) != result4["contradicted"]:
            bad4.append("named=%d contradicted=%d"
                        % (len(named), result4["contradicted"]))
        statuses4 = statuses(root, named_board)
        wanted = [(i) for i in statuses4 if i["status"] == "contradicted"]
        if len(wanted) != 3 or len(named) != 3:
            bad4.append("fixture-shape-wanted=%d named=%d"
                        % (len(wanted), len(named)))
        for item in named:
            for key in ("face", "line", "rows", "source", "source_rows", "why"):
                if key not in item:
                    bad4.append("missing-%s" % key)
        if [item["line"] for item in named] != [1, 2, 3]:
            bad4.append("lines=%s" % [item["line"] for item in named])
        if [item["rows"] for item in named] != [0, 9, 4]:
            bad4.append("rows=%s" % [item["rows"] for item in named])
        row = CC.detail_row(named[2])
        if not row.startswith("CLAIM board:3 rows=4 source=qa/other.log "
                              "source_rows=2 why=evidence-differs"):
            bad4.append("row-shape-%r" % row)
        capped = CC.detail_lines(named, 1)
        if len(capped) != 2 or capped[-1] != "+2 more":
            bad4.append("cap1=%r" % capped)
        full = CC.detail_lines(named, 5)
        if len(full) != 3 or any("more" in line for line in full):
            bad4.append("cap5=%r" % full)
        if CC.detail_lines([], 5) != []:
            bad4.append("cap-empty")
        report("AC-CLAIM4", bool(bad4), ",".join(bad4))

        # ---- AC-CLAIM5: the detail face is pure addition. ------------------
        bad5 = []
        named = []
        bare = CC.census(root)
        with_detail = CC.census(root, detail=named)
        for key in ("claimed", "captured", "contradicted", "uncaptured",
                    "rows", "present"):
            if bare[key] != with_detail[key]:
                bad5.append("detail-moved-%s" % key)
        if bare["faces"] != with_detail["faces"]:
            bad5.append("detail-moved-faces")
        literal = ("CLAIMS captured=%d uncaptured=%d contradicted=%d historic=%d "
                   "rows=%d present=%s"
                   % (bare["captured"], bare["uncaptured"],
                      bare["contradicted"], bare["historic"], bare["rows"],
                      "true" if bare["present"] else "false"))
        if CC.census_row(bare) != literal:
            bad5.append("main-row-text")
        reading = {}
        CG.check_claims(root, reading=reading)
        if set(reading) != {"claimed", "captured", "contradicted", "uncaptured",
                            "historic", "rows", "present"}:
            bad5.append("gate-keys-%s" % sorted(reading))
        gate_text = io.open(GATE, encoding="utf-8").read()
        # AC-CLAIM5 (R3383, AC-SXFB39): still exactly ONE census call in the
        # gate, and it now forwards the writer's candidate document - a second
        # derivation is what this line exists to forbid.
        if (gate_text.count("CC.census(") != 1
                or "export_text=export_text" not in gate_text):
            bad5.append("gate-passes-detail")
        watched = [os.path.join(root, "src", "os", "backlog.md"),
                   os.path.join(root, "state", "qa_replacements.jsonl"),
                   os.path.join(root, "qa", "other.log")]
        before = [(os.path.getsize(p), os.path.getmtime(p)) for p in watched]
        CC.census(root, detail=[])
        after = [(os.path.getsize(p), os.path.getmtime(p)) for p in watched]
        if before != after:
            bad5.append("detail-wrote")
        raw = io.open(MODULE, "rb").read()
        if any(byte > 126 or byte == 13 for byte in raw):
            bad5.append("not-ascii-lf")
        report("AC-CLAIM5", bool(bad5), ",".join(bad5))

        # ---- AC-CLAIM6: the source number is a reading, not a caption. ----
        bad6 = []
        vocab = {"live-snapshot", "live-now", "evidence-differs",
                 "evidence-no-ledger-row"}
        world(root, named_board, ledger_rows=1, cited=citations)
        named = []
        CC.census(root, detail=named)
        if [item["source_rows"] for item in named] != [[1], [1], [2]]:
            bad6.append("first-read=%s" % [i["source_rows"] for i in named])
        world(root, named_board, ledger_rows=4, cited=citations)
        named = []
        CC.census(root, detail=named)
        if [item["source_rows"] for item in named] != [[4], [4], [2]]:
            bad6.append("ledger-not-derived=%s"
                        % [i["source_rows"] for i in named])
        other = os.path.join(root, "qa", "other.log")
        write(other, "LEDGER OK rows=5 names=5 bad=0 broken=0\n")
        named = []
        CC.census(root, detail=named)
        if named[2]["source_rows"] != [5]:
            bad6.append("citation-not-re-read=%s" % named[2]["source_rows"])
        if named[0]["why"] != "live-snapshot" or named[1]["why"] != "live-now":
            bad6.append("tag-split=%s" % [i["why"] for i in named])
        untagged = ["- not dated LEDGER OK rows=9 path=state/qa_replacements.jsonl"]
        world(root, untagged, ledger_rows=4, cited=citations)
        named = []
        CC.census(root, detail=named)
        if [item["why"] for item in named] != ["live-now"]:
            bad6.append("untagged-%s" % [i["why"] for i in named])
        bad6.extend("bad-why-%s" % item["why"] for item in named
                    if item["why"] not in vocab)
        report("AC-CLAIM6", bool(bad6), ",".join(bad6))

        # ---- AC-CLAIM7: the historic sub-count is derived, not declared. ---
        bad7 = []
        snap_a = ("- [R3200] old snapshot A LEDGER OK rows=0 "
                  "path=state/qa_replacements.jsonl")
        snap_b = ("- [R3201] old snapshot B LEDGER OK rows=0 "
                  "path=state/qa_replacements.jsonl")
        err_now = ("- error about now LEDGER OK rows=9 "
                   "path=state/qa_replacements.jsonl")
        split_board = [snap_a, snap_b,
                       "- [R3230] newest marker rows=4 nobody can check",
                       err_now]
        world(root, split_board, ledger_rows=4, cited=citations)
        named = []
        result7 = CC.census(root, detail=named)
        if (result7["contradicted"], result7["historic"]) != (3, 2):
            bad7.append("split=%d/%d" % (result7["contradicted"],
                                         result7["historic"]))
        snapshots = sum(1 for item in named if item["why"] == "live-snapshot")
        if snapshots != result7["historic"]:
            bad7.append("detail-disagrees-%d" % snapshots)
        # Same board, but the snapshots' own tags are no longer older than the
        # newest one: the sub-count follows the tags, it is not a caption.
        same_tag = ["- [R3230] old snapshot A LEDGER OK rows=0 "
                    "path=state/qa_replacements.jsonl",
                    "- [R3230] old snapshot B LEDGER OK rows=0 "
                    "path=state/qa_replacements.jsonl",
                    "- [R3230] newest marker rows=4 nobody can check",
                    err_now]
        world(root, same_tag, ledger_rows=4, cited=citations)
        result7b = CC.census(root)
        if (result7b["contradicted"], result7b["historic"]) != (3, 0):
            bad7.append("tag-flip=%d/%d" % (result7b["contradicted"],
                                            result7b["historic"]))
        # A snapshot that agrees with today's ledger is captured, not historic.
        world(root, split_board, ledger_rows=0, cited=citations)
        result7c = CC.census(root)
        if (result7c["contradicted"], result7c["historic"]) != (1, 0):
            bad7.append("agreement=%d/%d" % (result7c["contradicted"],
                                             result7c["historic"]))
        # No contradiction at all answers 0 rather than an error.
        world(root, ["- nothing to contradict rows=7"], ledger_rows=4)
        result7d = CC.census(root)
        if (result7d["contradicted"], result7d["historic"]) != (0, 0):
            bad7.append("empty=%d/%d" % (result7d["contradicted"],
                                         result7d["historic"]))
        report("AC-CLAIM7", bool(bad7), ",".join(bad7))

        # ---- AC-CLAIM8: conservation and one published token. --------------
        bad8 = []
        world(root, split_board, ledger_rows=4, cited=citations)
        bare = CC.census(root)
        named = []
        with_detail = CC.census(root, detail=named)
        if bare["historic"] != with_detail["historic"]:
            bad8.append("detail-moved-historic")
        if not (0 <= bare["historic"] <= bare["contradicted"]):
            bad8.append("range-%d/%d" % (bare["historic"], bare["contradicted"]))
        # Independent path: classify again and count what is wrong about now.
        newest8 = CC._newest_tag([io.open(os.path.join(root, rel),
                                          encoding="utf-8").read()
                                  for _face, rel in CC.FACES])
        live_now = 0
        for line in split_board:
            for item in CC.classify(root, line, ledger_rows_of(root)):
                if (item["status"] == "contradicted"
                        and not CC._is_historic(line, item, newest8)):
                    live_now += 1
        if bare["historic"] + live_now != bare["contradicted"]:
            bad8.append("conservation-%d+%d!=%d"
                        % (bare["historic"], live_now, bare["contradicted"]))
        row8 = CC.census_row(bare)
        if row8.count("historic=") != 1:
            bad8.append("row-token-%d" % row8.count("historic="))
        if ("historic=%d" % bare["historic"]) not in row8:
            bad8.append("row-value")
        reading = {}
        CG.check_claims(root, reading=reading)
        if reading.get("historic") != bare["historic"]:
            bad8.append("reading-value")
        for key in ("claimed", "captured", "contradicted", "uncaptured",
                    "rows", "present"):
            if key not in bare or key not in with_detail:
                bad8.append("key-lost-%s" % key)
            elif bare[key] != with_detail[key]:
                bad8.append("detail-moved-%s" % key)
        report("AC-CLAIM8", bool(bad8), ",".join(bad8))

        # ---- AC-CLAIM9: the three existing faces are untouched. -------------
        bad9 = []
        world(root, named_board, ledger_rows=4, cited=citations)
        statuses9 = [item["status"] for item in statuses(root, named_board)]
        if statuses9 != ["contradicted", "contradicted", "contradicted",
                         "captured", "uncaptured"]:
            bad9.append("classification=%s" % statuses9)
        named = []
        CC.census(root, detail=named)
        vocab9 = {"live-snapshot", "live-now", "evidence-differs",
                  "evidence-no-ledger-row"}
        bad9.extend("bad-why-%s" % item["why"] for item in named
                    if item["why"] not in vocab9)
        row9 = CC.detail_row(named[2])
        if not row9.startswith("CLAIM board:3 rows=4 source=qa/other.log "
                               "source_rows=2 why=evidence-differs"):
            bad9.append("detail-shape-%r" % row9)
        ok9, line9 = CG.check_claims(root)
        if ok9 is not True or not line9.startswith("CLAIMS "):
            bad9.append("face-refused")
        live = CC.census()
        if not (0 <= live["historic"] <= live["contradicted"]):
            bad9.append("live-range-%d/%d" % (live["historic"],
                                              live["contradicted"]))
        report("AC-CLAIM9", bool(bad9), ",".join(bad9))
        # ---- AC-CLAIM10: only a token that STARTS a word is a claim. -------
        bad10 = []
        tokens = [
            # a compound identifier's tail is a different reading, not a claim
            ("- trend newest_rows=2 window_rows=5 last_stamp_rows=2026-11-20",
             []),
            # the same numbers behind a boundary are real claims
            ("- prose only rows=7 in a sentence", [7]),
            ("- quoted `rows=4` inside backticks", [4]),
            ("- after a colon: rows=6", [6]),
            ("- prefixed xrows=4 and my_rows=5 stay out", []),
        ]
        for line, want in tokens:
            got = [item["rows"] for item in CC.classify(root, line, 1)]
            if got != want:
                bad10.append("token-%r=%s want=%s" % (line[:28], got, want))
        # A cited file that carries only the compound form cannot speak for a
        # genuine claim: the two sides must agree about what a token is.
        write(os.path.join(root, "qa", "compound.log"),
              "TREND newest_rows=9 window_rows=9\n")
        cite = ["- cites compound only rows=9 (qa/compound.log)"]
        if [i["status"] for i in statuses(root, cite)] != ["uncaptured"]:
            bad10.append("compound-captured-%s"
                         % [i["status"] for i in statuses(root, cite)])
        # And a lattice: the live face's own number still classifies.
        world(root, ["- live agrees rows=1 path=state/qa_replacements.jsonl"],
              ledger_rows=1)
        if [i["status"] for i in statuses(
                root, ["- live agrees rows=1 path=state/qa_replacements.jsonl"])] \
                != ["captured"]:
            bad10.append("boundary-broke-genuine")
        report("AC-CLAIM10", bool(bad10), ",".join(bad10))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
