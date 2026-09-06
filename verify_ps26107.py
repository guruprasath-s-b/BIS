"""Eight capability groups + regression, grounding and API-boundary checks.
Offline by default. --live makes paid API calls using .env and verifies availability.
"""
import argparse
import json
import os
import re
import time
import unittest
from pathlib import Path
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--live', action='store_true')
parser.add_argument('--output', default='benchmark-results.json')
args, unittest_args = parser.parse_known_args()
if not args.live:
    os.environ['BIS_OFFLINE'] = '1'
from rag_engine import BISRAGEngine
from bis_knowledge import LANGUAGES

CASES = [
 ('1 Product discovery','smart electric kettle','product_standard_lookup','IS 302'),
 ('1 Product discovery','N95 masks','product_standard_lookup','IS 9473'),
 ('1 Product discovery','infant milk formula','product_standard_lookup','IS 14433'),
 ('1 Product discovery','gold jewelry','product_standard_lookup','IS 1417'),
 ('1 Product discovery','helmet for a motorcycle','product_standard_lookup','IS 4151'),
 ('1 Product discovery','electric toys','product_standard_lookup','IS 15644'),
 ('1 Product discovery','steel rebar','product_standard_lookup','IS 1786'),
 ('1 Product discovery','ordinary Portland cement','product_standard_lookup','IS 269'),
 ('1 Product discovery','lithium battery','product_standard_lookup','IS 16046'),
 ('2 ISI licensing','How to get ISI Mark?','certification_guide','Scheme I'),
 ('3 CRS registration','How to register a laptop under CRS?','certification_guide','Scheme II'),
 ('4 FMCS / Scheme IV / Ecomark','FMCS foreign manufacturer','certification_guide','not Scheme IV'),
 ('4 FMCS / Scheme IV / Ecomark','Scheme IV procedure','certification_guide','Certificate of Conformity'),
 ('4 FMCS / Scheme IV / Ecomark','ECO Mark application','certification_guide','CPCB'),
 ('5 Hallmarking and consumer affairs','Verify HUID ABC123','hallmarking','no live HUID'),
 ('5 Hallmarking and consumer affairs','Complaint about fake ISI mark','consumer_grievance','acknowledgement'),
 ('6 Laboratory finder','Find recognized testing labs in Chennai for toys','lab_finder','recognition'),
 ('7 Multilingual interaction','सोने का हॉलमार्क कैसे जांचें','hallmarking',''),
 ('7 Multilingual interaction','தங்க ஹால்மார்க் சரிபார்ப்பு','hallmarking',''),
 ('7 Multilingual interaction','బంగారం హాల్‌మార్క్','hallmarking',''),
 ('7 Multilingual interaction','সোনার হলমার্ক','hallmarking',''),
 ('8 Grounding and clause traceability','clause 5.4 boiling water surgical instruments','product_standard_lookup','5.4'),
]

class SafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=BISRAGEngine(Path(__file__).with_name('corpus_index.pkl'))
        cls.engine.client.enabled=False

    def test_unsupported_product_abstains(self):
        answer=self.engine.answer_question('quantum teleportation widget')
        self.assertEqual(answer['standards'],[])
        self.assertEqual(answer['retrieved_passages'],[])
        self.assertIn('cannot establish',answer['answer'])

    def test_no_live_authenticity_claim(self):
        a=self.engine.answer_question('Verify HUID ABC123')
        self.assertFalse(a['live_verification'])
        self.assertIn('does not prove authenticity',a['answer'])

    def test_api_outage_falls_back(self):
        with patch.object(self.engine.client,'enabled',True), patch.object(self.engine.client,'json',side_effect=TimeoutError):
            a=self.engine.answer_question('smart electric kettle',language='ta')
        self.assertEqual(a['mode'],'local')
        self.assertEqual(a['language'],'en')
        self.assertIn('translation_requires_available_api',a['warnings'])
        self.assertTrue(a['citations'])

    def test_fabricated_citations_rejected(self):
        with patch.object(self.engine.client,'enabled',True), patch.object(self.engine.client,'json',return_value={'answer':'Verified compliant with IS 999999 clause 99 [S900]'}):
            a=self.engine.answer_question('kettle')
        self.assertEqual(a['mode'],'local')
        self.assertNotIn('999999',a['answer'])

    def test_every_language_accepted(self):
        for language in LANGUAGES:
            a=self.engine.answer_question('kettle',language=language)
            self.assertEqual(a['requested_language'],language)
            self.assertTrue(a['answer'])

    def test_clause_is_in_source(self):
        a=self.engine.answer_question('clause 5.4 boiling water surgical instruments')
        self.assertTrue(any(c['clause']=='5.4' for c in a['citations']))
        self.assertIn('5.4 Procedure', a['answer'])
        self.assertTrue(all(c['status']=='draft' for c in a['citations']))

    def test_api_translation_success(self):
        local=self.engine.answer_question('kettle')
        translated='தமிழ் வழிகாட்டுதல் ' + local['answer']
        with patch.object(self.engine.client,'enabled',True), patch.object(self.engine.client,'json',return_value={'answer':translated}):
            answer=self.engine.answer_question('kettle',language='ta')
        self.assertEqual(answer['mode'],'openai')
        self.assertEqual(answer['language'],'ta')


def main():
    engine=BISRAGEngine(Path(__file__).with_name('corpus_index.pkl'))
    if args.live and not engine.client.enabled:
        raise SystemExit('--live requires OPENAI_API_KEY and BIS_OFFLINE=0')
    rows=[]
    for group,query,route,expected in CASES:
        started=time.perf_counter()
        a=engine.answer_question(query)
        cited=set(re.findall(r'\[(S\d+)\]',a['answer']))
        ok=(a['route']==route and bool(a['citations']) and cited=={c['id'] for c in a['citations']})
        # Wording may change with a real model, so inspect canonical evidence as well.
        evidence=' '.join(b['text'] for b in a['evidence_blocks'])
        ok=ok and expected.lower() in evidence.lower()
        if args.live:
            ok=ok and a['mode']=='openai' and a['language']==a['requested_language']
        rows.append(dict(capability=group,query=query,passed=ok,route=a['route'],mode=a['mode'],latency_ms=round((time.perf_counter()-started)*1000,1)))
        print(('PASS' if ok else 'FAIL')+' '+group+': '+query)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(SafetyTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=dict(mode='live' if args.live else 'offline', passed=sum(r['passed'] for r in rows),total=len(rows),cases=rows,safety_tests_passed=result.wasSuccessful(),limitations=['Offline tests validate routing and fallback, not translation quality.', 'Live model quality needs native-speaker review.', 'No live HUID or laboratory API is connected.'])
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"{report['passed']}/{len(rows)} benchmark cases; report: {args.output}")
    raise SystemExit(0 if all(r['passed'] for r in rows) and result.wasSuccessful() else 1)

if __name__=='__main__':
    main()
