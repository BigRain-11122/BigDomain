"""CEO blocker face: every row is a QUOTE from a register, resolved at render time.

Why this exists: the items only the CEO can unblock (physical pieces and
pricing/parameter confirmations) live scattered across BLUEPRINT.md,
HQ-FEEDBACK.md and docs/spec/*.md. A reader has to know which file to open and
which sentence to trust. This face collects the pointers, resolves each one on
every render, and prints the source line VERBATIM with its file and line number
so nothing on the page is typed by hand.

Discipline inherited from this company's face tooling:
  * a quote is a byte-identical window of the source line, never a paraphrase
  * a status is DERIVED by a declared rule; when no rule matches the row reads
    UNKNOWN and the page says so instead of inventing a verdict
  * --check must not author the artifact it verifies (AC-CBX5, self control)
  * no network literals, no clock except the state tick, no shell

Criteria are pre-registered in AC_CBX below and printed by --check.

Usage:
  python tools/ceo_blockers.py            # render preview/ceo-blockers.{html,json}
  python tools/ceo_blockers.py --check    # verify the landed artifacts
  python tools/ceo_blockers.py --write    # explicit re-render (same as default)
"""

import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH = os.path.join(REPO, "preview", "ceo-blockers.html")
JSON_PATH = os.path.join(REPO, "preview", "ceo-blockers.json")
STATE_PATH = os.path.join(REPO, "src", "os", "state.json")

TICK = "R2770"
QUOTE_CHARS = 150

# Each row is a POINTER, not a claim:
#   path   - source file relative to the repo root
#   anchor - regex that must match exactly one line in that file
#   title  - what the reader is being shown (this is the only typed prose)
#   action - DECLARED unblock action, labelled DECLARED on the page
#   face   - the openable artifact that documents the blocked capability
BLOCKERS = [
    {
        "id": "B1-physical-four",
        "title": "Physical pieces: server + domain + filing/ICP + WeChat Pay merchant id",
        "path": "BLUEPRINT.md",
        "anchor": r"≥11 天零到位",
        "action": "hand over the four physical pieces; the deploy chain is already gated and needs no re-decision",
        "face": "preview/platform-live-report.html",
    },
    {
        "id": "B2-pay-merchant-row",
        "title": "In-store experience spec carries the same physical dependency row",
        "path": "docs/spec/in-store-experience-v2-spec.md",
        "anchor": r"物理件依赖",
        "action": "same four pieces; this row is the spec-level echo, kept so the two registers cannot drift",
        "face": "preview/payment-gate-report.html",
    },
    {
        "id": "B3-pricing-confirm",
        "title": "Pricing confirmation batch (19.9 locked, 29.9 / 9.9 tier values)",
        "path": "BLUEPRINT.md",
        "anchor": r"决策件=定价确认批",
        "action": "confirm the tier values; confirmation locks them with zero re-legislation",
        "face": "preview/membership-benefit-report.html",
    },
    {
        "id": "B4-incentive-first-notch",
        "title": "Incentive agent first-notch parameters (numeric values only)",
        "path": "docs/spec/incentive-agent-spec.md",
        "anchor": r"数值纪律",
        "action": "approve the first-notch numbers; the structure and discipline are already locked",
        "face": "preview/ledger-business-report.html",
    },
    {
        "id": "B5-three-publicity",
        "title": "Three publicity faces: split ratio, settlement period, redemption floor",
        "path": "docs/spec/incentive-agent-spec.md",
        "anchor": r"\*\*三公示\*\*（gv 标准 1）",
        "action": "name the three numbers; missing any one of them keeps the split face a black box",
        "face": "preview/ledger-business-report.html",
    },
    {
        "id": "B6-t2-heritage",
        "title": "T2 heritage commercial line approval list",
        "path": "docs/spec/heritage-t2-spec.md",
        "anchor": r"\[needs-CEO\] 呈批清单",
        "action": "approve the pricing cases and the gate for the T2 pilot",
        "face": "preview/index.html",
    },
    {
        "id": "B7-msgseccheck-wiring",
        "title": "Production wiring of msgSecCheck (account-domain physical piece)",
        "path": "BLUEPRINT.md",
        "anchor": r"msgSecCheck 账号域物理件",
        "action": "supply the mini-program appid/secret so the content gate leaves the sandbox",
        "face": "preview/ugc-gate-report.html",
    },
    {
        "id": "B8-growth-hooks",
        "title": "Growth hooks: join-benefit grants and referral reward parameters",
        "path": "BLUEPRINT.md",
        "anchor": r"入群权益钩/裂变奖励参数",
        "action": "approve the hook values; the funnel design already maps every segment to a shipped face",
        "face": "preview/index.html",
    },
]

