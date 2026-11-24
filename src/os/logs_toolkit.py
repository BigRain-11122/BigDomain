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
  weights [--top N]      per-item log weight: bytes, bare round label, share
                         of the log and of the fold gate, heaviest first
                         (read-only; totals always cover every item)
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
  census                 archive reverse reconciliation (read-only):
                         section integrity (declared vs actual lines),
                         live-log section pointer resolution, and the
                         informational token census (not_embedded /
                         roll_native / archive_only)

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
# R3373 (AC-LTP5): the byte width the replacement summary item line is assumed
# to occupy when `fold --plan-only` is given no --summary-file. The plan reports
# it back as summary_source=assumed; only the byte prediction moves with it,
# never the minimality reading (a wider summary cannot make a smaller window fit).
PLAN_SUMMARY_ITEM_BYTES = 200
PAT = re.compile(r'(?:AC|BD|C|D|O|P|T|XL|OH|R)-[0-9A-Za-z][0-9A-Za-z]*(?:-[0-9A-Za-z]+)*')
# R3378 (AC-2PS1..AC-2PS6): the fold summary has two parts - one human sentence
# and the token list - and both are written by ONE composer, so a fold cannot
# trade readability for verifiability. The token set comes from the folded
# window's own PAT matches, never from the caller's prose.
SUMMARY_SEP = ' | tokens: '
SUMMARY_NONE = 'none'
SUMMARY_BUDGET = 1200

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


EVIDENCE_LOG_CLASS = 'qa-evidence'
EVIDENCE_OTHER_CLASS = 'evidence-other'
# Every class that retention must never select. The two evidence classes are
# here because qa/ is the shipped proof surface, not a log scratch area.
PROTECTED_CLASSES = frozenset(['archive-md', 'lock', 'other',
                               EVIDENCE_LOG_CLASS, EVIDENCE_OTHER_CLASS])


def classify_evidence(name):
    """Classify a qa/ evidence-directory filename.

    Evidence is grouped by kind rather than by retention family: a .log is
    a run record, anything else is a side-car artifact.
    """
    if name.endswith('.log'):
        return EVIDENCE_LOG_CLASS
    return EVIDENCE_OTHER_CLASS


def _root_classifier(label):
    """The logs/ root keeps the historical classifier; every other root is
    treated as an evidence root (label `logs` is the only special case, so a
    caller naming a root `logs` always gets the legacy dialect)."""
    return classify if label == 'logs' else classify_evidence


def inventory_scan(roots):
    """Adaptive multi-root inventory (AC-LTI1..AC-LTI7).

    roots: ordered list of (label, directory). Every regular file is counted
    once per (st_dev, st_ino) - a second appearance of the same inode
    (overlapping roots, hard links) is reported in `duplicates` instead of
    being counted again, so the catalog can never be inflated by a root
    declared twice. Nothing is cached: a file that appears between two calls
    is seen by the second one.

    Raises ValueError when a root is not a directory, so a caller cannot get
    a green reading for a root it failed to read.
    """
    seen = {}
    classes = {}
    root_stats = {}
    counted = 0
    duplicates = 0
    for label, path in roots:
        if not os.path.isdir(path):
            raise ValueError('root is not a directory: %s=%s' % (label, path))
        classify_fn = _root_classifier(label)
        files = 0
        for entry in sorted(os.scandir(path), key=lambda e: e.name):
            if not entry.is_file():
                continue
            files += 1
            counted += 1
            try:
                # os.stat(path), not entry.stat(): the scandir-cached stat on
                # Windows reports st_dev/st_ino as 0 for every entry, which
                # would collapse the whole tree into one inode.
                st = os.stat(entry.path)
            except OSError:
                continue
            key = (st.st_dev, st.st_ino)
            if key in seen:
                duplicates += 1
                continue
            seen[key] = entry.path
            c = classify_fn(entry.name)
            slot = classes.setdefault(c, {'count': 0, 'bytes': 0})
            slot['count'] += 1
            slot['bytes'] += st.st_size
        root_stats[label] = {'dir': path, 'files': files}
    return {'classes': classes, 'roots': root_stats,
            'counted_entries': counted, 'total_files': len(seen),
            'duplicates': duplicates}


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


ROUND_TAG = re.compile(r'\bR\d{3,5}\b')


def round_tag(item):
    """First bare round label in one log item (AC-LTW6).

    A bare round number is not a PAT token: PAT requires a hyphen after the
    family name, so `R1238` never matches it (R3176 a measurement). This is
    the separate extractor for that shape, not a second token law.
    """
    m = ROUND_TAG.search(item)
    return m.group(0) if m else None


def weight_report(state_path, st, top_n):
    """Per-item log weight, share of the log and share of the fold gate.

    Read-only: the weights are derived from the parsed log the gauge face
    already reads, so two faces cannot disagree about `log_content_bytes`.
    """
    log = st.get('log') or []
    rows = []
    for i, item in enumerate(log):
        rows.append({'index': i, 'round': round_tag(item),
                     'bytes': len(item.encode('utf-8'))})
    total = sum(r['bytes'] for r in rows)
    for r in rows:
        r['share_of_log'] = (r['bytes'] / total) if total else 0.0
        r['share_of_gate'] = r['bytes'] / GATE
    ordered = sorted(rows, key=lambda r: (-r['bytes'], r['index']))
    return {
        'state_path': state_path,
        'item_count': len(rows),
        'gate': GATE,
        'log_content_bytes': total,
        'sum_item_bytes': sum(r['bytes'] for r in rows),
        'residual_bytes': total - sum(r['bytes'] for r in rows),
        'shares_sum': sum(r['share_of_log'] for r in rows),
        'top_n': top_n,
        'top': ordered[:top_n],
    }


def cmd_weights(args):
    path, raw, st = load_state(args.root)
    if args.top < 0:
        print('error: --top must be >= 0', file=sys.stderr)
        return 2
    print(json.dumps(weight_report(path, st, args.top), ensure_ascii=False, indent=2))
    return 0


# R3379 (AC-BRC1..AC-BRC6): a bare round label is not a PAT token - PAT needs a
# hyphen right after the family name - so a fold whose only record of a round is
# that bare number leaves the live block no way to find it. This face answers the
# pre-fold question "which bare rounds in this window would become unfindable"
# without widening the token law: the separators below refuse a round that sits
# inside a PAT token (AC-R3379) on either side.
BARE_ROUND = re.compile(r'(?<![0-9A-Za-z-])R\d{3,5}(?![0-9A-Za-z-])')


def rounds_report(state_path, st, mode, start, end, summary_text):
    """Which bare round labels in log[start:end] (1-based) survive a fold.

    A round survives if the replacement summary names it, or if a log item
    outside the window still carries it. Read-only and clock-free: the summary
    text is the only input beyond state.json.
    """
    log = st.get('log') or []
    window = log[start - 1:end]
    outside = log[:start - 1] + log[end:]
    summary_rounds = set(BARE_ROUND.findall(summary_text or ''))
    live_rounds = set()
    for item in outside:
        live_rounds |= set(BARE_ROUND.findall(item))
    labels = sorted({m for item in window for m in BARE_ROUND.findall(item)})
    rows = []
    for label in labels:
        in_summary = label in summary_rounds
        in_live = label in live_rounds
        rows.append({'round': label, 'in_summary': in_summary,
                     'in_live': in_live, 'lost': not (in_summary or in_live)})
    return {
        'state_path': state_path,
        'window': {'mode': mode, 'start': start, 'end': end,
                   'items': len(window)},
        'summary_file': None,
        'total': len(rows),
        'covered_by_summary': sum(1 for r in rows if r['in_summary']),
        'covered_by_live': sum(1 for r in rows if r['in_live']),
        'lost': sum(1 for r in rows if r['lost']),
        'rounds': rows,
    }


