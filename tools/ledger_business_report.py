#!/usr/bin/env python3
"""Render the token-ledger business face into one browsable HTML report.

Why this exists: the P-47 item 2 ledger sandbox has shipped since 2026-09-24 and
passes 11/11 criteria plus 8/8 reconcile checks, but its database holds ZERO
transactions, so the only thing a reader could open was a stale hand-written
page. This driver seeds a throwaway demo ledger through the SHIPPED Ledger API,
asks the SHIPPED reconcile face for its verdict, and renders both into a single
static document, so the business loop is visible with real double-entry numbers
rather than asserted in prose.

Nothing here re-implements a ledger rule: every balance, entry and verdict comes
from src/sandbox/ledger/ledger.py and src/sandbox/ledger/reconcile.py.

Read-only with respect to the real sandbox: the demo database is created fresh
at --db (default preview/ledger-demo.db) and the shipped ledger.db is never
opened for writing.

Usage:
  python tools/ledger_business_report.py [--db PATH] [--out PATH] [--json PATH]
  python tools/ledger_business_report.py --check
Exit codes: 0 rendered, 2 reconcile FAIL or an unexpected ledger error,
            3 missing input file, 5 bad flags.

AC-LBR9 (BD-PROP-010, pre-registered before the change): the rendered json
carries a sizes block naming the byte count of both artifacts it belongs to,
iterated to a fixed point, and --check refuses when either number disagrees
with the bytes on disk.
AC-LBR10 (R3074, pinned in src/os/backlog.md before this change): sizes alone
cannot prove the page is FRESH - a page rendered before its inputs moved still
matches its own sizes. The rendered json therefore records the sha16 of the
three derivation inputs (this driver, ledger.py, config.json) in a sources
block, and --check recomputes them and names every input that moved
(E_SOURCE_STALE). Two inputs are deliberately NOT in that set and the
exclusion is named rather than implied: the demo database is re-seeded on
every render (so it is an output, not an input), and generated_utc is a clock
(so it is fresh by definition). reconcile.py is a fourth input this round does
not cover - carried, not claimed.
ASCII source, stdlib only, no network. Chinese only appears in the rendered
document, never in this file.
"""
import argparse
import hashlib
import html
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
sys.path.insert(0, LEDGER_DIR)

L = {
    "title": "\u4ee3\u5e01\u53cc\u5f0f\u8d26\u672c\u4e1a\u52a1\u62a5\u544a",
    "sub": "BigDomain \u00b7 P-47 \u4e8c\u00b7\u6c99\u7bb1\u5b9e\u6d4b\u4ef6",
    "gen": "\u751f\u6210\u65f6\u95f4",
    "src": "\u6570\u636e\u5e93",
    "since": "\u7531\u5e93\u5185\u5206\u5f55\u73b0\u7b97\u00b7\u975e\u624b\u586b",
    "ov": "\u4e00\u3001\u4e1a\u52a1\u6982\u89c8",
    "issued": "\u5df2\u94f8\u51fa",
    "circ": "\u7528\u6237\u6d41\u901a\u4e2d",
    "pool": "\u6c60\u4f59\u989d",
    "ident": "\u590d\u5f0f\u96f6\u548c \u03a3\u5168\u90e8\u8d26\u6237 = 0",
    "acc": "\u4e8c\u3001\u8d26\u6237\u8868\uff08\u7269\u5316\u4f59\u989d vs \u5206\u5f55\u6d3e\u751f\uff09",
    "accid": "\u8d26\u6237",
    "cls": "\u7c7b\u522b",
    "bal": "\u4f59\u989d",
    "der": "\u6d3e\u751f\u4f59\u989d",
    "same": "\u4e00\u81f4",
    "tx": "\u4e09\u3001\u4ea4\u6613\u4e0e\u53cc\u5f0f\u5206\u5f55",
    "type": "\u7c7b\u578b",
    "ref": "\u6765\u6e90\u5f15\u7528",
    "ent": "\u5206\u5f55",
    "ac": "\u56db\u3001\u5bf9\u8d26\u516b\u67e5\uff08\u76f4\u63a5\u8c03\u7528\u73b0\u5f79 reconcile.py\uff09",
    "rej": "\u4e94\u3001\u62d2\u7edd\u6ce8\u5165\uff08\u8d1f\u5411\u9a8c\u8bc1\uff09",
    "dis": "\u516d\u3001\u5e38\u9a7b\u98ce\u9669\u63d0\u793a",
    "rep": "\u4e03\u3001\u590d\u73b0",
    "cmd": "\u590d\u73b0\u547d\u4ee4",
    "yes": "\u2713",
    "no": "\u2717",
}


