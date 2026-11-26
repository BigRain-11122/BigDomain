"""Census every preview/ html half against its same-stem json half (R3499).

Why this exists: R3493 and R3498 each repaired one face whose two halves had
been written by different windows - ledger-reconcile-face (html a day newer
than its json) and ceo-blockers (html three days newer) - and both times the
defect was invisible until a shipped gate refused it. The board asked for a
face-by-face inventory before any mass re-derivation, and for a criterion
pinned on the oldest survivor.

The first measuring pass found that mtime ALONE cannot answer the question:

  The fifteen worst apimarket report faces all carry the same html mtime
  (2026-11-25 09:58) while their json halves date from 2026-10-25, and the
  working tree is clean. A bulk rewrite or restore of identical bytes writes
  exactly that trace. So a large mtime gap proves only "the two halves were
  written at different moments", not "the landed pair is not one derivation".

This census therefore classifies on COMMITTED HISTORY, which a later touch of
identical bytes cannot forge:

  no-json       no same-stem json half exists (named, not silently skipped)
  same-run      both halves written within SAME_RUN_SECONDS (120)
  same-commit   gap > 120s but both halves' last commit is the same commit,
                so history says they were published together and the gap came
                from a post-commit rewrite of identical content
  history-split gap > 120s and the two halves' last commits differ, so the
                two halves were never published in one commit
  untracked     one or both halves have no commit at all
  frozen-excused a history split that a freeze register names and proves by
                sha256 on BOTH halves - the halves differ in commit because the
                freeze said so, not because the pair landed half-derieved

The freeze register is read, never written. A registered face whose bytes no
longer match its registered sha256 is NOT excused: it keeps its split verdict
and says which half moved, because a frozen snapshot whose bytes changed is
exactly the drift this page exists to show.

The page is one derivation with two halves (html + json) written by the same
run, and `--check` re-derives both in memory and compares them to the landed
bytes, the volatile `generated_at` field aside. The census excludes its own
pair by name: a page describing itself would change class the moment it is
committed, which would make `--check` red for a reason that is not a defect.

Stdlib only, ASCII source except the page text, zero network.
"""

import datetime
import glob
import hashlib
import io
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
PREVIEW = os.path.join(REPO, "preview")
STATE = os.path.join(REPO, "src", "os", "state.json")
LABEL = "preview-pair-census"
JSON_OUT = os.path.join(PREVIEW, LABEL + ".json")
HTML_OUT = os.path.join(PREVIEW, LABEL + ".html")

# Measured basis (R3499 read-only pass): 63 of 102 pairs sit within 60s and 14
# more within 600s, i.e. a producer that writes both halves does so inside one
# minute; 120s keeps a margin for a slow render and still separates every pair
# the boards cared about (the smallest drifted case measured was 3.6h).
SAME_RUN_SECONDS = 120
# generated_at is the clock, and round is the label of the window that derived
# the page. Neither is a measurement, so --check ignores them - treating the
# label as volatile is what keeps a page honest for a whole window instead of
# going red the moment the tick it was derived under advances, the stale-pair
# trap this page itself exists to expose.
VOLATILE = ("generated_at", "round")
# R3508: the html half prints the round it was derived at ("Tick 3507"), and a
# label is not a measurement - without this the page went red the moment the
# tick advanced past its own derivation, which is the same stale-label trap
# R3503 healed on the receipt page. The exclusion is narrow and pinned: one
# digit changed anywhere else in the page still reads drift (AC-PPC4).
TICK_RE = re.compile(r"Tick \d+")
# R3506: an mtime is also a clock. The page was measured red after a round that
# re-derived the entry index (whose band quotes this page's byte counts): every
# per-pair digest and commit was unchanged, only the seconds moved, and the two
# gates could not both be green because deriving the index moves this page's own
# mtime while deriving this page moves the index's band. The measurement is the
# per-pair byte SIZE, DIGEST and COMMIT plus the verdict it produces; the clock
# fields are evidence, recorded on the row and excluded from the comparison.
# A pair whose bytes really moved still reads drift through its digest, and a
# pair whose class really changed still reads it through the verdict.
PAIR_CLOCKS = ("mtime", "mtime_epoch")
FREEZE_REGISTER = os.path.join(REPO, "state", "apimarket-face-freeze.json")
# R3508: one landed face prints a byte count for EVERY preview half, this page's
# own two included (measured: exactly one html under preview/ names this label).
# Its bytes therefore move whenever any listed page is re-derived, so its digest
# can never be a stable measurement - recording it made the two gates take turns:
# deriving the entry index reddened this page (measured: same 55908B, different
# digest), and deriving this page moved the index band that quotes these two
# byte counts. Such a pair is recorded as a READING - name, class and last
# commit - with no clock and no digest. The exclusion is read off the landed
# html, never trusted from a list, and it is NARROW: every other pair keeps its
# measurements, so a face that really changed still reads drift through its
# digest and its class.
MIRROR_REASON = ("prints a byte count for every preview half, this page's own included, "
                 "so its bytes move whenever a listed page is re-derived")
