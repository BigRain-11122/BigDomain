// Supplementary transport test (added 2026-10-08 after AC-YG6a root-cause):
// the y-websocket wire envelope, which is what yserve v1.22.0 actually
// implements per its server package docs (docName = URL path segment; bare
// message tags 0=Sync / 1=Awareness / 3=QueryAwareness; no docName prefix).
// AC-YG6c: two JS clients converge live through the yserve binary.
// AC-YG6d: state persists across a yserve process restart (sqlite).
import * as Y from 'yjs'
import * as encoding from 'lib0/encoding'
import * as decoding from 'lib0/decoding'
import * as syncProtocol from 'y-protocols/sync'

const BASE = 'ws://127.0.0.1:1987'
const ROOM = 'poc-room-1'

// Bounded watchdog, same policy as client-yserve.mjs.
setTimeout(() => {
  console.log('FAIL hard-timeout: no sync within 20s')
  process.exit(1)
}, 20000)

const until = async (fn, ms) => {
  const t0 = Date.now()
  while (Date.now() - t0 < ms) {
    if (fn()) return true
    await new Promise((r) => setTimeout(r, 50))
  }
  return fn()
}

// Minimal y-websocket-protocol client: tag 0 = sync step1/step2/update.
const connect = (doc) => {
  const ws = new WebSocket(`${BASE}/${ROOM}`)
  ws.binaryType = 'arraybuffer'
  const state = { ws, synced: false }
  ws.onopen = () => {
    const enc = encoding.createEncoder()
    encoding.writeVarUint(enc, 0)
    syncProtocol.writeSyncStep1(enc, doc)
    ws.send(encoding.toUint8Array(enc))
  }
  ws.onmessage = (ev) => {
    if (process.env.YWS_DEBUG) console.log('[dbg] frame bytes:', Array.from(new Uint8Array(ev.data)).map((b) => b.toString(16).padStart(2, '0')).join(' '))
    const dec = decoding.createDecoder(new Uint8Array(ev.data))
    const tag = decoding.readVarUint(dec)
    if (process.env.YWS_DEBUG) console.log('[dbg] tag:', tag)
    if (tag !== 0) return // Sync only in this PoC
    const reply = encoding.createEncoder()
    let smt
    try {
      smt = syncProtocol.readSyncMessage(dec, reply, doc, ws)
    } catch (err) {
      console.log('FAIL sync read error from server frame:', err.message)
      process.exit(1)
    }
    if (process.env.YWS_DEBUG) console.log('[dbg] smt:', smt, 'synced->', state.synced)
    if (smt === syncProtocol.messageYjsSyncStep2) state.synced = true
    if (encoding.length(reply) > 1) ws.send(encoding.toUint8Array(reply))
  }
  doc.on('update', (update, origin) => {
    if (process.env.YWS_DEBUG) console.log('[dbg] local update origin=', origin === ws ? 'echo-skip' : String(origin), 'readyState=', ws.readyState)
    if (origin === ws || ws.readyState !== 1) return
    const enc = encoding.createEncoder()
    encoding.writeVarUint(enc, 0)
    syncProtocol.writeUpdate(enc, update) // writes messageYjsUpdate tag + length-prefixed payload
    ws.send(encoding.toUint8Array(enc))
    if (process.env.YWS_DEBUG) console.log('[dbg] update sent, len=', update.length)
  })
  return state
}

const phase = process.argv[2]
if (phase === 'phase1') {
  const d1 = new Y.Doc()
  const c1 = connect(d1)
  const d2 = new Y.Doc()
  const c2 = connect(d2)
  const s1 = await until(() => c1.synced, 5000)
  const s2 = await until(() => c2.synced, 5000)
  if (process.env.YWS_DEBUG) console.log('[dbg] s1=', s1, 's2=', s2)
  d1.getMap('settings').set('msg', 'hello-from-c1')
  d1.getText('canvas').insert(0, 'c1-was-here')
  const ok = s1 && s2 && await until(() =>
    d2.getMap('settings').get('msg') === 'hello-from-c1' &&
    d2.getText('canvas').toString() === 'c1-was-here', 5000)
  console.log(ok
    ? 'PASS AC-YG6c two-client live convergence via yserve (y-websocket envelope)'
    : 'FAIL AC-YG6c convergence failed (y-websocket envelope)')
  c1.ws.close(); c2.ws.close()
  process.exit(ok ? 0 : 1)
} else if (phase === 'phase2') {
  const d3 = new Y.Doc()
  const c3 = connect(d3)
  const s3 = await until(() => c3.synced, 5000)
  const ok = s3 &&
    d3.getMap('settings').get('msg') === 'hello-from-c1' &&
    d3.getText('canvas').toString() === 'c1-was-here'
  console.log(ok
    ? 'PASS AC-YG6d state persisted across yserve restart (sqlite)'
    : 'FAIL AC-YG6d persistence lost')
  c3.ws.close()
  process.exit(ok ? 0 : 1)
} else {
  console.log('usage: node client-yws.mjs phase1|phase2')
  process.exit(2)
}
