"""Battery suite for tools/face_walk.py - criteria AC-FWS1..AC-FWS5 (R2931).

WHY: R2930 shipped the first browser walk in this repo and it found a real
defect (three dead links born of repo-relative hrefs on a page inside preview/).
But face_walk needs playwright, which is not stdlib, so it could not be a SUITES
row and nothing graded it. The board carried that debt to this window.

The ruling is NOT to run a browser inside the battery (registry law: stdlib
only, zero network, zero shell). It is to move the two laws the browser walk
depends on into pure functions - page-relative link resolution and the PNG
signature check - grade those here, and print the browser arm as a SKIP BY NAME
so an unrun arm can never read as a pass.

Coverage, stated honestly: this suite grades static href attributes. A link a
page's own JavaScript injects at runtime is visible to the browser walk and NOT
to this suite; that boundary is the price of the registry law, not a claim.

PINNED BEFORE THE CODE: AC-FWS1..AC-FWS5 were written into src/os/backlog.md in
the same window, BEFORE dead_targets/png_ok existed - in-window
pre-registration, disclosed as such. Source discipline: pure ASCII, stdlib only,
no clock, no network, writes nothing into qa/.
"""
import glob
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import face_walk as FW

HREF_RE = re.compile(r'href=["\']([^"\']+)["\']')
FAILS = []
CHECKS = []


def ok(name, cond, detail=''):
    CHECKS.append(name)
    if cond:
        print('  | PASS %s %s' % (name, detail))
    else:
        FAILS.append(name)
        print('  | FAIL %s %s' % (name, detail))


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


def census(page_paths):
    """Count static hrefs and the dead ones, page-relative, in one pass."""
    hrefs_total = 0
    dead = []
    for path in page_paths:
        with open(path, 'rb') as fh:
            text = fh.read().decode('utf-8', 'replace')
        hrefs = HREF_RE.findall(text)
        hrefs_total += len(hrefs)
        for href in FW.dead_targets(path, hrefs):
            dead.append((os.path.basename(path), href))
    return hrefs_total, dead


def main():
    # AC-FWS1: one law, page-relative, and walk_page delegates to it.
    with tempfile.TemporaryDirectory() as tmp:
        page_dir = os.path.join(tmp, 'preview')
        os.makedirs(page_dir)
        page = os.path.join(page_dir, 'a.html')
        with open(page, 'w', encoding='utf-8') as fh:
            fh.write('<a href="x.html">x</a><a href="preview/x.html">bad</a>')
        with open(os.path.join(page_dir, 'x.html'), 'w', encoding='utf-8') as fh:
            fh.write('')
        dead = FW.dead_targets(page, ['x.html', 'preview/x.html'])
        ok('AC-FWS1 repo-relative href on a page in preview/ is DEAD',
           dead == ['preview/x.html'], 'dead=%s' % dead)
        nested = os.path.join(page_dir, 'preview')
        os.makedirs(nested)
        with open(os.path.join(nested, 'x.html'), 'w', encoding='utf-8') as fh:
            fh.write('')
        ok('AC-FWS1 same href is ALIVE once the page-relative target exists',
           FW.dead_targets(page, ['x.html', 'preview/x.html']) == [], 'dead=[]')
        import inspect
        src = inspect.getsource(FW.walk_page)
        ok('AC-FWS1 walk_page delegates to dead_targets (no second copy)',
           'dead_targets(' in src, 'found=%s' % ('dead_targets(' in src))

    # AC-FWS2: remote and non-file links are never counted.
    skips = ['http://x/y', 'https://x/y', '//cdn/x.js', '#top', 'mailto:a@b',
             'javascript:void(0)', 'data:text/plain,hi', 'tel:123']
    survived = [h for h in skips if FW._local_href(h) is not None]
    ok('AC-FWS2 all eight non-file prefixes resolve to None',
       survived == [], 'leaked=%s' % survived)
    ok('AC-FWS2 local href keeps its target and drops query+fragment',
       FW._local_href('x.html') == 'x.html'
       and FW._local_href('x.html?a=1#b') == 'x.html'
       and FW._local_href('  ../docs/y.md  ') == '../docs/y.md',
       'local=ok')

    # AC-FWS3: the PNG signature law is one shipped function.
    ok('AC-FWS3 real signature passes, truncation/JPEG/zero fail',
       FW.png_ok(FW.PNG_SIG, 10) is True
       and FW.png_ok(FW.PNG_SIG[:7], 10) is False
       and FW.png_ok(b'\xff\xd8\xff\xe0\x00\x10JF', 10) is False
       and FW.png_ok(FW.PNG_SIG, 0) is False,
       'png_ok=four-way')
    ok('AC-FWS3 walk_page delegates to png_ok (no second copy)',
       'png_ok(' in inspect_source_walk(), 'found=%s'
       % ('png_ok(' in inspect_source_walk()))

    # AC-FWS4: the live census, with no browser at all.
    pages = sorted(glob.glob(os.path.join(ROOT, 'preview', '*.html')))
    href_total, dead_rows = census(pages)
    ok('AC-FWS4 the census measured a non-empty page set', len(pages) > 0,
       'pages=%d' % len(pages))
    ok('AC-FWS4 every live preview page has ZERO dead static links',
       dead_rows == [], 'pages=%d hrefs=%d dead=%d sample=%s'
       % (len(pages), href_total, len(dead_rows), dead_rows[:5]))
    with tempfile.TemporaryDirectory() as tmp:
        bad_dir = os.path.join(tmp, 'preview')
        os.makedirs(bad_dir)
        bad_page = os.path.join(bad_dir, 'bad.html')
        with open(bad_page, 'w', encoding='utf-8') as fh:
            fh.write('<a href="preview/gone.html">gone</a>')
        bad_hrefs, bad_dead = census([bad_page])
        ok('AC-FWS4 the census FIRES on a doctored world (dead=1)',
           bad_hrefs == 1 and bad_dead == [('bad.html', 'preview/gone.html')],
           'hrefs=%d dead=%s' % (bad_hrefs, bad_dead))

    # AC-FWS5: the browser arm is skipped by name, never silently passed.
    with open(os.path.join(ROOT, 'tools', 'face_walk.py'), 'rb') as fh:
        tool_src = fh.read().decode('utf-8', 'replace')
    hits = top_level_playwright_imports(tool_src)
    ok('AC-FWS5 face_walk imports under stdlib (no top-level playwright)',
       hits == [], 'hits=%s' % hits)
    probe = ('import os\nfrom playwright.sync_api import sync_playwright\n'
             'def f():\n    import playwright\n')
    ok('AC-FWS5 the scanner REFUSES a top-level playwright import',
       top_level_playwright_imports(probe)
       == ['from playwright.sync_api import sync_playwright'],
       'probe_hits=1')
    try:
        import playwright  # noqa: F401
        have_pw = True
    except Exception:
        have_pw = False
    reason = 'browser arm is on-demand by board decision (registry law)' \
        if have_pw else 'playwright not installed'
    print('  | SKIP arm=face_walk_browser reason=%s' % reason)

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


def inspect_source_walk():
    import inspect
    return inspect.getsource(FW.walk_page)


if __name__ == '__main__':
    sys.exit(main())
