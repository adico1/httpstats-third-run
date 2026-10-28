"""Minimal loopback HTTP service; the factory will add POST /analyze."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class Handler(BaseHTTPRequestHandler):
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
        else:
            self.send_json(404, {'error': 'not found'})

    def do_POST(self):
        if self.path != '/analyze':
            self.send_json(404, {'error': 'not found'})
            return
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
        if not isinstance(data, dict):
            self.send_json(400, {'error': 'JSON must be object'})
            return
        if 'text' not in data:
            self.send_json(400, {'error': 'missing text'})
            return
        if not isinstance(data['text'], str):
            self.send_json(400, {'error': 'text must be string'})
            return
        text_value = data['text']
        result = {
            'characters': len(text_value),
            'words': len(text_value.split()),
            'lines': len(text_value.splitlines()),
        }
        self.send_json(200, result)

    def do_PUT(self):
        if self.path == '/analyze':
            self.send_json(405, {'error': 'method not allowed'})
        else:
            self.send_json(404, {'error': 'not found'})

    def do_PATCH(self):
        if self.path == '/analyze':
            self.send_json(405, {'error': 'method not allowed'})
        else:
            self.send_json(404, {'error': 'not found'})

    def do_DELETE(self):
        if self.path == '/analyze':
            self.send_json(405, {'error': 'method not allowed'})
        else:
            self.send_json(404, {'error': 'not found'})

    def do_OPTIONS(self):
        if self.path == '/analyze':
            self.send_json(405, {'error': 'method not allowed'})
        else:
            self.send_json(404, {'error': 'not found'})

    def log_message(self, format, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    server = HTTPServer(('127.0.0.1', args.port), Handler)
    print(f'PORT={server.server_port}', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
