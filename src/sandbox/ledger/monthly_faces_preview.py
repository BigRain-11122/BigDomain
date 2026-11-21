"""R3193 product round: the first openable page over the shipped market
MONTHLY read faces.

Five market monthly faces already exist in the sandbox ledger
(api_market_months, api_market_supply_months, api_market_claim_months,
api_market_restock_months, api_market_discount_months) but the review
index preview/index.html only lists the settlement report family, so a
reader cannot see any of them without writing code. This generator
renders one self-contained HTML page plus one JSON payload from a
deterministic demo world and nothing else:

  * zero new read faces, zero new tables, zero business semantics;
  * the world comes from the shipped apimarket_report.seed_demo, so the
    page replays byte-identically and never touches a real transaction;
  * every visible string (titles, field names, empty states, the AIGC
    label and the non-advisory disclaimer) is loaded from
    preview/monthly-faces-copy.json, so this source stays pure ASCII;
  * the shipped preview/apimarket.db snapshot is never opened for write
    and its bytes are re-checked before the run reports PASS.

Usage:
  python src/sandbox/ledger/monthly_faces_preview.py
  python src/sandbox/ledger/monthly_faces_preview.py --verify \
      --log qa/preview-monthly-faces-R3193.log

Criteria AC-MFR1..AC-MFR8 are registered in src/os/backlog.md (R3193
PIN row) BEFORE this file existed.
"""
import argparse
import hashlib
import html
import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
LEDGER = os.path.join(BASE, "src", "sandbox", "ledger")
if LEDGER not in sys.path:
    sys.path.insert(0, LEDGER)

import apimarket_report as R  # noqa: E402

COPY_PATH = os.path.join(BASE, "preview", "monthly-faces-copy.json")
SNAPSHOT = os.path.join(BASE, "preview", "apimarket.db")
OUT_HTML = os.path.join(BASE, "preview", "apimarket-monthly-faces.html")
OUT_JSON = os.path.join(BASE, "preview", "apimarket-monthly-faces.json")

FACES = [
    "api_market_months",
    "api_market_supply_months",
    "api_market_claim_months",
    "api_market_restock_months",
    "api_market_discount_months",
]

# (row key, envelope key) pairs that must sum to the envelope total.
IDENTITY = {
    "api_market_months": [
        ("sales_count", "lifetime_sales_count"),
        ("gross", "lifetime_gross"),
        ("refund_count", "lifetime_refund_count"),
        ("refunded", "lifetime_refunded"),
        ("net", "lifetime_net"),
    ],
    "api_market_supply_months": [
        ("opened_count", "opened_total"),
        ("units_sold", "units_sold_total"),
        ("units_added", "units_added_total"),
    ],
    "api_market_restock_months": [
        ("restock_count", "restock_count"),
        ("units_added", "units_added"),
    ],
    "api_market_claim_months": [],
    "api_market_discount_months": [],
}


def sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def load_copy(path=COPY_PATH):
    with io.open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def collect(tmp_root):
    """Build the deterministic demo world in a private dir and read the
    five market monthly faces. Returns the ordered payload list."""
    db = os.path.join(tmp_root, "monthly-faces.db")
    led = mtr = dk = am = None
    payload = []
    led, mtr, dk, am = R.build_stack(db)
    try:
        R.seed_demo(am, led, dk)
        for fn in FACES:
            env = getattr(am, fn)()
            months = env.get("months") or []
            payload.append({
                "fn": fn,
                "key_count": len(env),
                "month_count": len(months),
                "first_month": env.get("first_month"),
                "last_month": env.get("last_month"),
                "envelope": env,
                "months": months,
            })
    finally:
        am.close()
        dk.close()
        mtr.close()
        led.close()
    return payload


def fmt(value):
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if abs(value - round(value)) < 1e-9:
            return str(int(round(value)))
        return ("%.2f" % value).rstrip("0").rstrip(".")
    return str(value)


def month_next(month):
    year, mm = month.split("-")
    year, mm = int(year), int(mm)
    if mm == 12:
        return "%04d-01" % (year + 1)
    return "%04d-%02d" % (year, mm + 1)


def numeric_columns(months):
    cols = []
    for key in months[0].keys():
        if key == "month" or key == "as_of":
            continue
        if isinstance(months[0][key], str):
            continue
        cols.append(key)
        if len(cols) >= 8:
            break
    return cols


