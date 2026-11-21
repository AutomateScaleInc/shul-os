#!/usr/bin/env python3
"""
Torah Sanctuary — The European Synagogue (Ohel Eliezer · theshul.eu)
Calendar, Rabbi Michoel Rosenblum's Programs, Brussels Shabbat Times (Hebcal),
ICS Feed Sync, and Weekly Mailing / Newsletter Hub.
"""

import csv
import html
import io
import json
import pathlib
import re
import sqlite3
import time
import urllib.request
from datetime import datetime, timedelta

import ai_engine
import torah_db

BASE_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "torah.db"
HEBCAL_CACHE = DATA_DIR / "brussels_hebcal_cache.json"
ICS_CACHE = DATA_DIR / "ics_events_cache.json"

SHUL_INFO = {
    "name": "The European Synagogue — Ohel Eliezer",
    "short_name": "The Shul (Ohel Eliezer)",
    "website": "https://www.theshul.eu",
    "address": "Rue Froissart 109, 1040 Brussels, Belgium",
    "rabbi": "Rabbi Michoel Rosenblum",
    "phone": "+32 2 335 5771",
    "email_office": "office@theshul.eu",
    "email_info": "info@theshul.eu",
    "email_kids": "Kids@theshul.eu",
    "geonameid": 2800866,  # Brussels, Belgium
}

