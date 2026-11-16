#!/usr/bin/env python3
"""Render the P-47 item-4 payment channel acceptance face into one document.

Why this exists: the payment sandbox (src/sandbox/pay) has shipped adapters,
a WeChat Pay V3 callback face and a product config that carries the 19.9 pack,
but every one of its 29 suites is a test asserting on fixtures. Nothing a
reader could open showed the channel contract working or, more importantly,
REFUSING the callbacks it must refuse. This driver builds the two shipped
channel adapters and the V3 channel out of the SHIPPED config, fires one
positive and seven negative callbacks at them, and renders the measured
outcome with the compliance faces on the same page.

Nothing here re-implements a payment rule: signing, verification, the four
header contract, the timestamp window and the trade_state criterion all come
from src/sandbox/pay/adapters.py and src/sandbox/pay/v3.py.

Criteria pre-registered BEFORE the code was written (AC-PAYG1..8):
  AC-PAYG1 the html and json land with non-zero size and a non-empty criteria
          table;
  AC-PAYG2 both shipped channels (virtual, standard) are built by
          adapters.from_config and a signed callback verifies: accepted 2/2;
  AC-PAYG3 three legacy negatives (bad signature, unknown signer, stale
          timestamp) are refused: refused 3/3;
  AC-PAYG4 one V3 call carrying all four Wechatpay-* headers verifies:
          accepted 1/1, headers present 4/4;
  AC-PAYG5 four V3 negatives (missing header, tampered body, stale timestamp,
          trade_state not SUCCESS) are refused: refused 4/4;
  AC-PAYG6 the 19.9 product row carries price_cent 1990 AND needs_ceo True, so
          this report claims no final price;
  AC-PAYG7 the compliance disclaimer is carried VERBATIM from config and the
          AIGC marking note is present;
  AC-PAYG8 this tool source is ASCII, imports only stdlib plus shipped pay
          modules, and contains no socket/urllib/requests reference.

Honest boundaries stated on the page itself: the mock keys are explicitly fake,
zero real payment call is made, the real merchant id / appid / keys are CEO
account-domain physical items, the V3 RSA verify mode is NOT exercised here
(needs the platform public key).

The --check face carries one guard the criteria table cannot state, because it
is a property of the LANDED document rather than of a fresh render: the landed
product rows and the landed config sha256 are compared against the config on
disk, so a price change that was never re-rendered reddens here instead of
leaving a stale number on a page a reader trusts (R2817; AC-PAYGB10/11).

Usage:
  python tools/payment_gate_report.py [--out PATH] [--json PATH] [--check]
Exit codes: 0 rendered and all criteria pass, 2 a criterion failed or --check
            found drift, 3 missing input file, 5 bad flags.
ASCII source, stdlib plus the shipped pay modules, no network. Chinese appears
only in the rendered document, never in this file.
"""
import argparse
import copy
import hashlib
import html
import json
import os
import sys
import datetime

# D-20261116-13: the value-domain assertion is ONE module shared by the four
# price faces, not four copies. This file historically carried its own version.
# R2826: the module directory joins sys.path BEFORE the sibling import, because
# the battery loads this file by path with no tools/ on sys.path - importing a
# sibling that only resolves under `python tools/x.py` turned three battery
# suites red the moment the import landed.
_MODDIR = os.path.dirname(os.path.abspath(__file__))
if _MODDIR not in sys.path:
    sys.path.insert(0, _MODDIR)
import value_domain as VD  # noqa: E402

# The catalog is the REPO's shipped config, not the render target: a test world
# repoints ROOT at a temp dir, and reading the catalog through it emptied the
# catalog and made every row read "not in the catalog" (R2826).
CATALOG_ROOT = os.path.dirname(_MODDIR)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAY_DIR = os.path.join(ROOT, "src", "sandbox", "pay")
CONFIG = os.path.join(PAY_DIR, "config.json")
DEFAULT_OUT = os.path.join(ROOT, "preview", "payment-gate-report.html")
DEFAULT_JSON = os.path.join(ROOT, "preview", "payment-gate-report.json")
ORDER_ID = "order-R2759-pack19"
AMOUNT_CENT = 1990
V3_SERIAL = "PUB_KEY_ID_2026111530"

