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
    {
        "slug": "lobby-session-trace",
        "producer": os.path.join("tools", "lobby_session_trace.py"),
        "why": ("fifth of the twelve splits (232.1h): html last committed at 700dd89a "
                "(the same R3288 back-hop channel), json at b0b07b2b, which shipped "
                "tools/lobby_session_trace.py and both halves in one commit; this "
                "producer is a live session (one sandbox server on loopback over a "
                "temp database), not a pure function, and it applies the back-hop "
                "channel itself"),
    },
    {
        "slug": "live-sandbox",
        "producer": os.path.join("tools", "ceo_live_shot.py"),
        "replay": {"function": "gallery", "table": "FACES"},
        "why": ("sixth of the twelve splits (147.3h): html last committed at 897e0f99 "
                "(the R3461 front-door round), json at 8092eff8, which shipped "
                "tools/ceo_live_shot.py and both halves in one commit; this producer "
                "is a real browser shoot, so a second shoot can never reproduce bytes "
                "- the page half is replayed from the landed report instead"),
    },
    {
        "slug": "city-face-report",
        "producer": os.path.join("tools", "city_face_report.py"),
        "replay": {"kind": "facts-report", "function": "render_html"},
        "why": ("seventh of the twelve splits (62.6h): html last committed at 897e0f99 "
                "(the R3461 front-door round), json at 700dd89a, which shipped the "
                "R3288 back-hop channel; this producer drives a live loopback server "
                "on an ephemeral port and stamps the clock into the page, so a second "
                "run can never reproduce bytes - the page and the report are replayed "
                "from the report it shipped beside"),
    },
    {
        "slug": "first-yuan",
        "producer": os.path.join("tools", "first_yuan_path.py"),
        "replay": {"kind": "landed-document", "function": "render_html"},
        "why": ("eighth of the twelve splits (62.6h): html last committed at 897e0f99 "
                "(the R3461 front-door round), json at 700dd89a, which shipped the "
                "R3288 back-hop channel; this producer reads six live reports plus the "
                "debt register and stamps its own byte sizes into BOTH halves, so the "
                "two landed halves record the sizes of two different moments - the "
                "page keeps the pre-channel numbers, the report the post-channel ones"),
    },
]

VOLATILE = ("generated_at", "round")

# The shipped channel stamps the shelf page's byte count into its own block at
# injection time. That number is a witness of WHEN the channel ran, not of what
# the pair is: it moves every time index.html grows, so a page spliced at R3461
# can never be reproduced byte for byte by a channel run today. AC-PPR9
# therefore compares the block with that one stamp normalised on BOTH sides and
# records both values, and the suite proves the normalisation is narrow.
SHELF_STAMP = re.compile(rb'data-back-bytes="\d+"')
# The same stamp is printed in the block's visible line ("2 个控件 · 55302B"),
# so it is normalised there too - and only there, keeping the controls count.
SHELF_SPAN = re.compile(rb'(\xe4\xb8\xaa\xe6\x8e\xa7\xe4\xbb\xb6 \xc2\xb7 )\d+(B</span>)')


def shelf_normalised(data):
    return SHELF_SPAN.sub(rb'\1*\2', SHELF_STAMP.sub(b'data-back-bytes="*"', data))


# The self-referential footer line a whole-document producer prints: it names
# both byte counts of the pair, and the landed page keeps the numbers from
# BEFORE the channel ran while the landed report keeps the numbers AFTER it.
# Reading the stamp back off the page is therefore not a convenience - it is the
# only value that makes the producer's own render reproducible.
SELF_SIZES = re.compile(rb'\xe5\xb0\xba\xe5\xaf\xb8 (\d+) B / (\d+) B')


def self_sizes_from_page(page):
    """The pair's own recorded sizes, read off the landed page (never guessed)."""
    found = SELF_SIZES.search(page)
    if not found:
        return None
    return {"html": int(found.group(1)), "json": int(found.group(2))}


