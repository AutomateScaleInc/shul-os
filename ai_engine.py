#!/usr/bin/env python3
"""
Torah Sanctuary — Hybrid Local (Ollama) + Optional Cloud AI Engine with Grounded RAG.
Every answer is anchored in verbatim local Hebrew + English Tanakh, Rashi, Ramban,
Ibn Ezra, Sforno, Pirkei Avot, Midrash Rabbah, and curated Storyteller/History dossiers.
"""

import json
import os
import pathlib
import urllib.error
import urllib.request

import torah_db
import scripture_foundation

BASE_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "synagogue_name": "The European Synagogue · Torah Sanctuary",
    "ollama_url": "http://127.0.0.1:11434",
    "ollama_model": "qwen2.5:1.5b",
    "cloud_provider": "none",  # none | openai | anthropic | gemini
    "cloud_model": "",
    "cloud_api_key": "",
    "calendar_ics_url": "",
    "mailing_webhook_url": "",
    "voice_profile": "grand_narrator",
    "auto_speak": True,
    "presence_sleep_minutes": 5,
    "default_theme": "sanctuary",  # sanctuary | parchment
    "os_color_temp_sync": True,
    "max_sanctuary_volume": 0.42,
    "scribe_enabled": True,
    "scribe_online_ingest": True,
    "broadcast_public_base_url": "",
    "broadcast_follow_url": "",
    "public_sanctuary_url": "",
    "donation_checkout_url": "https://www.theshul.eu",
    "syndication_webhook_url": "",
    "mesh_node_type": "synagogue",
    "mesh_camera_url": "",
    "mesh_auto_receive": True,
    "location": {
        "city": "Brussels, Belgium",
        "lat": 50.8503,
        "lon": 4.3517,
        "tz": "Europe/Brussels",
        "elevation_m": 58,
        "candle_lighting_offset_min": 18,
        "havdalah_deg": 8.5,
        "in_israel": False,
    },
}

FOUNDATION_GUARDRAIL = (
    " STRICT SOURCE STANDARD: Always separate (1) PRIMARY VERIFIED SCRIPTURE (verbatim Tanakh & coinciding cross-scripture parallels from local source files) "
    "from (2) CITED INTERPRETATIONS (Talmud Bavli tractate/folio, Rashi, Ramban, Ibn Ezra, Sforno, Or HaChaim, Midrash). "
    "Treat every Talmudic or rabbinic reading explicitly as ONE CITED INTERPRETATION — NEVER the sole interpretation — and present at least TWO distinct perspectives "
    "(e.g., plain Peshat reading alongside a cited Talmudic/Midrashic or differing classical commentator's view). Never invent verses or tractate citations."
)

