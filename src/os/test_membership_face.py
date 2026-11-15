"""Battery suite for tools/membership_face.py - criteria AC-MEMF1..AC-MEMF6.

AC-MEMF1..AC-MEMF6 were pinned in src/os/backlog.md at R2783, BEFORE the tool
existed; this suite is what finally puts them under a battery row (the tool
shipped at R2783 with only its own --check guarding it).

Isolation: every run happens in a PRIVATE world - the real preview/ tree is
copied into a temp directory and the module's path globals are repointed, so the
negative controls that tamper with an artifact and strip a needle never touch
the shipped tree.

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
TOOL = os.path.join(ROOT, "tools", "membership_face.py")

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
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_world():
    d = tempfile.mkdtemp(prefix="memf-")
    shutil.copytree(os.path.join(ROOT, "preview"), os.path.join(d, "preview"))
    os.makedirs(os.path.join(d, "docs", "spec"))
    os.makedirs(os.path.join(d, "tools"))
    shutil.copy(os.path.join(ROOT, "docs", "spec", "membership-spec.md"),
                os.path.join(d, "docs", "spec", "membership-spec.md"))
    shutil.copy(os.path.join(ROOT, "tools", "membership_face_config.json"),
                os.path.join(d, "tools", "membership_face_config.json"))
    return d


def load_tool(world):
    spec = importlib.util.spec_from_file_location("membership_face_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SPEC = os.path.join(world, "docs", "spec", "membership-spec.md")
    mod.PAY = os.path.join(world, "preview", "payment-gate-report.json")
    mod.CONF = os.path.join(world, "tools", "membership_face_config.json")
    mod.OUT_HTML = os.path.join(world, "preview", "membership-face.html")
    mod.OUT_JSON = os.path.join(world, "preview", "membership-face.json")
    return mod


def main():
    if not os.path.isfile(TOOL):
        print("SUITE FAIL 0/6 tool missing %s" % TOOL)
        return 1
    src = read(os.path.join(ROOT, "src", "os", "test_membership_face.py"))
    tool_src = read(TOOL)
    world = build_world()
    cwd = os.getcwd()
    try:
        mod = load_tool(world)
        conf, payload, spec_text = mod.build()
        html = mod.render_html(conf, payload)
        jb = mod.payload_bytes(payload)
        mod.write_atomic(mod.OUT_JSON, jb)
        mod.write_atomic(mod.OUT_HTML, html.encode("utf-8"))

        # ---- AC-MEMF1: every count is recomputed, and rows come from the spec ----
        tiers = payload["tiers"]
        want = {
            "tiers": len(tiers),
            "paid": sum(1 for t in tiers if not t["is_free"]),
            "pending": sum(1 for t in tiers if t["needs_ceo"]),
            "matched": sum(1 for t in tiers if t["products"]),
            "blocked": sum(t["blocked_refs"] for t in tiers),
            "privileges": sum(len(t["privileges"]) for t in tiers),
        }
        ok("AC-MEMF1 counts equal a recomputation from the tier rows",
           payload["counts"] == want, "counts=%s" % payload["counts"])
        stray = [t["name"] for t in tiers if t["name"] not in spec_text]
        ok("AC-MEMF1 every tier name is parsed from the spec text", not stray,
           "rows=%d stray=%s" % (len(tiers), stray))
        lits = [p for p in ("19.9", "49.9", "99.0", "1999") if p in tool_src]
        ok("AC-MEMF1 the tool source carries no price literal", not lits,
           "found=%s" % lits)

        # ---- AC-MEMF2: product binding is recomputed, never asserted ----
        products = json.loads(read(mod.PAY)).get("products") or []
        bad = []
        for t in tiers:
            want_ids = []
            if t["price_yuan"] is not None:
                cents = int(round(t["price_yuan"] * 100))
                want_ids = sorted(p["id"] for p in products if p.get("price_cent") == cents)
            have_ids = sorted(x["id"] for x in t["products"])
            if want_ids != have_ids:
                bad.append((t["name"], want_ids, have_ids))
        ok("AC-MEMF2 tier product matches equal the price cross-check",
           not bad, "bad=%s" % bad)
        missing = [t["name"] for t in tiers if t["name"] not in html]
        ok("AC-MEMF2 every tier is rendered on the page", not missing,
           "missing=%s" % missing)
        unsigned = [x["id"] for t in tiers for x in t["products"] if x["id"] not in html]
        ok("AC-MEMF2 every matched product id reaches the page", not unsigned,
           "unsigned=%s" % unsigned)

        # ---- AC-MEMF3: the four needles are read live and their loss is named ----
        ok("AC-MEMF3 every needle and compliance marker is found",
           all(n["found"] for n in payload["needles"]) and
           all(c["found"] for c in payload["compliance"]),
           "needles=%d compliance=%d"
           % (len(payload["needles"]), len(payload["compliance"])))
        spec_path = mod.SPEC
        keep = read(spec_path)
        needle = payload["needles"][0]["needle"]
        with io.open(spec_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(keep.replace(needle, ""))
        conf2, payload2, _ = mod.build()
        lost = [n["needle"] for n in payload2["needles"] if not n["found"]]
        reasons = mod.gate(conf2, payload2, mod.render_html(conf2, payload2),
                           mod.payload_bytes(payload2))
        ok("AC-MEMF3 stripping a needle turns the gate red naming E_NEEDLE",
           bool(lost) and any(r.startswith("E_NEEDLE") for r in reasons),
           "lost=%s reasons=%s" % (lost, reasons[:2]))
        with io.open(spec_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(keep)
        mod.build()

        # ---- AC-MEMF4: offline page whose every link target exists ----
        ok("AC-MEMF4 the page holds no http literal", "http" not in html,
           "links=%d" % len(payload["links"]))
        dead = [l["href"] for l in payload["links"] if not l["exists"]]
        ok("AC-MEMF4 every relative link target exists on disk", not dead,
           "dead=%s" % dead)

        # ---- AC-MEMF5: recorded sizes and a byte-identical second render ----
        real = {"spec_bytes": os.path.getsize(mod.SPEC),
                "pay_bytes": os.path.getsize(mod.PAY),
                "config_bytes": os.path.getsize(mod.CONF)}
        ok("AC-MEMF5 recorded sizes equal the bytes on disk",
           payload["sizes"] == real, "sizes=%s" % payload["sizes"])
        html2 = mod.render_html(conf, payload)
        ok("AC-MEMF5 a second render is byte identical on both artifacts",
           html2 == html and mod.payload_bytes(payload) == jb)

        # ---- AC-MEMF6: --check is read-only, and a tampered byte is caught ----
        snap = [(os.path.getsize(mod.OUT_HTML), os.stat(mod.OUT_HTML).st_mtime_ns),
                (os.path.getsize(mod.OUT_JSON), os.stat(mod.OUT_JSON).st_mtime_ns)]
        before_out = sys.stdout
        buf = io.StringIO()
        sys.stdout = buf
        try:
            rc = mod.main(["--check"])
        finally:
            sys.stdout = before_out
        snap2 = [(os.path.getsize(mod.OUT_HTML), os.stat(mod.OUT_HTML).st_mtime_ns),
                 (os.path.getsize(mod.OUT_JSON), os.stat(mod.OUT_JSON).st_mtime_ns)]
        ok("AC-MEMF6 --check exits 0 and writes nothing (bytes and mtime)",
           rc == 0 and snap == snap2, "rc=%s" % rc)
        with io.open(mod.OUT_HTML, "rb") as fh:
            keep_html = fh.read()
        with io.open(mod.OUT_HTML, "wb") as fh:
            fh.write(keep_html[:-1] + b" ")
        conf3, payload3, _ = mod.build()
        bad = mod.gate(conf3, payload3, mod.render_html(conf3, payload3),
                       mod.payload_bytes(payload3))
        ok("AC-MEMF6 one flipped byte on disk is caught as E_STALE",
           any(r.startswith("E_STALE") for r in bad), "reasons=%s" % bad[:2])
        with io.open(mod.OUT_HTML, "wb") as fh:
            fh.write(keep_html)
        conf4, payload4, _ = mod.build()
        ok("AC-MEMF6 restoring the byte returns the gate to clean",
           mod.gate(conf4, payload4, mod.render_html(conf4, payload4),
                    mod.payload_bytes(payload4)) == [])

        # ---- hygiene ----
        bad_bytes = [b for b in src if ord(b) > 127]
        ok("AC-MEMF6 suite source is pure ASCII", not bad_bytes,
           "non_ascii=%d" % len(bad_bytes))
        net = [m for m in ("urllib", "requests", "socket", "http.client", "subprocess")
               if ("import " + m) in src]
        ok("AC-MEMF6 suite has no network and no shell import", not net, "found=%s" % net)
    finally:
        os.chdir(cwd)
        shutil.rmtree(world, ignore_errors=True)

    total = len(CHECKS)
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s" % (total - len(FAILS), total, FAILS))
        return 1
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