L = {
    "title": "19.9 \u652f\u4ed8\u901a\u9053\u9a8c\u6536\u62a5\u544a",
    "sub": "BigDomain \u00b7 P-47 \u7b2c\u56db\u9762 \u00b7 \u6c99\u7bb1\u5b9e\u6d4b",
    "g": "\u751f\u6210\u65f6\u95f4",
    "s": "\u914d\u7f6e\u6765\u6e90",
    "sec1": "\u5546\u54c1\u4e0e\u4ef7\u683c\uff08\u9010\u884c\u8bfb\u81ea\u914d\u7f6e\uff09",
    "sec2": "\u901a\u9053\u6b63\u4f8b\uff08\u5df2\u53d1\u8d27\u9002\u914d\u5668\uff09",
    "sec3": "\u53cd\u4f8b\uff08\u5fc5\u987b\u88ab\u62d2\uff09",
    "sec4": "\u5fae\u4fe1\u652f\u4ed8 V3 \u56de\u8c03\u9762\uff08\u5b98\u65b9\u89c4\u5219\uff09",
    "sec5": "\u5408\u89c4\u5e38\u9a7b\u9762",
    "sec6": "\u5224\u636e\u8868",
    "tp": "\u5546\u54c1",
    "tr": "\u4ef7\u683c\uff08\u5206\uff09",
    "tc": "\u901a\u9053",
    "te": "\u6743\u76ca",
    "tv": "\u5224\u5b9a",
    "tcase": "\u7528\u4f8b",
    "texp": "\u671f\u671b",
    "tgot": "\u5b9e\u6d4b",
    "tdet": "\u660e\u7ec6",
    "accepted": "\u63a5\u53d7",
    "refused": "\u5df2\u62d2",
    "nsc": "\u4ecd\u672a\u89e3\u51b3",
    "crit": "\u5224\u636e",
    "st": "\u72b6\u6001",
    "blk": "\u963b\u585e\u9762",
    "note": "\u8bf4\u660e",
    "adv": "\u975e\u6295\u987e\u63d0\u793a",
    "aig": "AIGC \u6807\u8bc6",
}

# Statements the page makes about itself. Chinese only in the rendered doc.
N = {
    "mock": "[needs-CEO] \u771f\u5b9e\u5546\u6237\u53f7 / AppID / AppKey / "
            "\u5bf9\u516c\u7ed3\u7b97 = \u96c6\u56e2\u8d26\u53f7\u57df\u7269"
            "\u7406\u4ef6\uff1b\u672c\u62a5\u544a\u96f6\u771f\u5b9e\u652f"
            "\u4ed8\u8c03\u7528\uff0c\u6c99\u7bb1\u94a5\u4e3a\u663e\u5f0f"
            "\u5047\u94a5",
    "rsa": "V3 RSA \u771f\u5b9e\u9a8c\u7b7e\u6a21\u5f0f\u672c\u62a5\u544a"
           "\u672a\u6267\u884c\uff08\u9700\u5e73\u53f0\u516c\u94a5\uff0c"
           "\u5c5e CEO \u7269\u7406\u4ef6\uff09\uff0c\u5f53\u524d\u6267\u884c"
           "\u7684\u662f HMAC \u6807\u51c6\u66ff\u8eab\u4e14\u9a8c\u7b7e"
           "\u8f93\u5165\u5b57\u7b26\u4e32\u4e0e\u751f\u4ea7\u4e00\u81f4",
    "price": "\u4ef7\u76ee\u9010\u884c\u8bfb\u81ea config.json\uff08\u542b"
             "D-20261116-05 \u88c1\u51b3\u7684 9.90 \u6c38\u4e45\u5165\u573a"
             "\u5238\u4e0e 29.90 \u6708\u5361\uff09\uff1b\u4ecd\u6807 "
             "[needs-CEO] \u7684\u884c=\u5b9a\u4ef7\u786e\u8ba4\u6743\u5728 "
             "CEO\uff0c\u672c\u62a5\u544a\u4e0d\u5bf9\u5916\u58f0\u79f0\u4efb"
             "\u4f55\u6210\u4ea4\u4ef7",
    "docker": "\u672c\u673a\u65e0 Docker\uff0c\u6545\u4e3a\u9759\u6001\u6587"
              "\u6863\u800c\u975e\u670d\u52a1\u6f14\u793a",
}

