"""Append BD-PROP-007 (week 11-08~11-14 quota) to the shared proposal face.

The proposal track owes at least one entry per week window; the last entry is
BD-PROP-006 dated 2026-11-02 (window 11-01~11-07), so this window's quota was
unmet. The text is Chinese data and therefore belongs in the md face, not in
this ASCII script.
"""

import io

PATH = "docs/proposals.md"
MARKER = "BD-PROP-007"

TEXT = u"""

### BD-PROP-007 电池腿的接棒账（2026-11-11，窗 11-08~11-14，状态 open，试点窗 11-11~11-25）

- 现象：全量电池单腿实测 3500~4100s，而单窗预算 25 分钟——凡动过产品字节的窗都欠一条电池，而这条电池永远跑不完，于是形成慢性滞后一窗的接棒链：R2607 发射后在收轮时披露「仍在跑」、债行留开；R2621 把 reconcile-battery-R2621 登记为 first=yes 交给下一窗；R2622（本轮）发射 pid 59736 后同样只能交棒。欠账闸只记「欠这条电池」和预注册目标（642 套件/4828 判据），不记这条腿的起点——接棒窗无法从闸上分辨「有人正在跑、waiting」还是「没人跑、白欠」，最坏情况是连续几窗各自发射一条腿、彼此踩写同一个证据文件。
- 建议：给 debt 行的 note 增加三个只读事实字段——腿的 round 号、发射时的 pid、以及 qa/ 证据文件的绝对路径（由发射器写入，收轮窗读回校验），并在 debt_gate 的 CLAIM-FIRST 输出里原样回显；接棒窗的第一动作改为「读回该 pid 与证据文件：活着=改走等腿、死了且有证据=清账、死了且无证据=重发」。不加新闸、不加时钟、不动拦截面。
- 判据（先立 3 问）：① 发射后立刻读闸，输出必须含 pid 与证据路径且与 logs/ 下的 pid 文件逐字一致？② 手工杀掉该 pid 后读闸，必须能判出「腿死且证据未生成」（而非仍报 waiting），且判读耗时 ≤2s？③ 全链只读——跑完 `git status --short` 除 state/export 外为空？
- 收口锚：①②③ 全过=转正（并入 debt_gate 输出）；①不过=撤回（回显面不可靠则接棒律无从谈起）；②过③不过=回炉（去掉任何写面）。
"""


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    if MARKER in text:
        print("E_ALREADY_PRESENT %s" % MARKER)
        return 2
    if not text.endswith("\n"):
        text += "\n"
    text += TEXT
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("APPENDED bytes=%d -> %d" % (len(raw), len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
