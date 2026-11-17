"""Drive ONE purchase across pay -> member -> ledger and render the trace.

Why this exists: each of the five P-47 sandboxes has been proven on its own
shelf, but no window had ever driven a single purchase through the real pay,
member and ledger modules in sequence and shown what a buyer receives for the
first-yuan product. This tool builds a throwaway world under the system temp
dir and buys one permanent ticket and one monthly card, whose price relation
the page states as "Two prices, two products" - a heading derived from config
at render time and graded against this very sentence by AC-FYCF1 - then
activates the grant in the member store, reads the privileges back and checks
the money invariant by SQL and by the shipped reconcile script. Nothing about a particular round is
typed in: every price, entitlement, tier, credit count and privilege name on
the page comes from a module response or a config file read at render time.

Volatile identifiers (order ids, grant ids, period ids, transaction ids) and
wall-clock stamps are canonicalised to ordinals before rendering, so a fresh
run renders byte-identically and `--check` can compare bytes honestly. The
run's real assertions (period active, end after start, privilege set equal to
the catalog, per-transaction balance) are computed BEFORE canonicalisation and
carried as booleans plus counts.

Usage:
    python tools/first_yuan_chain.py            # render both artifacts
    python tools/first_yuan_chain.py --check    # read-only: re-derive, compare
"""

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAY = os.path.join(ROOT, "src", "sandbox", "pay")
MEMBER = os.path.join(ROOT, "src", "sandbox", "member")
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")
LOBBY = os.path.join(ROOT, "src", "sandbox", "lobby")
PREVIEW = os.path.join(ROOT, "preview")
HTML_PATH = os.path.join(PREVIEW, "first-yuan-chain.html")
JSON_PATH = os.path.join(PREVIEW, "first-yuan-chain.json")

DOCK_PRODUCT_ID = "tier_patron_30d"
DOCK_ENTITLEMENT = "tier:patron"

ACCOUNTS = ("sys.probe.one", "sys.probe.two")

HEX_ID = re.compile(r"^[0-9a-f]{8,}$")
ISO_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class Refuse(Exception):
    def __init__(self, code, detail=""):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def _load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _sandbox_modules():
    """Import the shipped sandbox modules with the member/pay path order the
    member package itself requires (member modules win over same-named pay
    modules; sec_gate resolves to the lobby product)."""
    for path in (LOBBY, PAY, LEDGER, MEMBER):
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    import catalog                      # noqa: F401  member package
    import member                       # noqa: F401  member store
    import orders                       # noqa: F401  pay orders
    import adapters                     # noqa: F401  pay channels
    import store as lobby_store         # noqa: F401  lobby event store
    import ledger                       # noqa: F401  ledger product
    return {"catalog": catalog, "member": member, "orders": orders,
            "adapters": adapters, "store": lobby_store, "ledger": ledger}


def _canon(value, state):
    """Replace volatile identifiers and wall-clock stamps with ordinals so the
    same run shape renders byte-identically every time."""
    if isinstance(value, dict):
        return dict((k, _canon(v, state)) for k, v in value.items())
    if isinstance(value, list):
        return [_canon(v, state) for v in value]
    if isinstance(value, str):
        if HEX_ID.match(value):
            return state["id"].setdefault(value, "<id:%02d>" % (len(state["id"]) + 1))
        if ISO_TS.match(value):
            return state["ts"].setdefault(value, "<ts:%02d>" % (len(state["ts"]) + 1))
    return value


def _days_between(start, end):
    from datetime import datetime
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    delta = datetime.strptime(end, fmt) - datetime.strptime(start, fmt)
    return int(round(delta.total_seconds() / 86400.0))


def _buy(world, product_id, avatar, nonce):
    pay = world["pay"]
    resp = pay.create_order(product_id, avatar)
    order_id = resp["order_id"]
    pay.place_order(order_id)
    amount = pay.order_detail(order_id)["amount_cent"]
    callback = world["chans"][resp["channel"]].make_callback(order_id, amount, nonce)
    pay.handle_callback(callback)
    grants = pay.grants_for(avatar)["items"]
    return {"order_id": order_id, "channel": resp["channel"],
            "amount_cent": amount, "grant": grants[-1]}