# Declared derivation rules, applied to the QUOTED text in order. The first
# match wins; no match reads UNKNOWN and the row says why.
RULES = [
    (r"零到位", "PENDING-PHYSICAL", "source says zero delivery after a stated interval"),
    (r"未到", "PENDING-PHYSICAL", "source says the piece has not arrived"),
    (r"blocked on CEO", "PENDING-PHYSICAL", "source states the block explicitly"),
    (r"物理件", "PENDING-PHYSICAL", "source names a physical piece as the block"),
    (r"\[needs-CEO\]", "PENDING-DECISION", "source marks the value as a CEO-only approval"),
    (r"CEO 保留面", "PENDING-DECISION", "source names the matter as a CEO reserved decision"),
    (r"呈批", "PENDING-DECISION", "source routes the value to the approval face"),
]

BANNER = "This page only collects what is blocked. It decides nothing and it approves nothing."
DISCLAIMER = "Non-advisory notice: this is a production status page, not investment advice."

AC_CBX = [
    "AC-CBX1 every row resolves: source file exists, anchor matches exactly one line, and the quote equals that line's byte window",
    "AC-CBX2 anchors are distinct across rows, so no two rows can silently duplicate one another",
    "AC-CBX3 every status is derived by a declared rule; an unmatched row reads UNKNOWN and records rule=none",
    "AC-CBX4 every row's face artifact exists on disk, and a missing one reads MISSING instead of vanishing",
    "AC-CBX5 --check must not rewrite the artifacts it verifies (size+mtime self control)",
    "AC-CBX6 the page carries zero network literals and therefore opens offline",
    "AC-CBX7 the sizes block is a self-referential fixed point equal to the disk bytes",
    "AC-CBX8 the page renders exactly one card per registry row and the header count equals the row count",
    "AC-CBX9 the standing no-decision banner, the non-advisory notice and the live tick are present and derived",
]


def _read(path):
    with io.open(path, encoding="utf-8-sig") as fh:
        return fh.read()


def _slim(text, limit=160):
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1] + "\u2026"


def derive_status(quote):
    for pattern, verdict, reason in RULES:
        if re.search(pattern, quote):
            return verdict, reason
    return "UNKNOWN", "no declared rule matched the quoted text"


def resolve_row(row):
    """Resolve one pointer against the tree as it stands RIGHT NOW."""
    out = dict(row)
    abs_path = os.path.join(REPO, row["path"])
    out["exists"] = os.path.isfile(abs_path)
    out["lineno"] = None
    out["quote"] = ""
    out["quote_truncated"] = False
    out["status"] = "UNKNOWN"
    out["reason"] = "source file missing"
    out["resolved"] = False
    if not out["exists"]:
        return out
    try:
        text = _read(abs_path)
    except Exception as exc:  # noqa: BLE001 - a read failure is a row state, not a crash
        out["reason"] = "source unreadable: %s" % exc.__class__.__name__
        return out
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        m = re.search(row["anchor"], line)
        if m:
            hits.append((lineno, line, m))
    if len(hits) != 1:
        out["reason"] = "anchor matched %d lines, expected exactly one" % len(hits)
        out["lineno"] = hits[0][0] if hits else None
        return out
    lineno, line, m = hits[0]
    window = line[m.start(): m.start() + QUOTE_CHARS]
    out["lineno"] = lineno
    out["quote"] = window
    out["quote_truncated"] = len(line) - m.start() > QUOTE_CHARS
    out["status"], out["reason"] = derive_status(window)
    out["resolved"] = True
    return out


def face_state(face_rel):
    abs_path = os.path.join(REPO, face_rel)
    if not os.path.isfile(abs_path):
        return {"path": face_rel, "state": "MISSING", "bytes": None}
    return {"path": face_rel, "state": "PRESENT", "bytes": os.path.getsize(abs_path)}


def live_tick():
    try:
        state = json.loads(_read(STATE_PATH))
        return str(state.get("tick"))
    except Exception:  # noqa: BLE001 - tick absence must not invent a number
        return "unknown"


