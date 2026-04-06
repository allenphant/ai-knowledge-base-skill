# AI Knowledge Base — Full Instructions

## Core Philosophy

Think of yourself as an extension of the user's learning process. When a human reads something new, they don't just store it in isolation — they connect it to what they already know, update outdated beliefs, and notice patterns across topics. This skill works the same way: every new piece of information should be woven into the existing knowledge fabric.

The key constraint: **the knowledge base will grow large**. You must never scan all notes in full. Instead, use the lightweight registry (`_registry.json`) to find relevant notes cheaply, then read only the ones that matter.

## Vault Location

The vault path is: `C:\Your\Path\To\Obsidian\AI-Knowledge`

On first use, if the vault is empty, initialize `_registry.json` and `_index.md` as described below.

### Vault Structure
```
AI-Knowledge/
├── _registry.json       # Lightweight index of ALL notes (the brain)
├── _index.md            # Human-readable master index for Obsidian
└── (all .md notes, flat structure)
```

---

## The Registry — Token-Efficient Knowledge Lookup

### Why a registry?

Reading 50 full notes to find connections would cost tens of thousands of tokens. Instead, `_registry.json` stores a compact summary of every note — enough to determine relevance without reading any note files.

| Knowledge base size | Without registry (read all) | With registry |
|---------------------|----------------------------|---------------|
| 10 notes | ~10,000 tokens | ~300 (index) + 2-3 reads ≈ **2,500** |
| 50 notes | ~50,000 tokens | ~700 + 3-5 reads ≈ **5,000** |
| 200 notes | ~200,000 tokens | ~2,000 + 3-5 reads ≈ **6,000** |

### Registry Schema

`_registry.json` is a single JSON file at the vault root:

```json
{
  "version": 1,
  "last_updated": "2026-03-31",
  "notes": [
    {
      "file": "crewai-overview.md",
      "title": "CrewAI Overview",
      "date": "2026-03-31",
      "type": "tool",
      "tags": ["ai-agents", "multi-agent", "framework", "python"],
      "concepts": ["multi-agent orchestration", "role-based agents", "task delegation"],
      "one_liner": "Python framework for orchestrating role-based AI agent teams",
      "relations": ["autogen-overview", "langchain-overview"]
    }
  ]
}
```

Field guide:
- **file**: filename (no path, all notes are in vault root)
- **type**: `article` | `tool` | `comparison` | `concept` | `news`
- **tags**: lowercase kebab-case, 3-7 tags per note. Use consistent vocabulary across notes.
- **concepts**: short phrases describing the key ideas — these are the semantic matching targets
- **one_liner**: one sentence that captures what this note is about. Keep under 100 characters.
- **relations**: filenames (without `.md`) of directly related notes

### How to use the registry

**When adding a new note:**

1. Read `_registry.json` (one read, cheap even at scale)
2. Match the new note's tags and concepts against existing entries
3. Only read full notes for entries with **2+ overlapping tags** or **1+ overlapping concept**
4. Typically this means reading 0-5 notes, not all of them
5. After writing the new note, append its entry to `_registry.json`
6. Update `relations` arrays in both the new entry AND matched existing entries

**When the user asks to update existing knowledge:**

1. Read `_registry.json`
2. Find the matching entry by title, tags, or concepts
3. Read only that note + its `relations` entries
4. Update as needed

---


---




---

## Phase 0.6: Dual-Mode Video Analysis (Knowledge vs. Visual)

When processing a video source, determine the analysis mode based on user preference or content type:

### Mode A: Knowledge-Centric (Deep Audio & Semantic Mode)
- **Goal**: Treat the video as a primary research source, focusing deeply on spoken words, underlying logic, and arguments.
- **Workflow**: 
    1. **Audio/Transcript Extraction**: Never rely just on metadata captions. Use `yt-dlp` to download the audio track (`-x --audio-format mp3`). If a direct transcript is unavailable, feed the audio directly to an Audio-to-Text (STT) model (like Gemini Native Audio or Whisper API).
    2. **NotebookLM-Style Deep Ingestion (MCP)**: If a NotebookLM MCP is configured, route the transcript there for synthesis. Otherwise, simulate NotebookLM's capability: treat the full transcript as a primary document.
    3. **Semantic Synthesis**: Do not provide a surface-level summary. Extract step-by-step methodologies, philosophical arguments, mentioned tools/concepts, and exact quotes. Ground every claim with timestamps if possible.