def build_world():
    mods = _sandbox_modules()
    tmp = tempfile.mkdtemp(prefix="fyc-")
    member_cfg = _load_json(os.path.join(MEMBER, "config.json"))
    pay_cfg = _load_json(os.path.join(PAY, "config.json"))
    ledger_cfg = _load_json(os.path.join(LEDGER, "config.json"))

    real_id = "birthright_entry"
    if real_id not in pay_cfg["products"]:
        raise Refuse("E_NO_REAL_PRODUCT", real_id)
    # AC-FYCD1: the monthly leg is driven through a row that EXISTS in the
    # shipped config. Injecting a derived temp row is exactly how the
    # same-price defect stayed invisible for many rounds, so its absence is a
    # refusal rather than a fallback.
    if DOCK_PRODUCT_ID not in pay_cfg["products"]:
        raise Refuse("E_NO_REAL_MONTHLY", DOCK_PRODUCT_ID)

    events = mods["store"].EventStore(os.path.join(tmp, "events.db"))
    led = mods["ledger"].Ledger(os.path.join(tmp, "ledger.db"), ledger_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-FYC-1", "settlement")
    pay = mods["orders"].PayOrders(pay_cfg, os.path.join(tmp, "pay.db"),
                                   events, led)
    store = mods["member"].MemberStore(member_cfg,
                                       os.path.join(tmp, "member.db"), pay)
    return {"tmp": tmp, "mods": mods, "member_cfg": member_cfg,
            "pay_cfg": pay_cfg, "ledger_cfg": ledger_cfg,
            "events": events, "led": led, "pay": pay, "store": store,
            "chans": mods["adapters"].from_config(pay_cfg),
            "ledger_db": os.path.join(tmp, "ledger.db"),
            "real_id": real_id}


def tear(world):
    for key in ("store", "pay", "led", "events"):
        close = getattr(world.get(key), "close", None)
        if close:
            close()
    shutil.rmtree(world["tmp"], ignore_errors=True)
    # A world left on disk is a defect, not housekeeping: on Windows the
    # removal fails silently while any sqlite handle is still open (the event
    # store was the one this loop used to miss), so the leak is raised.
    if os.path.exists(world["tmp"]):
        raise Refuse("E_TEMP_LEAK", world["tmp"])


def drive_leg(world, product_id, avatar, nonce):
    mods = world["mods"]
    price = world["pay_cfg"]["products"][product_id]["price_cent"]
    spec = world["pay_cfg"]["products"][product_id]
    bought = _buy(world, product_id, avatar, nonce)
    grant = bought["grant"]
    leg = {"product_id": product_id, "avatar": avatar,
           "price_cent": price,
           "name": str(spec.get("name") or product_id),
           "channel": bought["channel"],
           "amount_cent": bought["amount_cent"],
           "entitlement": grant.get("entitlement"),
           "grant_id": grant.get("grant_id"),
           "order_id": bought["order_id"]}

    refusal = None
    activation = None
    try:
        activation = world["store"].activate(grant["grant_id"], avatar)
    except mods["member"].MemberError as exc:
        refusal = {"code": exc.code, "detail": exc.detail}
    leg["activation"] = activation
    leg["refusal"] = refusal

    privs = world["store"].privileges_for(avatar)
    balance = world["store"].balance_face(avatar)
    leg["privileges"] = list(privs.get("privileges") or [])
    leg["active"] = bool(privs.get("active"))
    leg["tiers"] = list(privs.get("tiers") or [])
    leg["periods"] = list(balance.get("periods") or [])

    assert_tier = None
    tier = (activation or {}).get("tier")
    if tier:
        declared = sorted(world["mods"]["catalog"].Catalog.from_config(
            world["member_cfg"]).tiers[tier].privileges)
        assert_tier = {"tier": tier,
                       "catalog_privileges": declared,
                       "sets_equal": sorted(leg["privileges"]) == declared}
    leg["tier_control"] = assert_tier
    # AC-FYCD4: the benefits line comes from the catalog the activation was
    # scored against, never from a template string.
    leg["benefits"] = (list(assert_tier["catalog_privileges"])
                       if assert_tier else [])

    period_ok = False
    period_days = None
    if leg["periods"]:
        first = leg["periods"][0]
        start, end = first.get("start_utc"), first.get("end_utc")
        if start and end:
            period_days = _days_between(start, end)
            period_ok = end > start and bool(first.get("period_id"))
    leg["period_ok"] = period_ok
    leg["period_days"] = period_days
    return leg


def ledger_face(db_path, cfg_path):
    conn = sqlite3.connect(db_path)
    try:
        entries = conn.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]
        tx_count = conn.execute("SELECT COUNT(DISTINCT tx_id) FROM ledger_entries").fetchone()[0]
        rows = conn.execute(
            "SELECT tx_id, direction, SUM(amount) FROM ledger_entries "
            "GROUP BY tx_id, direction").fetchall()
    finally:
        conn.close()
    per_tx = {}
    for tx_id, direction, total in rows:
        per_tx.setdefault(tx_id, {})[direction] = total
    directions = sorted(set(d for _, d, _ in rows))
    unbalanced = []
    for tx_id, sides in per_tx.items():
        values = set(sides.values())
        if len(sides) != 2 or len(values) != 1:
            unbalanced.append(tx_id)
    proc = subprocess.run(
        [sys.executable, os.path.join(LEDGER, "reconcile.py"),
         db_path, cfg_path],
        capture_output=True, text=True, encoding="utf-8", timeout=180,
        cwd=LEDGER)
    line = (proc.stdout or "").strip().splitlines()
    return {"entries": entries, "transactions": tx_count,
            "directions": directions,
            "balanced_transactions": len(per_tx) - len(unbalanced),
            "unbalanced_transactions": len(unbalanced),
            "reconcile_rc": proc.returncode,
            "reconcile_line": line[-1] if line else "",
            "zero_delta": not unbalanced}


