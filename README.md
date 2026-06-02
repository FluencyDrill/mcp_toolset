# mcp_toolset

A scaffold for building [Haystack](https://haystack.deepset.ai/) pipelines and serving
them as **MCP tools** with [Hayhooks](https://github.com/deepset-ai/hayhooks) — so you
can call them straight from Claude Code (or any MCP client).

Write a pipeline once; Hayhooks exposes it simultaneously as a REST endpoint **and** an
MCP tool. The tool's name comes from the wrapper folder, its description from the
`run_api` docstring, and its input schema from `run_api`'s type-hinted arguments.

## Layout

```
src/mcp_toolset/
  custom_components/   # reusable Haystack @components
  pipelines/           # builder functions that assemble Pipelines
  prompt_templates/    # .jinja prompts + loader (scaffolding for LLM steps)
  schemas/             # pydantic models for typed pipeline I/O
  config.py            # config (e.g. where transcripts are written)
  stores.py            # shared, process-wide DocumentStore singleton
pipeline_wrappers/     # HAYHOOKS_PIPELINES_DIR — thin deployables (one folder = one tool)
  text_stats/          # offline smoke-test tool
  youtube_transcript/  # fetch a transcript, archive it, return a confirmation
data/transcripts/      # saved transcript markdown (git-ignored)
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

### The `youtube_transcript` pattern (context hygiene)

```
YouTubeTranscriptFetcher  ->  MetadataArchiver
  captions -> markdown          • write markdown -> data/transcripts/<video_id>.md
  + metadata dict               • write ONE metadata Document -> DocumentStore
                                • return {document_id, document_name, path, metadata}
```

The full transcript is written to a markdown **file on disk**; only **metadata** (a
pointer) goes into the document store; and the tool returns just a small **confirmation**.
The large transcript never enters the model's context until something explicitly opens
the file. `MetadataArchiver` is generic — reuse it in any pipeline that needs to "save
content + metadata and confirm what was saved".

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

Then in Claude Code, `/mcp` lists the `text_stats` and `youtube_transcript` tools.

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

- The in-memory document store is ephemeral per process; the saved `.md` files survive
  restarts. Swap `stores.get_document_store()` for a persistent backend when needed.
- Transcripts are captions-only (no audio/Whisper).
- Natural follow-ons: a `read_transcript(video_id)` tool, query/retrieval over stored
  transcripts, and an optional LLM "answer over transcript" step using
  `prompt_templates/` + a generator.