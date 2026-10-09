<!-- 机器派生文件：由 src/sandbox/suite_matrix.py 生成，勿手改（改=下轮 --check 漂移 exit 2）。再生命令见文档头「生成命令」行 -->
# 沙箱套件矩阵（对账可计费可见面）

- 生成时间: generated: 2026-10-10 05:32 +08:00
- 生成命令: python src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R1712.log
- 状态证据: reconcile-all-R1712.log (RUNNER PASS 48/48 suites green, reconcile controls 6/6, 101.9s)
- 回应: C-20261009-02「实质停摆零可计费」批评——本矩阵为机器派生的对账可计费可见面：套件注册表源自 reconcile_all.py 单一事实源，可计费面源自五域 config.json 单一事实源，逐套件状态源自最近全量回归证据 log，零手写数字。

## 汇总

| 套件数 | 判据总数 | 证据全绿 | 证据轮 |
|---|---|---|---|
| 48 | 517 | 48/48 | R1712 |

## 五域可计费/配置面（config.json 单一事实源）

| 域 | 面 | 计数 | 键名 |
|---|---|---|---|
| ledger | 可计费动作面（actions） | 6 | login, invite, active_day, cocreate, brain_hole, chat_mining |
| ledger | 分成比例面（share_ratios） | 4 | cocreate_share_pct, observation_share_pct, iaa_share_pct, note |
| ledger | 代币参数面（token） | 5 | code, official_name, ai_label_text, disclaimer, disclaimer_persistent |
| lobby | 房间面（rooms） | 3 | lobby, quant, cocreate |
| lobby | 限流面（rate_limit） | 4 | max_messages, window_seconds, mute_trigger_violations, mute_seconds |
| lobby | 幂等闸面（idempotency） | 2 | ttl_seconds, max_keys |
| member | 会员档位面（tiers·可计费） | 4 | experience, patron, mayor, cocreator |
| member | 会员商品面（products·可计费） | 4 | tier:experience, tier:patron, tier:mayor, tier:cocreator |
| member | 权益券面（vouchers） | 1 | building_naming |
| member | 提醒参数面（reminder） | 9 | channel, note, remind_days_before, remind_days_before_status, daily_send_cap_default, daily_send_cap_paid, daily_send_cap_note, reason_templates, templates |
| pay | 商品 SKU 面（products·可计费） | 4 | pack_compute_19_9, birthright_entry, report_data_b, share_observation |
| pay | 支付渠道面（channels） | 2 | virtual, standard |
| pay | 合规面（compliance） | 3 | disclaimer, disclaimer_persistent, note |
| ugc | 内容来源面（sources） | 4 | enum, enabled, entrance_required, note |
| ugc | 审核流面（approval） | 3 | threshold_len, landfall_keywords, note |
| ugc | 导出面（export） | 2 | dir, note |

## 套件×判据×状态矩阵

