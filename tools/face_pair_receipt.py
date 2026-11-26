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
import contextlib
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
        # R3514: this pair is NOT reproduced by the HEAD renderer (schema 6 vs
        # 17), so a version-drift reading alone leaves the question "was the page
        # edited by hand?" open. It was answered by replaying the producer AS IT
        # STOOD at the commit that wrote the pair: `git archive --output=<tar>
        # 6fb6c40b src` into a system temp tree, then that tree's own
        # preview_R2111.main() (no network, pinned demo clocks). Both halves came
        # back byte for byte, so the split is producer evolution, not editing.
        # The replay cannot live inside this tool (AC-PPR4 bans a child process),
        # so the digests are recorded and re-checked against the landed files.
        "historical": {
            "commit": "6fb6c40b",
            "method": ("git archive --output=<tar> 6fb6c40b src > tarfile, extract to a "
                       "temp tree, run that tree's preview_R2111.main() in process"),
            "rendered_html_bytes": 25254,
            "rendered_html_sha256_12": "5074953de674",            "rendered_json_bytes": 39928,
            "rendered_json_sha256_12": "6c96d0903068",
            "landed_html_bytes": 25966,
            "landed_html_sha256_12": "3d557fa82348",
            "landed_json_bytes": 39928,
            "landed_json_sha256_12": "6c96d0903068",
            "json_byte_identical": True,
            "html_channel_splice": ("the rendered page plus the shipped channel block "
                                    "equals the landed page byte for byte once the "
                                    "channel's own shelf stamp is normalised"),
        },
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
    {
        "slug": "membership-benefit-report",
        "producer": os.path.join("tools", "membership_benefit_report.py"),
        "replay": {"kind": "facts-report", "function": "render_html", "port": False,
                   "stamp_keys": ["expires", "periods"]},
        "why": ("ninth of the twelve splits (62.6h): html last committed at 897e0f99 "
                "(the R3461 front-door round), json at 700dd89a, which shipped the "
                "R3288 back-hop channel; this producer builds its member/lobby/ledger "
                "world IN PROCESS over a temp directory, so its page carries no "
                "loopback port stamp - the report's own top-level expires/periods are "
                "the stamps that make the render reproducible (AC-PPR12)"),
    },
    {
        "slug": "ledger-business-report",
        "producer": os.path.join("tools", "ledger_business_report.py"),
        "replay": {"kind": "clock-identity", "function": "build_html"},
        "why": ("tenth of the twelve splits: html last committed at 897e0f99 (the "
                "R3461 front-door round), json at 700dd89a, which shipped the R3288 "
                "back-hop channel; this producer seeds a demo ledger through the "
                "shipped Ledger API and every tx id is a content hash over the write "
                "second, so a later run reproduces the pair only when the clock is "
                "pinned to the second its own landed report records (AC-PPR13)"),
    },
    {
        "slug": "payment-gate-report",
        "producer": os.path.join("tools", "payment_gate_report.py"),
        "replay": {"kind": "clock-pin", "function": "main"},
        "why": ("eleventh of the twelve splits: html last committed at 897e0f99 (the "
                "R3461 front-door round), json at 700dd89a, which shipped the R3288 "
                "back-hop channel; this producer reads the wall clock in TWO packages "
                "- its own stamp plus the stale-timestamp refusals inside the shipped "
                "payment sandbox - so the pair is reproduced only when both sources "
                "are pinned to the second its landed report records (AC-PPR14)"),
    },
    {
        "slug": "platform-live-report",
        "producer": os.path.join("tools", "platform_live_report.py"),
        "replay": {
            "kind": "facts-spread-report",
            "function": "render",
            "facts_from": {
                "faces": "faces",
                "pages": "pages",
                "ports": "ports",
                "children_gone": "children_gone",
                "city_snapshot": "city_snapshot",
                "hub_live": "hub_live",
                "ports_refusing": "ports_refusing_after_teardown",
                "shipped_before": "shipped_sha256",
            },
        },
        "why": ("twelfth of the twelve splits: html last committed at 897e0f99 (the "
                "R3461 front-door round), json at 7e3a6f9c (R3333), which shipped the "
                "sandbox one-click proof; this producer starts eight real servers, reads "
                "every door over a socket and tears them down, and it keeps its facts at "
                "the TOP level of its report with no evidence block - the graded rows are "
                "the evidence and the hub URL is read back off the landed page (AC-PPR15)"),
    },
]

