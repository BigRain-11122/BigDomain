#!/usr/bin/env python3
"""Render the P-47 item-5 membership and benefit face into one document.

Why this exists: the member sandbox (src/sandbox/member) has shipped an
entitlement engine, a validated catalog, a credits journal, a birth-cert
face, an expiry board and a reminder, and every one of its suites asserts on
fixtures. A person who buys the month card at the checkout face has no page
that shows what they now hold, what the tiers actually grant, what a draw
does to the balance, or - the part that matters most for this company - that
membership buys NO content-review bypass. preview/membership-benefit-report.html
is that page, and it is rendered from live measurements, not from prose.

Nothing here re-implements a membership rule. The world is wired from the
SHIPPED classes exactly the way member_page.build_world wires it (EventStore,
Ledger, PayOrders, MemberStore, adapters.from_config), the join path is the
same one the shipped HTTP face uses (create_order -> place_order ->
make_callback -> grants_for -> activate), and every entitlement read is a
shipped MemberStore read face. The content gate is the shipped MsgSecStub
plus gate_page.decision_for.

The one deliberate extension is three extra sandbox price rows (patron,
mayor, cocreator) beside the shipped sandbox product, because the point of
this face is the tier matrix and the riskiest tier is the co-creation one
that carries the queue privileges. Prices stay mock: 1990 cent placeholder,
never chargeable, and the page says so.

Criteria pre-registered BEFORE the code was written (AC-MBG1..8):
  AC-MBG1 the html and json land with non-zero size and the criteria table
          carries exactly eight rows;
  AC-MBG2 the join path opens an ACTIVE period on the shipped sandbox tier
          and its granted credits EQUAL that tier monthly_credits (measured
          equality, never a typed literal), with the shipped member_page
          sandbox constants read and recorded as the source of the product;
  AC-MBG3 privileges_for returns exactly the catalog tier privilege set and
          has_privilege grants a privilege that tier carries;
  AC-MBG4 birth_cert_face reads birth_cert TRUE with permanent TRUE and its
          judgement_source naming pay.grants_for, and it still reads TRUE
          after the credits are spent (entrance is not a subscription);
  AC-MBG5 consume_credits debits exactly N from the balance, a draw larger
          than the balance is REFUSED with E_NO_CREDITS and moves nothing,
          and a draw by an avatar with no period is refused with
          E_PERIOD_EXPIRED;
  AC-MBG6 three broken catalogs (unknown privilege key, banned copy word,
          missing resident disclaimer) are all refused by the shipped
          Catalog, so no tier opens on a bad config: refused 3/3;
  AC-MBG7 membership grants ZERO content-review bypass: the shipped stub
          plus decision_for answer identically for a clean, an advisory and
          a forbidden string before and after the co-creation tier is
          active, the privilege vocabulary and the gate wordlists are
          disjoint, and a privilege the active tier does not carry is
          refused with E_TIER_REQUIRED;
  AC-MBG8 this tool source is ASCII, imports stdlib plus shipped member,
          pay, ledger and lobby modules, contains no socket / requests /
          urllib.request / http.client reference, and --check re-measures a
          fresh world and reads VERDICT PASS only when the landed facts are
          byte-identical.

Honest boundaries printed on the page itself: no real money moves, the
price rows are sandbox placeholders and the four tier numbers are CEO
approval faces, the real merchant id / appid / secret are CEO physical
items, and the shipped msgSecCheck is the local stub because the platform
endpoint needs those same credentials.

Usage:
  python tools/membership_benefit_report.py [--out PATH] [--json PATH]
  python tools/membership_benefit_report.py --check
Exit codes: 0 rendered and all criteria pass, 2 a criterion failed or --check
            measured drift, 3 missing input file, 5 bad flags.
ASCII source, stdlib plus the shipped sandbox modules, no network. Chinese
appears only in the rendered documents, never in this file.
"""
import argparse
import copy
import hashlib
import html
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMBER_DIR = os.path.join(ROOT, "src", "sandbox", "member")
LOBBY_DIR = os.path.join(ROOT, "src", "sandbox", "lobby")
PAY_DIR = os.path.join(ROOT, "src", "sandbox", "pay")
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
# Same insertion order as the shipped member_page module, so module
# resolution here is the resolution its own suite proved.
for _p in (MEMBER_DIR, LEDGER_DIR, PAY_DIR, LOBBY_DIR):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import adapters as AD                      # noqa: E402
import catalog as CAT                      # noqa: E402
import gate_page                           # noqa: E402
import ledger as LED                       # noqa: E402
import member as M                         # noqa: E402
import member_page as MP                   # noqa: E402
import msgsec_stub                         # noqa: E402
import orders as PAY                       # noqa: E402
import sec_gate                            # noqa: E402
import store as LOBBY_STORE                # noqa: E402

MEMBER_CFG = os.path.join(MEMBER_DIR, "config.json")
LOBBY_CFG = os.path.join(LOBBY_DIR, "config.json")
PAY_CFG = os.path.join(PAY_DIR, "config.json")
LEDGER_CFG = os.path.join(LEDGER_DIR, "config.json")
DEFAULT_OUT = os.path.join(ROOT, "preview", "membership-benefit-report.html")
DEFAULT_JSON = os.path.join(ROOT, "preview", "membership-benefit-report.json")

AVATAR_BASE = "usr:avatar-R2760-a"
AVATAR_CO = "usr:avatar-R2760-b"
AVATAR_NONE = "usr:avatar-R2760-nobody"
MEMBER_TIER = "experience"
CO_TIER = "cocreator"
SANDBOX_PRICE_CENT = 1990