def collect():
    rows = []
    for row in BLOCKERS:
        resolved = resolve_row(row)
        resolved["face_state"] = face_state(row["face"])
        rows.append(resolved)
    counts = {"total": len(rows)}
    for verdict in ("PENDING-PHYSICAL", "PENDING-DECISION", "UNKNOWN"):
        counts[verdict] = sum(1 for r in rows if r["status"] == verdict)
    counts["faces_missing"] = sum(1 for r in rows if r["face_state"]["state"] != "PRESENT")
    return {"tick": live_tick(), "rows": rows, "counts": counts}


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _card(row):
    badge = {
        "PENDING-PHYSICAL": "phys",
        "PENDING-DECISION": "dec",
        "UNKNOWN": "unk",
    }.get(row["status"], "unk")
    where = "%s:%s" % (row["path"], row["lineno"] if row["lineno"] else "-")
    truncated = " (quoted window, rest of line omitted)" if row["quote_truncated"] else ""
    face = row["face_state"]
    face_line = (
        "%s &middot; %s B" % (_esc(face["path"]), face["bytes"])
        if face["state"] == "PRESENT"
        else "%s &middot; MISSING" % _esc(face["path"])
    )
    return "".join(
        [
            '<div class="card %s" id="%s">' % (badge, _esc(row["id"])),
            '<div class="hd"><span class="badge %s">%s</span><span class="tid">%s</span></div>'
            % (badge, _esc(row["status"]), _esc(row["id"])),
            '<p class="title">%s</p>' % _esc(row["title"]),
            '<p class="quote">&ldquo;%s%s&rdquo;</p>' % (_esc(row["quote"]), "&hellip;" if row["quote_truncated"] else ""),
            '<p class="src">DERIVED from %s%s</p>' % (_esc(where), truncated),
            '<p class="why">rule: %s</p>' % _esc(row["reason"]),
            '<p class="act">DECLARED action: %s</p>' % _esc(row["action"]),
            '<p class="face">face: %s</p>' % face_line,
            "</div>",
        ]
    )


def render_html(doc):
    counts = doc["counts"]
    head = "".join(
        [
            "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">",
            "<title>BigDomain &middot; what only the CEO can unblock</title>",
            "<style>",
            "body{font:15px/1.55 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;margin:0;background:#12140f;color:#e8e6df}",
            ".wrap{max-width:980px;margin:0 auto;padding:32px 20px 64px}",
            "h1{font-size:24px;margin:0 0 6px}",
            ".sub{color:#9a9b90;margin:0 0 20px;font-size:13px}",
            ".banner{border-left:3px solid #c8a24a;background:#1c1e18;padding:12px 14px;margin:0 0 8px;font-size:14px}",
            ".disc{color:#8d8e83;font-size:12px;margin:0 0 24px}",
            ".tally{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 22px;font-size:13px}",
            ".tally span{background:#1c1e18;border:1px solid #2c2f26;border-radius:999px;padding:4px 12px}",
            ".card{background:#1a1c16;border:1px solid #2c2f26;border-radius:10px;padding:16px 18px;margin:0 0 14px}",
            ".hd{display:flex;align-items:center;gap:10px;margin:0 0 8px}",
            ".badge{font-size:11px;letter-spacing:.04em;padding:3px 9px;border-radius:999px;border:1px solid}",
            ".badge.phys{color:#e0b25a;border-color:#6b5320}",
            ".badge.dec{color:#7fb2e5;border-color:#2b4a63}",
            ".badge.unk{color:#c9c9c9;border-color:#4a4a4a}",
            ".tid{color:#7d7e74;font-size:12px}",
            ".title{margin:0 0 10px;font-weight:600}",
            ".quote{margin:0 0 8px;padding:10px 12px;background:#0e100c;border-radius:8px;color:#d6d4c8;font-size:14px}",
            ".src,.why,.face{margin:0 0 4px;color:#8d8e83;font-size:12px}",
            ".act{margin:10px 0 6px;color:#d8d6ca;font-size:13px}",
            "footer{color:#6f7066;font-size:12px;margin-top:26px}",
            "</style></head><body><div class=\"wrap\">",
            "<h1>What only the CEO can unblock</h1>",
            '<p class="sub">Every quote below is resolved from its source file at render time. Tick %s &middot; %s rows &middot; generated by tools/ceo_blockers.py</p>'
            % (_esc(doc["tick"]), counts["total"]),
            '<div class="banner">%s</div>' % _esc(BANNER),
            '<p class="disc">%s</p>' % _esc(DISCLAIMER),
            '<div class="tally">',
            "<span>%d rows</span>" % counts["total"],
            "<span>PENDING-PHYSICAL %d</span>" % counts["PENDING-PHYSICAL"],
            "<span>PENDING-DECISION %d</span>" % counts["PENDING-DECISION"],
            "<span>UNKNOWN %d</span>" % counts["UNKNOWN"],
            "<span>faces missing %d</span>" % counts["faces_missing"],
            "</div>",
        ]
    )
    body = "".join(_card(r) for r in doc["rows"])
    foot = (
        "<footer>%d of %d quoted rows resolved to a real source line. "
        "A row reading UNKNOWN means no declared rule matched the text the source actually carries, "
        "not that the block is gone.</footer></div></body></html>"
        % (sum(1 for r in doc["rows"] if r["resolved"]), counts["total"])
    )
    return head + body + foot


