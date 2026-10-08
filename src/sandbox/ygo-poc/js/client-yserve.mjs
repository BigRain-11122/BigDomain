// yserve transport test: two yjs clients converge live through the ygo
// single-binary Hocuspocus-compatible server; phase2 checks sqlite
// persistence across a server process restart.
import * as Y from 'yjs'
import { HocuspocusProvider } from '@hocuspocus/provider'

const url = 'ws://127.0.0.1:1987'
const room = 'poc-room-1'
// Hard watchdog: the initial 'synced' awaits below have no built-in timeout;
// if the server never completes the Hocuspocus handshake the process would
// otherwise hang silently (observed 2026-10-08). Bounded to 20s -> FAIL.
setTimeout(() => {
  console.log('FAIL hard-timeout: no sync within 20s (server never completed handshake)')
  process.exit(1)
}, 20000)
const once = (em, ev) => new Promise((res) => em.on(ev, res))
const until = async (fn, ms) => {
  const t0 = Date.now()
  while (Date.now() - t0 < ms) {
    if (fn()) return true
    await new Promise((r) => setTimeout(r, 50))
  }
  return fn()
}

const phase = process.argv[2]
if (phase === 'phase1') {
  const d1 = new Y.Doc()
  const p1 = new HocuspocusProvider({ url, name: room, document: d1 })
  const d2 = new Y.Doc()
  const p2 = new HocuspocusProvider({ url, name: room, document: d2 })
  await once(p1, 'synced')
  await once(p2, 'synced')
  d1.getMap('settings').set('msg', 'hello-from-c1')
  d1.getText('canvas').insert(0, 'c1-was-here')
  const ok = await until(() =>
    d2.getMap('settings').get('msg') === 'hello-from-c1' &&
    d2.getText('canvas').toString() === 'c1-was-here', 5000)
  console.log(ok ? 'PASS AC-YG6a two-client live convergence via yserve' : 'FAIL AC-YG6a convergence timeout')
  p1.destroy()
  p2.destroy()
  process.exit(ok ? 0 : 1)
} else if (phase === 'phase2') {
  const d3 = new Y.Doc()
  const p3 = new HocuspocusProvider({ url, name: room, document: d3 })
  await once(p3, 'synced')
  const ok = d3.getMap('settings').get('msg') === 'hello-from-c1' &&
    d3.getText('canvas').toString() === 'c1-was-here'
  console.log(ok ? 'PASS AC-YG6b state persisted across yserve restart (sqlite)' : 'FAIL AC-YG6b persistence lost')
  p3.destroy()
  process.exit(ok ? 0 : 1)
} else {
  console.log('usage: node client-yserve.mjs phase1|phase2')
  process.exit(2)
}