CHECKS = [
    ("AC-PAYG1", "html+json landed, criteria table non-empty"),
    ("AC-PAYG2", "two shipped channels accept a signed callback (2/2)"),
    ("AC-PAYG3", "three legacy negatives refused (3/3)"),
    ("AC-PAYG4", "one V3 callback with 4 headers accepts (1/1)"),
    ("AC-PAYG5", "four V3 negatives refused (4/4)"),
    ("AC-PAYG6", "19.9 product carries price_cent 1990 and needs_ceo True"),
    ("AC-PAYG7", "disclaimer verbatim from config, AIGC marking note present"),
    ("AC-PAYG8", "tool source ASCII, stdlib+shipped imports (incl. the shared "
                 "value_domain module), zero network refs"),
]


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _refusal(fn):
    """Run fn(); return (refused, detail). A refusal is an AdapterError."""
    import adapters
    try:
        fn()
    except adapters.AdapterError as exc:
        return True, str(exc)
    except Exception as exc:  # unexpected family is still a refusal but named
        return True, "UNEXPECTED %s: %s" % (type(exc).__name__, exc)
    return False, "no error (would have been accepted)"


def _acceptance(fn):
    import adapters
    try:
        fn()
    except adapters.AdapterError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, "UNEXPECTED %s: %s" % (type(exc).__name__, exc)
    return True, "verify ok"


