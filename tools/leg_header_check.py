"""Decide whether a leg's HEADER registry numbers are stale-by-date or a lie.

WHY: tools/leg_audit.py grades three shapes of drift (counts, duplicates, row
coherence) and deliberately does not compare a leg's header
`registry_suites=/registry_criteria=` pair against src/sandbox/reconcile_all.py.
R2889 named that as a gap and R2891 named the wrinkle: registering a suite AFTER
a leg closes will make that leg's header LEGITIMATELY stale, so a naive equality
check would reject honest legs and, worse, teach the operator to ignore it.

So the discriminator is TIME, not equality: a header that disagrees with the
current registry is either

  * DRIFT-DATED - the registry file was modified AFTER the leg was born, so the
    header truthfully describes the registry at launch and the leg stays
    publishable, provided its numbers are quoted as "at launch";
  * HEADER-LIES - the registry has NOT moved since the leg was born, so the
    header numbers were already wrong when they were written and the leg must
    not be published.

When the filesystem cannot supply a birth time and no launch time is declared,
this tool REFUSES TO GUESS (exit 3) instead of picking a side, because a wrong
side here silently launders a lying header into an adopted family number.

Usage:
    python tools/leg_header_check.py <leg.log> [--registry PATH]
                                    [--launched ISO8601] [--json]

Exit codes: 0 AGREE or DRIFT-DATED, 2 HEADER-LIES, 3 cannot decide/unreadable.
Source discipline: pure ASCII, stdlib only, no network, no clock read of "now".
"""
import json
import os
import re
import sys

HEADER_RE = re.compile(r'^SHARD\s+.*$')
FIELD_RE = re.compile(r'(\w+)=(\S+)')

DEF_REGISTRY = os.path.join('src', 'sandbox', 'reconcile_all.py')


def load_registry(path):
    """Run the registry file in a private namespace and return (suites, criteria).

    The battery registry is a literal SUITES list, so exec is what the battery
    itself relies on; anything that fails to expose SUITES is unreadable rather
    than zero.
    """
    src = open(path, 'r', encoding='utf-8-sig').read()
    ns = {'__name__': 'leg_header_registry', '__file__': path}
    exec(compile(src, path, 'exec'), ns)
    suites = ns.get('SUITES')
    if not isinstance(suites, list):
        raise ValueError('E_REGISTRY_NO_SUITES')
    return len(suites), sum(int(row[2]) for row in suites)


def read_header(path):
    """Return the k=v fields of the FIRST SHARD line that carries `selected`."""
    for raw in open(path, 'r', encoding='utf-8-sig', errors='replace'):
        line = raw.strip()
        if not line.startswith('SHARD') or line.startswith('SHARD row '):
            continue
        fields = dict(FIELD_RE.findall(line))
        if 'selected' in fields:
            return fields
    return None


def birth_time(path):
    """(timestamp, source) for when the file first existed, or (None, reason).

    Windows exposes creation time through st_ctime; platforms with st_birthtime
    expose it directly; elsewhere st_ctime is the inode change time and calling
    it a birth time would be a lie, so it is refused by name.
    """
    st = os.stat(path)
    born = getattr(st, 'st_birthtime', None)
    if born:
        return float(born), 'birthtime'
    if sys.platform == 'win32':
        return float(st.st_ctime), 'ctime-creation'
    return None, 'no-birthtime-on-%s' % sys.platform


def parse_iso(text):
    """Parse `YYYY-MM-DDTHH:MM[:SS]` (or a space separator) to a local timestamp.

    No timezone arithmetic is attempted: a declared launch time is compared with
    a filesystem mtime, and both are local wall clock on this box. An unparseable
    declaration returns None so the caller can refuse rather than ignore it.
    """
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?$', text.strip())
    if not m:
        return None
    import time as _time
    parts = [int(g) if g else 0 for g in m.groups()]
    try:
        return _time.mktime(tuple(parts + [0, 0, -1]))
    except (OverflowError, ValueError):
        return None


