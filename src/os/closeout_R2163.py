import io, json, re

DEC = r'C:\Users\sjs20\Desktop\FluxGroup\docs\decisions.md'
dtxt = io.open(DEC, encoding='utf-8', errors='replace').read()
live = sorted(set(re.findall(r'\b[DCTPOX][A-Z]?-\d{8}-\d{2,4}\b', dtxt)))
rows = len([ln for ln in dtxt.split('\n') if ln.strip()])

p = 'src/os/state.json'
d = json.load(io.open(p, encoding='utf-8'))
d['tick'] = 2163
d['last_order'] = '2026-10-27 20:22'
d['last_decision_rows'] = rows
d['last_dec_tokens'] = ','.join(live)
d['benchmarks_refreshed'] = '2026-10-27'

NARR = (
    "2026-10-27 R2163 (five-silence scan at open: decisions.md carries "
    "186 content-addressed tokens against the stored 210-token baseline "
    "- six of them are NEW (D-20261027-11..16, all other companies or "
    "fleet tooling: Bigmoney task-health pausing and the E1 disabled-set "
    "source fix, the ledger split, the BigStream write-silence ruling, "
    "the two-company dual audit and the machine-state shared-source "
    "repair), none of which is a BigDomain execution face, so all six are "
    "logged as aware-no-action and the baseline is re-anchored to the "
    "measured 186-token set as a rotation artifact in the same style as "
    "R2160; the ledger's three @BigDomain patrol rows stay paid off with "
    "zero unreplied; the group orders tail carries ONE new row - the "
    "OB-20261027-202256-910 fleet self-check at 20:22, addressed to bm-a/"
    "bm-b/bm-c machines, which is the fleet dispatcher execution face and "
    "not a domain face, so it is logged aware-no-action as well; "
    "benchmarks refreshed 2026-10-27 inside the seven-day gate; tree "
    "clean, no index.lock; the P1 canonical rows stay blocked-on-CEO and "
    "the weekly proposal duty is met by BD-PROP-005, and the four tech "
    "heads stayed gated) - so this window claimed the P3 explore FIFO head, "
    "the R2149 seed row for the per-category refund timeline, and "
    "registered AC-CRM1..AC-CRM8 in the queue row BEFORE the code "
    "(git grep -F against HEAD 2026-10-27: test_apimarket_"
    "categoryrefundmonths, ledger-apimarket-categoryrefundmonths, "
    "refund_rate and worst_refund_month all at zero occupancy rc=1, with "
    "the AC-CRM and face-name text occupancy coming only from the seed row "
    "itself). Gap statement: the category demand face sums a category over "
    "its whole life, the market months face sums the whole market per "
    "month and the refund register lists refunds one by one - none of them "
    "answers whether THIS category's refund load is abnormal THIS month, "
    "which is the question a seller asks before committing to a line of "
    "business and the operator asks before repricing. Product: "
    "APIMarketFace.api_category_refund_months(include_uncategorized=True) "
    "- a fourteen-key envelope, eight-key category rows and six-key month "
    "rows. The bucketing law is cash basis: a sale books in the UTC month "
    "of its purchased_utc and a refund in the UTC month of its "
    "refunded_utc, so a refund landing later never rewrites the month its "
    "sale landed in (the AUG row stays byte-frozen after an OCT refund); "
    "refund authority is the refund register joined to its purchase, so a "
    "refund-only month reports a positive refund amount and a negative net "
    "next to a zero gross instead of inventing a sale, and refund_rate is "
    "None rather than a fake zero wherever nothing settled; category "
    "ownership rides the one effective-category seam (_category_state), so "
    "revise_category moves gross and refunded in one step and a revert "
    "restores byte-identically; the two extremes are deliberately "
    "dissociated - worst_refund_month takes the highest rate among months "
    "that actually settled something (ties to the earliest month) while "
    "top_refund_month takes the largest refunded amount over all months, "
    "so the NOV refund-only month at 17 tokens outranks OCT at 15 while "
    "the worst rate belongs to OCT at 15/9; months order ascending, "
    "categories ascend with the honest uncategorized bucket last, and "
    "include_uncategorized is bool-only with fail-closed E_AM_BAD_ARGS "
    "before any read (eight bad forms proven). Pure read: zero row "
    "mutations, zero token movement, repeated calls byte-identical. "
    "Evidence: suite SUITE PASS 8/8 double-run rc=0/0 with byte-identical "
    "evidence files sha16 fa87745a78b8dc7c (qa/apimarket-"
    "categoryrefundmonths-R2163-a.log / -b.log, 866 bytes each, house "
    "single writer, utf-8 LF), wired as ledger-apimarket-"
    "categoryrefundmonths(8); four adjacent apimarket suites green "
    "(categorydemand 8/8, marketmonths 8/8, refundregister 13/13, "
    "repeatpurchase 8/8). Honest notes: (a) the first full battery of this "
    "window read RUNNER FAIL 362/365 with all three reds being the os "
    "ledger live gates (AC-LGB8, AC-LGR8, AC-LGN8), and the root cause was "
    "the PREVIOUS window's own bookkeeping: the R2162 tokens line had been "
    "written as '2026-10-27 R2162 tokens:' with a date prefix, so the "
    "round-ledger regex never recognised it and R2162 counted as a round "
    "without a ledger line - the remedy was to repair that line's prefix "
    "(the text and the figures are unchanged) rather than to add a "
    "baseline exemption that would have hidden the defect, after which all "
    "three suites re-read SUITE PASS 8/8; (b) AC-CRM2 first asserted a "
    "trade_count on the month rows, but the pre-registered month contract "
    "has six keys and no trade_count, so the criterion was re-expressed "
    "through gross==0 plus a positive refund amount instead of widening "
    "the contract after the fact; (c) the seed first let one buyer purchase "
    "the same listing twice, which E_AM_PURCHASE_DUP correctly refused, so "
    "the October tools sale moved to a dedicated buyer with the money "
    "structure unchanged; (d) the battery re-run on the committed tree and "
    "its truthful matrix regeneration are recorded in the closing line "
    "below."
)
TOK = ("R2163 tokens: local=~90k api=0 api_reason=five-silence scan + "
       "refund-months product change + suite 8/8 double-run + four "
       "adjacent regressions + full battery 362/365 diagnosis + previous-"
       "window ledger-line repair + three os gate suites re-run + "
       "state/export closeout, zero cloud calls")
d['log'].append(NARR)
d['log'].append(TOK)
io.open(p, 'w', encoding='utf-8', newline='\n').write(
    json.dumps(d, ensure_ascii=False, indent=2) + '\n')
print('tick', d['tick'], 'rows', rows, 'tokens', len(live))