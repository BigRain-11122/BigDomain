// Applies a pycrdt-produced binary update inside yjs@13 (reverse wire-compat leg).
// Opponent library reused read-only from ygo-poc/js/node_modules (yjs@13.6.33).
// Usage: node apply_in_yjs.mjs <update.bin> --v1|--v2
import * as Y from "file:///C:/Users/sjs20/Desktop/FluxGroup/domain/BigDomain/src/sandbox/ygo-poc/js/node_modules/yjs/dist/yjs.mjs";
import { readFileSync } from "node:fs";

const [file, flag] = process.argv.slice(2);
if (!file || (flag !== "--v1" && flag !== "--v2")) {
  console.error("usage: node apply_in_yjs.mjs <update.bin> --v1|--v2");
  process.exit(2);
}
const update = readFileSync(file);
const doc = new Y.Doc();
if (flag === "--v1") {
  Y.applyUpdate(doc, update);
} else {
  Y.applyUpdateV2(doc, update);
}
const snap = {
  map: doc.getMap("settings").toJSON(),
  array: doc.getArray("chatlog").toJSON(),
  text: doc.getText("canvas").toString(),
};
console.log(JSON.stringify(snap));
