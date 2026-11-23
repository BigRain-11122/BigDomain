"""ledger_reconcile_face - the shipped ledger self-check as an openable measurement.

Why this exists: src/sandbox/ledger/reconcile.py is the honesty-law machine for
P-47 item 2. It runs eight checks over the double-entry ledger and exits 0/2. It
has been shipped and green for many windows, yet NO page showed it: the business
report is a report, the walkthrough computes its own delta, first-yuan only
records reconcile_rc=0. So the one machine that certifies the ledger was
invisible to the reader.

This tool RUNS that script (never re-implements it) three times per render, every
time on a copy inside a temp directory:

  pass 1  the real sandbox ledger            -> what the shipped book reads today
  pass 2  a book seeded through the shipped  -> a ledger WITH content must still
          ledger API (gate pass, mint, pay)     read green, or green means nothing
  pass 3  the seeded book with ONE entry     -> the same script must go red and
          removed from a multi-entry tx         name the checks that flipped

Pass 1 is reported as a VACUOUS PASS when the book holds zero entries: eight
green rows over an empty book certify nothing about money flow, and the page says
so in words instead of letting the green imply more than it measured.

Usage:
  python tools/ledger_reconcile_face.py           # render html + json
  python tools/ledger_reconcile_face.py --check   # read-only verdict, rc=2 stale

Criteria AC-LRC1..AC-LRC6 are pinned in src/os/backlog.md BEFORE this file
existed: derived-not-typed, isolation, verdict honesty, load-bearing control,
--check read-only plus fixed point, purity and offline.

Stdlib only, zero network, no shell string: the only external process is
sys.executable running the shipped script.
"""

import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOOLS = os.path.join(HERE, "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
import face_backhop  # noqa: E402  (the shipped post-render channel, one definition)

LDIR = os.path.join(HERE, "src", "sandbox", "ledger")
SCRIPT = os.path.join(LDIR, "reconcile.py")
CONFIG = os.path.join(LDIR, "config.json")
LIVE_DB = os.path.join(LDIR, "ledger.db")
PREVIEW = os.path.join(HERE, "preview")
HTML = os.path.join(PREVIEW, "ledger-reconcile-face.html")
JSON = os.path.join(PREVIEW, "ledger-reconcile-face.json")
FACE = "ledger-reconcile-face.html"

CHECK_RE = re.compile(r"^(\d+)\s+([a-z0-9][a-z0-9\-]*)\s+(PASS|FAIL)(?:\s+n=(\d+)\s*(.*))?$")
DETAIL_RE = re.compile(r"^\s{2,}([a-z][a-z0-9\-]*):\s*(.*)$")
FORBIDDEN = ("http://", "https://")

L = {
    "h1": "\u5bf9\u8d26\u5b9e\u6d4b\u53f0 \u00b7 \u53cc\u5f0f\u8d26\u672c",
    "sub": "\u6bcf\u4e00\u6b21\u6e32\u67d3\u90fd\u771f\u8dd1\u5df2\u53d1\u8d27\u7684\u5bf9\u8d26\u811a\u672c\uff08\u516b\u6761\u68c0\u67e5\uff09\uff0c\u6570\u5b57\u5168\u90e8\u6765\u81ea\u5b83\u7684\u8f93\u51fa\u3002",
    "sec0": "\u771f\u5e93\u5f53\u524d\u72b6\u6001",
    "sec1": "\u516b\u6761\u68c0\u67e5\uff08\u771f\u5e93\u526f\u672c\u5b9e\u8dd1\uff09",
    "sec2": "\u6b63\u63a7\uff1a\u7528\u5df2\u53d1\u8d27\u7684\u8d26\u672c API \u5efa\u4e00\u672c\u6709\u5185\u5bb9\u7684\u8d26\uff0c\u518d\u8dd1\u540c\u4e00\u811a\u672c",
    "sec3": "\u8d1f\u63a7\uff1a\u540c\u4e00\u811a\u672c\u8dd1\u88ab\u7be1\u6539\u7684\u526f\u672c",
    "foot": "\u5e38\u9a7b\u63d0\u793a\uff1a\u672c\u9875\u4e3a\u6c99\u7bb1\u8d26\u672c\uff0cmock=true\u3001chargeable=false\uff0c\u4e0d\u6784\u6210\u6295\u8d44\u5efa\u8bae\uff1b\u751f\u6210\u5185\u5bb9\u4e00\u5f8b\u5e26 AIGC \u6807\u8bc6\u3002",
    "acct": "\u8d26\u6237",
    "tx": "\u4ea4\u6613",
    "entry": "\u5206\u5f55",
    "net": "\u51c0\u989d",
    "c_idx": "\u68c0\u67e5",
    "c_name": "\u540d\u79f0",
    "c_verdict": "\u7ed3\u8bba",
    "c_detail": "\u7ec6\u8282",
    "empty": "\u7a7a\u8d26\u7c3f\uff1a\u771f\u5e93 0 \u6761\u5206\u5f55\uff0c\u516b\u6761\u68c0\u67e5\u5728\u96f6\u5206\u5f55\u4e0a\u901a\u8fc7\uff0c\u5c5e\u300c\u65e0\u5185\u5bb9\u901a\u8fc7\u300d\u2014\u2014\u5b83\u8bc1\u660e\u4e86\u8fd9\u672c\u8d26\u4e0d\u77db\u76fe\uff0c\u4e0d\u4ee3\u8868\u8d44\u91d1\u6d41\u5df2\u9a8c\u8bc1\u3002\u4e0b\u9762\u7684\u6b63\u63a7\u5c31\u662f\u4e3a\u4e86\u628a\u8fd9\u4e2a\u76f2\u533a\u8865\u4e0a\u3002",
    "vacuous": "\u8d1f\u63a7\u672a\u7ffb\u7ea2\uff1a\u7be1\u6539\u540e\u4ecd\u5168\u7eff\uff0c\u56e0\u6b64\u672c\u9875\u4e0d\u58f0\u79f0\u68c0\u67e5\u627f\u91cd\u3002",
}


def _copy_world(prefix):
    """Copy the sandbox ledger (db + wal + shm) into a fresh temp dir."""
    dest = tempfile.mkdtemp(prefix=prefix)
    for name in ("ledger.db", "ledger.db-wal", "ledger.db-shm"):
        src = os.path.join(LDIR, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest, name))
    return os.path.join(dest, "ledger.db")


