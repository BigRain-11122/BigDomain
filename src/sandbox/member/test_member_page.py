"""Acceptance suite for the member face (P-47-5 page over the shipped engine).

Criteria AC-MFN1..AC-MFN6 below. HONESTY DISCLOSURE: unlike the shipped
suites in this sandbox, these criteria were written in the SAME window as
the module bytes, not before them - pre-registration was not honoured for
this face, so this suite is weaker evidence than a pre-registered one.

Runs the face in-process on an OS-assigned port against a temp sandbox data
directory, so no shipped config or live database is touched.

Usage: python test_member_page.py
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import member_page as MP  # noqa: E402

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def http_get(port, path):
    url = "http://127.0.0.1:%d%s" % (port, path)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def http_json(port, path):
    status, body = http_get(port, path)
    return status, json.loads(body.decode("utf-8"))


def http_post(port, path, payload):
    url = "http://127.0.0.1:%d%s" % (port, path)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def main():
    data_dir = tempfile.mkdtemp(prefix="member-face-ac-")
    server = MP.make_server("127.0.0.1", 0, data_dir)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        # AC-MFN1: the page is served from disk byte for byte, and the
        # service is read-only outside the one join route.
        with open(os.path.join(HERE, MP.PAGE_NAME), "rb") as handle:
            on_disk = handle.read()
        status, body = http_get(port, "/member/")
        status2, body2 = http_get(port, "/member")
        record("AC-MFN1",
               status == 200 and body == on_disk and body2 == on_disk,
               "page=%dB disk=%dB both_200=%s"
               % (len(body), len(on_disk), status == status2 == 200))

        # AC-MFN2: an empty / malformed request is refused by name, and an
        # unknown path or a write method other than join is refused too.
        s_blank, b_blank = http_json(port, "/member/api/state")
        s_days, b_days = http_json(port, "/member/api/state?avatar=a&days=x")
        s_404, b_404 = http_json(port, "/member/api/nope")
        s_post, b_post = http_post(port, "/member/api/nope", {})
        record("AC-MFN2",
               s_blank == 400 and b_blank["error"] == "E_NO_AVATAR"
               and s_days == 400 and b_days["error"] == "E_BAD_BODY"
               and s_404 == 404 and b_404["error"] == "E_NOT_FOUND"
               and s_post == 404 and b_post["error"] == "E_NOT_FOUND",
               "blank=%s/%s days=%s/%s get404=%s post404=%s"
               % (s_blank, b_blank["error"], s_days, b_days["error"],
                  s_404, s_post))

        # AC-MFN3: a resident with no grant reads an honest empty face -
        # no invented tier, no invented birth certificate.
        s_empty, b_empty = http_json(port, "/member/api/state?avatar=ghost")
        priv = b_empty["privileges"]
        record("AC-MFN3",
               s_empty == 200 and priv["active"] is False
               and priv["tiers"] == [] and priv["privileges"] == []
               and b_empty["birth_cert"]["birth_cert"] is False,
               "active=%s tiers=%s cert=%s"
               % (priv["active"], priv["tiers"],
                  b_empty["birth_cert"]["birth_cert"]))

        # AC-MFN4: the sandbox month card really grants - join returns the
        # mock order, and the SAME face then reads tier + privileges +
        # birth cert + one period for that resident.
        s_join, b_join = http_post(port, "/member/api/join", {"avatar": "alice"})
        s_state, b_state = http_json(port, "/member/api/state?avatar=alice")
        joined = b_join.get("joined") or {}
        record("AC-MFN4",
               s_join == 200 and joined.get("mock") is True
               and joined.get("amount_cent") == 1990
               and s_state == 200
               and b_state["privileges"]["tiers"] == ["experience"]
               and b_state["birth_cert"]["birth_cert"] is True
               and len(b_state["privileges"]["periods"]) == 1,
               "join=%s amount=%s tiers=%s cert=%s periods=%d"
               % (s_join, joined.get("amount_cent"),
                  b_state["privileges"]["tiers"],
                  b_state["birth_cert"]["birth_cert"],
                  len(b_state["privileges"]["periods"])))

        # AC-MFN5: the compliance face is carried by the ENGINE, never
        # re-typed here - the disclaimer on the page payload equals the
        # catalog disclaimer, the AI label comes from the catalog, and the
        # mock/no-charge markers are present on both read routes.
        with open(os.path.join(HERE, "config.json"), encoding="utf-8") as handle:
            mcfg = json.load(handle)
        cat = MP.CAT.Catalog.from_config(mcfg)
        s_av, b_av = http_json(port, "/member/api/avatars")
        record("AC-MFN5",
               b_state["disclaimer"] == cat.disclaimer
               and b_state["mock"] is True and b_state["chargeable"] is False
               and b_state["ai_label"] == cat.ai_label
               and s_av == 200 and b_av["disclaimer"] == cat.disclaimer
               and b_av["avatars"] == ["alice"] and b_av["count"] == 1,
               "disclaimer_match=%s ai_label=%r avatars=%s"
               % (b_state["disclaimer"] == cat.disclaimer,
                  b_state["ai_label"], b_av["avatars"]))

        # AC-MFN6: the page carries no external reference and every fetch
        # it makes is a same-origin /member/ path; the module source is
        # pure ASCII and stdlib only.
        page = on_disk.decode("utf-8")
        external = [tok for tok in ("http://", "https://", "//cdn", "src=\"//")
                    if tok in page]
        fetch_paths = page.count('"/member/') + page.count("'/member/")
        with open(os.path.join(HERE, "member_page.py"), "rb") as handle:
            raw = handle.read()
        ascii_ok = all(b < 128 for b in raw)
        network = [ln.strip() for ln in raw.decode("ascii").splitlines()
                   if "urllib.request" in ln or "socket." in ln
                   or "http.client" in ln]
        record("AC-MFN6",
               not external and fetch_paths >= 3 and ascii_ok and not network,
               "external=%s member_paths=%d ascii=%s egress=%d"
               % (external or "none", fetch_paths, ascii_ok, len(network)))

        status, body = http_get(port, "/member/api/state?avatar=alice")
        print("live: state=%s bytes=%d" % (status, len(body)), flush=True)
    finally:
        server.shutdown()
        server.server_close()
        MP.close_world(server.face.world)
        shutil.rmtree(data_dir, ignore_errors=True)

    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %d/%d green" % (len(RESULTS) - len(fails), len(RESULTS)),
          flush=True)
    if fails:
        print("FAILING: %s" % ",".join(fails), flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())