MODE_INSTRUCTIONS = {
    "scholar": (
        "You are a warm, deeply learned Torah & Tanakh scholar at a community synagogue study station. "
        "Anchor first in exact verbatim Scripture and coinciding verified biblical parallels, then explore multiple classical lenses "
        "(plain Peshat text, cited Babylonian Talmud tractates, Rashi, Or HaChaim, Ramban, Ibn Ezra, Sforno, Kli Yakar, Rashbam, Midrash) "
        "always clarifying which statements are verbatim Scripture and which are cited interpretations." + FOUNDATION_GUARDRAIL
    ),
    "storyteller": (
        "You are a beloved synagogue Torah storyteller speaking warmly to kids, families, and newcomers. "
        "Tell the story vividly and faithfully from the exact Torah/Tanakh verses provided, note clearly when sharing a charming rabbinic/Talmudic interpretation "
        "('One classical Talmudic/Midrashic interpretation adds...'), and end with 2 thoughtful Shabbat-table questions." + FOUNDATION_GUARDRAIL
    ),
    "history": (
        "You are a respectful, authoritative biblical historian and archaeologist at a synagogue learning center. "
        "Explain the historical era, coinciding biblical parallels, Ancient Near East context, Second Temple / Dead Sea Scrolls textual history, "
        "and classical rabbinic/Talmudic perspectives clearly distinguished from verified Scripture." + FOUNDATION_GUARDRAIL
    ),
    "all": (
        "You are Torah Sanctuary / ShulOS — a deeply knowledgeable, warm Torah & Tanakh study guide built to a rigorous source standard. "
        "Structure your response clearly into: "
        "(1) **📜 Primary Verified Scripture & Coinciding Parallels** (exact verse citations from local source files), "
        "(2) **⚖️ Cited Interpretations — Multiple Lenses** (cite Talmud Bavli tractates & classical commentators like Rashi, Ibn Ezra, Ramban, Or HaChaim explicitly as interpretations, contrasting at least two views), and "
        "(3) **🧭 Context & Living Reflection** (historical setting & applying this in today's terms)." + FOUNDATION_GUARDRAIL
    ),
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                cfg.update(saved)
        except Exception:
            pass
    # Also allow env overrides without storing keys on disk
    for env_k, cfg_k in [
        ("TORAH_CLOUD_PROVIDER", "cloud_provider"),
        ("TORAH_CLOUD_MODEL", "cloud_model"),
        ("TORAH_CLOUD_API_KEY", "cloud_api_key"),
        ("TORAH_OLLAMA_MODEL", "ollama_model"),
    ]:
        if os.environ.get(env_k):
            cfg[cfg_k] = os.environ[env_k]
    return cfg


def save_config(updates: dict) -> dict:
    cfg = load_config()
    allowed = set(DEFAULT_CONFIG.keys())
    for k, v in updates.items():
        if k in allowed:
            cfg[k] = v
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except Exception:
        pass
    return cfg


def check_ollama_status(cfg: dict = None) -> dict:
    cfg = cfg or load_config()
    url = cfg.get("ollama_url", "http://127.0.0.1:11434").rstrip("/")
    model = cfg.get("ollama_model", "qwen2.5:3b")
    try:
        with urllib.request.urlopen(f"{url}/api/tags", timeout=2.0) as r:
            data = json.loads(r.read().decode("utf-8"))
        models = [m.get("name", "") for m in data.get("models", [])]
        ready = any(m == model or m.startswith(model + ":") or model.split(":")[0] in m for m in models)
        return {"online": True, "models": models, "target_model": model, "model_ready": ready}
    except Exception as e:
        return {"online": False, "models": [], "target_model": model, "model_ready": False, "error": str(e)}


def build_rag_context(question: str, mode: str = "all", compact: bool = False) -> tuple[str, dict]:
    """Retrieve verbatim local verses, diverse classical commentaries, parashiyot, and curated / Mini-Orca study sheets.

    When compact=True (local Ollama CPU), allocates balanced budgets across verses, diverse commentators,
    and study sheets so Living Scribe dossiers & Or HaChaim/Ramban notes are NEVER truncated away!
    """
    hits = torah_db.search_all(question, limit_verses=6, limit_comm=6, limit_docs=3)
    parts = []
    sources = {"verses": [], "commentaries": [], "documents": [], "parashiyot": []}

    v_max = 3 if compact else 6
    c_max = 4 if compact else 6
    c_snip = 260 if compact else 550
    d_max = 1 if compact else 2
    d_snip = 620 if compact else 1100

    # Exact verse matches first
    seen_refs = set()
    for v in hits["exact_verses"][:6] + hits["verses"][:5]:
        if v["ref"] in seen_refs:
            continue
        seen_refs.add(v["ref"])
        sources["verses"].append(v)
        if len(sources["verses"]) <= v_max:
            en_v = (v["en_text"] or "")[:240 if compact else 500]
            if compact:
                parts.append(f"[VERSE {v['ref']}] {en_v}")
            else:
                parts.append(f"[VERSE {v['ref']}]\nEnglish: {en_v}\nHebrew: {v['he_text']}")

    for c in hits["commentaries"][:6]:
        sources["commentaries"].append(c)
        if len(sources["commentaries"]) <= c_max:
            en_snip = (c["en_text"] or "")[:c_snip]
            parts.append(f"[COMMENTARY {c['commentator']} on {c['target_ref']}] {en_snip}")

    for d in hits["documents"][:2]:
        sources["documents"].append({
            "slug": d["slug"],
            "category": d["category"],
            "title": d["title"],
            "he_title": d["he_title"],
            "subtitle": d["subtitle"],
            "refs": d["refs"],
        })
        if len(sources["documents"]) <= d_max:
            if mode == "storyteller" and d.get("kid_story"):
                parts.append(f"[STORY DOSSIER: {d['title']} ({d['refs']})]\n{d['kid_story'][:d_snip]}")
            else:
                label = "LIVING SCRIBE STUDY SHEET" if (d.get("category") or "").startswith("scribe_") else f"KNOWLEDGE DOSSIER ({d['category']})"
                parts.append(f"[{label}: {d['title']} ({d['refs']})]\n{(d.get('body_md') or '')[:d_snip]}")

    for p in hits["parashiyot"][:2]:
        sources["parashiyot"].append(p)
        if len(sources["parashiyot"]) <= (1 if compact else 2):
            parts.append(f"[PARASHAH {p['en_name']} ({p['he_name']}, {p['ref']}) · Haftarah: {p['haftarah_ref']}] {(p.get('summary') or '')[:260]}")

    try:
        p_slug = (sources["parashiyot"][0].get("slug") if sources["parashiyot"] else "") or ""
        f_txt = scripture_foundation.format_for_ai_rag(question, parasha_slug=p_slug)
        if f_txt:
            parts.append(f_txt[:420 if compact else 1400])
    except Exception:
        pass

    max_len = 2480 if compact else 7200
    context_str = "\n\n".join(parts)[:max_len]
    return context_str, sources


def _stream_cloud_openai(cfg: dict, system_prompt: str, messages: list):
    model = cfg.get("cloud_model") or "gpt-4o-mini"
    payload = {
        "model": model,
        "stream": True,
        "temperature": 0.4,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['cloud_api_key']}",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            body = line[5:].strip()
            if body == "[DONE]":
                break
            try:
                obj = json.loads(body)
                delta = obj["choices"][0]["delta"].get("content")
                if delta:
                    yield delta
            except Exception:
                pass


def _stream_cloud_anthropic(cfg: dict, system_prompt: str, messages: list):
    model = cfg.get("cloud_model") or "claude-3-5-sonnet-latest"
    payload = {
        "model": model,
        "max_tokens": 1200,
        "stream": True,
        "system": system_prompt,
        "messages": messages,
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": cfg["cloud_api_key"],
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            try:
                obj = json.loads(line[5:].strip())
                if obj.get("type") == "content_block_delta":
                    txt = (obj.get("delta") or {}).get("text")
                    if txt:
                        yield txt
            except Exception:
                pass


def _stream_cloud_gemini(cfg: dict, system_prompt: str, messages: list):
    model = cfg.get("cloud_model") or "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={cfg['cloud_api_key']}"
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1400},
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for cand in data.get("candidates", []):
        for part in (cand.get("content") or {}).get("parts", []):
            if part.get("text"):
                yield part["text"]


def _stream_ollama(cfg: dict, system_prompt: str, messages: list):
    url = cfg.get("ollama_url", "http://127.0.0.1:11434").rstrip("/") + "/api/chat"
    model = cfg.get("ollama_model", "qwen2.5:1.5b")
    # Keep local CPU prefill crisp on Sentinel's 2013 i5-4570R (compact RAG already packs every category cleanly!)
    local_sys = system_prompt[:3100]
    payload = {
        "model": model,
        "stream": True,
        "keep_alive": "30m",
        "options": {"temperature": 0.35, "num_ctx": 2048, "num_predict": 440},
        "messages": [{"role": "system", "content": local_sys}] + messages,
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8", "ignore").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                tok = (obj.get("message") or {}).get("content")
                if tok:
                    yield tok
                if obj.get("done"):
                    break
            except Exception:
                pass


def _fallback_verbatim_answer(question: str, sources: dict) -> str:
    lines = ["Here are the matching verified passages from our local Torah & Tanakh library:\n"]
    if sources["documents"]:
        d = sources["documents"][0]
        full = torah_db.get_document(d["slug"])
        if full:
            lines.append(f"### {full['title']} ({full['he_title']})\n{full['body_md'][:1800]}\n")
    if sources["verses"]:
        lines.append("### Scriptural Verses")
        for v in sources["verses"][:5]:
            lines.append(f"- **{v['ref']}**: {v['en_text']}\n  *{v['he_text']}*")
    if sources["commentaries"]:
        lines.append("\n### Classical Commentators")
        for c in sources["commentaries"][:4]:
            lines.append(f"- **{c['commentator']} on {c['target_ref']}**: {c['en_text'][:400]}")
    if len(lines) == 1:
        lines.append(f"No direct keyword matches were found for '{question}'. Try naming a Torah book/verse (e.g., *Genesis 1:1*, *Exodus 20*, *Psalm 23*), a weekly Parashah, or a story like *Burning Bush*, *Ruth*, or *Dead Sea Scrolls*.")
    return "\n".join(lines)


def stream_answer(question: str, mode: str = "all", history: list = None):
    """
    Generator yielding structured event dicts:
      {"type": "sources", "sources": ..., "backend": ...}
      {"type": "token", "text": "..."}
      {"type": "done", "backend": "..."}
    """
    cfg = load_config()
    mode = mode if mode in MODE_INSTRUCTIONS else "all"
    cloud_prov = (cfg.get("cloud_provider") or "none").lower().strip()
    cloud_key = (cfg.get("cloud_api_key") or "").strip()
    use_cloud = cloud_prov in ("openai", "anthropic", "gemini") and bool(cloud_key)

    context_str, sources = build_rag_context(question, mode=mode, compact=not use_cloud)

    system_prompt = (
        MODE_INSTRUCTIONS[mode]
        + "\n\nGROUNDING SOURCES FROM LOCAL SYNAGOGUE LIBRARY (use these exact citations & facts; do not fabricate quotes):\n"
        + (context_str or "(No direct local excerpt matched — answer faithfully from verified Torah/Tanakh scholarship and note the relevant books/chapters.)")
    )

    messages = []
    for h in (history or [])[-6:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": str(h["content"])[:1500]})
    messages.append({"role": "user", "content": question})

    backend_used = None
    yield {"type": "sources", "sources": sources}

    # 1. Try optional Cloud API if configured
    if use_cloud:
        try:
            gen = (
                _stream_cloud_openai(cfg, system_prompt, messages)
                if cloud_prov == "openai"
                else _stream_cloud_anthropic(cfg, system_prompt, messages)
                if cloud_prov == "anthropic"
                else _stream_cloud_gemini(cfg, system_prompt, messages)
            )
            emitted = False
            for tok in gen:
                emitted = True
                yield {"type": "token", "text": tok}
            if emitted:
                backend_used = f"cloud:{cloud_prov}"
                yield {"type": "done", "backend": backend_used}
                return
        except Exception:
            pass

    # 2. Local Offline Ollama
    try:
        emitted = False
        for tok in _stream_ollama(cfg, system_prompt, messages):
            emitted = True
            yield {"type": "token", "text": tok}
        if emitted:
            backend_used = f"local:ollama/{cfg.get('ollama_model', 'qwen2.5:3b')}"
            yield {"type": "done", "backend": backend_used}
            return
    except Exception:
        pass

    # 3. Verbatim Local Library Fallback (never fails even if Ollama is restarting)
    yield {"type": "token", "text": _fallback_verbatim_answer(question, sources)}
    yield {"type": "done", "backend": "local:verbatim-library"}


def ask_sync(question: str, mode: str = "all", history: list = None) -> dict:
    chunks = []
    sources = {}
    backend = ""
    for ev in stream_answer(question, mode=mode, history=history):
        if ev["type"] == "sources":
            sources = ev["sources"]
        elif ev["type"] == "token":
            chunks.append(ev["text"])
        elif ev["type"] == "done":
            backend = ev["backend"]
    return {"answer": "".join(chunks), "sources": sources, "backend": backend}
