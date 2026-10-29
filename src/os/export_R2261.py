# export_R2261.py - refresh docs/status-export.json for the R2261 window.
# Every derived field is recomputed from the live tree through the
# consistency checker's own recompute() (F3 law: nothing hardcoded that
# can be derived). The CEO-facing Chinese text lives in the sidecar
# export_face_R2261.json data file, so this source stays pure ASCII.
import datetime
import io
import json
import sys

sys.path.insert(0, 'src/os')
import check_export_consistency as cec

EXPORT = 'docs/status-export.json'
FACE = 'src/os/export_face_R2261.json'

DO = (
    "product window R2261 on the debt register first item: the per-round evidence ritual is now one "
    "callable (src/os/evidence_capture.py) - two legs of the same suite, a digest over the PASS/FAIL "
    "lines only, refusals before anything is written when a leg or an adjacent suite is red, one "
    "single-writer utf-8 LF body with a read-back proof and a refused second write, and its own exit "
    "codes per refusal"
)

RESULT = (
    "R2261 product window on the debt register first item (product-face-R2261): the top deliverable "
    "tech row (the R2259 evidence_capture seed) shipped as src/os/evidence_capture.py with AC-EVC1.."
    "AC-EVC6 pinned in that queue row BEFORE the code; anchor check at HEAD 2026-10-29 gave "
    "os-evidence-capture / test_evidence_capture / E_EVC zero-occupancy rc=1 while evidence_capture / "
    "AC-EVC hit only six text files (disclosed text occupancy, zero code occupancy). SUITE PASS 6/6 on "
    "the first run with no criterion relaxed, wired os-evidence-capture(6). This window's own evidence "
    "was produced BY the new callable instead of by an eighty-ninth hand-typed copy: EVIDENCE CAPTURE "
    "round=R2261 legs=2 identical=True adjacent=5 fails=0 verdict=CAPTURED (qa/evidence-capture-R2261.log, "
    "1886B, single writer utf-8 LF through src/os/evidence_R2261.py, never a shell redirection) plus a "
    "live CLI run on test_queue_floor.py rc=0 (qa/evidence-cli-R2261.log). The AC-EVC6 census measured 91 "
    "legacy scripts / 326455B against the 9509B callable (the count includes the thin R2261 driver, "
    "disclosed). Marking the row done dropped tech claimable to 9 against its floor of 10, so one real "
    "gap row was seeded in the same window (evidence_parity, AC-EVP1..AC-EVP6 pre-registered, five "
    "anchors git grep -F rc=1) and the gauge closed FLOOR-MET main 5/5 tech 10/10 explore 10/10. Honest "
    "score: one product face with its own suite, so 2 points. The full reconcile battery and the "
    "suite-matrix regeneration carry to R2262 (the R2168 mixed-tree rule) and are registered first=yes."
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
    rows.append(['R2261', RESULT])
    text = json.dumps(export, ensure_ascii=False, indent=2) + '\n'
    io.open(EXPORT, 'w', encoding='utf-8', newline='\n').write(text)
    print('export written bytes=%d tick=%s results=%d'
          % (len(text.encode('utf-8')), tick, len(rows)))
    return 0


if __name__ == '__main__':
    sys.exit(main())