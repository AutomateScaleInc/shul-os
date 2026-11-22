#!/usr/bin/env python3
"""
Torah Sanctuary — Fast Offline SQLite + FTS5 Retrieval Engine.
Handles verse lookups (Hebrew & English names/abbreviations), commentary joins,
FTS5 full-text search, Weekly Parashah (live cached + offline fallback), and curated dossiers.
"""

import json
import pathlib
import re
import sqlite3
import time
import urllib.request

BASE_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "torah.db"
PARASHA_CACHE = DATA_DIR / "weekly_parasha_cache.json"

BOOK_ALIASES = {
    # Torah (English + Hebrew transliterations + abbrevs)
    "genesis": "Genesis", "gen": "Genesis", "bereshit": "Genesis", "bereishit": "Genesis", "bereshis": "Genesis",
    "exodus": "Exodus", "ex": "Exodus", "exod": "Exodus", "shemot": "Exodus", "shemos": "Exodus",
    "leviticus": "Leviticus", "lev": "Leviticus", "vayikra": "Leviticus",
    "numbers": "Numbers", "num": "Numbers", "bamidbar": "Numbers",
    "deuteronomy": "Deuteronomy", "deut": "Deuteronomy", "devarim": "Deuteronomy",
    # Nevi'im
    "joshua": "Joshua", "josh": "Joshua", "yehoshua": "Joshua",
    "judges": "Judges", "judg": "Judges", "shoftim": "Judges",
    "1 samuel": "I Samuel", "i samuel": "I Samuel", "1 sam": "I Samuel", "shmuel a": "I Samuel",
    "2 samuel": "II Samuel", "ii samuel": "II Samuel", "2 sam": "II Samuel", "shmuel b": "II Samuel",
    "1 kings": "I Kings", "i kings": "I Kings", "1 kgs": "I Kings", "melachim a": "I Kings",
    "2 kings": "II Kings", "ii kings": "II Kings", "2 kgs": "II Kings", "melachim b": "II Kings",
    "isaiah": "Isaiah", "isa": "Isaiah", "yeshayahu": "Isaiah",
    "jeremiah": "Jeremiah", "jer": "Jeremiah", "yirmiyahu": "Jeremiah",
    "ezekiel": "Ezekiel", "ezek": "Ezekiel", "yechezkel": "Ezekiel",
    "hosea": "Hosea", "hos": "Hosea", "hoshea": "Hosea",
    "joel": "Joel", "yoel": "Joel",
    "amos": "Amos",
    "obadiah": "Obadiah", "obad": "Obadiah", "ovadiah": "Obadiah",
    "jonah": "Jonah", "yonah": "Jonah",
    "micah": "Micah", "mic": "Micah", "michah": "Micah",
    "nahum": "Nahum", "nah": "Nahum", "nachum": "Nahum",
    "habakkuk": "Habakkuk", "hab": "Habakkuk", "chavakuk": "Habakkuk",
    "zephaniah": "Zephaniah", "zeph": "Zephaniah", "tzefaniah": "Zephaniah",
    "haggai": "Haggai", "hag": "Haggai", "chaggai": "Haggai",
    "zechariah": "Zechariah", "zech": "Zechariah", "zecharyah": "Zechariah",
    "malachi": "Malachi", "mal": "Malachi",
    # Ketuvim
    "psalms": "Psalms", "psalm": "Psalms", "ps": "Psalms", "tehillim": "Psalms", "tehilim": "Psalms",
    "proverbs": "Proverbs", "prov": "Proverbs", "mishlei": "Proverbs",
    "job": "Job", "iyov": "Job",
    "song of songs": "Song of Songs", "song of solomon": "Song of Songs", "shir hashirim": "Song of Songs",
    "ruth": "Ruth", "rut": "Ruth",
    "lamentations": "Lamentations", "lam": "Lamentations", "eicha": "Lamentations", "eichah": "Lamentations",
    "ecclesiastes": "Ecclesiastes", "eccl": "Ecclesiastes", "kohelet": "Ecclesiastes", "koheleth": "Ecclesiastes",
    "esther": "Esther", "ester": "Esther", "megillat esther": "Esther",
    "daniel": "Daniel", "dan": "Daniel",
    "ezra": "Ezra",
    "nehemiah": "Nehemiah", "neh": "Nehemiah", "nechemyah": "Nehemiah",
    "1 chronicles": "I Chronicles", "i chronicles": "I Chronicles", "1 chr": "I Chronicles",
    "2 chronicles": "II Chronicles", "ii chronicles": "II Chronicles", "2 chr": "II Chronicles",
}

