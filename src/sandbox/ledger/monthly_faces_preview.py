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
E_MFP_WRITE: the delivered files cannot be rendered, staged, swapped or
proven by reading them back;
E_MFP_WORLD: the demo world cannot be built; E_MFP_LOG: the evidence log
cannot be staged, swapped in or proven by reading it back).

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

R3199 (AC-MFPX3..AC-MFPX5): the demo world and the evidence log are
refused by name as well. A build failure inside collect() used to escape
raw (measured: rc=1, empty stdout, a traceback) and, under --verify, the
--log file was never written at all - a failed verification left no
evidence that it had run. It now answers E_MFP_WORLD at rc=2, and the
verify text always reaches stdout, so the log carries the failure. The
log itself used to be written in place, which meant a bad path threw the
freshly computed answer away (measured: rc=1, stdout 0 bytes) and a
partial write could truncate the evidence file; it is now staged beside
its target and swapped in, answering E_MFP_LOG at rc=2 only AFTER the
text has been printed. A missing log directory is created, as it already
was for the outputs.

R3200 (AC-MFPX6): the log write now proves itself by reading back. Until
this window a successful os.replace was the whole evidence that the log
had landed, so a swap that reported success while carrying other bytes
went unnoticed (measured on three injected shapes: half the payload,
CRLF for LF, and zero bytes - all returned normally, rc stayed 0 and no
code was printed, while the file on disk no longer matched the answer).
tools/qa_log.py has proven its own writes back since AC-QAL2; this
applies the same law to the second writer: the landed bytes must equal
the intended payload byte for byte, and a mismatch answers E_MFP_LOG
with stage=read-back naming both the landed and the intended size and
sha16. A mismatch is not rolled back - at that point the previous
evidence bytes are already gone - so the file stays as landed and the
detail says it is unproven.

R3201 (AC-MFPX7): the two delivered files prove themselves the same way.
Until this window a successful os.replace was the whole evidence that the
page and the JSON had landed: a swap that reported success while carrying
same-length but different bytes left rc=0, the same "PASS preview" line
(its two numbers came from os.path.getsize) and no refusal, so a page
that was never rendered could be shipped as one. Measured: shrinking the
payload changes the printed size, but any same-length substitution is
invisible to every consumer - the artifact index reads sizes plus the
JSON's own verdict, the export face ages rows by mtime and size, and
reconcile_all and the closeout gate never name the page. Both swaps now
read their target back and must equal the rendered text byte for byte; a
mismatch answers E_MFP_WRITE with stage=read-back, the failing file named
first in the detail and both landed and intended bytes and sha16 given.
The proof is per file, not a joint boolean, because a false page beside a
true JSON must name the false one. The "PASS preview" line now quotes the
proof (bytes and sha16 of the bytes read back) instead of os.path.getsize.
A mismatch is not rolled back - the previous bytes are already gone - so the
landed file stays and the detail says it is unproven.

R3202 (AC-MFPX8): a proven log is named on stdout. write_log has returned
bytes/lines/sha16 since R3200, but run_verify dropped that value, so the
answer it printed carried no readable link to the file it wrote (measured:
healthy rc=0 with stdout lines equal to the log lines and no sha16, no byte
count anywhere in the output). The proof line cannot live in the log: it
would name the log own sha16 and that number changes the moment the line is
added (measured: 271ba9eb7b2d1230 became 50522dc2cc6582c6). So exactly one
"LOG OK path=... bytes=... lines=... sha16=..." line follows the answer on
stdout, quoting the read-back proof. It is printed only when a log was asked
for and proven, so a refusal never pretends the file landed, and the log
bytes, the page and the JSON stay byte-identical.
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
    """Named refusal for a failed render, stage, swap or read-back.

    All four stages mean the same thing to a caller - the delivered
    files cannot be produced - so they share one code and name the stage
    plus the underlying exception type in the detail. The read-back stage
    also names which delivered file disagreed with its rendered text.
    """

    code = "E_MFP_WRITE"

    def __init__(self, stage, detail):
        Exception.__init__(self, detail)
        self.stage = stage
        self.detail = detail

    def face(self):
        return "%s stage=%s %s" % (self.code, self.stage, self.detail)


def _write_error(stage, exc, path=None, note=None):
    where = "%s: " % os.path.basename(path) if path else ""
    tail = "; %s" % note if note else ""
    return WriteError(stage, "%s%s: %s%s" % (where, type(exc).__name__,
                                             _one_line(exc), tail))


