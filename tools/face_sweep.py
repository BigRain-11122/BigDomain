"""Face sweep: execute every CEO-facing page's own --check gate right now and render
the result as ONE openable page.

Why this exists: preview/index.html lists the eight faces and quotes the verdict each
artifact DECLARED when it was written, but nothing re-executes those gates. This driver
runs each shipped tool's read-only --check as a subprocess, records its exit code, its
VERDICT line and the landed artifact bytes, and renders a single board.

Laws honoured:
- criteria are pre-registered in --check (AC-FSW1..AC-FSW9, see check()).
- nothing is hardcoded: verdicts, sizes and timestamps are measured from the subprocess
  and from disk.
- the board never counts a face as passing unless its own gate exited zero AND printed a
  PASS verdict line.
- read-only toward every artifact: this tool only writes its own two outputs.

Usage:
    python tools/face_sweep.py                # run the sweep and render the board
    python tools/face_sweep.py --check        # verify the landed board, no sweep
    python tools/face_sweep.py --faces-json P # sweep an alternate face spec (controls)
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_HTML = os.path.join(ROOT, "preview", "face-sweep.html")
OUT_JSON = os.path.join(ROOT, "preview", "face-sweep.json")

SCHEMA = "face-sweep-v1"

# id, label, driver, html, json.  The driver is invoked as: python <driver> --check
# R2903: the row order is a READING order, not a shelf order. The money proof leads because
# it is the only row whose failure is a revenue fact rather than housekeeping; AC-FSW13
# grades the declared order against the landed rows so a later append cannot bury it again.
FACES = [
    ("first-yuan-chain", "first-yuan chain / one purchase, three modules",
     "tools/first_yuan_chain.py",
     "preview/first-yuan-chain.html", "preview/first-yuan-chain.json"),
    ("six-gate-live", "\u516d\u95e8\u5b9e\u51b5 / six gates live",
     "tools/platform_live_report.py",
     "preview/platform-live-report.html", "preview/platform-live-report.json"),
    ("lobby-ws", "\u5927\u5385 WebSocket / P-47 \u7b2c 1 \u9879",
     "tools/lobby_ws_report.py",
     "preview/lobby-ws-report.html", "preview/lobby-ws-report.json"),
    ("city-face", "\u57ce\u5e02\u89c2\u6d4b\u9762 / P-47 \u7b2c 1 \u9879",
     "tools/city_face_report.py",
     "preview/city-face-report.html", "preview/city-face-report.json"),
    ("ugc-gate", "UGC \u5b89\u5168\u9762 / P-47 \u7b2c 3 \u9879",
     "tools/ugc_gate_report.py",
     "preview/ugc-gate-report.html", "preview/ugc-gate-report.json"),
    ("payment-gate", "19.9 \u652f\u4ed8\u9762 / P-47 \u7b2c 4 \u9879",
     "tools/payment_gate_report.py",
     "preview/payment-gate-report.html", "preview/payment-gate-report.json"),
    ("membership", "\u6743\u76ca\u6708\u5361\u9762 / P-47 \u7b2c 5 \u9879",
     "tools/membership_benefit_report.py",
     "preview/membership-benefit-report.html", "preview/membership-benefit-report.json"),
    ("ledger-business", "\u4ee3\u5e01\u8d26\u672c\u9762 / P-47 \u7b2c 2 \u9879",
     "tools/ledger_business_report.py",
     "preview/ledger-business-report.html", "preview/ledger-business-report.json"),
    ("entry-index", "\u5165\u53e3\u9875\u5b9e\u7269\u53f0\u8d26 / index",
     "tools/deliverable_index.py",
     "preview/index.html", "preview/deliverable-index.json"),
]

# Deliberately excluded, and named instead of silently dropped: the API-market face
# (preview/apimarket-report.html) is rendered by src/sandbox/ledger/apimarket_report.py,
# which has NO read-only --check, so a sweep row for it could only quote a declaration.
EXCLUDED_NOTE = ("API \u5e02\u573a\u9762\u4e0d\u5728\u672c\u677f\u5b9e\u6d4b\u9762\u5185\uff1a"
                 "src/sandbox/ledger/apimarket_report.py \u65e0\u53ea\u8bfb --check\uff0c"
                 "\u5f3a\u884c\u5165\u677f\u53ea\u80fd\u5f15\u7528\u58f0\u660e\u3002")

# R2903: what a FAIL of each row costs. A board of green ticks answers "is it green" and
# leaves "does a red row cost money or is it housekeeping" to the reader's guess, which is
# the question a CEO actually opens this page to answer. One line per row, stated beside
# the verdict, is DATA derived from nothing - AC-FSW12 refuses a blank entry rather than
# letting an empty cell read as "no consequence".
MEANING = {
    "first-yuan-chain": "\u4e00\u7b14\u4ed8\u6b3e\u8de8\u4e0d\u8fc7\u652f\u4ed8\u3001\u4f1a\u5458\u3001\u8d26\u672c\u4e09\u6bb5\uff0c\u6536\u5165\u4e3a\u96f6\u3002",
    "payment-gate": "19.9 \u5b9a\u4ef7\u9762\u4e0e\u5546\u6237\u53f7\u63a5\u7ebf\u4e0d\u53ef\u7528\uff0c\u6536\u4e0d\u5230\u7b2c\u4e00\u7b14\u94b1\u3002",
    "membership": "\u6708\u5361\u6743\u76ca\u4e0d\u53ef\u5151\u73b0\uff0c\u590d\u8d2d\u4e3a\u96f6\u3002",
    "ledger-business": "\u4ee3\u5e01\u4e24\u5f0f\u8d26\u672c\u5bf9\u4e0d\u4e0a\uff0c\u6536\u5165\u4e0d\u53ef\u5ba1\u8ba1\u3002",
    "ugc-gate": "UGC \u5b89\u5168\u95f8\u672a\u63a5\u901a\uff0c\u5f00\u95e8\u5373\u4e0b\u67b6\uff0c\u6536\u5165\u5f52\u96f6\u3002",
    "lobby-ws": "\u5927\u5385\u8fde\u4e0d\u4e0a\uff0c\u7528\u6237\u8fdb\u4e0d\u6765\uff0c\u4efb\u4f55\u6536\u5165\u90fd\u65e0\u4ece\u53d1\u751f\u3002",
    "city-face": "\u57ce\u5e02\u89c2\u6d4b\u9762\u8bfb\u4e0d\u51fa\u771f\u5b9e\u72b6\u6001\uff0c\u8fd0\u8425\u5224\u65ad\u5931\u53bb\u4f9d\u636e\u3002",
    "six-gate-live": "\u516d\u95e8\u5b9e\u51b5\u4e0d\u53ef\u4fe1\u65f6\uff0c\u4e0a\u6e38\u6570\u636e\u5df2\u504f\u79bb\uff0c\u6240\u6709\u9762\u8bfb\u6570\u90fd\u8981\u91cd\u770b\u3002",
    "entry-index": "\u4ea4\u4ed8\u76ee\u5f55\u4e0e\u76d8\u4e0a\u4e0d\u4e00\u81f4\uff0c\u8bfb\u8005\u627e\u4e0d\u5230\u5b9e\u7269\u3002",
}
MONEY_ID = "first-yuan-chain"
# A row this table has not declared is published as UNDECLARED rather than blanked or
# given an invented consequence: a blank cell reads as "no consequence", and a made-up
# sentence is a claim nobody measured. AC-FSW12 still refuses the undeclared marker on any
# row the LIVE table owns, so the fallback cannot become a quiet bypass.
UNDECLARED = "\u672c\u884c\u672a\u58f0\u660e\u5bf9\u6536\u5165\u7684\u5f71\u54cd\u3002"
ORDER_LINE = "\u9605\u8bfb\u987a\u5e8f\uff1a\u4ece\u4e0a\u5230\u4e0b\u3002\u7b2c\u4e00\u884c\u662f\u94b1\u7684\u8bc1\u636e\u3002"
COL_MEANING = "\u8fd9\u4e00\u884c FAIL \u5bf9\u6536\u5165\u610f\u5473\u7740\u4ec0\u4e48"

# One declaration of what this gate claims to enforce; the printed total is len(CRITERIA),
# never a typed number. R2901 deleted a hand-moved count literal for the same reason: a
# count that lives in two places drifts, and a drift the gate prints is a gate lying about
# its own coverage.
CRITERIA = ["AC-FSW0", "AC-FSW1", "AC-FSW2", "AC-FSW3", "AC-FSW3b", "AC-FSW4",
            "AC-FSW5", "AC-FSW6", "AC-FSW7", "AC-FSW8", "AC-FSW9", "AC-FSW10",
            "AC-FSW11", "AC-FSW12", "AC-FSW13"]

# AC-FSW9: the per-face byte counts are a snapshot of the sweep that wrote them, never a
# live equality claim. Any face re-rendered afterwards changes its own bytes, so asserting
# equality here would redden this board forever and say nothing about the face. The live
# assertion on this board is each face's own gate, re-executed by every sweep.
SNAPSHOT_NOTE = ("The artifact bytes above are a snapshot taken when this sweep ran: a later "
                 "re-render of any face changes them, so the live assertion on this board is "
                 "each face's re-executed gate, not these numbers.")

VERDICT_WORD_RE = re.compile(r"\b(PASS|FAIL)\b")
EXTERNAL_RE = re.compile(r"https?://[A-Za-z0-9_.\-]+")
STANDING = [
    "\u975e\u6295\u8d44\u5efa\u8bae\uff1a\u672c\u9875\u4e0d\u6784\u6210\u4efb\u4f55\u6295\u8d44\u5efa\u8bae\uff0c\u4e0d\u63d0\u4f9b\u6295\u8d44\u54a8\u8be2\u670d\u52a1\u3002",
    "AIGC \u751f\u6210\u6807\u8bc6\uff1a\u4e00\u5207\u751f\u6210\u5185\u5bb9\u5728\u5448\u73b0\u9762\u5e26\u6807\u8bc6\uff0c\u672a\u6807\u8bc6\u4e0d\u5bf9\u5916\u3002",
    "msgSecCheck \u524d\u7f6e\u95f8\uff1a\u5185\u5bb9\u5b89\u5168\u672a\u63a5\u901a\u524d\u4e0d\u5f00\u95e8\u3002",
]


def _rel(p):
    return p.replace(os.sep, "/")


def _read_args(argv):
    opts = {"check": False, "faces_json": None, "timeout": 120}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--check":
            opts["check"] = True
        elif a == "--faces-json":
            i += 1
            opts["faces_json"] = argv[i]
        elif a == "--timeout":
            i += 1
            opts["timeout"] = int(argv[i])
        else:
            raise SystemExit("unknown argument: %s" % a)
        i += 1
    return opts


FACE_KEYS = ("id", "label", "driver", "html", "json", "meaning")


def load_faces(path):
    if not path:
        return [dict(zip(FACE_KEYS, row)) for row in FACES]
    with open(path, "r", encoding="utf-8") as fh:
        rows = json.load(fh)
    out = []
    for r in rows:
        d = {k: r[k] for k in FACE_KEYS[:5]}
        # R2903: the consequence sentence travels with the row. A fixture may declare it
        # inline; a row that declares none inherits the shipped table, and only a row in
        # neither place falls back to the marker check() refuses.
        d["meaning"] = r.get("meaning") or MEANING.get(r["id"], "")
        out.append(d)
    return out


def _stat(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    st = os.stat(p)
    return (st.st_size, st.st_mtime_ns)


def run_face(face, timeout):
    driver = os.path.join(ROOT, face["driver"])
    row = {
        "id": face["id"],
        "label": face["label"],
        "driver": face["driver"],
        "html": face["html"],
        "json": face["json"],
        "meaning": face.get("meaning") or MEANING.get(face["id"], UNDECLARED),
    }
    if not os.path.exists(driver):
        row.update({"exit": 127, "verdict": "MISSING-DRIVER", "duration_s": 0.0,
                    "html_bytes": None, "json_bytes": None, "tail": "",
                    "mutated": False, "mutated_files": []})
        return row
    before = {"html": _stat(face["html"]), "json": _stat(face["json"])}
    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, driver, "--check"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        text = proc.stdout.decode("utf-8", "replace")
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        text, rc = "", 124
    dur = round(time.time() - t0, 2)
    # The gates do not share one summary dialect: most print a VERDICT line, one prints
    # "<NAME> CHECK PASS fails=N", and the chain driver prints "VERDICT PASS legs=2 ...".
    # So the verdict is the LAST line carrying a PASS
    # or FAIL word, read from the output rather than assumed from a fixed prefix.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    verdict = ""
    for ln in reversed(lines):
        if VERDICT_WORD_RE.search(ln):
            verdict = ln[:200]
            break
    if rc == 124:
        verdict = "TIMEOUT"
    elif not verdict:
        verdict = "NO-VERDICT-LINE" if rc == 0 else "EXIT-%d-NO-VERDICT" % rc
    after = {"html": _stat(face["html"]), "json": _stat(face["json"])}
    mutated_files = [k for k in ("html", "json") if before[k] != after[k]]
    row.update({
        "exit": rc,
        "verdict": verdict,
        "duration_s": dur,
        "html_bytes": _size(face["html"]),
        "json_bytes": _size(face["json"]),
        "tail": lines[-1][:240] if lines else "",
        "mutated": bool(mutated_files),
        "mutated_files": mutated_files,
    })
    return row


def _size(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    return os.path.getsize(p)


def _passing(row):
    v = str(row.get("verdict") or "")
    return (row.get("exit") == 0 and "PASS" in v and "FAIL" not in v
            and not row.get("mutated"))


def fingerprint(rows):
    payload = "|".join(
        "%s:%s:%s:%s:%s:%s" % (r["id"], r["exit"], r["verdict"], r["html_bytes"],
                               r["json_bytes"], r.get("mutated"))
        for r in rows
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_json(rows, sizes, stamp, swept_ns):
    doc = {
        "schema_version": SCHEMA,
        "generated_utc": stamp,
        # AC-FSW10 (R2819): the epoch stamp of the sweep that measured these rows. Every
        # face artifact must be OLDER than this; an artifact written after the sweep is a
        # face whose gate result nobody has re-run, which is exactly how this board sat at
        # 8/8 for fifteen rounds while the entry page and the membership page were
        # re-rendered underneath it. Stored as integer ns so the comparison is the same
        # quantity os.stat reports and no string parsing can blur it.
        "swept_ns": int(swept_ns),
        "sizes": {"html": sizes["html"], "json": sizes["json"]},
        "headline": {
            "pass": sum(1 for r in rows if _passing(r)),
            "total": len(rows),
            "verdict": "PASS" if all(_passing(r) for r in rows) else "FAIL",
        },
        "fingerprint": fingerprint(rows),
        "reading_order": [r["id"] for r in rows],
        "faces": rows,
        "notes": [
            "Every row is a subprocess execution of that face's own read-only --check.",
            "A row counts as passing only when the gate exited zero AND printed PASS.",
            "Artifact byte counts are read from disk at sweep time.",
            EXCLUDED_NOTE,
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


CSS = """
body{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;margin:0;background:#12151a;color:#e8ebf0}
.wrap{max-width:1020px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:22px;margin:0 0 6px}
.sub{color:#98a2b3;font-size:13px;margin-bottom:22px}
.big{font-size:44px;font-weight:700;letter-spacing:1px}
.ok{color:#37d67a}.bad{color:#ff5c5c}
table{width:100%;border-collapse:collapse;margin-top:18px;font-size:13px}
th,td{padding:9px 8px;border-bottom:1px solid #262c36;text-align:left;vertical-align:top}
th{color:#98a2b3;font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums}
a{color:#7cc4ff;text-decoration:none}
.tag{display:inline-block;padding:2px 7px;border-radius:4px;font-size:12px}
.tag.ok{background:#12351f;color:#37d67a}.tag.bad{background:#3a1416;color:#ff5c5c}
.note{margin-top:26px;padding:14px 16px;background:#171c23;border-left:3px solid #2f3742;font-size:12.5px;line-height:1.7;color:#b6bfcc}
code{background:#1d232b;padding:1px 5px;border-radius:3px}
"""


def build_html(rows, sizes, stamp):
    passing = sum(1 for r in rows if _passing(r))
    total = len(rows)
    allpass = passing == total
    cls = "ok" if allpass else "bad"
    body = []
    body.append('<div class="wrap">')
    body.append("<h1>%d \u9762\u5b9e\u51b5\u677f / face sweep board</h1>" % total)
    body.append('<div class="sub">%s \u2014 \u4e00\u6761\u547d\u4ee4\u628a\u6bcf\u9762\u9875\u81ea\u5df1\u7684\u95f8\u5b9e\u8dd1\u4e00\u904d\uff0c'
                '\u7ed3\u679c\u6c47\u5230\u8fd9\u4e00\u9875\u3002' % stamp)
    body.append("</div>")
    body.append('<div class="sub">%s (%s)</div>'
                % (_esc(ORDER_LINE), _esc(rows[0]["id"] if rows else "-")))
    body.append('<div class="big %s">%d / %d</div>' % (cls, passing, total))
    body.append('<div class="sub">VERDICT <span class="tag %s">%s</span> \u00b7 fingerprint <code>%s</code>'
                ' \u00b7 \u672c\u9875 %d \u5b57\u8282 \u00b7 json %d \u5b57\u8282</div>'
                % (cls, "PASS" if allpass else "FAIL", fingerprint(rows), sizes["html"], sizes["json"]))
    body.append("<table><thead><tr><th>\u9762</th><th>\u95f8\u7ed3\u679c</th><th>\u9000\u51fa\u7801</th>"
                "<th>\u8017\u65f6</th><th>\u4ea7\u7269\u5b57\u8282</th><th>%s</th>"
                "</tr></thead><tbody>" % _esc(COL_MEANING))
    for r in rows:
        ok = _passing(r)
        tag = "ok" if ok else "bad"
        hb = "-" if r["html_bytes"] is None else format(r["html_bytes"], ",")
        jb = "-" if r["json_bytes"] is None else format(r["json_bytes"], ",")
        body.append(
            '<tr><td><a href="%s">%s</a><br><span style="color:#7b8595;font-size:12px">%s</span>%s</td>'
            '<td><span class="tag %s">%s</span></td><td class="n">%d</td><td class="n">%.2fs</td>'
            '<td class="n">%s / %s</td><td>%s</td></tr>'
            % (r["html"], r["label"], r["driver"],
               (' <span class="tag bad">MUTATED %s</span>' % ",".join(r.get("mutated_files") or []))
               if r.get("mutated") else "",
               tag, _esc(r["verdict"]), r["exit"],
               r["duration_s"], hb, jb, _esc(r.get("meaning") or UNDECLARED))
        )
    body.append("</tbody></table>")
    body.append('<div class="note">')
    body.append('<div><code>python tools/face_sweep.py</code> \u91cd\u6d4b\u5168\u90e8 %d \u9762\uff1b'
                '<code>python tools/face_sweep.py --check</code> \u53ea\u6838\u5bf9\u672c\u9875\u81ea\u8eab'
                '\u4e0e\u76d8\u4e0a\u4e00\u81f4\u3002</div>' % total)
    for line in STANDING:
        body.append("<div>%s</div>" % _esc(line))
    body.append("<div>%s</div>" % _esc(EXCLUDED_NOTE))
    body.append("<div>%s</div>" % _esc(SNAPSHOT_NOTE))
    body.append("</div>")
    body.append("</div>")
    title = "%d \u9762\u5b9e\u51b5\u677f / face sweep board" % total
    return ("<!doctype html>\n<html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
            "<title>%s</title>"
            "<style>%s</style></head><body>\n%s\n</body></html>\n"
            % (title, CSS, "\n".join(body)))


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render(rows, stamp, swept_ns):
    sizes = {"html": 0, "json": 0}
    html_text = json_text = None
    for _ in range(8):
        html_text = build_html(rows, sizes, stamp)
        json_text = build_json(rows, sizes, stamp, swept_ns)
        fresh = {"html": len(html_text.encode("utf-8")), "json": len(json_text.encode("utf-8"))}
        if fresh == sizes:
            break
        sizes = fresh
    if {"html": len(html_text.encode("utf-8")), "json": len(json_text.encode("utf-8"))} != sizes:
        raise SystemExit("E_SIZE_FIXPOINT: sizes did not converge")
    return html_text, json_text, sizes


def sweep(opts):
    faces = load_faces(opts["faces_json"])
    # Taken BEFORE a single gate runs: any artifact touched from here on is newer than the
    # result this board is about to publish, so it must be reported stale rather than counted.
    swept_ns = time.time_ns()
    rows = [run_face(f, opts["timeout"]) for f in faces]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    html_text, json_text, sizes = render(rows, stamp, swept_ns)
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html_text)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json_text)
    dh, dj = os.path.getsize(OUT_HTML), os.path.getsize(OUT_JSON)
    if (dh, dj) != (sizes["html"], sizes["json"]):
        raise SystemExit("E_SIZE_DISK: landed bytes %d/%d != stated %d/%d"
                         % (dh, dj, sizes["html"], sizes["json"]))
    passing = sum(1 for r in rows if _passing(r))
    for r in rows:
        print("face %-16s exit=%-3d verdict=%s (%.2fs)" % (r["id"], r["exit"], r["verdict"], r["duration_s"]))
    print("landed %s %dB / %s %dB" % (_rel(OUT_HTML), dh, _rel(OUT_JSON), dj))
    print("VERDICT %s %d/%d fingerprint=%s"
          % ("PASS" if passing == len(rows) else "FAIL", passing, len(rows), fingerprint(rows)))
    return 0 if passing == len(rows) else 2


def check():
    fails = []
    if not os.path.exists(OUT_JSON) or not os.path.exists(OUT_HTML):
        print("FAIL AC-FSW0: landed board missing")
        return 2
    with open(OUT_JSON, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    with open(OUT_HTML, "r", encoding="utf-8") as fh:
        html_text = fh.read()
    dh, dj = os.path.getsize(OUT_HTML), os.path.getsize(OUT_JSON)

    # AC-FSW1 the document states its own landed byte counts
    if doc.get("sizes") != {"html": dh, "json": dj}:
        fails.append("AC-FSW1 sizes %r != disk %r" % (doc.get("sizes"), {"html": dh, "json": dj}))

    # AC-FSW2 one row per registered face, ids unique
    rows = doc.get("faces") or []
    ids = [r.get("id") for r in rows]
    if len(rows) != len(FACES) or len(set(ids)) != len(ids) or not all(ids):
        fails.append("AC-FSW2 rows=%d unique=%d" % (len(rows), len(set(ids))))

    # AC-FSW3 the headline is derived, never asserted
    passing = sum(1 for r in rows if _passing(r))
    hl = doc.get("headline") or {}
    if hl.get("pass") != passing or hl.get("total") != len(rows):
        fails.append("AC-FSW3 headline %r vs derived %d/%d" % (hl, passing, len(rows)))
    if hl.get("verdict") != ("PASS" if passing == len(rows) else "FAIL"):
        fails.append("AC-FSW3b headline verdict %r inconsistent" % (hl.get("verdict"),))

    # AC-FSW4 every artifact path exists and carries a non-negative integer byte receipt.
    # AC-FSW9 (added R2804) split the old live-equality claim out of this criterion: a face
    # re-rendered after this sweep legitimately changes its own bytes, and this board must
    # not redden for that. Existence is still live; the receipt is a receipt.
    for r in rows:
        for key in ("html", "json"):
            p = os.path.join(ROOT, r.get(key) or "")
            stated = r.get(key + "_bytes")
            if not os.path.exists(p):
                fails.append("AC-FSW4 %s %s missing" % (r.get("id"), r.get(key)))
            elif not isinstance(stated, int) or isinstance(stated, bool) or stated < 0:
                fails.append("AC-FSW4 %s %s receipt=%r" % (r.get("id"), key, stated))

    # AC-FSW9 the snapshot label is present, so no reader mistakes the bytes for live truth
    if SNAPSHOT_NOTE not in html_text:
        fails.append("AC-FSW9 snapshot label absent")

    # AC-FSW5 the fingerprint is recomputed from the landed rows
    if doc.get("fingerprint") != fingerprint(rows):
        fails.append("AC-FSW5 fingerprint %r != %r" % (doc.get("fingerprint"), fingerprint(rows)))

    # AC-FSW6 no external literal: every link is a relative path
    ext = [m for m in EXTERNAL_RE.findall(html_text)]
    if ext:
        fails.append("AC-FSW6 external literals %r" % (ext[:3],))

    # AC-FSW7 the page renders every row and quotes its verdict token
    for r in rows:
        if r["html"] not in html_text:
            fails.append("AC-FSW7 row %s link absent" % r.get("id"))
        if _esc(r["verdict"]) not in html_text:
            fails.append("AC-FSW7 row %s verdict not quoted" % r.get("id"))

    # AC-FSW8 the three standing compliance faces are resident
    for line in STANDING:
        if _esc(line) not in html_text:
            fails.append("AC-FSW8 standing line absent")

    # AC-FSW9 no face authored the document it verified: a gate that rewrites its own
    # evidence can never report staleness, so mutation is a FAIL and not a footnote.
    for r in rows:
        if r.get("mutated"):
            fails.append("AC-FSW9 %s mutated %r during its own check"
                         % (r.get("id"), r.get("mutated_files")))

    # AC-FSW11 (R2819) a board that carries no sweep stamp cannot answer "am I behind?", so
    # it is REFUSED rather than read as "nothing is stale". Same law as the writer-census
    # baseline that refused a missing class key: an absent key is not a passing value.
    swept_ns = doc.get("swept_ns")
    if not isinstance(swept_ns, int) or isinstance(swept_ns, bool) or swept_ns <= 0:
        fails.append("AC-FSW11 E_FSW_NO_SWEEP_STAMP swept_ns=%r" % (swept_ns,))

    # AC-FSW10 (R2819) THE HOLE THIS SUITE WAS BUILT FOR: this board's verdicts are
    # subprocess executions, and nothing in the tree re-runs them, so a board whose stamp
    # predates an artifact re-render is a claim about a version of that face nobody
    # measured. Existing-only checks (AC-FSW4/AC-FSW9) cannot see it by design. Every face
    # artifact must therefore be OLDER than the sweep that published its verdict.
    if isinstance(swept_ns, int) and not isinstance(swept_ns, bool):
        for r in rows:
            for key in ("html", "json"):
                p = os.path.join(ROOT, r.get(key) or "")
                if not os.path.exists(p):
                    continue
                mtime_ns = os.stat(p).st_mtime_ns
                if mtime_ns > swept_ns:
                    fails.append("AC-FSW10 E_FACE_STALE %s %s written %dns after the sweep"
                                 % (r.get("id"), r.get(key), mtime_ns - swept_ns))

    # AC-FSW12 (R2903) every row must say what its FAIL costs, and the page must quote it.
    # A board of PASS/FAIL alone leaves the reader to guess whether a red row is a revenue
    # fact or housekeeping - the question a CEO opens the page to answer. A blank cell is
    # refused (it reads as "no consequence") AND so is the undeclared marker on any row the
    # LIVE table owns, so the fallback cannot become a quiet bypass.
    for r in rows:
        meaning = str(r.get("meaning") or "").strip()
        if not meaning or meaning == UNDECLARED:
            fails.append("AC-FSW12 %s carries no declared consequence" % r.get("id"))
            continue
        if _esc(meaning) not in html_text:
            fails.append("AC-FSW12 %s meaning not on the page" % r.get("id"))

    # AC-FSW13 (R2903) the row order is a READING order, declared in the document and
    # equal to the rows it landed, with the money proof first: a page and its own data
    # cannot disagree about which row a reader should trust first.
    order = doc.get("reading_order")
    if order != ids:
        fails.append("AC-FSW13 reading_order %r != rows %r" % (order, ids))
    # Scoped to the table this run loaded: a fixture world that owns no money row cannot be
    # asked to lead with one, so the rule bites exactly where the shipped table does.
    if MONEY_ID in [f[0] for f in FACES] and (not ids or ids[0] != MONEY_ID):
        fails.append("AC-FSW13 E_MONEY_NOT_FIRST first=%r" % (ids[0] if ids else None,))

    total = len(CRITERIA)
    for f in fails:
        print("FAIL " + f)
    print("VERDICT %s %d/%d" % ("PASS" if not fails else "FAIL", total - len(fails), total))
    return 0 if not fails else 2


def main(argv):
    opts = _read_args(argv)
    if opts["check"]:
        return check()
    return sweep(opts)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
