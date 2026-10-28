import io

P = "src/os/backlog.md"
ROW = ("- [x] 清欠账认领（R2195·非新面·R2193/R2194 两连挂账）：**全量电池 + 套件矩阵再生成**"
       "——两轮诚实注原文分别为「the full reconcile battery and the suite-matrix regeneration were NOT run ... "
       "recorded as R2194 first-item debt」与「first item of R2195 (second consecutive carry)」，故本轮不改产品代码"
       "（电池走树时改 apimarket.py 会让套件读到混树=R2168 先例），只把缺口结清：电池 RUNNER PASS **392/392 套件 + 控制 7/7** "
       "896.9s（qa/reconcile-all-R2195.log·731240B·单写者 utf-8 LF 经 src/os/battery_stream.py，绝无 shell 重定向），"
       "同一电池窗出生站清扫 874/874 世界、309.57 MiB、busy=0 failed=0；电池后四段全部 PASS 并由同一单写者追加进同一证据件——"
       "矩阵重生成 **392 套件 / 3258 判据** 并回读逐字节同一（docs/sandbox-suite-matrix.md 38021B·green=392/392）、"
       "指纹链五域 CLEAN（src/sandbox/migration_chains.json）、runner profile --daily --check PASS、"
       "qa writer census DRIFT-CLEAN files=2042 tee=1514 baselined=528 disappeared=0 flags=0。"
       "另：当日 reconcile-daily 证据 qa/reconcile-daily-20261028.log 在盘（profile/fingerprint/census 三段 PASS）。"
       "诚实注=①本轮产品分 0（零产品代码改动，只买回验证欠账）；②首跑 follow-up 点错两个 helper 名"
       "（fingerprint_chain.py / reconcile_daily.py --profile）即失败零写，改用真名指纹与 profile 两件；"
       "③日志门 LEDGER OK 2195、export 一致性 21/21 PASS、state eol bare_lf 0（indent_ok=false 为 HEAD 既有形态非本轮引入）。"
       "[done 2026-10-28 R2195]")

lines = io.open(P, encoding="utf-8").read().split("\n")
for i, line in enumerate(lines):
    if line.startswith("# BigDomain"):
        lines.insert(i + 1, ROW)
        break
for i, line in enumerate(lines):
    if line.startswith("- [ ] R2179"):
        lines[i] = line.replace("- [ ] R2179", "- [x] R2179", 1) + \
            " [done 2026-10-28 R2195·由本轮电池结清]"
        break
io.open(P, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("ok")