"""stamp_exempt_seed_guard_wire.py - the third declaration writer asks the guard.

Criteria AC-SGS1..AC-SGS6 were pinned in state/queue/tech.md:403 as the R2346
seed row BEFORE this file existed. Anchor check at HEAD 2026-11-02: the six
names (stamp_exempt_seed_guard_wire, AC-SGS, E_SGS, os-stamp-exempt-seed-guard-
wire, test_stamp_exempt_seed_guard_wire, TEMP_SUFFIX .sgsw-tmp) were git grep
-F hits ONLY in prose (docs/status-export.json, src/os/backlog.md,
src/os/closeout_R2346.py, src/os/closeout_R2360.py, src/os/export_R2360.py,
state/queue/tech.md) with zero executable occupancy.

Why this exists: after R2346 the pinned-text guard covered two of the three
writers of state/queue/stamp_exempt.json - stamp_exempt_append and
stamp_exempt_prune ask it - while the seed generator
(stamp_exempt_seed_R2280.py) still wrote the declaration straight through one
io.open(path, "w"): no pin, no digest, no atomic replace. A seed run over a
declaration another writer had just changed could clobber it, and nothing
named the collision.

The wire is the seed's plan/execute pair:

  * plan(path, body) reads the declaration as it stands right now, pins that
    reading (digest and byte count), counts the entries before and after, and
    returns a report naming what it would replace. It writes nothing, so a
    seed is never silent;
  * execute(plan) hands the pinned reading and the rendered bytes to
    stamp_exempt_guard.commit, which refuses E_SEG_STALE before a single byte
    when the declaration moved, and otherwise performs the one atomic replace
    with its read-back.

The wire deliberately carries no write mechanics of its own: there is no
second temp file and no second os.replace in this file, so the staleness law
and the atomic replace live in exactly one place.

Pure stdlib, pure-ASCII source, zero network, no clock.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import stamp_exempt_guard as SEG  # noqa: E402

LABEL = "STAMP EXEMPT SEED GUARD"

TEMP_SUFFIX = ".sgsw-tmp"

CODES = {
    "render": "E_SGS_RENDER",
    "empty": "E_SGS_EMPTY",
}

PLAN_KEYS = (
    "action",
    "path",
    "pinned",
    "entries_before",
    "entries_after",
    "before_bytes",
    "after_bytes",
    "dry_run",
)

USAGE = ("usage: stamp_exempt_seed_guard_wire.py [ROOT] [--execute]\n"
         "  default is a dry run: it prints the plan and writes nothing\n")


class SeedWireError(Exception):
    """One refusal with its own code and detail."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s %s" % (code, detail))
        self.code = code
        self.detail = detail


def count_entries(text):
    """How many exemptions a declaration text carries (0 for an empty file)."""
    if not text.strip():
        return 0
    try:
        parsed = json.loads(text)
    except ValueError as exc:
        raise SeedWireError(CODES["render"],
                            "declaration is not JSON: %s" % exc)
    if not isinstance(parsed, dict):
        raise SeedWireError(CODES["render"],
                            "declaration is not an object")
    entries = parsed.get("exemptions")
    if not isinstance(entries, list):
        raise SeedWireError(CODES["render"],
                            "declaration carries no exemptions array")
    return len(entries)


def render_body(body_bytes):
    """The rendered payload must be bytes, ASCII JSON, and non-empty."""
    if isinstance(body_bytes, str):
        try:
            body_bytes = body_bytes.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise SeedWireError(CODES["render"], "payload is not utf-8: %s" % exc)
    if not isinstance(body_bytes, bytes) or not body_bytes:
        raise SeedWireError(CODES["empty"], "rendered declaration is empty")
    try:
        text = body_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SeedWireError(CODES["render"], "payload is not utf-8: %s" % exc)
    try:
        count_entries(text)
    except SeedWireError:
        raise
    return body_bytes, text


def plan(path, body_bytes, dry_run=True):
    """Read the declaration as it stands, pin it, and name the replacement.

    Nothing is written here: the report carries the reading that execute will
    demand back, the entry counts on both sides and the byte counts, so a seed
    always says what it would replace before it can replace anything.
    """
    payload, rendered = render_body(body_bytes)
    try:
        with io.open(path, "r", encoding="utf-8", newline="") as handle:
            current = handle.read()
    except (IOError, OSError) as exc:
        raise SeedWireError(SEG.CODES["unreadable"], "%s (%s)" % (path, exc))
    try:
        entries_before = count_entries(current)
    except SeedWireError:
        entries_before = 0
    return {
        "action": "seed",
        "path": path,
        "pinned": SEG.pin(current),
        "entries_before": entries_before,
        "entries_after": count_entries(rendered),
        "before_bytes": len(current.encode("utf-8")),
        "after_bytes": len(payload),
        "dry_run": bool(dry_run),
        "payload": payload,
    }


def execute(plan_report):
    """Commit a plan through the guard: never a second write path."""
    report = SEG.commit(plan_report["path"], plan_report["pinned"],
                        plan_report["payload"], TEMP_SUFFIX)
    merged = dict(report)
    merged["entries_before"] = plan_report["entries_before"]
    merged["entries_after"] = plan_report["entries_after"]
    merged["replaced_digest"] = plan_report["pinned"]["digest"]
    return merged


def one_line(report):
    """The wire's own reconcile label, one line, stable field order."""
    if "wrote" in report:
        return ("%s wrote=%s read_back=%s entries=%d->%d before=%dB after=%dB "
                "replaced=%s now=%s"
                % (LABEL, "yes" if report.get("wrote") else "no",
                   "ok" if report.get("read_back_ok") else "BAD",
                   report.get("entries_before"), report.get("entries_after"),
                   report.get("before_bytes"), report.get("after_bytes"),
                   report.get("replaced_digest") or report.get("digest_before"),
                   report.get("digest_after")))
    return ("%s plan path=%s entries=%d->%d before=%dB after=%dB pin=%s dry=%s"
            % (LABEL, report.get("path"), report.get("entries_before"),
               report.get("entries_after"), report.get("before_bytes"),
               report.get("after_bytes"),
               (report.get("pinned") or {}).get("digest"),
               "yes" if report.get("dry_run") else "no"))


def plan_for_root(root, execute_it=False):
    """Plan (and optionally execute) a seed of the live declaration.

    Body rendering is delegated to stamp_exempt_seed_R2280 (build + render),
    so entry rules stay with that module and this one stays the write path.
    """
    sys.path.insert(0, BASE)
    import stamp_exempt_seed_R2280 as seeder
    import queue_done_stamp_exempt as SX
    gate, entries = seeder.build(root)
    body = seeder.render(entries)
    path = os.path.join(root, SX.DECL_REL)
    report = plan(path, body, dry_run=not execute_it)
    if not execute_it:
        return gate, report, None
    done = execute(report)
    return gate, report, done


def main(argv):
    root = REPO
    execute_it = False
    for arg in argv:
        if arg == "--execute":
            execute_it = True
        elif arg in ("-h", "--help"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write(USAGE)
            return 2
        else:
            root = arg
    gate, report, done = plan_for_root(root, execute_it)
    sys.stdout.write(one_line(report) + "\n")
    if done is not None:
        sys.stdout.write(one_line(done) + "\n")
    else:
        sys.stdout.write("%s dry run: nothing written (pass --execute to "
                         "commit)\n" % LABEL)
    sys.stdout.write("%s gate violations=%d verdict=%s\n"
                     % (LABEL, gate["violation_count"], gate["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))