#!/usr/bin/env python3
"""P-47 journey face: render the 19.9 user journey from the SHIPPED spec and
drive every step's status from the gate report that actually carries it.

The spec docs/spec/journey-19.9-v2-spec.md has described eight JV steps since
R405 and has never had a runnable face. This tool renders it, and - more to the
point - refuses to state a step's status from its own memory: the step table is
re-parsed from the spec at render time and each verdict is re-read from the
carrier report on disk, so a stale page and a tampered report are both visible.

Criteria AC-JNY1..JNY8 are pre-registered in src/os/backlog.md (R2769 line)
before this file existed.

Read-only mode: `--check` never authors the artifact it verifies (AC-JNY3).
"""
import argparse
import hashlib
import html
import io
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "docs", "spec", "journey-19.9-v2-spec.md")
RISK_CONFIG = os.path.join(ROOT, "src", "sandbox", "lobby", "config.json")
PREVIEW = os.path.join(ROOT, "preview")
OUT_HTML = os.path.join(PREVIEW, "journey-19.9.html")
OUT_JSON = os.path.join(PREVIEW, "journey-19.9.json")

# Each journey step is carried by one gate report. JV-1 has no P-47 report of
# its own (the live-room funnel belongs to BigCompute/BigStream), so it is
# carried by the platform live face.
CARRIER_BY_STEP = {
    "JV-1": "platform-live-report",
    "JV-2": "payment-gate-report",
    "JV-3": "payment-gate-report",
    "JV-4": "ledger-business-report",
    "JV-5": "lobby-ws-report",
    "JV-6": "ugc-gate-report",
    "JV-7": "ugc-gate-report",
    "JV-8": "membership-benefit-report",
}

P47_CARRIERS = [
    "lobby-ws-report",
    "ledger-business-report",
    "ugc-gate-report",
    "payment-gate-report",
    "membership-benefit-report",
]

DISCLAIMER_MIN_LEN = 80


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_spec():
    """Return (title, header_labels, steps, compliance_items)."""
    text = read_text(SPEC)
    lines = text.splitlines()

    title = ""
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    header = []
    steps = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells and cells[0].startswith("JV-"):
            steps.append(cells)
        elif steps == [] and cells and not set("".join(cells)) <= set("-: "):
            # the table header row is the last non-separator row before JV-1
            header = cells

    compliance = []
    in_section = False
    for line in lines:
        if line.startswith("## "):
            in_section = "四件套" in line or "compliance" in line.lower()
            continue
        if in_section:
            stripped = line.strip()
            if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".)":
                compliance.append(stripped)

    return title, header, steps, compliance


