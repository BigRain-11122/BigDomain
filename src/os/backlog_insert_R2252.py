# backlog_insert_R2252.py - prepend the R2252 done row to the backlog
# working board, immediately above the R2251 row. Single writer, utf-8,
# existing EOL style preserved.
import io

PATH = "src/os/backlog.md"
MARKER = "- [x] [done 2026-10-29 R2251] P2 tech head claim"

ROW = (
    "- [x] [done 2026-10-29 R2252] debt register first item closed: the full "
    "reconcile battery and the suite-matrix regeneration ran on the committed "
    "tree with zero product code changed (the R2168 mixed-tree rule) - "
    "RUNNER PASS 430/430 suites green plus reconcile controls 7/7 in 798.1s "
    "with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2252.log, 764259B, single-writer utf-8 LF through "
    "src/os/battery_stream.py), expected criteria total 3558; four "
    "post-battery sections all PASS through the new "
    "src/os/battery_followup_R2252.py: matrix regenerated to 430 suites / "
    "3558 criteria and read back byte-identical "
    "(docs/sandbox-suite-matrix.md, 41900B, green=430/430), fingerprint CLEAN "
    "over 5 domains, runner profile --daily --check PASS byte-identical, "
    "writer census re-frozen then DRIFT-CLEAN files=2188 tee=1659 "
    "baselined=529 disappeared=0 flags=0, VERDICT PASS. The measured deltas "
    "against R2249 (428 suites / 3546 criteria) are +2 suites and +12 "
    "criteria, exactly the R2250 export-freshness suite (6) and the R2251 "
    "os-debt-append suite (6) joining the registry, so both recent slices are "
    "now covered by the whole battery. Honest score: a 0-point verification "
    "window with no product face; state.json measures 46647B against the "
    "78500B waterline so no fold was due. Honest disclosure: a "
    "reconcile_all.py --help probe started a real battery run and was killed "
    "by a truncating pipe; zero surviving processes, no evidence file and one "
    "stray '--help' artefact in the repo root were confirmed and the artefact "
    "was deleted before the sanctioned run."
)


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read()
    count = text.count(MARKER)
    if count != 1:
        raise SystemExit("E_BLI markers=%d" % count)
    index = text.index(MARKER)
    eol = "\r\n" if "\r\n" in text else "\n"
    text = text[:index] + ROW + eol + text[index:]
    with io.open(PATH, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("inserted at %d (eol=%r)" % (index, eol))


if __name__ == "__main__":
    main()