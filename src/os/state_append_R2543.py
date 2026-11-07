import io
import json

STATE = 'src/os/state.json'

NEW_TOKENS = ["D-20261108-01", "D-20261108-02", "D-20261108-03",
              "D-20261108-04", "D-20261108-05", "D-20261108-06"]

LINES = [
    "2026-11-08 R2543 PRODUCT window on the tech head the register named "
    "(product-face-R2542, state/queue/tech.md:579 prefix AC-PNCF1 "
    "probe_seam_name_binding_control_flow_scope, criteria AC-PNCF1..AC-PNCF6 "
    "pinned in that row at R2541 BEFORE any code). Five-silence scan at open: "
    "git status EMPTY at HEAD 3ae0d426 with no index.lock, zero @BigDomain rows "
    "in cph4/evolution-ledger.md, the content-addressed decisions diff read SIX "
    "new tokens (D-20261108-01..06) over the stored 176-token baseline at a "
    "measured 344 rows, the group orders tail moved to 2026-11-08 00:04 "
    "(OB-20261108-000400-425, a lane-batch dispatch to @bm-m and the BigCompute "
    "lanes) so it is recorded as knowledge-only with its number, benchmarks "
    "2026-11-03 inside the seven-day gate. Debt gate read CLAIM-FIRST "
    "item=product-face-R2542 first=1 with no battery owed, queue_head named "
    "tech line 579 claimable=11 with the floor MET at 5/5 10/10 10/10, and all "
    "five pinned anchors were re-checked at zero occupancy at HEAD before any "
    "code (every hit was a seed row, a bookkeeping writer or state/debt prose).",
    "2026-11-08 R2543 SHIPPED src/os/probe_seam_name_binding_control_flow_scope.py "
    "plus its six-criteria suite. MEASURED at R2541 on the shipped position "
    "face own readers and re-measured here before shipping: a binding inside "
    "`if False:` still resolved, a `with ... as KEY` binding read unbound "
    "because it was never collected, and a try/except binding one name twice "
    "read a single ambiguity word. The face resolves a NAME step ONLY when its "
    "binding is PROVED to run before the loop: a binding behind a branch is "
    "NAMED guarded:if:<line> and never resolved while an unconditional binding "
    "still wins even when a later branch rebinds the name; a with-as binding is "
    "NAMED with-as; two EXCLUSIVE arms of one if binding two different "
    "literals publish BOTH arms by name instead of one ambiguity word; and a "
    "binding inside a loop body, a try arm or a handler is NAMED with its own "
    "guard. The shipped position face is asked FIRST so every answer it already "
    "gave keeps its answer, the seam classifier is still the shipped registry "
    "single `quiets`, and every row carries the shipped answer beside this face "
    "own.",
    "2026-11-08 R2543 PROOF measured, not quoted: AC-PNCF1..AC-PNCF6 SUITE PASS "
    "6/6 TWICE with identical output plus five adjacent probe suites green "
    "(position, scope awareness, local constant, registry, dynamic import) "
    "(qa/probe-seam-name-binding-control-flow-scope-R2543.log, 11053B, legs=2 "
    "identical=True fails=0 adjacent=5, landed through the shipped capture "
    "callable). A live leg on the REAL tree reads SEAMS-CONTROL-FLOW-COVERED "
    "over 1481 probes (3 covered, 181 out-of-scope, 1297 historical, "
    "missing=0, unreadable=0) with the covered probes publishing 9 own "
    "control-flow loop rows, written by one UTF-8 LF writer rather than a shell "
    "redirection (qa/probe-seam-name-binding-control-flow-scope-live-R2543.log). "
    "On the SAME fixtures the shipped position face reads the guarded binding "
    "as resolved 'b' and the arms fixture as one 'ambiguous' word, so the "
    "closed gap is measured on BOTH readers, which the suite asserts.",
    "2026-11-08 R2543 REGISTRY, MATRIX, BOARD AND DEBT: one runner row "
    "os-probe-seam-name-binding-control-flow-scope(6), so the registry reads "
    "601 suites / 4582 criteria, recounted by importing reconcile_all.SUITES "
    "rather than trusted. docs/sandbox-suite-matrix.md was regenerated "
    "stamp-aligned from the eligible battery leg qa/reconcile-all-R2542-leg3.log "
    "to 58105 bytes at 601/4582 with its green line honestly reading 600/601, "
    "and --check then read byte-identical. The claimed row 579 was closed "
    "through src/os/queue_close_R2543.py at its predicted and measured 1738378B "
    "and ONE row was seeded from this window own MEASURED limit (same-value "
    "arms refuse as guarded, two separate if statements read as one guard word, "
    "a nested binding publishes only the innermost guard) as AC-PNCG1..AC-PNCG6; "
    "queue_floor then read FLOOR-MET 5/5 11/10 10/10 with the new head at line "
    "581. DEBT through the shipped writers: product-face-R2542 closed (line "
    "278, open 19->18, done 241->242, 168141B -> 168144B, readback ok), "
    "reconcile-battery-R2543 appended first=yes at the pre-registered 601/4582 "
    "(168144B -> 168425B) and product-face-R2543 appended first=no naming tech "
    "line 581 AC-PNCG1 (168425B -> 168693B), both readback ok; the gate now "
    "names that battery first. The round was declared through the shipped batch "
    "writer at its predicted 304 -> 305 entries / 83775B -> 84151B until R2553 "
    "and residue_triage --check then read R2543 TRIAGED.",
    "2026-11-08 R2543 DECISIONS (content-addressed, six new tokens; canon read "
    "from the group file at 344 rows): D-20261108-01 (the 49-decision intake "
    "batch with the group silence-lift ruling), D-20261108-02 (quant lane host "
    "consolidation to bm-b), D-20261108-03 (two overdue BigCompute/quant "
    "commitments dispatched), D-20261108-04, D-20261108-05 (BigCompute M155 "
    "acceptance signature missing exec files 135/148), D-20261108-06 (a fleet "
    "push blocked ahead 78 / behind 5). Every one names another lane, another "
    "company or the group registry, and none opens a BigDomain execution face, "
    "so ALL SIX are ACKNOWLEDGED (no action, no dissent) with their numbers "
    "recorded here as the delivery law requires; the baseline was advanced by "
    "union and last_decision_rows set to the measured 344. The group orders tail "
    "OB-20261108-000400-425 is likewise knowledge-only.",
    "2026-11-08 R2543 honest disclosures: (a) TWO product points on the Executive "
    "Protocol scale - a runnable CLI with its own suite and a live reading a "
    "maintainer can run - but nothing a CEO could newly open and no P-47 "
    "business surface moved; (b) the defect was MEASURED at R2541 in that "
    "window own legs and re-measured here before shipping, so this is a repair "
    "of a disclosed gap rather than a new discovery; (c) DISCLOSED LIMITS "
    "measured this window rather than assumed and seeded as the next tech row: "
    "two arms binding the SAME literal still refuse as guarded although both "
    "agree, two SEPARATE if statements binding one name to two values read as "
    "one guard word, and a nested binding publishes only the innermost guard "
    "while the outer guard on the same path is dropped; (d) my first edit of "
    "this module carried a helper that imported a module that does not exist and "
    "it was removed before the first run, reported rather than quietly dropped; "
    "(e) the residue batch writer REFUSED my first invocation with --execute "
    "because that flag is not part of its interface, and the append was landed "
    "by its documented default action instead, which is a usage defect of mine "
    "and not a loosened law; (f) queue_row --check still reads VIOLATIONS on "
    "state/queue/tech.md:524, :537, :586 and explore.md:295, all of them rows "
    "that pre-date this window and none of them opened here - this window "
    "declined to mass-edit them and says so; (g) MEASURED DEFECT STILL OPEN "
    "from R2522: the shipped state_fold layout reader no longer matches this "
    "state file, so this append rewrites only the fields it owns and the fold "
    "remains owed; (h) Docker is absent on this host so no containerised "
    "bring-up of the sandbox faces is claimed; (i) the real 19.9 debit and the "
    "real msgSecCheck still wait on CEO physical items (merchant id, "
    "mini-program appid/secret); (j) tasks.md was not touched, it is the P-47 "
    "canonical board; (k) the S4U lane re-registration still needs an ELEVATED "
    "shell and remains a ceo-pending physical item with zero chase.",
    "R2543 tokens: local=~15k api=0 api_reason=product window - five-silence "
    "scan, one content-addressed decisions scan reading six new group tokens all "
    "acknowledged, one group orders tail read judged knowledge-only, one "
    "zero-occupancy anchor check on five anchors, one pre-registered face "
    "shipped with its six criteria proved on BOTH readers, one suite proved "
    "twice through the shipped capture callable plus five adjacent suites, one "
    "live leg on the real tree with a single UTF-8 LF writer, three limits "
    "measured and seeded as the next row, one registry row recounted by import, "
    "one stamp-aligned matrix regeneration checked byte-identical, one board row "
    "closed and one seeded through their shipped writers, three debt rows moved "
    "and one residue declaration appended through their shipped writers, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero external "
    "API touches",
]

text = io.open(STATE, encoding='utf-8').read()
marker = '\n  ]\n}'
index = text.rindex(marker)
block = "".join(',\n    ' + json.dumps(line, ensure_ascii=False)
                for line in LINES)
text = text[:index] + block + text[index:]
io.open(STATE, 'w', encoding='utf-8', newline='\n').write(text)

state = json.load(io.open(STATE, encoding='utf-8'))
state['tick'] = 2543
state['last_order'] = '2026-11-08 00:04'
state['last_decision_rows'] = 344
known = list(state.get('last_dec_tokens', []))
for token in NEW_TOKENS:
    if token not in known:
        known.append(token)
state['last_dec_tokens'] = known
payload = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
io.open(STATE, 'w', encoding='utf-8', newline='\n').write(payload)

back = json.load(io.open(STATE, encoding='utf-8'))
print('tick', back['tick'], 'log', len(back['log']),
      'tokens', len(back['last_dec_tokens']),
      'rows', back['last_decision_rows'],
      'order', back['last_order'])