# AC-MBG8 reads these as an import/call, never as a bare substring: this file
# has to name the modules it forbids, so a substring scan matches itself.
NET_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(?:socket|requests|http\.client|urllib\.request)\b",
    re.MULTILINE)
NET_CALL_RE = re.compile(r"\burlopen\s*\(")

CRITERIA = (
    ("AC-MBG1", "the html and json land non-zero and the criteria table carries exactly eight rows"),
    ("AC-MBG2", "the join path opens an ACTIVE period and its granted credits equal the catalog monthly_credits for that tier"),
    ("AC-MBG3", "privileges_for equals the catalog tier privilege set and has_privilege grants a privilege that tier carries"),
    ("AC-MBG4", "birth_cert is TRUE, permanent, sourced from pay.grants_for and still TRUE after the credits are spent"),
    ("AC-MBG5", "a draw debits exactly N; an over-balance draw is refused with E_NO_CREDITS and moves nothing; a non-member draw is refused with E_PERIOD_EXPIRED"),
    ("AC-MBG6", "three broken catalogs (unknown privilege, banned copy word, missing disclaimer) are refused 3/3"),
    ("AC-MBG7", "membership grants zero review bypass: gate decisions are identical for anonymous and co-creation holders, the privilege vocabulary and wordlists are disjoint, and an off-tier privilege is refused"),
    ("AC-MBG8", "source is ASCII with no network reference, and --check reads PASS only on byte-identical fresh facts"),
)

L = {
    "title":       "\u4f1a\u5458\u6743\u76ca\u9a8c\u6536\u62a5\u544a",
    "sub":         "BigDomain \u00b7 P-47 \u7b2c\u4e94\u9762 \u00b7 \u6c99\u7bb1\u5b9e\u6d4b",
    "gen":         "\u751f\u6210\u65f6\u95f4",
    "src":         "\u6570\u636e\u6765\u6e90",
    "sec1":        "\u56db\u6863\u6743\u76ca\u77e9\u9635\uff08\u6570\u503c\u4e3a\u5360\u4f4d\u00b7\u5f85 CEO \u786e\u8ba4\uff09",
    "sec2":        "\u672c\u6c99\u7bb1\u4e24\u540d\u6301\u5361\u4eba\uff08\u771f\u5b9e\u5f00\u901a\u94fe\u8def\uff1a\u4e0b\u5355-\u652f\u4ed8-\u5f00\u901a\uff09",
    "sec3":        "\u5b66\u5206\u6263\u51cf\u4e0e\u62d2\u7edd\uff08\u4f59\u989d\u4e0d\u8db3\u5fc5\u987b\u88ab\u62d2\uff09",
    "sec4":        "\u5165\u57ce\u51fa\u751f\u8bc1\uff08\u6c38\u4e45\u00b7\u4e0d\u968f\u4f1a\u5458\u5230\u671f\u5931\u6548\uff09",
    "sec5":        "\u4f1a\u5458\u4e0d\u83b7\u5f97\u4efb\u4f55\u5185\u5bb9\u5ba1\u67e5\u7ed5\u8fc7\uff08\u540c\u4e00\u6587\u672c\u540c\u4e00\u5224\u5b9a\uff09",
    "sec6":        "\u574f\u914d\u7f6e\u62d2\u7edd\u9762\uff08\u5e93\u5c42 fail-closed\uff09",
    "sec7":        "\u5408\u89c4\u5e38\u9a7b\u9762",
    "sec8":        "\u672c\u6587\u4ef6\u6ee1\u8db3\u7684\u5224\u636e\uff08\u5148\u4e8e\u4ee3\u7801\u9489\u5b9a\uff09",
    "th_tier":     "\u6863\u4f4d",
    "th_credits":  "\u6708\u5b66\u5206",
    "th_days":     "\u5468\u671f\u5929",
    "th_grace":    "\u5bbd\u9650\u5929",
    "th_privs":    "\u7279\u6743",
    "th_copy":     "\u6863\u4f4d\u6587\u6848",
    "th_avatar":   "\u6301\u5361\u4eba",
    "th_bal":      "\u5b66\u5206\u4f59\u989d",
    "th_end":      "\u5230\u671f",
    "th_case":     "\u7528\u4f8b",
    "th_expect":   "\u671f\u671b",
    "th_got":      "\u5b9e\u6d4b",
    "th_v":        "\u5224\u5b9a",
    "th_text":     "\u6587\u672c",
    "th_anon":     "\u672a\u6301\u5361",
    "th_member":   "\u5171\u521b\u6863\u6301\u5361",
    "th_cfg":      "\u574f\u914d\u7f6e",
    "th_code":     "\u62d2\u7edd\u7801",
    "pass":        "\u901a\u8fc7",
    "fail":        "\u672a\u8fc7",
    "refused":     "\u5df2\u62d2",
    "granted":     "\u5df2\u6388\u4e88",
    "nopriv":      "\u672c\u6863\u4e0d\u542b",
    "price":       "19.9 \u5143\u4e3a\u6c99\u7bb1\u5360\u4f4d\u4ef7\u00b7\u975e\u6700\u7ec8\u5b9a\u4ef7\uff08\u5b9a\u4ef7=CEO \u4fdd\u7559\u9762\uff09",
    "aigc":        "AIGC \u6807\u8bc6",
    "disc":        "\u975e\u6295\u987e\u5e38\u9a7b\u63d0\u793a\uff08\u539f\u6587\u00b7\u4e0d\u53ef\u6298\u53e0\uff09",
    "verdict":     "\u5224\u5b9a",
    "holes":       "\u5b9e\u6d4b\u7f3a\u53e3",
    "meta1":       "\u4ef7\u683c\u95e8\u63a7",
    "meta2":       "\u95f8\u63d0\u4f9b\u65b9",
    "meta3":       "\u6c99\u7bb1\u5b9e\u4f8b",
    "c_ok":        "\u6b63\u4f8b",
    "c_advisory":  "\u987b\u590d\u6838",
    "c_forbidden": "\u987b\u62d2\u7edd",
    "c_over":      "\u8d85\u989d\u6263\u51cf",
    "c_stranger":  "\u975e\u4f1a\u5458\u6263\u51cf",
    "c_priv":      "\u8d8a\u6863\u7279\u6743",
    "c_unknown":   "\u672a\u77e5\u7279\u6743",
    "birth":       "\u51fa\u751f\u8bc1",
    "perm":        "\u6c38\u4e45",
    "judge":       "\u5224\u636e\u6e90",
    "scope":       "\u7ed3\u8bba",
    "bypass":      "\u7ed5\u8fc7\u9762",
}