ALIAS_PATTERN = "|".join(sorted((re.escape(k) for k in BOOK_ALIASES), key=len, reverse=True))
REF_RE = re.compile(
    rf"\b({ALIAS_PATTERN})\s+(\d{{1,3}})(?:\s*:\s*(\d{{1,3}})(?:\s*[-–]\s*(\d{{1,3}}))?)?\b",
    re.IGNORECASE,
)

STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "what", "when", "where", "who", "why", "how",
    "does", "did", "about", "into", "your", "their", "have", "has", "had", "was", "were", "are", "is",
    "tell", "story", "explain", "mean", "meaning", "say", "says", "teach", "torah", "bible", "old",
    "testament", "verse", "chapter", "book", "please", "can", "you", "me", "give", "show", "interpret",
    "interpretation", "commentary", "rashi", "ramban", "midrash", "sforno", "ibn", "ezra", "chaim",
    "hachaim", "yakar", "chizkuni", "rashbam", "parasha", "parashat", "parshah", "today", "terms",
    "apply", "applying", "aliyah", "reading", "weekly", "portion", "families", "warmly",
}

COMMENTATOR_HINTS = [
    ("or hachaim", "Or HaChaim"),
    ("ohr hachaim", "Or HaChaim"),
    ("rashi", "Rashi"),
    ("ramban", "Ramban"),
    ("nachmanides", "Ramban"),
    ("ibn ezra", "Ibn Ezra"),
    ("sforno", "Sforno"),
    ("kli yakar", "Kli Yakar"),
    ("chizkuni", "Chizkuni"),
    ("rashbam", "Rashbam"),
    ("metzudat david", "Metzudat David"),
    ("midrash", "Midrash"),
    ("pirkei avot", "Pirkei Avot"),
    ("avot", "Pirkei Avot"),
]

COMMENTATOR_PRIORITY = {
    "Rashi": 1,
    "Or HaChaim": 2,
    "Ramban": 3,
    "Ibn Ezra": 4,
    "Sforno": 5,
    "Kli Yakar": 6,
    "Chizkuni": 7,
    "Rashbam": 8,
    "Metzudat David": 9,
}


def _detect_requested_commentators(query: str) -> list[str]:
    low = (query or "").lower()
    hits = []
    for kw, name in COMMENTATOR_HINTS:
        if kw in low and name not in hits:
            hits.append(name)
    return hits


def _diversify_commentaries(rows: list[dict], limit: int, preferred: list[str] = None) -> list[dict]:
    """Round-robin across distinct commentators so Or HaChaim, Ramban, Kli Yakar, etc. aren't crowded out by 5 Rashi rows."""
    if not rows:
        return []
    preferred = preferred or []

    def _pref_rank(name: str) -> tuple:
        for i, p in enumerate(preferred):
            if p.lower() in name.lower():
                return (0, i, name)
        return (1, COMMENTATOR_PRIORITY.get(name, 20), name)

    buckets: dict[str, list[dict]] = {}
    seen_refs = set()
    for r in rows:
        ref_k = r.get("ref") or f"{r.get('commentator')}:{r.get('target_ref')}:{(r.get('en_text') or '')[:40]}"
        if ref_k in seen_refs:
            continue
        seen_refs.add(ref_k)
        c_name = r.get("commentator") or "Classical"
        buckets.setdefault(c_name, []).append(r)

    ordered_names = sorted(buckets.keys(), key=_pref_rank)
    out = []
    while len(out) < limit and ordered_names:
        next_round = []
        for name in ordered_names:
            if len(out) >= limit:
                break
            b = buckets[name]
            if b:
                out.append(b.pop(0))
            if b:
                next_round.append(name)
        ordered_names = next_round
    return out


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _fts_query(raw: str) -> str:
    tokens = re.findall(r"[\w\u0590-\u05FF']+", raw.lower())
    clean = [t.strip("'") for t in tokens if len(t.strip("'")) >= 2 and t.strip("'") not in STOPWORDS]
    if not clean:
        clean = [t.strip("'") for t in tokens if len(t.strip("'")) >= 2]
    if not clean:
        return ""
    return " OR ".join(f'"{t}"' for t in clean[:8])


def parse_refs(text: str):
    """Extract canonical (book_title, chapter, start_verse, end_verse) tuples from free text."""
    hits = []
    for m in REF_RE.finditer(text or ""):
        bk = BOOK_ALIASES.get(m.group(1).lower())
        if not bk:
            continue
        ch = int(m.group(2))
        v1 = int(m.group(3)) if m.group(3) else None
        v2 = int(m.group(4)) if m.group(4) else v1
        hits.append((bk, ch, v1, v2))
    return hits


