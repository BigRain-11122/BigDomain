# seed_anchor.py - is a seed's face name provably unoccupied?
# Criteria AC-SAN1..AC-SAN5 were pinned in state/queue/tech.md as the R2248-e
# seed row BEFORE this file existed (claim note added by R2259).
# Anchor check at HEAD 2026-10-29: "os-seed-anchor" / "test_seed_anchor" /
# "E_SAN" were git grep -F zero-occupancy rc=1; "seed_anchor" and "AC-SAN"
# hit only the R2248 seed generator, the R2248 backlog row and the row text
# itself - text occupancy, disclosed, zero code occupancy.
#
# Why this exists: every window that seeds a queue row claims its face name is
# "zero-occupancy at HEAD", and that claim was a hand-run `git grep -F` whose
# output nobody kept. A seed that collides with a shipped module, or with a
# name another window is about to ship, would be discovered only when the
# second writer landed. This tool makes the claim a reading with two scopes:
#
#   * head - the committed revision. What a landed seed would collide with.
#   * tree - the working tree including untracked files. What a sibling window
#     that has written but not committed would collide with, and what this
#     window's own uncommitted edits already occupy.
#
# A hit in the tree scope but not at HEAD is exactly the case a HEAD-only
# check cannot see, which is why both scopes exist.
#
# Deliberate narrowings, disclosed:
#   * Git is reached through subprocess - there is no other way to read a
#     revision or the index. Purity here means no network and no writes, not
#     "no subprocess".
#   * The HEAD leg's output is prefixed "HEAD:" by git; that constant prefix
#     is stripped so both legs report the same repository-relative path.
#   * GIT_CEILING_DIRECTORIES is pinned to the parent of the scanned root, so
#     a directory that is not a repository fails closed at exit 3 instead of
#     silently borrowing an enclosing repository.
#   * Staged-but-unwritten blobs are not a scope.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import json
import os
import subprocess
import sys

SCOPES = ("head", "tree")

VERDICTS = ("FREE", "OCCUPIED")

HIT_KEYS = ("needle", "scope", "file", "line")

REPORT_KEYS = (
    "needles",
    "scopes",
    "by_needle",
    "head_count",
    "tree_count",
    "hits",
    "truncated",
    "verdict",
)

HEAD_PREFIX = "HEAD:"


class SeedAnchorError(Exception):
    """Raised when the anchor check cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _git(root, args):
    """Run one git command against root with a pinned ceiling directory."""
    env = dict(os.environ)
    env["GIT_CEILING_DIRECTORIES"] = os.path.dirname(os.path.abspath(root))
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        proc = subprocess.run(
            ["git", "-C", root] + list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
    except OSError as exc:
        raise SeedAnchorError("E_SAN_GIT", "cannot run git (%s)" % (exc,))
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"))


def _parse(scope, body):
    """Turn git grep -n output into hits, stripping the rev prefix (AC-SAN1)."""
    hits = []
    for line in body.splitlines():
        if not line:
            continue
        if scope == "head" and line.startswith(HEAD_PREFIX):
            line = line[len(HEAD_PREFIX):]
        path, sep, rest = line.partition(":")
        if not sep:
            continue
        number, sep2, text = rest.partition(":")
        if not sep2:
            continue
        try:
            line_no = int(number)
        except ValueError:
            continue
        hits.append({"file": path, "line": line_no, "text": text})
    hits.sort(key=lambda hit: (hit["file"], hit["line"]))
    return hits


def scan(root, needle, scope):
    """Every hit for one literal needle in one scope (AC-SAN1 / AC-SAN2)."""
    if not isinstance(needle, str) or not needle:
        raise SeedAnchorError("E_SAN_BAD_NEEDLE",
                              "needle must be non-empty text")
    if scope not in SCOPES:
        raise SeedAnchorError("E_SAN_BAD_SCOPE", "unknown scope %r" % (scope,))
    if not os.path.isdir(root):
        raise SeedAnchorError("E_SAN_GIT", "%s is not a directory" % (root,))
    if scope == "head":
        args = ["grep", "-F", "-n", "-I", "--no-color", "-e", needle,
                "HEAD", "--"]
    else:
        args = ["grep", "-F", "-n", "-I", "--no-color", "--untracked",
                "-e", needle, "--"]
    rc, out, err = _git(root, args)
    if rc == 1:
        return []
    if rc != 0:
        raise SeedAnchorError(
            "E_SAN_GIT",
            "git grep %s failed rc=%d (%s)"
            % (scope, rc, " ".join(err.split())[:200]))
    return _parse(scope, out)


def normalize_scopes(scopes):
    """Accepted scope inputs, returned in the canonical SCOPES order."""
    if scopes is None:
        return SCOPES
    if isinstance(scopes, str):
        given = [scopes]
    else:
        given = list(scopes)
    for scope in given:
        if scope not in SCOPES:
            raise SeedAnchorError("E_SAN_BAD_SCOPE",
                                  "unknown scope %r" % (scope,))
    ordered = tuple(scope for scope in SCOPES if scope in given)
    if not ordered:
        raise SeedAnchorError("E_SAN_BAD_SCOPE", "no scope requested")
    return ordered


def normalize_needles(needles):
    """A non-empty ordered list of literal needles, duplicates dropped."""
    if isinstance(needles, str):
        needles = [needles]
    out = []
    for needle in needles:
        if not isinstance(needle, str) or not needle:
            raise SeedAnchorError("E_SAN_BAD_NEEDLE",
                                  "needle must be non-empty text")
        if needle not in out:
            out.append(needle)
    if not out:
        raise SeedAnchorError("E_SAN_BAD_NEEDLE", "at least one needle")
    return out


def audit(root, needles, scopes=None, limit=20):
    """The closed report shape (AC-SAN3)."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise SeedAnchorError("E_SAN_BAD_LIMIT",
                              "limit must be a non-negative int")
    ordered_needles = normalize_needles(needles)
    ordered_scopes = normalize_scopes(scopes)
    rows = []
    by_needle = []
    for needle in ordered_needles:
        entry = {"needle": needle}
        for scope in SCOPES:
            if scope not in ordered_scopes:
                entry[scope] = None
                continue
            hits = scan(root, needle, scope)
            entry[scope] = len(hits)
            for hit in hits:
                rows.append({"needle": needle, "scope": scope,
                             "file": hit["file"], "line": hit["line"]})
        by_needle.append(entry)
    truncated = len(rows) > limit
    head_count = 0
    tree_count = 0
    for entry in by_needle:
        head_count += entry["head"] or 0
        tree_count += entry["tree"] or 0
    total = head_count + tree_count
    verdict = "FREE" if total == 0 else "OCCUPIED"
    return {
        "needles": ordered_needles,
        "scopes": list(ordered_scopes),
        "by_needle": by_needle,
        "head_count": head_count if "head" in ordered_scopes else None,
        "tree_count": tree_count if "tree" in ordered_scopes else None,
        "hits": rows[:limit],
        "truncated": truncated,
        "verdict": verdict,
    }


