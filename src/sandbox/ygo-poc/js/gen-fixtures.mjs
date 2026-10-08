// Generates yjs@13.6.33 wire fixtures for the ygo interop PoC.
// Fixtures cover Map/Array/Text/nested types, fractional + whole-number
// floats (whole-number = upstream-pinned byte-divergence probe), and a
// two-client concurrent-edit pair whose merged state is the convergence AC.
import * as Y from 'yjs'
import { mkdirSync, writeFileSync } from 'node:fs'

const D = 'data/fixtures'
mkdirSync(D, { recursive: true })

const snapshotState = (doc) => ({
  map: doc.getMap('settings').toJSON(),
  array: doc.getArray('chatlog').toJSON(),
  text: doc.getText('canvas').toString(),
})

// --- fixture 1: single-client doc ---
const docA = new Y.Doc()
docA.clientID = 424242
const m = docA.getMap('settings')
m.set('theme', 'dark')
m.set('x', 123.456) // fractional float (avatar-position-like value)
m.set('count', 8)   // whole-number float (upstream-pinned divergence probe)
const profile = new Y.Map()
m.set('profile', profile)
profile.set('level', 7)
profile.set('title', 'resident')
const arr = docA.getArray('chatlog')
arr.push(['hi', 'welcome'])
arr.insert(0, ['sys:room-open'])
arr.delete(1, 1)
const t = docA.getText('canvas')
t.insert(0, 'hello ')
t.insert(6, 'world')
t.insert(11, '!')
t.delete(0, 1)

const exp1 = snapshotState(docA)
writeFileSync(`${D}/fx1-v1.bin`, Y.encodeStateAsUpdate(docA))
writeFileSync(`${D}/fx1-v2.bin`, Y.encodeStateAsUpdateV2(docA))
writeFileSync(`${D}/sv-a.bin`, Y.encodeStateVector(docA))
writeFileSync(`${D}/fx1-expected.json`, JSON.stringify(exp1))

// --- fixture 2: concurrent two-client edits over a shared baseline ---
const docB = new Y.Doc()
docB.clientID = 777888
Y.applyUpdate(docB, Y.encodeStateAsUpdate(docA))
docA.getMap('settings').set('editA', 'from-A')
docB.getMap('settings').set('editB', 'from-B')
docA.getText('canvas').insert(0, 'A:')
docB.getText('canvas').insert(0, 'B:')
const updA = Y.encodeStateAsUpdate(docA)
const updB = Y.encodeStateAsUpdate(docB)
writeFileSync(`${D}/fxA-v1.bin`, updA)
writeFileSync(`${D}/fxB-v1.bin`, updB)
writeFileSync(`${D}/fxA-v2.bin`, Y.encodeStateAsUpdateV2(docA))
writeFileSync(`${D}/fxB-v2.bin`, Y.encodeStateAsUpdateV2(docB))
const merged = new Y.Doc()
Y.applyUpdate(merged, updA)
Y.applyUpdate(merged, updB)
writeFileSync(`${D}/fx-merge-expected.json`, JSON.stringify(snapshotState(merged)))

console.log('fixtures written | fx1 text:', exp1.text, '| merge text:', merged.getText('canvas').toString())
