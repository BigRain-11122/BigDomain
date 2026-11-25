"""R3292 producer: render the API-market current-reading face reproducibly.

Why this file exists: R3288 measured that 32 read-only faces carried no
visible way back and fixed it by injecting a block after the fact; R3289
measured that thirteen apimarket snapshots have no producer at all. The
fourteenth, preview/apimarket-report.html, DID have a generator
(src/sandbox/ledger/apimarket_report.py) but no on-disk recipe, so nobody
could say which world it came from. R3292 probed it read-only and found
that a fresh seed_demo render plus the R3288 back-hop injection reproduces
it byte for byte, so the recipe is now a file instead of a memory.

Order matters, and this is the fixed point the criteria imply:
  1. render html + json from one deterministic demo world (seed_demo);
  2. inject the back-hop block into the html (a post-render product, not a
     renderer output - saying otherwise would be a lie);
  3. re-measure the sibling sizes block against the bytes now on disk.

Both artifacts are written with bare LF: the recorded sizes are byte counts,
so a host that rewrites line endings would make them wrong. .gitattributes
pins the two paths for the same reason.

Usage:
    python src/os/preview_R3292.py            # write both artifacts
    python src/os/preview_R3292.py --dry-run  # render + report, write nothing
"""

import datetime
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LEDGER = os.path.join(BASE, "src", "sandbox", "ledger")
LOBBY = os.path.join(BASE, "src", "sandbox", "lobby")
TOOLS = os.path.join(BASE, "tools")
for path in (LEDGER, LOBBY, TOOLS):
    if path not in sys.path:
        sys.path.insert(0, path)

import apimarket_report as R  # noqa: E402
import face_backhop as B      # noqa: E402

FACE = "apimarket-report.html"
HTML = os.path.join(BASE, "preview", FACE)
JSON = os.path.join(BASE, "preview", "apimarket-report.json")

# R3293: the three sources whose bytes decide what this page says. The pair
# records their sha256 at render time, so the checker can name "the gate moved
# after the render" instead of letting an untouched page pass forever.
SOURCES = {
    "generator": os.path.join(LEDGER, "apimarket_report.py"),
    "injector": os.path.join(TOOLS, "face_backhop.py"),
    "producer": os.path.join(BASE, "src", "os", "preview_apimarket_current.py"),
}


def local_day():
    return datetime.date.today().isoformat()


# R3294: the day the render stamp shipped. This is the ONE definition - the
# checker (tools/apimarket_current_face.py, AC-ACF10/11) reads this value
# instead of keeping a copy, so "a page cannot claim to predate the feature"
# is stated once and enforced at both ends: the producer refuses such a stamp
# at birth, and the checker would still name an older page.
STAMP_FLOOR = "2026-11-22"

STAMP_FORMAT = "E_STAMP_FORMAT"
STAMP_EARLY = "E_STAMP_FLOOR"
STAMP_FUTURE = "E_STAMP_FUTURE"


def stamp_refusal(stamp, today=None):
    """(code, line) when this stamp may not be written, else None.

    A stamp is a claim about when the page was rendered, so a date this tree
    could not have produced - before the feature existed, or after today - is
    refused here, before anything is rendered. R3293 measured that the only
    gate was `fromisoformat`, so both out-of-range dates landed and only the
    sweep's AC-ACF10 reddened them afterwards. The sweep stays as the second
    line of defence; this is the birth site.

    `today` is a parameter for measurement only: a law that answers
    differently depending on the wall clock could not be tested.
    """
    try:
        datetime.date.fromisoformat(stamp)
    except (TypeError, ValueError):
        return (STAMP_FORMAT,
                "--stamp must be a calendar day YYYY-MM-DD, got %r"
                % (stamp,))
    if stamp < STAMP_FLOOR:
        return (STAMP_EARLY, "--stamp %s predates the stamp floor %s"
                % (stamp, STAMP_FLOOR))
    today = local_day() if today is None else today
    if stamp > today:
        return (STAMP_FUTURE, "--stamp %s is later than the machine local"
                " day %s" % (stamp, today))
    return None


def provenance():
    out = {}
    for key in sorted(SOURCES):
        with io.open(SOURCES[key], "rb") as fh:
            out[key] = hashlib.sha256(fh.read()).hexdigest()
    return out