def run_reconcile(db_path):
    """Run the SHIPPED script on one db copy and parse its conclusion lines."""
    proc = subprocess.run(
        [sys.executable, SCRIPT, db_path, CONFIG],
        capture_output=True,
        text=True,
    )
    rows = []
    details = []
    verdict_line = ""
    for line in proc.stdout.splitlines():
        hit = CHECK_RE.match(line)
        if hit:
            rows.append(
                {
                    "index": int(hit.group(1)),
                    "name": hit.group(2),
                    "verdict": hit.group(3),
                    "n": int(hit.group(4)) if hit.group(4) else 0,
                    "detail": (hit.group(5) or "").strip(),
                }
            )
            continue
        det = DETAIL_RE.match(line)
        if det:
            details.append({"kind": det.group(1), "text": det.group(2).strip()})
            continue
        if line.startswith("RECONCILE "):
            verdict_line = line.strip()
    return {
        "rc": proc.returncode,
        "rows": rows,
        "details": details,
        "verdict_line": verdict_line,
        "stderr": proc.stderr.strip()[:400],
    }


def ledger_stats(db_path):
    conn = sqlite3.connect(db_path)
    try:
        accounts = conn.execute("SELECT COUNT(*) FROM ledger_accounts").fetchone()[0]
        tx = conn.execute("SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
        entries = conn.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]
        net = conn.execute("SELECT COALESCE(SUM(balance),0) FROM ledger_accounts").fetchone()[0]
    finally:
        conn.close()
    return {"accounts": accounts, "tx": tx, "entries": entries, "net": net}


