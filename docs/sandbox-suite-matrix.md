<!-- 机器派生文件：由 src/sandbox/suite_matrix.py 生成，勿手改（改=下轮 --check 漂移 exit 2）。再生命令见文档头「生成命令」行 -->
# 沙箱套件矩阵（对账可计费可见面）

- 生成时间: generated: 2026-10-12 08:33 +08:00
- 生成命令: python src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R1854.log
- 状态证据: reconcile-all-R1854.log (RUNNER PASS 114/114 suites green, reconcile controls 7/7, 182.5s)
- 回应: C-20261009-02「实质停摆零可计费」批评——本矩阵为机器派生的对账可计费可见面：套件注册表源自 reconcile_all.py 单一事实源，可计费面源自五域 config.json 单一事实源，逐套件状态源自最近全量回归证据 log，零手写数字。

## 汇总

| 套件数 | 判据总数 | 证据全绿 | 证据轮 |
|---|---|---|---|
| 114 | 1049 | 114/114 | R1854 |

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
| 1 | lobby | lobby/test_client.py | 22 | green | 23.2 |
| 2 | ledger | ledger/test_ledger.py | 11 | green | 0.5 |
| 3 | ledger-props | ledger/test_props.py | 7 | green | 0.2 |
| 4 | ledger-incentive | ledger/test_incentive.py | 7 | green | 0.2 |
| 5 | ledger-settlement | ledger/test_settlement.py | 7 | green | 0.1 |
| 6 | ledger-venue | ledger/test_venue.py | 7 | green | 0.2 |
| 7 | ledger-collectibles | ledger/test_collectibles.py | 7 | green | 0.2 |
| 8 | ledger-expedite | ledger/test_expedite.py | 7 | green | 0.2 |
| 9 | ledger-ads | ledger/test_ads.py | 7 | green | 0.3 |
| 10 | ledger-observation | ledger/test_observation.py | 7 | green | 0.2 |
| 11 | ledger-identity | ledger/test_identity.py | 7 | green | 0.2 |
| 12 | ledger-studio | ledger/test_studio.py | 7 | green | 0.2 |
| 13 | ledger-metered | ledger/test_metered.py | 7 | green | 0.2 |
| 14 | ledger-reports | ledger/test_reports.py | 7 | green | 0.3 |
| 15 | ledger-effects | ledger/test_effects.py | 7 | green | 0.3 |
| 16 | ledger-growth-archive | ledger/test_growth_archive.py | 7 | green | 0.2 |
| 17 | ledger-companion | ledger/test_companion.py | 7 | green | 0.2 |
| 18 | ledger-tmarket | ledger/test_tmarket.py | 7 | green | 0.2 |
| 19 | ledger-festival | ledger/test_festival.py | 7 | green | 0.2 |
| 20 | ledger-showroom | ledger/test_showroom.py | 7 | green | 0.3 |
| 21 | ledger-sistercity | ledger/test_sistercity.py | 7 | green | 0.2 |
| 22 | ledger-apidev | ledger/test_apidev.py | 7 | green | 0.3 |
| 23 | ledger-apidev-lifecycle | ledger/test_apidev_lifecycle.py | 8 | green | 0.3 |
| 24 | ledger-apidev-rate | ledger/test_apidev_rate.py | 7 | green | 0.3 |
| 25 | ledger-apidev-reject | ledger/test_apidev_reject.py | 7 | green | 0.3 |
| 26 | ledger-apidev-usagelog | ledger/test_apidev_usagelog.py | 7 | green | 0.4 |
| 27 | ledger-apidev-rejectwin | ledger/test_apidev_rejectwin.py | 7 | green | 0.3 |
| 28 | ledger-apidev-usagewin | ledger/test_apidev_usagewin.py | 8 | green | 0.3 |
| 29 | ledger-apidev-usagekind | ledger/test_apidev_usagekind.py | 8 | green | 0.3 |
| 30 | ledger-apidev-lifecycletrace | ledger/test_apidev_lifecycle_trace.py | 7 | green | 0.2 |
| 31 | tourstate | tourstate/test_tourstate.py | 7 | green | 0.1 |
| 32 | ugc | ugc/test_ugc.py | 37 | green | 4.5 |
| 33 | ugc-sec-batch | ugc/test_sec_batch.py | 12 | green | 0.3 |
| 34 | pay | pay/test_pay.py | 16 | green | 2.2 |
| 35 | pay-v3 | pay/test_pay_v3.py | 14 | green | 0.3 |
| 36 | pay-v3-real | pay/test_pay_v3_real.py | 9 | green | 0.6 |
| 37 | pay-v3-window | pay/test_pay_v3_window.py | 6 | green | 0.5 |
| 38 | pay-notify | pay/test_pay_notify.py | 7 | green | 0.5 |
| 39 | pay-notify-wiring | pay/test_pay_notify_wiring.py | 7 | green | 1.4 |
| 40 | pay-authorize | pay/test_authorize.py | 7 | green | 0.5 |
| 41 | pay-notify-revoke | pay/test_notify_revoke.py | 7 | green | 5.4 |
| 42 | pay-revoke-reconcile | pay/test_pay_revoke_recon.py | 7 | green | 0.9 |
| 43 | pay-channel-matrix | pay/test_channel_matrix.py | 7 | green | 0.6 |
| 44 | pay-channel-window | pay/test_channel_window.py | 7 | green | 0.7 |
| 45 | ledger-clawback | pay/test_clawback_wiring.py | 8 | green | 1.5 |
| 46 | member | member/test_member.py | 16 | green | 1.8 |
| 47 | member-entry | member/test_entry_tier.py | 7 | green | 0.1 |
| 48 | member-refund-recovery | member/test_refund_recovery.py | 7 | green | 0.9 |
| 49 | member-expiring | member/test_expiring_soon.py | 7 | green | 1.0 |
| 50 | member-reminder-scanwire | member/test_reminder_scan_wire.py | 7 | green | 0.4 |
| 51 | member-banner-board | member/test_banner_board.py | 12 | green | 0.4 |
| 52 | watermark | watermark/test_watermark.py | 5 | green | 1.5 |
| 53 | watermark-robust | watermark/test_watermark_robust.py | 6 | green | 2.3 |
| 54 | watermark-sweep | watermark/test_watermark_sweep.py | 6 | green | 28.2 |
| 55 | watermark-scale-recover | watermark/test_scale_recover.py | 7 | green | 8.5 |
| 56 | watermark-scale-unknown | watermark/test_scale_unknown.py | 6 | green | 14.0 |
| 57 | watermark-scale-refine | watermark/test_scale_refine.py | 6 | green | 17.9 |
| 58 | dual-track | watermark/test_dual_track.py | 7 | green | 1.5 |
| 59 | watermark-bindbit | watermark/test_bind_bit.py | 7 | green | 4.1 |
| 60 | watermark-dualbit | watermark/test_dual_bit.py | 7 | green | 3.1 |
| 61 | opsreview | opsreview/test_opsreview.py | 7 | green | 1.1 |
| 62 | liveroom | liveroom/test_liveroom.py | 10 | green | 0.3 |
| 63 | benchgate | benchgate/test_bench_gate.py | 11 | green | 0.2 |
| 64 | citymodel | citymodel/test_scenario.py | 10 | green | 0.3 |
| 65 | compliance | compliance/test_sku_compliance_map.py | 15 | green | 0.2 |
| 66 | minors | minors/test_minors.py | 19 | green | 0.1 |
| 67 | minors-wiring | minors/test_wiring.py | 70 | green | 16.0 |
| 68 | schema-migrate | test_schema_migrate.py | 21 | green | 6.1 |
| 69 | fingerprint-regen | test_fingerprint_regen.py | 16 | green | 3.7 |
| 70 | reconcile-daily-sentinel | test_reconcile_daily_sentinel.py | 8 | green | 0.7 |
| 71 | suite-matrix-discovery | test_suite_matrix.py | 16 | green | 1.1 |
| 72 | runner-profile-daily | test_runner_profile_daily.py | 12 | green | 0.2 |
| 73 | reconcile-daily-profile | test_reconcile_daily_profile.py | 7 | green | 0.4 |
| 74 | reconcile-daily-census | test_reconcile_daily_census.py | 8 | green | 0.8 |
| 75 | ledger-showcase | ledger/test_showcase.py | 7 | green | 0.3 |
| 76 | ledger-curation | ledger/test_curation.py | 19 | green | 0.3 |
| 77 | ledger-civicpoints | ledger/test_civicpoints.py | 20 | green | 0.3 |
| 78 | ledger-honorcert | ledger/test_honorcert.py | 7 | green | 0.4 |
| 79 | ledger-devshare | ledger/test_devshare.py | 7 | green | 0.4 |
| 80 | ledger-apimarket | ledger/test_apimarket.py | 7 | green | 0.3 |
| 81 | ledger-datasub | ledger/test_datasub.py | 7 | green | 0.3 |
| 82 | ledger-proposal | ledger/test_proposal.py | 7 | green | 0.4 |
| 83 | ledger-eventtickets | ledger/test_eventtickets.py | 14 | green | 0.3 |
| 84 | ledger-eventtickets-boardwin | ledger/test_eventtickets_boardwin.py | 7 | green | 0.2 |
| 85 | ledger-eventtickets-boardlimit | ledger/test_eventtickets_boardlimit.py | 7 | green | 0.3 |
| 86 | ledger-freetrial | ledger/test_freetrial.py | 7 | green | 0.3 |
| 87 | ledger-freetrial-funnel | ledger/test_freetrial_funnel.py | 7 | green | 0.3 |
| 88 | ledger-freetrial-funnelwin | ledger/test_freetrial_funnelwin.py | 7 | green | 0.3 |
| 89 | ledger-freetrial-callmonth | ledger/test_freetrial_callmonth.py | 7 | green | 0.3 |
| 90 | ledger-freetrial-callkind | ledger/test_freetrial_callkind.py | 8 | green | 0.3 |
| 91 | ledger-freetrial-callplan | ledger/test_freetrial_callplan.py | 8 | green | 0.3 |
| 92 | ledger-freetrial-callengine | ledger/test_freetrial_callengine.py | 8 | green | 0.4 |
| 93 | ledger-freetrial-callaccount | ledger/test_freetrial_callaccount.py | 8 | green | 0.3 |
| 94 | ledger-freetrial-capusage | ledger/test_freetrial_capusage.py | 8 | green | 0.3 |
| 95 | ledger-freetrial-caplimit | ledger/test_freetrial_caplimit.py | 7 | green | 0.3 |
| 96 | ledger-freetrial-caproll | ledger/test_freetrial_caproll.py | 7 | green | 0.3 |
| 97 | ugc-pool-water | ugc/test_pool_water.py | 7 | green | 0.5 |
| 98 | ugc-pool-delta | ugc/test_pool_delta.py | 7 | green | 0.6 |
| 99 | ugc-ingest-waterwire | ugc/test_ingest_waterwire.py | 6 | green | 0.4 |
| 100 | ugc-batch-water | ugc/test_batch_waterwire.py | 6 | green | 0.4 |
| 101 | ugc-drain-water | ugc/test_drain_waterwire.py | 6 | green | 0.4 |
| 102 | ugc-submit-water | ugc/test_submit_waterwire.py | 7 | green | 0.5 |
| 103 | ugc-verdict-water | ugc/test_verdict_waterwire.py | 7 | green | 0.6 |
| 104 | ugc-water-journal | ugc/test_water_journal.py | 7 | green | 0.7 |
| 105 | ugc-water-kindtally | ugc/test_water_kind_tally.py | 7 | green | 0.2 |
| 106 | ugc-water-monthlyflow | ugc/test_water_monthly_flow.py | 7 | green | 0.2 |
| 107 | ugc-water-journalwin | ugc/test_water_journal_window.py | 7 | green | 0.2 |
| 108 | ugc-water-journalcap | ugc/test_water_journal_limit.py | 7 | green | 0.2 |
| 109 | ugc-water-celltotals | ugc/test_water_cell_totals.py | 7 | green | 0.2 |
| 110 | member-expiring-dist | member/test_expiring_dist.py | 7 | green | 0.7 |
| 111 | ledger-apidev-lineage | ledger/test_apidev_lineage.py | 7 | green | 0.3 |
| 112 | ledger-apidev-chainusage | ledger/test_apidev_chainusage.py | 8 | green | 0.4 |
| 113 | ledger-apidev-devboard-roll | ledger/test_apidev_devboard_roll.py | 7 | green | 0.3 |
| 114 | ledger-apidev-devboard-limit | ledger/test_apidev_devboard_limit.py | 8 | green | 0.3 |
|  | 合计 |  | 1049 | green 114 / FAIL 0 / no-evidence 0 |  |

## 证据出处

- reconcile-all-R1854.log (qa/reconcile-all-R1854.log)
- 状态列解析自上述证据 log 的 suite 行（exit 码）与 RUNNER 终态行；证据中缺失的套件记 no-evidence（不捏造）。判据数为预注册口径，源自套件注册表。
