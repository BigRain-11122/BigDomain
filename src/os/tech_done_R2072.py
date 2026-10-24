# -*- coding: utf-8 -*-
"""R2072 closeout: mark the evidence-dialect tech row done."""
import io

PATH = "state/queue/tech.md"
OLD = "零网络 import 行+shipped 配置零改动〕"
NEW = OLD + (
    "——[done 2026-10-24 R2072]（交付=src/os/evidence_writer.py 单写者"
    "〔normalize_lf/_payload 编码先于触盘+同目录临时件 os.replace 原子替换"
    "+写后 classify_file 断言 tee 否则 EvidenceDialectError+check_file 只读"
    "/fix_file 仅换行轴归一且非 utf-8 fail-closed 拒改+CLI --check 退出码"
    " 0/2/3 与 --fix 打印 post class〕+src/os/test_evidence_writer.py 套件"
    " 8/8 双跑 sha16 d39cf3aa81ac525120cd548859250b1d7a2c56937c9ded3d7321478d798659c5"
    "+src/os/evidence_census_R2072.py 普查读数件：qa/ 1660 件只读普查"
    "〔指纹 name/size/mtime_ns 前后逐位不变=PASS〕tee=1134 cmd-raw=15"
    " pwsh-capture=313 ps-utf16=98 other=100，证据"
    "=qa/evidence-writer-census-R2072.log 自写自检 class=tee"
    "+接线=reconcile_all SUITES os-evidence-writer(8)→RUNNER PASS 280/280"
    " suites+controls 7/7 222.4s=qa/reconcile-all-R2072.log〔本件经新工具"
    "自检 class=tee crlf=0〕+suite-matrix 280/2347 --check byte-identical"
    "·诚实边界=funnel CLI 既有 newline 显式 LF 已合规故零改动；shell 重定向"
    "捕获副本（cmd-raw/pwsh-capture 328 件历史）在代码控制面外，本窗交付"
    "检出+修复工具而非批量改写历史件）")

text = io.open(PATH, encoding="utf-8", newline="").read()
assert text.count(OLD) == 1, "anchor count %d" % text.count(OLD)
io.open(PATH, "w", encoding="utf-8", newline="").write(
    text.replace(OLD, NEW, 1))
print("tech row done note appended")