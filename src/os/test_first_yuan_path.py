"""Battery suite for tools/first_yuan_path.py - criteria AC-FYP1..AC-FYP7.

AC-FYP1..AC-FYP7 were pinned in state/queue/tech.md BEFORE the tool (owed since
R2775); the tool shipped with only its own --check guarding it, so this suite is
what puts the criteria under a battery row.

Isolation: the preview/ tree and state/debt.md are copied into a temp directory
and the module's BASE global is repointed, so the negative control that flips a
carrier verdict never touches the shipped reports.

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
TOOL = os.path.join(ROOT, "tools", "first_yuan_path.py")

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
    spec = importlib.util.spec_from_file_location("first_yuan_path_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.BASE = world
    return mod


def main():
    if not os.path.isfile(TOOL):
        print("SUITE FAIL 0/7 tool missing %s" % TOOL)
        return 1
    src = read(os.path.join(ROOT, "src", "os", "test_first_yuan_path.py"))
    world = tempfile.mkdtemp(prefix="fyp-")
    try:
        shutil.copytree(os.path.join(ROOT, "preview"), os.path.join(world, "preview"))
        os.makedirs(os.path.join(world, "state"))
        shutil.copy(os.path.join(ROOT, "state", "debt.md"),
                    os.path.join(world, "state", "debt.md"))
        mod = load_tool(world)
        mod.cmd_write()
        html_path = mod._abs(mod.HTML_REL)
        json_path = mod._abs(mod.JSON_REL)
        html = read(html_path)
        doc = json.loads(read(json_path))
        fresh = mod.derive()

        # ---- AC-FYP1: carriers are the pinned rows, in order ----
        want = [(c[0], c[1], c[2]) for c in mod.CARRIERS]
        have = [(r["id"], r["label"], r["source"]) for r in doc["carriers"]]
        ok("AC-FYP1 carriers equal the pinned carrier table in order", have == want,
           "carriers=%d" % len(have))

        # ---- AC-FYP2: every state is a fresh read, never a written string ----
        same = all(a["state"] == b["state"] and a["ok"] == b["ok"]
                   for a, b in zip(doc["carriers"], fresh["carriers"]))
        ok("AC-FYP2 every carrier state equals a fresh read of its report", same,
           "states=%s" % [r["state"] for r in fresh["carriers"]])
        drift = [r["id"] for r in doc["carriers"]
                 if r["bytes"] != os.path.getsize(mod._abs(r["source"]))]
        ok("AC-FYP2 every recorded carrier size equals the bytes on disk",
           not drift, "drift=%s" % drift)

        # ---- AC-FYP3: --check must not author what it verifies ----
        h0, j0 = os.stat(html_path), os.stat(json_path)
        before_out = sys.stdout
        buf = io.StringIO()
        sys.stdout = buf
        try:
            rc = mod.main(["--check"])
        finally:
            sys.stdout = before_out
        h1, j1 = os.stat(html_path), os.stat(json_path)
        ok("AC-FYP3 --check exits 0 and leaves both artifacts byte- and mtime-stable",
           rc == 0 and (h0.st_size, h0.st_mtime_ns) == (h1.st_size, h1.st_mtime_ns)
           and (j0.st_size, j0.st_mtime_ns) == (j1.st_size, j1.st_mtime_ns),
           "rc=%s" % rc)

        # ---- AC-FYP4: the standing compliance faces are on the page ----
        miss = [c for c in mod.COMPLIANCE if c not in html]
        ok("AC-FYP4 every standing compliance face is rendered", not miss,
           "compliance=%d missing=%d" % (len(mod.COMPLIANCE), len(miss)))

        # ---- AC-FYP5: the page opens offline ----
        ok("AC-FYP5 the page holds no absolute url",
           "http://" not in html and "https://" not in html)

        # ---- AC-FYP6: recorded sizes are a fixpoint ----
        real = {"html": os.path.getsize(html_path), "json": os.path.getsize(json_path)}
        ok("AC-FYP6 recorded sizes equal the bytes on disk", doc["sizes"] == real,
           "recorded=%s disk=%s" % (doc["sizes"], real))
        html2, text2, d2 = mod.build()
        html3, text3, _ = mod.build()
        ok("AC-FYP6 the build reaches a fixed point on both artifacts",
           html2 == html3 and text2 == text3 and d2["sizes"] == real)

        # ---- AC-FYP7: the verdict is the pinned rule applied to a FRESH read ----
        ok("AC-FYP7 the landed verdict equals the rule applied to a fresh derive",
           doc["verdict"] == fresh["verdict"] and doc["top_edge"] == fresh["top_edge"],
           "verdict=%s" % fresh["verdict"])
        # The pinned rule prefers physical blockers over code state, so the
        # control clears the physical and decision counts FIRST; only then can a
        # carrier flip reach the BLOCKED-CODE branch and be named.
        pay = os.path.join(world, "preview", "payment-gate-report.json")
        ceo = os.path.join(world, "preview", "ceo-blockers.json")
        keep_pay = read(pay)
        keep_ceo = read(ceo)
        doc_ceo = json.loads(keep_ceo)
        doc_ceo["counts"] = {"PENDING-PHYSICAL": 0, "PENDING-DECISION": 0}
        doc_ceo["rows"] = []
        with io.open(ceo, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc_ceo))
        cleared = mod.derive()
        ok("AC-FYP7 with no blockers the rule falls to code and names C6 (UGC hole)",
           cleared["verdict"] == "BLOCKED-CODE" and "C6" in cleared["top_edge"],
           "verdict=%s edge=%s" % (cleared["verdict"], cleared["top_edge"]))
        broken = json.loads(keep_pay)
        broken["verdict"] = "FAIL"
        with io.open(pay, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(broken))
        moved = mod.derive()
        ok("AC-FYP7 flipping C3 adds it to the named code edge",
           moved["verdict"] == "BLOCKED-CODE" and "C3" in moved["top_edge"]
           and "C6" in moved["top_edge"],
           "verdict=%s edge=%s" % (moved["verdict"], moved["top_edge"]))
        with io.open(pay, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(keep_pay)
        with io.open(ceo, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(keep_ceo)
        ok("AC-FYP7 restoring both reports returns the verdict",
           mod.derive()["verdict"] == fresh["verdict"])
    finally:
        shutil.rmtree(world, ignore_errors=True)

    # ---- hygiene ----
    bad_bytes = [b for b in src if ord(b) > 127]
    ok("AC-FYP7 suite source is pure ASCII", not bad_bytes,
       "non_ascii=%d" % len(bad_bytes))
    net = [m for m in ("urllib", "requests", "socket", "http.client", "subprocess")
           if ("import " + m) in src]
    ok("AC-FYP7 suite has no network and no shell import", not net, "found=%s" % net)

    total = len(CHECKS)
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s" % (total - len(FAILS), total, FAILS))
        return 1
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