# R3500: per-face receipts (tools/face_pair_receipt.py) say WHY a split exists.
# Only a receipt that reproduces the landed html byte for byte may excuse it;
# a version-drift receipt explains the split and leaves it standing.
RECEIPT_FILE = os.path.join(PREVIEW, "face-pair-receipt.json")


def rd_bytes(path):
    with io.open(path, "rb") as f:
        return f.read()


def sha8(data):
    return hashlib.sha1(data).hexdigest()[:8].upper()


def iso(ts):
    return datetime.datetime.fromtimestamp(ts).astimezone().replace(microsecond=0).isoformat()


def last_commit(rel):
    """Last commit that touched one path, or "" when git has nothing.

    Only called for pairs whose mtime gap already exceeds the same-run window:
    a same-run pair needs no history to be classified, and 200 git calls per
    run would buy nothing.
    """
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%h", "--", rel],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def side(path, rel):
    data = rd_bytes(path)
    return {
        "bytes": len(data),
        "sha": sha8(data),
        "mtime": iso(os.path.getmtime(path)),
        "mtime_epoch": int(os.path.getmtime(path)),
        "commit": last_commit(rel),
    }


def classify(delta_seconds, h_commit, j_commit):
    if delta_seconds <= SAME_RUN_SECONDS:
        return "same-run"
    if not h_commit or not j_commit:
        return "untracked"
    return "same-commit" if h_commit == j_commit else "history-split"


def sha256_hex(path):
    with io.open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def freeze_register():
    """Registered frozen faces keyed by html basename, with both registered digests.

    Read-only: the register is evidence, never a thing this tool may rewrite.
    """
    try:
        doc = json.load(io.open(FREEZE_REGISTER, "r", encoding="utf-8"))
    except Exception:
        return {}
    table = {}
    for face in doc.get("faces", []):
        html_rel = face.get("html") or ""
        if not html_rel:
            continue
        table[os.path.basename(html_rel)] = {
            "html": face.get("html_sha256"),
            "json": face.get("json_sha256"),
            "json_path": face.get("json") or "",
        }
    return table


def apply_freeze(row, html_path, json_path, register):
    """Excuse a history split only when the register names it and BOTH halves match.

    A half that moved off its registered digest is not excused: that is the
    drift worth seeing, so the row keeps its split verdict and names the half.
    """
    if row["verdict"] != "history-split":
        return
    reg = register.get(os.path.basename(html_path))
    if not reg:
        return
    h_ok = reg.get("html") and sha256_hex(html_path) == reg["html"]
    j_ok = reg.get("json") and sha256_hex(json_path) == reg["json"]
    if h_ok and j_ok:
        row["verdict"] = "frozen-excused"
        row["receipt"] = "sha256-both"
    else:
        row["freeze_bytes_match"] = ("html-only" if h_ok else "json-only" if j_ok else "neither")


def pair_receipts():
    """Per-face receipts keyed by html basename (read-only, R3500).

    A receipt is evidence, never a thing this tool may rewrite. It is also
    bound to bytes: a landed page that moved after the receipt is no longer
    the page the receipt describes, so the excuse lapses.
    """
    try:
        doc = json.load(io.open(RECEIPT_FILE, "r", encoding="utf-8"))
    except Exception:
        return {}
    table = {}
    for row in doc.get("faces", []):
        slug = row.get("slug")
        if slug:
            table[slug + ".html"] = row
    return table


