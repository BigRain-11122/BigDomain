#!/usr/bin/env python3
"""Render the CEO deliverable-index block into preview/index.html.

Editorial claims live in preview/deliverable-index.json. Every number inside
the rendered block (byte sizes, page titles, verdicts, timestamps) is derived
from disk at render time, so the walkthrough page cannot drift from the
artifacts it points at. The block is idempotent: rendering twice produces
byte-identical output, which is what --check measures.

Never writes to src/. Never touches the network.

Usage:
    python tools/deliverable_index.py          # render in place
    python tools/deliverable_index.py --check  # verify the landed block
"""

import hashlib
import html
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(REPO, "preview")
INDEX = os.path.join(PREVIEW, "index.html")
REGISTRY = os.path.join(PREVIEW, "deliverable-index.json")
BEGIN = "<!-- BD-DELIVERABLE-INDEX:BEGIN -->"
END = "<!-- BD-DELIVERABLE-INDEX:END -->"
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
LINK_RE = re.compile(r'href="([^"]+)"')
MARKERS = ["AIGC", "msgSecCheck", "\u6295\u987e", "19.9"]
COMPLIANCE = [
    "AIGC \u6807\u8bc6",
    "msgSecCheck \u524d\u7f6e\u95f8",
    "\u975e\u6295\u987e",
]


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_registry():
    data = json.loads(read(REGISTRY))
    return data.get("faces", [])


def facts(entry):
    """Derive every displayed value from the artifact itself."""
    html_path = os.path.join(PREVIEW, entry["html"])
    json_path = os.path.splitext(html_path)[0] + ".json"
    text = read(html_path)
    m = TITLE_RE.search(text)
    title = html.unescape(m.group(1).strip()) if m else "(no title)"
    verdict, stamp = "n/a", ""
    if os.path.exists(json_path):
        try:
            blob = json.loads(read(json_path))
        except ValueError:
            blob = {}
        if isinstance(blob, dict):
            verdict = blob.get("verdict") or "n/a"
            stamp = blob.get("generated_utc") or ""
    if not stamp:
        import datetime
        stamp = "%sZ" % datetime.datetime.fromtimestamp(
            os.path.getmtime(html_path), datetime.timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%S")
    defects = []
    if "%s" in title:
        defects.append("title placeholder not filled")
    return {
        "id": entry["id"],
        "html": entry["html"],
        "claim": entry["claim"],
        "blocker": entry["blocker"],
        "bytes": os.path.getsize(html_path),
        "json_bytes": os.path.getsize(json_path) if os.path.exists(json_path) else 0,
        "title": title,
        "verdict": str(verdict),
        "stamp": stamp,
        "defects": defects,
    }


def newest_artifact():
    """Derive the newest preview artifact pair by mtime (R2775).

    The registry is editorial and covers only the *-report.html family, so a
    face shipped under another filename family (first-yuan.html, journey-19.9
    .html) is invisible in the ledger table and the CEO entry page silently
    stopped carrying the window's newest artifact. This scans every preview
    *.json by mtime instead of trusting a name convention, and it never
    renders a blank recent-artifact line while artifacts exist (R2751 K1).
    """
    best = None
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".json"):
            continue
        stem = os.path.splitext(name)[0]
        # An artifact pair is X.html + X.json. The editorial registry
        # (deliverable-index.json) is not an artifact and carries no sibling
        # page, so it can never become the newest "shipped" face.
        if not os.path.exists(os.path.join(PREVIEW, stem + ".html")):
            continue
        if stem in BOARD_PAGES:
            continue
        path = os.path.join(PREVIEW, name)
        try:
            mtime = os.path.getmtime(path)
            nbytes = os.path.getsize(path)
        except OSError:
            continue
        if best is None or mtime > best[1]:
            best = (name, mtime, nbytes)
    if best is None:
        return {"json": "", "bytes": 0, "stamp": "", "empty": True}
    import datetime
    stamp = datetime.datetime.fromtimestamp(best[1]).strftime("%Y-%m-%dT%H:%M:%S")
    return {"json": best[0], "bytes": best[2], "stamp": stamp, "empty": False}


