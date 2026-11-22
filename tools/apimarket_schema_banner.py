#!/usr/bin/env python3
"""Page-local schema banner for the frozen apimarket report faces.

The thirteen faces pinned by state/apimarket-face-freeze.json are titled
"Settlement Ledger" and printed no schema at all, so a reader had no way to
tell a schema-4 snapshot from the current schema-17 generator.  This tool
injects one banner per face that says which schema the page's numbers came
from, which schema the generator is on today, and whether they agree.

It never touches a generator: the pages have none.  It never adds an href,
so the route law is unaffected.  The banner text lives in
state/apimarket-schema-banner.json (Chinese goes in data, the source here
stays ASCII), and the current schema is parsed from
src/sandbox/ledger/apimarket_report.py at run time instead of being pinned.

Criteria AC-ASB1..6 (pre-registered in src/os/backlog.md before this file):
  ASB1 exactly one banner block per frozen face
  ASB2 declared schema == sibling json schema_version, current == report source
  ASB3 stale token is one of yes/same/unknown and the visible sentence is the
       exact fresh-derived line for that token
  ASB4 the freeze manifest still matches the bytes on disk afterwards
  ASB5 a second --write changes nothing
  ASB6 only the frozen html files are written; json and other pages untouched
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "state", "apimarket-face-freeze.json")
DATA = os.path.join(ROOT, "state", "apimarket-schema-banner.json")
REPORT = os.path.join(ROOT, "src", "sandbox", "ledger", "apimarket_report.py")

ANCHOR = "</header>"
BANNER_RE = re.compile(r'<div class="wrap"><div class="schema-banner".*?</div></div>',
                       re.S)
BLOCK_MARK = 'data-schema-banner="'
STALE_TOKENS = ("yes", "same", "unknown")


def set_root(root):
    """Point the four module paths at another tree (negative controls only)."""
    global ROOT, MANIFEST, DATA, REPORT
    ROOT = os.path.abspath(root)
    MANIFEST = os.path.join(ROOT, "state", "apimarket-face-freeze.json")
    DATA = os.path.join(ROOT, "state", "apimarket-schema-banner.json")
    REPORT = os.path.join(ROOT, "src", "sandbox", "ledger", "apimarket_report.py")


def load_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.loads(handle.read())


def sha256(path):
    digest = hashlib.sha256()
    with io.open(path, "rb") as handle:
        while True:
            chunk = handle.read(1 << 16)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def current_schema():
    text = io.open(REPORT, "r", encoding="utf-8").read()
    match = re.search(r"^REPORT_SCHEMA\s*=\s*(\d+)\s*$", text, re.M)
    if not match:
        raise SystemExit("E_ASB2 cannot read REPORT_SCHEMA from %s" % REPORT)
    return int(match.group(1))


def frozen_faces():
    doc = load_json(MANIFEST)
    faces = doc.get("faces")
    if not isinstance(faces, list) or not faces:
        raise SystemExit("E_ASB1 freeze manifest has no faces: %s" % MANIFEST)
    return faces


def declared_of(face):
    value = face.get("schema_version")
    return None if value is None else int(value)


def verdict(declared, current):
    if declared is None:
        return "unknown"
    return "same" if declared == current else "yes"


def banner_text(data, face, current):
    declared = declared_of(face)
    stale = verdict(declared, current)
    key = {"yes": "line_stale", "same": "line_same", "unknown": "line_unknown"}[stale]
    body = data[key].format(
        slug=face["slug"],
        declared="unknown" if declared is None else declared,
        current=current,
        stale=stale)
    head = data["banner_open"].format(
        slug=face["slug"],
        declared="unknown" if declared is None else declared,
        current=current,
        stale=stale)
    return head + body + data["banner_close"]


def page_path(face):
    return os.path.join(ROOT, face["html"].replace("/", os.sep))


def apply_banner(text, banner, problems, slug):
    found = BANNER_RE.findall(text)
    if len(found) > 1:
        problems.append("E_ASB1 %r already carries %d banner blocks"
                        % (slug, len(found)))
        return None
    if found:
        return BANNER_RE.sub(lambda _m: banner, text, count=1)
    if ANCHOR not in text:
        problems.append("E_ASB1 %r has no %s anchor" % (slug, ANCHOR))
        return None
    head, rest = text.split(ANCHOR, 1)
    return head + ANCHOR + banner + rest


def write(data):
    current = current_schema()
    problems = []
    changed = []
    for face in frozen_faces():
        path = page_path(face)
        if not os.path.isfile(path):
            problems.append("E_ASB1 frozen face %r is not on disk" % face["slug"])
            continue
        text = io.open(path, "r", encoding="utf-8", newline="").read()
        banner = banner_text(data, face, current)
        fresh = apply_banner(text, banner, problems, face["slug"])
        if fresh is None or fresh == text:
            continue
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(fresh)
        changed.append(face["slug"])
    return current, changed, problems


def check(data):
    current = current_schema()
    fails = []
    faces = frozen_faces()
    seen = set()
    for face in faces:
        slug = face["slug"]
        seen.add(slug)
        path = page_path(face)
        if not os.path.isfile(path):
            fails.append("E_ASB1 %r is not on disk" % slug)
            continue
        text = io.open(path, "r", encoding="utf-8", newline="").read()
        blocks = text.count(BLOCK_MARK)
        if blocks != 1:
            fails.append("E_ASB1 %r carries %d banner blocks" % (slug, blocks))
            continue
        expected = banner_text(data, face, current)
        if expected not in text:
            fails.append("E_ASB2/3 %r banner is not the fresh-derived one" % slug)
        stale = verdict(declared_of(face), current)
        if stale not in STALE_TOKENS:
            fails.append("E_ASB3 %r verdict %r out of the closed set"
                         % (slug, stale))
        size = os.path.getsize(path)
        if size != face.get("html_bytes"):
            fails.append("E_ASB4 %r bytes %d != manifest %r"
                         % (slug, size, face.get("html_bytes")))
        if sha256(path) != face.get("html_sha256"):
            fails.append("E_ASB4 %r sha256 != manifest" % slug)
    return current, faces, seen, fails


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true",
                        help="inject or refresh the banner on every frozen face")
    parser.add_argument("--check", action="store_true",
                        help="read-only verification of AC-ASB1..4")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--root", default=None,
                        help="operate on another tree (negative controls)")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        parser.print_usage(sys.stderr)
        return 2
    if args.root:
        set_root(args.root)
    data = load_json(DATA)
    if args.write:
        current, changed, problems = write(data)
        payload = {"current": current, "changed": changed,
                   "changed_count": len(changed), "problems": problems}
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print("SCHEMA BANNER WRITE current=%d changed=%d problems=%d"
                  % (current, len(changed), len(problems)))
            for row in changed:
                print("  wrote %s" % row)
        for row in problems:
            print("  %s" % row)
        return 1 if problems else 0
    current, faces, seen, fails = check(data)
    if args.json:
        print(json.dumps({"current": current, "faces": len(faces),
                          "fails": fails}, sort_keys=True))
    else:
        print("SCHEMA BANNER CHECK current=%d faces=%d fails=%d"
              % (current, len(faces), len(fails)))
        for row in fails:
            print("  %s" % row)
    if not fails:
        print("VERDICT PASS criteria=6")
        return 0
    print("VERDICT FAIL")
    return 2


if __name__ == "__main__":
    sys.exit(main())
