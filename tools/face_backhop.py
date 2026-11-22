"""One post-render channel that gives every silent endpoint a visible way back.

Why a post-render channel instead of editing the generators: probe R3288 named
40 producer scripts for the 32 declared termini, and 13 of those faces have no
on-disk producer at all (the preview face came from a one-off invocation, and
apimarket_report.py only writes whatever --out it is given). Editing "each
generator" therefore cannot cover every face, while a single channel can.

Criteria AC-FBH1..AC-FBH6 (pinned in src/os/backlog.md, R3288 PIN line, before
this file existed):

  AC-FBH1 exactly one marked block per recorded face
  AC-FBH2 the block links a file that exists and is operable (controls > 0)
  AC-FBH3 printed bytes/controls equal the fresh reading
  AC-FBH4 the target equals the first matching RULES entry for that face, and
          the block carries a non-empty rule + reason (no silent fallback)
  AC-FBH5 a face whose sibling json carries a sizes{html} block must record the
          post-injection byte count (changing a page without the number is red)
  AC-FBH6 no graves: a recorded face missing from disk, or a block that no
          longer matches its record, is red

Nothing here renders a face, runs JS, opens a socket or touches the network.
"""
import argparse
import html
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import buyer_trial  # noqa: E402  (single definition of controls)

PREVIEW = os.path.join(ROOT, "preview")
TERMINI = os.path.join(ROOT, "state", "route-termini.json")
REPORT = os.path.join(ROOT, "state", "backhop-report.json")

MARK_ATTR = 'data-back-hop'
BLOCK_RE = re.compile(r'<div class="backhop"[^>]*>.*?</div>\s*', re.S)

# Ordered face-family rules. The first matching pattern decides the target and
# the sentence the reader sees. A face that matches nothing is an error rather
# than a silent default: AC-FBH4 grades that every block names its rule.
RULES = [
    (
        r'^apimarket-',
        "buyer-trial.html",
        "市场/结算读数面：回到这一族里唯一能下单的那一页",
    ),
    (
        r'^(lobby-(ws-report|session-trace))\.html$',
        "merchant-onboard.html",
        "大厅协议读数面：回到「这套协议要真跑起来还缺什么」那一页",
    ),
    (
        r'.*',
        "index.html",
        "内部/CEO 读数面：回到全站清单页，从这里挑下一页",
    ),
]


def load_json(path, default=None):
    if not os.path.isfile(path):
        return default
    with io.open(path, "r", encoding="utf-8") as fh:
        return json.loads(fh.read())


def dump_json(path, doc):
    payload = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
    return len(payload.encode("utf-8"))


def rule_for(face):
    for pattern, back, reason in RULES:
        if re.match(pattern, face):
            return back, reason
    return None, None


def block(face, preview=None):
    """Render the visible back-hop block for one face."""
    preview = preview or PREVIEW
    back, reason = rule_for(face)
    if not back:
        raise SystemExit("no rule matches face %s" % face)
    size, controls = buyer_trial.measure_hop(os.path.join(preview, back))
    return (
        '<div class="backhop" %s="1" data-back-face="%s" data-back-rule="%s"'
        ' data-back-bytes="%d" data-back-controls="%d"'
        ' style="border-top:1px solid rgba(128,128,128,.35);margin:22px 0 0;'
        'padding:10px 0 0;font-size:13px;line-height:1.6">\n'
        '<span style="opacity:.75">这是读数页，没有可填的东西。</span> '
        '回到可点的那一页：<a href="%s" data-back-target="1">%s</a> '
        '<span style="opacity:.7">&middot; %d 个控件 · %dB</span> '
        '<span style="opacity:.6">（%s；浏览器后退也行）</span>\n'
        '</div>\n'
        % (
            MARK_ATTR,
            html.escape(face, quote=True),
            html.escape(reason, quote=True),
            size,
            controls,
            html.escape(back, quote=True),
            html.escape(back),
            controls,
            size,
            html.escape(reason),
        )
    )