def render_both():
    """Iterate to a fixed point so the sizes block equals the disk bytes."""
    doc = collect()
    doc["sizes"] = {"html": 0, "json": 0}
    html = ""
    payload = ""
    for _ in range(8):
        html = render_html(doc)
        doc["sizes"] = {"html": len(html.encode("utf-8")), "json": doc["sizes"]["json"]}
        payload = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        size = len(payload.encode("utf-8"))
        if doc["sizes"]["json"] == size:
            break
        doc["sizes"]["json"] = size
    html = render_html(doc)
    doc["sizes"] = {"html": len(html.encode("utf-8")), "json": len(payload.encode("utf-8"))}
    payload = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    return html, payload


def write_artifacts():
    html, payload = render_both()
    os.makedirs(os.path.dirname(HTML_PATH), exist_ok=True)
    with io.open(HTML_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    with io.open(JSON_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload)
    return html, payload


def check():
    results = []
    doc = collect()
    rows = doc["rows"]

    unresolved = [r["id"] for r in rows if not r["resolved"]]
    results.append(("AC-CBX1", not unresolved, "unresolved=%s" % (unresolved or "none")))

    keys = [(r["path"], r["anchor"]) for r in rows]
    dupes = sorted({k[1] for k in keys if keys.count(k) > 1})
    results.append(("AC-CBX2", not dupes, "duplicate_anchors=%s" % (dupes or "none")))

    bad_status = [r["id"] for r in rows if r["status"] not in ("PENDING-PHYSICAL", "PENDING-DECISION", "UNKNOWN")]
    unknown = [r["id"] for r in rows if r["status"] == "UNKNOWN"]
    results.append(
        (
            "AC-CBX3",
            not bad_status,
            "unknown_rows=%s (allowed, named rather than hidden)" % (unknown or "none"),
        )
    )

    missing = [r["id"] for r in rows if r["face_state"]["state"] != "PRESENT"]
    results.append(("AC-CBX4", not missing, "faces_missing=%s" % (missing or "none")))

    for path in (HTML_PATH, JSON_PATH):
        if not os.path.isfile(path):
            results.append(("AC-CBX5", False, "artifact absent: %s" % os.path.basename(path)))
            break
    else:
        before = {p: (os.path.getsize(p), os.path.getmtime(p)) for p in (HTML_PATH, JSON_PATH)}
        lands = check_landed(doc)
        after = {p: (os.path.getsize(p), os.path.getmtime(p)) for p in (HTML_PATH, JSON_PATH)}
        results.append(("AC-CBX5", before == after, "artifacts untouched by --check=%s" % (before == after)))
        results.extend(lands)

    html = _read(HTML_PATH) if os.path.isfile(HTML_PATH) else ""
    literal = re.search(r"https?://[A-Za-z0-9]", html)
    results.append(("AC-CBX6", literal is None, "network_literal=%s" % (literal.group(0) if literal else "none")))

    return results


def check_landed(doc):
    out = []
    try:
        landed = json.loads(_read(JSON_PATH))
    except Exception as exc:  # noqa: BLE001
        return [("AC-CBX7", False, "json unreadable: %s" % exc.__class__.__name__)]
    sizes = landed.get("sizes") or {}
    disk = {"html": os.path.getsize(HTML_PATH), "json": os.path.getsize(JSON_PATH)}
    out.append(("AC-CBX7", sizes.get("html") == disk["html"] and sizes.get("json") == disk["json"], "sizes=%s disk=%s" % (sizes, disk)))

    html = _read(HTML_PATH)
    cards = html.count('<div class="card ')
    header = re.search(r"(\d+) rows &middot; generated by", html)
    ok = cards == len(doc["rows"]) and header is not None and int(header.group(1)) == len(doc["rows"])
    out.append(("AC-CBX8", ok, "cards=%d header=%s registry=%d" % (cards, header.group(1) if header else "absent", len(doc["rows"]))))

    ok9 = BANNER in html and DISCLAIMER in html and ("Tick %s" % doc["tick"]) in html
    out.append(("AC-CBX9", ok9, "banner=%s disclaimer=%s tick=%s" % (BANNER in html, DISCLAIMER in html, doc["tick"])))
    return out


def main(argv):
    if "--check" in argv:
        results = check()
        failed = [name for name, ok, _ in results if not ok]
        for name, ok, detail in results:
            print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
        print("VERDICT %s %d/%d" % ("PASS" if not failed else "FAIL", len(results) - len(failed), len(results)))
        return 0 if not failed else 2
    html, payload = write_artifacts()
    print("WROTE html=%dB json=%dB rows=%d" % (len(html.encode("utf-8")), len(payload.encode("utf-8")), len(BLOCKERS)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