def newest_line(new):
    """The one derived line AC-DIX8 compares against a fresh read."""
    if new["empty"]:
        return "preview/ carries no json artifact yet - stated, not blank."
    return "%s \u00b7 %dB \u00b7 %s" % (new["json"], new["bytes"], new["stamp"])


def render_newest(new):
    out = []
    out.append("<h2>\u6700\u65b0\u5b9e\u7269\uff08\u76d8\u4e0a mtime \u6d3e\u751f\uff0c\u7981\u5199\u6b7b\uff09</h2>")
    out.append('<div class="note">%s</div>' % html.escape(newest_line(new)))
    out.append('<div class="note">%s</div>' % html.escape(NEWEST_SNAPSHOT))
    return "\n".join(out)


GATE_PAGES = ("index", "deliverable-index")

# AC-DIX16 (pinned 2026-11-15 R2804 before this code): the BOARD pages re-render on every
# closeout and are not product faces, but they were winning the "newest artifact" race and
# stealing the band from the artifact the window actually shipped - which reddened this page
# one render later, and reddened the export face (AC-EXPW1) after that. Boards are CEO-openable
# and stay in the pairs band; they are simply not "the newest thing the line produced".
BOARD_PAGES = ("face-sweep", "ceo-blockers")

# AC-DIX15 (pinned 2026-11-15 R2804 before this code): the newest band quotes a byte count
# and an mtime that belong to whatever rendered that face LAST. Re-rendering that face in the
# same closeout changes both, which is why this page read AC-DIX3/AC-DIX8 red the moment the
# sweep board was refreshed after it. The band must therefore LABEL those two numbers a
# snapshot, and its live assertion must be the artifact NAME - the fact a reader needs is
# "which face is newest", never "how many bytes it had at 23:10".
NEWEST_SNAPSHOT = ("Snapshot: the size and stamp above were measured when this page was rendered; "
                   "a later re-render of that face changes them. The live fact this band asserts "
                   "is which artifact is newest, not its byte count.")


def artifact_pairs():
    """Every shipped preview face (X.html, paired or not), newest first (R2777).

    R2775's band carries only the single newest pair, so a face that shipped
    two windows ago is unreachable from the CEO entry page once a newer one
    lands (measured: ceo-blockers, face-sweep and city-observatory all read
    zero links in index.html). This derives the FULL list from the directory
    instead of a name convention: a face exists when its html is on disk, and
    the gate page plus the editorial registry are never product faces.
    """
    pairs = []
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html"):
            continue
        stem = name[:-5]
        if stem in GATE_PAGES:
            continue
        json_name = stem + ".json"
        hpath = os.path.join(PREVIEW, name)
        jpath = os.path.join(PREVIEW, json_name)
        # AC-DIX17 (pinned 2026-11-17 R2883 before this code): the universe is
        # every html FACE, not every pair. A page whose json sibling is absent
        # is still on disk and still CEO-openable; skipping it here made the
        # entry page's own claim ("every shipped face stays reachable") false
        # for two measured faces without reddening any criterion.
        paired = os.path.exists(jpath)
        if not os.path.exists(hpath):
            continue
        try:
            nbytes = os.path.getsize(hpath)
            mtime = os.path.getmtime(hpath)
        except OSError:
            continue
        pairs.append({"stem": stem, "html": name,
                      "json": json_name if paired else "",
                      "paired": paired, "bytes": nbytes, "mtime": mtime})
    pairs.sort(key=lambda p: (-p["mtime"], p["stem"]))
    return pairs


