"""repair_R3365_archive_marker.py - one named correction in a live archive.

Measured defect (R3365): the R3351 fold was executed through
state_fold.fold() with the FOLD NUMBER in the round slot, so the archive
carries a header whose round token is "642". The census reader recovers a
round from R##### form or a legacy bare #### form only, so that section landed
as unlabelled_sections=1 and the suite read pass=false (exit 2).

This script changes ONE header token and nothing else:
    "# --- 642 fold append ("  ->  "# --- R3351 fold append ("
R3351 is the round the fold actually served, and the ledger line the fold
itself wrote says so verbatim ("R3351 fold 642 of log lines 1..123 ...").

Guarantees, all asserted before the write and re-read after it:
  * the marker occurs exactly once in the archive;
  * a line-by-line comparison shows exactly one changed line, and that line is
    the header (payload bytes are untouched);
  * the section's "N lines verbatim" declaration still equals the number of
    body lines that follow the header;
  * LF/CRLF dialect and total line count are unchanged.
--execute writes; without it the script prints the plan and writes nothing.
"""
import hashlib
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARCHIVE = os.path.join(REPO, 'logs', 'state-log-archive-2026-11.md')
OLD = '# --- 642 fold append ('
NEW = '# --- R3351 fold append ('
DECLARED = re.compile(r'(\d+) lines verbatim')


def main(argv):
    execute = '--execute' in argv
    with io.open(ARCHIVE, 'rb') as fh:
        raw = fh.read()
    text = raw.decode('utf-8')
    hits = text.count(OLD)
    already = text.count(NEW)
    if hits == 0 and already == 1:
        line = [ln for ln in text.split('\n') if ln.startswith(NEW)][0]
        declared = int(DECLARED.search(line).group(1))
        print('already corrected: %r declared=%d (nothing to do)'
              % (line[:48], declared))
        return 0
    if hits != 1:
        print('REFUSE marker occurrences=%d (need exactly 1)' % hits)
        return 2
    new_text = text.replace(OLD, NEW, 1)
    old_lines = text.split('\n')
    new_lines = new_text.split('\n')
    if len(old_lines) != len(new_lines):
        print('REFUSE line count moved %d -> %d' % (len(old_lines), len(new_lines)))
        return 2
    changed = [i for i, (a, b) in enumerate(zip(old_lines, new_lines)) if a != b]
    if len(changed) != 1:
        print('REFUSE changed lines=%d (need exactly 1)' % len(changed))
        return 2
    at = changed[0]
    if not (old_lines[at].startswith(OLD) and new_lines[at].startswith(NEW)):
        print('REFUSE the single changed line is not the marker: %r'
              % (old_lines[at][:60],))
        return 2
    # declared count vs body lines, measured the way the census measures it:
    # non-empty verbatim body lines only
    declared = int(DECLARED.search(new_lines[at]).group(1))
    body = 0
    for line in new_lines[at + 1:]:
        if line.startswith('# --- '):
            break
        if line.strip():
            body += 1
    if body != declared:
        print('REFUSE declaration says %d lines, body holds %d' % (declared, body))
        return 2
    print('plan: line %d  %r -> %r' % (at + 1, old_lines[at][:48], new_lines[at][:48]))
    print('pre  bytes=%d sha256=%s' % (len(raw), hashlib.sha256(raw).hexdigest()[:16]))
    print('post bytes=%d sha256=%s'
          % (len(new_text.encode('utf-8')),
             hashlib.sha256(new_text.encode('utf-8')).hexdigest()[:16]))
    print('declared=%d body_lines=%d payload_untouched=%s'
          % (declared, body, changed == [at]))
    if not execute:
        print('mode=dry-run (nothing written)')
        return 0
    with io.open(ARCHIVE, 'wb') as fh:
        fh.write(new_text.encode('utf-8'))
    with io.open(ARCHIVE, 'rb') as fh:
        back = fh.read()
    payload = new_text.encode('utf-8')
    ok = (back == payload and back.count(OLD.encode('utf-8')) == 0
          and back.count(NEW.encode('utf-8')) == 1)
    print('mode=execute wrote=%s readback=%s' % (len(back), 'OK' if ok else 'DIFF'))
    return 0 if ok else 3


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