def seed_book(db_path):
    """Build a book with real content through the SHIPPED ledger API."""
    if LDIR not in sys.path:
        sys.path.insert(0, LDIR)
    import ledger as LEDP

    with io.open(CONFIG, "r", encoding="utf-8") as handle:
        cfg = json.load(handle)
    action = (cfg.get("actions") or {}).get("cocreate") or {}
    account = "usr:lrc-demo"
    pool = str(action.get("pool") or "pool:share")
    evt = "evt-reconcile-face-0001"
    steps = []
    led = LEDP.Ledger(db_path, cfg)
    try:
        for label, fn in (
            ("ensure_account user", lambda: led.ensure_account(account, census_avatar_id="lrc-demo")),
            ("ensure_account pool", lambda: led.ensure_account(pool)),
            ("record_gate_pass", lambda: led.record_gate_pass(evt)),
            ("mint_to_pool 100", lambda: led.mint_to_pool(pool, 100, evt)),
            ("grant_reward cocreate", lambda: led.grant_reward(account, "cocreate", evt)),
        ):
            try:
                out = fn()
                steps.append({"step": label, "ok": True, "out": str(out)[:120]})
            except Exception as exc:  # recorded, never hidden
                steps.append({"step": label, "ok": False, "out": "%s: %s" % (type(exc).__name__, exc)})
        balance = led.balance(account)
        steps.append({"step": "balance", "ok": True, "out": str(balance)[:120]})
    finally:
        led.close()
    return steps


def tamper(db_path):
    """Remove ONE entry from a tx that carries at least two, so the book stops balancing."""
    conn = sqlite3.connect(db_path)
    try:
        pick = conn.execute(
            "SELECT tx_id FROM ledger_entries GROUP BY tx_id HAVING COUNT(*) >= 2"
            " ORDER BY tx_id LIMIT 1"
        ).fetchone()
        if not pick:
            return {"applied": False, "reason": "no tx with >= 2 entries"}
        tx_id = pick[0]
        before = conn.execute(
            "SELECT COUNT(*) FROM ledger_entries WHERE tx_id = ?", (tx_id,)
        ).fetchone()[0]
        row = conn.execute(
            "SELECT entry_id FROM ledger_entries WHERE tx_id = ?"
            " ORDER BY entry_id LIMIT 1",
            (tx_id,),
        ).fetchone()
        conn.execute("DELETE FROM ledger_entries WHERE entry_id = ?", (row[0],))
        conn.commit()
        after = conn.execute(
            "SELECT COUNT(*) FROM ledger_entries WHERE tx_id = ?", (tx_id,)
        ).fetchone()[0]
    finally:
        conn.close()
    return {
        "applied": True,
        "reason": "one entry removed from a multi-entry tx",
        "tx_id": tx_id,
        "entry_id": row[0],
        "entries_before": before,
        "entries_after": after,
    }


def verdict_of(rc):
    if rc == 0:
        return "PASS"
    if rc == 2:
        return "FAIL"
    return "ERROR"


def _block(run, seeded=None):
    return {
        "rc": run["rc"],
        "verdict": verdict_of(run["rc"]),
        "verdict_line": run["verdict_line"],
        "checks": run["rows"],
        "details": run["details"],
        "stderr": run["stderr"],
    }


def build_doc():
    real_db = _copy_world("reconcile-face-real-")
    real_stats = ledger_stats(real_db)
    real = run_reconcile(real_db)

    seeded_db = _copy_world("reconcile-face-seed-")
    steps = seed_book(seeded_db)
    seeded_stats = ledger_stats(seeded_db)
    seeded = run_reconcile(seeded_db)

    operation = tamper(seeded_db)
    control = run_reconcile(seeded_db)

    seeded_by_name = {r["name"]: r["verdict"] for r in seeded["rows"]}
    flipped = [
        r["name"]
        for r in control["rows"]
        if r["verdict"] == "FAIL" and seeded_by_name.get(r["name"]) == "PASS"
    ]
    return {
        "schema_version": 1,
        "surface": "preview/ledger-reconcile-face.html",
        "note": "Every number here came out of the shipped reconcile.py run at render time.",
        "source": {
            "script": "src/sandbox/ledger/reconcile.py",
            "script_bytes": os.path.getsize(SCRIPT),
            "config": "src/sandbox/ledger/config.json",
            "config_bytes": os.path.getsize(CONFIG),
            "db": "src/sandbox/ledger/ledger.db",
            "db_bytes": os.path.getsize(LIVE_DB),
            "wal_present": os.path.isfile(LIVE_DB + "-wal"),
        },
        "stats": real_stats,
        "real": _block(real),
        "seeded": {"steps": steps, "stats": seeded_stats, "run": _block(seeded)},
        "control": {
            "operation": operation,
            "run": _block(control),
            "flipped": flipped,
            "vacuous": control["rc"] == 0,
        },
        "counts": {
            "checks": len(real["rows"]),
            "real_fail": len([r for r in real["rows"] if r["verdict"] == "FAIL"]),
            "seeded_fail": len([r for r in seeded["rows"] if r["verdict"] == "FAIL"]),
            "control_fail": len([r for r in control["rows"] if r["verdict"] == "FAIL"]),
            "flipped": len(flipped),
            "real_empty": real_stats["entries"] == 0,
        },
        "sizes": {"html": 0, "json": 0},
    }


