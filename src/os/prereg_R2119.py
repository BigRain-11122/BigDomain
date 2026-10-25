import io

row = ('- [ ] P3 explore 自补种并同窗认领（R2119）：apimarket 买家侧**我的问答全史**读面（api_buyer_questions）——R2118 立起售前问答后，提问方只有逐挂牌线程（api_listing_qna）与卖家侧债务队列（api_seller_questions）两张面：一个在 N 件挂牌上问过问题的住民，要回答「我问过什么、哪些还悬着、卖家回过什么」只能逐件打开并表。本窗补买家侧跨挂牌合并全史（answered 与 open 同列·最旧在前·退役挂牌仍可读·当前元数据标题·买家隔离·诚实空）。**判据 AC-AMBQ1..AC-AMBQ8 预注册于代码之前**（锚 api_buyer_questions / AC-AMBQ / ledger-apimarket-buyerquestions / MY_QUESTIONS_EMPTY 全仓 git grep -F 零占用 rc=1，2026-10-25）：**AC-AMBQ1 形与诚实空**=信封恰八键 {buyer_id,listing_count,question_count,answered_count,unanswered_count,oldest_open_utc,disclaimer,rows}·行恰十键 {question_id,listing_id,listing_key,title,dev_account,question_text,asked_utc,answered,answer_text,answered_utc}·前缀合法零提问账户=全零+空表+oldest None·disclaimer 在信封；**AC-AMBQ2 买家隔离**=只回 buyer_id 本人的提问·他人（卖家账户/另一买家）看不到·卖家账户得的诚实空不是他人行；**AC-AMBQ3 计数与顺序**=rows 全序 (asked_utc,question_id) 升序·question_count==len(rows)·answered_count+unanswered_count==question_count·oldest_open_utc==首个未答行的 asked_utc（全答则 None）·answered 行的 answer_text/answered_utc 非空且与线程面同值；**AC-AMBQ4 跨挂牌合并与当前元数据**=同一买家在两件以上挂牌的提问合并成一条时间线·title 取当前元数据修订值（edit_listing 后即现新标题）·listing_key 与 listing_id 同源；**AC-AMBQ5 退役可读**=挂牌 delist 后其提问与回答仍完整可读（退役不销史）；**AC-AMBQ6 纯读与账户门**=八形坏账户全拒 E_AM_BAD_ACCOUNT·拒绝前后十二表摘要与 ledger_tx 集恒等·零行变更零 token；**AC-AMBQ7 跨重启字节同一**=三实例同世界 rows 与信封 dumps 逐字节同一；**AC-AMBQ8 消费者与接线卫生**=买家块新增 questions 键（读面原样）·HTML 买家段渲染「my questions」表（计数标题+空态文案+敌对文本转义）·旧报表缺键降级诚实空·REPORT_SCHEMA 11→12 加法升级（JSON 仍恰 schema_version/report/attention 三键且既有块值不变）·runner 标签 ledger-apimarket-buyerquestions 已接线·套件源纯 ASCII 零网络库导入。')

p = 'state/queue/explore.md'
t = io.open(p, encoding='utf-8').read().splitlines(True)
io.open(p, 'w', encoding='utf-8', newline='\n').write(row + '\n' + ''.join(t))
print('explore lines now', len(io.open(p, encoding='utf-8').read().splitlines()))

row2 = ('- [ ] P3 explore 队头认领（R2119·自补种同窗）：apimarket 买家侧我的问答全史读面 api_buyer_questions + 买家块 questions 消费与 my-questions 表 + REPORT_SCHEMA 11→12（判据 AC-AMBQ1..AC-AMBQ8 预注册于 state/queue/explore.md 同名行·先于代码；四锚 git grep -F 零占用 rc=1）')
p2 = 'src/os/backlog.md'
t2 = io.open(p2, encoding='utf-8').read()
io.open(p2, 'w', encoding='utf-8', newline='\n').write(row2 + '\n' + t2)
print('backlog head ok')