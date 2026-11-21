#!/usr/bin/env python3
"""
Torah Sanctuary — Authoritative Sefaria Tanakh, Commentaries, Midrash & Knowledge Base Ingestor.
Builds a 100% offline-capable SQLite + FTS5 database at data/torah.db.
"""

import concurrent.futures
import html
import json
import os
import pathlib
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
DB_PATH = DATA_DIR / "torah.db"

TANAKH_BOOKS = [
    # Torah (Chumash) — 5 books
    ("Genesis", "בראשית", "Torah", 50),
    ("Exodus", "שמות", "Torah", 40),
    ("Leviticus", "ויקרא", "Torah", 27),
    ("Numbers", "במדבר", "Torah", 36),
    ("Deuteronomy", "דברים", "Torah", 34),
    # Nevi'im (Prophets) — 21 books
    ("Joshua", "יהושע", "Neviim", 24),
    ("Judges", "שופטים", "Neviim", 21),
    ("I Samuel", "שמואל א", "Neviim", 31),
    ("II Samuel", "שמואל ב", "Neviim", 24),
    ("I Kings", "מלכים א", "Neviim", 22),
    ("II Kings", "מלכים ב", "Neviim", 25),
    ("Isaiah", "ישעיהו", "Neviim", 66),
    ("Jeremiah", "ירמיהו", "Neviim", 52),
    ("Ezekiel", "יחזקאל", "Neviim", 48),
    ("Hosea", "הושע", "Neviim", 14),
    ("Joel", "יואל", "Neviim", 4),
    ("Amos", "עמוס", "Neviim", 9),
    ("Obadiah", "עובדיה", "Neviim", 1),
    ("Jonah", "יונה", "Neviim", 4),
    ("Micah", "מיכה", "Neviim", 7),
    ("Nahum", "נחום", "Neviim", 3),
    ("Habakkuk", "חבקוק", "Neviim", 3),
    ("Zephaniah", "צפניה", "Neviim", 3),
    ("Haggai", "חגי", "Neviim", 2),
    ("Zechariah", "זכריה", "Neviim", 14),
    ("Malachi", "מלאכי", "Neviim", 3),
    # Ketuvim (Writings) — 13 books
    ("Psalms", "תהילים", "Ketuvim", 150),
    ("Proverbs", "משלי", "Ketuvim", 31),
    ("Job", "איוב", "Ketuvim", 42),
    ("Song of Songs", "שיר השירים", "Ketuvim", 8),
    ("Ruth", "רות", "Ketuvim", 4),
    ("Lamentations", "איכה", "Ketuvim", 5),
    ("Ecclesiastes", "קהלת", "Ketuvim", 12),
    ("Esther", "אסתר", "Ketuvim", 10),
    ("Daniel", "דניאל", "Ketuvim", 12),
    ("Ezra", "עזרא", "Ketuvim", 10),
    ("Nehemiah", "נחמיה", "Ketuvim", 13),
    ("I Chronicles", "דברי הימים א", "Ketuvim", 29),
    ("II Chronicles", "דברי הימים ב", "Ketuvim", 36),
]

TORAH_COMMENTARIES = [
    ("Rashi", "Rashi_on_{book}", ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]),
    ("Ramban", "Ramban_on_{book}", ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]),
    ("Ibn Ezra", "Ibn_Ezra_on_{book}", ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]),
    ("Sforno", "Sforno_on_{book}", ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]),
]

