# Learnings & Issues Log

Started documenting late but captured key issues encountered during development and deployment.

## RAGAS Integration

- `evaluate()` is deprecated → replaced with `@experiment` decorator
- `faithfulness` / `answer_relevancy` changed from variables → class instances (`Faithfulness()`, `AnswerRelevancy()`)
- RAGAS 0.4.3 supports only OpenAI → Claude not supported via `LangchainLLMWrapper`
- **Decision:** Kept `ragas_evaluate()` method in code but not called — documented in README as pending OpenAI key

## Bug Fixes

- `format_response` crash → `retrieved` was a list of strings but treated as a dict with keys `documents`, `distances`, `metadatas`
- `file_generation = Generation()` on page load → caused crash on Streamlit Cloud on every refresh
- `read_files()` called on every button click → re-chunked and re-embedded on every query, causing 2min+ response time

## Streamlit Cloud Deployment

- Missing `txtDocuments/` and `pdfDocuments/` folders on cloud → fixed with `os.path.exists()` guard in all file reading methods
- ChromaDB `PersistentClient` fails on cloud (no persistent disk) → switched to `EphemeralClient` (in-memory)
- `requirements.txt` blocked by `.gitignore` → removed the entry to allow it to be pushed

## Performance

- `read_files()` called on every button click → optimized using `st.session_state` caching — reduced response time from ~2min to ~39sec
- CrossEncoder reranking runs on CPU → slow on free tier, documented in UI with info message

## Semantic Cache

- Cache threshold `< 0.1` too strict → almost nothing hit cache → updated to `< 0.15`
