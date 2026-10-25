<!-- 机器派生文件：由 src/sandbox/suite_matrix.py 生成，勿手改（改=下轮 --check 漂移 exit 2）。再生命令见文档头「生成命令」行 -->
# 沙箱套件矩阵（对账可计费可见面）

- 生成时间: generated: 2026-10-25 13:08 +08:00
- 生成命令: python src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R2121.log
- 状态证据: reconcile-all-R2121.log (RUNNER PASS 326/326 suites green, reconcile controls 7/7, 1084.0s)
- 回应: C-20261009-02「实质停摆零可计费」批评——本矩阵为机器派生的对账可计费可见面：套件注册表源自 reconcile_all.py 单一事实源，可计费面源自五域 config.json 单一事实源，逐套件状态源自最近全量回归证据 log，零手写数字。

## 汇总

| 套件数 | 判据总数 | 证据全绿 | 证据轮 |
|---|---|---|---|
| 326 | 2716 | 326/326 | R2121 |

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
| 1 | lobby | lobby/test_client.py | 79 | green | 52.1 |
| 2 | ledger | ledger/test_ledger.py | 11 | green | 3.6 |
| 3 | ledger-props | ledger/test_props.py | 7 | green | 1.6 |
| 4 | ledger-props-persist | ledger/test_props_persist.py | 7 | green | 1.0 |
| 5 | ledger-identity-persist | ledger/test_identity_persist.py | 7 | green | 1.3 |
| 6 | ledger-incentive | ledger/test_incentive.py | 7 | green | 0.3 |
| 7 | ledger-settlement | ledger/test_settlement.py | 7 | green | 0.2 |
| 8 | ledger-settlement-persist | ledger/test_settlement_persist.py | 7 | green | 1.1 |
| 9 | ledger-venue | ledger/test_venue.py | 7 | green | 1.2 |
| 10 | ledger-venue-persist | ledger/test_venue_persist.py | 7 | green | 0.7 |
| 11 | ledger-collectibles | ledger/test_collectibles.py | 7 | green | 0.4 |
| 12 | ledger-expedite | ledger/test_expedite.py | 7 | green | 0.4 |
| 13 | ledger-expedite-persist | ledger/test_expedite_persist.py | 7 | green | 0.4 |
| 14 | ledger-ads | ledger/test_ads.py | 7 | green | 0.8 |
| 15 | ledger-ads-persist | ledger/test_ads_persist.py | 7 | green | 2.5 |
| 16 | ledger-observation | ledger/test_observation.py | 7 | green | 1.4 |
| 17 | ledger-observation-persist | ledger/test_observation_persist.py | 7 | green | 1.1 |
| 18 | ledger-identity | ledger/test_identity.py | 7 | green | 2.1 |
| 19 | ledger-studio | ledger/test_studio.py | 7 | green | 1.2 |
| 20 | ledger-metered | ledger/test_metered.py | 7 | green | 1.0 |
| 21 | ledger-metered-persist | ledger/test_metered_persist.py | 7 | green | 0.5 |
| 22 | ledger-reports | ledger/test_reports.py | 7 | green | 1.1 |
| 23 | ledger-reports-persist | ledger/test_reports_persist.py | 7 | green | 1.8 |
| 24 | ledger-effects | ledger/test_effects.py | 7 | green | 0.5 |
| 25 | ledger-growth-archive | ledger/test_growth_archive.py | 7 | green | 0.3 |
| 26 | ledger-companion | ledger/test_companion.py | 7 | green | 0.4 |
| 27 | ledger-companion-persist | ledger/test_companion_persist.py | 7 | green | 0.6 |
| 28 | ledger-tmarket | ledger/test_tmarket.py | 7 | green | 2.5 |
| 29 | ledger-festival | ledger/test_festival.py | 7 | green | 1.7 |
| 30 | ledger-showroom | ledger/test_showroom.py | 7 | green | 2.9 |
| 31 | ledger-sistercity | ledger/test_sistercity.py | 7 | green | 1.0 |
| 32 | ledger-apidev | ledger/test_apidev.py | 7 | green | 2.6 |
| 33 | ledger-apidev-lifecycle | ledger/test_apidev_lifecycle.py | 8 | green | 1.5 |
| 34 | ledger-apidev-rate | ledger/test_apidev_rate.py | 7 | green | 0.6 |
| 35 | ledger-apidev-reject | ledger/test_apidev_reject.py | 7 | green | 3.0 |
| 36 | ledger-apidev-usagelog | ledger/test_apidev_usagelog.py | 7 | green | 2.2 |
| 37 | ledger-apidev-rejectwin | ledger/test_apidev_rejectwin.py | 7 | green | 2.9 |
| 38 | ledger-apidev-usagewin | ledger/test_apidev_usagewin.py | 8 | green | 1.6 |
| 39 | ledger-apidev-usagekind | ledger/test_apidev_usagekind.py | 8 | green | 2.2 |
| 40 | ledger-apidev-lifecycletrace | ledger/test_apidev_lifecycle_trace.py | 14 | green | 2.1 |
| 41 | tourstate | tourstate/test_tourstate.py | 7 | green | 0.2 |
| 42 | ugc | ugc/test_ugc.py | 37 | green | 23.1 |
| 43 | ugc-sec-batch | ugc/test_sec_batch.py | 22 | green | 2.6 |
| 44 | ugc-sec-batch-roll | ugc/test_sec_batch_roll.py | 7 | green | 1.2 |
| 45 | ugc-sec-batch-bannerpersist | ugc/test_sec_batch_bannerpersist.py | 7 | green | 3.0 |
| 46 | ugc-sec-batch-rowpersist | ugc/test_sec_batch_rowpersist.py | 7 | green | 1.6 |
| 47 | pay | pay/test_pay.py | 16 | green | 12.6 |
| 48 | pay-v3 | pay/test_pay_v3.py | 14 | green | 3.4 |
| 49 | pay-v3-real | pay/test_pay_v3_real.py | 9 | green | 2.7 |
| 50 | pay-v3-window | pay/test_pay_v3_window.py | 6 | green | 2.3 |
| 51 | pay-notify | pay/test_pay_notify.py | 7 | green | 4.4 |
| 52 | pay-notify-bannerlimit | pay/test_pay_notify_bannerlimit.py | 8 | green | 1.2 |
| 53 | pay-notify-bannerwin | pay/test_pay_notify_bannerwin.py | 7 | green | 2.8 |
| 54 | pay-notify-bannerroll | pay/test_pay_notify_bannerroll.py | 7 | green | 0.8 |
| 55 | pay-notify-bannerpersist | pay/test_pay_notify_bannerpersist.py | 7 | green | 3.6 |
| 56 | pay-authorize-persist | pay/test_authorize_persist.py | 7 | green | 0.9 |
| 57 | pay-authorize-idem | pay/test_authorize_idem.py | 7 | green | 1.6 |
| 58 | pay-notify-wiring | pay/test_pay_notify_wiring.py | 7 | green | 2.4 |
| 59 | pay-authorize | pay/test_authorize.py | 7 | green | 0.9 |
| 60 | pay-notify-revoke | pay/test_notify_revoke.py | 7 | green | 6.1 |
| 61 | pay-revoke-reconcile | pay/test_pay_revoke_recon.py | 7 | green | 1.2 |
| 62 | pay-channel-matrix | pay/test_channel_matrix.py | 7 | green | 1.5 |
| 63 | pay-channel-window | pay/test_channel_window.py | 7 | green | 4.0 |
| 64 | pay-channel-persist | pay/test_channel_persist.py | 7 | green | 2.5 |
| 65 | pay-channel-migrate-persist | pay/test_channel_migrate_persist.py | 5 | green | 1.5 |
| 66 | ledger-clawback | pay/test_clawback_wiring.py | 8 | green | 12.6 |
| 67 | ledger-clawback-persist | pay/test_clawback_persist.py | 7 | green | 0.8 |
| 68 | member | member/test_member.py | 16 | green | 2.3 |
| 69 | member-entry | member/test_entry_tier.py | 7 | green | 0.1 |
| 70 | member-entrytier-persist | member/test_entry_tier_persist.py | 7 | green | 0.6 |
| 71 | member-refund-recovery | member/test_refund_recovery.py | 7 | green | 3.7 |
| 72 | member-expiring | member/test_expiring_soon.py | 7 | green | 8.4 |
| 73 | member-reminder-scanwire | member/test_reminder_scan_wire.py | 7 | green | 6.1 |
| 74 | member-banner-board | member/test_banner_board.py | 17 | green | 5.4 |
| 75 | member-banner-roll | member/test_banner_board_roll.py | 7 | green | 0.4 |
| 76 | member-banner-queue-window | member/test_banner_queue_window.py | 7 | green | 0.3 |
| 77 | member-banner-queue-limit | member/test_banner_queue_limit.py | 8 | green | 0.4 |
| 78 | member-banner-queue-caproll | member/test_banner_queue_caproll.py | 7 | green | 0.3 |
| 79 | member-banner-queue-persist | member/test_banner_queue_persist.py | 7 | green | 0.3 |
| 80 | member-banner-board-persist | member/test_banner_board_persist.py | 7 | green | 0.4 |
| 81 | watermark | watermark/test_watermark.py | 5 | green | 1.2 |
| 82 | watermark-robust | watermark/test_watermark_robust.py | 6 | green | 1.8 |
| 83 | watermark-sweep | watermark/test_watermark_sweep.py | 6 | green | 28.9 |
| 84 | watermark-scale-recover | watermark/test_scale_recover.py | 7 | green | 9.8 |
| 85 | watermark-scale-unknown | watermark/test_scale_unknown.py | 6 | green | 12.5 |
| 86 | watermark-scale-refine | watermark/test_scale_refine.py | 6 | green | 16.4 |
| 87 | dual-track | watermark/test_dual_track.py | 7 | green | 1.7 |
| 88 | watermark-bindbit | watermark/test_bind_bit.py | 7 | green | 4.7 |
| 89 | watermark-dualbit | watermark/test_dual_bit.py | 7 | green | 3.9 |
| 90 | opsreview | opsreview/test_opsreview.py | 7 | green | 1.5 |
| 91 | liveroom | liveroom/test_liveroom.py | 10 | green | 0.4 |
| 92 | benchgate | benchgate/test_bench_gate.py | 11 | green | 0.2 |
| 93 | citymodel | citymodel/test_scenario.py | 10 | green | 0.4 |
| 94 | compliance | compliance/test_sku_compliance_map.py | 15 | green | 0.2 |
| 95 | minors | minors/test_minors.py | 19 | green | 0.2 |
| 96 | minors-wiring | minors/test_wiring.py | 70 | green | 29.2 |
| 97 | minors-persist | minors/test_minors_persist.py | 7 | green | 0.3 |
| 98 | schema-migrate | test_schema_migrate.py | 21 | green | 6.0 |
| 99 | fingerprint-regen | test_fingerprint_regen.py | 16 | green | 6.2 |
| 100 | reconcile-daily-sentinel | test_reconcile_daily_sentinel.py | 8 | green | 1.1 |
| 101 | suite-matrix-discovery | test_suite_matrix.py | 16 | green | 0.8 |
| 102 | runner-profile-daily | test_runner_profile_daily.py | 12 | green | 0.1 |
| 103 | reconcile-daily-profile | test_reconcile_daily_profile.py | 7 | green | 0.3 |
| 104 | reconcile-daily-census | test_reconcile_daily_census.py | 8 | green | 4.5 |
| 105 | ledger-showcase | ledger/test_showcase.py | 7 | green | 0.4 |
| 106 | ledger-curation | ledger/test_curation.py | 24 | green | 0.6 |
| 107 | ledger-curation-hotpersist | ledger/test_curation_hotpersist.py | 6 | green | 0.3 |
| 108 | ledger-curation-coldpersist | ledger/test_curation_coldpersist.py | 6 | green | 0.4 |
| 109 | ledger-curation-combined | ledger/test_curation_combined.py | 7 | green | 0.6 |
| 110 | ledger-curation-combinedpersist | ledger/test_curation_combinedpersist.py | 6 | green | 0.5 |
| 111 | ledger-curation-combinedboundary | ledger/test_curation_combinedboundary.py | 6 | green | 0.4 |
| 112 | ledger-curation-combinedmonth | ledger/test_curation_combinedmonth.py | 7 | green | 0.4 |
| 113 | ledger-curation-regpersist | ledger/test_curation_regpersist.py | 7 | green | 0.3 |
| 114 | ledger-civicpoints | ledger/test_civicpoints.py | 20 | green | 0.5 |
| 115 | ledger-honorcert | ledger/test_honorcert.py | 7 | green | 0.5 |
| 116 | ledger-honorcert-yearbook | ledger/test_honorcert_yearbook.py | 7 | green | 0.4 |
| 117 | ledger-civicpersist | ledger/test_civic_persist.py | 7 | green | 0.3 |
| 118 | ledger-devshare | ledger/test_devshare.py | 7 | green | 0.6 |
| 119 | ledger-apimarket | ledger/test_apimarket.py | 7 | green | 0.6 |
| 120 | ledger-datasub | ledger/test_datasub.py | 7 | green | 0.3 |
| 121 | ledger-proposal | ledger/test_proposal.py | 12 | green | 0.5 |
| 122 | ledger-proposal-persist | ledger/test_proposal_persist.py | 7 | green | 0.3 |
| 123 | ledger-incentive-persist | ledger/test_incentive_persist.py | 7 | green | 0.3 |
| 124 | ledger-eventtickets | ledger/test_eventtickets.py | 14 | green | 0.5 |
| 125 | ledger-eventtickets-boardwin | ledger/test_eventtickets_boardwin.py | 7 | green | 0.5 |
| 126 | ledger-eventtickets-boardlimit | ledger/test_eventtickets_boardlimit.py | 7 | green | 0.4 |
| 127 | ledger-eventtickets-roll | ledger/test_eventtickets_roll.py | 7 | green | 0.3 |
| 128 | ledger-eventtickets-telescope | ledger/test_eventtickets_telescope.py | 6 | green | 0.2 |
| 129 | ledger-freetrial | ledger/test_freetrial.py | 7 | green | 0.4 |
| 130 | ledger-freetrial-funnel | ledger/test_freetrial_funnel.py | 7 | green | 0.4 |
| 131 | ledger-freetrial-funnelwin | ledger/test_freetrial_funnelwin.py | 7 | green | 0.3 |
| 132 | ledger-freetrial-callmonth | ledger/test_freetrial_callmonth.py | 7 | green | 0.4 |
| 133 | ledger-freetrial-callkind | ledger/test_freetrial_callkind.py | 8 | green | 0.4 |
| 134 | ledger-freetrial-callplan | ledger/test_freetrial_callplan.py | 8 | green | 0.4 |
| 135 | ledger-freetrial-callengine | ledger/test_freetrial_callengine.py | 8 | green | 0.5 |
| 136 | ledger-freetrial-callaccount | ledger/test_freetrial_callaccount.py | 8 | green | 0.3 |
| 137 | ledger-freetrial-capusage | ledger/test_freetrial_capusage.py | 8 | green | 0.5 |
| 138 | ledger-freetrial-caplimit | ledger/test_freetrial_caplimit.py | 7 | green | 0.4 |
| 139 | ledger-freetrial-caproll | ledger/test_freetrial_caproll.py | 7 | green | 0.4 |
| 140 | ledger-freetrial-callroll | ledger/test_freetrial_callroll.py | 7 | green | 0.6 |
| 141 | ledger-freetrial-funnelroll | ledger/test_freetrial_funnelroll.py | 7 | green | 0.4 |
| 142 | ledger-freetrial-funnelcap | ledger/test_freetrial_funnelcap.py | 7 | green | 0.6 |
| 143 | ledger-freetrial-funnelpersist | ledger/test_freetrial_funnelpersist.py | 7 | green | 0.4 |
| 144 | ledger-freetrial-cappersist | ledger/test_freetrial_cappersist.py | 8 | green | 0.5 |
| 145 | ledger-freetrial-fivepersist | ledger/test_freetrial_fivepersist.py | 7 | green | 0.4 |
| 146 | ugc-pool-water | ugc/test_pool_water.py | 7 | green | 0.6 |
| 147 | ugc-pool-delta | ugc/test_pool_delta.py | 7 | green | 0.8 |
| 148 | ugc-ingest-waterwire | ugc/test_ingest_waterwire.py | 6 | green | 0.4 |
| 149 | ugc-batch-water | ugc/test_batch_waterwire.py | 6 | green | 0.5 |
| 150 | ugc-drain-water | ugc/test_drain_waterwire.py | 6 | green | 0.5 |
| 151 | ugc-submit-water | ugc/test_submit_waterwire.py | 7 | green | 1.0 |
| 152 | ugc-verdict-water | ugc/test_verdict_waterwire.py | 7 | green | 1.1 |
| 153 | ugc-water-journal | ugc/test_water_journal.py | 7 | green | 0.8 |
| 154 | ugc-water-kindtally | ugc/test_water_kind_tally.py | 7 | green | 0.3 |
| 155 | ugc-water-monthlyflow | ugc/test_water_monthly_flow.py | 7 | green | 0.3 |
| 156 | ugc-water-journalwin | ugc/test_water_journal_window.py | 7 | green | 0.3 |
| 157 | ugc-water-journalcap | ugc/test_water_journal_limit.py | 7 | green | 0.3 |
| 158 | ugc-water-celltotals | ugc/test_water_cell_totals.py | 7 | green | 0.3 |
| 159 | member-expiring-dist | member/test_expiring_dist.py | 7 | green | 1.8 |
| 160 | ledger-apidev-lineage | ledger/test_apidev_lineage.py | 22 | green | 1.6 |
| 161 | ledger-apidev-chainusage | ledger/test_apidev_chainusage.py | 14 | green | 1.2 |
| 162 | ledger-apidev-devboard-roll | ledger/test_apidev_devboard_roll.py | 7 | green | 0.3 |
| 163 | ledger-apidev-devboard-limit | ledger/test_apidev_devboard_limit.py | 14 | green | 0.5 |
| 164 | ledger-apidev-devboard-ancestry | ledger/test_apidev_devboard_ancestry.py | 7 | green | 0.3 |
| 165 | ledger-apidev-keyviewwin | ledger/test_apidev_keyviewwin.py | 7 | green | 0.7 |
| 166 | ugc-water-journalroll | ugc/test_water_journal_roll.py | 7 | green | 1.7 |
| 167 | ugc-sec-batch-rowsroll | ugc/test_sec_batch_rowsroll.py | 7 | green | 2.6 |
| 168 | ledger-apidev-lineagepersist | ledger/test_apidev_lineagepersist.py | 7 | green | 0.5 |
| 169 | ledger-apidev-chainusagepersist | ledger/test_apidev_chainusagepersist.py | 7 | green | 1.6 |
| 170 | ledger-apidev-devboardpersist | ledger/test_apidev_devboardpersist.py | 7 | green | 1.1 |
| 171 | ledger-eventtickets-boardpersist | ledger/test_eventtickets_boardpersist.py | 7 | green | 0.6 |
| 172 | ledger-eventtickets-sessionpersist | ledger/test_eventtickets_sessionpersist.py | 7 | green | 0.8 |
| 173 | member-expiring-soon-persist | member/test_expiring_soon_persist.py | 7 | green | 3.0 |
| 174 | ledger-apidev-usagelogpersist | ledger/test_apidev_usagelogpersist.py | 7 | green | 1.8 |
| 175 | ugc-water-journalboardpersist | ugc/test_water_journal_boardpersist.py | 7 | green | 0.8 |
| 176 | ugc-water-sisterpersist | ugc/test_water_journal_sisterpersist.py | 12 | green | 0.5 |
| 177 | ledger-apidev-keyviewpersist | ledger/test_apidev_keyviewpersist.py | 7 | green | 2.7 |
| 178 | ledger-apidev-rejecttallpersist | ledger/test_apidev_rejecttallpersist.py | 7 | green | 1.2 |
| 179 | ledger-apidev-lifecycletracepersist | ledger/test_apidev_lifecycletracepersist.py | 7 | green | 3.2 |
| 180 | ledger-apidev-usagekindpersist | ledger/test_apidev_usagekindpersist.py | 7 | green | 1.9 |
| 181 | member-balanceface-persist | member/test_balance_face_persist.py | 7 | green | 1.1 |
| 182 | member-privileges-persist | member/test_privileges_persist.py | 7 | green | 0.8 |
| 183 | ugc-drain-waterpersist | ugc/test_drain_waterpersist.py | 7 | green | 0.8 |
| 184 | ugc-pool-waterpersist | ugc/test_pool_waterpersist.py | 7 | green | 0.7 |
| 185 | ugc-reviewdesk-persist | ugc/test_reviewdesk_persist.py | 7 | green | 0.7 |
| 186 | member-birthcert-persist | member/test_birthcert_persist.py | 7 | green | 0.7 |
| 187 | member-expiring-dist-persist | member/test_expiring_dist_persist.py | 7 | green | 0.8 |
| 188 | ugc-export-persist | ugc/test_export_persist.py | 7 | green | 0.8 |
| 189 | ledger-showcaseview-persist | ledger/test_showcase_persist.py | 7 | green | 0.9 |
| 190 | ledger-collectibles-persist | ledger/test_collectibles_persist.py | 7 | green | 1.1 |
| 191 | liveroom-persist | liveroom/test_liveroom_persist.py | 7 | green | 0.4 |
| 192 | tourstate-persist | tourstate/test_tourstate_persist.py | 7 | green | 1.1 |
| 193 | ledger-datasub-persist | ledger/test_datasub_persist.py | 7 | green | 0.4 |
| 194 | ledger-datasub-coverage | ledger/test_datasub_coverage.py | 7 | green | 0.6 |
| 195 | ledger-devshare-persist | ledger/test_devshare_persist.py | 7 | green | 1.0 |
| 196 | ledger-apimarket-persist | ledger/test_apimarket_persist.py | 7 | green | 0.6 |
| 197 | ledger-apimarket-devboard | ledger/test_apimarket_devboard.py | 7 | green | 0.9 |
| 198 | ledger-apimarket-devsalespersist | ledger/test_apimarket_devsalespersist.py | 7 | green | 0.6 |
| 199 | ledger-apimarket-devboardwindow | ledger/test_apimarket_devboardwindow.py | 7 | green | 0.8 |
| 200 | ledger-apimarket-devboardmonthpersist | ledger/test_apimarket_devboardmonthpersist.py | 7 | green | 0.8 |
| 201 | ledger-apimarket-devboardboundary | ledger/test_apimarket_devboardboundarypersist.py | 7 | green | 0.4 |
| 202 | ledger-apimarket-devboardgatepersist | ledger/test_apimarket_devboardgatepersist.py | 8 | green | 0.5 |
| 203 | ledger-apimarket-devboardmonthboundary | ledger/test_apimarket_devboardmonthboundarypersist.py | 7 | green | 0.5 |
| 204 | ledger-apimarket-devboardmonthstraddle | ledger/test_apimarket_devboardmonth_straddlepersist.py | 7 | green | 1.0 |
| 205 | ledger-apimarket-ratingagg | ledger/test_apimarket_ratingagg.py | 8 | green | 1.0 |
| 206 | ledger-apimarket-delist | ledger/test_apimarket_delist.py | 8 | green | 0.6 |
| 207 | ledger-apimarket-pricerev | ledger/test_apimarket_pricerev.py | 8 | green | 2.8 |
| 208 | ledger-apimarket-buyerlibrary | ledger/test_apimarket_library.py | 8 | green | 1.0 |
| 209 | ledger-apimarket-search | ledger/test_apimarket_search.py | 8 | green | 0.5 |
| 210 | ledger-apimarket-searchpaging | ledger/test_apimarket_searchpage.py | 8 | green | 0.8 |
| 211 | ledger-apimarket-searchsort | ledger/test_apimarket_searchsort.py | 8 | green | 0.8 |
| 212 | ledger-apimarket-devprofile | ledger/test_apimarket_devprofile.py | 8 | green | 0.7 |
| 213 | ledger-apimarket-metadata | ledger/test_apimarket_metadata.py | 8 | green | 0.6 |
| 214 | ledger-apimarket-watchlist | ledger/test_apimarket_watchlist.py | 8 | green | 0.5 |
| 215 | ledger-apimarket-supply | ledger/test_apimarket_supply.py | 8 | green | 1.4 |
| 216 | ledger-apimarket-refund | ledger/test_apimarket_refund.py | 8 | green | 1.2 |
| 217 | ledger-apimarket-relist | ledger/test_apimarket_relist.py | 8 | green | 1.0 |
| 218 | ledger-apimarket-marketstats | ledger/test_apimarket_marketstats.py | 8 | green | 1.1 |
| 219 | ledger-apimarket-buyerprofile | ledger/test_apimarket_buyerprofile.py | 8 | green | 0.6 |
| 220 | ledger-apimarket-ratreply | ledger/test_apimarket_ratingreply.py | 8 | green | 0.5 |
| 221 | ledger-apimarket-ratingrev | ledger/test_apimarket_ratingrev.py | 8 | green | 0.5 |
| 222 | ledger-apimarket-restock | ledger/test_apimarket_restock.py | 8 | green | 1.2 |
| 223 | ledger-apimarket-sellerinbox | ledger/test_apimarket_sellerinbox.py | 8 | green | 0.9 |
| 224 | ledger-apimarket-listingdemand | ledger/test_apimarket_listingdemand.py | 8 | green | 0.6 |
| 225 | ledger-apimarket-refundexposure | ledger/test_apimarket_refundexposure.py | 8 | green | 0.7 |
| 226 | ledger-apimarket-revenuemonths | ledger/test_apimarket_revenuemonths.py | 8 | green | 0.5 |
| 227 | ledger-apimarket-marketmonths | ledger/test_apimarket_marketmonths.py | 8 | green | 0.9 |
| 228 | ledger-apimarket-buyermonths | ledger/test_apimarket_buyermonths.py | 8 | green | 0.5 |
| 229 | ledger-apimarket-report | ledger/test_apimarket_report.py | 9 | green | 5.1 |
| 230 | ledger-apimarket-attention | ledger/test_apimarket_report_attention.py | 9 | green | 2.0 |
| 231 | ledger-apimarket-reportjson | ledger/test_apimarket_report_json.py | 8 | green | 3.1 |
| 232 | ledger-apimarket-reportworkbench | ledger/test_apimarket_report_workbench.py | 8 | green | 9.3 |
| 233 | ledger-apimarket-watchalerts | ledger/test_apimarket_watchalerts.py | 8 | green | 0.8 |
| 234 | ledger-apimarket-marketfeed | ledger/test_apimarket_marketfeed.py | 8 | green | 0.8 |
| 235 | ledger-apimarket-feedlisting | ledger/test_apimarket_marketfeed_listing.py | 8 | green | 1.8 |
| 236 | ledger-apimarket-activity | ledger/test_apimarket_report_activity.py | 8 | green | 38.8 |
| 237 | ledger-apimarket-reportdossier | ledger/test_apimarket_report_dossier.py | 8 | green | 127.2 |
| 238 | ledger-apimarket-buyerhistory | ledger/test_apimarket_report_buyerhistory.py | 8 | green | 208.7 |
| 239 | ledger-apimarket-refundregister | ledger/test_apimarket_report_refundregister.py | 8 | green | 140.0 |
| 240 | ledger-apimarket-buyertodo | ledger/test_apimarket_buyertodo.py | 8 | green | 1.0 |
| 241 | ledger-apimarket-reportdemand | ledger/test_apimarket_report_demand.py | 8 | green | 9.4 |
| 242 | ledger-apimarket-sellerquality | ledger/test_apimarket_sellerquality.py | 8 | green | 0.5 |
| 243 | ledger-apimarket-qna | ledger/test_apimarket_qna.py | 8 | green | 0.5 |
| 244 | ledger-apimarket-buyerquestions | ledger/test_apimarket_buyerquestions.py | 8 | green | 0.5 |
| 245 | ledger-apimarket-selleranswers | ledger/test_apimarket_selleranswers.py | 8 | green | 0.8 |
| 246 | ledger-apimarket-reportslowanswer | ledger/test_apimarket_report_slowanswer.py | 8 | green | 0.5 |
| 247 | os-decwatermark | ../os/test_dec_watermark.py | 8 | green | 7.3 |
| 248 | ledger-effects-persist | ledger/test_effects_persist.py | 7 | green | 1.0 |
| 249 | ledger-honorcert-persist | ledger/test_honorcert_persist.py | 7 | green | 0.7 |
| 250 | ledger-honorcert-yearbookpersist | ledger/test_honorcert_yearbook_persist.py | 6 | green | 0.4 |
| 251 | ledger-honorcert-multiyear | ledger/test_honorcert_multiyear.py | 7 | green | 0.3 |
| 252 | ledger-honorcert-yearbookspersist | ledger/test_honorcert_yearbooks_persist.py | 7 | green | 0.6 |
| 253 | ledger-honorcert-yearbooksubsetaxis | ledger/test_honorcert_yearbook_subsetaxis.py | 7 | green | 0.8 |
| 254 | ledger-honorcert-yearbook-zeroboundary | ledger/test_honorcert_yearbook_zeroboundarypersist.py | 7 | green | 0.4 |
| 255 | ledger-honorcert-yearbook-zeroboundarygate | ledger/test_honorcert_yearbook_zeroboundarygatepersist.py | 7 | green | 0.3 |
| 256 | ledger-honorcert-grantwidthworld | ledger/test_honorcert_grantwidthworld.py | 8 | green | 0.4 |
| 257 | liveroom-minorguard-persist | liveroom/test_liveroom_minorguard_persist.py | 8 | green | 0.4 |
| 258 | ledger-honorcert-grantgate-persist | ledger/test_honorcert_grantgatepersist.py | 7 | green | 0.7 |
| 259 | ledger-studio-persist | ledger/test_studio_persist.py | 7 | green | 0.4 |
| 260 | ledger-showroom-persist | ledger/test_showroom_persist.py | 7 | green | 0.5 |
| 261 | ledger-tmarket-persist | ledger/test_tmarket_persist.py | 7 | green | 0.4 |
| 262 | ledger-festival-persist | ledger/test_festival_persist.py | 7 | green | 0.3 |
| 263 | ledger-sistercity-persist | ledger/test_sistercity_persist.py | 7 | green | 0.5 |
| 264 | ledger-growth-archive-persist | ledger/test_growth_archive_persist.py | 7 | green | 0.3 |
| 265 | member-refund-recovery-persist | member/test_refund_recovery_persist.py | 7 | green | 0.8 |
| 266 | member-reminder-persist | member/test_reminder_persist.py | 7 | green | 1.1 |
| 267 | pay-reconcile-persist | pay/test_pay_reconcile_persist.py | 7 | green | 2.3 |
| 268 | pay-sweep-persist | pay/test_pay_sweep_persist.py | 7 | green | 0.9 |
| 269 | lobby-persist | lobby/test_lobby_persist.py | 7 | green | 0.2 |
| 270 | civic-behavior-distribution | ledger/test_civic_distribution.py | 6 | green | 0.4 |
| 271 | ledger-showcase-stats | ledger/test_showcase_stats.py | 7 | green | 0.8 |
| 272 | ledger-coverageboard-persist | ledger/test_coverage_board_persist.py | 7 | green | 0.4 |
| 273 | ledger-coverageboard-window | ledger/test_coverage_board_window.py | 7 | green | 0.3 |
| 274 | ledger-datasub-coveragedual | ledger/test_datasub_coveragedual.py | 7 | green | 0.6 |
| 275 | ledger-datasub-coveragedualpersist | ledger/test_datasub_coveragedualpersist.py | 7 | green | 0.4 |
| 276 | ledger-datasub-coveragemonthroll | ledger/test_datasub_coveragemonthroll.py | 7 | green | 0.5 |
| 277 | ledger-datasub-coveragegatepersist | ledger/test_datasub_coveragegatepersist.py | 8 | green | 0.3 |
| 278 | ledger-statsboard-persist | ledger/test_stats_board_persist.py | 7 | green | 0.5 |
| 279 | ledger-showcase-statslimit | ledger/test_showcase_statslimit.py | 7 | green | 0.4 |
| 280 | ledger-showcase-statsdual | ledger/test_showcase_statsdual.py | 7 | green | 0.3 |
| 281 | ledger-showcase-statsdual-persist | ledger/test_showcase_statsdualpersist.py | 7 | green | 0.6 |
| 282 | ledger-showcase-statscap-persist | ledger/test_showcase_statscappersist.py | 7 | green | 0.4 |
| 283 | ledger-showcase-statsboundary-persist | ledger/test_showcase_statsboundarypersist.py | 7 | green | 0.4 |
| 284 | ledger-showcase-statsgatepersist | ledger/test_showcase_statsgatepersist.py | 7 | green | 0.4 |
| 285 | ledger-showcase-viewwindow-gatepersist | ledger/test_showcase_viewwindow_gatepersist.py | 7 | green | 0.2 |
| 286 | ledger-showcase-viewwindow-persist | ledger/test_showcase_viewwindow_persist.py | 7 | green | 0.3 |
| 287 | ledger-showcase-viewwindow-replacepersist | ledger/test_showcase_viewwindow_replacepersist.py | 7 | green | 0.3 |
| 288 | ledger-proposal-progresspersist | ledger/test_proposal_progresspersist.py | 7 | green | 0.3 |
| 289 | civic-behavior-monthwindow | ledger/test_civic_monthwindow.py | 7 | green | 0.3 |
| 290 | civic-behavior-monthwindow-persist | ledger/test_civic_monthwindow_persist.py | 7 | green | 0.2 |
| 291 | civic-competition-monthwindow | ledger/test_civic_competition_monthwindow.py | 7 | green | 0.3 |
| 292 | civic-competition-monthwindow-persist | ledger/test_civic_competition_monthwindowpersist.py | 7 | green | 0.2 |
| 293 | ledger-proposal-progressboundary-persist | ledger/test_proposal_progressboundarypersist.py | 7 | green | 0.3 |
| 294 | ledger-showcase-statsmonth | ledger/test_showcase_statsmonth.py | 7 | green | 0.3 |
| 295 | ledger-showcase-statsmonth-persist | ledger/test_showcase_statsmonthpersist.py | 7 | green | 0.3 |
| 296 | ledger-showcase-statsmonthboundary-persist | ledger/test_showcase_statsmonthboundarypersist.py | 7 | green | 0.4 |
| 297 | ledger-showcase-statsmonthretract-persist | ledger/test_showcase_statsmonthretractpersist.py | 7 | green | 0.3 |
| 298 | ledger-showcase-statsmonthreplace-persist | ledger/test_showcase_statsmonthreplacepersist.py | 7 | green | 0.3 |
| 299 | ledger-showcase-statsmonth-rere-persist | ledger/test_showcase_statsmonthrerepersist.py | 7 | green | 0.4 |
| 300 | ledger-showcase-statsmonth-straddle-persist | ledger/test_showcase_statsmonthstraddlepersist.py | 7 | green | 0.5 |
| 301 | ledger-showcase-statsmonth-straddle2-persist | ledger/test_showcase_statsmonth_straddle2persist.py | 7 | green | 0.3 |
| 302 | ledger-showcase-statsmonth-straddle3-persist | ledger/test_showcase_statsmonth_straddle3persist.py | 7 | green | 0.5 |
| 303 | funnel | funnel/test_funnel_daily.py | 8 | green | 1.0 |
| 304 | funnel-cli-gates | funnel/test_funnel_cli_gates.py | 7 | green | 0.4 |
| 305 | funnel-persist | funnel/test_funnel_persist.py | 8 | green | 1.2 |
| 306 | funnel-rescan | funnel/test_funnel_rescan.py | 8 | green | 1.9 |
| 307 | funnel-rerollup | funnel/test_funnel_rerollup.py | 8 | green | 2.0 |
| 308 | funnel-conservation | funnel/test_funnel_conservation.py | 8 | green | 2.1 |
| 309 | funnel-account | funnel/test_funnel_account.py | 8 | green | 1.3 |
| 310 | funnel-sku | funnel/test_funnel_sku.py | 8 | green | 1.1 |
| 311 | funnel-route | funnel/test_funnel_route.py | 8 | green | 1.4 |
| 312 | funnel-cli-chain | funnel/test_funnel_cli_chain.py | 8 | green | 7.6 |
| 313 | funnel-inbox | funnel/test_funnel_inbox.py | 8 | green | 1.0 |
| 314 | funnel-sku-persist | funnel/test_funnel_sku_persist.py | 8 | green | 1.3 |
| 315 | funnel-sku-top | funnel/test_funnel_sku_top.py | 8 | green | 1.3 |
| 316 | funnel-route-persist | funnel/test_funnel_route_persist.py | 8 | green | 0.5 |
| 317 | funnel-sku-gate | funnel/test_funnel_sku_gate.py | 8 | green | 0.9 |
| 318 | funnel-evidence-rotate | funnel/test_funnel_evidence_rotate.py | 8 | green | 1.6 |
| 319 | funnel-cli-env | funnel/test_funnel_cli_env.py | 8 | green | 3.6 |
| 320 | funnel-sku-top-rank | funnel/test_funnel_sku_top_rank.py | 8 | green | 1.1 |
| 321 | ledger-proposal-gatepersist | ledger/test_proposal_gatepersist.py | 7 | green | 0.4 |
| 322 | ledger-proposal-gateboundary-persist | ledger/test_proposal_gateboundarypersist.py | 7 | green | 0.4 |
| 323 | ledger-proposal-signbadargs-persist | ledger/test_proposal_signbadargspersist.py | 7 | green | 0.4 |
| 324 | ledger-proposal-signbadargs-loadedpersist | ledger/test_proposal_signbadargspersist_loaded.py | 7 | green | 0.3 |
| 325 | lobby-chat-mute-idem | lobby/test_chatmute_idem.py | 8 | green | 0.5 |
| 326 | os-evidence-writer | ../os/test_evidence_writer.py | 8 | green | 1.2 |
|  | 合计 |  | 2716 | green 326 / FAIL 0 / no-evidence 0 |  |

## 证据出处

- reconcile-all-R2121.log (qa/reconcile-all-R2121.log)
- 状态列解析自上述证据 log 的 suite 行（exit 码）与 RUNNER 终态行；证据中缺失的套件记 no-evidence（不捏造）。判据数为预注册口径，源自套件注册表。