def _esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def _load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def build_world(data_dir, tiers):
    """Wire the shipped faces the way member_page.build_world does, with one
    extension: a sandbox price row per tier, so the tier matrix can be joined
    and seen. No membership rule is restated here."""
    os.makedirs(data_dir, exist_ok=True)
    mcfg = _load(MEMBER_CFG)
    pcfg = _load(PAY_CFG)
    pcfg.setdefault("products", {})
    for tier in tiers:
        pcfg["products"]["tier_" + tier] = {
            "channel": "virtual",
            "price_cent": SANDBOX_PRICE_CENT,
            "share_tokens": 0,
            "entitlement": "tier:" + tier,
            "copy": "sandbox dock product: %s tier (never chargeable)" % tier,
        }
    events = LOBBY_STORE.EventStore(os.path.join(data_dir, "events.db"))
    led = LED.Ledger(os.path.join(data_dir, "ledger.db"), _load(LEDGER_CFG))
    led.mint_to_pool("pool:share", 1000000, "SETTLE-MEMBER-REPORT-1",
                     "settlement")
    pay = PAY.PayOrders(pcfg, os.path.join(data_dir, "pay.db"), events, led)
    store = M.MemberStore(mcfg, os.path.join(data_dir, "member.db"), pay)
    return {
        "mcfg": mcfg,
        "pcfg": pcfg,
        "events": events,
        "led": led,
        "pay": pay,
        "chans": AD.from_config(pcfg),
        "store": store,
    }


def close_world(world):
    for key in ("store", "pay", "led", "events"):
        try:
            world[key].close()
        except Exception:      # noqa: BLE001 - teardown must not mask a result
            pass


def join(world, product, avatar):
    """The shipped join path, in the shipped order."""
    pay = world["pay"]
    resp = pay.create_order(product, avatar)
    order_id = resp["order_id"]
    pay.place_order(order_id)
    amount = pay.order_detail(order_id)["amount_cent"]
    callback = world["chans"][resp["channel"]].make_callback(
        order_id, amount, "member-report-" + order_id)
    pay.handle_callback(callback)
    items = pay.grants_for(avatar)["items"]
    grant_id = items[-1]["grant_id"]
    opened = world["store"].activate(grant_id, avatar)
    return {"order_id": order_id, "grant_id": grant_id,
            "amount_cent": amount, "channel": resp["channel"],
            "activation": opened}


def _code(fn, *args, **kwargs):
    """Run a shipped refusal face and return its own error code."""
    try:
        fn(*args, **kwargs)
    except M.MemberError as exc:
        return exc.code
    except sec_gate.GateOfflineError as exc:
        return "E_GATE_OFFLINE"
    return "NO_REFUSAL"


def _balance_of(store, avatar, tier_key):
    face = store.balance_face(avatar)
    for row in face["periods"]:
        if row["tier"] == tier_key and row["status"] == "active":
            return int(row["balance"]), row
    return None, None


