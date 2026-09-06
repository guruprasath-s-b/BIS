"""Run with: venv/bin/python -m unittest test_web.py"""
import os
os.environ["BIS_OFFLINE"] = "1"
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch
import web_server

class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        web_server.ENGINE = web_server.BISRAGEngine(Path(__file__).parent / 'corpus_index.pkl')

    def request(self, path, data=None):
        handler = object.__new__(web_server.Handler)
        handler.path = path
        body = json.dumps(data).encode() if data is not None else b''
        handler.headers = {'Content-Length': str(len(body))}
        handler.rfile = io.BytesIO(body)
        results = []
        handler.respond = lambda payload, status=200, content_type=None: results.append((status, payload))
        (handler.do_POST if data is not None else handler.do_GET)()
        return results[0]

    def test_search_and_pdf_citation(self):
        status, answer = self.request('/api/ask', {'query': 'corrosion resistance of surgical instruments'})
        self.assertEqual(status, 200)
        self.assertTrue(answer['retrieved_passages'])
        self.assertIn('34489', answer['top_document'])
        for source in answer['retrieved_passages']:
            status, pdf = self.request('/documents/' + source['source_file'])
            self.assertEqual(status, 200)
            self.assertTrue(pdf.startswith(b'%PDF'))
            self.assertGreater(source['page_number'], 0)

    def test_restricted_files(self):
        for path in ['/corpus_index.pkl', '/documents/../web_server.py', '/web_server.py']:
            self.assertEqual(self.request(path)[0], 404)

    def test_input_validation(self):
        for query in ['', 'a', 'x' * 1501, ['invalid']]:
            self.assertEqual(self.request('/api/ask', {'query': query})[0], 400)

    def test_service_and_language_scope(self):
        for query in ['hallmarking requirements', 'सर्जिकल उपकरण']:
            status, result = self.request('/api/ask', {'query': query})
            self.assertEqual(status, 200)
            self.assertTrue(result['citations'])
            self.assertNotIn('Please ask your technical question in English', result['answer'])
        self.assertEqual(result['requested_language'], 'hi')

    def test_language_validation(self):
        for language in [[], 5, 'xx']:
            self.assertEqual(self.request('/api/ask', {'query':'gold', 'language':language})[0],400)

    def test_collection(self):
        status, result = self.request('/api/documents')
        self.assertEqual(status, 200)
        self.assertEqual(len(result['documents']), 54)

    def test_error_state(self):
        with patch.object(web_server.ENGINE, 'answer_question', side_effect=RuntimeError):
            self.assertEqual(self.request('/api/ask', {'query': 'surgical tools'})[0], 500)

if __name__ == '__main__':
    unittest.main()
