"""List every context-mode / web tool call of a transcript with its input (designer tool, P-1/P-5)."""
import json, sys
for l in open(sys.argv[1], encoding="utf-8"):
    d = json.loads(l)
    if d.get("type") != "assistant":
        continue
    for c in d["message"].get("content") or []:
        if isinstance(c, dict) and c.get("type") == "tool_use" and ("ctx_" in c["name"] or c["name"] in ("WebFetch", "WebSearch")):
            inp = dict(c["input"])
            for k in ("code", "commands"):
                if k in inp:
                    inp[k] = str(inp[k])[:300]
            print(c["name"].replace("mcp__plugin_context-mode_context-mode__", ""), json.dumps(inp, ensure_ascii=False)[:400])
