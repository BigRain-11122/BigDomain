# export_R2262.py - refresh docs/status-export.json for the R2262 window.
# Every derived field is recomputed from the live tree through the
# consistency checker's own recompute() (F3 law: nothing hardcoded that
# can be derived). The CEO-facing Chinese text lives in the sidecar
# export_face_R2262.json data file, so this source stays pure ASCII.
import datetime
import io
import json
import sys

sys.path.insert(0, 'src/os')
import check_export_consistency as cec

EXPORT = 'docs/status-export.json'
FACE = 'src/os/export_face_R2262.json'

DO = (
    "verification window R2262 on the debt register first item: the full reconcile battery on the "
    "committed tree went RED first (reconcile-daily-census cd7 drift) because the R2260 battery "
    "evidence log carried 35 CRLF lines appended by that round's own follow-up AFTER it froze the "
    "census baseline; the log was rewritten through run_identity.normalize (crlf 35->0, payload line "
    "set identical) and the battery was re-run on the committed repair tree to RUNNER PASS"
)

RESULT = (
    "R2262 verification window on the debt register first item (reconcile-battery-R2262): first run "
    "RED, RUNNER FAIL with 2 failed assertions in 861.6s (qa/reconcile-all-R2262.log, kept as the red "
    "leg) - suite reconcile-daily-census criterion cd7-live-real-tree exit=2 drift, plus the aggregate "
    "control that counts green suites (434/435) and the criteria total. The root cause was a real "
    "evidence-hygiene defect, not a flake: qa/reconcile-all-R2260.log carried 35 CRLF lines because "
    "the R2260 follow-up appended captured subprocess bodies verbatim, and the census re-freeze in "
    "that same follow-up ran BEFORE the append, so the file was frozen as tee and the next census "
    "would always see class=other. Repair: src/os/evidence_normalize_R2262.py rewrites the file "
    "through run_identity.normalize - crlf 35->0, bare_cr 0, payload line set identical, sha16 "
    "2b9e9a1afbff90ba before and after (768425B -> 768390B) - and the census re-checked DRIFT-CLEAN "
    "with files=2207 flags=0. Second run on the committed repair tree (commit bf07f5e5): RUNNER PASS "
    "435/435 suites plus controls 7/7 in 745.3s, expected criteria total=3587, birth-site TMP RECLAIM "
    "932/932 worlds 326.57 MiB busy=0 failed=0 (qa/reconcile-all-R2262-retry.log, single-writer utf-8 "
    "LF through battery_stream.py, never a shell redirection). Four follow-up sections all PASS via "
    "src/os/battery_followup_R2262.py, which now CRLF-normalizes every captured body and runs the "
    "census LAST: matrix regenerated to 435 suites / 3587 criteria and read back byte-identical "
    "(docs/sandbox-suite-matrix.md, 42285B, green=435/435), fingerprint chain CLEAN over five domains, "
    "runner profile --daily --check PASS, writer census re-frozen then DRIFT-CLEAN files=2208 tee=1679 "
    "baselined=529 flags=0, and the log's own EOL self-check crlf=0 bare_cr=0 bom=False over 769003B. "
    "The +1 suite / +6 criteria against R2260 is exactly the R2261 os-evidence-capture suite joining "
    "the registry. Zero product code changed (the R2168 mixed-tree rule), so the honest score is 0 "
    "product points; the two new modules are the repair helper and the hardened follow-up."
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
    rows.append(['R2262', RESULT])
    text = json.dumps(export, ensure_ascii=False, indent=2) + '\n'
    io.open(EXPORT, 'w', encoding='utf-8', newline='\n').write(text)
    print('export written bytes=%d tick=%s results=%d'
          % (len(text.encode('utf-8')), tick, len(rows)))
    return 0


if __name__ == '__main__':
    sys.exit(main())