def render_html(copy, faces):
    esc = html.escape
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="zh-CN"><head><meta charset="UTF-8">')
    parts.append('<meta name="viewport" content="width=device-width, '
                 'initial-scale=1.0">')
    parts.append("<title>%s</title>" % esc(copy["title"]))
    parts.append("""<style>
  :root { --ink:#182033; --muted:#6b7280; --line:#e5e7eb; --bg:#f7f8fa;
          --accent:#3b5bdb; --ok:#2f9e44; --warn:#e8590c; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;
         color:var(--ink); background:var(--bg); line-height:1.65;
         padding:0 0 48px; }
  .wrap { max-width:960px; margin:0 auto; padding:0 20px; }
  header { background:linear-gradient(135deg,#1f2b4d,#3b5bdb); color:#fff;
           padding:32px 0 24px; }
  header h1 { font-size:24px; letter-spacing:1px; }
  header .sub { margin-top:6px; font-size:14px; opacity:.92; }
  .badges { margin-top:14px; display:flex; gap:8px; flex-wrap:wrap; }
  .badge { font-size:12px; border:1px solid rgba(255,255,255,.55);
           border-radius:999px; padding:2px 10px; }
  .badge.ai { background:#fff; color:#1f2b4d; font-weight:700;
              border-color:#fff; }
  .card { background:#fff; border:1px solid var(--line); border-radius:8px;
          padding:16px 18px; margin:18px 0; }
  .card h2 { font-size:16px; margin-bottom:4px; }
  .card .src { font-size:12px; color:var(--muted); margin-bottom:10px; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th,td { border-bottom:1px solid var(--line); padding:7px 10px;
          text-align:right; }
  th:first-child,td:first-child { text-align:left; }
  th { background:#eef1f6; font-size:12px; }
  .empty { background:#fff8f0; border:1px dashed #ffc078; color:#8a4b08;
           border-radius:6px; padding:10px 12px; font-size:13px; }
  .kv { font-size:12px; color:var(--muted); margin:8px 0 0; }
  footer { max-width:960px; margin:8px auto 0; padding:0 20px;
           font-size:12px; color:var(--muted); }
  footer .dis { background:#fff; border:1px solid var(--line);
                border-radius:8px; padding:12px 14px; margin-top:10px; }
</style>""")
    parts.append("</head><body>")
    parts.append('<header><div class="wrap">')
    parts.append("<h1>%s</h1>" % esc(copy["title"]))
    parts.append('<div class="sub">%s</div>' % esc(copy["subtitle"]))
    parts.append('<div class="badges">')
    parts.append('<span class="badge ai">%s</span>' % esc(copy["aigc_label"]))
    parts.append('<span class="badge">%s</span>'
                 % esc(copy["source_note"]))
    parts.append("</div></div></header>")
    parts.append('<div class="wrap">')
    parts.append('<p class="kv">%s</p>' % esc(copy["section_note"]))
    for face in faces:
        fn = face["fn"]
        label = copy["faces"].get(fn, fn)
        parts.append('<div class="card">')
        parts.append("<h2>%s</h2>" % esc(label))
        parts.append('<div class="src">%s</div>'
                     % esc(copy["src_line"]
                           % (fn, face["key_count"], face["month_count"])))
        months = face["months"]
        if not months:
            msg = copy["empty"].get(fn, copy["empty_default"])
            parts.append('<div class="empty">%s</div>' % esc(msg))
        else:
            cols = numeric_columns(months)
            parts.append("<table><thead><tr><th>%s</th>"
                         % esc(copy["fields"].get("month", "month")))
            for col in cols:
                parts.append("<th>%s</th>"
                             % esc(copy["fields"].get(col, col)))
            parts.append("</tr></thead><tbody>")
            for row in months:
                parts.append("<tr><td>%s</td>" % esc(str(row.get("month"))))
                for col in cols:
                    parts.append("<td>%s</td>" % esc(fmt(row.get(col))))
                parts.append("</tr>")
            parts.append("</tbody></table>")
            if fn in copy["empty"]:
                parts.append('<p class="kv">%s</p>' % esc(copy["empty"][fn]))
        scalars = []
        for key, value in face["envelope"].items():
            if key in ("months", "disclaimer"):
                continue
            if isinstance(value, (list, dict)):
                continue
            scalars.append("%s=%s" % (copy["fields"].get(key, key),
                                      fmt(value)))
            if len(scalars) >= 8:
                break
        if scalars:
            parts.append('<p class="kv">%s</p>'
                         % esc(copy["sep"].join(scalars)))
        parts.append("</div>")
    parts.append("</div>")
    parts.append("<footer>")
    parts.append('<div class="dis">%s</div>' % esc(copy["disclaimer"]))
    parts.append('<p class="kv">%s</p>' % esc(copy["footer_note"]))
    parts.append("</footer>")
    parts.append("</body></html>")
    return "\n".join(parts) + "\n"


def render_json(faces):
    payload = {"source": "apimarket_report.seed_demo",
               "faces": faces}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      indent=2) + "\n"


def write_outputs(faces, copy, out_html, out_json):
    with io.open(out_html, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_html(copy, faces))
    with io.open(out_json, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_json(faces))


