"""Render preview/start-here.html - the one page a first visitor opens to see what
this machine can actually be operated for today.

Every number on the page is derived from preview/*.html on the same run; the
--check arm re-scans the disk and re-reads the page, so a stale page or a hand
edit reddens instead of passing. Chinese strings live in
state/start-here-faces.json and state/merchant-onboard-items.json; this source
stays ASCII (encoding law).
"""

import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(ROOT, "preview")
DATA = os.path.join(ROOT, "state", "start-here-faces.json")
OUT_HTML = os.path.join(PREVIEW, "start-here.html")
OUT_JSON = os.path.join(PREVIEW, "start-here.json")

EXCLUDE = {"index.html", "start-here.html"}
OPS = ("input", "button", "select", "textarea")
EXT = re.compile(r'(?:src|href)\s*=\s*["\']https?://', re.I)
HREF = re.compile(r'<a\s[^>]*href="([^"]+)"')


def sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def scan_faces():
    """Per preview face: how many controls it carries and whether it leaves the machine."""
    rows = {}
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html"):
            continue
        with open(os.path.join(PREVIEW, name), "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8", "replace")
        counts = {key: len(re.findall(r"<%s\b" % key, text, re.I)) for key in OPS}
        rows[name] = {
            "bytes": len(raw),
            "counts": counts,
            "ops": sum(counts.values()),
            "external": len(EXT.findall(text)),
        }
    return rows


def operable_set(rows):
    return [name for name, row in rows.items() if row["ops"] > 0 and name not in EXCLUDE]


def missing_ceo_items():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import merchant_onboard as mo

    return [row for row in mo.project_items() if row.get("owner") == "ceo" and not row.get("proven")]


def projection():
    rows = scan_faces()
    doc = load_json(DATA)
    operable = operable_set(rows)
    gaps = []
    for name in operable:
        entry = (doc.get("faces") or {}).get(name) or {}
        for key in ("label", "can", "cannot"):
            if not (entry.get(key) or "").strip():
                gaps.append("%s missing %s" % (name, key))
    return {
        "rows": rows,
        "doc": doc,
        "operable": operable,
        "faces_total": len([name for name in rows if name != "start-here.html"]),
        "gaps": gaps,
        "missing": missing_ceo_items(),
        "data16": sha16(DATA),
    }


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def render(proj):
    doc = proj["doc"]
    faces = doc.get("faces") or {}
    sub = doc["sub_fmt"].format(faces=proj["faces_total"], operable=len(proj["operable"]))
    cards = []
    for name in proj["operable"]:
        entry = faces.get(name) or {}
        if not entry:
            # A missing entry is graded by AC-SH3; render a named shell so the check
            # reports a missing row instead of crashing on it.
            entry = {"label": name, "can": "", "cannot": ""}
        label = entry.get("label") or ""
        can = entry.get("can") or ""
        cannot = entry.get("cannot") or ""
        cards.append(
            '  <article class="face" data-face="%s">\n'
            '    <h3><a href="%s">%s</a> <code>%s</code></h3>\n'
            '    <p><b>%s</b>%s</p>\n'
            '    <p class="limit"><b>%s</b>%s</p>\n'
            '    <p><a class="go" href="%s">%s &rarr;</a></p>\n'
            '  </article>\n' % (
                esc(name), esc(name), esc(label), esc(name),
                esc(doc["can_tag"]), esc(can),
                esc(doc["cannot_tag"]), esc(cannot),
                esc(name), esc(doc["open_link"]),
            )
        )
    if proj["missing"]:
        items = "\n".join(
            '    <li data-ceo-item="%s"><b>%s</b> &mdash; %s</li>'
            % (esc(row["id"]), esc(row["label"]), esc(row["how"]))
            for row in proj["missing"]
        )
        missing_block = ('  <p>%s</p>\n  <ul>\n%s\n  </ul>\n  <p>%s</p>'
                         % (esc(doc["missing_head_fmt"].format(n=len(proj["missing"]))),
                            items, esc(doc["missing_tail"])))
    else:
        missing_block = "  <p>%s</p>" % esc(doc["missing_absent"])
    notices = "\n".join(
        '  <p data-notice="%s">%s</p>' % (key, esc(doc["notices"][key]))
        for key in ("aigc", "advice", "mock")
    )
    return (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>%s</title>\n<style>\n"
        ":root{--ink:#182033;--muted:#6b7280;--line:#e5e7eb;--accent:#3b5bdb;--warn:#e8590c;}\n"
        "*{box-sizing:border-box;margin:0;padding:0}\n"
        'body{font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;color:var(--ink);'
        "background:#f7f8fa;line-height:1.65;padding:0 0 48px}\n"
        ".wrap{max-width:900px;margin:0 auto;padding:0 20px}\n"
        "header{background:linear-gradient(135deg,#1f2b4d,#3b5bdb);color:#fff;padding:34px 0 26px}\n"
        "header h1{font-size:26px;letter-spacing:1px}\n"
        "header .sub{margin-top:8px;font-size:14px;opacity:.94}\n"
        ".counts{margin-top:16px;display:flex;gap:10px;flex-wrap:wrap}\n"
        ".count{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.5);"
        "border-radius:8px;padding:8px 14px;font-size:13px}\n"
        ".count b{font-size:20px;margin-right:6px}\n"
        "h2{font-size:18px;margin:32px 0 12px;padding-left:10px;border-left:4px solid var(--accent)}\n"
        ".face{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 16px;"
        "margin-bottom:12px}\n"
        ".face h3{font-size:16px;margin-bottom:4px}\n"
        ".face h3 code{font-size:12px;color:var(--muted);font-weight:400;margin-left:6px}\n"
        ".face .tagline{font-size:12px;color:var(--accent);margin-bottom:6px}\n"
        ".face .limit{color:var(--warn);font-size:13px}\n"
        ".face p{font-size:13px;margin:4px 0}\n"
        ".face b{font-size:12px;color:var(--muted);display:block}\n"
        ".go{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;"
        "border-radius:6px;padding:4px 12px;font-size:13px}\n"
        "a{color:var(--accent)}\n"
        ".missing{background:#fde8ef;border:1px solid #f4b8cc;border-radius:8px;padding:14px 16px}\n"
        ".missing ul{padding-left:20px;margin:8px 0}\n"
        ".missing li{font-size:13px;margin:4px 0}\n"
        ".notices{background:#fffbe6;border:1px solid #ffe58f;border-radius:8px;padding:12px 16px;"
        "font-size:13px}\n"
        ".notices p{margin:4px 0}\n"
        "footer{margin-top:32px;font-size:12px;color:var(--muted);border-top:1px solid var(--line);"
        "padding-top:12px}\n"
        "code{background:#eef1f6;border-radius:3px;padding:1px 5px;font-size:12px}\n"
        "</style>\n</head>\n<body>\n"
        "<header><div class=\"wrap\">\n"
        "  <h1>%s</h1>\n"
        "  <div class=\"sub\">%s</div>\n"
        "  <div class=\"counts\">"
        "<span class=\"count\"><b data-count=\"faces\">%d</b>%s</span>"
        "<span class=\"count\"><b data-count=\"operable\">%d</b>%s</span>"
        "</div>\n"
        "</div></header>\n<div class=\"wrap\">\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=\"missing\">\n%s\n</div>\n"
        "<h2>%s</h2>\n<div class=\"notices\">\n%s\n</div>\n"
        "<footer>%s</footer>\n"
        "</div>\n</body>\n</html>\n"
    ) % (
        esc(doc["title"]),
        esc(doc["h1"]), esc(sub),
        proj["faces_total"], esc(doc.get("count_faces", "")),
        len(proj["operable"]), esc(doc.get("count_operable", "")),
        esc(doc["h2_can"].format(operable=len(proj["operable"]))), "\n".join(cards),
        esc(doc["h2_cannot"]), missing_block,
        esc(doc["h2_rule"]), notices,
        "sources: state/start-here-faces.json %s / state/merchant-onboard-items.json via "
        "tools/merchant_onboard.project_items()" % proj["data16"],
    )


