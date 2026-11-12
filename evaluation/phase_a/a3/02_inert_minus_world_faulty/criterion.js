'use strict';
// A3 version of the criterion of examples/02_inert_minus_world/faulty.py (E5-01): the stiffness fitted through the
// origin, k = sum(x f) / sum(x x), is 40 N/m within 4 N/m.
function criterion(msg) {
  const x = column(msg, 'x');
  const f = column(msg, 'f');
  if (x.length !== f.length) throw new Error('x and f differ in length');
  let den = 0;
  let num = 0;
  for (let i = 0; i < x.length; i++) {
    den += x[i] * x[i];
    num += x[i] * f[i];
  }
  if (!(den > 0.0)) return 'FAILS';
  const kHat = num / den;
  return Math.abs(kHat - 40.0) < 4.0 ? 'HOLDS' : 'FAILS';
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
