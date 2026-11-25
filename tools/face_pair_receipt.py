"""Per-face receipt: prove one preview pair is one derivation (R3500).

R3499's census left twelve history splits standing and named why neither a
re-render from the old json nor a blind re-derivation could heal them: the
landed html had been touched by later commits (the R3288 post-render channel,
the R3461 front door) while the json stayed at its producer commit. The board
therefore asked for ONE face at a time: re-render the producer into a scratch
directory, apply the shipped post-render channel, and compare the result with
the landed html byte for byte. If the pair really is one derivation, the
comparison is exact and the split is explained; if it is not, the first
differing byte is named and nothing is excused.

Criteria AC-PPR1..AC-PPR6 were pinned in src/os/backlog.md at R3500 BEFORE
this file existed.

Nothing here rewrites a preview page. The producer renders into the system temp
directory and is removed; the only files this tool writes are its own pair
(preview/face-pair-receipt.json and .html). No child process, no socket.

Source discipline: ASCII only, stdlib only, no clock read beyond the page stamp.
"""

import ast
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
PREVIEW = os.path.join(REPO, "preview")
STATE = os.path.join(REPO, "src", "os", "state.json")
LABEL = "face-pair-receipt"
JSON_OUT = os.path.join(PREVIEW, LABEL + ".json")
HTML_OUT = os.path.join(PREVIEW, LABEL + ".html")

sys.path.insert(0, BASE)

import face_backhop  # noqa: E402  (single definition of the post-render channel)

# One face per round, by design: a receipt is evidence for a specific pair, and
# adding twelve at once is exactly the mass re-derivation the board forbade.
FACES = [
    {
        "slug": "apimarket-report-refunds",
        "producer": os.path.join("src", "os", "preview_R2111.py"),
        "why": ("oldest survivor of the twelve splits: html last committed at "
                "700dd89a (the R3288 back-hop channel), json at 6fb6c40b (the "
                "R2111 producer)"),
    },
    {
        "slug": "apimarket-report-questions",
        "producer": os.path.join("src", "os", "preview_R2118.py"),
        "why": ("next oldest of the twelve splits (743.8h): html last committed at "
                "700dd89a (the same R3288 back-hop channel), json at e0fd7251 (the "
                "R2118 pre-purchase Q&A producer)"),
    },
    {
        "slug": "apimarket-report-buyerquestions",
        "producer": os.path.join("src", "os", "preview_R2119.py"),
        "why": ("third oldest of the twelve splits (742.4h): html last committed at "
                "700dd89a (the same R3288 back-hop channel), json at d3faa192 (the "
                "R2119 buyer-question-history producer)"),
    },
    {
        "slug": "apimarket-report-selleranswers",
        "producer": os.path.join("src", "os", "preview_R2120.py"),
        "why": ("fourth of the twelve splits: html last committed at 700dd89a (the "
                "same R3288 back-hop channel), json at ce3583ca, which shipped "
                "preview_R2120.py in the same commit (seller answered-question "
                "ledger, schema 12->13)"),
    },
]

VOLATILE = ("generated_at", "round")


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    with io.open(path, "rb") as f:
        return f.read()


def first_diff(a, b):
    """Offset of the first differing byte, or None when the two are equal."""
    limit = min(len(a), len(b))
    for i in range(limit):
        if a[i] != b[i]:
            return i
    return None if len(a) == len(b) else limit


def context(data, offset, width=40):
    start = max(0, offset - width)
    return data[start:offset + width].decode("utf-8", "replace")


def evaluate_output_discipline(source, slug):
    """AC-PPR7: can this producer render somewhere other than preview/?

    A receipt may only be taken into a scratch directory, so the producer's
    module-level main must accept exactly two defaulted output paths, and its
    own defaults must still name this face's landed halves - so a no-argument
    run keeps writing exactly the same files it always wrote.
    """
    problems = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return ["producer does not parse: %s" % exc]
    mains = [n for n in tree.body
             if isinstance(n, ast.FunctionDef) and n.name == "main"]
    if not mains:
        return ["producer has no module-level main"]
    args = mains[0].args
    if len(args.args) != 2 or len(args.defaults) != 2:
        problems.append("main takes %d positional args with %d defaults, not two outputs"
                        % (len(args.args), len(args.defaults)))
    for half in ("%s.html" % slug, "%s.json" % slug):
        if half not in source:
            problems.append("producer never names its own half %s" % half)
    if "preview" not in source:
        problems.append("producer never names the preview directory")
    return problems


