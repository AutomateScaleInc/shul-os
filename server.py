#!/usr/bin/env python3
"""
Torah Sanctuary — Standalone Synagogue Kiosk & Study Web Server (Port 8080).
Pure Python standard library + SQLite FTS5 + Hybrid Ollama/Cloud streaming SSE.
"""

import http.server
import json
import os
import pathlib
import socketserver
import subprocess
import tempfile
import urllib.parse
import urllib.request

import ai_engine
import broadcast_hub
import community_hub
import sacred_astronomy
import sacred_liturgy
import sanctuary_rich_data
import shul_events
import torah_db
import torah_scribe
import voice_engine

BASE_DIR = pathlib.Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
PORT = int(os.environ.get("TORAH_PORT", "8080"))
HOST = os.environ.get("TORAH_HOST", "0.0.0.0")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class TorahHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _send_json(self, obj, status: int = 200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(min(length, 262144))
            return json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/api/shul/events":
            try:
                eid = int(qs.get("id", ["0"])[0])
                ok = shul_events.delete_event(eid)
                self._send_json({"ok": ok})
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
            return
        if parsed.path == "/api/give/items":
            try:
                iid = int(qs.get("id", ["0"])[0])
                ok = community_hub.delete_sponsorship_item(iid)
                self._send_json({"ok": ok})
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
            return
        self.send_error(404, "Not Found")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            index_p = STATIC_DIR / "index.html"
            if not index_p.exists():
                self.send_error(404, "UI not found")
                return
            body = index_p.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path in ("/watch", "/watch/"):
            wp = STATIC_DIR / "watch.html"
            if not wp.exists():
                self.send_error(404, "Watch view not found")
                return
            body = wp.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path in ("/give", "/give/", "/donate", "/sponsor"):
            gp = STATIC_DIR / "give.html"
            if not gp.exists():
                self.send_error(404, "Give page not found")
                return
            body = gp.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path in ("/feed.xml", "/rss.xml"):
            xml_bytes = community_hub.build_rss_xml(self.headers.get("Host", "")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(xml_bytes)))
            self.end_headers()
            self.wfile.write(xml_bytes)
            return

        if path == "/embed.js":
            js_bytes = community_hub.build_embed_js(self.headers.get("Host", "")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(js_bytes)))
            self.end_headers()
            self.wfile.write(js_bytes)
            return

        if path == "/api/give/qr.svg":
            target_url = qs.get("url", [""])[0] or community_hub.get_give_url(self.headers.get("Host", ""))
            svg_bytes = broadcast_hub.generate_qr_svg(target_url)
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(svg_bytes)))
            self.end_headers()
            self.wfile.write(svg_bytes)
            return

        if path == "/api/give/items":
            cfg = ai_engine.load_config()
            base_u = community_hub.get_public_base_url(self.headers.get("Host", ""))
            self._send_json({
                "synagogue_name": cfg.get("synagogue_name", shul_events.SHUL_INFO["name"]),
                "give_url": base_u + "/give",
                "watch_url": base_u + "/watch",
                "checkout_url": cfg.get("donation_checkout_url", shul_events.SHUL_INFO["website"]),
                "items": community_hub.list_sponsorship_items(),
            })
            return

        if path == "/api/give/pledges":
            self._send_json({"pledges": community_hub.list_pledges()})
            return

        if path == "/api/syndication/pack":
            self._send_json(community_hub.build_syndication_pack(self.headers.get("Host", "")))
            return

        if path == "/api/broadcast/state":
            self._send_json(broadcast_hub.get_state(include_deck=True))
            return

        if path == "/api/broadcast/qr.svg":
            svg_bytes = broadcast_hub.generate_qr_svg(qs.get("url", [""])[0])
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(svg_bytes)))
            self.end_headers()
            self.wfile.write(svg_bytes)
            return

        if path == "/api/broadcast/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            q = broadcast_hub.subscribe()
            try:
                while True:
                    try:
                        msg = q.get(timeout=15.0)
                        self.wfile.write(f"data: {msg}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except Exception:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except Exception:
                pass
            finally:
                broadcast_hub.unsubscribe(q)
            return

        if path.startswith("/art/"):
            fname = os.path.basename(path[5:])
            art_p = STATIC_DIR / "art" / fname
            if not art_p.is_file():
                self.send_error(404, "Art not found")
                return
            body = art_p.read_bytes()
            ctype = "image/png" if fname.endswith(".png") else "image/jpeg"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "public, max-age=86400")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/symbols":
            self._send_json({"symbols": sanctuary_rich_data.list_symbols()})
            return

        if path == "/api/characters":
            self._send_json({"characters": sanctuary_rich_data.list_characters()})
            return

        if path == "/api/timeline":
            self._send_json({"timeline": sanctuary_rich_data.list_timeline()})
            return

        if path == "/api/quizzes":
            self._send_json({"quizzes": sanctuary_rich_data.list_quizzes()})
            return

        if path == "/api/liturgy/today":
            self._send_json(sacred_liturgy.get_today_liturgy())
            return

        if path == "/api/liturgy/psalm":
            try:
                ch = int(qs.get("chapter", ["23"])[0])
            except ValueError:
                ch = 23
            self._send_json(sacred_liturgy.get_psalm_chapter(ch))
            return

        if path == "/api/holidays":
            self._send_json(sacred_liturgy.get_holidays_encyclopedia())
            return

        if path == "/api/presentation":
            kind = qs.get("kind", ["parasha"])[0].strip().lower()
            slug = qs.get("slug", [""])[0].strip()
            self._send_json(sanctuary_rich_data.build_presentation(kind=kind, slug=slug))
            return

        if path == "/api/health":
            cfg = ai_engine.load_config()
            self._send_json({
                "ok": True,
                "synagogue_name": cfg.get("synagogue_name", "Torah Sanctuary"),
                "stats": torah_db.get_stats(),
                "ollama": ai_engine.check_ollama_status(cfg),
                "voice": voice_engine.voice_status(),
                "voice_profile": cfg.get("voice_profile", "grand_narrator"),
                "cloud_configured": bool(cfg.get("cloud_provider") not in ("", "none") and cfg.get("cloud_api_key")),
                "cloud_provider": cfg.get("cloud_provider", "none"),
            })
            return

        if path == "/api/books":
            self._send_json({"books": torah_db.list_books()})
            return

        if path == "/api/chapter":
            book = qs.get("book", ["Genesis"])[0]
            try:
                ch = int(qs.get("chapter", ["1"])[0])
            except ValueError:
                ch = 1
            self._send_json(torah_db.get_chapter(book, ch))
            return

        if path == "/api/commentary":
            book = qs.get("book", ["Genesis"])[0]
            try:
                ch = int(qs.get("chapter", ["1"])[0])
                v = int(qs.get("verse", ["1"])[0])
            except ValueError:
                ch, v = 1, 1
            self._send_json({
                "ref": f"{book} {ch}:{v}",
                "commentaries": torah_db.get_verse_commentaries(book, ch, v),
            })
            return

        if path == "/api/search":
            q = qs.get("q", [""])[0]
            self._send_json(torah_db.search_all(q, limit_verses=12, limit_comm=10, limit_docs=6))
            return

        if path == "/api/today":
            day_param = qs.get("day", [None])[0]
            day_idx = None
            if day_param is not None and str(day_param).strip() != "":
                try:
                    day_idx = int(day_param)
                except ValueError:
                    day_idx = None
            daily = torah_db.get_daily_portion(day_idx)
            # Weave Brussels Shabbat times & The Shul (theshul.eu) / Rabbi Michoel events into the scrolling ticker
            try:
                shul_ann = shul_events.get_ticker_announcements()
                if shul_ann:
                    base_t = list(daily.get("ticker_items") or [])
                    merged = []
                    for i, item in enumerate(base_t):
                        merged.append(item)
                        if i in (0, 5, 11, 17) and shul_ann:
                            merged.append(shul_ann.pop(0))
                    merged.extend(shul_ann)
                    daily["ticker_items"] = merged
                daily["shabbat_times"] = shul_events.get_brussels_shabbat_and_holidays()
            except Exception:
                pass
            try:
                p_pres = sanctuary_rich_data.build_presentation("parasha", "")
                p_slides = p_pres.get("slides") or []
                chars_s = next((sl.get("characters", []) for sl in p_slides if sl.get("type") == "characters"), [])
                syms_s = next((sl.get("symbols", []) for sl in p_slides if sl.get("type") == "symbols"), [])
                today_s = next((sl.get("points", []) for sl in p_slides if sl.get("type") == "today"), [])
                daily["rich"] = {
                    "art": p_pres.get("art") or "/art/sacred-symbols.jpg",
                    "characters": [{"slug": c.get("slug", ""), "name": c.get("name", ""), "he_name": c.get("he_name", "")} for c in chars_s[:3]],
                    "symbols": [{"slug": s.get("slug", ""), "name": s.get("name", ""), "he_name": s.get("he_name", "")} for s in syms_s[:3]],
                    "today_points": today_s[:2],
                }
                p_obj = daily.get("parasha") or {}
                p_key = (p_obj.get("slug") or p_obj.get("en_name") or "").lower().replace(" ", "-")
                daily["show_extras"] = sanctuary_rich_data.get_handsfree_show_extras(p_key)
                # Weave Today's Temple Psalm (Shir Shel Yom) + Month Chronicle right into show_extras!
                try:
                    lit = sacred_liturgy.get_today_liturgy()
                    daily["show_extras"]["daily_psalm"] = {
                        "day_en": lit["shir_shel_yom"]["day_en"],
                        "chapter": lit["shir_shel_yom"]["chapter"],
                        "title": lit["shir_shel_yom"]["title"],
                        "temple_history": lit["shir_shel_yom"]["temple_history"],
                        "prominent_note": lit["shir_shel_yom"]["prominent_note"],
                        "monthly_label": lit["monthly_tehillim"]["label"],
                    }
                    daily["show_extras"]["month_chronicle"] = lit["month_chronicle"]
                except Exception:
                    pass
                # Tag each verse slide with cute cast/angel badges for the right-hand panel!
                for sl in (daily.get("slides") or []):
                    sl["cast_badges"] = sanctuary_rich_data.detect_verse_cast(sl.get("en_text", "") + " " + sl.get("commentary", ""))
            except Exception:
                pass
            try:
                cel = sacred_astronomy.get_sacred_moment()
                daily["celestial"] = {
                    "hebrew_date": cel["hebrew_date"],
                    "after_sunset": cel["after_sunset"],
                    "shabbat_mode": cel["shabbat_mode"],
                    "is_shabbat": cel["is_shabbat"],
                    "watch": cel["watch"],
                    "sun": cel["sun"],
                    "moon": cel["moon"],
                    "next_zman": cel["next_zman"],
                    "location": cel["location"],
                }
                # Weave live Celestial & Lunar sky note into scrolling ticker
                m = cel["moon"]
                nz = cel.get("next_zman") or {}
                cel_line = f"{m['emoji']} {cel['hebrew_date']['en_str']} ({cel['hebrew_date']['he_str']}) · Moon {m['illumination_pct']}% {m['phase_en']} (Alt {m['altitude_deg']:+.0f}° {m['compass']}, Rise {m['moonrise']})"
                if nz:
                    cel_line += f" · Next Zman: {nz['name']} {nz['time']} (in {nz['countdown']})"
                t_items = list(daily.get("ticker_items") or [])
                t_items.insert(min(2, len(t_items)), cel_line)
                daily["ticker_items"] = t_items
            except Exception:
                pass
            self._send_json(daily)
            return

        if path == "/api/celestial":
            cfg = ai_engine.load_config()
            snap = sacred_astronomy.get_sacred_moment()
            snap["city_presets"] = sacred_astronomy.CITY_PRESETS
            snap["os_color_temp_sync"] = cfg.get("os_color_temp_sync", True)
            # Attach real verbatim Daily Pirkei Avot Wisdom from local SQLite corpus!
            try:
                with torah_db.get_conn() as conn:
                    avot = conn.execute("SELECT ref, en_text, he_text FROM commentaries WHERE commentator = 'Pirkei Avot' ORDER BY id").fetchall()
                if avot:
                    doy = int(snap["timestamp_iso"][8:10]) + int(snap["timestamp_iso"][5:7]) * 31
                    pick = dict(avot[doy % len(avot)])
                    snap["daily_pirkei_avot"] = pick
            except Exception:
                pass
            self._send_json(snap)
            return

        if path == "/api/scribe/status":
            self._send_json(torah_scribe.get_scribe_status())
            return

        if path == "/api/shul/events":
            force_ics = qs.get("refresh", ["0"])[0] == "1"
            self._send_json(shul_events.list_events(force_ics=force_ics))
            return

        if path == "/api/shul/mailing":
            self._send_json(shul_events.generate_weekly_mailing())
            return

        if path == "/api/shul/subscribers":
            self._send_json({"subscribers": shul_events.list_subscribers()})
            return

        if path == "/api/shul/subscribers.csv":
            csv_bytes = shul_events.export_subscribers_csv().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="theshul-mailing-subscribers.csv"')
            self.send_header("Content-Length", str(len(csv_bytes)))
            self.end_headers()
            self.wfile.write(csv_bytes)
            return

        if path == "/api/parasha":
            slug = qs.get("slug", [""])[0].strip()
            if slug:
                all_p = torah_db.list_parashiyot()
                match = next((p for p in all_p if p["slug"] == slug or p["en_name"].lower() == slug.lower()), None)
                if match:
                    match["verses_preview"] = torah_db.get_parasha_verses(match, max_verses=60)
                    self._send_json({"current": match, "all": all_p})
                    return
            self._send_json({
                "current": torah_db.get_weekly_parasha(),
                "all": torah_db.list_parashiyot(),
            })
            return

        if path == "/api/documents":
            cat = qs.get("category", [None])[0]
            docs = torah_db.list_documents(cat)
            for d in docs:
                if d.get("category") == "story":
                    d["enrichment"] = sanctuary_rich_data.get_story_enrichment(d["slug"])
            self._send_json({"documents": docs})
            return

        if path == "/api/document":
            slug = qs.get("slug", [""])[0]
            doc = torah_db.get_document(slug)
            if not doc:
                self._send_json({"error": "Not found"}, status=404)
                return
            if doc.get("category") == "story":
                doc["enrichment"] = sanctuary_rich_data.get_story_enrichment(doc["slug"])
            self._send_json({"document": doc})
            return

        if path == "/api/config":
            cfg = ai_engine.load_config()
            safe = dict(cfg)
            key = safe.get("cloud_api_key", "")
            safe["cloud_api_key_set"] = bool(key)
            safe["cloud_api_key"] = (key[:6] + "..." + key[-4:]) if len(key) > 12 else ("***" if key else "")
            self._send_json({"config": safe})
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/shul/events":
            body = self._read_json_body()
            try:
                ev = shul_events.add_event(body)
                self._send_json({"ok": True, "event": ev})
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
            return

        if path == "/api/shul/subscribe":
            body = self._read_json_body()
            try:
                res = shul_events.add_subscriber(body.get("name", ""), body.get("email", ""), body.get("interests", ""))
                self._send_json(res)
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
            return

        if path == "/api/give/items":
            body = self._read_json_body()
            try:
                it = community_hub.add_sponsorship_item(body)
                self._send_json({"ok": True, "item": it})
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
            return

        if path == "/api/give/pledge":
            body = self._read_json_body()
            try:
                res = community_hub.record_pledge(body)
                self._send_json(res)
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
            return

        if path == "/api/syndication/transmit":
            body = self._read_json_body()
            res = community_hub.transmit_all_channels(
                channels=body.get("channels"),
                request_host=self.headers.get("Host", ""),
            )
            self._send_json(res)
            return

        if path == "/api/shul/mailing/push":
            cfg = ai_engine.load_config()
            hook = (cfg.get("mailing_webhook_url") or "").strip()
            if not hook:
                self._send_json({"error": "No Mailing Webhook URL configured in Library & Settings yet."}, status=400)
                return
            mailing = shul_events.generate_weekly_mailing()
            try:
                req = urllib.request.Request(
                    hook,
                    data=json.dumps({"type": "weekly_shul_mailing", **mailing}).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "TorahSanctuary/1.0"},
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    status_code = r.status
                self._send_json({"ok": True, "webhook_status": status_code, "subject": mailing["subject"]})
            except Exception as e:
                self._send_json({"error": f"Webhook push failed: {e}"}, status=502)
            return

        if path == "/api/broadcast/start":
            body = self._read_json_body()
            st = broadcast_hub.start_broadcast(
                deck_kind=(body.get("kind") or "parasha").strip(),
                deck_slug=(body.get("slug") or "").strip(),
                slide_idx=int(body.get("slide_idx") or 0),
                public_tunnel=bool(body.get("public_tunnel", True)),
                port=PORT,
            )
            self._send_json({"ok": True, "broadcast": st})
            return

        if path == "/api/broadcast/sync":
            body = self._read_json_body()
            st = broadcast_hub.sync_broadcast(
                deck_kind=body.get("kind"),
                deck_slug=body.get("slug"),
                slide_idx=body.get("slide_idx"),
            )
            self._send_json({"ok": True, "broadcast": st})
            return

        if path == "/api/broadcast/stop":
            st = broadcast_hub.stop_broadcast()
            self._send_json({"ok": True, "broadcast": st})
            return

        if path == "/api/scribe/run":
            body = self._read_json_body()
            mission = (body.get("mission") or "").strip()
            cmd = ["python3", str(BASE_DIR / "torah_scribe.py"), "--force"]
            if mission and mission in ("ingest_commentary", "enrich_parasha", "enrich_tanakh_book"):
                cmd.append(f"--mission={mission}")
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._send_json({"ok": True, "started": True, "mission": mission or "auto"})
            return

        if path == "/api/config":
            body = self._read_json_body()
            # Keep existing API key if masked or empty placeholder passed
            if "cloud_api_key" in body and ("..." in str(body["cloud_api_key"]) or body["cloud_api_key"] == "***"):
                body.pop("cloud_api_key", None)
            cfg = ai_engine.save_config(body)
            # Trigger OS celestial rhythm sync cleanly in background
            try:
                daemon_py = BASE_DIR / "sacred-os-daemon.py"
                if daemon_py.exists():
                    subprocess.Popen(["python3", str(daemon_py), "--quiet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            self._send_json({"ok": True, "synagogue_name": cfg.get("synagogue_name"), "cloud_provider": cfg.get("cloud_provider")})
            return

        if path == "/api/ask":
            body = self._read_json_body()
            q = (body.get("question") or "").strip()
            mode = (body.get("mode") or "all").strip().lower()
            history = body.get("history") or []
            if not q:
                self._send_json({"error": "Empty question"}, status=400)
                return
            self._send_json(ai_engine.ask_sync(q, mode=mode, history=history))
            return

        if path == "/api/ask/stream":
            body = self._read_json_body()
            q = (body.get("question") or "").strip()
            mode = (body.get("mode") or "all").strip().lower()
            history = body.get("history") or []
            if not q:
                self._send_json({"error": "Empty question"}, status=400)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                for ev in ai_engine.stream_answer(q, mode=mode, history=history):
                    chunk = f"data: {json.dumps(ev, ensure_ascii=False)}\n\n".encode("utf-8")
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as e:
                try:
                    err_ev = f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n".encode("utf-8")
                    self.wfile.write(err_ev)
                    self.wfile.flush()
                except Exception:
                    pass
            return

        if path == "/api/tts":
            body = self._read_json_body()
            txt = (body.get("text") or "").strip()[:2600]
            cfg = ai_engine.load_config()
            prof = (body.get("profile") or cfg.get("voice_profile") or "grand_narrator").strip()
            if not txt:
                self._send_json({"error": "No text"}, status=400)
                return
            try:
                wav_bytes = voice_engine.synthesize_wav(txt, profile=prof)
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(wav_bytes)))
                self.end_headers()
                self.wfile.write(wav_bytes)
            except Exception as e:
                self._send_json({"error": f"TTS unavailable: {e}"}, status=500)
            return

        if path == "/api/stt":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw_audio = self.rfile.read(min(length, 15 * 1024 * 1024))
                ctype = (self.headers.get("Content-Type") or "").lower()
                suffix = ".ogg" if "ogg" in ctype else (".wav" if "wav" in ctype else ".webm")
                text = voice_engine.transcribe_audio(raw_audio, suffix=suffix)
                self._send_json({"ok": True, "text": text})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return

        self.send_error(404, "Not Found")


def main():
    srv = ThreadedHTTPServer((HOST, PORT), TorahHandler)
    print(f"Torah Sanctuary listening on http://{HOST}:{PORT}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
