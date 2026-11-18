# Reading rule for scan hits

The folder `agent_docs/` is a set of tool documentation that will be given to other agents. A word scan found the lines
listed in `SCAN_HITS.json` (file, line number, the words found, the full line text). Read each listed line in its context
in `agent_docs/` (the surrounding sentence or paragraph).

For each hit, decide: **remove** if the sentence that contains the hit states any of these:
- an evaluation of the tool, a result of one, or a count of cases or detections;
- a case (an evaluation case by name or number);
- a source key (a short citation key such as an author-year code);
- an evaluation class (B-1 to B-6, O-1 to O-3), a subtype of one (L1.1 to L3.2), or a mechanism tag;
- an evaluation phase (Phase A to Phase D);
- a checklist given to the authors of synthetic worlds.

Otherwise **keep**: the word is ordinary tool vocabulary. For example, "evaluation" meaning one run of a criterion;
"external" meaning a command criterion; "audit" meaning Python's audit hook or a blind review step of the user's own
study; "checklist" meaning the methods protocol's freeze checklist.

When one line holds several sentences, judge the sentence that contains the problem and quote it.

Write `READER2.json`: `{"decisions": [{"hit": <index in SCAN_HITS.json hits, from 0>, "file", "line", "decision": "keep" | "remove", "sentence": "<the sentence judged>", "reason": "<one line>"}], "other_sentences": [{"file", "line", "sentence", "reason"}]}`. Put in `other_sentences` any sentence near a hit that you would remove although it holds no scanned word.