DEFAULT_RECURRING_EVENTS = [
    (
        "shul-kabbalat-shabbat",
        "Kabbalat Shabbat & Community Kiddush",
        "Weekly · Friday",
        "At Candle Lighting",
        "Shabbat Services",
        "Rabbi Michoel Rosenblum",
        "Rue Froissart 109, 1040 Brussels",
        "Warm Friday evening Kabbalat Shabbat prayers followed by Kiddush & community fellowship. RSVP for Friday night dinners via office@theshul.eu.",
        "mailto:office@theshul.eu?subject=Friday%20Night%20RSVP",
        1,
        1,
    ),
    (
        "shul-shabbat-morning",
        "Shabbat Morning Shacharit, Torah Reading & Buffet Kiddush",
        "Weekly · Shabbat",
        "10:00 – 13:00",
        "Shabbat Services",
        "Rabbi Michoel Rosenblum",
        "Rue Froissart 109, 1040 Brussels",
        "Shacharit begins at 10:00 AM, Torah reading & D'var Torah with Rabbi Michoel Rosenblum, followed by a lavish community buffet Kiddush at 12:15 PM.",
        "https://www.theshul.eu",
        1,
        1,
    ),
    (
        "shul-kids-program",
        "Shabbat Children's Program & Kids Shul",
        "Weekly · Shabbat",
        "11:15 – 12:15",
        "Kids & Families",
        "Kids@theshul.eu",
        "Rue Froissart 109, 1040 Brussels",
        "Engaging weekly Torah stories, songs, games, and Jewish joy for children during Shabbat morning services. Contact Kids@theshul.eu.",
        "mailto:Kids@theshul.eu?subject=Kids%20Shul%20Program",
        1,
        1,
    ),
    (
        "shul-weekday-shacharit",
        "Weekday Morning Shacharit Minyan",
        "Weekly · Sun–Fri",
        "08:30",
        "Daily Minyan",
        "The European Synagogue",
        "Brussels (confirm daily location via office@theshul.eu)",
        "Daily weekday Shacharit services. Email office@theshul.eu or call +32 2 335 5771 for daily minyan updates.",
        "mailto:office@theshul.eu?subject=Weekday%20Minyan",
        1,
        1,
    ),
    (
        "shul-rabbi-michoel-torah",
        "Weekly Parashah & Torah Study with Rabbi Michoel",
        "Weekly · Contact for schedule",
        "TBA / Weekly",
        "Torah Class",
        "Rabbi Michoel Rosenblum",
        "The European Synagogue · theshul.eu",
        "Deep-dive Torah portion study, Jewish wisdom, and contemporary discussion led by Rabbi Michoel Rosenblum. Join our mailing list for weekly class times.",
        "https://www.theshul.eu",
        1,
        1,
    ),
    (
        "shul-kosher-business-lunch",
        "Kosher Business Club Lunch & Community Events",
        "Monthly · See theshul.eu",
        "12:30",
        "Community",
        "Rabbi Michoel Rosenblum",
        "Rue Froissart 109, 1040 Brussels",
        "Brussels European Quarter Kosher Business Club lunches, holiday celebrations, and community gatherings. Reservations at theshul.eu.",
        "https://www.theshul.eu",
        1,
        1,
    ),
]


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_tables():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS shul_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL DEFAULT '',
            event_time TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT 'Community',
            host TEXT NOT NULL DEFAULT 'Rabbi Michoel Rosenblum',
            location TEXT NOT NULL DEFAULT 'Rue Froissart 109, 1040 Brussels',
            description TEXT NOT NULL DEFAULT '',
            rsvp_url TEXT NOT NULL DEFAULT 'https://www.theshul.eu',
            recurring INTEGER NOT NULL DEFAULT 0,
            featured_ticker INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mailing_subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT '',
            email TEXT UNIQUE NOT NULL,
            interests TEXT NOT NULL DEFAULT 'Weekly Parashah & Shul Updates',
            source TEXT NOT NULL DEFAULT 'Torah Sanctuary Kiosk',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cnt = conn.execute("SELECT COUNT(*) FROM shul_events").fetchone()[0]
        if cnt == 0:
            conn.executemany(
                """
                INSERT OR IGNORE INTO shul_events
                (slug, title, event_date, event_time, category, host, location, description, rsvp_url, recurring, featured_ticker)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                DEFAULT_RECURRING_EVENTS,
            )
        conn.commit()


def get_brussels_shabbat_and_holidays() -> dict:
    """Fetch live Brussels Shabbat candle-lighting, Havdalah, Hebrew date, and upcoming holidays from Hebcal (cached 6h)."""
    now = time.time()
    cached = None
    if HEBCAL_CACHE.exists():
        try:
            cached = json.loads(HEBCAL_CACHE.read_text(encoding="utf-8"))
            if now - float(cached.get("fetched_at", 0)) < 21600:
                return cached["data"]
        except Exception:
            pass

    data = {
        "city": "Brussels, Belgium",
        "candle_lighting": "",
        "candle_date": "",
        "havdalah": "",
        "hebrew_date": "",
        "parasha": "",
        "upcoming_holidays": [],
        "source": "offline",
    }
    try:
        # 1. This week's Shabbat times for Brussels (geonameid=2800866)
        req1 = urllib.request.Request(
            f"https://www.hebcal.com/shabbat?cfg=json&geonameid={SHUL_INFO['geonameid']}&M=on&lg=en",
            headers={"User-Agent": "TorahSanctuary/1.0"},
        )
        with urllib.request.urlopen(req1, timeout=6) as r:
            sh = json.loads(r.read().decode("utf-8"))
        for it in sh.get("items", []):
            cat = it.get("category")
            if cat == "candles":
                data["candle_lighting"] = it.get("title", "").replace("Candle lighting: ", "")
                data["candle_date"] = (it.get("date") or "")[:10]
            elif cat == "havdalah":
                data["havdalah"] = it.get("title", "").replace("Havdalah: ", "")
            elif cat == "parashat":
                data["parasha"] = it.get("title", "")
                data["hebrew_date"] = it.get("hdate", "")

        # 2. Next 60 days of Jewish holidays & Rosh Chodesh for Brussels
        today = datetime.now()
        end = today + timedelta(days=60)
        url2 = (
            f"https://www.hebcal.com/hebcal?v=1&cfg=json&maj=on&min=on&mod=on&nx=on&ss=on"
            f"&start={today.strftime('%Y-%m-%d')}&end={end.strftime('%Y-%m-%d')}"
            f"&geonameid={SHUL_INFO['geonameid']}"
        )
        req2 = urllib.request.Request(url2, headers={"User-Agent": "TorahSanctuary/1.0"})
        with urllib.request.urlopen(req2, timeout=6) as r:
            cal = json.loads(r.read().decode("utf-8"))
        hols = []
        for it in cal.get("items", []):
            if it.get("category") in ("holiday", "roshchodesh"):
                hols.append({
                    "title": it.get("title", ""),
                    "hebrew": it.get("hebrew", ""),
                    "date": (it.get("date") or "")[:10],
                    "category": it.get("category", "holiday"),
                    "memo": it.get("memo", ""),
                })
        data["upcoming_holidays"] = hols[:12]
        data["source"] = "hebcal_live"
        HEBCAL_CACHE.write_text(json.dumps({"fetched_at": now, "data": data}, ensure_ascii=False), encoding="utf-8")
        return data
    except Exception:
        if cached and cached.get("data"):
            return cached["data"]
        return data


def _parse_ics_events(ics_text: str) -> list:
    """Zero-dependency RFC-5545 iCalendar VEVENT parser (supports Google Calendar, Chabad ICS, iCloud ICS)."""
    # Unfold RFC-5545 continuation lines
    unfolded = re.sub(r"\r?\n[ \t]", "", ics_text)
    events = []
    today_str = datetime.now().strftime("%Y-%m-%d")
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", unfolded, re.DOTALL):
        fields = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            k_part, val = line.split(":", 1)
            key = k_part.split(";", 1)[0].strip().upper()
            fields[key] = val.strip().replace("\\n", " ").replace("\\,", ",").replace("\\;", ";")
        summary = fields.get("SUMMARY", "").strip()
        dtstart = fields.get("DTSTART", "").strip()
        if not summary or not dtstart:
            continue
        m = re.match(r"(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2}))?", dtstart)
        if not m:
            continue
        date_s = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        time_s = f"{m.group(4)}:{m.group(5)}" if m.group(4) else "All Day"
        if date_s < today_str:
            continue
        events.append({
            "id": f"ics-{abs(hash(summary + dtstart)) % 1000000}",
            "title": summary,
            "event_date": date_s,
            "event_time": time_s,
            "category": "Calendar Feed",
            "host": "The European Synagogue (theshul.eu)",
            "location": fields.get("LOCATION") or SHUL_INFO["address"],
            "description": fields.get("DESCRIPTION", "")[:400],
            "rsvp_url": fields.get("URL") or SHUL_INFO["website"],
            "recurring": 0,
            "featured_ticker": 1,
            "source": "ics_feed",
        })
    events.sort(key=lambda e: (e["event_date"], e["event_time"]))
    return events[:25]


def get_ics_feed_events(force_refresh: bool = False) -> list:
    cfg = ai_engine.load_config()
    ics_url = (cfg.get("calendar_ics_url") or "").strip()
    if not ics_url:
        return []
    now = time.time()
    cached = None
    if not force_refresh and ICS_CACHE.exists():
        try:
            cached = json.loads(ICS_CACHE.read_text(encoding="utf-8"))
            if cached.get("url") == ics_url and (now - float(cached.get("fetched_at", 0))) < 1800:
                return cached.get("events", [])
        except Exception:
            pass
    try:
        req = urllib.request.Request(ics_url, headers={"User-Agent": "TorahSanctuary/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode("utf-8", "ignore")
        evs = _parse_ics_events(raw)
        ICS_CACHE.write_text(json.dumps({"url": ics_url, "fetched_at": now, "events": evs}, ensure_ascii=False), encoding="utf-8")
        return evs
    except Exception:
        return (cached or {}).get("events", [])


def list_events(force_ics: bool = False) -> dict:
    init_tables()
    with get_conn() as conn:
        local_evs = [
            {**dict(r), "source": "local"}
            for r in conn.execute("SELECT * FROM shul_events ORDER BY recurring ASC, event_date ASC, id ASC").fetchall()
        ]
    ics_evs = get_ics_feed_events(force_refresh=force_ics)
    shabbat = get_brussels_shabbat_and_holidays()
    return {
        "shul": SHUL_INFO,
        "shabbat_times": shabbat,
        "events": ics_evs + local_evs,
        "ics_count": len(ics_evs),
        "local_count": len(local_evs),
    }


def add_event(payload: dict) -> dict:
    init_tables()
    title = (payload.get("title") or "").strip()
    if not title:
        raise ValueError("Event title is required")
    slug = f"ev-{int(time.time())}-{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:24]}"
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO shul_events (slug, title, event_date, event_time, category, host, location, description, rsvp_url, recurring, featured_ticker)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug,
                title,
                (payload.get("event_date") or "").strip() or "Upcoming",
                (payload.get("event_time") or "").strip(),
                (payload.get("category") or "Rabbi Michoel Program").strip(),
                (payload.get("host") or SHUL_INFO["rabbi"]).strip(),
                (payload.get("location") or SHUL_INFO["address"]).strip(),
                (payload.get("description") or "").strip(),
                (payload.get("rsvp_url") or SHUL_INFO["website"]).strip(),
                1 if payload.get("recurring") else 0,
                0 if payload.get("featured_ticker") is False else 1,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM shul_events WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def delete_event(event_id: int) -> bool:
    init_tables()
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM shul_events WHERE id = ?", (int(event_id),))
        conn.commit()
        return cur.rowcount > 0


def add_subscriber(name: str, email: str, interests: str = "") -> dict:
    init_tables()
    email = (email or "").strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValueError("Please enter a valid email address.")
    name = (name or "").strip()
    interests = (interests or "Weekly Parashah & Shul Updates").strip()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO mailing_subscribers (name, email, interests)
            VALUES (?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET name=excluded.name, interests=excluded.interests
            """,
            (name, email, interests),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM mailing_subscribers WHERE email = ?", (email,)).fetchone()
        sub = dict(row)

    # Optional automatic webhook forward to Mailchimp / Brevo / Chabad CRM / GHL / Zapier
    cfg = ai_engine.load_config()
    hook = (cfg.get("mailing_webhook_url") or "").strip()
    forwarded = False
    if hook:
        try:
            req = urllib.request.Request(
                hook,
                data=json.dumps({
                    "type": "synagogue_mailing_signup",
                    "shul": SHUL_INFO["name"],
                    "website": SHUL_INFO["website"],
                    "subscriber": sub,
                }).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "TorahSanctuary/1.0"},
            )
            urllib.request.urlopen(req, timeout=5).close()
            forwarded = True
        except Exception:
            pass
    return {"ok": True, "subscriber": sub, "webhook_forwarded": forwarded}