def check_identity(faces, problems):
    for face in faces:
        fn = face["fn"]
        env = face["envelope"]
        months = face["months"]
        if face["month_count"] != len(months):
            problems.append("%s month_count != len(months)" % fn)
        if not months:
            if env.get("month_count") not in (0, None):
                problems.append("%s empty but month_count=%r"
                                % (fn, env.get("month_count")))
            continue
        stamps = [row["month"] for row in months]
        if stamps != sorted(stamps):
            problems.append("%s months not ascending" % fn)
        for left, right in zip(stamps, stamps[1:]):
            if month_next(left) != right:
                problems.append("%s month grid gap %s -> %s"
                                % (fn, left, right))
        for row_key, env_key in IDENTITY.get(fn, []):
            if env_key not in env:
                problems.append("%s envelope lacks %s" % (fn, env_key))
                continue
            total = sum(row.get(row_key) or 0 for row in months)
            if total != env.get(env_key):
                problems.append("%s sum(%s)=%r != %s=%r"
                                % (fn, row_key, total, env_key,
                                   env.get(env_key)))
        for key in months[0].keys():
            if key.startswith("running_") and key in env:
                if months[-1].get(key) != env.get(key):
                    problems.append("%s %s last=%r != envelope %r"
                                    % (fn, key, months[-1].get(key),
                                       env.get(key)))


def run_verify(copy, log_path):
    lines = []
    problems = []

    def say(text):
        lines.append(text)

    snap_before = (os.path.getsize(SNAPSHOT), sha16(SNAPSHOT))
    dirs = []
    try:
        runs = []
        for _ in range(2):
            tmp = tempfile.mkdtemp(prefix="monthly-faces-")
            dirs.append(tmp)
            faces = collect(tmp)
            check_identity(faces, problems)
            out_html = os.path.join(tmp, "page.html")
            out_json = os.path.join(tmp, "page.json")
            write_outputs(faces, copy, out_html, out_json)
            runs.append((sha16(out_html), sha16(out_json), faces))
        say("AC-MFR2 determinism html=%s json=%s"
            % ("same" if runs[0][0] == runs[1][0] else "DIFF",
               "same" if runs[0][1] == runs[1][1] else "DIFF"))
        if runs[0][0] != runs[1][0] or runs[0][1] != runs[1][1]:
            problems.append("two runs are not byte-identical")
        faces = runs[0][2]
        for face in faces:
            say("AC-MFR3 face %s keys=%d months=%d first=%s last=%s"
                % (face["fn"], face["key_count"], face["month_count"],
                   face["first_month"], face["last_month"]))
        page = io.open(os.path.join(dirs[0], "page.html"),
                       encoding="utf-8").read()
        if copy["aigc_label"] not in page:
            problems.append("page lacks the AIGC label")
        if copy["disclaimer"] not in page:
            problems.append("page lacks the non-advisory disclaimer")
        if "http://" in page or "https://" in page:
            problems.append("page carries an external reference")
        for face in faces:
            if face["month_count"] == 0 and face["fn"] in copy["empty"]:
                if copy["empty"][face["fn"]] not in page:
                    problems.append("%s empty state not rendered"
                                    % face["fn"])
        say("AC-MFR1/4/5 contract+empty+compliance html_bytes=%d json_bytes=%d"
            % (os.path.getsize(os.path.join(dirs[0], "page.html")),
               os.path.getsize(os.path.join(dirs[0], "page.json"))))
        snap_after = (os.path.getsize(SNAPSHOT), sha16(SNAPSHOT))
        say("AC-MFR7 snapshot size=%d sha16=%s unchanged=%s"
            % (snap_after[0], snap_after[1], snap_before == snap_after))
        if snap_before != snap_after:
            problems.append("preview/apimarket.db changed during the run")
    finally:
        for tmp in dirs:
            shutil.rmtree(tmp, ignore_errors=True)
    if problems:
        say("VERIFY FAIL problems=%d" % len(problems))
        for item in problems:
            say("  %s" % item)
    else:
        say("VERIFY PASS criteria=AC-MFR1..AC-MFR8 (MFR6 index entry and "
            "MFR8 hygiene checked by the caller)")
    text = "\n".join(lines) + "\n"
    if log_path:
        with io.open(log_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    sys.stdout.write(text)
    return 0 if not problems else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=OUT_HTML)
    parser.add_argument("--json-out", default=OUT_JSON)
    parser.add_argument("--copy", default=COPY_PATH)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--log", default=None)
    args = parser.parse_args(argv)
    copy = load_copy(args.copy)
    if args.verify:
        return run_verify(copy, args.log)
    tmp = tempfile.mkdtemp(prefix="monthly-faces-")
    try:
        faces = collect(tmp)
        problems = []
        check_identity(faces, problems)
        if problems:
            for item in problems:
                sys.stdout.write("FAIL %s\n" % item)
            return 1
        write_outputs(faces, copy, args.out, args.json_out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("PASS preview %s (%d bytes) + %s (%d bytes)"
          % (os.path.relpath(args.out, BASE), os.path.getsize(args.out),
             os.path.relpath(args.json_out, BASE),
             os.path.getsize(args.json_out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
