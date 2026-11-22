#!/usr/bin/env python3
"""
Torah Sanctuary OS — Multi-Channel Community Syndication & Mobile QR Sponsorship Hub.

1. Auto-Syndication across 7 Channels:
   - Live RSS 2.0 XML Feed (/feed.xml)
   - Website 1-Line Embed Widget (/embed.js)
   - Weekly HTML & Plain-Text Email Newsletter
   - WhatsApp Broadcast Message (+ wa.me 1-click link)
   - SMS / Text Message Digest
   - Eventbrite-Ready Event Payloads
   - Formal Community PR / Press Release
   - Automated Webhook Transmission (Zapier / Make / n8n / Brevo / Mailchimp / Twilio / Eventbrite)

2. Mobile QR Splash Page (/give) & Individual Shul Sponsorships:
   - Sponsor specific items & events (Shabbat Kiddush, Friday Dinner, Kids Shul, Parnas HaYom,
     Chanukah Menorah, Siddur/Chumash Dedication, General Tzedakah in Chai multiples)
   - Instant local SVG QR code + pledge tracking in SQLite + configurable live checkout URL.
"""

import email.utils
import html
import json
import pathlib
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import ai_engine
import broadcast_hub
import sacred_astronomy
import shul_events
import torah_db

BASE_DIR = pathlib.Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "torah.db"

