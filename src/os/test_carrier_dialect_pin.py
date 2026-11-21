"""Battery suite for the carrier dialect pin - criteria AC-CDPIN1..AC-CDPIN4.

Pinned in src/os/backlog.md at R3208 BEFORE this file existed, from a
read-only probe (tmp/probe_R3208.py, tmp/probe_R3208b.py, tmp/probe_R3208c.py)
run before any code changed.

The defect this suite holds, measured first: src/os/state.json was not pinned
in .gitattributes, and a blob is always stored as LF, so a checkout running
with core.autocrlf=false materialized the WHOLE carrier as bare LF - measured
bytes=59808 crlf=0 bare_lf=78 against the live bytes=59886 crlf=78. That is
the drift the closeout gate refused twice (R3204 bare_lf=49, R3207 bare_lf=70)
and each time repaired by hand. The pin holds for all three measured
add/checkout combinations, and no shipped round writer emits LF, so the pin
closes the only path that could recreate it.

Second half of the same window: state_fold.plan_fold used to fall back to a
bare-LF split, so an already-LF carrier was planned with newline=LF and
composed 77 bare-LF separators with every gate green - the fold propagated the
dialect instead of naming it. It now refuses with E_SF_EOL, matching the
sibling door that has refused an LF carrier since it shipped.

Isolation: every git repository, state file and archive this suite builds
lives in the system temp dir. The real .gitattributes, state.json and qa/ are
read only, never written. Source is pure ASCII, stdlib only, no clock in
assertions, no network.
"""
import io
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'src', 'os')
ATTRS = os.path.join(ROOT, '.gitattributes')
LIVE = os.path.join(SRC, 'state.json')
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
FAILS = []
CHECKS = []


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def read_bytes(path):
    with io.open(path, 'rb') as handle:
        return handle.read()


def read_text(path):
    with io.open(path, 'r', encoding='utf-8') as handle:
        return handle.read()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def profile(raw):
    crlf = raw.count(b'\r\n')
    return len(raw), crlf, raw.count(b'\n') - crlf


def git(argv, cwd):
    base = ['git', '-c', 'user.email=probe@example.invalid',
            '-c', 'user.name=probe']
    done = subprocess.run(base + argv, cwd=cwd, capture_output=True)
    return done.returncode, done.stdout.decode('utf-8', 'replace').strip(), \
        done.stderr.decode('utf-8', 'replace').strip()


def cycle(attrs_line, add_autocrlf, co_autocrlf, carrier):
    """Commit a carrier, remove it, check it out again; return (blob, landed).

    The whole point of the arm: the ABOVE measurement is what a checkout can
    do to this file on a machine whose git settings differ from this one.
    """
    box = tempfile.mkdtemp(prefix='cdpin_')
    try:
        git(['init', '-q'], box)
        os.makedirs(os.path.join(box, 'src', 'os'))
        if attrs_line is not None:
            with io.open(os.path.join(box, '.gitattributes'), 'w',
                         encoding='utf-8', newline='\n') as handle:
                handle.write(attrs_line + '\n')
        path = os.path.join(box, 'src', 'os', 'state.json')
        with io.open(path, 'wb') as handle:
            handle.write(carrier)
        git(['-c', 'core.autocrlf=%s' % add_autocrlf, 'add',
             'src/os/state.json'], box)
        git(['commit', '-q', '-m', 'x', '--no-verify'], box)
        blob = subprocess.run(
            ['git', 'cat-file', '-p', 'HEAD:src/os/state.json'],
            cwd=box, capture_output=True).stdout
        os.remove(path)
        git(['-c', 'core.autocrlf=%s' % co_autocrlf, 'checkout', '--',
             'src/os/state.json'], box)
        landed = read_bytes(path) if os.path.exists(path) else b''
        return blob, landed
    finally:
        shutil.rmtree(box, ignore_errors=True)


PIN = 'src/os/state.json text eol=crlf'