### Mode B: Visual-Centric (Vision Mode)
- **Goal**: Understand actions, aesthetics, and non-verbal cues.
- **Workflow**:
    1. Download video (low-res) using local tools if possible.
    2. Analyze using Multimodal Vision (describe scenes, OCR on-screen text, identify visual steps). A bundled local script is available at `C:\Users\raging\Desktop\Vibe_coding\Learning\vision_analyzer.py` (or bundled in `tools/vision/vision_analyzer.py` post-install).
    3. Format output as a "Visual Storyboard" or "Action Log" in Obsidian.

**Decision Logic**: 
During Phase 1 (Configuration), if a video URL is detected, add an extra choice:
- **Analysis Flavor**: "Knowledge (Text)" vs "Visual (Scenes)".




---

## Phase 0.7: Transcript Service Selection (Mode A Extensions)

If **Mode A (Knowledge-Centric)** is selected, ask the user for their preferred transcription engine:

### Option 1: NotebookLM MCP (Cloud)
- **Goal**: Use Google's specialized context-heavy reasoning.
- **Workflow**: 
    1. If a direct transcript is available, send it to the NotebookLM MCP.
    2. If not, download the audio and provide it as a source for the MCP tool.
    3. Use the MCP output for the final Obsidian note.

### Option 2: Local Whisper (Private/Offline)
- **Goal**: High-fidelity local transcription using the `faster-whisper-srt` tool.
- **Workflow**:
    1. Download the media file using `yt-dlp`.
    2. **Execute Local Tool**: Run `python C:\Users\raging\Desktop\Vibe_coding\video2srt\faster-whisper-srt\faster_whisper_srt.py [file_path] --model large-v3-turbo`.
    3. **Read SRT**: Find the generated `.srt` file in the same directory.
    4. **AI Synthesis**: Read the full SRT content, clean up the timestamps, and perform semantic indexing as described in Mode A.

**Updated Phase 1 (Secondary Configuration)**:
If Mode A is selected, ask:
- **Transcribe Engine**: "NotebookLM (Google)" or "Local Whisper (Fast-Whisper)".


## Phase 1: Research Discovery & Configuration (Optimized)

**Note on Tool Constraint:** The `ask_user` tool is limited to 4 questions per call. To gather comprehensive configuration, follow this multi-stage logic:

**Stage 1: Primary Configuration (4 questions)**
Ask (header: "Depth", "Compare", "Vault", "Slides"):
1. Depth: Shallow / Medium / Deep
2. Compare: Yes / No
3. Vault: Yes / No
4. Slides: Yes / No

**Stage 2: Secondary Configuration (Ask ONLY if needed)**
If `Slides=Yes` or `Deep` is selected, trigger a second `ask_user` call for:
1. Language: Traditional Chinese / English / Match Input
2. Vibe (for slides): Professional / Creative / Calm / Inspired
3. Specific focus areas: (Text input)

Based on answers:
- If **Deep** or **Compare=Yes**: Must run `google_web_search` even for URL inputs.
- If **Vault=Yes**: Perform full Knowledge Synthesis (Registry lookup/update).
- If **Slides=Yes**: Once research is complete, transition immediately to Phase 2 of Presentation Mode.




---

## Phase 0.5: Multimodal Video Handling (YT, Reels, Threads)

When a URL points to a video platform (YouTube, Instagram, Threads, TikTok):

### 1. Extraction Strategy
- **YouTube**: Use `google_web_search` to find transcripts or metadata. If I have internal access to fetch the video stream, prioritize direct analysis of the visual/audio content.
- **Instagram/Threads/TikTok**: These are visual-first. Treat the URL as a "Visual Source". Use the `web_fetch` or direct vision capabilities to:
    - Describe the visual actions/scenes.
    - Transcribe any visible text (OCR).
    - Summarize the audio/speech if available.

### 2. NotebookLM-Style Synthesis
- Do not just summarize the video. Treat it as a "Primary Source".
- Extract "Key Citations" (Timestamps or Scene Descriptions) to support any claims in the note.
- If the video is a tutorial, convert visual steps into a structured "Action Plan" in the Obsidian note.