# All 54 Weekly Parashiyot
PARASHIYOT = [
    (1, "Bereshit", "בראשית", "Genesis", "Genesis 1:1-6:8", 1, 1, 6, 8, "Isaiah 42:5-43:10", "Creation of the world, Shabbat, Adam and Eve in Eden, Cain and Abel, and the generations leading to Noah."),
    (2, "Noach", "נח", "Genesis", "Genesis 6:9-11:32", 6, 9, 11, 32, "Isaiah 54:1-55:5", "Noah builds the Ark, the Great Flood, the rainbow covenant, the Tower of Babel, and the lineage to Abram."),
    (3, "Lech-Lecha", "לך-לך", "Genesis", "Genesis 12:1-17:27", 12, 1, 17, 27, "Isaiah 40:27-41:16", "God calls Abram to leave his homeland for Canaan, the Covenant Between the Parts, Hagar and Ishmael, and brit milah."),
    (4, "Vayera", "וירא", "Genesis", "Genesis 18:1-22:24", 18, 1, 22, 24, "II Kings 4:1-37", "Abraham's hospitality to three visitors, pleading for Sodom, birth of Isaac, and the Binding of Isaac (Akeidah)."),
    (5, "Chayei Sara", "חיי שרה", "Genesis", "Genesis 23:1-25:18", 23, 1, 25, 18, "I Kings 1:1-31", "Purchase of the Cave of Machpelah for Sarah, Eliezer's mission to find Rebecca for Isaac, and Abraham's final years."),
    (6, "Toldot", "תולדות", "Genesis", "Genesis 25:19-28:9", 25, 19, 28, 9, "Malachi 1:1-2:7", "Birth of twins Esau and Jacob, the birthright, Isaac's wells in Gerar, and Jacob receiving Isaac's blessing."),
    (7, "Vayetzei", "ויצא", "Genesis", "Genesis 28:10-32:3", 28, 10, 32, 3, "Hosea 12:13-14:10", "Jacob's dream of the ladder at Beit El, fourteen years serving Laban for Rachel and Leah, birth of the tribes, and departure."),
    (8, "Vayishlach", "וישלח", "Genesis", "Genesis 32:4-36:43", 32, 4, 36, 43, "Obadiah 1:1-21", "Jacob wrestles with the angel and is named Israel, peaceful reunion with Esau, Dinah, and Rachel's passing."),
    (9, "Vayeshev", "וישב", "Genesis", "Genesis 37:1-40:23", 37, 1, 40, 23, "Amos 2:6-3:8", "Joseph's coat and dreams, sold into Egypt by his brothers, Judah and Tamar, Potiphar's house, and interpreting prison dreams."),
    (10, "Miketz", "מקץ", "Genesis", "Genesis 41:1-44:17", 41, 1, 44, 17, "I Kings 3:15-4:1", "Joseph interprets Pharaoh's dreams, becomes viceroy of Egypt, stores grain for the famine, and tests his brothers."),
    (11, "Vayigash", "ויגש", "Genesis", "Genesis 44:18-47:27", 44, 18, 47, 27, "Ezekiel 37:15-28", "Judah pleads for Benjamin, Joseph reveals his identity and forgives his brothers, and Jacob's family settles in Goshen."),
    (12, "Vayechi", "ויחי", "Genesis", "Genesis 47:28-50:26", 47, 28, 50, 26, "I Kings 2:1-12", "Jacob blesses Ephraim, Manasseh, and all twelve sons before his passing; Joseph reassures his brothers of God's providence."),
    (13, "Shemot", "שמות", "Exodus", "Exodus 1:1-6:1", 1, 1, 6, 1, "Isaiah 27:6-28:13", "Enslavement in Egypt, the courageous midwives, Moses saved from the Nile, the Burning Bush, and confronting Pharaoh."),
    (14, "Vaera", "וארא", "Exodus", "Exodus 6:2-9:35", 6, 2, 9, 35, "Ezekiel 28:25-29:21", "God's four promises of redemption and the first seven plagues upon Egypt: blood, frogs, lice, swarms, pestilence, boils, hail."),
    (15, "Bo", "בא", "Exodus", "Exodus 10:1-13:16", 10, 1, 13, 16, "Jeremiah 46:13-28", "The final three plagues (locusts, darkness, firstborn), the first Passover, the Exodus from Egypt, and mitzvot of remembrance."),
    (16, "Beshalach", "בשלח", "Exodus", "Exodus 13:17-17:16", 13, 17, 17, 16, "Judges 4:4-5:31", "Splitting of the Sea of Reeds, Song of the Sea (Shirat HaYam), manna from heaven, water from the rock, and Amalek."),
    (17, "Yitro", "יתרו", "Exodus", "Exodus 18:1-20:23", 18, 1, 20, 23, "Isaiah 6:1-7:6", "Jethro advises Moses on building a judicial system; the Revelation at Mount Sinai and the Ten Commandments."),
    (18, "Mishpatim", "משפטים", "Exodus", "Exodus 21:1-24:18", 21, 1, 24, 18, "Jeremiah 34:8-22", "Civil, ethical, and social justice laws protecting workers, strangers, and the vulnerable; Israel declares 'Na'aseh v'Nishma'."),
    (19, "Terumah", "תרומה", "Exodus", "Exodus 25:1-27:19", 25, 1, 27, 19, "I Kings 5:26-6:13", "Voluntary gifts of the heart to build the Mishkan (Tabernacle) — Ark, Menorah, Table, and Courtyard — so God may dwell among Israel."),
    (20, "Tetzaveh", "תצוה", "Exodus", "Exodus 27:20-30:10", 27, 20, 30, 10, "Ezekiel 43:10-27", "The Ner Tamid (eternal light), priestly garments of splendor and dignity for Aaron and his sons, and their consecration."),
    (21, "Ki Tisa", "כי תשא", "Exodus", "Exodus 30:11-34:35", 30, 11, 34, 35, "I Kings 18:1-39", "The half-shekel census, Shabbat, the sin of the Golden Calf, Moses' intercession, the Thirteen Attributes of Mercy, and the second Tablets."),
    (22, "Vayakhel", "ויקהל", "Exodus", "Exodus 35:1-38:20", 35, 1, 38, 20, "I Kings 7:40-50", "Shabbat observance and the joyful generosity of the whole community, led by Bezalel and Oholiab, constructing the Mishkan."),
    (23, "Pekudei", "פקודי", "Exodus", "Exodus 38:21-40:38", 38, 21, 40, 38, "I Kings 7:51-8:21", "Full transparent accounting of all Mishkan donations, completion of the Sanctuary, and God's Presence filling the Tabernacle."),
    (24, "Vayikra", "ויקרא", "Leviticus", "Leviticus 1:1-5:26", 1, 1, 5, 26, "Isaiah 43:21-44:23", "God calls affectionately to Moses; laws of voluntary and atonement offerings (korbanot) as pathways of drawing near."),
    (25, "Tzav", "צו", "Leviticus", "Leviticus 6:1-8:36", 6, 1, 8, 36, "Jeremiah 7:21-8:3", "Priestly duties for the altar fire that never goes out, thanksgiving offerings, and the seven-day inauguration of the Mishkan."),
    (26, "Shmini", "שמיני", "Leviticus", "Leviticus 9:1-11:47", 9, 1, 11, 47, "II Samuel 6:1-7:17", "The eighth day of dedication, the tragedy of Nadav and Avihu, and the foundational dietary laws of Kashrut."),
    (27, "Tazria", "תזריע", "Leviticus", "Leviticus 12:1-13:59", 12, 1, 13, 59, "II Kings 4:42-5:19", "Ritual purity after childbirth and the spiritual diagnosis of tzara'at (traditionally linked to harmful speech, lashon hara)."),
    (28, "Metzora", "מצורע", "Leviticus", "Leviticus 14:1-15:33", 14, 1, 15, 33, "II Kings 7:3-20", "Purification and restoration of one afflicted with tzara'at back into the community, and laws of family and household purity."),
    (29, "Achrei Mot", "אחרי מות", "Leviticus", "Leviticus 16:1-18:30", 16, 1, 18, 30, "Ezekiel 22:1-19", "The Yom Kippur service of the High Priest, the principle 'you shall live by them', and laws of ethical family holiness."),
    (30, "Kedoshim", "קדושים", "Leviticus", "Leviticus 19:1-20:27", 19, 1, 20, 27, "Amos 9:7-15", "The Holiness Code: 'Love your neighbor as yourself', leaving harvest corners for the poor, honest weights, and honoring elders."),
    (31, "Emor", "אמור", "Leviticus", "Leviticus 21:1-24:23", 21, 1, 24, 23, "Ezekiel 44:15-31", "Priestly standards of holiness, sanctifying God's Name (Kiddush Hashem), and the complete annual calendar of Jewish festivals."),
    (32, "Behar", "בהר", "Leviticus", "Leviticus 25:1-26:2", 25, 1, 26, 2, "Jeremiah 32:6-27", "Sabbatical year (Shmita) resting the land, the Jubilee (Yovel) proclaiming liberty, ethical lending without interest, and fair trade."),
    (33, "Bechukotai", "בחוקותי", "Leviticus", "Leviticus 26:3-27:34", 26, 3, 27, 34, "Jeremiah 16:19-17:14", "Blessings of walking in God's ways, the sobering rebuke (Tochachah), the eternal covenant never broken, and vows of dedication."),
    (34, "Bamidbar", "במדבר", "Numbers", "Numbers 1:1-4:20", 1, 1, 4, 20, "Hosea 2:1-22", "Census showing every individual matters in the wilderness camp, the banners of the twelve tribes, and Levitical duties."),
    (35, "Nasso", "נשא", "Numbers", "Numbers 4:21-7:89", 4, 21, 7, 89, "Judges 13:2-25", "The Nazirite vow, the Priestly Blessing (Birkat Kohanim), and the twelve tribal leaders' identical gifts to dedicate the Altar."),
    (36, "Beha'alotcha", "בהעלותך", "Numbers", "Numbers 8:1-12:16", 8, 1, 12, 16, "Zechariah 2:14-4:7", "Kindling the Menorah, Pesach Sheni (second chances), the silver trumpets, journeying from Sinai, seventy elders, and Miriam."),
    (37, "Sh'lach", "שלח", "Numbers", "Numbers 13:1-15:41", 13, 1, 15, 41, "Joshua 2:1-24", "The twelve spies scout the Land of Israel, Caleb and Joshua's courage, challah offering, and the mitzvah of tzitzit."),
    (38, "Korach", "קרח", "Numbers", "Numbers 16:1-18:32", 16, 1, 18, 32, "I Samuel 11:14-12:22", "Korach's rebellion against Moses and Aaron, the lesson of constructive vs. destructive debate, and Aaron's blossoming staff."),
    (39, "Chukat", "חקת", "Numbers", "Numbers 19:1-22:1", 19, 1, 22, 1, "Judges 11:1-33", "The Red Heifer (Parah Adumah), Miriam's passing and the waters of Merivah, Aaron's passing, and victories east of the Jordan."),
    (40, "Balak", "בלק", "Numbers", "Numbers 22:2-25:9", 22, 2, 25, 9, "Micah 5:6-6:8", "King Balak hires Balaam to curse Israel, Balaam's talking donkey, and God turning every intended curse into 'Mah Tovu' blessings."),
    (41, "Pinchas", "פינחס", "Numbers", "Numbers 25:10-30:1", 25, 10, 30, 1, "I Kings 18:46-19:21", "Covenant of peace, the daughters of Zelophehad championing women's inheritance rights, Joshua chosen as successor, and festival offerings."),
    (42, "Matot", "מטות", "Numbers", "Numbers 30:2-32:42", 30, 2, 32, 42, "Jeremiah 1:1-2:3", "The power and integrity of spoken vows, Midian, and the tribes of Reuben and Gad negotiating to settle east of the Jordan."),
    (43, "Masei", "מסעי", "Numbers", "Numbers 33:1-36:13", 33, 1, 36, 13, "Jeremiah 2:4-28", "Review of all 42 wilderness journeys, borders of the Land of Israel, and the six Cities of Refuge for unintentional harm."),
    (44, "Devarim", "דברים", "Deuteronomy", "Deuteronomy 1:1-3:22", 1, 1, 3, 22, "Isaiah 1:1-27", "Moses begins his final address on the plains of Moab, reviewing Israel's 40-year journey with honesty, humility, and hope."),
    (45, "Vaetchanan", "ואתחנן", "Deuteronomy", "Deuteronomy 3:23-7:11", 3, 23, 7, 11, "Isaiah 40:1-26", "Moses pleads to enter the Land, repeats the Ten Commandments, and proclaims the Shema ('Hear O Israel') and V'ahavta."),
    (46, "Eikev", "עקב", "Deuteronomy", "Deuteronomy 7:12-11:25", 7, 12, 11, 25, "Isaiah 49:14-51:3", "Heeding even 'small' mitzvot, gratitude and Grace After Meals (Birkat HaMazon), humility in prosperity, and the second paragraph of Shema."),
    (47, "Re'eh", "ראה", "Deuteronomy", "Deuteronomy 11:26-16:17", 11, 26, 16, 17, "Isaiah 54:11-55:5", "Choosing blessing and moral responsibility, open-handed tzedakah (charity) without a hardened heart, and the three pilgrimage festivals."),
    (48, "Shoftim", "שופטים", "Deuteronomy", "Deuteronomy 16:18-21:9", 16, 18, 21, 9, "Isaiah 51:12-52:12", "'Tzedek, tzedek tirdof' — Justice, justice shall you pursue; independent courts, limits on royal power, prophets, and environmental ethics (bal tashchit)."),
    (49, "Ki Teitzei", "כי תצא", "Deuteronomy", "Deuteronomy 21:10-25:19", 21, 10, 25, 19, "Isaiah 54:1-10", "74 mitzvot of everyday compassion: returning lost objects, kindness to animals, rooftop safety railings, fair wages, and honest weights."),
    (50, "Ki Tavo", "כי תבוא", "Deuteronomy", "Deuteronomy 26:1-29:8", 26, 1, 29, 8, "Isaiah 60:1-22", "First fruits (Bikkurim) ceremony of gratitude, Mount Gerizim and Mount Ebal covenant blessings, and remembering God's guidance."),
    (51, "Nitzavim", "נצבים", "Deuteronomy", "Deuteronomy 29:9-30:20", 29, 9, 30, 20, "Isaiah 61:10-63:9", "Everyone standing united in covenant, 'It is not in heaven', the promise of Teshuvah (return), and 'Choose life!'"),
    (52, "Vayeilech", "וילך", "Deuteronomy", "Deuteronomy 31:1-31:30", 31, 1, 31, 30, "Hosea 14:2-10", "Moses hands leadership to Joshua, institutes the Hakhel public Torah reading every seven years, and commands writing a Torah scroll."),
    (53, "Ha'Azinu", "האזינו", "Deuteronomy", "Deuteronomy 32:1-32:52", 32, 1, 32, 52, "II Samuel 22:1-51", "Moses' soaring poetic song calling heaven and earth as witnesses to God's faithfulness and Israel's destiny."),
    (54, "V'Zot HaBerachah", "וזאת הברכה", "Deuteronomy", "Deuteronomy 33:1-34:12", 33, 1, 34, 12, "Joshua 1:1-18", "Moses blesses each of the twelve tribes before ascending Mount Nebo, passing away, and completing the Five Books of the Torah."),
]

