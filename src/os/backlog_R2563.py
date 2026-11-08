"""backlog_R2563 - mark the R2563 item done and prepend the R2564 first item."""

import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(BASE, "src", "os", "backlog.md")

DONE_MARK = "[x] [done 2026-11-08 R2563] [was carried 2026-11-08 R2562]"
NEW = (
    "- [ ] [carried 2026-11-08 R2563] R2564 first item: a VERIFICATION window "
    "on the battery the register now names first - reconcile-battery-R2563 at "
    "the pre-registered 611 suites / 4642 criteria, because this window moved "
    "the registry by one row and shipped a document (the R2168 mixed-tree "
    "rule). Re-measure the target by importing reconcile_all.SUITES before the "
    "launch, run the full battery on a CLEAN committed tree with git status "
    "empty, launch it detached through src/os/battery_stream.py with an "
    "explicit --evidence path and NEVER a shell redirection of its stdout into "
    "qa/ (the ps-utf16 trap), keep the red leg if it goes red and commit a "
    "birth-site repair ALONE before any retry, then run the four follow-up "
    "sections through src/os/battery_followup.py (its matrix section FAILS "
    "first by design and must not rewrite the doc; regenerate with "
    "src/sandbox/suite_matrix.py --evidence <leg> --stamp-from "
    "docs/sandbox-suite-matrix.md after) and land the verdict. On green go "
    "back to the product face the queue head names - re-read it with "
    "`python src/os/queue_head.py --head tech`, which this window left at "
    "state/queue/tech.md:601 prefix AC-PNDCE1 (criteria AC-PNDCE1..AC-PNDCE6 "
    "pinned in that row THIS window before any code): a module bound by "
    "`from pkg import helper` reads attr-base-local:helper, a helper constant "
    "declared ONLY inside a function body reads attr-plain-import, and a "
    "with-open-module() as m binding reads attr-with-as even when the call "
    "returns a module. NOTE measured many times: a commit that moves the queue "
    "must also re-derive docs/status-export.json and land its queue block "
    "through queue_export_gate_wire --execute. Also open and misc: state.json "
    "reads far past the 78500B waterline so state_fold --check reads FOLD-DUE "
    "and this build ships only a --check face, so the fold stays an OWED "
    "obligation seeded as state_fold_run (AC-SFOLD1..6); the open rows "
    "product-face-R2511, R2513, R2515, R2517 and R2522 still overstate "
    "outstanding work and were disclosed rather than hand-closed; queue_row "
    "--check still reads pre-existing VIOLATIONS on rows that predate this "
    "window; and BigDomain-OSLoop still reads InteractiveToken, which the "
    "2026-09-29 machine law forbids for every lane task (carried as the "
    "ceo-pending physical item loop-s4u-reconcile, needs an ELEVATED shell)."
)


def main():
    with open(P, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    target = lines[0]
    if not target.startswith("- [ ] [carried 2026-11-08 R2562] R2563 first item"):
        raise SystemExit("unexpected backlog head: " + target[:80])
    lines[0] = target.replace("- [ ] [carried 2026-11-08 R2562]",
                              DONE_MARK, 1)
    lines.insert(0, NEW)
    out = "\n".join(lines).encode("utf-8")
    tmp = P + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(out)
    os.replace(tmp, P)
    with open(P, "rb") as fh:
        back = fh.read()
    print("backlog bytes", len(back), "lines", back.count(b"\n") + 1,
          "crlf", back.count(b"\r\n"))


if __name__ == "__main__":
    main()