def lost_rounds(st, start, end, summary_text):
    """Bare rounds the fold would erase: read off the shipped `rounds` face.

    AC-RLW3: the writer refuses on this list and the read-only pre-fold face
    prints it, so the two can never disagree - there is no second arithmetic.
    """
    rep = rounds_report('<fold>', st, 'slice', start, end, summary_text)
    return [row['round'] for row in rep['rounds'] if row['lost']]


def cmd_rounds(args):
    """Pre-fold bare-round pointer reading (AC-BRC1). Writes nothing."""
    path, raw, st = load_state(args.root)
    n = len(st.get('log') or [])
    if args.window_slice:
        try:
            start, end = [int(x) for x in args.window_slice.split(':')]
        except ValueError:
            print('error: --window-slice expects START:END', file=sys.stderr)
            return 2
        if start < 1 or end < start or end > n:
            print('error: E_WINDOW_RANGE: --window-slice out of log bounds',
                  file=sys.stderr)
            return 2
        mode = 'slice'
    elif args.window_tail:
        if args.window_tail < 1 or args.window_tail > n:
            print('error: --window-tail exceeds log length', file=sys.stderr)
            return 2
        mode, start, end = 'tail', n - args.window_tail + 1, n
    else:
        mode, start, end = 'all', 1, n
    summary_text = ''
    if args.file:
        summary_text, err = one_summary_line(args.file)
        if err:
            print('error: ' + err, file=sys.stderr)
            return 2
    out = rounds_report(path, st, mode, start, end, summary_text)
    out['summary_file'] = args.file
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if args.strict and out['lost']:
        return 4
    return 0


def inventory_roots(args):
    """Resolve the inventory roots for one CLI call.

    The logs/ root is always first (historical contract). `--roots LABEL=DIR`
    appends explicit roots in declaration order; `--with-qa` appends qa/ when
    no `qa` label was declared. Returns (roots, error_code).
    """
    roots = [('logs', os.path.join(args.root, 'logs'))]
    labels = {'logs'}
    for spec in (getattr(args, 'roots', None) or []):
        if '=' not in spec:
            print('error: --roots expects LABEL=DIR', file=sys.stderr)
            return None, 2
        label, path = spec.split('=', 1)
        label, path = label.strip(), path.strip()
        if not label or not path:
            print('error: --roots expects LABEL=DIR', file=sys.stderr)
            return None, 2
        if label in labels:
            print('error: duplicate root label: %s' % label, file=sys.stderr)
            return None, 2
        labels.add(label)
        full = path if os.path.isabs(path) else os.path.join(args.root, path)
        roots.append((label, full))
    if getattr(args, 'with_qa', False) and 'qa' not in labels:
        roots.append(('qa', os.path.join(args.root, 'qa')))
    return roots, 0


def cmd_inventory(args):
    roots, rc = inventory_roots(args)
    if roots is None:
        return rc
    scan = inventory_scan(roots)
    out = {'logs_dir': roots[0][1], 'classes': {}}
    for c in sorted(scan['classes']):
        s = scan['classes'][c]
        out['classes'][c] = {
            'count': s['count'], 'mb': round(s['bytes'] / 1048576.0, 2),
            'protected': c in PROTECTED_CLASSES,
            'prunable': c in PRUNE_KEEP,
        }
    out['total_files'] = scan['total_files']
    # Extra keys appear only when more than one root was declared, so the
    # historical single-root contract stays byte-identical (AC-LTI1).
    if len(roots) > 1:
        out['roots'] = scan['roots']
        out['counted_entries'] = scan['counted_entries']
        out['duplicates'] = scan['duplicates']
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


# --- closeout EOL repair (R1705 slice, AC-EO1..EO6 pre-registered in tech.md) ---
# R1697/R1704 both hit fold's E_STATE_LAYOUT refusal because a round's
# closeout wrote state.json with bare-LF line endings. This subcommand
# toolizes the manual byte surgery done in those rounds: report the EOL
# profile, and repair bare-LF terminators to CRLF with content bytes and
# JSON semantics untouched (verify-then-write).

BARE_LF = re.compile(r'(?<!\r)\n')


def item_indent_caliber(items):
    """Derive the log-item indent FROM THE DOCUMENT (R2747).

    The canonical writer emits two-space items while the legacy R1710
    form carries sixteen. Both are healthy; an eight-space block (the
    R1710 json.dump collapse) or a mixed block is disease. Returns the
    caliber (2 or 16) when the block is uniform and known, else None.
    """
    seen = set()
    for ln in items:
        m = re.match(r'^( +)"', ln)
        seen.add(len(m.group(1)) if m else -1)
    if len(seen) != 1:
        return None
    only = next(iter(seen))
    return only if only in (2, 16) else None


def eol_profile(raw):
    """Count terminator classes in raw (utf-8 bytes) without mutating."""
    text = raw.decode('utf-8')
    total_lf = text.count('\n')
    crlf = text.count('\r\n')
    bare_lf = total_lf - crlf
    lone_cr = text.count('\r') - crlf
    # indent conservation (R1710 lesson: a closeout json.dump re-write
    # destroyed the 16-space log-item canonical indent while CRLF stayed
    # healthy, escaping the eol check for three rounds). Same regex class
    # as split_ps_layout's item-line gate: '^ {16}"'.
    lines = re.split(r'\r\n|\n', text)
    log_start = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith('"log"') and s.endswith('['):
            log_start = i
            break
    log_block_found = log_start is not None
    log_item_lines = indent16 = indent_anomaly = 0
    caliber = None
    if log_block_found:
        # R2747: the close line may carry a trailing comma ('  ],') whenever
        # a sibling key follows the log array, which is exactly how the real
        # state.json closes. Comparing strip() == ']' alone never saw that
        # close and counted every line after the array as an item.
        items = []
        for ln in lines[log_start + 1:]:
            s = ln.strip()
            if s == ']' or s == '],':
                break
            if not s:
                continue
            items.append(ln)
        log_item_lines = len(items)
        caliber = item_indent_caliber(items)
        indent16 = sum(1 for ln in items if ln.startswith(' ' * 16 + '"'))
        indent_anomaly = 0 if caliber is not None else len(items)
    return {
        'bytes': len(raw),
        'total_lf': total_lf,
        'crlf': crlf,
        'bare_lf': bare_lf,
        'lone_cr': lone_cr,
        'ends_with_eol': text.endswith('\n') or text.endswith('\r'),
        'layout_ok': bare_lf == 0 and lone_cr == 0,
        'log_block_found': log_block_found,
        'log_item_lines': log_item_lines,
        'indent16_lines': indent16,
        'indent_anomaly': indent_anomaly,
        'indent_caliber': caliber,
        'indent_ok': (not log_block_found) or indent_anomaly == 0,
    }


