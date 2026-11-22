#!/usr/bin/env python3
"""Torah Sanctuary / ShulOS — Verified Scripture Foundation & Multi-Lens Interpretation Registry.

Enforces SOURCE_STANDARD.md:
  - Tier 1 (PRIMARY_SCRIPTURE): Every cross-scripture reference is hydrated VERBATIM
    directly from the local verified SQLite Tanakh corpus (`torah.db`, 39 books, 23,206 verses).
  - Tier 2 (CITED_INTERPRETATION): Babylonian Talmud (Bavli) tractate & folio citations and
    classical commentaries are ALWAYS explicitly framed as interpretations alongside differing
    lenses (Peshat / plain text, rationalist, thematic, Midrashic) — never presented as dogma.
  - Tier 3 (CONTEXT_REFLECTION): Historical/linguistic notes cleanly separated from Scripture.
"""

import torah_db

SOURCE_STANDARD_SUMMARY = {
    "version": "1.0",
    "tiers": [
        {
            "id": "PRIMARY_SCRIPTURE",
            "badge": "📜 Primary Verified Scripture",
            "rule": "Verbatim Hebrew & English verses directly from local verified source files (Tanakh — Torah, Nevi'im, Ketuvim).",
        },
        {
            "id": "CITED_INTERPRETATION",
            "badge": "⚖️ Cited Interpretation (Non-Exclusive)",
            "rule": "Talmudic (Babylonian Bavli & Jerusalem Yerushalmi) and classical rabbinic sources cited by tractate/folio or author and explicitly treated as interpretations alongside differing perspectives.",
        },
        {
            "id": "CONTEXT_REFLECTION",
            "badge": "🧭 Context & Reflection",
            "rule": "Historical, archaeological, linguistic, and practical reflections clearly distinguished from verbatim Scripture.",
        },
    ],
}

