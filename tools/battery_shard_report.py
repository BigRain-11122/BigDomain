"""battery_shard_report - a CEO-visible face for supervised shards (R2799).

The full reconcile battery covers every registered suite and needs thousands
of seconds in a single leg, so in practice it is permanently "owed".  R2797
shipped tools/battery_shard.py, which can green or redden ONE family of suites
in seconds - but that runner only prints stdout, so nothing on disk told a
reader whether the families touched this week were green.

This module runs the requested families through the SHIPPED shard runner,
parses its real closing and per-suite rows, and lands
preview/battery-shard-report.{json,html}.  Every number on the page is parsed
from that stdout or re-derived from the registry; none of them is typed here.

  python tools/battery_shard_report.py            # measure + render
  python tools/battery_shard_report.py --check    # read-only verification
  python tools/battery_shard_report.py --control  # the gate must redden

Exit codes: 0 pass, 2 refuse or red.

R3082: the page now carries the OTHER half of the criteria denominator. R3081
made the runner print crit_unchecked and taught this reader to parse it, but
the published pair was still the R2800 render, so --check read
E_REGISTRY_DRIFT on every family: the registry has grown since that render and
the page cannot be trusted to say by how much. The pair is regenerated here,
and the count is printed where a reader already looks: totals line plus one
column per family. A leg that predates the field (crit_unchecked_seen=0) prints
the word in Chinese rather than a measured 0, and unchecked_cell() is the
single source both the page and check_payload use.
"""

import copy
import io
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PREVIEW = os.path.join(ROOT, "preview")
OUT_JSON = os.path.join(PREVIEW, "battery-shard-report.json")
OUT_HTML = os.path.join(PREVIEW, "battery-shard-report.html")
SHARD = os.path.join(HERE, "battery_shard.py")
ROUND = "R3082"

# label prefix, family key, what the family guards.  These are the REQUEST;
# every number that comes back is measured.
FAMILIES = (
    ("lobby", "\u5927\u5385\u5b9e\u65f6\u5c42", "\u4f1a\u8bdd\u3001\u623f\u95f4\u3001\u9650\u6d41\u3001UGC \u95f8\u3001\u6301\u4e45\u5316"),
    ("os-export", "OS \u5bfc\u51fa\u9762", "\u5bfc\u51fa\u65b0\u9c9c\u5ea6\u3001\u53d1\u5e03\u8def\u5f84\u3001\u4e00\u81f4\u6027"),
    ("os-queue", "OS \u961f\u5217\u9762", "\u961f\u5934/\u961f\u5c3e/\u5360\u4f4d/\u76d6\u7ae0/\u4ea4\u4ed8"),
    ("os-ledger", "OS \u53f0\u8d26\u9762", "\u53cc\u5f0f\u8bb0\u8d26\u3001\u5bf9\u8d26\u95f8\u3001\u53f0\u8d26\u5f52\u6863\u3001\u5224\u636e\u524d\u7f00"),
    ("os-battery", "OS \u7535\u6c60\u9762", "\u5206\u7247\u5668\u3001\u5168\u91cf\u7535\u6c60\u53e3\u5f84\u3001\u81ea\u6d4b\u8bd5"),
    ("os-deliverable", "OS \u4ea4\u4ed8\u9762", "\u5165\u53e3\u9875\u751f\u6210\u5668\u3001\u94fe\u63a5\u8986\u76d6"),
)

LINKS = ("index.html", "lobby-session-trace.html", "ledger-reconcile-face.html")

SCOPE_RE = re.compile(
    r"^SHARD scope=SHARD registry_suites=(\d+) registry_criteria=(\d+) "
    r"selected=(\d+) selected_criteria=(\d+)", re.M)
ROW_RE = re.compile(
    r"^SHARD row (\S+) rc=(\d+) pass=(\d+) fail=(\d+)(?: detail=\S+)? "
    r"suite=(.*) crit=(\d+) ([\d.]+)s(?: timeout=yes)?$", re.M)
# AC-BSRB10 (R3081): this regex used to end at "elapsed=Ns$", which was true
# until R2919 appended crit_checked and R3081 appended crit_unchecked. Measured
# consequence: every shipped leg read "refused" while this file's own suite
# stayed green, because the suite built its fixture from the OLD row shape. The
# tail is optional on both sides so a leg from either era parses; a missing
# crit_unchecked is published as 0 WITH a seen flag rather than passed off as a
# measurement of zero.
CLOSE_RE = re.compile(
    r"^SHARD rc=(\d+) scope=SHARD selected=(\d+) executed=(\d+) green=(\d+) "
    r"criteria=(\d+) crit_mismatch=(\d+) elapsed=([\d.]+)s"
    r"(?: crit_checked=(\d+))?(?: crit_unchecked=(\d+))?$", re.M)


