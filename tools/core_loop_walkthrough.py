"""Core loop walkthrough: RUN the shipped sandbox pieces and publish the trace.

Every other shipped P-47 face reads a document. This one executes the real
modules against a throwaway world and prints what the platform actually did
with a piece of user content, then what the ledger did with the receipt.

Criteria AC-CLW1..AC-CLW6 are pinned in src/os/backlog.md BEFORE this file.

Usage:
    python tools/core_loop_walkthrough.py            render both artifacts
    python tools/core_loop_walkthrough.py --check    read-only gate
"""

import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UGC_DIR = os.path.join(ROOT, "src", "sandbox", "ugc")
LED_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
PREVIEW = os.path.join(ROOT, "preview")
JSON_PATH = os.path.join(PREVIEW, "core-loop-walkthrough.json")
HTML_PATH = os.path.join(PREVIEW, "core-loop-walkthrough.html")
EXPORT_DIR_NAME = "export-clw-walkthrough"
EXPORT_DIR = os.path.join(UGC_DIR, EXPORT_DIR_NAME)

for _path in (UGC_DIR, LED_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import pipeline as UGCP  # noqa: E402
import ledger as LEDP  # noqa: E402

KEEP = ("evt_id", "item_id", "state", "receipt", "noise", "line", "tx_id")


def _read_json(path):
    with io.open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _refusal(exc):
    return {"refused": True, "code": str(getattr(exc, "code", "") or ""),
            "type": type(exc).__name__, "detail": str(exc)[:140]}


def _accepted(out):
    if isinstance(out, str):
        # tx ids are bookkeeping handles, not evidence: keep the fact of a
        # return so a second render stays byte identical (AC-CLW5)
        return {"refused": False, "value": {"returned_bytes": len(out.encode("utf-8"))}}
    if not isinstance(out, dict):
        return {"refused": False, "value": str(out)[:140]}
    keep = {}
    for key in KEEP:
        if key in out and key != "tx_id":
            keep[key] = out[key]
    if "draft" in out:
        draft = out.get("draft") or {}
        keep["producer"] = draft.get("producer")
        keep["ai_generated"] = draft.get("ai_generated")
    if "disclaimer" in out:
        keep["disclaimer_present"] = bool(out["disclaimer"])
    if not keep:
        keep["keys"] = sorted(out.keys())
    return {"refused": False, "value": keep}


def _step(name, module, call):
    try:
        row = _accepted(call())
    except Exception as exc:  # noqa: BLE001 - the refusal IS the evidence
        row = _refusal(exc)
    row["name"] = name
    row["module"] = module
    return row


def run_ugc(tmp):
    cfg = _read_json(os.path.join(UGC_DIR, "config.json"))
    cfg["noise"] = dict(cfg.get("noise") or {}, flood_max_submissions=50)
    cfg["export"] = dict(cfg.get("export") or {}, dir=EXPORT_DIR_NAME)
    db = os.path.join(tmp, "ugc.db")

    rule = [r for r in cfg["routing"]["rules"] if r["line"] == "bigdomain"][0]
    clean = "plaza idea about " + rule["keywords"][0]
    texts = {
        "forbidden": "probe text carrying " + cfg["gate"]["forbidden_words"][0],
        "advisory": "probe text carrying " + cfg["gate"]["advisory_ban_words"][0],
        "short": "ha",
    }

    steps = []
    evt_id = None
    item_id = None
    pipe = UGCP.UGCPipeline(cfg, db)
    try:
        for actor in ("C-30001", "C-30003", "C-30004", "C-30005"):
            pipe.grant_entrance_sandbox(actor)  # sandbox mock entrance token
        steps.append(_step("submit a clean idea", "pipeline", lambda: pipe.submit(
            "direct", "C-30001", clean)))
        steps.append(_step("submit the SAME text again", "pipeline", lambda: pipe.submit(
            "direct", "C-30001", clean)))
        steps.append(_step("submit a forbidden word", "pipeline", lambda: pipe.submit(
            "direct", "C-30003", texts["forbidden"])))
        steps.append(_step("submit an investment-advice word", "pipeline", lambda: pipe.submit(
            "direct", "C-30004", texts["advisory"])))
        steps.append(_step("submit an under-length post", "pipeline", lambda: pipe.submit(
            "direct", "C-30005", texts["short"])))

        value = steps[0].get("value") or {}
        evt_id = value.get("evt_id")

        pool = pipe.pool_query(line="bigdomain")
        items = (pool or {}).get("items") or []
        steps.append({"name": "read the bigdomain pool", "module": "pipeline",
                      "refused": False, "value": {"pooled_items": len(items)}})
        if items:
            item_id = items[0].get("item_id")
            steps.append(_step("draft the first version", "pipeline",
                               lambda: pipe.draft(item_id)))
            steps.append(_step("open final review", "pipeline",
                               lambda: pipe.final_review(item_id)))
            steps.append(_step("decide: adopt", "pipeline",
                               lambda: pipe.final_decide(item_id, "adopt")))
    finally:
        pipe.close()
    return {"steps": steps, "evt_id": evt_id, "item_id": item_id}


def run_ledger(tmp, evt_id):
    cfg = _read_json(os.path.join(LED_DIR, "config.json"))
    db = os.path.join(tmp, "ledger.db")
    acct = "usr:clw-demo"
    ledger = LEDP.Ledger(db, cfg)
    steps = []
    balance = None
    try:
        ledger.ensure_account(acct, census_avatar_id="clw-demo")
        action = (cfg.get("actions") or {}).get("cocreate") or {}
        pool = str(action.get("pool") or "pool:share")
        ledger.ensure_account(pool)  # pool side of the double entry
        steps.append(_step("pay a co-creation share with NO gate pass", "ledger",
                           lambda: ledger.grant_reward(acct, "cocreate", evt_id)))
        steps.append(_step("record the gate pass the UGC pipeline produced", "ledger",
                           lambda: ledger.record_gate_pass(evt_id)))
        steps.append(_step("pay the SAME share again, gate now satisfied", "ledger",
                           lambda: ledger.grant_reward(acct, "cocreate", evt_id)))
        steps.append(_step("mint issuance into the share pool", "ledger",
                           lambda: ledger.mint_to_pool(pool, 100, evt_id)))
        steps.append(_step("pay the share out of the funded pool", "ledger",
                           lambda: ledger.grant_reward(acct, "cocreate", evt_id)))
        balance = ledger.balance(acct)
    finally:
        ledger.close()

    conn = sqlite3.connect(db)
    try:
        row = conn.execute(
            "SELECT COUNT(*),"
            " COALESCE(SUM(CASE WHEN direction='credit' THEN amount ELSE 0 END),0),"
            " COALESCE(SUM(CASE WHEN direction='debit' THEN amount ELSE 0 END),0),"
            " COUNT(DISTINCT tx_id) FROM ledger_entries").fetchone()
    finally:
        conn.close()
    invariant = {"entries": row[0], "credit_total": row[1],
                 "debit_total": row[2], "delta": row[1] - row[2],
                 "tx_count": row[3]}
    if isinstance(balance, dict):
        invariant["account_balance"] = balance.get("balance")
    return {"steps": steps, "invariant": invariant}


def build():
    # A leftover export from an interrupted run is not this run's evidence, so
    # clear it before the run: the published "removed" reading then measures
    # only what this run left behind (AC-CLW5: a second render, under any
    # ambient leftover, stays byte identical).
    if os.path.isdir(EXPORT_DIR):
        shutil.rmtree(EXPORT_DIR, ignore_errors=True)
    tmp = tempfile.mkdtemp(prefix="clw-")
    try:
        ugc = run_ugc(tmp)
        led = run_ledger(tmp, ugc["evt_id"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    export_left = os.path.isdir(EXPORT_DIR)
    if export_left:
        shutil.rmtree(EXPORT_DIR, ignore_errors=True)

    sources = []
    for rel in ("src/sandbox/ugc/pipeline.py", "src/sandbox/ledger/ledger.py"):
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        sources.append({"path": rel, "bytes": os.path.getsize(path)})

    return {
        "title": "Core loop walkthrough",
        "subtitle": "the shipped sandbox pieces, executed; every verdict below"
                    " was produced by this run, not typed",
        "ugc_steps": ugc["steps"],
        "ledger_steps": led["steps"],
        "ledger_invariant": led["invariant"],
        "receipt_evt_id": ugc["evt_id"],
        "item_id": ugc["item_id"],
        "world": {"database": "system temp dir (removed at end of run)",
                  "export_dir_within_repo": EXPORT_DIR_NAME,
                  "export_dir_removed": export_left is False},
        "seam": "The two sandboxes keep separate databases. The receipt event id"
                " is the only thing joining them: the ledger pays a content reward"
                " solely when its own gate record says pass, which is why row 1 of"
                " the ledger trace is REFUSED and row 3 is not.",
        "honest": [
            "This runs the SANDBOX modules. No merchant, no platform API, no"
            " msgSecCheck network call: the gate is the shipped local wordlist mock.",
            "The clean idea is Chinese text sourced from the config data file, not"
            " typed into this module, so the tool source stays pure ASCII.",
            "Adoption in the sandbox writes a chronicle export under the repo, which"
            " this run deletes before it exits; nothing of the world survives.",
        ],
        "sources": sources,
    }


def render_html(payload):
    rows_ugc = []
    for step in payload["ugc_steps"]:
        verdict = "REFUSED" if step.get("refused") else "ACCEPTED"
        code = step.get("code") or ""
        detail = step.get("detail") or json.dumps(step.get("value") or {}, ensure_ascii=False)[:160]
        rows_ugc.append(
            '<tr class="%s"><td>%s</td><td><code>%s</code></td><td>%s</td><td>%s</td></tr>'
            % ("bad" if step.get("refused") else "ok", esc(step["name"]), esc(code or "-"),
               verdict, esc(detail)))
    rows_led = []
    for step in payload["ledger_steps"]:
        verdict = "REFUSED" if step.get("refused") else "BOOKED"
        code = step.get("code") or ""
        detail = step.get("detail") or json.dumps(step.get("value") or {}, ensure_ascii=False)[:160]
        rows_led.append(
            '<tr class="%s"><td>%s</td><td><code>%s</code></td><td>%s</td><td>%s</td></tr>'
            % ("bad" if step.get("refused") else "ok", esc(step["name"]), esc(code or "-"),
               verdict, esc(detail)))
    inv = payload["ledger_invariant"]
    honest = "".join("<li>%s</li>" % esc(line) for line in payload["honest"])
    srcs = "".join("<li><code>%s</code> %dB</li>" % (esc(s["path"]), s["bytes"])
                   for s in payload["sources"])
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>%(title)s</title>
<style>
body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;padding:24px;background:#0f1115;color:#e6e8ee}
h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:26px 0 8px;color:#9fb4ff}
p.sub{color:#9aa3b2;margin:0 0 18px;font-size:13px}
table{border-collapse:collapse;width:100%%;font-size:13px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid #232733;vertical-align:top}
th{color:#8f98a8;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
tr.ok td:nth-child(3){color:#6ee7a8}tr.bad td:nth-child(3){color:#ff8b7a}
code{color:#c9d1e6}.box{background:#161a22;border:1px solid #232733;border-radius:8px;padding:14px;margin:10px 0;font-size:13px}
ul{margin:6px 0 0 18px;padding:0}li{margin:3px 0;color:#b6bfd0;font-size:13px}
.big{font-size:15px}
</style></head><body>
<h1>%(title)s</h1>
<p class="sub">%(subtitle)s</p>
<p class="sub"><a href="index.html" style="color:#9fb4ff">back to the entry page</a></p>

<h2>1. What the UGC pipeline did with the content</h2>
<table><tr><th>Probe</th><th>Verdict code</th><th>Outcome</th><th>Detail read from the run</th></tr>
%(rows_ugc)s
</table>

<h2>2. What the ledger did with the receipt</h2>
<table><tr><th>Action</th><th>Verdict code</th><th>Outcome</th><th>Detail read from the run</th></tr>
%(rows_led)s
</table>

<h2>3. Double-entry invariant, recomputed from the ledger database</h2>
<div class="box big">entries %(entries)d &nbsp; credit %(credit)d &nbsp; debit %(debit)d
&nbsp; delta <strong>%(delta)d</strong> &nbsp; tx %(tx)d &nbsp; account balance %(bal)s</div>
<p class="sub">Read by SQL over <code>ledger_entries</code> after the run, not asserted by hand.</p>

<h2>4. Why the two halves are joined this way</h2>
<div class="box">%(seam)s</div>

<h2>5. Honest notes</h2>
<ul>%(honest)s</ul>
<h2>6. Executed sources</h2>
<ul>%(srcs)s</ul>
<p class="sub">Rendered offline. Non-investment-advice surface: in-city tokens are
in-loop entitlements, not withdrawable, and no content here is investment advice.</p>
</body></html>
""" % {
        "title": esc(payload["title"]), "subtitle": esc(payload["subtitle"]),
        "rows_ugc": "".join(rows_ugc), "rows_led": "".join(rows_led),
        "entries": inv["entries"], "credit": inv["credit_total"],
        "debit": inv["debit_total"], "delta": inv["delta"], "tx": inv["tx_count"],
        "bal": inv.get("account_balance", "n/a"),
        "seam": esc(payload["seam"]), "honest": honest, "srcs": srcs,
    }


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _link_targets(html_text):
    out = []
    for chunk in html_text.split('href="')[1:]:
        target = chunk.split('"')[0]
        if target and "://" not in target and not target.startswith("#"):
            out.append(target)
    return out


def dump(payload):
    return json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def check():
    problems = []
    fresh = dump(build())
    if not os.path.isfile(JSON_PATH) or not os.path.isfile(HTML_PATH):
        print("VERDICT FAIL landed artifact missing")
        return 2
    with io.open(JSON_PATH, encoding="utf-8") as handle:
        landed_text = handle.read()
    if landed_text != fresh:
        problems.append("json is not the fresh derivation")
    landed = json.loads(landed_text)
    with io.open(HTML_PATH, encoding="utf-8") as handle:
        html_text = handle.read()
    if html_text != render_html(landed):
        problems.append("html is not a function of the landed json")
    if "http://" in html_text or "https://" in html_text:
        problems.append("html carries a network literal")
    for target in _link_targets(html_text):
        if not os.path.isfile(os.path.join(PREVIEW, target)):
            problems.append("link target missing: " + target)
    inv = landed["ledger_invariant"]
    if inv["delta"] != 0:
        problems.append("ledger is not balanced")
    rows = len(landed["ugc_steps"]) + len(landed["ledger_steps"])
    if rows == 0:
        problems.append("no executed rows")
    if problems:
        print("VERDICT FAIL %d %s" % (len(problems), "; ".join(problems)))
        return 2
    print("VERDICT PASS ugc_steps=%d ledger_steps=%d entries=%d delta=%d html=%dB"
          % (len(landed["ugc_steps"]), len(landed["ledger_steps"]),
             inv["entries"], inv["delta"], len(html_text.encode("utf-8"))))
    return 0


def _landing_is_default():
    """AC-PWC23 (R3545): a scratch render derives nothing.

    Both halves are derived from PREVIEW at import time, so a caller that
    redirects them off this root's own preview/ is rendering a private world,
    not landing the company face.
    """
    try:
        own = os.path.realpath(PREVIEW)
        return (
            os.path.dirname(os.path.realpath(JSON_PATH)) == own
            and os.path.dirname(os.path.realpath(HTML_PATH)) == own
        )
    except Exception:
        return False


def _refresh_face():
    """AC-PWC23 (R3545): landing this pair and re-deriving the CEO face are ONE run.

    The one definition lives in src/os/board_face_landing.py, so no second writer
    is kept here. ROOT is passed explicitly, so a private world derives that
    world's face. Refusals are named, never raised: both halves are already on
    disk when this runs, so the caller's exit code stays its own.
    """
    if not _landing_is_default():
        return "SKIPPED not-this-root"
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
    if "--check" in argv:
        return check()
    payload = json.loads(dump(build()))  # canonical order before rendering
    with io.open(JSON_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(dump(payload))
    with io.open(HTML_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_html(payload))
    face = _refresh_face()
    inv = payload["ledger_invariant"]
    print("RENDERED ugc_steps=%d ledger_steps=%d entries=%d delta=%d json=%dB html=%dB face=%s"
          % (len(payload["ugc_steps"]), len(payload["ledger_steps"]), inv["entries"],
             inv["delta"], os.path.getsize(JSON_PATH), os.path.getsize(HTML_PATH), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