TAG_FOOTNOTE_RE = re.compile(r'<sup class="footnote-marker">.*?</sup>|<i class="footnote">.*?</i>', re.DOTALL | re.IGNORECASE)
TAG_ANY_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'\s+')


def clean_text(raw) -> str:
    if not raw:
        return ""
    if isinstance(raw, list):
        return " ".join(clean_text(x) for x in raw if x).strip()
    s = str(raw)
    s = TAG_FOOTNOTE_RE.sub("", s)
    s = s.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    s = TAG_ANY_RE.sub("", s)
    s = html.unescape(s)
    s = WS_RE.sub(" ", s).strip()
    return s


def fetch_json(url: str, retries: int = 3) -> dict:
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TorahSanctuary/1.0 (Synagogue Study Appliance)"})
            with urllib.request.urlopen(req, timeout=35) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last_err = e
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"Failed fetching {url}: {last_err}")


def init_db(conn: sqlite3.Connection):
    conn.executescript("""
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;

    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        he_title TEXT NOT NULL,
        section TEXT NOT NULL,
        book_order INTEGER NOT NULL,
        chapters_count INTEGER NOT NULL DEFAULT 0,
        verses_count INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS verses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_slug TEXT NOT NULL,
        book_title TEXT NOT NULL,
        he_book_title TEXT NOT NULL,
        section TEXT NOT NULL,
        chapter INTEGER NOT NULL,
        verse INTEGER NOT NULL,
        ref TEXT UNIQUE NOT NULL,
        en_text TEXT NOT NULL,
        he_text TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_verses_book_ch ON verses(book_slug, chapter, verse);

    CREATE VIRTUAL TABLE IF NOT EXISTS verses_fts USING fts5(
        ref, book_title, section, en_text, he_text,
        content='verses', content_rowid='id',
        tokenize='unicode61'
    );

    CREATE TABLE IF NOT EXISTS commentaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        commentator TEXT NOT NULL,
        target_book TEXT NOT NULL,
        chapter INTEGER NOT NULL,
        verse INTEGER NOT NULL,
        comment_idx INTEGER NOT NULL,
        ref TEXT UNIQUE NOT NULL,
        target_ref TEXT NOT NULL,
        en_text TEXT NOT NULL,
        he_text TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_comm_target ON commentaries(target_book, chapter, verse);
    CREATE INDEX IF NOT EXISTS idx_comm_author ON commentaries(commentator, target_book);

    CREATE VIRTUAL TABLE IF NOT EXISTS commentaries_fts USING fts5(
        commentator, target_ref, en_text, he_text,
        content='commentaries', content_rowid='id',
        tokenize='unicode61'
    );

    CREATE TABLE IF NOT EXISTS parashiyot (
        id INTEGER PRIMARY KEY,
        order_num INTEGER UNIQUE NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        en_name TEXT NOT NULL,
        he_name TEXT NOT NULL,
        book_slug TEXT NOT NULL,
        ref TEXT NOT NULL,
        start_ch INTEGER NOT NULL,
        start_v INTEGER NOT NULL,
        end_ch INTEGER NOT NULL,
        end_v INTEGER NOT NULL,
        haftarah_ref TEXT NOT NULL,
        summary TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        he_title TEXT NOT NULL DEFAULT '',
        subtitle TEXT NOT NULL DEFAULT '',
        refs TEXT NOT NULL DEFAULT '',
        kid_story TEXT NOT NULL DEFAULT '',
        adult_analysis TEXT NOT NULL DEFAULT '',
        commentators_note TEXT NOT NULL DEFAULT '',
        discussion_questions TEXT NOT NULL DEFAULT '',
        body_md TEXT NOT NULL
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
        category, title, subtitle, refs, kid_story, adult_analysis, commentators_note, body_md,
        content='documents', content_rowid='id',
        tokenize='unicode61'
    );

    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)


def rebuild_fts(conn: sqlite3.Connection):
    conn.execute("INSERT INTO verses_fts(verses_fts) VALUES('rebuild')")
    conn.execute("INSERT INTO commentaries_fts(commentaries_fts) VALUES('rebuild')")
    conn.execute("INSERT INTO documents_fts(documents_fts) VALUES('rebuild')")
    conn.commit()


def ingest_tanakh_book(idx_info):
    order_num, title, he_title, section, expected_ch = idx_info
    slug = title.replace(" ", "_")
    ref_q = urllib.parse.quote(f"{slug}.1-{expected_ch}" if expected_ch > 1 else f"{slug}.1")
    url = f"https://www.sefaria.org/api/texts/{ref_q}?context=0&commentary=0"
    d = fetch_json(url)
    en_chapters = d.get("text", [])
    he_chapters = d.get("he", [])
    # Handle single-chapter book (Obadiah) returning 1D list
    if expected_ch == 1 and en_chapters and isinstance(en_chapters[0], str):
        en_chapters = [en_chapters]
    if expected_ch == 1 and he_chapters and isinstance(he_chapters[0], str):
        he_chapters = [he_chapters]

    rows = []
    max_ch = max(len(en_chapters), len(he_chapters))
    for ch_idx in range(max_ch):
        en_ch = en_chapters[ch_idx] if ch_idx < len(en_chapters) else []
        he_ch = he_chapters[ch_idx] if ch_idx < len(he_chapters) else []
        if isinstance(en_ch, str):
            en_ch = [en_ch]
        if isinstance(he_ch, str):
            he_ch = [he_ch]
        max_v = max(len(en_ch), len(he_ch))
        for v_idx in range(max_v):
            en_v = clean_text(en_ch[v_idx]) if v_idx < len(en_ch) else ""
            he_v = clean_text(he_ch[v_idx]) if v_idx < len(he_ch) else ""
            if not en_v and not he_v:
                continue
            ref = f"{title} {ch_idx + 1}:{v_idx + 1}"
            rows.append((slug, title, he_title, section, ch_idx + 1, v_idx + 1, ref, en_v, he_v))
    return (order_num, slug, title, he_title, section, max_ch, rows)


def ingest_commentary_book(task):
    commentator, template, book_title, max_ch = task
    book_slug = book_title.replace(" ", "_")
    sef_book = template.format(book=book_slug)
    ref_q = urllib.parse.quote(f"{sef_book}.1-{max_ch}")
    url = f"https://www.sefaria.org/api/texts/{ref_q}?context=0&commentary=0"
    d = fetch_json(url)
    en_chs = d.get("text", [])
    he_chs = d.get("he", [])
    rows = []
    n_ch = max(len(en_chs), len(he_chs))
    for ch_idx in range(n_ch):
        en_ch = en_chs[ch_idx] if ch_idx < len(en_chs) else []
        he_ch = he_chs[ch_idx] if ch_idx < len(he_chs) else []
        if not isinstance(en_ch, list):
            en_ch = []
        if not isinstance(he_ch, list):
            he_ch = []
        n_v = max(len(en_ch), len(he_ch))
        for v_idx in range(n_v):
            en_v = en_ch[v_idx] if v_idx < len(en_ch) else []
            he_v = he_ch[v_idx] if v_idx < len(he_ch) else []
            if isinstance(en_v, str):
                en_v = [en_v] if en_v.strip() else []
            if isinstance(he_v, str):
                he_v = [he_v] if he_v.strip() else []
            if not isinstance(en_v, list):
                en_v = []
            if not isinstance(he_v, list):
                he_v = []
            n_c = max(len(en_v), len(he_v))
            for c_idx in range(n_c):
                en_t = clean_text(en_v[c_idx]) if c_idx < len(en_v) else ""
                he_t = clean_text(he_v[c_idx]) if c_idx < len(he_v) else ""
                if not en_t and not he_t:
                    continue
                target_ref = f"{book_title} {ch_idx + 1}:{v_idx + 1}"
                ref = f"{commentator} on {target_ref}:{c_idx + 1}"
                rows.append((commentator, book_slug, ch_idx + 1, v_idx + 1, c_idx + 1, ref, target_ref, en_t, he_t))
    return (commentator, book_title, rows)


def ingest_flat_work(commentator_label: str, sef_slug: str, target_book: str, chapters: int):
    ref_q = urllib.parse.quote(f"{sef_slug}.1-{chapters}")
    url = f"https://www.sefaria.org/api/texts/{ref_q}?context=0&commentary=0"
    d = fetch_json(url)
    en_chs = d.get("text", [])
    he_chs = d.get("he", [])
    rows = []
    n_ch = max(len(en_chs), len(he_chs))
    for ch_idx in range(n_ch):
        en_ch = en_chs[ch_idx] if ch_idx < len(en_chs) else []
        he_ch = he_chs[ch_idx] if ch_idx < len(he_chs) else []
        if not isinstance(en_ch, list):
            en_ch = [en_ch] if en_ch else []
        if not isinstance(he_ch, list):
            he_ch = [he_ch] if he_ch else []
        n_v = max(len(en_ch), len(he_ch))
        for v_idx in range(n_v):
            en_t = clean_text(en_ch[v_idx]) if v_idx < len(en_ch) else ""
            he_t = clean_text(he_ch[v_idx]) if v_idx < len(he_ch) else ""
            if not en_t and not he_t:
                continue
            target_ref = f"{target_book} {ch_idx + 1}:{v_idx + 1}"
            ref = f"{commentator_label} {ch_idx + 1}:{v_idx + 1}"
            rows.append((commentator_label, target_book.replace(" ", "_"), ch_idx + 1, v_idx + 1, 1, ref, target_ref, en_t, he_t))
    return rows


def ingest_parashiyot(conn: sqlite3.Connection):
    conn.executemany(
        """
        INSERT OR REPLACE INTO parashiyot
        (id, order_num, slug, en_name, he_name, book_slug, ref, start_ch, start_v, end_ch, end_v, haftarah_ref, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                p[0], p[0], re.sub(r"[^a-z0-9]+", "-", p[1].lower()).strip("-"),
                p[1], p[2], p[3].replace(" ", "_"), p[4], p[5], p[6], p[7], p[8], p[9], p[10]
            )
            for p in PARASHIYOT
        ],
    )
    conn.commit()


