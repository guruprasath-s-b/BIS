# Manak — BIS intelligent assistant (PS 26107)

A working full-stack upgrade of the existing Python/BM25/TF-IDF application. The implementation keeps your medical-equipment corpus and adds curated BIS service and product discovery records, optional OpenAI translation/rendering, rich JSON, and a multilingual chat UI.

This is an independently built hackathon application and a foundation for further production engineering. It is not an official BIS service or a complete catalogue of Indian Standards.

## Execution plan and setup

1. Create a Python environment (or use the existing `venv`):

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   ```

   The existing pickle index requires compatible NumPy/scikit-learn versions. If loading fails after dependency changes, rebuild it with `.venv/bin/python index_model.py`. Only load the trusted project index; pickle files can execute code.

2. Configure optional AI support:

   ```sh
   cp .env.example .env
   ```

   Edit `.env` locally:

   ```dotenv
   OPENAI_API_KEY=your_actual_key_here
   OPENAI_MODEL=gpt-4o-mini
   BIS_OFFLINE=0
   ```

   `gpt-4o` can also be configured. The adapter uses the official Chat Completions endpoint with JSON mode, a fixed HTTPS destination, bounded response size, token cap and 15-second timeout per call. A non-English input may use two calls. Environment variables take precedence over `.env`; restart the server after changing configuration. This small `.env` reader supports literal `KEY=value` lines and optional surrounding quotes, not interpolation or shell commands. `.env` is gitignored and never served to the browser. The frontend sends no API key.

   Leave the key empty or set `BIS_OFFLINE=1` for local operation. With AI enabled, queries and selected evidence are sent to OpenAI. Without a working API, a small Hindi/Tamil/Telugu/Bengali alias dictionary supports common queries; answers fall back to English with a localized disclosure. Full multilingual translation requires an available API and has not been validated by native speakers.

3. Start the server:

   ```sh
   .venv/bin/python web_server.py --port 8000
   ```

   Open http://127.0.0.1:8000. With the existing environment, substitute `venv/bin/python` for `.venv/bin/python` throughout.

4. Run automated verification:

   ```sh
   BIS_OFFLINE=1 .venv/bin/python -m unittest test_web.py
   .venv/bin/python -m unittest test_extract_corpus.py
   .venv/bin/python verify_ps26107.py
   BIS_OFFLINE=1 .venv/bin/python test_model.py
   node --check web/app.js
   ```

   The PS benchmark writes `benchmark-results.json` and exits nonzero on failure. It groups the six goal bullets plus the detailed requested features into eight explicitly defined capability groups: product discovery; ISI; CRS; FMCS/Scheme IV/Ecomark; hallmarking/consumer affairs; labs; multilingual interaction; grounding/clauses. It contains 22 benchmark questions and seven additional safety/adapter tests. Offline acceptance of a language is not a claim of full translation quality.

5. Optionally run the paid live API benchmark:

   ```sh
   BIS_OFFLINE=0 .venv/bin/python verify_ps26107.py --live --output live-results.json
   ```

   This requires a valid API key. It fails if any request falls back to local mode. Mocked adapter tests are separate from live-model validation. Independently review translated terminology, citation entailment and regulatory correctness before deployment.

## Complete implementation files

- `rag_engine.py`: retained hybrid corpus search, five intent routes with multi-intent support, product candidate lookup, service procedures, grounded local answers, source-backed explicit clause extraction, optional AI rendering and translation, fallback metadata.
- `bis_knowledge.py`: curated schemes, official links, 13 product/category records spanning household electronics, IT, batteries, steel, toys, cement, food, jewellery and medical masks; multilingual aliases and fallback disclosures.
- `cli.py`: console entry point updated for structured citations and mode/route metadata.
- `ai_client.py`: `.env` configuration and optional OpenAI HTTP/JSON adapter; no OpenAI SDK dependency.
- `web_server.py`: `/api/ask`, `/api/documents`, `/api/health`, input validation, bounded concurrent inference, allowlisted static/PDF serving and response headers.
- `web/index.html`, `web/app.js`, `web/style.css`: existing responsive interface and document library, four quick-action pills, safe Markdown subset, official citation chips/action links, copy, optional browser speech recognition and synthesis, 12 output-language choices.
- `extract_corpus.py`: PDF text cleaning and overlapping chunk extraction with validation for chunk size and overlap settings.
- `.env.example`, `requirements.txt`: configuration and runtime dependencies.
- `verify_ps26107.py`, `test_web.py`, `test_extract_corpus.py`: capability, adapter, endpoint and corpus chunk regression tests.

All files contain complete runnable code in the workspace; no placeholders or omitted implementation sections need pasting.

## API contract

`GET /api/health` returns HTTP 200 with `status: "ok"`, `ready: true`, and
the configured engine mode (`local` or `openai`) when the engine is loaded.
If the engine is unavailable, it returns HTTP 503 with `status: "unavailable"`,
`ready: false`, and `mode: null`. This checks local engine readiness; it does
not call OpenAI or verify external-service availability.

```sh
curl http://127.0.0.1:8000/api/ask \
  -H 'Content-Type: application/json' \
  -d '{"query":"smart electric kettle","language":"en"}'