def require_free(root, needles, scopes=None, limit=20):
    """Refuse to seed on any hit (AC-SAN4)."""
    report = audit(root, needles, scopes=scopes, limit=limit)
    if report["verdict"] == "OCCUPIED":
        raise SeedAnchorError(
            "E_SAN_OCCUPIED",
            "%d hit(s) for %s" % (len(report["hits"]) if not report["truncated"]
                                  else (report["head_count"] or 0)
                                  + (report["tree_count"] or 0),
                                  ", ".join(report["needles"])))
    return report


def one_line(report):
    """The single line an operator reads."""
    return ("SEED ANCHOR needles=%d scopes=%s head=%s tree=%s hits=%d "
            "truncated=%s verdict=%s"
            % (len(report["needles"]), ",".join(report["scopes"]),
               report["head_count"], report["tree_count"],
               (report["head_count"] or 0) + (report["tree_count"] or 0),
               "yes" if report["truncated"] else "no", report["verdict"]))


def render(report):
    """Full text rendering: the one line, then every hit named."""
    out = [one_line(report)]
    for hit in report["hits"]:
        out.append("  HIT %s %s:%d needle=%s"
                   % (hit["scope"], hit["file"], hit["line"],
                      hit["needle"]))
    if report["truncated"]:
        out.append("  TRUNCATED detail cut at the requested limit")
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (no indent, ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    pinned_hits = []
    for hit in report["hits"]:
        row = {}
        for key in HIT_KEYS:
            row[key] = hit[key]
        pinned_hits.append(row)
    ordered["hits"] = pinned_hits
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: seed_anchor.py --check --needle TEXT [--needle TEXT ...]\n"
         "         [--root PATH] [--scope head|tree|both] [--limit N] "
         "[--json]\n"
         "  exit 0 = FREE (zero hits in every scanned scope)\n"
         "  exit 2 = OCCUPIED (refuse to seed) or bad flags\n"
         "  exit 3 = not a git repository, git failure, unreadable input\n")


def main(argv):
    check = False
    as_json = False
    needles = []
    scopes = ["head", "tree"]
    limit = 20
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--needle":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SAN_BAD_ARGS: --needle needs text\n")
                return 2
            needles.append(argv[index])
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SAN_BAD_ARGS: --root needs a path\n")
                return 2
            root = argv[index]
        elif arg == "--scope":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SAN_BAD_ARGS: --scope needs a value\n")
                return 2
            value = argv[index]
            if value == "both":
                scopes = ["head", "tree"]
            elif value in SCOPES:
                scopes = [value]
            else:
                sys.stdout.write("E_SAN_BAD_ARGS: unknown scope %s\n" % value)
                return 2
        elif arg == "--limit":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SAN_BAD_ARGS: --limit needs a number\n")
                return 2
            try:
                limit = int(argv[index])
            except ValueError:
                sys.stdout.write("E_SAN_BAD_ARGS: --limit needs a number\n")
                return 2
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_SAN_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if not check:
        sys.stdout.write("E_SAN_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = audit(root, needles, scopes=scopes, limit=limit)
    except SeedAnchorError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "OCCUPIED":
        if not as_json:
            sys.stdout.write("REFUSE TO SEED\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))