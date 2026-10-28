import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sqlite3
import sys
import contextlib
import pathlib
import re

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    analysis TEXT NOT NULL
);
"""

def has_unpaired_surrogates(s):
    for c in s:
        code = ord(c)
        if 0xD800 <= code <= 0xDFFF:
            return True
    return False

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    return conn

def init_db(db_path):
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        with conn:
            conn.executescript(DB_SCHEMA)

def analyze_text(data, for_persistence=False):
    if not isinstance(data, dict):
        return None, (400, {'error': 'JSON must be object'})
    if 'text' not in data:
        return None, (400, {'error': 'missing text'})
    if not isinstance(data['text'], str):
        return None, (400, {'error': 'text must be string'})
    text_value = data['text']
    include_word_frequencies = data.get('include_word_frequencies', False)
    if 'include_word_frequencies' in data:
        if not isinstance(include_word_frequencies, bool):
            return None, (400, {'error': 'include_word_frequencies must be boolean'})
    include_utf8_bytes = data.get('include_utf8_bytes', False)
    if 'include_utf8_bytes' in data:
        if not isinstance(include_utf8_bytes, bool):
            return None, (400, {'error': 'include_utf8_bytes must be boolean'})
    if include_utf8_bytes:
        if has_unpaired_surrogates(text_value):
            return None, (400, {'error': 'text contains unpaired surrogate'})
    if for_persistence and has_unpaired_surrogates(text_value):
        return None, (400, {'error': 'text contains unpaired surrogate'})
    result = {
        'characters': len(text_value),
        'words': len(text_value.split()),
        'lines': len(text_value.splitlines()),
    }
    if include_word_frequencies:
        tokens = text_value.split()
        freq = {}
        for token in tokens:
            if token:
                freq[token] = freq.get(token, 0) + 1
        result['word_frequencies'] = freq
    if include_utf8_bytes:
        try:
            utf8_bytes = len(text_value.encode('utf-8'))
        except Exception:
            return None, (400, {'error': 'failed to encode text as utf-8'})
        result['utf8_bytes'] = utf8_bytes
    return result, None

def persist_analysis(db_path, text, analysis):
    try:
        with contextlib.closing(sqlite3.connect(db_path)) as conn:
            with conn:
                cur = conn.execute(
                    "INSERT INTO analyses (text, analysis) VALUES (?, ?)",
                    (text, json.dumps(analysis, ensure_ascii=False))
                )
                return cur.lastrowid, None
    except (sqlite3.DataError, sqlite3.IntegrityError, sqlite3.ProgrammingError, sqlite3.InterfaceError, sqlite3.OperationalError, UnicodeEncodeError, TypeError, ValueError):
        return None, (400, {'error': 'invalid data'})
    except Exception:
        return None, (500, {'error': 'internal error'})

def get_analysis_by_id(db_path, id):
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        cur = conn.execute("SELECT id, text, analysis FROM analyses WHERE id = ?", (id,))
        row = cur.fetchone()
        if row:
            return {'id': row[0], 'text': row[1], 'analysis': json.loads(row[2])}
        return None

def parse_id_from_path(path):
    # Accept only /analyses/<id> where <id> is ASCII decimal in 1..9223372036854775807, no extra path
    m = re.fullmatch(r"/analyses/([1-9][0-9]*)", path)
    if not m:
        return None
    id_str = m.group(1)
    # SQLite INTEGER is signed 64-bit: 1..9223372036854775807
    try:
        if len(id_str) > 19:
            return None
        id_val = int(id_str)
        if not (1 <= id_val <= 9223372036854775807):
            return None
        return id_val
    except Exception:
        return None

class Handler(BaseHTTPRequestHandler):
    db_path = None

    def send_json(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/health':
            self.send_json(200, {'status': 'ok'})
        elif self.path == '/analyze':
            self.send_json(405, {'error': 'method not allowed'})
        elif self.path.startswith('/analyses/'):
            id_val = parse_id_from_path(self.path)
            if id_val is None:
                self.send_json(404, {'error': 'not found'})
                return
            record = get_analysis_by_id(self.db_path, id_val)
            if record is None:
                self.send_json(404, {'error': 'not found'})
                return
            self.send_json(200, record)
        elif self.path == '/analyses':
            self.send_json(405, {'error': 'method not allowed'})
        else:
            self.send_json(404, {'error': 'not found'})

    def do_POST(self):
        if self.path == '/analyze':
            self.handle_analyze(stateless=True)
        elif self.path == '/analyses':
            self.handle_analyze(stateless=False)
        elif self.path.startswith('/analyses/'):
            self.send_json(405, {'error': 'method not allowed'})
        else:
            self.send_json(404, {'error': 'not found'})

    def handle_analyze(self, stateless):
        content_length = self.headers.get('Content-Length')
        if content_length is None:
            self.send_json(400, {'error': 'missing Content-Length'})
            return
        try:
            length = int(content_length)
        except Exception:
            self.send_json(400, {'error': 'invalid Content-Length'})
            return
        try:
            raw = self.rfile.read(length)
        except Exception:
            self.send_json(400, {'error': 'failed to read body'})
            return
        try:
            text = raw.decode('utf-8')
        except Exception:
            self.send_json(400, {'error': 'invalid UTF-8'})
            return
        try:
            data = json.loads(text)
        except Exception:
            self.send_json(400, {'error': 'malformed JSON'})
            return
        # For /analyses, enforce unpaired surrogate check for persistence
        result, error = analyze_text(data, for_persistence=not stateless)
        if error:
            self.send_json(*error)
            return
        if stateless:
            self.send_json(200, result)
        else:
            new_id, persist_error = persist_analysis(self.db_path, data['text'], result)
            if persist_error:
                self.send_json(*persist_error)
                return
            response = {'id': new_id, 'text': data['text'], 'analysis': result}
            self.send_json(201, response)

    def do_PUT(self):
        if self.path == '/analyze' or self.path == '/analyses' or self.path.startswith('/analyses/'):
            self.send_json(405, {'error': 'method not allowed'})
        else:
            self.send_json(404, {'error': 'not found'})

    def do_PATCH(self):
        if self.path == '/analyze' or self.path == '/analyses' or self.path.startswith('/analyses/'):
            self.send_json(405, {'error': 'method not allowed'})
        else:
            self.send_json(404, {'error': 'not found'})

    def do_DELETE(self):
        if self.path == '/analyze' or self.path == '/analyses' or self.path.startswith('/analyses/'):
            self.send_json(405, {'error': 'method not allowed'})
        else:
            self.send_json(404, {'error': 'not found'})

    def do_OPTIONS(self):
        if self.path == '/analyze' or self.path == '/analyses' or self.path.startswith('/analyses/'):
            self.send_json(405, {'error': 'method not allowed'})
        else:
            self.send_json(404, {'error': 'not found'})

    def log_message(self, format, *args):
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--database', type=str, default='httpstats.sqlite3')
    args = parser.parse_args()
    db_path = pathlib.Path(args.database).resolve()
    Handler.db_path = str(db_path)
    init_db(str(db_path))
    server = HTTPServer(('127.0.0.1', args.port), Handler)
    print(f'PORT={server.server_port}', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