def inject_text(text, face):
    """Idempotent: replace a landed block, else insert before </body>, else append."""
    fresh = block(face)
    if BLOCK_RE.search(text):
        return BLOCK_RE.sub(fresh, text, count=1), "replaced"
    pos = text.rfind("</body>")
    if pos >= 0:
        return text[:pos] + fresh + text[pos:], "inserted"
    return text + fresh, "appended"


def sizes_span(raw):
    """(start, end) of the value of the "sizes" key inside a json document."""
    hit = re.search(r'"sizes"\s*:\s*\{', raw)
    if not hit:
        return None
    start = hit.end() - 1
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
    return None


def patch_sizes(page_path):
    """Keep a recorded sizes block equal to the bytes now on disk.

    The numbers are edited in place instead of re-serialising the document:
    a json.dumps round trip reorders keys, and a file whose recorded size is
    its own byte count would then chase its own formatting. Each pass patches
    only the digits, so the rest of the document stays byte-identical, and the
    loop repeats until the recorded numbers match the files on disk (writing
    the "json" number can change the json's own length).
    """
    json_path = page_path[:-5] + ".json"
    if not os.path.isfile(json_path):
        return None
    changed = False
    for _ in range(12):
        with io.open(json_path, "r", encoding="utf-8", newline="") as fh:
            raw = fh.read()
        span = sizes_span(raw)
        if span is None:
            return None
        block = raw[span[0]:span[1]]
        try:
            sizes = json.loads(block)
        except ValueError:
            return None
        if not isinstance(sizes, dict) or "html" not in sizes:
            return None
        want = {"html": os.path.getsize(page_path),
                "json": os.path.getsize(json_path)}
        stale = [(k, sizes[k], want[k]) for k in ("html", "json")
                 if k in sizes and sizes[k] != want[k]]
        if not stale:
            return changed
        new_block = block
        for key, old, new in stale:
            new_block = re.sub(r'("%s"\s*:\s*)%d' % (key, old),
                               lambda m, v=new: m.group(1) + str(v),
                               new_block, count=1)
        if new_block == block:
            return changed
        with io.open(json_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(raw[:span[0]] + new_block + raw[span[1]:])
        changed = True
    return changed


def write(preview=None, termini=None, report=None):
    preview = preview or PREVIEW
    termini = termini or TERMINI
    report = report or REPORT
    previous = (load_json(report, {}) or {}).get("faces") or {}
    faces = [t["face"] for t in (load_json(termini, {}).get("termini") or [])]
    if not faces:
        # After the first pass these faces have a downstream, so the endpoint
        # closure derives empty; the report is then the list that must keep
        # its block (AC-FBH6), and re-running stays idempotent.
        faces = sorted(previous)
    if not faces:
        sys.stderr.write("nothing to inject: %s declares no endpoint\n" % termini)
        return 2
    rows = []
    for face in faces:
        page = os.path.join(preview, face)
        if not os.path.isfile(page):
            sys.stderr.write("missing face %s\n" % face)
            return 2
        text = io.open(page, encoding="utf-8").read()
        before = len(text.encode("utf-8"))
        new_text, how = inject_text(text, face)
        with io.open(page, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new_text)
        after = os.path.getsize(page)
        patched = patch_sizes(page)
        back, reason = rule_for(face)
        rows.append({
            "face": face,
            "back": back,
            "rule_reason": reason,
            "how": previous.get(face, {}).get("how", how),
            "bytes_before": before,
            "bytes_after": after,
            "sizes_patched": bool(patched),
        })
        print("%s %s -> %s (%d -> %d bytes%s)"
              % (how, face, back, before, after,
                 ", sizes patched" if patched else ""))
    doc = {
        "law": "a read-only face must show the reader a clickable way back to an operable page",
        "back_rule_count": len(RULES),
        "face_count": len(rows),
        "sizes_patched": sum(1 for r in rows if r["sizes_patched"]),
        "faces": {r["face"]: r for r in rows},
    }
    size = dump_json(report, doc)
    print("backhop report written: %s (%d bytes, faces=%d, sizes patched=%d)"
          % (report, size, len(rows), doc["sizes_patched"]))
    return 0


def problems(preview=None, report=None):
    preview = preview or PREVIEW
    report = report or REPORT
    doc = load_json(report, {}) or {}
    faces = doc.get("faces") or {}
    fails = []
    if not faces:
        return ["AC-FBH0 report carries no faces (%s)" % report], faces
    for face in sorted(faces):
        rec = faces[face]
        page = os.path.join(preview, face)
        if not os.path.isfile(page):
            fails.append("AC-FBH6 recorded face missing from disk: %s" % face)
            continue
        text = io.open(page, encoding="utf-8").read()
        found = BLOCK_RE.findall(text)
        if len(found) != 1:
            fails.append("AC-FBH1 %s carries %d back blocks (want 1)" % (face, len(found)))
            continue
        chunk = found[0]
        back, reason = rule_for(face)
        target = re.search(r'data-back-target="1">[^<]*</a>', chunk)
        href = re.search(r'<a href="([^"]+)" data-back-target="1"', chunk)
        if not target or not href:
            fails.append("AC-FBH1 %s block carries no marked target link" % face)
            continue
        href = html.unescape(href.group(1))
        back_path = os.path.join(preview, href)
        size, controls = buyer_trial.measure_hop(back_path)
        if not os.path.isfile(back_path):
            fails.append("AC-FBH2 %s links a file not on disk: %s" % (face, href))
        elif controls <= 0:
            fails.append("AC-FBH2 %s links a read-only page (controls=0): %s" % (face, href))
        got_bytes = re.search(r'data-back-bytes="(\d+)"', chunk)
        got_controls = re.search(r'data-back-controls="(\d+)"', chunk)
        if not got_bytes or not got_controls:
            fails.append("AC-FBH3 %s block does not print its readings" % face)
        elif (int(got_bytes.group(1)) != size
              or int(got_controls.group(1)) != controls):
            fails.append("AC-FBH3 %s prints bytes/controls %s/%s fresh=%d/%d"
                         % (face, got_bytes.group(1), got_controls.group(1),
                            size, controls))
        if href != back or rec.get("back") != back:
            fails.append("AC-FBH4 %s back=%s rule=%s record=%s"
                         % (face, href, back, rec.get("back")))
        rule_attr = re.search(r'data-back-rule="([^"]*)"', chunk)
        if not rule_attr or not html.unescape(rule_attr.group(1)).strip():
            fails.append("AC-FBH4 %s block names no rule reason" % face)
        json_path = page[:-5] + ".json"
        sdoc = load_json(json_path)
        sizes = sdoc.get("sizes") if isinstance(sdoc, dict) else None
        if isinstance(sizes, dict) and "html" in sizes:
            if sizes.get("html") != os.path.getsize(page):
                fails.append("AC-FBH5 %s sizes.html=%s disk=%d"
                             % (face, sizes.get("html"), os.path.getsize(page)))
    return fails, faces


def check(preview=None, report=None):
    fails, faces = problems(preview, report)
    if fails:
        for line in fails:
            print("FAIL %s" % line)
        print("BACKHOP CHECK FAIL fails=%d faces=%d" % (len(fails), len(faces)))
        return 2
    by_back = {}
    for rec in faces.values():
        by_back[rec.get("back")] = by_back.get(rec.get("back"), 0) + 1
    print("BACKHOP CHECK PASS fails=0 faces=%d targets=%d %s"
          % (len(faces), len(by_back),
             " ".join("%s=%d" % (k, v) for k, v in sorted(by_back.items()))))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="give every declared endpoint a visible, clickable way back")
    parser.add_argument("--write", action="store_true",
                        help="inject the marked back-hop block into every declared endpoint")
    parser.add_argument("--check", action="store_true",
                        help="read-only verification of AC-FBH1..AC-FBH6")
    parser.add_argument("--preview", default=None, help="preview directory")
    parser.add_argument("--termini", default=None, help="endpoint closure json")
    parser.add_argument("--report", default=None, help="backhop report json")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.write:
        return write(args.preview, args.termini, args.report)
    if args.check:
        return check(args.preview, args.report)
    build_parser().print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