def get_stats() -> dict:
    with get_conn() as conn:
        meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM meta")}
        books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        verses = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]
        comms = conn.execute("SELECT COUNT(*) FROM commentaries").fetchone()[0]
        docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        paras = conn.execute("SELECT COUNT(*) FROM parashiyot").fetchone()[0]
        authors = [r[0] for r in conn.execute("SELECT DISTINCT commentator FROM commentaries ORDER BY commentator")]
        return {
            "books": books,
            "verses": verses,
            "commentaries": comms,
            "documents": docs,
            "parashiyot": paras,
            "commentators": authors,
            "built_at": meta.get("built_at", ""),
            "db_size_mb": round(DB_PATH.stat().st_size / (1024 * 1024), 1) if DB_PATH.exists() else 0.0,
        }


def list_books() -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT slug, title, he_title, section, book_order, chapters_count, verses_count FROM books ORDER BY book_order"
        ).fetchall()
        return [dict(r) for r in rows]


def get_chapter(book_slug_or_title: str, chapter: int) -> dict:
    slug = BOOK_ALIASES.get(book_slug_or_title.lower().replace("_", " "), book_slug_or_title).replace(" ", "_")
    with get_conn() as conn:
        book = conn.execute("SELECT * FROM books WHERE slug = ? OR lower(title) = lower(?)", (slug, book_slug_or_title)).fetchone()
        if not book:
            return {"error": f"Book not found: {book_slug_or_title}"}
        verses = [
            dict(r)
            for r in conn.execute(
                "SELECT chapter, verse, ref, en_text, he_text FROM verses WHERE book_slug = ? AND chapter = ? ORDER BY verse",
                (book["slug"], chapter),
            ).fetchall()
        ]
        # Mark which verses have commentaries available
        c_counts = {
            r["verse"]: r["cnt"]
            for r in conn.execute(
                "SELECT verse, COUNT(*) AS cnt FROM commentaries WHERE target_book = ? AND chapter = ? GROUP BY verse",
                (book["slug"], chapter),
            ).fetchall()
        }
        for v in verses:
            v["commentary_count"] = c_counts.get(v["verse"], 0)
        return {"book": dict(book), "chapter": chapter, "verses": verses}


def lookup_verses(ref_text: str, max_verses: int = 20) -> list:
    parsed = parse_refs(ref_text)
    if not parsed:
        return []
    out = []
    with get_conn() as conn:
        for bk, ch, v1, v2 in parsed[:3]:
            slug = bk.replace(" ", "_")
            if v1 is None:
                rows = conn.execute(
                    "SELECT ref, book_title, he_book_title, chapter, verse, en_text, he_text FROM verses WHERE book_slug = ? AND chapter = ? ORDER BY verse LIMIT ?",
                    (slug, ch, max_verses),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT ref, book_title, he_book_title, chapter, verse, en_text, he_text FROM verses WHERE book_slug = ? AND chapter = ? AND verse BETWEEN ? AND ? ORDER BY verse LIMIT ?",
                    (slug, ch, v1, v2 or v1, max_verses),
                ).fetchall()
            out.extend(dict(r) for r in rows)
    return out