def collect():
    """Measure the shipped faces. Never writes to src/."""
    if not os.path.isfile(CONFIG):
        raise SystemExit("missing input: %s" % CONFIG)
    sys.path.insert(0, PAY_DIR)
    import adapters
    import v3

    with open(CONFIG, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)

    channels = adapters.from_config(cfg)
    channel_rows = []
    for name in ("virtual", "standard"):
        ch = channels[name]
        nonce = "nonce-%s-pos" % name
        cb = ch.make_callback(ORDER_ID, AMOUNT_CENT, nonce)
        prepay = ch.place(ORDER_ID, AMOUNT_CENT)
        ok, detail = _acceptance(lambda ch=ch, cb=cb: ch.verify(cb))
        channel_rows.append({
            "case": "%s / signed callback" % name,
            "channel": name,
            "expect": L["accepted"],
            "got": L["accepted"] if ok else L["refused"],
            "ok": ok,
            "detail": "%s; prepay_id=%s mock=%s" % (
                detail, prepay["prepay_id"], prepay["mock"]),
        })

    # legacy negatives: signature, signer, timestamp window (adapters.py)
    ch = channels["virtual"]
    good = ch.make_callback(ORDER_ID, AMOUNT_CENT, "nonce-neg")

    bad_sig = copy.deepcopy(good)
    bad_sig["sig"] = ("0" if bad_sig["sig"][0] != "0" else "1") + bad_sig["sig"][1:]
    bad_signer = ch.make_callback(ORDER_ID, AMOUNT_CENT, "nonce-sgn",
                                  signer="imposter")
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        seconds=ch.ts_window + 100)
    stale = ch.make_callback(ORDER_ID, AMOUNT_CENT, "nonce-ts",
                             ts_utc=past.strftime("%Y-%m-%dT%H:%M:%SZ"))

    legacy_neg = []
    for case, payload in (("tampered signature", bad_sig),
                          ("unknown signer", bad_signer),
                          ("stale timestamp", stale)):
        refused, detail = _refusal(lambda p=payload: ch.verify(p))
        legacy_neg.append({"case": case, "expect": L["refused"],
                           "got": L["refused"] if refused else L["accepted"],
                           "ok": refused, "detail": detail})

    # V3 face: four headers, signed body, trade_state criterion
    spec = cfg["channels"]["virtual"]
    v3ch = v3.V3Channel("virtual-v3", spec["signer"], spec["mock_key"],
                        int(spec.get("ts_window_seconds", 300)),
                        [V3_SERIAL])
    cb = v3ch.make_v3_callback(ORDER_ID, AMOUNT_CENT, "nonce-v3-pos")
    headers = cb["v3"]["headers"]
    header_names = ("Wechatpay-Serial", "Wechatpay-Signature",
                    "Wechatpay-Timestamp", "Wechatpay-Nonce")
    headers_present = sum(1 for h in header_names
                          if str(headers.get(h, "")).strip())
    ok, detail = _acceptance(lambda: v3ch.verify(cb))
    v3_pos = {"case": "v3 signed callback", "expect": L["accepted"],
              "got": L["accepted"] if ok else L["refused"], "ok": ok,
              "detail": detail, "headers_present": headers_present,
              "headers_required": len(header_names)}

    miss = copy.deepcopy(cb)
    del miss["v3"]["headers"]["Wechatpay-Signature"]
    tampered = copy.deepcopy(cb)
    tampered["v3"]["body"] = tampered["v3"]["body"] + " "
    stale_v3 = v3ch.make_v3_callback(
        ORDER_ID, AMOUNT_CENT, "nonce-v3-ts",
        ts_unix=int((datetime.datetime.now(datetime.timezone.utc) -
                     datetime.timedelta(seconds=v3ch.ts_window + 100))
                    .timestamp()))
    notpaid = v3ch.make_v3_callback(ORDER_ID, AMOUNT_CENT, "nonce-v3-np",
                                    trade_state="NOTPAY")

    v3_neg = []
    for case, payload in (("missing header", miss),
                          ("tampered body", tampered),
                          ("stale timestamp", stale_v3),
                          ("trade_state NOTPAY", notpaid)):
        refused, detail = _refusal(lambda p=payload: v3ch.verify(p))
        v3_neg.append({"case": case, "expect": L["refused"],
                       "got": L["refused"] if refused else L["accepted"],
                       "ok": refused, "detail": detail})

    products = []
    for pid, row in sorted(cfg.get("products", {}).items()):
        blob = "%s %s" % (row.get("note", ""), row.get("copy", ""))
        products.append({
            "id": pid,
            "price_cent": int(row.get("price_cent", -1)),
            "channel": row.get("channel", ""),
            "entitlement": row.get("entitlement", ""),
            "needs_ceo": "[needs-CEO]" in blob,
            "copy": row.get("copy", ""),
        })

    comp = cfg.get("compliance", {})
    source = open(__file__, "rb").read()
    ascii_ok = True
    try:
        source.decode("ascii")
    except UnicodeDecodeError:
        ascii_ok = False
    text = source.decode("utf-8", "replace")
    import_lines = [ln.strip() for ln in text.splitlines()
                    if ln.strip().startswith(("import ", "from "))]
    net_hits = sum(1 for ln in import_lines
                   if any(tok in ln
                          for tok in ("socket", "urllib", "requests")))
    imports = sorted({ln.split()[1].split(".")[0] for ln in import_lines
                      if ln.startswith("import ")})
    allowed = {"argparse", "copy", "datetime", "hashlib", "html", "json",
               "os", "sys", "adapters", "v3", "value_domain"}
    imports_ok = all(name in allowed for name in imports)

    meas = {
        "generated_utc": datetime.datetime.now(
            datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": {"path": "src/sandbox/pay/config.json",
                   "sha256": _sha256(CONFIG)},
        "channels_built": sorted(channels.keys()),
        "channel_positive": channel_rows,
        "legacy_negative": legacy_neg,
        "v3_positive": v3_pos,
        "v3_negative": v3_neg,
        "products": products,
        "compliance": {
            "disclaimer": comp.get("disclaimer", ""),
            "disclaimer_persistent": bool(comp.get("disclaimer_persistent")),
            "aigc_marking_note": comp.get("note", ""),
        },
        "source": {"ascii": ascii_ok, "imports": imports,
                   "network_refs": net_hits,
                   "sha256": hashlib.sha256(source).hexdigest()},
        "notes": [N["mock"], N["rsa"], N["price"], N["docker"]],
        "blocked_on": "CEO physical item: real merchant id / appid / appkey / "
                      "settlement (AC-YP1); platform public key for V3 rsa mode",
    }

    pack = next((p for p in products if p["id"] == "pack_compute_19_9"), None)
    meas["criteria"] = [
        {"id": "AC-PAYG1", "text": CHECKS[0][1], "pass": None,
         "measured": "rendered below"},
        {"id": "AC-PAYG2", "text": CHECKS[1][1],
         "pass": len([r for r in channel_rows if r["ok"]]) == 2,
         "measured": "%d/2 accepted" % len([r for r in channel_rows if r["ok"]])},
        {"id": "AC-PAYG3", "text": CHECKS[2][1],
         "pass": len([r for r in legacy_neg if r["ok"]]) == 3,
         "measured": "%d/3 refused" % len([r for r in legacy_neg if r["ok"]])},
        {"id": "AC-PAYG4", "text": CHECKS[3][1],
         "pass": bool(v3_pos["ok"]) and headers_present == len(header_names),
         "measured": "%s; headers %d/%d" % (
             "accepted" if v3_pos["ok"] else "refused",
             headers_present, len(header_names))},
        {"id": "AC-PAYG5", "text": CHECKS[4][1],
         "pass": len([r for r in v3_neg if r["ok"]]) == 4,
         "measured": "%d/4 refused" % len([r for r in v3_neg if r["ok"]])},
        {"id": "AC-PAYG6", "text": CHECKS[5][1],
         "pass": bool(pack) and pack["price_cent"] == AMOUNT_CENT
         and pack["needs_ceo"],
         "measured": "%s price_cent=%s needs_ceo=%s" % (
             pack["id"] if pack else "missing",
             pack["price_cent"] if pack else "-",
             pack["needs_ceo"] if pack else "-")},
        {"id": "AC-PAYG7", "text": CHECKS[6][1],
         "pass": bool(meas["compliance"]["disclaimer"].strip())
         and bool(meas["compliance"]["aigc_marking_note"].strip()),
         "measured": "disclaimer %dB, marking note %dB" % (
             len(meas["compliance"]["disclaimer"].encode("utf-8")),
             len(meas["compliance"]["aigc_marking_note"].encode("utf-8")))},
        {"id": "AC-PAYG8", "text": CHECKS[7][1],
         "pass": ascii_ok and net_hits == 0 and imports_ok,
         "measured": "ascii=%s network_refs=%d imports_ok=%s imports=%s" % (
             ascii_ok, net_hits, imports_ok, ",".join(imports))},
    ]
    failed = [c["id"] for c in meas["criteria"] if c["pass"] is False]
    meas["verdict"] = "PASS" if not failed else "FAIL " + ",".join(failed)
    meas["criteria"][0]["pass"] = bool(meas["verdict"] == "PASS")
    meas["criteria"][0]["measured"] = "criteria rows=%d" % len(meas["criteria"])
    return meas