def apply_receipt(row, html_path, receipts):
    """Excuse a split only for a receipt that reproduced the landed bytes.

    Anything else still says something worth reading: the receipt's own verdict
    is attached to the row so a split is explained instead of merely counted.
    """
    if row["verdict"] != "history-split":
        return
    rec = receipts.get(os.path.basename(html_path))
    if not rec:
        return
    landed_now = sha256_hex(html_path)
    bound = rec.get("landed_html_sha256") == landed_now
    row["pair_receipt"] = rec.get("verdict") or "unknown"
    if rec.get("verdict") == "one-derivation" and bound:
        row["verdict"] = "channel-receipt"
        row["receipt"] = "channel-splice"
    else:
        row["receipt_bound"] = bound
        row["receipt_detail"] = rec.get("detail") or rec.get("error") or ""


# R3521: the four apimarket splits are every one of them explained by a
# byte-exact historical replay (R3514..R3518), yet the shipped law excuses only
# a receipt whose verdict is `one-derivation`, so they keep counting as splits.
# Whether a replay receipt SHOULD excuse a split is a law decision, and the
# board forbids flipping the count to make it green. So this face answers the
# numeric question without touching the law: how many splits would fall, which
# receipt blocks each survivor, and does a receiptless or unbound receipt still
# read as a split. The shipped totals are not written by this face.
ADMIT_OUT = os.path.join(PREVIEW, "receipt-admissibility.json")
ADMIT_HTML = os.path.join(PREVIEW, "receipt-admissibility.html")
# The face's clock and the window label are not measurements, exactly as on the
# census page: without this the pair would redden the moment the tick advanced.
ADMIT_VOLATILE = ("generated_at", "round")
ADMIT_LAW = ("a split stays a split; this face only answers what a law admitting "
             "byte-exact replay receipts would buy, and refuses to admit a receipt "
             "that is unbound, shape-less or absent")


def admit_reasons(rec, landed_full, landed_12):
    """Every reason this receipt may NOT excuse the split; empty means it may.

    Read off the record's own fields and the live bytes: the binding digest is
    recomputed from the file, never trusted from the receipt's `_now` copy.
    """
    if not rec:
        return ["no-receipt"]
    why = []
    if rec.get("verdict") != "version-drift":
        why.append("receipt-verdict=" + str(rec.get("verdict")))
    hist = rec.get("historical") or {}
    if not hist.get("commit"):
        why.append("no-historical-commit")
    if not hist.get("json_byte_identical"):
        why.append("json-not-byte-identical")
    if not hist.get("landed_digests_agree"):
        why.append("replay-digests-disagree")
    if rec.get("landed_html_sha256") != landed_full:
        why.append("receipt-not-bound-to-landed-bytes")
    if hist.get("landed_html_sha256_12") != landed_12:
        why.append("recorded-replay-digest-is-not-the-landed-page")
    return why


def negative_controls(receipts, rows):
    """Prove the admission test is not decorative, on the real records.

    Three controls, each a receipt that WOULD be admitted except for one moved
    field, so a green control means the moved field is load-bearing: the binding
    digest, the byte-identical json claim, and the absence of any receipt.
    """
    probe = next((r for r in rows if r["receipt_verdict"]), None)
    if probe is None:
        return [{"control": "no-probe", "expected": "a version-drift receipt on a split",
                 "answer": [], "ok": False}]
    name = probe["name"] + ".html"
    path = os.path.join(PREVIEW, name)
    full = sha256_hex(path) if os.path.exists(path) else ""
    twelve = full[:12]
    base = receipts.get(name) or {}
    out = []

    moved = json.loads(json.dumps(base))
    digest = moved.get("landed_html_sha256") or ""
    moved["landed_html_sha256"] = ("0" if digest[:1] != "0" else "1") + digest[1:]
    answer = admit_reasons(moved, full, twelve)
    out.append({"control": "binding-digest-moved-one-hex",
                "expected": "receipt-not-bound-to-landed-bytes",
                "answer": answer, "ok": answer == ["receipt-not-bound-to-landed-bytes"]})

    loose = json.loads(json.dumps(base))
    loose.setdefault("historical", {})["json_byte_identical"] = False
    answer = admit_reasons(loose, full, twelve)
    out.append({"control": "json-claim-dropped",
                "expected": "json-not-byte-identical",
                "answer": answer, "ok": answer == ["json-not-byte-identical"]})

    answer = admit_reasons(None, full, twelve)
    out.append({"control": "no-receipt-at-all",
                "expected": "no-receipt",
                "answer": answer, "ok": answer == ["no-receipt"]})
    return out


