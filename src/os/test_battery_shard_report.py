"""Battery suite for tools/battery_shard_report.py - AC-BSRB1..AC-BSRB12.

The eight criteria of the tool (AC-BSR1..AC-BSR8) were pinned in
src/os/backlog.md at R2799/R2800, BEFORE the tool existed.  The tool shipped
with its own --check and --control and NO row in src/sandbox/reconcile_all.py,
so for two windows the face that decides whether six families are green was
graded only by the run that rendered it.  The guard shape below
(AC-BSRB1..AC-BSRB8, pinned in src/os/backlog.md at R2801 BEFORE this file
existed) puts those eight under a battery row.

Scope, stated honestly: this suite never runs a real family.  A family is tens
of seconds of child processes and the R2800 six-family measurement already
stands as that evidence.  AC-BSRB10 (R3081) added ONE one-suite real leg
(os-debt-gate, ~1s) because a synthetic-only fixture is what let the reader go
stale while this suite stayed green; everything else is graded through the real
functions with synthetic streams in a PRIVATE world under the
system temp directory, which is removed before the run ends.

Every check is read-only against the repo: the landed report pair, the tool and
the registry are stat-signed before and after.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import contextlib
import copy
import hashlib
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
TOOLS = os.path.join(ROOT, "tools")
TOOL = os.path.join(TOOLS, "battery_shard_report.py")
SHARD = os.path.join(TOOLS, "battery_shard.py")
REGISTRY = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")
PAIR_JSON = os.path.join(ROOT, "preview", "battery-shard-report.json")
PAIR_HTML = os.path.join(ROOT, "preview", "battery-shard-report.html")

FAILS = []
CHECKS = []


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print("  | PASS %s %s" % (name, detail))
    else:
        FAILS.append(name)
        print("  | FAIL %s %s" % (name, detail))


def read_text(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def stat_sig(path):
    if not os.path.exists(path):
        return ("absent", 0, "")
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        digest.update(fh.read())
    return (os.path.getsize(path), os.path.getmtime(path),
            digest.hexdigest()[:16])


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stream(reg_suites, reg_crit, rows, close, legacy=False, unchecked=0,
           timeout_labels=()):
    """Build runner stdout.

    AC-BSRB10 (R3081): the default is the SHIPPED row shape - detail= on every
    row, an optional timeout=yes tail, and the closing row's crit_checked /
    crit_unchecked fields. This fixture used to be built from the PRE-R2919
    shape, which is exactly why the report reader could go stale for many
    rounds with this suite still green. legacy=True keeps the old shapes only
    for the backward-compatibility arm.
    """
    sel = sum(1 for r in rows)
    crit = sum(int(r[5]) for r in rows)
    lines = ["SHARD scope=SHARD registry_suites=%d registry_criteria=%d "
             "selected=%d selected_criteria=%d"
             % (reg_suites, reg_crit, sel, crit)]
    for label, rc, passed, failed, suite, crits, secs in rows:
        if legacy:
            lines.append("SHARD row %s rc=%d pass=%d fail=%d suite=%s "
                         "crit=%d %.1fs"
                         % (label, rc, passed, failed, suite, crits, secs))
            continue
        lines.append("SHARD row %s rc=%d pass=%d fail=%d detail=yes suite=%s "
                     "crit=%d %.1fs%s"
                     % (label, rc, passed, failed, suite, crits, secs,
                        " timeout=yes" if label in timeout_labels else ""))
    rc, executed, green, elapsed = close
    if legacy:
        lines.append("SHARD rc=%d scope=SHARD selected=%d executed=%d green=%d "
                     "criteria=%d crit_mismatch=0 elapsed=%.1fs"
                     % (rc, sel, executed, green, crit, elapsed))
    else:
        lines.append("SHARD rc=%d scope=SHARD selected=%d executed=%d green=%d "
                     "criteria=%d crit_mismatch=0 elapsed=%.1fs "
                     "crit_checked=%d crit_unchecked=%d"
                     % (rc, sel, executed, green, crit, elapsed,
                        sel - unchecked, unchecked))
    return "\n".join(lines) + "\n"


GREEN_ROWS = (("probe-a", 0, 3, 0, "SUITE PASS 3/3", 3, 0.1),
              ("probe-b", 0, 2, 0, "SUITE PASS 2/2", 2, 0.2))
RED_ROWS = (("probe-a", 0, 3, 0, "SUITE PASS 3/3", 3, 0.1),
            ("probe-c", 1, 0, 2, "SUITE FAIL 0/2", 2, 0.2))


def main():
    bsr = load("bsr_under_test", TOOL)
    sys.path.insert(0, TOOLS)
    import battery_shard as shard

    src_tool = read_text(TOOL)
    sig_pair = (stat_sig(PAIR_JSON), stat_sig(PAIR_HTML))
    sig_tool = stat_sig(TOOL)
    sig_reg = stat_sig(REGISTRY)

    # AC-BSRB1 - registry-by-import, re-derived by this suite's own loop.
    rows, _base, _cap, _ov = shard.registry()
    n_suites = len(rows)
    n_crit = sum(int(r[2]) for r in rows)
    mine = {}
    for prefix, key, _guards in bsr.FAMILIES:
        picked = [r for r in rows if str(r[0]).startswith(prefix)]
        mine[key] = (len(picked), sum(int(r[2]) for r in picked))
    got = bsr.expected_from_registry()
    lit_guard = [n for n in (n_suites, n_crit)
                 if re.search(r"(?<![0-9])%d(?![0-9])" % n, src_tool)]
    ok("AC-BSRB1",
       (got[0], got[1]) == (n_suites, n_crit) and got[2] == mine
       and not lit_guard,
       "suites=%d criteria=%d families=%d exp_equal=%s literals=%d"
       % (n_suites, n_crit, len(mine), got[2] == mine, len(lit_guard)))

    # AC-BSRB2 - the parse IS the only source; a bad stream is refused.
    text = stream(700, 5000, GREEN_ROWS, (0, 2, 2, 1.5))
    fam = bsr.parse_family("probe", "probe-", "guards", 0, text)
    rows_ok = len(fam["suites"]) == 2
    if rows_ok:
        first = fam["suites"][0]
        rows_ok = (first["label"] == "probe-a" and first["rc"] == 0
                   and first["pass"] == 3 and first["fail"] == 0
                   and first["crit"] == 3)
    nums_ok = (fam["registry_suites"] == 700 and fam["registry_criteria"] == 5000
               and fam["selected"] == 2 and fam["selected_criteria"] == 5
               and fam["green"] == 2 and fam["executed"] == 2
               and fam["crit_mismatch"] == 0)
    red_fam = bsr.parse_family("probe", "probe-", "g", 1,
                              stream(700, 5000, RED_ROWS, (2, 2, 1, 2.0)))
    red_ok = red_fam["red"] == ["probe-c"]
    bad = bsr.parse_family("probe", "probe-", "g", 2, "no rows here\n")
    bad_ok = (bad["parse"] == "refused" and bad["selected"] == 0
              and bad["green"] == 0 and bool(bad["reason"]))
    crlf = bsr.parse_family("probe", "probe-", "g", 0,
                            text.replace("\n", "\r\n"))
    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    crlf_ok = (crlf["parse"] == "refused"
               and bsr.parse_family("p", "p-", "g", 0, norm)["parse"] == "ok")
    ok("AC-BSRB2", rows_ok and nums_ok and red_ok and bad_ok and crlf_ok,
       "rows=%s nums=%s red=%s refused=%s crlf_refused=%s"
       % (rows_ok, nums_ok, red_ok, bad_ok, crlf_ok))

    # AC-BSRB3 - registry continuity: disagreement is fatal and writes nothing.
    world = tempfile.mkdtemp(prefix="bsr_suite_")
    preview = os.path.join(world, "preview")
    os.makedirs(preview)
    for name in ("index.html", "lobby-session-trace.html",
                 "ledger-reconcile-face.html"):
        with open(os.path.join(preview, name), "wb") as fh:
            fh.write(b"x\n")
    keep = (bsr.FAMILIES, bsr.run_family, bsr.PREVIEW, bsr.OUT_JSON,
            bsr.OUT_HTML)
    bsr.PREVIEW = preview
    bsr.OUT_JSON = os.path.join(preview, "battery-shard-report.json")
    bsr.OUT_HTML = os.path.join(preview, "battery-shard-report.html")
    drift_msg = ""
    drift_early = False
    try:
        bsr.FAMILIES = (("pa-", "fam-a", "a"), ("pb-", "fam-b", "b"))
        bsr.run_family = lambda prefix: (
            (0, stream(700, 5000, GREEN_ROWS, (0, 2, 2, 1.0)))
            if prefix == "pa-"
            else (0, stream(701, 5000, GREEN_ROWS, (0, 2, 2, 1.0))))
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                bsr.measure()
        except bsr.Refuse as exc:
            drift_msg = str(exc)
        drift_early = (sorted(os.listdir(preview)) ==
                       sorted(["index.html", "lobby-session-trace.html",
                               "ledger-reconcile-face.html"]))
    finally:
        bsr.FAMILIES, bsr.run_family, bsr.PREVIEW, bsr.OUT_JSON, bsr.OUT_HTML = keep
    ok("AC-BSRB3",
       "E_REGISTRY_DRIFT" in drift_msg and drift_early,
       "named=%s no_write=%s" % (bool(drift_msg), drift_early))

    # Build one coherent payload in the private world: family A green, family B
    # red, and a third family whose stream cannot be parsed at all.
    keep = (bsr.FAMILIES, bsr.run_family, bsr.PREVIEW, bsr.OUT_JSON,
            bsr.OUT_HTML)
    bsr.PREVIEW = preview
    bsr.OUT_JSON = os.path.join(preview, "battery-shard-report.json")
    bsr.OUT_HTML = os.path.join(preview, "battery-shard-report.html")
    bsr.FAMILIES = (("pa-", "fam-a", "a"), ("pb-", "fam-b", "b"),
                    ("pc-", "fam-c", "c"))
    canned = {"pa-": (0, stream(700, 5000, GREEN_ROWS, (0, 2, 2, 1.0))),
              "pb-": (2, stream(700, 5000, RED_ROWS, (2, 2, 1, 2.0))),
              "pc-": (2, "garbage stream\n")}
    bsr.run_family = lambda prefix: canned[prefix]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            payload = bsr.measure()
        html = bsr.render_html(payload)
        jtext = bsr.dumps(payload)

        # AC-BSRB4 - red is red, and an unparsable family cannot read green.
        red_named = payload["verdict"] == "RED"
        tot = payload["totals"]
        counts_ok = (tot["red_families"] == 2 and tot["green_families"] == 1
                     and tot["families"] == 3)
        red_row = ("<td class=\"red\">RED</td>" in html)
        refused_row = "fam-c" in html
        ok("AC-BSRB4",
           red_named and counts_ok and red_row and refused_row,
           "verdict=%s red=%d green=%d row_red=%s fam_c=%s"
           % (payload["verdict"], tot["red_families"],
              tot["green_families"], red_row, refused_row))

        # AC-BSRB5 - fixed point plus every total as arithmetic.
        bsr.write_atomic(bsr.OUT_JSON, jtext)
        bsr.write_atomic(bsr.OUT_HTML, html)
        back_json = read_text(bsr.OUT_JSON)
        back_html = read_text(bsr.OUT_HTML)
        exp = {f["key"]: (f["selected"], f["selected_criteria"])
               for f in payload["families"]}
        clean = bsr.check_payload(payload, back_html, back_json, 700, 5000, exp)
        tampered = []

        def reddens(token, mutate):
            bad = copy.deepcopy(payload)
            mutate(bad)
            fails = bsr.check_payload(bad, bsr.render_html(bad), bsr.dumps(bad),
                                      700, 5000, exp)
            # the shipped do_control matches by PREFIX (the tool appends
            # ":<family>" to drift tokens), so the same law is used here
            if any(f.startswith(token) for f in fails):
                tampered.append(token)
            return fails

        reddens("E_REGISTRY_DRIFT",
                lambda p: p["registry"].__setitem__("suites", 701))
        reddens("E_TOTALS_UNCOVERED",
                lambda p: p["totals"].__setitem__(
                    "uncovered_suites", p["totals"]["uncovered_suites"] + 1))
        reddens("E_TOTALS_COVER",
                lambda p: p["totals"].__setitem__(
                    "cover_pct", float(p["totals"]["cover_pct"]) + 1.0))
        reddens("E_TOTALS_RED",
                lambda p: p["totals"].__setitem__("red_families", 0))
        drift_fails = reddens(
            "E_REGISTRY_DRIFT",
            lambda p: p["families"][0].__setitem__(
                "selected_criteria", p["families"][0]["selected_criteria"] + 7))
        verdict_fails = reddens(
            "E_VERDICT", lambda p: p.__setitem__("verdict", "PASS"))
        ok("AC-BSRB5",
           clean == [] and len(tampered) == 6
           and back_json == jtext and back_html == html,
           "clean=%d tampered=%d json_eq=%s html_eq=%s"
           % (len(clean), len(tampered), back_json == jtext, back_html == html))

        # AC-BSRB7 - the controls are load-bearing and do not cross-fire.
        def has(fails, token):
            return any(f.startswith(token) for f in fails)

        ok("AC-BSRB7",
           has(drift_fails, "E_REGISTRY_DRIFT")
           and not has(drift_fails, "E_VERDICT")
           and has(verdict_fails, "E_VERDICT")
           and not has(verdict_fails, "E_REGISTRY_DRIFT"),
           "drift_named=%s verdict_named=%s cross=%s"
           % (has(drift_fails, "E_REGISTRY_DRIFT"),
              has(verdict_fails, "E_VERDICT"),
              (has(drift_fails, "E_VERDICT")
               or has(verdict_fails, "E_REGISTRY_DRIFT"))))

        # AC-BSRB6 - offline, scope honest, links on disk.
        nb = payload["not_the_battery"]
        links_ok = all(os.path.isfile(os.path.join(bsr.PREVIEW, n))
                       for n in bsr.LINKS)
        ok("AC-BSRB6",
           ("http://" not in html and "https://" not in html)
           and "\u5206\u7247\uff0c\u4e0d\u662f\u5168\u91cf\u7535\u6c60" in nb
           and tot["uncovered_suites"] == 700 - tot["selected"]
           and links_ok,
           "http=0 scope_note=True uncovered=%d links=%s"
           % (tot["uncovered_suites"], links_ok))

        # AC-BSRB8 - the two family-set laws, each reddenable on its own.
        overlap_tok, dup_tok, typed_tok, absent_tok = [], [], [], []
        try:
            bsr.FAMILIES = (("pa-", "fam-a", "a"), ("pa-x-", "fam-b", "b"))
            p2 = copy.deepcopy(payload)
            p2["families"] = [f for f in p2["families"] if f["key"] != "fam-c"]
            p2["families"][1]["key"] = "fam-b"
            t2 = bsr.dumps(p2)
            h2 = bsr.render_html(p2)
            e2 = {f["key"]: (f["selected"], f["selected_criteria"])
                  for f in p2["families"]}
            overlap_tok = bsr.check_payload(p2, h2, t2, 700, 5000, e2)
        finally:
            bsr.FAMILIES = (("pa-", "fam-a", "a"), ("pb-", "fam-b", "b"),
                            ("pc-", "fam-c", "c"))
        try:
            bsr.FAMILIES = (("pa-", "same", "a"), ("pb-", "same", "b"))
            p3 = copy.deepcopy(payload)
            p3["families"] = [f for f in p3["families"] if f["key"] != "fam-c"]
            p3["families"][0]["key"] = "same"
            p3["families"][1]["key"] = "same"
            t3 = bsr.dumps(p3)
            h3 = bsr.render_html(p3)
            e3 = {"same": (p3["families"][0]["selected"],
                           p3["families"][0]["selected_criteria"])}
            dup_tok = bsr.check_payload(p3, h3, t3, 700, 5000, e3)
        finally:
            bsr.FAMILIES = (("pa-", "fam-a", "a"), ("pb-", "fam-b", "b"),
                            ("pc-", "fam-c", "c"))
        typed_tok = bsr.check_payload(
            payload, html.replace("3 \u65cf", "\u4e09\u65cf"), jtext, 700, 5000,
            exp)
        absent_tok = bsr.check_payload(
            payload, html.replace("3 \u65cf", "  "), jtext, 700, 5000, exp)
        honest = bsr.check_payload(payload, html, jtext, 700, 5000, exp)
        ok("AC-BSRB8",
           has(overlap_tok, "E_FAMILY_PREFIX_OVERLAP")
           and has(dup_tok, "E_FAMILY_KEY_DUP")
           and has(typed_tok, "E_TYPED_FAMILY_COUNT")
           and has(absent_tok, "E_FAMILY_COUNT_ABSENT")
           and not [f for f in honest if f.startswith("E_FAMILY")],
           "overlap=%s dup=%s typed=%s absent=%s clean_no_family=%s"
           % (has(overlap_tok, "E_FAMILY_PREFIX_OVERLAP"),
              has(dup_tok, "E_FAMILY_KEY_DUP"),
              has(typed_tok, "E_TYPED_FAMILY_COUNT"),
              has(absent_tok, "E_FAMILY_COUNT_ABSENT"),
              not [f for f in honest if f.startswith("E_FAMILY")]))

        # AC-BSRB11 (R3082 pin): the unchecked face must reach the page from
        # the same single source as json totals, and a family whose leg never
        # declared the field must print the word, not a measured zero.
        unchecked_sum = sum(f.get("crit_unchecked", 0)
                            for f in payload["families"])
        seen_sum = sum(f.get("crit_unchecked_seen", 0)
                       for f in payload["families"])
        tot_ok = (tot["crit_unchecked"] == unchecked_sum
                  and tot["crit_unchecked_seen"] == seen_sum)
        page_total = ("\u672a\u6bd4\u8f83\u5224\u636e %d\uff08%d/%d \u65cf"
                      "\u5df2\u7533\u62a5\uff09"
                      % (tot["crit_unchecked"], tot["crit_unchecked_seen"],
                         tot["families"]))
        page_ok = page_total in html
        fam_c = [f for f in payload["families"] if f["key"] == "fam-c"][0]
        seen0_ok = (fam_c["crit_unchecked_seen"] == 0
                    and bsr.unchecked_cell(fam_c) == "\u672a\u7533\u62a5"
                    and html.count("<td class=\"n\">\u672a\u7533\u62a5</td>") == 1)
        nz = copy.deepcopy(payload)
        nz["families"][0]["crit_unchecked"] = 3
        nz["families"][0]["crit_unchecked_seen"] = 1
        nz["totals"]["crit_unchecked"] = 3 + sum(
            f.get("crit_unchecked", 0) for f in nz["families"][1:])
        nz_html = bsr.render_html(nz)
        nz_ok = (bsr.unchecked_cell(nz["families"][0]) == "3"
                 and "<td class=\"n\">3</td>" in nz_html
                 and ("\u672a\u6bd4\u8f83\u5224\u636e %d"
                      % nz["totals"]["crit_unchecked"]) in nz_html)
        page_tamper = bsr.check_payload(
            payload,
            html.replace("\u672a\u6bd4\u8f83\u5224\u636e %d"
                         % tot["crit_unchecked"],
                         "\u672a\u6bd4\u8f83\u5224\u636e %d"
                         % (tot["crit_unchecked"] + 9)),
            jtext, 700, 5000, exp)
        tb = copy.deepcopy(payload)
        tb["totals"]["crit_unchecked"] = 9
        totals_tamper = bsr.check_payload(tb, bsr.render_html(tb),
                                          bsr.dumps(tb), 700, 5000, exp)
        ok("AC-BSRB11",
           tot_ok and page_ok and seen0_ok and nz_ok
           and has(page_tamper, "E_PAGE_UNCHECKED")
           and has(totals_tamper, "E_TOTALS_UNCHECKED"),
           "tot=%s page=%s seen0=%s nonzero=%s page_tamper=%s tot_tamper=%s"
           % (tot_ok, page_ok, seen0_ok, nz_ok,
              has(page_tamper, "E_PAGE_UNCHECKED"),
              has(totals_tamper, "E_TOTALS_UNCHECKED")))

        # AC-BSRB12 (R3352): pass/fail count rows that START with PASS/FAIL,
        # so a suite that prints ONE summary row has no such rows at all - its
        # zero is emptiness, not a measurement, and a bare 0 beside
        # `suite=PASS 55/55` reads as a contradiction. detail=none prints the
        # word, detail=yes keeps its numbers, and a payload written BEFORE the
        # field existed keeps its numbers too (never re-read retroactively).
        bare_text = ("SHARD scope=SHARD registry_suites=1 registry_criteria=2 "
                     "selected=2 selected_criteria=2\n"
                     "SHARD row probe-bare rc=0 pass=0 fail=0 detail=none "
                     "suite=PASS 55/55 crit=6 0.4s\n"
                     "SHARD row probe-full rc=0 pass=1 fail=0 detail=yes "
                     "suite=PASS 1/1 crit=1 0.1s\n"
                     "SHARD rc=0 scope=SHARD selected=2 executed=2 green=2 "
                     "criteria=2 crit_mismatch=0 elapsed=0.5s "
                     "crit_checked=2 crit_unchecked=0\n")
        bare_fam = bsr.parse_family("probe", "probe-", "g", 0, bare_text)
        det_ok = [(r.get("label"), r.get("detail"))
                  for r in bare_fam.get("suites", [])] == [
                      ("probe-bare", "none"), ("probe-full", "yes")]
        det_payload = copy.deepcopy(payload)
        det_payload["families"][0]["suites"] = bare_fam.get("suites", [])
        det_html = bsr.render_html(det_payload)
        bare_row = [chunk for chunk in det_html.split("<tr>")
                    if "probe-bare" in chunk]
        full_row = [chunk for chunk in det_html.split("<tr>")
                    if "probe-full" in chunk]
        bare_ok = (len(bare_row) == 1
                   and ("<td class=\"n\">\u672a\u7533\u62a5</td>"
                        "<td class=\"n\">\u672a\u7533\u62a5</td>")
                   in bare_row[0])
        full_ok = (len(full_row) == 1
                   and "<td class=\"n\">1</td><td class=\"n\">0</td>"
                   in full_row[0])
        pre_field = copy.deepcopy(det_payload)
        pre_field["families"][0]["suites"] = [
            {"label": "probe-old", "rc": 0, "pass": 0, "fail": 0,
             "suite": "PASS 55/55", "crit": 6, "elapsed_s": 0.4}]
        legacy_num_ok = ("<td class=\"n\">0</td><td class=\"n\">0</td>"
                         in bsr.render_html(pre_field))
        ok("AC-BSRB12", det_ok and bare_ok and full_ok and legacy_num_ok,
           "detail=%s bare=%s full=%s prefield_number=%s"
           % (det_ok, bare_ok, full_ok, legacy_num_ok))
    finally:
        bsr.FAMILIES, bsr.run_family, bsr.PREVIEW, bsr.OUT_JSON, bsr.OUT_HTML = keep
        shutil.rmtree(world, ignore_errors=True)

    # AC-BSRB2b / AC-BSRB7 - the repo is read-only for this suite and both
    # sources stay pure.
    src_mine = read_text(os.path.abspath(__file__))
    untouched = (sig_pair == (stat_sig(PAIR_JSON), stat_sig(PAIR_HTML))
                 and sig_tool == stat_sig(TOOL)
                 and sig_reg == stat_sig(REGISTRY))
    # needles are assembled from fragments so this file cannot match itself -
    # the same self-match trap the fleet process probes hit.
    needles = ("import soc" + "ket", "urllib.re" + "quest",
               "http.cli" + "ent", "import req" + "uests",
               "os.sys" + "tem", "shell=" + "True")
    banned = [n for n in needles if n in src_tool or n in src_mine]
    ascii_ok = all(ord(ch) < 128 for ch in src_mine)
    ok("AC-BSRB6b", untouched, "pair_tool_registry_unchanged=%s" % untouched)
    ok("AC-BSRB7b", not banned and ascii_ok,
       "banned=%d ascii=%s" % (len(banned), ascii_ok))

    # ---- AC-BSRB10 (R3081 pin): the reader must read the row the writer ships.
    # This is the arm that would have caught the staleness: the fixture now
    # carries detail=/timeout=yes and the closing row's crit_checked /
    # crit_unchecked, and one arm runs a REAL shipped leg end to end.
    shipped = stream(733, 5965, GREEN_ROWS, (0, 2, 2, 1.5), unchecked=1,
                     timeout_labels=("probe-b",))
    fam = bsr.parse_family("probe", "probe-", "g", 0, shipped)
    today_ok = (fam["parse"] == "ok" and len(fam["suites"]) == 2
                and fam["crit_unchecked"] == 1
                and fam["crit_unchecked_seen"] == 1
                and fam["crit_mismatch"] == 0)
    old = stream(733, 5965, GREEN_ROWS, (0, 2, 2, 1.5), legacy=True)
    fam_old = bsr.parse_family("probe", "probe-", "g", 0, old)
    legacy_ok = (fam_old["parse"] == "ok" and len(fam_old["suites"]) == 2
                 and fam_old["crit_unchecked"] == 0
                 and fam_old["crit_unchecked_seen"] == 0)
    timeout_row = fam["suites"][1] if len(fam["suites"]) > 1 else {}
    timeout_ok = (timeout_row.get("label") == "probe-b"
                  and timeout_row.get("crit") == 2
                  and timeout_row.get("pass") == 2)
    proc = subprocess.run([sys.executable, SHARD, "--exact", "os-debt-gate"],
                          cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    real_out = proc.stdout.decode("utf-8", "replace")
    real_out = real_out.replace("\r\n", "\n").replace("\r", "\n")
    fam_real = bsr.parse_family("real", "os-debt-gate", "g", proc.returncode,
                                real_out)
    real_ok = (fam_real["parse"] == "ok" and fam_real["executed"] == 1
               and fam_real["crit_unchecked_seen"] == 1
               and fam_real["green"] == 1)
    ok("AC-BSRB10",
       today_ok and legacy_ok and timeout_ok and real_ok,
       "today=%s legacy=%s timeout=%s real=%s(%s)"
       % (today_ok, legacy_ok, timeout_ok, real_ok, fam_real["parse"]))

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