def get_verse_commentaries(book_slug_or_title: str, chapter: int, verse: int) -> list:
    slug = BOOK_ALIASES.get(book_slug_or_title.lower().replace("_", " "), book_slug_or_title).replace(" ", "_")
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT commentator, ref, target_ref, en_text, he_text
            FROM commentaries
            WHERE target_book = ? AND chapter = ? AND verse = ?
            ORDER BY
                CASE commentator
                    WHEN 'Rashi' THEN 1
                    WHEN 'Or HaChaim' THEN 2
                    WHEN 'Ramban' THEN 3
                    WHEN 'Ibn Ezra' THEN 4
                    WHEN 'Sforno' THEN 5
                    WHEN 'Kli Yakar' THEN 6
                    WHEN 'Chizkuni' THEN 7
                    WHEN 'Rashbam' THEN 8
                    ELSE 9
                END, comment_idx
            """,
            (slug, chapter, verse),
        ).fetchall()
        return [dict(r) for r in rows]


def search_all(query: str, limit_verses: int = 8, limit_comm: int = 6, limit_docs: int = 4) -> dict:
    q = (query or "").strip()
    if not q:
        return {"exact_verses": [], "verses": [], "commentaries": [], "documents": [], "parashiyot": []}

    exact_verses = lookup_verses(q, max_verses=10)
    fts_q = _fts_query(q)
    req_comms = _detect_requested_commentators(q)
    verses, comm_pool, docs, paras = [], [], [], []
    with get_conn() as conn:
        # 1. Pull commentaries directly for exact verse hits (wide pool -> diversified across commentators!)
        if exact_verses:
            for v_hit in exact_verses[:2]:
                bk_slug = v_hit["book_title"].replace(" ", "_")
                c_rows = conn.execute(
                    """
                    SELECT commentator, ref, target_ref, en_text, he_text
                    FROM commentaries
                    WHERE target_book = ? AND chapter = ? AND verse = ?
                    ORDER BY
                        CASE commentator
                            WHEN 'Rashi' THEN 1
                            WHEN 'Or HaChaim' THEN 2
                            WHEN 'Ramban' THEN 3
                            WHEN 'Ibn Ezra' THEN 4
                            WHEN 'Sforno' THEN 5
                            WHEN 'Kli Yakar' THEN 6
                            WHEN 'Chizkuni' THEN 7
                            WHEN 'Rashbam' THEN 8
                            ELSE 9
                        END, comment_idx
                    LIMIT ?
                    """,
                    (bk_slug, v_hit["chapter"], v_hit["verse"], limit_comm * 3),
                ).fetchall()
                comm_pool.extend(dict(r) for r in c_rows)

        # 2. Match Parashah by exact name/slug tokens inside conversational questions too!
        q_low = q.lower()
        q_tokens = set(re.findall(r"[a-z]{2,}", q_low))
        all_paras = [dict(r) for r in conn.execute("SELECT * FROM parashiyot ORDER BY order_num").fetchall()]
        for p in all_paras:
            p_slug = (p.get("slug") or "").lower()
            p_name = (p.get("en_name") or "").lower()
            name_hit = bool(p_name and re.search(rf"\b{re.escape(p_name)}\b", q_low))
            if name_hit or (p_slug and p_slug in q_tokens) or (p.get("he_name") and p["he_name"] in q):
                paras.append(p)
        if not paras:
            like_q = f"%{q}%"
            p_rows = conn.execute(
                "SELECT * FROM parashiyot WHERE lower(en_name) LIKE lower(?) OR he_name LIKE ? OR lower(summary) LIKE lower(?) ORDER BY order_num LIMIT 3",
                (like_q, like_q, like_q),
            ).fetchall()
            paras = [dict(r) for r in p_rows]
        paras = paras[:3]

        # 3. Auto-boost matching Living Scribe (Mini-Orca) Parashah & Tanakh Book study sheets!
        seen_doc_slugs = set()
        for p in paras[:2]:
            s_slug = f"scribe-parasha-{p['slug']}"
            row = conn.execute(
                "SELECT slug, category, title, he_title, subtitle, refs, kid_story, adult_analysis, commentators_note, discussion_questions, body_md FROM documents WHERE slug = ?",
                (s_slug,),
            ).fetchone()
            if row and row["slug"] not in seen_doc_slugs:
                docs.append(dict(row))
                seen_doc_slugs.add(row["slug"])
        for alias, book_title in BOOK_ALIASES.items():
            if len(alias) >= 4 and re.search(rf"\b{re.escape(alias)}\b", q_low):
                b_slug = f"scribe-book-{book_title.lower().replace(' ', '-')}"
                row = conn.execute(
                    "SELECT slug, category, title, he_title, subtitle, refs, kid_story, adult_analysis, commentators_note, discussion_questions, body_md FROM documents WHERE slug = ?",
                    (b_slug,),
                ).fetchone()
                if row and row["slug"] not in seen_doc_slugs:
                    docs.append(dict(row))
                    seen_doc_slugs.add(row["slug"])
                    break

        if fts_q:
            try:
                v_rows = conn.execute(
                    """
                    SELECT v.ref, v.book_title, v.he_book_title, v.section, v.chapter, v.verse, v.en_text, v.he_text
                    FROM verses_fts f
                    JOIN verses v ON v.id = f.rowid
                    WHERE verses_fts MATCH ?
                    ORDER BY bm25(verses_fts)
                    LIMIT ?
                    """,
                    (fts_q, limit_verses),
                ).fetchall()
                verses = [dict(r) for r in v_rows]
            except sqlite3.OperationalError:
                pass

            # Pull FTS commentaries (including explicit commentator boost if requested!)
            try:
                if req_comms:
                    like_clauses = " OR ".join("lower(c.commentator) LIKE ?" for _ in req_comms)
                    like_params = [f"%{rc.lower()}%" for rc in req_comms]
                    c_pref = conn.execute(
                        f"""
                        SELECT c.commentator, c.ref, c.target_ref, c.en_text, c.he_text
                        FROM commentaries_fts f
                        JOIN commentaries c ON c.id = f.rowid
                        WHERE commentaries_fts MATCH ? AND ({like_clauses})
                        ORDER BY bm25(commentaries_fts)
                        LIMIT ?
                        """,
                        (fts_q, *like_params, limit_comm * 2),
                    ).fetchall()
                    comm_pool.extend(dict(r) for r in c_pref)

                c_rows = conn.execute(
                    """
                    SELECT c.commentator, c.ref, c.target_ref, c.en_text, c.he_text
                    FROM commentaries_fts f
                    JOIN commentaries c ON c.id = f.rowid
                    WHERE commentaries_fts MATCH ?
                    ORDER BY bm25(commentaries_fts)
                    LIMIT ?
                    """,
                    (fts_q, limit_comm * 3),
                ).fetchall()
                comm_pool.extend(dict(r) for r in c_rows)
            except sqlite3.OperationalError:
                pass

            try:
                d_rows = conn.execute(
                    """
                    SELECT d.slug, d.category, d.title, d.he_title, d.subtitle, d.refs, d.kid_story, d.adult_analysis, d.commentators_note, d.discussion_questions, d.body_md
                    FROM documents_fts f
                    JOIN documents d ON d.id = f.rowid
                    WHERE documents_fts MATCH ?
                    ORDER BY bm25(documents_fts)
                    LIMIT ?
                    """,
                    (fts_q, limit_docs + 2),
                ).fetchall()
                for r in d_rows:
                    d = dict(r)
                    if d["slug"] not in seen_doc_slugs:
                        docs.append(d)
                        seen_doc_slugs.add(d["slug"])
            except sqlite3.OperationalError:
                pass

    comms = _diversify_commentaries(comm_pool, limit=limit_comm, preferred=req_comms)
    return {
        "exact_verses": exact_verses,
        "verses": verses,
        "commentaries": comms,
        "documents": docs[:limit_docs],
        "parashiyot": paras,
    }


def list_documents(category: str = None) -> list:
    with get_conn() as conn:
        if category:
            rows = conn.execute("SELECT * FROM documents WHERE category = ? ORDER BY slug", (category,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM documents ORDER BY category, slug").fetchall()
        return [dict(r) for r in rows]


def get_document(slug: str) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM documents WHERE slug = ?", (slug,)).fetchone()
        return dict(row) if row else None


def list_parashiyot() -> list:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM parashiyot ORDER BY order_num").fetchall()]


def get_parasha_verses(parasha: dict, max_verses: int = 80) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT chapter, verse, ref, en_text, he_text
            FROM verses
            WHERE book_slug = ?
              AND ((chapter > ? OR (chapter = ? AND verse >= ?))
               AND (chapter < ? OR (chapter = ? AND verse <= ?)))
            ORDER BY chapter, verse
            LIMIT ?
            """,
            (
                parasha["book_slug"],
                parasha["start_ch"], parasha["start_ch"], parasha["start_v"],
                parasha["end_ch"], parasha["end_ch"], parasha["end_v"],
                max_verses,
            ),
        ).fetchall()
        return [dict(r) for r in rows]