def admissibility(payload):
    receipts = pair_receipts()
    rows = []
    for row in payload["pairs"]:
        if row["verdict"] != "history-split":
            continue
        name = row["name"] + ".html"
        path = os.path.join(PREVIEW, name)
        full = sha256_hex(path) if os.path.exists(path) else ""
        rec = receipts.get(name) or {}
        hist = rec.get("historical") or {}
        why = admit_reasons(rec or None, full, full[:12])
        rows.append({
            "name": row["name"],
            "receipt_verdict": rec.get("verdict") or "",
            "historical_commit": hist.get("commit") or "",
            "live_sha256_12": full[:12],
            "recorded_sha256_12": hist.get("landed_html_sha256_12") or "",
            "would_be_admitted": not why,
            "blocked_by": why,
        })
    admitted = sum(1 for r in rows if r["would_be_admitted"])
    controls = negative_controls(receipts, rows)
    return {
        "generated_at": datetime.datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "round": payload.get("round", 0),
        "source": "tools/preview_pair_census.py --admissibility",
        "law_now": "a version-drift receipt explains a split and never excuses it",
        "law_question": ADMIT_LAW,
        "splits": len(rows),
        "admitted": admitted,
        "if_admitted": {
            "history_split_before": len(rows),
            "history_split_after": len(rows) - admitted,
            "shipped_totals_unchanged": True,
        },
        "rows": rows,
        "negative_controls": controls,
        "checks": 5,
    }


def admit_problems(payload, face):
    """Five named checks; any one failing makes the face refuse to print PASS."""
    problems = []
    total = payload["totals"]["history-split"]
    if face["splits"] != total:
        problems.append("face covers %d splits but the law counts %d"
                        % (face["splits"], total))
    bad = [c["control"] for c in face["negative_controls"] if not c.get("ok")]
    if bad:
        problems.append("negative control answered wrong: " + ",".join(bad))
    expect = face["splits"] - face["admitted"]
    if face["if_admitted"]["history_split_after"] != expect:
        problems.append("arithmetic is not this face's own count")
    for row in face["rows"]:
        if not row["would_be_admitted"]:
            continue
        path = os.path.join(PREVIEW, row["name"] + ".html")
        live = sha256_hex(path) if os.path.exists(path) else ""
        if live[:12] != row["live_sha256_12"]:
            problems.append("admitted row does not match the file now: " + row["name"])
        if not row["historical_commit"]:
            problems.append("admitted row carries no historical commit: " + row["name"])
    return problems


def admit_dumps(face):
    return json.dumps(face, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def admit_normalized(data):
    """Byte comparison with only the clock and the window label blanked."""
    text = data.decode("utf-8") if isinstance(data, bytes) else data
    try:
        obj = json.loads(text)
    except Exception:
        folded = "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n"))
        return TICK_RE.sub("Tick <label>", folded)
    for key in ADMIT_VOLATILE:
        if key in obj:
            obj[key] = "<volatile>"
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False).replace("\r\n", "\n")