def load_config():
    with open(os.path.join(LEDGER_DIR, "config.json"), encoding="utf-8") as fh:
        return json.load(fh)


def usd(amount):
    return "{:,}".format(int(amount))


def account_class(account_id):
    if account_id.startswith("equity:"):
        return "equity"
    if account_id.startswith("pool:"):
        return "pool"
    if account_id.startswith("usr:"):
        return "usr"
    return "other"


def seed_demo(db_path, config):
    """Drive the shipped Ledger API over a fresh demo database."""
    from ledger import Ledger, LedgerError

    if os.path.exists(db_path):
        os.remove(db_path)
    led = Ledger(db_path, config)
    steps = []

    led.mint_to_pool("pool:share", 300, "seed-mint-001", "settlement")
    steps.append(("mint", "pool:share", 300, None))

    led.ensure_account("usr:avatar-001", "avatar-001")
    led.ensure_account("usr:avatar-002", "avatar-002")
    led.share_from_pool("pool:share", "usr:avatar-001", 120, "order-19001", "order")
    steps.append(("share", "usr:avatar-001", 120, None))
    led.spend("usr:avatar-001", 45, "order-19002", "order", "expedite")
    steps.append(("spend", "usr:avatar-001", 45, None))

    rejected = []
    try:
        led.share_from_pool("pool:share", "usr:avatar-002", 60, "order-19001", "order")
        rejected.append(("same-ref share", "NO-ERROR", "", False))
    except LedgerError as exc:
        rejected.append(("same-ref share", getattr(exc, "code", "?"), str(exc), True))

    try:
        led.spend("usr:avatar-002", 999, "order-19003", "order", "overspend probe")
        rejected.append(("overspend", "NO-ERROR", "", False))
    except LedgerError as exc:
        rejected.append(("overspend", getattr(exc, "code", "?"), str(exc), True))

    disclaimer = led.disclaimer_payload()
    rows = read_rows(db_path)
    led.close()
    return steps, rejected, disclaimer, rows


def read_rows(db_path):
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    out = {}
    out["accounts"] = [dict(r) for r in conn.execute(
        "SELECT account_id, census_avatar_id, balance FROM ledger_accounts ORDER BY account_id")]
    out["derived"] = {r[0]: int(r[1] or 0) for r in conn.execute(
        "SELECT account_id, SUM(CASE WHEN direction='credit' THEN amount ELSE -amount END) "
        "FROM ledger_entries GROUP BY account_id")}
    out["tx"] = [dict(r) for r in conn.execute(
        "SELECT tx_id, type, ref, ref_type, source_ai, memo, ts_utc FROM ledger_tx ORDER BY ts_utc")]
    out["entries"] = [dict(r) for r in conn.execute(
        "SELECT tx_id, account_id, direction, amount FROM ledger_entries ORDER BY tx_id, entry_id")]
    conn.close()
    return out