def list_subscribers() -> list:
    init_tables()
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM mailing_subscribers ORDER BY id DESC").fetchall()]


def export_subscribers_csv() -> str:
    subs = list_subscribers()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Name", "Email", "Interests", "Source", "Subscribed At"])
    for s in subs:
        w.writerow([s["name"], s["email"], s["interests"], s["source"], s["created_at"]])
    return buf.getvalue()


def generate_weekly_mailing() -> dict:
    """Auto-compose a ready-to-send Weekly Shul Mailing (HTML + Plain Text) combining Today's Parashah, Brussels Shabbat times, and Rabbi Michoel / theshul.eu events."""
    daily = torah_db.get_daily_portion()
    ev_bundle = list_events()
    sh = ev_bundle["shabbat_times"]
    p = daily["parasha"]
    events = ev_bundle["events"][:10]
    story = daily.get("matching_story")

    subject = f"Shabbat Shalom — Parashat {p['en_name']} ({p['he_name']}) · The European Synagogue (theshul.eu)"
    candles_line = f"Candle Lighting (Brussels): {sh['candle_lighting']}" if sh.get("candle_lighting") else "Check theshul.eu for Brussels candle lighting times"
    havdalah_line = f" | Shabbat Ends (Havdalah): {sh['havdalah']}" if sh.get("havdalah") else ""
    hdate_line = f" · {sh['hebrew_date']}" if sh.get("hebrew_date") else ""

    # Plain text newsletter
    txt_lines = [
        f"{SHUL_INFO['name']} ({SHUL_INFO['website']})",
        f"{SHUL_INFO['address']} | {SHUL_INFO['phone']} | {SHUL_INFO['email_office']}",
        "=" * 64,
        f"SHABBAT SHALOM — PARASHAT {p['en_name'].upper()} ({p['he_name']}){hdate_line}",
        f"Torah Portion: {p['ref']}  |  Haftarah: {p['haftarah']}",
        f"Today's Reading ({daily['day_en']} — {daily['aliyah_en']}): {daily['aliyah_ref']}",
        f"{candles_line}{havdalah_line}",
        "",
        "THIS WEEK'S TORAH MESSAGE:",
        p["summary"],
        "",
    ]
    if story:
        txt_lines += [f"SHABBAT TABLE STORY: {story['title']} ({story['he_title']})", story["subtitle"], ""]
    txt_lines.append("UPCOMING AT THE SHUL & RABBI MICHOEL'S PROGRAMS:")
    for e in events:
        txt_lines.append(f"- {e['title']} ({e['event_date']} {e['event_time']}) — {e['location']}")
        if e.get("description"):
            txt_lines.append(f"  {e['description'][:200]}")
    if sh.get("upcoming_holidays"):
        txt_lines.append("")
        txt_lines.append("UPCOMING JEWISH CALENDAR DATES (BRUSSELS):")
        for h in sh["upcoming_holidays"][:5]:
            txt_lines.append(f"- {h['date']}: {h['title']} ({h['hebrew']})")
    txt_lines += [
        "",
        f"Warmly, {SHUL_INFO['rabbi']} & {SHUL_INFO['name']}",
        f"RSVP & Info: {SHUL_INFO['email_office']} | Kids: {SHUL_INFO['email_kids']} | {SHUL_INFO['website']}",
    ]
    plain_text = "\n".join(txt_lines)

    # Clean, responsive email-ready HTML
    ev_html = "".join(
        f"""<tr><td style="padding:10px 0;border-bottom:1px solid #e6dcc8;">
        <strong style="color:#1b2a4a;font-size:15px;">{html.escape(e['title'])}</strong><br>
        <span style="color:#8b5e14;font-size:13px;font-weight:bold;">{html.escape(e['event_date'])} {html.escape(e['event_time'])} · {html.escape(e['host'])}</span><br>
        <span style="color:#444;font-size:13px;">{html.escape(e.get('description',''))}</span>
        </td></tr>"""
        for e in events
    )
    hol_html = "".join(
        f"<li style='margin:4px 0;'><strong>{html.escape(h['date'])}</strong> — {html.escape(h['title'])} ({html.escape(h['hebrew'])})</li>"
        for h in (sh.get("upcoming_holidays") or [])[:5]
    )
    email_html = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:24px;background:#f5efe3;font-family:Georgia,serif;color:#1f2430;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #d9c59b;border-radius:12px;overflow:hidden;">
  <tr><td style="background:#0f192d;color:#e4bc69;padding:24px 28px;text-align:center;">
    <div style="font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#b7c2d6;">{html.escape(SHUL_INFO['name'])}</div>
    <h1 style="margin:8px 0 4px;font-size:26px;color:#e4bc69;">Parashat {html.escape(p['en_name'])} · פרשת {html.escape(p['he_name'])}</h1>
    <div style="font-size:14px;color:#f4efe6;">{html.escape(p['ref'])} · Haftarah: {html.escape(p['haftarah'])}{html.escape(hdate_line)}</div>
  </td></tr>
  <tr><td style="background:#fbf5e6;padding:14px 28px;border-bottom:1px solid #e6dcc8;text-align:center;font-family:Arial,sans-serif;font-size:14px;">
    <strong>🕯 {html.escape(candles_line)}{html.escape(havdalah_line)}</strong>
  </td></tr>
  <tr><td style="padding:22px 28px;line-height:1.65;font-size:15px;">
    <h2 style="margin:0 0 8px;color:#1b2a4a;font-size:19px;">This Week's Torah Portion</h2>
    <p style="margin:0 0 14px;">{html.escape(p['summary'])}</p>
    <div style="background:#f9f4ea;border-left:4px solid #b8872c;padding:12px 16px;margin:14px 0;font-size:14px;">
      <strong>Today's Aliyah ({html.escape(daily['day_en'])} · {html.escape(daily['aliyah_en'])}):</strong> {html.escape(daily['aliyah_ref'])}
    </div>
    <h2 style="margin:22px 0 8px;color:#1b2a4a;font-size:19px;">Upcoming at The Shul &amp; Rabbi Michoel's Programs</h2>
    <table width="100%" cellpadding="0" cellspacing="0" style="font-family:Arial,sans-serif;">{ev_html}</table>
    {f'<h3 style="margin:20px 0 6px;color:#1b2a4a;font-size:16px;">Upcoming Jewish Calendar (Brussels)</h3><ul style="font-family:Arial,sans-serif;font-size:14px;">{hol_html}</ul>' if hol_html else ''}
  </td></tr>
  <tr><td style="background:#0f192d;color:#b7c2d6;padding:16px 28px;text-align:center;font-family:Arial,sans-serif;font-size:12px;">
    <strong style="color:#e4bc69;">{html.escape(SHUL_INFO['name'])}</strong> · {html.escape(SHUL_INFO['address'])}<br>
    {html.escape(SHUL_INFO['rabbi'])} · {html.escape(SHUL_INFO['phone'])} ·
    <a href="mailto:{html.escape(SHUL_INFO['email_office'])}" style="color:#e4bc69;">{html.escape(SHUL_INFO['email_office'])}</a> ·
    <a href="{html.escape(SHUL_INFO['website'])}" style="color:#e4bc69;">theshul.eu</a>
  </td></tr>
