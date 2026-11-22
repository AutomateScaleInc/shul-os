# Torah Sanctuary / ShulOS — Epistemic & Source Foundation Standard

This document defines the non-negotiable foundation standard for all scripture,
commentary, Talmudic citation, liturgy, and AI-assisted study across this OS.

## The Three-Tier Separation Standard

### Tier 1 — Primary Verified Scripture (`PRIMARY_SCRIPTURE`)
- **Source of Record**: Local verbatim Hebrew & English Tanakh database
  (`data/torah.db` — 39 books, 23,206 verses) and verified coinciding
  cross-scripture parallels fetched verbatim from the same local corpus.
- **Rule**: Primary Scripture is always cited with exact book, chapter, and verse
  numbers and is **never altered, fabricated, or blurred** with later commentary.
- **Cross-Scripture Verification**: Whenever a passage echoes another verified
  biblical book (Torah ↔ Nevi'im / Prophets ↔ Ketuvim / Writings), coinciding
  verses are pulled directly from the verified local corpus so the reader sees
  how Scripture illuminates Scripture.

### Tier 2 — Cited Classical & Talmudic Interpretations (`CITED_INTERPRETATION`)
- **Sources**: Babylonian Talmud (*Bavli*, cited by tractate and folio, e.g.
  `Talmud Bavli, Chullin 91a`), Midrash Rabbah, and classical Jewish
  commentators (*Rashi, Ramban, Ibn Ezra, Sforno, Or HaChaim, Rashbam, Kli Yakar*).
- **Non-Exclusivity Rule**: Every Talmudic, Midrashic, or rabbinic reading MUST
  be explicitly framed and labeled as an **interpretation** — never presented as
  the only possible reading of the text.
- **Multi-Lens Requirement**: Whenever interpreting a verse or theme, the system
  must present **multiple distinct lenses** (e.g. *Peshat* / plain contextual
  reading alongside *Talmudic Aggadah* or differing classical commentators) so
  the learner sees the richness of honest inquiry rather than single-voice dogma.

### Tier 3 — Historical, Linguistic & Living Context (`CONTEXT_REFLECTION`)
- **Sources**: Ancient Near Eastern history, archaeology, Hebrew 3-letter root
  (*Shoresh*) linguistics, and contemporary ethical reflection (*"In Today's Terms"*).
- **Rule**: Always labeled cleanly as context or reflection, clearly separated
  from verbatim Scripture and classical citations.

## Enforcement
1. `scripture_foundation.py` hydrates all cross-scripture parallels verbatim from
   `torah.db` and pairs every Talmudic citation with explicit lens labels and
   alternative classical perspectives.
2. `ai_engine.py` embeds the Three-Tier Standard into every local & cloud AI
   system prompt.
3. The UI displays distinct tier badges (`📜 Primary Scripture`,
   `⚖️ Cited Interpretation (Non-Exclusive)`, `🧭 Context & Reflection`).
4. `tests/test_sanctuary.py` verifies source-standard compliance on every build.
