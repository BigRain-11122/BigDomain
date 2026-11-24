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
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "deliverable_index.py")
N = 28  # AC-DIX1..14, the two R2804 snapshot controls, the R2883 html-only controls,
#         the two R3232 claims-age controls, the three R3234 claims-readings controls,
#         and the five R3393 byte-width arms AC-BYI1..5 registered by R3397

FAILS = []
CHECKS = []
# R3353: the arms and the criteria are two units. The registry row counts the
# AC ids the run grades; this suite runs 23 arms over them, and the closing
# SUITE row states both so no reader has to guess which number is which.
GATE_IDS = []
ID_RE = re.compile(r"^(AC-(?:DIX|CVL|IDX|COO|BYI)\d+)[a-z]?$")


def arm_ids(names):
    """The distinct AC criteria these arm names grade, suffix arms collapsed."""
    out = []
    for name in names:
        token = name.split()[0] if name.split() else ""
        match = ID_RE.match(token)
        if match and match.group(1) not in out:
            out.append(match.group(1))
    return out

FACE = "alpha-report"
BLOCKER = "blocked on the merchant id"
TITLE = "Alpha Report"
CENSUS_TS = "2026-11-22T07:00:00+08:00"


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
    # R3301: the entry page carries the first-visit walk over four FIXED faces
    # (buyer_route.FIRST_VISIT). A world without them has links that do not
    # resolve, so AC-DIX5 reddened and every arm needing a green gate failed
    # with it. These four are fixture faces, not criteria; two carry a control
    # so the walk promises something operable (AC-IDX1). They are written
    # BEFORE beta-face so the newest-pair arm still lands on beta-face.
    route = {"start-here.html": "<p>read-only summary of today</p>",
             "buyer-trial.html": '<button type="button">mock order</button>',
             "merchant-onboard.html": '<input name="merchant" />',
             "money-path-demo.html": '<button type="button">run the path</button>'}
    for href in ("start-here.html", "buyer-trial.html",
                 "merchant-onboard.html", "money-path-demo.html"):
        write(os.path.join(pv, href),
              "<!DOCTYPE html>\n<html><head><title>%s</title></head><body>%s"
              "</body></html>\n" % (href, route[href]))
        write(os.path.join(pv, os.path.splitext(href)[0] + ".json"), "{}\n")
    # keep beta-face the newest artifact regardless of write-clock granularity
    stamp = max(os.path.getmtime(os.path.join(pv, n)) for n in os.listdir(pv))
    for name in ("beta-face.html", "beta-face.json"):
        os.utime(os.path.join(pv, name), (stamp + 5, stamp + 5))
    body = ("<!DOCTYPE html>\n<html><head><title>Entry</title></head><body>\n"
            "<!-- BD-DELIVERABLE-INDEX:BEGIN -->\n(placeholder block)\n"
            "<!-- BD-DELIVERABLE-INDEX:END -->\n"
            "<h2>Artifact ledger</h2>\n"
            "<p>AIGC msgSecCheck \u9a71\u6295\u987e 19.9</p>\n"
            + ("<p>padding line so the entry page clears its own byte floor</p>\n" * 100)
            + "</body></html>\n")
    write(os.path.join(pv, "index.html"), body)
    write(os.path.join(d, "docs", "status-export.json"),
          json.dumps({"export_ts": CENSUS_TS,
                      "claims": {"claimed": 3, "captured": 2, "contradicted": 0,
                                 "uncaptured": 1, "historic": 0, "rows": 1,
                                 "present": True, "census_ts": CENSUS_TS}},
                     sort_keys=True) + "\n")
    # R3301: AC-DIX20 grades frozen-face tags against the freeze manifest. The
    # suite used to leave the tool pointed at the PRODUCTION manifest, so a
    # private page was graded against thirteen faces it never listed - red by
    # construction. The world owns its own manifest now (one frozen face).
    write(os.path.join(d, "state", "apimarket-face-freeze.json"),
          json.dumps({"faces": [{"html": FACE + ".html", "schema_version": 3}]},
                     sort_keys=True) + "\n")
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
    mod.EXPORT = os.path.join(world, "docs", "status-export.json")
    mod.FREEZE = os.path.join(world, "state", "apimarket-face-freeze.json")


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
        if len(parts) >= 2 and parts[0] in ("PASS", "FAIL") \
                and parts[1].startswith(("AC-DIX", "AC-CVL")):
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
    world4 = None
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
                 if ("%s</span>"
                     % mod.BYTES_PAD(os.path.getsize(os.path.join(pv, h))))
                 not in block]
        ok("AC-DIX2 every row byte size quoted equals disk", not wrong,
           "rows=%d wrong=%s" % (len(reg_set), wrong))

        # ---- AC-DIX3: writer is idempotent and the gate is green + load-bearing ----
        first, stat_a = read(index_path), (os.path.getsize(index_path),
                                           os.path.getmtime(index_path))
        call(mod, [])
        second = read(index_path)
        # The gate's printed total used to be pinned as a literal ("17/17"),
        # which rotted silently every time a criterion was added: the arm
        # reddened while the gate itself was healthy. R3301: the total is now
        # graded against the PASS rows the gate itself printed (one row per
        # criterion it recorded), with a floor so a collapsed gate cannot pass.
        pass_rows = [ln for ln in out_c.splitlines() if ln.startswith("PASS ")]
        total = len(pass_rows)
        gate_line = "VERDICT PASS %d/%d" % (total, total)
        world3 = os.path.join(tempfile.mkdtemp(prefix="dix3-"), "w")
        shutil.copytree(world, world3)
        tampered = first.replace("verdict=PASS", "verdict=PAS5", 1)
        write(os.path.join(world3, "preview", "index.html"), tampered)
        point_to(mod, world3)
        rc_t, out_t = call(mod, ["--check"])
        rows_t = rows_of(out_t)
        point_to(mod, world)
        ok("AC-DIX3 two writer runs byte identical and the gate reads all criteria",
           first == second and rc_c == 0 and total >= 20 and gate_line in out_c
           and "VERDICT FAIL" in out_t and rc_t == 2
           and rows_t.get("AC-DIX7") == "FAIL"
           and rows_t.get("AC-DIX1") in (None, "PASS"),
           "identical=%s rc=%s tamper_rc=%s tamper_row=%s verdict_row=%s criteria=%d"
           % (first == second, rc_c, rc_t, rows_t.get("AC-DIX3"), rows_t.get("AC-DIX7"),
              total))

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
           and (("%s</span>"
                 % mod.BYTES_PAD(os.path.getsize(os.path.join(pv, newest[1]))))
                in block),
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
                      if (("%s</span>"
                           % mod.BYTES_PAD(os.path.getsize(os.path.join(pv, h))))
                          not in block)]
        ok("AC-DIX13 every recorded pair byte size equals disk", not wrong_size,
           "pairs=%d wrong=%s" % (len(pairs), wrong_size))

        # ---- AC-DIX14: a gate page is never listed as an artifact ----
        gate = [g for g in ("index", "deliverable-index")
                if ('href="%s.html"' % g) in block]
        ok("AC-DIX14 no gate page listed as an artifact", not gate,
           "gate-pages-listed=%s" % gate)

        # ---- AC-DIX17/AC-DIX18 (pinned 2026-11-17 R2883 BEFORE the tool edit):
        # an html-only face is still a face. The band universe is re-measured
        # from raw html names, so a page without a json sibling is LISTED and
        # LABELLED instead of silently dropping out of the CEO entry page.
        world4 = os.path.join(tempfile.mkdtemp(prefix="dix4-"), "w")
        shutil.copytree(world, world4)
        pv4 = os.path.join(world4, "preview")
        write(os.path.join(pv4, "delta-face.html"),
              "<!DOCTYPE html>\n<html><head><title>Delta</title></head>"
              "<body><p>landed without a json sibling</p></body></html>\n")
        point_to(mod, world4)
        call(mod, [])
        block4 = block_of(read(os.path.join(pv4, "index.html")))

        def row_of(block_text, name):
            # R3301: a fixed 400-char window ran into the NEXT row once the
            # first-visit faces joined the band, so beta-face was accused of a
            # label that belonged to delta-face. A row ends at its </li>.
            at = block_text.find('href="%s"' % name)
            if at < 0:
                return ""
            end = block_text.find("</li>", at)
            return block_text[at:end if end > 0 else at + 400]

        rc_4, out_4 = call(mod, ["--check"])
        rows_4 = rows_of(out_4)
        delta_at = block4.find('href="delta-face.html"')
        delta_label = "json=missing" in row_of(block4, "delta-face.html")
        beta_at = block4.find('href="beta-face.html"')
        beta_clean = "json=missing" not in row_of(block4, "beta-face.html")
        os.remove(os.path.join(pv4, "delta-face.html"))
        call(mod, [])
        block4b = block_of(read(os.path.join(pv4, "index.html")))
        rc_4b, out_4b = call(mod, ["--check"])
        rows_4b = rows_of(out_4b)
        point_to(mod, world)
        ok("AC-DIX17 an html-only face is listed and labelled incomplete by the gate",
           delta_at >= 0 and delta_label and rows_4.get("AC-DIX17") == "PASS"
           and rc_4 == 0,
           "listed=%s label=%s gate=%s rc=%s"
           % (delta_at >= 0, delta_label, rows_4.get("AC-DIX17"), rc_4))
        ok("AC-DIX18 negative control: the label is load-bearing, the row leaves with its html",
           beta_clean and 'href="delta-face.html"' not in block4b
           and rows_4b.get("AC-DIX17") == "PASS" and rc_4b == 0,
           "paired-unlabelled=%s gone=%s gate=%s"
           % (beta_clean, 'href="delta-face.html"' not in block4b,
              rows_4b.get("AC-DIX17")))

        # ---- AC-DIX19: the static page prints the export's census moment, and a
        # page left behind by an --apply reddens rather than keeping a quiet stamp ----
        point_to(mod, world)
        block5 = block_of(read(os.path.join(pv, "index.html")))
        printed_now = ("census day %s" % CENSUS_TS[:10]) in block5
        rc_5, out_5 = call(mod, ["--check"])
        rows_5 = rows_of(out_5)
        moved = "2026-11-23T09:30:00+08:00"
        write(os.path.join(world, "docs", "status-export.json"),
              json.dumps({"export_ts": moved,
                          "claims": {"claimed": 3, "captured": 2, "contradicted": 0,
                                     "uncaptured": 1, "historic": 0, "rows": 1,
                                     "present": True, "census_ts": moved}},
                         sort_keys=True) + "\n")
        rc_6, out_6 = call(mod, ["--check"])
        rows_6 = rows_of(out_6)
        call(mod, [])
        rc_7, out_7 = call(mod, ["--check"])
        rows_7 = rows_of(out_7)
        ok("AC-DIX19 the landed page prints the export census moment it was rendered from",
           printed_now and rc_5 == 0 and rows_5.get("AC-DIX19") == "PASS",
           "printed=%s gate=%s rc=%s" % (printed_now, rows_5.get("AC-DIX19"), rc_5))
        ok("AC-DIX19 negative control: an --apply the page never followed reddens the gate",
           rc_6 == 2 and rows_6.get("AC-DIX19") == "FAIL" and rc_7 == 0
           and rows_7.get("AC-DIX19") == "PASS",
           "stale_rc=%s stale_gate=%s rerendered_gate=%s"
           % (rc_6, rows_6.get("AC-DIX19"), rows_7.get("AC-DIX19")))

        # ---- AC-CVL1/AC-CVL2 (pinned 2026-11-22 R3234 BEFORE this tool edit):
        # the six printed numbers are judged, not only the moment beside them.
        point_to(mod, world)
        call(mod, [])
        index_path = os.path.join(pv, "index.html")
        page_cvl = read(index_path)
        live_readings = ("claimed=3 captured=2 contradicted=0 uncaptured=1 "
                         "historic=0 records=1")
        write(index_path, page_cvl.replace("contradicted=0",
                                           "contradicted=999", 1))
        rc_c1, out_c1 = call(mod, ["--check"])
        rows_c1 = rows_of(out_c1)
        call(mod, [])
        rc_c2, out_c2 = call(mod, ["--check"])
        rows_c2 = rows_of(out_c2)
        ok("AC-CVL1 the landed page prints exactly the live six readings",
           live_readings in page_cvl and rows_c2.get("AC-CVL1") == "PASS"
           and rc_c2 == 0,
           "printed=%s gate=%s" % (live_readings in page_cvl,
                                   rows_c2.get("AC-CVL1")))
        ok("AC-CVL1 negative control: one drifted number reddens CVL1 while the moment row stays green",
           rc_c1 == 2 and rows_c1.get("AC-CVL1") == "FAIL"
           and rows_c1.get("AC-DIX19") == "PASS",
           "rc=%s cvl=%s dix19=%s"
           % (rc_c1, rows_c1.get("AC-CVL1"), rows_c1.get("AC-DIX19")))
        zero_claims = {"claimed": 0, "captured": 0, "contradicted": 0,
                       "uncaptured": 0, "historic": 0, "rows": 0,
                       "present": False}
        write(os.path.join(world, "docs", "status-export.json"),
              json.dumps({"export_ts": CENSUS_TS, "claims": zero_claims},
                         sort_keys=True) + "\n")
        rc_c3, out_c3 = call(mod, ["--check"])
        rows_c3 = rows_of(out_c3)
        call(mod, [])
        rc_c4, out_c4 = call(mod, ["--check"])
        rows_c4 = rows_of(out_c4)
        ok("AC-CVL2 an export without readings reddens a page still printing six numbers",
           rc_c3 == 2 and rows_c3.get("AC-CVL2") == "FAIL"
           and rows_c4.get("AC-CVL2") == "PASS" and rc_c4 == 0,
           "stale=%s rendered=%s"
           % (rows_c3.get("AC-CVL2"), rows_c4.get("AC-CVL2")))

        # R3353: the unit law. The gate rows are the criteria the registry
        # counts, so they are read from the last clean render rather than
        # spelled as a literal; an arm that names an id the gate never reports
        # is a red here instead of a silent undercount in the SUITE row.
        GATE_IDS[:] = sorted(rows_of(out_c4))

        # ---- AC-BYI1..AC-BYI5 (pinned at R3393, registered by R3397): the page's
        # own size must stop being an input to itself. Every printed byte count
        # goes through ONE fixed-width formatter, so a pair whose byte count moves
        # inside one digit width cannot move the page it is listed on.
        toolsrc = read(TOOL)
        width_defs = toolsrc.count("BYTES_WIDTH = ")
        pad_defs = toolsrc.count("def BYTES_PAD(")
        bare_fmt = [ln.strip() for ln in toolsrc.splitlines()
                    if '"%dB"' in ln or "'%dB'" in ln]
        point_to(mod, world)
        call(mod, [])
        band_y = block_of(read(os.path.join(pv, "index.html")))
        sizes = re.findall(r"([ ]*\d+B)", band_y)
        padded = [s for s in sizes if len(s) == mod.BYTES_WIDTH + 1]
        face_size = os.path.getsize(os.path.join(pv, FACE + ".html"))
        face_row = ("%s</span>" % mod.BYTES_PAD(face_size)) in band_y
        # R3397 carve-out, measured rather than assumed: the block embeds one
        # walk fragment written by ANOTHER module, whose four byte counts are
        # printed in that module's own shape. Those rows are named by their
        # marker; every other byte count on this page must carry the pinned
        # width, so a new unpadded print anywhere else reddens here.
        ctl_marker = "\u4e2a\u63a7\u4ef6"
        short = [t for t in sizes if len(t) != mod.BYTES_WIDTH + 1]
        short_lines = [ln for ln in band_y.splitlines()
                       if any(t in ln for t in short)]
        carve_ok = all(ctl_marker in ln for ln in short_lines)
        ok("AC-BYI1 one fixed-width formatter and every printed size uses it",
           width_defs == 1 and pad_defs == 1 and not bare_fmt and bool(sizes)
           and len(padded) == len(sizes) - len(short) and face_row and carve_ok,
           "width_defs=%d pad_defs=%d bare=%s sizes=%d padded=%d foreign=%d carve=%s row=%s"
           % (width_defs, pad_defs, bare_fmt[:2], len(sizes), len(padded),
              len(short), carve_ok, face_row))

        probe = [0, 1, 9, 10, 99, 1000, 28799, 1234567, 999999999]
        widths = sorted(set(len(mod.BYTES_PAD(v)) for v in probe))
        exact = all(mod.BYTES_PAD(v).replace(" ", "") == ("%dB" % v)
                    for v in probe)
        reg_faces = json.loads(
            read(os.path.join(pv, "deliverable-index.json")))["faces"]
        unpadded = [e["html"] for e in reg_faces
                    if mod.BYTES_PAD(
                        os.path.getsize(os.path.join(pv, e["html"]))) not in band_y]
        ok("AC-BYI2 the printed number still equals the bytes on disk",
           exact and widths == [mod.BYTES_WIDTH + 1] and not unpadded
           and face_size > 0,
           "widths=%s exact=%s unpadded=%s" % (widths, exact, unpadded))

        # AC-BYI3: same digit width, different value -> the entry page must land
        # the same number of bytes. Measured by rendering two worlds that differ
        # only in one listed pair's byte count.
        world5 = os.path.join(tempfile.mkdtemp(prefix="dix5-"), "w")
        shutil.copytree(world, world5)
        target = os.path.join(world5, "preview", "beta-face.html")
        start_n = os.path.getsize(target)
        while len(str(os.path.getsize(target))) == len(str(start_n)) \
                and os.path.getsize(target) - start_n < 40:
            with io.open(target, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(" <!-- w -->")
        moved_n = os.path.getsize(target)
        call(mod, [])
        page_a = os.path.getsize(os.path.join(pv, "index.html"))
        mod_repo_before = mod.REPO
        point_to(mod, world5)
        call(mod, [])
        page_b = os.path.getsize(os.path.join(world5, "preview", "index.html"))
        point_to(mod, world)
        call(mod, [])
        ok("AC-BYI3 a same-width byte change leaves the entry page size unmoved",
           len(str(start_n)) == len(str(moved_n)) and moved_n != start_n
           and page_a == page_b and page_a > 4096,
           "pair=%d->%d page=%d,%d" % (start_n, moved_n, page_a, page_b))
        mod.REPO = mod_repo_before
        shutil.rmtree(os.path.dirname(world5), ignore_errors=True)

        # AC-BYI4: a declared two-step recipe settles in ONE check pass. The
        # private world owns both writers, so the shipped recipe arm runs end to
        # end without touching the real preview/ tree.
        world6 = os.path.join(tempfile.mkdtemp(prefix="dix6-"), "w")
        shutil.copytree(world, world6)
        renderer = os.path.join(world6, "tmp_recipe_render.py")
        injector = os.path.join(world6, "tmp_recipe_inject.py")
        write(renderer,
              "import io, os\n"
              "HERE = os.path.dirname(os.path.abspath(__file__))\n"
              "PV = os.path.join(HERE, 'preview')\n"
              "def put(name, text):\n"
              "    with io.open(os.path.join(PV, name), 'w', encoding='utf-8',\n"
              "                 newline='\\n') as fh:\n"
              "        fh.write(text)\n"
              "put('recipe-face.json', '{\"verdict\": \"PASS\"}\\n')\n"
              "put('recipe-face.html',\n"
              "    '<!DOCTYPE html>\\n<html><body>recipe face</body></html>\\n')\n"
              "print('RECIPE RENDER OK')\n")
        write(injector,
              "import io, os\n"
              "HERE = os.path.dirname(os.path.abspath(__file__))\n"
              "P = os.path.join(HERE, 'preview', 'recipe-face.html')\n"
              "text = io.open(P, encoding='utf-8').read()\n"
              "if 'back-hop' not in text:\n"
              "    text = text.replace('</body>', '<!-- back-hop --></body>')\n"
              "    with io.open(P, 'w', encoding='utf-8', newline='\\n') as fh:\n"
              "        fh.write(text)\n"
              "print('RECIPE INJECT OK')\n")

        def run_recipe_world(world_x, inject_path):
            mod.REPO = world_x
            mod.PAIR_RECIPES["recipe-face.json"] = (
                "tmp_recipe_render.py", os.path.basename(inject_path), [])
            point_to(mod, world_x)
            for script in (os.path.join(world_x, "tmp_recipe_render.py"),
                           inject_path):
                subprocess.run([sys.executable, script], cwd=world_x,
                               capture_output=True, text=True)
            call(mod, [])
            rc_x, out_x = call(mod, ["--check"])
            row = [ln for ln in out_x.splitlines() if "AC-DIX21" in ln]
            return rc_x, (row[0] if row else "")

        saved_recipes = dict(mod.PAIR_RECIPES)
        saved_repo = mod.REPO
        rc_y4, row_y4 = run_recipe_world(world6, injector)
        world7 = os.path.join(tempfile.mkdtemp(prefix="dix7-"), "w")
        shutil.copytree(world6, world7)
        os.remove(os.path.join(world7, "preview", "recipe-face.html"))
        os.remove(os.path.join(world7, "preview", "recipe-face.json"))
        subprocess.run([sys.executable, os.path.join(world7, "tmp_recipe_render.py")],
                       cwd=world7, capture_output=True, text=True)
        loose = os.path.join(world7, "tmp_recipe_loose.py")
        write(loose,
              "import io, os\n"
              "HERE = os.path.dirname(os.path.abspath(__file__))\n"
              "P = os.path.join(HERE, 'preview', 'recipe-face.html')\n"
              "C = os.path.join(HERE, 'tmp_recipe_counter.txt')\n"
              "n = int(io.open(C).read()) if os.path.exists(C) else 0\n"
              "n += 1\n"
              "io.open(C, 'w').write(str(n))\n"
              "text = io.open(P, encoding='utf-8').read()\n"
              "text = text.replace('</body>', ('<!-- hop -->' * n) + '</body>')\n"
              "with io.open(P, 'w', encoding='utf-8', newline='\\n') as fh:\n"
              "    fh.write(text)\n"
              "print('LOOSE INJECT OK')\n")
        rc_y5, row_y5 = run_recipe_world(world7, loose)
        mod.PAIR_RECIPES = saved_recipes
        mod.REPO = saved_repo
        point_to(mod, world)
        call(mod, [])
        ok("AC-BYI4 a declared recipe settles in one check pass (control reddens)",
           rc_y4 == 0 and "all-arms-green" in row_y4
           and rc_y5 == 2 and "pair-bytes-reproduced=False" in row_y5,
           "rc=%s row=%s control_rc=%s" % (rc_y4, row_y4[:60], rc_y5))
        shutil.rmtree(os.path.dirname(world6), ignore_errors=True)
        shutil.rmtree(os.path.dirname(world7), ignore_errors=True)

        # AC-BYI5: the change is whitespace only, and the law stays written down.
        white = all(mod.BYTES_PAD(v).replace(" ", "") == ("%dB" % v)
                    for v in probe)
        law = "BYTES_WIDTH = 9" in toolsrc and "whitespace collapses" in toolsrc
        ok("AC-BYI5 the width is whitespace only and the law is stated",
           white and law, "whitespace_only=%s law_stated=%s" % (white, law))

        # suite hygiene, scored inside AC-DIX3..AC-CVL2 by design: none of the
        # criteria above may import network or shell, and this file
        # itself must stay ASCII (the parser reads it back below).
        bad_bytes = [i for i, ch in enumerate(src) if ord(ch) > 127]
        assert not bad_bytes, "suite source is not ASCII at %s" % bad_bytes[:5]
    finally:
        os.chdir(cwd)
        for d in (world, world2, world3, world4):
            if d and os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)

    total = N
    criteria = len(set(GATE_IDS) | set(arm_ids(CHECKS)))
    stray = [name.split()[0] for name in CHECKS
             if name.split() and not ID_RE.match(name.split()[0])]
    if len(CHECKS) != total or stray or not GATE_IDS:
        print("SUITE FAIL %d/%d announced=%d arms=%d gate=%d graded=%d stray=%s"
              % (len(CHECKS) - len(FAILS), total, len(CHECKS), total,
                 len(GATE_IDS), criteria, stray or ("no gate rows" if not GATE_IDS else [])))
        return 1
    print("SUITE %s %d/%d announced=%d arms=%d gate=%d graded=%d"
          % ("PASS" if not FAILS else "FAIL", total - len(FAILS), total,
             len(CHECKS), len(CHECKS), len(GATE_IDS), criteria))
    if FAILS:
        print("failed=%s" % FAILS)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