</table></body></html>"""

    return {
        "subject": subject,
        "plain_text": plain_text,
        "html": email_html,
        "subscribers_count": len(list_subscribers()),
    }


def get_ticker_announcements() -> list:
    """Short, dignified community & Shabbat-time items to weave into the Sanctuary scrolling ticker."""
    ev_bundle = list_events()
    sh = ev_bundle["shabbat_times"]
    items = []
    if sh.get("candle_lighting"):
        hav = f" · Havdalah {sh['havdalah']}" if sh.get("havdalah") else ""
        hd = f" ({sh['hebrew_date']})" if sh.get("hebrew_date") else ""
        items.append(f"🕯 BRUSSELS SHABBAT{hd} · The Shul (theshul.eu): Candle Lighting {sh['candle_lighting']}{hav} · Shabbat Shacharit 10:00 AM · Kids Program 11:15 AM · Kiddush 12:15 PM")
    for e in ev_bundle["events"]:
        if e.get("featured_ticker", 1):
            items.append(f"📅 THE SHUL ({e['event_date']} {e['event_time']}): {e['title']} — {e['host']}")
    for h in (sh.get("upcoming_holidays") or [])[:3]:
        items.append(f"✨ UPCOMING: {h['title']} ({h['hebrew']}) — {h['date']}")
    return items[:8]
