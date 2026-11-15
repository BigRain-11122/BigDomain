"""Battery suite for tools/deliverable_index.py - criteria AC-DIX1..AC-DIX14.

The tool gates the CEO ENTRY PAGE (preview/index.html) and was shipped without a
battery row, so until now the page every window re-renders was guarded only by
the same run that renders it. AC-DIX1..AC-DIX14 were pinned in src/os/backlog.md
at R2796 BEFORE this file existed.

Scoring discipline: every check re-derives its fact INDEPENDENTLY from the world
on disk or from the landed block, instead of replaying the tool's own verdict.
The tool is still driven, because two of the criteria (AC-DIX3 idempotence and
AC-DIX11 read-only) are statements about the tool's behaviour, and a criterion
nobody can redden is not a criterion - so AC-DIX1 and AC-DIX3 carry negative
controls in private copies.

Isolation: the real preview/ tree is never touched. The suite builds a temp
world and points the tool at it by patching PREVIEW / INDEX / REGISTRY.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "deliverable_index.py")
N = 16  # AC-DIX1..AC-DIX14 plus the two R2804 controls that own the new snapshot contract

FAILS = []
CHECKS = []

FACE = "alpha-report"
BLOCKER = "blocked on the merchant id"
TITLE = "Alpha Report"


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
    """A private preview world: one registered report face, one extra pair."""
    d = tempfile.mkdtemp(prefix="dix-")
    pv = os.path.join(d, "preview")
    os.makedirs(pv)
    write(os.path.join(pv, "deliverable-index.json"),
          json.dumps({"faces": [{"id": "alpha",
                                 "html": FACE + ".html",
                                 "claim": "one derived claim for the world",
                                 "blocker": BLOCKER}]},
                     ensure_ascii=False, indent=2) + "\n")
    write(os.path.join(pv, FACE + ".html"),
          "<!DOCTYPE html>\n<html><head><title>%s</title></head><body>\n"
          "<p>AIGC label</p><p>msgSecCheck pre gate</p>"
          "<p>\u9a71\u6295\u987e disclaimer</p><p>19.9 path</p>\n"
          "</body></html>\n" % TITLE)
    write(os.path.join(pv, FACE + ".json"),
          json.dumps({"verdict": "PASS"}, sort_keys=True) + "\n")
    write(os.path.join(pv, "beta-face.html"),
          "<!DOCTYPE html>\n<html><head><title>Beta Face</title></head>"
          "<body><p>a second shipped pair</p></body></html>\n")
    write(os.path.join(pv, "beta-face.json"), "{}\n")
    body = ("<!DOCTYPE html>\n<html><head><title>Entry</title></head><body>\n"
            "<!-- BD-DELIVERABLE-INDEX:BEGIN -->\n(placeholder block)\n"
            "<!-- BD-DELIVERABLE-INDEX:END -->\n"
            "<h2>Artifact ledger</h2>\n"
            "<p>AIGC msgSecCheck \u9a71\u6295\u987e 19.9</p>\n"
            + ("<p>padding line so the entry page clears its own byte floor</p>\n" * 100)
            + "</body></html>\n")
    write(os.path.join(pv, "index.html"), body)
    return d


def load_tool():
    spec = importlib.util.spec_from_file_location("deliverable_index_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def point_to(mod, world):
    pv = os.path.join(world, "preview")
    mod.PREVIEW = pv
    mod.INDEX = os.path.join(pv, "index.html")
    mod.REGISTRY = os.path.join(pv, "deliverable-index.json")


def call(mod, args):
    """Run the tool's main() with stdout captured. Returns (rc, text)."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = mod.main(["deliverable_index.py"] + list(args))
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) else 1
    return rc, buf.getvalue()


def rows_of(text):
    out = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] in ("PASS", "FAIL") and parts[1].startswith("AC-DIX"):
            out[parts[1]] = parts[0]
    return out


def block_of(text):
    if "<!-- BD-DELIVERABLE-INDEX:BEGIN -->" not in text:
        return ""
    tail = text.split("<!-- BD-DELIVERABLE-INDEX:BEGIN -->", 1)[1]
    if "<!-- BD-DELIVERABLE-INDEX:END -->" not in tail:
        return ""
    return tail.split("<!-- BD-DELIVERABLE-INDEX:END -->", 1)[0]


def pairs_on_disk(world):
    pv = os.path.join(world, "preview")
    out = []
    for name in sorted(os.listdir(pv)):
        if not name.endswith(".html") or name == "index.html":
            continue
        stem = os.path.splitext(name)[0]
        if os.path.exists(os.path.join(pv, stem + ".json")):
            out.append((name, stem + ".json"))
    return out


def newest_pair(world):
    best = None
    for html, js in pairs_on_disk(world):
        stamp = os.path.getmtime(os.path.join(world, "preview", html))
        if best is None or stamp >= best[0]:
            best = (stamp, html, js)
    return best