def shelf_stamp(data):
    found = SHELF_STAMP.search(data)
    return int(found.group(0).split(b'"')[1]) if found else None


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


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render(face, workdir):
    """Run the face's producer into a scratch directory and return both halves.

    The producer is imported by path so no second copy of its body exists. A
    producer that cannot run is an 'unreproducible' reading, never an excuse.
    """
    name = "receipt_producer_%s" % face["slug"].replace("-", "_")
    path = os.path.join(REPO, face["producer"])
    module = load_module(path, name)
    html_path = os.path.join(workdir, "rendered.html")
    json_path = os.path.join(workdir, "rendered.json")
    # R3505: a producer that reads sys.argv inherits OUR flags, and
    # lobby_session_trace reads "--check" to mean "verify the landed pages
    # instead of rendering". Measured: running the receipt with --check made
    # that producer write nothing, so the receipt blamed the producer for a
    # FileNotFoundError it had caused itself. The producer now sees only its
    # own path and the two output paths, never this tool's flags.
    saved = sys.argv[:]
    sys.argv = [path, html_path, json_path]
    try:
        module.main(html_path, json_path)
    finally:
        sys.argv = saved
    return read_bytes(html_path), read_bytes(json_path)


def replay_render(face, workdir, landed_json_bytes, landed_html_bytes):
    """AC-PPR9: rebuild the page from the landed report with the producer's renderer.

    A live-shoot producer cannot be re-run to the same bytes - a second shoot
    brings a new clock stamp and new screenshots - so the only reproducible half
    left is the page-shaped one: the producer's own gallery applied to the
    report it shipped beside, with the page told it sits in preview/ exactly as
    the landed page does. No browser, no clock, no child process.
    """
    spec = face["replay"]
    path = os.path.join(REPO, face["producer"])
    module = load_module(path, "receipt_replay_%s" % face["slug"].replace("-", "_"))
    doc = json.loads(landed_json_bytes.decode("utf-8"))
    if spec.get("kind") == "facts-report":
        return facts_report_replay(face, module, doc, landed_json_bytes,
                                   landed_html_bytes, workdir)
    if spec.get("kind") == "landed-document":
        return landed_document_replay(face, module, doc, landed_json_bytes,
                                      landed_html_bytes, workdir)
    return gallery_replay(face, module, doc, landed_json_bytes, workdir)


def gallery_replay(face, module, doc, landed_json_bytes, workdir):
    spec = face["replay"]
    meta = {key: (title, blurb) for key, title, blurb in getattr(module, spec["table"])}
    rows = []
    for shot in doc.get("shots", []):
        title, blurb = meta[shot["face"]]
        rows.append({
            "face": shot["face"], "title": title, "blurb": blurb,
            "url": shot.get("url"), "status": shot.get("status"),
            "ok": shot.get("ok"), "acted": shot.get("acted"),
            "why": shot.get("why"), "errors": shot.get("errors") or [],
            "png": shot.get("png"),
        })
    html_path = os.path.join(workdir, "replayed.html")
    getattr(module, spec["function"])(rows, {"ok": doc.get("ok")}, html_path,
                                      proof=doc.get("proof"), page_dir=PREVIEW)
    return read_bytes(html_path), landed_json_bytes


