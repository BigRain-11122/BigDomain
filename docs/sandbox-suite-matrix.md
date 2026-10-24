<!-- 机器派生文件：由 src/sandbox/suite_matrix.py 生成，勿手改（改=下轮 --check 漂移 exit 2）。再生命令见文档头「生成命令」行 -->
# 沙箱套件矩阵（对账可计费可见面）

- 生成时间: generated: 2026-10-24 13:57 +08:00
- 生成命令: python src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R2082.log
- 状态证据: reconcile-all-R2082.log (RUNNER PASS 288/288 suites green, reconcile controls 7/7, 290.1s)
- 回应: C-20261009-02「实质停摆零可计费」批评——本矩阵为机器派生的对账可计费可见面：套件注册表源自 reconcile_all.py 单一事实源，可计费面源自五域 config.json 单一事实源，逐套件状态源自最近全量回归证据 log，零手写数字。

## 汇总

| 套件数 | 判据总数 | 证据全绿 | 证据轮 |
|---|---|---|---|
| 288 | 2410 | 288/288 | R2082 |

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
| 1 | lobby | lobby/test_client.py | 79 | green | 42.7 |
| 2 | ledger | ledger/test_ledger.py | 11 | green | 0.4 |
| 3 | ledger-props | ledger/test_props.py | 7 | green | 0.1 |
| 4 | ledger-props-persist | ledger/test_props_persist.py | 7 | green | 0.2 |
| 5 | ledger-identity-persist | ledger/test_identity_persist.py | 7 | green | 0.2 |
| 6 | ledger-incentive | ledger/test_incentive.py | 7 | green | 0.2 |
| 7 | ledger-settlement | ledger/test_settlement.py | 7 | green | 0.1 |
| 8 | ledger-settlement-persist | ledger/test_settlement_persist.py | 7 | green | 0.2 |
| 9 | ledger-venue | ledger/test_venue.py | 7 | green | 0.2 |
| 10 | ledger-venue-persist | ledger/test_venue_persist.py | 7 | green | 0.3 |
| 11 | ledger-collectibles | ledger/test_collectibles.py | 7 | green | 0.1 |
| 12 | ledger-expedite | ledger/test_expedite.py | 7 | green | 0.2 |
| 13 | ledger-expedite-persist | ledger/test_expedite_persist.py | 7 | green | 0.2 |
| 14 | ledger-ads | ledger/test_ads.py | 7 | green | 0.2 |
| 15 | ledger-ads-persist | ledger/test_ads_persist.py | 7 | green | 0.2 |
| 16 | ledger-observation | ledger/test_observation.py | 7 | green | 0.2 |
| 17 | ledger-observation-persist | ledger/test_observation_persist.py | 7 | green | 0.2 |
| 18 | ledger-identity | ledger/test_identity.py | 7 | green | 0.2 |
| 19 | ledger-studio | ledger/test_studio.py | 7 | green | 0.2 |
| 20 | ledger-metered | ledger/test_metered.py | 7 | green | 0.1 |
| 21 | ledger-metered-persist | ledger/test_metered_persist.py | 7 | green | 0.2 |
| 22 | ledger-reports | ledger/test_reports.py | 7 | green | 0.1 |
| 23 | ledger-reports-persist | ledger/test_reports_persist.py | 7 | green | 0.2 |
| 24 | ledger-effects | ledger/test_effects.py | 7 | green | 0.1 |
| 25 | ledger-growth-archive | ledger/test_growth_archive.py | 7 | green | 0.2 |
| 26 | ledger-companion | ledger/test_companion.py | 7 | green | 0.1 |
| 27 | ledger-companion-persist | ledger/test_companion_persist.py | 7 | green | 0.2 |
| 28 | ledger-tmarket | ledger/test_tmarket.py | 7 | green | 0.2 |
| 29 | ledger-festival | ledger/test_festival.py | 7 | green | 0.2 |
| 30 | ledger-showroom | ledger/test_showroom.py | 7 | green | 0.2 |
| 31 | ledger-sistercity | ledger/test_sistercity.py | 7 | green | 0.2 |
| 32 | ledger-apidev | ledger/test_apidev.py | 7 | green | 0.2 |
| 33 | ledger-apidev-lifecycle | ledger/test_apidev_lifecycle.py | 8 | green | 0.3 |
| 34 | ledger-apidev-rate | ledger/test_apidev_rate.py | 7 | green | 0.2 |
| 35 | ledger-apidev-reject | ledger/test_apidev_reject.py | 7 | green | 0.2 |
| 36 | ledger-apidev-usagelog | ledger/test_apidev_usagelog.py | 7 | green | 0.5 |
| 37 | ledger-apidev-rejectwin | ledger/test_apidev_rejectwin.py | 7 | green | 0.2 |
| 38 | ledger-apidev-usagewin | ledger/test_apidev_usagewin.py | 8 | green | 0.2 |
| 39 | ledger-apidev-usagekind | ledger/test_apidev_usagekind.py | 8 | green | 0.2 |
| 40 | ledger-apidev-lifecycletrace | ledger/test_apidev_lifecycle_trace.py | 14 | green | 0.2 |
| 41 | tourstate | tourstate/test_tourstate.py | 7 | green | 0.1 |
| 42 | ugc | ugc/test_ugc.py | 37 | green | 5.3 |
| 43 | ugc-sec-batch | ugc/test_sec_batch.py | 22 | green | 0.3 |
| 44 | ugc-sec-batch-roll | ugc/test_sec_batch_roll.py | 7 | green | 0.2 |
| 45 | ugc-sec-batch-bannerpersist | ugc/test_sec_batch_bannerpersist.py | 7 | green | 0.2 |
| 46 | ugc-sec-batch-rowpersist | ugc/test_sec_batch_rowpersist.py | 7 | green | 0.2 |
| 47 | pay | pay/test_pay.py | 16 | green | 1.3 |
| 48 | pay-v3 | pay/test_pay_v3.py | 14 | green | 0.2 |
| 49 | pay-v3-real | pay/test_pay_v3_real.py | 9 | green | 0.4 |
| 50 | pay-v3-window | pay/test_pay_v3_window.py | 6 | green | 0.4 |
| 51 | pay-notify | pay/test_pay_notify.py | 7 | green | 0.3 |
| 52 | pay-notify-bannerlimit | pay/test_pay_notify_bannerlimit.py | 8 | green | 0.2 |
| 53 | pay-notify-bannerwin | pay/test_pay_notify_bannerwin.py | 7 | green | 0.3 |
| 54 | pay-notify-bannerroll | pay/test_pay_notify_bannerroll.py | 7 | green | 0.5 |
| 55 | pay-notify-bannerpersist | pay/test_pay_notify_bannerpersist.py | 7 | green | 0.2 |
| 56 | pay-authorize-persist | pay/test_authorize_persist.py | 7 | green | 0.3 |
| 57 | pay-authorize-idem | pay/test_authorize_idem.py | 7 | green | 1.5 |
| 58 | pay-notify-wiring | pay/test_pay_notify_wiring.py | 7 | green | 0.9 |
| 59 | pay-authorize | pay/test_authorize.py | 7 | green | 0.3 |
| 60 | pay-notify-revoke | pay/test_notify_revoke.py | 7 | green | 5.2 |
| 61 | pay-revoke-reconcile | pay/test_pay_revoke_recon.py | 7 | green | 1.3 |
| 62 | pay-channel-matrix | pay/test_channel_matrix.py | 7 | green | 0.7 |
| 63 | pay-channel-window | pay/test_channel_window.py | 7 | green | 0.7 |
| 64 | pay-channel-persist | pay/test_channel_persist.py | 7 | green | 0.3 |
| 65 | pay-channel-migrate-persist | pay/test_channel_migrate_persist.py | 5 | green | 0.3 |
| 66 | ledger-clawback | pay/test_clawback_wiring.py | 8 | green | 1.4 |
| 67 | ledger-clawback-persist | pay/test_clawback_persist.py | 7 | green | 0.4 |
| 68 | member | member/test_member.py | 16 | green | 1.8 |
| 69 | member-entry | member/test_entry_tier.py | 7 | green | 0.1 |
| 70 | member-entrytier-persist | member/test_entry_tier_persist.py | 7 | green | 0.3 |
| 71 | member-refund-recovery | member/test_refund_recovery.py | 7 | green | 1.4 |
| 72 | member-expiring | member/test_expiring_soon.py | 7 | green | 1.1 |
| 73 | member-reminder-scanwire | member/test_reminder_scan_wire.py | 7 | green | 0.5 |
| 74 | member-banner-board | member/test_banner_board.py | 17 | green | 0.6 |
| 75 | member-banner-roll | member/test_banner_board_roll.py | 7 | green | 0.3 |
| 76 | member-banner-queue-window | member/test_banner_queue_window.py | 7 | green | 0.3 |
| 77 | member-banner-queue-limit | member/test_banner_queue_limit.py | 8 | green | 0.3 |
| 78 | member-banner-queue-caproll | member/test_banner_queue_caproll.py | 7 | green | 0.3 |
| 79 | member-banner-queue-persist | member/test_banner_queue_persist.py | 7 | green | 0.3 |
| 80 | member-banner-board-persist | member/test_banner_board_persist.py | 7 | green | 0.5 |
| 81 | watermark | watermark/test_watermark.py | 5 | green | 1.8 |
| 82 | watermark-robust | watermark/test_watermark_robust.py | 6 | green | 2.8 |
| 83 | watermark-sweep | watermark/test_watermark_sweep.py | 6 | green | 28.2 |
| 84 | watermark-scale-recover | watermark/test_scale_recover.py | 7 | green | 12.6 |
| 85 | watermark-scale-unknown | watermark/test_scale_unknown.py | 6 | green | 19.7 |
| 86 | watermark-scale-refine | watermark/test_scale_refine.py | 6 | green | 22.9 |
| 87 | dual-track | watermark/test_dual_track.py | 7 | green | 1.6 |
| 88 | watermark-bindbit | watermark/test_bind_bit.py | 7 | green | 4.6 |
| 89 | watermark-dualbit | watermark/test_dual_bit.py | 7 | green | 3.8 |
| 90 | opsreview | opsreview/test_opsreview.py | 7 | green | 1.4 |
| 91 | liveroom | liveroom/test_liveroom.py | 10 | green | 0.3 |
| 92 | benchgate | benchgate/test_bench_gate.py | 11 | green | 0.2 |
| 93 | citymodel | citymodel/test_scenario.py | 10 | green | 0.4 |
| 94 | compliance | compliance/test_sku_compliance_map.py | 15 | green | 0.2 |
| 95 | minors | minors/test_minors.py | 19 | green | 0.1 |
| 96 | minors-wiring | minors/test_wiring.py | 70 | green | 12.6 |
| 97 | minors-persist | minors/test_minors_persist.py | 7 | green | 0.3 |
| 98 | schema-migrate | test_schema_migrate.py | 21 | green | 8.6 |
| 99 | fingerprint-regen | test_fingerprint_regen.py | 16 | green | 7.6 |
| 100 | reconcile-daily-sentinel | test_reconcile_daily_sentinel.py | 8 | green | 0.6 |
| 101 | suite-matrix-discovery | test_suite_matrix.py | 16 | green | 0.7 |
| 102 | runner-profile-daily | test_runner_profile_daily.py | 12 | green | 0.1 |
| 103 | reconcile-daily-profile | test_reconcile_daily_profile.py | 7 | green | 0.3 |
| 104 | reconcile-daily-census | test_reconcile_daily_census.py | 8 | green | 0.8 |
| 105 | ledger-showcase | ledger/test_showcase.py | 7 | green | 0.3 |
| 106 | ledger-curation | ledger/test_curation.py | 24 | green | 0.3 |
| 107 | ledger-curation-hotpersist | ledger/test_curation_hotpersist.py | 6 | green | 0.2 |
| 108 | ledger-curation-coldpersist | ledger/test_curation_coldpersist.py | 6 | green | 1.0 |
| 109 | ledger-curation-combined | ledger/test_curation_combined.py | 7 | green | 0.2 |
| 110 | ledger-curation-combinedpersist | ledger/test_curation_combinedpersist.py | 6 | green | 0.2 |
| 111 | ledger-curation-combinedboundary | ledger/test_curation_combinedboundary.py | 6 | green | 0.4 |
| 112 | ledger-curation-combinedmonth | ledger/test_curation_combinedmonth.py | 7 | green | 0.3 |
| 113 | ledger-curation-regpersist | ledger/test_curation_regpersist.py | 7 | green | 0.2 |
| 114 | ledger-civicpoints | ledger/test_civicpoints.py | 20 | green | 0.2 |
| 115 | ledger-honorcert | ledger/test_honorcert.py | 7 | green | 0.3 |
| 116 | ledger-honorcert-yearbook | ledger/test_honorcert_yearbook.py | 7 | green | 0.2 |
| 117 | ledger-civicpersist | ledger/test_civic_persist.py | 7 | green | 0.1 |
| 118 | ledger-devshare | ledger/test_devshare.py | 7 | green | 0.2 |
| 119 | ledger-apimarket | ledger/test_apimarket.py | 7 | green | 0.9 |
| 120 | ledger-datasub | ledger/test_datasub.py | 7 | green | 0.2 |
| 121 | ledger-proposal | ledger/test_proposal.py | 12 | green | 0.4 |
| 122 | ledger-proposal-persist | ledger/test_proposal_persist.py | 7 | green | 0.2 |
| 123 | ledger-incentive-persist | ledger/test_incentive_persist.py | 7 | green | 0.2 |
| 124 | ledger-eventtickets | ledger/test_eventtickets.py | 14 | green | 0.2 |
| 125 | ledger-eventtickets-boardwin | ledger/test_eventtickets_boardwin.py | 7 | green | 0.3 |
| 126 | ledger-eventtickets-boardlimit | ledger/test_eventtickets_boardlimit.py | 7 | green | 0.4 |
| 127 | ledger-eventtickets-roll | ledger/test_eventtickets_roll.py | 7 | green | 0.2 |
| 128 | ledger-eventtickets-telescope | ledger/test_eventtickets_telescope.py | 6 | green | 0.2 |
| 129 | ledger-freetrial | ledger/test_freetrial.py | 7 | green | 0.3 |
| 130 | ledger-freetrial-funnel | ledger/test_freetrial_funnel.py | 7 | green | 0.2 |
| 131 | ledger-freetrial-funnelwin | ledger/test_freetrial_funnelwin.py | 7 | green | 0.2 |
| 132 | ledger-freetrial-callmonth | ledger/test_freetrial_callmonth.py | 7 | green | 0.2 |
| 133 | ledger-freetrial-callkind | ledger/test_freetrial_callkind.py | 8 | green | 0.3 |
| 134 | ledger-freetrial-callplan | ledger/test_freetrial_callplan.py | 8 | green | 0.2 |
| 135 | ledger-freetrial-callengine | ledger/test_freetrial_callengine.py | 8 | green | 0.2 |
| 136 | ledger-freetrial-callaccount | ledger/test_freetrial_callaccount.py | 8 | green | 0.2 |
| 137 | ledger-freetrial-capusage | ledger/test_freetrial_capusage.py | 8 | green | 0.2 |
| 138 | ledger-freetrial-caplimit | ledger/test_freetrial_caplimit.py | 7 | green | 0.3 |
| 139 | ledger-freetrial-caproll | ledger/test_freetrial_caproll.py | 7 | green | 0.2 |
| 140 | ledger-freetrial-callroll | ledger/test_freetrial_callroll.py | 7 | green | 0.2 |
| 141 | ledger-freetrial-funnelroll | ledger/test_freetrial_funnelroll.py | 7 | green | 0.2 |
| 142 | ledger-freetrial-funnelcap | ledger/test_freetrial_funnelcap.py | 7 | green | 0.3 |
| 143 | ledger-freetrial-funnelpersist | ledger/test_freetrial_funnelpersist.py | 7 | green | 0.2 |
| 144 | ledger-freetrial-cappersist | ledger/test_freetrial_cappersist.py | 8 | green | 0.2 |
| 145 | ledger-freetrial-fivepersist | ledger/test_freetrial_fivepersist.py | 7 | green | 0.3 |
| 146 | ugc-pool-water | ugc/test_pool_water.py | 7 | green | 0.9 |
| 147 | ugc-pool-delta | ugc/test_pool_delta.py | 7 | green | 0.4 |
| 148 | ugc-ingest-waterwire | ugc/test_ingest_waterwire.py | 6 | green | 0.3 |
| 149 | ugc-batch-water | ugc/test_batch_waterwire.py | 6 | green | 0.3 |
| 150 | ugc-drain-water | ugc/test_drain_waterwire.py | 6 | green | 0.3 |
| 151 | ugc-submit-water | ugc/test_submit_waterwire.py | 7 | green | 1.0 |
| 152 | ugc-verdict-water | ugc/test_verdict_waterwire.py | 7 | green | 0.5 |
| 153 | ugc-water-journal | ugc/test_water_journal.py | 7 | green | 0.5 |
| 154 | ugc-water-kindtally | ugc/test_water_kind_tally.py | 7 | green | 0.2 |
| 155 | ugc-water-monthlyflow | ugc/test_water_monthly_flow.py | 7 | green | 0.2 |
| 156 | ugc-water-journalwin | ugc/test_water_journal_window.py | 7 | green | 0.1 |
| 157 | ugc-water-journalcap | ugc/test_water_journal_limit.py | 7 | green | 0.2 |
| 158 | ugc-water-celltotals | ugc/test_water_cell_totals.py | 7 | green | 0.2 |
| 159 | member-expiring-dist | member/test_expiring_dist.py | 7 | green | 0.4 |
| 160 | ledger-apidev-lineage | ledger/test_apidev_lineage.py | 22 | green | 0.3 |
| 161 | ledger-apidev-chainusage | ledger/test_apidev_chainusage.py | 14 | green | 0.3 |
| 162 | ledger-apidev-devboard-roll | ledger/test_apidev_devboard_roll.py | 7 | green | 0.2 |
| 163 | ledger-apidev-devboard-limit | ledger/test_apidev_devboard_limit.py | 14 | green | 0.7 |
| 164 | ledger-apidev-devboard-ancestry | ledger/test_apidev_devboard_ancestry.py | 7 | green | 0.2 |
| 165 | ledger-apidev-keyviewwin | ledger/test_apidev_keyviewwin.py | 7 | green | 0.2 |
| 166 | ugc-water-journalroll | ugc/test_water_journal_roll.py | 7 | green | 0.1 |
| 167 | ugc-sec-batch-rowsroll | ugc/test_sec_batch_rowsroll.py | 7 | green | 0.4 |
| 168 | ledger-apidev-lineagepersist | ledger/test_apidev_lineagepersist.py | 7 | green | 0.2 |
| 169 | ledger-apidev-chainusagepersist | ledger/test_apidev_chainusagepersist.py | 7 | green | 0.2 |
| 170 | ledger-apidev-devboardpersist | ledger/test_apidev_devboardpersist.py | 7 | green | 0.7 |
| 171 | ledger-eventtickets-boardpersist | ledger/test_eventtickets_boardpersist.py | 7 | green | 0.4 |
| 172 | ledger-eventtickets-sessionpersist | ledger/test_eventtickets_sessionpersist.py | 7 | green | 0.2 |
| 173 | member-expiring-soon-persist | member/test_expiring_soon_persist.py | 7 | green | 0.3 |
| 174 | ledger-apidev-usagelogpersist | ledger/test_apidev_usagelogpersist.py | 7 | green | 0.2 |
| 175 | ugc-water-journalboardpersist | ugc/test_water_journal_boardpersist.py | 7 | green | 0.1 |
| 176 | ugc-water-sisterpersist | ugc/test_water_journal_sisterpersist.py | 12 | green | 0.2 |
| 177 | ledger-apidev-keyviewpersist | ledger/test_apidev_keyviewpersist.py | 7 | green | 0.2 |
| 178 | ledger-apidev-rejecttallpersist | ledger/test_apidev_rejecttallpersist.py | 7 | green | 0.2 |
| 179 | ledger-apidev-lifecycletracepersist | ledger/test_apidev_lifecycletracepersist.py | 7 | green | 0.2 |
| 180 | ledger-apidev-usagekindpersist | ledger/test_apidev_usagekindpersist.py | 7 | green | 0.2 |
| 181 | member-balanceface-persist | member/test_balance_face_persist.py | 7 | green | 0.6 |
| 182 | member-privileges-persist | member/test_privileges_persist.py | 7 | green | 0.3 |
| 183 | ugc-drain-waterpersist | ugc/test_drain_waterpersist.py | 7 | green | 0.5 |
| 184 | ugc-pool-waterpersist | ugc/test_pool_waterpersist.py | 7 | green | 0.3 |
| 185 | ugc-reviewdesk-persist | ugc/test_reviewdesk_persist.py | 7 | green | 0.5 |
| 186 | member-birthcert-persist | member/test_birthcert_persist.py | 7 | green | 0.3 |
| 187 | member-expiring-dist-persist | member/test_expiring_dist_persist.py | 7 | green | 0.3 |
| 188 | ugc-export-persist | ugc/test_export_persist.py | 7 | green | 0.5 |
| 189 | ledger-showcaseview-persist | ledger/test_showcase_persist.py | 7 | green | 0.2 |
| 190 | ledger-collectibles-persist | ledger/test_collectibles_persist.py | 7 | green | 0.2 |
| 191 | liveroom-persist | liveroom/test_liveroom_persist.py | 7 | green | 0.2 |
| 192 | tourstate-persist | tourstate/test_tourstate_persist.py | 7 | green | 0.9 |
| 193 | ledger-datasub-persist | ledger/test_datasub_persist.py | 7 | green | 0.2 |
| 194 | ledger-datasub-coverage | ledger/test_datasub_coverage.py | 7 | green | 0.2 |
| 195 | ledger-devshare-persist | ledger/test_devshare_persist.py | 7 | green | 0.3 |
| 196 | ledger-apimarket-persist | ledger/test_apimarket_persist.py | 7 | green | 0.7 |
| 197 | ledger-apimarket-devboard | ledger/test_apimarket_devboard.py | 7 | green | 0.3 |
| 198 | ledger-apimarket-devsalespersist | ledger/test_apimarket_devsalespersist.py | 7 | green | 0.3 |
| 199 | ledger-apimarket-devboardwindow | ledger/test_apimarket_devboardwindow.py | 7 | green | 0.3 |
| 200 | ledger-apimarket-devboardmonthpersist | ledger/test_apimarket_devboardmonthpersist.py | 7 | green | 0.3 |
| 201 | ledger-apimarket-devboardboundary | ledger/test_apimarket_devboardboundarypersist.py | 7 | green | 0.3 |
| 202 | ledger-apimarket-devboardgatepersist | ledger/test_apimarket_devboardgatepersist.py | 8 | green | 0.3 |
| 203 | ledger-apimarket-devboardmonthboundary | ledger/test_apimarket_devboardmonthboundarypersist.py | 7 | green | 0.3 |
| 204 | ledger-apimarket-devboardmonthstraddle | ledger/test_apimarket_devboardmonth_straddlepersist.py | 7 | green | 0.3 |
| 205 | ledger-apimarket-ratingagg | ledger/test_apimarket_ratingagg.py | 8 | green | 0.3 |
| 206 | ledger-apimarket-delist | ledger/test_apimarket_delist.py | 8 | green | 0.2 |
| 207 | ledger-apimarket-pricerev | ledger/test_apimarket_pricerev.py | 8 | green | 0.2 |
| 208 | ledger-apimarket-buyerlibrary | ledger/test_apimarket_library.py | 8 | green | 0.9 |
| 209 | ledger-apimarket-search | ledger/test_apimarket_search.py | 8 | green | 0.2 |
| 210 | ledger-effects-persist | ledger/test_effects_persist.py | 7 | green | 0.2 |
| 211 | ledger-honorcert-persist | ledger/test_honorcert_persist.py | 7 | green | 0.2 |
| 212 | ledger-honorcert-yearbookpersist | ledger/test_honorcert_yearbook_persist.py | 6 | green | 0.4 |
| 213 | ledger-honorcert-multiyear | ledger/test_honorcert_multiyear.py | 7 | green | 0.2 |
| 214 | ledger-honorcert-yearbookspersist | ledger/test_honorcert_yearbooks_persist.py | 7 | green | 0.2 |
| 215 | ledger-honorcert-yearbooksubsetaxis | ledger/test_honorcert_yearbook_subsetaxis.py | 7 | green | 0.2 |
| 216 | ledger-honorcert-yearbook-zeroboundary | ledger/test_honorcert_yearbook_zeroboundarypersist.py | 7 | green | 0.2 |
| 217 | ledger-honorcert-yearbook-zeroboundarygate | ledger/test_honorcert_yearbook_zeroboundarygatepersist.py | 7 | green | 0.2 |
| 218 | ledger-honorcert-grantwidthworld | ledger/test_honorcert_grantwidthworld.py | 8 | green | 0.2 |
| 219 | liveroom-minorguard-persist | liveroom/test_liveroom_minorguard_persist.py | 8 | green | 0.2 |
| 220 | ledger-honorcert-grantgate-persist | ledger/test_honorcert_grantgatepersist.py | 7 | green | 0.3 |
| 221 | ledger-studio-persist | ledger/test_studio_persist.py | 7 | green | 0.2 |
| 222 | ledger-showroom-persist | ledger/test_showroom_persist.py | 7 | green | 0.2 |
| 223 | ledger-tmarket-persist | ledger/test_tmarket_persist.py | 7 | green | 0.6 |
| 224 | ledger-festival-persist | ledger/test_festival_persist.py | 7 | green | 0.2 |
| 225 | ledger-sistercity-persist | ledger/test_sistercity_persist.py | 7 | green | 0.2 |
| 226 | ledger-growth-archive-persist | ledger/test_growth_archive_persist.py | 7 | green | 0.2 |
| 227 | member-refund-recovery-persist | member/test_refund_recovery_persist.py | 7 | green | 0.3 |
| 228 | member-reminder-persist | member/test_reminder_persist.py | 7 | green | 0.3 |
| 229 | pay-reconcile-persist | pay/test_pay_reconcile_persist.py | 7 | green | 1.4 |
| 230 | pay-sweep-persist | pay/test_pay_sweep_persist.py | 7 | green | 0.2 |
| 231 | lobby-persist | lobby/test_lobby_persist.py | 7 | green | 0.1 |
| 232 | civic-behavior-distribution | ledger/test_civic_distribution.py | 6 | green | 0.2 |
| 233 | ledger-showcase-stats | ledger/test_showcase_stats.py | 7 | green | 0.2 |
| 234 | ledger-coverageboard-persist | ledger/test_coverage_board_persist.py | 7 | green | 0.2 |
| 235 | ledger-coverageboard-window | ledger/test_coverage_board_window.py | 7 | green | 0.2 |
| 236 | ledger-datasub-coveragedual | ledger/test_datasub_coveragedual.py | 7 | green | 0.3 |
| 237 | ledger-datasub-coveragedualpersist | ledger/test_datasub_coveragedualpersist.py | 7 | green | 0.2 |
| 238 | ledger-datasub-coveragemonthroll | ledger/test_datasub_coveragemonthroll.py | 7 | green | 0.2 |
| 239 | ledger-datasub-coveragegatepersist | ledger/test_datasub_coveragegatepersist.py | 8 | green | 0.2 |
| 240 | ledger-statsboard-persist | ledger/test_stats_board_persist.py | 7 | green | 0.2 |
| 241 | ledger-showcase-statslimit | ledger/test_showcase_statslimit.py | 7 | green | 0.3 |
| 242 | ledger-showcase-statsdual | ledger/test_showcase_statsdual.py | 7 | green | 0.2 |
| 243 | ledger-showcase-statsdual-persist | ledger/test_showcase_statsdualpersist.py | 7 | green | 0.2 |
| 244 | ledger-showcase-statscap-persist | ledger/test_showcase_statscappersist.py | 7 | green | 0.2 |
| 245 | ledger-showcase-statsboundary-persist | ledger/test_showcase_statsboundarypersist.py | 7 | green | 0.2 |
| 246 | ledger-showcase-statsgatepersist | ledger/test_showcase_statsgatepersist.py | 7 | green | 0.2 |
| 247 | ledger-showcase-viewwindow-gatepersist | ledger/test_showcase_viewwindow_gatepersist.py | 7 | green | 0.2 |
| 248 | ledger-showcase-viewwindow-persist | ledger/test_showcase_viewwindow_persist.py | 7 | green | 0.2 |
| 249 | ledger-showcase-viewwindow-replacepersist | ledger/test_showcase_viewwindow_replacepersist.py | 7 | green | 0.2 |
| 250 | ledger-proposal-progresspersist | ledger/test_proposal_progresspersist.py | 7 | green | 0.2 |
| 251 | civic-behavior-monthwindow | ledger/test_civic_monthwindow.py | 7 | green | 0.4 |
| 252 | civic-behavior-monthwindow-persist | ledger/test_civic_monthwindow_persist.py | 7 | green | 0.1 |
| 253 | civic-competition-monthwindow | ledger/test_civic_competition_monthwindow.py | 7 | green | 0.2 |
| 254 | civic-competition-monthwindow-persist | ledger/test_civic_competition_monthwindowpersist.py | 7 | green | 0.1 |
| 255 | ledger-proposal-progressboundary-persist | ledger/test_proposal_progressboundarypersist.py | 7 | green | 0.2 |
| 256 | ledger-showcase-statsmonth | ledger/test_showcase_statsmonth.py | 7 | green | 0.2 |
| 257 | ledger-showcase-statsmonth-persist | ledger/test_showcase_statsmonthpersist.py | 7 | green | 0.2 |
| 258 | ledger-showcase-statsmonthboundary-persist | ledger/test_showcase_statsmonthboundarypersist.py | 7 | green | 0.2 |
| 259 | ledger-showcase-statsmonthretract-persist | ledger/test_showcase_statsmonthretractpersist.py | 7 | green | 0.2 |
| 260 | ledger-showcase-statsmonthreplace-persist | ledger/test_showcase_statsmonthreplacepersist.py | 7 | green | 0.2 |
| 261 | ledger-showcase-statsmonth-rere-persist | ledger/test_showcase_statsmonthrerepersist.py | 7 | green | 0.3 |
| 262 | ledger-showcase-statsmonth-straddle-persist | ledger/test_showcase_statsmonthstraddlepersist.py | 7 | green | 0.2 |
| 263 | ledger-showcase-statsmonth-straddle2-persist | ledger/test_showcase_statsmonth_straddle2persist.py | 7 | green | 0.2 |
| 264 | ledger-showcase-statsmonth-straddle3-persist | ledger/test_showcase_statsmonth_straddle3persist.py | 7 | green | 0.2 |
| 265 | funnel | funnel/test_funnel_daily.py | 8 | green | 0.5 |
| 266 | funnel-cli-gates | funnel/test_funnel_cli_gates.py | 7 | green | 0.2 |
| 267 | funnel-persist | funnel/test_funnel_persist.py | 8 | green | 0.5 |
| 268 | funnel-rescan | funnel/test_funnel_rescan.py | 8 | green | 1.0 |
| 269 | funnel-rerollup | funnel/test_funnel_rerollup.py | 8 | green | 1.7 |
| 270 | funnel-conservation | funnel/test_funnel_conservation.py | 8 | green | 1.8 |
| 271 | funnel-account | funnel/test_funnel_account.py | 8 | green | 1.0 |
| 272 | funnel-sku | funnel/test_funnel_sku.py | 8 | green | 1.0 |
| 273 | funnel-route | funnel/test_funnel_route.py | 8 | green | 1.4 |
| 274 | funnel-cli-chain | funnel/test_funnel_cli_chain.py | 8 | green | 6.3 |
| 275 | funnel-inbox | funnel/test_funnel_inbox.py | 8 | green | 1.0 |
| 276 | funnel-sku-persist | funnel/test_funnel_sku_persist.py | 8 | green | 1.2 |
| 277 | funnel-sku-top | funnel/test_funnel_sku_top.py | 8 | green | 1.1 |
| 278 | funnel-route-persist | funnel/test_funnel_route_persist.py | 8 | green | 0.4 |
| 279 | funnel-sku-gate | funnel/test_funnel_sku_gate.py | 8 | green | 0.8 |
| 280 | funnel-evidence-rotate | funnel/test_funnel_evidence_rotate.py | 8 | green | 1.3 |
| 281 | funnel-cli-env | funnel/test_funnel_cli_env.py | 8 | green | 3.0 |
| 282 | funnel-sku-top-rank | funnel/test_funnel_sku_top_rank.py | 8 | green | 1.1 |
| 283 | ledger-proposal-gatepersist | ledger/test_proposal_gatepersist.py | 7 | green | 0.6 |
| 284 | ledger-proposal-gateboundary-persist | ledger/test_proposal_gateboundarypersist.py | 7 | green | 0.4 |
| 285 | ledger-proposal-signbadargs-persist | ledger/test_proposal_signbadargspersist.py | 7 | green | 0.5 |
| 286 | ledger-proposal-signbadargs-loadedpersist | ledger/test_proposal_signbadargspersist_loaded.py | 7 | green | 0.5 |
| 287 | lobby-chat-mute-idem | lobby/test_chatmute_idem.py | 8 | green | 0.5 |
| 288 | os-evidence-writer | ../os/test_evidence_writer.py | 8 | green | 1.1 |
|  | 合计 |  | 2410 | green 288 / FAIL 0 / no-evidence 0 |  |

## 证据出处

- reconcile-all-R2082.log (qa/reconcile-all-R2082.log)
- 状态列解析自上述证据 log 的 suite 行（exit 码）与 RUNNER 终态行；证据中缺失的套件记 no-evidence（不捏造）。判据数为预注册口径，源自套件注册表。
