#!/usr/bin/env python3
"""
Torah Sanctuary OS — Pure-Stdlib Automated Test Suite.

Run offline repo checks anywhere:
    python3 -m unittest discover -s tests -v

Include live HTTP endpoint checks against a running Sanctuary node:
    TORAH_TEST_URL=http://127.0.0.1:8080 python3 -m unittest discover -s tests -v
"""

import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ai_engine
import broadcast_hub
import community_hub
import sacred_astronomy as sa
import sacred_liturgy
import sanctuary_rich_data as srd
import shul_events
import torah_db


class TestSacredAstronomy(unittest.TestCase):
    def test_hebrew_calendar_benchmarks(self):
        # Verified exact Dershowitz-Reingold Gregorian -> Hebrew mappings
        cases = [
            (datetime.date(2025, 10, 2), (5786, 7, 10)),   # Yom Kippur 5786
            (datetime.date(2026, 4, 2), (5786, 1, 15)),    # Pesach I 5786
            (datetime.date(2026, 9, 12), (5787, 7, 1)),    # Rosh Hashanah 5787
            (datetime.date(2026, 11, 21), (5787, 9, 11)),  # 11 Kislev 5787
            (datetime.date(2026, 11, 22), (5787, 9, 12)),  # 12 Kislev 5787
            (datetime.date(2026, 12, 5), (5787, 9, 25)),   # Chanukah I 5787
            (datetime.date(2027, 3, 23), (5787, 13, 14)),  # Purim (Adar II) 5787 leap year
        ]
        for gdate, expected in cases:
            hd = sa.gregorian_to_hebrew(gdate)
            self.assertEqual((hd["year"], hd["month"], hd["day"]), expected, f"Mismatch on {gdate}")

    def test_brussels_zmanim_and_astronomy(self):
        snap = sa.get_sacred_moment()
        self.assertIn("hebrew_date", snap)
        self.assertIn("sun", snap)
        self.assertIn("moon", snap)
        self.assertTrue(0.0 <= snap["moon"]["illumination_pct"] <= 100.0)
        # Mizrach Jerusalem bearing from Brussels ~118 deg ESE
        if "Brussels" in snap["location"]["city"]:
            self.assertTrue(115.0 <= snap["mizrach"]["bearing_deg"] <= 122.0)

        zmap = {z["key"]: z["time"] for z in snap["zmanim"]}
        for req_k in ("alot", "sunrise", "shema_gra", "chatzot", "plag_hamincha", "candle_lighting", "sunset", "tzeit"):
            self.assertTrue(zmap.get(req_k), f"Missing zman {req_k}")
        # Strict chronological ordering for daytime Zmanim
        ordered = ["alot", "sunrise", "shema_gra", "chatzot", "plag_hamincha", "candle_lighting", "sunset", "tzeit"]
        times = [zmap[k] for k in ordered]
        self.assertEqual(times, sorted(times), f"Zmanim out of order: {list(zip(ordered, times))}")

    def test_milestones_and_city_presets(self):
        self.assertGreaterEqual(len(sa.CITY_PRESETS), 9)
        snap = sa.get_sacred_moment()
        ms = snap["year_context"]["milestones"]
        self.assertIn("next_rosh_chodesh", ms)
        self.assertGreaterEqual(len(ms["upcoming_holidays"]), 4)
        self.assertIn(len(ms["wheel_months"]), (12, 13))