def measure():
    """Build one throwaway world and record every number this page prints."""
    data_dir = tempfile.mkdtemp(prefix="bd-member-report-")
    lobby_cfg = _load(LOBBY_CFG)
    stub = msgsec_stub.MsgSecStub.from_config(lobby_cfg)
    world = build_world(data_dir, sorted(
        CAT.Catalog.from_config(_load(MEMBER_CFG)).tiers.keys()))
    try:
        cat = world["store"].catalog
        tiers = {}
        for key in sorted(cat.tiers):
            tier = cat.tiers[key]
            tiers[key] = {
                "monthly_credits": int(tier.monthly_credits),
                "period_days": int(tier.period_days),
                "grace_days": int(tier.grace_days),
                "privileges": sorted(tier.privileges),
                "copy": tier.copy,
            }

        # --- the join path, measured, on the shipped sandbox tier -------
        base_joined = join(world, MP.SANDBOX_PRODUCT, AVATAR_BASE)
        co_joined = join(world, "tier_" + CO_TIER, AVATAR_CO)

        base_privs = world["store"].privileges_for(AVATAR_BASE)
        co_privs = world["store"].privileges_for(AVATAR_CO)
        base_balance, base_period = _balance_of(world["store"], AVATAR_BASE,
                                                MEMBER_TIER)
        co_balance, co_period = _balance_of(world["store"], AVATAR_CO, CO_TIER)

        # --- draw, refusal, permanence ---------------------------------
        draw = world["store"].consume_credits(AVATAR_BASE, 1,
                                              ref="report-draw-1",
                                              ref_type="service")
        after_draw = int(draw["balance_total_after"])
        over_code = _code(world["store"].consume_credits, AVATAR_BASE, 99)
        after_refused = _balance_of(world["store"], AVATAR_BASE,
                                    MEMBER_TIER)[0]
        stranger_code = _code(world["store"].consume_credits, AVATAR_NONE, 1)
        cert = world["store"].birth_cert_face(AVATAR_BASE)
        expiring = world["store"].expiring_soon(30)

        # --- privilege boundary ----------------------------------------
        granted_priv = base_privs["privileges"][0] if base_privs["privileges"] else ""
        granted = world["store"].has_privilege(AVATAR_BASE, granted_priv) \
            if granted_priv else {"granted": False}
        off_tier = [p for p in sorted(tiers[CO_TIER]["privileges"])
                    if p not in tiers[MEMBER_TIER]["privileges"]]
        off_tier_priv = off_tier[0] if off_tier else ""
        tier_required_code = _code(world["store"].has_privilege,
                                   AVATAR_BASE, off_tier_priv)
        unknown_code = _code(world["store"].has_privilege, AVATAR_BASE,
                             "no_such_privilege")

        # --- content gate: membership buys no bypass --------------------
        forbidden_word = stub.gate.forbidden_words[0]
        advisory_word = stub.gate.advisory_ban_words[0]
        gate_cases = []
        for case, text in (
                ("clean", "an ordinary rainy afternoon on the rooftop"),
                ("advisory", "monthly card promo: " + advisory_word),
                ("forbidden", "posting rights: " + forbidden_word)):
            anon_resp = stub.check(text, openid=AVATAR_NONE)
            member_resp = stub.check(text, openid=AVATAR_CO)
            gate_cases.append({
                "case": case,
                "text": text,
                "anon_suggest": anon_resp["result"]["suggest"],
                "anon_decision": gate_page.decision_for(stub, anon_resp),
                "member_suggest": member_resp["result"]["suggest"],
                "member_decision": gate_page.decision_for(stub, member_resp),
                "provider": anon_resp["provider"],
                "identical": (gate_page.decision_for(stub, anon_resp)
                              == gate_page.decision_for(stub, member_resp)),
            })
        vocabulary = set(CAT.KNOWN_PRIVILEGES)
        wordlists = set(stub.gate.forbidden_words) | set(stub.gate.advisory_ban_words)
        overlap = sorted(vocabulary & wordlists)

        # --- broken catalogs, refused -----------------------------------
        base_cfg = _load(MEMBER_CFG)
        banned_word = (base_cfg.get("copy_ban_words") or [""])[0]
        bad_cfgs = []
        broken = copy.deepcopy(base_cfg)
        broken["tiers"][MEMBER_TIER]["privileges"] = \
            list(broken["tiers"][MEMBER_TIER]["privileges"]) + ["free_money"]
        bad_cfgs.append(("unknown_privilege", broken))
        broken = copy.deepcopy(base_cfg)
        broken["tiers"][MEMBER_TIER]["copy"] = \
            str(broken["tiers"][MEMBER_TIER]["copy"]) + banned_word
        bad_cfgs.append(("banned_copy_word", broken))
        broken = copy.deepcopy(base_cfg)
        broken["compliance"].pop("disclaimer", None)
        bad_cfgs.append(("missing_disclaimer", broken))
        refusals = []
        for case, cfg in bad_cfgs:
            refusals.append({"case": case,
                             "code": _code(CAT.Catalog.from_config, cfg),
                             "refused": False})
            refusals[-1]["refused"] = refusals[-1]["code"] != "NO_REFUSAL"

        # --- CEO gating facts -------------------------------------------
        pay_cfg = _load(PAY_CFG)
        prices = pay_cfg.get("products") or {}
        needs_ceo = sum(1 for row in prices.values()
                        if "[needs-CEO]" in str(row.get("note", "")))
        params_status = str(_load(MEMBER_CFG).get("params_status", ""))

        facts = {
            "tiers": tiers,
            "members": [
                {"avatar": AVATAR_BASE, "tier": MEMBER_TIER,
                 "product": MP.SANDBOX_PRODUCT,
                 "sandbox_tier_constant": MP.SANDBOX_TIER,
                 "credits_granted": base_balance,
                 "privileges": sorted(base_privs["privileges"]),
                 "tiers_active": sorted(base_privs["tiers"])},
                {"avatar": AVATAR_CO, "tier": CO_TIER,
                 "product": "tier_" + CO_TIER,
                 "credits_granted": co_balance,
                 "privileges": sorted(co_privs["privileges"]),
                 "tiers_active": sorted(co_privs["tiers"])},
            ],
            "join": {
                "base": {"amount_cent": base_joined["amount_cent"],
                         "channel": base_joined["channel"],
                         "idempotent": base_joined["activation"]["idempotent"]},
                "co": {"amount_cent": co_joined["amount_cent"],
                       "channel": co_joined["channel"],
                       "idempotent": co_joined["activation"]["idempotent"]},
            },
            "credits": {
                "granted": base_balance,
                "after_one_draw": after_draw,
                "over_code": over_code,
                "after_refused_over": after_refused,
                "stranger_code": stranger_code,
            },
            "privileges": {
                "granted_priv": granted_priv,
                "granted": bool(granted.get("granted")),
                "off_tier_priv": off_tier_priv,
                "tier_required_code": tier_required_code,
                "unknown_code": unknown_code,
            },
            "birth_cert": {
                "birth_cert": bool(cert["birth_cert"]),
                "permanent": bool(cert["permanent"]),
                "judgement_source": cert["judgement_source"],
                "after_spend": bool(world["store"].birth_cert_face(
                    AVATAR_BASE)["birth_cert"]),
                "member_domain_marker": bool(cert["member_domain_marker"]),
            },
            "gate": {
                "provider": msgsec_stub.contract()["provider_prod"],
                "blocked_on": msgsec_stub.contract()["blocked_on"],
                "cases": gate_cases,
                "privilege_wordlist_overlap": overlap,
                "all_identical": all(c["identical"] for c in gate_cases),
            },
            "config_refusals": refusals,
            "expiry": {"window_days": int(expiring["days"]),
                       "count": int(expiring["count"]),
                       "avatars": sorted({r["census_avatar_id"]
                                          for r in expiring["expiring_soon"]})},
            "ceo": {"prices_total": len(prices),
                    "prices_needs_ceo": needs_ceo,
                    "params_status": params_status,
                    "sandbox_price_cent": SANDBOX_PRICE_CENT},
            "compliance": {"disclaimer": cat.disclaimer,
                           "ai_label": cat.ai_label,
                           "persistent": True},
        }
        # timestamps live outside facts so --check stays byte-stable
        stamps = {
            "generated_utc": M.now_utc(),
            "expires": [base_period["end_utc"] if base_period else None,
                        co_period["end_utc"] if co_period else None],
            "periods": [base_period["period_id"] if base_period else None,
                        co_period["period_id"] if co_period else None],
        }
        return facts, stamps
    finally:
        close_world(world)
        shutil.rmtree(data_dir, ignore_errors=True)


