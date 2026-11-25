"""Suite for the door's deliverable shelf: the shipped pages get one URL.

TWENTY-ONE criteria. AC-FDPV1 (six arms) pins the shelf itself: the pages come back
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
AC-FDPV9 (six arms, R3468) pins the shelf's refusal: every verb this door does
not implement answers through the door's own policy (405 plus Allow for a
standard verb, 501 for an unknown one, 400 for a request that names both
framings), every refusal closes its connection, no 100 Continue is ever
invited, and nothing already delivered moved.
AC-FDPV10 (six arms, R3469) pins the route: the path alone picks the face, so
a share link carrying a query string opens the root, the health face and the
bare shelf exactly as the bare path does, a query never turns an unknown path
or a path escape into a page, and a query changes no header law.
AC-FDPV11 (six arms, R3470) pins the target form: an absolute-form target --
the form a client sends to a proxy, which RFC 9112 sec.3.2.2 requires a server
to accept -- answers exactly like its origin-form twin, an absolute target with
no path is the root, a scheme this door does not implement is refused 501 by
name rather than read as a path, the escape law still holds inside an absolute
target, and a protocol-relative target is folded by this door instead of by
the stdlib.
AC-FDPV12 (six arms, R3471) pins the Host field: an HTTP/1.1 message that
lacks Host, names Host twice, or carries an invalid value is refused 400 by
name with the door's policy, an absolute-form target has its Host ignored for
routing but still judged as a value, HTTP/1.0 stays exempt from the duty, and
nothing already delivered moved.
AC-FDPV13 (six arms, R3472) pins the head as a message: the request line
carries three tokens and an origin, absolute or asterisk target, no answer may
drop to HTTP/0.9 framing, the field block may not fold or carry a non-token
name, a colonless line or a control byte in a value, and conflicting
Content-Length values are refused 400 while equal duplicates stay legal.
AC-FDPV14 (six arms, R3473) pins the wire version and the connection law: an
answer names HTTP/1.1 to a 1.1 request and HTTP/1.0 to a 1.0 one, a 1.1
connection carries three requests, a 1.0 peer is told close when it did not ask
for keep-alive and gets keep-alive when it did, a request that declared a body
closes so its bytes are never parsed as a request line, Expect: 100-continue is
refused 417 (or the verb's own refusal) without ever sending 100 Continue, and
nothing already delivered moved.
AC-FDPV15 (six arms, R3474) pins the frame of a no-body answer: a 304 states
the content length of the 200 it stands in for (never zero), a face whose bytes
move on every render answers no false 304, a stable in-memory face answers its
own validator, HEAD ignores Range and keeps the whole-face count, the same HEAD
under gzip describes the gzip representation, and GET keeps its range
semantics and its disk bytes.
AC-FDPV16 (six arms, R3475) pins If-Range in both shapes RFC 9110 sec.13.1.5
allows: the exact published Last-Modified authorises the range (200 was the
measured bug -- the date shape was never parsed), a date older than the last
change still answers the whole face, a strong tag still resumes while a weak
one never does, a value in neither shape is ignored rather than 500, "not
modified since" is a <= test and If-None-Match still wins the order, and the
module stays ASCII/LF with both shapes wired to one call site.
AC-FDPV17 (six arms, R3476) pins the Range list: two segments answer 206 as
multipart/byteranges with each part carrying its own Content-Range and its
exact disk slice (the measured bug -- a multi-segment header was answered as
the whole 55KB face), the framing is complete from the opening boundary to the
closing one with no trailing byte, three segments still answer while a fourth
falls back to the whole face, an If-Range that no longer matches answers the
whole face rather than a spliced multipart, a segment past the end is dropped
while an all-past-end list answers 416 carrying the total (a malformed segment
ignores the header instead), and the single-range, whole-face, HEAD and module
dialect laws that were already delivered did not move.
AC-FDPV18 (six arms, R3477) pins the Range list's arithmetic: overlapping,
adjacent and fully contained segments are merged into one part before any
byte is written, a merged list is ordered by start, and the delivered
single-range, past-end and four-segment laws did not move.
AC-FDPV19 (six arms, R3478) pins a repeated Range line: two Range lines are
not a comma list, so the door answers the whole face instead of half-
executing the first line, and every single-line range answer did not move.
AC-FDPV20 (six arms, R3479) pins the repeated conditional fields: If-Match
and If-None-Match arrive as one comma list, a repeated HTTP-date is dropped
whole rather than half-executed, a repeated If-Range refuses the range, and
every single-line conditional answer did not move.
AC-FDPV21 (six arms, R3480) pins a repeated Accept-Encoding line: the lines
are one coding list, so gzip named only on the second line is served (200
was the measured bug -- identity came back), a q=0 on any line refuses that
coding, a wildcard on any line accepts gzip, and every single-line coding
answer did not move.
AC-FDPV22 (six arms, R3481) pins the framing and connection lists: two
Transfer-Encoding lines are one coding list, so gzip applied before chunked
answers 501 (200 was the measured bug -- a coding this door cannot decode)
while chunked anywhere but last answers 400, a repeated Connection line that
says close really closes, and every single-line framing and persistence
answer did not move.

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
import socket
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

# R3475: one place states how many criteria the registry must
# declare, so adding a criterion cannot leave eleven stale literals.
DECLARED_TAG = "22)"


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


def frame(port, method, path, headers=None):
    """R3474: the fields a no-body answer is judged on, coding included."""
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        conn.request(method, path, headers=headers or {})
        resp = conn.getresponse()
        return {"status": resp.status,
                "ctype": resp.getheader("Content-Type", "") or "",
                "length": resp.getheader("Content-Length") or "",
                "etag": resp.getheader("ETag") or "",
                "crange": resp.getheader("Content-Range") or "",
                "coding": resp.getheader("Content-Encoding") or "",
                "body": resp.read()}
    finally:
        conn.close()


def serve():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), frontdoor.Handler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    return srv, srv.server_address[1]


def raw_request(port, payload, timeout=10):
    """R3468: one raw request, read to end-of-stream.

    Several refusals this suite grades are only visible on the wire: a 100
    Continue and a second answer on the same connection are both invisible to
    http.client, which stops at the first response it likes.
    """
    sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
    sock.settimeout(timeout)
    try:
        sock.sendall(payload)
        chunks = []
        while True:
            try:
                piece = sock.recv(65536)
            except (socket.timeout, ConnectionResetError):
                break
            if not piece:
                break
            chunks.append(piece)
            # R3473: the door now keeps an HTTP/1.1 connection open, so an idle
            # read is no longer proof that the answer ended. After the first
            # bytes a short grace is long enough for a second answer this suite
            # must still see (the door writes it in the same segment), and
            # short enough that a live connection is not waited on for the
            # whole timeout.
            sock.settimeout(0.4)
        return b"".join(chunks)
    finally:
        sock.close()


def wire_reply(blob):
    """R3468: split one raw answer into its status line, headers and body."""
    head, _, body = blob.partition(b"\r\n\r\n")
    lines = head.decode("latin-1").split("\r\n") if head else []
    status = lines[0] if lines else ""
    headers = {}
    for line in lines[1:]:
        name, _, value = line.partition(":")
        headers[name.strip().lower()] = value.strip()
    return status, headers, body


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
        if 'path.startswith("/preview/")' not in text:
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
            if DECLARED_TAG not in block:
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

        # ---- f: HEAD keeps the whole-face contract and eight readers agree --
        # R3474 re-pinned: HEAD ignores Range (RFC 9110 sec.14.2 defines range
        # handling for GET alone), so the probe answers 200 with the whole-face
        # count and no Content-Range; the range face itself stays graded in
        # AC-FDPV15 d and f.
        status, _t, length, crange, _r, body = request(
            port, "HEAD", path, {"Range": "bytes=0-9"})
        if status != 200 or length != str(size) or body != b"" or crange != "":
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
            if reply["length"] != str(size4):
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
        if DECLARED_TAG not in block4:
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
        if DECLARED_TAG not in block5:
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
        if DECLARED_TAG not in block6:
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
        if DECLARED_TAG not in block7:
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
        if DECLARED_TAG not in block8r:
            bad8.append("f-declared")
        if "test_frontdoor_preview_pages.py" not in block8r:
            bad8.append("f-row-file")

        # ===== AC-FDPV9: the door refuses what it does not implement =======
        # R3468 measured before the code: every verb other than GET/HEAD fell
        # through to the stock 501 page, which carried no nosniff, no
        # Referrer-Policy, no Content-Security-Policy, no
        # Cross-Origin-Resource-Policy and no Permissions-Policy at all -- the
        # only answer on this door with no policy -- and never named Allow. A
        # request naming both Transfer-Encoding and Content-Length answered
        # 501 rather than the 400 the smuggling shape deserves, and the door
        # speaks HTTP/1.0, so no 100 Continue was invited.
        bad9 = []

        def refusal(payload):
            """One raw request, split into the three fields this arm grades."""
            return wire_reply(raw_request(port, payload))

        # ---- a: a standard verb this door does not implement is a 405 ----
        for method in ("POST", "PUT", "DELETE", "PATCH", "OPTIONS", "TRACE",
                       "CONNECT"):
            status, headers, body = refusal(
                ("%s /preview/index.html HTTP/1.1\r\nHost: door\r\n"
                 "Content-Length: 0\r\n\r\n" % method).encode("ascii"))
            if " 405 " not in status:
                bad9.append("a-status-%s-%r" % (method, status))
            if headers.get("allow") != "GET, HEAD":
                bad9.append("a-allow-%s-%r" % (method, headers.get("allow")))
            if headers.get("content-type") != "text/plain; charset=utf-8":
                bad9.append("a-ctype-%s-%r" % (method,
                                                headers.get("content-type")))
            if headers.get("connection", "").lower() != "close":
                bad9.append("a-close-%s-%r" % (method,
                                               headers.get("connection")))
            if b"405" not in body:
                bad9.append("a-body-%s" % method)

        # ---- b: an unknown verb is a 501 and must not pretend to be a 405 --
        status, headers, _body = refusal(
            b"FOO /preview/index.html HTTP/1.1\r\nHost: door\r\n\r\n")
        if " 501 " not in status:
            bad9.append("b-status-%r" % status)
        if "allow" in headers:
            bad9.append("b-allow-on-501-%r" % headers.get("allow"))
        if headers.get("connection", "").lower() != "close":
            bad9.append("b-close-%r" % headers.get("connection"))

        # ---- c: every refusal carries the full policy, and no document one -
        denied9 = ("camera=()", "microphone=()", "geolocation=()", "payment=()",
                   "usb=()", "display-capture=()",
                   "publickey-credentials-get=()", "fullscreen=()")
        refusals9 = (
            b"POST /preview/index.html HTTP/1.1\r\nHost: door\r\n\r\n",
            b"FOO /preview/index.html HTTP/1.1\r\nHost: door\r\n\r\n",
            b"POST /preview/index.html HTTP/1.1\r\nHost: door\r\n"
            b"Transfer-Encoding: chunked\r\nContent-Length: 5\r\n\r\n"
            b"5\r\nhello\r\n0\r\n\r\n",
        )
        for payload in refusals9:
            status, headers, _body = refusal(payload)
            if headers.get("x-content-type-options") != "nosniff":
                bad9.append("c-nosniff-%r" % status)
            if headers.get("referrer-policy") != "no-referrer":
                bad9.append("c-referrer-%r" % status)
            if headers.get("content-security-policy") != \
                    frontdoor.TEXT_POLICY:
                bad9.append("c-csp-%r" % status)
            if headers.get("cross-origin-resource-policy") != "same-origin":
                bad9.append("c-corp-%r" % status)
            policy9 = headers.get("permissions-policy", "")
            for token in denied9:
                if token not in policy9:
                    bad9.append("c-perm-%r-%s" % (status,
                                                   token.split("=")[0]))
            if headers.get("server") != "BigDomain":
                bad9.append("c-server-%r-%r" % (status,
                                                 headers.get("server")))
            if "cross-origin-opener-policy" in headers:
                bad9.append("c-coop-%r" % status)
            if "x-frame-options" in headers:
                bad9.append("c-xfo-%r" % status)

        # ---- d: both framings at once is a 400, answered exactly once ------
        blob9 = raw_request(port, b"POST /preview/index.html HTTP/1.1\r\nHost: door\r\n"
                          b"Transfer-Encoding: chunked\r\nContent-Length: 5\r\n"
                          b"\r\n5\r\nhello\r\n0\r\n\r\n")
        status, headers, body = wire_reply(blob9)
        if " 400 " not in status:
            bad9.append("d-status-%r" % status)
        if headers.get("connection", "").lower() != "close":
            bad9.append("d-close-%r" % headers.get("connection"))
        answers9 = blob9.count(b"HTTP/1.0 ") + blob9.count(b"HTTP/1.1 ")
        if answers9 != 1:
            bad9.append("d-answers-%d" % answers9)
        if b"400" not in body:
            bad9.append("d-body")

        # ---- e: the door never invites a body it will not read ------------
        blob9 = raw_request(port, b"POST /preview/index.html HTTP/1.1\r\nHost: door\r\n"
                          b"Expect: 100-continue\r\nContent-Length: 5\r\n"
                          b"\r\nhello")
        status, _headers, _body = wire_reply(blob9)
        if b"100 Continue" in blob9:
            bad9.append("e-invited")
        if " 405 " not in status:
            bad9.append("e-status-%r" % status)
        blob9 = raw_request(port, b"GET /healthz HTTP/1.1\r\nHost: door\r\n"
                          b"Content-Length: 5\r\n\r\nhello")
        status, headers, body = wire_reply(blob9)
        if " 200 " not in status or body != b"ok":
            bad9.append("e-get-%r" % status)
        if headers.get("connection", "").lower() != "close":
            bad9.append("e-get-close-%r" % headers.get("connection"))
        if b"100 Continue" in blob9:
            bad9.append("e-get-invited")

        # ---- f: nothing already delivered moved, and the count is 9 -------
        for method in ("GET", "HEAD"):
            status, headers, _body = refusal(
                ("%s /preview/index.html HTTP/1.1\r\nHost: door\r\n\r\n"
                 % method).encode("ascii"))
            if " 200 " not in status:
                bad9.append("f-%s-%r" % (method, status))
            if headers.get("x-content-type-options") != "nosniff":
                bad9.append("f-%s-policy" % method)
        with io.open(MODULE, "rb") as handle:
            raw10 = handle.read()
        if raw10[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw10:
            bad9.append("f-module-dialect")
        try:
            text10 = raw10.decode("utf-8")
            text10.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad9.append("f-module-not-ascii")
            text10 = raw10.decode("utf-8", "replace")
        for needle in ("ALLOWED_METHODS", "def send_error(",
                       "def handle_expect_100(", "def _method_refused("):
            if needle not in text10:
                bad9.append("f-missing-" + needle)
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block9r = handle.read().split('"' + ROW + '"', 1)[-1][:200]
        if DECLARED_TAG not in block9r:
            bad9.append("f-declared")
        if "test_frontdoor_preview_pages.py" not in block9r:
            bad9.append("f-row-file")

        # ===== AC-FDPV10: the route is chosen on the path alone ============
        # R3469 measured before the code: /, /index.html, /healthz and the
        # bare /preview compared self.path whole, so a share link carrying a
        # tracking parameter answered 404 on those four routes while
        # /preview/index.html?v=2 answered the page -- one door, two query
        # laws. No face on this door selects by query, so the query is now
        # dropped once, for every route.
        bad10 = []
        with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
            disk_index = handle.read()

        # ---- a: the root answers the same page with and without a query ---
        # Measured: render() runs a live probe that books a transaction id per
        # render, so two calls differ at that one field (offset 11603, same
        # length). The arm therefore pins what a reader sees -- status, type,
        # length and the page's own head -- and says why bytes cannot be
        # compared, rather than pretending the root is a static file.
        bare10 = get(port, "/")
        query10 = get(port, "/?utm_source=share")
        if bare10[0] != 200 or query10[0] != 200:
            bad10.append("a-status-%r-%r" % (bare10[0], query10[0]))
        if query10[1] != bare10[1]:
            bad10.append("a-ctype-%r" % query10[1])
        if len(query10[2]) != len(bare10[2]):
            bad10.append("a-length-%d-%d" % (len(query10[2]),
                                             len(bare10[2])))
        for label10, body10 in (("bare", bare10[2]), ("query", query10[2])):
            if not body10.startswith(b"<!DOCTYPE html>"):
                bad10.append("a-%s-not-page" % label10)
            if body10 == b"404 not found":
                bad10.append("a-%s-404" % label10)

        # ---- b: the health face answers ok with a query -------------------
        status10, ctype10, body10 = get(port, "/healthz?probe=1")
        if status10 != 200 or body10 != b"ok" or \
                not ctype10.startswith("text/plain"):
            bad10.append("b-health-%r-%r-%r" % (status10, ctype10, body10))

        # ---- c: the bare shelf name opens the index face ------------------
        status10, _ctype10, body10 = get(port, "/preview?x=1")
        if status10 != 200 or body10 != disk_index:
            bad10.append("c-shelf-%r-%d-%d" % (status10, len(body10),
                                               len(disk_index)))
        status10, ctype10, body10 = get(port, "/index.html?x=1")
        if status10 != 200 or len(body10) != len(bare10[2]) or \
                ctype10 != bare10[1] or \
                not body10.startswith(b"<!DOCTYPE html>"):
            bad10.append("c-root-alias-%r-%d" % (status10, len(body10)))

        # ---- d: the query is not a wildcard -------------------------------
        status10, _ctype10, body10 = get(port, "/nope?x=1")
        if status10 != 404 or b"404" not in body10:
            bad10.append("d-unknown-%r" % status10)
        for escape10 in ("/preview/../frontdoor.py?x=1",
                         "/preview/..%2ffrontdoor.py?x=1",
                         "/preview/%2e%2e/frontdoor.py?x=1"):
            status10, _ctype10, _body10 = get(port, escape10)
            if status10 != 404:
                bad10.append("d-escape-%r" % status10)

        # ---- e: a query changes no law ------------------------------------
        status10, headers10, _body10 = wire_reply(
            raw_request(port, b"GET /?utm=1 HTTP/1.1\r\nHost: door\r\n\r\n"))
        if " 200 " not in status10:
            bad10.append("e-root-%r" % status10)
        if headers10.get("x-content-type-options") != "nosniff":
            bad10.append("e-nosniff")
        if headers10.get("referrer-policy") != "no-referrer":
            bad10.append("e-referrer")
        if headers10.get("cross-origin-resource-policy") != "same-origin":
            bad10.append("e-corp")
        if headers10.get("cache-control") != "no-store":
            bad10.append("e-cache-%r" % headers10.get("cache-control"))
        for token10 in ("camera=()", "geolocation=()", "usb=()"):
            if token10 not in headers10.get("permissions-policy", ""):
                bad10.append("e-perm-" + token10.split("=")[0])
        status10, headers10, body10 = wire_reply(
            raw_request(port, b"GET /preview/index.html?v=2 HTTP/1.1\r\n"
                              b"Host: door\r\nAccept-Encoding: gzip\r\n\r\n"))
        if headers10.get("content-encoding") != "gzip":
            bad10.append("e-gzip-%r" % headers10.get("content-encoding"))
        else:
            try:
                if gzip.decompress(body10) != disk_index:
                    bad10.append("e-gzip-bytes")
            except OSError:
                bad10.append("e-gzip-broken")
        status10, ctype10, length10, body10 = head(port, "/?x=1")
        if status10 != 200 or body10 != b"":
            bad10.append("e-head-%r-%d" % (status10, len(body10)))
        if length10 != str(len(bare10[2])):
            bad10.append("e-head-length-%r" % length10)
        if ctype10 != bare10[1]:
            bad10.append("e-head-ctype-%r" % ctype10)

        # ---- f: nothing delivered moved, and the count is 10 --------------
        for path10 in ("/", "/healthz", "/preview", "/preview/index.html"):
            status10, _ctype10, _body10 = get(port, path10)
            if status10 != 200:
                bad10.append("f-%s-%r" % (path10, status10))
        with io.open(MODULE, "rb") as handle:
            raw11 = handle.read()
        if raw11[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw11:
            bad10.append("f-module-dialect")
        try:
            text11 = raw11.decode("utf-8")
            text11.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad10.append("f-module-not-ascii")
            text11 = raw11.decode("utf-8", "replace")
        if "def _request_path(" not in text11:
            bad10.append("f-missing-_request_path")
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block10r = handle.read().split('"' + ROW + '"', 1)[-1][:200]
        if DECLARED_TAG not in block10r:
            bad10.append("f-declared")
        if "test_frontdoor_preview_pages.py" not in block10r:
            bad10.append("f-row-file")

        # ===== AC-FDPV11: the target may be absolute-form ==================
        # R3470 measured before the code: every absolute-form target -- the
        # form a client sends to a proxy, which RFC 9112 sec.3.2.2 requires a
        # server to accept -- answered 404 on this door, the same answer as a
        # missing face. The authority is dropped (one shelf, never selected by
        # host), a scheme this door does not implement is refused by name, and
        # a protocol-relative target is folded by this door instead of by the
        # stdlib.
        bad11 = []
        with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
            disk_index11 = handle.read()
        base11 = "http://127.0.0.1:%d" % port

        def abs_get11(target11, method11="GET"):
            return wire_reply(raw_request(
                port, ("%s %s HTTP/1.1\r\nHost: door\r\n\r\n"
                       % (method11, target11)).encode("ascii")))

        # ---- a: absolute-form answers like its origin-form twin -----------
        for twin11 in ("/healthz", "/preview", "/preview/index.html"):
            status11, ctype11, body11 = get(port, twin11)
            line11, headers11, abs_body11 = abs_get11(base11 + twin11)
            label11 = twin11.replace("/", "-").strip("-")
            if " 200 " not in line11:
                bad11.append("a-status-%s-%r" % (label11, line11))
                continue
            if abs_body11 != body11:
                bad11.append("a-bytes-%s-%d-%d" % (label11, len(abs_body11),
                                                   len(body11)))
            if headers11.get("content-type") != ctype11:
                bad11.append("a-ctype-%s" % label11)
        bare_root11 = get(port, "/")
        line11, headers11, body11 = abs_get11(base11 + "/")
        if " 200 " not in line11 or \
                headers11.get("content-type") != bare_root11[1] or \
                len(body11) != len(bare_root11[2]) or \
                not body11.startswith(b"<!DOCTYPE html>"):
            bad11.append("a-root-%r-%d-%d" % (line11, len(body11),
                                              len(bare_root11[2])))

        # ---- b: the query and fragment law survives the authority ---------
        line11, _headers11, body11 = abs_get11(
            base11 + "/preview/index.html?v=2")
        if " 200 " not in line11 or body11 != disk_index11:
            bad11.append("b-query-%r-%d" % (line11, len(body11)))
        line11, _headers11, body11 = abs_get11(base11 + "/healthz?probe=1")
        if " 200 " not in line11 or body11 != b"ok":
            bad11.append("b-health-%r-%r" % (line11, body11))

        # ---- c: the escape law holds inside an absolute target ------------
        for escape11 in (base11 + "/preview/../frontdoor.py",
                         base11 + "/preview/%2e%2e/frontdoor.py",
                         base11 + "/../frontdoor.py"):
            line11, _headers11, _body11 = abs_get11(escape11)
            if " 404 " not in line11:
                bad11.append("c-escape-%r" % line11)

        # ---- d: an absolute target with no path is the root ---------------
        for empty11 in (base11, base11 + "?x=1"):
            line11, headers11, body11 = abs_get11(empty11)
            if " 200 " not in line11 or \
                    headers11.get("content-type") != bare_root11[1] or \
                    len(body11) != len(bare_root11[2]) or \
                    not body11.startswith(b"<!DOCTYPE html>"):
                bad11.append("d-empty-%r-%d" % (line11, len(body11)))

        # ---- e: a scheme this door does not implement is refused by name --
        for scheme11 in ("file:///preview/index.html",
                         "ftp://127.0.0.1/preview/index.html"):
            line11, headers11, body11 = abs_get11(scheme11)
            if " 501 " not in line11:
                bad11.append("e-status-%r" % line11)
            if not body11.startswith(b"501 unsupported scheme"):
                bad11.append("e-body-%r" % body11[:24])
            if headers11.get("x-content-type-options") != "nosniff":
                bad11.append("e-nosniff")
            if headers11.get("cross-origin-resource-policy") != "same-origin":
                bad11.append("e-corp")
            if "camera=()" not in headers11.get("permissions-policy", ""):
                bad11.append("e-perm")
            if headers11.get("server") != "BigDomain":
                bad11.append("e-server-%r" % headers11.get("server"))
        line11, _headers11, body11 = abs_get11(
            "HTTP://127.0.0.1:%d/healthz" % port)
        if " 200 " not in line11 or body11 != b"ok":
            bad11.append("e-upper-%r-%r" % (line11, body11))

        # ---- f: nothing delivered moved, and the count is 11 --------------
        for path11 in ("/", "/healthz", "/preview", "/preview/index.html",
                       "//healthz", "//preview/index.html"):
            status11, _ctype11, _body11 = get(port, path11)
            if status11 != 200:
                bad11.append("f-%s-%r" % (path11, status11))
        line11, _headers11, body11 = abs_get11(
            base11 + "/preview/index.html", method11="HEAD")
        if " 200 " not in line11 or body11 != b"":
            bad11.append("f-head-%r-%d" % (line11, len(body11)))
        with io.open(MODULE, "rb") as handle:
            raw12 = handle.read()
        if raw12[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw12:
            bad11.append("f-module-dialect")
        try:
            text12 = raw12.decode("utf-8")
            text12.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad11.append("f-module-not-ascii")
            text12 = raw12.decode("utf-8", "replace")
        for token12 in ("ABSOLUTE_FORM", "def _resolve_target(",
                        "def _request_path("):
            if token12 not in text12:
                bad11.append("f-missing-" + token12.split("(")[0].strip()
                             .replace(" ", "-"))
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block11r = handle.read().split('"' + ROW + '"', 1)[-1][:200]
        if DECLARED_TAG not in block11r:
            bad11.append("f-declared")
        if "test_frontdoor_preview_pages.py" not in block11r:
            bad11.append("f-row-file")

        # ===== AC-FDPV12: the Host field law ==============================
        # R3471 measured before the code: fourteen Host shapes -- none at all,
        # an empty value, two field lines, a space, a path character, a
        # userinfo character, a comma list, a 300-byte name, an absolute-form
        # target with a conflicting Host and one with no Host -- all answered
        # 200 "ok". RFC 9112 sec.3.2 makes each malformed shape a 400.
        bad12 = []
        door12 = "127.0.0.1:%d" % port

        def host12(lines12, verb12="GET", target12="/healthz"):
            payload12 = ("%s %s HTTP/1.1\r\n%s\r\n\r\n"
                         % (verb12, target12, lines12)).encode("ascii")
            return wire_reply(raw_request(port, payload12))

        # ---- a: a missing Host is a 400 on every message shape ------------
        for label12, payload12 in (
                ("plain", b"GET /healthz HTTP/1.1\r\n\r\n"),
                ("absolute",
                 b"GET http://elsewhere.example/healthz HTTP/1.1\r\n\r\n"),
                ("refused-verb", b"POST /healthz HTTP/1.1\r\n\r\n")):
            blob12 = raw_request(port, payload12)
            line12, headers12, body12 = wire_reply(blob12)
            if " 400 " not in line12:
                bad12.append("a-status-%s-%r" % (label12, line12))
            if body12 != b"400 host field required\n":
                bad12.append("a-body-%s-%r" % (label12, body12[:26]))
            if headers12.get("x-content-type-options") != "nosniff" or \
                    headers12.get("cross-origin-resource-policy") != \
                    "same-origin" or \
                    headers12.get("server") != "BigDomain" or \
                    headers12.get("connection") != "close":
                bad12.append("a-policy-%s" % label12)
            if blob12.count(b"HTTP/1.") != 1:
                bad12.append("a-second-answer-%s" % label12)

        # ---- b: two Host fields, and one field carrying a list -------------
        blob12 = raw_request(
            port, b"GET /healthz HTTP/1.1\r\nHost: a\r\nHost: b\r\n\r\n")
        line12, _headers12, body12 = wire_reply(blob12)
        if " 400 " not in line12 or body12 != b"400 duplicate host field\n":
            bad12.append("b-dupe-%r-%r" % (line12, body12[:26]))
        if blob12.count(b"HTTP/1.") != 1:
            bad12.append("b-dupe-second-answer")
        line12, _headers12, body12 = host12("Host: a, b")
        if " 400 " not in line12 or body12 != b"400 invalid host field\n":
            bad12.append("b-list-%r-%r" % (line12, body12[:26]))

        # ---- c: the value law ---------------------------------------------
        for value12 in ("", "bad host", "a/b", "u@h", "a:b:c", "[::1",
                        "a" * 300):
            line12, _headers12, body12 = host12("Host: " + value12)
            if " 400 " not in line12 or \
                    body12 != b"400 invalid host field\n":
                bad12.append("c-bad-%r-%r-%r" % (value12[:8], line12,
                                                 body12[:26]))
        for value12 in ("door", "door:8080", door12, "[::1]", "[::1]:8080",
                        "door."):
            line12, _headers12, body12 = host12("Host: " + value12)
            if " 200 " not in line12 or body12 != b"ok":
                bad12.append("c-good-%r-%r-%r" % (value12, line12,
                                                  body12[:12]))

        # ---- d: absolute-form ignores Host for routing, not for judging ----
        with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
            disk_index12 = handle.read()
        line12, _headers12, body12 = host12(
            "Host: elsewhere.example",
            target12="http://%s/preview/index.html" % door12)
        if " 200 " not in line12 or body12 != disk_index12:
            bad12.append("d-conflict-%r-%d" % (line12, len(body12)))
        line12, _headers12, body12 = host12(
            "Host: bad host", target12="http://%s/healthz" % door12)
        if " 400 " not in line12 or body12 != b"400 invalid host field\n":
            bad12.append("d-conflict-bad-%r-%r" % (line12, body12[:26]))

        # ---- e: HTTP/1.0 is exempt from the duty --------------------------
        line12, _headers12, body12 = wire_reply(raw_request(
            port, b"GET /healthz HTTP/1.0\r\n\r\n"))
        if " 200 " not in line12 or body12 != b"ok":
            bad12.append("e-nohost-%r-%r" % (line12, body12[:12]))
        line12, _headers12, body12 = wire_reply(raw_request(
            port, b"GET /healthz HTTP/1.0\r\nHost: bad host\r\n\r\n"))
        if " 200 " not in line12 or body12 != b"ok":
            bad12.append("e-badhost-%r-%r" % (line12, body12[:12]))

        # ---- f: nothing delivered moved, and the count is 12 --------------
        for path12 in ("/", "/healthz", "/preview", "/preview/index.html"):
            status12, _ctype12, _body12 = get(port, path12)
            if status12 != 200:
                bad12.append("f-%s-%r" % (path12, status12))
        line12, headers12, _body12 = host12("Host: door", verb12="POST")
        if " 405 " not in line12 or headers12.get("allow") != "GET, HEAD":
            bad12.append("f-post-%r-%r" % (line12, headers12.get("allow")))
        line12, headers12, _body12 = host12("Host: door", verb12="FOO")
        if " 501 " not in line12 or "allow" in headers12:
            bad12.append("f-foo-%r" % line12)
        with io.open(MODULE, "rb") as handle:
            raw12b = handle.read()
        if raw12b[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw12b:
            bad12.append("f-module-dialect")
        try:
            text12b = raw12b.decode("utf-8")
            text12b.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad12.append("f-module-not-ascii")
            text12b = raw12b.decode("utf-8", "replace")
        for token12b in ("HOST_MAX", "def _host_value_ok(",
                         "def _host_refusal("):
            if token12b not in text12b:
                bad12.append("f-missing-" + token12b.split("(")[0]
                             .replace(" ", "-"))
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block12r = handle.read().split('"' + ROW + '"', 1)[-1][:220]
        if DECLARED_TAG not in block12r:
            bad12.append("f-declared")
        if "test_frontdoor_preview_pages.py" not in block12r:
            bad12.append("f-row-file")
        # ===== AC-FDPV13: the request line and header block grammar =======
        # R3472 measured before the code: a two-word request line was answered
        # in HTTP/0.9 mode -- no status line, no policy header, no
        # Content-Length, no Server; a target that was not origin-form
        # ("?x=1") answered the root page; a field name with a space or a
        # control byte, an empty name, a colonless line, an obs-fold and a NUL
        # inside a value all answered 200; and two Content-Length fields with
        # different values answered 200. RFC 9112 gives each of those a 400.
        bad13 = []

        def refuse13(label13, payload13, body13):
            blob13 = raw_request(port, payload13)
            line13, headers13, got13 = wire_reply(blob13)
            if " 400 " not in line13:
                bad13.append("%s-status-%r" % (label13, line13))
            if got13 != body13:
                bad13.append("%s-body-%r" % (label13, got13[:26]))
            if blob13.count(b"HTTP/1.") != 1:
                bad13.append("%s-status-line-count" % label13)
            if headers13.get("x-content-type-options") != "nosniff" or \
                    headers13.get("cross-origin-resource-policy") != \
                    "same-origin" or \
                    "camera=()" not in headers13.get("permissions-policy",
                                                     "") or \
                    headers13.get("server") != "BigDomain" or \
                    headers13.get("connection") != "close" or \
                    not headers13.get("content-length"):
                bad13.append("%s-policy" % label13)

        # ---- a: no request line may be answered as HTTP/0.9 ----------------
        for label13, payload13 in (
                ("two-word-path", b"GET /healthz\r\n\r\n"),
                ("two-word-root", b"GET /\r\n\r\n"),
                ("two-word-version",
                 b"GET HTTP/1.1\r\nHost: door\r\n\r\n"),
                ("empty-target",
                 b"GET  HTTP/1.1\r\nHost: door\r\n\r\n")):
            refuse13("a-" + label13, payload13, b"400 bad request line\n")

        # ---- b: the target grammar ----------------------------------------
        refuse13("b-query-only",
                 b"GET ?x=1 HTTP/1.1\r\nHost: door\r\n\r\n",
                 b"400 bad request target\n")
        blob13 = raw_request(port, b"GET * HTTP/1.1\r\nHost: door\r\n\r\n")
        line13, _headers13, body13 = wire_reply(blob13)
        if " 404 " not in line13 or body13 != b"404 not found":
            bad13.append("b-star-%r-%r" % (line13, body13[:12]))
        if blob13.count(b"HTTP/1.") != 1:
            bad13.append("b-star-status-line-count")
        status13, _ctype13, body13 = get(port, "/?utm=1")
        if status13 != 200 or not body13.startswith(b"<!DOCTYPE html>"):
            bad13.append("b-root-moved-%r" % status13)

        # ---- c: the field-name token law ----------------------------------
        for label13, line13raw in (
                ("space", b"Bad Header: x"),
                ("control", b"Bad\x01Header: x"),
                ("empty", b": x")):
            refuse13("c-" + label13,
                     b"GET /healthz HTTP/1.1\r\nHost: door\r\n" +
                     line13raw + b"\r\n\r\n",
                     b"400 invalid header name\n")
        line13, _headers13, body13 = wire_reply(raw_request(
            port, b"GET /healthz HTTP/1.1\r\nHost: door\r\n"
                  b"X-Fine_1: v\r\n\r\n"))
        if " 200 " not in line13 or body13 != b"ok":
            bad13.append("c-good-%r-%r" % (line13, body13[:12]))

        # ---- d: obs-fold is refused ---------------------------------------
        refuse13("d-fold-plain",
                 b"GET /healthz HTTP/1.1\r\nHost: door\r\n"
                 b"X-A: a\r\n b\r\n\r\n",
                 b"400 folded header line\n")
        refuse13("d-fold-host",
                 b"GET /healthz HTTP/1.1\r\nHost: door\r\n more\r\n\r\n",
                 b"400 folded header line\n")

        # ---- e: colonless, control value, and conflicting lengths ---------
        refuse13("e-no-colon",
                 b"GET /healthz HTTP/1.1\r\nHost: door\r\nJUNKLINE\r\n\r\n",
                 b"400 malformed header line\n")
        refuse13("e-value-nul",
                 b"GET /healthz HTTP/1.1\r\nHost: door\r\n"
                 b"X-A: a\x00b\r\n\r\n",
                 b"400 invalid header value\n")
        refuse13("e-length-two-fields",
                 b"GET /healthz HTTP/1.1\r\nHost: door\r\n"
                 b"Content-Length: 5\r\nContent-Length: 6\r\n\r\n",
                 b"400 conflicting content length\n")
        refuse13("e-length-list",
                 b"GET /healthz HTTP/1.1\r\nHost: door\r\n"
                 b"Content-Length: 5, 6\r\n\r\n",
                 b"400 conflicting content length\n")
        line13, headers13, body13 = wire_reply(raw_request(
            port, b"GET /healthz HTTP/1.1\r\nHost: door\r\n"
                  b"Content-Length: 5\r\nContent-Length: 5\r\n\r\n"))
        if " 200 " not in line13 or body13 != b"ok" or \
                headers13.get("connection") != "close":
            bad13.append("e-length-equal-%r-%r-%r" % (
                line13, body13[:12], headers13.get("connection")))
        line13, _headers13, body13 = wire_reply(raw_request(
            port, b"GET /healthz HTTP/1.1\r\nHost: door\r\n"
                  b"X-A: a\tb\r\n\r\n"))
        if " 200 " not in line13 or body13 != b"ok":
            bad13.append("e-value-tab-%r-%r" % (line13, body13[:12]))

        # ---- f: nothing delivered moved, and the count is 14 --------------
        for path13 in ("/", "/healthz", "/preview", "/preview/index.html"):
            status13, _ctype13, _body13 = get(port, path13)
            if status13 != 200:
                bad13.append("f-%s-%r" % (path13, status13))
        line13, headers13, _body13 = wire_reply(raw_request(
            port, b"POST /healthz HTTP/1.1\r\nHost: door\r\n\r\n"))
        if " 405 " not in line13 or headers13.get("allow") != "GET, HEAD":
            bad13.append("f-post-%r-%r" % (line13, headers13.get("allow")))
        line13, headers13, _body13 = wire_reply(raw_request(
            port, b"FOO /healthz HTTP/1.1\r\nHost: door\r\n\r\n"))
        if " 501 " not in line13 or "allow" in headers13:
            bad13.append("f-foo-%r" % line13)
        with io.open(MODULE, "rb") as handle:
            raw13b = handle.read()
        if raw13b[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw13b:
            bad13.append("f-module-dialect")
        try:
            text13 = raw13b.decode("utf-8")
            text13.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad13.append("f-module-not-ascii")
            text13 = raw13b.decode("utf-8", "replace")
        for token13 in ("HEADER_NAME", "def _head_refusal(", "class HeaderTap",
                        "def parse_request("):
            if token13 not in text13:
                bad13.append("f-missing-" + token13.split("(")[0]
                             .replace(" ", "-"))
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block13 = handle.read().split('"' + ROW + '"', 1)[-1][:220]
        if DECLARED_TAG not in block13:
            bad13.append("f-declared")
        if "test_frontdoor_preview_pages.py" not in block13:
            bad13.append("f-row-file")

        # ===== AC-FDPV14: the wire version and the connection law ==========
        # R3473 measured before the code (tmp/probe-R3473.py, eight raw
        # shapes). Every answer named HTTP/1.0, even to an HTTP/1.1 request
        # the door judged by 1.1 duties; no 200 named a Connection field and
        # the socket closed, so a 1.1 peer's second request met a reset with
        # nothing on the wire to warn it; a 1.0 peer that asked keep-alive got
        # the same silent close; Expect: 100-continue was unreachable (1.0
        # mode never consults the hook) and a 1.1 GET carrying a body was
        # answered 200 with its bytes left unread; two pipelined 1.1
        # requests got one status line and one "ok".
        bad14 = []

        def dialog14(payloads, timeout=6.0):
            """One socket, several writes, one framed answer read per write.

            A connection that dies mid-dialog is a READING, not a crash: the
            transport name is appended so the arm reddens by name instead of
            taking the whole suite down with it.
            """
            sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
            sock.settimeout(timeout)
            got = []
            try:
                for piece in payloads:
                    try:
                        sock.sendall(piece)
                        buf = b""
                        while b"\r\n\r\n" not in buf:
                            chunk = sock.recv(65536)
                            if not chunk:
                                break
                            buf += chunk
                        if b"\r\n\r\n" in buf:
                            head14, _, rest14 = buf.partition(b"\r\n\r\n")
                            length14 = 0
                            for line14 in head14.split(b"\r\n")[1:]:
                                name14, _, value14 = line14.partition(b":")
                                if name14.strip().lower() == b"content-length":
                                    length14 = int(value14.strip())
                            while len(rest14) < length14:
                                chunk = sock.recv(65536)
                                if not chunk:
                                    break
                                rest14 += chunk
                            buf = head14 + b"\r\n\r\n" + rest14
                    except OSError as exc:
                        got.append(b"transport:" +
                                   exc.__class__.__name__.encode("ascii"))
                        break
                    got.append(buf)
            finally:
                sock.close()
            return got

        # ---- a: the answer names the version it was written in ------------
        ans14 = dialog14([b"GET /healthz HTTP/1.1\r\nHost: door\r\n"
                          b"Connection: close\r\n\r\n"])
        if not ans14[0].startswith(b"HTTP/1.1 200 "):
            bad14.append("a-11-%r" % ans14[0][:18])
        ans14 = dialog14([b"GET /healthz HTTP/1.0\r\n\r\n"])
        if not ans14[0].startswith(b"HTTP/1.0 200 "):
            bad14.append("a-10-%r" % ans14[0][:18])
        ans14 = dialog14([b"GET /healthz\r\n\r\n"])
        if not ans14[0].startswith(b"HTTP/1.0 400 "):
            bad14.append("a-lift-%r" % ans14[0][:22])

        # ---- b: a 1.1 connection carries three requests -------------------
        trio14 = dialog14([b"GET /healthz HTTP/1.1\r\nHost: door\r\n\r\n"] * 3)
        if len(trio14) != 3:
            bad14.append("b-count-%d" % len(trio14))
        for idx14, one14 in enumerate(trio14):
            head14 = one14.split(b"\r\n\r\n", 1)[0]
            if not one14.startswith(b"HTTP/1.1 200 OK"):
                bad14.append("b-status%d-%r" % (idx14, one14[:18]))
            if one14.split(b"\r\n\r\n", 1)[-1] != b"ok":
                bad14.append("b-body%d-%r" % (idx14,
                                              one14.split(b"\r\n\r\n", 1)[-1]))
            if b"connection: close" in head14.lower():
                bad14.append("b-closed%d" % idx14)

        # ---- c: HTTP/1.0 -- told when closed, honoured when asked ---------
        blob14 = raw_request(port, b"GET /healthz HTTP/1.0\r\n\r\n")
        line14, headers14, body14 = wire_reply(blob14)
        if " 200 " not in line14 or body14 != b"ok":
            bad14.append("c10-status-%r-%r" % (line14, body14[:10]))
        if headers14.get("connection") != "close":
            bad14.append("c10-silent-%r" % headers14.get("connection"))
        ka14 = dialog14([b"GET /healthz HTTP/1.0\r\nConnection: keep-alive\r\n"
                         b"\r\n"] * 2)
        if len(ka14) != 2:
            bad14.append("c10-keep-count-%d" % len(ka14))
        elif b"connection: keep-alive" not in ka14[0].lower():
            bad14.append("c10-keep-header")
        elif not ka14[1].startswith(b"HTTP/1.0 200 "):
            bad14.append("c10-second-%r" % ka14[1][:18])

        # ---- d: a declared body closes and its bytes are never parsed -----
        blob14 = raw_request(port, b"GET /healthz HTTP/1.1\r\nHost: door\r\n"
                                  b"Content-Length: 5\r\n\r\nhello"
                                  b"GET /healthz HTTP/1.1\r\nHost: door\r\n\r\n")
        line14, headers14, body14 = wire_reply(blob14)
        if " 200 " not in line14 or body14 != b"ok":
            bad14.append("d-status-%r-%r" % (line14, body14[:10]))
        if headers14.get("connection") != "close":
            bad14.append("d-close-%r" % headers14.get("connection"))
        if blob14.count(b"HTTP/1.") != 1:
            bad14.append("d-status-lines-%d" % blob14.count(b"HTTP/1."))

        # ---- e: Expect is reachable and never invites a body --------------
        blob14 = raw_request(port, b"GET /healthz HTTP/1.1\r\nHost: door\r\n"
                                  b"Expect: 100-continue\r\n"
                                  b"Content-Length: 5\r\n\r\n")
        line14, headers14, _body14 = wire_reply(blob14)
        if " 417 " not in line14:
            bad14.append("e-get-%r" % line14)
        if headers14.get("connection") != "close":
            bad14.append("e-get-close-%r" % headers14.get("connection"))
        if b"100 Continue" in blob14:
            bad14.append("e-get-invited")
        blob14 = raw_request(port, b"POST /healthz HTTP/1.1\r\nHost: door\r\n"
                                  b"Expect: 100-continue\r\n"
                                  b"Content-Length: 5\r\n\r\nhello")
        line14, headers14, _body14 = wire_reply(blob14)
        if " 405 " not in line14 or headers14.get("allow") != "GET, HEAD":
            bad14.append("e-post-%r-%r" % (line14, headers14.get("allow")))
        if b"100 Continue" in blob14:
            bad14.append("e-post-invited")
        blob14 = raw_request(port, b"GET /healthz HTTP/1.0\r\n"
                                  b"Expect: 100-continue\r\n"
                                  b"Content-Length: 5\r\n\r\n")
        line14, headers14, body14 = wire_reply(blob14)
        if " 200 " not in line14 or body14 != b"ok":
            bad14.append("e-10-%r-%r" % (line14, body14[:10]))
        if headers14.get("connection") != "close":
            bad14.append("e-10-close-%r" % headers14.get("connection"))
        if b"100 Continue" in blob14:
            bad14.append("e-10-invited")

        # ---- f: nothing delivered moved, and the count is 14 --------------
        for path14 in ("/", "/healthz", "/preview", "/preview/index.html"):
            status14, _ctype14, _body14 = get(port, path14)
            if status14 != 200:
                bad14.append("f-%s-%r" % (path14, status14))
        status14, _ctype14, body14 = get(port, "/nope")
        if status14 != 404 or body14 != b"404 not found":
            bad14.append("f-404-%r-%r" % (status14, body14[:12]))
        line14, headers14, _body14 = wire_reply(raw_request(
            port, b"POST /healthz HTTP/1.1\r\nHost: door\r\n\r\n"))
        if " 405 " not in line14 or headers14.get("allow") != "GET, HEAD":
            bad14.append("f-post-%r-%r" % (line14, headers14.get("allow")))
        line14, headers14, _body14 = wire_reply(raw_request(
            port, b"FOO /healthz HTTP/1.1\r\nHost: door\r\n\r\n"))
        if " 501 " not in line14 or "allow" in headers14:
            bad14.append("f-foo-%r" % line14)
        with io.open(MODULE, "rb") as handle:
            raw14 = handle.read()
        if raw14[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw14:
            bad14.append("f-module-dialect")
        try:
            text14 = raw14.decode("utf-8")
            text14.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad14.append("f-module-not-ascii")
            text14 = raw14.decode("utf-8", "replace")
        for token14 in ("PROTOCOL_11", "def _persistent(",
                        "def _wire_version(", "def handle_expect_100("):
            if token14 not in text14:
                bad14.append("f-missing-" + token14.split("(")[0]
                             .replace(" ", "-"))
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block14 = handle.read().split('"' + ROW + '"', 1)[-1][:220]
        if DECLARED_TAG not in block14:
            bad14.append("f-declared")
        if "test_frontdoor_preview_pages.py" not in block14:
            bad14.append("f-row-file")

        # ===== AC-FDPV15: the frame of a no-body answer ====================
        # R3474 measured before the edit: a shelf 304 declared Content-Length:
        # 0 against a 55185-byte representation, the root and /healthz sent an
        # ETag they never read, HEAD + Range answered 206 with a 10-byte count,
        # and HEAD + Range + gzip answered 206 with the identity count while a
        # GET under the same headers was gzip. RFC 9110 sec.8.6 lets a 304
        # carry only the count its 200 content has, and sec.14.2 defines range
        # handling for GET alone.
        bad15 = []
        # ---- a: a shelf 304 states the length of the 200 it stands in for --
        page15 = "/preview/index.html"
        plain15 = frame(port, "GET", page15)
        stale15 = frame(port, "GET", page15,
                        {"If-None-Match": plain15["etag"]})
        if stale15["status"] != 304:
            bad15.append("a-status-%d" % stale15["status"])
        if stale15["length"] != plain15["length"]:
            bad15.append("a-length-%r-%r" % (stale15["length"],
                                            plain15["length"]))
        if stale15["body"] != b"":
            bad15.append("a-body-%d" % len(stale15["body"]))
        # ---- b: a face whose bytes move every render answers no false 304 --
        first15 = frame(port, "GET", "/")
        second15 = frame(port, "GET", "/")
        if first15["status"] != 200 or second15["status"] != 200:
            bad15.append("b-status-%d-%d" % (first15["status"],
                                             second15["status"]))
        if first15["etag"] == second15["etag"]:
            bad15.append("b-stable-etag-%r" % first15["etag"])
        again15 = frame(port, "GET", "/", {"If-None-Match": first15["etag"]})
        if again15["status"] != 200:
            bad15.append("b-false-304-%d" % again15["status"])
        # ---- c: /healthz is stable, so it answers its own validator --------
        hz15 = frame(port, "GET", "/healthz")
        hz304 = frame(port, "GET", "/healthz",
                      {"If-None-Match": hz15["etag"]})
        if hz304["status"] != 304 or hz304["length"] != "2" or hz304["body"]:
            bad15.append("c-304-%d-%r-%d" % (hz304["status"], hz304["length"],
                                             len(hz304["body"])))
        # ---- d: HEAD ignores Range and keeps the whole-face count ----------
        head_rng = frame(port, "HEAD", page15, {"Range": "bytes=0-9"})
        if head_rng["status"] != 200:
            bad15.append("d-status-%d" % head_rng["status"])
        if head_rng["length"] != plain15["length"]:
            bad15.append("d-length-%r-%r" % (head_rng["length"],
                                            plain15["length"]))
        if head_rng["crange"] or head_rng["body"]:
            bad15.append("d-crange-%r-body-%d" % (head_rng["crange"],
                                                  len(head_rng["body"])))
        # ---- e: the same HEAD under gzip describes the gzip representation -
        gz15 = frame(port, "GET", page15, {"Accept-Encoding": "gzip"})
        head_gz = frame(port, "HEAD", page15,
                        {"Range": "bytes=0-9", "Accept-Encoding": "gzip"})
        if gz15["coding"] != "gzip":
            bad15.append("e-get-coding-%r" % gz15["coding"])
        if head_gz["status"] != 200 or head_gz["crange"]:
            bad15.append("e-head-%d-%r" % (head_gz["status"],
                                           head_gz["crange"]))
        if head_gz["length"] != gz15["length"] or \
                head_gz["coding"] != "gzip":
            bad15.append("e-head-%r-%r" % (head_gz["length"],
                                           head_gz["coding"]))
        # ---- f: GET keeps its range semantics and its bytes ---------------
        got_rng = frame(port, "GET", page15, {"Range": "bytes=0-9"})
        if got_rng["status"] != 206 or got_rng["length"] != "10":
            bad15.append("f-range-%d-%r" % (got_rng["status"],
                                            got_rng["length"]))
        if got_rng["crange"] != "bytes 0-9/%s" % plain15["length"]:
            bad15.append("f-crange-%r" % got_rng["crange"])
        with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
            disk15 = handle.read()
        if plain15["body"] != disk15:
            bad15.append("f-bytes-%d-%d" % (len(plain15["body"]),
                                           len(disk15)))
        with io.open(MODULE, "rb") as handle:
            text15 = handle.read().decode("utf-8")
        for token15 in ("def _face(", "ignore_range", "content_length"):
            if token15 not in text15:
                bad15.append("f-missing-" + token15.split("(")[0]
                             .replace(" ", "-"))
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block15 = handle.read().split('"' + ROW + '"', 1)[-1][:220]
        if DECLARED_TAG not in block15:
            bad15.append("f-declared")

        # ===== AC-FDPV16: If-Range in both shapes RFC 9110 allows =========
        # R3475 measured before the edit (tmp/probe_if_range_date.py): the door
        # published Last-Modified, but _if_range_ok compared the header to the
        # ETag as a literal, so If-Range carrying the exact published date
        # answered the whole 55185-byte face where a 206 slice was asked for.
        bad16 = []
        page16 = "/preview/index.html"
        plain16 = cond(port, "GET", page16)
        size16 = len(plain16["body"])
        with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
            disk16 = handle.read()
        # ---- a: the published Last-Modified authorises the range ----------
        date16 = cond(port, "GET", page16,
                      {"Range": "bytes=0-9",
                       "If-Range": plain16["last_modified"]})
        if date16["status"] != 206 or \
                date16["crange"] != "bytes 0-9/%d" % size16:
            bad16.append("a-status-%d-%r" % (date16["status"],
                                             date16["crange"]))
        if date16["body"] != disk16[:10]:
            bad16.append("a-bytes-%d" % len(date16["body"]))
        # ---- b: a date older than the last change gives the whole face ----
        old16 = cond(port, "GET", page16,
                     {"Range": "bytes=0-9",
                      "If-Range": "Thu, 01 Jan 1970 00:00:00 GMT"})
        if old16["status"] != 200 or old16["crange"] or \
                old16["body"] != disk16:
            bad16.append("b-%d-%r-%d" % (old16["status"], old16["crange"],
                                         len(old16["body"])))
        # ---- c: a strong tag still resumes, a weak one never does ---------
        strong16 = cond(port, "GET", page16,
                        {"Range": "bytes=0-9",
                         "If-Range": plain16["etag"]})
        if strong16["status"] != 206 or strong16["body"] != disk16[:10]:
            bad16.append("c-strong-%d" % strong16["status"])
        weak16 = cond(port, "GET", page16,
                      {"Range": "bytes=0-9",
                       "If-Range": "W/" + plain16["etag"]})
        if weak16["status"] != 200 or weak16["body"] != disk16:
            bad16.append("c-weak-%d-%d" % (weak16["status"],
                                           len(weak16["body"])))
        # ---- d: a value in neither shape is ignored, never a 500 ----------
        junk16 = cond(port, "GET", page16,
                      {"Range": "bytes=0-9", "If-Range": "not a validator"})
        if junk16["status"] != 200 or junk16["body"] != disk16 or \
                junk16["ranges"] != "bytes":
            bad16.append("d-%d-%r-%d" % (junk16["status"], junk16["ranges"],
                                         len(junk16["body"])))
        # ---- e: "not modified since" is a <= test, and the order holds ----
        stamp16 = email.utils.parsedate_to_datetime(
            plain16["last_modified"])
        later16 = email.utils.formatdate(stamp16.timestamp() + 60,
                                         usegmt=True)
        soon16 = cond(port, "GET", page16,
                      {"Range": "bytes=0-9", "If-Range": later16})
        if soon16["status"] != 206 or soon16["body"] != disk16[:10]:
            bad16.append("e-later-%d" % soon16["status"])
        order16 = cond(port, "GET", page16,
                       {"Range": "bytes=0-9", "If-Range": later16,
                        "If-None-Match": plain16["etag"]})
        if order16["status"] != 304 or order16["body"]:
            bad16.append("e-order-%d-%d" % (order16["status"],
                                            len(order16["body"])))
        # ---- f: the module stays ASCII/LF, both shapes are wired ----------
        with io.open(MODULE, "rb") as handle:
            raw16 = handle.read()
        if raw16[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw16:
            bad16.append("f-module-dialect")
        try:
            text16 = raw16.decode("utf-8")
            text16.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad16.append("f-module-not-ascii")
            text16 = raw16.decode("utf-8", "replace")
        for token16 in ("def _if_range_ok(self, etag, last_modified)",
                        "self._if_range_ok(etag, last_modified)"):
            if token16 not in text16:
                bad16.append("f-missing-if-range-param")
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block16 = handle.read().split('"' + ROW + '"', 1)[-1][:220]
        if DECLARED_TAG not in block16:
            bad16.append("f-declared")

        # ===== AC-FDPV17: one Range header may name several segments ======
        # R3476 measured before the edit (tmp/probe_range_multi.py): seven
        # shapes -- two segments, three, four, a suffix second segment, a
        # second segment past the end, an all-past-end list and a malformed
        # segment -- all answered 200 with the whole 55185-byte face, so no
        # reader could take two slices in one answer.
        bad17 = []
        page17 = "/preview/index.html"
        with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
            disk17 = handle.read()
        size17 = len(disk17)
        plain17 = cond(port, "GET", page17)

        def parts17(blob, boundary):
            """Split one multipart/byteranges body into (fields, payload)."""
            edge = b"--" + boundary.encode("ascii")
            if not blob.startswith(edge + b"\r\n"):
                return None
            if not blob.endswith(b"\r\n" + edge + b"--\r\n"):
                return None
            inner = blob[len(edge) + 2:-(len(edge) + 6)]
            out = []
            for raw in inner.split(b"\r\n" + edge + b"\r\n"):
                head, _, payload = raw.partition(b"\r\n\r\n")
                fields = {}
                for line in head.decode("latin-1").split("\r\n"):
                    name, _, value = line.partition(":")
                    fields[name.strip().lower()] = value.strip()
                out.append((fields, payload))
            return out

        # ---- a: two segments answer 206 with their exact disk slices ------
        two17 = cond(port, "GET", page17,
                     {"Range": "bytes=0-9,20-29"})
        if two17["status"] != 206:
            bad17.append("a-status-%d" % two17["status"])
        elif "multipart/byteranges; boundary=" not in two17["ctype"]:
            bad17.append("a-ctype-%r" % two17["ctype"])
        else:
            bound17 = two17["ctype"].split("boundary=", 1)[1].strip()
            got17 = parts17(two17["body"], bound17)
            if got17 is None:
                bad17.append("a-framing")
            elif len(got17) != 2:
                bad17.append("a-parts-%d" % len(got17))
            else:
                wants17 = [("0-9", disk17[0:10]), ("20-29", disk17[20:30])]
                for (fields, payload), (span, want) in zip(got17, wants17):
                    if fields.get("content-range") != \
                            "bytes %s/%d" % (span, size17):
                        bad17.append("a-crange-%s-%r"
                                     % (span, fields.get("content-range")))
                    if fields.get("content-type") != plain17["ctype"]:
                        bad17.append("a-part-ctype-%s-%r"
                                     % (span, fields.get("content-type")))
                    if payload != want:
                        bad17.append("a-part-bytes-%s-%d"
                                     % (span, len(payload)))
            # ---- b: the framing is complete and the 206 names no total ----
            if two17["crange"]:
                bad17.append("b-top-crange-%r" % two17["crange"])
            expect17 = (b"--" + bound17.encode("ascii") + b"\r\n")
            expect17 += ("Content-Type: " + plain17["ctype"] + "\r\n"
                         ).encode("ascii")
            expect17 += ("Content-Range: bytes 0-9/%d\r\n\r\n" % size17
                         ).encode("ascii")
            expect17 += disk17[0:10]
            expect17 += b"\r\n--" + bound17.encode("ascii") + b"\r\n"
            expect17 += ("Content-Type: " + plain17["ctype"] + "\r\n"
                         ).encode("ascii")
            expect17 += ("Content-Range: bytes 20-29/%d\r\n\r\n" % size17
                         ).encode("ascii")
            expect17 += disk17[20:30]
            expect17 += b"\r\n--" + bound17.encode("ascii") + b"--\r\n"
            if two17["body"] != expect17:
                bad17.append("b-wire-%d-%d" % (len(two17["body"]),
                                               len(expect17)))
            if bound17.encode("ascii") in disk17:
                bad17.append("b-boundary-in-payload")
        # ---- c: three segments answer, a fourth falls back ----------------
        three17 = cond(port, "GET", page17,
                       {"Range": "bytes=0-9,20-29,40-49"})
        if three17["status"] != 206 or \
                "multipart/byteranges; boundary=" not in three17["ctype"]:
            bad17.append("c-three-%d-%r" % (three17["status"],
                                            three17["ctype"]))
        else:
            b317 = three17["ctype"].split("boundary=", 1)[1].strip()
            p317 = parts17(three17["body"], b317)
            if p317 is None or len(p317) != 3:
                bad17.append("c-three-parts-%r"
                             % (None if p317 is None else len(p317)))
            elif [payload for _fields, payload in p317] != \
                    [disk17[0:10], disk17[20:30], disk17[40:50]]:
                bad17.append("c-three-bytes")
        four17 = cond(port, "GET", page17,
                      {"Range": "bytes=0-9,20-29,40-49,60-69"})
        if four17["status"] != 200 or four17["body"] != disk17 or \
                "multipart" in four17["ctype"]:
            bad17.append("c-four-%d-%r-%d" % (four17["status"],
                                              four17["ctype"],
                                              len(four17["body"])))
        # ---- d: If-Range still guards the list ---------------------------
        stale17 = cond(port, "GET", page17,
                       {"Range": "bytes=0-9,20-29",
                        "If-Range": "Thu, 01 Jan 1970 00:00:00 GMT"})
        if stale17["status"] != 200 or stale17["body"] != disk17 or \
                "multipart" in stale17["ctype"]:
            bad17.append("d-stale-%d-%d" % (stale17["status"],
                                            len(stale17["body"])))
        weak17 = cond(port, "GET", page17,
                      {"Range": "bytes=0-9,20-29",
                       "If-Range": "W/" + plain17["etag"]})
        if weak17["status"] != 200 or weak17["body"] != disk17:
            bad17.append("d-weak-%d-%d" % (weak17["status"],
                                           len(weak17["body"])))
        fresh17 = cond(port, "GET", page17,
                       {"Range": "bytes=0-9,20-29",
                        "If-Range": plain17["last_modified"]})
        if fresh17["status"] != 206:
            bad17.append("d-fresh-%d" % fresh17["status"])
        # ---- e: a past-end segment is dropped, all-past-end is 416 -------
        drop17 = cond(port, "GET", page17,
                      {"Range": "bytes=0-9,999999-"})
        if drop17["status"] != 206 or \
                drop17["crange"] != "bytes 0-9/%d" % size17 or \
                drop17["body"] != disk17[:10]:
            bad17.append("e-drop-%d-%r-%d" % (drop17["status"],
                                               drop17["crange"],
                                               len(drop17["body"])))
        none17 = cond(port, "GET", page17,
                      {"Range": "bytes=999999-,9999990-"})
        if none17["status"] != 416 or \
                none17["crange"] != "bytes */%d" % size17 or none17["body"]:
            bad17.append("e-416-%d-%r-%d" % (none17["status"],
                                             none17["crange"],
                                             len(none17["body"])))
        junk17 = cond(port, "GET", page17,
                      {"Range": "bytes=0-9,zz"})
        if junk17["status"] != 200 or junk17["body"] != disk17:
            bad17.append("e-junk-%d-%d" % (junk17["status"],
                                           len(junk17["body"])))
        # ---- f: nothing already delivered moved, dialect holds -----------
        single17 = cond(port, "GET", page17, {"Range": "bytes=0-9"})
        if single17["status"] != 206 or single17["body"] != disk17[:10] or \
                single17["crange"] != "bytes 0-9/%d" % size17:
            bad17.append("f-single-%d-%r" % (single17["status"],
                                             single17["crange"]))
        whole17 = cond(port, "GET", page17)
        if whole17["status"] != 200 or whole17["body"] != disk17:
            bad17.append("f-whole-%d-%d" % (whole17["status"],
                                            len(whole17["body"])))
        head17 = cond(port, "HEAD", page17,
                      {"Range": "bytes=0-9,20-29"})
        if head17["status"] != 200 or head17["body"] or \
                head17["length"] != str(size17):
            bad17.append("f-head-%d-%r-%d" % (head17["status"],
                                              head17["length"],
                                              len(head17["body"])))
        with io.open(MODULE, "rb") as handle:
            raw17 = handle.read()
        if raw17[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw17:
            bad17.append("f-module-dialect")
        try:
            text17 = raw17.decode("utf-8")
            text17.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad17.append("f-module-not-ascii")
            text17 = raw17.decode("utf-8", "replace")
        for token17 in ("RANGE_MAX_SEGMENTS = 3",
                        "def _parse_ranges(header, size)",
                        "def _multipart_ranges(spans, ctype, size, boundary, "
                        "body)"):
            if token17 not in text17:
                bad17.append("f-missing-%s" % token17.split("(")[0].strip())
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block17 = handle.read().split('"' + ROW + '"', 1)[-1][:220]
        if DECLARED_TAG not in block17:
            bad17.append("f-declared")
        # R3477 measured before the edit (tmp/probe_range_merge.py): overlap,
        # adjacency, reversed order and full containment each answered two
        # parts, so the bytes inside an overlap travelled twice and the
        # answer's byte set did not match the asked union.
        bad18 = []
        page18 = "/preview/index.html"
        with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
            disk18 = handle.read()
        size18 = len(disk18)
        plain18 = cond(port, "GET", page18)

        def merged18(value):
            """One list; the single-part answer the merge law predicts."""
            return cond(port, "GET", page18, {"Range": value})

        # ---- a: an overlapping pair becomes one slice ---------------------
        over18 = merged18("bytes=0-9,5-14")
        if over18["status"] != 206 or "multipart" in over18["ctype"]:
            bad18.append("a-kind-%d-%r" % (over18["status"],
                                           over18["ctype"]))
        elif over18["crange"] != "bytes 0-14/%d" % size18:
            bad18.append("a-crange-%r" % over18["crange"])
        elif over18["body"] != disk18[0:15]:
            bad18.append("a-bytes-%d" % len(over18["body"]))
        # ---- b: two sides of one boundary become one slice ----------------
        next18 = merged18("bytes=0-9,10-19")
        if next18["status"] != 206 or "multipart" in next18["ctype"] or \
                next18["crange"] != "bytes 0-19/%d" % size18 or \
                next18["body"] != disk18[0:20]:
            bad18.append("b-adjacent-%d-%r-%d" % (next18["status"],
                                                   next18["crange"],
                                                   len(next18["body"])))
        # ---- c: a contained segment adds no byte, either order ------------
        nest18 = merged18("bytes=0-9,0-4")
        if nest18["status"] != 206 or "multipart" in nest18["ctype"] or \
                nest18["crange"] != "bytes 0-9/%d" % size18 or \
                nest18["body"] != disk18[:10]:
            bad18.append("c-nested-%d-%r-%d" % (nest18["status"],
                                                nest18["crange"],
                                                len(nest18["body"])))
        back18 = merged18("bytes=0-4,0-9")
        if back18["status"] != 206 or "multipart" in back18["ctype"] or \
                back18["crange"] != "bytes 0-9/%d" % size18 or \
                back18["body"] != disk18[:10]:
            bad18.append("c-nested-back-%d-%r-%d"
                         % (back18["status"], back18["crange"],
                            len(back18["body"])))
        # ---- d: an unordered list merges and answers in byte order --------
        mixed18 = merged18("bytes=20-29,0-9,25-40")
        if mixed18["status"] != 206 or \
                "multipart/byteranges; boundary=" not in mixed18["ctype"]:
            bad18.append("d-kind-%d-%r" % (mixed18["status"],
                                           mixed18["ctype"]))
        else:
            bound18 = mixed18["ctype"].split("boundary=", 1)[1].strip()
            got18 = parts17(mixed18["body"], bound18)
            wants18 = [("bytes 0-9/%d" % size18, disk18[0:10]),
                       ("bytes 20-40/%d" % size18, disk18[20:41])]
            if got18 is None:
                bad18.append("d-framing")
            elif len(got18) != 2:
                bad18.append("d-parts-%d" % len(got18))
            else:
                for (fields, payload), (want, body18) in zip(got18, wants18):
                    if fields.get("content-range") != want:
                        bad18.append("d-crange-%r" % fields.get("content-range"))
                    if payload != body18:
                        bad18.append("d-bytes-%d" % len(payload))
                if b"".join(pl for _f, pl in got18) != \
                        disk18[0:10] + disk18[20:41]:
                    bad18.append("d-union")
        # ---- e: nothing already delivered moved --------------------------
        two18 = cond(port, "GET", page18, {"Range": "bytes=0-9,20-29"})
        if two18["status"] != 206 or \
                "multipart/byteranges; boundary=" not in two18["ctype"]:
            bad18.append("e-two-%d-%r" % (two18["status"], two18["ctype"]))
        else:
            b218 = two18["ctype"].split("boundary=", 1)[1].strip()
            p218 = parts17(two18["body"], b218)
            if p218 is None or [pl for _f, pl in p218] != \
                    [disk18[0:10], disk18[20:30]]:
                bad18.append("e-two-parts-%r"
                             % (None if p218 is None else len(p218)))
        four18 = merged18("bytes=0-9,20-29,40-49,60-69")
        if four18["status"] != 200 or four18["body"] != disk18:
            bad18.append("e-four-%d-%d" % (four18["status"],
                                           len(four18["body"])))
        drop18 = merged18("bytes=0-9,999999-")
        if drop18["status"] != 206 or \
                drop18["crange"] != "bytes 0-9/%d" % size18 or \
                drop18["body"] != disk18[:10]:
            bad18.append("e-drop-%d-%r" % (drop18["status"],
                                           drop18["crange"]))
        none18 = merged18("bytes=999999-,9999990-")
        if none18["status"] != 416 or \
                none18["crange"] != "bytes */%d" % size18:
            bad18.append("e-416-%d-%r" % (none18["status"],
                                          none18["crange"]))
        stale18 = cond(port, "GET", page18,
                       {"Range": "bytes=0-9,5-14",
                        "If-Range": "Thu, 01 Jan 1970 00:00:00 GMT"})
        if stale18["status"] != 200 or stale18["body"] != disk18:
            bad18.append("e-stale-%d-%d" % (stale18["status"],
                                            len(stale18["body"])))
        head18 = cond(port, "HEAD", page18, {"Range": "bytes=0-9,5-14"})
        if head18["status"] != 200 or head18["body"] or \
                head18["length"] != str(size18):
            bad18.append("e-head-%d-%r" % (head18["status"],
                                           head18["length"]))
        # ---- f: dialect, tokens on disk, declared count -------------------
        with io.open(MODULE, "rb") as handle:
            raw18 = handle.read()
        if raw18[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw18:
            bad18.append("f-module-dialect")
        try:
            text18 = raw18.decode("utf-8")
            text18.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad18.append("f-module-not-ascii")
            text18 = raw18.decode("utf-8", "replace")
        for token18 in ("def _merge_spans(spans)",
                        "RANGE_MAX_SEGMENTS = 3"):
            if token18 not in text18:
                bad18.append("f-missing-%s" % token18.split("(")[0].strip())
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block18 = handle.read().split('"' + ROW + '"', 1)[-1][:220]
        if DECLARED_TAG not in block18:
            bad18.append("f-declared")
        # R3478 measured before the edit (tmp/probe-R3478.py): two Range lines
        # answered only the first line's slice -- lines naming 0-9 and 20-29
        # returned 206 bytes 0-9 while the same-shaped single line returned
        # two parts, and a 4-segment pair returned 206 two parts. Range is a
        # single ranges-specifier, not a list field, so two lines cannot be
        # joined; the door now ignores a repeated Range and serves the whole
        # representation instead of executing half of a message it could not
        # interpret.
        bad19 = []
        page19 = "/preview/index.html"
        with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
            disk19 = handle.read()
        size19 = len(disk19)

        def repeat19(lines, extra=()):
            """One raw request carrying several Range lines, in order."""
            payload = ["GET " + page19 + " HTTP/1.1", "Host: 127.0.0.1"]
            payload.extend(lines)
            payload.extend(extra)
            payload.extend(["Connection: close", "", ""])
            blob = raw_request(port, "\r\n".join(payload).encode("latin-1"))
            return wire_reply(blob)

        # ---- a: two lines naming different spans answer the whole face ----
        for tag19, lines19 in (
                ("a-apart", ["Range: bytes=0-9", "Range: bytes=20-29"]),
                ("b-overlap", ["Range: bytes=0-9", "Range: bytes=5-14"]),
                ("c-four", ["Range: bytes=0-9,20-29",
                            "Range: bytes=40-49,60-69"]),
                ("d-past", ["Range: bytes=0-9", "Range: bytes=999999-"]),
                ("d-bad", ["Range: bytes=0-9", "Range: bytes=zz"]),
                ("d-none", ["Range: bytes=999999-", "Range: bytes=999998-"])):
            status19, fields19, body19 = repeat19(lines19)
            if status19.split(" ")[1] != "200" or body19 != disk19 or \
                    fields19.get("content-range") or \
                    "multipart" in (fields19.get("content-type") or ""):
                bad19.append("%s-%r-%d" % (tag19, status19, len(body19)))
        # ---- e: nothing already delivered moved --------------------------
        single19 = cond(port, "GET", page19, {"Range": "bytes=0-9"})
        if single19["status"] != 206 or single19["body"] != disk19[:10] or \
                single19["crange"] != "bytes 0-9/%d" % size19:
            bad19.append("e-single-%d-%r" % (single19["status"],
                                             single19["crange"]))
        two19 = cond(port, "GET", page19, {"Range": "bytes=0-9,20-29"})
        if two19["status"] != 206 or \
                "multipart/byteranges; boundary=" not in two19["ctype"]:
            bad19.append("e-two-%d-%r" % (two19["status"], two19["ctype"]))
        else:
            b19 = two19["ctype"].split("boundary=", 1)[1].strip()
            p19 = parts17(two19["body"], b19)
            if p19 is None or [pl for _f, pl in p19] != \
                    [disk19[0:10], disk19[20:30]]:
                bad19.append("e-two-parts")
        over19 = cond(port, "GET", page19, {"Range": "bytes=0-9,5-14"})
        if over19["status"] != 206 or \
                over19["crange"] != "bytes 0-14/%d" % size19 or \
                over19["body"] != disk19[:15]:
            bad19.append("e-overlap-%d-%r" % (over19["status"],
                                              over19["crange"]))
        four19 = cond(port, "GET", page19,
                      {"Range": "bytes=0-9,20-29,40-49,60-69"})
        if four19["status"] != 200 or four19["body"] != disk19:
            bad19.append("e-four-%d-%d" % (four19["status"],
                                           len(four19["body"])))
        none19 = cond(port, "GET", page19,
                      {"Range": "bytes=999999-,9999990-"})
        if none19["status"] != 416 or \
                none19["crange"] != "bytes */%d" % size19:
            bad19.append("e-416-%d-%r" % (none19["status"],
                                          none19["crange"]))
        stale19 = cond(port, "GET", page19,
                       {"Range": "bytes=0-9",
                        "If-Range": "Thu, 01 Jan 1970 00:00:00 GMT"})
        if stale19["status"] != 200 or stale19["body"] != disk19:
            bad19.append("e-stale-%d-%d" % (stale19["status"],
                                            len(stale19["body"])))
        head19 = cond(port, "HEAD", page19, {"Range": "bytes=0-9"})
        if head19["status"] != 200 or head19["body"] or \
                head19["length"] != str(size19):
            bad19.append("e-head-%d-%r" % (head19["status"],
                                           head19["length"]))
        # a repeated Range must not silently disable negotiation either
        gz19 = repeat19(["Range: bytes=0-9", "Range: bytes=20-29"],
                        ["Accept-Encoding: gzip"])
        if gz19[0].split(" ")[1] != "200" or \
                (gz19[1].get("content-encoding") or "") != "gzip":
            bad19.append("e-gzip-%r-%r" % (gz19[0],
                                           gz19[1].get("content-encoding")))
        onegz19 = cond(port, "GET", page19,
                       {"Range": "bytes=0-9", "Accept-Encoding": "gzip"})
        if onegz19["status"] != 206 or onegz19["body"] != disk19[:10]:
            bad19.append("e-one-gzip-%d-%d" % (onegz19["status"],
                                               len(onegz19["body"])))
        # ---- f: dialect, tokens on disk, declared count -------------------
        with io.open(MODULE, "rb") as handle:
            raw19 = handle.read()
        if raw19[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw19:
            bad19.append("f-module-dialect")
        try:
            text19 = raw19.decode("utf-8")
            text19.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad19.append("f-module-not-ascii")
            text19 = raw19.decode("utf-8", "replace")
        for token19 in ("def _range_header(headers)",
                        "RANGE_MAX_SEGMENTS = 3",
                        "_range_header(self.headers)"):
            if token19 not in text19:
                bad19.append("f-missing-%s" % token19.split("(")[0].strip())
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block19 = handle.read().split('"' + ROW + '"', 1)[-1][:220]
        if DECLARED_TAG not in block19:
            bad19.append("f-declared")
        # R3479 measured before the edit (tmp/probe-R3479.py, thirteen raw
        # shapes): every conditional field reached the door through
        # self.headers.get, so only the first line spoke. If-Match lined up as
        # miss-then-hit answered 412 while the reader's second tag was current;
        # If-None-Match as miss-then-hit sent all 55185 bytes the reader
        # already held; a repeated If-Modified-Since answered 304 and a
        # repeated If-Unmodified-Since answered 412 on the first line alone;
        # a repeated If-Range still authorised a 10-byte slice. The list fields
        # (If-Match, If-None-Match) are now combined into one comma value, the
        # single-value fields are dropped whole, and a repeated If-Range
        # refuses the range so no slice is spliced onto an unknown prefix.
        bad20 = []
        page20 = "/preview/index.html"
        with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
            disk20 = handle.read()
        size20 = len(disk20)
        base20 = cond(port, "GET", page20)
        etag20 = base20["etag"]
        mod20 = base20["last_modified"]
        old20 = "Thu, 01 Jan 1970 00:00:00 GMT"
        miss20 = '"notthisone"'

        def repeat20(lines, extra=()):
            """One raw request carrying several conditional lines, in order."""
            payload = ["GET " + page20 + " HTTP/1.1", "Host: 127.0.0.1"]
            payload.extend(lines)
            payload.extend(extra)
            payload.extend(["Connection: close", "", ""])
            blob = raw_request(port, "\r\n".join(payload).encode("latin-1"))
            return wire_reply(blob)

        if not etag20 or not mod20 or base20["status"] != 200 or \
                base20["body"] != disk20:
            bad20.append("base-%r" % base20["status"])
        # ---- a: If-Match is a list field, so the lines are one list -------
        for tag20, lines20, want20 in (
                ("a-miss-hit", ["If-Match: " + miss20, "If-Match: " + etag20],
                 "200"),
                ("a-hit-miss", ["If-Match: " + etag20, "If-Match: " + miss20],
                 "200"),
                ("a-hit-hit", ["If-Match: " + etag20, "If-Match: " + etag20],
                 "200"),
                ("a-miss-miss", ["If-Match: " + miss20,
                                 "If-Match: " + miss20], "412")):
            status20, fields20, body20 = repeat20(lines20)
            got20 = status20.split(" ")[1]
            if got20 != want20:
                bad20.append("%s-%s" % (tag20, got20))
            elif want20 == "200" and body20 != disk20:
                bad20.append("%s-body-%d" % (tag20, len(body20)))
        # ---- b: If-None-Match is a list field too -------------------------
        for tag20, lines20, want20 in (
                ("b-miss-hit", ["If-None-Match: " + miss20,
                                "If-None-Match: " + etag20], "304"),
                ("b-hit-miss", ["If-None-Match: " + etag20,
                                "If-None-Match: " + miss20], "304"),
                ("b-hit-hit", ["If-None-Match: " + etag20,
                               "If-None-Match: " + etag20], "304"),
                ("b-miss-miss", ["If-None-Match: " + miss20,
                                 "If-None-Match: " + miss20], "200")):
            status20, fields20, body20 = repeat20(lines20)
            got20 = status20.split(" ")[1]
            if got20 != want20:
                bad20.append("%s-%s" % (tag20, got20))
            elif want20 == "304" and body20:
                bad20.append("%s-body-%d" % (tag20, len(body20)))
            elif want20 == "200" and body20 != disk20:
                bad20.append("%s-body-%d" % (tag20, len(body20)))
        # ---- c: a repeated date is dropped whole, never half-executed -----
        for tag20, lines20 in (
                ("c-ims-mod-old", ["If-Modified-Since: " + mod20,
                                   "If-Modified-Since: " + old20]),
                ("c-ims-old-mod", ["If-Modified-Since: " + old20,
                                   "If-Modified-Since: " + mod20]),
                ("c-ius-old-mod", ["If-Unmodified-Since: " + old20,
                                   "If-Unmodified-Since: " + mod20]),
                ("c-ius-mod-old", ["If-Unmodified-Since: " + mod20,
                                   "If-Unmodified-Since: " + old20])):
            status20, fields20, body20 = repeat20(lines20)
            if status20.split(" ")[1] != "200" or body20 != disk20:
                bad20.append("%s-%r-%d" % (tag20, status20, len(body20)))
        # ---- d: a repeated If-Range refuses the range ---------------------
        for tag20, lines20 in (
                ("d-hit-old", ["If-Range: " + etag20, "If-Range: " + old20,
                               "Range: bytes=0-9"]),
                ("d-old-hit", ["If-Range: " + old20, "If-Range: " + etag20,
                               "Range: bytes=0-9"]),
                ("d-hit-hit", ["If-Range: " + etag20, "If-Range: " + etag20,
                               "Range: bytes=0-9"])):
            status20, fields20, body20 = repeat20(lines20)
            if status20.split(" ")[1] != "200" or body20 != disk20 or \
                    fields20.get("content-range") or \
                    "multipart" in (fields20.get("content-type") or ""):
                bad20.append("%s-%r-%d" % (tag20, status20, len(body20)))
        # ---- e: every single-line answer still reads as it did ------------
        single20 = (
                ("e-im-hit", {"If-Match": etag20}, 200, size20),
                ("e-im-miss", {"If-Match": miss20}, 412, None),
                ("e-inm-hit", {"If-None-Match": etag20}, 304, 0),
                ("e-inm-miss", {"If-None-Match": miss20}, 200, size20),
                ("e-ims-mod", {"If-Modified-Since": mod20}, 304, 0),
                ("e-ims-old", {"If-Modified-Since": old20}, 200, size20),
                ("e-ius-old", {"If-Unmodified-Since": old20}, 412, None),
                ("e-ius-mod", {"If-Unmodified-Since": mod20}, 200, size20),
                ("e-ir-hit", {"If-Range": etag20, "Range": "bytes=0-9"},
                 206, 10),
                ("e-ir-old", {"If-Range": old20, "Range": "bytes=0-9"},
                 200, size20))
        for tag20, headers20, want20, size_want in single20:
            got20 = cond(port, "GET", page20, headers20)
            if got20["status"] != want20:
                bad20.append("%s-%d" % (tag20, got20["status"]))
            elif size_want is not None and len(got20["body"]) != size_want:
                bad20.append("%s-len-%d" % (tag20, len(got20["body"])))
            elif tag20 == "e-ir-hit" and \
                    got20["crange"] != "bytes 0-9/%d" % size20:
                bad20.append("%s-crange-%r" % (tag20, got20["crange"]))
        two20 = cond(port, "GET", page20, {"Range": "bytes=0-9,20-29"})
        if two20["status"] != 206 or \
                "multipart/byteranges; boundary=" not in two20["ctype"]:
            bad20.append("e-two-%d-%r" % (two20["status"], two20["ctype"]))
        # ---- f: dialect, tokens on disk, declared count -------------------
        with io.open(MODULE, "rb") as handle:
            raw20h = handle.read()
        if raw20h[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw20h:
            bad20.append("f-module-dialect")
        try:
            text20 = raw20h.decode("utf-8")
            text20.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad20.append("f-module-not-ascii")
            text20 = raw20h.decode("utf-8", "replace")
        for token20 in ("def _list_header(headers, name)",
                        "def _single_line(headers, name)",
                        '_list_header(self.headers, "If-Match")',
                        '_list_header(self.headers, "If-None-Match")',
                        '_single_line(self.headers,\n                                             "If-Modified-Since")',
                        '_single_line(self.headers,\n                                             "If-Unmodified-Since")',
                        'self.headers.get_all("If-Range")'):
            if token20 not in text20:
                bad20.append("f-missing-%s" % token20.split("(")[0].strip()[:18])
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block20r = handle.read().split('"' + ROW + '"', 1)[-1][:220]
        if DECLARED_TAG not in block20r:
            bad20.append("f-declared")
        # R3480 measured before the edit (tmp/probe-R3480.py, eight raw
        # shapes): Accept-Encoding reached the door through
        # self.headers.get, so only the first line spoke. gzip named only on
        # the second line answered identity; a q=0 on the second line still
        # answered gzip the reader had refused; a wildcard on the second line
        # was ignored. The lines are one coding list (RFC 9110 sec.5.3), so
        # the door joins them and grades the joined list once.
        bad21 = []
        page21 = "/preview/index.html"
        with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
            disk21 = handle.read()
        size21 = len(disk21)

        def coding21(lines, extra=()):
            """One raw request carrying its own Accept-Encoding lines."""
            payload = ["GET " + page21 + " HTTP/1.1", "Host: 127.0.0.1"]
            payload.extend(lines)
            payload.extend(extra)
            payload.extend(["Connection: close", "", ""])
            blob = raw_request(port, "\r\n".join(payload).encode("latin-1"))
            status21, fields21, body21 = wire_reply(blob)
            return status21, fields21, body21

        def lines21(*values):
            return ["Accept-Encoding: " + value for value in values]

        def graded21(tag21, status21, fields21, body21):
            """A 200 body that is either the gzip of disk or the disk bytes."""
            if status21.split(" ")[1] != "200":
                bad21.append("%s-%s" % (tag21, status21.split(" ")[1]))
                return
            if fields21.get("content-encoding") == "gzip":
                try:
                    if gzip.decompress(body21) != disk21:
                        bad21.append("%s-gunzip-bytes" % tag21)
                except Exception:  # noqa: BLE001
                    bad21.append("%s-gunzip" % tag21)
            elif body21 != disk21:
                bad21.append("%s-bytes-%d" % (tag21, len(body21)))

        # ---- a: two coding lines are one list -----------------------------
        for tag21, values21 in (("a-id-gz", ("identity", "gzip")),
                                ("a-br-gz", ("br", "gzip")),
                                ("a-gz-id", ("gzip", "identity"))):
            status21, fields21, body21 = coding21(lines21(*values21))
            if fields21.get("content-encoding") != "gzip":
                bad21.append("%s-coding-%r" % (tag21,
                                               fields21.get("content-encoding")))
            graded21(tag21, status21, fields21, body21)
        # ---- b: an explicit token beats the wildcard, q=0 included --------
        status21, fields21, body21 = coding21(lines21("*", "gzip;q=0"))
        if status21.split(" ")[1] != "200" or body21 != disk21 or \
                fields21.get("content-encoding"):
            bad21.append("b-star-refused-%s-%d" % (status21.split(" ")[1],
                                                   len(body21)))
        status21, fields21, body21 = coding21(lines21("gzip;q=0", "gzip"))
        if status21.split(" ")[1] != "200" or \
                fields21.get("content-encoding") != "gzip":
            bad21.append("b-heaviest-gzip-%r" % fields21.get("content-encoding"))
        graded21("b-heaviest", status21, fields21, body21)
        # ---- c: a wildcard on any line accepts gzip ------------------------
        status21, fields21, body21 = coding21(lines21("identity", "*"))
        if status21.split(" ")[1] != "200" or \
                fields21.get("content-encoding") != "gzip":
            bad21.append("c-star-%r" % fields21.get("content-encoding"))
        graded21("c-star", status21, fields21, body21)
        # ---- d: a refusal is still a refusal, on any line ------------------
        for tag21, values21 in (("d-id-gz0", ("identity", "gzip;q=0")),
                                ("d-gz0-gz0", ("gzip;q=0", "gzip;q=0")),
                                ("d-single-gz0", ("gzip;q=0",))):
            status21, fields21, body21 = coding21(lines21(*values21))
            if status21.split(" ")[1] != "200" or body21 != disk21 or \
                    fields21.get("content-encoding"):
                bad21.append("%s-%s-%r-%d" % (tag21, status21.split(" ")[1],
                                              fields21.get("content-encoding"),
                                              len(body21)))
        # ---- e: every single-line answer still reads as it did ------------
        for tag21, values21, want21 in (("e-gz", ("gzip",), "gzip"),
                                        ("e-gz-half", ("gzip;q=0.5",), "gzip"),
                                        ("e-star", ("*",), "gzip"),
                                        ("e-id", ("identity",), ""),
                                        ("e-br", ("br",), ""),
                                        ("e-none", (), "")):
            status21, fields21, body21 = coding21(lines21(*values21))
            if status21.split(" ")[1] != "200" or \
                    (fields21.get("content-encoding") or "") != want21:
                bad21.append("%s-%r-%r" % (tag21, status21.split(" ")[1],
                                           fields21.get("content-encoding")))
            elif "accept-encoding" not in (fields21.get("vary") or "").lower():
                bad21.append("%s-vary" % tag21)
            graded21(tag21, status21, fields21, body21)
        status21, fields21, body21 = coding21(
            lines21("gzip", "identity"), ("Range: bytes=0-9",))
        if status21.split(" ")[1] != "206" or body21 != disk21[:10] or \
                fields21.get("content-encoding"):
            bad21.append("e-range-%s-%d-%r" % (status21.split(" ")[1],
                                               len(body21),
                                               fields21.get("content-encoding")))
        # ---- f: dialect, tokens on disk, declared count -------------------
        with io.open(MODULE, "rb") as handle:
            raw21 = handle.read()
        if raw21[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw21:
            bad21.append("f-module-dialect")
        try:
            text21 = raw21.decode("utf-8")
            text21.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad21.append("f-module-not-ascii")
            text21 = raw21.decode("utf-8", "replace")
        if '_list_header(self.headers, "Accept-Encoding")' not in text21:
            bad21.append("f-missing-listreader")
        if 'self.headers.get("Accept-Encoding")' in text21:
            bad21.append("f-old-reader")
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block21r = handle.read().split('"' + ROW + '"', 1)[-1][:220]
        if DECLARED_TAG not in block21r:
            bad21.append("f-declared")
        # R3481 measured before the edit (tmp/probe-R3481.py, seventeen raw
        # shapes): Transfer-Encoding and Connection reached the door through
        # self.headers.get, so only the first line spoke. "chunked" followed
        # by "gzip" answered 200 although the final coding was not chunked;
        # "gzip" followed by "chunked" answered 200 although this door cannot
        # decode gzip; and a Connection list saying close on its second line
        # left the connection open. Both fields are comma lists (RFC 9110
        # sec.5.3), so the door now joins the lines and grades the list once.
        bad22 = []
        page22 = "/preview/index.html"
        with io.open(os.path.join(PREVIEW, "index.html"), "rb") as handle:
            disk22 = handle.read()

        def framed22(lines):
            """One raw request with its own framing lines, graded on the wire."""
            payload = ["GET " + page22 + " HTTP/1.1", "Host: 127.0.0.1"]
            payload.extend(lines)
            payload.extend(["Connection: close", "", ""])
            return wire_reply(raw_request(
                port, "\r\n".join(payload).encode("latin-1")))

        # ---- a: two coding lines are one list, and gzip needs 501 ---------
        for tag22, lines22 in (
                ("a-split", ["Transfer-Encoding: gzip",
                             "Transfer-Encoding: chunked"]),
                ("a-one-line", ["Transfer-Encoding: gzip, chunked"])):
            status22, fields22, body22 = framed22(lines22)
            if " 501 " not in status22:
                bad22.append("%s-%r" % (tag22, status22))
            elif b"501" not in body22:
                bad22.append("%s-body" % tag22)
            elif fields22.get("connection", "").lower() != "close":
                bad22.append("%s-close-%r" % (tag22,
                                              fields22.get("connection")))
        # ---- b: a list whose final coding is not chunked is a 400 ---------
        for tag22, lines22 in (
                ("b-split", ["Transfer-Encoding: chunked",
                             "Transfer-Encoding: gzip"]),
                ("b-one-line", ["Transfer-Encoding: chunked, gzip"]),
                ("b-no-chunked", ["Transfer-Encoding: gzip"]),
                ("b-empty", ["Transfer-Encoding:"])):
            status22, fields22, body22 = framed22(lines22)
            if " 400 " not in status22:
                bad22.append("%s-%r" % (tag22, status22))
            elif fields22.get("connection", "").lower() != "close":
                bad22.append("%s-close-%r" % (tag22,
                                              fields22.get("connection")))
        # ---- c: every delivered framing answer still reads as it did ------
        status22, fields22, body22 = framed22(["Transfer-Encoding: chunked"])
        if " 200 " not in status22 or body22 != disk22:
            bad22.append("c-chunked-%r-%d" % (status22, len(body22)))
        elif fields22.get("connection", "").lower() != "close":
            bad22.append("c-chunked-close-%r" % fields22.get("connection"))
        for tag22, lines22 in (
                ("c-cl", ["Transfer-Encoding: chunked",
                          "Content-Length: 5"]),
                ("c-cl-split", ["Transfer-Encoding: gzip",
                                "Transfer-Encoding: chunked",
                                "Content-Length: 5"])):
            status22, fields22, body22 = framed22(lines22)
            if " 400 " not in status22 or \
                    b"conflicting body framing" not in body22:
                bad22.append("%s-%r" % (tag22, status22))
        status22, fields22, _body22 = framed22(
            ["Transfer-Encoding: chunked, gzip"])
        if fields22.get("x-content-type-options") != "nosniff" or \
                "camera=()" not in (fields22.get("permissions-policy")
                                    or "") or \
                fields22.get("server") != "BigDomain":
            bad22.append("c-policy")

        def dialog22(conn_lines, requests=2, version="HTTP/1.1",
                     timeout=6.0):
            """One socket, one framed answer read per request."""
            sock22 = socket.create_connection(("127.0.0.1", port),
                                              timeout=timeout)
            sock22.settimeout(timeout)
            got22 = []
            try:
                for _ in range(requests):
                    payload22 = ["GET /healthz " + version,
                                 "Host: 127.0.0.1"]
                    payload22.extend(conn_lines)
                    payload22.extend(["", ""])
                    try:
                        sock22.sendall(
                            "\r\n".join(payload22).encode("latin-1"))
                        buf22 = b""
                        while b"\r\n\r\n" not in buf22:
                            chunk22 = sock22.recv(65536)
                            if not chunk22:
                                break
                            buf22 += chunk22
                        if b"\r\n\r\n" not in buf22:
                            got22.append(b"eof")
                            break
                        head22, _, rest22 = buf22.partition(b"\r\n\r\n")
                        length22 = 0
                        for line22 in head22.split(b"\r\n")[1:]:
                            name22, _, value22 = line22.partition(b":")
                            if name22.strip().lower() == b"content-length":
                                length22 = int(value22.strip())
                        while len(rest22) < length22:
                            chunk22 = sock22.recv(65536)
                            if not chunk22:
                                break
                            rest22 += chunk22
                        got22.append(head22 + b"\r\n\r\n" + rest22)
                    except OSError:
                        got22.append(b"transport")
                        break
            finally:
                sock22.close()
            return got22

        def head22(one22):
            return one22.split(b"\r\n\r\n", 1)[0].lower()

        # ---- d: two Connection lines are one list, and close anywhere -----
        for tag22, lines22 in (
                ("d-keep-close", ["Connection: keep-alive",
                                  "Connection: close"]),
                ("d-close-keep", ["Connection: close",
                                  "Connection: keep-alive"]),
                ("d-one-line", ["Connection: keep-alive, close"])):
            answers22 = dialog22(lines22)
            if len(answers22) != 2:
                bad22.append("%s-count-%d" % (tag22, len(answers22)))
            elif not answers22[0].startswith(b"HTTP/1.1 200 OK"):
                bad22.append("%s-status-%r" % (tag22, answers22[0][:18]))
            elif b"connection: close" not in head22(answers22[0]):
                bad22.append("%s-not-closed" % tag22)
            elif answers22[1].startswith(b"HTTP/1.1 200"):
                bad22.append("%s-second-answered" % tag22)
        # ---- e: every single-line persistence answer still reads ----------
        answers22 = dialog22([], requests=3)
        if len(answers22) != 3:
            bad22.append("e-persist-count-%d" % len(answers22))
        else:
            for idx22, one22 in enumerate(answers22):
                if not one22.startswith(b"HTTP/1.1 200 OK"):
                    bad22.append("e-persist-%d-%r" % (idx22, one22[:18]))
                elif b"connection: close" in head22(one22):
                    bad22.append("e-persist-closed-%d" % idx22)
        answers22 = dialog22(["Connection: close"])
        if not answers22 or \
                not answers22[0].startswith(b"HTTP/1.1 200 OK"):
            bad22.append("e-close-status")
        elif b"connection: close" not in head22(answers22[0]):
            bad22.append("e-close-header")
        elif len(answers22) > 1 and answers22[1].startswith(b"HTTP/1.1 200"):
            bad22.append("e-close-second")
        answers22 = dialog22(["Connection: keep-alive"], requests=2,
                             version="HTTP/1.0")
        if len(answers22) != 2:
            bad22.append("e-10-keep-count-%d" % len(answers22))
        elif not answers22[0].startswith(b"HTTP/1.0 200 OK"):
            bad22.append("e-10-keep-%r" % answers22[0][:18])
        elif b"connection: keep-alive" not in answers22[0].lower():
            bad22.append("e-10-keep-header")
        elif not answers22[1].startswith(b"HTTP/1.0 200"):
            bad22.append("e-10-second-%r" % answers22[1][:18])
        answers22 = dialog22([], requests=1, version="HTTP/1.0")
        if len(answers22) != 1 or \
                b"connection: close" not in answers22[0].lower():
            bad22.append("e-10-silent")
        # ---- f: dialect, tokens on disk, declared count -------------------
        with io.open(MODULE, "rb") as handle:
            raw22 = handle.read()
        if raw22[:3] == b"\xef\xbb\xbf" or b"\r\n" in raw22:
            bad22.append("f-module-dialect")
        try:
            text22 = raw22.decode("utf-8")
            text22.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad22.append("f-module-not-ascii")
            text22 = raw22.decode("utf-8", "replace")
        for token22 in ('_list_header(self.headers, "Transfer-Encoding")',
                        '_list_header(self.headers, "Connection")'):
            if token22 not in text22:
                bad22.append("f-missing-listreader")
        for token22 in ('self.headers.get("Transfer-Encoding")',
                        'self.headers.get("Connection")'):
            if token22 in text22:
                bad22.append("f-old-reader")
        with io.open(REGISTRY, encoding="utf-8") as handle:
            block22r = handle.read().split('"' + ROW + '"', 1)[-1][:220]
        if DECLARED_TAG not in block22r:
            bad22.append("f-declared")
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
    report("AC-FDPV9", bool(bad9), ",".join(bad9))
    report("AC-FDPV10", bool(bad10), ",".join(bad10))
    report("AC-FDPV11", bool(bad11), ",".join(bad11))
    report("AC-FDPV12", bool(bad12), ",".join(bad12))
    report("AC-FDPV13", bool(bad13), ",".join(bad13))
    report("AC-FDPV14", bool(bad14), ",".join(bad14))
    report("AC-FDPV15", bool(bad15), ",".join(bad15))
    report("AC-FDPV16", bool(bad16), ",".join(bad16))
    report("AC-FDPV17", bool(bad17), ",".join(bad17))
    report("AC-FDPV18", bool(bad18), ",".join(bad18))
    report("AC-FDPV19", bool(bad19), ",".join(bad19))
    report("AC-FDPV20", bool(bad20), ",".join(bad20))
    report("AC-FDPV21", bool(bad21), ",".join(bad21))
    report("AC-FDPV22", bool(bad22), ",".join(bad22))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