def admit_html_of(face):
    """One openable page for the same reading the json half carries.

    It names no census label on purpose: a page that prints this tool's own
    label is re-classified as a mirror, which would hide it from the census.
    """
    rows = []
    for row in face["rows"]:
        cls = "same" if row["would_be_admitted"] else "split"
        rows.append(
            '<tr><td class="n">%s</td><td class="m">%s</td><td class="m">%s</td>'
            '<td class="m">%s</td><td class="m">%s</td><td class="%s">%s</td>'
            '<td class="m">%s</td></tr>'
            % (esc(row["name"]), esc(row["receipt_verdict"] or "-"),
               esc(row["historical_commit"] or "-"), esc(row["live_sha256_12"]),
               esc(row["recorded_sha256_12"] or "-"), cls,
               "yes" if row["would_be_admitted"] else "no",
               esc(",".join(row["blocked_by"]) or "-")))
    controls = []
    for con in face["negative_controls"]:
        controls.append(
            '<tr><td class="n">%s</td><td class="m">%s</td><td class="m">%s</td>'
            '<td class="%s">%s</td></tr>'
            % (esc(con["control"]), esc(con["expected"]),
               esc(",".join(con["answer"]) or "-"),
               "same" if con["ok"] else "split", "yes" if con["ok"] else "no"))
    ia = face["if_admitted"]
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<title>BigDomain &middot; replay receipts</title><style>%s</style></head><body>'
            '<div class="wrap"><h1>Replay receipts: what an admitting law would buy</h1>'
            '<p class="sub">Tick %d &middot; %d history splits &middot; derived by %s</p>'
            '<div class="banner">%s</div>'
            '<div class="banner">Today\'s law: %s. Nothing on this page changes a verdict - '
            'the shipped census still counts %d history splits, so admitting these receipts '
            'is a decision, not a re-render.</div>'
            '<div class="tally"><span>%d splits</span><span>%d admitted</span>'
            '<span>%d would remain</span><span>controls %d</span></div>'
            '<table><thead><tr><th>face</th><th>receipt</th><th>historical commit</th>'
            '<th>live sha</th><th>recorded sha</th><th>admitted</th><th>blocked by</th>'
            '</tr></thead><tbody>%s</tbody></table>'
            '<h2 style="font-size:15px;margin:26px 0 8px">Negative controls on the real '
            'records</h2>'
            '<table><thead><tr><th>control</th><th>what a green answer must name</th>'
            '<th>answer</th><th>ok</th></tr></thead><tbody>%s</tbody></table>'
            '<footer>Every digest on this page is recomputed from the live bytes, never '
            'trusted from the receipt. Non-advisory notice: this is a build status page, '
            'not investment advice.</footer></div></body></html>\n'
            % (STYLE, face["round"], face["splits"], esc(face["source"]),
               esc(face["law_question"]), esc(face["law_now"]), ia["history_split_before"],
               face["splits"], face["admitted"], ia["history_split_after"],
               len(face["negative_controls"]), "\n".join(rows), "\n".join(controls)))


def admit_check(payload, face, out=None, html=None):
    """Name every way the landed page is not this derivation, or has gone stale.

    The staleness arm reads the LANDED rows, not the fresh ones: it answers
    whether the bytes the page describes are still the bytes on disk, which is
    the question a decision reader actually asks of it.
    """
    out = ADMIT_OUT if out is None else out
    html = ADMIT_HTML if html is None else html
    problems = []
    for path, fresh in ((out, admit_dumps(face).encode("utf-8")),
                        (html, admit_html_of(face).encode("utf-8"))):
        if not os.path.exists(path):
            problems.append("missing half " + os.path.basename(path))
            continue
        if admit_normalized(rd_bytes(path)) != admit_normalized(fresh):
            problems.append("landed half is not this derivation: " + os.path.basename(path))
    if payload["totals"]["history-split"] != face["splits"]:
        problems.append("the law counts %d splits but this face covers %d"
                        % (payload["totals"]["history-split"], face["splits"]))
    try:
        landed = json.loads(rd_bytes(out).decode("utf-8"))
    except Exception:
        landed = {}
    for row in landed.get("rows") or ():
        if not row.get("would_be_admitted"):
            continue
        path = os.path.join(PREVIEW, row["name"] + ".html")
        live = sha256_hex(path)[:12] if os.path.exists(path) else ""
        if live != row.get("live_sha256_12"):
            problems.append("live bytes moved since this face was written: " + row["name"])
    return problems


def prints_this_page(path):
    """True when a landed html half names this census page in its own text.

    A directory index prints every preview half's byte count, this page's
    included, which is why its own bytes cannot be a measurement of itself.
    """
    try:
        return LABEL in rd_bytes(path).decode("utf-8", "replace")
    except OSError:
        return False


def mirror_row(stem, h, j):
    """A pair whose html half prints this page's size: a reading, not a measurement.

    The class is computed exactly as for every other pair, so a mirror pair that
    really changed hands is still named; the two clocks, the two digests and both
    last-commit labels are dropped, because they move whenever ANY listed page is
    re-derived - and a mirror page is re-derived by this very derivation order
    every window, so its commit label was the one reading that could never settle.
    """
    if j is None:
        verdict = "no-json"
    else:
        verdict = classify(abs(h["mtime_epoch"] - j["mtime_epoch"]), h["commit"], j["commit"])
    return {"name": stem, "verdict": verdict, "mirror": MIRROR_REASON}


