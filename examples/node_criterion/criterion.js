'use strict';
// Claim: the treated plots yield at least 0.5 t/ha more than the control plots (difference of group means).
const { serve } = require('./tg_line');

function mean(xs) {
  let sum = 0;
  for (const x of xs) sum += x;
  return sum / xs.length;
}

serve({
  effect(d) {
    const treated = [];
    const control = [];
    d.group.forEach((g, i) => {
      if (g === 'treated') treated.push(d.y[i]);
      else if (g === 'control') control.push(d.y[i]);
    });
    if (treated.length === 0 || control.length === 0) return 'UNDEFINED'; // an empty selection
    if (![...treated, ...control].every(Number.isFinite)) return 'UNDEFINED'; // NaN or infinity
    return mean(treated) - mean(control) >= 0.5 ? 'HOLDS' : 'FAILS';
  },
});
