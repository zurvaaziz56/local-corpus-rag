# local-corpus-rag

Private, offline search over your own past writing. It combines meaning-based (semantic) search with keyword search, and adds filters for client, outcome and status.

Embeddings run on a local model through [Ollama](https://ollama.com), so no text ever leaves your machine. That makes it safe to use on confidential client material.

## The problem it solves

After a few hundred deliverables, the best paragraph you ever wrote for a given kind of client is somewhere in there, and you can't find it. Plain keyword search misses it when the wording differs, and pure semantic search handles names, gig numbers and dollar figures badly. This tool blends the two and lets you filter by what happened (`won`, `replied`, `no-reply`…).

## How it works

- **Corpus:** a folder of Markdown files, one per document. Each file has YAML frontmatter, for example `client`, `outcome`, `status` and `words`.
- **Index:** built once (and incrementally after that) by the indexer in the MIT-licensed [`obsidian-second-brain`](https://github.com/eugeniughelbur/obsidian-second-brain) skill (`scripts/eval/semantic_search.py`). It writes `.obsidian-semantic-index.json` next to the corpus.
- **Ranking:** `0.72 × semantic + 0.28 × lexical`. The semantic side finds meaning ("rate pushback" matches a document that never uses those words); the lexical side anchors identifiers.
- **Search:** `query.py` runs ad-hoc search with filters.

## Setup

Requirements: Python 3 (standard library only), Ollama with the `bge-m3` model, and the indexer mentioned above.

```bash
brew install ollama && brew services start ollama
ollama pull bge-m3
```

Put `query.py` in the corpus folder (it looks for the index next to itself), then build the index:

```bash
export OBSIDIAN_EMBED_EXCLUDE="_excluded/"
python3 /path/to/obsidian-second-brain/scripts/eval/semantic_search.py --path /path/to/corpus --build
```

## Usage

```bash
python3 query.py "security page copy" --min-words 300 -n 5
```

`query.py` filters: `--client`, `--outcome`, `--status`, `--min-words`, `-n/--limit`, `--lexical-only`.

## Design choices worth knowing

- **Filter by client.** If one client dominates the corpus, unfiltered topical queries drift toward that client's material. This is corpus balance, not a bug.
- **Keep files under about 1,500 words.** The indexer embeds at most 8 chunks of 1,200 characters per file and silently ignores the rest. Split long documents.

## Limits

- Assumes a Markdown corpus with consistent frontmatter. The tool doesn't build the frontmatter for you.
- Tuned for a few hundred to a few thousand files on one machine. It's not a server.

Built with Claude Code.
