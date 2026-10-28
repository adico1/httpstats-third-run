# HTTPStats factory trial

Minimal standard-library Python service. The baseline serves GET /health only.
The factory task is to add POST /analyze; acceptance checks are external to this repository.

```sh
python3 server.py --port 8000
curl http://127.0.0.1:8000/health
```

The service binds only to 127.0.0.1. Port 0 selects a temporary port and prints PORT=<port>.
This is a local experiment, not a production service.
