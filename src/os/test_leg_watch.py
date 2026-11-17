"""Battery suite for tools/leg_watch.py - criteria AC-LGW1..AC-LGW6.

WHY: R2890 shipped tools/leg_watch.py, the sampler that answers "is a leg
readable WHILE it runs past the 300s wall", and read it on a real 285-suite leg.
The tool had no battery row, so a sampler that measures nothing, or one that
quietly drops a torn read, would look exactly like a sampler that works. This
suite pins the observer instead of pinning its round: every fixture is built in
a private world from bytes this suite writes, so nothing here depends on a leg
still being on disk, and no shipped file is written.

The premise being pinned is narrow on purpose. leg_watch judges a file, not a
battery: it must REFUSE a file that was written once at the end (that proves the
output, not the streaming), must COUNT a torn read rather than hide it, and must
leave the leg it watches byte- and mtime-identical.

Criteria were pinned in state/queue/tech.md BEFORE this file existed (R2891);
registration in src/sandbox/reconcile_all.py is deliberately NOT done while a
same-family leg is in flight (the R2886 edit-race law), so AC-LGW6 verifies the
wiring only if it is already there and stays silent otherwise - it never
fabricates a green for work that has not landed.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import hashlib
import importlib.util
import io
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, 'tools', 'leg_watch.py')
FAILS = []
CHECKS = []

RUNNING = ('SHARD scope=SHARD registry_suites=711 registry_criteria=5434 '
           'selected=286 selected_criteria=1930 cap=600s leg_cap=0s '
           'overrides=1 exact=0 state=RUNNING\n'
           'SHARD row probe-a rc=0 pass=6 fail=0 detail=yes suite=PASS 6/6 crit=6 0.5s\n'
           'SHARD row probe-b rc=0 pass=6 fail=0 detail=yes suite=PASS 6/6 crit=6 0.6s\n')
CLOSED = RUNNING + ('SHARD rc=0 scope=SHARD selected=2 executed=2 green=2 '
                    'criteria=12 crit_mismatch=0 elapsed=1.1s\n')


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if not cond:
        FAILS.append('%s [%s]' % (name.split(' ', 1)[0], detail))


def load_mod():
    spec = importlib.util.spec_from_file_location('leg_watch_under_test', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def put(world, name, text, newline=True):
    path = os.path.join(world, name)
    with io.open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text if newline else text.rstrip('\n'))
    return path


def digest(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest(), os.stat(path).st_mtime_ns


def run_cli(mod, argv, world):
    """Drive the shipped CLI in a private world, capturing both return and text."""
    saved = mod.QA_DIR
    mod.QA_DIR = world
    buf = io.StringIO()
    saved_out = sys.stdout
    try:
        sys.stdout = buf
        try:
            rc = mod.main(argv)
        except SystemExit as exc:            # argparse refuses with its own code
            rc = int(exc.code or 0)
    finally:
        sys.stdout = saved_out
        mod.QA_DIR = saved
    return rc, buf.getvalue()


def refusals(mod, names):
    out = []
    for name in names:
        try:
            mod.evidence_name(name)
            out.append('ACCEPTED:%s' % name)
        except mod.Refuse as exc:
            out.append(str(exc))
    return out


def main():
    mod = load_mod()
    world = tempfile.mkdtemp(prefix='legwatch-')

    # AC-LGW1: the evidence path law (AC-BSH6 carried to this tool).
    good = mod.evidence_name('leg-watch-R2890.log')
    bad = refusals(mod, ['', 'C:/tmp/x.log', 'a/b.log', 'a\\b.log',
                         '../x.log', 'x.txt'])
    ok('AC-LGW1 only a bare qa/ .log basename is accepted',
       good == 'leg-watch-R2890.log'
       and all(x.startswith('E_EVIDENCE_PATH') for x in bad),
       'good=%s bad=%s' % (good, bad))

    # AC-LGW2: one honest reading, torn reads counted rather than dropped.
    p_run = put(world, 'run.log', RUNNING)
    p_closed = put(world, 'closed.log', CLOSED)
    p_torn = put(world, 'torn.log', RUNNING, newline=False)
    s_run, s_closed, s_torn = mod.sample(p_run), mod.sample(p_closed), mod.sample(p_torn)
    s_missing = mod.sample(os.path.join(world, 'absent.log'))
    ok('AC-LGW2 a RUNNING file with rows is a mid-run reading',
       s_run['readable'] and s_run['rows'] == 2 and s_run['running']
       and not s_run['closing'] and not s_run['torn'],
       'rows=%s running=%s closing=%s torn=%s'
       % (s_run['rows'], s_run['running'], s_run['closing'], s_run['torn']))
    ok('AC-LGW2 a finished file is readable but carries a closing row',
       s_closed['readable'] and s_closed['closing'] and s_closed['rc'] == 0,
       'closing=%s rc=%s' % (s_closed['closing'], s_closed['rc']))
    ok('AC-LGW2 a truncated tail is COUNTED torn, not dropped',
       s_torn['readable'] and s_torn['rows'] == 2 and s_torn['torn']
       and s_torn['tail_ok'] is False,
       'torn=%s rows=%s tail_ok=%s'
       % (s_torn['torn'], s_torn['rows'], s_torn['tail_ok']))
    ok('AC-LGW2 a missing file is unreadable and raises nothing',
       s_missing['readable'] is False and s_missing['rows'] == 0
       and s_missing['torn'] is True,
       'readable=%s torn=%s' % (s_missing['readable'], s_missing['torn']))

    # AC-LGW3: the verdict refuses a premise rather than reporting a pass.
    def series(*pairs):
        return [{'t': t, 'info': info} for t, info in pairs]

    write_once = mod.judge(series((0.0, s_closed), (1.0, s_closed)), 0)
    lawful = mod.judge(series((0.0, s_run), (301.0, s_run)), 300)
    backwards = mod.judge(series((0.0, dict(s_run, rows=5)),
                                 (10.0, dict(s_run, rows=3))), 0)
    short = mod.judge(series((0.0, s_run), (10.0, s_run)), 300)
    ok('AC-LGW3 a write-once file is refused E_NO_MIDRUN_SAMPLE',
       write_once['ok'] is False
       and 'E_NO_MIDRUN_SAMPLE' in write_once['reasons'],
       'reasons=%s' % write_once['reasons'])
    ok('AC-LGW3 a lawful series past the wall is CONFIRMED',
       lawful['ok'] is True and lawful['midrun'] == 2
       and abs(lawful['span'] - 301.0) < 0.01,
       'ok=%s midrun=%s span=%s'
       % (lawful['ok'], lawful['midrun'], lawful['span']))
    ok('AC-LGW3 rows going backwards are refused by name',
       backwards['ok'] is False
       and 'E_ROWS_WENT_BACKWARDS' in backwards['reasons'],
       'reasons=%s' % backwards['reasons'])
    ok('AC-LGW3 a span under min_window is refused by name',
       short['ok'] is False and any(r.startswith('E_WINDOW_SHORT')
                                     for r in short['reasons']),
       'reasons=%s' % short['reasons'])
    # Negative control: the SAME readable RUNNING file turns red once it carries
    # zero rows, so acceptance is a function of the reading, not of the branch.
    # A mid-run sample followed by a closing sample is deliberately NOT the
    # control: that is what a lawful watch looks like when the leg finishes.
    flipped = mod.judge(series((0.0, dict(s_run, rows=0))), 0)
    ok('AC-LGW3 the confirmation is not a constant (zero rows flips it red)',
       flipped['ok'] is False and 'E_NO_MIDRUN_SAMPLE' in flipped['reasons']
       and lawful['ok'] is True and s_run['rows'] > 0,
       'reasons=%s lawful=%s' % (flipped['reasons'], lawful['ok']))

    # AC-LGW4: CLI codes, and the observed leg is left byte- and mtime-identical.
    before = digest(p_run)
    rc_missing, _ = run_cli(mod, ['absent.log'], world)
    rc_run, out_run = run_cli(mod, ['run.log'], world)
    rc_closed, _ = run_cli(mod, ['closed.log'], world)
    after = digest(p_run)
    ok('AC-LGW4 CLI exits 3 missing / 0 mid-run / 2 finished',
       rc_missing == 3 and rc_run == 0 and rc_closed == 2,
       'missing=%s run=%s closed=%s' % (rc_missing, rc_run, rc_closed))
    ok('AC-LGW4 the watched leg is byte- and mtime-identical after the run',
       before == after and 'MID-RUN CONFIRMED' in out_run,
       'before=%s after=%s' % (before, after))

    # AC-LGW5: the evidence file is exactly the report it declared, atomically.
    # The DECL line is a stdout receipt, NOT part of the file (that is the
    # shipped behaviour R2890 evidenced); the file must equal the report text
    # that preceded it, byte for byte.
    rc_ev, out_ev = run_cli(mod, ['run.log', '--evidence', 'watch.log'], world)
    written = os.path.join(world, 'watch.log')
    body = io.open(written, 'rb').read().decode('utf-8')
    decl = [l for l in out_ev.splitlines() if l.startswith('DECL evidence')]
    residue = [n for n in os.listdir(world) if n.endswith('.partial')]
    want = ('bytes=%d lines=%d'
            % (len(body.encode('utf-8')), len(body.splitlines())))
    ok('AC-LGW5 --evidence writes exactly the declared report, atomically',
       rc_ev == 0 and out_ev == body + (decl[0] + '\n' if decl else '')
       and len(decl) == 1 and want in decl[0] and residue == []
       and 'MID-RUN CONFIRMED' in body,
       'rc=%s equal=%s decl=%s residue=%s'
       % (rc_ev, out_ev == body, decl, residue))

    # AC-LGW6: hygiene plus CONDITIONAL wiring - silent until registration lands.
    src = io.open(TOOL, 'r', encoding='utf-8').read()
    net = [m for m in re.findall(r'^\s*(?:import|from)\s+([\w.]+)', src, re.M)
           if m.split('.')[0] in ('socket', 'requests', 'http', 'urllib',
                                  'urllib3', 'subprocess')]
    reg_path = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
    reg = io.open(reg_path, 'r', encoding='utf-8').read()
    rows = re.findall(r'"os-leg-watch"\)\s*,\s*(\d+)', reg)
    matrix = ''
    mpath = os.path.join(ROOT, 'docs', 'sandbox-suite-matrix.md')
    if os.path.exists(mpath):
        matrix = io.open(mpath, 'r', encoding='utf-8', errors='replace').read()
    wiring = True
    if rows:
        wiring = (len(rows) == 1 and matrix.count('os-leg-watch') >= 1
                  and ('os-leg-watch' in matrix))
    ok('AC-LGW6 hygiene holds and wiring is verified only when registered',
       all(ord(c) < 128 for c in src) and net == [] and wiring,
       'net=%s rows=%s wiring=%s' % (net, rows, wiring))

    total = len(CHECKS)
    acs = set()
    for name in CHECKS:
        token = name.split(' ', 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    print('suite: %d assertions over %d criteria' % (total, len(acs)))
    if FAILS:
        print('SUITE FAIL %d/%d failed=%s' % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d' % (total, total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