class WorldError(Exception):
    """Named refusal for a demo world that cannot be built.

    Until R3199 a failing collect() escaped as the raw exception, so a
    --verify run answered rc=1 with empty stdout and - worse - never
    wrote the evidence log it was asked for.
    """

    code = "E_MFP_WORLD"

    def __init__(self, detail):
        Exception.__init__(self, detail)
        self.detail = detail

    def face(self):
        return "%s %s" % (self.code, self.detail)


class LogError(Exception):
    """Named refusal for an evidence log that cannot be written.

    The verify text is already computed when this is raised, so a caller
    that only sees this code has still been handed the answer: the text
    reaches stdout before the refusal line.
    """

    code = "E_MFP_LOG"

    def __init__(self, stage, detail):
        Exception.__init__(self, detail)
        self.stage = stage
        self.detail = detail

    def face(self):
        return "%s stage=%s %s" % (self.code, self.stage, self.detail)


def _log_error(stage, exc):
    return LogError(stage, "%s: %s" % (type(exc).__name__,
                                       _one_line(exc)))


def _log_proof_line(path, proof):
    """One readable line of evidence for a log that is already proven.

    R3202 (AC-MFPX8): write_log has returned bytes/lines/sha16 since
    R3200, but run_verify dropped the value, so a printed VERIFY answer
    carried no readable link to the file on disk. The line cannot be part
    of the log itself - naming the log own sha16 changes that sha16 the
    moment the line is added (measured: 271ba9eb7b2d1230 became
    50522dc2cc6582c6) - so it goes to stdout right after the answer and
    names the file it proves.
    """
    return ("LOG OK path=%s bytes=%d lines=%d sha16=%s"
            % (os.path.relpath(path, BASE), proof["bytes"],
               proof["lines"], proof["sha256"]))


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


def build_world(tmp_root):
    """collect() with every build failure named instead of raw.

    The original exception stays reachable as __cause__, so a caller can
    still see what the ledger said when the demo world would not build.
    """
    try:
        return collect(tmp_root)
    except Exception as exc:
        raise WorldError("%s: %s" % (type(exc).__name__,
                                     _one_line(exc))) from exc


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


def verify_log(path, text):
    """Read a swapped-in file back and prove it carries the intended text.

    R3200 (AC-MFPX6): a successful os.replace used to be the only proof
    that the log had landed, so bytes other than the computed answer were
    reported as written (measured: 29B of 58B, CRLF for LF and zero
    bytes all returned without a refusal and left rc=0). tools/qa_log.py
    has proven its writes back since AC-QAL2; this is the same law on the
    second writer, stated as byte equality with the intended payload.

    R3201 (AC-MFPX7) applies the same proof to the two delivered files:
    the page and the JSON were swapped in with nothing but os.replace
    reporting success, so a same-length substitution shipped silently.
    One implementation serves both doors - the log and the outputs - so
    there is exactly one place where "landed" is compared with "wanted".
    """
    want = text.encode("utf-8")
    raw = io.open(path, "rb").read()
    if raw != want:
        raise ValueError(
            "landed %d bytes sha16=%s, intended %d bytes sha16=%s"
            % (len(raw), hashlib.sha256(raw).hexdigest()[:16],
               len(want), hashlib.sha256(want).hexdigest()[:16]))
    return {"bytes": len(raw),
            "lines": len(text.splitlines()),
            "sha256": hashlib.sha256(raw).hexdigest()[:16]}


def write_log(path, text):
    """Write the evidence log beside its target, then swap it in.

    Until R3199 the log was written in place, so a path that could not
    be opened threw away the freshly computed verify text (measured:
    rc=1, stdout 0 bytes, a traceback) and a partial write could leave a
    truncated evidence file. The text is staged and os.replace is the
    only write to the log path; the target directory is created when it
    is missing, exactly as the outputs are.

    Since R3200 the swapped-in file is read back and must equal the
    intended payload byte for byte (verify_log). A mismatch is named at
    read-back and the landed bytes are left as they are: the previous
    evidence is already gone, so the refusal says unproven rather than
    pretending a rollback happened.
    """
    try:
        temp, target = _stage(path, text)
    except Exception as exc:
        raise _log_error("stage", exc) from exc
    try:
        os.replace(temp, target)
    except Exception as exc:
        raise _log_error("replace", exc) from exc
    finally:
        if os.path.exists(temp):
            _remove_quietly(temp)
    try:
        return verify_log(target, text)
    except Exception as exc:
        raise _log_error("read-back", exc) from exc


