'use strict';
// A3 version of the criterion of examples/01_tautology/faulty.py (E1-08): the targets are computed from the labels and
// compared with the same rule applied to the same labels; `observed` is never read (the tautology of the faulty twin).

// (3 L + 1) mod 9 with numpy's mod: the result takes the sign of the divisor.
function rule(x) {
  const v = 3 * x + 1;
  let m = v % 9;
  if (m !== 0 && m < 0) m += 9;
  return m;
}

function criterion(msg) {
  const labels = column(msg, 'L');
  const targets = labels.map(rule); // computed from the labels...
  const again = labels.map(rule); // ...and compared with the same rule on the same labels
  let hits = 0;
  for (let i = 0; i < labels.length; i++) if (targets[i] === again[i]) hits += 1;
  return hits / labels.length >= 0.95 ? 'HOLDS' : 'FAILS';
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