def write():
    proj = projection()
    html = render(proj)
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    snapshot = {
        "face": "start-here",
        "generated_from": {
            "state/start-here-faces.json": proj["data16"],
        },
        "faces_total": proj["faces_total"],
        "operable": proj["operable"],
        "missing_ceo_items": [row["id"] for row in proj["missing"]],
        "sizes": {"html_bytes": len(html.encode("utf-8"))},
    }
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(snapshot, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("WROTE %s html=%dB operable=%d faces=%d missing=%d"
          % (os.path.relpath(OUT_HTML, ROOT), len(html.encode("utf-8")),
             len(proj["operable"]), proj["faces_total"], len(proj["missing"])))
    return 0


def check():
    proj = projection()
    failures = []
    if not os.path.exists(OUT_HTML):
        print("VERDICT FAIL reason=page_missing")
        return 2
    with open(OUT_HTML, encoding="utf-8") as fh:
        text = fh.read()

    # AC-SH1: the two counters on the page equal a fresh scan of preview/
    for key, want in (("faces", proj["faces_total"]), ("operable", len(proj["operable"]))):
        got = re.search(r'data-count="%s">(\d+)<' % key, text)
        if not got or int(got.group(1)) != want:
            failures.append("SH1 count:%s page=%s fresh=%d"
                            % (key, got.group(1) if got else "absent", want))

    # AC-SH2: listed faces == fresh operable set, every link resolves, zero external refs
    listed = set(re.findall(r'data-face="([^"]+)"', text))
    if listed != set(proj["operable"]):
        failures.append("SH2 listed=%s fresh=%s" % (sorted(listed), sorted(proj["operable"])))
    for href in HREF.findall(text):
        if not os.path.exists(os.path.join(PREVIEW, href)):
            failures.append("SH2 dead_link=%s" % href)
    if EXT.search(text):
        failures.append("SH2 external_ref_present")

    # AC-SH3: every operable face still has label/can/cannot in the data file
    for gap in proj["gaps"]:
        failures.append("SH3 " + gap)

    # AC-SH4: the blocked list carries every missing CEO item, by id
    want_ids = {row["id"] for row in proj["missing"]}
    got_ids = set(re.findall(r'data-ceo-item="([^"]+)"', text))
    if want_ids != got_ids:
        failures.append("SH4 ceo_items page=%s fresh=%s" % (sorted(got_ids), sorted(want_ids)))

    # AC-SH5: the three standing notices are verbatim on the page
    for key in ("aigc", "advice", "mock"):
        if esc(proj["doc"]["notices"][key]) not in text:
            failures.append("SH5 notice_missing=%s" % key)

    # AC-SH6: the page must be the current render of the current data (no self-proof)
    if text != render(proj):
        failures.append("SH6 page_out_of_date")

    if failures:
        for line in failures:
            print("  FAIL " + line)
        print("VERDICT FAIL criteria=6 failures=%d" % len(failures))
        return 2
    print("VERDICT PASS criteria=6 faces=%d operable=%d missing_ceo=%d external_refs=0"
          % (proj["faces_total"], len(proj["operable"]), len(proj["missing"])))
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--write"]:
        return write()
    if argv[:1] == ["--check"]:
        return check()
    print(__doc__.strip().splitlines()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
