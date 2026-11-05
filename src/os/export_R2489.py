"""export_R2489 - refresh docs/status-export.json for the R2489 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2489 business window: the membership page - the 'what do I hold "
           "now' side of the 19.9 entrance - is now one click from the entry "
           "page and one click from the control panel, where R2487 had left it "
           "reachable only by a command nobody had been told about")

base.LATEST = ("src/sandbox/lobby/hub.html + src/sandbox/lobby/hub_page.py + "
               "src/sandbox/panel.py (member published and startable; "
               "qa/hub-member-R2489.log 1321B legs=2 identical, "
               "qa/hub-member-live-R2489.log LIVE PASS member page 8752B "
               "byte-identical to disk) at 2026-11-06 R2489")

base.NEXT = ("2026-11-07 the debt register owes the full reconcile battery on "
             "this committed tree first (reconcile-battery-R2489, "
             "pre-registered 573 suites / 4414 criteria, because two registry "
             "rows were wired); after green the queue head named by "
             "src/os/queue_head.py --head tech resumes. Every P-47 item beyond "
             "the shipped sandbox faces still waits on CEO physical items "
             "(merchant id, mini-program appid/secret)")

base.RESULT = (
    "2026-11-06 R2489 BUSINESS window on the CEO standing order "
    "OB-20261105-003656-879 (real output only). The claim was R2487's own "
    "disclosed half: the membership page shipped with no way to reach it from "
    "the one door, and its suite was never wired into the runner. Shipped the "
    "hub member face (member/member_note/member_cmd, member_port default 8096, "
    "in build_faces and face_ports, a --member-port flag on server.py and a "
    "seventh card with its live marker in hub.html), added member to the "
    "panel's FACE_MODULES/FACE_IDS so a click starts it, and moved "
    "member_page.py's own --port default off the hub's customary 8095 to 8096 "
    "because the two collided. AC-HMB1..AC-HMB6 were pinned in "
    "src/os/backlog.md BEFORE any code and read SUITE PASS 6/6 twice with "
    "identical verdicts plus three adjacent suites green "
    "(qa/hub-member-R2489.log 1321B); the live leg started the real lobby "
    "server and the real member page and read live[member]=False before, True "
    "after, the published URL serving 8752B byte-identical to member.html, "
    "both ports refusing afterwards. The registry moved 571/4402 -> 573/4414 "
    "by exactly two rows (lobby-hub-member and the previously unregistered "
    "member-face), the matrix was restamped stamp-aligned to 54983B with a "
    "byte-identical --check whose green line honestly reads 571/573, census "
    "read DRIFT-CLEAN flags=0, and reconcile-battery-R2489 was appended "
    "first=no at the pre-registered target. Four neighbouring pinned criteria "
    "were amended openly (two exact face_ports maps and two exact startable "
    "lists each gained the new member without loosening to a subset), and "
    "test_start_all AC-STL6 was replaced with its intent preserved because "
    "'git diff --quiet HEAD' over the hub bytes can only hold on the round "
    "that wrote it. Four new group decisions D-20261106-01..04 were read in "
    "full and judged KNOWLEDGE-ONLY with the baseline widened. Honest: the "
    "panel still starts member on its own port rather than together with the "
    "lobby, the hub still cannot start anything itself, the member page still "
    "uses a throwaway temp world per run, Docker is absent so no containerised "
    "bring-up is claimed, the real 19.9 debit and the real msgSecCheck still "
    "wait on CEO physical items, tasks.md was not touched, and no fold was due "
    "(state 45294B at open against the 78500B waterline)."
)

base.OUTS = (
    "src/sandbox/lobby/hub.html + src/sandbox/lobby/hub_page.py + "
    "src/sandbox/lobby/server.py + src/sandbox/lobby/test_hub_member.py + "
    "src/sandbox/panel.py + src/sandbox/panel.html + "
    "src/sandbox/member/member_page.py + src/sandbox/reconcile_all.py + "
    "qa/hub-member-R2489.log + qa/hub-member-live-R2489.log + "
    "docs/sandbox-suite-matrix.md + state/debt.md + src/os/live_R2489.py + "
    "src/os/closeout_R2489.py + src/os/export_R2489.py + src/os/state.json + "
    "docs/status-export.json + heartbeat.txt + src/os/backlog.md"
)

if __name__ == "__main__":
    print(base.main())