def eol_content_lines(text):
    """Terminator-insensitive line-content sequence (CRLF and LF both split)."""
    return re.split(r'\r\n|\n', text)


def fix_indent_text(text):
    """Re-indent log item lines to the 16-space canonical (R1710 manual
    byte surgery toolized, AC-FI2). Only item lines whose stripped body
    starts with a JSON string quote are touched; content bytes and each
    line's own EOL terminator are preserved (EOL disease stays with
    --fix; two diseases, two repairs). Returns (fixed_text, repaired)
    or (None, 0) when no log block exists (non-state shape)."""
    lines = text.splitlines(True)
    log_start = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith('"log"') and s.endswith('['):
            log_start = i
            break
    if log_start is None:
        return None, 0
    out = list(lines)
    repaired = 0
    for j in range(log_start + 1, len(lines)):
        s = lines[j].strip()
        if s == ']':
            break
        if not s:
            continue
        body = lines[j]
        eol = ''
        if body.endswith('\r\n'):
            body, eol = body[:-2], '\r\n'
        elif body.endswith('\n'):
            body, eol = body[:-1], '\n'
        core = body.lstrip(' ')
        if core.startswith('"') and len(body) - len(core) != 16:
            out[j] = ' ' * 16 + core + eol
            repaired += 1
    return ''.join(out), repaired


def eol_fix_indent(args, path, raw, prof):
    """--fix-indent face: indent-only repair, dry-run default (AC-FI2..FI4)."""
    text = raw.decode('utf-8')
    out = {'file': path,
           'mode': 'fix-indent-execute' if args.execute else 'fix-indent-dry-run'}
    out.update(prof)
    fixed, repaired = fix_indent_text(text)
    if fixed is None:
        out['written'] = False
        out['note'] = 'no log block found (non-state shape): nothing to fix'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    fixed_raw = fixed.encode('utf-8')
    new_prof = eol_profile(fixed_raw)
    out['repaired_lines'] = repaired
    out['predicted_bytes'] = len(fixed_raw)
    out['delta_bytes'] = len(fixed_raw) - len(raw)
    # triple verification, all before any write (AC-FI3)
    out['content_eq'] = ([l.strip() for l in eol_content_lines(text)]
                         == [l.strip() for l in eol_content_lines(fixed)])
    out['eol_eq'] = all(prof[k] == new_prof[k]
                        for k in ('bare_lf', 'crlf', 'lone_cr'))
    json_eq = None
    try:
        json_eq = json.loads(text) == json.loads(fixed)
    except ValueError:
        try:
            json.loads(text)
            json_eq = False  # raw parses, fixed does not: semantics broken
        except ValueError:
            json_eq = None   # non-JSON target (--file): equivalence n/a
    out['json_eq'] = json_eq
    out['verify_pass'] = (out['content_eq'] and out['eol_eq']
                          and json_eq is not False)
    if not out['verify_pass']:
        out['error'] = 'E_EOL_VERIFY: content/eol/json equivalence broken (refusing)'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 2
    if repaired == 0:
        out['written'] = False
        if prof['indent_ok']:
            out['note'] = 'nothing to fix (indent already canonical)'
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0
        # anomaly lines exist but none is indent-repairable: content
        # disease, not indent disease - fail-closed, no false green
        out['note'] = ('no indent-repairable item line found while '
                       'indent_anomaly > 0 (content disease?)')
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 2
    if not args.execute:
        out['note'] = 'dry-run: zero mutation'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    dirname = os.path.dirname(path) or '.'
    fd, tmp = tempfile.mkstemp(prefix='eol_fixindent_', dir=dirname)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(fixed_raw)
        os.replace(tmp, path)
    except OSError:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    with open(path, 'rb') as f:
        on_disk = f.read()
    post = eol_profile(on_disk)
    out['written'] = True
    out['post_indent_anomaly'] = post['indent_anomaly']
    out['post_indent_ok'] = post['indent_ok']
    out['predicted_eq_actual'] = on_disk == fixed_raw
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out['predicted_eq_actual'] and post['indent_ok'] else 2


def cmd_eol(args):
    if args.fix and args.fix_indent:
        print('error: --fix and --fix-indent are mutually exclusive '
              '(--fix is EOL-only, --fix-indent is indent-only)', file=sys.stderr)
        return 2
    if args.file:
        path = os.path.abspath(args.file)
    else:
        path = os.path.join(args.root, 'src', 'os', 'state.json')
    with open(path, 'rb') as f:
        raw = f.read()
    prof = eol_profile(raw)
    if args.fix_indent:
        return eol_fix_indent(args, path, raw, prof)
    text = raw.decode('utf-8')
    out = {'file': path, 'mode': 'check'}
    out.update(prof)
    if not args.fix:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        # AC-LF2: exit green only when both the CRLF face (layout_ok) and
        # the indent conservation face (indent_ok) are green.
        return 0 if prof['layout_ok'] and prof['indent_ok'] else 2
    fixed_text = BARE_LF.sub('\r\n', text)
    fixed_raw = fixed_text.encode('utf-8')
    out['mode'] = 'fix-execute' if args.execute else 'fix-dry-run'
    out['predicted_bytes'] = len(fixed_raw)
    out['delta_bytes'] = len(fixed_raw) - len(raw)
    out['content_eq'] = eol_content_lines(text) == eol_content_lines(fixed_text)
    json_eq = None
    try:
        json_eq = json.loads(text) == json.loads(fixed_text)
    except ValueError:
        try:
            json.loads(text)
            json_eq = False  # raw parses, fixed does not: semantics broken
        except ValueError:
            json_eq = None   # non-JSON target (--file): equivalence n/a
    out['json_eq'] = json_eq
    out['verify_pass'] = out['content_eq'] and json_eq is not False
    if not out['verify_pass']:
        out['error'] = 'E_EOL_VERIFY: content or json equivalence broken (refusing)'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 2
    if prof['bare_lf'] == 0:
        out['written'] = False
        out['note'] = 'nothing to fix (no bare-LF terminator)'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    if not args.execute:
        out['note'] = 'dry-run: zero mutation'
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    dirname = os.path.dirname(path) or '.'
    fd, tmp = tempfile.mkstemp(prefix='eol_fix_', dir=dirname)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(fixed_raw)
        os.replace(tmp, path)
    except OSError:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    with open(path, 'rb') as f:
        on_disk = f.read()
    out['written'] = True
    out['post_bare_lf'] = eol_profile(on_disk)['bare_lf']
    out['predicted_eq_actual'] = on_disk == fixed_raw
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out['post_bare_lf'] == 0 and out['predicted_eq_actual'] else 2


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
        s = lines[j].strip()
        # R2747: accept the comma-carrying close ('  ],') the canonical
        # writer emits when a sibling key follows the log array.
        if s == ']' or s == '],':
            close_idx = j
            break
        if not s:
            continue
        items.append(j)
    if close_idx is None or len(items) != log_len:
        return None
    caliber = item_indent_caliber([lines[j] for j in items])
    if caliber is None:
        return None
    return lines, log_start, items, close_idx, caliber


