"""Suite for the door's deliverable shelf: the shipped pages get one URL.

EIGHT criteria. AC-FDPV1 (six arms) pins the shelf itself: the pages come back
byte-identical to disk and no path can turn the door into a filesystem
reader. AC-FDPV2 (six arms, R3462) pins the door's manners: HEAD answers the
same status, type and length as GET with an empty body (a standard probe must
not see 501), and no answer on this door may be cached (a face rebuilt under
the same URL is otherwise a stale face). AC-FDPV3 (six arms, R3463) pins the
shelf's resumability: one byte range answers 206 with exactly that slice, a
range past the last byte answers 416 carrying the total, a malformed range is
ignored rather than 500, and eight concurrent readers all get the same bytes.
AC-FDPV4 (six arms, R3464) pins the shelf's conditionals: every 200 carries a
strong content ETag and a Last-Modified, If-None-Match and If-Modified-Since
answer 304 with no body, and an If-Range that no longer matches answers the
whole face instead of splicing a new version onto an old prefix.
AC-FDPV5 (six arms, R3465) pins the shelf's negotiation: an Accept-Encoding
that names gzip gets a gzip representation that decompresses to the disk
bytes, identity stays byte-identical, and every answer says it varies with
Accept-Encoding. AC-FDPV6 (six arms, R3465) pins the write preconditions:
If-Match and If-Unmodified-Since answer 412 when the reader's copy is not
current, in the RFC 7232 sec.6 order, without bypassing the shelf guard.
AC-FDPV7 (six arms, R3466) pins the shelf's policy: every answer on every verb
names nosniff and no-referrer, an HTML face carries a policy that allows
exactly what the shipped pages use (inline style, inline script, same-origin
images) and closes everything else, a non-HTML face gets the tightest policy,
and none of the headers changes a status, a type, a byte or a body.
AC-FDPV8 (six arms, R3467) pins the shelf's reach: every answer names who may
read it (Cross-Origin-Resource-Policy same-origin) and which capabilities are
refused (Permissions-Policy), a document also names its opener policy while a
json face does not claim to be one, no shipped page uses a refused capability,
and the Server header names the door instead of the interpreter version.

Usage: python test_frontdoor_preview_pages.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import email.utils
import gzip
import hashlib
import http.client
import io
import os
import re
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


def request(port, method, path, headers=None):
    """One request carrying its own headers; every reply field this suite
    grades comes back together so no arm can silently skip one."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        conn.request(method, path, headers=headers or {})
        resp = conn.getresponse()
        return (resp.status, resp.getheader("Content-Type", "") or "",
                resp.getheader("Content-Length", "") or "",
                resp.getheader("Content-Range", "") or "",
                resp.getheader("Accept-Ranges", "") or "", resp.read())
    finally:
        conn.close()