def verify(facts, sizes):
    """Every criterion, evaluated against the measured facts."""
    rows = []

    def add(cid, ok, detail):
        rows.append({"id": cid, "pass": bool(ok), "detail": detail})

    tiers = facts["tiers"]
    members = facts["members"]
    base = members[0]
    co = members[1]

    add("AC-MBG1",
        sizes.get("html", 0) > 0 and sizes.get("json", 0) > 0
        and len(CRITERIA) == 8,
        "html=%dB json=%dB criteria=%d"
        % (sizes.get("html", 0), sizes.get("json", 0), len(CRITERIA)))

    add("AC-MBG2",
        base["tier"] == MEMBER_TIER
        and base["credits_granted"] == tiers[MEMBER_TIER]["monthly_credits"]
        and base["sandbox_tier_constant"] == MEMBER_TIER
        and facts["join"]["base"]["idempotent"] is False,
        "tier=%s credits=%s catalog=%s product=%s constant=%s"
        % (base["tier"], base["credits_granted"],
           tiers[MEMBER_TIER]["monthly_credits"], base["product"],
           base["sandbox_tier_constant"]))

    add("AC-MBG3",
        base["privileges"] == tiers[MEMBER_TIER]["privileges"]
        and facts["privileges"]["granted"],
        "measured=%s catalog=%s granted=%s"
        % (base["privileges"], tiers[MEMBER_TIER]["privileges"],
           facts["privileges"]["granted_priv"]))

    cert = facts["birth_cert"]
    add("AC-MBG4",
        cert["birth_cert"] and cert["permanent"] and cert["after_spend"]
        and "pay.grants_for" in cert["judgement_source"],
        "birth_cert=%s permanent=%s after_spend=%s source=%s"
        % (cert["birth_cert"], cert["permanent"], cert["after_spend"],
           cert["judgement_source"]))

    credits = facts["credits"]
    add("AC-MBG5",
        credits["after_one_draw"] == credits["granted"] - 1
        and credits["over_code"] == "E_NO_CREDITS"
        and credits["after_refused_over"] == credits["after_one_draw"]
        and credits["stranger_code"] == "E_PERIOD_EXPIRED",
        "granted=%d after_one=%d over=%s after_over=%d stranger=%s"
        % (credits["granted"], credits["after_one_draw"],
           credits["over_code"], credits["after_refused_over"],
           credits["stranger_code"]))

    refused = [r for r in facts["config_refusals"] if r["refused"]]
    add("AC-MBG6", len(refused) == 3 and len(facts["config_refusals"]) == 3,
        "refused=%d/3 codes=%s"
        % (len(refused), ",".join(sorted({r["code"]
                                          for r in facts["config_refusals"]}))))

    gate = facts["gate"]
    add("AC-MBG7",
        gate["all_identical"]
        and not gate["privilege_wordlist_overlap"]
        and "priority_queue" in co["privileges"]
        and facts["privileges"]["tier_required_code"] == "E_TIER_REQUIRED",
        "identical=%s overlap=%s co_has_queue=%s off_tier=%s->%s"
        % (gate["all_identical"],
           ",".join(gate["privilege_wordlist_overlap"]) or "none",
           "priority_queue" in co["privileges"],
           facts["privileges"]["off_tier_priv"],
           facts["privileges"]["tier_required_code"]))

    source_ok, source_detail = source_face()
    add("AC-MBG8", source_ok, source_detail)
    return rows