| # | 套件 | 路径 | 判据数 | 状态 | 证据耗时(s) |
|---|---|---|---|---|---|
| 1 | lobby | lobby/test_client.py | 16 | green | 22.3 |
| 2 | ledger | ledger/test_ledger.py | 11 | green | 0.5 |
| 3 | ledger-props | ledger/test_props.py | 7 | green | 0.2 |
| 4 | ledger-incentive | ledger/test_incentive.py | 7 | green | 0.2 |
| 5 | ledger-settlement | ledger/test_settlement.py | 7 | green | 0.1 |
| 6 | ledger-venue | ledger/test_venue.py | 7 | green | 0.2 |
| 7 | ledger-collectibles | ledger/test_collectibles.py | 7 | green | 0.2 |
| 8 | ledger-expedite | ledger/test_expedite.py | 7 | green | 0.3 |
| 9 | ledger-ads | ledger/test_ads.py | 7 | green | 0.2 |
| 10 | ledger-observation | ledger/test_observation.py | 7 | green | 0.2 |
| 11 | ledger-identity | ledger/test_identity.py | 7 | green | 0.2 |
| 12 | ledger-studio | ledger/test_studio.py | 7 | green | 0.2 |
| 13 | ledger-metered | ledger/test_metered.py | 7 | green | 0.2 |
| 14 | ledger-reports | ledger/test_reports.py | 7 | green | 0.2 |
| 15 | ledger-effects | ledger/test_effects.py | 7 | green | 0.2 |
| 16 | ledger-growth-archive | ledger/test_growth_archive.py | 7 | green | 0.2 |
| 17 | ledger-companion | ledger/test_companion.py | 7 | green | 0.2 |
| 18 | ledger-tmarket | ledger/test_tmarket.py | 7 | green | 0.2 |
| 19 | ledger-festival | ledger/test_festival.py | 7 | green | 0.2 |
| 20 | ledger-showroom | ledger/test_showroom.py | 7 | green | 0.3 |
| 21 | ledger-sistercity | ledger/test_sistercity.py | 7 | green | 0.3 |
| 22 | ledger-apidev | ledger/test_apidev.py | 7 | green | 0.2 |
| 23 | ledger-apidev-lifecycle | ledger/test_apidev_lifecycle.py | 8 | green | 0.3 |
| 24 | ledger-apidev-rate | ledger/test_apidev_rate.py | 7 | green | 0.5 |
| 25 | tourstate | tourstate/test_tourstate.py | 7 | green | 0.1 |
| 26 | ugc | ugc/test_ugc.py | 37 | green | 4.4 |
| 27 | ugc-sec-batch | ugc/test_sec_batch.py | 7 | green | 0.2 |
| 28 | pay | pay/test_pay.py | 16 | green | 2.0 |
| 29 | pay-v3 | pay/test_pay_v3.py | 14 | green | 0.4 |
| 30 | pay-v3-real | pay/test_pay_v3_real.py | 9 | green | 0.6 |
| 31 | pay-v3-window | pay/test_pay_v3_window.py | 6 | green | 0.5 |
| 32 | pay-notify | pay/test_pay_notify.py | 7 | green | 0.4 |
| 33 | member | member/test_member.py | 16 | green | 1.6 |
| 34 | member-entry | member/test_entry_tier.py | 7 | green | 0.1 |
| 35 | watermark | watermark/test_watermark.py | 5 | green | 1.6 |
| 36 | watermark-robust | watermark/test_watermark_robust.py | 6 | green | 2.0 |
| 37 | watermark-sweep | watermark/test_watermark_sweep.py | 6 | green | 24.4 |
| 38 | watermark-scale-recover | watermark/test_scale_recover.py | 7 | green | 8.9 |
| 39 | dual-track | watermark/test_dual_track.py | 7 | green | 1.3 |
| 40 | opsreview | opsreview/test_opsreview.py | 7 | green | 1.0 |
| 41 | liveroom | liveroom/test_liveroom.py | 10 | green | 0.3 |
| 42 | benchgate | benchgate/test_bench_gate.py | 11 | green | 0.2 |
| 43 | citymodel | citymodel/test_scenario.py | 10 | green | 0.3 |
| 44 | compliance | compliance/test_sku_compliance_map.py | 15 | green | 0.1 |
| 45 | minors | minors/test_minors.py | 19 | green | 0.1 |
| 46 | minors-wiring | minors/test_wiring.py | 70 | green | 16.0 |
| 47 | schema-migrate | test_schema_migrate.py | 21 | green | 5.6 |
| 48 | suite-matrix-discovery | test_suite_matrix.py | 15 | green | 0.8 |
|  | 合计 |  | 517 | green 48 / FAIL 0 / no-evidence 0 |  |

## 证据出处

- reconcile-all-R1712.log (qa/reconcile-all-R1712.log)
- 状态列解析自上述证据 log 的 suite 行（exit 码）与 RUNNER 终态行；证据中缺失的套件记 no-evidence（不捏造）。判据数为预注册口径，源自套件注册表。
