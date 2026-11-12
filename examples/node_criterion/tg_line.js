'use strict';
// Minimal, dependency-free helper for protocol tg-line/1 (see README.md).
// serve({ criterion_id: (data, types) => "HOLDS" | "FAILS" | "UNDEFINED" | { component: outcome, ... } })

const readline = require('readline');

const PROTOCOL = 'tg-line/1';
const NON_FINITE = { NaN: NaN, Infinity: Infinity, '-Infinity': -Infinity };

// The gate sends non-finite floats as the strings "NaN", "Infinity" and "-Infinity"; turn them back into numbers.
function decodeFloats(value) {
  if (Array.isArray(value)) return value.map(decodeFloats);
  if (typeof value === 'string' && Object.prototype.hasOwnProperty.call(NON_FINITE, value)) return NON_FINITE[value];
  return value;
}

function decodeData(data, types) {
  const out = {};
  for (const key of Object.keys(data)) {
    out[key] = types[key].dtype === 'float' ? decodeFloats(data[key]) : data[key];
  }
  return out;
}

function send(message) {
  process.stdout.write(JSON.stringify(message) + '\n'); // one line per reply; logs go to stderr
}

function serve(criteria) {
  const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  rl.on('line', (line) => {
    const msg = JSON.parse(line);
    if (msg.op === 'hello') {
      send({ ok: true, tg: PROTOCOL, rid: msg.rid });
    } else if (msg.op === 'criterion') {
      const fn = criteria[msg.id];
      if (typeof fn !== 'function') {
        send({ rid: msg.rid, error: 'unknown criterion ' + msg.id });
        return;
      }
      try {
        send({ rid: msg.rid, outcome: fn(decodeData(msg.data, msg.types), msg.types) });
      } catch (err) {
        send({ rid: msg.rid, error: String((err && err.message) || err) });
      }
    } else if (msg.op === 'bye') {
      rl.close();
    }
  });
}

module.exports = { serve, decodeFloats };