def output_discipline(face):
    path = os.path.join(REPO, face["producer"])
    try:
        source = io.open(path, encoding="utf-8").read()
    except OSError as exc:
        return ["producer source is unreadable: %s" % exc]
    return evaluate_output_discipline(source, face["slug"])


def render(face, workdir):
    """Run the face's producer into a scratch directory and return both halves.

    The producer is imported by path so no second copy of its body exists. A
    producer that cannot run is an 'unreproducible' reading, never an excuse.
    """
    name = "receipt_producer_%s" % face["slug"].replace("-", "_")
    path = os.path.join(REPO, face["producer"])
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    html_path = os.path.join(workdir, "rendered.html")
    json_path = os.path.join(workdir, "rendered.json")
    module.main(html_path, json_path)
    return read_bytes(html_path), read_bytes(json_path)


def measure(face):
    """One receipt for one face: render, apply the channel, compare with disk.

    Three outcomes, and the difference between them is the whole point:

      one-derivation  landed html == producer html + channel block, byte for byte
      version-drift   the landed page predates the current renderer (its schema
                      number is older and the current badge is absent), so no
                      re-render at HEAD can reproduce it; the split is explained
                      but NOT excused
      drift           the pair disagrees for a reason nobody has named yet
    """
    slug = face["slug"]
    landed_html_path = os.path.join(PREVIEW, slug + ".html")
    landed_json_path = os.path.join(PREVIEW, slug + ".json")
    row = {
        "slug": slug,
        "producer": face["producer"].replace("\\", "/"),
        "why": face["why"],
        "landed_html": "preview/%s.html" % slug,
        "landed_json": "preview/%s.json" % slug,
    }
    problems = output_discipline(face)
    if problems:
        row["verdict"] = "unreproducible"
        row["error"] = ("producer cannot render into a scratch directory: "
                        + "; ".join(problems))
        return row

    work = tempfile.mkdtemp(prefix="face-pair-receipt-")
    try:
        try:
            rendered, rendered_json = render(face, work)
        except Exception as exc:  # noqa: BLE001 - the reading is the point
            row["verdict"] = "unreproducible"
            row["error"] = "%s: %s" % (type(exc).__name__, exc)
            return row
    finally:
        shutil.rmtree(work, ignore_errors=True)

    landed = read_bytes(landed_html_path)
    landed_json_bytes = read_bytes(landed_json_path)
    channel, how = face_backhop.inject_text(rendered.decode("utf-8"), slug + ".html")
    injected = channel.encode("utf-8")

    # Where the channel spliced its block: the first difference between the
    # producer's own html and the injected one is the block's insertion point.
    splice = first_diff(rendered, injected)
    block = b"" if splice is None else injected[splice:splice + (len(injected) - len(rendered))]

    landed_schema = None
    current_schema = None
    try:
        landed_schema = json.loads(landed_json_bytes.decode("utf-8")).get("schema_version")
        producer_doc = json.loads(rendered_json.decode("utf-8"))
        current_schema = producer_doc.get("schema_version")
    except Exception:
        pass

    row.update({
        "rendered_html_bytes": len(rendered),
        "rendered_html_sha256": sha256_hex(rendered),
        "rendered_json_bytes": len(rendered_json),
        "rendered_json_sha256": sha256_hex(rendered_json),
        "channel_how": how,
        "channel_block_bytes": len(block),
        "splice_offset": splice,
        "spliced_html_bytes": len(injected),
        "spliced_html_sha256": sha256_hex(injected),
        "landed_html_bytes": len(landed),
        "landed_html_sha256": sha256_hex(landed),
        "landed_json_bytes": len(landed_json_bytes),
        "landed_json_sha256": sha256_hex(landed_json_bytes),
        "landed_schema_version": landed_schema,
        "current_schema_version": current_schema,
        "json_same_as_render": landed_json_bytes == rendered_json,
        "landed_carries_schema_badge": b'data-report-schema="' in landed,
    })

    if splice is None:
        row["verdict"] = "channel-noop"
        row["detail"] = "the shipped channel changed nothing, so it cannot explain any gap"
        return row

    delta = first_diff(injected, landed)
    # AC-PPR2 / AC-PPR3: equality is claimed only when the landed page is
    # EXACTLY the producer html with the channel block spliced in, and the
    # un-injected render is proved to differ at that same offset.
    exact = (landed == rendered[:splice] + block + rendered[splice:])
    raw_delta = first_diff(rendered, landed)
    row["raw_first_diff_offset"] = raw_delta
    if delta is None and exact:
        row["verdict"] = "one-derivation"
        row["receipt"] = "channel-splice"
        row["detail"] = ("landed html = producer html with the shipped post-render "
                         "block spliced at byte %d (%d bytes)" % (splice, len(block)))
        return row

    at = splice if delta is None else delta
    row["first_diff_offset"] = at
    row["first_diff_context"] = context(landed, at)
    # A page rendered before the schema badge existed cannot be reproduced by a
    # renderer that always writes it: that is a version gap, not a lost splice.
    if (not row["landed_carries_schema_badge"] and landed_schema is not None
            and current_schema is not None and landed_schema != current_schema):
        row["verdict"] = "version-drift"
        row["detail"] = ("landed page is a schema %s render and the renderer is at schema %s, "
                         "so no re-render at HEAD can reproduce it; explained, not excused: "
                         "first difference at byte %d"
                         % (landed_schema, current_schema, at))
    else:
        row["verdict"] = "drift"
        row["detail"] = ("landed html is not the producer html plus the channel block: "
                         "first difference at byte %d" % at)
    return row