DEFAULT_SPONSORSHIP_ITEMS = [
    (
        "shabbat-kiddush",
        "🥂 Sponsor This Week's Shabbat Buffet Kiddush",
        "Shabbat & Meals",
        360,
        "EUR",
        "Honor a birthday, anniversary, or Yahrzeit by sponsoring our warm community Shabbat buffet Kiddush for 80+ members & European Quarter guests.",
        "Weekly · Shabbat 12:15 PM",
        1,
    ),
    (
        "friday-night-dinner",
        "🕯 Host a Friday Night Community Shabbat Dinner",
        "Shabbat & Meals",
        540,
        "EUR",
        "Welcome diplomats, students, young professionals, and travelers to Rabbi Michoel's Shabbat table at Rue Froissart 109.",
        "Weekly · Friday Evening",
        1,
    ),
    (
        "kids-shul-program",
        "🧸 Sponsor Shabbat Kids Shul & Youth Treats",
        "Kids & Education",
        180,
        "EUR",
        "Support weekly Torah stories, crafts, games, and kosher treats for Brussels' next generation (Kids@theshul.eu).",
        "Weekly · Shabbat 11:15 AM",
        1,
    ),
    (
        "parnas-hayom",
        "📖 Sponsor a Day of Torah Learning (Parnas HaYom)",
        "Torah Dedication",
        100,
        "EUR",
        "Dedicate today's Torah Sanctuary display & daily study in honor of a simcha, recovery (Refuah Shleimah), or loving memory (L'Ilui Nishmat).",
        "Any Day of the Year",
        1,
    ),
    (
        "chanukah-celebration",
        "🕎 Chanukah Public Menorah & Community Celebration",
        "Upcoming Holiday",
        500,
        "EUR",
        "Help bring glowing public Chanukah light, live music, hot latkes, and sufganiyot to Brussels' European Quarter.",
        "25 Kislev · Dec 2026",
        1,
    ),
    (
        "siddur-chumash",
        "📚 Dedicate a Prayer Book (Siddur) or Chumash",
        "Synagogue Sanctuary",
        54,
        "EUR",
        "Place a permanently inscribed bookplate inside a synagogue Siddur or Chumash used every Shabbat at Ohel Eliezer.",
        "Permanent Dedication",
        0,
    ),
    (
        "general-tzedakah",
        "💛 General Tzedakah & Synagogue Support (Chai €18+)",
        "General Giving",
        36,
        "EUR",
        "Strengthen Jewish life, daily minyanim, adult education, and warm hospitality in the heart of Europe.",
        "Any Amount Welcome",
        0,
    ),
]


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_tables():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS sponsorship_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            title TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Community',
            amount INTEGER NOT NULL DEFAULT 180,
            currency TEXT NOT NULL DEFAULT 'EUR',
            description TEXT NOT NULL DEFAULT '',
            schedule_label TEXT NOT NULL DEFAULT '',
            featured INTEGER NOT NULL DEFAULT 1,
            sponsored_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS donation_pledges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_slug TEXT NOT NULL DEFAULT 'general-tzedakah',
            item_title TEXT NOT NULL DEFAULT '',
            amount INTEGER NOT NULL DEFAULT 36,
            currency TEXT NOT NULL DEFAULT 'EUR',
            donor_name TEXT NOT NULL DEFAULT '',
            donor_email TEXT NOT NULL DEFAULT '',
            donor_phone TEXT NOT NULL DEFAULT '',
            dedication TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pledged',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS syndication_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channels TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'ok',
            detail TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS community_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visitor_name TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            topic TEXT NOT NULL DEFAULT 'Connect & Say Shalom',
            message TEXT NOT NULL DEFAULT '',
            opt_in_updates INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cnt = conn.execute("SELECT COUNT(*) FROM sponsorship_items").fetchone()[0]
        if cnt == 0:
            conn.executemany(
                """
                INSERT OR IGNORE INTO sponsorship_items
                (slug, title, category, amount, currency, description, schedule_label, featured)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                DEFAULT_SPONSORSHIP_ITEMS,
            )
        conn.commit()


def get_public_base_url(request_host: str = "") -> str:
    """Resolve the best scannable base URL: configured public URL > active Cloudflare broadcast tunnel > LAN IP."""
    cfg = ai_engine.load_config()
    for key in ("public_sanctuary_url", "broadcast_public_base_url"):
        val = (cfg.get(key) or "").strip().rstrip("/")
        if val:
            return val
    bstate = broadcast_hub.get_state(include_deck=False)
    if bstate.get("public_url"):
        # Strip /watch suffix if present
        pub = bstate["public_url"].rstrip("/")
        if pub.endswith("/watch"):
            pub = pub[:-6]
        return pub
    if request_host and not request_host.startswith(("127.0.0.1", "localhost")):
        return f"http://{request_host}"
    lan = broadcast_hub._detect_lan_ip()
    return f"http://{lan}:8080"


def get_give_url(request_host: str = "") -> str:
    return get_public_base_url(request_host) + "/give"


def list_sponsorship_items() -> list:
    init_tables()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sponsorship_items ORDER BY featured DESC, id ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def add_sponsorship_item(payload: dict) -> dict:
    init_tables()
    title = (payload.get("title") or "").strip()
    if not title:
        raise ValueError("Item title is required")
    amount = max(1, int(payload.get("amount") or 180))
    slug = f"sp-{int(datetime.now().timestamp())}-{abs(hash(title)) % 10000}"
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO sponsorship_items (slug, title, category, amount, currency, description, schedule_label, featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug,
                title,
                (payload.get("category") or "Community").strip(),
                amount,
                (payload.get("currency") or "EUR").strip().upper(),
                (payload.get("description") or "").strip(),
                (payload.get("schedule_label") or "Upcoming").strip(),
                1 if payload.get("featured", True) else 0,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM sponsorship_items WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def delete_sponsorship_item(item_id: int) -> bool:
    init_tables()
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM sponsorship_items WHERE id = ?", (int(item_id),))
        conn.commit()
        return cur.rowcount > 0


def record_pledge(payload: dict) -> dict:
    init_tables()
    item_slug = (payload.get("item_slug") or "general-tzedakah").strip()
    donor_name = (payload.get("donor_name") or "").strip()
    if not donor_name:
        raise ValueError("Please enter your name.")
    amount = max(1, int(payload.get("amount") or 36))
    currency = (payload.get("currency") or "EUR").strip().upper()
    donor_email = (payload.get("donor_email") or "").strip()
    donor_phone = (payload.get("donor_phone") or "").strip()
    dedication = (payload.get("dedication") or "").strip()

    with get_conn() as conn:
        item = conn.execute("SELECT title FROM sponsorship_items WHERE slug = ?", (item_slug,)).fetchone()
        item_title = (payload.get("item_title") or (item["title"] if item else "General Tzedakah")).strip()
        cur = conn.execute(
            """
            INSERT INTO donation_pledges (item_slug, item_title, amount, currency, donor_name, donor_email, donor_phone, dedication)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item_slug, item_title, amount, currency, donor_name, donor_email, donor_phone, dedication),
        )
        if item:
            conn.execute(
                "UPDATE sponsorship_items SET sponsored_count = sponsored_count + 1 WHERE slug = ?",
                (item_slug,),
            )
        conn.commit()
        pledge = dict(conn.execute("SELECT * FROM donation_pledges WHERE id = ?", (cur.lastrowid,)).fetchone())

    cfg = ai_engine.load_config()
    hook = (cfg.get("syndication_webhook_url") or cfg.get("mailing_webhook_url") or "").strip()
    forwarded = False
    if hook:
        try:
            req = urllib.request.Request(
                hook,
                data=json.dumps({
                    "type": "synagogue_sponsorship_pledge",
                    "shul": shul_events.SHUL_INFO["name"],
                    "pledge": pledge,
                }).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "TorahSanctuary/1.0"},
            )
            urllib.request.urlopen(req, timeout=5).close()
            forwarded = True
        except Exception:
            pass

    checkout_url = (cfg.get("donation_checkout_url") or shul_events.SHUL_INFO["website"]).strip()
    return {
        "ok": True,
        "pledge": pledge,
        "webhook_forwarded": forwarded,
        "checkout_url": checkout_url,
    }


