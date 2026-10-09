#!/usr/bin/env python3
"""logs_toolkit.py - BigDomain OSLoop logs/ toolchain reuse + hygiene.

Consolidates the mechanical pieces historically rewritten as one-off
scripts each fold round (water gauge, log-tail inventory, catalog token
extraction with zero-loss presence check) plus logs/ retention
enforcement (dry-run default).

Calibers (R1580 fold precedent):
  - content byte sums are UTF-8; waterline gate = 78500B disk size
    (P-2026-09-25-18 chain);
  - token regex = R1580 PAT (AC/BD/C/D/O/P/T/XL/OH/R families);
  - archive .md files and *.lock are PROTECTED classes: never deletable,
    even when a name also matches a prune class;
  - mtime floor: files modified within --floor-seconds (default 1800)
    are never deleted (in-flight writer protection).

Subcommands (all accept --root, default = repo root two levels up):
  gauge                  water report for src/os/state.json
  inventory              logs/ class breakdown (counts + MB)
  tail [-n N]            state.json log tail inventory (class + bytes)
  prune [--execute]      retention enforcement (dry-run default)
  catalog                window token extraction + presence check
                         (--tail N | --window-file F) --roll-file R
  fold                   state.json fold surgery (pre-op backup +
                         verbatim archive append + text-surgical log
                         window replacement, verify-then-write; window =
                         last --window-tail N log lines, mid-array
                         windows stay manual per precedent)

Fold targets the canonical on-disk PS 5.1 serialization (CRLF, 4-space
indent, two spaces after colon, 16-space log items, 12-space closing
bracket) and refuses any other layout (fail-closed E_STATE_LAYOUT).

Exit codes: 0 pass, 2 fail/unknown subcommand, 3 IO error.
Source is ASCII-only per encoding law; stdlib only; zero network.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
GATE = 78500
PAT = re.compile(r'(?:AC|BD|C|D|O|P|T|XL|OH|R)-[0-9A-Za-z][0-9A-Za-z]*(?:-[0-9A-Za-z]+)*')

# prune classes -> keep-newest counts (retention policy, R1686 AC-LT4)
PRUNE_KEEP = {'tmp-script': 60, 'preop-bak': 12, 'round-transcript': 300}
DEFAULT_FLOOR = 1800
# launcher transcript family has two naming forms: round_<ts>.out/.err and
# run_<ts>.log (first live run discovered the run_*.log family miss)
TRANSCRIPT_RE = re.compile(r'^(round|run)_.*\.(out|err|log)$')


def default_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ser_state(st):
    return json.dumps(st, ensure_ascii=False, indent=2) + '\n'


def classify(name):
    """Classify a logs/ filename. Returns class tag."""
    if 'state-log-archive' in name or name.endswith('.md'):
        return 'archive-md'
    if name.endswith('.lock'):
        return 'lock'
    if name.startswith('state-preop-') and name.endswith('.bak'):
        return 'preop-bak'
    if name.startswith('tmp_') or name.startswith('tmp-'):
        return 'tmp-script'
    if TRANSCRIPT_RE.match(name):
        return 'round-transcript'
    return 'other'


def classify_log_line(line):
    """Classify a state.json log entry for tail inventory."""
    if 'tokens:' in line:
        return 'tokens'
    if re.match(r'^\d{4}-\d{2}-\d{2}\uff08', line):
        return 'roll-window'
    if 'no-pullable' in line or 'waiting' in line:
        return 'declaration'
    return 'round-main'


def load_state(root):
    path = os.path.join(root, 'src', 'os', 'state.json')
    with open(path, 'rb') as f:
        raw = f.read()
    st = json.loads(raw.decode('utf-8'))
    return path, raw, st


def cmd_gauge(args):
    path, raw, st = load_state(args.root)
    disk = os.path.getsize(path)
    content = sum(len(x.encode('utf-8')) for x in st['log'])
    out = {
        'state_path': path,
        'disk_bytes': disk,
        'gate': GATE,
        'log_lines': len(st['log']),
        'log_content_bytes': content,
        'margin_bytes': GATE - disk,
        'fold_needed': disk > GATE,
        'tick': st.get('tick'),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_inventory(args):
    d = os.path.join(args.root, 'logs')
    stats = {}
    for entry in os.scandir(d):
        if not entry.is_file():
            continue
        c = classify(entry.name)
        s = stats.setdefault(c, {'count': 0, 'bytes': 0})
        s['count'] += 1
        try:
            s['bytes'] += entry.stat().st_size
        except OSError:
            pass
    out = {'logs_dir': d, 'classes': {}}
    total = 0
    for c in sorted(stats):
        s = stats[c]
        total += s['count']
        out['classes'][c] = {
            'count': s['count'], 'mb': round(s['bytes'] / 1048576.0, 2),
            'protected': c in ('archive-md', 'lock') or c == 'other',
            'prunable': c in PRUNE_KEEP,
        }
    out['total_files'] = total
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_tail(args):
    _, _, st = load_state(args.root)
    lines = st['log'][-args.n:]
    base = len(st['log']) - len(lines)
    for i, line in enumerate(lines):
        print(json.dumps({
            'index': base + i,
            'class': classify_log_line(line),
            'utf8_bytes': len(line.encode('utf-8')),
            'head': line[:60],
        }, ensure_ascii=False))
    return 0


def prune_plan(root, floor):
    """Compute the prune plan. Returns (plan, notes).

    plan: {class: [paths to delete]} ; files beyond keep-newest, excluding
    protected names and files newer than the mtime floor.
    """
    d = os.path.join(root, 'logs')
    now = time.time()
    buckets = {c: [] for c in PRUNE_KEEP}
    notes = {'floor_skipped': 0, 'protected_skipped': 0}
    for entry in os.scandir(d):
        if not entry.is_file():
            continue
        name = entry.name
        c = classify(name)
        if c not in PRUNE_KEEP:
            continue
        if 'state-log-archive' in name or name.endswith('.md') or name.endswith('.lock'):
            notes['protected_skipped'] += 1
            continue
        try:
            mtime = entry.stat().st_mtime
        except OSError:
            continue
        if (now - mtime) < floor:
            notes['floor_skipped'] += 1
            continue
        buckets[c].append((mtime, os.path.join(d, name)))
    plan = {}
    for c, items in buckets.items():
        items.sort(reverse=True)  # newest first
        victims = [p for _, p in items[PRUNE_KEEP[c]:]]
        if victims:
            plan[c] = victims
    return plan, notes


def cmd_prune(args):
    plan, notes = prune_plan(args.root, args.floor_seconds)
    total = sum(len(v) for v in plan.values())
    summary = {c: len(v) for c, v in sorted(plan.items())}
    print(json.dumps({
        'mode': 'execute' if args.execute else 'dry-run',
        'policy': {'keep_newest': PRUNE_KEEP, 'floor_seconds': args.floor_seconds},
        'to_delete': summary,
        'to_delete_total': total,
        **notes,
    }, ensure_ascii=False, indent=2))
    if not args.execute:
        return 0
    deleted = {}
    failed = 0
    for c, paths in plan.items():
        n = 0
        for p in paths:
            try:
                os.remove(p)
                n += 1
            except OSError:
                failed += 1
        if n:
            deleted[c] = n
    actual_total = sum(deleted.values())
    mismatch = [c for c in summary if deleted.get(c, 0) != summary[c]]
    print(json.dumps({
        'deleted': deleted, 'deleted_total': actual_total,
        'failed': failed, 'predicted_total': total,
        'prediction_match': not mismatch and actual_total == total,
        'mismatch_classes': mismatch,
    }, ensure_ascii=False, indent=2))
    if mismatch or actual_total != total:
        return 2
    return 0


def cmd_catalog(args):
    if bool(args.tail) == bool(args.window_file):
        print('error: exactly one of --tail or --window-file is required', file=sys.stderr)
        return 2
    if not args.roll_file:
        print('error: --roll-file is required', file=sys.stderr)
        return 2
    if args.tail:
        _, _, st = load_state(args.root)
        window = st['log'][-args.tail:]
    else:
        with open(args.window_file, encoding='utf-8') as f:
            window = [l for l in (x.rstrip('\n').rstrip('\r') for x in f) if l.strip()]
    toks = set()
    for line in window:
        toks |= set(PAT.findall(line))
    with open(args.roll_file, encoding='utf-8') as f:
        roll = f.read()
    missing = sorted(t for t in toks if t not in roll)
    out = {
        'window_lines': len(window),
        'tokens_total': len(toks),
        'tokens': sorted(toks),
        'missing_in_roll': missing,
        'pass': not missing,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if not missing else 2


# --- fold surgery (R1687 slice, AC-LT8..LT14 pre-registered in tech.md) ---

def ps_escape(s):
    """Serialize one log string as a JSON literal in the on-disk PS 5.1
    style: json escaping plus JavaScriptSerializer-sensitive chars
    (observed live escapes: \\u003c for '<')."""
    j = json.dumps(s, ensure_ascii=False)
    for ch, esc in (('<', '\\u003c'), ('>', '\\u003e'),
                    ('&', '\\u0026'), ("'", '\\u0027')):
        j = j.replace(ch, esc)
    return j


def split_ps_layout(text, log_len):
    """Locate the log array item lines in the canonical PS layout.
    Returns (lines, log_start_idx, item_idx_list, close_idx) or None."""
    lines = text.split('\r\n')
    log_start = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith('"log"') and s.endswith('['):
            log_start = i
            break
    if log_start is None:
        return None
    items, close_idx = [], None
    for j in range(log_start + 1, len(lines)):
        if lines[j].strip() == ']':
            close_idx = j
            break
        if not re.match(r'^ {16}"', lines[j]):
            return None
        items.append(j)
    if close_idx is None or len(items) != log_len:
        return None
    return lines, log_start, items, close_idx


def cmd_fold(args):
    if args.window_tail < 1:
        print('error: --window-tail must be >= 1', file=sys.stderr)
        return 2
    for req, val in (('--round', args.round), ('--fold-no', args.fold_no),
                     ('--desc', args.desc), ('--summary-file', args.summary_file)):
        if not val:
            print('error: %s is required' % req, file=sys.stderr)
            return 2
    with open(args.summary_file, encoding='utf-8') as f:
        slines = [l for l in (x.rstrip('\n').rstrip('\r') for x in f) if l.strip()]
    if len(slines) != 1:
        print('error: summary file must hold exactly one non-empty line (got %d)'
              % len(slines), file=sys.stderr)
        return 2
    summary = slines[0]

    path, raw, st = load_state(args.root)
    text = raw.decode('utf-8')
    if '\r\n' not in text:
        print('error: E_STATE_LAYOUT: CRLF layout not found (refusing)', file=sys.stderr)
        return 2
    layout = split_ps_layout(text, len(st['log']))
    if layout is None:
        print('error: E_STATE_LAYOUT: PS item-line layout mismatch (refusing)',
              file=sys.stderr)
        return 2
    lines, log_start, item_idx, close_idx = layout
    if args.window_tail > len(st['log']):
        print('error: --window-tail exceeds log length', file=sys.stderr)
        return 2

    n = args.window_tail
    window = st['log'][-n:]
    keep_count = len(st['log']) - n
    new_log = st['log'][:-n] + [summary]

    # verifications (all BEFORE any write; R1157 write-before-verify lesson)
    toks = set()
    for line in window:
        toks |= set(PAT.findall(line))
    missing = sorted(t for t in toks if t not in summary)

    summary_literal = ' ' * 16 + ps_escape(summary)
    first_window_idx = log_start + 1 + keep_count
    new_lines = (lines[:first_window_idx] + [summary_literal]
                 + lines[close_idx:])
    new_text = '\r\n'.join(new_lines)
    predicted = len(new_text.encode('utf-8'))
    gate_ok = predicted + args.reserve_bytes <= GATE

    now = datetime.now(CST)
    sha16 = hashlib.sha256(raw).hexdigest()[:16]
    backup_path = os.path.join(args.root, 'logs', 'state-preop-%s.bak' % args.round)
    archive = args.archive_file or os.path.join(
        args.root, 'logs', 'state-log-archive-%s.md' % now.strftime('%Y-%m'))
    date = now.strftime('%Y-%m-%d')
    header = ('# --- %s fold append (%s, %d lines verbatim: %s, '
              'fold R%s window, pre-op sha16 %s)') % (
        args.round, date, len(window), args.desc, args.fold_no, sha16)
    archive_exists = os.path.exists(archive)
    appendix = (header + '\n' + '\n'.join(window) + '\n').encode('utf-8')
    preamble = None
    if archive_exists:
        with open(archive, 'rb') as f:
            blob = f.read()
        if blob and not blob.endswith(b'\n'):
            appendix = b'\n' + appendix
    elif args.allow_create:
        preamble = ('# logs/%s (created by logs_toolkit.py fold --allow-create %s)\n'
                    % (os.path.basename(archive), date)).encode('utf-8')

    verdicts = {
        'token_missing': missing,
        'token_ok': not missing,
        'gate_ok': gate_ok,
        'predicted_bytes': predicted,
        'reserve_bytes': args.reserve_bytes,
        'gate': GATE,
    }
    plan = {
        'mode': 'execute' if args.execute else 'dry-run',
        'round': args.round, 'fold_no': args.fold_no,
        'window_lines': len(window),
        'window_content_bytes': sum(len(x.encode('utf-8')) for x in window),
        'summary_head': summary[:60],
        'preop_sha16': sha16,
        'backup_path': backup_path,
        'archive_file': archive,
        'archive_header': header,
        'state_path': path,
        'pre_bytes': len(raw),
        'new_log_len': len(new_log),
        **verdicts,
    }
    fail = []
    if missing:
        fail.append('token-missing')
    if not gate_ok:
        fail.append('gate-exceed')
    if not archive_exists and not args.allow_create:
        fail.append('archive-missing')
    plan['would_fail'] = fail

    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 2 if fail else 0

    if fail:
        print('error: refusing fold, failed checks: %s' % ','.join(fail),
              file=sys.stderr)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 2

    # step 2: pre-op backup (byte-identical, read back)
    with open(backup_path, 'wb') as f:
        f.write(raw)
    with open(backup_path, 'rb') as f:
        if f.read() != raw:
            print('error: backup verify failed', file=sys.stderr)
            return 2

    # step 3: archive append (single write, byte-verified)
    if archive_exists:
        with open(archive, 'rb') as f:
            before_blob = f.read()
        with open(archive, 'ab') as f:
            f.write(appendix)
        with open(archive, 'rb') as f:
            after_blob = f.read()
        archive_ok = after_blob == before_blob + appendix
    else:
        blob = preamble + appendix
        with open(archive, 'wb') as f:
            f.write(blob)
        with open(archive, 'rb') as f:
            archive_ok = f.read() == blob
    if not archive_ok:
        print('error: archive append verification failed', file=sys.stderr)
        return 2

    # step 4: state.json write (temp + atomic replace), verify-then-read
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix='.state-fold-')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(new_text.encode('utf-8'))
        os.replace(tmp, path)
    except OSError:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    with open(path, 'rb') as f:
        post_raw = f.read()
    post_st = json.loads(post_raw.decode('utf-8'))
    ok_write = (post_raw == new_text.encode('utf-8')
                and post_st['log'] == new_log
                and os.path.getsize(path) == predicted)
    result = {
        **plan,
        'post_bytes': os.path.getsize(path),
        'predicted_eq_actual': ok_write,
        'appendix_bytes': len(appendix),
        'archive_appended': True,
        'backup_written': True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not ok_write:
        print('error: post-write verification failed', file=sys.stderr)
        return 2
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog='logs_toolkit.py', description=__doc__)
    p.add_argument('--root', default=default_root(), help='repo root (default: auto)')
    sub = p.add_subparsers(dest='cmd', required=True)

    sub.add_parser('gauge', help='water report for src/os/state.json')
    sub.add_parser('inventory', help='logs/ class breakdown')
    pt = sub.add_parser('tail', help='state.json log tail inventory')
    pt.add_argument('-n', type=int, default=10)
    pp = sub.add_parser('prune', help='logs/ retention enforcement')
    pp.add_argument('--execute', action='store_true', help='actually delete (default: dry-run)')
    pp.add_argument('--floor-seconds', type=int, default=DEFAULT_FLOOR)
    pc = sub.add_parser('catalog', help='window token extraction + presence check')
    pc.add_argument('--tail', type=int, help='window = last N state log lines')
    pc.add_argument('--window-file', help='window = non-empty lines of this file')
    pc.add_argument('--roll-file', required=False, help='roll/summary text to check presence against')
    pf = sub.add_parser('fold', help='state.json fold surgery (verify-then-write)')
    pf.add_argument('--round', help='round label e.g. R1687 (backup + header naming)')
    pf.add_argument('--fold-no', help='fold knife number e.g. 455 (header)')
    pf.add_argument('--desc', help='window description for the archive header')
    pf.add_argument('--window-tail', type=int, default=0, help='window = last N log lines')
    pf.add_argument('--summary-file', help='file holding exactly one non-empty summary line')
    pf.add_argument('--reserve-bytes', type=int, default=3000)
    pf.add_argument('--archive-file', help='override archive path (default: logs/state-log-archive-<month>.md)')
    pf.add_argument('--allow-create', action='store_true', help='create archive if missing (else fail-closed)')
    pf.add_argument('--execute', action='store_true', help='perform surgery (default: dry-run, zero mutation)')

    args = p.parse_args(argv)
    handlers = {'gauge': cmd_gauge, 'inventory': cmd_inventory, 'tail': cmd_tail,
                'prune': cmd_prune, 'catalog': cmd_catalog, 'fold': cmd_fold}
    if args.cmd not in handlers:
        return 2
    try:
        return handlers[args.cmd](args)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print('error: %s' % e, file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