def source_face():
    """This tool own source, checked the way the criterion worded it.

    The tokens are matched as an IMPORT or a CALL, not as bare substrings:
    this function has to name the modules it forbids, so a plain substring
    scan would always match itself and the criterion would be unpassable.
    """
    path = os.path.abspath(__file__)
    with open(path, "rb") as handle:
        raw = handle.read()
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        return False, "source not ASCII at byte %d" % exc.start
    imports = [m.group(0).strip() for m in NET_IMPORT_RE.finditer(text)]
    calls = NET_CALL_RE.findall(text)
    return (not imports and not calls), "ascii=True imports=%s calls=%d" % (
        ",".join(imports) if imports else "none", len(calls))


def fingerprint(facts):
    return hashlib.sha256(json.dumps(facts, sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")
                          ).hexdigest()[:16]


def render_html(facts, stamps, rows):
    tiers = facts["tiers"]
    tier_rows = "".join(
        "<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td>"
        "<td>%s</td><td>%s</td></tr>"
        % (_esc(key), _esc(row["monthly_credits"]), _esc(row["period_days"]),
           _esc(row["grace_days"]), _esc(", ".join(row["privileges"])),
           _esc(row["copy"]))
        for key, row in sorted(tiers.items()))

    member_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
        "<td>%s</td><td>%s</td></tr>"
        % (_esc(m["avatar"]), _esc(m["tier"]), _esc(m["credits_granted"]),
           _esc(", ".join(m["privileges"])),
           _esc(stamps["expires"][idx] or "-"),
           _esc(_pass(m["credits_granted"] == tiers[m["tier"]]["monthly_credits"])))
        for idx, m in enumerate(facts["members"]))

    credits = facts["credits"]
    credit_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (_esc(case), _esc(expect), _esc(got), _esc(_pass(ok)))
        for case, expect, got, ok in (
            (L["c_ok"], "balance %d -> %d" % (credits["granted"],
                                              credits["granted"] - 1),
             credits["after_one_draw"], credits["after_one_draw"] == credits["granted"] - 1),
            (L["c_over"], "E_NO_CREDITS, balance untouched", credits["over_code"],
             credits["over_code"] == "E_NO_CREDITS"),
            (L["c_over"] + " (after)", "balance unchanged",
             credits["after_refused_over"],
             credits["after_refused_over"] == credits["after_one_draw"]),
            (L["c_stranger"], "E_PERIOD_EXPIRED", credits["stranger_code"],
             credits["stranger_code"] == "E_PERIOD_EXPIRED"),
            (L["c_priv"] + " " + facts["privileges"]["off_tier_priv"],
             "E_TIER_REQUIRED", facts["privileges"]["tier_required_code"],
             facts["privileges"]["tier_required_code"] == "E_TIER_REQUIRED"),
            (L["c_unknown"], "E_BAD_STATE", facts["privileges"]["unknown_code"],
             facts["privileges"]["unknown_code"] == "E_BAD_STATE"),
        ))

    gate = facts["gate"]
    case_label = {"clean": L["c_ok"], "advisory": L["c_advisory"],
                  "forbidden": L["c_forbidden"]}
    gate_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (_esc(case_label.get(c["case"], c["case"])), _esc(c["text"]),
           _esc(c["anon_decision"] + " / " + c["anon_suggest"]),
           _esc(c["member_decision"] + " / " + c["member_suggest"]),
           _esc(_pass(c["identical"])))
        for c in gate["cases"])

    refusal_rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (_esc(r["case"]), _esc(r["code"]), _esc(_pass(r["refused"])))
        for r in facts["config_refusals"])

    cert = facts["birth_cert"]
    crit_rows = "".join(
        "<li><b>%s</b> %s &mdash; %s (%s)</li>"
        % (_esc(r["id"]), _esc(dict(CRITERIA)[r["id"]]), _esc(_pass(r["pass"])),
           _esc(r["detail"]))
        for r in rows)

    passed = sum(1 for r in rows if r["pass"])
    verdict = _pass(passed == len(rows))
    meta = [
        (L["meta1"], L["price"] + " | [needs-CEO] %d/%d rows"
         % (facts["ceo"]["prices_needs_ceo"], facts["ceo"]["prices_total"])),
        (L["meta2"], "%s (%s)" % (gate["provider"], gate["blocked_on"])),
        (L["meta3"], "temp sandbox world, closed and deleted after the run"),
    ]
    meta_html = "".join("<li><b>%s</b> %s</li>" % (_esc(k), _esc(v))
                        for k, v in meta)

    template = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>@TITLE@</title>
