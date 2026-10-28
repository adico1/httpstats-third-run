# HTTPStats

A small Python 3.11+ standard-library HTTP service, implemented by a CrewAI SDLC
team. No package installation or API keys are needed to run it.

## Run

```sh
python3 server.py --port 8000 --database httpstats.sqlite3
```

In another terminal:

```sh
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/analyze -H 'Content-Type: application/json' -d '{"text":"hello world"}'
```

Expected analysis: `{"characters": 11, "words": 2, "lines": 1}`.
The service binds only to `127.0.0.1`. `--port 0` chooses a temporary port;
the first output line is `PORT=<actual-port>`. Stop the service with Ctrl-C.

## Contract

- `GET /health` returns 200 and `{"status":"ok"}`.
- `POST /analyze` accepts a UTF-8 JSON object with a required string `text`.
  Extra fields are ignored except for the optional boolean `include_word_frequencies` and `include_utf8_bytes`.
  If `include_word_frequencies` is true, the response includes a `word_frequencies` object mapping each token (from Python `str.split()`) to its occurrence count. Counting is case-sensitive and preserves punctuation and Unicode. Empty or whitespace-only text yields an empty object. Non-boolean values for the flag (including null, numbers, strings, arrays, objects) are rejected with HTTP 400 and a nonempty JSON error string.
  If `include_utf8_bytes` is true, the response includes a `utf8_bytes` field equal to the UTF-8 byte length of the input text (using Python `len(text.encode('utf-8'))`). Non-boolean values for the flag (including null, numbers, strings, arrays, objects) are rejected with HTTP 400 and a nonempty JSON error string. If the text contains an unpaired surrogate and the flag is true, the server responds with HTTP 400 and a nonempty JSON error instead of crashing. Empty text returns `utf8_bytes` as 0.
  Counts use Python `len(text)`, `len(text.split())`, and `len(text.splitlines())`; empty text produces three zero counts.
- Empty, malformed or invalid UTF-8 bodies, non-object JSON, missing text and
  non-string text return 400 with a nonempty JSON `error`.
- GET, PUT, PATCH, DELETE and OPTIONS on `/analyze` return 405.
- Unknown GET/POST paths return 404. Specified responses use JSON Content-Type.

### Example: Opt-in word frequencies

```sh
curl http://127.0.0.1:8000/analyze -H 'Content-Type: application/json' -d '{"text":"red red blue", "include_word_frequencies": true}'
```

Expected response:

```json
{"characters": 12, "words": 3, "lines": 1, "word_frequencies": {"red": 2, "blue": 1}}
```

### Example: Opt-in UTF-8 byte count

```sh
curl http://127.0.0.1:8000/analyze -H 'Content-Type: application/json' -d '{"text":"hé", "include_utf8_bytes": true}'
```

Expected response:

```json
{"characters": 2, "words": 1, "lines": 1, "utf8_bytes": 3}
```

### Example: Both opt-in flags

```sh
curl http://127.0.0.1:8000/analyze -H 'Content-Type: application/json' -d '{"text":"hé hé", "include_word_frequencies": true, "include_utf8_bytes": true}'
```

Expected response:

```json
{"characters": 5, "words": 2, "lines": 1, "word_frequencies": {"hé": 2}, "utf8_bytes": 7}
```

This is a local experiment, not a production-hardened server. Normal Content-Length
framing is supported. Request limits, adversarial framing, concurrency, authentication,
TLS and cloud hosting were outside the trial scope.

## Saved Analysis History

The service supports persistent analysis history using SQLite. Use the `--database PATH` option (default: `httpstats.sqlite3`). Each database path is isolated. The schema is initialized on startup and records survive restarts.

### Save an analysis

```sh
curl -i http://127.0.0.1:8000/analyses -H 'Content-Type: application/json' -d '{"text":"hé hé","include_utf8_bytes":true,"include_word_frequencies":true}'
```

Returns HTTP 201 and a JSON object with `id`, `text`, and `analysis` fields. Example response on a fresh database:

```json
{"id":1,"text":"hé hé","analysis":{"characters":5,"words":2,"lines":1,"word_frequencies":{"hé":2},"utf8_bytes":7}}
```

### Retrieve a saved analysis

```sh
curl -i http://127.0.0.1:8000/analyses/1
```

Returns HTTP 200 and the saved object:

```json
{"id":1,"text":"hé hé","analysis":{"characters":5,"words":2,"lines":1,"word_frequencies":{"hé":2},"utf8_bytes":7}}
```