def list_pledges(limit: int = 30) -> list:
    init_tables()
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM donation_pledges ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
        return [dict(r) for r in rows]


def record_visitor_message(payload: dict) -> dict:
    """Save a direct message / prayer request / opt-in from a phone that scanned the Sanctuary QR code."""
    init_tables()
    name = (payload.get("visitor_name") or payload.get("name") or "").strip()
    phone = (payload.get("phone") or "").strip()
    email_addr = (payload.get("email") or "").strip()
    topic = (payload.get("topic") or "Connect & Say Shalom").strip()
    message = (payload.get("message") or "").strip()
    opt_in = 1 if payload.get("opt_in_updates", True) else 0
    if not name and not phone and not email_addr:
        raise ValueError("Please enter your name and phone or email so Rabbi Michoel can connect with you.")
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO community_messages (visitor_name, phone, email, topic, message, opt_in_updates)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name or "Synagogue Guest", phone, email_addr, topic, message, opt_in),
        )
        conn.commit()
        msg_row = dict(conn.execute("SELECT * FROM community_messages WHERE id = ?", (cur.lastrowid,)).fetchone())

    # Also auto-subscribe to shul mailing list if email provided & opted in
    if email_addr and opt_in:
        try:
            shul_events.add_subscriber(name or "Sanctuary Guest", email_addr, f"QR Connect · {topic}")
        except Exception:
            pass

    cfg = ai_engine.load_config()
    hook = (cfg.get("syndication_webhook_url") or cfg.get("mailing_webhook_url") or "").strip()
    forwarded = False
    if hook:
        try:
            req = urllib.request.Request(
                hook,
                data=json.dumps({
                    "type": "synagogue_visitor_connect",
                    "shul": shul_events.SHUL_INFO["name"],
                    "visitor": msg_row,
                }).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "TorahSanctuary/1.0"},
            )
            urllib.request.urlopen(req, timeout=5).close()
            forwarded = True
        except Exception:
            pass
    return {"ok": True, "message": msg_row, "webhook_forwarded": forwarded}


def list_visitor_messages(limit: int = 30) -> list:
    init_tables()
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM community_messages ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
        return [dict(r) for r in rows]