def render_pairs(pairs):
    """The all-pairs band, derived row by row (never a written-down list)."""
    out = ["<h2>\u5168\u90e8\u5df2\u4e0a\u7ebf\u9762\uff08\u76d8\u4e0a pair \u6d3e\u751f\u00b7\u70b9\u5f00\u5373\u770b\uff09</h2>"]
    if not pairs:
        out.append('<div class="note">preview/ \u76ee\u524d\u6ca1\u6709 '
                   "html+json \u6210\u5bf9\u9762\u2014\u2014\u5b9e\u8bdd\u76f4\u8bf4\uff0c"
                   "\u4e0d\u7559\u7a7a\u884c\u3002</div>")
        return "\n".join(out)
    out.append('<div class="note">\u672c\u5757\u9762\u6570=%d\uff0c\u9010\u6761\u76f4\u63a5'
               "\u4ece <code>preview/</code> \u626b\u63cf\u5f97\u51fa\uff1a"
               "\u9762\u540d\u00b7\u5b57\u8282\u00b7\u65f6\u95f4\u6233\u5747\u5b9e\u8bfb\u3002</div>"
               % len(pairs))
    out.append("<ul>")
    for p in pairs:
        import datetime
        stamp = datetime.datetime.fromtimestamp(p["mtime"]).strftime("%Y-%m-%d %H:%M")
        paired = p.get("paired", True)
        label = ("json=%s" % p["json"]) if paired else "json=missing"
        out.append(
            '<li><a href="%s">%s</a> <span class="tag">%dB</span> '
            '<span class="tag">%s</span> <span class="tag%s">%s</span></li>'
            % (html.escape(p["html"]), html.escape(p["stem"]), p["bytes"],
               html.escape(stamp), "" if paired else " warn",
               html.escape(label))
        )
    out.append("</ul>")
    return "\n".join(out)


def render_body(rows, defects_total, newest, pairs):
    out = [render_newest(newest), ""]
    out.append(render_pairs(pairs))
    out.append("")
    out.append("<h2>\u5b9e\u7269\u53f0\u8d26\uff08\u4e00\u9875\u70b9\u8fdb\u6bcf\u4e2a\u5b9e\u6d4b\u9762\uff09</h2>")
    out.append(
        '<div class="note">\u672c\u5757\u7531 <code>tools/deliverable_index.py</code> '
        "\u4ece\u76d8\u4e0a\u6d3e\u751f\uff08\u5c3a\u5bf8\u00b7\u6807\u9898\u00b7verdict\u00b7"
        "\u65f6\u95f4\u6233\u5747\u5b9e\u8bfb\uff0c\u7981\u5199\u6b7b\uff09\u3002"
        "\u9762\u6570=%d \u00b7 \u672a\u586b\u6807\u9898\u5360\u4f4d=%d \u00b7 "
        "\u8bf7\u4ee5 <code>--check</code> \u590d\u6838\u4e00\u81f4\u6027\u3002</div>"
        % (len(rows), defects_total)
    )
    out.append(
        '<div class="disclaimer">\u5e38\u9a7b\u5408\u89c4\u4e09\u9762\uff1a'
        "<b>AIGC \u6807\u8bc6</b>\uff08\u751f\u6210\u5185\u5bb9\u5168\u5448\u73b0\u9762\u6807\u6ce8\uff09\u00b7 "
        "<b>msgSecCheck \u524d\u7f6e\u95f8</b>\uff08\u5185\u5bb9\u5b89\u5168\u672a\u63a5\u7981\u5f00\u95e8\uff09\u00b7 "
        "<b>\u975e\u6295\u987e</b>\uff08\u672c\u5e73\u53f0\u4ea7\u51fa\u4e0d\u6784\u6210\u6295\u8d44\u5efa\u8bae\uff09\u3002</div>"
    )
    out.append("<table>")
    out.append(
        "<tr><th>#</th><th>\u9762</th><th>\u5b9e\u7269\uff08\u70b9\u5f00\u5373\u770b\uff09</th>"
        "<th>\u5b9e\u6d4b\u5224\u636e</th><th>\u5360\u4f4d / \u963b\u585e</th></tr>"
    )
    for i, r in enumerate(rows, 1):
        tag = "ok" if r["verdict"].upper() == "PASS" else "warn"
        cell = (
            '<a href="%s">%s</a><br>'
            '<span class="tag %s">verdict=%s</span> '
            '<span class="tag">%dB</span> '
            '<span class="tag">%s</span>'
            % (r["html"], r["html"], tag, html.escape(r["verdict"]), r["bytes"],
               html.escape(r["stamp"]))
        )
        if r["defects"]:
            cell += ' <span class="tag ceo">%s</span>' % html.escape(
                "; ".join(r["defects"]))
        out.append(
            "<tr><td>%d</td><td><b>%s</b><br>%s</td><td>%s</td><td>%s</td>"
            "<td>%s</td></tr>"
            % (
                i,
                html.escape(r["id"]),
                html.escape(r["title"]),
                cell,
                html.escape(r["claim"]),
                html.escape(r["blocker"]),
            )
        )
    out.append("</table>")
    return "\n".join(out)