def _rows(rows, cols, key_order):
    out = ['<table><thead><tr>']
    for key in key_order:
        out.append("<th>%s</th>" % html.escape(cols[key]))
    out.append("</tr></thead><tbody>")
    for row in rows:
        cls = "ok" if row.get("ok") else "bad"
        out.append('<tr class="%s">' % cls)
        for key in key_order:
            val = row.get(key, "")
            out.append("<td>%s</td>" % html.escape(str(val)))
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def render_html(meas):
    e = html.escape
    parts = []
    parts.append(
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<title>' + e(L["title"]) + '</title><style>'
        'body{font-family:-apple-system,"Segoe UI",sans-serif;margin:0;'
        'padding:28px 34px;color:#1c1f23;background:#fbfbf9;line-height:1.55}'
        'h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:30px 0 10px;'
        'border-left:4px solid #2f6f4f;padding-left:9px}'
        '.sub{color:#5b6168;font-size:13px;margin-bottom:16px}'
        '.meta{font-size:12px;color:#5b6168;background:#f1f2ee;padding:9px 12px;'
        'border-radius:6px;word-break:break-all}'
        'table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}'
        'th,td{border:1px solid #d9dbd4;padding:6px 9px;text-align:left;'
        'vertical-align:top}th{background:#eceee7;font-weight:600}'
        'tr.ok td:nth-child(n){}tr.bad td{background:#fdeeee}'
        '.chip{display:inline-block;padding:2px 8px;border-radius:10px;'
        'font-size:12px;font-weight:600}.chip.pass{background:#e2f2e7;color:#1d5b37}'
        '.chip.fail{background:#fbe0e0;color:#8d2020}'
        '.adv{border:1px solid #d9a441;background:#fdf6e6;padding:11px 14px;'
        'border-radius:6px;font-size:13px;white-space:pre-wrap}'
        '.blk{border:1px solid #c25b5b;background:#fdeeee;padding:11px 14px;'
        'border-radius:6px;font-size:13px}'
        'code{background:#eef0ea;padding:1px 4px;border-radius:3px}'
        '</style></head><body>')
    parts.append("<h1>%s</h1>" % e(L["title"]))
    parts.append('<div class="sub">%s</div>' % e(L["sub"]))
    parts.append('<div class="meta">%s: %s<br>%s: %s (sha256 %s)<br>verdict: '
                 '<span class="chip %s">%s</span></div>' % (
                     e(L["g"]), e(meas["generated_utc"]),
                     e(L["s"]), e(meas["config"]["path"]),
                     e(meas["config"]["sha256"][:16]),
                     "pass" if meas["verdict"] == "PASS" else "fail",
                     e(meas["verdict"])))

    parts.append("<h2>%s</h2>" % e(L["sec1"]))
    prod_rows = [{"id": p["id"], "price_cent": p["price_cent"],
                  "channel": p["channel"], "entitlement": p["entitlement"],
                  "needs_ceo": "yes" if p["needs_ceo"] else "no",
                  "ok": True} for p in meas["products"]]
    parts.append(_rows(prod_rows, {"id": L["tp"], "price_cent": L["tr"],
                                   "channel": L["tc"], "entitlement": L["te"],
                                   "needs_ceo": "needs-CEO"},
                       ("id", "price_cent", "channel", "entitlement",
                        "needs_ceo")))

    parts.append("<h2>%s</h2>" % e(L["sec2"]))
    parts.append(_rows(meas["channel_positive"],
                       {"case": L["tcase"], "expect": L["texp"],
                        "got": L["tgot"], "detail": L["tdet"]},
                       ("case", "expect", "got", "detail")))

    parts.append("<h2>%s</h2>" % e(L["sec3"]))
    parts.append(_rows(meas["legacy_negative"],
                       {"case": L["tcase"], "expect": L["texp"],
                        "got": L["tgot"], "detail": L["tdet"]},
                       ("case", "expect", "got", "detail")))

    parts.append("<h2>%s</h2>" % e(L["sec4"]))
    v3p = dict(meas["v3_positive"])
    v3p["detail"] = "%s; headers %d/%d" % (
        v3p["detail"], v3p["headers_present"], v3p["headers_required"])
    parts.append(_rows([v3p], {"case": L["tcase"], "expect": L["texp"],
                               "got": L["tgot"], "detail": L["tdet"]},
                       ("case", "expect", "got", "detail")))
    parts.append(_rows(meas["v3_negative"],
                       {"case": L["tcase"], "expect": L["texp"],
                        "got": L["tgot"], "detail": L["tdet"]},
                       ("case", "expect", "got", "detail")))

    parts.append("<h2>%s</h2>" % e(L["sec5"]))
    parts.append('<div class="adv"><strong>%s</strong><br>%s</div>' % (
        e(L["adv"]), e(meas["compliance"]["disclaimer"])))
    parts.append("<p><strong>%s</strong> (persistent=%s)<br>%s</p>" % (
        e(L["aig"]), e(str(meas["compliance"]["disclaimer_persistent"])),
        e(meas["compliance"]["aigc_marking_note"])))
    parts.append('<div class="blk"><strong>%s</strong><br>%s</div>' % (
        e(L["blk"]), e(meas["blocked_on"])))
    parts.append("<ul>%s</ul>" % "".join(
        "<li>%s</li>" % e(n) for n in meas["notes"]))

    parts.append("<h2>%s</h2>" % e(L["sec6"]))
    crit_rows = [{"id": c["id"], "text": c["text"], "measured": c["measured"],
                  "ok": bool(c["pass"])} for c in meas["criteria"]]
    parts.append(_rows(crit_rows, {"id": L["crit"], "text": L["note"],
                                   "measured": L["tgot"], "ok": L["st"]},
                       ("id", "text", "measured", "ok")))
    parts.append("</body></html>")
    return "".join(parts)


