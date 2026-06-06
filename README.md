# mcp_toolset

A scaffold for building [Haystack](https://haystack.deepset.ai/) pipelines and serving
them as **MCP tools** with [Hayhooks](https://github.com/deepset-ai/hayhooks) — so you
can call them straight from Claude (Claude Desktop, Claude Code, or Claude.ai
integrations) or any MCP client.

Write a pipeline once; Hayhooks exposes it simultaneously as a REST endpoint **and** an
MCP tool. The tool's name comes from the wrapper folder, its description from the
`run_api` docstring, and its input schema from `run_api`'s type-hinted arguments.

**Claude is the engine.** Pipelines do deterministic work — fetch, store, retrieve,
structure — and **Claude does the reasoning** by calling the tools. No paid LLM API and
no embeddings are used inside the pipelines, so it runs on your Claude subscription with
no extra per-token cost.

## Layout

```
src/mcp_toolset/
  custom_components/   # reusable Haystack @components
  pipelines/           # builder functions that assemble Pipelines
  prompt_templates/    # .jinja prompts + loader (scaffolding for LLM steps)
  schemas/             # pydantic models for typed pipeline I/O
  config.py            # config (transcripts dir, store backend)
  stores.py            # store backend factory + matching keyword retriever
pipeline_wrappers/     # HAYHOOKS_PIPELINES_DIR — thin deployables (one folder = one tool)
  text_stats/          # offline smoke-test tool
  youtube_transcript/  # fetch a transcript, archive it, return a confirmation
  search_knowledge/    # keyword search over the stored knowledge base
data/transcripts/      # saved transcript markdown (git-ignored)
docker-compose.yml     # local Postgres + pgvector for the durable store
tests/
```

Package `pipelines/` holds the **construction logic**; root `pipeline_wrappers/` holds
the **deployable wrappers** that import those builders. Pipelines are built in code (not
serialized YAML).

## Included tools

| Tool | Inputs | Returns | Needs network/keys |
|------|--------|---------|--------------------|
| `text_stats` | `text: str` | character/word/sentence counts + reading time | no |
| `youtube_transcript` | `url: str` | `ArchiveResult` — `document_id`, `document_name`, `path`, `metadata` | YouTube only, no API key |
| `search_knowledge` | `query: str`, `top_k=5`, `max_chars=500` | `SearchResults` — `query` + `hits[]` (truncated snippets + metadata) | no |

### The `youtube_transcript` pattern (context hygiene)

```
YouTubeTranscriptFetcher  ->  MetadataArchiver
  captions -> markdown          • write markdown -> data/transcripts/<video_id>.md
  + metadata dict               • write ONE metadata Document -> DocumentStore
                                • return {document_id, document_name, path, metadata}
```

The full transcript is written to a markdown **file on disk** (the canonical artifact);
the searchable text + metadata go into the **document store**; and the tool returns just
a small **confirmation**. Context stays lean because the *tool return shape* is small —
`search_knowledge` later returns only short snippets, never whole documents. The big
content enters Claude's context only when it explicitly opens a file or pulls a snippet.
`MetadataArchiver` is generic — reuse it in any pipeline that needs to "save content +
metadata and confirm what was saved".

### Knowledge store & search

Everything archived lands in a shared document store, and `search_knowledge` does
**keyword** (lexical) retrieval over it — Postgres full-text or in-memory BM25 depending
on the backend. **No embeddings, no models, no LLM, no tokens.** It returns the top
matches as short snippets; Claude reads them and decides what to open or compare.

#### Store backends

Pick the backend with `MCP_TOOLSET_STORE` (one swap point — `stores.get_document_store()`):

- **`memory`** (default) — `InMemoryDocumentStore`. Zero config, ephemeral. Great for dev.
- **`pgvector`** — durable Postgres via the [pgvector](https://github.com/pgvector/pgvector)
  integration. Survives restarts, shareable across coworkers, and the foundation for
  evals/measurement.

Bring up Postgres locally and point the toolkit at it:

```bash
docker compose up -d                                  # Postgres + pgvector on :5432
uv sync --extra postgres                              # install the pgvector integration
export MCP_TOOLSET_STORE=pgvector
export PG_CONN_STR=postgresql://mcp:mcp@localhost:5432/mcp_toolset
make run
```

Semantic (embedding) search is a later, still-token-free upgrade (local
`sentence-transformers` + `PgvectorEmbeddingRetriever`); keyword retrieval needs neither.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11+.

```bash
uv sync                       # create the env, install deps (editable)
cp .env.example .env          # optional: tweak ports / transcripts dir
uv run pytest                 # all tests run offline

make run                      # REST server  -> http://localhost:1416  (/docs, /status)
make mcp                      # MCP server    -> http://localhost:1417/mcp
```

Try the REST endpoints:

Each deployed pipeline is served at `POST /<tool>/run`:

```bash
curl localhost:1416/status
curl -X POST localhost:1416/text_stats/run \
  -H 'content-type: application/json' \
  -d '{"text": "Hello world. This is Haystack."}'
# -> {"result": {"characters": 30, "words": 5, "sentences": 2, "reading_time_seconds": 1.5}}

curl -X POST localhost:1416/youtube_transcript/run \
  -H 'content-type: application/json' \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
# -> {"result": {"document_id": "...", "path": "data/transcripts/<id>.md", "metadata": {...}}}

curl -X POST localhost:1416/search_knowledge/run \
  -H 'content-type: application/json' \
  -d '{"query": "haystack pipelines", "top_k": 3}'
# -> {"result": {"query": "...", "hits": [{"document_id": "...", "snippet": "...", ...}]}}
```

> Note: fetching transcripts requires outbound access to YouTube. Datacenter/cloud IPs
> are often rate-limited or blocked by YouTube (HTTP 403); the error is surfaced cleanly
> in the response. It works from a residential network or with a proxy configured.

## Connect Claude Code

Start the MCP server (`make mcp`), then either rely on the committed `.mcp.json`
(project-scoped, HTTP) when you open this repo in Claude Code, or register it explicitly:

```bash
# HTTP transport (recommended — Claude Code speaks HTTP natively)
claude mcp add --transport http hayhooks http://localhost:1417/mcp
```

Hayhooks' MCP server serves **Streamable HTTP** and **SSE** — there is no raw stdio
transport. If a client only speaks stdio, bridge it with supergateway:

```bash
# stdio bridge (only if you need stdio specifically)
claude mcp add hayhooks -- npx -y supergateway --streamableHttp http://localhost:1417/mcp
```

Then in Claude, `/mcp` lists the `text_stats`, `youtube_transcript`, and
`search_knowledge` tools.

## Add your own tool

1. Add components under `src/mcp_toolset/custom_components/`.
2. Add a builder under `src/mcp_toolset/pipelines/` that wires them.
3. Create `pipeline_wrappers/<your_tool>/pipeline_wrapper.py` with a
   `PipelineWrapper(BasePipelineWrapper)`: build the pipeline in `setup()` and expose a
   typed `run_api(...)` whose docstring describes the tool.
4. Restart the server — it auto-loads every wrapper folder.

## Make targets

```
make install   # uv sync
make run       # REST server (:1416)
make mcp       # MCP server (:1417/mcp)
make mcp-stdio # bridge MCP to stdio via supergateway
make test      # pytest
make lint      # ruff check
make fmt       # ruff format + autofix
```

## Notes & next steps

- The in-memory store is ephemeral per process; use the `pgvector` backend for durable,
  shared storage. The saved `.md` files survive restarts regardless.
- Retrieval is keyword-only today; transcripts are captions-only (no audio/Whisper).
- Natural follow-ons: richer analysis tools (`read_transcript(video_id)`, `find_related`,
  cross-doc compare), more ingestion sources (web, PDFs, files), semantic/embedding
  search, and an evals harness (golden query→doc sets, retrieval metrics) — now that the
  store is durable and structured.