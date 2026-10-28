# HTTPStats

A small Python 3.11+ standard-library HTTP service, implemented by a CrewAI SDLC
team. No package installation or API keys are needed to run it.

## Run

```sh
python3 server.py --port 8000
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
  Extra fields are ignored. Counts use Python `len(text)`, `len(text.split())`,
  and `len(text.splitlines())`; empty text produces three zero counts.
- Empty, malformed or invalid UTF-8 bodies, non-object JSON, missing text and
  non-string text return 400 with a nonempty JSON `error`.
- GET, PUT, PATCH, DELETE and OPTIONS on `/analyze` return 405.
- Unknown GET/POST paths return 404. Specified responses use JSON Content-Type.

This is a local experiment, not a production-hardened server. Normal Content-Length
framing is supported. Request limits, adversarial framing, concurrency, authentication,
TLS and cloud hosting were outside the trial scope.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

One test method executes 44 independent real HTTP scenarios, including three
baseline checks. It starts a temporary loopback process and stops it afterward.
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
The original source header still describes the starting baseline and is preserved
to retain byte-for-byte provenance. See `provenance.json` for the SHA-256 digest.

[Factory trial report](https://github.com/adico1/ai_pipeline/blob/df2c3d51690eb08adbec348e90f0bba3779e1bc1/reports/httpstats-trial-20261028.json).
This one success does not establish reliability across arbitrary projects.
