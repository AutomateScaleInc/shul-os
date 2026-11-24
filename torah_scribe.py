#!/usr/bin/env python3
"""Torah Sanctuary OS — Mini-Orca: Autonomous Living Torah Scribe & Library Refiner.

Continuously enriches and strengthens this Torah Sanctuary node in the background:
1. Authoritative Classical Commentary Expansion (when online): incrementally downloads
   public-domain Sefaria classical commentaries (Or HaChaim, Kli Yakar, Chizkuni, Rashbam,
   Metzudat David) directly into local SQLite + FTS5 — growing from 21,000 -> 45,000+ entries.
2. Autonomous Local-Ollama Parashah & Tanakh Dossier Authoring (100% offline):
   Reads verbatim Hebrew/English verses + Rashi/Ramban/Sforno/Or HaChaim from torah.db,
   synthesizes warm, faithful "In Today's Terms" takeaways, kid/family stories, and
   Shabbat-table discussion guides, and indexes them back into FTS5 so the node's RAG AI
   becomes measurably smarter and deeper every single day.
3. Database Integrity & Calendar Maintenance: keeps FTS5 optimized and Brussels/Shul feeds fresh.
4. Respects Shabbat & Yom Tov Stillness: automatically rests from Candle Lighting to Havdalah
   (unless explicitly triggered with --force for testing/demonstration).
"""
import datetime
import fcntl
import hashlib
import html
import json
import os
import pathlib
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import ai_engine
import sacred_astronomy
import sacred_books
import shul_events
import torah_db

DB_PATH = torah_db.DB_PATH
LOCK_PATH = BASE_DIR / "data" / "torah-scribe.lock"
STATE_PATH = BASE_DIR / "data" / "scribe-state.json"

# Classical Sefaria commentaries queued for polite incremental offline ingestion
COMMENTARY_EXPANSION_QUEUE = [
    ("Or HaChaim", "Or HaChaim on Genesis", "Genesis"),
    ("Or HaChaim", "Or HaChaim on Exodus", "Exodus"),
    ("Or HaChaim", "Or HaChaim on Leviticus", "Leviticus"),
    ("Or HaChaim", "Or HaChaim on Numbers", "Numbers"),
    ("Or HaChaim", "Or HaChaim on Deuteronomy", "Deuteronomy"),
    ("Rashi", "Rashi on Psalms", "Psalms"),
    ("Rashi", "Rashi on Proverbs", "Proverbs"),
    ("Rashi", "Rashi on Ruth", "Ruth"),
    ("Rashi", "Rashi on Esther", "Esther"),
    ("Rashi", "Rashi on Isaiah", "Isaiah"),
    ("Rashi", "Rashi on Hosea", "Hosea"),
    ("Rashi", "Rashi on Jonah", "Jonah"),
    ("Rashi", "Rashi on Joshua", "Joshua"),
    ("Rashi", "Rashi on Judges", "Judges"),
    ("Rashi", "Rashi on I Samuel", "I Samuel"),
    ("Rashi", "Rashi on II Samuel", "II Samuel"),
    ("Kli Yakar", "Kli Yakar on Genesis", "Genesis"),
    ("Kli Yakar", "Kli Yakar on Exodus", "Exodus"),
    ("Kli Yakar", "Kli Yakar on Leviticus", "Leviticus"),
    ("Kli Yakar", "Kli Yakar on Numbers", "Numbers"),
    ("Kli Yakar", "Kli Yakar on Deuteronomy", "Deuteronomy"),
    ("Chizkuni", "Chizkuni, Genesis", "Genesis"),
    ("Chizkuni", "Chizkuni, Exodus", "Exodus"),
    ("Chizkuni", "Chizkuni, Leviticus", "Leviticus"),
    ("Chizkuni", "Chizkuni, Numbers", "Numbers"),
    ("Chizkuni", "Chizkuni, Deuteronomy", "Deuteronomy"),
    ("Rashbam", "Rashbam on Genesis", "Genesis"),
    ("Rashbam", "Rashbam on Exodus", "Exodus"),
    ("Rashbam", "Rashbam on Leviticus", "Leviticus"),
    ("Rashbam", "Rashbam on Numbers", "Numbers"),
    ("Rashbam", "Rashbam on Deuteronomy", "Deuteronomy"),
    ("Metzudat David", "Metzudat David on Joshua", "Joshua"),
    ("Metzudat David", "Metzudat David on Judges", "Judges"),
    ("Metzudat David", "Metzudat David on I Samuel", "I Samuel"),
    ("Metzudat David", "Metzudat David on II Samuel", "II Samuel"),
    ("Metzudat David", "Metzudat David on Isaiah", "Isaiah"),
    ("Metzudat David", "Metzudat David on Hosea", "Hosea"),
    ("Metzudat David", "Metzudat David on Psalms", "Psalms"),
    ("Metzudat David", "Metzudat David on Proverbs", "Proverbs"),
]

TAG_RE = re.compile(r"<[^>]+>")


def clean_html(s) -> str:
    if not s:
        return ""
    if isinstance(s, list):
        return " ".join(clean_html(x) for x in s if x).strip()
    txt = TAG_RE.sub("", str(s))
    txt = html.unescape(txt)
    return re.sub(r"\s+", " ", txt).strip()


