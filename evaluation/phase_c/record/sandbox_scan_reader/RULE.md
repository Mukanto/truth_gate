# Reading rule for scan hits

The folder `agent_docs/` is a set of tool documentation that will be given to other agents. A word scan found the lines
listed in `SCAN_HITS.json` (file, line number, the words found, the full line text). Read each listed line in its context
in `agent_docs/` (the surrounding sentence or paragraph).

For each hit, decide: **remove** if the sentence that contains the hit states an evaluation of the tool, a result of
one, a count of cases or detections, a case (an evaluation case by name or number), a source key (a short citation key
such as an author-year code), or an evaluation class (B-1 to B-6, O-1 to O-3); otherwise **keep** (the word is ordinary
tool vocabulary, for example "evaluation" meaning one run of a criterion, "external" meaning a command criterion,
"audit" meaning Python's audit hook or a blind review step of the user's own study).

When one line holds several sentences, judge the sentence that contains the problem and quote it.