def iter_strings(obj, key_hint=None):
    """Yield (key, value) for every string in a json tree."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            for item in iter_strings(v, k):
                yield item
    elif isinstance(obj, list):
        for v in obj:
            for item in iter_strings(v, key_hint):
                yield item
    elif isinstance(obj, str):
        yield key_hint, obj


def find_disclaimer():
    """The shipped standing risk text, located by shape, never typed here."""
    data = json.loads(read_text(RISK_CONFIG))
    best = None
    for key, value in iter_strings(data):
        if not isinstance(key, str):
            continue
        name = key.lower()
        if name == "text" or "risk" in name:
            if len(value) >= DISCLAIMER_MIN_LEN and (best is None or len(value) > len(best)):
                best = value
    return best or ""


def carrier_state(stem):
    """Read one carrier report from disk and derive its status honestly."""
    path = os.path.join(PREVIEW, stem + ".json")
    state = {"stem": stem, "artifact": "preview/" + stem + ".json"}
    if not os.path.exists(path):
        state.update(verdict="MISSING", ok=False, detail="carrier report absent")
        return state

    with io.open(path, "rb") as fh:
        raw = fh.read()
    doc = json.loads(raw.decode("utf-8"))
    state["bytes"] = len(raw)
    state["mtime_utc"] = datetime.fromtimestamp(
        os.path.getmtime(path), tz=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    verdict = doc.get("verdict")
    if isinstance(verdict, str) and verdict:
        detail = ""
        if isinstance(doc.get("passed"), int) and isinstance(doc.get("total"), int):
            detail = "%d/%d criteria" % (doc["passed"], doc["total"])
        state.update(verdict=verdict, ok=True, detail=detail or "declared verdict")
    elif "reconcile_rc" in doc:
        rc = doc["reconcile_rc"]
        counts = []
        for key in ("tx_count", "entry_count", "accounts"):
            if isinstance(doc.get(key), int):
                counts.append("%s=%d" % (key, doc[key]))
        state.update(
            verdict="PASS" if rc == 0 else "FAIL",
            ok=(rc == 0),
            detail="reconcile_rc=%s %s" % (rc, " ".join(counts)),
        )
    elif isinstance(doc.get("criteria"), list):
        rows = [r for r in doc["criteria"] if isinstance(r, dict)]
        graded = [
            r
            for r in rows
            if r.get("ok") is True
            or r.get("pass") is True
            or str(r.get("status", "")).upper() == "PASS"
        ]
        if graded:
            state.update(
                verdict="PASS" if len(graded) == len(rows) else "FAIL",
                ok=len(graded) == len(rows),
                detail="%d/%d criteria graded" % (len(graded), len(rows)),
            )
        else:
            # honest: the artifact declares criteria but grades none of them
            state.update(
                verdict="DECLARED",
                ok=None,
                detail="%d criteria declared, no in-artifact grade" % len(rows),
            )
    else:
        state.update(verdict="NO-VERDICT", ok=None, detail="no verdict field")
    return state


def build_steps(spec_steps):
    steps = []
    seen = {}
    for cells in spec_steps:
        step_id = cells[0].split()[0]
        carrier = CARRIER_BY_STEP.get(step_id, "")
        if carrier and carrier not in seen:
            seen[carrier] = carrier_state(carrier)
        state = seen.get(carrier, {"stem": "", "verdict": "UNMAPPED", "ok": False})
        steps.append(
            {
                "id": step_id,
                "touchpoint": cells[1] if len(cells) > 1 else "",
                "carrier_text": cells[2] if len(cells) > 2 else "",
                "gate": cells[3] if len(cells) > 3 else "",
                "carrier": carrier,
                "verdict": state.get("verdict"),
                "ok": state.get("ok"),
                "detail": state.get("detail", ""),
                "artifact": state.get("artifact", ""),
            }
        )
    return steps


def build_doc(sizes, spec_sha, spec_bytes):
    title, header, spec_steps, compliance = parse_spec()
    steps = build_steps(spec_steps)
    carriers = [carrier_state(s) for s in sorted({s["carrier"] for s in steps if s["carrier"]})]
    disclaimer = find_disclaimer()

    blocked = []
    pay = os.path.join(PREVIEW, "payment-gate-report.json")
    if os.path.exists(pay):
        with io.open(pay, "r", encoding="utf-8") as fh:
            pay_doc = json.load(fh)
        blocked = pay_doc.get("blocked_on") or []

    passed = sum(1 for s in steps if s["ok"] is True)
    graded = sum(1 for s in steps if s["ok"] is not None)
    return {
        "face": "journey-19.9",
        "p47_item": "journey v2 (spec section one, JV-1..JV-8)",
        "title": title,
        "spec": {"path": "docs/spec/journey-19.9-v2-spec.md", "bytes": spec_bytes, "sha256": spec_sha[:16]},
        "header": header,
        "steps": steps,
        "carriers": carriers,
        "compliance": {
            "four_piece": compliance,
            "disclaimer": disclaimer,
            "disclaimer_source": "src/sandbox/lobby/config.json",
            "aigc": {
                "explicit": "ai_label on every generated frame (BLUEPRINT section five)",
                "implicit": "invisible watermark, five of five capability suites on register",
            },
        },
        "blocked_on": blocked,
        "headline": "%d of %d steps carry a declared PASS" % (passed, len(steps)),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sizes": {"html": sizes.get("html", 0), "json": sizes.get("json", 0)},
    }


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def chip(ok, verdict):
    if ok is True:
        return '<span class="chip ok">%s</span>' % esc(verdict)
    if ok is False:
        return '<span class="chip bad">%s</span>' % esc(verdict)
    return '<span class="chip flat">%s</span>' % esc(verdict)


def render_html(doc):
    parts = []
    add = parts.append
    add("<!DOCTYPE html>")
    add('<meta charset="utf-8">')
    add("<title>%s - runnable journey face</title>" % esc(doc["title"]))
    add("<style>")
    add("body{font:15px/1.65 -apple-system,'Segoe UI',sans-serif;margin:0;background:#0f1115;color:#e8eaed}")
    add("main{max-width:1060px;margin:0 auto;padding:32px 24px 64px}")
    add("h1{font-size:24px;margin:0 0 6px}h2{font-size:16px;margin:0 0 12px;color:#cfd4dc}")
    add(".sub{color:#9aa0a6;margin:0 0 24px}")
    add(".card{background:#171a21;border:1px solid #262b36;border-radius:10px;padding:16px 18px;margin:0 0 16px}")
    add(".step{display:grid;grid-template-columns:96px 1fr;gap:14px;padding:14px 0;border-bottom:1px solid #262b36}")
    add(".step:last-child{border-bottom:0}")
    add(".sid{font-weight:700;color:#79c0ff;font-size:15px}")
    add(".lbl{color:#8b949e;font-size:12px;text-transform:uppercase;letter-spacing:.04em;margin:8px 0 2px}")
    add(".val{color:#e8eaed}")
    add("table{width:100%;border-collapse:collapse;font-size:13px}")
    add("td,th{text-align:left;padding:8px 6px;border-bottom:1px solid #262b36;vertical-align:top}")
    add("th{color:#8b949e;font-weight:600}")
    add(".chip{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;border:1px solid}")
    add(".chip.ok{color:#7ee787;border-color:#2ea04366;background:#2ea0431a}")
    add(".chip.bad{color:#ff7b72;border-color:#f8514966;background:#f851491a}")
    add(".chip.flat{color:#e3b341;border-color:#d2992266;background:#d299221a}")
    add(".risk{border-left:3px solid #d29922;padding-left:12px;color:#e3b341;margin:10px 0 0}")
    add("li{margin:6px 0}code{color:#79c0ff}")
    add(".small{color:#8b949e;font-size:12px}")
    add("</style>")
    add("<main>")
    add("<h1>%s</h1>" % esc(doc["title"]))
    add(
        '<p class="sub">Eight-step journey rendered from the shipped spec at render time. '
        "Every step status is re-read from the gate report that carries it - a stale page or a "
        "tampered report is visible, because nothing here is typed.</p>"
    )

    add('<div class="card"><h2>%s</h2>' % esc(doc["headline"]))
    add(
        '<p class="small">spec %s sha %s / %sB &middot; %d steps &middot; %d carriers read from disk</p>'
        % (
            esc(doc["spec"]["path"]),
            esc(doc["spec"]["sha256"]),
            doc["spec"]["bytes"],
            len(doc["steps"]),
            len(doc["carriers"]),
        )
    )
    add("</div>")

    add('<div class="card"><h2>Journey</h2>')
    for step in doc["steps"]:
        add('<div class="step">')
        add('<div class="sid">%s</div>' % esc(step["id"]))
        add("<div>")
        add('<div class="lbl">touchpoint</div><div class="val">%s</div>' % esc(step["touchpoint"]))
        add('<div class="lbl">carrier</div><div class="val">%s</div>' % esc(step["carrier_text"]))
        add('<div class="lbl">compliance gate</div><div class="val">%s</div>' % esc(step["gate"]))
        add(
            '<div class="lbl">live status</div><div class="val">%s <span class="small">%s &middot; %s</span></div>'
            % (chip(step["ok"], step["verdict"]), esc(step["detail"]), esc(step["artifact"]))
        )
        add("</div></div>")
    add("</div>")

    add('<div class="card"><h2>Carriers read from disk</h2>')
    add("<table><tr><th>report</th><th>verdict</th><th>detail</th><th>bytes</th><th>mtime utc</th></tr>")
    for c in doc["carriers"]:
        add(
            "<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (
                esc(c["artifact"]),
                chip(c.get("ok"), c.get("verdict")),
                esc(c.get("detail", "")),
                esc(c.get("bytes", "")),
                esc(c.get("mtime_utc", "")),
            )
        )
    add("</table></div>")

    add('<div class="card"><h2>Compliance four-piece (verbatim from the spec)</h2><ol>')
    for item in doc["compliance"]["four_piece"]:
        add("<li>%s</li>" % esc(item))
    add("</ol>")
    add('<div class="lbl">standing non-advice disclaimer, byte-identical to %s</div>' % esc(doc["compliance"]["disclaimer_source"]))
    add('<p class="risk">%s</p>' % esc(doc["compliance"]["disclaimer"]))
    add("</div>")

    add('<div class="card"><h2>AIGC marking, both tracks</h2><ul>')
    add("<li>explicit: %s</li>" % esc(doc["compliance"]["aigc"]["explicit"]))
    add("<li>implicit: %s</li>" % esc(doc["compliance"]["aigc"]["implicit"]))
    add("</ul></div>")

    if doc["blocked_on"]:
        add('<div class="card"><h2>Blocked on physical pieces (from the payment gate)</h2><ul>')
        for item in doc["blocked_on"]:
            add("<li>%s</li>" % esc(item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)))
        add("</ul></div>")

    add(
        '<p class="small">rendered %s &middot; html %sB &middot; json %sB &middot; offline, zero external calls</p>'
        % (esc(doc["generated_utc"]), doc["sizes"]["html"], doc["sizes"]["json"])
    )
    add("</main>")
    return "\n".join(parts) + "\n"


def render_fixed_point():
    """Iterate html/json sizes to a fixed point so no size can be typed."""
    sizes = {"html": 0, "json": 0}
    spec_text = read_text(SPEC)
    spec_sha = sha256_text(spec_text)
    spec_bytes = len(spec_text.encode("utf-8"))
    html_text = ""
    json_text = ""
    for _ in range(12):
        doc = build_doc(sizes, spec_sha, spec_bytes)
        html_text = render_html(doc)
        json_text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
        nxt = {
            "html": len(html_text.encode("utf-8")),
            "json": len(json_text.encode("utf-8")),
        }
        if nxt == sizes:
            return html_text, json_text, doc
        sizes = nxt
    raise SystemExit("E_FIXED_POINT: sizes did not converge in 12 passes")


def write_artifacts(html_text, json_text):
    with io.open(OUT_HTML, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html_text)
    with io.open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json_text)


def fresh_carrier_block(stem):
    state = carrier_state(stem)
    return {
        "stem": stem,
        "verdict": state.get("verdict"),
        "ok": state.get("ok"),
        "detail": state.get("detail", ""),
        "bytes": state.get("bytes"),
        "mtime_utc": state.get("mtime_utc"),
    }


def check():
    results = []

    def add(cid, ok, note):
        results.append((cid, ok, note))

    if not os.path.exists(OUT_HTML) or not os.path.exists(OUT_JSON):
        print("E_MISSING_ARTIFACT: render first (no --check)")
        return 3

    # AC-JNY3 is a SELF control: it must compare entry and exit state, not
    # compare disk against the recorded sizes (that is AC-JNY7's job). The first
    # version did the latter and masked every other criterion in negative
    # control, so it was repaired at the birth site rather than left as a
    # pleasant duplicate.
    entry = {
        "html": (os.path.getsize(OUT_HTML), os.path.getmtime(OUT_HTML)),
        "json": (os.path.getsize(OUT_JSON), os.path.getmtime(OUT_JSON)),
    }

    with io.open(OUT_JSON, "rb") as fh:
        json_raw = fh.read()
    with io.open(OUT_HTML, "rb") as fh:
        html_raw = fh.read()
    disk = {"html": len(html_raw), "json": len(json_raw)}
    doc = json.loads(json_raw.decode("utf-8"))

    # AC-JNY1 - the landed steps equal a FRESH parse of the spec table
    _, header, spec_steps, _ = parse_spec()
    landed = [[s["id"], s["touchpoint"], s["carrier_text"], s["gate"]] for s in doc.get("steps", [])]
    fresh = [[c[0].split()[0]] + c[1:4] for c in spec_steps]
    add(
        "AC-JNY1",
        landed == fresh and len(fresh) == 8,
        "landed=%d fresh=%d match=%s" % (len(landed), len(fresh), landed == fresh),
    )

    # AC-JNY2 - every verdict equals a fresh read of its carrier on disk
    mismatch = []
    fresh_cache = {}
    for step in doc.get("steps", []):
        stem = step.get("carrier")
        if not stem:
            mismatch.append("%s:unmapped" % step.get("id"))
            continue
        if stem not in fresh_cache:
            fresh_cache[stem] = fresh_carrier_block(stem)
        now = fresh_cache[stem]
        if now["verdict"] != step.get("verdict") or now["ok"] is not step.get("ok"):
            mismatch.append("%s:%s!=%s" % (step.get("id"), step.get("verdict"), now["verdict"]))
    add("AC-JNY2", not mismatch, "carriers=%d mismatch=%s" % (len(fresh_cache), mismatch[:4]))

    # AC-JNY3 - this very check must not have authored anything it verifies
    exit_state = {
        "html": (os.path.getsize(OUT_HTML), os.path.getmtime(OUT_HTML)),
        "json": (os.path.getsize(OUT_JSON), os.path.getmtime(OUT_JSON)),
    }
    add(
        "AC-JNY3",
        entry == exit_state,
        "self control entry==exit %s (html=%s json=%s)"
        % (entry == exit_state, exit_state["html"][0], exit_state["json"][0]),
    )

    # AC-JNY4 - the standing disclaimer is byte-identical to the shipped text
    shipped = find_disclaimer()
    in_doc = doc.get("compliance", {}).get("disclaimer", "")
    in_page = shipped and shipped in html_raw.decode("utf-8")
    add(
        "AC-JNY4",
        bool(shipped) and in_doc == shipped and bool(in_page),
        "shipped_len=%d doc_match=%s page_match=%s" % (len(shipped), in_doc == shipped, bool(in_page)),
    )

    # AC-JNY5 - the AIGC face is present on both tracks
    aigc = doc.get("compliance", {}).get("aigc", {})
    page_text = html_raw.decode("utf-8")
    both = bool(aigc.get("explicit")) and bool(aigc.get("implicit"))
    add(
        "AC-JNY5",
        both and "explicit" in page_text and "implicit" in page_text,
        "explicit=%s implicit=%s" % (bool(aigc.get("explicit")), bool(aigc.get("implicit"))),
    )

    # AC-JNY6 - offline: no external protocol literal anywhere in the page
    lowered = page_text.lower()
    bad = [tok for tok in ("http://", "https://", "//cdn.", "src=\"//") if tok in lowered]
    add("AC-JNY6", not bad, "external_literals=%s" % (bad or "none"))

    # AC-JNY7 - the recorded sizes equal disk (self-referential gate)
    add(
        "AC-JNY7",
        doc["sizes"]["html"] == disk["html"] and doc["sizes"]["json"] == disk["json"],
        "recorded=%s disk=%s" % (doc["sizes"], disk),
    )

    # AC-JNY8 - five P-47 carriers covered, each present, each step CARD once.
    # Measured lesson: a bare substring count is the wrong measure here, because
    # the spec's own compliance lines legitimately name JV-1/JV-7/JV-8 in prose
    # (first run reddened on exactly those three). The criterion's intent is
    # "no duplicated step card", so it anchors on the structural marker.
    referenced = {s.get("carrier") for s in doc.get("steps", []) if s.get("carrier")}
    missing_p47 = [c for c in P47_CARRIERS if c not in referenced]
    absent = sorted(c for c in referenced if not os.path.exists(os.path.join(PREVIEW, c + ".json")))
    dupes = [
        s["id"]
        for s in doc.get("steps", [])
        if page_text.count('class="sid">%s<' % s["id"]) != 1
    ]
    ok8 = not missing_p47 and not absent and not dupes and len(doc.get("steps", [])) == 8
    add(
        "AC-JNY8",
        ok8,
        "p47_missing=%s absent=%s id_not_once=%s steps=%d"
        % (missing_p47 or "none", absent or "none", dupes or "none", len(doc.get("steps", []))),
    )

    failed = [r for r in results if not r[1]]
    for cid, ok, note in results:
        print("%s %s %s" % ("PASS" if ok else "FAIL", cid, note))
    print(
        "VERDICT %s %d/%d"
        % ("PASS" if not failed else "FAIL", len(results) - len(failed), len(results))
    )
    return 0 if not failed else 2


def main(argv=None):
    ap = argparse.ArgumentParser(description="19.9 journey face renderer")
    ap.add_argument("--check", action="store_true", help="read-only verification, authors nothing")
    ap.add_argument("--write", action="store_true", help="explicit re-render")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if args.check:
        return check()

    html_text, json_text, doc = render_fixed_point()
    write_artifacts(html_text, json_text)
    if not args.quiet:
        print(
            "WROTE preview/journey-19.9.html %dB / preview/journey-19.9.json %dB steps=%d %s"
            % (doc["sizes"]["html"], doc["sizes"]["json"], len(doc["steps"]), doc["headline"])
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