def compose_summary(sentence, tokens, budget=SUMMARY_BUDGET):
    """Compose the two-part fold summary: (line, error). One composer, one site.

    Part 1 is the human sentence, part 2 is the token list derived from the
    folded window (AC-2PS1/AC-2PS2). Refuses an empty sentence, a token that is
    not a PAT match, or a composed line over the byte budget - all BEFORE any
    write, so a summary that cannot be read or verified is never landed.
    """
    text = (sentence or '').strip()
    if not text:
        return None, 'E_SUMMARY_SENTENCE: the human sentence is empty (refusing)'
    seen = []
    for tok in tokens or []:
        if not PAT.fullmatch(str(tok)):
            return None, ('E_SUMMARY_TOKEN: %r is not a PAT token (refusing)'
                          % (tok,))
        if tok not in seen:
            seen.append(tok)
    part2 = ','.join(sorted(seen)) if seen else SUMMARY_NONE
    line = text + SUMMARY_SEP + part2
    if len(line.encode('utf-8')) > budget:
        return None, ('E_SUMMARY_BUDGET: %d bytes over the %d-byte summary budget'
                      ' (refusing)' % (len(line.encode('utf-8')), budget))
    return line, None


def summary_parts(line):
    """Split a summary line into its two parts, or name what is missing.

    Read-only and clock-free (AC-2PS4): the verdict reports whether the human
    sentence is non-empty AND the token part parses, which is what a reader and
    a machine each need.
    """
    text = (line or '').lstrip('\ufeff').strip()
    out = {'sentence': '', 'tokens': [], 'token_text': '',
           'two_part': False, 'sentence_ok': False, 'tokens_ok': False,
           'bytes': len((line or '').encode('utf-8')), 'error': None}
    if text.count(SUMMARY_SEP) != 1:
        out['error'] = ('E_SUMMARY_SHAPE: expected exactly one %r separator '
                        '(got %d)' % (SUMMARY_SEP.strip(), text.count(SUMMARY_SEP)))
        return out
    sentence, token_text = text.split(SUMMARY_SEP)
    out['two_part'] = True
    out['sentence'] = sentence.strip()
    out['token_text'] = token_text.strip()
    out['sentence_ok'] = bool(out['sentence'])
    if out['token_text'] == SUMMARY_NONE:
        out['tokens'], out['tokens_ok'] = [], True
    else:
        toks = [t.strip() for t in out['token_text'].split(',') if t.strip()]
        out['tokens'] = sorted(set(toks))
        out['tokens_ok'] = bool(toks) and all(PAT.fullmatch(t) for t in toks)
    if not out['sentence_ok']:
        out['error'] = 'E_SUMMARY_SENTENCE: the human sentence is empty'
    elif not out['tokens_ok']:
        out['error'] = ('E_SUMMARY_TOKEN: the token part parses to nothing or '
                        'carries a non-PAT token')
    return out


def cmd_summary(args):
    """Read-only two-part summary reading (AC-2PS4). Writes nothing."""
    try:
        with open(args.file, encoding='utf-8-sig') as f:
            slines = [l for l in (x.rstrip('\n').rstrip('\r') for x in f)
                      if l.strip()]
    except OSError as e:
        print('error: %s' % e, file=sys.stderr)
        return 3
    if len(slines) != 1:
        print('SUMMARY-CHECK FAIL file=%s reason=E_SUMMARY_LINES lines=%d'
              % (args.file, len(slines)))
        return 2
    parts = summary_parts(slines[0])
    over = parts['bytes'] > args.budget
    verdict = 'PASS' if (not parts['error'] and not over) else 'FAIL'
    reason = parts['error']
    if reason is None and over:
        reason = ('E_SUMMARY_BUDGET: %d bytes over the %d-byte budget'
                  % (parts['bytes'], args.budget))
    print('SUMMARY-CHECK %s file=%s bytes=%d two_part=%s sentence_ok=%s '
          'tokens=%d tokens_ok=%s reason=%s'
          % (verdict, args.file, parts['bytes'], parts['two_part'],
             parts['sentence_ok'], len(parts['tokens']), parts['tokens_ok'],
             reason or 'none'))
    if parts['sentence']:
        print('SUMMARY-SENTENCE %s' % parts['sentence'])
    return 0 if verdict == 'PASS' else 2


def one_summary_line(path):
    """Read the fold summary file: (summary, error). One rule, one site."""
    with open(path, encoding='utf-8') as f:
        slines = [l for l in (x.rstrip('\n').rstrip('\r') for x in f) if l.strip()]
    if len(slines) != 1:
        return None, ('summary file must hold exactly one non-empty line (got %d)'
                      % len(slines))
    return slines[0], None


def fold_rewrite(lines, log_start, w_start, n, log_len, item_caliber, summary):
    """Replace log lines w_start..w_start+n-1 (1-based) with one summary item
    line. Returns (new_lines, predicted_bytes).

    The ONE arithmetic: the read-only plan searches widths with this function
    and the execute path writes the lines it returns, so a plan can never
    predict a size the fold does not produce (AC-LTP1, R3373).
    """
    summary_literal = ' ' * item_caliber + ps_escape(summary)
    if w_start - 1 + n < log_len:
        summary_literal += ','  # mid-window: item lines follow the summary
    first_window_idx = log_start + 1 + (w_start - 1)
    new_lines = (lines[:first_window_idx] + [summary_literal]
                 + lines[first_window_idx + n:])
    return new_lines, len('\r\n'.join(new_lines).encode('utf-8'))


def fold_layout_or_none(root):
    """Load state and locate its canonical item lines. Returns
    (path, raw, st, layout) or None after printing the refusal and its hint."""
    path, raw, st = load_state(root)
    text = raw.decode('utf-8')
    if '\r\n' not in text:
        print('error: E_STATE_LAYOUT: CRLF layout not found (refusing)', file=sys.stderr)
        print('hint: run: python src/os/logs_toolkit.py eol --fix --execute', file=sys.stderr)
        return None
    layout = split_ps_layout(text, len(st['log']))
    if layout is None:
        print('error: E_STATE_LAYOUT: PS item-line layout mismatch (refusing)',
              file=sys.stderr)
        print('hint: run: python src/os/logs_toolkit.py eol --fix-indent --execute',
              file=sys.stderr)
        return None
    return path, raw, st, layout