def census():
    register = freeze_register()
    receipts = pair_receipts()
    rows = []
    for html in sorted(glob.glob(os.path.join(PREVIEW, "*.html"))):
        stem = os.path.basename(html)[:-5]
        if stem == LABEL:
            continue
        json_path = html[:-5] + ".json"
        rel_h = "preview/" + os.path.basename(html)
        h = side(html, rel_h)
        if prints_this_page(html):
            j = None
            if os.path.exists(json_path):
                j = side(json_path, "preview/" + os.path.basename(json_path))
            rows.append(mirror_row(stem, h, j))
            continue
        if not os.path.exists(json_path):
            rows.append({"name": stem, "verdict": "no-json", "delta_seconds": 0,
                         "html": h, "json": None})
            continue
        j = side(json_path, "preview/" + os.path.basename(json_path))
        delta = abs(h["mtime_epoch"] - j["mtime_epoch"])
        row = {"name": stem, "verdict": classify(delta, h["commit"], j["commit"]),
               "delta_seconds": delta, "html": h, "json": j}
        apply_freeze(row, html, json_path, register)
        apply_receipt(row, html, receipts)
        rows.append(row)

    totals = {"html": len(rows)}
    for name in ("same-run", "same-commit", "history-split", "channel-receipt",
                 "frozen-excused", "untracked", "no-json"):
        totals[name] = sum(1 for r in rows if r["verdict"] == name)
    totals["paired"] = totals["html"] - totals["no-json"]
    totals["explained"] = sum(1 for r in rows if r.get("pair_receipt"))

    splits = [r for r in rows if r["verdict"] == "history-split"]
    splits.sort(key=lambda r: (-r.get("delta_seconds", 0), r["name"]))
    oldest = None
    if splits:
        head = splits[0]
        oldest = {"name": head["name"], "delta_hours": round(head["delta_seconds"] / 3600.0, 1),
                  "html_mtime": head["html"]["mtime"], "json_mtime": head["json"]["mtime"],
                  "html_commit": head["html"]["commit"], "json_commit": head["json"]["commit"]}

    tick = 0
    try:
        tick = int(json.load(io.open(STATE, "r", encoding="utf-8")).get("tick", 0))
    except Exception:
        pass

    return {
        "generated_at": datetime.datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "round": tick,
        "source": "tools/preview_pair_census.py",
        "law": ("a split is claimed only when the two halves' last commits differ; "
                "an mtime gap alone is published as a bucket, never as a split"),
        "same_run_seconds": SAME_RUN_SECONDS,
        "self_excluded": LABEL,
        "totals": totals,
        "oldest_split": oldest,
        "pairs": rows,
    }


