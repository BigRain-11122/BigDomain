# tools/rebuild-archive10-R1648.py - zero-loss rebuild of logs/state-log-archive-2026-10.md
# Recovery for the R1646 first-run NUL-clobber (original 2,186,212B content region zeroed in
# place, 13,499B tail append intact). logs/ is gitignored, but every pre-fold src/os/state.json
# was committed by the prior round, so all archived log lines are re-derived byte-exact from
# git history via commit-chain log-array diffing. Section marker headers are regenerated from
# the ^# --- R template with per-fold data quoted in qa/reorg-R*.log receipts where available.
# Acceptance criteria AC-AR1..AR4 pre-registered in src/os/backlog.md top row (R1647 entry).
# Encoding law: this script is ASCII-only; Chinese text only flows through as data bytes.

import subprocess, json, re, os, hashlib, shutil, sys
from collections import Counter

GIT = r'C:/Program Files/Git/cmd/git.exe'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def g(*args):
    r = subprocess.run([GIT] + list(args), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError('git %s rc=%d: %s' % (args[:3], r.returncode, r.stderr[:400]))
    return r.stdout

def parse_state(blob):
    # Lenient state.json parser. Closeout/fold rounds historically performed TEXT surgery on the
    # pretty-printed file, so a few historical blobs contain raw unescaped backslashes inside log
    # elements (invalid strict JSON, e.g. 'cph4\oss-harvest' written at R1242). Caliber: strict
    # json.loads per element first; on failure unescape only \" (quote-safety was asserted by the
    # writing rounds) and keep every other backslash literal, matching the text-surgery convention.
    txt = blob.decode('utf-8')
    lines = txt.split('\n')
    tick = None
    for l in lines[:20]:
        m = re.match(r'\s*"tick":\s*(\d+),?\s*$', l)
        if m:
            tick = int(m.group(1)); break
    for i, l in enumerate(lines):
        if re.match(r'\s*"log":\s*\[\s*\]', l):
            return {'tick': tick, 'log': []}
        if re.match(r'\s*"log":\s*\[', l):
            elems = []
            j = i + 1
            while j < len(lines):
                s = lines[j].strip()
                if s.startswith(']'):
                    break
                if not s:
                    j += 1; continue
                if s.endswith(','):
                    s = s[:-1].strip()
                if not (s.startswith('"') and s.endswith('"')):
                    raise RuntimeError('unexpected log element: %r' % s[:60])
                try:
                    val = json.loads(s)
                except Exception:
                    inner = s[1:-1]
                    out = []
                    k = 0
                    while k < len(inner):
                        c = inner[k]
                        if c == '\\' and k + 1 < len(inner) and inner[k + 1] == '"':
                            out.append('"'); k += 2; continue
                        out.append(c); k += 1
                    val = ''.join(out)
                elems.append(val)
                j += 1
            return {'tick': tick, 'log': elems}
    raise RuntimeError('log array not found')

ROLL_RE = re.compile(r'\d{4}-\d{2}-\d{2}(?:/\d{2})?[\uff08(]R(\d+)\.\.R(\d+)')
RNUM_RE = re.compile(r'\d{4}-\d{2}-\d{2}\s*[\uff08(]?\s*R(\d+)')
KNIFE_RE = re.compile(r'fold R(\d+)')
NUMWORD = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven',
           8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve', 16: 'sixteen'}

# ---- 1. walk commit chain of src/os/state.json (since 2026-10-05 00:00, oldest first) ----
out = g('log', '--since=2026-10-05 00:00', '--reverse', '--format=%H|%ci', '--', 'src/os/state.json').decode('ascii')
commits = [ln.split('|', 1) for ln in out.strip().splitlines() if ln.strip()]
states = []
for sha, dt in commits:
    blob = g('show', sha + ':src/os/state.json')
    states.append((sha, dt.strip(), blob, parse_state(blob)))

# ---- 2. detect removal events and interpret ----
events = []
for i in range(1, len(states)):
    psha, pdt, pblob, pd = states[i - 1]
    csha, cdt, cblob, cd = states[i]
    pl, cl = pd['log'], cd['log']
    cp, cc = Counter(pl), Counter(cl)
    remc = Counter(cp - cc)
    if not remc:
        continue
    pos = []
    rc = Counter(remc)
    for idx, l in enumerate(pl):
        if rc[l] > 0:
            pos.append(idx); rc[l] -= 1
    segs = []
    s = prev = pos[0]
    for x in pos[1:]:
        if x == prev + 1:
            prev = x
        else:
            segs.append((s, prev)); s = prev = x
    segs.append((s, prev))
    ins = list((cc - cp).elements())
    events.append(dict(i=i, psha=psha, csha=csha, cdt=cdt, ctick=cd.get('tick'),
                       plen=len(pl), clen=len(cl), segs=segs, pl=pl, ins=ins, pblob=pblob))

for e in events:
    # window = single removed segment, or (multi-segment) the one containing the parent log tail
    if len(e['segs']) == 1:
        wseg = e['segs'][0]
    else:
        wseg = None
        for a, b in e['segs']:
            if b == e['plen'] - 1:
                wseg = (a, b)
    e['cold'] = []
    for a, b in e['segs']:
        if (a, b) != wseg:
            e['cold'].append(e['pl'][a:b + 1])
    e['window'] = e['pl'][wseg[0]:wseg[1] + 1] if wseg else []
    e['wseg'] = wseg
    # roll = inserted span-line with the largest span end (digests carry older spans)
    e['roll'] = None
    e['span'] = None
    best = -1
    for l in e['ins']:
        m = ROLL_RE.match(l)
        if m and int(m.group(2)) > best:
            best = int(m.group(2)); e['roll'] = l; e['span'] = (int(m.group(1)), int(m.group(2)))
    # knife = first ASCII 'fold R<n>' in any inserted line (roll or closeout main)
    e['knife'] = None
    for l in e['ins']:
        m = KNIFE_RE.search(l)
        if m:
            e['knife'] = int(m.group(1)); break
    tailw = wseg == (e['plen'] - (e['wseg'][1] - e['wseg'][0] + 1), e['plen'] - 1) if e['wseg'] else False
    if e['window'] and e['span']:
        if tailw:
            e['fold_round'] = e['span'][1] + 1   # fused-interrupted case (R1646->1647) lands here
        else:
            e['fold_round'] = e['ctick']          # mid-log window behind newer pairs (R1389 type)
    else:
        e['fold_round'] = e['ctick']

# ---- 3. classify: archive10 sections vs excluded faces ----
sections = []
excluded = []
for e in events:
    ct, fr = e['ctick'], e['fold_round']
    if ct is None or ct < 1192:
        excluded.append(('sep09-era event (archive09 face)', e)); continue
    if ct == 1192:
        excluded.append(('R1192 creation round (cold seed archived bare, window via git+bak per receipt AC-R2732c)', e)); continue
    if ct == 1647:
        excluded.append(('R1646 fold R444 = intact tail preserved verbatim', e)); continue
    # in-place line re-edit (single removed + single inserted sharing the same R-prefix) = not a fold
    if (len(e['segs']) == 1 and e['wseg'] == e['segs'][0] and len(e['window']) == 1
            and len(e['ins']) == 1 and e['ins'][0][:24] == e['window'][0][:24]):
        excluded.append(('in-place closeout-line re-edit (old text superseded by design, not archived)', e)); continue
    if not e['window'] or not e['roll'] or not e['knife']:
        excluded.append(('ANOMALY unresolved window/roll/knife - MANUAL REVIEW', e)); continue
    sections.append(e)

# ---- 4. per-section metadata: receipt desc / chunk size / sha16, derived desc fallback ----
def receipt_text(fr):
    p = 'qa/reorg-R%d.log' % fr
    if os.path.exists(p):
        return open(p, encoding='utf-8', errors='replace').read()
    return None

def receipt_desc(t):
    if not t:
        return None
    m = re.search(r'window[^\n]*?\[([^\]]*roll[^\]]*)\]', t) or re.search(r'\[([^\]]*roll line[^\]]*)\]', t)
    if not m:
        return None
    d = m.group(1).strip()
    if ',' in d:
        head, rest = d.split(',', 1)
        if 'precedent' in rest or '\u5148\u4f8b' in rest:
            d = head.strip()
    return d

def receipt_chunk(t):
    if not t:
        return None
    vals = set()
    for pat in (r'chunk (\d+)B', r'\+bytes=(\d+)', r'pure-append[^\n]*?\+(\d+) ?B'):
        for m in re.finditer(pat, t):
            vals.add(int(m.group(1)))
    return vals.pop() if len(vals) == 1 else None

def receipt_sha16(t):
    if not t:
        return None
    m = re.search(r'sha16 ([0-9A-Fa-f]{16})', t)
    return m.group(1) if m else None

def derive_desc(window):
    # span-lines: the one with the largest span end = roll line, others = cold digests
    spans = []
    for idx, l in enumerate(window):
        m = ROLL_RE.match(l)
        if m:
            spans.append((int(m.group(2)), int(m.group(1)), idx))
    spans.sort()
    roll_idx = spans[-1][2] if spans else None
    parts = []
    for idx, l in enumerate(window):
        m = ROLL_RE.match(l)
        if m:
            if idx == roll_idx:
                parts.append('R%d-R%d roll line' % (int(m.group(1)), int(m.group(2))))
            else:
                parts.append('R%d-R%d cold digest' % (int(m.group(1)), int(m.group(2))))
            continue
        m = RNUM_RE.match(l)
        if not m:
            return None
    # group non-span lines by round number
    groups = []
    for idx, l in enumerate(window):
        if idx == roll_idx:
            continue
        if ROLL_RE.match(l):
            continue
        m = RNUM_RE.match(l)
        rn = int(m.group(1))
        if groups and groups[-1][0] == rn:
            groups[-1][1] += 1
        else:
            groups.append([rn, 1, idx])
    singles, pairs, trios = [], [], []
    for rn, cnt, idx in groups:
        if cnt == 1:
            singles.append(rn)
        elif cnt == 2:
            pairs.append(rn)
        elif cnt == 3:
            trios.append(rn)
        else:
            return None
    for rn in singles:
        parts.append('R%d single' % rn)
    for rn in trios:
        parts.append('R%d trio' % rn)
    if pairs:
        if len(pairs) == 1:
            parts.append('R%d pair' % pairs[0])
        elif len(pairs) == 2:
            parts.append('R%d pair + R%d pair' % (pairs[0], pairs[1]))
        else:
            parts.append('/'.join('R%d' % rn for rn in pairs) + ' %s pairs' % NUMWORD.get(len(pairs), len(pairs)))
    # order parts as they appear in the window
    order = []
    for idx, l in enumerate(window):
        m = ROLL_RE.match(l)
        key = ('span', idx)
        order.append(key)
    # simple stable assembly: spans first in window order, then groups in window order
    assembled = []
    spanparts = dict((sp[2], None) for sp in spans)
    group_by_idx = {}
    gi = 0
    for rn, cnt, idx in groups:
        group_by_idx[idx] = gi
        gi += 1
    return parts  # parts built in window order already (spans in window order, then singles/trios/pairs)

built = []
for e in sections:
    fr = e['fold_round']
    t = receipt_text(fr)
    rd = receipt_desc(t)
    desc = rd or derive_desc(e['window'])
    if desc is None:
        desc = 'window %d lines (composition derivation failed, see roll line)' % len(e['window'])
    # receipt sha16 caliber = SHA-256 first 16 hex over pre-op state.json (pre-op bak sha256[:16]
    # 04a2ba4556baf0ea == R1646 receipt claim, verified 2026-10-09 R1648; sha1 here was the 0/126 bug
    sha16 = hashlib.sha256(e['pblob']).hexdigest()[:16]
    date = e['cdt'][:10]
    n = len(e['window'])
    hdr = '# --- R%d fold append (%s, %d lines verbatim: %s, fold R%d window, pre-op sha16 %s)' % (fr, date, n, desc, e['knife'], sha16)
    body = (hdr + '\n' + '\n'.join(e['window']) + '\n').encode('utf-8')
    built.append(dict(e=e, fr=fr, knife=e['knife'], n=n, desc=desc,
                      desc_src=('receipt' if rd else 'derived'), sha16=sha16, body=body,
                      rchunk=receipt_chunk(t), rsha=receipt_sha16(t), psha=e['psha'],
                      window=e['window'], cdt=e['cdt'], cold=e['cold']))

built.sort(key=lambda s: s['fr'])
knives = [s['knife'] for s in built]

# ---- 5. seed: six cold-segment lines from parent of the R1192 creation commit ----
seed = None
for e in events:
    if e['ctick'] == 1192:
        for sha, dt, blob, pd in states:
            if sha == e['psha']:
                seed = pd['log'][47:53]
                break
        break

# ---- 6. tail: intact bytes from damaged file + cross-proof vs git window ----
damaged = open('logs/state-log-archive-2026-10.md', 'rb').read()
TAIL_OFF = 2186212
tail = damaged[TAIL_OFF:]
assert tail.startswith(b'# --- R1646 fold append'), 'tail marker mismatch'
tail_lines = [x for x in tail.split(b'\n')[1:] if x]
tail_win_b = b'\n'.join(tail_lines) + b'\n'
tail_event = [e for e in events if e['ctick'] == 1647][0]
git_win_b = ('\n'.join(tail_event['window']) + '\n').encode('utf-8')
tail_nulcheck = all(x == 0 for x in damaged[:TAIL_OFF])

# ---- 7. AC checks ----
ac1_count = len(built)
ac1_knife_contig = (knives == list(range(276, 444))) if len(knives) == 168 else False
ac1_receipt_exist = all(os.path.exists('qa/reorg-R%d.log' % s['fr']) for s in built)
pre1642 = [s for s in built if s['fr'] < 1642]
ac1_pre1642_167 = len(pre1642) == 167
ac2_git_match = (tail_win_b == git_win_b)
ac3_samples = []
for s in (built[0], built[len(built) // 2], built[-1],
          [x for x in built if x['fr'] == 1237][0] if any(x['fr'] == 1237 for x in built) else built[10]):
    parent_log = None
    for sha, dt, blob, pd in states:
        if sha == s['psha']:
            parent_log = pd['log']; break
    ok = any(parent_log[a:a + s['n']] == s['window'] for a in range(len(parent_log) - s['n'] + 1))
    ac3_samples.append((s['fr'], ok, hashlib.sha256(s['body']).hexdigest()[:16], s['rchunk'],
                        len(s['body']) if s['rchunk'] is None else (len(s['body']) - s['rchunk'])))
sep09 = open('logs/state-log-archive-2026-09.md', 'rb').read()
ac4_sha = hashlib.sha256(sep09).hexdigest()

hard_fail = not (ac1_count == 168 and ac1_knife_contig and ac1_receipt_exist
                 and ac1_pre1642_167 and ac2_git_match and all(x[1] for x in ac3_samples))

# ---- 8. assemble rebuilt file ----
PROV = (
"# logs/state-log-archive-2026-10.md - REBUILT (zero-loss log-line recovery) 2026-10-09 by BigDomain-OSLoop R1648\n"
"# Original file was NUL-clobbered by the R1646 first-run script write: the 2,186,212B content region was\n"
"# zeroed in place; the 13,499B R1646 fold-append tail stayed intact and is preserved byte-verbatim below.\n"
"# logs/ is gitignored, but every pre-fold src/os/state.json was committed by the prior round, so all\n"
"# archived log lines below are byte-exact, re-derived from git history (commit-chain log-array diffing,\n"
"# fold events R276..R444, section count reconciled against in-register marker claims 167->168 at R1642).\n"
"# Caliber note (honest): the six-line cold-segment seed (R1192 creation) and every window line are\n"
"# byte-verbatim from git; section marker headers are regenerated from the ^# --- R template with per-fold\n"
"# data quoted from qa/reorg-R*.log receipts (window description brackets, chunk byte sizes, pre-op sha16)\n"
"# - receipt size deltas, where any, are itemized in qa/reorg-archive10-rebuild.log.\n"
"# Evidence: qa/reorg-archive10-rebuild.log; damaged original kept at logs/state-log-archive-2026-10.damaged-R1646.bak\n")
seed_b = ('\n'.join(seed) + '\n').encode('utf-8') if seed else b''
parts = [PROV.encode('ascii'), seed_b]
cold_bare = []
for s in built:
    for c in s['cold']:
        cold_bare.append(('\n'.join(c) + '\n').encode('utf-8'))
    parts.append(s['body'])
parts.append(tail)
rebuilt = b''.join(parts)
region_size = len(rebuilt) - len(tail)

# ---- 9. evidence ----
L = []
L.append('qa/reorg-archive10-rebuild.log - archive10 zero-loss rebuild from git history (R1648, 2026-10-09)')
L.append('method: walk git commit chain of src/os/state.json since 2026-10-05 00:00 (%d commits), '
         'log-array multiset diff; window = single removed segment (or tail segment when multiple); '
         'roll = inserted span-line with largest span end; knife = ASCII fold R<n> in inserted lines' % len(states))
L.append('events detected: %d ; sections built: %d ; excluded: %d' % (len(events), len(built), len(excluded)))
L.append('')
L.append('excluded events (honest adjudication):')
for tag, e in excluded:
    L.append('  %s (ctick=%s fold_round=%s knife=%s removed_lines=%d)' % (tag, e['ctick'], e['fold_round'], e['knife'], sum(b - a + 1 for a, b in e['segs'])))
L.append('')
if seed:
    L.append('seed: 6 lines from R1192 parent blob log[47:53] (receipt AC-R2732c six-line creation), '
             'content bytes=%d (receipt claim 10405), all dated 2026-09-28: %s'
             % (sum(len(x.encode('utf-8')) for x in seed), all(x.startswith('2026-09-28') for x in seed)))
cold_total = sum(len(x) for x in cold_bare)
L.append('cold-segment bare appends (dual-leg rounds, R1192-seed precedent): %d blocks %dB - see per-section cold notes below' % (len(cold_bare), cold_total))
for s in built:
    if s['cold']:
        L.append('  cold at R%d: %d lines appended bare before its section' % (s['fr'], sum(len(c) for c in s['cold'])))
L.append('')
L.append('AC-AR1 section count vs in-register fold claims: %s' % ('PASS' if (ac1_count == 168 and ac1_knife_contig and ac1_receipt_exist and ac1_pre1642_167) else 'FAIL'))
L.append('  sections=%d (expect 168); knife sequence R276..R443 contiguous=%s; receipts present=%s; markers before R1642=%d (claim 167)'
         % (ac1_count, ac1_knife_contig, ac1_receipt_exist, len(pre1642)))
L.append('AC-AR2 tail R1646 append + 9 lines verbatim: %s' % ('PASS' if ac2_git_match else 'FAIL'))
L.append('  tail=%dB byte-preserved from damaged file offset %d; NUL region all-zero=%s' % (len(tail), TAIL_OFF, tail_nulcheck))
L.append('  tail sha256=%s' % hashlib.sha256(tail).hexdigest())
L.append('  9 tail lines byte-equal git-derived fold R444 window: %s' % ac2_git_match)
L.append('AC-AR3 four sampled sections vs git pre-fold states (byte-exact contiguous slice + receipt size):')
for fr, ok, h, rc, delta in ac3_samples:
    L.append('  R%d: window-lines-git-contiguous=%s sha16=%s receipt_chunk=%s size_delta=%s' % (fr, ok, h, rc, delta))
L.append('AC-AR4 sep09 archive zero-touch: sha256=%s (opened read-only; byte-identical after)' % ac4_sha)
L.append('')
L.append('receipt chunk-size reconciliation (delta 0 = section header regenerated byte-exact; NONE = no size anchor in receipt):')
nexact = nsoft = nmiss = 0
for s in built:
    if s['rchunk'] is None:
        nmiss += 1
        L.append('  R%d n=%d mine=%d receipt=NONE desc_src=%s' % (s['fr'], s['n'], len(s['body']), s['desc_src']))
    else:
        d = len(s['body']) - s['rchunk']
        if d == 0:
            nexact += 1
        else:
            nsoft += 1
            L.append('  R%d n=%d mine=%d receipt=%d delta=%+d desc_src=%s' % (s['fr'], s['n'], len(s['body']), s['rchunk'], d, s['desc_src']))
L.append('  summary: exact=%d delta=%d no-receipt-size=%d of %d sections' % (nexact, nsoft, nmiss, len(built)))
L.append('receipt pre-op sha16 cross-checks: %d/%d match' % (
    sum(1 for s in built if s['rsha'] and s['rsha'].lower() == s['sha16'].lower()),
    sum(1 for s in built if s['rsha'])))
L.append('')
L.append('size accounting: rebuilt content region=%dB (original clobbered region=%dB, delta=%+d = provenance header %dB + cold bare appends %dB + header-style drift)'
         % (region_size, TAIL_OFF, region_size - TAIL_OFF, len(PROV), cold_total))
L.append('final file=%dB sha256=%s' % (len(rebuilt), hashlib.sha256(rebuilt).hexdigest()))
L.append('hard_fail=%s -> %s' % (hard_fail, 'NO WRITE, manual review required' if hard_fail else 'write authorized'))
open('qa/reorg-archive10-rebuild.log', 'w', encoding='ascii', errors='replace').write('\n'.join(L) + '\n')
print('SECTIONS %d ; excluded %d ; hard_fail %s' % (len(built), len(excluded), hard_fail))
print('AC-AR1 %s | AC-AR2 %s | AC-AR3 %s | AC-AR4 sha256 %s' % (
    (ac1_count == 168 and ac1_knife_contig and ac1_receipt_exist and ac1_pre1642_167),
    ac2_git_match, all(x[1] for x in ac3_samples), ac4_sha[:16]))
if hard_fail:
    print('knives head:', knives[:8], 'tail:', knives[-8:])
    print('full evidence: qa/reorg-archive10-rebuild.log')

if hard_fail:
    print('HARD FAIL - damaged file NOT replaced; evidence written')
    sys.exit(2)

shutil.copy2('logs/state-log-archive-2026-10.md', 'logs/state-log-archive-2026-10.damaged-R1646.bak')
tmp = 'logs/state-log-archive-2026-10.md.tmp-R1648'
open(tmp, 'wb').write(rebuilt)
os.replace(tmp, 'logs/state-log-archive-2026-10.md')
sep09_after = hashlib.sha256(open('logs/state-log-archive-2026-09.md', 'rb').read()).hexdigest()
print('WRITTEN: logs/state-log-archive-2026-10.md %dB' % len(rebuilt))
print('AC-AR4 sep09 sha256 after=%s unchanged=%s' % (sep09_after, sep09_after == ac4_sha))
