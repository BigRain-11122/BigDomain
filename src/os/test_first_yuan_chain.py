"""Battery suite for tools/first_yuan_chain.py - AC-FYC1..AC-FYC8.

The eight criteria belong to the tool and were pinned in src/os/backlog.md at
R2802, BEFORE the tool existed. This suite is what puts them under a battery
row; the guard shape AC-FYCB1..AC-FYCB8 was pinned at R2803, again before this
file existed.

Scope, stated honestly: this suite DOES drive the real shipped pay, member and
ledger modules, but only inside throwaway worlds under the system temp dir.
The live book src/sandbox/ledger/ledger.db is read as a digest before and
after and must be unchanged; the negative control runs on PRIVATE copies of
the landed artifacts, never on the repo bytes.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import contextlib
import datetime
import importlib.util
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "first_yuan_chain.py")
OUT_HTML = os.path.join(ROOT, "preview", "first-yuan-chain.html")
OUT_JSON = os.path.join(ROOT, "preview", "first-yuan-chain.json")
PAY_CFG = os.path.join(ROOT, "src", "sandbox", "pay", "config.json")
MEMBER_CFG = os.path.join(ROOT, "src", "sandbox", "member", "config.json")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
LEDGER_CFG = os.path.join(LEDGER_DIR, "config.json")

NET_IMPORT = re.compile(
    r"\s*(import|from)\s+(socket|urllib|http|requests|httpx|aiohttp)\b")

FAILS = []
CHECKS = []


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print("  | PASS %s %s" % (name, detail))
    else:
        FAILS.append(name)
        print("  | FAIL %s %s" % (name, detail))


def read_text(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def load_tool():
    # R3374 (AC-FYCP1..AC-FYCP3): the tool imports its sibling module
    # `face_backhop` at module level (since R3296), so a spec load from any
    # other cwd raised ModuleNotFoundError before a single criterion ran -
    # the battery row had been red at import time since that wiring and no
    # leg had re-run it. The search path is widened for this one load and
    # removed again, so the suite leaves no global residue.
    tools_dir = os.path.dirname(TOOL)
    added = tools_dir not in sys.path
    if added:
        sys.path.insert(0, tools_dir)
    try:
        spec = importlib.util.spec_from_file_location("fyc_under_test", TOOL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        if added:
            sys.path.remove(tools_dir)
    return mod


def stat_sig(path):
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def quoted_leg(html_text, product_id):
    return ("<code>%s</code>: tier=" % product_id) in html_text


def main():
    tool = load_tool()
    src = read_text(TOOL)
    html_text = read_text(OUT_HTML)
    json_text = read_text(OUT_JSON)
    pay_cfg = json.loads(read_text(PAY_CFG))
    digest_open = tool.live_ledger_digest()

    payload = tool.build_payload()
    legs = payload["legs"]

    # AC-FYCB1 <- AC-FYC1: derived, not typed.
    real_id = legs[0]["product_id"]
    cfg_price = pay_cfg["products"][real_id]["price_cent"]
    price_tokens = sorted(set(p["price_cent"] for p in pay_cfg["products"].values()))
    typed = [str(p) for p in price_tokens
             if re.search(r"(?<![0-9])%s(?![0-9])" % p, src)]
    ok("fycb1-derived",
       legs[0]["price_cent"] == cfg_price and not typed and len(legs) == 2,
       "cfg_price=%d typed_in_source=%s legs=%d"
       % (cfg_price, typed, len(legs)))

    # AC-FYCB2 <- AC-FYC2, rewritten at R2827 (AC-FYCE4): D-20261116-05 moved
    # the law from "same price, different value" to "two products, two
    # prices", so the criterion asserts the DIFFERENCE and that the landed
    # page states it, and refuses the old equal-price claim outright. Nothing
    # is deleted and nothing is relaxed: the assertion followed the law.
    values = set((len(leg["privileges"]), len(leg["periods"]),
                  (leg["activation"] or {}).get("tier")) for leg in legs)
    cmp_row = payload["comparison"]
    pair = cmp_row["price_pair"]
    delta_text = "%.2f" % (abs(pair[0]["price_cent"] - pair[1]["price_cent"])
                           / 100.0)
    stated = (tool.price_section(payload)["heading"] in html_text
              and delta_text in html_text
              and "Same price" not in html_text
              and all(quoted_leg(html_text, leg["product_id"]) for leg in legs))

    # AC-FYCE3: the red path must be measurable - a renderer that stops
    # stating the difference has to be refused BY NAME, on a self-consistent
    # private pair where the byte comparison cannot be the reason.
    real_section = tool.price_section
    priv_dir = tempfile.mkdtemp(prefix="fyce3-")
    orig_paths = (tool.HTML_PATH, tool.JSON_PATH)
    try:
        def silent_section(payload_arg):
            row = real_section(payload_arg)
            return {"heading": row["heading"],
                    "body": "<p>prices as configured</p>"}

        tool.price_section = silent_section
        silent_html = tool.render_html(payload)
        priv_html = os.path.join(priv_dir, "first-yuan-chain.html")
        priv_json = os.path.join(priv_dir, "first-yuan-chain.json")
        with open(priv_html, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(silent_html)
        with open(priv_json, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(tool.dumps(payload))
        tool.HTML_PATH, tool.JSON_PATH = priv_html, priv_json
        buf_silent = io.StringIO()
        with contextlib.redirect_stdout(buf_silent):
            rc_silent = tool.do_check()
        silent_out = buf_silent.getvalue()
    finally:
        tool.price_section = real_section
        tool.HTML_PATH, tool.JSON_PATH = orig_paths
        shutil.rmtree(priv_dir, ignore_errors=True)

    ok("fycb2-stated",
       (not cmp_row["same_price"]) and bool(cmp_row["value_differs"])
       and len(values) > 1 and stated
       and rc_silent == 2 and "E_PRICE_NOT_STATED" in silent_out,
       "same_price=%s differs=%s distinct_values=%d delta=%s stated=%s"
       " silent_rc=%d names_E_PRICE_NOT_STATED=%s"
       % (cmp_row["same_price"], cmp_row["value_differs"], len(values),
          delta_text, stated, rc_silent,
          "E_PRICE_NOT_STATED" in silent_out))

    # AC-FYCB3 <- AC-FYC3 and AC-FYCB4 <- AC-FYC4 share ONE throwaway world,
    # read RAW (the rendered payload is canonicalised, so its period stamps are
    # ordinals and cannot carry a real start/end reading).
    world = tool.build_world()
    tmp_world = world["tmp"]
    try:
        raw_real = tool.drive_leg(world, world["real_id"], "sys.probe.one", "fycb4-n1")
        raw_dock = tool.drive_leg(world, tool.DOCK_PRODUCT_ID, "sys.probe.two", "fycb4-n2")
        conn = sqlite3.connect(world["ledger_db"])
        try:
            rows = conn.execute(
                "SELECT tx_id, direction, SUM(amount) FROM ledger_entries "
                "GROUP BY tx_id, direction").fetchall()
            n_entries = conn.execute(
                "SELECT COUNT(*) FROM ledger_entries").fetchone()[0]
            n_tx = conn.execute(
                "SELECT COUNT(DISTINCT tx_id) FROM ledger_entries").fetchone()[0]
        finally:
            conn.close()
        money = tool.ledger_face(world["ledger_db"], LEDGER_CFG)
    finally:
        tool.tear(world)

    # AC-FYCB3 <- AC-FYC3: the membership chain is a real chain.
    mods = tool._sandbox_modules()
    member_cfg = json.loads(read_text(MEMBER_CFG))
    tier = (raw_dock["activation"] or {}).get("tier")
    declared = []
    if tier:
        declared = sorted(
            mods["catalog"].Catalog.from_config(member_cfg).tiers[tier].privileges)
    period0 = (raw_dock["periods"] or [{}])[0]
    period_days = 0
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    if period0.get("start_utc") and period0.get("end_utc"):
        span = (datetime.datetime.strptime(period0["end_utc"], fmt)
                - datetime.datetime.strptime(period0["start_utc"], fmt))
        period_days = span.days
    # AC-FYCB3 <- AC-FYC3, tier expectation derived at R2827 (AC-FYCE4): the
    # dock product's entitlement names the tier, so the criterion reads
    # "tier:<name>" from the catalog instead of hardcoding a tier name that a
    # later ruling can rename (it did: experience -> patron at
    # D-20261116-05, which is why this row read red on a healthy tree).
    entitlement = pay_cfg["products"][tool.DOCK_PRODUCT_ID].get("entitlement", "")
    expect_tier = (entitlement.split(":", 1)[1]
                   if entitlement.startswith("tier:") else None)
    chain_ok = (expect_tier is not None and tier == expect_tier
                and bool(period0.get("period_id"))
                and period_days > 0
                and sorted(raw_dock["privileges"]) == declared
                and bool(declared))
    ok("fycb3-chain", chain_ok,
       "tier=%s expect=%s period_id=%s days=%d privs=%d catalog=%d equal=%s"
       % (tier, expect_tier, bool(period0.get("period_id")), period_days,
          len(raw_dock["privileges"]), len(declared),
          sorted(raw_dock["privileges"]) == declared))

    real_ok = ((raw_real["activation"] or {}).get("tier") is None
               and len(raw_real["periods"]) == 0
               and len(raw_real["privileges"]) == 0)
    ok("fycb3-real-leg", real_ok,
       "product=%s tier=%s periods=%d privs=%d"
       % (raw_real["product_id"],
          (raw_real["activation"] or {}).get("tier"),
          len(raw_real["periods"]), len(raw_real["privileges"])))

    # AC-FYCB4 <- AC-FYC4: the ledger invariant recomputed by our own SQL.
    per_tx = {}
    for tx_id, direction, total in rows:
        per_tx.setdefault(tx_id, {})[direction] = total
    own_balanced = bool(per_tx) and all(
        len(sides) == 2 and sides.get("credit") == sides.get("debit")
        for sides in per_tx.values())
    ok("fycb4-ledger",
       own_balanced and bool(money["zero_delta"]) and money["reconcile_rc"] == 0
       and money["entries"] == n_entries and money["transactions"] == n_tx,
       "own_balanced=%s entries=%d/%d tx=%d/%d rc=%d zero_delta=%s"
       % (own_balanced, money["entries"], n_entries,
          money["transactions"], n_tx, money["reconcile_rc"], money["zero_delta"]))

    # AC-FYCB7 (temp world) - the throwaway world must be gone after tear().
    # The path itself is a random temp name, so it is not printed: the reading
    # must be reproducible for a double run to be byte-identical.
    ok("fycb7-temp-removed", not os.path.exists(tmp_world),
       "removed=%s" % (not os.path.exists(tmp_world)))

    # AC-FYCB5 <- AC-FYC5: --check is read-only and really re-derives.
    before = (stat_sig(OUT_HTML), stat_sig(OUT_JSON))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = tool.do_check()
    after = (stat_sig(OUT_HTML), stat_sig(OUT_JSON))
    ok("fycb5-readonly",
       rc == 0 and before == after and "VERDICT PASS" in buf.getvalue(),
       "rc=%d stats_equal=%s verdict=%s"
       % (rc, before == after, "PASS" if "VERDICT PASS" in buf.getvalue() else "other"))

    # AC-FYCB6 <- AC-FYC6: the gate must be load-bearing (private copies only).
    priv = tempfile.mkdtemp(prefix="fycb6-")
    orig_html, orig_json = tool.HTML_PATH, tool.JSON_PATH
    try:
        priv_html = os.path.join(priv, "first-yuan-chain.html")
        priv_json = os.path.join(priv, "first-yuan-chain.json")
        clean_html = read_bytes(OUT_HTML)
        shutil.copyfile(OUT_JSON, priv_json)
        with open(priv_html, "wb") as handle:
            handle.write(clean_html)
        tool.HTML_PATH, tool.JSON_PATH = priv_html, priv_json
        tampered = clean_html.replace(b"Two prices, two products",
                                      b"Two prices, one product", 1)
        with open(priv_html, "wb") as handle:
            handle.write(tampered)
        buf_bad = io.StringIO()
        with contextlib.redirect_stdout(buf_bad):
            rc_bad = tool.do_check()
        with open(priv_html, "wb") as handle:
            handle.write(clean_html)
        buf_ok = io.StringIO()
        with contextlib.redirect_stdout(buf_ok):
            rc_ok = tool.do_check()
        ok("fycb6-negctl",
           tampered != clean_html and rc_bad == 2 and "E_STALE" in buf_bad.getvalue()
           and rc_ok == 0,
           "tampered=%s rc_bad=%d names_E_STALE=%s rc_restored=%d"
           % (tampered != clean_html, rc_bad,
              "E_STALE" in buf_bad.getvalue(), rc_ok))
    finally:
        tool.HTML_PATH, tool.JSON_PATH = orig_html, orig_json
        shutil.rmtree(priv, ignore_errors=True)

    # AC-FYCB7 <- AC-FYC7: offline, pure, and the live book untouched.
    ok("fycb7-offline",
       "http://" not in html_text and "https://" not in html_text,
       "html_network_literals=%d"
       % (html_text.count("http://") + html_text.count("https://")))
    net_lines = [ln.strip() for ln in src.splitlines() if NET_IMPORT.match(ln)]
    ok("fycb7-pure",
       all(ord(ch) < 128 for ch in src) and not net_lines,
       "pure_ascii=%s network_imports=%s"
       % (all(ord(ch) < 128 for ch in src), net_lines))
    ok("fycb7-live-book", digest_open == tool.live_ledger_digest(),
       "%s -> %s" % (digest_open, tool.live_ledger_digest()))

    # AC-FYCB8 <- AC-FYC8: the honest scope is printed on the page.
    ok("fycb8-scope",
       payload["scope"]["network"] == "none"
       and "Honest scope" in html_text and "msgSecCheck" in html_text
       and "CEO physical pieces" in html_text,
       "network=%s honest=%s msgseccheck=%s ceo=%s"
       % (payload["scope"]["network"], "Honest scope" in html_text,
          "msgSecCheck" in html_text, "CEO physical pieces" in html_text))

    # AC-FYCF1 (R2903): the tool's own docstring must agree with the relation
    # it measures. The heading comes from the ONE shipped definition, so the
    # sentence cannot drift away from the page it describes; the same
    # predicate is applied to DOCTORED copies so the criterion is measured
    # instead of being a constant that happens to match today.
    doc = tool.__doc__ or ""
    heading = tool.price_section(payload)["heading"]
    equality_claim = re.compile(r"\bsame price\b", re.I)

    def doc_agrees(text):
        if cmp_row["same_price"]:
            return bool(equality_claim.search(text))
        return not equality_claim.search(text) and heading in text

    arms = [doc_agrees(doc.replace(heading, "the price statement"))]
    if not cmp_row["same_price"]:
        arms.append(doc_agrees("It buys two products at the same price.\n" + doc))
    ok("fycf1-docstring",
       doc_agrees(doc) and not any(arms),
       "same_price=%s heading=%r live=%s doctored=%s"
       % (cmp_row["same_price"], heading, doc_agrees(doc), arms))

    total = len(CHECKS)
    if FAILS:
        print("SUITE FAIL %d/%d %s"
              % (total - len(FAILS), total, ",".join(FAILS)))
        return 1
    print("SUITE PASS %d/%d criteria=%d" % (total, total, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