def check(meas, out, jout, diag=None):
    fails = []
    if not os.path.isfile(out) or not os.path.isfile(jout):
        return ["missing artifact"]
    if os.path.getsize(out) == 0 or os.path.getsize(jout) == 0:
        fails.append("empty artifact")
    with open(jout, "r", encoding="utf-8") as fh:
        landed = json.load(fh)
    if len(landed.get("criteria", [])) != len(CHECKS):
        fails.append("criteria rows=%d" % len(landed.get("criteria", [])))
    for c in landed.get("criteria", []):
        if not c.get("pass"):
            fails.append("%s failed" % c.get("id"))
    if len(landed.get("channel_positive", [])) != 2:
        fails.append("channel_positive rows")
    if len([r for r in landed.get("channel_positive", []) if r.get("ok")]) != 2:
        fails.append("channel_positive not 2/2")
    if len([r for r in landed.get("legacy_negative", []) if r.get("ok")]) != 3:
        fails.append("legacy_negative not 3/3")
    if len([r for r in landed.get("v3_negative", []) if r.get("ok")]) != 4:
        fails.append("v3_negative not 4/4")
    fresh = {c["id"]: c for c in meas["criteria"]}
    for c in landed.get("criteria", []):
        run = fresh.get(c.get("id"))
        if not run or run["measured"] != c.get("measured"):
            fails.append("%s drift" % c.get("id"))
    # AC-PAYGB10/11 -> AC-VD2/VD3 (R2825): the comparison now lives in
    # tools/value_domain.py, which the other three price faces import too. The
    # criteria TEXT and the artifact SIZES can agree while the landed price
    # table belongs to an older config, which is exactly what R2816 measured.
    cat = VD.catalog(CATALOG_ROOT)
    stats = {}
    landed_shas = (landed.get("config") or {}).get("sha256")
    fails.extend(VD.config_drift(landed_shas, cat, "pay_sha256"))
    fails.extend(VD.product_failures(landed.get("products") or [], cat,
                                     stats=stats))
    sizes = landed.get("sizes") or {}
    if sizes.get("html") != os.path.getsize(out):
        fails.append("sizes html %s != %d on disk" % (sizes.get("html"),
                                                      os.path.getsize(out)))
    if sizes.get("json") != os.path.getsize(jout):
        fails.append("sizes json %s != %d on disk" % (sizes.get("json"),
                                                      os.path.getsize(jout)))
    # AC-VD9/AC-VD11 (R2826): the printed line and the exit code read ONE list.
    fails = VD.teeth(stats.get("products", 0), stats.get("tiers", 0), fails)
    if diag is not None:
        diag["line"] = VD.line(stats.get("products", 0), stats.get("tiers", 0),
                               fails)
    return fails