def cmd_fold_plan(args):
    """Read-only minimal-width plan (AC-LTP1..AC-LTP5, pinned in backlog R3373).

    Answers the question the execute path cannot: how many log lines must be
    folded to clear the gate with a given reserve. Writes nothing.
    """
    got = fold_layout_or_none(args.root)
    if got is None:
        return 2
    path, raw, st, layout = got
    lines, log_start, item_idx, close_idx, caliber = layout
    log_len = len(st['log'])

    has_sentence = getattr(args, 'summary_sentence', None) is not None
    if args.summary_file and has_sentence:
        print('error: E_SUMMARY_MODE: --summary-file and --summary-sentence are '
              'mutually exclusive (refusing)', file=sys.stderr)
        return 2
    if has_sentence and not (args.summary_sentence or '').strip():
        print('error: E_SUMMARY_SENTENCE: --summary-sentence is empty (refusing)',
              file=sys.stderr)
        return 2

    if args.summary_file:
        summary, err = one_summary_line(args.summary_file)
        if err:
            print('error: ' + err, file=sys.stderr)
            return 2
        summary_source = 'file'
    elif has_sentence:
        # AC-RPS1: the execute path composes the line from the human sentence
        # plus the folded window's own PAT set; the plan asks the SAME composer
        # at every width instead of pinning one line, because the line grows
        # with the window and the window is chosen by the line (AC-RPS2).
        summary = None
        summary_source = 'sentence'
    else:
        # A declared placeholder, not a guess about the caller's prose: the
        # assumed width of the replacement item line itself (indent + the two
        # quotes ps_escape writes around the literal + the text).
        summary = 'x' * max(1, PLAN_SUMMARY_ITEM_BYTES - caliber - 2)
        summary_source = 'assumed'

    pre = len(raw)
    target = GATE - args.reserve_bytes
    plan_err = []

    def summary_of(n):
        """The summary line the execute path would land for a fold of n lines."""
        if not has_sentence:
            return summary
        win = st['log'][log_len - n:] if n else []
        toks = set()
        for line in win:
            toks |= set(PAT.findall(line))
        text, cerr = compose_summary(args.summary_sentence, sorted(toks),
                                     args.summary_budget)
        if cerr:
            plan_err.append(cerr)
            return None
        return text

    def post_for(n, text):
        return fold_rewrite(lines, log_start, log_len - n + 1, n, log_len,
                            caliber, text)[1]

    def predict(n):
        return post_for(n, summary_of(n))

    minimal, predicted, plan_summary, skipped = 0, pre, summary, 0
    if has_sentence:
        # the widest fold the byte budget allows: a width whose composition is
        # over budget is not a fold the writer would accept, so it cannot be
        # the size this key reports
        max_post = pre
        for n in range(log_len, 0, -1):
            text = summary_of(n)
            if text is not None:
                max_post = post_for(n, text)
                break
    else:
        max_post = predict(log_len) if log_len else pre
    if pre > target:
        minimal = None
        for n in range(1, log_len + 1):
            text = summary_of(n)
            if text is None:
                skipped += 1
                continue
            post = post_for(n, text)
            if post <= target:
                minimal, predicted, plan_summary = n, post, text
                break
    if minimal is None and log_len and skipped == log_len:
        # every width failed the composer: name the composer's own reason
        # rather than pretending the gate is unreachable (AC-RPS4)
        print('error: ' + plan_err[0], file=sys.stderr)
        return 2
    if not minimal and has_sentence and log_len:
        # nothing needs folding: report the line a zero-width window would land
        # so the item width still answers under the caller's own sentence
        text0 = summary_of(0)
        if text0 is None:
            print('error: ' + (plan_err[0] if plan_err else 'E_SUMMARY_BUDGET'),
                  file=sys.stderr)
            return 2
        plan_summary = text0

    below = None
    if minimal and minimal >= 2:
        below_text = summary_of(minimal - 1)
        if below_text is not None:
            below = post_for(minimal - 1, below_text)
    item_bytes = len(' ' * caliber + ps_escape(plan_summary))
    window = st['log'][log_len - minimal:] if minimal else []
    tokens = set()
    for line in window:
        tokens |= set(PAT.findall(line))
    # AC-RLP1: the plan answers the writer's own round-loss law on the very
    # window it publishes, read off the shipped rounds face (lost_rounds) so a
    # plan and a refusal can never disagree - there is no second arithmetic.
    # With a placeholder summary the list is an upper bound (the placeholder
    # names no round); AC-RLP3 then keeps it out of would_fail.
    if minimal:
        lost = lost_rounds(st, log_len - minimal + 1, log_len, plan_summary)
    else:
        lost = []
    round_loss_declared = bool(getattr(args, 'allow_round_loss', False))
    # AC-RPS1: a summary the plan could compose from the caller's own sentence
    # is exact, exactly like a summary it read from a file
    round_loss_exact = summary_source in ('file', 'sentence')

    archive = args.archive_file or os.path.join(
        args.root, 'logs', 'state-log-archive-%s.md' % datetime.now(CST).strftime('%Y-%m'))
    would_fail = []
    if minimal is None:
        would_fail.append('gate-unreachable')
    if round_loss_exact and lost and not round_loss_declared:
        # the execute path refuses on this list (E_ROUND_LOST); the plan names
        # the same reason, but only when it could read the real summary
        # (AC-RLP2) - an assumed summary never predicts a refusal (AC-RLP3)
        would_fail.append('round-lost')
    if minimal and not os.path.exists(archive) and not args.allow_create:
        # the execute path would refuse here; the plan says so instead of
        # creating an archive to make its own answer true
        would_fail.append('archive-missing')

    plan = {
        'mode': 'plan-only',
        'state_path': path,
        'pre_bytes': pre,
        'gate': GATE,
        'reserve_bytes': args.reserve_bytes,
        'target_bytes': target,
        'log_lines': log_len,
        'summary_source': summary_source,
        'summary_item_bytes': item_bytes,
        'summary_text': plan_summary,
        'minimal_window_lines': minimal,
        'minimal_window_start': (log_len - minimal + 1) if minimal else None,
        'window_content_bytes': sum(len(x.encode('utf-8')) for x in window),
        'window_token_count': len(tokens),
        'window_tokens': sorted(tokens),
        'round_pointer_lost': lost,
        'round_loss_declared': round_loss_declared,
        'round_loss_exact': round_loss_exact,
        'predicted_post_bytes': predicted,
        'width_below_minimal_bytes': below,
        'width_below_minimal_clears_gate': (None if below is None
                                            else below <= target),
        'max_fold_post_bytes': max_post,
        'archive_file': archive,
        'would_fail': would_fail,
        'writes_nothing': True,
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0 if not would_fail else 2


def cmd_fold(args):
    # window selector: exactly one of --window-tail / --window-slice
    # (mid-window support; AC-LT20 pre-registered in tech.md R1690 claim)
    has_tail = args.window_tail > 0
    has_slice = args.window_slice is not None
    if args.plan_only:
        if has_tail or has_slice:
            print('error: --plan-only takes no --window-tail / --window-slice '
                  '(it searches for the minimal width)', file=sys.stderr)
            return 2
        return cmd_fold_plan(args)
    if has_tail == has_slice:
        print('error: exactly one of --window-tail / --window-slice is required',
              file=sys.stderr)
        return 2
    window_mode = 'slice' if has_slice else 'tail'
    w_start = w_end = None
    if has_slice:
        parts = str(args.window_slice).split(':')
        if len(parts) != 2:
            print('error: --window-slice must be START:END integers',
                  file=sys.stderr)
            return 2
        try:
            w_start, w_end = int(parts[0]), int(parts[1])
        except ValueError:
            print('error: --window-slice must be START:END integers',
                  file=sys.stderr)
            return 2
    for req, val in (('--round', args.round), ('--fold-no', args.fold_no),
                     ('--desc', args.desc)):
        if not val:
            print('error: %s is required' % req, file=sys.stderr)
            return 2
    has_summary_file = bool(args.summary_file)
    has_summary_sentence = args.summary_sentence is not None
    if has_summary_file and has_summary_sentence:
        print('error: E_SUMMARY_MODE: --summary-file and --summary-sentence are '
              'mutually exclusive (refusing)', file=sys.stderr)
        return 2
    if not has_summary_file and not has_summary_sentence:
        print('error: --summary-file is required', file=sys.stderr)
        return 2
    if has_summary_sentence and not (args.summary_sentence or '').strip():
        print('error: E_SUMMARY_SENTENCE: --summary-sentence is empty (refusing)',
              file=sys.stderr)
        return 2
    # strict --round form gate (AC-LT25, pre-registered in tech.md R1968
    # next-slice registry): fail-closed on any non-RNNNN form
    if not re.fullmatch(r'R\d{4,}', str(args.round)):
        print('error: --round must match R + 4+ digits like R1968 (got %r)'
              % (args.round,), file=sys.stderr)
        return 2
    summary, err = None, None
    if has_summary_file:
        summary, err = one_summary_line(args.summary_file)
        if err:
            print('error: ' + err, file=sys.stderr)
            return 2

    got = fold_layout_or_none(args.root)
    if got is None:
        return 2
    path, raw, st, layout = got
    lines, log_start, item_idx, close_idx, item_caliber = layout
    if window_mode == 'tail':
        if args.window_tail > len(st['log']):
            print('error: --window-tail exceeds log length', file=sys.stderr)
            return 2
        w_start = len(st['log']) - args.window_tail + 1  # 1-based inclusive
        w_end = len(st['log'])
    else:
        if w_start < 1 or w_end < w_start or w_end > len(st['log']):
            print('error: E_WINDOW_RANGE: --window-slice out of log bounds',
                  file=sys.stderr)
            return 2

    n = w_end - w_start + 1
    window = st['log'][w_start - 1:w_end]
    toks = set()
    for line in window:
        toks |= set(PAT.findall(line))
    if has_summary_sentence:
        # AC-2PS2: the token part is the folded window's own PAT set, so token
        # completeness is structural - no summary prose can drop a pointer.
        summary, err = compose_summary(args.summary_sentence, sorted(toks),
                                       args.summary_budget)
        if err:
            print('error: ' + err, file=sys.stderr)
            return 2
    new_log = st['log'][:w_start - 1] + [summary] + st['log'][w_end:]

    # verifications (all BEFORE any write; R1157 write-before-verify lesson)
    missing = sorted(t for t in toks if t not in summary)
    # AC-RLW1/AC-RLW3: a bare round named neither in the summary nor in an item
    # that stays live would become unfindable, so the writer refuses by name
    # rather than landing a silent loss; the list is read off the shipped
    # read-only `rounds` face so refusal and reading cannot disagree.
    lost = lost_rounds(st, w_start, w_end, summary)
    round_loss_declared = bool(getattr(args, 'allow_round_loss', False))

    new_lines, predicted = fold_rewrite(lines, log_start, w_start, n,
                                       len(st['log']), item_caliber, summary)
    new_text = '\r\n'.join(new_lines)
    gate_ok = predicted + args.reserve_bytes <= GATE

    now = datetime.now(CST)
    sha16 = hashlib.sha256(raw).hexdigest()[:16]
    backup_path = os.path.join(args.root, 'logs', 'state-preop-%s.bak' % args.round)
    archive = args.archive_file or os.path.join(
        args.root, 'logs', 'state-log-archive-%s.md' % now.strftime('%Y-%m'))
    date = now.strftime('%Y-%m-%d')
    header = ('# --- %s fold append (%s, %d lines verbatim: %s, '
              'fold R%s %s, pre-op sha16 %s)') % (
        args.round, date, len(window), args.desc, args.fold_no,
        'mid-window' if window_mode == 'slice' else 'window', sha16)
    if lost and round_loss_declared:
        # AC-RLW2: the declaration is written where the fold is recorded, not
        # only printed, so the archive itself says which pointers went away.
        header += '; round-loss declared: %s' % ','.join(lost)
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
        'round_pointer_lost': lost,
        'round_loss_declared': round_loss_declared,
        'gate_ok': gate_ok,
        'predicted_bytes': predicted,
        'reserve_bytes': args.reserve_bytes,
        'gate': GATE,
    }
    plan = {
        'mode': 'execute' if args.execute else 'dry-run',
        'round': args.round, 'round_label': args.round,
        'fold_no': args.fold_no,
        'window_mode': window_mode, 'window_start': w_start,
        'window_end': w_end,
        'window_lines': len(window),
        'window_content_bytes': sum(len(x.encode('utf-8')) for x in window),
        'summary_head': summary[:60],
        'summary_source': ('sentence' if has_summary_sentence else 'file'),
        'summary_bytes': len(summary.encode('utf-8')),
        'summary_two_part': summary_parts(summary)['two_part'],
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
    if lost and not round_loss_declared:
        fail.append('round-lost')
    if not gate_ok:
        fail.append('gate-exceed')
    if not archive_exists and not args.allow_create:
        fail.append('archive-missing')
    plan['would_fail'] = fail

    if lost and not round_loss_declared:
        print('error: E_ROUND_LOST: %s named neither in the summary nor in the '
              'remaining live items (refusing; name them in --summary-sentence '
              'or declare with --allow-round-loss)' % ','.join(lost),
              file=sys.stderr)

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


# --- census (archive reverse reconciliation, R1688 slice, AC-LT15..LT19
# pre-registered in state/queue/tech.md) ---

# section pointer marker (U+00A7) and original-archive marker (U+539F)
# kept as ASCII \u escapes in patterns per encoding law
CEN_PTR = re.compile(r'\u00a7R([0-9]{2,})')
CEN_FILE_ORIG = re.compile(r'state-log-archive-(\d{4}-\d{2})\.md(.{0,4})\u539f')
CEN_HEADER = re.compile(r'^# --- (R\d+) (.*)$')
CEN_DECLARED = re.compile(r'(\d+) lines verbatim')

# R3211 (AC-CEN1..4, pinned in src/os/backlog.md BEFORE this edit): a section
# header is any "# --- " line that is NOT a date-led annotation. The round
# token is read through four documented shapes because 14 such lines in the
# live archives were written before the AC-LT25 --round gate existed, and the
# old grammar silently merged each of their bodies into the previous section
# (14 unadjudicated mismatches on an honest tree, census exit 2).
CEN_ANY = re.compile(r'^# --- ')
CEN_ANNOT = re.compile(r'^# --- \d{4}-\d{2}-\d{2} ')
CEN_HDR_RANGE = re.compile(r'^# --- (R\d+)-(R\d+)\b')
CEN_HDR_LABEL = re.compile(r'^# --- (R\d+[a-z]?)(?=[\s(])')
CEN_HDR_BARE = re.compile(r'^# --- (\d{4}) fold append\b')
CEN_HDR_FOLD = re.compile(r'^# --- Fold \d+ \((R\d+)\)')
CEN_HDR_FOLD2 = re.compile(r'^# --- Fold (R\d+)\b')
# markdown level-2 headers are section boundaries too: the pre-re-org archive
# used "## \u00a7R#### append(...)" and one 2026-11 fold wrote "## Fold R####"
CEN_SUB_ANY = re.compile(r'^##\s')
CEN_HDR_SUB = re.compile(r'^##\s*\u00a7?(R\d+)\b')
CEN_HDR_SUB_FOLD = re.compile(r'^##\s*Fold (R\d+)\b')


def header_rounds(line):
    """Round tokens of one "# --- " line, or None when it is not a header.

    Shapes: canonical R####, letter suffix R####b, range R####-R####,
    missing-R "#### fold append", and legacy "Fold N (R####)". A date-led
    line is an annotation, never a header (handled by the caller).
    """
    m = CEN_HDR_RANGE.match(line)
    if m:
        return [m.group(1), m.group(2)]
    m = CEN_HDR_LABEL.match(line)
    if m:
        return [m.group(1)]
    m = CEN_HDR_FOLD.match(line)
    if m:
        return [m.group(1)]
    m = CEN_HDR_FOLD2.match(line)
    if m:
        return [m.group(1)]
    m = CEN_HDR_SUB_FOLD.match(line)
    if m:
        return [m.group(1)]
    m = CEN_HDR_SUB.match(line)
    if m:
        return [m.group(1)]
    m = CEN_HDR_BARE.match(line)
    if m:
        return ['R' + m.group(1)]
    return None


def parse_archives(root):
    """Parse all logs/state-log-archive-*.md into (files, sections, stats).

    files: {month: {'path','bytes','sections': [section dicts]}}
    sections: {'R####': first section dict with that round tag} (aliases of a
    range header point at their primary section)
    section dict: {'round','file','header','declared'(int|None),'lines'}
    stats: {'header_lines','annotation_lines','unlabeled_sections',
    'body_header_lines','aliases'} - R3211 boundary-completeness face
    """
    ldir = os.path.join(root, 'logs')
    files, sections = {}, {}
    stats = {'header_lines': 0, 'annotation_lines': 0,
             'unlabeled_sections': [], 'body_header_lines': 0, 'aliases': {}}
    if not os.path.isdir(ldir):
        return files, sections, stats
    for entry in sorted(os.scandir(ldir), key=lambda e: e.name):
        m = re.match(r'^state-log-archive-(\d{4}-\d{2})\.md$', entry.name)
        if not m or not entry.is_file():
            continue
        month = m.group(1)
        with open(entry.path, 'rb') as f:
            raw = f.read()
        text = raw.decode('utf-8')
        cur = None
        secs = []
        for ln in text.split('\n'):
            if CEN_ANY.match(ln) or CEN_SUB_ANY.match(ln):
                stats['header_lines'] += 1
                if CEN_ANNOT.match(ln):
                    # annotation, not a boundary: it stays inside the body
                    stats['annotation_lines'] += 1
                    if cur is not None:
                        cur['lines'].append(ln)
                    continue
                rounds = header_rounds(ln)
                if rounds is None:
                    cur = {'round': None, 'file': month, 'header': ln,
                           'declared': None, 'lines': []}
                    stats['unlabeled_sections'].append(
                        {'file': month, 'header': ln[:120]})
                else:
                    cur = {'round': rounds[0], 'file': month, 'header': ln,
                           'declared': None, 'lines': []}
                    for alias in rounds[1:]:
                        stats['aliases'][alias] = rounds[0]
                        if alias not in sections:
                            sections[alias] = cur
                    if rounds[0] not in sections:
                        sections[rounds[0]] = cur
                dm = CEN_DECLARED.search(ln)
                if dm:
                    cur['declared'] = int(dm.group(1))
                secs.append(cur)
            elif cur is not None:
                if CEN_ANY.match(ln) or CEN_SUB_ANY.match(ln):
                    stats['body_header_lines'] += 1
                cur['lines'].append(ln)
        files[month] = {'path': entry.path, 'bytes': len(raw), 'sections': secs}
    return files, sections, stats


def load_known_findings(path):
    """Load adjudicated known-findings data file (may be absent = none).

    Returns ({known mismatch rounds -> reason}, {known dangling ptrs -> reason}).
    Known findings stay visible in output but are excluded from the FAIL
    verdict; every entry requires an evidence-backed adjudication (R1688).
    """
    if not path or not os.path.exists(path):
        return {}, {}
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    mm = {e['round']: e.get('reason', '') for e in d.get('section_line_mismatches', [])}
    dg = {e['pointer']: e.get('reason', '') for e in d.get('dangling_pointers', [])}
    return mm, dg


def cmd_census(args):
    _, _, st = load_state(args.root)
    files, sections, hstats = parse_archives(args.root)
    known_path = args.known_file or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'census_known_findings.json')
    known_mm, known_dg = load_known_findings(known_path)

    # (1) section integrity: declared vs actual non-empty verbatim lines
    # (fold-append headers only; legacy 09-format headers carry no declared)
    mismatches = []
    sec_tokens = {}
    all_archive_toks = set()
    for month, finfo in sorted(files.items()):
        for s in finfo['sections']:
            toks = set()
            for l in s['lines']:
                toks |= set(PAT.findall(l))
            sec_tokens[s['round']] = toks
            all_archive_toks |= toks
            if s['declared'] is None:
                continue
            actual = len([l for l in s['lines'] if l.strip()])
            if s['declared'] != actual:
                e = {'round': s['round'], 'file': month,
                     'declared': s['declared'], 'actual': actual,
                     'adjudicated': s['round'] in known_mm}
                if e['adjudicated']:
                    e['reason'] = known_mm[s['round']]
                mismatches.append(e)

    # (2)+(3) pointer resolution + informational token census
    pointer_lines = []
    dangling_total = 0
    live_toks = set()
    for line in st['log']:
        live_toks |= set(PAT.findall(line))
        ptrs = ['R' + p for p in CEN_PTR.findall(line)]
        origs = sorted(set(m.group(1) for m in CEN_FILE_ORIG.finditer(line)))
        if not ptrs and not origs:
            continue
        line_toks = set(PAT.findall(line))
        dangling = [p for p in ptrs if p not in sections]
        dangling_total += len(dangling)
        union_toks = set()
        not_embedded = {}
        for p in ptrs:
            if p not in sections:
                continue
            t = sec_tokens.get(p, set())
            union_toks |= t
            miss = sorted(t - line_toks)
            if miss:
                not_embedded[p] = miss
        for month in origs:
            if month in files:
                for s in files[month]['sections']:
                    union_toks |= sec_tokens.get(s['round'], set())
        pointer_lines.append({
            'head': line[:60],
            'pointers': ptrs,
            'file_refs': origs,
            'dangling': dangling,
            'not_embedded': not_embedded,
            'roll_native': sorted(line_toks - union_toks),
        })

    archive_only = sorted(all_archive_toks - live_toks)
    unknown_mismatches = [m for m in mismatches if not m['adjudicated']]
    live_dangling = set()
    for pl in pointer_lines:
        live_dangling |= set(pl['dangling'])
    dangling_known = [{'pointer': p, 'reason': known_dg[p]}
                      for p in sorted(live_dangling & set(known_dg))]
    unknown_dangling_total = len(live_dangling - set(known_dg))
    out = {
        'files': {m: {'path': f['path'], 'bytes': f['bytes'],
                      'sections': len(f['sections'])}
                  for m, f in sorted(files.items())},
        'sections_total': sum(len(f['sections']) for f in files.values()),
        'section_line_mismatches': mismatches,
        'pointer_lines': pointer_lines,
        'dangling_total': dangling_total,
        'known_findings_file': known_path if os.path.exists(known_path) else None,
        'dangling_known': dangling_known,
        'unknown_mismatch_count': len(unknown_mismatches),
        'unknown_dangling_count': unknown_dangling_total,
        'archive_tokens_total': len(all_archive_toks),
        'live_tokens_total': len(live_toks),
        'archive_only_count': len(archive_only),
        'archive_only_tokens': archive_only,
        'header_lines': hstats['header_lines'],
        'annotation_lines': hstats['annotation_lines'],
        'unlabeled_sections': hstats['unlabeled_sections'],
        'body_header_lines': hstats['body_header_lines'],
        'section_aliases': hstats['aliases'],
        'pass': (not unknown_mismatches and unknown_dangling_total == 0
                 and hstats['body_header_lines'] == 0
                 and not hstats['unlabeled_sections']),
    }
    # R3372 (AC-LTC1..4): --json buys a parser a CONTRACT, not different bytes -
    # the tool already printed one JSON document, but nothing promised that, so
    # a reader had to re-discover the shape every window. Both modes now go
    # through this single write: one document, keys in emitted order, exactly
    # one trailing newline, and the verdict exit code unchanged.
    body = json.dumps(out, ensure_ascii=False, indent=2)
    sys.stdout.write(body + '\n')
    sys.stdout.flush()
    return 0 if out['pass'] else 2


