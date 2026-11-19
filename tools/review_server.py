"""Serve the local review room; records user decisions, never publishes."""
import argparse
import json
import re
import secrets
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from review_store import ReviewStore

ROOT = Path(__file__).resolve().parents[1]
STORE = ReviewStore(ROOT)
TOKEN = secrets.token_urlsafe(32)


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, content_type='application/json; charset=utf-8'):
        body = json.dumps(data, ensure_ascii=False).encode() if isinstance(data, (dict, list)) else data
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        route = urlparse(self.path).path
        if route == '/':
            return self.reply(200, (ROOT/'review/index.html').read_bytes(), 'text/html; charset=utf-8')
        if route == '/api/state':
            return self.reply(200, {**STORE.snapshot(), 'review_token': TOKEN})
        if route.startswith('/cover/'):
            variant_id = route.removeprefix('/cover/')
            variant = next((v for d in STORE.plan()['days'] for v in d.get('variants', []) if v['id'] == variant_id), None)
            if not variant or not variant.get('cover'):
                return self.reply(404, {'error': 'Cover not ready'})
            p = STORE.media_path({'file': variant['cover']})
            return self.reply(200, p.read_bytes(), 'image/jpeg')
        if route.startswith('/media/'):
            variant_id = route.removeprefix('/media/')
            variant = next((v for d in STORE.plan()['days'] for v in d.get('variants', []) if v['id'] == variant_id), None)
            if not variant or not STORE.media_path(variant).is_file():
                return self.reply(404, {'error': 'Media not ready'})
            p = STORE.media_path(variant)
            size = p.stat().st_size
            begin, end = 0, size-1
            range_header = self.headers.get('Range')
            if range_header:
                match = re.fullmatch(r'bytes=(\d+)-(\d*)', range_header)
                if not match:
                    return self.reply(416, {'error': 'Invalid range'})
                begin = int(match.group(1)); end = min(int(match.group(2)) if match.group(2) else end, end)
                if begin > end:
                    return self.reply(416, {'error': 'Invalid range'})
            self.send_response(206 if range_header else 200)
            self.send_header('Content-Type', 'video/mp4')
            self.send_header('Content-Length', str(end-begin+1))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Cache-Control', 'no-cache')
            if range_header:
                self.send_header('Content-Range', f'bytes {begin}-{end}/{size}')
            self.end_headers()
            if self.command != 'HEAD':
                try:
                    with p.open('rb') as f:
                        f.seek(begin); remaining=end-begin+1
                        while remaining:
                            chunk=f.read(min(1024*128,remaining))
                            if not chunk: break
                            self.wfile.write(chunk); remaining-=len(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            return
        return self.reply(404, {'error': 'Not found'})

    def do_POST(self):
        if urlparse(self.path).path != '/api/review':
            return self.reply(404, {'error': 'Not found'})
        if self.headers.get('X-Review-Token') != TOKEN:
            return self.reply(403, {'error': 'Open the local review room to record a decision.'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.reply(415, {'error': 'JSON required'})
        try:
            length = int(self.headers.get('Content-Length', 0))
            if length > 16384: raise ValueError('Request too large')
            data = json.loads(self.rfile.read(length))
            event = STORE.decide(data['item_id'], data['variant_id'], data['fingerprint'], data['action'], data.get('note',''))
            return self.reply(200, {'saved': True, 'event': event})
        except (ValueError, KeyError, TypeError) as e:
            return self.reply(409, {'error': str(e)})


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=8892); a=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    print(f'Review room: http://127.0.0.1:{a.port}/',flush=True)
    server.serve_forever()