def check(leg_path, registry_path, launched=None):
    """Return {'verdict', 'reasons', 'facts'} for one leg/registry pair."""
    reasons = []
    facts = {'file': leg_path, 'registry': registry_path}

    try:
        header = read_header(leg_path)
    except OSError as exc:
        return {'verdict': 'UNDECIDABLE', 'reasons': ['E_LEG_UNREADABLE:%s' % exc],
                'facts': facts}
    if header is None:
        return {'verdict': 'UNDECIDABLE', 'reasons': ['E_NO_HEADER'],
                'facts': facts}

    def as_int(key):
        try:
            return int(header[key])
        except (KeyError, ValueError):
            return None

    h_suites, h_crit = as_int('registry_suites'), as_int('registry_criteria')
    facts.update({'header_suites': h_suites, 'header_criteria': h_crit})
    if h_suites is None or h_crit is None:
        return {'verdict': 'UNDECIDABLE',
                'reasons': ['E_HEADER_NO_REGISTRY_FIELDS'],
                'facts': facts}

    try:
        r_suites, r_crit = load_registry(registry_path)
    except (OSError, ValueError, SyntaxError, TypeError) as exc:
        return {'verdict': 'UNDECIDABLE', 'reasons': ['E_REGISTRY_UNREADABLE:%s' % exc],
                'facts': facts}
    facts.update({'registry_suites': r_suites, 'registry_criteria': r_crit})

    if (h_suites, h_crit) == (r_suites, r_crit):
        facts.update({'birth': None, 'birth_source': 'not-needed'})
        return {'verdict': 'AGREE', 'reasons': [], 'facts': facts}

    # They disagree. Which side is lying is decided by WHEN the registry moved.
    if launched is not None:
        born = parse_iso(launched)
        if born is None:
            return {'verdict': 'UNDECIDABLE',
                    'reasons': ['E_LAUNCHED_UNPARSEABLE:%s' % launched],
                    'facts': facts}
        source = 'declared'
    else:
        born, source = birth_time(leg_path)

    try:
        moved = os.stat(registry_path).st_mtime
    except OSError as exc:
        return {'verdict': 'UNDECIDABLE', 'reasons': ['E_REGISTRY_STAT:%s' % exc],
                'facts': facts}
    facts.update({'birth': born, 'birth_source': source, 'registry_mtime': moved})

    if born is None:
        return {'verdict': 'UNDECIDABLE',
                'reasons': ['E_NO_BIRTH_CLOCK:%s' % source],
                'facts': facts}

    if moved > born:
        return {'verdict': 'DRIFT-DATED', 'reasons': [], 'facts': facts}
    reasons.append('E_HEADER_LIES:%d/%d!=%d/%d'
                   % (h_suites, h_crit, r_suites, r_crit))
    return {'verdict': 'HEADER-LIES', 'reasons': reasons, 'facts': facts}


def render(result):
    """One line, same dialect as the leg it describes."""
    f = result['facts']
    named = ','.join(result['reasons'][:4]) or 'none'
    return ('LEG-HEADER %s file=%s header=%s/%s registry=%s/%s birth=%s '
            'source=%s registry_mtime=%s reasons=%s'
            % (result['verdict'], f.get('file'), f.get('header_suites'),
               f.get('header_criteria'), f.get('registry_suites'),
               f.get('registry_criteria'), f.get('birth'),
               f.get('birth_source'), f.get('registry_mtime'), named))


def main(argv):
    leg = None
    registry = DEF_REGISTRY
    launched = None
    as_json = '--json' in argv
    it = iter(range(len(argv)))
    for i in it:
        arg = argv[i]
        if arg == '--registry':
            if i + 1 >= len(argv):
                print('E_ARG_DANGLING --registry')
                return 3
            registry = argv[i + 1]
            next(it, None)
        elif arg == '--launched':
            if i + 1 >= len(argv):
                print('E_ARG_DANGLING --launched')
                return 3
            launched = argv[i + 1]
            next(it, None)
        elif arg in ('-h', '--help'):
            print('usage: leg_header_check.py <leg.log> [--registry PATH] '
                  '[--launched ISO8601] [--json]')
            return 0
        elif arg.startswith('-'):
            print('E_ARG_UNKNOWN %s' % arg)
            return 3
        elif leg is None:
            leg = arg
        else:
            print('E_ARG_EXTRA %s' % arg)
            return 3
    if leg is None:
        print('usage: leg_header_check.py <leg.log> [--registry PATH] '
              '[--launched ISO8601] [--json]')
        return 3

    result = check(leg, registry, launched)
    if as_json:
        print(json.dumps(result, indent=1, sort_keys=True))
    else:
        print(render(result))
    if result['verdict'] in ('AGREE', 'DRIFT-DATED'):
        return 0
    if result['verdict'] == 'HEADER-LIES':
        return 2
    return 3


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
