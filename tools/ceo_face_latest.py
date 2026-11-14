"""R2751 read side for the CEO-face recent-artifact fields.

Pre-registered at R2750 with three criteria, BEFORE any code:
  C1 on a round that landed a qa artifact, latest_artifact and last_artifact
     both read that artifact BYTE-IDENTICALLY to the shipped derive_latest;
  C2 on a wait round, latest_artifact keeps the strict
     'none landed yet for R<tick>' wording while last_artifact names the
     newest PRIOR qa artifact WITH its round number;
  C3 re-rendering the real export must never present a blank
     recent-artifact line while any qa artifact exists for an earlier round.

The shipped face has two measured defects on the live document:
  (a) src/os/export_R2431.py derive_latest scans only qa/ for the string
      'R<tick>', so a wait round renders 'none landed yet for R<tick>' even
      though artifacts landed in an earlier round;
  (b) main() assigns ceo['last_artifact'] = latest, i.e. the SAME value, so
      the field cannot serve as the fallback its name promises.

This module is the READ SIDE only: pure functions over a listing supplied by
the caller, plus two CLIs. No clock, no shell, no network, no write path, and
it does not touch src/os. Wiring the two fields into export_R2431.py is owed
to the first window that opens after the battery leg closes, because src/os
bytes are frozen while a battery runs (R2746/R2747 reason).
"""

import argparse
import io
import json
import os
import re
import sys
import tempfile

ROUND_RE = re.compile(r"R(\d+)")
NONE_TMPL = "none landed yet for R%s"


def round_of(name):
    """The round number a qa filename carries, or None."""
    match = ROUND_RE.search(name)
    return int(match.group(1)) if match else None


def render(entries):
    """'<name> (<bytes>B)' joined by ' + ', first four -- shipped rendering."""
    return " + ".join("%s (%dB)" % (name, size) for name, size in entries[:4])


def none_line(tick):
    return NONE_TMPL % tick


def derive_latest_artifact(listing, tick):
    """Shipped derive_latest semantics on a supplied listing."""
    hits = sorted(((n, b) for n, b in listing if ("R%s" % tick) in n),
                  key=lambda item: item[0])
    if not hits:
        return none_line(tick)
    return render(hits)


def derive_last_artifact(listing, tick):
    """latest when this round landed something, else the newest PRIOR round."""
    latest = derive_latest_artifact(listing, tick)
    if latest != none_line(tick):
        return latest
    prior = [(n, b) for n, b in listing
             if round_of(n) is not None and round_of(n) < tick]
    if not prior:
        return latest
    newest = max(round_of(n) for n, _ in prior)
    entries = sorted(((n, b) for n, b in prior if round_of(n) == newest),
                     key=lambda item: item[0])
    return "R%d: %s" % (newest, render(entries))


def scan(directory):
    """(name, bytes) for regular files, sorted by name, OSError-tolerant."""
    out = []
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return out
    for name in names:
        path = os.path.join(directory, name)
        try:
            if os.path.isfile(path):
                out.append((name, os.path.getsize(path)))
        except OSError:
            continue
    return out


def evaluate(listing, tick):
    """Both fields plus which criterion this tree exercises."""
    latest = derive_latest_artifact(listing, tick)
    last = derive_last_artifact(listing, tick)
    if latest != none_line(tick):
        mode = "round"
    elif last != none_line(tick):
        mode = "fallback"
    else:
        mode = "empty"
    return {"latest_artifact": latest, "last_artifact": last, "mode": mode}


def criteria(listing, tick):
    """C1/C2/C3 as applicable on this listing; returns [(key, ok, detail)]."""
    fields = evaluate(listing, tick)
    latest, last, mode = (fields["latest_artifact"], fields["last_artifact"],
                          fields["mode"])
    prior_exists = any(round_of(n) is not None and round_of(n) < tick
                       for n, _ in listing)
    out = []
    if mode == "round":
        out.append(("C1-round-identity", last == latest,
                    "last_artifact equals latest_artifact byte for byte"))
    else:
        out.append(("C1-round-identity", True, "not applicable: no qa artifact for this round"))
    if mode == "fallback":
        out.append(("C2-wait-fallback",
                    latest == none_line(tick) and last.startswith("R"),
                    "strict none-line kept while last_artifact names a prior round"))
    else:
        out.append(("C2-wait-fallback", True, "not applicable: mode=%s" % mode))
    out.append(("C3-never-blank", (not prior_exists) or last != none_line(tick),
                "prior qa artifacts exist=%s" % prior_exists))
    return out, fields


REAL_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _shipped_latest(world_root, tick):
    """The shipped function itself; only its REPO constant is pointed at a world."""
    base = os.path.join(REAL_REPO, "src", "os")
    if base not in sys.path:
        sys.path.insert(0, base)
    import export_R2431 as shipped
    saved = shipped.REPO
    try:
        shipped.REPO = world_root
        return shipped.derive_latest(tick)
    finally:
        shipped.REPO = saved