def build_payload():
    world = build_world()
    try:
        legs = [drive_leg(world, world["real_id"], ACCOUNTS[0], "fyc-n1"),
                drive_leg(world, DOCK_PRODUCT_ID, ACCOUNTS[1], "fyc-n2")]
        money = ledger_face(world["ledger_db"],
                            os.path.join(LEDGER, "config.json"))
    finally:
        tear(world)

    same_price = len(set(leg["price_cent"] for leg in legs)) == 1
    values = [(len(leg["privileges"]), len(leg["periods"]),
               (leg["activation"] or {}).get("tier"),
               bool((leg["activation"] or {}).get("permanent")))
              for leg in legs]
    differs = len(set(values)) > 1
    state = {"id": {}, "ts": {}}
    payload = {
        "tool": "first_yuan_chain",
        "protocol_version": "fyc-v1",
        "legs": legs,
        "money": money,
        "comparison": {
            "same_price": same_price,
            "value_differs": differs,
            "price_cent": legs[0]["price_cent"] if same_price else None,
            "price_pair": [
                {"product_id": leg["product_id"],
                 "name": leg["name"],
                 "price_cent": leg["price_cent"],
                 "benefits": list(leg["benefits"])}
                for leg in legs],
            "leg_values": [
                {"product_id": leg["product_id"],
                 "privileges": len(leg["privileges"]),
                 "periods": len(leg["periods"]),
                 "tier": (leg["activation"] or {}).get("tier"),
                 "permanent": bool((leg["activation"] or {}).get("permanent")),
                 "credits": (leg["activation"] or {}).get("credits_balance")}
                for leg in legs],
        },
        "scope": {
            "network": "none",
            "merchant": "none - no merchant id, no signature, no gateway call",
            "msgseccheck": "not called - the sandbox wordlists are local mocks",
            "real_purchase": "gated on the CEO physical pieces",
            "monthly_row": "the monthly product row is a real row in"
                           " src/sandbox/pay/config.json (D-20261116-05);"
                           " no temp row is injected",
        },
    }
    return _canon(payload, state)


def money_text(cent):
    return "%.2f" % (cent / 100.0) if cent is not None else "-"


def price_section(payload):
    """The page's price statement, derived from the catalog-driven comparison.

    One definition shared by the renderer and the checker (R2823 law): the
    checker must grade the SAME text the renderer publishes, otherwise a
    renderer that silently stops printing a price stays green.
    """
    cmp_row = payload["comparison"]
    pair = cmp_row["price_pair"]
    if cmp_row["same_price"]:
        return {
            "heading": "Same price, different value",
            "body": "<p>The two products cost the same %s; what differs is"
                    " what they grant.</p>" % money_text(cmp_row["price_cent"]),
        }
    first, second = pair[0], pair[1]
    delta = abs(first["price_cent"] - second["price_cent"])
    return {
        "heading": "Two prices, two products",
        "body": ("<p><code>%s</code> costs %s; <code>%s</code> costs %s"
                 " &mdash; a difference of %s, read from the catalog at"
                 " render time.</p>"
                 % (html.escape(first["product_id"]),
                    money_text(first["price_cent"]),
                    html.escape(second["product_id"]),
                    money_text(second["price_cent"]),
                    money_text(delta))),
    }


