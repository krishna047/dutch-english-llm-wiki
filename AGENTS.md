# Dutch → English LLM Wiki — agent schema

This repository follows Andrej Karpathy’s **LLM Wiki** pattern: **raw sources** (immutable) → **English markdown wiki** (you maintain with the agent) → **this file** (rules + workflows). Human curates sources and asks questions; the agent does summarizing, cross-linking, filing, and housekeeping.

## Repository layout

- `raw/` — **Source of truth.** Drop PDFs, `.docx`, `.md`, `.txt`, exports, etc. here. **Never edit sources to “fix” content**; add a new version as a new file instead. Large binaries are fine; prefer text/markdown when you can. Optional images: `raw/assets/`.
- `wiki/` — **Agent-written** markdown only. Pages, synthesis, entity/topic notes, indexes. You read here (Obsidian recommended).
- `wiki/index.md` — Content catalog: every wiki page linked, one-line summary, optional metadata (category, last updated, related sources).
- `wiki/log.md` — Append-only timeline: ingests, major queries filed as pages, lint passes.

## Language policy (critical)

- **Sources may be Dutch (or mixed).** The agent reads them as-is.
- **All wiki pages are written in English:** titles, body text, summaries, tables, and synthesis.
- When a **Dutch term or proper noun** matters, write English first and add the Dutch in parentheses once, e.g. *municipal tax (gemeentelijke belasting)*.
- If a **verbatim Dutch phrase** is legally or technically important, put it in a short quote with an English gloss — do not leave paragraphs of Dutch in the wiki unless explicitly requested.
- **Questions in English → answers in English.** Cite wiki pages and, when useful, the underlying `raw/` filename.

## Wiki conventions

- **Filenames:** `kebab-case.md` under `wiki/`. One main concept or entity per page unless a tight cluster belongs together.
- **Links:** Prefer **Obsidian wikilinks** between wiki pages: `[[Some Page]]`. Link the first meaningful mention on a page and in “See also” where helpful.
- **Frontmatter (optional but useful):** at the top of substantive pages:

```yaml
---
title: Short English title
type: entity | concept | source-summary | synthesis | howto
sources: ["raw/example-dutch-doc.md"]
updated: 2026-04-14
tags: [tag-one, tag-two]
---
```

- **Source summaries:** For each ingested file, consider a page `wiki/sources/<slug>.md` that states: what it is, key claims, limitations, and links to entity/concept pages you updated.

## Ingest workflow

1. User adds a file under `raw/` (and optional note: priority topics).
2. Agent **reads** the source, identifies entities, dates, claims, and open questions.
3. Agent **updates the wiki:** new/updated pages, cross-links, contradictions called out explicitly.
4. Agent **updates `wiki/index.md`** (add/move entries, refresh one-liners).
5. Agent **appends `wiki/log.md`** with a line like:
  `## [YYYY-MM-DD] ingest | <short source title> | raw/<filename>`
6. If the source is large, **split work**: ingest in logical chunks and log each chunk; still keep one primary `sources/` summary page per file.

## Query workflow (English answers, neat formatting)

When the user asks a question:

1. **Skim `wiki/index.md`** to find candidate pages; open the most relevant pages (and `raw/` only if the wiki is missing detail or looks stale).
2. **Answer in English** using this structure unless the user asks otherwise:
  - **TL;DR** — 2–4 bullets or one short paragraph.
  - **Details** — `##` sections with clear headings.
  - **Sources** — bullet list: wiki pages (`[[Page]]`) and `raw/filename` where applicable.
  - Use **tables** for comparisons, **numbered steps** for procedures, and **bold labels** for definitions — keep it scannable.
3. If the answer is **durable value** (e.g. recurring FAQ, deep synthesis), **add or update a wiki page** and link it from the chat reply. Append a `log.md` entry:
  `## [YYYY-MM-DD] query-filed | <page title> | <one line why>`

## Lint workflow (periodic)

User asks for a “wiki lint.” Agent checks: contradictions, stale pages vs newer sources, orphans (no inbound wikilinks), missing hub pages for repeated concepts, broken links, and gaps worth a follow-up question. Propose concrete edits; after applying, update `index.md` and append `log.md`.

## Local Mac workflow (constant query + wiki updates)

Everything in this repo already lives **on your machine**. The usual loop is: **Cursor** (or another coding agent) reads/writes markdown here; **Obsidian** (optional) is the comfortable reader for `wiki/`.

### Daily loop (recommended)

1. **Open this folder in Cursor** as the project workspace (you already do this).
2. **Pin or habitually attach** `@AGENTS.md` so every chat follows ingest/query/lint rules.
3. **Query:** start from `@wiki/index.md` (or `@wiki`) plus `@raw/…` only when the wiki is thin or you need a verbatim passage. Ask in English; ask for answers **filed into `wiki/`** when you want compounding knowledge.
4. **Ingest:** after copying new files into `raw/`, run one chat per source (or one tight batch): *“Ingest `raw/…` per AGENTS.md.”*
5. **Git** (optional but useful): commit after a good wiki session so you have a local timeline of changes.

### Obsidian (browse + graph, same files)

1. Install [Obsidian](https://obsidian.md/) on the Mac.
2. **File → Open folder as vault…** and choose **this repository root** (the folder that contains `raw/`, `wiki/`, and `AGENTS.md`).
3. Keep Obsidian open beside Cursor: you see graph, backlinks, and `[[wikilinks]]` instantly when the agent edits the wiki.

From the repo root you can also run:

```bash
./scripts/open-obsidian-vault.sh
```

That tries to open this folder in Obsidian (falls back to revealing the folder in Finder if Obsidian is not installed).

### Optional: stronger local search (when `index.md` is not enough)

If the wiki grows large, add a **local** search tool the agent can call from the terminal, for example [qmd](https://github.com/tobi/qmd) (hybrid search over markdown on-device). Not required at small scale.

### Optional: fully local language models

Cursor’s chat typically uses whatever model you configure in Cursor (often cloud). If you need **models running only on your Mac**, use **Ollama** or **LM Studio** and a client that talks to them (e.g. local agent plugins, or run queries there and paste summaries back into this repo). The **files** (`raw/`, `wiki/`) stay the same regardless of which LLM edits them.

**CLI (no `@AGENTS.md` in chat):** from the repo root, install [Ollama](https://ollama.com/), pull a model (`ollama pull llama3.2`), then run **`./query.py "Your question"`** or **`./query.py --interactive`**. The script always loads **`AGENTS.md`** and all **`wiki/**/*.md`**, then calls Ollama’s local HTTP API. Optional: **`./query.py --raw-grep patroon "question"`** (requires `brew install ripgrep`) to attach matching lines from `raw/`.

### Plain preview (weak but zero-install)

`python3 -m http.server 8765` from the repo root, then open `http://localhost:8765/wiki/` — browsers do not render markdown as nicely as Obsidian.

## Safety

Do not invent facts not supported by sources or the existing wiki. Mark uncertainty (*appears*, *unclear from source*) and distinguish **inference** from **verbatim** content.