class TestRichVisualAtlas(unittest.TestCase):
    def test_all_art_assets_exist(self):
        art_dir = ROOT / "static" / "art"
        jpgs = list(art_dir.glob("*.jpg"))
        self.assertGreaterEqual(len(jpgs), 16)
        combined = (ROOT / "sanctuary_rich_data.py").read_text(encoding="utf-8") + (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        refs = set(re.findall(r"/art/([a-z0-9\-]+\.jpg)", combined))
        missing = [r for r in sorted(refs) if not (art_dir / r).exists()]
        self.assertEqual(missing, [], f"Missing referenced art files: {missing}")

    def test_atlas_completeness(self):
        self.assertGreaterEqual(len(srd.list_symbols()), 12)
        self.assertGreaterEqual(len(srd.list_characters()), 12)
        self.assertGreaterEqual(len(srd.list_timeline()), 10)
        self.assertGreaterEqual(len(srd.list_quizzes()), 35)
        self.assertGreaterEqual(len(srd.CHARACTER_SCENES), 15)
        self.assertGreaterEqual(len(srd.HEBREW_WORDS), 10)
        self.assertGreaterEqual(len([k for k in srd.STORY_ANATOMY if k != "default"]), 14)

        for q in srd.list_quizzes():
            self.assertTrue(0 <= q["correct_idx"] < len(q["options"]), f"Bad correct_idx in {q['id']}")
            self.assertTrue(q.get("reveal_fact"), f"Missing reveal_fact in {q['id']}")

        for era in srd.list_timeline():
            self.assertIn(era["story_slug"], srd.STORY_ENRICHMENT, f"Unknown timeline story {era['story_slug']}")

    def test_verse_cast_detection(self):
        cast = srd.detect_verse_cast("Jacob sent angels ahead to meet Esau while Rachel watched")
        labels = [c["label"] for c in cast]
        self.assertGreaterEqual(len(labels), 3)


class TestBroadcastHub(unittest.TestCase):
    def test_omarchy_shul_mesh(self):
        import shul_mesh
        caps = shul_mesh.detect_omarchy_capabilities(force=True)
        self.assertIn("hostname", caps)
        self.assertIn("tailscale", caps)
        beacon = shul_mesh.build_beacon()
        self.assertTrue(beacon.get("ok"))
        self.assertTrue(beacon.get("protocol", "").startswith("torah-sanctuary"))
        jp = shul_mesh.build_join_pack()
        self.assertIn("/watch", jp.get("watch_url", ""))
        self.assertIn("broadcast_follow_url", jp.get("join_command", ""))

    def test_broadcast_lifecycle(self):
        st0 = broadcast_hub.get_state(include_deck=False)
        self.assertIn("active", st0)
        st1 = broadcast_hub.start_broadcast(deck_kind="character", deck_slug="moses", slide_idx=0, public_tunnel=False)
        try:
            self.assertTrue(st1["active"])
            self.assertEqual(st1["slide_idx"], 0)
            st2 = broadcast_hub.sync_broadcast(slide_idx=2)
            self.assertEqual(st2["slide_idx"], 2)
        finally:
            st3 = broadcast_hub.stop_broadcast()
            self.assertFalse(st3["active"])

    def test_qr_svg_generation(self):
        svg = broadcast_hub.generate_qr_svg("https://theshul.eu/watch")
        self.assertTrue(b"<svg" in svg.lower())


class TestFrontendAndConfig(unittest.TestCase):
    def test_config_example_matches_defaults(self):
        cfg = json.loads((ROOT / "config.example.json").read_text(encoding="utf-8"))
        for k in ("synagogue_name", "ollama_model", "max_sanctuary_volume", "os_color_temp_sync", "broadcast_follow_url"):
            self.assertIn(k, cfg)
            self.assertIn(k, ai_engine.DEFAULT_CONFIG)

    def test_html_js_syntax_with_node(self):
        if not shutil.which("node"):
            self.skipTest("node not installed")
        for fname in ("static/index.html", "static/watch.html", "static/give.html"):
            html = (ROOT / fname).read_text(encoding="utf-8")
            scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.S)
            self.assertTrue(scripts, f"No script blocks in {fname}")
            for i, sc in enumerate(scripts):
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as tf:
                    tf.write(sc)
                    tmp = tf.name
                try:
                    res = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
                    self.assertEqual(res.returncode, 0, f"JS syntax error in {fname} script #{i}:\n{res.stderr}")
                finally:
                    pathlib.Path(tmp).unlink(missing_ok=True)