def write_outputs(faces, copy, out_html, out_json):
    """Render both faces fully, then swap them in and read them back.

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

    Since R3201 each swap is proven by reading the target back and
    comparing it with the text that was meant to land (verify_log), so a
    successful os.replace is no longer accepted as evidence on its own
    (measured: same-length substitutions landed silently). A mismatch
    answers stage=read-back with the failing file named first. The proof
    is per file: a false page beside a true JSON must name the page. The
    returned mapping is role -> (bytes, lines, sha256) as read back.
    """
    try:
        texts = (("html", out_html, render_html(copy, faces)),
                 ("json", out_json, render_json(faces)))
    except Exception as exc:
        raise _write_error("render", exc) from exc
    staged = []
    try:
        for role, path, text in texts:
            try:
                staged.append((role, _stage(path, text), text))
            except Exception as exc:
                raise _write_error("stage", exc) from exc
        proofs = {}
        for role, (temp, path), text in staged:
            try:
                os.replace(temp, path)
            except Exception as exc:
                raise _write_error("replace", exc) from exc
            try:
                proofs[role] = verify_log(path, text)
            except Exception as exc:
                note = "landed bytes left as they are, unproven"
                if role != texts[-1][0]:
                    note += "; later outputs unproven"
                raise _write_error("read-back", exc, path, note) from exc
    finally:
        for _role, (temp, _unused), _text in staged:
            if os.path.exists(temp):
                _remove_quietly(temp)
    return proofs


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


def _verify_body(copy, say, problems):
    """Build two worlds, check identity and write outputs into them.

    Reports through say(); every problem is appended to problems().
    Snapshot bytes are re-checked before anything is claimed.
    """
    snap_before = (os.path.getsize(SNAPSHOT), sha16(SNAPSHOT))
    dirs = []
    try:
        runs = []
        for _ in range(2):
            tmp = tempfile.mkdtemp(prefix="monthly-faces-")
            dirs.append(tmp)
            faces = build_world(tmp)
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


def run_verify(copy, log_path):
    """Answer the criteria, then write the answer out as evidence.

    A world that cannot be built, an output that cannot be written and a
    log that cannot be staged are each named at rc=2. The computed text
    is printed BEFORE any log refusal, so a bad --log path can no longer
    cost the caller the whole verify answer (measured before R3199:
    rc=1, stdout 0 bytes, a traceback).

    Since R3202 a proven log is named on stdout: write_log has returned
    bytes/lines/sha16 since R3200 and this face used to drop it, so the
    answer could not be tied to the file it wrote. The proof line comes
    after the text and never enters the log, because a log cannot carry
    its own sha16 (measured).
    """
    lines = []
    problems = []
    rc = 0

    def say(text):
        lines.append(text)

    try:
        _verify_body(copy, say, problems)
    except WorldError as exc:
        problems.append(exc.face())
        rc = 2
    except WriteError as exc:
        problems.append(exc.face())
        rc = 2
    if problems:
        say("VERIFY FAIL problems=%d" % len(problems))
        for item in problems:
            say("  %s" % item)
    else:
        say("VERIFY PASS criteria=AC-MFR1..AC-MFR8 (MFR6 index entry and "
            "MFR8 hygiene checked by the caller)")
    text = "\n".join(lines) + "\n"
    proof = None
    if log_path:
        try:
            proof = write_log(log_path, text)
        except LogError as exc:
            sys.stdout.write(text)
            sys.stdout.write("%s\n" % exc.face())
            return 2
    sys.stdout.write(text)
    if proof is not None:
        sys.stdout.write("%s\n" % _log_proof_line(log_path, proof))
    if rc == 0 and problems:
        rc = 1
    return rc


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
        faces = build_world(tmp)
        problems = []
        check_identity(faces, problems)
        if problems:
            for item in problems:
                sys.stdout.write("FAIL %s\n" % item)
            return 1
        proofs = write_outputs(faces, copy, args.out, args.json_out)
    except WorldError as exc:
        sys.stdout.write("%s\n" % exc.face())
        return 2
    except WriteError as exc:
        sys.stdout.write("%s\n" % exc.face())
        return 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("PASS preview %s (%d bytes sha16=%s) + %s (%d bytes sha16=%s)"
          % (os.path.relpath(args.out, BASE), proofs["html"]["bytes"],
             proofs["html"]["sha256"],
             os.path.relpath(args.json_out, BASE), proofs["json"]["bytes"],
             proofs["json"]["sha256"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