### 3. Integration with Slides
- If `Slides=Yes`, the generated presentation must include a "Visual Recap" section, translating the video's aesthetic and key frames into the chosen slide style.


## Input Handling

The user may provide input in several ways. Detect and handle each:

### URL Input
Supported sources:
- **Articles/Blog posts** — Medium, Substack, personal blogs, company blogs
- **Social media** — Twitter/X, Instagram, Threads, LinkedIn, Facebook, Reddit
- **GitHub repos** — README, description, stars, language, recent activity
- **Product pages** — Landing pages, pricing pages, documentation
- **Papers** — arXiv, research papers
- **Video descriptions** — YouTube (fetch page metadata, not the video itself)


### URL Fetching Strategy (ENFORCED)

**Decision rule (NON-NEGOTIABLE):** If the URL domain is from a social platform (`threads.com`, `x.com`, `twitter.com`, `instagram.com`, `facebook.com`, `linkedin.com`, `reddit.com`, `youtube.com`), you **MUST** prefix it with `https://r.jina.ai/` and use the `web_fetch` tool. Do not attempt direct fetch for these domains as they will fail or return incomplete shells.


Social media platforms (Threads, Twitter/X, Instagram, Facebook, LinkedIn) render content via JavaScript, so direct HTTP fetching usually returns empty shells. Use this two-tier strategy:

**Tier 1 — Jina Reader API (preferred for social media & JS-heavy sites)**
Prefix any URL with `https://r.jina.ai/` to get clean, LLM-friendly Markdown output.
Examples:
- Threads: `https://r.jina.ai/https://www.threads.com/@user/post/ID`
- Twitter/X: `https://r.jina.ai/https://x.com/user/status/ID`
- Instagram: `https://r.jina.ai/https://www.instagram.com/p/ID`
- Facebook: `https://r.jina.ai/https://www.facebook.com/user/posts/ID`
- LinkedIn: `https://r.jina.ai/https://www.linkedin.com/posts/ID`
- Any JS-heavy page: `https://r.jina.ai/<full-url>`

Jina Reader renders the page in a headless browser and returns the extracted content as Markdown. No API key required for basic usage.

**Tier 2 — Direct fetch (for static sites)**
For simple blog posts, documentation, arXiv papers, and other server-rendered pages, fetch the URL directly using available web/fetch tools. This is faster and doesn't depend on an external service.

**Decision rule:** If the URL domain is any of these, use Jina Reader (Tier 1):
`threads.com`, `x.com`, `twitter.com`, `instagram.com`, `facebook.com`, `linkedin.com`, `reddit.com`, `youtube.com`

For all other URLs, try direct fetch first (Tier 2). If the result is empty or contains only navigation/boilerplate, fall back to Jina Reader.

When the user pastes a URL (with or without commentary), fetch it and proceed to processing.

### Embedded Reference Extraction

After fetching any URL (especially social media posts), scan the content for references to:
- **GitHub repos** — URLs like `github.com/org/repo`, or mentions like "check out the repo at..."
- **Papers** — arXiv links (`arxiv.org/abs/...`), DOI links, or mentions like "based on the paper..."
- **Product/tool pages** — official sites mentioned in the post
- **Other linked posts or articles** — URLs embedded in the content

When embedded references are found, **fetch and research them too** — they are part of the same research unit. The final note should synthesize the post AND its referenced materials together, not just summarize the post in isolation.

How to handle this:
1. Fetch the primary URL (the post)
2. Extract all embedded links and references from the content
3. Fetch each reference (use appropriate tier — Jina for social media, direct for repos/papers)
4. For GitHub repos: read the README, note stars/language/recent activity, understand what the project does
5. For papers: read the abstract, key findings, and methodology
6. Synthesize everything into a single cohesive note — the post provides context and opinion, the references provide substance
7. In the note's `## Sources` section, list all fetched URLs (primary + references)

This means a single Threads post about a new AI paper could result in a note that covers:
- What the post author said and why they think it matters
- What the paper actually proposes (from reading the paper itself)
- What the linked repo does (from reading the README)
- How all of this connects to existing knowledge in the vault

### Topic/Question Input
The user may ask about a topic without a URL:
- "What is CrewAI?"
- "Compare LangChain vs LlamaIndex"
- "What's new in the RAG space?"

Use web search to find current information, then process.