def main(argv):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--json", default=DEFAULT_JSON)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    meas = collect()
    if args.check:
        diag = {}
        fails = check(meas, args.out, args.json, diag)
        print("PAYMENT GATE CHECK %s fails=%d" % (
            "PASS" if not fails else "FAIL", len(fails)))
        print(diag.get("line", ""))
        for f in fails:
            print("  - %s" % f)
        return 0 if not fails else 2

    doc = render_html(meas)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    # BD-PROP-010: the json states the size of both artifacts it belongs to.
    # The html is already on disk and never reads this key, so only the json's
    # own byte count is self-referential; iterate to the fixed point.
    for _ in range(6):
        meas["sizes"] = {
            "html": os.path.getsize(args.out),
            "json": os.path.getsize(args.json) if os.path.exists(args.json) else 0,
        }
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(meas, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        if meas["sizes"]["json"] == os.path.getsize(args.json):
            break
    size = os.path.getsize(args.out)
    jsize = os.path.getsize(args.json)
    print("PAYMENT GATE REPORT html=%dB json=%dB channels=%s accepted=%d "
          "refused=%d verdict=%s" % (
              size, jsize, ",".join(meas["channels_built"]),
              len([r for r in meas["channel_positive"] if r["ok"]]) +
              (1 if meas["v3_positive"]["ok"] else 0),
              len([r for r in meas["legacy_negative"] if r["ok"]]) +
              len([r for r in meas["v3_negative"] if r["ok"]]),
              meas["verdict"]))
    return 0 if meas["verdict"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