def build_rss_xml(request_host: str = "") -> str:
    """Generate standards-compliant RSS 2.0 XML for Mailchimp, WordPress, Slack, News & Aggregators."""
    base_url = get_public_base_url(request_host)
    give_url = base_url + "/give"
    daily = torah_db.get_daily_portion()
    ev_bundle = shul_events.list_events()
    sh = ev_bundle["shabbat_times"]
    p = daily["parasha"]
    pub_date = email.utils.format_datetime(datetime.now(timezone.utc))
    shul = shul_events.SHUL_INFO

    p_slug = (p.get("slug") or p.get("en_name") or "parasha").lower().replace(" ", "-")
    items_xml = [
        f"""    <item>
      <title>{html.escape(f"Parashat {p['en_name']} ({p['he_name']}) — Shabbat Times & Torah Message")}</title>
      <link>{html.escape(base_url)}</link>
      <guid isPermaLink="false">parasha-{html.escape(p_slug)}-{datetime.now().strftime('%Y-%W')}</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{html.escape(f"{p['summary']} | Torah: {p['ref']} | Haftarah: {p['haftarah']} | Candle Lighting: {sh.get('candle_lighting','')} | Havdalah: {sh.get('havdalah','')} | Sponsor or Donate: {give_url}")}</description>
    </item>"""
    ]

    for ev in ev_bundle["events"][:10]:
        items_xml.append(
            f"""    <item>
      <title>{html.escape(f"{ev['title']} ({ev['event_date']} {ev['event_time']})")}</title>
      <link>{html.escape(ev.get('rsvp_url') or shul['website'])}</link>
      <guid isPermaLink="false">shul-event-{html.escape(str(ev.get('slug') or ev.get('id')))}</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{html.escape(f"{ev.get('description','')} — Location: {ev.get('location','')} · Host: {ev.get('host','')} · Sponsor: {give_url}")}</description>
    </item>"""
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{html.escape(shul['name'])} — Weekly Torah, Shabbat Times &amp; Community Events</title>
    <link>{html.escape(shul['website'])}</link>
    <atom:link href="{html.escape(base_url)}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Live Weekly Parashah, Brussels Shabbat Candle Lighting, Rabbi Michoel Rosenblum's programs, and community sponsorships.</description>
    <language>en</language>
    <lastBuildDate>{pub_date}</lastBuildDate>
{chr(10).join(items_xml)}
  </channel>
</rss>
"""


def build_embed_js(request_host: str = "") -> str:
    """1-line drop-in JavaScript widget for theshul.eu or any synagogue website."""
    base_url = get_public_base_url(request_host)
    daily = torah_db.get_daily_portion()
    ev_bundle = shul_events.list_events()
    sh = ev_bundle["shabbat_times"]
    p = daily["parasha"]
    payload = {
        "shul": shul_events.SHUL_INFO["name"],
        "parasha": f"Parashat {p['en_name']} ({p['he_name']})",
        "ref": p["ref"],
        "summary": p["summary"],
        "candles": sh.get("candle_lighting", ""),
        "havdalah": sh.get("havdalah", ""),
        "give_url": base_url + "/give",
        "watch_url": base_url + "/watch",
        "events": [
            {"title": e["title"], "when": f"{e['event_date']} {e['event_time']}".strip(), "url": e.get("rsvp_url") or shul_events.SHUL_INFO["website"]}
            for e in ev_bundle["events"][:4]
        ],
    }
    data_json = json.dumps(payload, ensure_ascii=False)
    return f"""(function(){{
  var d = {data_json};
  var host = document.currentScript && document.currentScript.parentNode;
  var box = document.createElement('div');
  box.style.cssText = 'font-family:Georgia,serif;background:#0f192d;color:#f4efe6;border:1px solid #d9b45d;border-radius:14px;padding:18px;max-width:460px;box-shadow:0 12px 30px rgba(0,0,0,0.35);';
  var evs = d.events.map(function(e){{ return '<li style="margin:4px 0;"><a href="'+e.url+'" style="color:#f3d796;text-decoration:none;"><strong>'+e.title+'</strong></a> <span style="color:#b7c2d6;font-size:12px;">('+e.when+')</span></li>'; }}).join('');
  box.innerHTML = '<div style="font-size:11px;letter-spacing:1.4px;text-transform:uppercase;color:#e4bc69;font-weight:bold;">✡ '+d.shul+'</div>'
    + '<h3 style="margin:6px 0 4px;color:#fff;font-size:20px;">'+d.parasha+'</h3>'
    + '<div style="font-size:13px;color:#9fd8f8;margin-bottom:8px;">🕯 Candles: <strong>'+d.candles+'</strong> · Havdalah: <strong>'+d.havdalah+'</strong></div>'
    + '<p style="font-size:13.5px;line-height:1.5;margin:0 0 10px;color:#e8dfd0;">'+d.summary+'</p>'
    + '<ul style="padding-left:18px;margin:0 0 12px;font-family:Arial,sans-serif;font-size:13px;">'+evs+'</ul>'
    + '<div style="display:flex;gap:8px;flex-wrap:wrap;font-family:Arial,sans-serif;">'
    + '<a href="'+d.give_url+'" style="background:#e4bc69;color:#0b1120;padding:8px 14px;border-radius:8px;font-weight:bold;text-decoration:none;font-size:13px;">💛 Sponsor / Donate</a>'
    + '<a href="'+d.watch_url+'" style="border:1px solid #e4bc69;color:#e4bc69;padding:8px 14px;border-radius:8px;font-weight:bold;text-decoration:none;font-size:13px;">📺 Live Sanctuary</a>'
    + '</div>';
  if (host) host.insertBefore(box, document.currentScript);
}})();
"""


def build_syndication_pack(request_host: str = "") -> dict:
    """Build ready-to-transmit multi-channel outreach payloads for all 7 channels."""
    init_tables()
    base_url = get_public_base_url(request_host)
    give_url = base_url + "/give"
    watch_url = base_url + "/watch"
    rss_url = base_url + "/feed.xml"
    embed_snippet = f'<script src="{base_url}/embed.js"></script>'

    daily = torah_db.get_daily_portion()
    ev_bundle = shul_events.list_events()
    mailing = shul_events.generate_weekly_mailing()
    snap = sacred_astronomy.get_sacred_moment()
    sh = ev_bundle["shabbat_times"]
    p = daily["parasha"]
    shul = shul_events.SHUL_INFO
    candles = sh.get("candle_lighting") or next((z["time"] for z in snap["zmanim"] if z["key"] == "candle_lighting"), "")
    havdalah = sh.get("havdalah") or next((z["time"] for z in snap["zmanim"] if z["key"] == "tzeit"), "")

    # 1. WhatsApp Broadcast
    ev_bullets = "\n".join(f"• *{e['title']}* — {e['event_date']} {e['event_time']}" for e in ev_bundle["events"][:5])
    whatsapp_text = (
        f"✡ *Shabbat Shalom — Parashat {p['en_name']} ({p['he_name']})*\n"
        f"_{shul['name']} · {shul['address']}_\n\n"
        f"🕯 *Candle Lighting (Brussels):* {candles}\n"
        f"✨ *Shabbat Ends (Havdalah):* {havdalah}\n"
        f"📖 *Torah:* {p['ref']} | *Haftarah:* {p['haftarah']}\n\n"
        f"{p['summary']}\n\n"
        f"*Upcoming at The Shul:*\n{ev_bullets}\n\n"
        f"💛 *Sponsor a Kiddush, Kids Shul or Day of Learning:* {give_url}\n"
        f"📺 *Connect to Live Sanctuary Screen:* {watch_url}"
    )
    whatsapp_url = "https://wa.me/?text=" + urllib.parse.quote(whatsapp_text)

    # 2. SMS / Text Blast (concise <= 300 chars)
    sms_text = (
        f"Shabbat Shalom from The Shul (theshul.eu)! Parashat {p['en_name']}. "
        f"Brussels Candles {candles}, Havdalah {havdalah}. Shacharit 10:00, Kids 11:15, Kiddush 12:15. "
        f"Sponsor/RSVP: {give_url}"
    )

    # 3. Eventbrite-Ready Structured Event Payloads
    eventbrite_events = []
    for e in ev_bundle["events"][:6]:
        eventbrite_events.append({
            "name": f"{e['title']} — {shul['short_name']}",
            "summary": (e.get("description") or f"Join {shul['rabbi']} at {shul['name']}.")[:140],
            "description": f"{e.get('description','')}\n\nHosted by: {e.get('host', shul['rabbi'])}\nLocation: {e.get('location', shul['address'])}\nWeekly Portion: Parashat {p['en_name']}\nSponsor this event: {give_url}",
            "venue": e.get("location") or shul["address"],
            "schedule": f"{e.get('event_date','')} {e.get('event_time','')}".strip(),
            "category": e.get("category", "Community"),
            "tags": ["Brussels", "Jewish Community", "Synagogue", "European Quarter", p["en_name"]],
            "rsvp_url": e.get("rsvp_url") or shul["website"],
        })

    # 4. Formal Community PR / Press Release
    today_str = datetime.now().strftime("%B %d, %Y")
    pr_text = (
        f"FOR IMMEDIATE RELEASE — {today_str}\n"
        f"Contact: {shul['rabbi']} | {shul['email_office']} | {shul['phone']} | {shul['website']}\n\n"
        f"THE EUROPEAN SYNAGOGUE (OHEL ELIEZER) WELCOMES BRUSSELS COMMUNITY FOR PARASHAT {p['en_name'].upper()} & UPCOMING PROGRAMS\n\n"
        f"BRUSSELS, BELGIUM — {shul['name']}, located in the heart of the European Quarter at {shul['address']}, "
        f"invites residents, European institutions staff, families, and visitors to join {shul['rabbi']} for Shabbat services, "
        f"children's programming, and community fellowship this week.\n\n"
        f"This Shabbat marks Parashat {p['en_name']} ({p['ref']}), with Brussels candle lighting at {candles} and Havdalah at {havdalah}. "
        f"{p['summary']}\n\n"
        f"Community members and supporters can view live schedules, join Torah study broadcasts, or sponsor a Shabbat Kiddush, "
        f"Children's Program, or Day of Learning directly at {give_url} or {shul['website']}.\n\n"
        f"###"
    )

    with get_conn() as conn:
        logs = [dict(r) for r in conn.execute("SELECT * FROM syndication_log ORDER BY id DESC LIMIT 10").fetchall()]

    cfg = ai_engine.load_config()
    return {
        "base_url": base_url,
        "give_url": give_url,
        "watch_url": watch_url,
        "rss_url": rss_url,
        "embed_snippet": embed_snippet,
        "checkout_url": (cfg.get("donation_checkout_url") or shul["website"]).strip(),
        "webhook_configured": bool((cfg.get("syndication_webhook_url") or cfg.get("mailing_webhook_url") or "").strip()),
        "parasha": p,
        "channels": {
            "rss": {"url": rss_url, "xml_preview": build_rss_xml(request_host)[:1400]},
            "website": {"embed_snippet": embed_snippet, "script_url": base_url + "/embed.js"},
            "email": {"subject": mailing["subject"], "plain_text": mailing["plain_text"], "html_len": len(mailing["html"])},
            "whatsapp": {"text": whatsapp_text, "share_url": whatsapp_url},
            "sms": {"text": sms_text, "char_count": len(sms_text)},
            "eventbrite": {"events": eventbrite_events},
            "pr": {"text": pr_text},
        },
        "recent_transmissions": logs,
    }


def transmit_all_channels(channels: list = None, request_host: str = "") -> dict:
    """Transmit the multi-channel syndication bundle to the configured automation webhook (Zapier/Make/n8n/Brevo/Twilio/Eventbrite)."""
    init_tables()
    pack = build_syndication_pack(request_host)
    selected = channels or ["rss", "website", "email", "whatsapp", "sms", "eventbrite", "pr"]
    cfg = ai_engine.load_config()
    hook = (cfg.get("syndication_webhook_url") or cfg.get("mailing_webhook_url") or "").strip()

    status = "ready_local"
    detail = "Generated & logged all 7 channel payloads locally. Configure Syndication Webhook URL in Settings (Zapier / Make / n8n / Brevo / Twilio / Eventbrite) for automatic one-click external delivery!"
    if hook:
        try:
            body = {
                "type": "torah_sanctuary_syndication_broadcast",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "shul": shul_events.SHUL_INFO,
                "channels_requested": selected,
                "rss_url": pack["rss_url"],
                "give_url": pack["give_url"],
                "watch_url": pack["watch_url"],
                "payloads": {k: pack["channels"][k] for k in selected if k in pack["channels"]},
            }
            req = urllib.request.Request(
                hook,
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "TorahSanctuary/1.0"},
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                code = r.status
            status = "transmitted"
            detail = f"Transmitted {', '.join(selected)} to webhook (HTTP {code})."
        except Exception as e:
            status = "webhook_error"
            detail = f"Webhook delivery error: {e}"

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO syndication_log (channels, status, detail) VALUES (?, ?, ?)",
            (", ".join(selected), status, detail),
        )
        conn.commit()
    return {"ok": status != "webhook_error", "status": status, "detail": detail, "channels": selected, "give_url": pack["give_url"], "rss_url": pack["rss_url"]}