### Update Request
The user may ask to update or revisit existing knowledge:
- "Update my notes on vector databases"
- "What's changed since I last looked at Anthropic's API?"

Read the registry, find the relevant entry, read that note, then research what's new.

---

## Research Depth Levels

Every request operates at one of three depths. If the user doesn't specify, default to **medium**. The user can request a specific depth with phrases like "quick summary", "just a glance" (shallow), "look into this" (medium), or "deep dive", "full comparison" (deep).

### Shallow — Quick Assessment
- Use **only** existing registry + matched notes + the provided URL content
- No external searches beyond fetching the given URL
- Fast synthesis: what is this, why does it matter, how does it connect to what we already know
- Output: concise note (under 100 lines)
- Best for: "I saw this link, what's it about?"

### Medium — Verified Research
- Fetch the URL content AND run web searches to verify claims and find additional context
- Cross-reference with registry-matched notes (read only the relevant ones)
- Check: Is what this article claims actually true? Are there counterpoints?
- Output: thorough note with sources (100-200 lines)
- Best for: "I heard about this tool, tell me about it"

### Deep — Comprehensive Analysis
- Everything in Medium, plus:
- Actively search for competing/similar products, repos, and services
- Build a comparison covering:
  - **Feature comparison** — what each product does and doesn't do
  - **Pricing / execution cost** — free tier, paid plans, infrastructure costs, API pricing
  - **Scalability** — can it handle production workloads? what are the limits?
  - **Community & ecosystem** — GitHub stars, contributors, documentation quality, community size
  - **Maturity** — how long has it been around, how stable is it
- Output: detailed analysis + comparison table (200+ lines)
- Best for: "Compare X vs Y vs Z", "What are my options for doing X?"

---

## Knowledge Synthesis — The Update Loop

This is the core mechanism. It runs for every note at every depth level, but stays cheap thanks to the registry.

### Step-by-step:

1. **Read `_registry.json`** — one file, always the first step
2. **Find matches** — compare new note's tags/concepts against registry:
   - **Strong match**: 2+ overlapping tags OR 1+ overlapping concept → read full note
   - **Weak match**: 1 overlapping tag → note it in Connections but don't read full note
   - **No match**: skip entirely
3. **Read only strong matches** — typically 0-5 notes
4. **Write the new note** — using the appropriate template (see Output Format)
5. **Add Connections section** to the new note:
   - Strong matches: `[[note-title]] — specific explanation of how they relate`
   - Weak matches: `[[note-title]] — possibly related (shared tag: #tag-name)`
6. **Update matched notes** — for strong matches only, if the new info materially extends them, add to their `## Updates` section:
   ```markdown
   - **2026-03-31**: [[New Note Title]] — brief description of new context
   ```
7. **Update `_registry.json`**:
   - Append new entry
   - Update `relations` arrays on matched entries
8. **Update `_index.md`** — add to Recent Additions and appropriate category

### What "materially extends" means

Don't update old notes for trivial connections. Update only when:
- The new information contradicts something in the old note
- The new information adds a significant capability, pricing change, or ecosystem shift
- A new competitor or alternative has emerged that the old note should reference

This keeps the knowledge base clean and avoids unnecessary file writes.

---

## Output Format

All notes are Obsidian-compatible Markdown with YAML frontmatter.

### Article / General Note Template
```markdown
---
title: "Note Title"
date: 2026-03-31
source: "https://original-url.com"
source_type: article | tweet | thread | repo | product | paper | video
depth: shallow | medium | deep
tags:
  - ai
  - relevant-tag
---

# Note Title

## TL;DR
One-paragraph summary of the key takeaway.

## Key Points
- Bullet points of the main ideas
- Each point should be self-contained and useful on its own

## Details
Longer-form explanation organized by subtopic.

## Connections
- [[Related Note 1]] — how it relates
- [[Related Note 2]] — how it relates

## Sources
- [Source title](url)

## Updates
(future updates to this note go here)
```

### Tool / Product Note Template
```markdown
---
title: "Tool Name"
date: 2026-03-31
source: "https://tool-url.com"
source_type: tool
category: "e.g., LLM Framework, Vector DB, Agent Platform"
depth: shallow | medium | deep
tags:
  - ai
  - tool
  - category-tag
---

# Tool Name

## TL;DR
What it is in one sentence.

## What It Does
Core functionality and use cases.

## Key Features
- Feature 1
- Feature 2

## Pricing & Cost
(if available)

## Scalability
(if researched)

## Connections
- [[Related Tool]] — how it compares or relates

## Sources
- [Source](url)

## Updates
```