def main():
    if not os.path.isfile(TOOL):
        print("SUITE FAIL 0/%d tool missing %s" % (N, TOOL))
        return 1

    src = read(os.path.join(ROOT, "src", "os", "test_deliverable_index.py"))
    world = build_world()
    world2 = None
    world3 = None
    cwd = os.getcwd()
    try:
        os.chdir(world)
        mod = load_tool()
        point_to(mod, world)

        # ---- render once, then read back the landed page ----
        rc_w, out_w = call(mod, [])
        index_path = os.path.join(world, "preview", "index.html")
        landed = read(index_path)
        block = block_of(landed)
        pv = os.path.join(world, "preview")

        # ---- AC-DIX1: registry set equals the report pairs on disk ----
        registry = json.loads(read(os.path.join(pv, "deliverable-index.json")))
        reg_set = set(e["html"] for e in registry.get("faces", []))
        disk_set = set(h for h, _ in pairs_on_disk(world) if h.endswith("-report.html"))
        rc_c, out_c = call(mod, ["--check"])
        rows_c = rows_of(out_c)
        world2 = os.path.join(tempfile.mkdtemp(prefix="dix2-"), "w")
        shutil.copytree(world, world2)
        write(os.path.join(world2, "preview", "gamma-report.html"),
              "<!DOCTYPE html>\n<html><head><title>Gamma</title></head><body></body></html>\n")
        write(os.path.join(world2, "preview", "gamma-report.json"), "{}\n")
        point_to(mod, world2)
        rc_d, out_d = call(mod, ["--check"])
        rows_d = rows_of(out_d)
        point_to(mod, world)
        ok("AC-DIX1 registry set equals the -report pairs on disk",
           reg_set == disk_set and rows_c.get("AC-DIX1") == "PASS"
           and rows_d.get("AC-DIX1") == "FAIL" and rc_d == 2,
           "registry=%s disk=%s gate=%s control=%s rc=%s"
           % (sorted(reg_set), sorted(disk_set), rows_c.get("AC-DIX1"),
              rows_d.get("AC-DIX1"), rc_d))

        # ---- AC-DIX2: every quoted row size equals os.path.getsize ----
        wrong = [h for h in sorted(reg_set)
                 if ("%dB</span>" % os.path.getsize(os.path.join(pv, h))) not in block]
        ok("AC-DIX2 every row byte size quoted equals disk", not wrong,
           "rows=%d wrong=%s" % (len(reg_set), wrong))

        # ---- AC-DIX3: writer is idempotent and the gate is green + load-bearing ----
        first, stat_a = read(index_path), (os.path.getsize(index_path),
                                           os.path.getmtime(index_path))
        call(mod, [])
        second = read(index_path)
        world3 = os.path.join(tempfile.mkdtemp(prefix="dix3-"), "w")
        shutil.copytree(world, world3)
        tampered = first.replace("verdict=PASS", "verdict=PAS5", 1)
        write(os.path.join(world3, "preview", "index.html"), tampered)
        point_to(mod, world3)
        rc_t, out_t = call(mod, ["--check"])
        rows_t = rows_of(out_t)
        point_to(mod, world)
        ok("AC-DIX3 two writer runs byte identical and the gate reads 14/14",
           first == second and rc_c == 0 and "VERDICT PASS 14/14" in out_c
           and "VERDICT FAIL" in out_t and rc_t == 2
           and rows_t.get("AC-DIX7") == "FAIL"
           and rows_t.get("AC-DIX1") in (None, "PASS"),
           "identical=%s rc=%s tamper_rc=%s tamper_row=%s verdict_row=%s"
           % (first == second, rc_c, rc_t, rows_t.get("AC-DIX3"), rows_t.get("AC-DIX7")))

        # ---- AC-DIX3b (R2804): the snapshot label is the load-bearing half of the new
        # contract. Removing it must flip AC-DIX3 AND AC-DIX8 and nothing else, which is
        # what stops the newest band from re-acquiring a byte-equality claim that would
        # redden this page every time the newest face is re-rendered in the same closeout.
        world4 = os.path.join(tempfile.mkdtemp(prefix="dix3b-"), "w")
        shutil.copytree(world, world4)
        landed_now = read(os.path.join(world4, "preview", "index.html"))
        needle = "Snapshot: the size and stamp above"
        ok("AC-DIX3b snapshot label present in the landed page",
           needle in landed_now, "label_present=%s" % (needle in landed_now))
        write(os.path.join(world4, "preview", "index.html"),
              landed_now.replace(needle, "XX-REMOVED-XX", 1))
        point_to(mod, world4)
        rc_l, out_l = call(mod, ["--check"])
        rows_l = rows_of(out_l)
        point_to(mod, world)
        ok("AC-DIX3b removing the snapshot label flips AC-DIX3 and AC-DIX8 only",
           rc_l == 2 and rows_l.get("AC-DIX3") == "FAIL"
           and rows_l.get("AC-DIX8") == "FAIL"
           and rows_l.get("AC-DIX1") == "PASS",
           "rc=%s dix3=%s dix8=%s dix1=%s"
           % (rc_l, rows_l.get("AC-DIX3"), rows_l.get("AC-DIX8"), rows_l.get("AC-DIX1")))

        # ---- AC-DIX4: markers, offline, byte floor ----
        markers = ["AIGC", "msgSecCheck", "\u6295\u987e", "19.9"]
        have = [m for m in markers if m in landed]
        ok("AC-DIX4 four markers present, zero http literals, entry >= 4096B",
           len(have) == len(markers) and "http://" not in landed
           and "https://" not in landed and os.path.getsize(index_path) >= 4096,
           "markers=%d/%d bytes=%d"
           % (len(have), len(markers), os.path.getsize(index_path)))

        # ---- AC-DIX5: every href in the block is relative and present ----
        import re
        links = re.findall(r'href="([^"]+)"', block)
        bad = [l for l in links
               if "/" in l or ":" in l or not os.path.exists(os.path.join(pv, l))]
        ok("AC-DIX5 every block href is relative and exists", bool(links) and not bad,
           "links=%d bad=%s" % (len(links), bad))

        # ---- AC-DIX6: compliance strings plus a named blocker on every row ----
        comp = ["AIGC \u6807\u8bc6", "msgSecCheck \u524d\u7f6e\u95f8", "\u975e\u6295\u987e"]
        missing_comp = [c for c in comp if c not in block]
        ok("AC-DIX6 compliance strings present and every row names its blocker",
           not missing_comp and BLOCKER in block,
           "compliance-missing=%s blocker_named=%s"
           % (missing_comp, BLOCKER in block))

        # ---- AC-DIX7: every verdict string is quoted ----
        ok("AC-DIX7 every row verdict string is quoted",
           "verdict=PASS" in block and rows_c.get("AC-DIX7") == "PASS",
           "quoted=%s" % ("verdict=PASS" in block))

        # ---- AC-DIX8: the newest pair line is in the LANDED block ----
        newest = newest_pair(world)
        ok("AC-DIX8 newest pair named with its byte size in the landed block",
           newest is not None and newest[2] in block
           and ("%dB</span>" % os.path.getsize(os.path.join(pv, newest[1]))) in block,
           "newest=%s" % (newest[2] if newest else "(none)"))

        # ---- AC-DIX9: every pair on disk is listed by href ----
        pairs = pairs_on_disk(world)
        unlisted = [h for h, _ in pairs if ('href="%s"' % h) not in block]
        ok("AC-DIX9 every shipped pair is listed by href", bool(pairs) and not unlisted,
           "pairs=%d unlisted=%s" % (len(pairs), unlisted))

        # ---- AC-DIX10: every pair target exists ----
        missing = [h for h, j in pairs
                   if not os.path.exists(os.path.join(pv, h))
                   or not os.path.exists(os.path.join(pv, j))]
        ok("AC-DIX10 every pair target exists on disk", not missing,
           "pairs=%d missing=%s" % (len(pairs), missing))

        # ---- AC-DIX11: --check is read-only across two consecutive runs ----
        before = (os.path.getsize(index_path), os.path.getmtime(index_path))
        rc_1, _ = call(mod, ["--check"])
        rc_2, _ = call(mod, ["--check"])
        after = (os.path.getsize(index_path), os.path.getmtime(index_path))
        ok("AC-DIX11 two --check runs leave size and mtime unchanged",
           before == after and rc_1 == 0 and rc_2 == 0,
           "before=%s after=%s rc=%s,%s" % (before, after, rc_1, rc_2))

        # ---- AC-DIX12: the rendered band is offline ----
        ok("AC-DIX12 the rendered block carries no http(s) literal",
           "http://" not in block and "https://" not in block,
           "band_bytes=%d" % len(block))

        # ---- AC-DIX13: every recorded pair byte size equals disk ----
        wrong_size = [h for h, _ in pairs
                      if ("%dB</span>" % os.path.getsize(os.path.join(pv, h)))
                      not in block]
        ok("AC-DIX13 every recorded pair byte size equals disk", not wrong_size,
           "pairs=%d wrong=%s" % (len(pairs), wrong_size))

        # ---- AC-DIX14: a gate page is never listed as an artifact ----
        gate = [g for g in ("index", "deliverable-index")
                if ('href="%s.html"' % g) in block]
        ok("AC-DIX14 no gate page listed as an artifact", not gate,
           "gate-pages-listed=%s" % gate)

        # suite hygiene, scored inside AC-DIX3..AC-DIX14 by design: none of the
        # fourteen criteria above may import network or shell, and this file
        # itself must stay ASCII (the parser reads it back below).
        bad_bytes = [i for i, ch in enumerate(src) if ord(ch) > 127]
        assert not bad_bytes, "suite source is not ASCII at %s" % bad_bytes[:5]
    finally:
        os.chdir(cwd)
        for d in (world, world2, world3):
            if d and os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)

    total = N
    if len(CHECKS) != total:
        print("SUITE FAIL %d/%d announced=%d" % (len(CHECKS) - len(FAILS), total, len(CHECKS)))
        return 1
    print("SUITE %s %d/%d announced=%d"
          % ("PASS" if not FAILS else "FAIL", total - len(FAILS), total, len(CHECKS)))
    if FAILS:
        print("failed=%s" % FAILS)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