def ingest_knowledge_docs(conn: sqlite3.Connection):
    """Ingest curated Markdown dossiers (stories, history, guides) with YAML-lite frontmatter."""
    conn.execute("DELETE FROM documents")
    count = 0
    for cat_dir, cat_name in [("stories", "story"), ("history", "history"), ("guides", "guide")]:
        folder = KNOWLEDGE_DIR / cat_dir
        if not folder.exists():
            continue
        for md_path in sorted(folder.glob("*.md")):
            raw = md_path.read_text(encoding="utf-8")
            meta = {}
            body = raw
            if raw.startswith("---\n"):
                parts = raw.split("\n---\n", 1)
                if len(parts) == 2:
                    for line in parts[0].splitlines()[1:]:
                        if ":" in line:
                            k, v = line.split(":", 1)
                            meta[k.strip().lower()] = v.strip().strip('"').strip("'")
                    body = parts[1].strip()
            # Extract named sections if present
            sections = {}
            cur_sec = "intro"
            buf = []
            for line in body.splitlines():
                if line.startswith("## "):
                    sections[cur_sec] = "\n".join(buf).strip()
                    cur_sec = line[3:].strip().lower()
                    buf = []
                else:
                    buf.append(line)
            sections[cur_sec] = "\n".join(buf).strip()

            kid_story = sections.get("the story (for kids & families)", "") or sections.get("the story", "")
            adult_analysis = sections.get("deeper meaning & pardes interpretation", "") or sections.get("deeper meaning", "")
            comm_note = sections.get("what the classical commentators say", "") or sections.get("classical commentators", "")
            disc_q = sections.get("shabbat table & discussion questions", "") or sections.get("discussion questions", "")

            conn.execute(
                """
                INSERT OR REPLACE INTO documents
                (slug, category, title, he_title, subtitle, refs, kid_story, adult_analysis, commentators_note, discussion_questions, body_md)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    md_path.stem,
                    cat_name,
                    meta.get("title", md_path.stem.replace("-", " ").title()),
                    meta.get("he_title", ""),
                    meta.get("subtitle", ""),
                    meta.get("refs", ""),
                    kid_story,
                    adult_analysis,
                    comm_note,
                    disc_q,
                    body,
                ),
            )
            count += 1
    conn.commit()
    return count


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    only_docs = "--only-docs" in sys.argv
    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)
    ingest_parashiyot(conn)

    if only_docs:
        doc_cnt = ingest_knowledge_docs(conn)
        rebuild_fts(conn)
        print(f"Re-indexed {doc_cnt} curated knowledge documents + 54 parashiyot.")
        return

    t0 = time.time()
    print("1/4 Ingesting complete 39-book Tanakh (Hebrew + English) from Sefaria...")
    book_tasks = [(i + 1, b[0], b[1], b[2], b[3]) for i, b in enumerate(TANAKH_BOOKS)]
    total_verses = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for order_num, slug, title, he_title, section, ch_cnt, rows in ex.map(ingest_tanakh_book, book_tasks):
            conn.execute(
                """
                INSERT OR REPLACE INTO books (slug, title, he_title, section, book_order, chapters_count, verses_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (slug, title, he_title, section, order_num, ch_cnt, len(rows)),
            )
            conn.executemany(
                """
                INSERT OR REPLACE INTO verses (book_slug, book_title, he_book_title, section, chapter, verse, ref, en_text, he_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            total_verses += len(rows)
            print(f"  [Tanakh] {title:16s} ({section:7s}): {ch_cnt:3d} ch, {len(rows):4d} verses")
    conn.commit()
    print(f"Tanakh complete: {total_verses} verses in {time.time() - t0:.1f}s")

    print("2/4 Ingesting Classical Torah Commentaries (Rashi, Ramban, Ibn Ezra, Sforno)...")
    ch_map = {b[0]: b[3] for b in TANAKH_BOOKS}
    comm_tasks = []
    for author, tmpl, bks in TORAH_COMMENTARIES:
        for bk in bks:
            comm_tasks.append((author, tmpl, bk, ch_map[bk]))
    total_comm = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(ingest_commentary_book, t): t for t in comm_tasks}
        for fut in concurrent.futures.as_completed(futs):
            t = futs[fut]
            try:
                author, bk, rows = fut.result()
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO commentaries
                    (commentator, target_book, chapter, verse, comment_idx, ref, target_ref, en_text, he_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                total_comm += len(rows)
                print(f"  [Commentary] {author:10s} on {bk:12s}: {len(rows):5d} entries")
            except Exception as e:
                print(f"  [WARN] {t[0]} on {t[2]}: {e}")
    conn.commit()

    print("3/4 Ingesting Pirkei Avot & Midrash Rabbah (Bereishit + Shemot Rabbah)...")
    extra_works = [
        ("Pirkei Avot", "Pirkei_Avot", "Pirkei Avot", 6),
        ("Midrash Bereishit Rabbah", "Bereishit_Rabbah", "Genesis", 100),
        ("Midrash Shemot Rabbah", "Shemot_Rabbah", "Exodus", 52),
    ]
    for label, slug, tgt, chs in extra_works:
        try:
            rows = ingest_flat_work(label, slug, tgt, chs)
            conn.executemany(
                """
                INSERT OR REPLACE INTO commentaries
                (commentator, target_book, chapter, verse, comment_idx, ref, target_ref, en_text, he_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            total_comm += len(rows)
            print(f"  [Midrash/Mishnah] {label:26s}: {len(rows):5d} entries")
        except Exception as e:
            print(f"  [WARN] {label}: {e}")
    conn.commit()

    print("4/4 Ingesting curated Storyteller, History & PaRDeS Knowledge Dossiers...")
    doc_cnt = ingest_knowledge_docs(conn)
    rebuild_fts(conn)

    conn.executemany(
        "INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)",
        [
            ("built_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            ("verses_count", str(total_verses)),
            ("commentaries_count", str(total_comm)),
            ("documents_count", str(doc_cnt)),
            ("parashiyot_count", str(len(PARASHIYOT))),
            ("source", "Sefaria Open Texts + Torah Sanctuary Curated Library"),
        ],
    )
    conn.commit()
    conn.close()
    print(f"ALL DONE in {time.time() - t0:.1f}s -> {DB_PATH} ({DB_PATH.stat().st_size / (1024*1024):.1f} MB)")


if __name__ == "__main__":
    main()