def render(out_html, out_json, stamp):
    """Render the report from a fresh deterministic demo world."""
    tmp = tempfile.mkdtemp(prefix="apimarket-current-face-")
    try:
        db = os.path.join(tmp, "ledger.db")
        led, mtr, dk, am = R.build_stack(db)
        try:
            R.seed_demo(am, led, dk)
        finally:
            am.close()
            dk.close()
            mtr.close()
            led.close()
        R.main(["--db", db, "--out", out_html, "--json-out", out_json,
                "--rendered-on", stamp])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def expected_page(stamp=None):
    """The page this tree would produce now: render + back-hop injection."""
    tmp = tempfile.mkdtemp(prefix="apimarket-current-face-probe-")
    try:
        out_html = os.path.join(tmp, FACE)
        out_json = os.path.join(tmp, "apimarket-report.json")
        render(out_html, out_json, stamp or local_day())
        with io.open(out_html, "r", encoding="utf-8", newline="") as fh:
            text = fh.read()
        text, how = B.inject_text(text, FACE)
        return text, how
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def record_provenance(path, stamp):
    """Add the date and the source fingerprints to the sibling json.

    Written through the generator's own serializer and then re-fixed by
    face_backhop.patch_sizes, so the recorded byte counts still equal the
    files on disk after this append.
    """
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        doc = json.load(fh)
    doc["rendered_on"] = stamp
    doc["source_sha256"] = provenance()
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(R.dump_payload(doc))


def _render_pair_to(directory, stamp):
    """Reproduce the write path inside `directory` and return its two files.

    R3461: `--check` used to fall through to the write path, so a caller
    asking the producer to prove the page was current got that page silently
    rewritten (measured: deliverable_index --check moved both artifacts, which
    then reddened face_sweep AC-FSW10 as stale). The whole chain -- render,
    back-hop injection, provenance, size fixpoint -- now runs on a throwaway
    directory, so the proof never touches the tree it judges.
    """
    out_html = os.path.join(directory, FACE)
    out_json = os.path.join(directory, "apimarket-report.json")
    render(out_html, out_json, stamp)
    with io.open(out_html, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    text, how = B.inject_text(text, FACE)
    with io.open(out_html, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    record_provenance(out_json, stamp)
    B.patch_sizes(out_html)
    return out_html, out_json, how


def _check_only(stamp):
    """Prove the landed pair is what this tree renders now, writing nothing."""
    try:
        with io.open(JSON, encoding="utf-8") as fh:
            landed = json.load(fh)
        landed_stamp = landed.get("rendered_on") or stamp
    except (IOError, OSError, ValueError):
        landed_stamp = stamp
    tmp = tempfile.mkdtemp(prefix="apimarket-current-check-")
    try:
        out_html, out_json, how = _render_pair_to(tmp, landed_stamp)
        problems = []
        for live, mine in ((HTML, out_html), (JSON, out_json)):
            with io.open(live, "rb") as fh:
                have = fh.read()
            with io.open(mine, "rb") as fh:
                want = fh.read()
            if have != want:
                problems.append("%s disk=%dB expected=%dB"
                                % (os.path.basename(live), len(have),
                                   len(want)))
        if problems:
            print("FAIL E_APIMKT_STALE %s" % FACE)
            for problem in problems:
                print("  %s" % problem)
            return 2
        print("PASS %s check disk=expected bytes=%dB how=%s (nothing written)"
              % (FACE, os.path.getsize(HTML), how))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    dry = "--dry-run" in argv
    check = "--check" in argv
    stamp = local_day()
    for i, token in enumerate(argv):
        if token == "--stamp" and i + 1 < len(argv):
            stamp = argv[i + 1]
        elif token.startswith("--stamp="):
            stamp = token.split("=", 1)[1]
    refusal = stamp_refusal(stamp)
    if refusal is not None:
        # R3294: refused before --dry-run answers too, because a dry run that
        # prints a page the write path would refuse is a promise nobody keeps.
        print("%s %s" % refusal)
        return 2
    if dry:
        text, how = expected_page(stamp)
        print("DRY %s %s bytes=%d stamp=%s (nothing written)"
              % (FACE, how, len(text.encode("utf-8")), stamp))
        return 0
    if check:
        return _check_only(stamp)
    render(HTML, JSON, stamp)
    with io.open(HTML, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    text, how = B.inject_text(text, FACE)
    with io.open(HTML, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    record_provenance(JSON, stamp)
    patched = B.patch_sizes(HTML)
    print("PASS preview %s (%d bytes, %s, sizes_patched=%s, stamp=%s)"
          " + %s (%d bytes)"
          % (FACE, os.path.getsize(HTML), how, patched, stamp,
             os.path.basename(JSON), os.path.getsize(JSON)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
