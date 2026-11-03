"""R2429 fold record: append the waterline fold line to the state log, then
re-derive the CEO-visible export from the changed state."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
STATE = os.path.join(SRC, "state.json")

LINE = (
    "2026-11-04 R2429 waterline fold, measured not assumed: the closeout left "
    "state.json at 83060B against the 78500B gate (margin -4560B), so fold 641 "
    "moved log items 1..100 verbatim into the monthly archive at a TRUE "
    "round-block boundary - planned first through src/os/state_fold.plan_fold "
    "with the token family asked of the module own PAT rather than a second "
    "regex (167 tokens, tokens_missing empty, round_split None), then executed "
    "through the same callable at its predicted 11149B post size; --check now "
    "reads FOLD-CLEAR margin 67351B over 10 log lines. The fold then created "
    "the residue the law predicts - 7 rounds whose blocks moved read untriaged "
    "- and all seven (R2417/R2418/R2420/R2422/R2424/R2426/R2428) were spliced "
    "in ONE atomic batch through the shipped residue_triage_append_batch at "
    "their measured DELIVERED status, by R2429, until R2460, after which "
    "residue_triage --check reads declaration=PINNED residue=270 triaged=270 "
    "untriaged=0 verdict=TRIAGED."
)


def main():
    sys.path.insert(0, SRC)
    import state_io
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.loads(handle.read())
    before = len(state["log"])
    state["log"].append(LINE)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = STATE + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, STATE)
    back = json.loads(io.open(STATE, "r", encoding="utf-8").read())
    if len(back["log"]) != before + 1 or back["log"][-1] != LINE:
        raise SystemExit("E_FOLDREC_READBACK")
    print("state lines=%d bytes=%d" % (len(back["log"]),
                                       os.path.getsize(STATE)))
    import closeout_R2429
    closeout_R2429.step_export()


if __name__ == "__main__":
    main()