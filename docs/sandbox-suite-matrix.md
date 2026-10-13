<!-- 机器派生文件：由 src/sandbox/suite_matrix.py 生成，勿手改（改=下轮 --check 漂移 exit 2）。再生命令见文档头「生成命令」行 -->
# 沙箱套件矩阵（对账可计费可见面）

- 生成时间: generated: 2026-10-14 02:52 +08:00
- 生成命令: python src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R1938.log
- 状态证据: reconcile-all-R1938.log (RUNNER PASS 176/176 suites green, reconcile controls 7/7, 211.8s)
- 回应: C-20261009-02「实质停摆零可计费」批评——本矩阵为机器派生的对账可计费可见面：套件注册表源自 reconcile_all.py 单一事实源，可计费面源自五域 config.json 单一事实源，逐套件状态源自最近全量回归证据 log，零手写数字。

## 汇总

| 套件数 | 判据总数 | 证据全绿 | 证据轮 |
|---|---|---|---|
| 176 | 1571 | 176/176 | R1938 |

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
| 1 | lobby | lobby/test_client.py | 57 | green | 34.1 |
| 2 | ledger | ledger/test_ledger.py | 11 | green | 0.5 |
| 3 | ledger-props | ledger/test_props.py | 7 | green | 0.2 |
| 4 | ledger-incentive | ledger/test_incentive.py | 7 | green | 0.2 |
| 5 | ledger-settlement | ledger/test_settlement.py | 7 | green | 0.1 |
| 6 | ledger-venue | ledger/test_venue.py | 7 | green | 0.2 |
| 7 | ledger-venue-persist | ledger/test_venue_persist.py | 7 | green | 0.3 |
| 8 | ledger-collectibles | ledger/test_collectibles.py | 7 | green | 0.2 |
| 9 | ledger-expedite | ledger/test_expedite.py | 7 | green | 0.3 |
| 10 | ledger-expedite-persist | ledger/test_expedite_persist.py | 7 | green | 0.2 |
| 11 | ledger-ads | ledger/test_ads.py | 7 | green | 0.2 |
| 12 | ledger-observation | ledger/test_observation.py | 7 | green | 0.2 |
| 13 | ledger-observation-persist | ledger/test_observation_persist.py | 7 | green | 0.3 |
| 14 | ledger-identity | ledger/test_identity.py | 7 | green | 0.2 |
| 15 | ledger-studio | ledger/test_studio.py | 7 | green | 0.2 |
| 16 | ledger-metered | ledger/test_metered.py | 7 | green | 0.2 |
| 17 | ledger-reports | ledger/test_reports.py | 7 | green | 0.4 |
| 18 | ledger-effects | ledger/test_effects.py | 7 | green | 0.2 |
| 19 | ledger-growth-archive | ledger/test_growth_archive.py | 7 | green | 0.2 |
| 20 | ledger-companion | ledger/test_companion.py | 7 | green | 0.5 |
| 21 | ledger-tmarket | ledger/test_tmarket.py | 7 | green | 0.2 |
| 22 | ledger-festival | ledger/test_festival.py | 7 | green | 0.2 |
| 23 | ledger-showroom | ledger/test_showroom.py | 7 | green | 0.3 |
| 24 | ledger-sistercity | ledger/test_sistercity.py | 7 | green | 0.3 |
| 25 | ledger-apidev | ledger/test_apidev.py | 7 | green | 0.3 |
| 26 | ledger-apidev-lifecycle | ledger/test_apidev_lifecycle.py | 8 | green | 0.3 |
| 27 | ledger-apidev-rate | ledger/test_apidev_rate.py | 7 | green | 0.5 |
| 28 | ledger-apidev-reject | ledger/test_apidev_reject.py | 7 | green | 0.3 |
| 29 | ledger-apidev-usagelog | ledger/test_apidev_usagelog.py | 7 | green | 0.3 |
| 30 | ledger-apidev-rejectwin | ledger/test_apidev_rejectwin.py | 7 | green | 0.3 |
| 31 | ledger-apidev-usagewin | ledger/test_apidev_usagewin.py | 8 | green | 0.3 |
| 32 | ledger-apidev-usagekind | ledger/test_apidev_usagekind.py | 8 | green | 0.3 |
| 33 | ledger-apidev-lifecycletrace | ledger/test_apidev_lifecycle_trace.py | 14 | green | 0.3 |
| 34 | tourstate | tourstate/test_tourstate.py | 7 | green | 0.1 |
| 35 | ugc | ugc/test_ugc.py | 37 | green | 4.4 |
| 36 | ugc-sec-batch | ugc/test_sec_batch.py | 22 | green | 0.3 |
| 37 | ugc-sec-batch-roll | ugc/test_sec_batch_roll.py | 7 | green | 0.2 |
| 38 | ugc-sec-batch-bannerpersist | ugc/test_sec_batch_bannerpersist.py | 7 | green | 0.2 |
| 39 | ugc-sec-batch-rowpersist | ugc/test_sec_batch_rowpersist.py | 7 | green | 0.2 |
| 40 | pay | pay/test_pay.py | 16 | green | 2.1 |
| 41 | pay-v3 | pay/test_pay_v3.py | 14 | green | 0.3 |
| 42 | pay-v3-real | pay/test_pay_v3_real.py | 9 | green | 0.5 |
| 43 | pay-v3-window | pay/test_pay_v3_window.py | 6 | green | 0.4 |
| 44 | pay-notify | pay/test_pay_notify.py | 7 | green | 0.5 |
| 45 | pay-notify-bannerlimit | pay/test_pay_notify_bannerlimit.py | 8 | green | 0.3 |
| 46 | pay-notify-bannerwin | pay/test_pay_notify_bannerwin.py | 7 | green | 0.3 |
| 47 | pay-notify-bannerroll | pay/test_pay_notify_bannerroll.py | 7 | green | 0.3 |
| 48 | pay-notify-bannerpersist | pay/test_pay_notify_bannerpersist.py | 7 | green | 0.3 |
| 49 | pay-authorize-persist | pay/test_authorize_persist.py | 7 | green | 0.3 |
| 50 | pay-authorize-idem | pay/test_authorize_idem.py | 7 | green | 1.5 |
| 51 | pay-notify-wiring | pay/test_pay_notify_wiring.py | 7 | green | 1.4 |
| 52 | pay-authorize | pay/test_authorize.py | 7 | green | 0.5 |
| 53 | pay-notify-revoke | pay/test_notify_revoke.py | 7 | green | 5.5 |
| 54 | pay-revoke-reconcile | pay/test_pay_revoke_recon.py | 7 | green | 0.8 |
| 55 | pay-channel-matrix | pay/test_channel_matrix.py | 7 | green | 0.6 |
| 56 | pay-channel-window | pay/test_channel_window.py | 7 | green | 0.9 |
| 57 | pay-channel-persist | pay/test_channel_persist.py | 7 | green | 0.3 |
| 58 | pay-channel-migrate-persist | pay/test_channel_migrate_persist.py | 5 | green | 0.6 |
| 59 | ledger-clawback | pay/test_clawback_wiring.py | 8 | green | 1.3 |
| 60 | member | member/test_member.py | 16 | green | 1.4 |
| 61 | member-entry | member/test_entry_tier.py | 7 | green | 0.1 |
| 62 | member-entrytier-persist | member/test_entry_tier_persist.py | 7 | green | 0.3 |
| 63 | member-refund-recovery | member/test_refund_recovery.py | 7 | green | 0.9 |
| 64 | member-expiring | member/test_expiring_soon.py | 7 | green | 0.8 |
| 65 | member-reminder-scanwire | member/test_reminder_scan_wire.py | 7 | green | 0.3 |
| 66 | member-banner-board | member/test_banner_board.py | 17 | green | 0.8 |
| 67 | member-banner-roll | member/test_banner_board_roll.py | 7 | green | 0.2 |
| 68 | member-banner-queue-window | member/test_banner_queue_window.py | 7 | green | 0.2 |
| 69 | member-banner-queue-limit | member/test_banner_queue_limit.py | 8 | green | 0.2 |
| 70 | member-banner-queue-caproll | member/test_banner_queue_caproll.py | 7 | green | 0.2 |
| 71 | member-banner-queue-persist | member/test_banner_queue_persist.py | 7 | green | 0.2 |
| 72 | member-banner-board-persist | member/test_banner_board_persist.py | 7 | green | 0.2 |
| 73 | watermark | watermark/test_watermark.py | 5 | green | 1.6 |
| 74 | watermark-robust | watermark/test_watermark_robust.py | 6 | green | 2.0 |
| 75 | watermark-sweep | watermark/test_watermark_sweep.py | 6 | green | 23.0 |
| 76 | watermark-scale-recover | watermark/test_scale_recover.py | 7 | green | 7.5 |
| 77 | watermark-scale-unknown | watermark/test_scale_unknown.py | 6 | green | 12.7 |
| 78 | watermark-scale-refine | watermark/test_scale_refine.py | 6 | green | 19.3 |
| 79 | dual-track | watermark/test_dual_track.py | 7 | green | 1.4 |
| 80 | watermark-bindbit | watermark/test_bind_bit.py | 7 | green | 3.6 |
| 81 | watermark-dualbit | watermark/test_dual_bit.py | 7 | green | 2.8 |
| 82 | opsreview | opsreview/test_opsreview.py | 7 | green | 1.0 |
| 83 | liveroom | liveroom/test_liveroom.py | 10 | green | 0.3 |
| 84 | benchgate | benchgate/test_bench_gate.py | 11 | green | 0.2 |
| 85 | citymodel | citymodel/test_scenario.py | 10 | green | 0.2 |
| 86 | compliance | compliance/test_sku_compliance_map.py | 15 | green | 0.1 |
| 87 | minors | minors/test_minors.py | 19 | green | 0.1 |
| 88 | minors-wiring | minors/test_wiring.py | 70 | green | 14.5 |
| 89 | schema-migrate | test_schema_migrate.py | 21 | green | 5.0 |
| 90 | fingerprint-regen | test_fingerprint_regen.py | 16 | green | 3.6 |
| 91 | reconcile-daily-sentinel | test_reconcile_daily_sentinel.py | 8 | green | 0.5 |
| 92 | suite-matrix-discovery | test_suite_matrix.py | 16 | green | 0.8 |
| 93 | runner-profile-daily | test_runner_profile_daily.py | 12 | green | 0.2 |
| 94 | reconcile-daily-profile | test_reconcile_daily_profile.py | 7 | green | 0.4 |
| 95 | reconcile-daily-census | test_reconcile_daily_census.py | 8 | green | 10.8 |
| 96 | ledger-showcase | ledger/test_showcase.py | 7 | green | 0.2 |
| 97 | ledger-curation | ledger/test_curation.py | 19 | green | 0.4 |
| 98 | ledger-curation-hotpersist | ledger/test_curation_hotpersist.py | 6 | green | 0.3 |
| 99 | ledger-curation-regpersist | ledger/test_curation_regpersist.py | 7 | green | 0.2 |
| 100 | ledger-civicpoints | ledger/test_civicpoints.py | 20 | green | 0.2 |
| 101 | ledger-honorcert | ledger/test_honorcert.py | 7 | green | 0.3 |
| 102 | ledger-civicpersist | ledger/test_civic_persist.py | 7 | green | 0.2 |
| 103 | ledger-devshare | ledger/test_devshare.py | 7 | green | 0.4 |
| 104 | ledger-apimarket | ledger/test_apimarket.py | 7 | green | 0.3 |
| 105 | ledger-datasub | ledger/test_datasub.py | 7 | green | 0.2 |
| 106 | ledger-proposal | ledger/test_proposal.py | 7 | green | 0.3 |
| 107 | ledger-eventtickets | ledger/test_eventtickets.py | 14 | green | 0.3 |
| 108 | ledger-eventtickets-boardwin | ledger/test_eventtickets_boardwin.py | 7 | green | 0.2 |
| 109 | ledger-eventtickets-boardlimit | ledger/test_eventtickets_boardlimit.py | 7 | green | 0.2 |
| 110 | ledger-eventtickets-roll | ledger/test_eventtickets_roll.py | 7 | green | 0.2 |
| 111 | ledger-eventtickets-telescope | ledger/test_eventtickets_telescope.py | 6 | green | 0.2 |
| 112 | ledger-freetrial | ledger/test_freetrial.py | 7 | green | 0.3 |
| 113 | ledger-freetrial-funnel | ledger/test_freetrial_funnel.py | 7 | green | 0.2 |
| 114 | ledger-freetrial-funnelwin | ledger/test_freetrial_funnelwin.py | 7 | green | 0.3 |
| 115 | ledger-freetrial-callmonth | ledger/test_freetrial_callmonth.py | 7 | green | 0.2 |
| 116 | ledger-freetrial-callkind | ledger/test_freetrial_callkind.py | 8 | green | 0.2 |
| 117 | ledger-freetrial-callplan | ledger/test_freetrial_callplan.py | 8 | green | 0.2 |
| 118 | ledger-freetrial-callengine | ledger/test_freetrial_callengine.py | 8 | green | 0.3 |
| 119 | ledger-freetrial-callaccount | ledger/test_freetrial_callaccount.py | 8 | green | 0.4 |
| 120 | ledger-freetrial-capusage | ledger/test_freetrial_capusage.py | 8 | green | 0.3 |
| 121 | ledger-freetrial-caplimit | ledger/test_freetrial_caplimit.py | 7 | green | 0.2 |
| 122 | ledger-freetrial-caproll | ledger/test_freetrial_caproll.py | 7 | green | 0.2 |
| 123 | ledger-freetrial-callroll | ledger/test_freetrial_callroll.py | 7 | green | 0.2 |
| 124 | ledger-freetrial-funnelroll | ledger/test_freetrial_funnelroll.py | 7 | green | 0.3 |
| 125 | ledger-freetrial-funnelcap | ledger/test_freetrial_funnelcap.py | 7 | green | 0.3 |
| 126 | ledger-freetrial-funnelpersist | ledger/test_freetrial_funnelpersist.py | 7 | green | 0.3 |
| 127 | ledger-freetrial-cappersist | ledger/test_freetrial_cappersist.py | 8 | green | 0.3 |
| 128 | ledger-freetrial-fivepersist | ledger/test_freetrial_fivepersist.py | 7 | green | 0.3 |
| 129 | ugc-pool-water | ugc/test_pool_water.py | 7 | green | 0.4 |
| 130 | ugc-pool-delta | ugc/test_pool_delta.py | 7 | green | 0.5 |
| 131 | ugc-ingest-waterwire | ugc/test_ingest_waterwire.py | 6 | green | 0.4 |
| 132 | ugc-batch-water | ugc/test_batch_waterwire.py | 6 | green | 0.4 |
| 133 | ugc-drain-water | ugc/test_drain_waterwire.py | 6 | green | 0.4 |
| 134 | ugc-submit-water | ugc/test_submit_waterwire.py | 7 | green | 0.5 |
| 135 | ugc-verdict-water | ugc/test_verdict_waterwire.py | 7 | green | 0.5 |
| 136 | ugc-water-journal | ugc/test_water_journal.py | 7 | green | 0.7 |
| 137 | ugc-water-kindtally | ugc/test_water_kind_tally.py | 7 | green | 0.2 |
| 138 | ugc-water-monthlyflow | ugc/test_water_monthly_flow.py | 7 | green | 0.2 |
| 139 | ugc-water-journalwin | ugc/test_water_journal_window.py | 7 | green | 0.2 |
| 140 | ugc-water-journalcap | ugc/test_water_journal_limit.py | 7 | green | 0.2 |
| 141 | ugc-water-celltotals | ugc/test_water_cell_totals.py | 7 | green | 0.2 |
| 142 | member-expiring-dist | member/test_expiring_dist.py | 7 | green | 0.5 |
| 143 | ledger-apidev-lineage | ledger/test_apidev_lineage.py | 22 | green | 0.3 |
| 144 | ledger-apidev-chainusage | ledger/test_apidev_chainusage.py | 14 | green | 0.3 |
| 145 | ledger-apidev-devboard-roll | ledger/test_apidev_devboard_roll.py | 7 | green | 0.2 |
| 146 | ledger-apidev-devboard-limit | ledger/test_apidev_devboard_limit.py | 14 | green | 0.3 |
| 147 | ledger-apidev-devboard-ancestry | ledger/test_apidev_devboard_ancestry.py | 7 | green | 0.2 |
| 148 | ledger-apidev-keyviewwin | ledger/test_apidev_keyviewwin.py | 7 | green | 0.2 |
| 149 | ugc-water-journalroll | ugc/test_water_journal_roll.py | 7 | green | 0.2 |
| 150 | ugc-sec-batch-rowsroll | ugc/test_sec_batch_rowsroll.py | 7 | green | 0.2 |
| 151 | ledger-apidev-lineagepersist | ledger/test_apidev_lineagepersist.py | 7 | green | 0.3 |
| 152 | ledger-apidev-chainusagepersist | ledger/test_apidev_chainusagepersist.py | 7 | green | 0.3 |
| 153 | ledger-apidev-devboardpersist | ledger/test_apidev_devboardpersist.py | 7 | green | 0.3 |
| 154 | ledger-eventtickets-boardpersist | ledger/test_eventtickets_boardpersist.py | 7 | green | 0.2 |
| 155 | ledger-eventtickets-sessionpersist | ledger/test_eventtickets_sessionpersist.py | 7 | green | 0.2 |
| 156 | member-expiring-soon-persist | member/test_expiring_soon_persist.py | 7 | green | 0.3 |
| 157 | ledger-apidev-usagelogpersist | ledger/test_apidev_usagelogpersist.py | 7 | green | 0.3 |
| 158 | ugc-water-journalboardpersist | ugc/test_water_journal_boardpersist.py | 7 | green | 0.2 |
| 159 | ugc-water-sisterpersist | ugc/test_water_journal_sisterpersist.py | 12 | green | 0.2 |
| 160 | ledger-apidev-keyviewpersist | ledger/test_apidev_keyviewpersist.py | 7 | green | 0.3 |
| 161 | ledger-apidev-rejecttallpersist | ledger/test_apidev_rejecttallpersist.py | 7 | green | 0.3 |
| 162 | ledger-apidev-lifecycletracepersist | ledger/test_apidev_lifecycletracepersist.py | 7 | green | 0.3 |
| 163 | ledger-apidev-usagekindpersist | ledger/test_apidev_usagekindpersist.py | 7 | green | 0.3 |
| 164 | member-balanceface-persist | member/test_balance_face_persist.py | 7 | green | 0.3 |
| 165 | member-privileges-persist | member/test_privileges_persist.py | 7 | green | 0.4 |
| 166 | ugc-drain-waterpersist | ugc/test_drain_waterpersist.py | 7 | green | 0.7 |
| 167 | ugc-pool-waterpersist | ugc/test_pool_waterpersist.py | 7 | green | 0.5 |
| 168 | ugc-reviewdesk-persist | ugc/test_reviewdesk_persist.py | 7 | green | 0.8 |
| 169 | member-birthcert-persist | member/test_birthcert_persist.py | 7 | green | 0.5 |
| 170 | member-expiring-dist-persist | member/test_expiring_dist_persist.py | 7 | green | 0.4 |
| 171 | ugc-export-persist | ugc/test_export_persist.py | 7 | green | 0.8 |
| 172 | ledger-showcaseview-persist | ledger/test_showcase_persist.py | 7 | green | 0.5 |
| 173 | ledger-collectibles-persist | ledger/test_collectibles_persist.py | 7 | green | 0.2 |
| 174 | liveroom-persist | liveroom/test_liveroom_persist.py | 7 | green | 0.3 |
| 175 | tourstate-persist | tourstate/test_tourstate_persist.py | 7 | green | 0.9 |
| 176 | ledger-datasub-persist | ledger/test_datasub_persist.py | 7 | green | 0.3 |
|  | 合计 |  | 1571 | green 176 / FAIL 0 / no-evidence 0 |  |

## 证据出处

- reconcile-all-R1938.log (qa/reconcile-all-R1938.log)
- 状态列解析自上述证据 log 的 suite 行（exit 码）与 RUNNER 终态行；证据中缺失的套件记 no-evidence（不捏造）。判据数为预注册口径，源自套件注册表。