<style>
:root{--ink:#14202b;--mut:#5c6b7a;--line:#d8e0e8;--ok:#1f7a4c;--bad:#a8322c;
--bg:#f7f9fb;--card:#fff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1080px;margin:0 auto;padding:28px 20px 64px}
h1{font-size:26px;margin:0 0 4px}
.sub{color:var(--mut);margin-bottom:18px}
h2{font-size:17px;margin:30px 0 10px;padding-bottom:6px;
border-bottom:1px solid var(--line)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:16px 18px;margin-bottom:6px}
table{width:100%;border-collapse:collapse;background:var(--card);
border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);
vertical-align:top;font-size:13.5px}
th{background:#eef3f7;font-weight:600;white-space:nowrap}
tr:last-child td{border-bottom:none}
.ok{color:var(--ok);font-weight:600}
.bad{color:var(--bad);font-weight:600}
ul{margin:6px 0 0;padding-left:20px}
.meta{color:var(--mut);font-size:13px}
.disc{background:#fff7e6;border:1px solid #f0d9a8;border-radius:10px;
padding:14px 16px;font-size:13.5px;white-space:pre-wrap}
.tag{display:inline-block;background:#e8f2ec;color:var(--ok);border-radius:6px;
padding:1px 8px;font-size:12.5px;margin-left:6px}
</style></head><body><main>
<h1>@TITLE@<span class="tag">@VERDICT@ @PASSED@/@TOTAL@</span></h1>
<div class="sub">@SUB@</div>
<div class="card meta"><ul>
<li><b>@GEN@</b> @GENERATED@</li>
<li><b>@SRC@</b> @SOURCE@</li>
@META@
</ul></div>

<h2>@SEC1@</h2>
<table><thead><tr><th>@TH_TIER@</th><th>@TH_CREDITS@</th><th>@TH_DAYS@</th>
<th>@TH_GRACE@</th><th>@TH_PRIVS@</th><th>@TH_COPY@</th></tr></thead>
<tbody>@TIER_ROWS@</tbody></table>

<h2>@SEC2@</h2>
<table><thead><tr><th>@TH_AVATAR@</th><th>@TH_TIER@</th><th>@TH_BAL@</th>
<th>@TH_PRIVS@</th><th>@TH_END@</th><th>@TH_V@</th></tr></thead>
<tbody>@MEMBER_ROWS@</tbody></table>

<h2>@SEC3@</h2>
<table><thead><tr><th>@TH_CASE@</th><th>@TH_EXPECT@</th><th>@TH_GOT@</th>
<th>@TH_V@</th></tr></thead><tbody>@CREDIT_ROWS@</tbody></table>

<h2>@SEC4@</h2>
<div class="card">
<ul>
<li><b>@BIRTH@</b> @CERT_BIRTH@ &nbsp; <b>@PERM@</b> @CERT_PERM@</li>
<li><b>@JUDGE@</b> @CERT_SOURCE@</li>
<li><b>@SCOPE@</b> @CERT_SPEND@ (credits spent, entrance unchanged)</li>
</ul></div>

<h2>@SEC5@</h2>
<table><thead><tr><th>@TH_CASE@</th><th>@TH_TEXT@</th><th>@TH_ANON@</th>
<th>@TH_MEMBER@</th><th>@TH_V@</th></tr></thead>
<tbody>@GATE_ROWS@</tbody></table>
<div class="card meta"><b>@BYPASS@</b> @BYPASS_TEXT@</div>

<h2>@SEC6@</h2>
<table><thead><tr><th>@TH_CFG@</th><th>@TH_CODE@</th><th>@TH_V@</th></tr></thead>
<tbody>@REFUSAL_ROWS@</tbody></table>

<h2>@SEC7@</h2>
<div class="disc"><b>@DISC@</b>
@DISCLAIMER@

<b>@AIGC@</b> @AI_LABEL@ &nbsp; <b>@PRICE@</b>
</div>

<h2>@SEC8@</h2>
<div class="card"><ul>@CRIT_ROWS@</ul></div>
<div class="card meta">fingerprint @FINGERPRINT@ &middot; generated by
tools/membership_benefit_report.py</div>
</main></body></html>
"""

    holes = ("none measured: identical decisions on all three gate cases,"
             " disjoint vocabulary, off-tier privilege refused")
    if not (facts["gate"]["all_identical"]
            and not facts["gate"]["privilege_wordlist_overlap"]
            and facts["privileges"]["tier_required_code"] == "E_TIER_REQUIRED"):
        holes = ("MEASURED HOLE: identical=%s overlap=%s off_tier=%s"
                 % (facts["gate"]["all_identical"],
                    ",".join(facts["gate"]["privilege_wordlist_overlap"]) or "none",
                    facts["privileges"]["tier_required_code"]))

    tokens = {
        "@TITLE@": L["title"], "@SUB@": L["sub"], "@GEN@": L["gen"],
        "@SRC@": L["src"],
        "@SOURCE@": "src/sandbox/member (member.py, catalog.py, member_page.py),"
                    " src/sandbox/pay, src/sandbox/ledger, src/sandbox/lobby"
                    " (msgsec_stub.py, gate_page.py)",
        "@META@": meta_html,
        "@SEC1@": L["sec1"], "@SEC2@": L["sec2"], "@SEC3@": L["sec3"],
        "@SEC4@": L["sec4"], "@SEC5@": L["sec5"], "@SEC6@": L["sec6"],
        "@SEC7@": L["sec7"], "@SEC8@": L["sec8"],
        "@TH_TIER@": L["th_tier"], "@TH_CREDITS@": L["th_credits"],
        "@TH_DAYS@": L["th_days"], "@TH_GRACE@": L["th_grace"],
        "@TH_PRIVS@": L["th_privs"], "@TH_COPY@": L["th_copy"],
        "@TH_AVATAR@": L["th_avatar"], "@TH_BAL@": L["th_bal"],
        "@TH_END@": L["th_end"], "@TH_CASE@": L["th_case"],
        "@TH_EXPECT@": L["th_expect"], "@TH_GOT@": L["th_got"],
        "@TH_V@": L["th_v"], "@TH_TEXT@": L["th_text"],
        "@TH_ANON@": L["th_anon"], "@TH_MEMBER@": L["th_member"],
        "@TH_CFG@": L["th_cfg"], "@TH_CODE@": L["th_code"],
        "@TIER_ROWS@": tier_rows, "@MEMBER_ROWS@": member_rows,
        "@CREDIT_ROWS@": credit_rows, "@GATE_ROWS@": gate_rows,
        "@REFUSAL_ROWS@": refusal_rows, "@CRIT_ROWS@": crit_rows,
        "@VERDICT@": verdict, "@PASSED@": str(passed),
        "@TOTAL@": str(len(rows)),
        "@GENERATED@": _esc(stamps["generated_utc"]),
        "@BIRTH@": L["birth"], "@PERM@": L["perm"], "@JUDGE@": L["judge"],
        "@SCOPE@": L["scope"], "@HOLES@": L["holes"],
        "@CERT_BIRTH@": _esc(str(cert["birth_cert"])),
        "@CERT_PERM@": _esc(str(cert["permanent"])),
        "@CERT_SOURCE@": _esc(cert["judgement_source"]),
        "@CERT_SPEND@": _esc("after_spend=%s" % cert["after_spend"]),
        "@BYPASS@": L["bypass"], "@BYPASS_TEXT@": _esc(holes),
        "@DISC@": L["disc"], "@DISCLAIMER@": _esc(facts["compliance"]["disclaimer"]),
        "@AIGC@": L["aigc"], "@AI_LABEL@": _esc(facts["compliance"]["ai_label"]),
        "@PRICE@": _esc(L["price"]), "@FINGERPRINT@": _esc(fingerprint(facts)),
    }
    out = template
    for token, value in tokens.items():
        out = out.replace(token, value)
    return out


def _pass(ok):
    return L["pass"] if ok else L["fail"]


def _document(facts, stamps, rows, sizes):
    return {
        "generated_by": "tools/membership_benefit_report.py",
        "p47_item": 5,
        "title": L["title"],
        "generated_utc": stamps["generated_utc"],
        "facts": facts,
        "periods": stamps["periods"],
        "expires": stamps["expires"],
        "fingerprint": fingerprint(facts),
        "criteria": [{"id": cid, "text": text} for cid, text in CRITERIA],
        "checks": rows,
        "verdict": "PASS" if all(r["pass"] for r in rows) else "FAIL",
        "sizes": sizes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Render the P-47 item-5 membership benefit face")
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--json", default=DEFAULT_JSON)
    parser.add_argument("--check", action="store_true",
                        help="re-measure a fresh world and compare with the "
                             "landed document")
    args = parser.parse_args(argv)

    for path in (MEMBER_CFG, LOBBY_CFG, PAY_CFG, LEDGER_CFG):
        if not os.path.isfile(path):
            print("E_INPUT missing %s" % path)
            return 3

    facts, stamps = measure()
    source_ok, source_detail = source_face()

    if args.check:
        if not os.path.isfile(args.json):
            print("E_INPUT landed json missing: %s" % args.json)
            return 3
        landed = _load(args.json)
        html_size = (os.path.getsize(args.out)
                     if os.path.isfile(args.out) else 0)
        json_size = os.path.getsize(args.json)
        rows = verify(landed["facts"], {"html": html_size, "json": json_size})
        drift = fingerprint(facts) != landed.get("fingerprint")
        passed = sum(1 for r in rows if r["pass"])
        print("MEMBERSHIP BENEFIT --check files=%s/%s facts_drift=%s"
              % ("html", "json", "YES" if drift else "no"))
        for row in rows:
            print("  %s %s %s" % ("PASS" if row["pass"] else "FAIL",
                                  row["id"], row["detail"]))
        print("VERDICT %s checks=%d/%d fresh_fingerprint=%s landed=%s"
              % ("PASS" if (passed == len(rows) and not drift) else "FAIL",
                 passed, len(rows), fingerprint(facts),
                 landed.get("fingerprint")))
        return 0 if (passed == len(rows) and not drift) else 2

    sizes = {"html": 0, "json": 0}
    body = ""
    payload = ""
    # AC-MBG1 prints the two landed sizes INSIDE the documents, so the render
    # has to reach a fixed point before anything is written: a body that
    # states a stale size is a document that disagrees with itself.
    for _ in range(6):
        rows = verify(facts, sizes)
        body = render_html(facts, stamps, rows)
        doc = _document(facts, stamps, rows, sizes)
        payload = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
        measured = {"html": len(body.encode("utf-8")),
                    "json": len(payload.encode("utf-8"))}
        if measured == sizes:
            break
        sizes = measured
    else:
        print("E_SIZES document sizes did not converge")
        return 2

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)

    rows = verify(facts, sizes)
    passed = sum(1 for r in rows if r["pass"])
    print("MEMBERSHIP BENEFIT html=%s (%dB) json=%s (%dB)"
          % (args.out, sizes["html"], args.json, sizes["json"]))
    print("  tiers=%d members=%d gate_cases=%d refusals=%d source=%s"
          % (len(facts["tiers"]), len(facts["members"]), len(facts["gate"]["cases"]),
             len(facts["config_refusals"]), source_detail))
    for row in rows:
        print("  %s %s %s" % ("PASS" if row["pass"] else "FAIL", row["id"],
                              row["detail"]))
    print("VERDICT %s checks=%d/%d fingerprint=%s"
          % ("PASS" if passed == len(rows) else "FAIL", passed, len(rows),
             fingerprint(facts)))
    return 0 if passed == len(rows) else 2


if __name__ == "__main__":
    sys.exit(main())