### Restart instructions

Stop the server with Ctrl-C. Restart with the same `--database` path to preserve history. Using a different path creates a new, empty database.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

One test method executes 122 independent checks: 89 existing regression scenarios,
30 history/API checks, and 3 documentation checks. It starts temporary loopback
processes, checks SQLite records across restarts, and cleans up test databases.
The README save/retrieve examples below are executed against a fresh database.
The checker is copied unchanged from the factory's independent acceptance suite,
so the repository can be tested without the factory or model credentials.

## Provenance

The CrewAI team implemented the feature in run `dfd4d8e1e18d` from baseline
`9fa3c5848a526a5db894393f7ea239f16237893a`. All 11 lifecycle stages completed,
with 44/44 HTTP checks against both candidate and installed service, zero manual
candidate edits, zero operator retries and zero engine repair cycles. Codex reviewed
three approval gates under user authorization.

Promotion copied the exact verified `server.py` bytes; Codex added documentation
and regression-test packaging without rewriting the generated implementation.
That original promotion preserved the baseline source header. Later features
have evolved the source; each promotion records its own byte-for-byte provenance. See `provenance.json` for the SHA-256 digest.

[Factory trial report](https://github.com/adico1/ai_pipeline/blob/df2c3d51690eb08adbec348e90f0bba3779e1bc1/reports/httpstats-trial-20261028.json).
This one success does not establish reliability across arbitrary projects.

### Ongoing-development feature: word frequencies

CrewAI added the optional word-frequency feature in run `d6a512cbd7e3`, starting
from the published analyze version `a299ec9`. All 11 stages passed, with 63/63
checks on both candidate and installed source. The run needed zero operator
retries, manual candidate edits, or engine repair cycles. Codex reviewed the
three approval gates and promoted the exact verified source, then packaged the
independent checks and updated provenance. The earlier trial above describes
the original analyze feature; `provenance.json` records the current source.

[Word-frequency trial report](https://github.com/adico1/ai_pipeline/blob/main/reports/httpstats-word-frequencies-20261028.json).

### Ongoing-development feature: UTF-8 byte count

CrewAI implemented the opt-in UTF-8 byte count in run `47dcad718a5c`, starting
from published word-frequency commit `2da1271`. All 11 lifecycle stages completed;
89/89 HTTP scenarios passed against the candidate and installed copy.

This was an assisted success: the earlier run `42ffe90fe4c4` was withheld for
missing documentation. The second run required two operator-directed CrewAI
README correction attempts; the first made no changes, and the second corrected
an example and removed premature success claims. Verification and review were
rerun after those edits. Codex did not rewrite the candidate implementation;
promotion copied the exact verified server.py and packaged the regression checks.

[UTF-8 trial evidence](https://github.com/adico1/ai_pipeline/blob/main/reports/httpstats-utf8-bytes-20261028.json).

```json history-examples
[
  {
    "method": "POST",
    "path": "/analyses",
    "status": 201,
    "json": {"text": "hé hé", "include_utf8_bytes": true, "include_word_frequencies": true},
    "response": {"id": 1, "text": "hé hé", "analysis": {"characters": 5, "words": 2, "lines": 1, "word_frequencies": {"hé": 2}, "utf8_bytes": 7}}
  },
  {
    "method": "GET",
    "path": "/analyses/1",
    "status": 200,
    "response": {"id": 1, "text": "hé hé", "analysis": {"characters": 5, "words": 2, "lines": 1, "word_frequencies": {"hé": 2}, "utf8_bytes": 7}}
  }
]
```


### Ongoing-development feature: saved analysis history

CrewAI implemented SQLite-backed save/retrieve history in run `e20e5202da3a`,
starting from published commit `f0120f3`. All 11 lifecycle stages completed and
122/122 checks passed on both candidate and installed source, preserving the 89
existing scenarios. The initial implementation attempt made no edits and failed.
Two operator-directed CrewAI recovery calls followed: the first implemented the
feature but failed oversized-ID handling; the second repaired it. One factory
retry then passed normal verification and review. This was an assisted success.

Codex supplied the acceptance sensors, reviewed three gates, and promoted the
exact verified server.py. Packaging adds the expanded regression suite, corrects
the README test count, and extends database sidecar exclusions. No candidate
implementation was manually rewritten. SQLite data stays local and is excluded
from source control and the source-only release archive.

[Saved-history trial evidence](https://github.com/adico1/ai_pipeline/blob/main/reports/httpstats-history-20261028.json).