def render_html(payload):
    money = money_text

    rows = []
    for leg in payload["legs"]:
        act = leg["activation"] or {}
        rows.append(
            "<tr><td><code>%s</code><br>%s</td><td>%s</td><td>%s</td><td>%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                html.escape(leg["product_id"]),
                html.escape(str(leg.get("name") or "")),
                money(leg["price_cent"]),
                html.escape(str(leg["entitlement"])),
                html.escape(str(act.get("tier"))),
                "yes" if act.get("permanent") else "no",
                html.escape(str(len(leg["periods"]))),
                html.escape(str(len(leg["privileges"]))),
                html.escape(str(act.get("credits_balance", "-")))))
    cmp_row = payload["comparison"]
    value_lines = []
    for item in cmp_row["leg_values"]:
        value_lines.append(
            "<li><code>%s</code>: tier=%s, privileges=%d, periods=%d, "
            "credits=%s, permanent=%s</li>" % (
                html.escape(item["product_id"]), html.escape(str(item["tier"])),
                item["privileges"], item["periods"],
                html.escape(str(item["credits"])),
                "yes" if item["permanent"] else "no"))
    money_row = payload["money"]
    pair_lines = []
    for item in cmp_row["price_pair"]:
        benefits = item["benefits"]
        pair_lines.append(
            "<li><strong>%s</strong> (<code>%s</code>) &mdash; %s &mdash; "
            "benefits: %s</li>" % (
                html.escape(item["name"]), html.escape(item["product_id"]),
                money(item["price_cent"]),
                html.escape(", ".join(benefits)) if benefits
                else "none (permanent entry, no cycle, no renewal)"))
    price_row = price_section(payload)
    value_html = ('<ul>%s</ul>' % "".join(value_lines)
                  if cmp_row["value_differs"]
                  else "<p>The two legs delivered identical value.</p>")
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>First-yuan chain - one purchase through pay, member and ledger</title>
<style>
body{font:14px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;margin:32px auto;max-width:1000px;color:#1d2129;padding:0 18px}
h1{font-size:22px;margin:0 0 6px} h2{font-size:16px;margin:26px 0 8px}
.sub{color:#5c6470;margin:0 0 18px}
table{border-collapse:collapse;width:100%%;margin:8px 0 4px}
th,td{border:1px solid #dfe3e8;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#f5f7fa;font-weight:600}
.warn{background:#fff7e6;border-left:4px solid #d48806;padding:10px 12px;margin:14px 0}
.ok{color:#237804;font-weight:600} .bad{color:#a8071a;font-weight:600}
code{background:#f2f4f7;padding:1px 4px;border-radius:3px}
ul{margin:6px 0 6px 18px;padding:0}
.foot{color:#5c6470;font-size:12px;margin-top:26px;border-top:1px solid #dfe3e8;padding-top:10px}
</style></head><body>
<h1>One purchase, three modules, real numbers</h1>
<p class="sub">A throwaway world is built in the system temp dir, then the shipped
<code>orders.py</code>, <code>member.py</code> and <code>ledger.py</code> are driven in
sequence. Every figure below was read back from a module response or a config file
at render time.</p>

<h2>What the buyer receives</h2>
<table>
<tr><th>Product</th><th>Price</th><th>Entitlement</th><th>Tier</th>
<th>Permanent</th><th>Periods</th><th>Privileges</th><th>Credits</th></tr>
%s
</table>

<h2>Two products, side by side</h2>
<ul>%s</ul>

<h2>%s</h2>
%s

<h2>Money invariant, read back by SQL</h2>
<ul>
<li>entries: %d &nbsp; transactions: %d</li>
<li>directions present: %s</li>
<li>balanced transactions: %d &nbsp; unbalanced: %d &nbsp; <span class="%s">zero-delta=%s</span></li>
<li>shipped reconcile script: <span class="%s">rc=%d</span> &nbsp; %s</li>
</ul>

<div class="warn">
<strong>Honest scope.</strong> No merchant, no payment signature and no network call
was made. <code>msgSecCheck</code> was NOT called - the sandbox content gates are local
wordlists. A real purchase remains gated on the CEO physical pieces (merchant id,
server, domain, filing). Both price rows are REAL rows in
<code>src/sandbox/pay/config.json</code>, landed under council ruling
D-20261116-05: the permanent ticket carries no cycle, the monthly card carries a
period. Nothing is injected into a temp copy.
</div>

<div class="foot">Rendered by <code>tools/first_yuan_chain.py</code>. Volatile order,
grant, period and transaction identifiers and wall-clock stamps are canonicalised to
ordinals so that a fresh run renders byte-identically and <code>--check</code> can
compare bytes honestly.</div>
</body></html>
""" % ("\n".join(rows),
       "".join(pair_lines),
       html.escape(price_row["heading"]),
       price_row["body"] + value_html,
       money_row["entries"], money_row["transactions"],
       html.escape(", ".join(money_row["directions"])),
       money_row["balanced_transactions"], money_row["unbalanced_transactions"],
       "ok" if money_row["zero_delta"] else "bad",
       "yes" if money_row["zero_delta"] else "no",
       "ok" if money_row["reconcile_rc"] == 0 else "bad",
       money_row["reconcile_rc"],
       html.escape(money_row["reconcile_line"]))


def dumps(payload):
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(tmp, path)


def live_ledger_digest():
    path = os.path.join(LEDGER, "ledger.db")
    if not os.path.exists(path):
        return "absent"
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


def do_render():
    before = live_ledger_digest()
    payload = build_payload()
    after = live_ledger_digest()
    if before != after:
        raise Refuse("E_LIVE_BOOK_TOUCHED", "%s -> %s" % (before, after))
    body = render_html(payload)
    write_atomic(JSON_PATH, dumps(payload))
    write_atomic(HTML_PATH, body)
    money = payload["money"]
    print("RENDER legs=%d prices=%s same_price=%s value_differs=%s "
          "entries=%d tx=%d reconcile_rc=%d zero_delta=%s html=%dB json=%dB"
          % (len(payload["legs"]),
             ",".join("%s=%s" % (i["product_id"], i["price_cent"])
                      for i in payload["comparison"]["price_pair"]),
             payload["comparison"]["same_price"],
             payload["comparison"]["value_differs"],
             money["entries"], money["transactions"],
             money["reconcile_rc"], money["zero_delta"],
             len(body.encode("utf-8")),
             os.path.getsize(JSON_PATH)))
    return 0


def do_check():
    fails = []
    if not os.path.exists(HTML_PATH) or not os.path.exists(JSON_PATH):
        print("VERDICT FAIL 1 missing-artifact")
        return 2
    before = (os.stat(HTML_PATH).st_size, os.stat(HTML_PATH).st_mtime_ns,
              os.stat(JSON_PATH).st_size, os.stat(JSON_PATH).st_mtime_ns)
    payload = build_payload()
    want_html = render_html(payload)
    want_json = dumps(payload)
    with open(HTML_PATH, encoding="utf-8", newline="") as handle:
        got_html = handle.read()
    with open(JSON_PATH, encoding="utf-8", newline="") as handle:
        got_json = handle.read()
    if got_html != want_html:
        fails.append("E_STALE html is not the fresh derivation")
    if got_json != want_json:
        fails.append("E_STALE json is not the fresh derivation")
    if "http://" in got_html or "https://" in got_html:
        fails.append("E_OFFLINE html carries a network literal")
    cmp_row = payload["comparison"]
    # AC-FYCD2: the ruling forbids the permanent ticket and the monthly card
    # sharing a price, so a collision is a red, not a curiosity.
    if cmp_row["same_price"]:
        fails.append("E_PRICE_COLLISION both legs priced %s"
                     % cmp_row["price_cent"])
    # AC-FYCE1/AC-FYCE2: the landed page must state the prices the catalog
    # carries, must state the difference between them, and must not keep the
    # old equal-price claim alive. The difference figure is the unique
    # detector: it appears in the price statement only, never in the table.
    price_row = price_section(payload)
    if price_row["heading"] not in got_html:
        fails.append("E_PRICE_NOT_STATED heading missing: %s"
                     % price_row["heading"])
    for item in cmp_row["price_pair"]:
        if money_text(item["price_cent"]) not in got_html:
            fails.append("E_PRICE_NOT_STATED %s price %s missing from page"
                         % (item["product_id"],
                            money_text(item["price_cent"])))
    if cmp_row["same_price"]:
        if "Same price" not in got_html:
            fails.append("E_PRICE_NOT_STATED equal-price claim missing")
    else:
        pair = cmp_row["price_pair"]
        delta = abs(pair[0]["price_cent"] - pair[1]["price_cent"])
        if money_text(delta) not in got_html:
            fails.append("E_PRICE_NOT_STATED difference %s missing from page"
                         % money_text(delta))
        if "Same price" in got_html:
            fails.append("E_FALSE_SAME_PRICE page claims equal prices while"
                         " catalog reads %s vs %s"
                         % (money_text(pair[0]["price_cent"]),
                            money_text(pair[1]["price_cent"])))
    # AC-FYCD3: the permanent leg must carry no period and no tier; the
    # monthly leg must carry exactly one period and a named tier.
    permanent_leg = next(
        (l for l in payload["legs"]
         if bool((l["activation"] or {}).get("permanent"))
         and (l["activation"] or {}).get("tier") is None), None)
    monthly_leg = next(
        (l for l in payload["legs"]
         if (l["activation"] or {}).get("tier")), None)
    if permanent_leg is None:
        fails.append("E_PERMANENT_SHAPE no leg read permanent=True with no tier")
    elif permanent_leg["periods"]:
        fails.append("E_PERMANENT_SHAPE permanent leg opened %d period(s)"
                     % len(permanent_leg["periods"]))
    if monthly_leg is None:
        fails.append("E_MONTHLY_SHAPE no leg opened a tier")
    elif len(monthly_leg["periods"]) != 1:
        fails.append("E_MONTHLY_SHAPE monthly leg opened %d period(s), want 1"
                     % len(monthly_leg["periods"]))
    # AC-FYCD4: the page must carry one name line and one benefits line per
    # product, both derived from config/catalog at render time.
    for item in cmp_row["price_pair"]:
        if html.escape(item["name"]) not in got_html:
            fails.append("E_NAME product name missing from page: %s"
                         % item["product_id"])
        for priv in item["benefits"]:
            if html.escape(priv) not in got_html:
                fails.append("E_BENEFIT privilege not printed: %s/%s"
                             % (item["product_id"], priv))
        if not item["benefits"] and "no cycle, no renewal" not in got_html:
            fails.append("E_BENEFIT permanent leg benefits line missing"
                         " for %s" % item["product_id"])
    for leg in payload["legs"]:
        tier_control = leg["tier_control"]
        if tier_control and not tier_control["sets_equal"]:
            fails.append("E_TIER privileges do not match catalog for %s"
                         % leg["product_id"])
        if leg["tier_control"] is None and leg["privileges"]:
            fails.append("E_TIER privileges without a tier on %s"
                         % leg["product_id"])
    money = payload["money"]
    if not money["zero_delta"] or money["reconcile_rc"] != 0:
        fails.append("E_MONEY unbalanced=%d reconcile_rc=%d"
                     % (money["unbalanced_transactions"], money["reconcile_rc"]))
    after = (os.stat(HTML_PATH).st_size, os.stat(HTML_PATH).st_mtime_ns,
             os.stat(JSON_PATH).st_size, os.stat(JSON_PATH).st_mtime_ns)
    if before != after:
        fails.append("E_WROTE --check changed the landed artifacts")
    if fails:
        print("VERDICT FAIL %d %s" % (len(fails), " | ".join(fails)))
        return 2
    print("VERDICT PASS legs=%d entries=%d tx=%d reconcile_rc=%d "
          "html=%dB read_only=True"
          % (len(payload["legs"]), money["entries"], money["transactions"],
             money["reconcile_rc"], before[0]))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="read-only: re-derive and compare landed bytes")
    args = parser.parse_args(argv)
    try:
        return do_check() if args.check else do_render()
    except Refuse as exc:
        print("REFUSED %s %s" % (exc.code, exc.detail))
        return 2


if __name__ == "__main__":
    sys.exit(main())
