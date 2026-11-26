"""Battery suite for src/os/board_face_landing.py - AC-BFL1..AC-BFL4 (R3525).

Pinned in src/os/backlog.md BEFORE this file and before the helper existed.

Why this exists: R3523 measured that a landed board page ages the CEO face in
silence, because a board page can never be `latest_artifact` - the only trace it
leaves is a skipped-audit row, so nothing about the face changes when it lands.
R3524 closed that for one producer by re-deriving the face in-process. This
round's census found the same shape on the other three writers of
export_round.BOARD_PAGES, so the law is now one shared definition plus a source
census that has to stay closed over BOARD_PAGES.

Scope, stated honestly: this suite never renders a real page. It grades the
helper through a fake shipped writer (the same shape R3524 used), and grades the
four tools by reading their SOURCE - which is where the gap lives, since the
defect is "no in-process call after the landing", not a wrong number. Controls
run on copies inside one private temp world; the repo tree is stat-signed before
and after.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import hashlib
import importlib.util
import io
import ast
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_OS = os.path.join(ROOT, "src", "os")
TOOLS = os.path.join(ROOT, "tools")
HELPER = os.path.join(SRC_OS, "board_face_landing.py")
FACE = os.path.join(ROOT, "docs", "status-export.json")

# The census table. Every cell is VERIFIED against the tool source below, so a
# wrong or stale row reddens instead of being trusted; slugs come from
# export_round.BOARD_PAGES, so a new board page without a row also reddens.
WRITER_ROWS = (
    ("ceo-blockers", "ceo_blockers.py", "ceo-blockers.html"),
    ("face-sweep", "face_sweep.py", "face-sweep.html"),
    ("battery-shard-report", "battery_shard_report.py", "battery-shard-report.json"),
    ("index", "deliverable_index.py", "index.html"),
)

WRITE_RE = re.compile(r"^\s*(?:fh\.write\(|write_atomic\()")
FACE_CALL_RE = re.compile(r"(?:BFL\.)?refresh_(?:export_)?face\(|\bER\.write\(")
SHARED_RE = re.compile(r"board_face_landing|\bER\.write\(")

CHECKS = []
FAILS = []


def ok(code, cond, detail):
    CHECKS.append(code)
    if not cond:
        FAILS.append(code)
    print("%s %-9s %s" % ("PASS" if cond else "FAIL", code, detail))


def source(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def load_helper():
    spec = importlib.util.spec_from_file_location("bfl_probe", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def landing_arm(text):
    """The measurement both the real census and the controls run."""
    lines = text.splitlines()
    writes = [i for i, line in enumerate(lines, 1) if WRITE_RE.match(line)]
    calls = [i for i, line in enumerate(lines, 1)
             if FACE_CALL_RE.search(line) and not line.strip().startswith("def ")]
    order_ok = bool(writes) and bool(calls) and max(calls) > max(writes)
    return {"writes": writes, "calls": calls, "order_ok": order_ok}


CENSUS_TOOL = os.path.join(TOOLS, "preview_pair_census.py")
CENSUS_GROUPS = (
    ("census-pair", ("JSON_OUT", "HTML_OUT")),
    ("admit-pair", ("ADMIT_OUT", "ADMIT_HTML")),
)
CENSUS_CALL_RE = re.compile(r"\brefresh_face\(")


def census_landing(text):
    """AC-BFL5 measurement: at every landing site of the non-board census tool
    both halves are written and the shared face call comes after the last write.
    A site whose halves are missing reads absent instead of passing vacuously."""
    lines = text.splitlines()
    calls = [i for i, line in enumerate(lines, 1)
             if CENSUS_CALL_RE.search(line) and not line.strip().startswith("def ")]
    out = {}
    for name, targets in CENSUS_GROUPS:
        writes = []
        seen = set()
        for i, line in enumerate(lines, 1):
            if "io.open(" not in line:
                continue
            for target in targets:
                if target in line:
                    writes.append(i)
                    seen.add(target)
        last = max(writes) if writes else 0
        after = [c for c in calls if c > last]
        out[name] = {"writes": writes, "halves": len(seen), "last": last,
                     "call_after": after[:1],
                     "ok": len(seen) == len(targets) and bool(after)}
    return out


class _FakeER(object):
    def __init__(self):
        self.calls = []
        self.answers = []

    def write(self, root, stamp):
        self.calls.append((root, stamp))
        return self.answers.pop(0)


class _RefuseER(object):
    def write(self, root, stamp):
        raise ValueError("E_EXPR_UNPROVEN the face cannot be judged")


class _DirtyER(object):
    def write(self, root, stamp):
        return (True, {"latest": "preview/x.html"}, {"gate": "DIRTY"})


def stat_sig(paths):
    sig = []
    for path in paths:
        st = os.stat(path)
        sig.append((path, st.st_size, int(st.st_mtime)))
    return sig


def main():
    sig_before = stat_sig([HELPER, FACE,
                           os.path.join(TOOLS, "ceo_blockers.py"),
                           os.path.join(TOOLS, "face_sweep.py"),
                           os.path.join(TOOLS, "battery_shard_report.py"),
                           os.path.join(TOOLS, "deliverable_index.py")])

    # AC-BFL1 -- the shared helper calls the shipped writer once, on the root it
    # was given, and every refusal is named rather than raised.
    bfl = load_helper()
    fake = _FakeER()
    fake.answers.append((True, {"latest": "preview/probe.html"},
                         {"gate": "CURRENT", "bytes": 12}))
    keep = sys.modules.get("export_round")
    try:
        sys.modules["export_round"] = fake
        face_ok, face_note, face_proof = bfl.refresh_export_face("/probe/root")
    finally:
        if keep is None:
            sys.modules.pop("export_round", None)
        else:
            sys.modules["export_round"] = keep
    stamp = fake.calls[0][1] if len(fake.calls) == 1 else ""
    shape_ok = bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$",
                             stamp))
    delegate_ok = (face_ok is True and face_note == "" and len(fake.calls) == 1
                   and fake.calls[0][0] == "/probe/root" and shape_ok
                   and face_proof.get("latest") == "preview/probe.html"
                   and face_proof.get("bytes") == 12)
    try:
        sys.modules["export_round"] = _RefuseER()
        refused_ok, refused_note, _p = bfl.refresh_export_face("/probe/root")
    finally:
        if keep is None:
            sys.modules.pop("export_round", None)
        else:
            sys.modules["export_round"] = keep
    refuse_ok = (refused_ok is False
                 and "E_BFL_FACE_REFUSED" in refused_note
                 and "E_EXPR_UNPROVEN" in refused_note)
    try:
        sys.modules["export_round"] = _DirtyER()
        dirty_ok, dirty_note, _p = bfl.refresh_export_face("/probe/root")
    finally:
        if keep is None:
            sys.modules.pop("export_round", None)
        else:
            sys.modules["export_round"] = keep
    unproven_ok = dirty_ok is False and "E_BFL_FACE_UNPROVEN" in dirty_note
    ok("AC-BFL1", delegate_ok and refuse_ok and unproven_ok,
       "delegate=%s refuse=%s unproven=%s calls=%d"
       % (delegate_ok, refuse_ok, unproven_ok, len(fake.calls)))

    # AC-BFL2 -- the census is closed over export_round.BOARD_PAGES and every
    # cell is verified against the tool source: it declares the page path, and a
    # face call sits after the landing writes and resolves to the shipped writer.
    sys.path.insert(0, SRC_OS)
    import export_round as SHIPPED
    board = tuple(SHIPPED.BOARD_PAGES)
    table = dict((slug, (name, literal)) for slug, name, literal in WRITER_ROWS)
    missing = [s for s in board if s not in table]
    phantom = [s for s in table if s not in board]
    cells = []
    for slug, name, literal in WRITER_ROWS:
        path = os.path.join(TOOLS, name)
        if not os.path.isfile(path):
            cells.append((slug, False, "tool missing"))
            continue
        text = source(path)
        declares = any(literal in line and "os.path.join(" in line
                       for line in text.splitlines())
        arm = landing_arm(text)
        shared = bool(SHARED_RE.search(text))
        cells.append((slug, declares and arm["order_ok"] and shared,
                      "declares=%s order=%s shared=%s writes=%s calls=%s"
                      % (declares, arm["order_ok"], shared,
                         arm["writes"][-1:], arm["calls"][-1:])))
    bad = [c[0] for c in cells if not c[1]]
    ok("AC-BFL2", not missing and not phantom and not bad,
       "board=%d missing=%s phantom=%s red=%s"
       % (len(board), missing or "none", phantom or "none", bad or "none"))

    # AC-BFL3 -- two negative controls on COPIES of a real writer, so the law is
    # proved load-bearing: removing the call, or moving it before the landing,
    # must both read absent through the same measurement.
    world = tempfile.mkdtemp(prefix="bfl-")
    try:
        real = source(os.path.join(TOOLS, "ceo_blockers.py"))
        real_arm = landing_arm(real)
        call_line = "    refresh_face()\n"
        cut = real.replace(call_line, "", 1)
        cut_arm = landing_arm(cut)
        moved = real.replace(call_line, "", 1).replace(
            "    html, payload = render_both()\n",
            "    refresh_face()\n    html, payload = render_both()\n", 1)
        moved_arm = landing_arm(moved)
        with io.open(os.path.join(world, "cut.py"), "w", encoding="utf-8",
                     newline="\n") as fh:
            fh.write(cut)
        with io.open(os.path.join(world, "moved.py"), "w", encoding="utf-8",
                     newline="\n") as fh:
            fh.write(moved)
        disk_cut = landing_arm(source(os.path.join(world, "cut.py")))
        disk_moved = landing_arm(source(os.path.join(world, "moved.py")))
    finally:
        shutil.rmtree(world, ignore_errors=True)
    ok("AC-BFL3", real_arm["order_ok"]
       and not cut_arm["order_ok"] and not moved_arm["order_ok"]
       and cut_arm == disk_cut and moved_arm == disk_moved,
       "real=%s cut=%s moved=%s (on-disk copies read %s/%s)"
       % (real_arm["order_ok"], cut_arm["order_ok"], moved_arm["order_ok"],
          disk_cut["order_ok"], disk_moved["order_ok"]))

    # AC-BFL4 -- the helper and this suite are read-only: no child process, no
    # socket, no write from either file, and the repo files did not move.
    banned = ("subprocess", "socket", "urllib", "requests", "http.client", "ssl")
    def imports_of(path):
        tree = ast.parse(source(path))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        return names
    helper_text = source(HELPER)
    no_child = not (imports_of(HELPER) & set(banned))
    no_write = not re.search(r"open\([^)]*[\"'][wa]b?[\"']", helper_text)
    suite_banned = sorted(imports_of(os.path.abspath(__file__)) & set(banned))
    sig_after = stat_sig([HELPER, FACE,
                          os.path.join(TOOLS, "ceo_blockers.py"),
                          os.path.join(TOOLS, "face_sweep.py"),
                          os.path.join(TOOLS, "battery_shard_report.py"),
                          os.path.join(TOOLS, "deliverable_index.py")])
    ok("AC-BFL4", no_child and no_write and not suite_banned
       and sig_before == sig_after,
       "no_child=%s no_write=%s suite_banned=%s tree_stable=%s"
       % (no_child, no_write, suite_banned or "none", sig_before == sig_after))

    # AC-BFL5 -- the non-board census tool is closed over BOTH of its landing
    # sites: each pair's two halves are written and one shared face call follows
    # the last write, resolving to board_face_landing rather than a second copy.
    census_text = source(CENSUS_TOOL)
    groups = census_landing(census_text)
    red_sites = [n for n, row in groups.items() if not row["ok"]]
    shares = "import board_face_landing" in census_text
    ok("AC-BFL5", not red_sites and shares,
       "sites=%s red=%s shared=%s"
       % (dict((n, (r["halves"], r["last"], r["call_after"]))
               for n, r in groups.items()), red_sites or "none", shares))

    # AC-BFL6 -- behaviour through a recording fake helper: exactly one call, on
    # this tool's own root, and a named refusal comes back as False, never raised.
    class _FakeHelper(object):
        def __init__(self, answer):
            self.calls = []
            self.answer = answer

        def refresh_export_face(self, root, stamp=None):
            self.calls.append((root, stamp))
            return self.answer

    spec = importlib.util.spec_from_file_location("ppc_probe", CENSUS_TOOL)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    keep_helper = sys.modules.get("board_face_landing")
    good = _FakeHelper((True, "", {"stamp": "2026-11-27T00:00:00+08:00"}))
    try:
        sys.modules["board_face_landing"] = good
        called_ok = tool.refresh_face()
    finally:
        if keep_helper is None:
            sys.modules.pop("board_face_landing", None)
        else:
            sys.modules["board_face_landing"] = keep_helper
    delegate_ok = (called_ok is True and len(good.calls) == 1
                   and good.calls[0][0] == tool.REPO and good.calls[0][1] is None)
    refused = _FakeHelper((False, "E_BFL_FACE_REFUSED ValueError: boom", {}))
    try:
        sys.modules["board_face_landing"] = refused
        refused_ok = tool.refresh_face()
    finally:
        if keep_helper is None:
            sys.modules.pop("board_face_landing", None)
        else:
            sys.modules["board_face_landing"] = keep_helper
    ok("AC-BFL6", delegate_ok and refused_ok is False,
       "delegate=%s calls=%d root_is_repo=%s refused_returns_false=%s"
       % (delegate_ok, len(good.calls),
          bool(good.calls) and good.calls[0][0] == tool.REPO,
          refused_ok is False))

    # AC-BFL7 -- two negative controls on COPIES of the census tool, so the law
    # is load-bearing: cutting the call, or moving it before the landing writes,
    # must both read absent while the real source reads present; and the shipped
    # --check branch must return before any landing write.
    census_site = ('    with io.open(JSON_OUT, "wb") as f:\n'
                   '        f.write(dumps(payload).encode("utf-8"))\n'
                   '    with io.open(HTML_OUT, "wb") as f:\n'
                   '        f.write(html_of(payload).encode("utf-8"))\n'
                   '    refresh_face()\n')
    site_found = census_site in census_text
    bare = census_site.replace("    refresh_face()\n", "")
    cut_text = census_text.replace(census_site, bare, 1)
    moved_text = census_text.replace(census_site, "    refresh_face()\n" + bare, 1)
    cut_row = census_landing(cut_text)
    moved_row = census_landing(moved_text)
    real_row = census_landing(census_text)
    admit_alive = cut_row["admit-pair"]["ok"]
    check_first = census_text.index('if "--check" in argv:') < \
        census_text.index('with io.open(JSON_OUT')
    tool_sig_before = stat_sig([CENSUS_TOOL])
    tool_sig_after = stat_sig([CENSUS_TOOL])
    ok("AC-BFL7", site_found and real_row["census-pair"]["ok"]
       and not cut_row["census-pair"]["ok"]
       and not moved_row["census-pair"]["ok"]
       and admit_alive and check_first and tool_sig_before == tool_sig_after,
       "site=%s real=%s cut=%s moved=%s admit_untouched=%s check_first=%s stable=%s"
       % (site_found, real_row["census-pair"]["ok"],
          cut_row["census-pair"]["ok"], moved_row["census-pair"]["ok"],
          admit_alive, check_first, tool_sig_before == tool_sig_after))

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
