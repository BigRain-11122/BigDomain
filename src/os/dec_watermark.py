"""Source-anchored watermark, format v2 (D-20261025-08).

The five-silence scan advances its decisions baseline from a content
hash alone, so the same hash cannot tell "the content changed" from
"history was rewritten" or "I read an unmerged local ref". The group
decision of 2026-10-25 turns the watermark into a FOUR-TUPLE
{repo, commit_sha, blob_bytes, sha256} and pins a reproducible fetch
command beside it.

Comparison order (pinned): repo, then commit_sha, then blob_bytes,
then sha256. A tuple whose source disagrees (repo changed, or the same
commit and byte count carrying a different sha256) is STALE: the
watermark must not advance and one line is recorded instead, so no
consumption decision is ever taken against a ghost sha.

Pure stdlib, ASCII source, no network. Git is the only external tool.
"""

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

WATERMARK_FORMAT = "watermark-v2"
TUPLE_KEYS = ("repo", "commit_sha", "blob_bytes", "sha256")

# Verdicts returned by classify().
UNCHANGED = "unchanged"
MOVED = "moved"
STALE = "stale"
NEW = "new"
LEGACY = "legacy"

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_STALE = 3
EXIT_MOVED = 4


class WatermarkError(Exception):
    """Raised when git cannot resolve the requested ref or path."""


def _git(repo, args):
    proc = subprocess.run(["git", "-C", repo] + list(args),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise WatermarkError(proc.stderr.decode("utf-8", "replace").strip()
                             or "git %s failed" % " ".join(args))
    return proc.stdout


def _posix(path):
    return os.path.abspath(path).replace("\\", "/")


def repo_identity(repo):
    """Origin URL when the repo has one, else the absolute path.

    A repo label must identify the SOURCE, so a fork with a different
    remote can never look like the same origin.
    """
    try:
        url = _git(repo, ["config", "--get", "remote.origin.url"])
    except WatermarkError:
        url = b""
    url = url.decode("utf-8", "replace").strip()
    return url or _posix(repo)


def resolve(repo, path, ref):
    """Observe the four-tuple of one file at one ref."""
    commit = _git(repo, ["rev-parse", ref]).decode("ascii", "replace").strip()
    spec = "%s:%s" % (ref, path)
    blob_sha = _git(repo, ["rev-parse", spec]).decode("ascii", "replace").strip()
    size = int(_git(repo, ["cat-file", "-s", blob_sha]).decode("ascii").strip())
    blob = _git(repo, ["cat-file", "blob", blob_sha])
    return {
        "repo": repo_identity(repo),
        "commit_sha": commit,
        "blob_bytes": size,
        "sha256": hashlib.sha256(blob).hexdigest(),
    }


def fetch_command(entry):
    """One reproducible command that prints exactly the observed blob."""
    return 'git -C "%s" cat-file blob %s:%s' % (
        entry["repo_path"], entry["commit_sha"], entry["path"])


def classify(stored, observed):
    """Compare in the pinned order and return a verdict plus a note."""
    if not stored:
        return NEW, "no stored watermark"
    missing = [k for k in TUPLE_KEYS if k not in stored]
    if missing:
        return LEGACY, "stored watermark lacks %s" % ",".join(missing)
    if stored["repo"] != observed["repo"]:
        return STALE, "repo %s != %s" % (stored["repo"], observed["repo"])
    same_stamp = (stored["commit_sha"] == observed["commit_sha"]
                  and int(stored["blob_bytes"]) == int(observed["blob_bytes"]))
    if same_stamp:
        if stored["sha256"] == observed["sha256"]:
            return UNCHANGED, "same source and content"
        return STALE, ("same commit and byte count but a different"
                       " sha256: history was rewritten")
    return MOVED, "commit %s -> %s" % (stored["commit_sha"],
                                       observed["commit_sha"])


def build_entry(observed, repo_path, path, ref, now_utc):
    entry = dict(observed)
    entry["format"] = WATERMARK_FORMAT
    entry["path"] = path
    entry["ref"] = ref
    entry["repo_path"] = _posix(repo_path)
    entry["fetch"] = fetch_command(entry)
    entry["recorded_utc"] = now_utc
    return entry


def dumps(entry):
    return json.dumps(entry, indent=1, sort_keys=True,
                      ensure_ascii=True) + "\n"


def write_atomic(path, entry):
    """Serialize fully, then temp + replace so no half file survives."""
    text = dumps(entry)
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(tmp, path)


def load(path):
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def record(repo, path, ref, watermark, stamp=None):
    observed = resolve(repo, path, ref)
    stored = load(watermark)
    verdict, note = classify(stored, observed)
    if verdict == STALE:
        return verdict, note, stored
    entry = build_entry(observed, repo, path, ref, stamp or now_utc())
    write_atomic(watermark, entry)
    return verdict, note, entry


def check(watermark, repo=None, path=None, ref=None):
    stored = load(watermark)
    if not stored:
        return NEW, "no stored watermark", {}
    repo = repo or stored.get("repo_path") or stored.get("repo")
    path = path or stored.get("path")
    ref = ref or stored.get("ref") or "origin/main"
    if not repo or not path:
        return LEGACY, "stored watermark lacks repo or path", stored
    if not os.path.isdir(repo):
        return STALE, "repo path %s is not a directory" % repo, stored
    observed = resolve(repo, path, ref)
    verdict, note = classify(stored, observed)
    return verdict, note, stored


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="dec_watermark",
        description="Four-tuple source watermark (D-20261025-08).")
    sub = parser.add_subparsers(dest="command")
    rec = sub.add_parser("record", help="observe and record the watermark")
    rec.add_argument("--repo", required=True)
    rec.add_argument("--path", required=True)
    rec.add_argument("--ref", default="origin/main")
    rec.add_argument("--watermark", required=True)
    rec.add_argument("--now", default=None)
    chk = sub.add_parser("check", help="re-observe and classify")
    chk.add_argument("--watermark", required=True)
    chk.add_argument("--repo", default=None)
    chk.add_argument("--path", default=None)
    chk.add_argument("--ref", default=None)
    args = parser.parse_args(argv)
    if args.command == "record":
        verdict, note, entry = record(args.repo, args.path, args.ref,
                                      args.watermark, args.now)
        print("WATERMARK %s: %s" % (verdict, note), flush=True)
        return EXIT_OK if verdict != STALE else EXIT_STALE
    if args.command == "check":
        verdict, note, _stored = check(args.watermark, args.repo,
                                       args.path, args.ref)
        print("WATERMARK %s: %s" % (verdict, note), flush=True)
        if verdict == STALE:
            return EXIT_STALE
        if verdict == MOVED:
            return EXIT_MOVED
        return EXIT_OK
    parser.print_usage(sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())