def get_weekly_parasha() -> dict:
    """Fetch live weekly Parashat Hashavua from Sefaria (cached per local calendar day), with offline calendar fallback."""
    now = time.time()
    today_iso = time.strftime("%Y-%m-%d")
    cached = None
    if PARASHA_CACHE.exists():
        try:
            cached = json.loads(PARASHA_CACHE.read_text(encoding="utf-8"))
            if cached.get("cache_date") == today_iso and (now - float(cached.get("fetched_at", 0))) < 43200:
                return cached["data"]
        except Exception:
            pass

    live_name = None
    live_he = None
    live_ref = None
    live_aliyot = []
    live_haftarah = None
    live_daf_yomi = None
    live_929 = None
    live_date = time.strftime("%Y-%m-%d")

    try:
        lt = time.localtime()
        in_il = False
        cfg_p = BASE_DIR / "config.json"
        if cfg_p.exists():
            try:
                in_il = bool((json.loads(cfg_p.read_text(encoding="utf-8")).get("location") or {}).get("in_israel", False))
            except Exception:
                pass
        diaspora = 0 if in_il else 1
        cal_url = f"https://www.sefaria.org/api/calendars?year={lt.tm_year}&month={lt.tm_mon}&day={lt.tm_mday}&diaspora={diaspora}"
        req = urllib.request.Request(cal_url, headers={"User-Agent": "TorahSanctuary/1.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            cal = json.loads(r.read().decode("utf-8"))
        live_date = cal.get("date", live_date)
        for item in cal.get("calendar_items", []):
            title_en = (item.get("title") or {}).get("en", "")
            if title_en == "Parashat Hashavua":
                live_name = (item.get("displayValue") or {}).get("en", "")
                live_he = (item.get("displayValue") or {}).get("he", "")
                live_ref = item.get("ref", "")
                live_aliyot = (item.get("extraDetails") or {}).get("aliyot", [])
            elif title_en == "Haftarah":
                live_haftarah = item.get("ref", "")
            elif title_en == "Daf Yomi":
                dv = item.get("displayValue") or {}
                live_daf_yomi = f"{dv.get('en', '')} ({dv.get('he', '')})".strip()
            elif title_en == "929":
                dv = item.get("displayValue") or {}
                live_929 = dv.get("en", "")
    except Exception:
        pass

    with get_conn() as conn:
        row = None
        if live_name:
            # Normalize e.g. "Vayetzei" / "Lech-Lecha"
            norm = re.sub(r"[^a-z0-9]", "", live_name.lower())
            for r in conn.execute("SELECT * FROM parashiyot ORDER BY order_num").fetchall():
                if re.sub(r"[^a-z0-9]", "", r["en_name"].lower()) == norm or r["he_name"] == live_he:
                    row = dict(r)
                    break
        if row is None and cached and cached.get("data"):
            return cached["data"]
        if row is None:
            # Offline fallback based on week of Jewish year (~Simchat Torah in late Oct -> week index)
            doy = time.localtime().tm_yday
            approx_idx = ((doy - 295) % 365) // 7 + 1
            approx_idx = max(1, min(54, approx_idx))
            row = dict(conn.execute("SELECT * FROM parashiyot WHERE order_num = ?", (approx_idx,)).fetchone())

    result = {
        **row,
        "date": live_date,
        "aliyot": live_aliyot,
        "live_haftarah": live_haftarah or row["haftarah_ref"],
        "daf_yomi": live_daf_yomi or "",
        "tanakh_929": live_929 or "",
        "source": "live" if live_name else "offline_calendar",
        "verses_preview": get_parasha_verses(row, max_verses=45),
    }
    try:
        PARASHA_CACHE.write_text(json.dumps({"fetched_at": now, "cache_date": today_iso, "data": result}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return result


DAILY_LABELS = [
    ("Sunday", "יום ראשון", "1st Aliyah · Rishon", "ראשון"),
    ("Monday", "יום שני", "2nd Aliyah · Sheni", "שני"),
    ("Tuesday", "יום שלישי", "3rd Aliyah · Shlishi", "שלישי"),
    ("Wednesday", "יום רביעי", "4th Aliyah · Revi'i", "רביעי"),
    ("Thursday", "יום חמישי", "5th Aliyah · Chamishi", "חמישי"),
    ("Friday", "יום שישי", "6th Aliyah · Shishi", "שישי"),
    ("Shabbat", "שבת קודש", "7th Aliyah · Shevi'i & Haftarah", "שביעי ומפטיר"),
]

SPAN_RE = re.compile(r"^([A-Za-z0-9\s]+?)\s+(\d+):(\d+)\s*[-–]\s*(?:(\d+):)?(\d+)$")


def get_verses_for_span(book_slug: str, span_ref: str) -> list:
    m = SPAN_RE.match((span_ref or "").strip())
    if not m:
        return []
    bk_raw = m.group(1).strip()
    bk_title = BOOK_ALIASES.get(bk_raw.lower(), bk_raw)
    slug = bk_title.replace(" ", "_") or book_slug
    c1, v1 = int(m.group(2)), int(m.group(3))
    c2 = int(m.group(4)) if m.group(4) else c1
    v2 = int(m.group(5))
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT book_slug, book_title, chapter, verse, ref, en_text, he_text
            FROM verses
            WHERE book_slug = ?
              AND ((chapter > ? OR (chapter = ? AND verse >= ?))
               AND (chapter < ? OR (chapter = ? AND verse <= ?)))
            ORDER BY chapter, verse
            """,
            (slug, c1, c1, v1, c2, c2, v2),
        ).fetchall()
        return [dict(r) for r in rows]


def get_daily_portion(day_index: int = None) -> dict:
    """
    Returns today's exact Aliyah (Sunday=0 .. Saturday=6) of the Weekly Parashah,
    with Hebrew + English verses, linked Rashi/Ramban/Ibn Ezra/Sforno commentary,
    curated story tie-in, spotlight slides, and scrolling sanctuary ticker messages.
    """
    # Python tm_wday: Mon=0..Sun=6 -> Jewish week index: Sun=0, Mon=1..Sat=6
    lt = time.localtime()
    today_idx = (lt.tm_wday + 1) % 7
    idx = today_idx if day_index is None else max(0, min(6, int(day_index)))

    parasha = get_weekly_parasha()
    book_slug = parasha["book_slug"]
    aliyot_raw = list(parasha.get("aliyot") or [])

    # Build 7 daily aliyot (using Sefaria's exact 7 aliyot, or offline balanced 7-way split)
    all_parasha_verses = get_parasha_verses(parasha, max_verses=350)
    daily_refs = []
    if len(aliyot_raw) >= 7:
        daily_refs = aliyot_raw[:7]
        day_verses = get_verses_for_span(book_slug, daily_refs[idx])
    else:
        n = len(all_parasha_verses)
        chunk = max(1, (n + 6) // 7)
        buckets = [all_parasha_verses[i * chunk:(i + 1) * chunk] for i in range(7)]
        for b in buckets:
            if b:
                daily_refs.append(f"{parasha['book_slug'].replace('_', ' ')} {b[0]['chapter']}:{b[0]['verse']}-{b[-1]['chapter']}:{b[-1]['verse']}")
            else:
                daily_refs.append(parasha["ref"])
        day_verses = buckets[idx] if idx < len(buckets) else all_parasha_verses[:15]

    if not day_verses:
        day_verses = all_parasha_verses[:18]

    # Attach best classical commentaries for every verse in today's Aliyah
    enriched_verses = []
    with get_conn() as conn:
        for v in day_verses:
            c_rows = conn.execute(
                """
                SELECT commentator, ref, target_ref, en_text, he_text
                FROM commentaries
                WHERE target_book = ? AND chapter = ? AND verse = ? AND length(en_text) > 15
                ORDER BY
                    CASE commentator
                        WHEN 'Rashi' THEN 1
                        WHEN 'Ramban' THEN 2
                        WHEN 'Sforno' THEN 3
                        WHEN 'Ibn Ezra' THEN 4
                        ELSE 5
                    END, comment_idx
                LIMIT 3
                """,
                (book_slug, v["chapter"], v["verse"]),
            ).fetchall()
            comms = [dict(r) for r in c_rows]
            enriched_verses.append({**v, "commentaries": comms})

        # Find a matching curated story dossier for this Parashah's book/chapters (match CHAPTERS only, never verse numbers!)
        matching_story = None
        for d in conn.execute("SELECT slug, title, he_title, subtitle, refs, kid_story, adult_analysis, discussion_questions FROM documents WHERE category = 'story' ORDER BY slug").fetchall():
            d_dict = dict(d)
            refs_txt = d_dict["refs"] or ""
            if parasha["book_slug"].replace("_", " ").lower() in refs_txt.lower():
                # Extract real chapter numbers: e.g. "Genesis 12:1-3; 18:1-33" -> [12, 18], "Genesis 28-33" -> [28..33]
                chapters = set()
                for m_ch in re.finditer(r"(?:^|[\s;,])(\d+)(?=:)", refs_txt):
                    chapters.add(int(m_ch.group(1)))
                for m_rng in re.finditer(r"[A-Za-z]\s+(\d+)\s*[-–]\s*(\d+)(?!\s*:)", refs_txt):
                    c1, c2 = int(m_rng.group(1)), int(m_rng.group(2))
                    if c1 <= c2 <= 150:
                        chapters.update(range(c1, c2 + 1))
                for _bk, ch, _v1, _v2 in parse_refs(refs_txt):
                    if _bk.replace(" ", "_").lower() == parasha["book_slug"].lower():
                        chapters.add(ch)
                if any(parasha["start_ch"] <= ch <= parasha["end_ch"] for ch in chapters):
                    matching_story = d_dict
                    break

    day_en, day_he, aliyah_en, aliyah_he = DAILY_LABELS[idx]
    aliyah_ref = daily_refs[idx] if idx < len(daily_refs) else parasha["ref"]

    # Build reverent spotlight slides & scrolling sanctuary marquee messages for TODAY's portion
    slides = [
        {
            "kind": "banner",
            "kicker": f"{day_en} · {aliyah_en}",
            "he_kicker": f"{day_he} · {aliyah_he}",
            "title": f"Parashat {parasha['en_name']}",
            "he_title": f"פרשת {parasha['he_name']}",
            "ref": aliyah_ref,
            "en_text": parasha["summary"],
            "he_text": f"קריאת היום: {aliyah_ref}",
            "commentator": "Weekly Parashah & Daily Aliyah",
            "commentary": f"Full Portion: {parasha['ref']}  ·  Haftarah: {parasha.get('live_haftarah') or parasha['haftarah_ref']}"
            + (f"  ·  Daf Yomi: {parasha['daf_yomi']}" if parasha.get("daf_yomi") else ""),
        }
    ]

    ticker_items = [
        f"✡ TODAY'S TORAH READING ({day_en} — {aliyah_en}): Parashat {parasha['en_name']} ({parasha['he_name']}) · {aliyah_ref}",
        f"📖 Weekly Theme: {parasha['summary']}",
    ]
    if parasha.get("live_haftarah"):
        ticker_items.append(f"📜 This Shabbat's Haftarah: {parasha['live_haftarah']}" + (f"  ·  Daf Yomi: {parasha['daf_yomi']}" if parasha.get("daf_yomi") else ""))

    for v in enriched_verses:
        top_c = v["commentaries"][0] if v["commentaries"] else None
        c_snippet = ""
        c_author = ""
        if top_c:
            c_author = top_c["commentator"]
            raw_c = top_c["en_text"].strip()
            c_snippet = (raw_c[:340].rsplit(" ", 1)[0] + "...") if len(raw_c) > 340 else raw_c

        slides.append({
            "kind": "verse",
            "kicker": f"Parashat {parasha['en_name']} · {day_en} ({aliyah_en})",
            "he_kicker": f"פרשת {parasha['he_name']} · {aliyah_he}",
            "title": v["ref"],
            "he_title": parasha["he_name"],
            "ref": v["ref"],
            "book_slug": book_slug,
            "chapter": v["chapter"],
            "verse": v["verse"],
            "en_text": v["en_text"],
            "he_text": v["he_text"],
            "commentator": c_author,
            "commentary": c_snippet,
            "all_commentaries": v["commentaries"],
        })

        v_short = (v["en_text"][:170].rsplit(" ", 1)[0] + "...") if len(v["en_text"]) > 170 else v["en_text"]
        ticker_items.append(f"✦ {v['ref']} — “{v_short}”")
        if top_c and len(ticker_items) < 28:
            tc_short = (top_c["en_text"][:175].rsplit(" ", 1)[0] + "...") if len(top_c["en_text"]) > 175 else top_c["en_text"]
            ticker_items.append(f"💡 {top_c['commentator']} on {v['ref']}: {tc_short}")

    if matching_story:
        kid_snip = (matching_story["kid_story"][:420].rsplit(" ", 1)[0] + "...") if len(matching_story["kid_story"]) > 420 else matching_story["kid_story"]
        slides.append({
            "kind": "story",
            "kicker": f"Torah Story for Parashat {parasha['en_name']}",
            "he_kicker": matching_story["he_title"],
            "title": matching_story["title"],
            "he_title": matching_story["he_title"],
            "ref": matching_story["refs"],
            "slug": matching_story["slug"],
            "en_text": kid_snip,
            "he_text": matching_story["he_title"],
            "commentator": "Shabbat Table Reflection",
            "commentary": matching_story.get("discussion_questions", "")[:320],
        })
        ticker_items.append(f"✨ Story Spotlight ({matching_story['title']}): {matching_story['subtitle']}")

    return {
        "date_str": time.strftime("%A, %B %d, %Y", lt),
        "today_index": today_idx,
        "selected_day_index": idx,
        "day_en": day_en,
        "day_he": day_he,
        "aliyah_number": idx + 1,
        "aliyah_en": aliyah_en,
        "aliyah_he": aliyah_he,
        "aliyah_ref": aliyah_ref,
        "daily_schedule": [
            {
                "day_index": i,
                "day_en": DAILY_LABELS[i][0],
                "day_he": DAILY_LABELS[i][1],
                "aliyah_en": DAILY_LABELS[i][2],
                "aliyah_he": DAILY_LABELS[i][3],
                "ref": daily_refs[i] if i < len(daily_refs) else parasha["ref"],
                "is_today": i == today_idx,
            }
            for i in range(7)
        ],
        "parasha": {
            "en_name": parasha["en_name"],
            "he_name": parasha["he_name"],
            "ref": parasha["ref"],
            "haftarah": parasha.get("live_haftarah") or parasha["haftarah_ref"],
            "daf_yomi": parasha.get("daf_yomi", ""),
            "tanakh_929": parasha.get("tanakh_929", ""),
            "summary": parasha["summary"],
            "book_slug": book_slug,
        },
        "verses_count": len(enriched_verses),
        "slides": slides,
        "ticker_items": ticker_items,
        "matching_story": {
            "slug": matching_story["slug"],
            "title": matching_story["title"],
            "he_title": matching_story["he_title"],
            "subtitle": matching_story["subtitle"],
        } if matching_story else None,
    }
