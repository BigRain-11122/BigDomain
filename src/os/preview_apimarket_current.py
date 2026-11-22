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

import io
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


def render(out_html, out_json):
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
        R.main(["--db", db, "--out", out_html, "--json-out", out_json])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def expected_page():
    """The page this tree would produce now: render + back-hop injection."""
    tmp = tempfile.mkdtemp(prefix="apimarket-current-face-probe-")
    try:
        out_html = os.path.join(tmp, FACE)
        out_json = os.path.join(tmp, "apimarket-report.json")
        render(out_html, out_json)
        with io.open(out_html, "r", encoding="utf-8", newline="") as fh:
            text = fh.read()
        text, how = B.inject_text(text, FACE)
        return text, how
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    dry = "--dry-run" in argv
    if dry:
        text, how = expected_page()
        print("DRY %s %s bytes=%d (nothing written)"
              % (FACE, how, len(text.encode("utf-8"))))
        return 0
    render(HTML, JSON)
    with io.open(HTML, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    text, how = B.inject_text(text, FACE)
    with io.open(HTML, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    patched = B.patch_sizes(HTML)
    print("PASS preview %s (%d bytes, %s, sizes_patched=%s) + %s (%d bytes)"
          % (FACE, os.path.getsize(HTML), how, patched,
             os.path.basename(JSON), os.path.getsize(JSON)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
