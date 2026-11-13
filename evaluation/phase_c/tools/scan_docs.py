"""Phase C agent-document scan (PREREG_PHASE_C section 4 step 0).

Prints every line (file:line:text) of every .md file under DIR that contains any of the scan tokens (case-insensitive).
Short tokens (E1, E2, E3, B-1 to B-6, miss) match on word boundaries ("miss" also as "misses"/"missed", never inside
"missing" or "permission"); the other tokens match as substrings. The agent document set may not contain any hit
(an evaluation-result sentence is removed or the hit is recorded as a removal before the freeze).

--allow FILE lists hits that are accepted in advance. FILE is JSON:
    {"listed": [{"file": "<path relative to DIR, forward slashes>", "text": "<the exact line text, without the line
                 ending>", "tokens": ["<token label>", ...], "reason": "<free text>"}, ...]}
A hit is LISTED when an entry has the same file, exactly the same text, and every token label of the hit is in the
entry's tokens. Listed hits are not printed as hits and do not count towards the exit code; only their count is printed on
stderr ("N listed hit line(s)"). An entry that matches no hit is reported on stderr as "stale allow entry: file: text"
(it does not change the exit code). Without --allow every hit is a hit.

Output streams are reconfigured to UTF-8 (errors="replace"), so a line with a non-cp1252 character never crashes a
Windows console run.

Usage:
    py scan_docs.py DIR [--allow ALLOW.json] [--json REPORT.json]
--json writes {"dir", "n_hits", "hits", "n_listed", "listed", "stale"}: "hits" holds only the unlisted hits, "n_hits"
counts them, "listed" holds the listed hits and "stale" the allow entries that matched no hit.
Exit code 0 if there is no unlisted hit, 1 if there is at least one unlisted hit, 2 on a usage error, 3 on any other
exception (printed on stderr).
"""
import argparse, json, os, re, sys

SUBSTRING_TOKENS = ["Phase A", "Phase B", "Phase C", "world author", "evaluation", "REPORT", "pilot", "case study",
                    "Tenkit", "external", "detection rate", "private", "audit"]
# word-boundary tokens: (label, regex)
BOUNDARY_TOKENS = [("E1", r"\bE1\b"), ("E2", r"\bE2\b"), ("E3", r"\bE3\b")] + \
                  [(f"B-{i}", rf"\bB-{i}\b") for i in range(1, 7)] + \
                  [("miss", r"\bmiss(?:es|ed)?\b")]
TOKENS = [(t, re.compile(re.escape(t), re.IGNORECASE)) for t in SUBSTRING_TOKENS] + \
         [(t, re.compile(rx, re.IGNORECASE)) for t, rx in BOUNDARY_TOKENS]


def scan(root):
    hits = []
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            if not f.lower().endswith(".md"):
                continue
            path = os.path.join(dp, f)
            with open(path, encoding="utf-8", errors="replace") as fh:
                for n, line in enumerate(fh, start=1):
                    text = line.rstrip("\r\n")
                    toks = [t for t, rx in TOKENS if rx.search(text)]
                    if toks:
                        hits.append({"file": os.path.relpath(path, root).replace("\\", "/"), "line": n, "text": text, "tokens": toks})
    return hits


def load_allow(path):
    """Read the allow file; return the list of entries ({"file", "text", "tokens", "reason"?}). Raises on any malformed content."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("listed"), list):
        raise ValueError('allow file must be a JSON object with a "listed" list')
    entries = []
    for i, e in enumerate(data["listed"]):
        if (not isinstance(e, dict) or not isinstance(e.get("file"), str) or not isinstance(e.get("text"), str)
                or not isinstance(e.get("tokens"), list) or not all(isinstance(t, str) for t in e["tokens"])):
            raise ValueError(f'allow entry {i}: needs string "file", string "text" and a list of string "tokens"')
        entries.append({**e, "file": e["file"].replace("\\", "/")})
    return entries


def split_listed(hits, entries):
    """Return (unlisted hits, listed hits, stale entries)."""
    used = [False] * len(entries)
    unlisted, listed = [], []
    for h in hits:
        match = [i for i, e in enumerate(entries)
                 if e["file"] == h["file"] and e["text"] == h["text"] and set(h["tokens"]) <= set(e["tokens"])]
        for i in match:
            used[i] = True
        (listed if match else unlisted).append(h)
    return unlisted, listed, [e for i, e in enumerate(entries) if not used[i]]


def run(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dir")
    ap.add_argument("--allow", dest="allow", default=None, help="JSON file of listed (accepted) hit lines")
    ap.add_argument("--json", dest="json_out", default=None, help="write the hit list as JSON")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dir):
        print(f"not a directory: {a.dir}", file=sys.stderr)
        return 2
    entries = load_allow(a.allow) if a.allow else []
    hits, listed, stale = split_listed(scan(a.dir), entries)
    for h in hits:
        print(f"{h['file']}:{h['line']}:{h['text']}")
    nfiles = len({h["file"] for h in hits})
    print(f"{len(hits)} hit line(s) in {nfiles} file(s)", file=sys.stderr)
    if a.allow:
        print(f"{len(listed)} listed hit line(s)", file=sys.stderr)
        for e in stale:
            print(f"stale allow entry: {e['file']}: {e['text']}", file=sys.stderr)
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as fh:
            json.dump({"dir": os.path.abspath(a.dir), "n_hits": len(hits), "hits": hits,
                       "n_listed": len(listed), "listed": listed, "stale": stale}, fh, indent=2, ensure_ascii=False)
    return 1 if hits else 0


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    try:
        return run(argv)
    except Exception as e:
        print(f"error: {type(e).__name__}: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