class Refuse(Exception):
    pass


def run_family(prefix):
    """AC-BSR1: run the shipped shard runner and keep its raw stdout."""
    cmd = [sys.executable, SHARD, "--match", prefix]
    proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    # the runner's rows are line-anchored, so CRLF must not defeat the anchors
    return proc.returncode, text.replace("\r\n", "\n").replace("\r", "\n")


def parse_family(key, prefix, guards, rc, out):
    resp = {"key": key, "match": prefix, "guards": guards, "rc": rc,
            "suites": [], "red": [], "parse": "ok"}
    scope = SCOPE_RE.search(out)
    close = CLOSE_RE.search(out)
    if not scope or not close:
        resp["parse"] = "refused"
        head = [l for l in out.splitlines() if l.strip()][:2]
        resp["reason"] = " / ".join(head)[:300]
        resp["selected"] = 0
        resp["selected_criteria"] = 0
        resp["executed"] = 0
        resp["green"] = 0
        resp["crit_mismatch"] = 0
        resp["crit_unchecked"] = 0
        resp["crit_unchecked_seen"] = 0
        resp["elapsed_s"] = 0.0
        resp["registry_suites"] = 0
        resp["registry_criteria"] = 0
        return resp
    resp["registry_suites"] = int(scope.group(1))
    resp["registry_criteria"] = int(scope.group(2))
    resp["selected"] = int(close.group(2))
    resp["executed"] = int(close.group(3))
    resp["green"] = int(close.group(4))
    resp["selected_criteria"] = int(close.group(5))
    resp["crit_mismatch"] = int(close.group(6))
    resp["elapsed_s"] = float(close.group(7))
    # AC-BSRB10: the unchecked count is published only when the row carried it;
    # seen=0 says "this leg predates the field", never "zero unmeasured rows".
    if close.group(9) is None:
        resp["crit_unchecked"] = 0
        resp["crit_unchecked_seen"] = 0
    else:
        resp["crit_unchecked"] = int(close.group(9))
        resp["crit_unchecked_seen"] = 1
    for m in ROW_RE.finditer(out):
        row = {"label": m.group(1), "rc": int(m.group(2)),
               "pass": int(m.group(3)), "fail": int(m.group(4)),
               "suite": m.group(5).strip(), "crit": int(m.group(6)),
               "elapsed_s": float(m.group(7))}
        resp["suites"].append(row)
        if row["rc"] != 0:
            resp["red"].append(row["label"])
    return resp


def unchecked_cell(fam):
    """AC-BSRB11 (R3082): one source for the page and the gate.

    A leg that predates crit_unchecked has seen=0 and must NOT print a measured
    zero -- the word says the family never declared, which is the honest read.
    """
    if fam.get("crit_unchecked_seen"):
        return "%d" % fam.get("crit_unchecked", 0)
    return "\u672a\u7533\u62a5"


