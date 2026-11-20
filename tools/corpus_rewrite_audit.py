"""Corpus rewrite audit - does the drift law's evidence corpus get rewritten
in place, and what can a stat-only fingerprint actually see?

WHY THIS TOOL EXISTS (measured at R3102, not assumed):
the R3101 board row measured that a windowed drift scan would cost 180.8ms
instead of 1216.8ms, and the round refused it on a LAW argument ("skipping old
files turns drift detection into sampling"), not on a number. The R3102 row
asked for that refusal to become falsifiable: are old evidence files ever
rewritten in place, and would a cheap stat fingerprint be equivalent to the
full read? Three readings answered it on this tree:

  * git history: 71 of 4,122 tracked evidence files were MODIFIED after being
    added - 109 modify events across 73 commits - so "old evidence never
    changes" is false as a historical statement;
  * recursive basenames: 4,125 .log files, 0 duplicate basenames;
  * a stat-only pass over the whole corpus costs ~9.6ms against ~735ms to read
    it, so the ceiling of any windowed scheme is ~77x;
  * the fingerprint blind spot is REACHABLE: a same-length rewrite whose
    mtime_ns is restored reads as unchanged, and R3098 measured that two
    different writes inside one second carry the same st_mtime_ns on NTFS.

RULING (board, R3102): the sampling law is REFUSED, and the compensation arm
(stat fingerprint + read only what moved) ships as an INSTRUMENT, not as a new
law - it cannot pair with a same-size, same-mtime rewrite, so it cannot stand
in for the whole-corpus read. `--manifest-out` / `--verify` make that
compensation arm executable by anyone who wants to re-measure it.

Read-only toward the repository: git log is read through subprocess, evidence
files are opened for reading only, the blind-spot world is a temp directory.
Zero socket, zero network, zero clock dependence beyond measured durations.

CLI:
    python tools/corpus_rewrite_audit.py [--qa PATH] [--json]
    python tools/corpus_rewrite_audit.py --manifest-out FILE
    python tools/corpus_rewrite_audit.py --verify FILE
Lines (one per reading, plus one derived verdict):
    CORPUS-REWRITES tracked= commits= files= events=
    CORPUS-DUPLICATES log_files= basenames= duplicate_names= duplicate_files=
    CORPUS-COST stat_only_ms= read_all_ms= speedup= bytes=
    CORPUS-BLIND-SPOT undetected= detected_by_size= detected_by_mtime=
    CORPUS-VERDICT sampling-law=REFUSED|UNREFUTED|UNKNOWN reason=...
Exit 0 = every face answered, 2 = git cannot answer (named), 3 = no corpus.
"""
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QA = os.path.join(ROOT, "qa")


def log_files(path):
    """Yield (directory, name) for every .log under path, recursively."""
    for base, dirs, files in os.walk(path):
        for name in files:
            if name.lower().endswith(".log"):
                yield base, name


def git_modify_census(root=ROOT, pathspec="qa"):
    """Tracked evidence files modified after being added, from git history."""
    try:
        log = subprocess.run(
            ["git", "-C", root, "log", "--diff-filter=M", "--name-only",
             "--format=%x01%H", "--", pathspec],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tracked = subprocess.run(
            ["git", "-C", root, "ls-files", pathspec],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        return {"error": "E_CRA_NO_GIT", "detail": str(exc)[:160]}
    if log.returncode != 0 or tracked.returncode != 0:
        detail = (log.stderr or tracked.stderr or b"")
        return {"error": "E_CRA_NO_GIT",
                "detail": detail.decode("utf-8", "replace").strip()[:160]}
    names = [n.strip() for n in tracked.stdout.decode("utf-8", "replace").split("\n")
             if n.strip().lower().endswith(".log")]
    commits = 0
    files = []
    events = 0
    for line in log.stdout.decode("utf-8", "replace").split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("\x01"):
            commits += 1
            continue
        files.append(line)
        events += 1
    return {"tracked": len(names), "commits": commits,
            "files": len(set(files)), "events": events,
            "modified": sorted(set(files))}


def basename_census(path=QA):
    """Count .log basenames over the whole tree, duplicates included."""
    names = {}
    for base, name in log_files(path):
        full = os.path.join(base, name)
        names.setdefault(name, []).append(
            os.path.relpath(full, path).replace(os.sep, "/"))
    dups = {k: sorted(v) for k, v in names.items() if len(v) > 1}
    return {"log_files": sum(len(v) for v in names.values()),
            "basenames": len(names),
            "duplicate_names": len(dups),
            "duplicate_files": sum(len(v) for v in dups.values()),
            "duplicates": dups}


def manifest(path=QA):
    """name -> [size, mtime_ns] for every .log under path."""
    table = {}
    for base, name in log_files(path):
        full = os.path.join(base, name)
        st = os.stat(full)
        table[os.path.relpath(full, path).replace(os.sep, "/")] = [
            st.st_size, st.st_mtime_ns]
    return table


def verify_manifest(path, table):
    """Compare a manifest against the world, by size and mtime_ns only."""
    current = manifest(path)
    changed = sorted(k for k in current
                     if k in table
                     and (table[k][0], table[k][1])
                     != (current[k][0], current[k][1]))
    missing = sorted(k for k in table if k not in current)
    added = sorted(k for k in current if k not in table)
    return {"files": len(current), "changed": changed,
            "missing": missing, "added": added}


def _pass(path, read):
    t0 = time.perf_counter()
    files = 0
    size = 0
    for base, name in log_files(path):
        full = os.path.join(base, name)
        if read:
            with open(full, "rb") as handle:
                size += len(handle.read())
        else:
            size += os.stat(full).st_size
        files += 1
    return {"files": files, "bytes": size,
            "ms": round((time.perf_counter() - t0) * 1000.0, 1)}


def blind_spot():
    """Measure what a size+mtime_ns fingerprint can and cannot see."""
    with tempfile.TemporaryDirectory(prefix="cra-blind-") as world:
        path = os.path.join(world, "a.log")
        with open(path, "wb") as handle:
            handle.write(b"aaaa\n")
        st = os.stat(path)
        table = {"a.log": [st.st_size, st.st_mtime_ns]}
        with open(path, "wb") as handle:
            handle.write(b"bbbb\n")
        os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))
        hidden = "a.log" not in verify_manifest(world, table)["changed"]
        with open(path, "wb") as handle:
            handle.write(b"bbbbbb\n")
        by_size = "a.log" in verify_manifest(world, table)["changed"]
        table2 = manifest(world)
        os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 1000000000))
        by_mtime = "a.log" in verify_manifest(world, table2)["changed"]
    return {"undetected": hidden, "detected_by_size": by_size,
            "detected_by_mtime": by_mtime}