```

`query`: 2–1500 characters. `language`: `auto`, `en`, `hi`, `ta`, `te`, `bn`, `mr`, `gu`, `kn`, `ml`, `pa`, `or`, `ur`. Select the language explicitly for ambiguous scripts such as Hindi/Marathi. Default `auto` uses script detection. The UI sends its selected output language. Each question is independent; session history is displayed but is not sent as conversational memory.

Responses include:

```json
{
  "answer": "Candidate guidance ... [S1]",
  "route": "product_standard_lookup",
  "routes": ["product_standard_lookup"],
  "mode": "local",
  "requested_language": "en",
  "language": "en",
  "citations": [{"id":"S1","title":"Source title","url":"https://standards.bis.gov.in/","kind":"standard_discovery","clause":null}],
  "action_cards": [{"type":"official_link","title":"Search Indian Standards","url":"https://standards.bis.gov.in/"}],
  "standards": [],
  "retrieved_passages": [],
  "warnings": [],
  "live_verification": false
}
```

Additional fields include `evidence_blocks` (canonical English evidence), `official_links`, `normalized_query`, `grounding` and `knowledge_reviewed_on`. The response uses rich JSON rather than streaming. `confidence` is null: normalized retrieval scores are not probabilities. Citation objects replace the old citation strings; existing `answer`, `retrieved_passages`, `top_document`, `top_title` and `primary_page` fields remain available.

## Grounding and regulatory scope

- **FMCS is not Scheme IV.** Scheme IV concerns Certificates of Conformity; the routes have separate guidance. See [BIS Scheme IV](https://www.bis.gov.in/specific-guidelines-for-scheme-iv-certificate-of-conformity/?lang=en) and [FMCS](https://www.bis.gov.in/fmcs/certification-process/aboutfmcs/?lang=en).
- Ecomark guidance references the 2024 framework implemented by CPCB in partnership with BIS, rather than assuming an ISI licence grants Ecomark. See [government announcement](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2061878).
- Product records recommend **candidates**, not unconditional legal applicability. Published editions, amendments, effective dates, QCOs, exemptions and product particulars need validation. The [BIS compulsory list](https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-i-mark-scheme/?lang=en) marks infant milk substitutes as de-notified; the app does not state all food products require BIS certification.
- Archived [BIS product manuals](https://www.bis.gov.in/product-manual-archive/?lang=en) establish standard identity, not current status. Review dated source records periodically. The server does not refresh these records from the web on each request.
- Clauses are returned only when their text is found in the local corpus. Try `clause 5.4 boiling water surgical instruments`: the source page and clause are returned with a **draft** label. The medical corpus contains wide-circulation drafts; these do not become published requirements merely because they are cited. Discovery-only records return `clause: null` explicitly.
- HUID checking explains the [official verification flow](https://www.bis.gov.in/hallmarking-overview/hallmarking-faqs/hallmarking-faq/?lang=en). There is no live HUID API. Six-character syntax never establishes authenticity.
- The lab route provides scope/search instructions and official [LIMS](https://lims.bis.gov.in/) and [CRS laboratory](https://crsbis.in/BIS/bis_lab.do) links. It does not invent nearby facilities, recognition status, prices, availability or test schedules. Live matching needs a maintained directory or authorized API integration.
- Model output must retain the exact citation set, may not introduce URLs or new numeric identifiers, and falls back on validation failure. These checks do not prove semantic entailment; human review remains needed. This is a constrained renderer over evidence, not an autonomous filing agent.

## UI and deployment boundaries

The renderer supports paragraphs, bold, code, simple headings and lists, with HTML escaping and an official-domain URL allowlist. It intentionally does not execute HTML or render arbitrary model-generated links. Browser voice support and available languages vary. Dictation begins only on click and can use the browser vendor’s speech service; read-aloud uses installed/browser voices. History stays in memory and resets on reload.

The standard-library server binds to localhost and is intended for local development. Public production deployment still requires a production HTTP/ASGI layer, authentication as appropriate, per-user quotas/rate limits, TLS, secret management, operational logging/monitoring, versioned published-standard ingestion, retrieval relevance evaluation beyond the small benchmark, native-language review and maintenance of regulatory/directory data. The current four-request inference limit bounds concurrent model calls but is not a per-user quota. No website deployment or external application submission was performed.

OpenAI implementation references: [GPT-4o mini](https://developers.openai.com/api/docs/models/gpt-4o-mini), [Chat API](https://developers.openai.com/api/reference/resources/chat).
