<!-- 机器派生文件：由 src/sandbox/suite_matrix.py 生成，勿手改（改=下轮 --check 漂移 exit 2）。再生命令见文档头「生成命令」行 -->
# 沙箱套件矩阵（对账可计费可见面）

- 生成时间: generated: 2026-10-11 05:47 +08:00
- 生成命令: python src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R1774.log
- 状态证据: reconcile-all-R1774.log (RUNNER PASS 76/76 suites green, reconcile controls 7/7, 202.4s)
- 回应: C-20261009-02「实质停摆零可计费」批评——本矩阵为机器派生的对账可计费可见面：套件注册表源自 reconcile_all.py 单一事实源，可计费面源自五域 config.json 单一事实源，逐套件状态源自最近全量回归证据 log，零手写数字。

## 汇总

| 套件数 | 判据总数 | 证据全绿 | 证据轮 |
|---|---|---|---|
| 76 | 764 | 76/76 | R1774 |

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
| 1 | lobby | lobby/test_client.py | 18 | green | 23.0 |
| 2 | ledger | ledger/test_ledger.py | 11 | green | 0.7 |
| 3 | ledger-props | ledger/test_props.py | 7 | green | 0.3 |
| 4 | ledger-incentive | ledger/test_incentive.py | 7 | green | 0.3 |
| 5 | ledger-settlement | ledger/test_settlement.py | 7 | green | 0.1 |
| 6 | ledger-venue | ledger/test_venue.py | 7 | green | 0.3 |
| 7 | ledger-collectibles | ledger/test_collectibles.py | 7 | green | 0.4 |
| 8 | ledger-expedite | ledger/test_expedite.py | 7 | green | 0.3 |
| 9 | ledger-ads | ledger/test_ads.py | 7 | green | 0.3 |
| 10 | ledger-observation | ledger/test_observation.py | 7 | green | 0.3 |
| 11 | ledger-identity | ledger/test_identity.py | 7 | green | 0.4 |
| 12 | ledger-studio | ledger/test_studio.py | 7 | green | 0.2 |
| 13 | ledger-metered | ledger/test_metered.py | 7 | green | 0.3 |
| 14 | ledger-reports | ledger/test_reports.py | 7 | green | 0.3 |
| 15 | ledger-effects | ledger/test_effects.py | 7 | green | 0.3 |
| 16 | ledger-growth-archive | ledger/test_growth_archive.py | 7 | green | 0.3 |
| 17 | ledger-companion | ledger/test_companion.py | 7 | green | 0.3 |
| 18 | ledger-tmarket | ledger/test_tmarket.py | 7 | green | 0.3 |
| 19 | ledger-festival | ledger/test_festival.py | 7 | green | 0.3 |
| 20 | ledger-showroom | ledger/test_showroom.py | 7 | green | 0.3 |
| 21 | ledger-sistercity | ledger/test_sistercity.py | 7 | green | 0.3 |
| 22 | ledger-apidev | ledger/test_apidev.py | 7 | green | 0.3 |
| 23 | ledger-apidev-lifecycle | ledger/test_apidev_lifecycle.py | 8 | green | 0.3 |
| 24 | ledger-apidev-rate | ledger/test_apidev_rate.py | 7 | green | 0.4 |
| 25 | ledger-apidev-reject | ledger/test_apidev_reject.py | 7 | green | 0.4 |
| 26 | ledger-apidev-usagelog | ledger/test_apidev_usagelog.py | 7 | green | 0.4 |
| 27 | ledger-apidev-rejectwin | ledger/test_apidev_rejectwin.py | 7 | green | 0.5 |
| 28 | ledger-apidev-usagewin | ledger/test_apidev_usagewin.py | 8 | green | 0.4 |
| 29 | ledger-apidev-usagekind | ledger/test_apidev_usagekind.py | 8 | green | 0.4 |
| 30 | tourstate | tourstate/test_tourstate.py | 7 | green | 0.1 |
| 31 | ugc | ugc/test_ugc.py | 37 | green | 5.2 |
| 32 | ugc-sec-batch | ugc/test_sec_batch.py | 7 | green | 0.3 |
| 33 | pay | pay/test_pay.py | 16 | green | 2.7 |
| 34 | pay-v3 | pay/test_pay_v3.py | 14 | green | 0.5 |
| 35 | pay-v3-real | pay/test_pay_v3_real.py | 9 | green | 0.7 |
| 36 | pay-v3-window | pay/test_pay_v3_window.py | 6 | green | 0.7 |
| 37 | pay-notify | pay/test_pay_notify.py | 7 | green | 0.6 |
| 38 | pay-notify-wiring | pay/test_pay_notify_wiring.py | 7 | green | 1.7 |
| 39 | pay-authorize | pay/test_authorize.py | 7 | green | 0.7 |
| 40 | pay-notify-revoke | pay/test_notify_revoke.py | 7 | green | 5.8 |
| 41 | pay-revoke-reconcile | pay/test_pay_revoke_recon.py | 7 | green | 1.3 |
| 42 | ledger-clawback | pay/test_clawback_wiring.py | 8 | green | 2.0 |
| 43 | member | member/test_member.py | 16 | green | 2.1 |
| 44 | member-entry | member/test_entry_tier.py | 7 | green | 0.1 |
| 45 | member-refund-recovery | member/test_refund_recovery.py | 7 | green | 1.4 |
| 46 | member-expiring | member/test_expiring_soon.py | 7 | green | 1.5 |
| 47 | watermark | watermark/test_watermark.py | 5 | green | 1.9 |
| 48 | watermark-robust | watermark/test_watermark_robust.py | 6 | green | 3.7 |
| 49 | watermark-sweep | watermark/test_watermark_sweep.py | 6 | green | 36.7 |
| 50 | watermark-scale-recover | watermark/test_scale_recover.py | 7 | green | 11.4 |
| 51 | watermark-scale-unknown | watermark/test_scale_unknown.py | 6 | green | 18.7 |
| 52 | watermark-scale-refine | watermark/test_scale_refine.py | 6 | green | 23.1 |
| 53 | dual-track | watermark/test_dual_track.py | 7 | green | 2.0 |
| 54 | opsreview | opsreview/test_opsreview.py | 7 | green | 1.5 |
| 55 | liveroom | liveroom/test_liveroom.py | 10 | green | 0.4 |
| 56 | benchgate | benchgate/test_bench_gate.py | 11 | green | 0.3 |
| 57 | citymodel | citymodel/test_scenario.py | 10 | green | 0.4 |
| 58 | compliance | compliance/test_sku_compliance_map.py | 15 | green | 0.2 |
| 59 | minors | minors/test_minors.py | 19 | green | 0.1 |
| 60 | minors-wiring | minors/test_wiring.py | 70 | green | 21.2 |
| 61 | schema-migrate | test_schema_migrate.py | 21 | green | 7.3 |
| 62 | fingerprint-regen | test_fingerprint_regen.py | 16 | green | 5.5 |
| 63 | reconcile-daily-sentinel | test_reconcile_daily_sentinel.py | 8 | green | 0.6 |
| 64 | suite-matrix-discovery | test_suite_matrix.py | 16 | green | 1.0 |
| 65 | runner-profile-daily | test_runner_profile_daily.py | 12 | green | 0.3 |
| 66 | reconcile-daily-profile | test_reconcile_daily_profile.py | 7 | green | 0.5 |
| 67 | ledger-showcase | ledger/test_showcase.py | 7 | green | 0.3 |
| 68 | ledger-curation | ledger/test_curation.py | 19 | green | 0.4 |
| 69 | ledger-civicpoints | ledger/test_civicpoints.py | 20 | green | 0.5 |
| 70 | ledger-honorcert | ledger/test_honorcert.py | 7 | green | 0.5 |
| 71 | ledger-devshare | ledger/test_devshare.py | 7 | green | 0.6 |
| 72 | ledger-apimarket | ledger/test_apimarket.py | 7 | green | 0.5 |
| 73 | ledger-datasub | ledger/test_datasub.py | 7 | green | 0.2 |
| 74 | ledger-proposal | ledger/test_proposal.py | 7 | green | 0.5 |
| 75 | ledger-eventtickets | ledger/test_eventtickets.py | 14 | green | 0.4 |
| 76 | ledger-freetrial | ledger/test_freetrial.py | 7 | green | 0.4 |
|  | 合计 |  | 764 | green 76 / FAIL 0 / no-evidence 0 |  |

## 证据出处

- reconcile-all-R1774.log (qa/reconcile-all-R1774.log)
- 状态列解析自上述证据 log 的 suite 行（exit 码）与 RUNNER 终态行；证据中缺失的套件记 no-evidence（不捏造）。判据数为预注册口径，源自套件注册表。
