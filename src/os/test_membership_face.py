"""Battery suite for tools/membership_face.py - criteria AC-MEMF1..AC-MEMF10.

AC-MEMF1..AC-MEMF6 were pinned in src/os/backlog.md at R2783, BEFORE the tool
existed; this suite is what finally puts them under a battery row (the tool
shipped at R2783 with only its own --check guarding it). AC-MEMF7..AC-MEMF10
were pinned at R2818, also BEFORE the code, for the debt R2816 recorded: the
page listed the four spec tiers and NONE of the two products the ruling
D-20261116-05 actually sells, so a buyer could open the membership page and see
no permanent ticket at all.

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
    os.makedirs(os.path.join(d, "src", "sandbox", "pay"))
    os.makedirs(os.path.join(d, "src", "sandbox", "member"))
    shutil.copy(os.path.join(ROOT, "src", "sandbox", "pay", "config.json"),
                os.path.join(d, "src", "sandbox", "pay", "config.json"))
    shutil.copy(os.path.join(ROOT, "src", "sandbox", "member", "config.json"),
                os.path.join(d, "src", "sandbox", "member", "config.json"))
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
    mod.PAYCONF = os.path.join(world, "src", "sandbox", "pay", "config.json")
    mod.MCONF = os.path.join(world, "src", "sandbox", "member", "config.json")
    return mod


def main():
    if not os.path.isfile(TOOL):
        print("SUITE FAIL 0/10 tool missing %s" % TOOL)
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
            "products": len(payload.get("catalogue") or []),
            "no_cycle_products": sum(1 for r in payload.get("catalogue") or []
                                     if r["no_cycle"]),
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
                "config_bytes": os.path.getsize(mod.CONF),
                "payconf_bytes": os.path.getsize(mod.PAYCONF),
                "mconf_bytes": os.path.getsize(mod.MCONF)}
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

        # ---- AC-MEMF7: the shipped catalogue is derived, not typed ----
        payconf_path = mod.PAYCONF
        mconf_path = mod.MCONF
        payconf_keep = read(payconf_path)
        catalogue = payload.get("catalogue") or []
        shipped_ids = sorted(json.loads(payconf_keep)["products"].keys())
        ok("AC-MEMF7 the page lists every shipped pay-config product",
           sorted(r["id"] for r in catalogue) == shipped_ids,
           "page=%s config=%s" % (len(catalogue), len(shipped_ids)))
        off_page = [r["id"] for r in catalogue if r["id"] not in html]
        ok("AC-MEMF7 every shipped product reaches the landed page",
           not off_page, "off_page=%s" % off_page)
        grown = json.loads(payconf_keep)
        grown["products"]["probe_growth_R2818"] = {
            "channel": "virtual", "copy": "probe row", "entitlement": "probe",
            "price_cent": 1234, "share_tokens": 0}
        with io.open(payconf_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(grown, ensure_ascii=False, indent=2) + "\n")
        conf5, payload5, _ = mod.build()
        html5 = mod.render_html(conf5, payload5)
        ok("AC-MEMF7 a product added to the config appears with no module edit",
           "probe_growth_R2818" in [r["id"] for r in payload5.get("catalogue") or []]
           and "probe_growth_R2818" in html5,
           "rows=%d" % len(payload5.get("catalogue") or []))
        with io.open(payconf_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payconf_keep)
        conf, payload, spec_text = mod.build()
        html = mod.render_html(conf, payload)
        jb = mod.payload_bytes(payload)

        # ---- AC-MEMF8: the two D-05 products stand side by side, shape checked ----
        by_id = {r["id"]: r for r in payload.get("catalogue") or []}
        perm = by_id.get("birthright_entry") or {}
        month = by_id.get("tier_patron_30d") or {}
        ok("AC-MEMF8 the permanent ticket carries no cycle and no privileges",
           perm.get("period_days") is None and not perm.get("privileges")
           and perm.get("no_cycle") is True,
           "perm=%s" % {k: perm.get(k) for k in ("period_days", "privileges", "no_cycle")})
        ok("AC-MEMF8 the monthly card carries its period and its privileges",
           month.get("period_days") == 30 and len(month.get("privileges") or []) == 2
           and month.get("no_cycle") is False,
           "month=%s" % {k: month.get(k) for k in ("period_days", "privileges", "no_cycle")})
        ok("AC-MEMF8 both names and both prices reach the landed page",
           bool(perm.get("name")) and bool(month.get("name"))
           and perm.get("name") in html and month.get("name") in html
           and ("%.2f" % perm.get("price_yuan", -1)) in html
           and ("%.2f" % month.get("price_yuan", -1)) in html,
           "perm=%s month=%s" % (perm.get("price_yuan"), month.get("price_yuan")))
        swapped = json.loads(json.dumps(payload))
        for r in swapped.get("catalogue") or []:
            if r["id"] == "birthright_entry":
                r["period_days"] = 30
                r["no_cycle"] = False
            elif r["id"] == "tier_patron_30d":
                r["period_days"] = None
                r["no_cycle"] = True
        swap_reasons = mod.gate(conf, swapped, html, mod.payload_bytes(swapped))
        ok("AC-MEMF8 swapping the two cycle shapes reddens E_PRODUCT_SHAPE",
           any(r.startswith("E_PRODUCT_SHAPE") for r in swap_reasons),
           "reasons=%s" % swap_reasons[:2])

        # ---- AC-MEMF9: a landed page rendered against another config reddens ----
        real_payconf = {"payconf_bytes": os.path.getsize(mod.PAYCONF),
                        "mconf_bytes": os.path.getsize(mod.MCONF)}
        rec = dict((k, payload["sizes"].get(k)) for k in real_payconf)
        ok("AC-MEMF9 the shipped config bytes are recorded at render time",
           rec == real_payconf, "recorded=%s disk=%s" % (rec, real_payconf))
        with io.open(payconf_path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(" ")
        stale_reasons = mod.gate(conf, payload, html, jb)
        ok("AC-MEMF9 a config that moved under the page reddens E_PAYCONF_STALE",
           any(r.startswith("E_PAYCONF_STALE") for r in stale_reasons),
           "reasons=%s" % stale_reasons[:2])
        with io.open(payconf_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payconf_keep)
        conf, payload, spec_text = mod.build()
        html = mod.render_html(conf, payload)
        jb = mod.payload_bytes(payload)
        ok("AC-MEMF9 restoring the config returns the gate to clean",
           mod.gate(conf, payload, html, jb) == [])

        # ---- AC-MEMF10: prices are derived from cents, not typed into a template ----
        moved = json.loads(payconf_keep)
        moved["products"]["birthright_entry"]["price_cent"] = 1290
        with io.open(payconf_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(moved, ensure_ascii=False, indent=2) + "\n")
        conf6, payload6, _ = mod.build()
        html6 = mod.render_html(conf6, payload6)
        probe = {r["id"]: r for r in payload6.get("catalogue") or []}.get("birthright_entry") or {}
        yen = chr(0xa5)
        ok("AC-MEMF10 a one-cent-scale move changes the printed yuan on the page",
           abs((probe.get("price_yuan") or 0) - 12.90) < 1e-9
           and (yen + "12.90") in html6 and (yen + "9.90") not in html6,
           "yuan=%s moved=%s" % (probe.get("price_yuan"), (yen + "12.90") in html6))
        with io.open(payconf_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payconf_keep)
        conf, payload, spec_text = mod.build()
        html = mod.render_html(conf, payload)
        jb = mod.payload_bytes(payload)
        mod.write_atomic(mod.OUT_JSON, jb)
        mod.write_atomic(mod.OUT_HTML, html.encode("utf-8"))

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
    # Declared units (R2860): the AC inventory below is derived from CHECKS,
    # never echoed from the registry - a declaration copied out of the
    # registry could never disagree with it.
    acs = set()
    for name in CHECKS:
        token = name.split(' ', 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    print('suite: %d assertions over %d criteria' % (total, len(acs)))
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s" % (total - len(FAILS), total, FAILS))
        return 1
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
