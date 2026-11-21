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

Exit codes: 0 written or verified, 1 identity problems (VERIFY FAIL), and
2 refused by name (E_MFP_COPY: the copy file cannot drive this renderer;
E_MFP_WRITE: the delivered files cannot be rendered, staged or swapped).

Criteria AC-MFR1..AC-MFR8 are registered in src/os/backlog.md (R3193
PIN row) BEFORE this file existed.

R3195 (AC-MFPC1..AC-MFPC6): the copy file is a contract, not a
convenience. Every top-level key this renderer reads is listed in
REQUIRED_COPY_KEYS and load_copy refuses a file that drops one with the
named code E_MFP_COPY, BEFORE any output file is opened - until this
window a missing key raised a bare KeyError (rc=1, 14 traceback lines,
empty stdout) and left a zero-byte page.html behind. A copy file that
is not a JSON object is refused the same way, and extra unread keys are
tolerated so a newer copy file still renders here. The healthy render
stays byte-identical: the refusal never touches what is written.

R3196 (AC-MFPR1..AC-MFPR5): the reading itself is refused by name too.
A path that does not exist, bytes that are not UTF-8 and malformed JSON
used to escape as FileNotFoundError, UnicodeDecodeError and
JSONDecodeError (rc=1, empty stdout, a traceback, and - for the CLI - no
output file either). All three now answer the same E_MFP_COPY code at
rc=2 with the underlying reader type named in the detail, where the old
shapes kept one code per family apart only by prose.

R3197 (AC-MFPW1..AC-MFPW6): a render-time failure no longer damages the
delivered files. write_outputs used to open each target and render into
it, so an exception truncated the previous page to zero bytes (measured:
1800B -> 0B) and left the JSON untouched, or truncated the JSON and left
a fresh page. Both texts are now rendered before any target is opened,
each goes to a temp file beside its target, and os.replace is the only
write to a delivered path. The CLI face is unchanged on purpose: the
same exception still reaches the caller, so rc and the traceback stay as
they were - what changed is what is left on disk.

R3198 (AC-MFPX1..AC-MFPX2): the CLI face of a write failure is named
too. A render, stage or swap failure used to escape as the raw exception
(rc=1, empty stdout, a 13-line traceback) while the disk stayed intact.
The three stages now answer one E_MFP_WRITE line at rc=2 with the stage
and the underlying exception type in the detail, and the caught
exception stays reachable as __cause__. The healthy run is untouched:
rc=0, the same "PASS preview" line, the same 6834B/13015B bytes.
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


# Every top-level copy key render_html reads, in document order. The
# contract pin is src/os/backlog.md R3195 PIN (AC-MFPC1..AC-MFPC6); a key
# missing here raises a bare KeyError in the renderer, and empty_default
# is REQUIRED even for a world where every empty face has its own entry,
# because copy["empty"].get(fn, copy["empty_default"]) evaluates its
# default eagerly.
REQUIRED_COPY_KEYS = (
    "title",
    "subtitle",
    "aigc_label",
    "source_note",
    "section_note",
    "src_line",
    "sep",
    "empty",
    "empty_default",
    "fields",
    "faces",
    "disclaimer",
    "footer_note",
)


class CopyError(Exception):
    """Named refusal for a copy file that cannot drive this renderer."""

    code = "E_MFP_COPY"

    def __init__(self, detail):
        Exception.__init__(self, detail)
        self.detail = detail

    def face(self):
        return "%s %s" % (self.code, self.detail)


def _one_line(text, limit=160):
    """Collapse a reader message to one bounded line."""
    flat = " ".join(str(text).split())
    if len(flat) > limit:
        flat = flat[:limit] + "..."
    return flat


class WriteError(Exception):
    """Named refusal for a failed render, stage or swap of the outputs.

    All three stages mean the same thing to a caller - the delivered
    files cannot be produced - so they share one code and name the stage
    plus the underlying exception type in the detail.
    """

    code = "E_MFP_WRITE"

    def __init__(self, stage, detail):
        Exception.__init__(self, detail)
        self.stage = stage
        self.detail = detail

    def face(self):
        return "%s stage=%s %s" % (self.code, self.stage, self.detail)


def _write_error(stage, exc):
    return WriteError(stage, "%s: %s" % (type(exc).__name__,
                                         _one_line(exc)))


def read_copy_file(path):
    """Read the copy JSON, turning every read failure into CopyError.

    A missing path, undecodable bytes and malformed JSON used to escape
    as FileNotFoundError, UnicodeDecodeError and json.JSONDecodeError
    (rc=1 with a traceback). They are one family here - the copy file
    cannot drive this renderer - so they share the E_MFP_COPY code and
    name the underlying type in the detail instead of adding three codes.
    """
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except UnicodeDecodeError as exc:
        raise CopyError("UnicodeDecodeError: %s" % _one_line(exc))
    except json.JSONDecodeError as exc:
        raise CopyError("JSONDecodeError: %s" % _one_line(exc))
    except OSError as exc:
        raise CopyError("%s: %s" % (type(exc).__name__, _one_line(exc)))


def load_copy(path=COPY_PATH):
    data = read_copy_file(path)
    if not isinstance(data, dict):
        raise CopyError("top level is %s, expected object"
                        % type(data).__name__)
    missing = [key for key in REQUIRED_COPY_KEYS if key not in data]
    if missing:
        raise CopyError("missing keys: %s" % ",".join(missing))
    return data


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


def _remove_quietly(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _stage(path, text):
    """Write text to a temp file beside path; return (temp, path).

    Nothing is written to the delivered path here, so a failure in this
    step leaves the previous file exactly as it was.
    """
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".mfp-write-", dir=directory)
    os.close(fd)
    try:
        with io.open(temp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    except BaseException:
        _remove_quietly(temp)
        raise
    return temp, path


def write_outputs(faces, copy, out_html, out_json):
    """Render both faces fully, then swap them in.

    Until R3197 this opened each target first and rendered into it, so a
    render-time exception truncated the previous page to zero bytes and
    left the JSON untouched (or the other way round); a fresh run left a
    zero-byte page with no JSON at all. Both texts are now built before
    any target is opened, each goes to a temp file beside its target, and
    the two swaps are the only writes to the delivered paths.

    Since R3198 each of the three stages answers WriteError (E_MFP_WRITE)
    with the stage named, instead of letting the raw exception escape to
    a caller that can only see rc=1 and a traceback. The original
    exception stays reachable as __cause__.
    """
    try:
        texts = ((out_html, render_html(copy, faces)),
                 (out_json, render_json(faces)))
    except Exception as exc:
        raise _write_error("render", exc) from exc
    staged = []
    try:
        for path, text in texts:
            try:
                staged.append(_stage(path, text))
            except Exception as exc:
                raise _write_error("stage", exc) from exc
        for temp, path in staged:
            try:
                os.replace(temp, path)
            except Exception as exc:
                raise _write_error("replace", exc) from exc
    finally:
        for temp, _unused in staged:
            if os.path.exists(temp):
                _remove_quietly(temp)


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
    try:
        copy = load_copy(args.copy)
    except CopyError as exc:
        sys.stdout.write("%s\n" % exc.face())
        return 2
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
    except WriteError as exc:
        sys.stdout.write("%s\n" % exc.face())
        return 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("PASS preview %s (%d bytes) + %s (%d bytes)"
          % (os.path.relpath(args.out, BASE), os.path.getsize(args.out),
             os.path.relpath(args.json_out, BASE),
             os.path.getsize(args.json_out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
