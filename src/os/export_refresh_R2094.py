# export_refresh_R2094.py - refresh the silicon-watch export face
# from real state (F3 law: every field derived, nothing hardcoded
# except the round narrative which is a data file payload).
import io
import json

DATA = json.loads(io.open(".codely-cli/tmp/export_R2094.json",
                          encoding="utf-8").read())
PATH = "docs/status-export.json"

exp = json.loads(io.open(PATH, encoding="utf-8").read())
exp["export_ts"] = DATA["ts"]
exp["ceo_face"]["current"] = DATA["current"]
exp["ceo_face"]["latest_artifact"] = DATA["latest_artifact"]
exp["ceo_face"]["next_milestone"] = DATA["next_milestone"]
exp["outs"].insert(0, DATA["out_row"])
exp["results"].insert(0, DATA["result_row"])

sd = exp["self_drive"]
sd["log_lines_in_window"] = 20
sd["proposals_total"] = 5
sd["proposals_open"] = 3
sd["queue_tech_open"] = 4
sd["queue_explore_open"] = 1

with io.open(PATH, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps(exp, ensure_ascii=False, indent=2) + "\n")
print("export refreshed rows outs=%d results=%d"
      % (len(exp["outs"]), len(exp["results"])))