def _world(root, files):
    os.makedirs(os.path.join(root, "qa"))
    for name, size in files:
        with io.open(os.path.join(root, "qa", name), "wb") as handle:
            handle.write(b"x" * size)
    return root


def state_tick(repo_root):
    """The live tick, read-only from state.json; 0 when unreadable."""
    try:
        with io.open(os.path.join(repo_root, "src", "os", "state.json"),
                     encoding="utf-8") as handle:
            return int(json.load(handle).get("tick") or 0)
    except (OSError, ValueError):
        return 0


def self_check(repo_root):
    """Private worlds, then equality against the shipped tool on each."""
    rows = []

    def one(key, ok, detail):
        rows.append({"check": key, "ok": bool(ok), "detail": detail})

    worlds = []
    temp = tempfile.mkdtemp(prefix="ceo-face-latest-")
    worlds.append(("W1-round", 2751,
                   [("a-R2751.log", 10), ("b-R2751-R2751.log", 20)]))
    worlds.append(("W2-wait", 2751, [("x-R2749.log", 5), ("y-R2750.log", 7)]))
    worlds.append(("W3-empty", 2751, []))
    worlds.append(("W4-future-guard", 2751, [("z-R2800.log", 3)]))
    worlds.append(("W5-cap", 2751, [("f%d-R2750.log" % i, i) for i in range(1, 7)]))

    for name, tick, files in worlds:
        root = _world(os.path.join(temp, name), files)
        listing = scan(os.path.join(root, "qa"))
        fields = evaluate(listing, tick)
        shipped = _shipped_latest(root, tick)
        one("%s-shipped-identity" % name,
            fields["latest_artifact"] == shipped,
            "latest=%r shipped=%r" % (fields["latest_artifact"], shipped))
        one("%s-criteria" % name,
            all(ok for _, ok, _ in criteria(listing, tick)[0]),
            json.dumps(fields, sort_keys=True))

    root = os.path.join(temp, "W2-wait")
    fields = evaluate(scan(os.path.join(root, "qa")), 2751)
    one("W2-names-prior-round",
        fields["last_artifact"] == "R2750: y-R2750.log (7B)",
        "last=%r" % fields["last_artifact"])

    root = os.path.join(temp, "W4-future-guard")
    fields = evaluate(scan(os.path.join(root, "qa")), 2751)
    one("W4-does-not-name-future",
        fields["last_artifact"] == none_line(2751),
        "last=%r" % fields["last_artifact"])

    root = os.path.join(temp, "W5-cap")
    fields = evaluate(scan(os.path.join(root, "qa")), 2751)
    one("W5-four-entry-cap",
        fields["last_artifact"].count(" + ") == 3
        and fields["last_artifact"].startswith("R2750: "),
        "last=%r" % fields["last_artifact"])

    # Live tree identity on the newest round at or below the live tick. The
    # bound matters: qa/ also carries diagnostic fixtures such as R9999, and a
    # round number that never ran is not a round to prove identity on.
    live = scan(os.path.join(repo_root, "qa"))
    bound = state_tick(repo_root)
    rounds = [round_of(n) for n, _ in live]
    rounds = [r for r in rounds if r is not None and (not bound or r <= bound)]
    live_tick = max(rounds or [0])
    fields = evaluate(live, live_tick)
    shipped = _shipped_latest(repo_root, live_tick)
    one("LIVE-round-identity-%d" % live_tick,
        fields["latest_artifact"] == shipped and fields["last_artifact"] == shipped,
        "latest=%r shipped=%r" % (fields["latest_artifact"], shipped))
    return rows, fields, live_tick


def main(argv=None):
    parser = argparse.ArgumentParser(description="CEO-face recent-artifact read side")
    parser.add_argument("--qa-dir", default="qa")
    parser.add_argument("--tick", type=int, default=0)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.check and not args.self_check:
        parser.error("choose --check or --self-check")
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rc = 0
    if args.check:
        listing = scan(os.path.join(repo_root, args.qa_dir))
        rows, fields = criteria(listing, args.tick)
        for key, ok, detail in rows:
            sys.stdout.write("%s %s %s\n" % ("PASS" if ok else "FAIL", key, detail))
            if not ok:
                rc = 2
        sys.stdout.write("FIELDS %s\n" % json.dumps(fields, sort_keys=True))
    if args.self_check:
        rows, fields, live_tick = self_check(repo_root)
        for row in rows:
            sys.stdout.write("%s %s %s\n"
                             % ("PASS" if row["ok"] else "FAIL",
                                row["check"], row["detail"]))
            if not row["ok"]:
                rc = 2
        sys.stdout.write("SELF-CHECK %d/%d rc=%d live_tick=%d\n"
                         % (sum(1 for r in rows if r["ok"]), len(rows), rc, live_tick))
    if args.json:
        sys.stdout.write("JSON %s\n" % json.dumps({"rc": rc}, sort_keys=True))
    return rc


if __name__ == "__main__":
    sys.exit(main())