def cond(port, method, path, headers=None):
    """R3464: every conditional-request field, named so no arm skips one."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        conn.request(method, path, headers=headers or {})
        resp = conn.getresponse()
        return {"status": resp.status,
                "ctype": resp.getheader("Content-Type", "") or "",
                "length": resp.getheader("Content-Length", "") or "",
                "etag": resp.getheader("ETag", "") or "",
                "last_modified": resp.getheader("Last-Modified", "") or "",
                "crange": resp.getheader("Content-Range", "") or "",
                "ranges": resp.getheader("Accept-Ranges", "") or "",
                "cache": resp.getheader("Cache-Control", "") or "",
                "body": resp.read()}
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
            if "8)" not in block:
                bad2.append("f-declared-%s" % block.split(")")[0].strip()[-3:])

        # ===== AC-FDPV3: the shelf is resumable and concurrent ============
        # R3463 measured before the code: every answer was the whole body, so
        # Range was silently ignored (no Accept-Ranges, no 206, no 416) and a
        # 55KB face could be neither resumed nor fetched in slices; and
        # concurrency had never been pinned by any arm.
        bad3 = []
        json_name = "face-sweep.json"
        json_disk = os.path.join(PREVIEW, json_name)
        with io.open(json_disk, "rb") as handle:
            raw = handle.read()
        size = len(raw)
        path = "/preview/" + json_name

        # ---- a: without Range the whole face comes back, byte for byte ----
        status, ctype, length, crange, rngs, body = request(port, "GET", path)
        if status != 200:
            bad3.append("a-status-%d" % status)
        if "application/json" not in ctype:
            bad3.append("a-ctype")
        if rngs != "bytes":
            bad3.append("a-accept-ranges-%r" % rngs)
        if crange != "":
            bad3.append("a-crange-on-200-%r" % crange)
        if length != str(size):
            bad3.append("a-length-%s-vs-%d" % (length, size))
        if body != raw:
            bad3.append("a-bytes")

        # ---- b: a closed range answers 206 with exactly that slice --------
        status, _t, length, crange, _r, body = request(
            port, "GET", path, {"Range": "bytes=0-99"})
        if status != 206:
            bad3.append("b-status-%d" % status)
        if crange != "bytes 0-99/%d" % size:
            bad3.append("b-crange-%r" % crange)
        if length != "100":
            bad3.append("b-length-%s" % length)
        if body != raw[0:100]:
            bad3.append("b-bytes")

        # ---- c: suffix and open-ended ranges -----------------------------
        status, _t, _l, crange, _r, body = request(
            port, "GET", path, {"Range": "bytes=-50"})
        if status != 206 or crange != "bytes %d-%d/%d" % (
                size - 50, size - 1, size):
            bad3.append("c-suffix-%d-%r" % (status, crange))
        if body != raw[-50:]:
            bad3.append("c-suffix-bytes")
        status, _t, _l, crange, _r, body = request(
            port, "GET", path, {"Range": "bytes=100-"})
        if status != 206 or crange != "bytes 100-%d/%d" % (size - 1, size):
            bad3.append("c-open-%d-%r" % (status, crange))
        if body != raw[100:]:
            bad3.append("c-open-bytes")

        # ---- d: a range past the last byte is 416 carrying the total -----
        status, _t, _l, crange, _r, body = request(
            port, "GET", path, {"Range": "bytes=%d-" % size})
        if status != 416:
            bad3.append("d-status-%d" % status)
        if crange != "bytes */%d" % size:
            bad3.append("d-crange-%r" % crange)
        if body != b"":
            bad3.append("d-body")

        # ---- e: a malformed Range is ignored, never a 500 ----------------
        for header in ("bytes=abc", "items=0-9", "bytes=9-3", "bytes="):
            status, _t, _l, _c, _r, body = request(
                port, "GET", path, {"Range": header})
            if status != 200:
                bad3.append("e-%s-%d" % (header, status))
            elif body != raw:
                bad3.append("e-%s-bytes" % header)

        # ---- f: HEAD keeps the range contract and eight readers agree ----
        status, _t, length, crange, _r, body = request(
            port, "HEAD", path, {"Range": "bytes=0-9"})
        if status != 206 or length != "10" or body != b"" or \
                crange != "bytes 0-9/%d" % size:
            bad3.append("f-head-%d-%s-%r" % (status, length, crange))
        answers = []
        lock = threading.Lock()

        def read_once():
            try:
                reply = request(port, "GET", path)
            except Exception as exc:  # honest failure, never a silent pass
                reply = ("error", repr(exc))
            with lock:
                answers.append(reply)

        threads = [threading.Thread(target=read_once) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(60)
        if len(answers) != 8:
            bad3.append("f-concurrent-%d" % len(answers))
        for reply in answers:
            if not isinstance(reply, tuple) or reply[0] != 200:
                bad3.append("f-concurrent-status")
                break
            if reply[5] != raw or reply[2] != str(size):
                bad3.append("f-concurrent-bytes")
                break
        with io.open(MODULE, "rb") as handle:
            raw3 = handle.read()
        try:
            text3 = raw3.decode("utf-8")
            text3.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad3.append("f-module-not-ascii")
            text3 = raw3.decode("utf-8", "replace")
        if b"\r\n" in raw3 or raw3[:3] == b"\xef\xbb\xbf":
            bad3.append("f-module-dialect")
        if "def _parse_range(" not in text3:
            bad3.append("f-range-parser-missing")
        if text3.count("def do_HEAD(") != 1:
            bad3.append("f-head-count")
        # ===== AC-FDPV4: the shelf publishes a validator ===================
        # R3464 measured before the code: every answer was unconditional --
        # no ETag, no Last-Modified, If-None-Match and If-Modified-Since
        # ignored -- so a reader could not prove its copy was current, and a
        # resumer that spliced a new version's slice onto an old version's
        # prefix would build a file that exists nowhere.
        bad4 = []
        json_disk4 = os.path.join(PREVIEW, json_name)
        with io.open(json_disk4, "rb") as handle:
            raw4 = handle.read()
        size4 = len(raw4)
        path4 = "/preview/" + json_name
        etag4 = '"%s"' % hashlib.sha256(raw4).hexdigest()[:16]
        lm4 = email.utils.formatdate(os.path.getmtime(json_disk4), usegmt=True)

        # ---- a: every 200 names its entity ---------------------------------
        reply = cond(port, "GET", path4)
        if reply["etag"] != etag4:
            bad4.append("a-etag-%r" % reply["etag"])
        if reply["last_modified"] != lm4:
            bad4.append("a-last-modified-%r" % reply["last_modified"])
        if reply["cache"] != "no-store":
            bad4.append("a-cache")
        for in_memory in ("/", "/healthz"):
            reply = cond(port, "GET", in_memory)
            tag = reply["etag"]
            if not (tag.startswith('"') and tag.endswith('"')) or \
                    len(tag) != 18:
                bad4.append("a-tag-shape-%s-%r" % (in_memory, tag))

        # ---- b: If-None-Match answers 304 with no body ---------------------
        for header in (etag4, "W/" + etag4, "*"):
            reply = cond(port, "GET", path4, {"If-None-Match": header})
            if reply["status"] != 304:
                bad4.append("b-status-%s-%d" % (header, reply["status"]))
            if reply["body"] != b"":
                bad4.append("b-body-%s" % header)
            if reply["length"] != "0":
                bad4.append("b-length-%s" % header)
            if reply["etag"] != etag4:
                bad4.append("b-etag-%s" % header)
            if reply["cache"] != "no-store":
                bad4.append("b-cache-%s" % header)
        reply = cond(port, "GET", path4,
                     {"If-None-Match": '"0000000000000000"'})
        if reply["status"] != 200 or reply["body"] != raw4:
            bad4.append("b-stale-%d" % reply["status"])

        # ---- c: the slice carries the full representation's tag ------------
        reply = cond(port, "GET", path4, {"Range": "bytes=0-99"})
        if reply["status"] != 206 or reply["etag"] != etag4:
            bad4.append("c-tag-%d-%r" % (reply["status"], reply["etag"]))
        if reply["body"] != raw4[:100]:
            bad4.append("c-bytes")
        reply = cond(port, "GET", path4,
                     {"Range": "bytes=0-99", "If-Range": etag4})
        if reply["status"] != 206 or reply["body"] != raw4[:100]:
            bad4.append("c-match-%d" % reply["status"])
        if reply["crange"] != "bytes 0-99/%d" % size4:
            bad4.append("c-crange-%r" % reply["crange"])

        # ---- d: a validator that no longer matches serves the whole face ---
        for header in ('"0000000000000000"', "W/" + etag4,
                       "Wed, 21 Oct 2015 07:28:00 GMT"):
            reply = cond(port, "GET", path4,
                         {"Range": "bytes=0-99", "If-Range": header})
            if reply["status"] != 200:
                bad4.append("d-status-%s-%d" % (header, reply["status"]))
            if reply["body"] != raw4:
                bad4.append("d-body-%s" % header)
            if reply["crange"] != "":
                bad4.append("d-crange-%s" % header)
            if reply["ranges"] != "bytes":
                bad4.append("d-ranges-%s" % header)

        # ---- e: If-Modified-Since is a real condition ----------------------
        reply = cond(port, "GET", path4, {"If-Modified-Since": lm4})
        if reply["status"] != 304 or reply["body"] != b"":
            bad4.append("e-equal-%d" % reply["status"])
        reply = cond(port, "GET", path4,
                     {"If-Modified-Since":
                      email.utils.formatdate(0, usegmt=True)})
        if reply["status"] != 200 or reply["body"] != raw4:
            bad4.append("e-older-%d" % reply["status"])

        # ---- f: the module dialect and the declared count -------------------
        with io.open(MODULE, "rb") as handle:
            raw5 = handle.read()
        if raw5[:3] == b"\xef\xbb\xbf":
            bad4.append("f-module-bom")
        if b"\r\n" in raw5:
            bad4.append("f-module-crlf")
        try:
            text5 = raw5.decode("utf-8")
            text5.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad4.append("f-module-not-ascii")
            text5 = raw5.decode("utf-8", "replace")
        if text5.count("def do_HEAD(") != 1:
            bad4.append("f-head-count")
        for needle in ("def _etag(", "def _parse_http_date(",
                       "def _not_modified(", "def _if_range_ok("):
            if needle not in text5:
                bad4.append("f-missing-" + needle)
        with io.open(REGISTRY, encoding="utf-8") as handle:
            registry_text4 = handle.read()
        block4 = registry_text4.split('"' + ROW + '"', 1)[-1][:160]
        if "8)" not in block4:
            bad4.append("f-declared-%r" % block4.split(")")[0][-8:])

        # ===== AC-FDPV5: the shelf negotiates a coding ======================
        # R3465 measured before the code: every answer was the whole identity
        # body with no Content-Encoding and no Vary, so a browser or downloader
        # that named gzip still paid the full 55KB for index.html, and an
        # intermediate cache had no way to tell the two representations apart.
        bad5 = []
        page = "index.html"
        page_path = "/preview/" + page
        with io.open(os.path.join(PREVIEW, page), "rb") as handle:
            page_raw = handle.read()

        def neg(method, path, headers=None):
            """One request naming every negotiation field this suite grades."""
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
            try:
                conn.request(method, path, headers=headers or {})
                resp = conn.getresponse()
                return {"status": resp.status,
                        "ctype": resp.getheader("Content-Type", "") or "",
                        "length": resp.getheader("Content-Length", "") or "",
                        "encoding":
                            resp.getheader("Content-Encoding", "") or "",
                        "vary": resp.getheader("Vary", "") or "",
                        "etag": resp.getheader("ETag", "") or "",
                        "last_modified":
                            resp.getheader("Last-Modified", "") or "",
                        "crange": resp.getheader("Content-Range", "") or "",
                        "ranges": resp.getheader("Accept-Ranges", "") or "",
                        "body": resp.read()}
            finally:
                conn.close()

        # ---- a: a gzip request gets a gzip representation ------------------
        reply = neg("GET", page_path, {"Accept-Encoding": "gzip"})
        if reply["status"] != 200:
            bad5.append("a-status-%d" % reply["status"])
        if reply["encoding"] != "gzip":
            bad5.append("a-encoding-%r" % reply["encoding"])
        if "accept-encoding" not in reply["vary"].lower():
            bad5.append("a-vary-%r" % reply["vary"])
        try:
            plain = gzip.decompress(reply["body"])
        except Exception:
            plain = b""
            bad5.append("a-not-gzip")
        if plain != page_raw:
            bad5.append("a-bytes")
        gzip_tag = reply["etag"]

        # ---- b: identity is untouched and the two tags differ --------------
        reply = neg("GET", page_path)
        if reply["status"] != 200 or reply["body"] != page_raw:
            bad5.append("b-identity-%d" % reply["status"])
        if reply["encoding"]:
            bad5.append("b-encoding-%r" % reply["encoding"])
        if "accept-encoding" not in reply["vary"].lower():
            bad5.append("b-vary")
        ident_tag = reply["etag"]
        for tag in (gzip_tag, ident_tag):
            if not (tag.startswith('"') and tag.endswith('"')) or \
                    len(tag) != 18:
                bad5.append("b-tag-shape-%r" % tag)
        if gzip_tag == ident_tag:
            bad5.append("b-tag-collision")

        # ---- c: the negotiation lexicon ------------------------------------
        for header in ("gzip;q=0", "deflate", "identity"):
            reply = neg("GET", page_path, {"Accept-Encoding": header})
            if reply["encoding"]:
                bad5.append("c-identity-%s-%r" % (header, reply["encoding"]))
            if reply["body"] != page_raw:
                bad5.append("c-identity-bytes-%s" % header)
        for header in ("*", "GZIP", "gzip;q=0.5, identity;q=0"):
            reply = neg("GET", page_path, {"Accept-Encoding": header})
            if reply["encoding"] != "gzip":
                bad5.append("c-gzip-%s-%r" % (header, reply["encoding"]))

        # ---- d: HEAD mirrors the negotiated GET ----------------------------
        got = neg("GET", page_path, {"Accept-Encoding": "gzip"})
        said = neg("HEAD", page_path, {"Accept-Encoding": "gzip"})
        if said["status"] != got["status"]:
            bad5.append("d-status")
        if said["encoding"] != got["encoding"]:
            bad5.append("d-encoding")
        if said["length"] != got["length"]:
            bad5.append("d-length")
        if said["body"] != b"":
            bad5.append("d-body")

        # ---- e: a range always addresses the identity bytes ----------------
        reply = neg("GET", page_path,
                    {"Accept-Encoding": "gzip", "Range": "bytes=0-99"})
        if reply["status"] != 206:
            bad5.append("e-status-%d" % reply["status"])
        if reply["encoding"]:
            bad5.append("e-encoding-%r" % reply["encoding"])
        if reply["body"] != page_raw[:100]:
            bad5.append("e-bytes")
        if reply["etag"] != ident_tag:
            bad5.append("e-tag-%r" % reply["etag"])
        reply = neg("GET", page_path,
                    {"Accept-Encoding": "gzip", "Range": "bytes=0-99",
                     "If-Range": gzip_tag})
        if reply["status"] != 200 or reply["body"] != page_raw:
            bad5.append("e-cross-%d" % reply["status"])
        if reply["encoding"]:
            bad5.append("e-cross-encoding")

        # ---- f: the module dialect, the root face and the declared count ---
        with io.open(MODULE, "rb") as handle:
            raw6 = handle.read()
        if raw6[:3] == b"\xef\xbb\xbf":
            bad5.append("f-module-bom")
        if b"\r\n" in raw6:
            bad5.append("f-module-crlf")
        try:
            text6 = raw6.decode("utf-8")
            text6.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad5.append("f-module-not-ascii")
            text6 = raw6.decode("utf-8", "replace")
        if "import gzip" not in text6:
            bad5.append("f-gzip-import")
        if "def _accepts_gzip(" not in text6:
            bad5.append("f-gzip-parser")
        if 'self.send_header("Vary", "Accept-Encoding")' not in text6:
            bad5.append("f-vary-header")
        root = neg("GET", "/", {"Accept-Encoding": "gzip"})
        if root["status"] != 200 or root["encoding"] != "gzip":
            bad5.append("f-root-%d-%r" % (root["status"], root["encoding"]))
        elif b"/preview/index.html" not in gzip.decompress(root["body"]):
            bad5.append("f-root-bytes")
        with io.open(REGISTRY, encoding="utf-8") as handle:
            registry_text5 = handle.read()
        block5 = registry_text5.split('"' + ROW + '"', 1)[-1][:160]
        if "8)" not in block5:
            bad5.append("f-declared-%r" % block5.split(")")[0][-8:])

        # ===== AC-FDPV6: the shelf honours the write preconditions ==========
        # R3465 measured before the code: If-Match and If-Unmodified-Since
        # were dropped on the floor, so a reader could not say "answer only if
        # this is still the version I hold".
        bad6 = []
        lm6 = email.utils.formatdate(
            os.path.getmtime(os.path.join(PREVIEW, page)), usegmt=True)
        stale = '"0000000000000000"'

        # ---- a: If-Match compares strongly ---------------------------------
        for header in (ident_tag, "*"):
            reply = neg("GET", page_path, {"If-Match": header})
            if reply["status"] != 200 or reply["body"] != page_raw:
                bad6.append("a-match-%s-%d" % (header, reply["status"]))
        reply = neg("GET", page_path, {"If-Match": "W/" + ident_tag})
        if reply["status"] != 412:
            bad6.append("a-weak-%d" % reply["status"])

        # ---- b: a stale If-Match is refused with a small named body --------
        reply = neg("GET", page_path, {"If-Match": stale})
        if reply["status"] != 412:
            bad6.append("b-status-%d" % reply["status"])
        if len(reply["body"]) > 64:
            bad6.append("b-body-%d" % len(reply["body"]))
        if reply["etag"] != ident_tag:
            bad6.append("b-etag")
        if reply["last_modified"] != lm6:
            bad6.append("b-last-modified")
        if "accept-encoding" not in reply["vary"].lower():
            bad6.append("b-vary")

        # ---- c: If-Unmodified-Since is a real condition --------------------
        reply = neg("GET", page_path,
                    {"If-Unmodified-Since":
                     email.utils.formatdate(0, usegmt=True)})
        if reply["status"] != 412:
            bad6.append("c-old-%d" % reply["status"])
        for stamp in (lm6, email.utils.formatdate(4102444800, usegmt=True)):
            reply = neg("GET", page_path, {"If-Unmodified-Since": stamp})
            if reply["status"] != 200 or reply["body"] != page_raw:
                bad6.append("c-fresh-%d" % reply["status"])

        # ---- d: If-Match wins, and its absence lets the date speak ---------
        reply = neg("GET", page_path,
                    {"If-Match": ident_tag,
                     "If-Unmodified-Since":
                     email.utils.formatdate(0, usegmt=True)})
        if reply["status"] != 200 or reply["body"] != page_raw:
            bad6.append("d-match-wins-%d" % reply["status"])
        reply = neg("GET", page_path,
                    {"If-Match": stale,
                     "If-Unmodified-Since":
                     email.utils.formatdate(4102444800, usegmt=True)})
        if reply["status"] != 412:
            bad6.append("d-match-fails-%d" % reply["status"])

        # ---- e: 412 never bypasses the shelf guard -------------------------
        for path in ("/preview/../src/os/state.json", "/nope"):
            reply = neg("GET", path, {"If-Match": stale})
            if reply["status"] != 404:
                bad6.append("e-guard-%s-%d" % (path, reply["status"]))
        reply = neg("HEAD", page_path, {"If-Match": stale})
        if reply["status"] != 412 or reply["body"] != b"":
            bad6.append("e-head-%d" % reply["status"])

        # ---- f: the module dialect and the declared count ------------------
        if "def _precondition_failed(" not in text6:
            bad6.append("f-precondition")
        with io.open(MODULE, "rb") as handle:
            raw7 = handle.read()
        if raw7[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw7:
            bad6.append("f-module-dialect")
        with io.open(REGISTRY, encoding="utf-8") as handle:
            registry_text6 = handle.read()
        block6 = registry_text6.split('"' + ROW + '"', 1)[-1][:200]
        if "8)" not in block6:
            bad6.append("f-declared")
        if "test_frontdoor_preview_pages.py" not in block6:
            bad6.append("f-row-file")

        # ===== AC-FDPV7: the shelf publishes a policy ========================
        # R3466 measured before the code: no answer carried
        # X-Content-Type-Options, Referrer-Policy or Content-Security-Policy,
        # so a browser was free to sniff a json face as a script and any site
        # could frame this door.
        bad7 = []

        def sec(method, path, headers=None):
            """One request naming every policy field this suite grades."""
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
            try:
                conn.request(method, path, headers=headers or {})
                resp = conn.getresponse()
                return {"status": resp.status,
                        "ctype": resp.getheader("Content-Type", "") or "",
                        "nosniff":
                            resp.getheader("X-Content-Type-Options", "") or "",
                        "referrer": resp.getheader("Referrer-Policy", "") or "",
                        "csp": resp.getheader("Content-Security-Policy", "") or "",
                        "xfo": resp.getheader("X-Frame-Options", "") or "",
                        "etag": resp.getheader("ETag", "") or "",
                        "encoding":
                            resp.getheader("Content-Encoding", "") or "",
                        "body": resp.read()}
            finally:
                conn.close()

        ident7 = sec("GET", page_path)
        ident_tag7 = ident7["etag"]
        stale7 = '"0000000000000000"'
        json_name = sorted(name for name in os.listdir(PREVIEW)
                           if name.endswith(".json"))[0]

        # ---- a: every answer on every verb carries the two base headers ----
        probes = [("GET", "/"), ("HEAD", "/"), ("GET", "/healthz"),
                  ("HEAD", "/healthz"), ("GET", page_path),
                  ("HEAD", page_path), ("GET", "/preview/" + json_name),
                  ("GET", "/nope"), ("HEAD", "/nope"),
                  ("GET", page_path, {"Range": "bytes=0-9"}),
                  ("GET", "/nope", {"Range": "bytes=0-9"}),
                  ("GET", page_path, {"If-None-Match": ident_tag7}),
                  ("GET", page_path, {"If-Match": stale7})]
        for probe in probes:
            reply = sec(*probe)
            if reply["nosniff"] != "nosniff":
                bad7.append("a-nosniff-%s-%s" % (probe[0], probe[1]))
            if reply["referrer"] != "no-referrer":
                bad7.append("a-referrer-%s-%s" % (probe[0], probe[1]))

        # ---- b: an HTML face names what it allows and nothing else ---------
        for path in ("/", page_path):
            reply = sec("GET", path)
            if reply["status"] != 200:
                bad7.append("b-status-%s-%d" % (path, reply["status"]))
            policy = reply["csp"]
            for token in ("default-src 'none'", "script-src 'unsafe-inline'",
                          "style-src 'unsafe-inline'", "img-src 'self'",
                          "base-uri 'none'", "form-action 'none'",
                          "frame-ancestors 'none'"):
                if token not in policy:
                    bad7.append("b-token-%s-%s" % (path, token.split()[0]))
            if reply["xfo"] != "DENY":
                bad7.append("b-xfo-%s-%r" % (path, reply["xfo"]))

        # ---- c: a non-HTML face gets the tightest policy and its old type --
        reply = sec("GET", "/preview/" + json_name)
        if reply["ctype"] != "application/json; charset=utf-8":
            bad7.append("c-json-ctype-%r" % reply["ctype"])
        if "default-src 'none'" not in reply["csp"]:
            bad7.append("c-json-default")
        for token in ("script-src", "style-src", "img-src", "unsafe-inline"):
            if token in reply["csp"]:
                bad7.append("c-json-loose-%s" % token)
        reply = sec("GET", "/healthz")
        if reply["ctype"] != "text/plain" or reply["body"] != b"ok":
            bad7.append("c-healthz-%r-%r" % (reply["ctype"], reply["body"]))

        # ---- d: the policy covers what the shipped pages actually use ------
        pages = sorted(name for name in os.listdir(PREVIEW)
                       if name.endswith(".html"))
        inline_style = 0
        inline_script = 0
        same_origin_img = 0
        external = 0
        for name in pages:
            with io.open(os.path.join(PREVIEW, name), "rb") as handle:
                text = handle.read().decode("utf-8", "replace")
            if "<style" in text:
                inline_style += 1
            if re.search(r"<script(?![^>]*\bsrc=)", text):
                inline_script += 1
            if re.search(r"<img[^>]*\bsrc=['\"]live/", text):
                same_origin_img += 1
            if re.search(r"(?:src|href)=['\"]https?:", text):
                external += 1
        policy = sec("GET", page_path)["csp"]
        if inline_style and "style-src 'unsafe-inline'" not in policy:
            bad7.append("d-inline-style-%d" % inline_style)
        if inline_script and "script-src 'unsafe-inline'" not in policy:
            bad7.append("d-inline-script-%d" % inline_script)
        if same_origin_img and "img-src 'self'" not in policy:
            bad7.append("d-img-%d" % same_origin_img)
        if external:
            bad7.append("d-external-%d" % external)
        if len(pages) < 100:
            bad7.append("d-pages-%d" % len(pages))

        # ---- e: the new headers change no existing semantics ---------------
        reply = sec("GET", page_path, {"Accept-Encoding": "gzip"})
        try:
            plain7 = gzip.decompress(reply["body"])
        except Exception:
            plain7 = b""
            bad7.append("e-not-gzip")
        if plain7 != page_raw:
            bad7.append("e-gzip-bytes")
        reply = sec("GET", page_path, {"Range": "bytes=0-99"})
        if reply["status"] != 206 or reply["body"] != page_raw[:100]:
            bad7.append("e-range-%d" % reply["status"])
        reply = sec("GET", page_path, {"If-None-Match": ident_tag7})
        if reply["status"] != 304 or reply["body"] != b"":
            bad7.append("e-304-%d" % reply["status"])
        reply = sec("GET", page_path, {"If-Match": stale7})
        if reply["status"] != 412 or len(reply["body"]) > 64:
            bad7.append("e-412-%d" % reply["status"])

        # ---- f: the module dialect and the declared count ------------------
        with io.open(MODULE, "rb") as handle:
            raw8 = handle.read()
        if raw8[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw8:
            bad7.append("f-module-dialect")
        try:
            text8 = raw8.decode("utf-8")
            text8.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad7.append("f-module-not-ascii")
            text8 = raw8.decode("utf-8", "replace")
        for needle in ("SECURITY_HEADERS", "HTML_POLICY", "TEXT_POLICY",
                       "def _security_headers("):
            if needle not in text8:
                bad7.append("f-missing-" + needle)
        with io.open(REGISTRY, encoding="utf-8") as handle:
            registry_text7 = handle.read()
        block7 = registry_text7.split('"' + ROW + '"', 1)[-1][:200]
        if "8)" not in block7:
            bad7.append("f-declared")
        if "test_frontdoor_preview_pages.py" not in block7:
            bad7.append("f-row-file")

        # ===== AC-FDPV8: who may read the shelf and what it may do =========
        # R3467 measured before the code: no answer carried
        # Cross-Origin-Resource-Policy, Cross-Origin-Opener-Policy or
        # Permissions-Policy, so any origin could take a face as a subresource
        # and no capability was refused; the Server header handed out the
        # interpreter version. The capability list denies everything because
        # measurement found no shipped page using any of it.
        bad8 = []

        def reach(method, path, headers=None):
            """One request naming every reach field this suite grades."""
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
            try:
                conn.request(method, path, headers=headers or {})
                resp = conn.getresponse()
                return {"status": resp.status,
                        "server": resp.getheader("Server", "") or "",
                        "corp":
                            resp.getheader("Cross-Origin-Resource-Policy", "")
                            or "",
                        "coop":
                            resp.getheader("Cross-Origin-Opener-Policy", "")
                            or "",
                        "perms":
                            resp.getheader("Permissions-Policy", "") or "",
                        "etag": resp.getheader("ETag", "") or "",
                        "body": resp.read()}
            finally:
                conn.close()

        ident8 = reach("GET", page_path)
        ident_tag8 = ident8["etag"]
        stale8 = '"1111111111111111"'
        probes8 = [("GET", "/"), ("HEAD", "/"), ("GET", "/healthz"),
                   ("HEAD", "/healthz"), ("GET", page_path),
                   ("HEAD", page_path), ("GET", "/preview/" + json_name),
                   ("GET", "/nope"), ("HEAD", "/nope"),
                   ("GET", page_path, {"Range": "bytes=0-9"}),
                   ("GET", page_path, {"If-None-Match": ident_tag8}),
                   ("GET", page_path, {"If-Match": stale8})]

        # ---- a: every answer names which origins may read it --------------
        for probe in probes8:
            reply = reach(*probe)
            if reply["corp"] != "same-origin":
                bad8.append("a-corp-%s-%s" % (probe[0], probe[1]))

        # ---- b: a document names an opener policy, a json face does not ---
        for path in ("/", page_path):
            reply = reach("GET", path)
            if reply["coop"] != "same-origin":
                bad8.append("b-coop-%s-%r" % (path, reply["coop"]))
        for path in ("/preview/" + json_name, "/healthz", "/nope"):
            if reach("GET", path)["coop"]:
                bad8.append("b-nondoc-coop-%s" % path)

        # ---- c: the capability list refuses what the shipped pages never use
        denied = ("camera=()", "microphone=()", "geolocation=()", "payment=()",
                  "usb=()", "display-capture=()",
                  "publickey-credentials-get=()", "fullscreen=()")
        for probe in probes8:
            policy = reach(*probe)["perms"]
            if not policy:
                bad8.append("c-missing-%s" % probe[1])
                continue
            for token in denied:
                if token not in policy:
                    bad8.append("c-%s-%s" % (probe[1],
                                             token.split("=")[0]))

        # ---- d: no shipped page uses a refused capability -----------------
        refused = ("PaymentRequest", "requestPayment", "navigator.payment",
                   "geolocation", "getUserMedia", "getDisplayMedia",
                   "clipboard", "usb.")
        pages8 = sorted(name for name in os.listdir(PREVIEW)
                        if name.endswith(".html"))
        if len(pages8) < 100:
            bad8.append("d-pages-%d" % len(pages8))
        for name in pages8:
            with io.open(os.path.join(PREVIEW, name), "rb") as handle:
                page_text = handle.read().decode("utf-8", "replace")
            for token in refused:
                if token in page_text:
                    bad8.append("d-used-%s-%s" % (name, token))

        # ---- e: the Server header names the door, and nothing else moved ---
        for probe in probes8:
            server = reach(*probe)["server"]
            if server != "BigDomain":
                bad8.append("e-server-%s-%r" % (probe[1], server))
        reply = reach("GET", page_path, {"Accept-Encoding": "gzip"})
        try:
            plain8 = gzip.decompress(reply["body"])
        except Exception:
            plain8 = b""
            bad8.append("e-not-gzip")
        if plain8 != page_raw:
            bad8.append("e-gzip-bytes")
        reply = reach("GET", page_path, {"Range": "bytes=0-99"})
        if reply["status"] != 206 or reply["body"] != page_raw[:100]:
            bad8.append("e-range-%d" % reply["status"])
        reply = reach("GET", page_path, {"If-None-Match": ident_tag8})
        if reply["status"] != 304 or reply["body"] != b"":
            bad8.append("e-304-%d" % reply["status"])
        reply = reach("GET", page_path, {"If-Match": stale8})
        if reply["status"] != 412 or len(reply["body"]) > 64:
            bad8.append("e-412-%d" % reply["status"])

        # ---- f: the module dialect and the declared count ------------------
        with io.open(MODULE, "rb") as handle:
            raw9 = handle.read()
        if raw9[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw9:
            bad8.append("f-module-dialect")
        try:
            text9 = raw9.decode("utf-8")
            text9.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad8.append("f-module-not-ascii")
            text9 = raw9.decode("utf-8", "replace")
        for needle in ("CROSS_ORIGIN_HEADERS", "COOP_POLICY",
                       "PERMISSIONS_POLICY", "def version_string("):
            if needle not in text9:
                bad8.append("f-missing-" + needle)
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block8r = handle.read().split('"' + ROW + '"', 1)[-1][:200]
        if "8)" not in block8r:
            bad8.append("f-declared")
        if "test_frontdoor_preview_pages.py" not in block8r:
            bad8.append("f-row-file")
    finally:
        srv.shutdown()
        srv.server_close()

    report("AC-FDPV1", bool(bad), ",".join(bad))
    report("AC-FDPV2", bool(bad2), ",".join(bad2))
    report("AC-FDPV3", bool(bad3), ",".join(bad3))
    report("AC-FDPV4", bool(bad4), ",".join(bad4))
    report("AC-FDPV5", bool(bad5), ",".join(bad5))
    report("AC-FDPV6", bool(bad6), ",".join(bad6))
    report("AC-FDPV7", bool(bad7), ",".join(bad7))
    report("AC-FDPV8", bool(bad8), ",".join(bad8))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