def run_reconcile(db_path):
    proc = subprocess.run(
        [sys.executable, os.path.join(LEDGER_DIR, "reconcile.py"), db_path],
        capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def build_html(ctx):
    e = html.escape
    acc_rows = []
    total = 0
    for row in ctx["rows"]["accounts"]:
        aid = row["account_id"]
        bal = int(row["balance"])
        derived = ctx["rows"]["derived"].get(aid, 0)
        total += bal
        ok = L["yes"] if bal == derived else L["no"]
        acc_rows.append(
            "<tr><td><code>%s</code></td><td>%s</td><td class=n>%s</td>"
            "<td class=n>%s</td><td class=n>%s</td></tr>"
            % (e(aid), account_class(aid), usd(bal), usd(derived), ok))

    by_tx = {}
    for en in ctx["rows"]["entries"]:
        by_tx.setdefault(en["tx_id"], []).append(en)
    tx_rows = []
    for tx in ctx["rows"]["tx"]:
        parts = []
        for en in by_tx.get(tx["tx_id"], []):
            parts.append("%s <code>%s</code> %s"
                         % (en["direction"], e(en["account_id"]), usd(en["amount"])))
        ai = "AI" if int(tx["source_ai"]) else "-"
        tx_rows.append(
            "<tr><td><code>%s</code></td><td>%s</td><td><code>%s</code></td>"
            "<td>%s</td><td class=n>%s</td></tr>"
            % (e(tx["tx_id"][:12]), e(tx["type"]), e(tx["ref"]), "<br>".join(parts), ai))

    rej_rows = []
    for name, code, detail, ok in ctx["rejected"]:
        mark = L["yes"] if ok else L["no"]
        rej_rows.append("<tr><td>%s</td><td class=n>%s</td><td>%s</td><td class=n>%s</td></tr>"
                        % (e(name), e(code), e(detail), mark))

    rc_line = "RECONCILE PASS" if ctx["rc"] == 0 else "RECONCILE FAIL"
    verdict_cls = "ok" if ctx["rc"] == 0 else "bad"
    issued = int(ctx["issued"])
    pool_total = sum(int(r["balance"]) for r in ctx["rows"]["accounts"]
                     if account_class(r["account_id"]) == "pool")
    user_total = sum(int(r["balance"]) for r in ctx["rows"]["accounts"]
                     if account_class(r["account_id"]) == "usr")

    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--ok:#1f7a4d;--bad:#a4302c;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1040px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:14px}
table{width:100%%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:12.5px}
td.n{text-align:right;font-variant-numeric:tabular-nums}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
.kpi{display:flex;gap:12px;flex-wrap:wrap}
.kpi div{flex:1 1 160px;border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:20px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.ok{color:var(--ok);font-weight:650}.bad{color:var(--bad);font-weight:650}
pre{background:#0f1419;color:#dfe4ea;padding:12px 14px;border-radius:8px;overflow-x:auto;font-size:12.5px;line-height:1.5}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;font-size:13px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
</style></head><body><main>
<h1>%s</h1>
<div class=meta>%s \u00b7 %s %s \u00b7 %s <code>%s</code> \u00b7 %s</div>

<div class=card><div class=kpi>
<div><span>%s</span><b>%s</b></div>
<div><span>%s</span><b>%s</b></div>
<div><span>%s</span><b>%s</b></div>
<div><span>%s</span><b class=%s>%s</b></div>
</div></div>

<h2>%s</h2>
<div class=card><table>
<tr><th>%s</th><th>%s</th><th class=n>%s</th><th class=n>%s</th><th class=n>%s</th></tr>
%s
</table></div>

<h2>%s</h2>
<div class=card><table>
<tr><th>tx</th><th>%s</th><th>%s</th><th>%s</th><th class=n>AI</th></tr>
%s
</table></div>

<h2>%s</h2>
<div class=card><pre>%s</pre><div class=%s>%s</div></div>

<h2>%s</h2>
<div class=card><table>
<tr><th>\u573a\u666f</th><th class=n>\u9519\u7801</th><th>\u8be6\u60c5</th><th class=n>\u62e6\u622a</th></tr>
%s
</table></div>

<h2>%s</h2>
<div class=card><div class=disclaimer>%s</div></div>

<h2>%s</h2>
<div class=card><code>%s</code></div>
<footer>BigDomain OSLoop \u00b7 %s \u00b7 \u672c\u9875\u7531 tools/ledger_business_report.py \u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>
</main></body></html>
""" % (
        e(L["title"]), e(L["title"]), e(L["sub"]), e(L["gen"]), e(ctx["now"]),
        e(L["src"]), e(ctx["db"]), e(L["since"]),
        e(L["issued"]), usd(issued), e(L["circ"]), usd(user_total),
        e(L["pool"]), usd(pool_total), e(L["ident"]),
        verdict_cls if total != 0 else "ok", usd(total),
        e(L["acc"]), e(L["accid"]), e(L["cls"]), e(L["bal"]), e(L["der"]), e(L["same"]),
        "\n".join(acc_rows),
        e(L["tx"]), e(L["type"]), e(L["ref"]), e(L["ent"]), "\n".join(tx_rows),
        e(L["ac"]), e(ctx["recon"]), verdict_cls, e(rc_line),
        e(L["rej"]), "\n".join(rej_rows),
        e(L["dis"]), e(ctx["disclaimer"]),
        e(L["rep"]), e(ctx["cmd"]), e(ctx["now"]),
    )


def _landing_is_default(html_path, json_path):
    """True only when both halves land under THIS root's own preview/.

    The wanted folder is computed from ROOT, not from the rebindable --out and
    --json flags, so a run that redirects its outputs cannot pose as the root.
    """
    want = os.path.realpath(os.path.join(ROOT, "preview"))
    for path in (html_path, json_path):
        if os.path.dirname(os.path.realpath(path)) != want:
            return False
    return True


def _refresh_face(html_path, json_path):
    """AC-PWC25 (R3547): landing this pair and re-deriving the CEO face are ONE run.

    The one definition lives in src/os/board_face_landing.py, so no second
    writer is kept here. ROOT is passed explicitly, so a private world derives
    that world's face. Refusals are named, never raised: both halves are
    already on disk when this runs, so the caller's exit code stays its own.
    """
    if not _landing_is_default(html_path, json_path):
        return "SKIPPED scratch"
    try:
        os_src = os.path.join(ROOT, "src", "os")
        if os_src not in sys.path:
            sys.path.insert(0, os_src)
        import board_face_landing
        ok, note, _proof = board_face_landing.refresh_export_face(ROOT)
        return "WRITTEN" if ok else "REFUSED %s" % note
    except Exception as exc:  # a private world may carry no shared writer
        return "SKIPPED %s" % type(exc).__name__


def main(argv):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--db", default=os.path.join(ROOT, "preview", "ledger-demo.db"))
    ap.add_argument("--out", default=os.path.join(ROOT, "preview", "ledger-business-report.html"))
    ap.add_argument("--json", default=os.path.join(ROOT, "preview", "ledger-business-report.json"))
    ap.add_argument("--check", action="store_true",
                    help="verify the landed sizes AND that no recorded input moved")
    try:
        args = ap.parse_args(argv[1:])
    except SystemExit:
        return 5
    if not os.path.exists(os.path.join(LEDGER_DIR, "ledger.py")):
        sys.stderr.write("E_NO_LEDGER: src/sandbox/ledger/ledger.py missing\n")
        return 3
    if args.check:
        fails = check_sizes(args.out, args.json) + check_sources(args.json)
        print("LEDGER BUSINESS CHECK %s fails=%d" % (
            "PASS" if not fails else "FAIL", len(fails)))
        for f in fails:
            print("  - %s" % f)
        return 0 if not fails else 2

    config = load_config()
    steps, rejected, disclaimer, rows = seed_demo(args.db, config)
    rc, recon = run_reconcile(args.db)

    issued = 0
    for tx in rows["tx"]:
        if tx["type"] == "mint":
            issued += sum(int(en["amount"]) for en in rows["entries"]
                          if en["tx_id"] == tx["tx_id"] and en["direction"] == "debit")
    if not issued:
        issued = sum(int(r["balance"]) for r in rows["accounts"]
                     if account_class(r["account_id"]) == "pool")

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    ctx = {
        "now": now,
        "db": os.path.relpath(args.db, ROOT).replace("\\", "/"),
        "issued": issued,
        "rejected": rejected,
        "disclaimer": disclaimer_text(disclaimer),
        "rows": rows,
        "rc": rc,
        "recon": recon.rstrip(),
        "cmd": "python tools/ledger_business_report.py",
    }
    doc = build_html(ctx)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "db": ctx["db"],
        "accounts": rows["accounts"],
        "tx_count": len(rows["tx"]),
        "entry_count": len(rows["entries"]),
        "issued": issued,
        "reconcile_rc": rc,
        "rejected": [{"case": c, "code": k, "detail": d, "blocked": b} for c, k, d, b in rejected],
        "report": os.path.relpath(args.out, ROOT).replace("\\", "/"),
        "sources": source_fingerprints(),
    }
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    # BD-PROP-010: the json states the size of both artifacts it belongs to.
    # The html is already on disk and never reads this key, so only the json's
    # own byte count is self-referential; iterate to the fixed point.
    for _ in range(6):
        payload["sizes"] = {
            "html": os.path.getsize(args.out),
            "json": os.path.getsize(args.json) if os.path.exists(args.json) else 0,
        }
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        if payload["sizes"]["json"] == os.path.getsize(args.json):
            break

    face = _refresh_face(args.out, args.json)
    print("REPORT %s bytes=%d tx=%d entries=%d issued=%d reconcile=%s face=%s"
          % (payload["report"], len(doc.encode("utf-8")), len(rows["tx"]),
             len(rows["entries"]), issued, rc_line_of(rc), face))
    return 0 if rc == 0 else 2


def check_sizes(out, jout):
    """AC-LBR9: the json's own size note must agree with the bytes on disk.

    Read-only: it opens the landed artifacts and never renders. A json whose
    sizes block is missing, empty or stale fails, so the note cannot rot into
    decoration.
    """
    if not (os.path.exists(out) and os.path.exists(jout)):
        return ["artifacts missing: %s / %s" % (out, jout)]
    with open(jout, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    sizes = doc.get("sizes") or {}
    fails = []
    if sizes.get("html") != os.path.getsize(out):
        fails.append("sizes html %s != %d on disk" % (sizes.get("html"),
                                                     os.path.getsize(out)))
    if sizes.get("json") != os.path.getsize(jout):
        fails.append("sizes json %s != %d on disk" % (sizes.get("json"),
                                                      os.path.getsize(jout)))
    return fails


def sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def source_fingerprints():
    """AC-LBR10: the three inputs this page's facts are derived from."""
    return {
        "driver": sha16(os.path.abspath(__file__)),
        "ledger": sha16(os.path.join(LEDGER_DIR, "ledger.py")),
        "config": sha16(os.path.join(LEDGER_DIR, "config.json")),
    }


def check_sources(jout):
    """AC-LBR10: name every recorded input whose bytes moved since the render."""
    if not os.path.exists(jout):
        return ["artifacts missing: %s" % jout]
    with open(jout, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    recorded = doc.get("sources") or {}
    live = source_fingerprints()
    fails = []
    for key in sorted(live):
        if recorded.get(key) != live[key]:
            fails.append("E_SOURCE_STALE %s recorded %s current %s"
                         % (key, recorded.get(key), live[key]))
    return fails


def rc_line_of(rc):
    return "PASS" if rc == 0 else "FAIL"


def disclaimer_text(payload):
    """The shipped payload is a dict; render its text plus the persistence flag."""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        text = payload.get("disclaimer") or ""
        if payload.get("persistent"):
            return text
        return text + " [persistent=False]"
    return json.dumps(payload, ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
