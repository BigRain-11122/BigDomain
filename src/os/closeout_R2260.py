# closeout_R2260.py - one-shot closeout writer for the R2260 window.
# Appends the three R2260 log items to src/os/state.json, bumps the tick,
# and verifies the canonical layout afterwards. ASCII source, utf-8 CRLF
# output, single writer.
import io
import json
import sys

sys.path.insert(0, 'src/os')
import state_fold as sf
import state_io as sio

P = 'src/os/state.json'

L1 = (
    "2026-10-29 R2260 (five-silence scan clean at open: tree clean with an empty git status --short and "
    "no index.lock; the queue gauge read main 5/5 tech 10/10 explore 10/10 FLOOR-MET with tech 11 open of "
    "which 1 gated and explore 10 open; decisions.md carries 289 non-empty rows and 194 content-addressed "
    "D/C/O/T/XL tokens against the stored 194-token superset baseline with ZERO additions, so zero domain "
    "action; the group ledger carries the same three @BigDomain patrol rows already paid off, none "
    "numbered, so zero unreplied handoffs; the group orders tail is unchanged at the 2026-10-29 02:1x "
    "CEO-PROXY event round R2.48 already consumed in R2226; benchmarks refreshed 2026-10-29 inside the "
    "seven-day gate) - the P1 canonical rows stay blocked-on-CEO, the weekly proposal duty is met by "
    "BD-PROP-005, and the debt register named exactly one first=yes row (reconcile-battery-R2260, opened "
    "by R2259), so this window took the verification debt instead of opening a new product face: R2259 "
    "shipped src/os code (seed_anchor.py, test_seed_anchor.py, evidence_R2259.py) plus a runner entry that "
    "no full battery had covered, and the R2168 mixed-tree rule forbids product edits inside a battery "
    "window. RESULT on the committed tree (5d1cbce7): full reconcile battery RUNNER PASS 434/434 suites "
    "green plus reconcile controls 7/7 in 732.0s with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB "
    "busy=0 failed=0 (qa/reconcile-all-R2260.log, single-writer utf-8 LF through src/os/battery_stream.py, "
    "never a shell redirection), expected criteria total=3581. Four post-battery sections then all PASS "
    "through the new src/os/battery_followup_R2260.py (same shape as R2258, only the evidence path and the "
    "round label changed): matrix regenerated to 434 suites / 3581 criteria and read back byte-identical "
    "(docs/sandbox-suite-matrix.md, 42181B, green=434/434), fingerprint chain CLEAN over 5 domains, runner "
    "profile --daily --check PASS byte-identical, writer census re-frozen then DRIFT-CLEAN files=2204 "
    "tee=1675 baselined=529 flags=0, closing on VERDICT PASS. The measured deltas against R2258 (433 "
    "suites / 3576 criteria) are +1 suite and +5 criteria, exactly the R2259 os-seed-anchor suite joining "
    "the registry, so the newest slice is now covered by the whole battery and not only by its own suite "
    "plus neighbours. Honest score: a 0-point verification window with no product face. state.json "
    "measured 78004B against the 78500B waterline (margin 496B) before this window, so a fold was due and "
    "was executed first: fold R594 moved log lines 1:25 (36907 content bytes, 514 tokens, token_missing "
    "empty) into logs/state-log-archive-2026-10.md verbatim, 78004B -> 45329B with predicted==actual and "
    "33 live log items. Register row closed and the successor product-face-R2261 opened as first=yes.")

L2 = (
    "R2260 tokens: local=~10k api=0 api_reason=verification window on the debt register first item - one "
    "streamed full battery with the birth-site tmp reclaim inside its own window, one new four-section "
    "follow-up helper, one state fold R594 inside a measured waterline breach, one register row closed "
    "with its successor opened, and the backlog/state/export closeout; zero cloud calls and zero external "
    "API touches; no product code changed (the R2168 mixed-tree rule)")

L3 = (
    "R2260 self-heal check: BigDomain-OSLoop is registered and its principal still reads "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; "
    "src/os/register_loop_task.ps1 already passes an explicit S4U principal and needs an elevated shell to "
    "apply it, and this session runs unelevated, so the definition of the loop hosting this window was "
    "left untouched. Open local-lane item for an elevated window (twenty-eighth consecutive disclosure, "
    "registered as the stale row loop-s4u-reconcile in state/debt.md).")


def main():
    raw = io.open(P, 'rb').read()
    text = raw.decode('utf-8')
    lines = text.split('\r\n')
    if lines[1] != '  "tick": 2259,':
        print('UNEXPECTED tick line: %r' % lines[1])
        return 2
    lines[1] = '  "tick": 2260,'
    close = len(lines) - 2
    if lines[close].strip() != ']':
        print('UNEXPECTED close line: %r' % lines[close])
        return 2
    if lines[close - 1].rstrip().endswith(','):
        print('UNEXPECTED trailing comma on last item')
        return 2
    lines[close - 1] = lines[close - 1] + ','
    items = [sf.ITEM_PREFIX + json.dumps(s, ensure_ascii=True)
             for s in (L1, L2, L3)]
    # every spliced item but the last carries a trailing comma
    new = [item + ',' for item in items[:-1]] + [items[-1]]
    lines[close:close] = new
    out = '\r\n'.join(lines)
    try:
        data = json.loads(out)
    except ValueError as exc:
        ol = out.split('\r\n')
        print('JSON FAIL %s (lines=%d)' % (exc, len(ol)))
        for idx in range(40, min(len(ol), 46)):
            print(idx + 1, len(ol[idx]), repr(ol[idx][:70]))
        return 2
    if data['tick'] != 2260 or len(data['log']) != 36:
        print('VERIFY FAIL tick=%r items=%d' % (data['tick'], len(data['log'])))
        return 2
    io.open(P, 'wb').write(out.encode('utf-8'))
    print('written bytes', len(out.encode('utf-8')),
          'log items', len(data['log']))
    print(sio.check('.', gate=78500))
    return 0


if __name__ == '__main__':
    sys.exit(main())