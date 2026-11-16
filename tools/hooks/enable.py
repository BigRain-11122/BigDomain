"""Measured enablement for the commit-side freeze gate (R2840, AC-HK4).

`core.hooksPath` is host-local configuration, so it cannot be shipped by
committing a file: what ships is the hook plus this vehicle that sets and then
READS BACK the setting. Unset is reported as unset, never assumed.

  python tools/hooks/enable.py --check    read only, exit 0 ENABLED / 2 DISABLED
  python tools/hooks/enable.py --apply    set core.hooksPath, verify read-back

  exit 0 = ENABLED (check) or APPLIED (apply)
  exit 2 = E_HK_NOT_ENABLED (check) or E_HK_APPLY_FAILED (apply)
  exit 3 = E_HK_NO_GIT / E_HK_NO_HOOK
  exit 5 = E_HK_BAD_FLAGS
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HOOK_REL = "tools/hooks"

USAGE = (
    "usage: enable.py [--check | --apply] [--root PATH] [--help]\n"
    "  --check  report hooks_path and whether the gate is enabled\n"
    "  --apply  set core.hooksPath to tools/hooks and read it back\n"
    "  --root   git work tree (default the tree above tools/)\n"
    "  exit 0 enabled/applied, 2 not enabled/apply failed, 3 no git/hook,\n"
    "  5 bad flags\n"
)


def git(root, *args):
    proc = subprocess.run(["git", "-C", root] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace").strip(),
            proc.stderr.decode("utf-8", "replace").strip())


def read_hooks_path(root):
    """The configured hooks path, or '' when git says it is unset."""
    code, out, _ = git(root, "config", "--get", "core.hooksPath")
    return out if code == 0 else ""


def hook_present(root):
    return os.path.isfile(os.path.join(root, HOOK_REL, "pre-commit"))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--help" in argv or "-h" in argv:
        sys.stdout.write(USAGE)
        return 0
    apply_it = False
    check_it = False
    root = ROOT
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--apply":
            apply_it = True
            i += 1
        elif arg == "--check":
            check_it = True
            i += 1
        elif arg == "--root":
            if i + 1 >= len(argv):
                sys.stderr.write("E_HK_BAD_FLAGS missing value for --root\n")
                return 5
            root = argv[i + 1]
            i += 2
        else:
            sys.stderr.write("E_HK_BAD_FLAGS unknown argument %s\n" % arg)
            return 5
    if apply_it == check_it:
        sys.stderr.write(USAGE)
        return 5

    code, _, err = git(root, "rev-parse", "--show-toplevel")
    if code != 0:
        sys.stderr.write("E_HK_NO_GIT %s\n" % err)
        return 3
    if not hook_present(root):
        sys.stderr.write("E_HK_NO_HOOK %s/pre-commit\n"
                         % HOOK_REL)
        return 3

    if apply_it:
        code, _, err = git(root, "config", "core.hooksPath", HOOK_REL)
        if code != 0:
            sys.stderr.write("E_HK_APPLY_FAILED %s\n" % err)
            return 2
        back = read_hooks_path(root)
        if back.replace("\\", "/").strip("/") != HOOK_REL:
            sys.stderr.write("E_HK_APPLY_FAILED read-back=%r\n" % back)
            return 2
        sys.stdout.write("APPLIED hooks_path=%s hook_present=yes rc=0\n"
                         % HOOK_REL)
        return 0

    configured = read_hooks_path(root)
    enabled = configured.replace("\\", "/").strip("/") == HOOK_REL
    freeze = "unknown"
    try:
        sys.path.insert(0, os.path.join(root, "src", "os"))
        import one_off_round_scripts as law

        freeze = law.FREEZE_ROUND
    except Exception:
        pass
    verdict = "ENABLED" if enabled else "DISABLED"
    sys.stdout.write(
        "HOOKS hooks_path=%s hook_present=yes freeze=%s verdict=%s\n"
        % (configured if configured else "(unset)", freeze, verdict))
    if not enabled:
        sys.stderr.write("E_HK_NOT_ENABLED core.hooksPath is not %s; run "
                         "python tools/hooks/enable.py --apply\n" % HOOK_REL)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
