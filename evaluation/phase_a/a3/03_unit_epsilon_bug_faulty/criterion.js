'use strict';
// A3 version of the criterion of examples/03_unit_epsilon_bug (E5-20), the `rate` pattern of the A2 manifests: the
// fraction of pixels above 1.5 exceeds 0.8.  Like the pattern: UNDEFINED for an empty selection, a non-numeric column
// or a value that is not finite.
function criterion(msg) {
  const dtype = msg.types.pixel && msg.types.pixel.dtype;
  const pixel = column(msg, 'pixel');
  if (dtype !== 'float' && dtype !== 'int') return 'UNDEFINED';
  if (pixel.length === 0) return 'UNDEFINED';
  if (!pixel.every(Number.isFinite)) return 'UNDEFINED';
  let above = 0;
  for (const v of pixel) if (v > 1.5) above += 1;
  return above / pixel.length > 0.8 ? 'HOLDS' : 'FAILS';
}

// ---- protocol tg-line/1 (spec 0.6, section 5): one JSON object per line in, one line out, logs to stderr ----
const readline = require('readline');
const NON_FINITE = { NaN: NaN, Infinity: Infinity, '-Infinity': -Infinity };

// The array behind a key; non-finite floats arrive as the strings "NaN", "Infinity", "-Infinity".
function column(msg, key) {
  if (!Object.prototype.hasOwnProperty.call(msg.data, key)) throw new Error('missing key ' + key);
  return msg.data[key].map((v) => (typeof v === 'string' && v in NON_FINITE ? NON_FINITE[v] : v));
}

const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
rl.on('line', (line) => {
  const msg = JSON.parse(line);
  if (msg.op === 'hello') {
    process.stdout.write(JSON.stringify({ ok: true, tg: 'tg-line/1', rid: msg.rid }) + '\n');
  } else if (msg.op === 'criterion') {
    let reply;
    try {
      reply = { rid: msg.rid, outcome: criterion(msg) };
    } catch (err) {
      reply = { rid: msg.rid, error: String((err && err.message) || err) }; // this one outcome becomes UNDEFINED
    }
    process.stdout.write(JSON.stringify(reply) + '\n');
  } else if (msg.op === 'bye') {
    rl.close();
  }
});