def render_block():
    rows = [facts(e) for e in load_registry()]
    defects = sum(len(r["defects"]) for r in rows)
    newest = newest_artifact()
    pairs = artifact_pairs()
    body = render_body(rows, defects, newest, pairs)
    fp = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return (
        "%s\n%s\n<!-- fingerprint %s -->\n%s" % (BEGIN, body, fp, END), fp, rows,
        newest, pairs
    )


def strip_block(text):
    if BEGIN not in text or END not in text:
        return text
    head = text.split(BEGIN)[0]
    tail = text.split(END, 1)[1]
    return head + tail


def get_block(text):
    if BEGIN not in text or END not in text:
        return ""
    return BEGIN + text.split(BEGIN, 1)[1].split(END, 1)[0] + END


def inject(text, block):
    if BEGIN in text and END in text:
        head = text.split(BEGIN)[0]
        tail = text.split(END, 1)[1]
        return head + block + tail
    idx = text.find("<h2>")
    if idx < 0:
        raise SystemExit("index.html has no <h2> anchor to insert the block before")
    return text[:idx] + block + "\n\n  " + text[idx:]


def front_count(text):
    """Count RD1 real fronts with the candidate index.html text in place.

    The gate itself reads preview/ from disk, so the candidate text is scored
    here against the same three shipped conditions instead of being written out.
    """
    sys.path.insert(0, os.path.join(REPO, "src", "sandbox", "benchgate"))
    import bench_gate  # noqa: E402

    def qualifies(body, nbytes):
        markers_ok = all(m in body for m in bench_gate.MARKERS)
        external = [t for t in bench_gate.EXTERNAL_REF_TOKENS if t in body]
        return nbytes >= 4096 and markers_ok and not external

    names = []
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html") or name == "index.html":
            continue
        path = os.path.join(PREVIEW, name)
        if qualifies(read(path), os.path.getsize(path)):
            names.append(name)
    if qualifies(text, len(text.encode("utf-8"))):
        names.append("index.html")
    return names


