"""Battery suite for tools/ship_checklist.py - criteria AC-SCL1..AC-SCL8.

AC-SCL1..AC-SCL8 were pinned in src/os/backlog.md at R2779, BEFORE the tool
existed; this suite is what finally puts them under a battery row. Every check
runs inside a PRIVATE world created under a temp directory, because AC-SCL7 is a
negative control that removes an evidence file and the real preview/ tree must
never be touched by a test run.

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
TOOL = os.path.join(ROOT, "tools", "ship_checklist.py")

FAILS = []
CHECKS = []


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print("  | PASS %s %s" % (name, detail))
    else:
        FAILS.append(name)
        print("  | FAIL %s %s" % (name, detail))


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def read(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_world():
    """A private world whose every SELF row is READY and every face exists."""
    d = tempfile.mkdtemp(prefix="scl-")
    # hard-door text sources: AIGC label and msgSecCheck must be on disk
    write(os.path.join(d, "BLUEPRINT.md"),
          "# Blueprint\n\nAIGC labelling is a hard door.\n"
          "msgSecCheck is a pre-gate, never a post filter.\n")
    # the filing + pre-approval sources carry the two Chinese needles
    write(os.path.join(d, "docs", "global-benchmarks.md"),
          "# Benchmarks\n\n" + "\u5907\u6848" + " guide and " + "\u7248\u53f7" + " category table.\n")
    write(os.path.join(d, "preview", "ceo-blockers.json"),
          json.dumps({"counts": {"PENDING-PHYSICAL": 3}}, ensure_ascii=False))
    for name in ("ugc-gate-report.json", "platform-live-report.json",
                 "payment-gate-report.json", "lobby-ws-report.json"):
        write(os.path.join(d, "preview", name), "{}\n")
    for name in ("face-sweep.html", "ugc-gate-report.html", "lobby-ws-report.html",
                 "platform-live-report.html", "payment-gate-report.html",
                 "ceo-blockers.html"):
        write(os.path.join(d, "preview", name), "<!DOCTYPE html>\n")
    return d


def load_tool():
    spec = importlib.util.spec_from_file_location("ship_checklist_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    if not os.path.isfile(TOOL):
        print("SUITE FAIL 0/%d tool missing %s" % (8, TOOL))
        return 1
    src = read(os.path.join(ROOT, "src", "os", "test_ship_checklist.py"))
    world = build_world()
    cwd = os.getcwd()
    try:
        os.chdir(world)
        mod = load_tool()

        # ---- AC-SCL2: registry equality, criterion + owner on every item ----
        html, text, rows, sizes = mod.render(write=True)
        doc = json.loads(text)
        ids_registry = [i["id"] for i in mod.ITEMS]
        ids_doc = [r["id"] for r in doc["items"]]
        ok("AC-SCL2 item ids equal the ITEMS registry", ids_doc == ids_registry,
           "items=%d" % len(ids_doc))
        bad = [r["id"] for r in doc["items"]
               if not r.get("criterion") or r.get("owner") not in (mod.SELF, mod.CEO)]
        ok("AC-SCL2 every item carries criterion and owner", not bad, "bad=%s" % bad)
        owners = {"SELF": len([r for r in rows if r["owner"] == mod.SELF]),
                  "CEO": len([r for r in rows if r["owner"] == mod.CEO])}
        ok("AC-SCL2 owner counts derived match the registry",
           owners == doc["owner_counts"], "owners=%s" % owners)

        # ---- AC-SCL1: readiness is recomputed from disk, never written by hand ----
        before = {r["id"]: r["state"] for r in doc["items"]}
        ugc = os.path.join("preview", "ugc-gate-report.json")
        os.remove(ugc)
        fresh = {r["id"]: r["state"] for r in mod.build_rows()}
        moved = [k for k in fresh if fresh[k] != before[k]]
        ok("AC-SCL1 deleting an evidence file moves exactly that row",
           moved == ["self-ugc-gate-face"], "moved=%s" % moved)
        on_disk = json.loads(read(os.path.join("preview", "ship-checklist.json")))
        still = {r["id"]: r["state"] for r in on_disk["items"]}
        ok("AC-SCL1 the json on disk keeps the old stamp until re-rendered",
           still["self-ugc-gate-face"] == "READY" and fresh["self-ugc-gate-face"] == "OPEN")
        ok("AC-SCL1 --check catches the stale stamp", bool(mod.check()))
        write(os.path.join("preview", "ceo-blockers.json"),
              json.dumps({"counts": {"PENDING-PHYSICAL": 3}}, ensure_ascii=False))
        write(os.path.join("preview", "ugc-gate-report.json"), "{}\n")
        html, text, rows, sizes = mod.render(write=True)
        ok("AC-SCL1 re-render restores READY and --check reads clean", mod.check() == [])

        # ---- AC-SCL3: the page opens offline ----
        bad_schemes = [b for b in mod.FORBIDDEN if b in html]
        ok("AC-SCL3 html holds no http(s) literal", not bad_schemes,
           "forbidden=%s" % bad_schemes)

        # ---- AC-SCL4: stable tick ids, one namespace, one inline script ----
        missing = [r["id"] for r in rows if ('data-ck="%s"' % r["id"]) not in html]
        ok("AC-SCL4 every row carries a stable data-ck id", not missing,
           "missing=%s" % missing)
        ok("AC-SCL4 exactly one inline script and no external script",
           html.count("<script>") == 1 and html.count("<script src") == 0
           and html.count("<script ") == 0,
           "inline=%d" % html.count("<script>"))
        # the criterion is ONE namespace, not ONE mention: the page also prints
        # the namespace in prose, so the reading is the declaration count plus
        # the fact that both storage calls go through the variable.
        decl = "var NS='bd-ship-checklist-v1';"
        ok("AC-SCL4 one localStorage namespace guards the tick state",
           html.count(decl) == 1 and "localStorage.getItem(NS)" in html,
           "decl=%d literal_get=%d"
           % (html.count(decl), html.count("localStorage.getItem('")))

        # ---- AC-SCL5: recorded sizes are a fixed point ----
        doc = json.loads(read(os.path.join("preview", "ship-checklist.json")))
        hb = os.path.getsize(os.path.join("preview", "ship-checklist.html"))
        jb = os.path.getsize(os.path.join("preview", "ship-checklist.json"))
        ok("AC-SCL5 recorded sizes equal the bytes on disk",
           doc["sizes"]["html"] == hb and doc["sizes"]["json"] == jb,
           "html=%d json=%d" % (hb, jb))
        html2, text2, _, _ = mod.render(write=False)
        ok("AC-SCL5 a second render is byte identical (no clock, no drift)",
           html2 == html and text2 == text)

        # ---- AC-SCL6: --check never writes ----
        hp = os.path.join("preview", "ship-checklist.html")
        jp = os.path.join("preview", "ship-checklist.json")
        snap = [(os.path.getsize(hp), os.stat(hp).st_mtime_ns),
                (os.path.getsize(jp), os.stat(jp).st_mtime_ns)]
        fails = mod.check()
        snap2 = [(os.path.getsize(hp), os.stat(hp).st_mtime_ns),
                 (os.path.getsize(jp), os.stat(jp).st_mtime_ns)]
        ok("AC-SCL6 --check writes nothing and both files keep bytes and mtime",
           snap == snap2 and fails == [], "fails=%d" % len(fails))
        rc = mod.main(["--check"])
        ok("AC-SCL6 the CLI exit code is 0 on a clean world", rc == 0, "rc=%s" % rc)

        # ---- AC-SCL7: negative control, removing an evidence file flips red ----
        pay = os.path.join("preview", "payment-gate-report.json")
        keep = read(pay)
        os.remove(pay)
        bad = mod.check()
        ok("AC-SCL7 removing an evidence file flips --check red",
           bool(bad) and any("self-payment-gate" in b for b in bad), "fails=%s" % bad[:2])
        rc = mod.main(["--check"])
        ok("AC-SCL7 the CLI exit code is 2 on a red world", rc == 2, "rc=%s" % rc)
        write(pay, keep)
        ok("AC-SCL7 restoring the file returns --check to clean", mod.check() == [])

        # ---- AC-SCL8: three BLUEPRINT hard doors present with landing faces ----
        doors = ("hard-aigc-label", "hard-msgseccheck", "hard-non-advisory")
        rows_now = mod.build_rows()
        detail = []
        good = True
        for rid in doors:
            hit = [r for r in rows_now if r["id"] == rid]
            if not hit:
                good = False
                detail.append("%s missing" % rid)
            elif not hit[0]["face_present"]:
                good = False
                detail.append("%s face missing" % rid)
            elif rid not in html:
                good = False
                detail.append("%s not rendered" % rid)
        ok("AC-SCL8 the three hard doors exist, have faces and are rendered", good,
           "detail=%s" % detail)

        # ---- hygiene ----
        bad_bytes = [b for b in src if ord(b) > 127]
        ok("AC-SCL8 suite source is pure ASCII", not bad_bytes,
           "non_ascii=%d" % len(bad_bytes))
        net = [m for m in ("urllib", "requests", "socket", "http.client", "subprocess")
               if ("import " + m) in src]
        ok("AC-SCL8 suite has no network and no shell import", not net, "found=%s" % net)
    finally:
        os.chdir(cwd)
        shutil.rmtree(world, ignore_errors=True)

    total = len(CHECKS)
    # R2859: this suite owns two units - the checks above and the AC ids the
    # registry counts - so it states both in the corpus's lowercase dialect.
    # The count is derived from CHECKS itself, never copied from the registry:
    # a declaration that echoed the registry could never disagree with it.
    acs = set()
    for name in CHECKS:
        token = name.split(" ", 1)[0]
        if token.startswith("AC-SCL"):
            acs.add(token)
    print("suite: %d assertions over %d criteria" % (total, len(acs)))
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s" % (total - len(FAILS), total, FAILS))
        return 1
    print("SUITE PASS %d/%d %s" % (total, total, " ".join(CHECKS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