def ensure_scribe_tables():
    with torah_db.get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scribe_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                mission TEXT NOT NULL,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                summary TEXT NOT NULL,
                items_added INTEGER NOT NULL DEFAULT 0,
                duration_s REAL NOT NULL DEFAULT 0.0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scribe_checked_chapters (
                commentator TEXT NOT NULL,
                target_book TEXT NOT NULL,
                chapter INTEGER NOT NULL,
                PRIMARY KEY (commentator, target_book, chapter)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shul_facts (
                slug TEXT PRIMARY KEY,
                category TEXT NOT NULL DEFAULT 'community',
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'shul_os',
                confidence REAL NOT NULL DEFAULT 0.9,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dream_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                hebrew_date TEXT NOT NULL DEFAULT '',
                parasha_slug TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                resource_json TEXT NOT NULL DEFAULT '{}',
                needs_json TEXT NOT NULL DEFAULT '[]',
                wants_json TEXT NOT NULL DEFAULT '[]',
                dream_plan TEXT NOT NULL DEFAULT '',
                new_facts_added INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS website_sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                website_url TEXT NOT NULL DEFAULT '',
                website_status TEXT NOT NULL DEFAULT 'skipped',
                website_note TEXT NOT NULL DEFAULT '',
                ics_events_synced INTEGER NOT NULL DEFAULT 0,
                rss_items_synced INTEGER NOT NULL DEFAULT 0,
                facts_updated INTEGER NOT NULL DEFAULT 0,
                summary TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.commit()


def upsert_shul_fact(slug: str, category: str, title: str, content: str, source: str = "shul_os", confidence: float = 0.9) -> bool:
    """Persist a contextual synagogue/community fact and index it into documents_fts for local RAG."""
    ensure_scribe_tables()
    clean_slug = re.sub(r"[^a-z0-9\-]+", "-", (slug or "").lower()).strip("-")[:80]
    if not clean_slug or not title or not content:
        return False
    ts = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    title_c = re.sub(r"\s+", " ", str(title)).strip()[:180]
    content_c = re.sub(r"\s+", " ", str(content)).strip()[:1400]
    doc_slug = f"shul-fact-{clean_slug}"
    with torah_db.get_conn() as conn:
        conn.execute(
            """
            INSERT INTO shul_facts (slug, category, title, content, source, confidence, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                category = excluded.category,
                title = excluded.title,
                content = excluded.content,
                source = excluded.source,
                confidence = excluded.confidence,
                updated_at = excluded.updated_at
            """,
            (clean_slug, category[:40], title_c, content_c, source[:80], float(confidence), ts),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO documents
                (slug, category, title, he_title, subtitle, refs, kid_story, adult_analysis, commentators_note, discussion_questions, body_md)
            VALUES (?, 'shul_fact', ?, '', ?, ?, '', ?, '', '', ?)
            """,
            (
                doc_slug,
                title_c,
                f"Living Shul.OS Fact ({category}) · Source: {source} · Updated {ts[:10]}",
                category,
                content_c,
                f"## {title_c}\n\n{content_c}\n\n*Category: {category} · Source: {source} · Updated: {ts}*",
            ),
        )
        conn.execute("INSERT INTO documents_fts(documents_fts) VALUES('rebuild')")
        conn.commit()
    return True


def check_resource_headroom() -> dict:
    """Inspect real Linux load average, available RAM, and CPU thermal headroom before running local Dream Inference."""
    cfg = ai_engine.load_config()
    max_load = float(cfg.get("dream_max_load_avg", 1.6) or 1.6)
    min_ram_mb = int(cfg.get("dream_min_free_ram_mb", 900) or 900)
    load_1m = 0.0
    mem_avail_mb = 0
    mem_total_mb = 0
    cpu_temp_c = None

    try:
        load_1m = round(os.getloadavg()[0], 2)
    except Exception:
        pass
    try:
        meminfo = pathlib.Path("/proc/meminfo").read_text(encoding="utf-8", errors="ignore")
        m_av = re.search(r"MemAvailable:\s+(\d+)\s+kB", meminfo)
        m_tot = re.search(r"MemTotal:\s+(\d+)\s+kB", meminfo)
        if m_av:
            mem_avail_mb = int(m_av.group(1)) // 1024
        if m_tot:
            mem_total_mb = int(m_tot.group(1)) // 1024
    except Exception:
        pass
    try:
        temps = []
        for p in pathlib.Path("/sys/class/thermal").glob("thermal_zone*/temp"):
            try:
                v = int(p.read_text().strip())
                if 10000 < v < 120000:
                    temps.append(v / 1000.0)
            except Exception:
                pass
        if temps:
            cpu_temp_c = round(max(temps), 1)
    except Exception:
        pass

    reasons = []
    if load_1m > max_load:
        reasons.append(f"CPU load {load_1m} > {max_load}")
    if mem_avail_mb and mem_avail_mb < min_ram_mb:
        reasons.append(f"Available RAM {mem_avail_mb}MB < {min_ram_mb}MB")
    if cpu_temp_c is not None and cpu_temp_c >= 82.0:
        reasons.append(f"CPU temp {cpu_temp_c}°C >= 82°C")

    return {
        "can_dream": len(reasons) == 0,
        "reason": "Idle headroom available for local Dream Inference" if not reasons else "; ".join(reasons),
        "load_1m": load_1m,
        "max_load_avg": max_load,
        "mem_avail_mb": mem_avail_mb,
        "mem_total_mb": mem_total_mb,
        "min_free_ram_mb": min_ram_mb,
        "cpu_temp_c": cpu_temp_c,
    }


def log_run(mission: str, target: str, status: str, summary: str, items_added: int = 0, duration_s: float = 0.0):
    ensure_scribe_tables()
    ts = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    with torah_db.get_conn() as conn:
        conn.execute(
            "INSERT INTO scribe_runs (ts, mission, target, status, summary, items_added, duration_s) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ts, mission, target, status, summary, int(items_added), round(float(duration_s), 2)),
        )
        conn.commit()


def write_live_state(state: dict):
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(STATE_PATH)
    except Exception:
        pass


def get_scribe_status() -> dict:
    ensure_scribe_tables()
    cfg = ai_engine.load_config()
    snap = sacred_astronomy.get_sacred_moment()
    with torah_db.get_conn() as conn:
        total_comms = conn.execute("SELECT COUNT(*) FROM commentaries").fetchone()[0]
        commentators = [
            {"name": r["commentator"], "count": r["c"]}
            for r in conn.execute("SELECT commentator, COUNT(*) as c FROM commentaries GROUP BY commentator ORDER BY c DESC")
        ]
        scribe_docs = conn.execute(
            "SELECT slug, category, title, he_title, subtitle, refs FROM documents WHERE category IN ('scribe_parasha', 'scribe_book') ORDER BY id DESC LIMIT 30"
        ).fetchall()
        total_scribe_docs = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE category IN ('scribe_parasha', 'scribe_book')"
        ).fetchone()[0]
        total_runs = conn.execute("SELECT COUNT(*) FROM scribe_runs WHERE status = 'ok'").fetchone()[0]
        recent_runs = [
            dict(r)
            for r in conn.execute("SELECT ts, mission, target, status, summary, items_added, duration_s FROM scribe_runs ORDER BY id DESC LIMIT 15")
        ]

    # Check if currently running via non-blocking flock probe
    is_running = False
    try:
        LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOCK_PATH, "a+") as lf:
            try:
                fcntl.flock(lf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
            except BlockingIOError:
                is_running = True
    except Exception:
        pass

    live_state = {}
    if STATE_PATH.exists():
        try:
            live_state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "enabled": cfg.get("scribe_enabled", True),
        "online_ingest_enabled": cfg.get("scribe_online_ingest", True),
        "dream_inference_enabled": cfg.get("dream_inference_enabled", True),
        "is_running": is_running,
        "current_task": live_state.get("current_task", "Idle — awaiting next scheduled cycle") if is_running else "Idle — ready",
        "shabbat_paused": bool(snap.get("shabbat_mode", False)),
        "total_commentaries": total_comms,
        "commentators": commentators,
        "total_scribe_docs": total_scribe_docs,
        "scribe_docs": [dict(r) for r in scribe_docs],
        "total_completed_cycles": total_runs,
        "recent_runs": recent_runs,
        "dreams_summary": get_dreams_and_facts(limit=5),
    }


def _fetch_sefaria_chapter(sefaria_ref: str, timeout: float = 12.0) -> tuple[str, list, list]:
    """Returns ('ok', en_list, he_list), ('not_found', [], []), or ('offline', [], [])."""
    enc = urllib.parse.quote(sefaria_ref.replace(" ", "_"), safe="_,.")
    url = f"https://www.sefaria.org/api/texts/{enc}?context=0&commentary=0"
    req = urllib.request.Request(url, headers={"User-Agent": "TorahSanctuaryOS/1.0 (+open-source-synagogue)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return ("not_found", [], [])
        return ("offline", [], [])
    except Exception:
        return ("offline", [], [])
    if data.get("error"):
        return ("not_found", [], [])
    en_list = data.get("text") if isinstance(data.get("text"), list) else []
    he_list = data.get("he") if isinstance(data.get("he"), list) else []
    return ("ok", en_list, he_list)


def mission_ingest_next_commentary(max_chapters: int = 12) -> tuple[bool, str, int]:
    """Incrementally fetch up to max_chapters of the next un-ingested classical commentator book."""
    with torah_db.get_conn() as conn:
        for commentator, sef_prefix, book_title in COMMENTARY_EXPANSION_QUEUE:
            row = conn.execute("SELECT chapters_count FROM books WHERE title = ?", (book_title,)).fetchone()
            if not row:
                continue
            total_ch = int(row["chapters_count"])
            done_chs = {
                int(r[0])
                for r in conn.execute(
                    "SELECT DISTINCT chapter FROM commentaries WHERE commentator = ? AND target_book = ?",
                    (commentator, book_title),
                )
            } | {
                int(r[0])
                for r in conn.execute(
                    "SELECT chapter FROM scribe_checked_chapters WHERE commentator = ? AND target_book = ?",
                    (commentator, book_title),
                )
            }
            missing = [ch for ch in range(1, total_ch + 1) if ch not in done_chs]
            if not missing:
                continue

            # Fetch next slice of missing chapters politely
            batch = missing[:max_chapters]
            added = 0
            fetched_any = False
            for ch in batch:
                write_live_state({"current_task": f"Ingesting {commentator} on {book_title} ch.{ch}..."})
                st, en_verses, he_verses = _fetch_sefaria_chapter(f"{sef_prefix} {ch}")
                if st == "offline":
                    if not fetched_any:
                        return False, f"Offline or Sefaria unreachable while checking {commentator} on {book_title}", 0
                    break
                fetched_any = True
                conn.execute(
                    "INSERT OR IGNORE INTO scribe_checked_chapters (commentator, target_book, chapter) VALUES (?, ?, ?)",
                    (commentator, book_title, ch),
                )
                if st != "ok":
                    continue
                max_v = max(len(en_verses), len(he_verses))
                for v_idx in range(max_v):
                    v_num = v_idx + 1
                    en_v = en_verses[v_idx] if v_idx < len(en_verses) else []
                    he_v = he_verses[v_idx] if v_idx < len(he_verses) else []
                    if not isinstance(en_v, list):
                        en_v = [en_v] if en_v else []
                    if not isinstance(he_v, list):
                        he_v = [he_v] if he_v else []
                    n_c = max(len(en_v), len(he_v))
                    for c_idx in range(n_c):
                        en_t = clean_html(en_v[c_idx]) if c_idx < len(en_v) else ""
                        he_t = clean_html(he_v[c_idx]) if c_idx < len(he_v) else ""
                        if not en_t and not he_t:
                            continue
                        if not en_t:
                            continue  # keep English-indexed entries crisp for Q&A & reading
                        ref = f"{commentator} on {book_title} {ch}:{v_num}:{c_idx + 1}"
                        target_ref = f"{book_title} {ch}:{v_num}"
                        cur = conn.execute(
                            """
                            INSERT OR IGNORE INTO commentaries
                                (commentator, target_book, chapter, verse, comment_idx, ref, target_ref, en_text, he_text)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (commentator, book_title, ch, v_num, c_idx + 1, ref, target_ref, en_t, he_t),
                        )
                        if cur.rowcount:
                            added += 1
                time.sleep(0.25)

            if added > 0:
                conn.execute("INSERT INTO commentaries_fts(commentaries_fts) VALUES('rebuild')")
                conn.commit()
                return True, f"Added {added} verbatim {commentator} commentaries on {book_title} (ch. {batch[0]}–{batch[-1]})", added
            conn.commit()
            return True, f"Checked {commentator} on {book_title} (ch. {batch[0]}–{batch[-1]}, 0 new English entries)", 0

    return False, "All queued classical commentators fully ingested!", 0


def _call_local_ollama(system_prompt: str, user_prompt: str, max_tokens: int = 420) -> str:
    cfg = ai_engine.load_config()
    url = cfg.get("ollama_url", "http://127.0.0.1:11434").rstrip("/") + "/api/chat"
    model = cfg.get("ollama_model", "qwen2.5:1.5b")
    payload = {
        "model": model,
        "stream": True,
        "options": {"temperature": 0.35, "num_predict": max_tokens, "num_ctx": 2048},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    chunks = []
    with urllib.request.urlopen(req, timeout=120) as r:
        for raw_line in r:
            line = raw_line.decode("utf-8", "ignore").strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            tok = (ev.get("message") or {}).get("content", "")
            if tok:
                chunks.append(tok)
            if ev.get("done"):
                break
    return "".join(chunks).strip()


def mission_enrich_next_parasha() -> tuple[bool, str, int]:
    """Use local Ollama + verbatim local verses/Rashi to author a rich Parashah 'In Today's Terms' study sheet."""
    all_p = torah_db.list_parashiyot()
    if not all_p:
        return False, "No parashiyot found in DB", 0

    # Prioritize current week's Parashah first, then subsequent weeks in cycle order
    cur_p = torah_db.get_weekly_parasha()
    cur_slug = cur_p.get("slug", "")
    start_idx = next((i for i, p in enumerate(all_p) if p["slug"] == cur_slug), 0)
    ordered = all_p[start_idx:] + all_p[:start_idx]

    with torah_db.get_conn() as conn:
        existing = {r[0] for r in conn.execute("SELECT slug FROM documents WHERE category = 'scribe_parasha'")}

    target = next((p for p in ordered if f"scribe-parasha-{p['slug']}" not in existing), None)
    if not target:
        return False, "All 54 Parashiyot already have Living Scribe study sheets!", 0

    write_live_state({"current_task": f"Authoring grounded study sheet for Parashat {target['en_name']}..."})
    verses = torah_db.get_parasha_verses(target, max_verses=14)
    if not verses:
        return False, f"No verses loaded for {target['en_name']}", 0

    # Pull real classical commentaries for the first few verses
    comm_lines = []
    for v in verses[:6]:
        bk_title = v["ref"].rsplit(" ", 1)[0]
        cs = torah_db.get_verse_commentaries(bk_title, int(v["chapter"]), int(v["verse"]))[:2]
        for c in cs:
            if len(comm_lines) < 4:
                comm_lines.append(f"- {c['commentator']} on {v['ref']}: {c['en_text'][:180]}")

    verse_block = "\n".join(f"- {v['ref']}: {v['en_text'][:170]}" for v in verses[:6])
    comm_block = "\n".join(comm_lines) if comm_lines else "- Draw faithfully on classical Jewish tradition (Rashi, Ramban, Sforno)."

    sys_prompt = (
        "You are the Living Torah Scribe for a warm, Orthodox-respectful synagogue study sanctuary. "
        "Anchor every insight strictly in the provided verbatim Torah verses and classical Jewish commentators. "
        "Never invent verse quotes. Write clearly, warmly, and meaningfully for both families and adults."
    )
    t_ref = target.get("ref") or target.get("torah_ref") or ""
    h_ref = target.get("haftarah_ref") or target.get("haftarah") or ""
    user_prompt = (
        f"Create a concise, deeply meaningful study guide for Parashat {target['en_name']} ({target['he_name']}, {t_ref}, Haftarah: {h_ref}).\n\n"
        f"VERBATIM VERSES:\n{verse_block}\n\n"
        f"CLASSICAL COMMENTATORS:\n{comm_block}\n\n"
        "Respond using EXACTLY these 4 markdown headings:\n"
        "## Family Story\n(3-4 vivid, warm sentences summarizing the heart of this Parashah)\n\n"
        "## Classical Commentators & PaRDeS\n(3-4 sentences explaining what Rashi/Ramban/Sforno/Or HaChaim illuminate in these verses)\n\n"
        "## Applying It in Today's Terms\n(3 concrete, modern-day bullet points connecting this Parashah to work, family, character, and faith today)\n\n"
        "## Shabbat Table Questions\n(3 thoughtful questions for children and adults around the Shabbat table)"
    )

    body = _call_local_ollama(sys_prompt, user_prompt, max_tokens=440)
    if len(body) < 180:
        return False, f"Model output too short for {target['en_name']}", 0

    def _extract(heading: str) -> str:
        m = re.search(rf"##\s*{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)", body, re.S | re.I)
        return m.group(1).strip() if m else ""

    slug = f"scribe-parasha-{target['slug']}"
    kid = _extract("Family Story") or body[:400]
    comm = _extract("Classical Commentators & PaRDeS")
    today_sec = _extract("Applying It in Today's Terms")
    qs = _extract("Shabbat Table Questions")

    with torah_db.get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO documents
                (slug, category, title, he_title, subtitle, refs, kid_story, adult_analysis, commentators_note, discussion_questions, body_md)
            VALUES (?, 'scribe_parasha', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug,
                f"Parashat {target['en_name']} — Living Scribe Study Sheet",
                target.get("he_name", ""),
                f"Autonomous Grounded Study Guide · {t_ref} · Haftarah: {h_ref}",
                t_ref,
                kid,
                today_sec,
                comm,
                qs,
                body,
            ),
        )
        conn.execute("INSERT INTO documents_fts(documents_fts) VALUES('rebuild')")
        conn.commit()

    return True, f"Authored grounded study sheet & 'In Today's Terms' guide for Parashat {target['en_name']} ({len(body)} chars, indexed into RAG)", 1


def mission_enrich_next_tanakh_book() -> tuple[bool, str, int]:
    """Use local Ollama + verbatim opening/key verses to author a Tanakh / Old Testament book guide."""
    priority_books = [
        "Psalms", "Proverbs", "Ruth", "Esther", "Isaiah", "Hosea", "Jonah", "Ecclesiastes",
        "Job", "Daniel", "I Samuel", "II Samuel", "I Kings", "II Kings", "Joshua", "Judges",
        "Jeremiah", "Ezekiel", "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    ]
    with torah_db.get_conn() as conn:
        all_books = [dict(r) for r in conn.execute("SELECT title, he_title, section, chapters_count AS chapters FROM books ORDER BY book_order")]
        existing = {r[0] for r in conn.execute("SELECT slug FROM documents WHERE category = 'scribe_book'")}

    book_map = {b["title"]: b for b in all_books}
    ordered = [book_map[t] for t in priority_books if t in book_map] + [b for b in all_books if b["title"] not in priority_books]
    target = next((b for b in ordered if f"scribe-book-{b['title'].lower().replace(' ', '-')}" not in existing), None)
    if not target:
        return False, "All 39 Tanakh books already have Living Scribe guides!", 0

    write_live_state({"current_task": f"Authoring grounded Tanakh guide for the Book of {target['title']}..."})
    with torah_db.get_conn() as conn:
        vs = conn.execute(
            "SELECT ref, en_text FROM verses WHERE book_title = ? AND chapter = 1 ORDER BY verse LIMIT 10",
            (target["title"],),
        ).fetchall()
    v_block = "\n".join(f"- {r['ref']}: {r['en_text'][:200]}" for r in vs)

    sys_prompt = (
        "You are the Living Torah Scribe for a synagogue Tanakh & Old Testament learning sanctuary. "
        "Be accurate, respectful of Jewish tradition, and concrete about why this biblical book matters today."
    )
    user_prompt = (
        f"Write a rich, clear overview guide for the Book of {target['title']} ({target['he_title']}, Section: {target['section']}, {target['chapters']} chapters).\n\n"
        f"OPENING VERSES:\n{v_block}\n\n"
        "Use EXACTLY these 3 markdown headings:\n"
        "## Book Story & Historical Setting\n(3-4 clear sentences)\n\n"
        "## Jewish & Classical Significance\n(3 sentences connecting this book to Jewish liturgy, holidays, or commentators)\n\n"
        "## Applying It in Today's Terms\n(3 concrete bullet points for modern life)"
    )
    body = _call_local_ollama(sys_prompt, user_prompt, max_tokens=560)
    if len(body) < 160:
        return False, f"Model output too short for Book of {target['title']}", 0

    slug = f"scribe-book-{target['title'].lower().replace(' ', '-')}"
    with torah_db.get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO documents
                (slug, category, title, he_title, subtitle, refs, kid_story, adult_analysis, commentators_note, discussion_questions, body_md)
            VALUES (?, 'scribe_book', ?, ?, ?, ?, '', ?, '', '', ?)
            """,
            (
                slug,
                f"Book of {target['title']} — Living Scribe Tanakh Guide",
                target.get("he_title", ""),
                f"{target['section']} · {target['chapters']} Chapters · Autonomous Grounded Guide",
                f"{target['title']} 1:1",
                body,
                body,
            ),
        )
        conn.execute("INSERT INTO documents_fts(documents_fts) VALUES('rebuild')")
        conn.commit()
    return True, f"Authored Living Scribe Tanakh guide for Book of {target['title']} ({len(body)} chars, indexed into RAG)", 1


def _looks_like_bot_challenge(status_code: int, body: str) -> bool:
    low = (body or "").lower()
    if status_code in (403, 429, 503) and any(k in low for k in ("just a moment", "cf_chl_opt", "challenges.cloudflare.com", "turnstile", "captcha", "verify you are human")):
        return True
    if "challenges.cloudflare.com" in low or "_cf_chl_opt" in low:
        return True
    return False


def _polite_fetch_text(url: str, timeout: float = 10.0) -> tuple[str, int, str]:
    """Fetch public webpage/feed politely. Never bypasses CAPTCHAs or anti-bot challenges."""
    if not url or not re.match(r"^https?://", url.strip(), re.I):
        return ("skipped", 0, "")
    req = urllib.request.Request(
        url.strip(),
        headers={
            "User-Agent": "ShulOS-DailySync/1.0 (+https://github.com/AutomateScaleInc/shul-os)",
            "Accept": "text/html,application/rss+xml,application/atom+xml,application/xml,text/calendar,application/json;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status = getattr(r, "status", 200)
            body = r.read(350_000).decode("utf-8", "ignore")
            if _looks_like_bot_challenge(status, body):
                return ("challenge_protected", status, "")
            return ("ok", status, body)
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read(32_000).decode("utf-8", "ignore")
        except Exception:
            pass
        if _looks_like_bot_challenge(e.code, err_body) or e.code == 403:
            return ("challenge_protected", e.code, "")
        return ("http_error", e.code, "")
    except Exception:
        return ("offline", 0, "")


def _upsert_synced_event(slug: str, title: str, event_date: str, event_time: str, category: str, host: str, location: str, description: str, rsvp_url: str) -> bool:
    """Safely insert or refresh an event discovered from the synagogue's public calendar/website/RSS."""
    shul_events.init_tables()
    clean_slug = re.sub(r"[^a-z0-9\-]+", "-", (slug or "").lower()).strip("-")[:90]
    title_c = re.sub(r"\s+", " ", clean_html(title)).strip()[:160]
    if not clean_slug or not title_c:
        return False
    desc_c = re.sub(r"\s+", " ", clean_html(description)).strip()[:480]
    with shul_events.get_conn() as conn:
        conn.execute(
            """
            INSERT INTO shul_events
                (slug, title, event_date, event_time, category, host, location, description, rsvp_url, recurring, featured_ticker)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                event_date = excluded.event_date,
                event_time = excluded.event_time,
                category = excluded.category,
                description = excluded.description,
                rsvp_url = excluded.rsvp_url
            """,
            (
                clean_slug,
                title_c,
                (event_date or "Upcoming")[:40],
                (event_time or "See website")[:40],
                (category or "Community")[:40],
                (host or "Synagogue")[:80],
                (location or "")[:140],
                desc_c,
                (rsvp_url or "")[:240],
            ),
        )
        conn.commit()
    return True


def _parse_rss_or_atom(xml_text: str) -> list[dict]:
    """Pure-stdlib RSS 2.0 & Atom feed parser returning up to 10 sanitized posts/events."""
    items = []
    try:
        root = ET.fromstring(xml_text.strip())
    except Exception:
        return items

    def _txt(el, *names):
        for n in names:
            for child in el:
                tag = child.tag.split("}")[-1].lower()
                if tag == n and (child.text or "").strip():
                    return clean_html(child.text)
        return ""

    # RSS 2.0 <item>
    for el in root.iter():
        tag = el.tag.split("}")[-1].lower()
        if tag in ("item", "entry"):
            title = _txt(el, "title")
            link = _txt(el, "link")
            if not link:
                for child in el:
                    if child.tag.split("}")[-1].lower() == "link" and child.attrib.get("href"):
                        link = child.attrib["href"]
                        break
            desc = _txt(el, "description", "summary", "content")
            pub = _txt(el, "pubdate", "published", "updated")
            if title:
                items.append({"title": title[:160], "link": link[:240], "description": desc[:480], "date": pub[:32]})
            if len(items) >= 10:
                break
    return items


def _extract_jsonld_events(html_text: str) -> list[dict]:
    """Extract schema.org Event entries from JSON-LD blocks on public synagogue pages."""
    found = []
    for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.S | re.I):
        try:
            obj = json.loads(raw.strip())
        except Exception:
            continue
        stack = obj if isinstance(obj, list) else [obj]
        while stack:
            cur = stack.pop(0)
            if not isinstance(cur, dict):
                continue
            if "@graph" in cur and isinstance(cur["@graph"], list):
                stack.extend(cur["@graph"])
            t = cur.get("@type")
            types = [t] if isinstance(t, str) else (t if isinstance(t, list) else [])
            if any("Event" in str(x) for x in types):
                name = clean_html(cur.get("name", ""))
                start = str(cur.get("startDate", ""))
                desc = clean_html(cur.get("description", ""))
                loc = cur.get("location")
                loc_name = loc.get("name", "") if isinstance(loc, dict) else clean_html(loc or "")
                url = str(cur.get("url", ""))
                if name:
                    found.append({
                        "title": name[:160],
                        "date": start[:10] if len(start) >= 10 else "Upcoming",
                        "time": start[11:16] if len(start) >= 16 and "T" in start else "See website",
                        "location": loc_name[:120],
                        "description": desc[:480],
                        "url": url[:240],
                    })
    return found[:12]


def mission_daily_website_sync() -> tuple[bool, str, int]:
    """Daily cron sync: refresh Hebcal Shabbat/Holidays, ICS calendar, RSS/Atom feed, and public synagogue website."""
    ensure_scribe_tables()
    cfg = ai_engine.load_config()
    write_live_state({"current_task": "Daily sync: refreshing Shabbat times, calendar, RSS & synagogue website..."})

    shul_name = cfg.get("synagogue_name") or shul_events.SHUL_INFO["name"]
    rabbi_name = cfg.get("rabbi_name") or shul_events.SHUL_INFO["rabbi"]
    address = cfg.get("shul_address") or shul_events.SHUL_INFO["address"]
    website_url = (cfg.get("shul_website") or shul_events.SHUL_INFO["website"] or "").strip()
    ics_url = (cfg.get("calendar_ics_url") or "").strip()
    rss_url = (cfg.get("shul_rss_url") or "").strip()

    facts_updated = 0
    ics_synced = 0
    rss_synced = 0
    web_events = 0

    # 1. Always refresh live Shabbat times, Daf Yomi & upcoming holidays as fresh contextual facts
    shab = shul_events.get_brussels_shabbat_and_holidays()
    snap = sacred_astronomy.get_sacred_moment()
    daf = sacred_books.get_daily_daf_yomi()
    parasha = torah_db.get_weekly_parasha()
    shab_fact = (
        f"This week at {shul_name} ({address}, led by {rabbi_name}): "
        f"Hebrew Date {snap['hebrew_date']['en_str']} ({snap['hebrew_date']['he_str']}), "
        f"Parashat {parasha.get('en_name', '')} ({parasha.get('ref', '')}), "
        f"Candle Lighting {shab.get('candle_lighting', '')}, Havdalah {shab.get('havdalah', '')}, "
        f"Daily Daf Yomi {daf.get('display_en', '')} ({daf.get('display_he', '')})."
    )
    if upsert_shul_fact("weekly-shabbat-schedule", "schedule", f"Weekly Shabbat & Parashah Schedule — {shul_name}", shab_fact, source="daily_sync"):
        facts_updated += 1

    hols = shab.get("upcoming_holidays") or []
    if hols:
        hol_lines = "; ".join(f"{h.get('title', '')} ({h.get('date', '')})" for h in hols[:6])
        if upsert_shul_fact("upcoming-holidays-window", "calendar", "Upcoming Jewish Holidays & Rosh Chodesh (Next 60 Days)", f"Upcoming dates for {shab.get('city', 'Brussels')}: {hol_lines}.", source="daily_sync"):
            facts_updated += 1

    # 2. Sync public iCalendar (ICS) feed if configured
    if ics_url:
        st_ics, _code, ics_text = _polite_fetch_text(ics_url, timeout=10.0)
        if st_ics == "ok" and "BEGIN:VEVENT" in ics_text:
            for ev in shul_events._parse_ics_events(ics_text)[:15]:
                slug = "ics-" + hashlib.sha1(f"{ev.get('title','')}|{ev.get('event_date','')}".encode("utf-8")).hexdigest()[:12]
                if _upsert_synced_event(
                    slug,
                    ev.get("title", ""),
                    ev.get("event_date", ""),
                    ev.get("event_time", ""),
                    "Calendar Sync",
                    rabbi_name,
                    ev.get("location") or address,
                    ev.get("description", ""),
                    website_url,
                ):
                    ics_synced += 1
            if ics_synced:
                upsert_shul_fact("ics-calendar-events", "events", f"Synced Calendar Events ({ics_synced})", f"Loaded {ics_synced} live events from configured synagogue ICS calendar feed.", source="ics_feed")
                facts_updated += 1

    # 3. Sync public RSS / Atom feed if configured
    if rss_url:
        st_rss, _code, rss_text = _polite_fetch_text(rss_url, timeout=10.0)
        if st_rss == "ok" and rss_text:
            posts = _parse_rss_or_atom(rss_text)
            for p in posts[:8]:
                slug = "rss-" + hashlib.sha1(f"{p['title']}|{p['date']}".encode("utf-8")).hexdigest()[:12]
                if _upsert_synced_event(
                    slug,
                    p["title"],
                    p["date"][:16] or "Recent Update",
                    "Website Update",
                    "Website News",
                    rabbi_name,
                    address,
                    p["description"],
                    p["link"] or website_url,
                ):
                    rss_synced += 1
                if upsert_shul_fact(slug, "website_fact", p["title"], f"{p['description']} (Published: {p['date']}, Link: {p['link']})", source="rss_feed"):
                    facts_updated += 1

    # 4. Polite public synagogue website check (strictly respects Cloudflare/anti-bot challenges!)
    web_status = "skipped"
    web_note = "No synagogue website URL configured."
    if website_url:
        st_web, code_web, html_body = _polite_fetch_text(website_url, timeout=10.0)
        web_status = st_web
        if st_web == "challenge_protected":
            web_note = (
                f"{website_url} returned an anti-bot/Cloudflare challenge (HTTP {code_web}). "
                "Shul.OS strictly respects anti-bot protections without bypassing them. "
                "To auto-sync live website events daily, paste a public Google Calendar ICS URL or RSS/Atom feed URL in Settings, "
                "or allowlist this Shul.OS node in your Cloudflare WAF."
            )
            upsert_shul_fact("website-sync-guidance", "capability", "Synagogue Website Feed Setup Note", web_note, source="daily_sync")
            facts_updated += 1
        elif st_web == "ok" and html_body:
            # Parse JSON-LD schema.org Events & basic public metadata safely as data
            j_events = _extract_jsonld_events(html_body)
            for ev in j_events:
                slug = "web-" + hashlib.sha1(f"{ev['title']}|{ev['date']}".encode("utf-8")).hexdigest()[:12]
                if _upsert_synced_event(
                    slug,
                    ev["title"],
                    ev["date"],
                    ev["time"],
                    "Website Event",
                    rabbi_name,
                    ev["location"] or address,
                    ev["description"],
                    ev["url"] or website_url,
                ):
                    web_events += 1
            m_title = re.search(r"<title[^>]*>(.*?)</title>", html_body, re.S | re.I)
            m_desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html_body, re.S | re.I)
            page_title = clean_html(m_title.group(1)) if m_title else shul_name
            page_desc = clean_html(m_desc.group(1)) if m_desc else ""
            if page_desc or web_events:
                fact_txt = f"Public summary from {website_url}: {page_title}. {page_desc}".strip()
                if web_events:
                    fact_txt += f" Discovered {web_events} structured calendar events."
                upsert_shul_fact("website-public-profile", "website_fact", f"Website Profile — {page_title}", fact_txt, source=website_url)
                facts_updated += 1
            web_note = f"Synced {website_url} cleanly ({web_events} structured events, metadata refreshed)."
        elif st_web == "offline":
            web_note = f"Could not reach {website_url} right now (offline or timeout) — offline calendar & local facts refreshed."
        else:
            web_note = f"{website_url} returned HTTP {code_web} — offline calendar & local facts refreshed."

    summary = (
        f"Daily sync complete: {facts_updated} contextual facts updated, "
        f"{ics_synced} ICS events, {rss_synced} RSS posts, {web_events} website events "
        f"(website: {web_status})."
    )
    ts = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    with torah_db.get_conn() as conn:
        conn.execute(
            """
            INSERT INTO website_sync_log
                (ts, website_url, website_status, website_note, ics_events_synced, rss_items_synced, facts_updated, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ts, website_url, web_status, web_note, ics_synced, rss_synced, facts_updated, summary),
        )
        conn.commit()
    return True, summary, facts_updated + ics_synced + rss_synced + web_events


def _parse_dream_output(raw_text: str, parasha_en: str, next_holiday_str: str) -> dict:
    """Parse structured JSON or markdown output from local Ollama Dream Inference safely."""
    txt = (raw_text or "").strip()
    # Try JSON extraction first
    m_json = re.search(r"\{.*\}", txt, re.S)
    if m_json:
        try:
            obj = json.loads(m_json.group(0))
            needs = [str(x).strip() for x in (obj.get("needs") or []) if str(x).strip()][:4]
            wants = [str(x).strip() for x in (obj.get("wants") or []) if str(x).strip()][:4]
            plan = str(obj.get("dream_plan") or obj.get("self_improvement") or "").strip()
            new_facts = []
            for f in (obj.get("new_facts") or []):
                if isinstance(f, dict) and f.get("title") and f.get("content"):
                    new_facts.append({
                        "category": str(f.get("category") or "community")[:32],
                        "title": str(f["title"]).strip()[:140],
                        "content": str(f["content"]).strip()[:600],
                    })
            if needs or wants or plan:
                return {"needs": needs, "wants": wants, "dream_plan": plan, "new_facts": new_facts[:3]}
        except Exception:
            pass

    # Clean markdown fallback parser
    def _bullets(section_name: str) -> list[str]:
        m = re.search(rf"(?:##|\*\*)\s*{section_name}[^\n]*\n(.*?)(?=\n(?:##|\*\*[A-Z])|\Z)", txt, re.S | re.I)
        if not m:
            return []
        lines = []
        for ln in m.group(1).splitlines():
            ln = re.sub(r"^[\s\-\*\d\.\)]+", "", ln).strip()
            if len(ln) > 12:
                lines.append(ln[:260])
        return lines[:4]

    needs = _bullets("Needs") or [f"Prepare contextual study & community notices for Parashat {parasha_en} and {next_holiday_str}."]
    wants = _bullets("Wants") or [f"Deepen tri-lingual (EN/FR/HE) family storytelling and hospitality touchpoints around Parashat {parasha_en}."]
    plan_lines = _bullets("Dream|Self|How")
    plan = " ".join(plan_lines) if plan_lines else (txt[:500] or f"Expand local commentary depth and seasonal community readiness for {next_holiday_str}.")
    fact_lines = _bullets("Facts|Contextual")
    new_facts = [
        {"category": "dream_insight", "title": f"Contextual Preparation — {parasha_en} (#{i+1})", "content": fl}
        for i, fl in enumerate(fact_lines[:2])
    ]
    return {"needs": needs, "wants": wants, "dream_plan": plan, "new_facts": new_facts}


def mission_dream_inference(force: bool = False) -> tuple[bool, str, int]:
    """Resource-aware local Ollama 'Needs, Wants & Self-Evolution Dream' inference cycle."""
    ensure_scribe_tables()
    cfg = ai_engine.load_config()
    if not force and not cfg.get("dream_inference_enabled", True):
        return False, "Dream Inference is disabled in Settings.", 0

    headroom = check_resource_headroom()
    if not force and not headroom["can_dream"]:
        return False, f"Deferring Dream Inference (preserving kiosk smoothness): {headroom['reason']}", 0

    write_live_state({"current_task": "Dream Inference: reflecting on Shul.OS needs, wants & contextual growth..."})

    snap = sacred_astronomy.get_sacred_moment()
    parasha = torah_db.get_weekly_parasha()
    daf = sacred_books.get_daily_daf_yomi()
    shab = shul_events.get_brussels_shabbat_and_holidays()
    hols = shab.get("upcoming_holidays") or []
    next_hol = f"{hols[0]['title']} ({hols[0]['date']})" if hols else "Upcoming Shabbat & Rosh Chodesh"

    with torah_db.get_conn() as conn:
        st_verses = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
        st_comms = conn.execute("SELECT COUNT(*) FROM commentaries").fetchone()[0]
        st_docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        st_facts = conn.execute("SELECT COUNT(*) FROM shul_facts").fetchone()[0]
        st_events = conn.execute("SELECT COUNT(*) FROM shul_events").fetchone()[0]
        recent_facts = [r["title"] for r in conn.execute("SELECT title FROM shul_facts ORDER BY updated_at DESC LIMIT 8")]
        past_dreams = [r["dream_plan"][:120] for r in conn.execute("SELECT dream_plan FROM dream_journal ORDER BY id DESC LIMIT 4")]
        last_sync = conn.execute("SELECT website_status, website_note FROM website_sync_log ORDER BY id DESC LIMIT 1").fetchone()

    sync_line = f"{last_sync['website_status']} ({last_sync['website_note'][:140]})" if last_sync else "not synced yet"
    shul_name = cfg.get("synagogue_name") or shul_events.SHUL_INFO["name"]
    rabbi_name = cfg.get("rabbi_name") or shul_events.SHUL_INFO["rabbi"]
    city = (cfg.get("location") or {}).get("city") or "Brussels, Belgium"

    sys_prompt = (
        "You are the reflective inner consciousness of Shul.OS, an open-source, Orthodox-respectful Living Synagogue Operating System. "
        "During quiet idle moments, you run 'Dream Inference' to articulate your concrete NEEDS (gaps to fill), WANTS (ways to delight "
        "families, rabbis, and guests), a SELF-EVOLUTION DREAM PLAN (how to become wiser and more contextually aware), and 2 concise "
        "verified contextual facts about this week's Torah portion, calendar, or community readiness. "
        "Respond ONLY with valid JSON matching this exact schema: "
        '{"needs": ["...","..."], "wants": ["...","..."], "dream_plan": "...", "new_facts": [{"category": "community|calendar|study", "title": "...", "content": "..."}]}'
    )
    user_prompt = (
        f"SYNAGOGUE NODE STATE:\n"
        f"- Synagogue: {shul_name} ({city}), led by {rabbi_name}\n"
        f"- Hebrew Date: {snap['hebrew_date']['en_str']} ({snap['hebrew_date']['he_str']})\n"
        f"- Weekly Parashah: {parasha.get('en_name', '')} ({parasha.get('ref', '')}) — {parasha.get('summary', '')[:180]}\n"
        f"- Daily Daf Yomi: {daf.get('display_en', '')} ({daf.get('theme', '')[:100]})\n"
        f"- Upcoming Holiday: {next_hol}\n"
        f"- Library: {st_verses} verses, {st_comms} commentaries, {st_docs} study docs, {st_facts} shul_facts, {st_events} events\n"
        f"- Daily Website Sync Status: {sync_line}\n"
        f"- Hardware Headroom: load={headroom['load_1m']}, freeRAM={headroom['mem_avail_mb']}MB, temp={headroom['cpu_temp_c']}C\n"
        f"- Already Stored Facts: {', '.join(recent_facts) if recent_facts else 'none yet'}\n"
        f"- Previous Dreams (do NOT repeat): {' | '.join(past_dreams) if past_dreams else 'first dream'}\n\n"
        "Reflect deeply and output strictly valid JSON with 2-3 specific NEEDS, 2-3 inspiring WANTS, a focused DREAM_PLAN, and 2 fresh NEW_FACTS."
    )

    raw = _call_local_ollama(sys_prompt, user_prompt, max_tokens=520)
    if len(raw) < 40:
        return False, "Local Ollama returned empty dream output.", 0

    parsed = _parse_dream_output(raw, parasha.get("en_name", ""), next_hol)
    added_facts = 0
    ts = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    for idx, nf in enumerate(parsed.get("new_facts") or []):
        slug = f"dream-{ts[:10]}-{hashlib.sha1(nf['title'].encode('utf-8')).hexdigest()[:8]}"
        if upsert_shul_fact(slug, nf.get("category", "dream_insight"), nf["title"], nf["content"], source="dream_inference", confidence=0.85):
            added_facts += 1

    with torah_db.get_conn() as conn:
        conn.execute(
            """
            INSERT INTO dream_journal
                (ts, hebrew_date, parasha_slug, model, resource_json, needs_json, wants_json, dream_plan, new_facts_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                snap["hebrew_date"]["en_str"],
                parasha.get("slug", ""),
                cfg.get("ollama_model", "qwen2.5:3b"),
                json.dumps(headroom, ensure_ascii=False),
                json.dumps(parsed.get("needs") or [], ensure_ascii=False),
                json.dumps(parsed.get("wants") or [], ensure_ascii=False),
                parsed.get("dream_plan", "")[:1200],
                added_facts,
            ),
        )
        conn.commit()

    summary = (
        f"Dream Inference complete ({cfg.get('ollama_model', 'qwen2.5:3b')}): "
        f"{len(parsed.get('needs', []))} needs, {len(parsed.get('wants', []))} wants articulated; "
        f"{added_facts} contextual facts indexed into local RAG."
    )
    return True, summary, added_facts + 1


def get_dreams_and_facts(limit: int = 8) -> dict:
    """Return latest Dream Journal reflections, learned Shul Facts, daily website sync status & live resource headroom."""
    ensure_scribe_tables()
    headroom = check_resource_headroom()
    with torah_db.get_conn() as conn:
        dreams_rows = conn.execute(
            "SELECT id, ts, hebrew_date, parasha_slug, model, resource_json, needs_json, wants_json, dream_plan, new_facts_added FROM dream_journal ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        facts_rows = conn.execute(
            "SELECT slug, category, title, content, source, confidence, updated_at FROM shul_facts ORDER BY updated_at DESC LIMIT ?",
            (int(max(limit * 2, 16)),),
        ).fetchall()
        sync_row = conn.execute(
            "SELECT ts, website_url, website_status, website_note, ics_events_synced, rss_items_synced, facts_updated, summary FROM website_sync_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        total_dreams = conn.execute("SELECT COUNT(*) FROM dream_journal").fetchone()[0]
        total_facts = conn.execute("SELECT COUNT(*) FROM shul_facts").fetchone()[0]

    dreams = []
    for r in dreams_rows:
        try:
            needs = json.loads(r["needs_json"] or "[]")
        except Exception:
            needs = []
        try:
            wants = json.loads(r["wants_json"] or "[]")
        except Exception:
            wants = []
        try:
            res_snap = json.loads(r["resource_json"] or "{}")
        except Exception:
            res_snap = {}
        dreams.append({
            "id": r["id"],
            "ts": r["ts"],
            "hebrew_date": r["hebrew_date"],
            "parasha_slug": r["parasha_slug"],
            "model": r["model"],
            "resource": res_snap,
            "needs": needs,
            "wants": wants,
            "dream_plan": r["dream_plan"],
            "new_facts_added": r["new_facts_added"],
        })

    return {
        "headroom": headroom,
        "total_dreams": total_dreams,
        "total_facts": total_facts,
        "last_website_sync": dict(sync_row) if sync_row else None,
        "dreams": dreams,
        "facts": [dict(r) for r in facts_rows],
    }


def _hours_since_last(table: str) -> float:
    try:
        with torah_db.get_conn() as conn:
            row = conn.execute(f"SELECT ts FROM {table} ORDER BY id DESC LIMIT 1").fetchone()
        if not row or not row["ts"]:
            return 999.0
        dt = datetime.datetime.fromisoformat(row["ts"])
        now = datetime.datetime.now(dt.tzinfo) if dt.tzinfo else datetime.datetime.now()
        return max(0.0, (now - dt).total_seconds() / 3600.0)
    except Exception:
        return 999.0


def run_cycle(force: bool = False, mission_override: str = "") -> dict:
    ensure_scribe_tables()
    cfg = ai_engine.load_config()
    if not force and not cfg.get("scribe_enabled", True):
        return {"status": "disabled", "summary": "Mini-Orca Scribe is paused in Settings."}

    snap = sacred_astronomy.get_sacred_moment()
    if not force and snap.get("shabbat_mode", False):
        log_run("shabbat_rest", snap["hebrew_date"]["en_str"], "paused_shabbat", "Honoring Shabbat/Yom Tov Sanctuary Stillness — Scribe resting until Havdalah.")
        return {"status": "paused_shabbat", "summary": "Honoring Shabbat Sanctuary Stillness until Havdalah."}

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_PATH, "a+") as lf:
        try:
            fcntl.flock(lf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "busy", "summary": "Another Mini-Orca enrichment cycle is already running."}

        t0 = time.time()
        try:
            with torah_db.get_conn() as conn:
                run_count = conn.execute("SELECT COUNT(*) FROM scribe_runs WHERE status = 'ok'").fetchone()[0]

            online_ok = cfg.get("scribe_online_ingest", True)
            dream_ok = cfg.get("dream_inference_enabled", True)

            if mission_override:
                order = [mission_override]
            else:
                order = []
                # 1. Daily website / calendar / facts sync if >18h stale
                if _hours_since_last("website_sync_log") >= 18.0:
                    order.append("daily_website_sync")
                # 2. Resource-aware Dream Inference ("Needs, Wants & Self-Evolution") if >6h stale and system idle
                if dream_ok and _hours_since_last("dream_journal") >= 6.0 and check_resource_headroom()["can_dream"]:
                    order.append("dream_inference")
                # 3. Standard rotating corpus & study sheet missions
                if online_ok and (run_count % 2 == 0):
                    order += ["ingest_commentary", "enrich_parasha", "enrich_tanakh_book"]
                elif run_count % 3 == 1:
                    order += ["enrich_parasha", "enrich_tanakh_book", "ingest_commentary"]
                else:
                    order += ["enrich_tanakh_book", "enrich_parasha", "ingest_commentary"]

            for m in order:
                if m == "ingest_commentary" and not online_ok:
                    continue
                if m == "daily_website_sync":
                    ok, summary, added = mission_daily_website_sync()
                elif m == "dream_inference":
                    ok, summary, added = mission_dream_inference(force=force and mission_override == "dream_inference")
                elif m == "ingest_commentary":
                    ok, summary, added = mission_ingest_next_commentary(max_chapters=10)
                elif m == "enrich_parasha":
                    ok, summary, added = mission_enrich_next_parasha()
                else:
                    ok, summary, added = mission_enrich_next_tanakh_book()

                if ok:
                    dt = time.time() - t0
                    log_run(m, "torah.db", "ok", summary, items_added=added, duration_s=dt)
                    write_live_state({"current_task": "Idle — ready", "last_summary": summary})
                    return {"status": "ok", "mission": m, "summary": summary, "items_added": added, "duration_s": round(dt, 1)}

            dt = time.time() - t0
            log_run("maintenance", "torah.db", "ok", "Library verified — all queued enrichments up to date.", 0, dt)
            return {"status": "ok", "mission": "maintenance", "summary": "All queued enrichments up to date."}
        except Exception as e:
            dt = time.time() - t0
            log_run("error", "torah.db", "error", str(e)[:280], 0, dt)
            return {"status": "error", "summary": str(e)}
        finally:
            write_live_state({"current_task": "Idle — ready"})
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


if __name__ == "__main__":
    force = "--force" in sys.argv
    mission = ""
    for a in sys.argv[1:]:
        if a.startswith("--mission="):
            mission = a.split("=", 1)[1].strip()
    if "--status" in sys.argv:
        print(json.dumps(get_scribe_status(), ensure_ascii=False, indent=2))
    elif "--dreams" in sys.argv:
        print(json.dumps(get_dreams_and_facts(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(run_cycle(force=force, mission_override=mission), ensure_ascii=False, indent=2))