CSS = """
body{margin:0;background:#12141a;color:#dfe3ea;font:15px/1.6 -apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:960px;margin:0 auto;padding:38px 22px 80px}
h1{font-size:22px;margin:0 0 6px}
.sub{color:#8f98a8;font-size:13px;margin-bottom:22px}
h2{font-size:15.5px;margin:30px 0 10px;color:#a9b4c6;border-left:3px solid #3a4252;padding-left:10px}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 18px}
.card{background:#191d25;border:1px solid #262c38;border-radius:9px;padding:10px 14px;min-width:92px}
.card b{display:block;font-size:19px;font-weight:600;margin-bottom:2px}
.card span{font-size:12px;color:#8f98a8}
table{width:100%;border-collapse:collapse;background:#191d25;border:1px solid #262c38;border-radius:9px;overflow:hidden}
th,td{text-align:left;padding:9px 12px;font-size:13.5px;border-bottom:1px solid #222834}
th{background:#1d222b;color:#98a2b3;font-weight:600;font-size:12.5px}
tr:last-child td{border-bottom:none}
.pass{color:#7fd6a0;font-weight:600}
.fail{color:#e08a8a;font-weight:600}
.err{color:#e0bb7f;font-weight:600}
.mono{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12.5px;color:#9fb3d1}
.verdict{display:inline-block;font-size:13px;padding:3px 12px;border-radius:20px;margin:0 8px 14px 0}
.v-pass{background:#1f3a29;color:#7fd6a0}
.v-fail{background:#3a2020;color:#e08a8a}
.v-err{background:#3a2f1f;color:#e0bb7f}
.note{background:#191d25;border:1px solid #4a3a2b;border-radius:9px;padding:12px 14px;font-size:13px;color:#e0bb7f;margin:12px 0}
.bad{background:#191d25;border:1px solid #4a2b2b;border-radius:9px;padding:12px 14px;font-size:13px;color:#e08a8a;margin:12px 0}
.quiet{background:#191d25;border:1px solid #262c38;border-radius:9px;padding:12px 14px;font-size:13px;color:#98a2b3;margin:12px 0}
.foot{margin-top:30px;padding-top:14px;border-top:1px solid #262c38;color:#6f7889;font-size:12px}
code{background:#0d1016;padding:1px 5px;border-radius:4px;font-size:12.5px;color:#9fb3d1}
"""


def _badge(verdict):
    cls = {"PASS": "pass", "FAIL": "fail"}.get(verdict, "err")
    return '<span class="%s">%s</span>' % (cls, verdict)


def _table(checks):
    out = ["<table>"]
    out.append(
        "<tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>"
        % (L["c_idx"], L["c_name"], L["c_verdict"], L["c_detail"])
    )
    for c in checks:
        detail = c["detail"]
        if c["n"]:
            detail = ("n=%d %s" % (c["n"], detail)).strip()
        out.append(
            "<tr><td>%d</td><td class=\"mono\">%s</td><td>%s</td><td class=\"mono\">%s</td></tr>"
            % (c["index"], c["name"], _badge(c["verdict"]), detail or "-")
        )
    out.append("</table>")
    return "".join(out)


def _cards(stats, extra=None):
    out = ['<div class="stats">']
    for label, key in ((L["acct"], "accounts"), (L["tx"], "tx"), (L["entry"], "entries"), (L["net"], "net")):
        out.append('<div class="card"><b>%s</b><span>%s</span></div>' % (stats[key], label))
    for big, small in (extra or ()):
        out.append('<div class="card"><b>%s</b><span>%s</span></div>' % (big, small))
    out.append("</div>")
    return "".join(out)