def verdict(payload):
    """Derived from the readings, never typed: a rewrite history or a reachable
    blind spot refuses the sampling law; nothing else is claimed."""
    rw = payload["rewrites"]
    if rw.get("error"):
        return "sampling-law=UNKNOWN reason=%s" % rw["error"]
    if rw["events"] > 0 or payload["blind_spot"]["undetected"]:
        return ("sampling-law=REFUSED reason=rewrites=%d blind_spot=%s"
                % (rw["events"], payload["blind_spot"]["undetected"]))
    return "sampling-law=UNREFUTED reason=rewrites=0 blind_spot=False"


def audit(root=ROOT, qa=None):
    corpus = qa or os.path.join(root, "qa")
    rewrites = git_modify_census(root)
    duplicates = basename_census(corpus)
    stat = _pass(corpus, False)
    read = _pass(corpus, True)
    blind = blind_spot()
    speedup = round(read["ms"] / stat["ms"], 1) if stat["ms"] else 0.0
    payload = {"rewrites": rewrites, "duplicates": duplicates,
               "cost": {"stat": stat, "read": read, "speedup": speedup},
               "blind_spot": blind}
    payload["verdict"] = verdict(payload)
    return payload


def render(payload):
    rw = payload["rewrites"]
    if rw.get("error"):
        print("CORPUS-REWRITES error=%s detail=%s"
              % (rw["error"], rw["detail"]))
    else:
        print("CORPUS-REWRITES tracked=%d commits=%d files=%d events=%d"
              % (rw["tracked"], rw["commits"], rw["files"], rw["events"]))
    d = payload["duplicates"]
    print("CORPUS-DUPLICATES log_files=%d basenames=%d duplicate_names=%d "
          "duplicate_files=%d"
          % (d["log_files"], d["basenames"], d["duplicate_names"],
             d["duplicate_files"]))
    c = payload["cost"]
    print("CORPUS-COST stat_only_ms=%.1f read_all_ms=%.1f speedup=%.1f "
          "bytes=%d"
          % (c["stat"]["ms"], c["read"]["ms"], c["speedup"],
             c["read"]["bytes"]))
    b = payload["blind_spot"]
    print("CORPUS-BLIND-SPOT undetected=%s detected_by_size=%s "
          "detected_by_mtime=%s"
          % (b["undetected"], b["detected_by_size"], b["detected_by_mtime"]))
    print("CORPUS-VERDICT " + payload["verdict"])


def main(argv):
    corpus = QA
    as_json = False
    manifest_out = None
    verify = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--json":
            as_json = True
        elif arg == "--qa" and i + 1 < len(argv):
            i += 1
            corpus = os.path.abspath(argv[i])
        elif arg == "--manifest-out" and i + 1 < len(argv):
            i += 1
            manifest_out = os.path.abspath(argv[i])
        elif arg == "--verify" and i + 1 < len(argv):
            i += 1
            verify = os.path.abspath(argv[i])
        else:
            print("usage: corpus_rewrite_audit.py [--qa PATH] [--json] "
                  "[--manifest-out FILE] [--verify FILE]")
            return 3
        i += 1
    if not os.path.isdir(corpus):
        print("E_CRA_NO_CORPUS %s" % corpus)
        return 3
    if manifest_out:
        with open(manifest_out, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest(corpus), handle, sort_keys=True, indent=1)
            handle.write("\n")
        print("MANIFEST-WRITE files=%d path=%s"
              % (len(manifest(corpus)), manifest_out))
        return 0
    if verify:
        with open(verify, encoding="utf-8") as handle:
            table = json.load(handle)
        report = verify_manifest(corpus, table)
        print("MANIFEST-VERIFY files=%d changed=%d missing=%d added=%d"
              % (report["files"], len(report["changed"]),
                 len(report["missing"]), len(report["added"])))
        for key in ("changed", "missing", "added"):
            for name in report[key][:10]:
                print("MANIFEST-%s %s" % (key.upper(), name))
        return 0 if not (report["changed"] or report["missing"]
                         or report["added"]) else 1
    payload = audit(ROOT, corpus)
    if as_json:
        print(json.dumps(payload, sort_keys=True, indent=1))
    else:
        render(payload)
    return 2 if payload["rewrites"].get("error") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
