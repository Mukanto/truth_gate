# A criterion written in Node (protocol `tg-line/1`)

A `command` criterion is any program that speaks one JSON object per line on standard input and output
(spec 0.6, section 5). This folder holds a dependency-free helper (`tg_line.js`), one criterion (`criterion.js`),
two small synthetic worlds (`world.py`) and the manifest (`truthgate.toml`).

1. The gate starts the program once (`command` is an argv list, resolved on `PATH`) in a private working folder that holds
   only the `[external] uses` files, with a restricted environment. Logs go to standard error.
2. Handshake: the gate sends `{"op":"hello","tg":"tg-line/1","rid":0}`; the program answers `{"ok":true,"tg":"tg-line/1","rid":0}`.
3. For every sample: `{"op":"criterion","id":"effect","rid":k,"types":{...},"data":{...}}`. `data` holds nested lists,
   `types` the dtype (`float`, `int`, `bool`, `str`) and shape of each key; non-finite floats are the strings
   `"NaN"`, `"Infinity"`, `"-Infinity"`; integers beyond 2^53 are refused.
4. The reply is `{"rid":k,"outcome":"HOLDS"}` (or `"FAILS"`, `"UNDEFINED"`, or an object of those for components), or
   `{"rid":k,"error":"text"}`, which makes that one outcome UNDEFINED. Answer every request, in order, with its `rid`.
5. A timeout, a line that is not JSON, a wrong `rid` or a reply with neither `outcome` nor `error` kills the process;
   its later requests are UNDEFINED and the study note `EXTERNAL_DIED` is written.
6. The leak guard cannot see inside another process: the certificate carries the study note `K6_EXTERNAL_UNGUARDED`
   and records the SHA-256 of the executable and of the `uses` files (not of the libraries it loads).

```text
truth-gate check examples/node_criterion/truthgate.toml --out node_example.json
```