def receipt():
    tick = 0
    try:
        tick = int(json.load(io.open(STATE, "r", encoding="utf-8")).get("tick", 0))
    except Exception:
        pass
    import datetime
    rows = [measure(face) for face in FACES]
    return {
        "generated_at": datetime.datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "round": tick,
        "source": "tools/face_pair_receipt.py",
        "law": ("a history split is excused for one face only when the producer's own html, "
                "plus the shipped post-render channel, reproduces the landed html byte for byte"),
        "faces": rows,
        "totals": {
            "faces": len(rows),
            "one_derivation": sum(1 for r in rows if r["verdict"] == "one-derivation"),
            "version_drift": sum(1 for r in rows if r["verdict"] == "version-drift"),
            "drift": sum(1 for r in rows if r["verdict"] == "drift"),
            "unreproducible": sum(1 for r in rows if r["verdict"] == "unreproducible"),
        },
    }


STYLE = ("body{font:15px/1.55 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;margin:0;"
         "background:#12140f;color:#e8e6df}.wrap{max-width:900px;margin:0 auto;padding:32px 20px 64px}"
         "h1{font-size:23px;margin:0 0 6px}.sub{color:#9a9b90;margin:0 0 18px;font-size:13px}"
         ".banner{border-left:3px solid #c8a24a;background:#1c1e18;padding:12px 14px;margin:0 0 20px;font-size:14px}"
         "table{width:100%;border-collapse:collapse;font-size:13px}"
         "th,td{text-align:left;padding:7px 8px;border-bottom:1px solid #2c2f26;vertical-align:top}"
         "th{color:#9a9b90;font-weight:600;font-size:12px}"
         "code{font:12px/1.4 ui-monospace,Consolas,monospace;color:#d8d6ca}"
         ".ok{color:#7fb2e5}.bad{color:#e0b25a}"
         "footer{color:#6f7066;font-size:12px;margin-top:26px}")


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def html_of(payload):
    t = payload["totals"]
    body = []
    for r in payload["faces"]:
        cls = "ok" if r["verdict"] == "one-derivation" else "bad"
        rows = [
            ("producer", esc(r["producer"])),
            ("why this face", esc(r["why"])),
            ("producer html", "%d B / <code>%s</code>" % (r.get("rendered_html_bytes", 0),
                                                           esc(r.get("rendered_html_sha256", "-")))),
            ("+ post-render channel", "%s &rarr; %d B / <code>%s</code>"
             % (esc(r.get("channel_how", "-")), r.get("spliced_html_bytes", 0),
                esc(r.get("spliced_html_sha256", "-")))),
            ("landed html", "%d B / <code>%s</code>" % (r.get("landed_html_bytes", 0),
                                                         esc(r.get("landed_html_sha256", "-")))),
            ("landed json", "%d B / <code>%s</code>%s"
             % (r.get("landed_json_bytes", 0), esc(r.get("landed_json_sha256", "-")),
                "" if r.get("json_same_as_render") else " &middot; json differs from the render")),
            ("schema", "landed %s &rarr; renderer %s &middot; badge on landed page: %s"
             % (esc(r.get("landed_schema_version", "-")), esc(r.get("current_schema_version", "-")),
                "yes" if r.get("landed_carries_schema_badge") else "no")),
            ("detail", esc(r.get("detail", r.get("error", "-")))),
        ]
        body.append('<tr><td><b>%s</b><br><span class="%s">%s</span></td><td>%s</td></tr>'
                    % (esc(r["slug"]), cls, esc(r["verdict"]),
                       "<br>".join("%s: %s" % (k, v) for k, v in rows)))
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<title>BigDomain &middot; face pair receipt</title><style>%s</style></head><body>'
            '<div class="wrap"><h1>Face pair receipt: one split at a time</h1>'
            '<p class="sub">Tick %d &middot; %d face &middot; one-derivation %d &middot; '
            'version-drift %d &middot; drift %d &middot; unreproducible %d &middot; derived by %s</p>'
            '<div class="banner">A history split is excused for a face only when the producer\'s '
            'own html, plus the shipped post-render channel, reproduces the landed html byte for '
            'byte. A landed page that moved after this receipt is not covered by it, and a page '
            'older than the current renderer is explained, never excused.</div>'
            '<table><thead><tr><th>face</th><th>reading</th></tr></thead><tbody>%s</tbody></table>'
            '<footer>Non-advisory notice: this is a build status page, not investment advice. '
            'The producer renders into a scratch directory that is removed; no preview page is '
            'rewritten by this tool.</footer></div></body></html>\n'
            % (STYLE, payload["round"], t["faces"], t["one_derivation"], t["version_drift"],
               t["drift"], t["unreproducible"], payload["source"], "\n".join(body)))


