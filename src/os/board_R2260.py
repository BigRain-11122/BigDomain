# board_R2260.py - append the R2260 rows to the two boards.
# Backlog: one done row inserted above the newest done row (ASCII anchor).
# tasks.md: one done row appended at the tail.
import io

DONE = (
    "- [x] [done 2026-10-29 R2260] verification window on the debt register first item "
    "(reconcile-battery-R2260, opened by R2259): the full reconcile battery and the suite-matrix "
    "regeneration ran on the committed tree with zero product code changed (the R2168 mixed-tree "
    "rule) - RUNNER PASS 434/434 suites green plus reconcile controls 7/7 in 732.0s with birth-site "
    "TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0 (qa/reconcile-all-R2260.log, single-writer "
    "utf-8 LF through src/os/battery_stream.py), expected criteria total=3581. Four post-battery "
    "sections then all PASS through the new single-writer helper src/os/battery_followup_R2260.py: "
    "matrix regenerated to 434 suites / 3581 criteria and read back byte-identical "
    "(docs/sandbox-suite-matrix.md, 42181B, green=434/434), fingerprint chain CLEAN over 5 domains, "
    "runner profile --daily --check PASS byte-identical, writer census re-frozen then DRIFT-CLEAN "
    "files=2204 tee=1675 baselined=529 disappeared=0 flags=0, closing on VERDICT PASS. The measured "
    "deltas against R2258 (433 suites / 3576 criteria) are +1 suite and +5 criteria, exactly the R2259 "
    "os-seed-anchor suite joining the registry. Honest score: a 0-point verification window with no "
    "product face; state.json measured 78004B against the 78500B waterline so fold R594 ran first "
    "(log lines 1:25, 36907 content bytes, 514 tokens, token_missing empty, 78004B -> 45329B, "
    "predicted==actual, 33 live items). Register row closed and the successor product-face-R2261 "
    "opened as first=yes."
)

TASK = (
    "- [x] R2260 \u9a8c\u8bc1\u7a97\uff1a\u5168\u91cf\u7535\u6c60 434/434 \u5957\u4ef6 + "
    "\u63a7\u5236 7/7\uff08732.0s\u00b7qa/reconcile-all-R2260.log\uff09\uff0c\u77e9\u9635 "
    "434 \u5957\u4ef6 / 3581 \u5224\u636e\u9010\u5b57\u8282\u540c\u4e00\uff0c\u6307\u7eb9 "
    "CLEAN\uff0cprofile PASS\uff0ccensus DRIFT-CLEAN\uff1b\u540c\u7a97 fold R594\uff08state.json "
    "78004B -> 45329B\uff09\uff1b\u65e0\u4ea7\u54c1\u4ee3\u7801\u6539\u52a8\u3002"
)


def main():
    path = 'src/os/backlog.md'
    text = io.open(path, encoding='utf-8', newline='').read()
    anchor = '- [x] [done 2026-10-29 R2258]'
    idx = text.find(anchor)
    if idx < 0:
        print('BACKLOG ANCHOR MISSING')
        return 2
    text = text[:idx] + DONE + '\n' + text[idx:]
    io.open(path, 'w', encoding='utf-8', newline='').write(text)

    tpath = 'tasks.md'
    ttext = io.open(tpath, encoding='utf-8', newline='').read()
    if not ttext.endswith('\n'):
        ttext += '\n'
    ttext += TASK + '\n'
    io.open(tpath, 'w', encoding='utf-8', newline='').write(ttext)
    print('boards written: backlog row inserted at byte %d, tasks row appended' % idx)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())