STYLE = ("body{font:15px/1.55 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;margin:0;"
         "background:#12140f;color:#e8e6df}.wrap{max-width:980px;margin:0 auto;padding:32px 20px 64px}"
         "h1{font-size:24px;margin:0 0 6px}.sub{color:#9a9b90;margin:0 0 20px;font-size:13px}"
         ".banner{border-left:3px solid #c8a24a;background:#1c1e18;padding:12px 14px;margin:0 0 8px;font-size:14px}"
         ".tally{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 22px;font-size:13px}"
         ".tally span{background:#1c1e18;border:1px solid #2c2f26;border-radius:999px;padding:4px 12px}"
         "table{width:100%;border-collapse:collapse;font-size:13px}"
         "th,td{text-align:left;padding:7px 8px;border-bottom:1px solid #2c2f26}"
         "th{color:#9a9b90;font-weight:600;font-size:12px;letter-spacing:.03em}"
         "td.n{color:#d8d6ca}td.m{color:#8d8e83;white-space:nowrap}"
         ".split{color:#e0b25a}.same{color:#7fb2e5}footer{color:#6f7066;font-size:12px;margin-top:26px}")


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def html_of(payload):
    t = payload["totals"]
    drifted = [p for p in payload["pairs"] if p.get("delta_seconds", 0) > SAME_RUN_SECONDS]
    drifted.sort(key=lambda p: (-p.get("delta_seconds", 0), p["name"]))
    body = []
    for p in drifted:
        cls = {"history-split": "split", "frozen-excused": "frozen"}.get(p["verdict"], "same")
        note = p["verdict"]
        if p.get("receipt"):
            note = "%s (%s)" % (note, p["receipt"])
        if p.get("pair_receipt") and not p.get("receipt"):
            note = "%s (receipt: %s)" % (note, p["pair_receipt"])
        if p.get("freeze_bytes_match"):
            note = "%s (frozen bytes match %s)" % (note, p["freeze_bytes_match"])
        body.append(
            '<tr><td class="n">%s</td><td class="m">%s</td><td class="m">%s</td>'
            '<td class="m">%.1fh</td><td class="%s">%s</td></tr>'
            % (esc(p["name"]), esc(p["html"]["mtime"].replace("T", " ")[:16]),
               esc((p["json"] or {}).get("mtime", "").replace("T", " ")[:16]),
               p["delta_seconds"] / 3600.0, cls, esc(note)))
    oldest = payload["oldest_split"]
    if oldest:
        oldest_line = ("Oldest history split: <b>%s</b> &middot; %s vs %s &middot; %.1fh &middot; %s vs %s"
                       % (esc(oldest["name"]), esc(oldest["html_mtime"][:16].replace("T", " ")),
                          esc(oldest["json_mtime"][:16].replace("T", " ")), oldest["delta_hours"],
                          esc(oldest["html_commit"] or "-"), esc(oldest["json_commit"] or "-")))
    else:
        oldest_line = "Oldest history split: none &mdash; no pair's halves sit in different commits."

    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<title>BigDomain &middot; preview page pairs</title><style>%s</style></head><body>'
            '<div class="wrap"><h1>Preview page pairs: which halves left together</h1>'
            '<p class="sub">Tick %d &middot; %d html &middot; %d with a same-stem json &middot; '
            'derived by %s</p>'
            '<div class="banner">An mtime gap alone proves nothing: a bulk rewrite of identical '
            'bytes leaves the same trace. A pair is called a split only when its two halves\' last '
            'commits differ.</div>'
            '<div class="tally"><span>%d html</span><span>%d paired</span>'
            '<span>same-run %d</span><span>same-commit %d</span><span>history-split %d</span>'
            '<span>channel-receipt %d</span><span>frozen-excused %d</span>'
            '<span>untracked %d</span><span>no-json %d</span><span>explained %d</span></div>'
            '<p class="sub">%s</p>'
            '<table><thead><tr><th>pair</th><th>html written</th><th>json written</th>'
            '<th>gap</th><th>verdict</th></tr></thead><tbody>%s</tbody></table>'
            '<footer>Pairs within %ds are counted as one run and not listed. A frozen-excused '
            'pair is named in state/apimarket-face-freeze.json and both of its halves still match '
            'their registered sha256; a registered face whose bytes moved is NOT excused. A '
            'channel-receipt pair is named in preview/face-pair-receipt.json AND the receipt '
            'reproduced the landed html byte for byte; a receipt that explains a split without '
            'reproducing it leaves the split standing. '
            'This page excludes its own pair by name, so committing it cannot change its own '
            'reading. A pair whose html half prints this page\'s own byte count (the entry '
            'index does) is recorded as a reading - class and last commit, no clocks and no '
            'digests - because its bytes move whenever any listed page is re-derived. '
            'Non-advisory notice: this is a build status page, not investment advice.'
            '</footer>'
            '</div></body></html>\n'
            % (STYLE, payload["round"], t["html"], t["paired"], payload["source"],
               t["html"], t["paired"], t["same-run"], t["same-commit"], t["history-split"],
               t["channel-receipt"], t["frozen-excused"], t["untracked"], t["no-json"],
               t["explained"], oldest_line, "\n".join(body), SAME_RUN_SECONDS))