# Curated verified Cross-Scripture Parallels & Multi-Lens Talmudic / Classical Interpretations
# Every verse tuple (book, chapter, verse, relation) is hydrated verbatim from torah.db!
FOUNDATION_ENTRIES = {
    "vayishlach": {
        "topic": "Parashat Vayishlach · Jacob's Struggle, Reunion & Renewal",
        "primary_anchor": ("Genesis", 32, 25, 29),
        "coinciding_scripture": [
            ("Hosea", 12, 4, "Prophet Hosea explicitly references Jacob wrestling the angel and weeping for a blessing."),
            ("Hosea", 12, 5, "Coinciding prophetic confirmation that Jacob prevailed through prayer and supplication."),
            ("Obadiah", 1, 1, "Traditional Haftarah — prophetic oracle regarding Edom (descendants of Esau)."),
            ("Psalms", 91, 11, "Scriptural parallel on divine guardianship through angelic messengers."),
        ],
        "interpretations": [
            {
                "source": "Talmud Bavli, Chullin 91a–92a",
                "tier": "CITED_INTERPRETATION",
                "lens": "Talmudic Aggadah (One Classical View)",
                "position": "Identifies Jacob's nocturnal adversary as the spiritual guardian angel (Sar) of Esau, wrestling until dawn over the spiritual destiny of Israel, and links the sciatic nerve (gid hanasheh) prohibition to this encounter.",
                "counter_or_other_lens": "Contrast with Rashbam & Ibn Ezra (Peshat): read the text more directly as a real mysterious messenger sent to test Jacob's resolve against fleeing from Esau, rather than necessarily Esau's metaphysical guardian.",
            },
            {
                "source": "Rambam (Maimonides, Guide for the Perplexed II:42)",
                "tier": "CITED_INTERPRETATION",
                "lens": "Rationalist / Prophetic Vision Lens",
                "position": "Interprets the wrestling encounter as a profound prophetic vision experienced by Jacob at night rather than a physical brawl with a corporeal being.",
                "counter_or_other_lens": "Contrast with Ramban (Genesis 32:25): insists the limp in Jacob's hip (v. 32) proves the encounter had a tangible physical dimension, not solely a dream.",
            },
            {
                "source": "Rashi (citing Genesis Rabbah 78:9) vs. Ibn Ezra (Genesis 33:4)",
                "tier": "CITED_INTERPRETATION",
                "lens": "Esau's Kiss — Debate Between Sages",
                "position": "Rashi cites a Midrashic tradition noting the dots over 'and he kissed him' (Genesis 33:4) as questioning Esau's sincerity, yet also records Rabbi Yannai's dissenting view that Esau kissed Jacob with genuine wholehearted compassion.",
                "counter_or_other_lens": "Ibn Ezra & Netziv take the plain wording seriously: Jacob's humility genuinely softened Esau's heart, proving that brotherhood can heal even after 20 years of estrangement.",
            },
            {
                "source": "Talmud Yerushalmi, Berakhot 9:1 & Nedarim 9:4 (Jerusalem Talmud)",
                "tier": "CITED_INTERPRETATION",
                "lens": "Land of Israel Talmudic Parallel (Yerushalmi)",
                "position": "The Jerusalem Talmud (compiled earlier in Tiberias, c. 350–400 CE) emphasizes direct whispered intimacy in prayer (Berakhot 9:1) and Rabbi Akiva's call to 'Love your neighbor as yourself' alongside Ben Azzai's universal dignity of every human being (Nedarim 9:4).",
                "counter_or_other_lens": "Paired alongside the Babylonian Talmud (Bavli, c. 500 CE) to give learners BOTH great Talmudic traditions rather than a single lens.",
            },
        ],
    },
    "bereshit": {
        "topic": "Parashat Bereshit · Creation, Light & Human Dignity",
        "primary_anchor": ("Genesis", 1, 1, 5),
        "coinciding_scripture": [
            ("Psalms", 33, 6, "Ketuvim parallel affirming creation through the Divine word."),
            ("Isaiah", 45, 7, "Prophetic parallel on forming light and creating peace."),
            ("Psalms", 104, 24, "Hymn of creation marveling at wisdom throughout nature."),
        ],
        "interpretations": [
            {
                "source": "Talmud Bavli, Chagigah 12a",
                "tier": "CITED_INTERPRETATION",
                "lens": "Talmudic Aggadah (One Classical View)",
                "position": "Describes the primordial light of Day 1 as a spiritual radiance by which one could see from one end of the world to the other, hidden away for the righteous in the future.",
                "counter_or_other_lens": "Contrast with Ibn Ezra & Sforno (Peshat): understand the light of Day 1 as physical cosmic light before the atmospheric clearing of sun, moon, and stars on Day 4.",
            },
            {
                "source": "Talmud Bavli, Sanhedrin 37a",
                "tier": "CITED_INTERPRETATION",
                "lens": "Ethical Talmudic Interpretation",
                "position": "Explains why humanity began from a single individual (Adam): to teach that saving one single life is like saving an entire world, and so no person can claim superior ancestry over another.",
                "counter_or_other_lens": "Ramban (Genesis 1:26) adds a distinct theological lens on 'image of God' (Tzelem Elokim) as combining earthly body with spiritual free will.",
            },
        ],
    },
    "tefillin": {
        "topic": "Tefillin & Shema · Binding Torah to Mind & Heart",
        "primary_anchor": ("Deuteronomy", 6, 4, 9),
        "coinciding_scripture": [
            ("Exodus", 13, 9, "Torah parallel: 'It shall be for you as a sign on your hand and a reminder between your eyes.'"),
            ("Exodus", 13, 16, "Second Exodus passage inscribed inside the Tefillin parchments."),
            ("Deuteronomy", 11, 18, "Parallel command to place these words upon heart and soul, binding them on hand and forehead."),
            ("Hosea", 2, 21, "Prophetic verse recited while wrapping the strap around the fingers: 'I will betroth you to Me forever.'"),
            ("Hosea", 2, 22, "Continuation of the covenant betrothal in faithfulness and knowledge of God."),
        ],
        "interpretations": [
            {
                "source": "Talmud Bavli, Menachot 35b–37b & Berakhot 6a",
                "tier": "CITED_INTERPRETATION",
                "lens": "Talmudic Halachah & Aggadah",
                "position": "Details the black leather boxes, four parchment passages, and arm/head placement received in Oral Tradition; Berakhot 6a poetically pictures God metaphorically wearing Tefillin praising Israel's devotion.",
                "counter_or_other_lens": "Contrast with Rashbam (Exodus 13:9): while fully observing physical Tefillin in practice, notes that at the purely literal poetic level (Peshat) 'sign on your hand' also functions as an idiom for constant remembrance (comparable to Song of Songs 8:6, 'Set me as a seal upon your heart').",
            },
            {
                "source": "Sefer HaChinuch (#421–422) vs. Kabbalistic / Chassidic Lens",
                "tier": "CITED_INTERPRETATION",
                "lens": "Educational Psychology vs. Mystical Alignment",
                "position": "Sefer HaChinuch frames Tefillin pragmatically: binding the arm (action) opposite the heart (emotion) and head (intellect) trains our daily habits toward integrity.",
                "counter_or_other_lens": "Mystical interpretations emphasize uniting higher spiritual intellect (Mochin) with emotional attributes (Middot) — a complementary devotional lens, not exclusive of the plain ethical meaning.",
            },
        ],
    },
    "shabbat": {
        "topic": "Shabbat · Sacred Rest, Creation & Liberation",
        "primary_anchor": ("Exodus", 20, 8, 11),
        "coinciding_scripture": [
            ("Genesis", 2, 2, "Creation anchor: God completed creation and rested on the seventh day."),
            ("Deuteronomy", 5, 12, "Second Decalogue parallel emphasizing 'Guard' (Shamor) and liberation from Egyptian slavery."),
            ("Isaiah", 58, 13, "Prophetic call to treat Shabbat as a delight (Oneg Shabbat)."),
            ("Psalms", 92, 1, "Mizmor Shir L'Yom HaShabbat — the dedicated Psalm for the Sabbath day."),
        ],
        "interpretations": [
            {
                "source": "Talmud Bavli, Shabbat 118a–119b & Rosh Hashanah 27a",
                "tier": "CITED_INTERPRETATION",
                "lens": "Talmudic Synthesis of Exodus & Deuteronomy",
                "position": "Harmonizes Exodus 20:8 ('Remember / Zachor') and Deuteronomy 5:12 ('Guard / Shamor') as twin dimensions of Shabbat—positive celebration and restful restraint—and celebrates Shabbat as a foretaste of a peaceful world.",
                "counter_or_other_lens": "Ibn Ezra (Exodus 20:1) offers a strictly linguistic/literary explanation for the variation between Exodus and Deuteronomy without requiring a miraculous simultaneous utterance, demonstrating legitimate classical diversity.",
            },
        ],
    },
    "vayetzei": {
        "topic": "Parashat Vayetzei · Jacob's Ladder & Discovering Holiness Anywhere",
        "primary_anchor": ("Genesis", 28, 11, 17),
        "coinciding_scripture": [
            ("Psalms", 121, 1, "Shir LaMa'alot — lifting eyes to the hills for Divine help, traditionally linked to Jacob's journey."),
            ("Hosea", 12, 13, "Prophetic reference to Jacob fleeing to Aram and serving for a wife."),
        ],
        "interpretations": [
            {
                "source": "Talmud Bavli, Chullin 91b & Genesis Rabbah 68",
                "tier": "CITED_INTERPRETATION",
                "lens": "Talmudic Aggadah (One Classical View)",
                "position": "Pictures the angels ascending and descending as comparing Jacob's earthly face to his spiritual image, or as angels of the Land of Israel handing off escort to angels of the Diaspora.",
                "counter_or_other_lens": "Contrast with Rambam (Guide I:15) & Ibn Ezra: read the ladder as a symbol of human spiritual ascent—prayers and intellect rising from earth to heaven, and providence descending in response.",
            },
        ],
    },
    "shemot": {
        "topic": "Parashat Shemot · The Burning Bush & Sacred Calling",
        "primary_anchor": ("Exodus", 3, 2, 14),
        "coinciding_scripture": [
            ("Deuteronomy", 33, 16, "Moses' final blessing recalls 'the favor of Him who dwelt in the thornbush.'"),
            ("Psalms", 105, 26, "Ketuvim retelling of God sending Moses and Aaron to liberate Israel."),
        ],
        "interpretations": [
            {
                "source": "Talmud Bavli, Shabbat 67a & Exodus Rabbah 2:5",
                "tier": "CITED_INTERPRETATION",
                "lens": "Midrashic / Rabbinic Symbolism",
                "position": "Asks why God appeared in a humble thornbush rather than a towering cedar: to teach that God shares in the pain of the oppressed and no humble place is devoid of Divine presence.",
                "counter_or_other_lens": "Contrast with Ibn Ezra & Rashbam (Peshat): emphasize the direct wonder of an unconsumed fire as a clear sensory sign confirming Moses' mission to Pharaoh.",
            },
        ],
    },
    "yitro": {
        "topic": "Parashat Yitro · Revelation at Sinai & Shared Leadership",
        "primary_anchor": ("Exodus", 19, 18, 20),
        "coinciding_scripture": [
            ("Deuteronomy", 4, 12, "Moses' parallel testimony: 'You heard the sound of words, yet saw no form—only a voice.'"),
            ("Deuteronomy", 5, 6, "Parallel Ten Commandments text in Moses' farewell address."),
            ("Psalms", 29, 4, "Poetic echo of the Divine voice resounding in majesty."),
        ],
        "interpretations": [
            {
                "source": "Talmud Bavli, Shabbat 88a",
                "tier": "CITED_INTERPRETATION",
                "lens": "Talmudic Aggadah (Famous Debate)",
                "position": "Rabbi Avdimi offers the dramatic metaphor of Mount Sinai held over Israel like a barrel—yet the Talmud itself immediately raises an objection and resolves (through Esther 9:27) that true covenant commitment must be freely re-accepted out of love.",
                "counter_or_other_lens": "Plain text (Exodus 19:8 & 24:7, 'All that the Lord has spoken we will do and hear') presents Israel's voluntary joyful acceptance directly—showing how the Talmud's own debate preserves freedom of conscience.",
            },
        ],
    },
}


