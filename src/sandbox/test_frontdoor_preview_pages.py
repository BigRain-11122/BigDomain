"""Suite for the door's deliverable shelf: the shipped pages get one URL.

ONE criterion AC-FDPV1 with six arms, pinned in src/os/backlog.md in the
round that lands this file (honest disclosure: the PIN row and the code
landed in the same window; the six arms below were fixed before the driver
was edited and the implementation was not allowed to move them).

Measured before the code: the door answered exactly two paths ("/" and
"/healthz") and every one of the 103 shipped preview/*.html faces answered
404, so the "one openable URL" door could not reach a single deliverable
page. The shelf is now served from the same door, and this suite proves
both halves: the pages come back byte-identical to disk, and no path can
turn the door into a filesystem reader.

Usage: python test_frontdoor_preview_pages.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import http.client
import io
import os
import sys
import threading
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MODULE = os.path.join(HERE, "frontdoor.py")
PREVIEW = os.path.join(REPO, "preview")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
ROW = "frontdoor-preview-pages"

sys.path.insert(0, HERE)
import frontdoor  # noqa: E402  (the page module, import-time journey)

RESULTS = []


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def get(port, path):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        conn.request("GET", path)
        resp = conn.getresponse()
        return resp.status, resp.getheader("Content-Type", "") or "", \
            resp.read()
    finally:
        conn.close()


def serve():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), frontdoor.Handler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    return srv, srv.server_address[1]


def main():
    bad = []
    srv, port = serve()
    try:
        # ---- a: the two named faces come back byte-identical to disk ------
        for name in ("index.html", "library-board.html",
                     "face-sweep.html"):
            disk = os.path.join(PREVIEW, name)
            if not os.path.isfile(disk):
                bad.append("a-disk-missing-" + name)
                continue
            status, ctype, body = get(port, "/preview/" + name)
            if status != 200:
                bad.append("a-status-%s-%d" % (name, status))
                continue
            if "text/html" not in ctype:
                bad.append("a-ctype-" + name)
            with io.open(disk, "rb") as handle:
                if handle.read() != body:
                    bad.append("a-bytes-" + name)
        # the bare directory is the index, not a 404
        status, _ctype, body = get(port, "/preview/")
        if status != 200:
            bad.append("a-bare-dir-%d" % status)
        else:
            with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
                if handle.read() != body:
                    bad.append("a-bare-dir-bytes")

        # ---- b: no path escapes the shelf ---------------------------------
        for path in ("/preview/../src/os/state.json",
                     "/preview/%2e%2e/src/os/state.json",
                     "/preview/..%2f..%2fsrc%2fos%2fstate.json",
                     "/preview/frontdoor.py",
                     "/preview/does-not-exist.html",
                     "/preview/.env",
                     "/preview/C:/Windows/win.ini",
                     "/preview/sub/dir.html",
                     "/preview/%5c..%5csrc%5cos%5cstate.json"):
            status, _ctype, _body = get(port, path)
            if status != 404:
                bad.append("b-escaped-%s-%d" % (path, status))

        # ---- c: the root page names the shelf ------------------------------
        page = frontdoor.render().decode("utf-8")
        if 'href="/preview/index.html"' not in page:
            bad.append("c-root-link-missing")
        if 'href="/preview/face-sweep.html"' not in page:
            bad.append("c-root-sweep-link-missing")

        # ---- d: the existing two paths did not move -----------------------
        status, ctype, body = get(port, "/healthz")
        if status != 200 or body != b"ok" or "text/plain" not in ctype:
            bad.append("d-healthz")
        status, _ctype, _body = get(port, "/")
        if status != 200:
            bad.append("d-root-status-%d" % status)
        status, _ctype, _body = get(port, "/nope")
        if status != 404:
            bad.append("d-unknown-not-404")

        # ---- e: the module stays pure ASCII and the shelf is wired --------
        with io.open(MODULE, "rb") as handle:
            raw = handle.read()
        if raw[:3] == b"\xef\xbb\xbf":
            bad.append("e-module-bom")
        if b"\r\n" in raw:
            bad.append("e-module-crlf")
        try:
            text = raw.decode("utf-8")
            text.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad.append("e-module-not-ascii")
            text = raw.decode("utf-8", "replace")
        if "def _serve_preview(" not in text:
            bad.append("e-serve-missing")
        if "STATIC_EXTS = {" not in text:
            bad.append("e-exts-missing")
        if 'self.path.startswith("/preview/")' not in text:
            bad.append("e-route-missing")
        if '".py"' in text.split("STATIC_EXTS = {", 1)[-1].split("}", 1)[0]:
            bad.append("e-python-served")

        # ---- f: the suite is registered exactly once -----------------------
        with io.open(REGISTRY, encoding="utf-8") as handle:
            rows = handle.read().count('"' + ROW + '"')
        if rows != 1:
            bad.append("f-registry-rows-%d" % rows)
    finally:
        srv.shutdown()
        srv.server_close()

    report("AC-FDPV1", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