def main():
    started = time.time()
    live = read_bytes(LIVE)
    attrs = read_text(ATTRS)

    # ---- AC-CDPIN1: the law is pinned, once, on the right path ----------
    rc, out, err = git(['check-attr', 'text', 'eol', '--',
                        'src/os/state.json'], ROOT)
    pin_lines = [row for row in attrs.splitlines()
                 if row.strip() == PIN]
    ok('AC-CDPIN1 the carrier dialect is pinned in .gitattributes',
       rc == 0
       and 'text: set' in out
       and 'eol: crlf' in out
       and len(pin_lines) == 1
       and attrs.count('src/os/state.json') == 2,
       'rc=%d los=%s pins=%d' % (rc, out.replace('\n', ';')[:60],
                                 len(pin_lines)))

    # ---- AC-CDPIN2: the decisive arm - the pin is what stops the drift --
    blob_free, land_free = cycle(None, 'true', 'false', live)
    blob_pin, land_pin = cycle(PIN, 'true', 'false', live)
    blob_pin2, land_pin2 = cycle(PIN, 'false', 'false', live)
    ok('AC-CDPIN2 an unpinned carrier lands bare LF, the pinned one cannot',
       profile(land_free)[1] == 0
       and profile(land_free)[2] == profile(live)[1] > 0
       and land_pin == live
       and land_pin2 == live
       and profile(blob_free)[1] == 0
       and profile(blob_pin)[1] == 0,
       'free=%s pinned=%s pinned2=%s blob_free_crlf=%d'
       % (profile(land_free), profile(land_pin), profile(land_pin2),
          profile(blob_free)[1]))

    # ---- AC-CDPIN3: both fold doors refuse an LF carrier by name --------
    mod = load('state_fold_under_test', os.path.join(SRC, 'state_fold.py'))
    toolkit = load('logs_toolkit_under_test',
                   os.path.join(SRC, 'logs_toolkit.py'))
    log_len = len(json.loads(live.decode('utf-8'))['log'])
    lf_carrier = live.replace(b'\r\n', b'\n')
    code = ''
    detail = ''
    try:
        mod.plan_fold(lf_carrier, json.loads(live.decode('utf-8')), 1, 2,
                      'R0001 probe summary', gate=200000)
    except mod.StateFoldError as exc:
        code = exc.code
        detail = exc.detail
    control, folded = mod.plan_fold(live, json.loads(live.decode('utf-8')),
                                    1, 2, 'R0001 probe summary', gate=200000)
    toolkit_reads_lf = toolkit.split_ps_layout(
        lf_carrier.decode('utf-8'), log_len)
    ok('AC-CDPIN3 the fold names an LF carrier instead of carrying it',
       code == 'E_SF_EOL'
       and 'eol --fix' in detail
       and control['newline'] == 'CRLF'
       and b'\r\n' in folded.encode('utf-8')
       and toolkit_reads_lf is None,
       'code=%s hint=%s control=%s toolkit_lf=%s'
       % (code, '--fix' in detail, control['newline'],
          'refused' if toolkit_reads_lf is None else 'readable'))

    # ---- AC-CDPIN4: the live carrier is clean, and the refusal is one ---
    live_prof = profile(live)
    raises = read_text(os.path.join(SRC, 'state_fold.py')).count('E_SF_EOL')
    ok('AC-CDPIN4 the live carrier needs no repair and the refusal is single',
       live_prof[1] > 0
       and live_prof[2] == 0
       and raises == 2  # the raise plus the docstring mention
       and mod.split_layout(live.decode('utf-8'), log_len) is not None,
       'live=%s e_sf_eol_sites=%d' % (live_prof, raises))

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
        print('SUITE FAIL %d/%d failed=%s'
              % (total - len(FAILS), total, FAILS))
        return 1
    print('SUITE PASS %d/%d in %.1fs' % (total, total, time.time() - started))
    return 0


if __name__ == '__main__':
    sys.exit(main())