def _fetch_verified_verse(book: str, chapter: int, verse: int) -> dict | None:
    try:
        with torah_db.get_conn() as conn:
            row = conn.execute(
                """
                SELECT book_title AS book, he_book_title AS he_book, chapter, verse, he_text, en_text
                FROM verses
                WHERE (lower(book_title) = lower(?) OR lower(book_slug) = lower(?)) AND chapter = ? AND verse = ?
                LIMIT 1
                """,
                (book, book, int(chapter), int(verse)),
            ).fetchone()
            return dict(row) if row else None
    except Exception:
        return None


def _fetch_anchor_range(book: str, chapter: int, v_start: int, v_end: int) -> list[dict]:
    try:
        with torah_db.get_conn() as conn:
            rows = conn.execute(
                """
                SELECT book_title AS book, he_book_title AS he_book, chapter, verse, he_text, en_text
                FROM verses
                WHERE (lower(book_title) = lower(?) OR lower(book_slug) = lower(?)) AND chapter = ? AND verse BETWEEN ? AND ?
                ORDER BY verse ASC
                """,
                (book, book, int(chapter), int(v_start), int(v_end)),
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


def get_foundation_dossier(parasha_slug: str = "", topic: str = "") -> dict:
    """Return a 3-Tier Source-Standard dossier with verbatim verified parallels + multi-lens cited interpretations."""
    key = (topic or parasha_slug or "").strip().lower().replace(" ", "_").replace("-", "_")
    # Smart alias matching
    if key not in FOUNDATION_ENTRIES:
        q = f"{parasha_slug} {topic}".lower()
        for k in FOUNDATION_ENTRIES:
            if k in q:
                key = k
                break
        if key not in FOUNDATION_ENTRIES:
            if any(w in q for w in ("tefil", "shema", "phylact", "tallit", "prayer")):
                key = "tefillin"
            elif any(w in q for w in ("shabbat", "sabbath", "friday", "kiddush")):
                key = "shabbat"
            elif any(w in q for w in ("sinai", "commandment", "yitro", "jethro")):
                key = "yitro"
            elif any(w in q for w in ("bush", "moses", "exodus", "shemot")):
                key = "shemot"
            elif any(w in q for w in ("ladder", "vayetzei", "vayeitzei")):
                key = "vayetzei"
            elif any(w in q for w in ("creation", "adam", "bereshit", "bereishit")):
                key = "bereshit"
            else:
                key = "vayishlach"

    entry = FOUNDATION_ENTRIES[key]
    a_book, a_ch, a_vs, a_ve = entry["primary_anchor"]
    anchor_verses = _fetch_anchor_range(a_book, a_ch, a_vs, a_ve)

    parallels = []
    for p_book, p_ch, p_v, relation in entry["coinciding_scripture"]:
        v = _fetch_verified_verse(p_book, p_ch, p_v)
        if v:
            parallels.append({
                "tier": "PRIMARY_SCRIPTURE",
                "ref": f"{v['book']} {v['chapter']}:{v['verse']}",
                "he_book": v["he_book"],
                "he_text": v["he_text"],
                "en_text": v["en_text"],
                "relation": relation,
                "verified_from_db": True,
            })

    return {
        "key": key,
        "topic": entry["topic"],
        "standard": SOURCE_STANDARD_SUMMARY,
        "primary_anchor_ref": f"{a_book} {a_ch}:{a_vs}-{a_ve}",
        "primary_anchor_verses": anchor_verses,
        "coinciding_scripture": parallels,
        "interpretations": entry["interpretations"],
        "available_keys": list(FOUNDATION_ENTRIES.keys()),
    }


def format_for_ai_rag(query: str, parasha_slug: str = "") -> str:
    """Format verified coinciding scripture & multi-lens Talmudic citations for RAG injection."""
    dossier = get_foundation_dossier(parasha_slug=parasha_slug, topic=query)
    lines = [
        f"=== VERIFIED COINCIDING SCRIPTURE PARALLELS ({dossier['topic']}) ===",
    ]
    for p in dossier["coinciding_scripture"][:3]:
        lines.append(f"- [PRIMARY SCRIPTURE] {p['ref']}: \"{p['en_text']}\" ({p['relation']})")
    lines.append("=== CITED TALMUDIC & CLASSICAL INTERPRETATIONS (NON-EXCLUSIVE — PRESENT AS INTERPRETATIONS) ===")
    for it in dossier["interpretations"][:3]:
        lines.append(
            f"- [{it['source']} | {it['lens']}]: {it['position']} "
            f"|| Differing view: {it['counter_or_other_lens']}"
        )
    return "\n".join(lines)
