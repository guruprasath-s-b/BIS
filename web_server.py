"""Local web UI for the existing BIS Domain 54 retrieval engine."""
import json
import argparse
import threading
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote
from rag_engine import BISRAGEngine
from bis_knowledge import LANGUAGES, REVIEWED

ROOT = Path(__file__).resolve().parent
CORPUS = json.loads((ROOT / 'corpus_chunks.json').read_text())
ENGINE = None
INFLIGHT = threading.BoundedSemaphore(4)

class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(40)

    def respond(self, data, status=200, content_type='application/json; charset=utf-8'):
        body = json.dumps(data, ensure_ascii=False).encode() if isinstance(data, (dict, list)) else data
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == '/api/health':
            ready = ENGINE is not None
            mode = ('openai' if ENGINE.client.enabled else 'local') if ready else None
            return self.respond({
                'status': 'ok' if ready else 'unavailable',
                'ready': ready,
                'mode': mode,
                'languages': LANGUAGES,
                'knowledge_reviewed_on': REVIEWED,
            }, 200 if ready else 503)
        if path == '/api/documents':
            return self.respond({'metadata': CORPUS['metadata'], 'documents': CORPUS['documents']})
        if path.startswith('/documents/'):
            name = path.removeprefix('/documents/')
            allowed = {d['source_file'] for d in CORPUS['documents']}
            file = ROOT / 'PDFs' / name
            if name in allowed and file.is_file():
                return self.respond(file.read_bytes(), content_type='application/pdf')
        assets = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8'), '/style.css': ('style.css', 'text/css; charset=utf-8')}
        if path in assets:
            name, mime = assets[path]
            return self.respond((ROOT / 'web' / name).read_bytes(), content_type=mime)
        self.respond({'error': 'Not found'}, 404)

    def do_POST(self):
        if urlparse(self.path).path != '/api/ask':
            return self.respond({'error': 'Not found'}, 404)
        try:
            if self.headers.get('Transfer-Encoding'):
                return self.respond({'error': 'Transfer encoding is unsupported.'}, 400)
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16384:
                return self.respond({'error': 'Request too large or empty.'}, 400)
            payload = json.loads(self.rfile.read(size))
            query = payload.get('query') if isinstance(payload, dict) else None
            if not isinstance(query, str) or not 2 <= len(query.strip()) <= 1500:
                return self.respond({'error': 'Please enter a question between 2 and 1,500 characters.'}, 400)
            query = query.strip()
            language = payload.get('language', 'auto')
            if not isinstance(language, str) or language not in {'auto', *LANGUAGES}:
                return self.respond({'error': 'Unsupported language.'}, 400)
            if not INFLIGHT.acquire(blocking=False):
                return self.respond({'error': 'Assistant is busy. Please retry shortly.'}, 429)
            try:
                result = ENGINE.answer_question(query, language=language)
            finally:
                INFLIGHT.release()
            return self.respond(result)
        except (ValueError, json.JSONDecodeError):
            self.respond({'error': 'Invalid request.'}, 400)
        except Exception:
            logging.exception('BIS request failed')
            self.respond({'error': 'Search is temporarily unavailable. Please try again.'}, 500)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    ENGINE = BISRAGEngine(ROOT / 'corpus_index.pkl')
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'BIS assistant: http://127.0.0.1:{args.port}', flush=True)
    server.serve_forever()
