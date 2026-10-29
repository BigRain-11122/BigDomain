"""seed_anchor suite (R2259; criteria AC-SAN1..AC-SAN5 were pinned in
state/queue/tech.md as the R2248-e seed row BEFORE this code existed).

What this proves: every window claims its seed's face name is zero-occupancy
at HEAD, and that claim was a hand-run git grep nobody kept. This suite pins
the reading on throwaway git repositories - the HEAD leg sees what a landed
seed would collide with, the working-tree leg sees the uncommitted and
untracked hits a HEAD-only check cannot, the verdict and its counts reconcile,
an occupancy refuses to seed, and the tool is read-only, pure ASCII, stdlib
only and wired into the battery.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import seed_anchor as SA  # noqa: E402

EXPECTED_CRITERIA = 5
MODULE = os.path.join(BASE, "seed_anchor.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-seed-anchor"
WIRED_EXPECT = '"test_seed_anchor.py"), 5),'

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def git(args, cwd=None):
    proc = subprocess.run(["git"] + list(args), cwd=cwd,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"))


def write_text(path, body):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)


def make_repo(files):
    """A throwaway git repository with one commit holding `files`."""
    repo = tempfile.mkdtemp(prefix="bigdomain-sanchor-")
    git(["init", "-q", repo])
    for name, body in files.items():
        write_text(os.path.join(repo, name), body)
    git(["-C", repo, "add", "-A"])
    git(["-C", repo, "-c", "user.name=seed", "-c",
         "user.email=seed@example.com", "commit", "-q", "-m", "seed"])
    return repo


def drop(path):
    shutil.rmtree(path, ignore_errors=True)


def digest_tree(root):
    parts = []
    for base, _dirs, files in os.walk(root):
        for name in sorted(files):
            full = os.path.join(base, name)
            try:
                with io.open(full, "rb") as handle:
                    body = handle.read()
            except (IOError, OSError):
                body = b"<unreadable>"
            parts.append((os.path.relpath(full, root), len(body),
                          hashlib.sha256(body).hexdigest()))
    return parts


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + list(args),
                          cwd=BASE, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ac_san1():
    """The HEAD scope reports exactly the committed hits it should."""
    repo = make_repo({"a.txt": "alpha-needle here\n",
                      "b.txt": "nothing to see\n"})
    try:
        hit = SA.scan(repo, "alpha-needle", "head")
        absent = SA.scan(repo, "absent-needle", "head")
        report = SA.audit(repo, ["alpha-needle", "absent-needle"],
                          scopes=("head",))
    finally:
        drop(repo)
    ok = (len(hit) == 1 and hit[0]["file"] == "a.txt"
          and hit[0]["line"] == 1
          and absent == []
          and report["by_needle"] == [
              {"needle": "alpha-needle", "head": 1, "tree": None},
              {"needle": "absent-needle", "head": 0, "tree": None}]
          and report["head_count"] == 1
          and report["verdict"] == "OCCUPIED")
    if not ok:
        print("  measured hit=%r absent=%r by_needle=%r"
              % (hit, absent, report["by_needle"]), flush=True)
    check(ok, "AC-SAN1 HEAD scope names exact committed hits, absent reads zero")


def ac_san2():
    """The tree scope sees what the HEAD scope cannot."""
    repo = make_repo({"a.txt": "base line\n"})
    try:
        write_text(os.path.join(repo, "a.txt"), "base line\ngamma-needle\n")
        write_text(os.path.join(repo, "b.txt"), "beta-needle\n")
        head_gamma = SA.scan(repo, "gamma-needle", "head")
        head_beta = SA.scan(repo, "beta-needle", "head")
        tree_gamma = SA.scan(repo, "gamma-needle", "tree")
        tree_beta = SA.scan(repo, "beta-needle", "tree")
        report = SA.audit(repo, ["gamma-needle", "beta-needle"])
    finally:
        drop(repo)
    ok = (head_gamma == [] and head_beta == []
          and len(tree_gamma) == 1 and tree_gamma[0]["file"] == "a.txt"
          and len(tree_beta) == 1 and tree_beta[0]["file"] == "b.txt"
          and report["head_count"] == 0 and report["tree_count"] == 2
          and report["verdict"] == "OCCUPIED"
          and [hit["scope"] for hit in report["hits"]] == ["tree", "tree"])
    if not ok:
        print("  measured head_gamma=%r head_beta=%r tree_gamma=%r "
              "tree_beta=%r report=%r"
              % (head_gamma, head_beta, tree_gamma, tree_beta,
                 (report["head_count"], report["tree_count"],
                  report["verdict"])), flush=True)
    check(ok, "AC-SAN2 tree scope sees the uncommitted and untracked hits")


def ac_san3():
    """FREE/OCCUPIED with counts that reconcile and an honest limit."""
    repo = make_repo({"c.txt": "alpha-needle\n",
                      "d.txt": "alpha-needle again\n",
                      "e.txt": "other-needle\n"})
    try:
        report = SA.audit(repo, ["alpha-needle", "free-needle"], limit=100)
        free = SA.audit(repo, ["free-needle"])
        one_scope = SA.audit(repo, ["alpha-needle"], scopes=("head",))
        capped = SA.audit(repo, ["alpha-needle"], limit=1)
    finally:
        drop(repo)
    head_sum = sum(entry["head"] for entry in report["by_needle"])
    tree_sum = sum(entry["tree"] for entry in report["by_needle"])
    ok = (report["head_count"] == 2 and report["tree_count"] == 2
          and len(report["hits"]) == 4
          and head_sum == report["head_count"]
          and tree_sum == report["tree_count"]
          and report["head_count"] + report["tree_count"] == len(report["hits"])
          and report["truncated"] is False
          and report["verdict"] == "OCCUPIED"
          and free["verdict"] == "FREE" and free["hits"] == []
          and free["head_count"] == 0 and free["tree_count"] == 0
          and one_scope["tree_count"] is None
          and one_scope["head_count"] == 2 and len(one_scope["hits"]) == 2
          and capped["truncated"] is True and len(capped["hits"]) == 1
          and capped["head_count"] + capped["tree_count"] == 4)
    if not ok:
        print("  measured report=%r free=%r one_scope=%r capped=%r"
              % ((report["head_count"], report["tree_count"],
                  len(report["hits"]), report["truncated"],
                  report["verdict"]),
                 (free["verdict"], free["hits"]),
                 (one_scope["tree_count"], one_scope["head_count"]),
                 (capped["truncated"], len(capped["hits"]),
                  capped["head_count"] + capped["tree_count"])), flush=True)
    check(ok, "AC-SAN3 verdict, reconciling counts, honest limit and truncation")


def ac_san4():
    """Occupancy refuses to seed; every other path exits cleanly; no writes."""
    busy = make_repo({"a.txt": "alpha-needle\n"})
    free = make_repo({"a.txt": "nothing\n"})
    bare = tempfile.mkdtemp(prefix="bigdomain-sanchor-bare-")
    try:
        code = None
        raised = False
        try:
            SA.require_free(busy, ["alpha-needle"])
        except SA.SeedAnchorError as exc:
            raised = True
            code = exc.code
        before = digest_tree(busy)
        rc_busy, body_busy = run_cli(["--check", "--needle", "alpha-needle",
                                      "--root", busy])
        rc_free, body_free = run_cli(["--check", "--needle", "alpha-needle",
                                      "--root", free])
        rc_flag, _body_flag = run_cli(["--check", "--needle", "x",
                                       "--root", free, "--bogus"])
        rc_bare, body_bare = run_cli(["--check", "--needle", "x",
                                      "--root", bare])
        after = digest_tree(busy)
        good = SA.require_free(free, ["alpha-needle"])
    finally:
        for path in (busy, free, bare):
            drop(path)
    ok = (raised and code == "E_SAN_OCCUPIED"
          and rc_busy == 2 and "REFUSE TO SEED" in body_busy
          and rc_free == 0 and "FREE" in body_free
          and rc_flag == 2
          and rc_bare == 3 and "E_SAN_GIT" in body_bare
          and before == after and good["verdict"] == "FREE")
    if not ok:
        print("  measured code=%r busy=%r free=%r flag=%r bare=%r "
              "write=%r good=%r"
              % (code, rc_busy, rc_free, rc_flag, rc_bare,
                 before == after, good["verdict"]), flush=True)
    check(ok, "AC-SAN4 occupancy refuses, codes 0/2/3 hold, tree untouched")


def ac_san5():
    """Purity: ASCII, no network, wired, byte-stable json over pinned keys."""
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_only = True
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        ascii_only = False
    text = raw.decode("ascii", "replace")
    blocked = ("import socket", "import urllib", "import http",
               "import requests", "import asyncio", "urlopen")
    no_net = not any(token in text for token in blocked)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        wiring = handle.read()
    wired = (LABEL in wiring) and ("test_seed_anchor.py" in wiring) \
        and (WIRED_EXPECT in wiring)
    first = run_cli(["--check", "--needle", "os-seed-anchor",
                     "--root", REPO, "--scope", "head", "--json"])
    second = run_cli(["--check", "--needle", "os-seed-anchor",
                      "--root", REPO, "--scope", "head", "--json"])
    keys = list(json.loads(first[1]).keys())
    hit_keys = set()
    report = SA.audit(REPO, ["os-seed-anchor", "seed_anchor"],
                      scopes=("head",))
    for hit in report["hits"]:
        hit_keys.update(hit.keys())
    ok = (ascii_only and no_net and wired
          and first == second and keys == list(SA.REPORT_KEYS)
          and hit_keys == set(SA.HIT_KEYS))
    if not ok:
        print("  measured ascii=%r net=%r wired=%r stable=%r keys=%r "
              "hit_keys=%r"
              % (ascii_only, no_net, wired, first == second, keys,
                 sorted(hit_keys)), flush=True)
    check(ok, "AC-SAN5 pure ASCII, no network, wired, byte-stable pinned json")


def main():
    print("seed_anchor suite (expected criteria %d)" % EXPECTED_CRITERIA,
          flush=True)
    ac_san1()
    ac_san2()
    ac_san3()
    ac_san4()
    ac_san5()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())