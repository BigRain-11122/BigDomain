-- BigDomain token double-entry ledger sandbox schema (P-47-2b).
-- Source of truth: docs/spec/token-ledger-spec.md section 2; acceptance
-- criteria AC-L1..AC-L11 were pre-registered there before this file existed.
-- Storage discipline: one SQLite DB in this repo, WAL mode, single writer
-- (same as the lobby event store).
-- Structural bans (BLUEPRINT section 5.4, double insurance): no withdraw,
-- no transfer-out, no fiat field, no exchange/out verb exists anywhere in
-- this schema. Tokens are pure in-loop consumption credits.
-- Extra implementation columns beyond the spec DDL (documented deltas):
--   ledger_tx.action   grant classification; key for cap/gate checks (AC-L7/L8)
--   ledger_tx.closed   tx completion flag; trigger T2 turns closing into the
--                     DB-side double-entry gate (spec: "app validates first,
--                     triggers as the fallback" for AC-L1)

CREATE TABLE IF NOT EXISTS ledger_accounts (
  account_id       TEXT PRIMARY KEY,            -- 'usr:<avatar_id>' | 'pool:reserve' | 'pool:reward' | 'pool:share' | 'equity:auth'
  census_avatar_id TEXT UNIQUE,                 -- usr:* only: census avatar binding (AC-L11), reference not copy
  balance          INTEGER NOT NULL DEFAULT 0,  -- sign law: usr/pool >= 0, equity:auth <= 0 (trigger T1, AC-L2)
  status           TEXT NOT NULL DEFAULT 'active',
  created_utc      TEXT NOT NULL
);

-- Gate-pass receipts (AC-L8): sandbox stand-in for the lobby gate pipeline
-- product; only 'pass' rows are ever inserted here.
CREATE TABLE IF NOT EXISTS gate_events (
  evt_id      TEXT PRIMARY KEY,
  gate        TEXT NOT NULL DEFAULT 'pass',
  checked_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ledger_tx (
  tx_id     TEXT PRIMARY KEY,                   -- content-addressed: sha256 six-field core + entries digest (AC-L3)
  type      TEXT NOT NULL CHECK (type IN ('mint','spend','share','adjust')),
  action    TEXT NOT NULL DEFAULT '',           -- mint/spend/reward-classification/manual key
  ref       TEXT NOT NULL,                      -- source reference (evt_id / order id / settlement id)
  ref_type  TEXT NOT NULL CHECK (ref_type IN ('event','order','settlement','manual')),
  source_ai INTEGER NOT NULL DEFAULT 0,         -- AI-adjudicated marker, server-authoritative (AC-L9)
  memo      TEXT,                               -- adjust requires an approval memo (reconcile names every adjust line)
  closed    INTEGER NOT NULL DEFAULT 0,        -- 0 = open, 1 = booked; T2 validates on close
  ts_utc    TEXT NOT NULL,
  UNIQUE (ref, ref_type)                        -- AC-L4 source idempotence
);

CREATE TABLE IF NOT EXISTS ledger_entries (
  entry_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  tx_id      TEXT NOT NULL REFERENCES ledger_tx(tx_id),
  account_id TEXT NOT NULL REFERENCES ledger_accounts(account_id),
  direction  TEXT NOT NULL CHECK (direction IN ('debit','credit')),
  amount     INTEGER NOT NULL CHECK (amount > 0),
  ts_utc     TEXT NOT NULL
);

-- T0: entries may only attach to an open tx (closed txs are immutable books).
CREATE TRIGGER IF NOT EXISTS trg_entries_open_tx
BEFORE INSERT ON ledger_entries
WHEN (SELECT closed FROM ledger_tx WHERE tx_id = NEW.tx_id) = 1
BEGIN
  SELECT RAISE(ABORT, 'E_TX_CLOSED');
END;

-- T1: balance sync + sign law (AC-L2). Credit adds, debit subtracts for every
-- account; equity:* must stay <= 0 (mint counterparty stays negative), all
-- other accounts must stay >= 0 (no overdraft anywhere, whole tx refused).
CREATE TRIGGER IF NOT EXISTS trg_entry_balance
AFTER INSERT ON ledger_entries
BEGIN
  UPDATE ledger_accounts
     SET balance = balance + CASE WHEN NEW.direction = 'credit' THEN NEW.amount ELSE -NEW.amount END
   WHERE account_id = NEW.account_id;
  SELECT RAISE(ABORT, 'E_NEGATIVE_BALANCE')
   WHERE EXISTS (SELECT 1 FROM ledger_accounts
                  WHERE account_id = NEW.account_id
                    AND ((account_id LIKE 'equity:%' AND balance > 0)
                      OR (account_id NOT LIKE 'equity:%' AND balance < 0)));
END;

-- T2: tx close gate (AC-L1 DB-side fallback): a booked tx needs >= 2 entries
-- and debit sum = credit sum, otherwise the close (and the whole tx) aborts.
CREATE TRIGGER IF NOT EXISTS trg_tx_close
AFTER UPDATE OF closed ON ledger_tx
WHEN NEW.closed = 1
BEGIN
  SELECT RAISE(ABORT, 'E_TX_MIN_ENTRIES')
   WHERE (SELECT COUNT(*) FROM ledger_entries WHERE tx_id = NEW.tx_id) < 2;
  SELECT RAISE(ABORT, 'E_TX_IMBALANCE')
   WHERE (SELECT COALESCE(SUM(CASE WHEN direction = 'debit' THEN amount ELSE 0 END), 0)
               - COALESCE(SUM(CASE WHEN direction = 'credit' THEN amount ELSE 0 END), 0)
          FROM ledger_entries WHERE tx_id = NEW.tx_id) <> 0;
END;

-- T3: booked (closed) txs are immutable: ref/type/amounts locked once booked.
CREATE TRIGGER IF NOT EXISTS trg_tx_immutable
BEFORE UPDATE ON ledger_tx
WHEN OLD.closed = 1
BEGIN
  SELECT RAISE(ABORT, 'E_TX_IMMUTABLE');
END;

-- V1: materialized vs derived balances (AC-L5; reconcile cross-check view).
CREATE VIEW IF NOT EXISTS v_derived_balance AS
SELECT a.account_id,
       a.balance AS materialized,
       COALESCE(SUM(CASE WHEN e.direction = 'credit' THEN e.amount ELSE -e.amount END), 0) AS derived
  FROM ledger_accounts a
  LEFT JOIN ledger_entries e ON e.account_id = a.account_id
 GROUP BY a.account_id;