def facts_report_replay(face, module, doc, landed_json_bytes, landed_html_bytes, workdir):
    """AC-PPR10: replay a live-run producer from the report it shipped beside.

    city_face_report measures a live loopback server (an ephemeral port) and
    stamps the clock into the page, so a second run can never reproduce the
    landed bytes. What IS reproducible is the pair as a function of its own
    report: the facts live in the json, and the two stamps the renderer needs
    (the loopback port and generated_utc) are read back off the landed page.
    The replay then runs the producer's own fixed-point loop - the page records
    its own byte size - and finally applies the shipped channel in the same
    order the R3288 round did: splice the block into the page, then restamp
    the json's recorded sizes with the post-channel byte counts.

    The claim this buys is narrow and stated: html is the producer's render of
    the landed facts, and json is that same render with only its size block
    restamped. Nothing about the live world is re-measured.
    """
    facts = doc.get("facts")
    generated = doc.get("generated_utc")
    if not isinstance(facts, dict) or not generated:
        raise ValueError("landed report carries no facts/generated_utc")
    port = port_from_page(module, landed_html_bytes)
    if port is None:
        raise ValueError("landed page carries no loopback port stamp")
    stamps = {"generated_utc": generated, "port": port}
    # The landed report is checked out with CRLF on this working tree while the
    # producer writes LF. That is a repo EOL artifact, not a derivation gap:
    # the replay adopts the landed newline so the two halves are comparable
    # byte for byte, and the choice is recorded on the row.
    crlf = b"\r\n" in landed_json_bytes

    sizes = {"html": 0, "json": 0}
    body = b""
    payload = b""
    for _ in range(6):
        rows = module.verify(facts, sizes)
        body = module.render_html(facts, stamps, rows).encode("utf-8")
        document = module._document(facts, stamps, rows, sizes)
        payload = (json.dumps(document, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
        measured = {"html": len(body), "json": len(payload)}
        if measured == sizes:
            break
        sizes = measured
    else:
        raise ValueError("document sizes did not converge")

    # The producer writes LF; the landed report is checked out with CRLF on this
    # tree. The page's own criterion row records the LF numbers the producer
    # measured, so the newline conversion happens after the loop, exactly where
    # the working-tree conversion happened for the landed file.
    if crlf:
        payload = payload.replace(b"\n", b"\r\n")

    html_path = os.path.join(workdir, "rendered.html")
    json_path = os.path.join(workdir, "rendered.json")
    with io.open(json_path, "wb") as handle:
        handle.write(payload)
    injected, _how = face_backhop.inject_text(body.decode("utf-8"),
                                              face["slug"] + ".html")
    with io.open(html_path, "wb") as handle:
        handle.write(injected.encode("utf-8"))
    # The channel's second step: the json's recorded sizes are restamped to the
    # post-channel byte counts by editing the digits in place, so the document
    # keeps the producer's formatting. The html keeps the pre-channel numbers
    # in its criterion row, which is exactly what the landed pair shows.
    face_backhop.patch_sizes(html_path)
    return body, read_bytes(json_path)


def landed_document_replay(face, module, doc, landed_json_bytes, landed_html_bytes, workdir):
    """AC-PPR11: replay a whole-document producer from the report it shipped beside.

    first_yuan_path reads six live reports plus the debt register, and it prints
    its own byte counts into BOTH halves. Those counts are not one number seen
    twice: the landed page carries the pre-channel pair (3911 / 2600, the LF
    bytes the producer wrote) while the landed report carries the post-channel
    pair (4593 / 2701, the working-tree CRLF bytes the channel's size patch
    measured). So the replay takes its facts from the report and its sizes stamp
    from the PAGE - guessing either one from the other would make the render
    unreproducible for a reason that is not a derivation gap.

    What this buys is stated narrowly: the page is the producer's own
    render_html applied to the landed document, and the report is that same
    document re-serialised and then restamped by the shipped channel against the
    post-channel page. Nothing about the live world is re-measured.
    """
    sizes = self_sizes_from_page(landed_html_bytes)
    if sizes is None:
        raise ValueError("landed page carries no self-referential sizes stamp")
    document = dict(doc)
    document["sizes"] = sizes
    body = module.render_html(document).encode("utf-8")
    # The landed report is checked out with CRLF on this working tree while the
    # producer writes LF (R3506 measured the same split on another face); the
    # replay adopts the landed newline so the two reports are comparable byte
    # for byte, and the choice is recorded on the row.
    crlf = b"\r\n" in landed_json_bytes
    payload = (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True)
               + "\n").encode("utf-8")
    if crlf:
        payload = payload.replace(b"\n", b"\r\n")

    html_path = os.path.join(workdir, "rendered.html")
    json_path = os.path.join(workdir, "rendered.json")
    with io.open(json_path, "wb") as handle:
        handle.write(payload)
    injected, _how = face_backhop.inject_text(body.decode("utf-8"),
                                              face["slug"] + ".html")
    with io.open(html_path, "wb") as handle:
        handle.write(injected.encode("utf-8"))
    face_backhop.patch_sizes(html_path)
    return body, read_bytes(json_path)


def port_from_page(module, landed_html_bytes):
    """The loopback port the landed page was rendered with (never guessed)."""
    host = getattr(module, "HOST", "127.0.0.1").encode("utf-8")
    found = re.search(re.escape(host) + rb":(\d+)", landed_html_bytes)
    return found.group(1).decode("ascii") if found else None


def applied_channel_verdict(rendered, landed):
    """AC-PPR8: a producer that applies the channel itself is compared directly.

    There is no block for the receipt to splice in, so the reading cannot lean
    on the channel at all: equal bytes are one derivation, anything else is a
    drift with the first differing byte named.
    """
    if rendered == landed:
        return "one-derivation", None
    return "drift", first_diff(rendered, landed)


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
    problems = [] if face.get("replay") else output_discipline(face)
    if problems:
        row["verdict"] = "unreproducible"
        row["error"] = ("producer cannot render into a scratch directory: "
                        + "; ".join(problems))
        return row

    work = tempfile.mkdtemp(prefix="face-pair-receipt-")
    try:
        try:
            if face.get("replay"):
                # AC-PPR9 / AC-PPR10 / AC-PPR11: the pair is replayed from the
                # landed report, and the label names which replay shape read it.
                label = "%s-from-report" % face["replay"]["function"]
                if face["replay"].get("kind") == "landed-document":
                    label = "%s-from-landed-document" % face["replay"]["function"]
                row["replay"] = label
                rendered, rendered_json = replay_render(
                    face, work, read_bytes(landed_json_path),
                    read_bytes(landed_html_path))
            else:
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
        # AC-PPR8: this producer already applies the shipped channel to its own
        # page, so there is no block for the receipt to splice. The reading is
        # then the strictest one available: the producer's own html must equal
        # the landed page byte for byte, with no block surgery to hide a gap.
        verdict, at = applied_channel_verdict(rendered, landed)
        row["raw_first_diff_offset"] = at
        row["channel_how"] = "producer-applied"
        row["spliced_html_bytes"] = len(rendered)
        row["spliced_html_sha256"] = sha256_hex(rendered)
        if verdict == "one-derivation":
            row["verdict"] = "one-derivation"
            row["receipt"] = "producer-applies-channel"
            row["detail"] = ("the producer carries the shipped channel block itself and its "
                             "own html equals the landed page byte for byte (%d bytes)" % len(landed))
        else:
            row["verdict"] = "drift"
            row["first_diff_offset"] = at
            row["first_diff_context"] = context(landed, at)
            row["detail"] = ("the producer carries the channel block itself, and its html "
                             "differs from the landed page: first difference at byte %d" % at)
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
    # AC-PPR9: the only tolerated difference is the channel's own shelf stamp.
    # Both values are recorded, and the suite pins that this normalisation is
    # narrow enough that any other single-byte change still reads drift.
    if delta is not None and shelf_normalised(injected) == shelf_normalised(landed):
        row["verdict"] = "one-derivation"
        row["receipt"] = "channel-shelf-stamp"
        row["shelf_stamp_landed"] = shelf_stamp(landed)
        row["shelf_stamp_now"] = shelf_stamp(injected)
        # R3506: the digest is taken over the shelf-NORMALISED page, because the
        # raw digest of a page that embeds a clock is itself a clock - it moved
        # 55645 -> 56041 with every verdict unchanged. The normalised digest
        # still detects any other byte, which is what the page is for.
        row["spliced_html_sha256"] = sha256_hex(shelf_normalised(injected))
        row["detail"] = ("landed html = producer html + the shipped channel block, equal "
                         "byte for byte once the channel's own shelf stamp is normalised "
                         "on both sides (landed %s, today %s): the stamp records when the "
                         "channel ran, not which derivation the page is"
                         % (row["shelf_stamp_landed"], row["shelf_stamp_now"]))
        return row

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
                "plus the shipped post-render channel, reproduces the landed html byte for byte "
                "- and for a producer that applies the channel itself, when its own html equals "
                "the landed page with no block surgery at all"),
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
# R3506: the channel's shelf stamp is a witness of WHEN the channel ran, not of
# which derivation the page is - it moves every time index.html grows, i.e. on
# every round that re-derives the entry index. AC-PPR9 already normalises that
# one number out of the byte comparison; the page then records both values as
# evidence, and those recorded values (plus the digest of a page that embeds
# them, and the sentence that quotes them) are clocks too. Treating them as
# measurements made the page red for a reason that is not a defect: measured
# 2026-11-26, shelf_stamp_now moved 55645 -> 56041 with every per-face verdict
# unchanged. The stable claim is the shelf-normalised byte equality, which the
# verdict records and the suite pins with a negative control.
WITNESS = ("shelf_stamp_now", "shelf_stamp_landed")
SHELF_DIGITS = re.compile(r"(landed|today) \d+")


def normalized(data):
    text = data.decode("utf-8") if isinstance(data, bytes) else data
    try:
        obj = json.loads(text)
    except Exception:
        # The page prints the round it was derived at and, in each detail
        # sentence, the two shelf stamps; neither is a measurement, so --check
        # ignores them the same way the census page does (R3499 precedent) -
        # every per-face size and digest is still compared byte for byte, so a
        # tampered reading is never excused by this.
        text = ROUND_LABEL.sub("Tick <volatile>", text)
        text = SHELF_DIGITS.sub(r"\1 <stamp>", text)
        return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n"))
    for key in VOLATILE:
        if key in obj:
            obj[key] = "<volatile>"
    for row in obj.get("faces") or ():
        if not isinstance(row, dict):
            continue
        for key in WITNESS:
            if key in row:
                row[key] = "<volatile>"
        if isinstance(row.get("detail"), str):
            row["detail"] = SHELF_DIGITS.sub(r"\1 <stamp>", row["detail"])
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