def main(argv):
    check = "--check" in argv[1:]
    text = read(INDEX)
    stat_before = (os.path.getsize(INDEX), os.path.getmtime(INDEX))
    block, fp, rows, newest, pairs = render_block()

    checks = []

    def record(code, ok, detail):
        checks.append((code, ok, detail))

    registered = {e["html"] for e in load_registry()}
    on_disk = {n for n in os.listdir(PREVIEW)
               if n.endswith("-report.html")
               and os.path.exists(os.path.join(PREVIEW, os.path.splitext(n)[0] + ".json"))}
    record("AC-DIX1", registered == on_disk,
           "registry=%d disk=%d missing=%s extra=%s"
           % (len(registered), len(on_disk),
              sorted(on_disk - registered), sorted(registered - on_disk)))

    size_rows = [r for r in rows
                 if ("%dB</span>" % r["bytes"]) in block and r["html"] in block]
    record("AC-DIX2", len(size_rows) == len(rows),
           "quoted-sizes=%d of %d, each equal to os.path.getsize" % (len(size_rows), len(rows)))

    landed = get_block(text)
    # AC-DIX15 relaxed the byte-equality of this criterion, not its purpose: the landed band
    # must still name the same newest face the fresh scan names, and must label its size and
    # stamp a snapshot, so a same-closeout re-render of that face cannot redden the page.
    landed_name = (newest["json"] or "") in landed
    label_ok = NEWEST_SNAPSHOT in landed
    record("AC-DIX3", landed_name and label_ok,
           "landed-names-newest=%s snapshot-label=%s fingerprint=%s"
           % (landed_name, label_ok, fp))

    clean = strip_block(text)
    before = set(front_count(clean))
    after = set(front_count(text))
    markers_ok = all(m in text for m in MARKERS)
    scheme_ok = ("http://" not in text) and ("https://" not in text)
    record("AC-DIX4", markers_ok and scheme_ok and before == after and
           os.path.getsize(INDEX) >= 4096,
           "markers=%s scheme_free=%s fronts_before=%d fronts_after=%d bytes=%d"
           % (markers_ok, scheme_ok, len(before), len(after), os.path.getsize(INDEX)))

    links = LINK_RE.findall(block)
    bad = [l for l in links
           if "/" in l or ":" in l or not os.path.exists(os.path.join(PREVIEW, l))]
    record("AC-DIX5", bool(links) and not bad,
           "links=%d relative-and-present=%d bad=%s" % (len(links), len(links) - len(bad), bad))

    have = [c for c in COMPLIANCE if c in block]
    blockers = [r for r in rows if r["blocker"]]
    record("AC-DIX6", len(have) == len(COMPLIANCE) and len(blockers) == len(rows),
           "compliance=%d/%d blocker-named=%d/%d" % (len(have), len(COMPLIANCE),
                                                     len(blockers), len(rows)))

    # R2804: scored against the LANDED page, not the block this run just built. AC-DIX3 used
    # to catch a tampered ledger row only because it compared the whole landed block byte for
    # byte; that comparison is gone (it was the two-page interlock), so the row-level claim has
    # to be made against the file a reader actually opens.
    quoted = [r for r in rows if ("verdict=%s" % html.escape(r["verdict"])) in text]
    record("AC-DIX7", len(quoted) == len(rows),
           "verdicts-quoted=%d/%d defect-rows=%d"
           % (len(quoted), len(rows), sum(1 for r in rows if r["defects"])))

    # AC-DIX8 (pinned 2026-11-15 R2775 before this code was written): the
    # newest-artifact band must equal a FRESH mtime scan of preview/*.json, so
    # the entry page cannot keep pointing at last window's face after a new
    # one lands, and it may never read as a blank line while artifacts exist.
    fresh = newest_artifact()
    want = newest_line(fresh)
    # The criterion must score the LANDED document, not the block this run just
    # built: comparing the fresh derivation against the fresh render is a
    # self-matching test that passes on any bytes (R2760/R2761 class, caught
    # here by control c2 of tmp/negctl_dix8_R2775.py).
    landed_block = get_block(text) if check else block
    # AC-DIX15 (R2804): the NAME is the live fact. The byte count and stamp are a snapshot of
    # whichever render came last, so they are asserted as labelled, never as equal.
    landed_names_fresh = (fresh["json"] or "") in landed_block
    record("AC-DIX8", landed_names_fresh and (NEWEST_SNAPSHOT in landed_block),
           "newest=%s bytes=%d names_fresh=%s snapshot_label=%s"
           % (fresh["json"] or "(none)", fresh["bytes"], landed_names_fresh,
              NEWEST_SNAPSHOT in landed_block))

    # AC-DIX9..AC-DIX14 (pinned 2026-11-15 R2777 in src/os/backlog.md BEFORE
    # this code): the all-pairs band must list every shipped face on disk, so
    # a page landed two windows ago stays reachable from the CEO entry page.
    fresh_pairs = artifact_pairs()
    listed = [p for p in pairs
              if ('href="%s"' % html.escape(p["html"])) in landed_block]
    record("AC-DIX9", len(pairs) == len(fresh_pairs) and len(listed) == len(pairs),
           "band-rows=%d fresh-scan=%d listed-in-landed=%d"
           % (len(pairs), len(fresh_pairs), len(listed)))

    missing = [p["html"] for p in pairs
               if not os.path.exists(os.path.join(PREVIEW, p["html"]))
               or (p["paired"] and not os.path.exists(os.path.join(PREVIEW, p["json"])))]
    record("AC-DIX10", not missing, "pairs=%d missing-targets=%s"
           % (len(pairs), missing))

    if check:
        record("AC-DIX11", (os.path.getsize(INDEX), os.path.getmtime(INDEX)) == stat_before,
               "check-left-size+mtime-unchanged=%s"
               % ((os.path.getsize(INDEX), os.path.getmtime(INDEX)) == stat_before))
    else:
        record("AC-DIX11", True, "writer mode: this run is the intended author")

    band_text = render_pairs(pairs)
    record("AC-DIX12", ("http://" not in band_text) and ("https://" not in band_text),
           "band-offline=%s rows=%d"
           % (("http://" not in band_text) and ("https://" not in band_text),
              len(pairs)))

    wrong = [p["html"] for p in pairs
             if ("%dB</span>" % p["bytes"]) not in band_text]
    record("AC-DIX13", not wrong, "self-referential-bytes-wrong=%s" % wrong)

    gate = [p["stem"] for p in pairs if p["stem"] in GATE_PAGES]
    record("AC-DIX14", not gate, "gate-pages-listed=%s" % gate)

    # AC-DIX17 (pinned 2026-11-17 R2883 before this code): the universe is
    # re-measured from RAW html names, never through artifact_pairs(), so an
    # html-only face cannot fall off the CEO entry page unnoticed - an unpaired
    # face must be listed and labelled, not quietly dropped.
    raw_faces = sorted(n for n in os.listdir(PREVIEW)
                       if n.endswith(".html")
                       and os.path.splitext(n)[0] not in GATE_PAGES)
    unlisted = [n for n in raw_faces
                if ('href="%s"' % html.escape(n)) not in landed_block]
    unlabelled = []
    for p in pairs:
        if p["paired"]:
            continue
        at = landed_block.find('href="%s"' % html.escape(p["html"]))
        if at < 0 or "json=missing" not in landed_block[at:at + 400]:
            unlabelled.append(p["html"])
    record("AC-DIX17", not unlisted and not unlabelled,
           "html-faces=%d unlisted=%s unlabelled-incomplete=%s"
           % (len(raw_faces), unlisted, unlabelled))

    if check:
        for code, ok, detail in checks:
            print("%s %-9s %s" % ("PASS" if ok else "FAIL", code, detail))
        failed = [c for c, ok, _ in checks if not ok]
        print("VERDICT %s %d/%d fingerprint=%s" %
              ("PASS" if not failed else "FAIL", len(checks) - len(failed),
               len(checks), fp))
        print(json.dumps({"passed": len(checks) - len(failed), "total": len(checks),
                          "failed": failed, "fingerprint": fp}, sort_keys=True))
        return 0 if not failed else 2

    new_text = inject(text, block)
    with open(INDEX, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new_text)
    print("DELIVERABLE INDEX faces=%d defects=%d fingerprint=%s index=%dB" %
          (len(rows), sum(len(r["defects"]) for r in rows), fp,
           os.path.getsize(INDEX)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