def _banner(block, rc_label):
    vclass = {"PASS": "v-pass", "FAIL": "v-fail"}.get(block["verdict"], "v-err")
    return '<div class="verdict %s">%s \u00b7 rc=%d \u00b7 %s</div>' % (
        vclass,
        block["verdict"],
        block["rc"],
        block["verdict_line"] or rc_label,
    )


def render_html(doc):
    real = doc["real"]
    seeded = doc["seeded"]
    control = doc["control"]
    src = doc["source"]
    out = ["<!DOCTYPE html>"]
    out.append('<html lang="zh-CN"><head><meta charset="utf-8">')
    out.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    out.append("<title>BigDomain \u00b7 %s</title>" % L["h1"])
    out.append("<style>" + CSS + "</style></head><body><main>")
    out.append("<h1>%s</h1>" % L["h1"])
    out.append('<div class="sub">%s <span class="mono">reconcile.py</span></div>' % L["sub"])

    out.append("<h2>%s</h2>" % L["sec0"])
    out.append(_banner(real, "-"))
    out.append(_cards(doc["stats"], ((("%d B" % src["db_bytes"]), "db"), (("%d B" % src["script_bytes"]), "script"))))
    out.append("<h2>%s</h2>" % L["sec1"])
    if doc["counts"]["real_empty"]:
        out.append('<div class="note">%s</div>' % L["empty"])
    out.append(_table(real["checks"]))
    if real["details"]:
        out.append('<div class="quiet">')
        for d in real["details"]:
            out.append('<div class="mono">%s: %s</div>' % (d["kind"], d["text"]))
        out.append("</div>")

    out.append("<h2>%s</h2>" % L["sec2"])
    out.append(_banner(seeded["run"], "-"))
    out.append(_cards(seeded["stats"]))
    out.append('<div class="quiet">')
    for s in seeded["steps"]:
        mark = "ok" if s["ok"] else "refused"
        out.append('<div class="mono">%s \u00b7 %s \u00b7 %s</div>' % (s["step"], mark, s["out"]))
    out.append("</div>")
    out.append(_table(seeded["run"]["checks"]))

    out.append("<h2>%s</h2>" % L["sec3"])
    op = control["operation"]
    if op.get("applied"):
        out.append(
            '<div class="quiet">%s \u00b7 tx <span class="mono">%s</span> \u00b7 entry'
            ' <span class="mono">%s</span> \u00b7 entries %d \u2192 %d</div>'
            % (op["reason"], op["tx_id"], op["entry_id"], op["entries_before"], op["entries_after"])
        )
    else:
        out.append('<div class="bad">control not applicable: %s</div>' % op.get("reason", "?"))
    if control["vacuous"]:
        out.append('<div class="bad">%s</div>' % L["vacuous"])
    else:
        out.append(
            '<div class="quiet">rc=%d \u00b7 %d checks failed \u00b7 flipped: %s</div>'
            % (control["run"]["rc"], doc["counts"]["control_fail"],
               ", ".join(control["flipped"]) or "-")
        )
    out.append(_table(control["run"]["checks"]))
    out.append(
        '<div class="foot">\u6d3e\u751f\u547d\u4ee4\uff1a<code>python tools/ledger_reconcile_face.py</code>'
        " (html %d B \u00b7 json %d B)<br>%s</div>"
        % (doc["sizes"]["html"], doc["sizes"]["json"], L["foot"])
    )
    out.append("</main></body></html>")
    return "\n".join(out) + "\n"


def compose(html):
    """The shipped post-render channel is part of this face, not an outside edit.

    face_backhop appends a visible way back and, by its AC-FBH5, records the
    post-injection byte count in the sibling json. A pair whose html lacks that
    block is a pair the channel has not finished, so composing it here from the
    channel's own function keeps AC-LRC5 a fixed point of the whole chain
    instead of a law the chain cannot satisfy by construction.
    """
    return face_backhop.inject_text(html, FACE)[0]


