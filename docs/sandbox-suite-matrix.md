<!-- 机器派生文件：由 src/sandbox/suite_matrix.py 生成，勿手改（改=下轮 --check 漂移 exit 2）。再生命令见文档头「生成命令」行 -->
# 沙箱套件矩阵（对账可计费可见面）

- 生成时间: generated: 2026-10-13 21:26 +08:00
- 生成命令: python src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R1931.log
- 状态证据: reconcile-all-R1931.log (RUNNER PASS 169/169 suites green, reconcile controls 7/7, 214.2s)
- 回应: C-20261009-02「实质停摆零可计费」批评——本矩阵为机器派生的对账可计费可见面：套件注册表源自 reconcile_all.py 单一事实源，可计费面源自五域 config.json 单一事实源，逐套件状态源自最近全量回归证据 log，零手写数字。

## 汇总

| 套件数 | 判据总数 | 证据全绿 | 证据轮 |
|---|---|---|---|
| 169 | 1522 | 169/169 | R1931 |

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
| 1 | lobby | lobby/test_client.py | 57 | green | 34.0 |
| 2 | ledger | ledger/test_ledger.py | 11 | green | 0.5 |
| 3 | ledger-props | ledger/test_props.py | 7 | green | 0.2 |
| 4 | ledger-incentive | ledger/test_incentive.py | 7 | green | 0.2 |
| 5 | ledger-settlement | ledger/test_settlement.py | 7 | green | 0.1 |
| 6 | ledger-venue | ledger/test_venue.py | 7 | green | 0.2 |
| 7 | ledger-collectibles | ledger/test_collectibles.py | 7 | green | 0.2 |
| 8 | ledger-expedite | ledger/test_expedite.py | 7 | green | 0.2 |
| 9 | ledger-ads | ledger/test_ads.py | 7 | green | 0.2 |
| 10 | ledger-observation | ledger/test_observation.py | 7 | green | 0.2 |
| 11 | ledger-identity | ledger/test_identity.py | 7 | green | 0.2 |
| 12 | ledger-studio | ledger/test_studio.py | 7 | green | 0.2 |
| 13 | ledger-metered | ledger/test_metered.py | 7 | green | 0.3 |
| 14 | ledger-reports | ledger/test_reports.py | 7 | green | 0.2 |
| 15 | ledger-effects | ledger/test_effects.py | 7 | green | 0.2 |
| 16 | ledger-growth-archive | ledger/test_growth_archive.py | 7 | green | 0.3 |
| 17 | ledger-companion | ledger/test_companion.py | 7 | green | 0.2 |
| 18 | ledger-tmarket | ledger/test_tmarket.py | 7 | green | 0.2 |
| 19 | ledger-festival | ledger/test_festival.py | 7 | green | 0.2 |
| 20 | ledger-showroom | ledger/test_showroom.py | 7 | green | 0.2 |
| 21 | ledger-sistercity | ledger/test_sistercity.py | 7 | green | 0.2 |
| 22 | ledger-apidev | ledger/test_apidev.py | 7 | green | 0.4 |
| 23 | ledger-apidev-lifecycle | ledger/test_apidev_lifecycle.py | 8 | green | 0.3 |
| 24 | ledger-apidev-rate | ledger/test_apidev_rate.py | 7 | green | 0.6 |
| 25 | ledger-apidev-reject | ledger/test_apidev_reject.py | 7 | green | 0.3 |
| 26 | ledger-apidev-usagelog | ledger/test_apidev_usagelog.py | 7 | green | 0.3 |
| 27 | ledger-apidev-rejectwin | ledger/test_apidev_rejectwin.py | 7 | green | 0.3 |
| 28 | ledger-apidev-usagewin | ledger/test_apidev_usagewin.py | 8 | green | 0.3 |
| 29 | ledger-apidev-usagekind | ledger/test_apidev_usagekind.py | 8 | green | 0.3 |
| 30 | ledger-apidev-lifecycletrace | ledger/test_apidev_lifecycle_trace.py | 14 | green | 0.2 |
| 31 | tourstate | tourstate/test_tourstate.py | 7 | green | 0.1 |
| 32 | ugc | ugc/test_ugc.py | 37 | green | 6.1 |
| 33 | ugc-sec-batch | ugc/test_sec_batch.py | 22 | green | 0.5 |
| 34 | ugc-sec-batch-roll | ugc/test_sec_batch_roll.py | 7 | green | 0.2 |
| 35 | ugc-sec-batch-bannerpersist | ugc/test_sec_batch_bannerpersist.py | 7 | green | 0.2 |
| 36 | ugc-sec-batch-rowpersist | ugc/test_sec_batch_rowpersist.py | 7 | green | 0.3 |
| 37 | pay | pay/test_pay.py | 16 | green | 2.3 |
| 38 | pay-v3 | pay/test_pay_v3.py | 14 | green | 0.3 |
| 39 | pay-v3-real | pay/test_pay_v3_real.py | 9 | green | 0.5 |
| 40 | pay-v3-window | pay/test_pay_v3_window.py | 6 | green | 0.4 |
| 41 | pay-notify | pay/test_pay_notify.py | 7 | green | 0.4 |
| 42 | pay-notify-bannerlimit | pay/test_pay_notify_bannerlimit.py | 8 | green | 0.4 |
| 43 | pay-notify-bannerwin | pay/test_pay_notify_bannerwin.py | 7 | green | 0.3 |
| 44 | pay-notify-bannerroll | pay/test_pay_notify_bannerroll.py | 7 | green | 0.3 |
| 45 | pay-notify-bannerpersist | pay/test_pay_notify_bannerpersist.py | 7 | green | 0.4 |
| 46 | pay-authorize-persist | pay/test_authorize_persist.py | 7 | green | 0.3 |
| 47 | pay-authorize-idem | pay/test_authorize_idem.py | 7 | green | 1.5 |
| 48 | pay-notify-wiring | pay/test_pay_notify_wiring.py | 7 | green | 1.2 |
| 49 | pay-authorize | pay/test_authorize.py | 7 | green | 0.4 |
| 50 | pay-notify-revoke | pay/test_notify_revoke.py | 7 | green | 5.3 |
| 51 | pay-revoke-reconcile | pay/test_pay_revoke_recon.py | 7 | green | 0.8 |
| 52 | pay-channel-matrix | pay/test_channel_matrix.py | 7 | green | 0.6 |
| 53 | pay-channel-window | pay/test_channel_window.py | 7 | green | 0.6 |
| 54 | pay-channel-persist | pay/test_channel_persist.py | 7 | green | 0.2 |
| 55 | pay-channel-migrate-persist | pay/test_channel_migrate_persist.py | 5 | green | 0.3 |
| 56 | ledger-clawback | pay/test_clawback_wiring.py | 8 | green | 1.6 |
| 57 | member | member/test_member.py | 16 | green | 1.4 |
| 58 | member-entry | member/test_entry_tier.py | 7 | green | 0.1 |
| 59 | member-refund-recovery | member/test_refund_recovery.py | 7 | green | 1.1 |
| 60 | member-expiring | member/test_expiring_soon.py | 7 | green | 0.8 |
| 61 | member-reminder-scanwire | member/test_reminder_scan_wire.py | 7 | green | 0.3 |
| 62 | member-banner-board | member/test_banner_board.py | 17 | green | 0.5 |
| 63 | member-banner-roll | member/test_banner_board_roll.py | 7 | green | 0.3 |
| 64 | member-banner-queue-window | member/test_banner_queue_window.py | 7 | green | 0.2 |
| 65 | member-banner-queue-limit | member/test_banner_queue_limit.py | 8 | green | 0.2 |
| 66 | member-banner-queue-caproll | member/test_banner_queue_caproll.py | 7 | green | 0.2 |
| 67 | member-banner-queue-persist | member/test_banner_queue_persist.py | 7 | green | 0.5 |
| 68 | member-banner-board-persist | member/test_banner_board_persist.py | 7 | green | 0.2 |
| 69 | watermark | watermark/test_watermark.py | 5 | green | 1.2 |
| 70 | watermark-robust | watermark/test_watermark_robust.py | 6 | green | 1.8 |
| 71 | watermark-sweep | watermark/test_watermark_sweep.py | 6 | green | 21.9 |
| 72 | watermark-scale-recover | watermark/test_scale_recover.py | 7 | green | 7.3 |
| 73 | watermark-scale-unknown | watermark/test_scale_unknown.py | 6 | green | 12.3 |
| 74 | watermark-scale-refine | watermark/test_scale_refine.py | 6 | green | 16.1 |
| 75 | dual-track | watermark/test_dual_track.py | 7 | green | 1.2 |
| 76 | watermark-bindbit | watermark/test_bind_bit.py | 7 | green | 3.4 |
| 77 | watermark-dualbit | watermark/test_dual_bit.py | 7 | green | 3.0 |
| 78 | opsreview | opsreview/test_opsreview.py | 7 | green | 1.0 |
| 79 | liveroom | liveroom/test_liveroom.py | 10 | green | 0.4 |
| 80 | benchgate | benchgate/test_bench_gate.py | 11 | green | 0.2 |
| 81 | citymodel | citymodel/test_scenario.py | 10 | green | 0.3 |
| 82 | compliance | compliance/test_sku_compliance_map.py | 15 | green | 0.1 |
| 83 | minors | minors/test_minors.py | 19 | green | 0.1 |
| 84 | minors-wiring | minors/test_wiring.py | 70 | green | 22.2 |
| 85 | schema-migrate | test_schema_migrate.py | 21 | green | 5.7 |
| 86 | fingerprint-regen | test_fingerprint_regen.py | 16 | green | 4.0 |
| 87 | reconcile-daily-sentinel | test_reconcile_daily_sentinel.py | 8 | green | 0.7 |
| 88 | suite-matrix-discovery | test_suite_matrix.py | 16 | green | 1.2 |
| 89 | runner-profile-daily | test_runner_profile_daily.py | 12 | green | 0.3 |
| 90 | reconcile-daily-profile | test_reconcile_daily_profile.py | 7 | green | 0.5 |
| 91 | reconcile-daily-census | test_reconcile_daily_census.py | 8 | green | 11.2 |
| 92 | ledger-showcase | ledger/test_showcase.py | 7 | green | 0.2 |
| 93 | ledger-curation | ledger/test_curation.py | 19 | green | 0.3 |
| 94 | ledger-curation-hotpersist | ledger/test_curation_hotpersist.py | 6 | green | 0.2 |
| 95 | ledger-curation-regpersist | ledger/test_curation_regpersist.py | 7 | green | 0.2 |
| 96 | ledger-civicpoints | ledger/test_civicpoints.py | 20 | green | 0.2 |
| 97 | ledger-honorcert | ledger/test_honorcert.py | 7 | green | 0.3 |
| 98 | ledger-civicpersist | ledger/test_civic_persist.py | 7 | green | 0.2 |
| 99 | ledger-devshare | ledger/test_devshare.py | 7 | green | 0.3 |
| 100 | ledger-apimarket | ledger/test_apimarket.py | 7 | green | 0.3 |
| 101 | ledger-datasub | ledger/test_datasub.py | 7 | green | 0.2 |
| 102 | ledger-proposal | ledger/test_proposal.py | 7 | green | 0.3 |
| 103 | ledger-eventtickets | ledger/test_eventtickets.py | 14 | green | 0.3 |
| 104 | ledger-eventtickets-boardwin | ledger/test_eventtickets_boardwin.py | 7 | green | 0.2 |
| 105 | ledger-eventtickets-boardlimit | ledger/test_eventtickets_boardlimit.py | 7 | green | 0.3 |
| 106 | ledger-eventtickets-roll | ledger/test_eventtickets_roll.py | 7 | green | 0.2 |
| 107 | ledger-eventtickets-telescope | ledger/test_eventtickets_telescope.py | 6 | green | 0.2 |
| 108 | ledger-freetrial | ledger/test_freetrial.py | 7 | green | 0.2 |
| 109 | ledger-freetrial-funnel | ledger/test_freetrial_funnel.py | 7 | green | 0.4 |
| 110 | ledger-freetrial-funnelwin | ledger/test_freetrial_funnelwin.py | 7 | green | 0.6 |
| 111 | ledger-freetrial-callmonth | ledger/test_freetrial_callmonth.py | 7 | green | 0.3 |
| 112 | ledger-freetrial-callkind | ledger/test_freetrial_callkind.py | 8 | green | 0.3 |
| 113 | ledger-freetrial-callplan | ledger/test_freetrial_callplan.py | 8 | green | 0.3 |
| 114 | ledger-freetrial-callengine | ledger/test_freetrial_callengine.py | 8 | green | 0.2 |
| 115 | ledger-freetrial-callaccount | ledger/test_freetrial_callaccount.py | 8 | green | 0.2 |
| 116 | ledger-freetrial-capusage | ledger/test_freetrial_capusage.py | 8 | green | 0.2 |
| 117 | ledger-freetrial-caplimit | ledger/test_freetrial_caplimit.py | 7 | green | 0.2 |
| 118 | ledger-freetrial-caproll | ledger/test_freetrial_caproll.py | 7 | green | 0.3 |
| 119 | ledger-freetrial-callroll | ledger/test_freetrial_callroll.py | 7 | green | 0.3 |
| 120 | ledger-freetrial-funnelroll | ledger/test_freetrial_funnelroll.py | 7 | green | 0.3 |
| 121 | ledger-freetrial-funnelcap | ledger/test_freetrial_funnelcap.py | 7 | green | 0.4 |
| 122 | ledger-freetrial-funnelpersist | ledger/test_freetrial_funnelpersist.py | 7 | green | 0.3 |
| 123 | ledger-freetrial-cappersist | ledger/test_freetrial_cappersist.py | 8 | green | 0.4 |
| 124 | ledger-freetrial-fivepersist | ledger/test_freetrial_fivepersist.py | 7 | green | 0.8 |
| 125 | ugc-pool-water | ugc/test_pool_water.py | 7 | green | 0.4 |
| 126 | ugc-pool-delta | ugc/test_pool_delta.py | 7 | green | 0.6 |
| 127 | ugc-ingest-waterwire | ugc/test_ingest_waterwire.py | 6 | green | 0.3 |
| 128 | ugc-batch-water | ugc/test_batch_waterwire.py | 6 | green | 0.4 |
| 129 | ugc-drain-water | ugc/test_drain_waterwire.py | 6 | green | 0.5 |
| 130 | ugc-submit-water | ugc/test_submit_waterwire.py | 7 | green | 0.5 |
| 131 | ugc-verdict-water | ugc/test_verdict_waterwire.py | 7 | green | 0.7 |
| 132 | ugc-water-journal | ugc/test_water_journal.py | 7 | green | 0.5 |
| 133 | ugc-water-kindtally | ugc/test_water_kind_tally.py | 7 | green | 0.3 |
| 134 | ugc-water-monthlyflow | ugc/test_water_monthly_flow.py | 7 | green | 0.2 |
| 135 | ugc-water-journalwin | ugc/test_water_journal_window.py | 7 | green | 0.2 |
| 136 | ugc-water-journalcap | ugc/test_water_journal_limit.py | 7 | green | 0.2 |
| 137 | ugc-water-celltotals | ugc/test_water_cell_totals.py | 7 | green | 0.2 |
| 138 | member-expiring-dist | member/test_expiring_dist.py | 7 | green | 0.9 |
| 139 | ledger-apidev-lineage | ledger/test_apidev_lineage.py | 22 | green | 0.3 |
| 140 | ledger-apidev-chainusage | ledger/test_apidev_chainusage.py | 14 | green | 0.3 |
| 141 | ledger-apidev-devboard-roll | ledger/test_apidev_devboard_roll.py | 7 | green | 0.2 |
| 142 | ledger-apidev-devboard-limit | ledger/test_apidev_devboard_limit.py | 14 | green | 0.3 |
| 143 | ledger-apidev-devboard-ancestry | ledger/test_apidev_devboard_ancestry.py | 7 | green | 0.2 |
| 144 | ledger-apidev-keyviewwin | ledger/test_apidev_keyviewwin.py | 7 | green | 0.2 |
| 145 | ugc-water-journalroll | ugc/test_water_journal_roll.py | 7 | green | 0.1 |
| 146 | ugc-sec-batch-rowsroll | ugc/test_sec_batch_rowsroll.py | 7 | green | 0.2 |
| 147 | ledger-apidev-lineagepersist | ledger/test_apidev_lineagepersist.py | 7 | green | 0.2 |
| 148 | ledger-apidev-chainusagepersist | ledger/test_apidev_chainusagepersist.py | 7 | green | 0.3 |
| 149 | ledger-apidev-devboardpersist | ledger/test_apidev_devboardpersist.py | 7 | green | 0.4 |
| 150 | ledger-eventtickets-boardpersist | ledger/test_eventtickets_boardpersist.py | 7 | green | 0.2 |
| 151 | ledger-eventtickets-sessionpersist | ledger/test_eventtickets_sessionpersist.py | 7 | green | 0.2 |
| 152 | member-expiring-soon-persist | member/test_expiring_soon_persist.py | 7 | green | 0.3 |
| 153 | ledger-apidev-usagelogpersist | ledger/test_apidev_usagelogpersist.py | 7 | green | 0.3 |
| 154 | ugc-water-journalboardpersist | ugc/test_water_journal_boardpersist.py | 7 | green | 0.2 |
| 155 | ugc-water-sisterpersist | ugc/test_water_journal_sisterpersist.py | 12 | green | 0.2 |
| 156 | ledger-apidev-keyviewpersist | ledger/test_apidev_keyviewpersist.py | 7 | green | 0.3 |
| 157 | ledger-apidev-rejecttallpersist | ledger/test_apidev_rejecttallpersist.py | 7 | green | 0.3 |
| 158 | ledger-apidev-lifecycletracepersist | ledger/test_apidev_lifecycletracepersist.py | 7 | green | 0.2 |
| 159 | ledger-apidev-usagekindpersist | ledger/test_apidev_usagekindpersist.py | 7 | green | 0.5 |
| 160 | member-balanceface-persist | member/test_balance_face_persist.py | 7 | green | 0.3 |
| 161 | member-privileges-persist | member/test_privileges_persist.py | 7 | green | 0.3 |
| 162 | ugc-drain-waterpersist | ugc/test_drain_waterpersist.py | 7 | green | 0.6 |
| 163 | ugc-pool-waterpersist | ugc/test_pool_waterpersist.py | 7 | green | 0.4 |
| 164 | ugc-reviewdesk-persist | ugc/test_reviewdesk_persist.py | 7 | green | 0.6 |
| 165 | member-birthcert-persist | member/test_birthcert_persist.py | 7 | green | 0.3 |
| 166 | member-expiring-dist-persist | member/test_expiring_dist_persist.py | 7 | green | 0.4 |
| 167 | ugc-export-persist | ugc/test_export_persist.py | 7 | green | 0.6 |
| 168 | ledger-showcaseview-persist | ledger/test_showcase_persist.py | 7 | green | 0.2 |
| 169 | ledger-collectibles-persist | ledger/test_collectibles_persist.py | 7 | green | 0.2 |
|  | 合计 |  | 1522 | green 169 / FAIL 0 / no-evidence 0 |  |

## 证据出处

- reconcile-all-R1931.log (qa/reconcile-all-R1931.log)
- 状态列解析自上述证据 log 的 suite 行（exit 码）与 RUNNER 终态行；证据中缺失的套件记 no-evidence（不捏造）。判据数为预注册口径，源自套件注册表。