# The stamp a wall-clock producer records for its own render. Shape is the
# producer's, not the ledger's: "YYYY-MM-DD HH:MM:SSZ" (the ledger's own ts
# dialect uses a "T" separator, and the replay converts).
CLOCK_STAMP = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\dZ$")

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
    if spec.get("kind") == "clock-identity":
        return clock_identity_replay(face, module, doc, landed_json_bytes,
                                     landed_html_bytes, workdir)
    if spec.get("kind") == "clock-pin":
        return clock_pin_replay(face, module, doc, landed_json_bytes,
                                landed_html_bytes, workdir)
    if spec.get("kind") == "facts-spread-report":
        return facts_spread_replay(face, module, doc, landed_json_bytes,
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
    spec = face["replay"]
    stamps = {"generated_utc": generated}
    # AC-PPR12: a producer that measures its world in process stamps no loopback
    # port into its page, so the stamps that make its render reproducible are the
    # ones its own report records. Every declared key must be present - a report
    # missing one is refused rather than replayed with the gap guessed over.
    for key in spec.get("stamp_keys") or []:
        if key not in doc:
            raise ValueError("landed report carries no %s stamp" % key)
        stamps[key] = doc[key]
    if spec.get("port", True):
        port = port_from_page(module, landed_html_bytes)
        if port is None:
            raise ValueError("landed page carries no loopback port stamp")
        stamps["port"] = port
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


def page_url_with_port(page, port):
    """The url the landed page prints for one loopback port (never guessed)."""
    if port is None:
        return None
    prefix = b"http://127.0.0.1:" + str(port).encode("ascii")
    found = re.search(re.escape(prefix) + rb"(/[^\"<\s]*)", page)
    return found.group(0).decode("utf-8") if found else None


def facts_spread_replay(face, module, doc, landed_json_bytes, landed_html_bytes, workdir):
    """AC-PPR15: replay a live-run report whose facts sit at the TOP level.

    platform_live_report starts eight real servers, reads every door over a
    socket and tears the lot down, so a second run can never reproduce bytes:
    the ports are OS-assigned and the pages it reads are live. What is
    reproducible is the pair as a function of the report it shipped beside -
    but that report keeps its facts at top-level keys (faces, pages, ports,
    children_gone, ...) instead of one facts dict, and it carries no evidence
    block: the graded rows ARE the evidence. The one stamp the report does not
    record is the hub URL as the page prints it, so that is read back off the
    landed page by the port the report itself names. The report's fingerprint
    pins what the run proved and never the ephemeral ports, so reproducing it
    from the landed facts is what proves this is the landed run and not a
    fresh measurement.
    """
    spec = face["replay"]
    rows = doc.get("criteria")
    if not isinstance(rows, list) or not rows:
        raise ValueError("landed report carries no criteria list")
    # The report carries every criterion, but only the ones the page graded at
    # render time were ever evidence; the rest say so on the landed page with a
    # "later" row. Reading that set off the page keeps the evidence block the
    # producer's own, instead of rebuilding it from a guess.
    later = {cid.decode("ascii") for cid in
             re.findall(rb'<tr class="later"><td>([A-Z0-9-]+)</td>', landed_html_bytes)}
    evidence = {row["id"]: {"pass": bool(row["pass"]),
                            "measured": str(row["measured"])}
                for row in rows if row["id"] not in later}
    facts = {}
    for key, source in spec["facts_from"].items():
        if source not in doc:
            raise ValueError("landed report carries no %s" % source)
        facts[key] = doc[source]
    hub_port = (doc.get("ports") or {}).get("hub")
    hub_url = page_url_with_port(landed_html_bytes, hub_port)
    if hub_url is None:
        raise ValueError("landed page carries no hub url stamp")
    facts["hub_url"] = hub_url
    if module._fingerprint(evidence, facts) != doc.get("fingerprint"):
        raise ValueError("landed facts do not reproduce the report fingerprint")

    page, data = module.render(evidence, facts)
    body = page.encode("utf-8")
    html_bytes = len(body)
    prev_json = 0
    payload = b""
    for _ in range(12):
        data["sizes"] = {"html": html_bytes, "json": prev_json}
        row8 = module.ac_plr8(page, html_bytes, prev_json)
        row9 = module.ac_plr9(page, module.CRITERIA)
        for row in data["criteria"]:
            if row["id"] == "AC-PLVR8":
                row["pass"], row["measured"] = row8["pass"], row8["measured"]
            elif row["id"] == "AC-PLVR9":
                row["pass"], row["measured"] = row9["pass"], row9["measured"]
        data["passed"] = sum(1 for c in data["criteria"] if c["pass"])
        data["verdict"] = "PASS" if data["passed"] == data["total"] else "FAIL"
        payload = (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
        if prev_json == len(payload):
            break
        prev_json = len(payload)
    else:
        raise ValueError("document sizes did not converge")

    json_path = os.path.join(workdir, "rendered.json")
    with io.open(json_path, "wb") as handle:
        handle.write(payload)
    injected, _how = face_backhop.inject_text(page, face["slug"] + ".html")
    html_path = os.path.join(workdir, "rendered.html")
    with io.open(html_path, "wb") as handle:
        handle.write(injected.encode("utf-8"))
    face_backhop.patch_sizes(html_path)
    return body, read_bytes(json_path)


def clock_identity_replay(face, module, doc, landed_json_bytes, landed_html_bytes, workdir):
    """AC-PPR13: replay a wall-clock producer from the second its report records.

    ledger_business_report seeds a throwaway demo ledger through the shipped
    Ledger API, and every tx id is a content hash over the write timestamp:
    _write_tx takes the wall clock, so no later run can reproduce the three ids
    - unless the clock is pinned to the second the landed report stamped. The
    replay therefore pins ledger.now_utc to that second, re-seeds through the
    producer's own seed_demo, runs the shipped reconcile IN PROCESS (stdout
    captured, no child process) and renders with the producer's own build_html.

    What this buys is stated narrowly: the pair is the producer's render of a
    world rebuilt from the landed facts under the landed clock. The demo
    database is re-seeded, which is what the producer's own AC-LBR10 note says
    it is - an output, not an input. Nothing about the live world is
    re-measured.
    """
    stamp = doc.get("generated_utc")
    if not isinstance(stamp, str) or not CLOCK_STAMP.match(stamp):
        raise ValueError("landed report carries no generated_utc clock stamp")
    for key in ("db", "accounts", "tx_count", "entry_count", "issued",
                "reconcile_rc", "rejected"):
        if key not in doc:
            raise ValueError("landed report carries no %s field" % key)
    # The producer put the shipped ledger package on sys.path when it was
    # imported, so this is the same module object its seed_demo imports.
    import ledger
    import reconcile

    db_path = os.path.join(workdir, "demo.db")
    config = module.load_config()
    original_now = ledger.now_utc
    ledger.now_utc = lambda: stamp.replace(" ", "T")
    try:
        _steps, rejected, disclaimer, rows = module.seed_demo(db_path, config)
    finally:
        ledger.now_utc = original_now

    buf = io.StringIO()
    cfg_path = os.path.join(REPO, "src", "sandbox", "ledger", "config.json")
    with contextlib.redirect_stdout(buf):
        rc = reconcile.main(["reconcile.py", db_path, cfg_path])

    issued = 0
    for tx in rows["tx"]:
        if tx["type"] == "mint":
            issued += sum(int(en["amount"]) for en in rows["entries"]
                          if en["tx_id"] == tx["tx_id"] and en["direction"] == "debit")
    if not issued:
        issued = sum(int(r["balance"]) for r in rows["accounts"]
                     if module.account_class(r["account_id"]) == "pool")

    ctx = {
        "now": stamp,
        "db": doc["db"],
        "issued": issued,
        "rejected": rejected,
        "disclaimer": module.disclaimer_text(disclaimer),
        "rows": rows,
        "rc": rc,
        "recon": buf.getvalue().rstrip(),
        "cmd": "python tools/ledger_business_report.py",
    }
    body = module.build_html(ctx).encode("utf-8")

    payload = {
        "generated_utc": stamp,
        "db": doc["db"],
        "accounts": rows["accounts"],
        "tx_count": len(rows["tx"]),
        "entry_count": len(rows["entries"]),
        "issued": issued,
        "reconcile_rc": rc,
        "rejected": [{"case": c, "code": k, "detail": d, "blocked": b}
                     for c, k, d, b in rejected],
        "report": doc.get("report") or ("preview/%s.html" % face["slug"]),
        "sources": module.source_fingerprints(),
    }
    html_path = os.path.join(workdir, "rendered.html")
    json_path = os.path.join(workdir, "rendered.json")
    with io.open(html_path, "wb") as handle:
        handle.write(body)
    # The producer's own fixed point: only the json's byte count is
    # self-referential, so it is iterated until the recorded number is the
    # number on disk. The html size recorded here is the pre-channel page.
    for _ in range(6):
        payload["sizes"] = {
            "html": os.path.getsize(html_path),
            "json": os.path.getsize(json_path) if os.path.exists(json_path) else 0,
        }
        raw = (json.dumps(payload, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
        with io.open(json_path, "wb") as handle:
            handle.write(raw)
        if payload["sizes"]["json"] == os.path.getsize(json_path):
            break
    else:
        raise ValueError("document sizes did not converge")

    # The landed report is checked out with CRLF on this working tree while the
    # producer writes LF; the replay adopts the landed newline so the two
    # reports are comparable byte for byte, and the choice is recorded on the row.
    if b"\r\n" in landed_json_bytes:
        raw = read_bytes(json_path).replace(b"\n", b"\r\n")
        with io.open(json_path, "wb") as handle:
            handle.write(raw)

    injected, _how = face_backhop.inject_text(body.decode("utf-8"),
                                              face["slug"] + ".html")
    with io.open(html_path, "wb") as handle:
        handle.write(injected.encode("utf-8"))
    face_backhop.patch_sizes(html_path)
    return body, read_bytes(json_path)


def clock_pin_replay(face, module, doc, landed_json_bytes, landed_html_bytes, workdir):
    """AC-PPR14: replay a two-clock producer from the second its report records.

    payment_gate_report reads the wall clock in two packages: it stamps its own
    generated_utc, and its stale-timestamp negative cases are refused by the
    shipped payment sandbox, whose verify() compares the payload timestamp with
    its own wall clock. A replay that pins only the producer reproduces every
    world fact and still prints delta=867202s where the landed report says
    400s - the second clock is load-bearing, and the first attempt proved it.
    Both sources are therefore pinned to the second the landed report carries,
    and the producer's own main() runs into a scratch directory.

    What this buys is stated narrowly: the page half is the producer's render of
    the world it measures today, under the landed clock. No real gateway is
    re-measured. The report's self-stamps - its two byte sizes and the sha256 of
    the producer source itself - are recorded on the row, never equalised: they
    witness the moment of writing, not the derivation, and the landed json
    predates the channel that later rewrote its page.
    """
    import datetime

    stamp = doc.get("generated_utc")
    if not isinstance(stamp, str) or not stamp.endswith("Z"):
        raise ValueError("landed report carries no generated_utc clock stamp")
    pin = datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)
    pay_dir = os.path.join(REPO, "src", "sandbox", "pay")
    if pay_dir not in sys.path:
        sys.path.insert(0, pay_dir)
    import adapters

    original_now = module._now
    original_sandbox_now = adapters.now_utc
    out = os.path.join(workdir, "rendered.html")
    jout = os.path.join(workdir, "rendered.json")
    module._now = lambda: pin
    adapters.now_utc = lambda: pin
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            module.main(["--out", out, "--json", jout])
    finally:
        module._now = original_now
        adapters.now_utc = original_sandbox_now
    return read_bytes(out), read_bytes(jout)


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
    landed_json_bytes = read_bytes(landed_json_path)
    try:
        try:
            if face.get("replay"):
                # AC-PPR9 / AC-PPR10 / AC-PPR11 / AC-PPR13: the pair is replayed
                # from the landed report, and the label names which replay shape
                # read it.
                label = "%s-from-report" % face["replay"]["function"]
                if face["replay"].get("kind") == "landed-document":
                    label = "%s-from-landed-document" % face["replay"]["function"]
                if face["replay"].get("kind") == "clock-identity":
                    label = "%s-from-report-clock-pin" % face["replay"]["function"]
                if face["replay"].get("kind") == "clock-pin":
                    label = "%s-from-report-two-clock-pin" % face["replay"]["function"]
                if face["replay"].get("kind") == "facts-spread-report":
                    label = "%s-from-report-facts-spread" % face["replay"]["function"]
                row["replay"] = label
                if face["replay"].get("kind") == "facts-spread-report":
                    row["replay_stamps"] = [
                        "hub_url (read back off the landed page at the reported hub port)",
                        "facts from landed top-level keys: "
                        + ",".join(sorted(face["replay"]["facts_from"])),
                    ]
                if face["replay"].get("kind") == "facts-report":
                    used = ["generated_utc"] + list(face["replay"].get("stamp_keys") or [])
                    if face["replay"].get("port", True):
                        used.append("port")
                    row["replay_stamps"] = used
                if face["replay"].get("kind") == "clock-identity":
                    # The pin is not a promise: the row names the exact second
                    # the replay held the ledger clock at.
                    try:
                        pin = json.loads(landed_json_bytes.decode("utf-8")).get("generated_utc")
                    except Exception:
                        pin = None
                    row["replay_stamps"] = ["generated_utc=%s (clock pin)" % pin]
                if face["replay"].get("kind") == "clock-pin":
                    # AC-PPR14: two clocks, one second. The self-stamps are
                    # recorded beside the pin because they differ by design.
                    try:
                        landed_doc = json.loads(landed_json_bytes.decode("utf-8"))
                        pin = landed_doc.get("generated_utc")
                        row["replay_stamps"] = [
                            "generated_utc=%s (producer clock and payment sandbox clock)" % pin]
                        row["self_stamps"] = {
                            "landed": {"sizes": landed_doc.get("sizes"),
                                       "source_sha256": (landed_doc.get("source") or {}).get("sha256")},
                        }
                    except Exception:
                        pin = None
                        row["replay_stamps"] = ["generated_utc pin unavailable"]
                rendered, rendered_json = replay_render(
                    face, work, landed_json_bytes,
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
    if (face.get("replay") or {}).get("kind") == "clock-pin":
        # AC-PPR14: name the two self-stamps instead of letting a size mismatch
        # read as a lost derivation. The landed json is a pre-channel render, so
        # its recorded html size is its own moment's, not the shipped page's.
        try:
            now_doc = json.loads(rendered_json.decode("utf-8"))
            row.setdefault("self_stamps", {})["rendered"] = {
                "sizes": now_doc.get("sizes"),
                "source_sha256": (now_doc.get("source") or {}).get("sha256"),
            }
        except Exception:
            pass
    if (face.get("replay") or {}).get("kind") == "facts-spread-report":
        # AC-PPR15: the fingerprint is the run's identity (it pins what the run
        # proved, never the ephemeral ports), so the row records whether the
        # replay reproduced it instead of leaving that to prose.
        try:
            row["fingerprint_same"] = (
                json.loads(rendered_json.decode("utf-8")).get("fingerprint")
                == json.loads(landed_json_bytes.decode("utf-8")).get("fingerprint"))
        except Exception:
            row["fingerprint_same"] = False

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
        # R3514: a version-drift row may carry a replay of the producer as it
        # stood at the commit that wrote the pair. The replay itself is run by
        # the window (AC-PPR4 forbids this tool a child process), so what is
        # re-checked here is the part that can be: the landed pair must still
        # hash to the digests that replay recorded, which detects the page being
        # edited after the evidence was taken.
        hist = face.get("historical")
        if hist:
            now = {"landed_html_sha256_12_now": sha256_hex(landed)[:12],
                   "landed_json_sha256_12_now": sha256_hex(landed_json_bytes)[:12]}
            row["historical"] = dict(hist)
            row["historical"].update(now)
            agree = landed_digest_agrees(hist, landed, landed_json_bytes)
            row["historical"]["landed_digests_agree"] = agree
            if not agree:
                row["verdict"] = "drift"
                row["detail"] = ("the landed pair no longer hashes to what the historical "
                                 "replay at %s recorded, so the page was edited after that "
                                 "evidence was taken" % hist["commit"])
            else:
                row["detail"] += ("; and the pair IS reproduced by the producer as it stood "
                                  "at %s (html %d B + the channel block = %d B, json %d B "
                                  "identical), so the split is producer evolution, not editing"
                                  % (hist["commit"], hist["rendered_html_bytes"],
                                     hist["landed_html_bytes"],
                                     hist["rendered_json_bytes"]))
    else:
        row["verdict"] = "drift"
        row["detail"] = ("landed html is not the producer html plus the channel block: "
                         "first difference at byte %d" % at)
    return row


def landed_digest_agrees(hist, landed_html, landed_json):
    """R3514: the re-checkable half of a historical-producer replay.

    A replay of the producer AS IT STOOD at the commit that wrote a pair cannot
    run inside this tool (AC-PPR4 bans a child process, and reaching an old tree
    needs git), so the window runs it and records the digests. What the tool can
    re-check is that the landed pair still hashes to those digests: that is what
    detects a page being edited after the evidence was taken. A record without a
    commit is refused rather than trusted.
    """
    if not hist or not hist.get("commit"):
        return None
    return (sha256_hex(landed_html)[:12] == hist.get("landed_html_sha256_12")
            and sha256_hex(landed_json)[:12] == hist.get("landed_json_sha256_12"))


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
