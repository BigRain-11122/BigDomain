# export_R2260.py - refresh docs/status-export.json for the R2260 window.
# Every derived field is recomputed from the live tree through the
# consistency checker's own recompute() (F3 law: nothing hardcoded that
# can be derived). The CEO-facing Chinese text lives in the sidecar
# export_face_R2260.json data file, so this source stays pure ASCII.
import datetime
import io
import json
import sys

sys.path.insert(0, 'src/os')
import check_export_consistency as cec

EXPORT = 'docs/status-export.json'
FACE = 'src/os/export_face_R2260.json'

DO = (
    "verification window R2260: the full reconcile battery ran on the committed R2259 tree "
    "(5d1cbce7) with zero product code changed - 434/434 suites green plus controls 7/7 in 732.0s "
    "with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB, expected criteria total 3581, then the "
    "four post-battery sections all PASS (matrix 434 suites / 3581 criteria byte-identical, "
    "fingerprint CLEAN over 5 domains, runner profile --daily --check PASS, qa writer census "
    "DRIFT-CLEAN files=2204); no product face this window, only the verification debt"
)

RESULT = (
    "R2260 verification window on the debt register first item (reconcile-battery-R2260): RUNNER "
    "PASS 434/434 suites plus controls 7/7 in 732.0s with birth-site TMP RECLAIM 932/932 worlds "
    "326.57 MiB busy=0 failed=0 (qa/reconcile-all-R2260.log, single-writer utf-8 LF through "
    "src/os/battery_stream.py), expected criteria total=3581; four follow-up sections all PASS via "
    "src/os/battery_followup_R2260.py - matrix regenerated to 434 suites / 3581 criteria and read back "
    "byte-identical (docs/sandbox-suite-matrix.md, 42181B, green=434/434), fingerprint chain CLEAN over "
    "5 domains, runner profile --daily --check PASS, writer census re-frozen then DRIFT-CLEAN "
    "files=2204 tee=1675 baselined=529 flags=0, VERDICT PASS. The +1 suite / +5 criteria against R2258 "
    "is exactly the R2259 os-seed-anchor suite joining the registry. Zero product code changed (the "
    "R2168 mixed-tree rule), so the honest score is 0 product points; state.json measured 78004B "
    "against the 78500B waterline, so fold R594 ran first (log lines 1:25, 36907 content bytes, 514 "
    "tokens, token_missing empty, 78004B -> 45329B, predicted==actual)."
)


def main():
    derived, state, export, pat = cec.recompute()
    face = json.loads(io.open(FACE, encoding='utf-8').read())
    export['export_ts'] = datetime.datetime.now().astimezone().replace(
        microsecond=0).isoformat()
    export['do'] = DO
    export['ceo_face'] = face
    export['self_drive'] = derived
    label = pat['tick_row_label']
    tick = str(state['tick'])
    rows = export.get('results')
    if not isinstance(rows, list):
        print('results container missing')
        return 2
    ticks = [r for r in rows if isinstance(r, list) and len(r) >= 2 and r[1] == label]
    if len(ticks) != 1:
        print('expected exactly one tick row, found %d' % len(ticks))
        return 2
    ticks[0][0] = tick
    rows.append(['R2260', RESULT])
    text = json.dumps(export, ensure_ascii=False, indent=2) + '\n'
    io.open(EXPORT, 'w', encoding='utf-8', newline='\n').write(text)
    print('export written bytes=%d tick=%s results=%d'
          % (len(text.encode('utf-8')), tick, len(rows)))
    return 0


if __name__ == '__main__':
    sys.exit(main())