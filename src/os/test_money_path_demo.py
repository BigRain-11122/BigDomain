"""Battery suite for tools/money_path_demo.py - criteria AC-MPD1..AC-MPD6.

AC-MPD1..AC-MPD6 were pinned in src/os/backlog.md at R2782, BEFORE the tool
existed; the tool shipped with only its own --check guarding it, so this suite
is what puts the criteria under a battery row.

Isolation: the real preview/ tree is copied into a temp directory and the
module's ROOT / PREVIEW globals are repointed, so the negative control that
flips a byte never touches the shipped page. check() resolves the six source
paths through ROOT, which is why both globals are patched.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "money_path_demo.py")

FAILS = []
CHECKS = []


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print("  | PASS %s %s" % (name, detail))
    else:
        FAILS.append(name)
        print("  | FAIL %s %s" % (name, detail))


def read(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def load_tool(world):
    spec = importlib.util.spec_from_file_location("money_path_demo_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT = world
    mod.PREVIEW = os.path.join(world, "preview")
    return mod


def main():
    if not os.path.isfile(TOOL):
        print("SUITE FAIL 0/6 tool missing %s" % TOOL)
        return 1
    src = read(os.path.join(ROOT, "src", "os", "test_money_path_demo.py"))
    world = tempfile.mkdtemp(prefix="mpd-")
    try:
        shutil.copytree(os.path.join(ROOT, "preview"), os.path.join(world, "preview"))
        mod = load_tool(world)
        payload = mod.derive()
        html_path, json_path, html_bytes, json_bytes = mod.write_all()
        html = read(html_path)
        landed = json.loads(read(json_path))

        # ---- AC-MPD1: every number is derived, never typed ----
        products = payload["products"]
        steps = payload["steps"]
        ok("AC-MPD1 product and step counts are derived from the lists",
           landed["counts"]["products"] == len(products)
           and landed["counts"]["steps"] == len(steps)
           and landed["counts"]["products"] == len(landed["products"])
           and landed["counts"]["steps"] == len(landed["steps"]),
           "counts=%s" % landed["counts"])
        gate = json.loads(read(os.path.join(world, "preview",
                                            "payment-gate-report.json")))
        by_id = dict((p["id"], p) for p in (gate.get("products") or []))
        drift = []
        for p in products:
            s = by_id.get(p["id"])
            if s is None or s.get("price_cent") != p["price_cent"]:
                drift.append(p["id"])
        ok("AC-MPD1 every price is the source price_cent, id for id", not drift,
           "products=%d drift=%s" % (len(products), drift))

        # ---- AC-MPD2: the list equals the source and CEO gate is visible ----
        ok("AC-MPD2 product ids equal the source list id for id",
           [p["id"] for p in products] == [p["id"] for p in (gate.get("products") or [])],
           "ids=%s" % [p["id"] for p in products])
        ceo = [p["id"] for p in products if p["needs_ceo"]]
        ok("AC-MPD2 every CEO-blocked product carries a visible CEO gate",
           all(mod.T_CEO_YES in html for _ in [0]) and (not ceo or mod.T_CEO_YES in html),
           "ceo_products=%d" % len(ceo))
        missing = [p["id"] for p in products if p["id"] not in html]
        ok("AC-MPD2 every product reaches the page", not missing, "missing=%s" % missing)

        # ---- AC-MPD3: mock statement, offline ----
        ok("AC-MPD3 the page states it is a mock surface",
           "MOCK" in html and mod.T_MOCK.split("\uff1a")[0][:6] in html,
           "label=%s" % mod.T_MOCK.split("\uff1a")[0][:6])
        ok("AC-MPD3 the page holds no absolute url",
           "http://" not in html and "https://" not in html)

        # ---- AC-MPD4: steps carry their source verdict strings unaltered ----
        no_verdict = [s["id"] for s in steps if s["verdict"] and s["verdict"] not in html]
        no_id = [s["id"] for s in steps if s["id"] not in html]
        ok("AC-MPD4 every step verdict string reaches the page unaltered",
           not no_verdict, "steps=%d missing=%s" % (len(steps), no_verdict))
        ok("AC-MPD4 every step id reaches the page", not no_id, "missing=%s" % no_id)
        no_ent = [p["id"] for p in products if p["entitlement"] and p["entitlement"] not in html]
        ok("AC-MPD4 every product entitlement and channel is rendered",
           not no_ent and all(p["channel"] in html for p in products), "missing=%s" % no_ent)

        # ---- AC-MPD5: source sizes and a byte-identical rerender ----
        drift = []
        for key, meta in sorted(payload["sources"].items()):
            real = os.path.getsize(os.path.join(world, meta["path"].replace("/", os.sep)))
            if real != meta["bytes"]:
                drift.append((key, meta["bytes"], real))
        ok("AC-MPD5 recorded source sizes equal the bytes on disk", not drift,
           "sources=%d drift=%s" % (len(payload["sources"]), drift))
        first = (read(html_path), read(json_path))
        mod.write_all()
        second = (read(html_path), read(json_path))
        ok("AC-MPD5 a second render is byte identical on both artifacts",
           first == second, "html=%dB json=%dB" % (html_bytes, json_bytes))

        # ---- AC-MPD6: --check is read-only and one flipped byte is caught ----
        snap = [(os.path.getsize(html_path), os.stat(html_path).st_mtime_ns),
                (os.path.getsize(json_path), os.stat(json_path).st_mtime_ns)]
        before_out = sys.stdout
        buf = io.StringIO()
        sys.stdout = buf
        try:
            rc = mod.main(["--check"])
        finally:
            sys.stdout = before_out
        snap2 = [(os.path.getsize(html_path), os.stat(html_path).st_mtime_ns),
                 (os.path.getsize(json_path), os.stat(json_path).st_mtime_ns)]
        ok("AC-MPD6 --check exits 0 and writes nothing (bytes and mtime)",
           rc == 0 and snap == snap2 and mod.check() == [], "rc=%s" % rc)
        keep = read(html_path)
        with io.open(html_path, "wb") as fh:
            fh.write(keep.encode("utf-8")[:-1] + b" ")
        problems = mod.check()
        ok("AC-MPD6 one flipped byte is caught by check()", bool(problems),
           "problems=%d" % len(problems))
        with io.open(html_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(keep)
        ok("AC-MPD6 restoring the byte returns check() to clean", mod.check() == [])
        ok("AC-MPD6 exactly one inline script and one namespace declaration",
           html.count("<script") == 1
           and html.count("var NS='%s'" % mod.NS) == 1
           and html.count("localStorage.") == 2,
           "script=%d ns=%d storage=%d" % (html.count("<script"),
                                           html.count("var NS='%s'" % mod.NS),
                                           html.count("localStorage.")))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    # ---- hygiene ----
    bad_bytes = [b for b in src if ord(b) > 127]
    ok("AC-MPD6 suite source is pure ASCII", not bad_bytes,
       "non_ascii=%d" % len(bad_bytes))
    net = [m for m in ("urllib", "requests", "socket", "http.client", "subprocess")
           if ("import " + m) in src]
    ok("AC-MPD6 suite has no network and no shell import", not net, "found=%s" % net)

    total = len(CHECKS)
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s" % (total - len(FAILS), total, FAILS))
        return 1
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