def dumps(payload):
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def normalized(data):
    """Byte comparison with the volatile stamp blanked, and whitespace folded.

    generated_at is the one field a re-derivation cannot reproduce; everything
    else must match byte for byte, which is what makes landings comparable to
    their own producer run after the fact.
    """
    text = data.decode("utf-8") if isinstance(data, bytes) else data
    try:
        obj = json.loads(text)
    except Exception:
        folded = "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n"))
        return TICK_RE.sub("Tick <label>", folded)
    for key in VOLATILE:
        if key in obj:
            obj[key] = "<volatile>"
    for pair in obj.get("pairs") or ():
        if not isinstance(pair, dict):
            continue
        # delta_seconds is arithmetic over the two clocks, so it is a clock too;
        # `verdict` is the class those clocks produce and IS compared, so a pair
        # that really re-split still reddens this gate.
        if "delta_seconds" in pair:
            pair["delta_seconds"] = "<clock>"
        for half in ("html", "json"):
            write = pair.get(half)
            if isinstance(write, dict):
                for key in PAIR_CLOCKS:
                    if key in write:
                        write[key] = "<clock>"
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False).replace("\r\n", "\n")


def check(payload):
    problems = []
    for path, fresh in ((JSON_OUT, dumps(payload)), (HTML_OUT, html_of(payload))):
        if not os.path.exists(path):
            problems.append("missing half " + os.path.basename(path))
            continue
        if normalized(rd_bytes(path)) != normalized(fresh):
            problems.append("landed half is not this derivation: " + os.path.basename(path))
    return problems


def main(argv):
    payload = census()
    if "--admissibility" in argv:
        face = admissibility(payload)
        if "--check" in argv:
            problems = admit_check(payload, face)
            if problems:
                print("PPC-ADMIT-CHECK VERDICT FAIL read_only=True")
                for p in problems:
                    print("  " + p)
                return 2
            print("PPC-ADMIT-CHECK VERDICT PASS read_only=True splits=%d admitted=%d "
                  "if_admitted=%d"
                  % (face["splits"], face["admitted"],
                     face["if_admitted"]["history_split_after"]))
            return 0
        problems = admit_problems(payload, face)
        if problems:
            print("PPC-ADMIT VERDICT FAIL read_only=True")
            for p in problems:
                print("  " + p)
            return 2
        if "--write" in argv:
            with io.open(ADMIT_OUT, "wb") as f:
                f.write(admit_dumps(face).encode("utf-8"))
            with io.open(ADMIT_HTML, "wb") as f:
                f.write(admit_html_of(face).encode("utf-8"))
        print("PPC-ADMIT VERDICT PASS read_only=%s splits=%d admitted=%d "
              "if_admitted=%d controls=%d checks=%d"
              % ("False" if "--write" in argv else "True", face["splits"],
                 face["admitted"], face["if_admitted"]["history_split_after"],
                 len(face["negative_controls"]), face["checks"]))
        for row in face["rows"]:
            print("  %s verdict=%s admitted=%s blocked_by=%s"
                  % (row["name"], row["receipt_verdict"] or "-",
                     row["would_be_admitted"], ",".join(row["blocked_by"]) or "-"))
        for con in face["negative_controls"]:
            print("  control %s ok=%s answer=%s"
                  % (con["control"], con["ok"], ",".join(con["answer"]) or "-"))
        return 0
    if "--check" in argv:
        problems = check(payload)
        if problems:
            print("PPC-CHECK VERDICT FAIL read_only=True")
            for p in problems:
                print("  " + p)
            return 2
        t = payload["totals"]
        print("PPC-CHECK VERDICT PASS read_only=True html=%d paired=%d "
              "history_split=%d channel_receipt=%d frozen_excused=%d same_commit=%d "
              "explained=%d"
              % (t["html"], t["paired"], t["history-split"], t["channel-receipt"],
                 t["frozen-excused"], t["same-commit"], t["explained"]))
        return 0

    with io.open(JSON_OUT, "wb") as f:
        f.write(dumps(payload).encode("utf-8"))
    with io.open(HTML_OUT, "wb") as f:
        f.write(html_of(payload).encode("utf-8"))
    t = payload["totals"]
    print("PPC (%s) round=%s html=%d paired=%d no_json=%d same_run=%d same_commit=%d "
          "history_split=%d frozen_excused=%d untracked=%d"
          % (LABEL, payload["round"], t["html"], t["paired"], t["no-json"], t["same-run"],
             t["same-commit"], t["history-split"], t["frozen-excused"], t["untracked"]))
    oldest = payload["oldest_split"]
    if oldest:
        print("  oldest history split: %s %.1fh (html %s / json %s)"
              % (oldest["name"], oldest["delta_hours"],
                 oldest["html_commit"] or "-", oldest["json_commit"] or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