def dumps(payload):
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


ROUND_LABEL = re.compile(r"Tick \d+")


def normalized(data):
    text = data.decode("utf-8") if isinstance(data, bytes) else data
    try:
        obj = json.loads(text)
    except Exception:
        # The page prints the round it was derived at; that label is not a
        # measurement, so --check ignores it the same way the census page does
        # (R3499 precedent) - every per-face size and digest is still compared
        # byte for byte, so a tampered reading is never excused by this.
        text = ROUND_LABEL.sub("Tick <volatile>", text)
        return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n"))
    for key in VOLATILE:
        if key in obj:
            obj[key] = "<volatile>"
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False).replace("\r\n", "\n")


def check(payload):
    problems = []
    for path, fresh in ((JSON_OUT, dumps(payload)), (HTML_OUT, html_of(payload))):
        if not os.path.exists(path):
            problems.append("missing half " + os.path.basename(path))
            continue
        if normalized(read_bytes(path)) != normalized(fresh):
            problems.append("landed half is not this derivation: " + os.path.basename(path))
    return problems


def main(argv):
    payload = receipt()
    t = payload["totals"]
    if "--check" in argv:
        problems = check(payload)
        if problems:
            print("FPR-CHECK VERDICT FAIL read_only=True")
            for p in problems:
                print("  " + p)
            return 2
        print("FPR-CHECK VERDICT PASS read_only=True faces=%d one_derivation=%d drift=%d"
              % (t["faces"], t["one_derivation"], t["drift"]))
        return 0 if t["drift"] == 0 and t["unreproducible"] == 0 else 2

    with io.open(JSON_OUT, "wb") as f:
        f.write(dumps(payload).encode("utf-8"))
    with io.open(HTML_OUT, "wb") as f:
        f.write(html_of(payload).encode("utf-8"))
    for r in payload["faces"]:
        print("%-32s %-16s %s" % (r["slug"], r["verdict"], r.get("detail", r.get("error", ""))))
    print("FPR (%s) round=%s faces=%d one_derivation=%d drift=%d unreproducible=%d"
          % (LABEL, payload["round"], t["faces"], t["one_derivation"], t["drift"],
             t["unreproducible"]))
    return 0 if t["drift"] == 0 and t["unreproducible"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