def measure():
    fams = []
    for prefix, key, guards in FAMILIES:
        rc, out = run_family(prefix)
        fam = parse_family(key, prefix, guards, rc, out)
        fams.append(fam)
        print("BSR family %s rc=%d selected=%d green=%d criteria=%d %.1fs"
              % (key, fam["rc"], fam["selected"], fam["green"],
                 fam["selected_criteria"], fam["elapsed_s"]))
    reg = {(f["registry_suites"], f["registry_criteria"]) for f in fams
           if f["parse"] == "ok"}
    # AC-BSR2: three families answer from ONE registry; disagreement is fatal.
    if len(reg) != 1:
        raise Refuse("E_REGISTRY_DRIFT families disagree on the registry "
                     "size: %s" % sorted(reg))
    suites, crit = reg.pop()
    total_sel = sum(f["selected"] for f in fams)
    total_crit = sum(f["selected_criteria"] for f in fams)
    red = [f["key"] for f in fams if f["rc"] != 0 or f["parse"] != "ok"]
    verdict = "PASS" if not red else "RED"
    payload = {
        "round": ROUND,
        "registry": {"suites": suites, "criteria": crit},
        "families": fams,
        "totals": {
            "families": len(fams),
            "green_families": len(fams) - len(red),
            "red_families": len(red),
            "selected": total_sel,
            "selected_criteria": total_crit,
            "uncovered_suites": suites - total_sel,
            "cover_pct": round(100.0 * total_sel / suites, 1) if suites else 0.0,
            "crit_mismatch": sum(f["crit_mismatch"] for f in fams),
            "crit_unchecked": sum(f.get("crit_unchecked", 0) for f in fams),
            "crit_unchecked_seen": sum(f.get("crit_unchecked_seen", 0)
                                       for f in fams),
        },
        "verdict": verdict,
        "not_the_battery": (
            "\u672c\u9875\u662f\u5206\u7247\uff0c\u4e0d\u662f\u5168\u91cf\u7535\u6c60\uff1a\u5b83\u53ea\u8dd1\u4e0b\u5217\u65cf\uff0c\u672a\u8986\u76d6\u7684 "
            "%d \u5957\u4ef6\u4ecd\u662f\u6b20\u8d26\u3002" % (suites - total_sel)),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    return payload


def render_html(p):
    t = p["totals"]
    reg = p["registry"]
    out = []
    a = out.append
    a("<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">")
    a("<title>BigDomain \u5206\u7247\u7535\u6c60\u9762 %s</title>" % p["round"])
    a("<style>body{font-family:system-ui,'Microsoft YaHei',sans-serif;"
      "margin:28px;max-width:1000px;line-height:1.6;color:#222}"
      "h1{font-size:22px;margin:0 0 6px}h2{font-size:16px;margin:22px 0 8px;"
      "border-bottom:1px solid #ddd;padding-bottom:4px}"
      "table{border-collapse:collapse;width:100%;font-size:13px}"
      "th,td{border:1px solid #ddd;padding:5px 7px;text-align:left}"
      "th{background:#f4f4f4}td.n{text-align:right;font-variant-numeric:tabular-nums}"
      ".pass{color:#0a6b28;font-weight:600}.red{color:#a11;font-weight:600}"
      ".note{background:#fbf7e6;border-left:4px solid #d9b74a;padding:9px 12px;"
      "margin:12px 0;font-size:13px}code{background:#f2f2f2;padding:1px 4px}"
      "</style></head><body>")
    a("<h1>BigDomain \u5206\u7247\u7535\u6c60\u9762 \u00b7 %s</h1>" % p["round"])
    a("<div>\u6e32\u67d3\u81ea <code>tools/battery_shard_report.py</code>"
      "\uff08\u8dd1 <code>tools/battery_shard.py</code> \u7684\u771f\u5b9e stdout\uff09\u00b7 %s</div>"
      % p["generated_at"])
    a("<div class=\"note\"><b>%s</b><br>\u5168\u8868\u518c %d \u5957\u4ef6 / %d \u5224\u636e\uff1b\u672c\u9875\u8986\u76d6 %d \u5957\u4ef6 / "
      "%d \u5224\u636e\uff08%.1f%%\uff09\uff0c\u672a\u8986\u76d6 %d \u5957\u4ef6\u3002<br>\u5206\u7247\u4e0d\u6784\u6210\u7535\u6c60\u8986\u76d6\u2014\u2014"
      "<code>battery_shard.py</code> \u81ea\u5df1\u62d2\u7edd <code>--claim full</code>\u3002</div>"
      % (p["not_the_battery"], reg["suites"], reg["criteria"], t["selected"],
         t["selected_criteria"], t["cover_pct"], t["uncovered_suites"]))
    a("<h2>\u7ed3\u8bba</h2>")
    cls = "pass" if p["verdict"] == "PASS" else "red"
    a("<p>VERDICT <span class=\"%s\">%s</span> \u00b7 \u7eff\u65cf %d / %d \u00b7 "
      "\u65cf\u5185\u5957\u4ef6 %d / %d \u6267\u884c\u7eff \u00b7 \u5224\u636e %d \u00b7 \u5224\u636e\u6570\u4e0d\u4e00\u81f4 %d \u00b7 "
      "\u672a\u6bd4\u8f83\u5224\u636e %d\uff08%d/%d \u65cf\u5df2\u7533\u62a5\uff09</p>"
      % (cls, p["verdict"], t["green_families"], t["families"],
         sum(f["green"] for f in p["families"]),
         sum(f["executed"] for f in p["families"]),
         t["selected_criteria"], t["crit_mismatch"],
         t["crit_unchecked"], t["crit_unchecked_seen"], t["families"]))
    a("<h2>\u65cf\u8bfb\u6570</h2><table><tr><th>\u65cf</th><th>\u6807\u7b7e\u524d\u7f00</th><th>\u5b88\u62a4\u9762</th>"
      "<th>rc</th><th>\u5957\u4ef6</th><th>\u5224\u636e</th><th>\u672a\u6bd4\u8f83</th><th>\u7eff/\u6267\u884c</th><th>\u8017\u65f6</th>"
      "<th>\u7ed3\u8bba</th></tr>")
    for f in p["families"]:
        ok = f["rc"] == 0 and f["parse"] == "ok"
        a("<tr><td>%s</td><td><code>%s</code></td><td>%s</td>"
          "<td class=\"n\">%d</td><td class=\"n\">%d</td><td class=\"n\">%d</td>"
          "<td class=\"n\">%s</td><td class=\"n\">%d / %d</td><td class=\"n\">%.1fs</td>"
          "<td class=\"%s\">%s</td></tr>"
          % (f["key"], f["match"], f["guards"], f["rc"], f["selected"],
             f["selected_criteria"], unchecked_cell(f), f["green"], f["executed"],
             f["elapsed_s"], "pass" if ok else "red",
             "GREEN" if ok else "RED"))
    a("</table>")
    a("<h2>\u9010\u5957\u4ef6\u884c</h2>")
    for f in p["families"]:
        a("<h3 style=\"font-size:14px;margin:16px 0 6px\">%s "
          "\uff08%d \u884c\uff09</h3>" % (f["key"], len(f["suites"])))
        a("<table><tr><th>\u6807\u7b7e</th><th>rc</th><th>pass</th><th>fail</th>"
          "<th>\u5957\u4ef6\u81ea\u62a5</th><th>\u5224\u636e</th><th>\u79d2</th></tr>")
        for r in f["suites"]:
            a("<tr><td><code>%s</code></td><td class=\"n\">%d</td>"
              "<td class=\"n\">%d</td><td class=\"n\">%d</td><td>%s</td>"
              "<td class=\"n\">%d</td><td class=\"n\">%.1f</td></tr>"
              % (r["label"], r["rc"], r["pass"], r["fail"], r["suite"],
                 r["crit"], r["elapsed_s"]))
        a("</table>")
    a("<h2>\u8bda\u5b9e\u6ce8</h2><ul>")
    a(("<li>\u5c01\u9762\u4e0a\u7684\u6bcf\u4e2a\u6570\u90fd\u89e3\u6790\u81ea\u5206\u7247\u5668\u672c\u6b21 stdout\uff0c"
       "\u6e90\u7801\u4e0d\u5e26\u8fd9\u4e9b\u6570\u5b57\u7684\u5b57\u9762\u91cf\uff1b\u6ce8\u518c\u8868\u5927\u5c0f\u53d6\u81ea\u672c\u9875\u8dd1\u7684 "
       "%d \u65cf\u5404\u81ea\u6253\u5370\u7684 <code>SHARD scope=</code> \u884c\uff0c\u4e92\u4e0d\u4e00\u81f4\u5373\u62d2\u6e32\u67d3\u3002</li>")
      % len(p["families"]))
    a("<li>\u8017\u65f6\u9010\u6b21\u4e0d\u540c\uff0c\u6240\u4ee5 <code>--check</code> \u4e0d\u91cd\u8dd1\u5957\u4ef6\uff1b\u5b83\u590d\u7b97\u7684\u662f"
      "json \u9010\u5b57\u8282\u91cd\u5e8f\u5217\u5316\u3001html \u9010\u5b57\u8282\u91cd\u6e32\u67d3\u3001\u5404\u65cf\u5224\u636e\u6570\u4e0e\u6ce8\u518c\u8868\u91cd\u65b0\u9009\u62e9\u76f8\u7b49\u3001"
      "\u6c47\u603b\u7b97\u672f\u81ea\u6d3d\u3001verdict=\u5404\u65cf rc \u6700\u5927\u503c\u6620\u5c04\u3002</li>")
    a("<li>\u300c\u672a\u6bd4\u8f83\u300d\u53d6\u81ea\u6bcf\u65cf\u5c3e\u884c\u81ea\u62a5\u7684 "
      "<code>crit_unchecked=</code>\uff1b\u8be5\u65cf\u5c3e\u884c\u65e9\u4e8e\u8fd9\u4e2a\u5b57\u6bb5"
      "\uff08R3081 \u4e4b\u524d\uff09\u65f6\u9875\u9762\u5199\u300c\u672a\u7533\u62a5\u300d\uff0c"
      "\u800c\u4e0d\u662f\u5b9e\u6d4b\u7684 0\u3002</li>")
    a("<li>\u672c\u9875\u4e0d\u8bc1\u660e\u672a\u88ab\u9009\u4e2d\u65cf\u7684\u72b6\u6001\uff0c\u4e5f\u4e0d\u66ff\u4ee3\u5168\u91cf\u7535\u6c60\uff1b\u672a\u8986\u76d6\u5957\u4ef6\u6570\u89c1\u9996\u5c4f\u3002</li>")
    a("</ul>")
    a("<h2>\u90bb\u5c45\u9762</h2><ul>")
    for name in LINKS:
        a("<li><a href=\"%s\">%s</a></li>" % (name, name))
    a("</ul></body></html>")
    return "\n".join(out) + "\n"


def dumps(payload):
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_atomic(path, text):
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


def expected_from_registry():
    """AC-BSR4: re-select from the registry itself, not from the payload."""
    sys.path.insert(0, HERE)
    import battery_shard as bs

    rows, _base, _cap, _ov = bs.registry()
    exp = {}
    for prefix, key, _g in FAMILIES:
        picked = bs.select(rows, [prefix], 0)
        exp[key] = (len(picked), sum(int(r[2]) for r in picked))
    return len(rows), sum(int(r[2]) for r in rows), exp


def check_payload(payload, html_text, json_text, reg_suites, reg_criteria, exp):
    fails = []
    if json_text != dumps(payload):
        fails.append("E_JSON_FIXED_POINT")
    if html_text != render_html(payload):
        fails.append("E_HTML_FIXED_POINT")
    if (payload["registry"]["suites"], payload["registry"]["criteria"]) != (
            reg_suites, reg_criteria):
        fails.append("E_REGISTRY_DRIFT")
    for fam in payload["families"]:
        want = exp.get(fam["key"])
        if want is None:
            fails.append("E_FAMILY_UNKNOWN:%s" % fam["key"])
        elif (fam["selected"], fam["selected_criteria"]) != want:
            fails.append("E_REGISTRY_DRIFT:%s" % fam["key"])
    t = payload["totals"]
    # AC-BSR7: the family SET must be self-consistent, or totals double-count.
    want_keys = [k for _p, k, _g in FAMILIES]
    if len(set(want_keys)) != len(want_keys):
        fails.append("E_FAMILY_KEY_DUP")
    for i, (pi, _k, _g) in enumerate(FAMILIES):
        for j, (pj, _k2, _g2) in enumerate(FAMILIES):
            if i != j and pj.startswith(pi):
                fails.append("E_FAMILY_PREFIX_OVERLAP:%s:%s" % (pi, pj))
    if [f["key"] for f in payload["families"]] != want_keys:
        fails.append("E_FAMILY_SET")
    # AC-BSR8: every count on the page is arithmetic over the payload.
    if "\u4e09\u65cf" in html_text:
        fails.append("E_TYPED_FAMILY_COUNT")
    if ("%d \u65cf" % len(payload["families"])) not in html_text:
        fails.append("E_FAMILY_COUNT_ABSENT")
    if t["selected"] != sum(f["selected"] for f in payload["families"]):
        fails.append("E_TOTALS_SELECTED")
    if t["selected_criteria"] != sum(f["selected_criteria"]
                                     for f in payload["families"]):
        fails.append("E_TOTALS_CRITERIA")
    if t["families"] != len(payload["families"]):
        fails.append("E_TOTALS_FAMILIES")
    if t["uncovered_suites"] != reg_suites - t["selected"]:
        fails.append("E_TOTALS_UNCOVERED")
    want_cover = (round(100.0 * t["selected"] / reg_suites, 1)
                  if reg_suites else 0.0)
    if abs(float(t["cover_pct"]) - want_cover) > 1e-9:
        fails.append("E_TOTALS_COVER")
    reds = [f for f in payload["families"]
            if f["rc"] != 0 or f["parse"] != "ok"]
    want_verdict = "PASS" if not reds else "RED"
    if payload["verdict"] != want_verdict:
        fails.append("E_VERDICT")
    if t["red_families"] != len(reds):
        fails.append("E_TOTALS_RED")
    # AC-BSRB11 (R3082): the unchecked face is arithmetic over the payload, and
    # the page prints that same single source -- never a literal left behind by
    # an older round.
    if t.get("crit_unchecked") != sum(f.get("crit_unchecked", 0)
                                      for f in payload["families"]):
        fails.append("E_TOTALS_UNCHECKED")
    if t.get("crit_unchecked_seen") != sum(f.get("crit_unchecked_seen", 0)
                                           for f in payload["families"]):
        fails.append("E_TOTALS_UNCHECKED_SEEN")
    if ("\u672a\u6bd4\u8f83\u5224\u636e %d" % t.get("crit_unchecked", 0)) \
            not in html_text:
        fails.append("E_PAGE_UNCHECKED")
    for fam in payload["families"]:
        if ("<td class=\"n\">%s</td>" % unchecked_cell(fam)) not in html_text:
            fails.append("E_PAGE_UNCHECKED:%s" % fam["key"])
    if "http://" in html_text or "https://" in html_text:
        fails.append("E_HTTP_LITERAL")
    for name in LINKS:
        if not os.path.isfile(os.path.join(PREVIEW, name)):
            fails.append("E_LINK_TARGET:%s" % name)
    if "\u5206\u7247\uff0c\u4e0d\u662f\u5168\u91cf\u7535\u6c60" not in payload.get("not_the_battery", ""):
        fails.append("E_SCOPE_NOTE")
    return fails


def do_check():
    stats = {}
    for path in (OUT_HTML, OUT_JSON):
        stats[path] = (os.path.getsize(path), os.path.getmtime(path))
    html_text = io.open(OUT_HTML, encoding="utf-8").read()
    json_text = io.open(OUT_JSON, encoding="utf-8").read()
    try:
        payload = json.loads(json_text)
    except ValueError as exc:
        print("BSR-CHECK RED E_JSON_UNDECODABLE reason=%s" % exc)
        return 2
    reg_suites, reg_criteria, exp = expected_from_registry()
    fails = check_payload(payload, html_text, json_text, reg_suites,
                          reg_criteria, exp)
    after = {}
    for path in (OUT_HTML, OUT_JSON):
        after[path] = (os.path.getsize(path), os.path.getmtime(path))
    if stats != after:
        fails.append("E_WROTE_DURING_CHECK")
    if fails:
        print("BSR-CHECK RED %s" % ",".join(fails))
        return 2
    print("BSR-CHECK name=battery-shard-report checks=8 bytes_html=%d "
          "bytes_json=%d verdict=%s read_only=True"
          % (stats[OUT_HTML][0], stats[OUT_JSON][0], payload["verdict"]))
    print("BSR-CHECK VERDICT PASS")
    return 0


def do_control():
    """AC-BSR6: the gate must redden on a tampered private copy."""
    json_text = io.open(OUT_JSON, encoding="utf-8").read()
    payload = json.loads(json_text)
    bad = copy.deepcopy(payload)
    fam = bad["families"][0]
    fam["selected_criteria"] = fam["selected_criteria"] + 7
    bad_text = dumps(bad)
    bad_html = render_html(bad)
    reg_suites, reg_criteria, exp = expected_from_registry()
    fails = check_payload(bad, bad_html, bad_text, reg_suites, reg_criteria, exp)
    named = [f for f in fails if f.startswith("E_REGISTRY_DRIFT")]
    if not fails:
        print("BSR-CONTROL SUMMARY VACUOUS the gate could not see a tampered "
              "criteria count")
        return 2
    if not named:
        print("BSR-CONTROL SUMMARY MISFILED fails=%s" % ",".join(fails))
        return 2
    print("BSR-CONTROL tampered=%s field=selected_criteria delta=+7 "
          "named=%s" % (fam["key"], ",".join(fails)))
    print("BSR-CONTROL VERDICT CONFIRMED")
    return 0


def main(argv):
    args = list(argv[1:])
    try:
        if "--check" in args:
            return do_check()
        if "--control" in args:
            return do_control()
        payload = measure()
        html_text = render_html(payload)
        write_atomic(OUT_JSON, dumps(payload))
        write_atomic(OUT_HTML, html_text)
        print("BSR landed json=%dB html=%dB verdict=%s families=%d selected=%d "
              "criteria=%d uncovered=%d"
              % (os.path.getsize(OUT_JSON), os.path.getsize(OUT_HTML),
                 payload["verdict"], payload["totals"]["families"],
                 payload["totals"]["selected"],
                 payload["totals"]["selected_criteria"],
                 payload["totals"]["uncovered_suites"]))
        return 0 if payload["verdict"] == "PASS" else 2
    except Refuse as exc:
        print(str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