@unittest.skipUnless(torah_db.DB_PATH.exists(), "Local torah.db not present in this checkout")
class TestDatabaseAndRAG(unittest.TestCase):
    def test_corpus_integrity(self):
        st = torah_db.get_stats()
        self.assertEqual(st["books"], 39)
        self.assertGreaterEqual(st["verses"], 23000)
        self.assertGreaterEqual(st["commentaries"], 21000)
        self.assertEqual(st["parashiyot"], 54)

    def test_rag_diversity_and_word_boundaries(self):
        ctx, src = ai_engine.build_rag_context("What does Or HaChaim say about Exodus 1:1?", mode="scholar", compact=True)
        comms = [c["commentator"] for c in src["commentaries"]]
        self.assertGreaterEqual(len(set(comms)), 3, f"Expected >=3 distinct commentators, got {comms}")
        self.assertLessEqual(len(ctx), 2500)

        # Ensure 'book' never falsely triggers Parashat Bo
        _ctx_j, src_j = ai_engine.build_rag_context("Tell me about the Book of Jonah", mode="all", compact=True)
        self.assertNotIn("Bo", [p["en_name"] for p in src_j["parashiyot"]])

    def test_weekly_shul_mailing(self):
        m = shul_events.generate_weekly_mailing()
        for needle in (
            "Halachic Zmanim",
            "Next Rosh Chodesh",
            "Applying It in Today",
            "Hebrew Word &amp; Root of the Week",
            "Shabbat Table Riddle of the Week",
        ):
            self.assertIn(needle, m["html"])

    def test_liturgy_psalms_tefillin_meals_songs_and_holidays(self):
        lit = sacred_liturgy.get_today_liturgy()
        self.assertGreaterEqual(len(lit["shir_shel_yom"]["verses"]), 5)
        self.assertGreaterEqual(len(lit["monthly_tehillim"]["psalms"]), 1)
        self.assertGreaterEqual(len(lit["tefillin"]["steps"]), 7)
        self.assertGreaterEqual(len(lit["before_meal_blessings"]), 7)
        self.assertGreaterEqual(len(lit["after_meal_blessings"]["birkat_hamazon"]["sections"]), 6)
        self.assertGreaterEqual(len(lit["songs"]), 11)
        self.assertIn("say_with_me", lit["tefillin"])
        self.assertGreaterEqual(len(lit["tefillin"]["say_with_me"]), 5)
        self.assertIn("melody", lit["songs"][0])

    def test_scripture_foundation_and_studio_voice(self):
        import scripture_foundation
        import voice_engine
        f = scripture_foundation.get_foundation_dossier(parasha_slug="vayishlach")
        self.assertGreaterEqual(len(f["coinciding_scripture"]), 2)
        self.assertTrue(all(p["verified_from_db"] for p in f["coinciding_scripture"]))
        self.assertGreaterEqual(len(f["interpretations"]), 2)
        for it in f["interpretations"]:
            self.assertEqual(it["tier"], "CITED_INTERPRETATION")
            self.assertTrue(bool(it.get("counter_or_other_lens")))
        self.assertEqual(voice_engine.detect_language("שְׁמַע יִשְׂרָאֵל", "auto"), "he")
        self.assertEqual(voice_engine.detect_language("In the beginning", "auto"), "en")
        self.assertIn("אֲדֹנָי", voice_engine.clean_for_speech("בָּרוּךְ אַתָּה ה׳", lang="he"))

        import sacred_books
        lib = sacred_books.get_books_library()
        self.assertGreaterEqual(len(lib["haggadah"]["steps"]), 14)
        self.assertGreaterEqual(len(lib["siddur_blessings"]), 10)
        self.assertEqual(len(lib["five_megillot"]), 5)
        self.assertGreaterEqual(sacred_books.index_into_db(), 3)

        ps23 = sacred_liturgy.get_psalm_chapter(23)
        self.assertEqual(ps23["chapter"], 23)
        self.assertEqual(ps23["verses_count"], 6)

        hols = sacred_liturgy.get_holidays_encyclopedia()
        self.assertGreaterEqual(len(hols["holidays"]), 11)
        art_dir = ROOT / "static" / "art"
        for h in hols["holidays"]:
            self.assertGreaterEqual(len(h["prominent_celebrations"]), 2, f"Missing prominent stories in {h['slug']}")
            self.assertTrue((art_dir / h["art"].replace("/art/", "")).exists(), f"Missing holiday art {h['art']}")

    def test_community_syndication_and_sponsorships(self):
        items = community_hub.list_sponsorship_items()
        self.assertGreaterEqual(len(items), 7)
        rss = community_hub.build_rss_xml("127.0.0.1:8080")
        self.assertIn("<rss version=\"2.0\"", rss)
        self.assertIn("<item>", rss)
        emb = community_hub.build_embed_js("127.0.0.1:8080")
        self.assertIn("document.createElement('div')", emb)
        pack = community_hub.build_syndication_pack("127.0.0.1:8080")
        for ch in ("rss", "website", "email", "whatsapp", "sms", "eventbrite", "pr"):
            self.assertIn(ch, pack["channels"], f"Missing syndication channel {ch}")


LIVE_URL = os.environ.get("TORAH_TEST_URL", "").rstrip("/")


@unittest.skipUnless(bool(LIVE_URL), "Set TORAH_TEST_URL=http://127.0.0.1:8080 to run live HTTP tests")
class TestLiveHTTP(unittest.TestCase):
    def test_all_core_endpoints_200(self):
        endpoints = [
            "/",
            "/watch",
            "/give",
            "/feed.xml",
            "/embed.js",
            "/api/give/qr.svg",
            "/api/give/items",
            "/api/connect/messages",
            "/api/syndication/pack",
            "/api/today",
            "/api/today?date=2026-11-15",
            "/api/celestial",
            "/api/characters",
            "/api/symbols",
            "/api/timeline",
            "/api/quizzes",
            "/api/liturgy/today",
            "/api/liturgy/psalm?chapter=24",
            "/api/holidays",
            "/api/foundation?parasha=vayishlach",
            "/api/books/library",
            "/api/admin/export-bundle",
            "/api/shul/events",
            "/api/shul/mailing",
            "/api/scribe/status",
            "/api/broadcast/state",
            "/api/mesh/overview",
            "/api/mesh/beacon",
            "/api/mesh/incoming",
            "/api/mesh/join-qr.svg",
            "/art/esther-shushan.jpg",
            "/art/elijah-horeb.jpg",
            "/art/solomon-temple.jpg",
            "/art/promised-land.jpg",
        ]
        for ep in endpoints:
            with urllib.request.urlopen(LIVE_URL + ep, timeout=10) as r:
                body = r.read()
                self.assertEqual(r.status, 200, f"{ep} returned {r.status}")
                self.assertGreater(len(body), 20, f"{ep} returned empty body")


if __name__ == "__main__":
    unittest.main()
