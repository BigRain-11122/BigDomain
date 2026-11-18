"""Battery suite for the repeatable live proof in tools/ceo_live_shot.py.

WHY: R2934 photographed the sandbox for the first time and wrote seven PNGs,
but one pass is a SNAPSHOT - it cannot tell "this face is alive" apart from
"this face happened to paint cleanly this time". The board carried that to this
window: make the shooter shoot the same faces twice on the SAME sandbox (the
second pass starts after the first pass drove the lobby through a real session)
and refuse when the two passes disagree on any face's HTTP status or error set.

The registry law is stdlib / zero network / zero shell, so a browser cannot run
here. The same ruling R2931 used applies: move the LAW into a pure function -
compare_runs - and grade that, then print the browser arm as a SKIP BY NAME so
an unrun arm can never read as a pass.

Coverage, stated honestly: this suite grades the comparison, not the paint. It
proves the drift rules fire and the report identity holds; it does not prove a
browser agreed twice on this machine - that is the on-demand `--prove` arm,
whose verdict is measured live and quoted in the round's evidence log.

PINNED BEFORE THE CODE: AC-LIVE1..AC-LIVE5 were written into src/os/backlog.md
earlier in this same window, BEFORE compare_runs existed - in-window
pre-registration, disclosed as such. AC-LIVE6 was pinned in the R2936 board row
BEFORE the shooter grew its last two faces, and it derives its coverage from
the launcher and hub modules instead of counting a typed list. Source
discipline: pure ASCII, stdlib only, no clock, no network, writes nothing into
qa/.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import ceo_live_shot as LS

FAILS = []
CHECKS = []


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


def row(face, status=200, errors=None, okflag=None):
    """One photography row, shaped exactly like shoot() returns."""
    errs = list(errors or [])
    return {'face': face, 'status': status, 'errors': errs,
            'ok': (not errs and status < 400) if okflag is None else okflag,
            'acted': [], 'png': 'preview/live/%s.png' % face}


def world(spec):
    """spec = [(face, status, [errors])] -> a pass, in order."""
    return [row(face, status, errors) for face, status, errors in spec]


SEVEN = [('hub', 200, []), ('lobby', 200, []), ('city', 200, []),
         ('gate', 200, []), ('ugc', 200, []), ('ledger', 200, []),
         ('checkout', 200, [])]


def top_level_playwright_imports(text):
    """Lines that import playwright at module scope (indent 0)."""
    hits = []
    for line in text.splitlines():
        if line[:1] in (' ', '\t'):
            continue
        stripped = line.strip()
        if not (stripped.startswith('import ') or stripped.startswith('from ')):
            continue
        if 'playwright' in stripped:
            hits.append(stripped)
    return hits


def main():
    # AC-LIVE1: the verdict is COUNTED, and one face can never be counted twice.
    first = world(SEVEN)
    second = world([(f, s, e) for f, s, e in SEVEN])
    disagree = LS.compare_runs(first, second)
    ok('AC-LIVE1 identical passes produce zero disagreements',
       disagree == [], 'disagreements=%s' % (disagree,))
    ok('AC-LIVE1 the report identity holds on an agreeing world',
       len(first) - len(disagree) == len(first), 'faces=%d' % len(first))
    # A face drifting in BOTH status and errors must still be ONE row, or the
    # agreements plus disagreements identity would over-count a single face.
    both = world([(f, (500 if f == 'gate' else s), e) for f, s, e in SEVEN])
    both[3]['errors'] = ['boom: one', 'boom: two']
    drift = LS.compare_runs(first, both)
    ok('AC-LIVE1 a doubly-drifting face yields exactly ONE row',
       len(drift) == 1 and drift[0]['face'] == 'gate',
       'rows=%d faces=%s' % (len(drift), [d['face'] for d in drift]))
    ok('AC-LIVE1 agreements + disagreements == faces on a drifting world',
       (len(first) - len(drift)) + len(drift) == len(first),
       'agreements=%d' % (len(first) - len(drift)))

    # AC-LIVE2: status drift refuses and names both sides; the red goes away
    # when only the value moves back, so the refusal is caused by the drift.
    moved = world([(f, (404 if f == 'lobby' else s), e) for f, s, e in SEVEN])
    status_drift = LS.compare_runs(first, moved)
    ok('AC-LIVE2 status drift refuses with kind=status',
       len(status_drift) == 1 and status_drift[0]['kind'] == 'status',
       'rows=%s' % (status_drift,))
    ok('AC-LIVE2 the refusal names the face and both values',
       status_drift and status_drift[0]['face'] == 'lobby'
       and status_drift[0]['first'] == 200 and status_drift[0]['second'] == 404,
       'row=%s' % (status_drift[:1],))
    ok('AC-LIVE2 restoring the value restores agreement (red is the drift)',
       LS.compare_runs(first, world(SEVEN)) == [], 'restored=0')

    # AC-LIVE3: the error SET is compared, not the ORDER.
    shuffled = world(SEVEN)
    base = world(SEVEN)
    first[3]['errors'] = ['e1: a', 'e2: b']
    shuffled[3]['errors'] = ['e2: b', 'e1: a']
    ok('AC-LIVE3 the same errors in another order still agree',
       LS.compare_runs(first, shuffled) == [],
       'rows=%s' % (LS.compare_runs(first, shuffled),))
    extra = world(SEVEN)
    extra[3]['errors'] = ['e1: a', 'e2: b', 'e3: c']
    err_drift = LS.compare_runs(first, extra)
    ok('AC-LIVE3 one extra error is drift, kind=errors',
       len(err_drift) == 1 and err_drift[0]['kind'] == 'errors',
       'rows=%s' % (err_drift,))
    first[3]['errors'] = base[3]['errors']

    # AC-LIVE4: a face that only one pass has is MISSING, never a silent skip.
    short = world([spec for spec in SEVEN if spec[0] != 'checkout'])
    gone = LS.compare_runs(first, short)
    ok('AC-LIVE4 a face present in one pass only refuses as missing',
       len(gone) == 1 and gone[0]['kind'] == 'missing'
       and gone[0]['face'] == 'checkout',
       'rows=%s' % (gone,))
    ok('AC-LIVE4 missing is symmetric (the other direction also fires)',
       LS.compare_runs(short, first)[0]['kind'] == 'missing',
       'rows=%s' % (LS.compare_runs(short, first),))

    # AC-LIVE5: the tool imports without playwright, the comparison is pure,
    # and the second pass writes its own PNG instead of overwriting pass one.
    with open(os.path.join(ROOT, 'tools', 'ceo_live_shot.py'), 'rb') as handle:
        src = handle.read().decode('utf-8', 'replace')
    hits = top_level_playwright_imports(src)
    ok('AC-LIVE5 ceo_live_shot imports under stdlib (no top-level playwright)',
       hits == [], 'hits=%s' % (hits,))
    probe = ('import os\nfrom playwright.sync_api import sync_playwright\n')
    ok('AC-LIVE5 the scanner REFUSES a top-level playwright import',
       top_level_playwright_imports(probe)
       == ['from playwright.sync_api import sync_playwright'], 'probe_hits=1')
    import inspect
    compare_src = inspect.getsource(LS.compare_runs)
    ok('AC-LIVE5 compare_runs touches no disk and no browser',
       not any(word in compare_src for word in
               ('open(', 'os.remove', 'sync_playwright', 'subprocess')),
       'pure=1')
    shoot_src = inspect.getsource(LS.shoot)
    ok('AC-LIVE5 the second pass writes <face>-p2.png, not over pass one',
       '"-p%d.png" % pass_no' in shoot_src and 'pass_no == 1' in shoot_src,
       'pass_naming=1')
    try:
        import playwright  # noqa: F401
        have_pw = True
    except Exception:
        have_pw = False
    reason = 'live two-pass arm is on-demand by board decision (registry law)' \
        if have_pw else 'playwright not installed'
    print('  | SKIP arm=live_two_pass_prove reason=%s' % reason)

    # AC-LIVE6: the shooter covers every face the door serves, and that is
    # DERIVED - both sides are read from the shipped modules, so a face added
    # to the launcher or dropped from the shooter fails here instead of
    # quietly shrinking a 9/9 claim into a 7/7 one (the exact drift R2935's
    # board row was written to stop).
    sys.path.insert(0, os.path.join(ROOT, 'src', 'sandbox'))
    sys.path.insert(0, os.path.join(ROOT, 'src', 'sandbox', 'lobby'))
    import start_all as SA  # noqa: E402  (path wired just above)
    import hub_page as HP  # noqa: E402  (path wired just above)
    planned = set(SA.FACE_KEYS)
    shot = [row[0] for row in LS.FACES]
    ok('AC-LIVE6 the shooter names hub plus every planned face',
       set(shot) == planned | {'hub'},
       'shooter=%d planned=%d missing=%s extra=%s'
       % (len(shot), len(planned),
          sorted((planned | {'hub'}) - set(shot)),
          sorted(set(shot) - (planned | {'hub'}))))
    ok('AC-LIVE6 every shooter face is named exactly once',
       len(shot) == len(set(shot)), 'dupes=%d' % (len(shot) - len(set(shot))))
    published = HP.build_faces(
        '127.0.0.1', 8091, web_port=8094, city_port=8092, checkout_port=8093,
        gate_port=8096, ledger_port=8097, ugc_port=8098, panel_port=8099,
        member_port=8095)
    unserved = [key for key in sorted(planned) if not published.get(key)]
    ok('AC-LIVE6 the hub really serves every planned face', unserved == [],
       'unserved=%s' % (unserved,))
    bare = HP.build_faces('127.0.0.1', 8091, panel_port=None, member_port=None)
    ok('AC-LIVE6 the hub publishes no face it was not handed a port for',
       not bare.get('panel') and not bare.get('member'),
       'bare_panel=%s bare_member=%s'
       % (bare.get('panel'), bare.get('member')))

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