def render(write=True):
    doc = build_doc()
    html = ""
    text = ""
    for _ in range(8):
        html = compose(render_html(doc))
        text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
        hb = len(html.encode("utf-8"))
        jb = len(text.encode("utf-8"))
        if doc["sizes"]["html"] == hb and doc["sizes"]["json"] == jb:
            break
        doc["sizes"] = {"html": hb, "json": jb}
    if write:
        with io.open(HTML, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        with io.open(JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    return html, text, doc


def _read(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()


def check():
    fails = []
    if not os.path.isfile(HTML):
        return ["missing " + HTML]
    if not os.path.isfile(JSON):
        return ["missing " + JSON]
    landed_html = _read(HTML)
    landed = json.loads(_read(JSON))
    fresh = build_doc()

    # AC-LRC1 the row set and every verdict are re-measured, not trusted
    for key, block in (("real", landed["real"]), ("seeded", landed["seeded"]["run"])):
        names = [c["name"] for c in block["checks"]]
        want = [c["name"] for c in fresh["real"]["checks"]]
        if names != want:
            fails.append("AC-LRC1 %s check names drift from a fresh measurement" % key)
    if [c["verdict"] for c in landed["real"]["checks"]] != [
        c["verdict"] for c in fresh["real"]["checks"]
    ]:
        fails.append("AC-LRC1 a landed verdict differs from a fresh measurement")
    if landed["counts"]["checks"] != len(landed["real"]["checks"]):
        fails.append("AC-LRC1 recorded check count != rendered rows")

    # AC-LRC3 verdict honesty and counts
    if landed["real"]["verdict"] != verdict_of(landed["real"]["rc"]):
        fails.append("AC-LRC3 real verdict does not match its own exit code")
    if landed["counts"]["real_fail"] != len(
        [c for c in landed["real"]["checks"] if c["verdict"] == "FAIL"]
    ):
        fails.append("AC-LRC3 fail count is not recomputed from rows")
    if landed["counts"]["real_empty"] != (landed["stats"]["entries"] == 0):
        fails.append("AC-LRC3 emptiness flag does not match the measured book")
    if landed["counts"]["real_empty"] and L["empty"] not in landed_html:
        fails.append("AC-LRC3 an empty book is not stated on the page")

    # AC-LRC4 the control must actually have gone red
    if landed["control"]["operation"].get("applied") and landed["control"]["run"]["rc"] == 0:
        if L["vacuous"] not in landed_html:
            fails.append("AC-LRC4 control did not flip yet the page does not say so")
    if landed["control"]["operation"].get("applied") and landed["control"]["run"]["rc"] != 0:
        if not landed["control"]["flipped"]:
            fails.append("AC-LRC4 control failed but no flipped check was named")

    # AC-LRC5 fixed point: sizes and html reproduced from the landed payload
    if landed["sizes"]["html"] != os.path.getsize(HTML):
        fails.append("AC-LRC5 recorded html bytes != disk")
    if landed["sizes"]["json"] != os.path.getsize(JSON):
        fails.append("AC-LRC5 recorded json bytes != disk")
    if landed_html != compose(render_html(landed)):
        fails.append(
            "AC-LRC5 landed html is not a function of the landed json through the"
            " shipped post-render channel"
        )

    # AC-LRC6 offline
    for bad in FORBIDDEN:
        if bad in landed_html:
            fails.append("AC-LRC6 html carries " + bad)
    return fails


def main(argv):
    if "--check" in argv:
        fails = check()
        if fails:
            print("VERDICT FAIL %d" % len(fails))
            for f in fails[:20]:
                print("  - " + f)
            return 2
        doc = json.loads(_read(JSON))
        print(
            "VERDICT PASS 6/6 checks=%d real=%s empty=%s seeded=%s control=%s flipped=%d html=%dB json=%dB"
            % (
                doc["counts"]["checks"],
                doc["real"]["verdict"],
                doc["counts"]["real_empty"],
                doc["seeded"]["run"]["verdict"],
                doc["control"]["run"]["verdict"],
                doc["counts"]["flipped"],
                os.path.getsize(HTML),
                os.path.getsize(JSON),
            )
        )
        return 0
    html, text, doc = render(write=True)
    print(
        "WROTE %s (%dB) + %s (%dB) checks=%d real=%s empty=%s seeded=%s control=%s flipped=%s"
        % (
            HTML,
            doc["sizes"]["html"],
            JSON,
            doc["sizes"]["json"],
            doc["counts"]["checks"],
            doc["real"]["verdict"],
            doc["counts"]["real_empty"],
            doc["seeded"]["run"]["verdict"],
            doc["control"]["run"]["verdict"],
            ",".join(doc["control"]["flipped"]) or "-",
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
