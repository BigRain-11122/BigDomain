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
the launcher and hub modules instead of counting a typed list. AC-LIVE12 was
pinned in the R2988 board row BEFORE exit_status existed (in-window
pre-registration, disclosed). Source discipline: pure ASCII, stdlib only, no
clock, no network, writes nothing into qa/.
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

    # AC-LIVE7: the record face finally has a reader on the path a PERSON
    # runs. The report already names a collision when it is published (R2981),
    # so the honest scope of this criterion is the moment nothing else speaks:
    # the report never arrives and the record is the only carrier. Every arm
    # below is a private file in a throwaway directory - no browser, no
    # launcher, no network.
    import json as _json
    import tempfile
    box = tempfile.mkdtemp(prefix='live7-')

    def record(name, payload_text):
        path = os.path.join(box, name)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(payload_text)
        return path

    collided = record('collide.json', _json.dumps(
        {'pid': 4242, 'state': 'starting',
         'override_duplicates': [[7000, ['city', 'ws']]]}))
    ok('AC-LIVE7 a collided record names both keys, not a boolean',
       LS.recorded_collisions(collided) == ((7000, ('city', 'ws')),),
       'read=%s' % (LS.recorded_collisions(collided),))

    healthy = record('healthy.json', _json.dumps(
        {'pid': 4242, 'state': 'serving', 'override_duplicates': []}))
    ok('AC-LIVE7 a healthy record reads empty', LS.recorded_collisions(healthy)
       == (), 'read=%s' % (LS.recorded_collisions(healthy),))

    absent = os.path.join(box, 'never-written.json')
    broken = record('broken.json', '{"override_duplicates": [[7000, [')
    ok('AC-LIVE7 a missing or unreadable record answers empty, never raises',
       LS.recorded_collisions(absent) == ()
       and LS.recorded_collisions(broken) == (),
       'absent=%s broken=%s' % (LS.recorded_collisions(absent),
                                LS.recorded_collisions(broken)))

    messy = record('messy.json', _json.dumps(
        {'override_duplicates': [[7002, ['gate']], ['nope', ['x']],
                                 ['7001', ['ugc', 'web']]]}))
    ok('AC-LIVE7 order is not identity and a bad port is skipped, not fatal',
       LS.recorded_collisions(messy)
       == ((7001, ('ugc', 'web')), (7002, ('gate',))),
       'read=%s' % (LS.recorded_collisions(messy),))

    with open(os.path.join(ROOT, 'tools', 'ceo_live_shot.py'), 'rb') as handle:
        shot_src = handle.read().decode('utf-8', 'replace')
    blocks = shot_src.split('if not report or not report.get("ok")', 1)
    # R2986: the window was 600 chars; naming the refusal added a few comment
    # lines and pushed `return 3` past it, so the arm read red although every
    # anchor was still in the branch. Widened, not weakened: all three
    # anchors are still required.
    branch = blocks[1][:1200] if len(blocks) == 2 else ''
    ok('AC-LIVE7 the shipped failure branch reads the merged collision field',
       len(blocks) == 2 and 'published_collisions(' in branch
       and '"record_collisions"' in branch and 'return 3' in branch,
       'wired=%d' % (len(blocks) - 1))

    # AC-LIVE8 (R2984): the record is deleted in the same finally block that
    # writes the report - measured: zero of thirteen samples taken after the
    # report was parseable still had a record. So the report is the survivor
    # on the path where it arrives, and one named field must cover both.
    collided_report = {'ok': False,
                       'errors': ['E_NOT_UP: ws,city,gate,web,hub'],
                       'override_duplicates': [[7000, ['city', 'ws']]]}
    ok('AC-LIVE8 a report that arrived names the collision with the record gone',
       LS.published_collisions(absent, collided_report)
       == ((7000, ('city', 'ws')),),
       'read=%s' % (LS.published_collisions(absent, collided_report),))
    ok('AC-LIVE8 a record alone still names it (the R2983 face is not lost)',
       LS.published_collisions(collided, None) == ((7000, ('city', 'ws')),),
       'read=%s' % (LS.published_collisions(collided, None),))
    ok('AC-LIVE8 both survivors name one collision exactly once',
       LS.published_collisions(collided, collided_report)
       == ((7000, ('city', 'ws')),),
       'read=%s' % (LS.published_collisions(collided, collided_report),))
    ok('AC-LIVE8 healthy, empty or absent answers empty',
       LS.published_collisions(absent, {'ok': True,
                                        'override_duplicates': []}) == ()
       and LS.published_collisions(absent, None) == ()
       and LS.published_collisions(healthy, {'ok': True}) == (),
       'empty=1')
    ok('AC-LIVE8 a malformed report row is skipped, not fatal',
       LS.published_collisions(
           absent, {'override_duplicates': [['nope', ['x']],
                                            [7001, ['ugc', 'web']]]})
       == ((7001, ('ugc', 'web')),), 'skipped=1')
    ok('AC-LIVE8 the merged reader really calls the record reader',
       'recorded_collisions(' in inspect.getsource(LS.published_collisions),
       'wired=1')

    # AC-LIVE9 (R2985): a REFUSED launch never claimed the record, so the file
    # on disk is the holder's and must not be credited to this launch. The
    # probe measured the defect before this criterion existed: a healthy
    # refusal plus a holder record carrying a collision returned the holder's
    # pair. Arms 2 and 3 keep the R2983/R2984 faces honest - the record is
    # still read when the report is absent or says nothing about a record.
    holding = record('holding.json', _json.dumps(
        {'pid': 4242, 'state': 'serving',
         'override_duplicates': [[7000, ['city', 'ws']]]}))
    healthy_refusal = {'ok': False,
                       'errors': ['E_LAUNCHER_ALREADY_RUNNING source=mutex'],
                       'override_duplicates': [],
                       'registry': {'path': holding, 'claimed': False,
                                    'held_by': {'pid': 4242}}}
    ok('AC-LIVE9 a refused launch does not inherit the holder record',
       LS.published_collisions(holding, healthy_refusal) == (),
       'read=%s' % (LS.published_collisions(holding, healthy_refusal),))
    ok('AC-LIVE9 a report that never arrives still reads the record',
       LS.published_collisions(holding, None) == ((7000, ('city', 'ws')),),
       'read=%s' % (LS.published_collisions(holding, None),))
    ok('AC-LIVE9 a report silent about its record still merges (no break)',
       LS.published_collisions(holding, {'ok': True}) == ((7000,
                                                          ('city', 'ws')),),
       'read=%s' % (LS.published_collisions(holding, {'ok': True}),))

    # AC-LIVE10 (R2986): the driver could not tell a REFUSED launch from a
    # BROKEN sandbox. The probe ran three real launches first: both refusal
    # doors answered E_LAUNCHER_ALREADY_RUNNING with registry.claimed False,
    # a real failure answered E_NOT_UP with claimed True - and today's driver
    # printed the same `why` for all three, leaving the difference nested.
    # This criterion pins the reader, including the honest direction: a real
    # failure must NOT be renamed a refusal.
    mutex_refusal = {'ok': False,
                     'errors': ['E_LAUNCHER_ALREADY_RUNNING source=mutex '
                                'pid=- name=Local\\BigDomainSandboxLauncher'],
                     'registry': {'path': 'x', 'claimed': False,
                                  'held_by': {'pid': 4242}}}
    seen = LS.refusal_of(mutex_refusal)
    ok('AC-LIVE10 a kernel-claim refusal names its door',
       isinstance(seen, dict)
       and seen.get('code') == 'E_LAUNCHER_ALREADY_RUNNING'
       and seen.get('door') == 'kernel-mutex'
       and seen.get('source') == 'mutex'
       and seen.get('detail') == mutex_refusal['errors'][0],
       'seen=%s' % (seen,))
    record_refusal = {'ok': False,
                      'errors': ['E_LAUNCHER_ALREADY_RUNNING pid=4242 '
                                 'hub_url=- reason=still-starting'],
                      'registry': {'path': 'x', 'claimed': False,
                                   'verdict': {'reason': 'still-starting'}}}
    seen = LS.refusal_of(record_refusal)
    ok('AC-LIVE10 a record refusal names its door and reason',
       isinstance(seen, dict) and seen.get('door') == 'machine-record'
       and seen.get('reason') == 'still-starting'
       and seen.get('source') is None, 'seen=%s' % (seen,))
    real_failure = {'ok': False, 'errors': ['E_NOT_UP: ws,city,gate,web,hub'],
                    'registry': {'path': 'x', 'claimed': True,
                                 'pid': 1, 'state': 'starting'}}
    ok('AC-LIVE10 a real failure is NOT renamed a refusal',
       LS.refusal_of(real_failure) is None,
       'seen=%r' % (LS.refusal_of(real_failure),))
    ok('AC-LIVE10 an absent or malformed report answers None without raising',
       LS.refusal_of(None) is None and LS.refusal_of({}) is None
       and LS.refusal_of({'errors': []}) is None
       and LS.refusal_of({'errors': ['E_LAUNCHER_ALREADY_RUNNING '
                                     'source=mutex']}) is None,
       'none=4')
    import socket
    import subprocess
    import launcher_mutex as LM  # noqa: E402  (sandbox path wired above)
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    clash = sock.getsockname()[1]
    sock.close()
    real_box = tempfile.mkdtemp(prefix='live10-')
    real_registry = os.path.join(real_box, 'registry.json')
    real_report = os.path.join(real_box, 'report.json')
    real_stop = os.path.join(real_box, 'stop')
    lane = LM.acquire(LM.name_for(real_registry))
    try:
        proc = subprocess.run(
            [sys.executable, LS.START_ALL, '--registry', real_registry,
             '--report-json', real_report, '--stop-file', real_stop,
             '--timeout', '2', '--check',
             '--mutex-name', LM.name_for(real_registry),
             '--ws-port', str(clash), '--city-port', str(clash)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=60)
    finally:
        LM.release(lane.get('handle'))
    with open(real_report, 'r', encoding='utf-8') as handle:
        fresh = _json.load(handle)
    read = LS.refusal_of(fresh)
    ok('AC-LIVE10 a REAL refusal reads its door through the shipped reader',
       proc.returncode != 0 and isinstance(read, dict)
       and read.get('door') == 'kernel-mutex'
       and read.get('code') == 'E_LAUNCHER_ALREADY_RUNNING',
       'read=%s rc=%s' % (read, proc.returncode))
    blocks = shot_src.split('if not report or not report.get("ok")', 1)
    wired = blocks[1][:900] if len(blocks) == 2 else ''
    ok('AC-LIVE10 the shipped failure branch publishes the refusal key',
       len(blocks) == 2 and '"refusal": refusal_of(' in wired
       and 'return 3' in wired, 'wired=%d' % (len(blocks) - 1))

    # AC-LIVE11 (R2987): the failure line was printed and then lost with the
    # process. The launcher's own --report-json belongs to the SUCCESS product
    # and it is published - the probe rewrote that one path in a throwaway
    # world and both derivers moved together, 126B -> 199B, i.e. the failure
    # would have been named and sized as the newest product while its gallery
    # half still showed a healthy run. So the payload goes to the gitignored
    # scratch file. This criterion pins the PLACE, the payload shape and the
    # honest direction: a real failure must never be written down as a
    # refusal.
    default_place = LS.failure_artifact_path()
    scratch = os.path.join(ROOT, 'tmp')
    ok('AC-LIVE11 the failure artifact lives in the scratch dir, not preview/',
       os.path.dirname(default_place) == scratch
       and os.path.basename(default_place) != 'live-sandbox.json'
       and not default_place.startswith(os.path.join(ROOT, 'preview') + os.sep),
       'place=%s' % os.path.relpath(default_place, ROOT).replace('\\', '/'))

    refused_path = os.path.join(scratch, 'live11-refused.json')
    written = LS.write_failure(absent, mutex_refusal, path=refused_path)
    with open(refused_path, 'r', encoding='utf-8') as handle:
        landed = _json.load(handle)
    ok('AC-LIVE11 a refusal lands on disk with its door named',
       bool(written) and os.path.exists(refused_path)
       and sorted(landed) == ['ok', 'record_collisions', 'refusal', 'report',
                              'why']
       and landed['ok'] is False
       and (landed['refusal'] or {}).get('door') == 'kernel-mutex',
       'keys=%s door=%s' % (sorted(landed),
                            (landed['refusal'] or {}).get('door')))

    failed_path = os.path.join(scratch, 'live11-failed.json')
    LS.write_failure(absent, real_failure, path=failed_path)
    with open(failed_path, 'r', encoding='utf-8') as handle:
        landed_fail = _json.load(handle)
    ok('AC-LIVE11 a real failure is NOT written down as a refusal',
       landed_fail['refusal'] is None and landed_fail['ok'] is False,
       'refusal=%r' % (landed_fail['refusal'],))

    collided_path = os.path.join(scratch, 'live11-collided.json')
    LS.write_failure(collided, {'ok': False, 'errors': ['E_NOT_UP: ws,city']},
                     path=collided_path)
    with open(collided_path, 'r', encoding='utf-8') as handle:
        landed_coll = _json.load(handle)
    ok('AC-LIVE11 a collision survives onto the failure artifact',
       landed_coll['record_collisions'] == [[7000, ['city', 'ws']]],
       'rows=%s' % (landed_coll['record_collisions'],))

    missing_dir = os.path.join(scratch, 'live11-absent-dir', 'x.json')
    ok('AC-LIVE11 a target it cannot write answers None without raising',
       LS.write_failure(absent, real_failure, path=missing_dir) is None
       and not os.path.isdir(os.path.dirname(missing_dir)), 'none=1')

    branch2 = shot_src.split('if not report or not report.get("ok")', 1)
    wired2 = branch2[1][:900] if len(branch2) == 2 else ''
    ok('AC-LIVE11 the shipped failure branch writes the artifact before exit',
       len(branch2) == 2 and 'write_failure(' in wired2
       and '"artifact"' in wired2
       and wired2.find('write_failure(') < wired2.find('return 3'),
       'wired=%d' % (len(branch2) - 1))
    for path in (refused_path, failed_path, collided_path):
        if os.path.exists(path):
            os.remove(path)

    # AC-LIVE12 (R2988): the docstring promised "2 = at least one face failed
    # to load or raised", and main() ended with `return code if args.check
    # else 0` - so a person running this to CHECK the sandbox got the exit code
    # of a green run. The probe drove the shipped main() with the photographic
    # layer stubbed against a real launcher on a world where every face failed
    # and measured rc=0 with payload ok=False with_errors=9; the census found
    # zero scripted callers, so making the code truthful by default breaks
    # nobody. Pinned: the mapping, the honest direction on a shapeless
    # payload, the gate's absence, and the shipped main() wiring.
    main_src = inspect.getsource(LS.main)
    ok('AC-LIVE12 the mapping matches the documented contract',
       LS.EXIT_OK == 0 and LS.EXIT_FACES == 2
       and '2 = at least one face failed' in (LS.__doc__ or '')
       and LS.exit_status({'ok': True}) == 0
       and LS.exit_status({'ok': False, 'with_errors': 3}) == 2,
       'ok=%s faces=%s doc=1' % (LS.exit_status({'ok': True}),
                                 LS.exit_status({'ok': False})))
    ok('AC-LIVE12 a missing or shapeless payload never reads as success',
       LS.exit_status(None) == 2 and LS.exit_status({}) == 2
       and LS.exit_status({'ok': 0}) == 2,
       'none=%s empty=%s falsy=%s' % (LS.exit_status(None), LS.exit_status({}),
                                      LS.exit_status({'ok': 0})))
    # The gate would live in main()'s return, so the absence is judged there:
    # the module docstring may quote the old line as history without this arm
    # reading red over a quotation.
    ok('AC-LIVE12 the flag gate is gone from the shipped main',
       'args.check else' not in main_src, 'gate=%s'
       % ('args.check else' in main_src))
    ok('AC-LIVE12 the shipped main returns the mapped code',
       main_src.rstrip().endswith('return code')
       and 'exit_status(payload)' in main_src,
       'maps=%s' % ('exit_status(payload)' in main_src))
    ok('AC-LIVE12 --check is still accepted as a compatibility alias',
       '"--check"' in shot_src and 'compatibility' in shot_src,
       'compat=1')
    exit_src = inspect.getsource(LS.exit_status)
    ok('AC-LIVE12 exit_status is pure (no disk, no browser, no subprocess)',
       not any(word in exit_src for word in
               ('open(', 'subprocess', 'sync_playwright', 'os.remove')),
       'pure=1')

    # AC-LIVE13 (R2988 second pin): the round's OWN real run answered rc=0 with
    # eighteen shots, and the page a person opens showed nine empty frames -
    # the gallery lives in preview/ while the shots live in preview/live/, so
    # a bare basename pointed every <img> at preview/hub.png
    # (measured: no such file). Pinned: the reference must RESOLVE from the
    # page's own directory, and that is graded by touching a real file.
    import re as _re
    lane = tempfile.mkdtemp(prefix='live13-')
    page_dir = os.path.join(lane, 'preview')
    shots_dir = os.path.join(page_dir, 'live')
    os.makedirs(shots_dir)
    png_abs = os.path.join(shots_dir, 'hub.png')
    with open(png_abs, 'wb') as handle:
        handle.write(b'\x89PNG\r\n\x1a\n fake but present')
    def lane_row(face, png, okflag=True, why=''):
        base = row(face, okflag=okflag)
        base.update({'title': face, 'blurb': 'blurb', 'url': 'u',
                     'why': why, 'png': png})
        return base

    lane_rows = [lane_row('hub', os.path.join('preview', 'live', 'hub.png')),
                 lane_row('lobby', None, okflag=False, why='no picture')]
    page_path = os.path.join(page_dir, 'live-sandbox.html')
    LS.gallery(lane_rows, {'ok': True}, page_path)
    with open(page_path, 'r', encoding='utf-8') as handle:
        html = handle.read()
    srcs = _re.findall(r"<img src='([^']+)'", html)
    want = os.path.abspath(os.path.join(ROOT, 'preview', 'live', 'hub.png'))
    resolved = [os.path.normpath(os.path.join(page_dir, src)) for src in srcs]
    ok('AC-LIVE13 the reference is resolved from the page directory',
       srcs != ['hub.png'] and resolved == [want],
       'srcs=%s' % (srcs,))
    ok('AC-LIVE13 every referenced picture really exists where it points',
       bool(srcs) and all(os.path.exists(path) for path in resolved),
       'resolved=%s' % resolved)
    ok('AC-LIVE13 no backslash reaches the html',
       '\\' not in ''.join(srcs), 'srcs=%s' % (srcs,))
    ok('AC-LIVE13 a row without a picture emits no img and does not raise',
       len(srcs) == 1 and 'no picture' in html, 'imgs=%d' % len(srcs))

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