def main(argv=None):
    p = argparse.ArgumentParser(prog='logs_toolkit.py', description=__doc__)
    p.add_argument('--root', default=default_root(), help='repo root (default: auto)')
    sub = p.add_subparsers(dest='cmd', required=True)

    sub.add_parser('gauge', help='water report for src/os/state.json')
    pw = sub.add_parser('weights', help='per-item log weight + share of log and gate (read-only)')
    pw.add_argument('--top', type=int, default=10,
                    help='rows on the top face (default 10; totals always cover every item)')
    pi = sub.add_parser('inventory', help='logs/ class breakdown')
    pi.add_argument('--with-qa', action='store_true',
                    help='also inventory qa/ evidence (qa-evidence / evidence-other)')
    pi.add_argument('--roots', action='append', metavar='LABEL=DIR',
                    help='extra root to inventory (repeatable; label `logs` '
                         'keeps the legacy classifier, any other label is '
                         'treated as an evidence root)')
    pt = sub.add_parser('tail', help='state.json log tail inventory')
    pt.add_argument('-n', type=int, default=10)
    pp = sub.add_parser('prune', help='logs/ retention enforcement')
    pp.add_argument('--execute', action='store_true', help='actually delete (default: dry-run)')
    pp.add_argument('--floor-seconds', type=int, default=DEFAULT_FLOOR)
    pc = sub.add_parser('catalog', help='window token extraction + presence check')
    pc.add_argument('--tail', type=int, help='window = last N state log lines')
    pc.add_argument('--window-file', help='window = non-empty lines of this file')
    pc.add_argument('--roll-file', required=False, help='roll/summary text to check presence against')
    cn = sub.add_parser('census', help='archive reverse reconciliation census (read-only)')
    cn.add_argument('--known-file', help='adjudicated known-findings data file '
                    '(default: census_known_findings.json alongside this tool)')
    cn.add_argument('--json', action='store_true',
                    help='machine mode (contract, not a second renderer): stdout is '
                         'exactly one JSON document with the same keys in the same '
                         'order as the default block and one trailing newline; '
                         'writes nothing, verdict exit code unchanged')
    pe = sub.add_parser('eol', help='state.json closeout EOL repair (bare-LF report + CRLF surgery)')
    pe.add_argument('--file', default=None, help='target file (default: src/os/state.json)')
    pe.add_argument('--fix', action='store_true', help='perform CRLF surgery (default: read-only check)')
    pe.add_argument('--fix-indent', action='store_true',
                    help='re-indent log item lines to the 16-space canonical '
                         '(mutually exclusive with --fix; default: dry-run)')
    pe.add_argument('--execute', action='store_true', help='with --fix/--fix-indent: actually write (default: dry-run)')
    pf = sub.add_parser('fold', help='state.json fold surgery (verify-then-write)')
    pf.add_argument('--round', help='round label e.g. R1687 (backup + header naming)')
    pf.add_argument('--fold-no', help='fold knife number e.g. 455 (header)')
    pf.add_argument('--desc', help='window description for the archive header')
    pf.add_argument('--window-tail', type=int, default=0, help='window = last N log lines')
    pf.add_argument('--window-slice', default=None,
                    help='window = log lines START:END (1-based inclusive, mid-array)')
    pf.add_argument('--summary-file', help='file holding exactly one non-empty summary line')
    pf.add_argument('--summary-sentence',
                    help='two-part summary: the human sentence; the token list is '
                         'derived from the folded window (mutually exclusive with '
                         '--summary-file)')
    pf.add_argument('--summary-budget', type=int, default=SUMMARY_BUDGET,
                    help='byte ceiling for a composed two-part summary '
                         '(default %d)' % SUMMARY_BUDGET)
    pf.add_argument('--reserve-bytes', type=int, default=3000)
    pf.add_argument('--plan-only', action='store_true',
                    help='read-only: report the MINIMAL window width that clears '
                         'gate - reserve, its predicted post size and tokens; '
                         'takes no window selector and writes nothing')
    pf.add_argument('--archive-file', help='override archive path (default: logs/state-log-archive-<month>.md)')
    pf.add_argument('--allow-create', action='store_true', help='create archive if missing (else fail-closed)')
    pf.add_argument('--allow-round-loss', action='store_true',
                    help='declare that the fold erases bare R#### pointers named '
                         'nowhere else; without it such a fold refuses by name '
                         '(E_ROUND_LOST)')
    pf.add_argument('--execute', action='store_true', help='perform surgery (default: dry-run, zero mutation)')
    ps = sub.add_parser('summary', help='two-part fold summary reading (read-only)')
    ps.add_argument('--file', required=True,
                    help='summary file holding exactly one non-empty line')
    ps.add_argument('--budget', type=int, default=SUMMARY_BUDGET,
                    help='byte ceiling (default %d)' % SUMMARY_BUDGET)
    pr = sub.add_parser('rounds',
                        help='pre-fold bare-round pointer reading (read-only)')
    pr.add_argument('--window-tail', type=int, default=0,
                    help='window = last N log lines (default: the whole log)')
    pr.add_argument('--window-slice', default=None,
                    help='window = log lines START:END (1-based inclusive)')
    pr.add_argument('--file', default=None,
                    help='summary file whose text may name the window rounds')
    pr.add_argument('--strict', action='store_true',
                    help='exit 4 when any window round would be lost')

    args = p.parse_args(argv)
    handlers = {'gauge': cmd_gauge, 'weights': cmd_weights,
                'inventory': cmd_inventory, 'tail': cmd_tail,
                'prune': cmd_prune, 'catalog': cmd_catalog, 'fold': cmd_fold,
                'census': cmd_census, 'eol': cmd_eol, 'summary': cmd_summary,
                'rounds': cmd_rounds}
    if args.cmd not in handlers:
        return 2
    try:
        return handlers[args.cmd](args)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print('error: %s' % e, file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