### Comparison Note Template
```markdown
---
title: "Comparison: X vs Y vs Z"
date: 2026-03-31
source_type: comparison
depth: deep
tags:
  - ai
  - comparison
  - category-tag
---

# Comparison: X vs Y vs Z

## TL;DR
One-paragraph verdict.

## Comparison Table

| Aspect | X | Y | Z |
|--------|---|---|---|
| Core Purpose | ... | ... | ... |
| Pricing | ... | ... | ... |
| Scalability | ... | ... | ... |
| Community | ... | ... | ... |
| Maturity | ... | ... | ... |

## Detailed Analysis

### X
...

### Y
...

### Z
...

## Verdict & Recommendation
When to choose each option.

## Connections
- [[Related Note]] — context

## Sources

## Updates
```

---

## File Naming Convention

Use kebab-case based on the title:
- `crewai-overview.md`
- `langchain-vs-llamaindex-comparison.md`
- `openai-gpt4o-announcement-2026-03.md`

Include date fragments only when timeliness matters (announcements, news).

## The `_index.md` File

Maintain a human-readable master index for browsing in Obsidian:

```markdown
# AI Knowledge Base Index

## Recent Additions
- [[note-title]] — one-line description (2026-03-31)

## By Category
### LLM Frameworks
- [[langchain-overview]]
- [[llamaindex-overview]]

### Agent Platforms
- [[crewai-overview]]

(categories grow organically as notes are added)
```

---

## Workflow Summary

When the user triggers this skill:

1. **Detect input type** (URL, question, update request)
2. **Determine depth** (shallow/medium/deep, ask if ambiguous)
3. **Check vault** (if empty, initialize `_registry.json` and `_index.md`)
4. **Fetch & research** (appropriate to depth level)
5. **Read `_registry.json`** — find related notes by tag/concept overlap
6. **Read only matched notes** (0-5 full reads, not all notes)
7. **Generate note** (using appropriate template)
8. **Synthesize** (add connections, update matched notes if materially relevant)
9. **Update `_registry.json`** and `_index.md`
10. **Report to user** — brief summary:
    - New note path
    - Related notes found and/or updated
    - Suggested next steps ("want me to go deeper?" / "related topics to explore")


---

## Presentation Output Mode (Integrated with Frontend Slides)

When the user requests a presentation, slide deck, or HTML summary of a topic:

### 1. Source Discovery
- Read `_registry.json` to find all notes matching the topic or tags.
- Read the full content of the top 3-5 most relevant notes.
- Synthesize these notes into a 10-20 page slide outline.

### 2. Style Selection (Mandatory Flow)
- Activate the `frontend-slides` logic.
- **Step A:** Ask the user for Purpose, Length, and general Mood/Vibe (e.g., Professional, Creative, Calm, Inspired). Do NOT ask them to pick a specific final style preset yet.
- **Step B:** Read `{{SKILL_DIR}}\tools\frontend-slides\STYLE_PRESETS.md`. Based on the chosen Vibe, select 3 matching style presets. Physically generate 3 separate HTML preview files in the temporary directory and open ALL 3 of them in the user's browser.
- **Step C:** AFTER the previews are opened, use a NEW `ask_user` call to ask the user which of the 3 previewed styles they prefer (e.g., Preview 1, Preview 2, or Preview 3). DO NOT use text-based choice menus for the final style selection until the user has seen the rendered HTML.

### 3. HTML Generation
- Use `C:\Users\raging\.gemini\skills\frontend-slides\html-template.md` as the base.
- Include the full contents of `{{SKILL_DIR}}\tools\frontend-slides\viewport-base.css` in the `<style>` block.
- Inject the synthesized content into the slides, following the Content Density Limits defined in Frontend Slides instructions.
- Add Inline Editing support by default.

### 4. Delivery
- Save the final presentation as `[topic]-presentation.html` in the current directory.
- Offer to deploy to Vercel or export to PDF using the scripts in `{{SKILL_DIR}}\tools\frontend-slides\scripts\`.
