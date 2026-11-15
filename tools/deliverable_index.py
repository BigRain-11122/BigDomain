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


def render_body(rows, defects_total):
    out = []
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
    body = render_body(rows, defects)
    fp = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return (
        "%s\n%s\n<!-- fingerprint %s -->\n%s" % (BEGIN, body, fp, END), fp, rows
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
    block, fp, rows = render_block()

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
    record("AC-DIX3", landed == block,
           "landed-block==fresh-block %s, fingerprint=%s" % (landed == block, fp))

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

    quoted = [r for r in rows if ("verdict=%s" % html.escape(r["verdict"])) in block]
    record("AC-DIX7", len(quoted) == len(rows),
           "verdicts-quoted=%d/%d defect-rows=%d"
           % (len(quoted), len(rows), sum(1 for r in rows if r["defects"])))

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
