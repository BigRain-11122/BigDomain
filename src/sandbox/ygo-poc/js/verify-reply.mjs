// Verifies ygo-encoded outputs against yjs@13.6.33 semantics (reverse direction
// of the wire-compat claim) + byte-level state-vector compare + merge convergence.
import * as Y from 'yjs'
import { readFileSync } from 'node:fs'
import { deepStrictEqual } from 'node:assert'

const D = 'data/fixtures'
const O = 'data/out'
let failed = 0
const check = (name, detail, fn) => {
  try {
    fn()
    console.log(`PASS ${name}${detail ? ' | ' + detail : ''}`)
  } catch (e) {
    failed = 1
    console.log(`FAIL ${name} | ${e.message}`)
  }
}
const stateOf = (doc) => ({
  map: doc.getMap('settings').toJSON(),
  array: doc.getArray('chatlog').toJSON(),
  text: doc.getText('canvas').toString(),
})

const exp1 = JSON.parse(readFileSync(`${D}/fx1-expected.json`, 'utf8'))

const dv1 = new Y.Doc()
check('AC-YG2 ygo-state-v1 -> yjs apply, full semantic match', '', () => {
  Y.applyUpdate(dv1, readFileSync(`${O}/go-state-a-v1.bin`))
  deepStrictEqual(stateOf(dv1), exp1)
})

const dv2 = new Y.Doc()
check('AC-YG3 ygo-state-v2 -> yjs applyV2, full semantic match', '', () => {
  Y.applyUpdateV2(dv2, readFileSync(`${O}/go-state-a-v2.bin`))
  deepStrictEqual(stateOf(dv2), exp1)
})

check('AC-YG4 state-vector byte-for-byte (ygo vs Y.encodeStateVector)', `sv len=${readFileSync(`${D}/sv-a.bin`).length}`, () => {
  deepStrictEqual(new Uint8Array(readFileSync(`${O}/sv-go-a.bin`)), new Uint8Array(readFileSync(`${D}/sv-a.bin`)))
})

const exp2 = JSON.parse(readFileSync(`${D}/fx-merge-expected.json`, 'utf8'))
const dm = new Y.Doc()
check('AC-YG5 ygo merge of concurrent updates converges to yjs-merged state', `merge text=${JSON.stringify(exp2.text)}`, () => {
  Y.applyUpdate(dm, readFileSync(`${O}/go-merge.bin`))
  deepStrictEqual(stateOf(dm), exp2)
})

process.exit(failed)
