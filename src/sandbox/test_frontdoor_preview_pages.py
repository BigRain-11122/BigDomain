"""Suite for the door's deliverable shelf: the shipped pages get one URL.

TWO criteria. AC-FDPV1 (six arms) pins the shelf itself: the pages come back
byte-identical to disk and no path can turn the door into a filesystem
reader. AC-FDPV2 (six arms, R3462) pins the door's manners: HEAD answers the
same status, type and length as GET with an empty body (a standard probe must
not see 501), and no answer on this door may be cached (a face rebuilt under
the same URL is otherwise a stale face).

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


def head(port, path):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        conn.request("HEAD", path)
        resp = conn.getresponse()
        return resp.status, resp.getheader("Content-Type", "") or "", \
            resp.getheader("Content-Length", "") or "", resp.read()
    finally:
        conn.close()


def cache_control(port, path):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        conn.request("GET", path)
        resp = conn.getresponse()
        value = resp.getheader("Cache-Control", "") or ""
        resp.read()
        return value
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

        # ===== AC-FDPV2: HEAD is a real probe and no face is cached ======
        # R3462 measured before the code: HEAD answered 501 on every path
        # (BaseHTTPRequestHandler default), so a link checker, a CDN warmer or
        # `curl -I` saw a broken door while GET answered 200; and the preview
        # answers carried no Cache-Control at all, so a rebuilt face stayed
        # stale in the browser under the same URL.
        bad2 = []

        # ---- a: HEAD mirrors GET on the named faces, with no body ---------
        for path in ("/", "/healthz", "/preview/index.html",
                     "/preview/library-board.html",
                     "/preview/face-sweep.html"):
            g_status, g_type, g_body = get(port, path)
            h_status, h_type, h_length, h_body = head(port, path)
            if h_status != g_status:
                bad2.append("a-status-%s-%d" % (path, h_status))
            if h_type != g_type:
                bad2.append("a-ctype-%s" % path)
            if h_length != str(len(g_body)):
                bad2.append("a-length-%s" % path)
            if h_body != b"":
                bad2.append("a-body-%s" % path)

        # ---- b: HEAD refuses what GET refuses -----------------------------
        for path in ("/nope", "/preview/nope.html"):
            status, _t, _l, body = head(port, path)
            if status != 404 or body != b"":
                bad2.append("b-miss-%s-%d" % (path, status))

        # ---- c: nothing on this door may be cached -------------------------
        for path in ("/", "/healthz", "/preview/index.html",
                     "/preview/library-board.html"):
            if cache_control(port, path) != "no-store":
                bad2.append("c-cache-%s" % path)

        # ---- d: HEAD is not a way around the shelf guard -------------------
        for path in ("/preview/../src/os/state.json",
                     "/preview/%2e%2e/src/os/state.json",
                     "/preview/%5c..%5csrc%5cos%5cstate.json",
                     "/preview/frontdoor.py",
                     "/preview/C:/Windows/win.ini"):
            status, _t, _l, _b = head(port, path)
            if status != 404:
                bad2.append("d-escape-%s-%d" % (path, status))

        # ---- e: one routing table, one HEAD handler -----------------------
        with io.open(MODULE, "rb") as handle:
            raw2 = handle.read()
        if raw2[:3] == b"\xef\xbb\xbf":
            bad2.append("e-module-bom")
        if b"\r\n" in raw2:
            bad2.append("e-module-crlf")
        try:
            raw2.decode("utf-8").encode("ascii")
            text2 = raw2.decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad2.append("e-module-not-ascii")
            text2 = raw2.decode("utf-8", "replace")
        if text2.count("def do_HEAD(") != 1:
            bad2.append("e-head-count-%d" % text2.count("def do_HEAD("))
        if "def _route(" not in text2:
            bad2.append("e-route-table-missing")
        if 'self.send_header("Cache-Control", "no-store")' not in text2:
            bad2.append("e-no-store-missing")

        # ---- f: the suite declares both criteria exactly once --------------
        with io.open(REGISTRY, encoding="utf-8") as handle:
            registry_text = handle.read()
        if registry_text.count('"' + ROW + '"') != 1:
            bad2.append("f-registry-rows")
        if ('"' + ROW + '"') in registry_text:
            block = registry_text.split('"' + ROW + '"', 1)[1][:160]
            if "test_frontdoor_preview_pages.py" not in block:
                bad2.append("f-row-file")
            if "2)" not in block:
                bad2.append("f-declared-%s" % block.split(")")[0].strip()[-3:])
    finally:
        srv.shutdown()
        srv.server_close()

    report("AC-FDPV1", bool(bad), ",".join(bad))
    report("AC-FDPV2", bool(bad2), ",".join(bad2))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
