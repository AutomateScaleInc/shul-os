#!/usr/bin/env python3
"""Shul.OS — Synagogue Mailings, Event Notifications & Marketing Broadcast Engine.

Zero external Python dependencies (Python 3.9+ stdlib).
Composes 6 Shabbat-safe, tri-lingual (EN / FR / HE) synagogue campaigns:
  1. pre_shabbos        — Friday Pre-Shabbos Candle Lighting & Parashah Alert
  2. weekly_prep        — Weekly Prep, Parashah Digest, Hebrew Root & Table Riddle
  3. event_notification — Upcoming Shul Events & RSVP Blast
  4. special_days       — Rosh Chodesh, Molad, Fast Days & Community Dedications
  5. holiday_chag       — Upcoming Chag / Holiday Guide & Service Schedule
  6. custom_marketing   — Custom Rabbi Announcement, Sponsorship or Community Promo

Supports direct delivery via:
  - Resend API, Mailgun API, Brevo API, SMTP (TLS/SSL), or Webhook (n8n/Make/Zapier/GHL)
  - Optional instant mobile Push Notification (ntfy.sh / Telegram / Push webhook)
  - WhatsApp & SMS copy-ready payloads
  - Automatic Halachic Shabbat & Yom Tov Send Guard (never sends on Shabbat or Chag!)
"""
from __future__ import annotations

import base64
import datetime
import html
import json
import smtplib
import sqlite3
import ssl
import urllib.parse
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

import ai_engine
import community_hub
import sacred_astronomy
import shul_events
import torah_db

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "torah.db"

CAMPAIGN_TYPES = {
    "pre_shabbos": {
        "id": "pre_shabbos",
        "label": "Pre-Shabbos Alert",
        "icon": "🕯️",
        "desc": "Candle lighting, Kabbalat Shabbat, Kiddush, Parashah highlight & Havdalah",
    },
    "weekly_prep": {
        "id": "weekly_prep",
        "label": "Weekly Prep & Parashah",
        "icon": "📖",
        "desc": "Full weekly Parashah digest, Hebrew Root, Table Riddle, Daf Yomi & Zmanim",
    },
    "event_notification": {
        "id": "event_notification",
        "label": "Event Notification",
        "icon": "🎉",
        "desc": "Upcoming Shul events, classes, Shabbatons & RSVP reminders",
    },
    "special_days": {
        "id": "special_days",
        "label": "Special Days & Rosh Chodesh",
        "icon": "🌙",
        "desc": "Rosh Chodesh watch, Lunar phase, Fast days & Community Dedications",
    },
    "holiday_chag": {
        "id": "holiday_chag",
        "label": "Holidays & Chagim Guide",
        "icon": "🕎",
        "desc": "Next upcoming Yom Tov / Chag schedule, candle times & celebration guide",
    },
    "custom_marketing": {
        "id": "custom_marketing",
        "label": "Custom Announcement / Promo",
        "icon": "📢",
        "desc": "Custom Rabbi message, Kiddush sponsorship drive, Kids Shul or Gala push",
    },
}

LANG_GREETINGS = {
    "en": {
        "shabbat_shalom": "Shabbat Shalom",
        "pre_shabbos_title": "Pre-Shabbos Times & Community Alert",
        "events_title": "Upcoming Events & Programs",
        "special_title": "Special Days, Rosh Chodesh & Community Notes",
        "holiday_title": "Upcoming Holiday & Chagim Guide",
        "candles": "Candle Lighting",
        "havdalah": "Shabbat Ends (Havdalah)",
        "cta_give": "Sponsor a Kiddush or Support the Shul",
        "warmly": "Warmly,",
    },
    "fr": {
        "shabbat_shalom": "Chabbat Chalom",
        "pre_shabbos_title": "Horaires de Chabbat & Message de la Communauté",
        "events_title": "Événements & Programmes à Venir",
        "special_title": "Roch Hodech, Dates Spéciales & Dédicaces",
        "holiday_title": "Guide des Fêtes & Horaires",
        "candles": "Allumage des bougies",
        "havdalah": "Fin de Chabbat (Havdala)",
        "cta_give": "Parrainer un Kiddouch ou Soutenir la Synagogue",
        "warmly": "Chaleureusement,",
    },
    "he": {
        "shabbat_shalom": "שבת שלום",
        "pre_shabbos_title": "זמני שבת והודעות הקהילה",
        "events_title": "אירועים ושיעורים קרובים",
        "special_title": "ראש חודש, ימים מיוחדים והקדשות",
        "holiday_title": "מדריך לחגים ומועדים קרובים",
        "candles": "הדלקת נרות",
        "havdalah": "צאת השבת (הבדלה)",
        "cta_give": "הקדישו קידוש או תמכו בבית הכנסת",
        "warmly": "בברכה,",
    },
}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_tables() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS campaign_sends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_type TEXT NOT NULL,
                lang TEXT NOT NULL DEFAULT 'en',
                subject TEXT NOT NULL,
                channels TEXT NOT NULL,
                provider TEXT NOT NULL,
                recipient_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                is_test INTEGER NOT NULL DEFAULT 0,
                schedule_key TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_campaign_schedule_key ON campaign_sends(schedule_key);
            """
        )


def is_shabbat_or_yomtov_now() -> Dict[str, Any]:
    """Halachic guard: returns True if right now falls inside Shabbat or Yom Tov."""
    try:
        snap = sacred_astronomy.get_sacred_moment()
        active = bool(snap.get("shabbat_mode") or snap.get("is_yom_tov_now"))
        return {"blocked": active, "reason": "Shabbat / Yom Tov stillness guard active — broadcasts pause until Havdalah." if active else ""}
    except Exception:
        return {"blocked": False, "reason": ""}


def _wrap_sanctuary_html(
    synagogue: str,
    rabbi: str,
    address: str,
    website: str,
    give_url: str,
    badge: str,
    headline: str,
    subheadline: str,
    body_blocks_html: str,
    cta_label: str,
    cta_url: str,
    lang: str = "en",
) -> str:
    direction = "rtl" if lang == "he" else "ltr"
    align = "right" if lang == "he" else "left"
    g = LANG_GREETINGS.get(lang, LANG_GREETINGS["en"])
    return f"""<!DOCTYPE html>
<html lang="{html.escape(lang)}" dir="{direction}">
<body style="margin:0;padding:0;background:#f4efe4;font-family:Georgia,'Times New Roman',serif;color:#1b2438;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4efe4;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="620" cellspacing="0" cellpadding="0" style="max-width:620px;width:100%;background:#ffffff;border:1px solid #d9c38c;border-radius:14px;overflow:hidden;">
        <tr>
          <td style="background:#0d162c;padding:26px 28px;border-bottom:3px solid #d4af37;text-align:center;">
            <div style="font-size:11px;letter-spacing:2.4px;text-transform:uppercase;color:#e6c773;font-family:Arial,sans-serif;font-weight:bold;">
              {html.escape(badge)}
            </div>
            <h1 style="margin:8px 0 4px;font-size:24px;color:#fff7e2;font-weight:normal;">
              {html.escape(headline)}
            </h1>
            <div style="font-size:14px;color:#d6c8a6;">
              {html.escape(subheadline)}
            </div>
          </td>
        </tr>
        <tr>
          <td style="padding:26px 28px;text-align:{align};line-height:1.65;font-size:15px;color:#222c40;">
            {body_blocks_html}
            <div style="text-align:center;margin:26px 0 10px;">
              <a href="{html.escape(cta_url)}" style="display:inline-block;background:#0d162c;color:#f0cf7b;border:1px solid #d4af37;text-decoration:none;padding:12px 24px;border-radius:8px;font-family:Arial,sans-serif;font-size:14px;font-weight:bold;">
                {html.escape(cta_label)}
              </a>
            </div>
          </td>
        </tr>
        <tr>
          <td style="background:#faf6ec;padding:18px 28px;border-top:1px solid #e6dcc4;text-align:center;font-family:Arial,sans-serif;font-size:12px;color:#5a6275;">
            <div style="margin-bottom:4px;">{html.escape(g['warmly'])} <strong>{html.escape(rabbi)}</strong> &middot; {html.escape(synagogue)}</div>
            <div>{html.escape(address)} &middot; <a href="{html.escape(website)}" style="color:#8b5e14;">{html.escape(website)}</a></div>
            <div style="margin-top:6px;"><a href="{html.escape(give_url)}" style="color:#8b5e14;">{html.escape(g['cta_give'])}</a></div>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def compose_campaign(
    campaign_type: str = "pre_shabbos",
    lang: str = "en",
    custom_title: str = "",
    custom_body: str = "",
    custom_cta_label: str = "",
    custom_cta_url: str = "",
) -> Dict[str, Any]:
    """Auto-compose a rich multi-channel synagogue campaign (HTML Email + Plain Text + WhatsApp + SMS + Push)."""
    ctype = campaign_type if campaign_type in CAMPAIGN_TYPES else "pre_shabbos"
    lang = lang if lang in ("en", "fr", "he") else "en"
    g = LANG_GREETINGS[lang]

    cfg = ai_engine.load_config()
    synagogue = (cfg.get("synagogue_name") or shul_events.SHUL_INFO["name"]).strip()
    rabbi = (cfg.get("rabbi_name") or shul_events.SHUL_INFO["rabbi"]).strip()
    address = (cfg.get("shul_address") or shul_events.SHUL_INFO["address"]).strip()
    website = (cfg.get("shul_website") or shul_events.SHUL_INFO["website"]).strip()
    give_url = (cfg.get("donation_checkout_url") or website).strip()
    city = ((cfg.get("location") or {}).get("city") or "Brussels").split(",")[0]

    daily = torah_db.get_daily_portion()
    p = daily["parasha"]
    ev_bundle = shul_events.list_events()
    events = ev_bundle.get("events", [])[:8]
    sh = ev_bundle.get("shabbat_times", {})
    offline_cel = shul_events._compute_offline_shabbat_zmanim()

    candle_val = sh.get("candle_lighting") or offline_cel.get("candle_lighting") or "Check local zmanim"
    havdalah_val = sh.get("havdalah") or offline_cel.get("havdalah") or "Check local zmanim"
    friday_date = offline_cel.get("friday_date") or ""
    hdate = sh.get("hebrew_date") or offline_cel.get("hebrew_date") or ""
    holidays = offline_cel.get("upcoming_holidays") or []
    next_rc = offline_cel.get("next_rosh_chodesh") or {}
    moon = offline_cel.get("moon") or {}

    if ctype == "weekly_prep":
        base = shul_events.generate_weekly_mailing()
        subject = custom_title.strip() or base["subject"]
        html_body = base["html"]
        plain_text = base["plain_text"]
        whatsapp_text = (
            f"📖 *{g['shabbat_shalom']} — Parashat {p['en_name']} ({p['he_name']})*\n"
            f"_{synagogue}_\n\n"
            f"🕯 *{g['candles']} ({city}):* {candle_val}\n"
            f"✨ *{g['havdalah']}:* {havdalah_val}\n"
            f"📜 *Torah:* {p['ref']} | *Haftarah:* {p['haftarah']}\n\n"
            f"{p['summary']}\n\n"
            f"💛 {g['cta_give']}: {give_url}"
        )
        sms_text = f"{synagogue}: Weekly Prep for Parashat {p['en_name']}. {g['candles']} {candle_val}, Havdalah {havdalah_val}. {website}"
        push_title = f"Weekly Prep · Parashat {p['en_name']}"
        push_body = f"{g['candles']} ({city}): {candle_val} · Havdalah: {havdalah_val} · {p['ref']}"

    elif ctype == "pre_shabbos":
        subject = custom_title.strip() or f"🕯️ {g['shabbat_shalom']} — Parashat {p['en_name']} ({p['he_name']}) · {g['candles']} {candle_val}"
        ev_rows = "".join(
            f"<li style='margin:6px 0;'><strong>{html.escape(e['title'])}</strong> — {html.escape(e['event_date'])} {html.escape(e['event_time'])} ({html.escape(e.get('location',''))})</li>"
            for e in events[:4]
        )
        body_html = f"""
        <div style="background:#0d162c;color:#fff6df;padding:16px 18px;border-radius:10px;border:1px solid #d4af37;margin-bottom:18px;">
          <div style="font-size:13px;color:#e6c773;text-transform:uppercase;letter-spacing:1.4px;font-family:Arial,sans-serif;">{html.escape(city)} &middot; {html.escape(friday_date)} &middot; {html.escape(hdate)}</div>
          <div style="font-size:18px;margin-top:6px;">🕯️ <strong>{html.escape(g['candles'])}:</strong> {html.escape(candle_val)} &nbsp;&nbsp;|&nbsp;&nbsp; ✨ <strong>{html.escape(g['havdalah'])}:</strong> {html.escape(havdalah_val)}</div>
        </div>
        <h2 style="color:#0d162c;font-size:18px;margin:0 0 8px;">Parashat {html.escape(p['en_name'])} ({html.escape(p['he_name'])})</h2>
        <div style="font-size:13px;color:#8b5e14;margin-bottom:10px;">{html.escape(p['ref'])} &middot; Haftarah: {html.escape(p['haftarah'])}</div>
        <p style="margin:0 0 14px;">{html.escape(custom_body.strip() or p['summary'])}</p>
        {"<h3 style='color:#0d162c;font-size:15px;margin:16px 0 6px;'>Shabbat &amp; Weekend Schedule</h3><ul style='padding-left:20px;margin:0;'>" + ev_rows + "</ul>" if ev_rows else ""}
        """
        html_body = _wrap_sanctuary_html(
            synagogue, rabbi, address, website, give_url,
            f"PRE-SHABBOS ALERT · {city.upper()}",
            f"{g['shabbat_shalom']} — Parashat {p['en_name']}",
            f"{g['candles']}: {candle_val} · {g['havdalah']}: {havdalah_val}",
            body_html,
            custom_cta_label.strip() or g["cta_give"],
            custom_cta_url.strip() or give_url,
            lang=lang,
        )
        plain_text = (
            f"{g['shabbat_shalom']} from {synagogue}!\n"
            f"Parashat {p['en_name']} ({p['he_name']}) — {p['ref']}\n"
            f"{g['candles']} ({city}, {friday_date}): {candle_val}\n"
            f"{g['havdalah']}: {havdalah_val}\n\n"
            f"{custom_body.strip() or p['summary']}\n\n"
            f"Support / Sponsor Kiddush: {custom_cta_url.strip() or give_url}\n"
            f"{g['warmly']} {rabbi}"
        )
        whatsapp_text = (
            f"🕯️ *{g['shabbat_shalom']} — Parashat {p['en_name']} ({p['he_name']})*\n"
            f"_{synagogue}_\n\n"
            f"🕯 *{g['candles']} ({city}):* {candle_val}\n"
            f"✨ *{g['havdalah']}:* {havdalah_val}\n\n"
            f"{custom_body.strip() or p['summary']}\n\n"
            f"💛 {custom_cta_label.strip() or g['cta_give']}: {custom_cta_url.strip() or give_url}"
        )
        sms_text = f"{g['shabbat_shalom']}! {synagogue} — Parashat {p['en_name']}. {g['candles']} {candle_val}, Havdalah {havdalah_val}. {give_url}"
        push_title = f"🕯️ {g['shabbat_shalom']} · {g['candles']} {candle_val}"
        push_body = f"Parashat {p['en_name']} ({city}) · Havdalah {havdalah_val}"

    elif ctype == "event_notification":
        spotlight = events[0] if events else {"title": "Community Shabbat & Torah Learning", "event_date": friday_date, "event_time": "10:00", "location": address, "description": "Join us at the Synagogue."}
        subject = custom_title.strip() or f"🎉 {g['events_title']}: {spotlight['title']} · {synagogue}"
        ev_cards = "".join(
            f"""<div style="border:1px solid #e5d8bc;border-radius:10px;padding:14px 16px;margin-bottom:12px;background:#fcfaf4;">
              <div style="font-size:16px;font-weight:bold;color:#0d162c;">{html.escape(e['title'])}</div>
              <div style="font-size:13px;color:#8b5e14;margin:4px 0;">📅 {html.escape(e['event_date'])} {html.escape(e['event_time'])} &middot; 📍 {html.escape(e.get('location') or address)}</div>
              <div style="font-size:14px;color:#333;">{html.escape(e.get('description',''))}</div>
            </div>"""
            for e in events[:6]
        )
        intro = f"<p style='margin:0 0 16px;'>{html.escape(custom_body.strip())}</p>" if custom_body.strip() else f"<p style='margin:0 0 16px;'>Join <strong>{html.escape(rabbi)}</strong> and our community for upcoming events, classes, and celebrations:</p>"
        html_body = _wrap_sanctuary_html(
            synagogue, rabbi, address, website, give_url,
            "COMMUNITY EVENT NOTIFICATION",
            custom_title.strip() or g["events_title"],
            f"{synagogue} · {city}",
            intro + ev_cards,
            custom_cta_label.strip() or "RSVP & View Full Calendar",
            custom_cta_url.strip() or website,
            lang=lang,
        )
        ev_lines = "\n".join(f"• {e['title']} — {e['event_date']} {e['event_time']} ({e.get('location') or address})" for e in events[:6])
        plain_text = f"{subject}\n\n{custom_body.strip()}\n\n{ev_lines}\n\nRSVP: {custom_cta_url.strip() or website}\n{g['warmly']} {rabbi}"
        whatsapp_text = f"🎉 *{custom_title.strip() or g['events_title']} — {synagogue}*\n\n{ev_lines}\n\n🔗 RSVP: {custom_cta_url.strip() or website}"
        sms_text = f"{synagogue} Event Alert: {spotlight['title']} ({spotlight['event_date']} {spotlight['event_time']}). RSVP: {custom_cta_url.strip() or website}"
        push_title = f"🎉 {spotlight['title']}"
        push_body = f"{spotlight['event_date']} {spotlight['event_time']} · {spotlight.get('location') or city}"

    elif ctype == "special_days":
        rc_name = next_rc.get("month_en") or "Upcoming Month"
        rc_date = next_rc.get("gregorian_date") or ""
        rc_days = next_rc.get("days_away", "")
        dedications = community_hub.list_dedications()[:5] if hasattr(community_hub, "list_dedications") else []
        subject = custom_title.strip() or f"🌙 {g['special_title']} — Rosh Chodesh {rc_name} ({rc_date}) · {synagogue}"
        ded_html = "".join(
            f"<li style='margin:5px 0;'><strong>{html.escape(str(d.get('kind','Dedication')).title())}:</strong> {html.escape(d.get('honoree',''))} — {html.escape(d.get('message',''))}</li>"
            for d in dedications
        )
        body_html = f"""
        <div style="background:#101c38;color:#fff6df;padding:16px 18px;border-radius:10px;border:1px solid #d4af37;margin-bottom:16px;">
          <div style="font-size:12px;color:#e6c773;text-transform:uppercase;letter-spacing:1.5px;font-family:Arial,sans-serif;">LUNAR &amp; HEBREW CALENDAR WATCH</div>
          <div style="font-size:18px;margin-top:6px;">🌙 <strong>Next Rosh Chodesh:</strong> {html.escape(rc_name)} — {html.escape(rc_date)} (in {html.escape(str(rc_days))} days)</div>
          <div style="font-size:13px;color:#d6c8a6;margin-top:4px;">Current Moon Phase: {html.escape(str(moon.get('phase_en','')))} ({html.escape(str(moon.get('illumination_pct','')))}% illuminated) &middot; {html.escape(hdate)}</div>
        </div>
        {f"<p>{html.escape(custom_body.strip())}</p>" if custom_body.strip() else "<p>As we prepare for the new Hebrew month, we invite you to mark Rosh Chodesh, upcoming Yahrzeits, and family simchas with our community.</p>"}
        {"<h3 style='color:#0d162c;font-size:15px;margin:16px 0 6px;'>Active Community Dedications &amp; Yahrzeits</h3><ul style='padding-left:20px;'>" + ded_html + "</ul>" if ded_html else ""}
        """
        html_body = _wrap_sanctuary_html(
            synagogue, rabbi, address, website, give_url,
            "SPECIAL DAYS & ROSH CHODESH",
            custom_title.strip() or f"Rosh Chodesh {rc_name} & Special Days",
            f"{hdate} · {synagogue}",
            body_html,
            custom_cta_label.strip() or "Dedicate a Day of Learning or Yahrzeit",
            custom_cta_url.strip() or give_url,
            lang=lang,
        )
        plain_text = f"{subject}\n\nNext Rosh Chodesh: {rc_name} ({rc_date}, in {rc_days} days).\nHebrew Date: {hdate}.\n{custom_body.strip()}\nDedications: {custom_cta_url.strip() or give_url}"
        whatsapp_text = f"🌙 *Chodesh Tov & Special Days — {synagogue}*\nNext Rosh Chodesh: *{rc_name}* ({rc_date}, in {rc_days} days)\n{custom_body.strip()}\n🕯 Dedicate a Day of Learning: {custom_cta_url.strip() or give_url}"
        sms_text = f"{synagogue}: Rosh Chodesh {rc_name} arrives {rc_date} (in {rc_days}d). Dedications & times: {give_url}"
        push_title = f"🌙 Rosh Chodesh {rc_name} ({rc_date})"
        push_body = f"In {rc_days} days · {hdate} · {synagogue}"

    elif ctype == "holiday_chag":
        next_hol = holidays[0] if holidays else {"name": "Upcoming Yom Tov", "he": "חג שמח", "gregorian_date": "", "days_away": ""}
        subject = custom_title.strip() or f"🕎 {next_hol['name']} ({next_hol.get('he','')}) Guide & Times · {synagogue}"
        hol_list_html = "".join(
            f"<li style='margin:6px 0;'><strong>{html.escape(h['name'])}</strong> ({html.escape(h.get('he',''))}) — {html.escape(h['gregorian_date'])} <em>(in {h['days_away']} days)</em></li>"
            for h in holidays[:6]
        )
        body_html = f"""
        <div style="background:#0d162c;color:#fff6df;padding:18px;border-radius:10px;border:1px solid #d4af37;margin-bottom:16px;">
          <div style="font-size:12px;color:#e6c773;text-transform:uppercase;letter-spacing:1.6px;font-family:Arial,sans-serif;">CHAGIM &amp; HOLIDAY COUNTDOWN</div>
          <div style="font-size:21px;margin-top:6px;">🕎 <strong>{html.escape(next_hol['name'])}</strong> ({html.escape(next_hol.get('he',''))})</div>
          <div style="font-size:14px;color:#e6d8b5;margin-top:4px;">Begins {html.escape(next_hol.get('gregorian_date',''))} &middot; {html.escape(str(next_hol.get('days_away','')))} days away</div>
        </div>
        <p style="margin:0 0 14px;">{html.escape(custom_body.strip() or f'Prepare your home and family to celebrate {next_hol["name"]} together at {synagogue}. Below are our upcoming calendar highlights and holiday milestones.')}</p>
        {"<h3 style='color:#0d162c;font-size:15px;margin:14px 0 6px;'>Upcoming Jewish Holidays</h3><ul style='padding-left:20px;'>" + hol_list_html + "</ul>" if hol_list_html else ""}
        """
        html_body = _wrap_sanctuary_html(
            synagogue, rabbi, address, website, give_url,
            "HOLIDAYS & CHAGIM GUIDE",
            custom_title.strip() or f"Preparing for {next_hol['name']}",
            f"{next_hol.get('gregorian_date','')} · {synagogue}",
            body_html,
            custom_cta_label.strip() or f"RSVP & Holiday Schedule",
            custom_cta_url.strip() or website,
            lang=lang,
        )
        plain_text = f"{subject}\n\n{next_hol['name']} ({next_hol.get('he','')}) arrives {next_hol.get('gregorian_date','')} (in {next_hol.get('days_away','')} days).\n\n{custom_body.strip()}\nFull Holiday Guide: {custom_cta_url.strip() or website}"
        whatsapp_text = f"🕎 *Chag Sameach Prep — {next_hol['name']} ({next_hol.get('he','')})*\n📅 {next_hol.get('gregorian_date','')} ({next_hol.get('days_away','')} days away)\n_{synagogue}_\n\n{custom_body.strip()}\n🔗 RSVP & Times: {custom_cta_url.strip() or website}"
        sms_text = f"{synagogue}: {next_hol['name']} starts {next_hol.get('gregorian_date','')} (in {next_hol.get('days_away','')}d). Schedule & RSVP: {website}"
        push_title = f"🕎 {next_hol['name']} in {next_hol.get('days_away','')} days"
        push_body = f"{next_hol.get('gregorian_date','')} · {synagogue}"

    else:  # custom_marketing
        headline = custom_title.strip() or f"Special Message from {rabbi}"
        msg_body = custom_body.strip() or f"We look forward to welcoming you and your family to {synagogue} this week! Click below to RSVP, join our upcoming programs, or sponsor a Kiddush."
        cta_lbl = custom_cta_label.strip() or g["cta_give"]
        cta_u = custom_cta_url.strip() or give_url
        subject = f"📣 {headline} · {synagogue}"
        paragraphs = "".join(f"<p style='margin:0 0 12px;'>{html.escape(para)}</p>" for para in msg_body.splitlines() if para.strip())
        html_body = _wrap_sanctuary_html(
            synagogue, rabbi, address, website, give_url,
            "COMMUNITY ANNOUNCEMENT",
            headline,
            f"{synagogue} · {hdate}",
            paragraphs,
            cta_lbl,
            cta_u,
            lang=lang,
        )
        plain_text = f"{headline}\n{synagogue}\n\n{msg_body}\n\n{cta_lbl}: {cta_u}\n{g['warmly']} {rabbi}"
        whatsapp_text = f"📣 *{headline}*\n_{synagogue}_\n\n{msg_body}\n\n🔗 {cta_lbl}: {cta_u}"
        sms_text = f"{synagogue}: {headline} — {msg_body[:160]} {cta_u}"
        push_title = f"📣 {headline}"
        push_body = msg_body[:180]

    subs = shul_events.list_subscribers()
    return {
        "campaign_type": ctype,
        "campaign_meta": CAMPAIGN_TYPES[ctype],
        "lang": lang,
        "subject": subject,
        "html": html_body,
        "plain_text": plain_text,
        "whatsapp_text": whatsapp_text,
        "whatsapp_url": "https://wa.me/?text=" + urllib.parse.quote(whatsapp_text),
        "sms_text": sms_text,
        "push_title": push_title,
        "push_body": push_body,
        "subscribers_count": len(subs),
        "shabbat_guard": is_shabbat_or_yomtov_now(),
    }


def _send_email_resend(cfg: dict, recipients: List[str], subject: str, html_body: str, plain_text: str) -> Dict[str, Any]:
    api_key = (cfg.get("mailing_api_key") or "").strip()
    sender = (cfg.get("mailing_from_email") or "").strip()
    from_name = (cfg.get("mailing_from_name") or cfg.get("synagogue_name") or "Shul.OS").strip()
    if not api_key or not sender:
        return {"ok": False, "detail": "Resend requires Mailing API Key and From Email in Settings."}
    sent = 0
    errors = []
    for rcpt in recipients:
        payload = {
            "from": f"{from_name} <{sender}>",
            "to": [rcpt],
            "subject": subject,
            "html": html_body,
            "text": plain_text,
        }
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "Shul.OS/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as r:
                if 200 <= r.status < 300:
                    sent += 1
        except Exception as e:
            errors.append(f"{rcpt}: {e}")
    return {"ok": sent > 0 and not errors, "sent": sent, "detail": f"Resend delivered to {sent}/{len(recipients)} recipient(s)." + (f" Errors: {'; '.join(errors[:3])}" if errors else "")}


def _send_email_mailgun(cfg: dict, recipients: List[str], subject: str, html_body: str, plain_text: str) -> Dict[str, Any]:
    api_key = (cfg.get("mailing_api_key") or "").strip()
    domain = (cfg.get("mailing_domain") or "").strip()
    sender = (cfg.get("mailing_from_email") or "").strip()
    from_name = (cfg.get("mailing_from_name") or cfg.get("synagogue_name") or "Shul.OS").strip()
    if not api_key or not domain or not sender:
        return {"ok": False, "detail": "Mailgun requires API Key, Mailgun Domain, and From Email in Settings."}
    auth = base64.b64encode(f"api:{api_key}".encode("utf-8")).decode("ascii")
    sent = 0
    errors = []
    for rcpt in recipients:
        form = urllib.parse.urlencode({
            "from": f"{from_name} <{sender}>",
            "to": rcpt,
            "subject": subject,
            "text": plain_text,
            "html": html_body,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.mailgun.net/v3/{domain}/messages",
            data=form,
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as r:
                if 200 <= r.status < 300:
                    sent += 1
        except Exception as e:
            errors.append(f"{rcpt}: {e}")
    return {"ok": sent > 0 and not errors, "sent": sent, "detail": f"Mailgun delivered to {sent}/{len(recipients)} recipient(s)." + (f" Errors: {'; '.join(errors[:3])}" if errors else "")}


def _send_email_brevo(cfg: dict, recipients: List[str], subject: str, html_body: str, plain_text: str) -> Dict[str, Any]:
    api_key = (cfg.get("mailing_api_key") or "").strip()
    sender = (cfg.get("mailing_from_email") or "").strip()
    from_name = (cfg.get("mailing_from_name") or cfg.get("synagogue_name") or "Shul.OS").strip()
    if not api_key or not sender:
        return {"ok": False, "detail": "Brevo requires API Key and From Email in Settings."}
    sent = 0
    errors = []
    for rcpt in recipients:
        payload = {
            "sender": {"name": from_name, "email": sender},
            "to": [{"email": rcpt}],
            "subject": subject,
            "htmlContent": html_body,
            "textContent": plain_text,
        }
        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload).encode("utf-8"),
            headers={"api-key": api_key, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as r:
                if 200 <= r.status < 300:
                    sent += 1
        except Exception as e:
            errors.append(f"{rcpt}: {e}")
    return {"ok": sent > 0 and not errors, "sent": sent, "detail": f"Brevo delivered to {sent}/{len(recipients)} recipient(s)." + (f" Errors: {'; '.join(errors[:3])}" if errors else "")}


def _send_email_smtp(cfg: dict, recipients: List[str], subject: str, html_body: str, plain_text: str) -> Dict[str, Any]:
    host = (cfg.get("smtp_host") or "").strip()
    port = int(cfg.get("smtp_port") or 587)
    user = (cfg.get("smtp_user") or "").strip()
    pwd = (cfg.get("smtp_password") or "").strip()
    sender = (cfg.get("mailing_from_email") or user).strip()
    from_name = (cfg.get("mailing_from_name") or cfg.get("synagogue_name") or "Shul.OS").strip()
    if not host or not sender:
        return {"ok": False, "detail": "SMTP requires SMTP Host and From Email in Settings."}
    sent = 0
    try:
        ctx = ssl.create_default_context()
        if port == 465:
            srv = smtplib.SMTP_SSL(host, port, timeout=15, context=ctx)
        else:
            srv = smtplib.SMTP(host, port, timeout=15)
            srv.ehlo()
            if srv.has_extn("starttls"):
                srv.starttls(context=ctx)
        if user and pwd:
            srv.login(user, pwd)
        for rcpt in recipients:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{sender}>"
            msg["To"] = rcpt
            msg.attach(MIMEText(plain_text, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))
            srv.sendmail(sender, [rcpt], msg.as_string())
            sent += 1
        srv.quit()
        return {"ok": True, "sent": sent, "detail": f"SMTP ({host}:{port}) delivered to {sent} recipient(s)."}
    except Exception as e:
        return {"ok": False, "sent": sent, "detail": f"SMTP delivery failed: {e}"}


def _send_mobile_push(cfg: dict, title: str, body: str, click_url: str) -> Dict[str, Any]:
    push_url = (cfg.get("push_channel_url") or "").strip()
    if not push_url:
        return {"ok": False, "skipped": True, "detail": "No Mobile Push URL (ntfy.sh / Push webhook) configured."}
    try:
        if "ntfy.sh/" in push_url or "/ntfy/" in push_url:
            req = urllib.request.Request(
                push_url,
                data=body.encode("utf-8"),
                headers={
                    "Title": title.encode("ascii", "ignore").decode("ascii") or "Shul.OS Alert",
                    "Click": click_url,
                    "Tags": "star_of_david",
                },
            )
        else:
            req = urllib.request.Request(
                push_url,
                data=json.dumps({"title": title, "message": body, "url": click_url, "source": "Shul.OS"}).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "Shul.OS/1.0"},
            )
        with urllib.request.urlopen(req, timeout=10) as r:
            return {"ok": 200 <= r.status < 300, "detail": f"Push notification delivered (HTTP {r.status})."}
    except Exception as e:
        return {"ok": False, "detail": f"Push notification error: {e}"}


def dispatch_campaign(
    campaign_type: str = "pre_shabbos",
    lang: str = "en",
    channels: Optional[List[str]] = None,
    test_email: str = "",
    custom_title: str = "",
    custom_body: str = "",
    custom_cta_label: str = "",
    custom_cta_url: str = "",
    schedule_key: str = "",
    force_ignore_shabbat: bool = False,
) -> Dict[str, Any]:
    """Send or test-send a composed campaign across selected channels with Shabbat Guard & full audit log."""
    init_tables()
    cfg = ai_engine.load_config()
    guard = is_shabbat_or_yomtov_now()
    if cfg.get("shabbat_send_guard", True) and guard["blocked"] and not force_ignore_shabbat:
        return {
            "ok": False,
            "blocked_by_shabbat": True,
            "status": "paused_shabbat",
            "detail": guard["reason"],
        }

    pack = compose_campaign(
        campaign_type=campaign_type,
        lang=lang,
        custom_title=custom_title,
        custom_body=custom_body,
        custom_cta_label=custom_cta_label,
        custom_cta_url=custom_cta_url,
    )
    selected = channels or ["email", "webhook", "push"]
    provider = (cfg.get("mailing_provider") or "webhook").strip().lower()
    is_test = bool(test_email.strip())

    if is_test:
        recipients = [test_email.strip()]
    else:
        recipients = [s["email"] for s in shul_events.list_subscribers() if s.get("email")]
        # Optional default rabbi/test address fallback if list is empty
        fallback_rcpt = (cfg.get("mailing_test_email") or "").strip()
        if not recipients and fallback_rcpt:
            recipients = [fallback_rcpt]

    results: Dict[str, Any] = {}
    delivered_count = 0
    overall_ok = False
    details: List[str] = []

    if "email" in selected:
        if provider == "resend":
            r = _send_email_resend(cfg, recipients, pack["subject"], pack["html"], pack["plain_text"])
        elif provider == "mailgun":
            r = _send_email_mailgun(cfg, recipients, pack["subject"], pack["html"], pack["plain_text"])
        elif provider == "brevo":
            r = _send_email_brevo(cfg, recipients, pack["subject"], pack["html"], pack["plain_text"])
        elif provider == "smtp":
            r = _send_email_smtp(cfg, recipients, pack["subject"], pack["html"], pack["plain_text"])
        else:
            r = {"ok": False, "sent": 0, "detail": f"Email provider is set to '{provider}' (uses Webhook channel)."}
        results["email"] = r
        delivered_count = max(delivered_count, int(r.get("sent") or 0))
        if r.get("ok"):
            overall_ok = True
        details.append(r["detail"])

    if "webhook" in selected:
        hook = (cfg.get("syndication_webhook_url") or cfg.get("mailing_webhook_url") or "").strip()
        if hook:
            try:
                payload = {
                    "type": "shul_os_campaign_broadcast",
                    "campaign_type": pack["campaign_type"],
                    "lang": lang,
                    "is_test": is_test,
                    "recipients": recipients,
                    "subject": pack["subject"],
                    "html": pack["html"],
                    "plain_text": pack["plain_text"],
                    "whatsapp_text": pack["whatsapp_text"],
                    "sms_text": pack["sms_text"],
                    "push_title": pack["push_title"],
                    "push_body": pack["push_body"],
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
                req = urllib.request.Request(
                    hook,
                    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "Shul.OS/1.0"},
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    code = resp.status
                results["webhook"] = {"ok": True, "http_status": code}
                delivered_count = max(delivered_count, len(recipients))
                overall_ok = True
                details.append(f"Broadcast webhook delivered (HTTP {code}).")
            except Exception as e:
                results["webhook"] = {"ok": False, "error": str(e)}
                details.append(f"Webhook error: {e}")
        else:
            results["webhook"] = {"ok": False, "skipped": True}
            if provider == "webhook":
                details.append("No Mailing/Syndication Webhook URL configured in Settings yet (copy-ready HTML/WhatsApp/SMS prepared).")

    if "push" in selected:
        click_u = custom_cta_url.strip() or (cfg.get("public_sanctuary_url") or cfg.get("shul_website") or "https://www.theshul.eu").strip()
        pr = _send_mobile_push(cfg, pack["push_title"], pack["push_body"], click_u)
        results["push"] = pr
        if pr.get("ok"):
            overall_ok = True
        if not pr.get("skipped"):
            details.append(pr["detail"])

    status = "sent" if overall_ok else "composed_only"
    summary_detail = " | ".join(details) if details else "Campaign composed cleanly."

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO campaign_sends (campaign_type, lang, subject, channels, provider, recipient_count, status, detail, is_test, schedule_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pack["campaign_type"],
                lang,
                pack["subject"],
                ", ".join(selected),
                provider,
                delivered_count or len(recipients),
                status,
                summary_detail,
                1 if is_test else 0,
                schedule_key,
            ),
        )
        conn.commit()

    return {
        "ok": overall_ok or status == "composed_only",
        "delivered": overall_ok,
        "status": status,
        "provider": provider,
        "recipient_count": delivered_count or len(recipients),
        "subject": pack["subject"],
        "detail": summary_detail,
        "results": results,
        "whatsapp_url": pack["whatsapp_url"],
    }


def list_campaign_history(limit: int = 15) -> List[Dict[str, Any]]:
    init_tables()
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM campaign_sends ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def _already_sent_schedule(schedule_key: str) -> bool:
    init_tables()
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM campaign_sends WHERE schedule_key=? LIMIT 1", (schedule_key,)).fetchone()
        return row is not None


def run_scheduled_automations() -> Dict[str, Any]:
    """Called periodically by sacred-os-daemon.py. Checks enabled auto-push toggles and fires Shabbat-safe broadcasts."""
    init_tables()
    cfg = ai_engine.load_config()
    guard = is_shabbat_or_yomtov_now()
    if cfg.get("shabbat_send_guard", True) and guard["blocked"]:
        return {"ran": [], "skipped": "shabbat_guard"}

    # Only run automations if at least one delivery target is actually configured
    has_delivery = bool(
        (cfg.get("mailing_provider") in ("resend", "mailgun", "brevo") and cfg.get("mailing_api_key"))
        or (cfg.get("mailing_provider") == "smtp" and cfg.get("smtp_host"))
        or (cfg.get("mailing_webhook_url") or cfg.get("syndication_webhook_url") or cfg.get("push_channel_url"))
    )
    if not has_delivery:
        return {"ran": [], "skipped": "no_delivery_provider_configured"}

    now = datetime.datetime.now()
    today_str = now.date().isoformat()
    wd = now.weekday()  # Mon=0 .. Fri=4, Sat=5, Sun=6
    hour = now.hour
    lang = (cfg.get("auto_broadcast_lang") or "en").strip().lower()
    ran = []

    # 1. Pre-Shabbos Alert: Friday between 09:00 and 12:59 (well before candle lighting!)
    if cfg.get("auto_pre_shabbos") and wd == 4 and 9 <= hour < 13:
        key = f"pre_shabbos:{today_str}"
        if not _already_sent_schedule(key):
            res = dispatch_campaign("pre_shabbos", lang=lang, schedule_key=key)
            ran.append({"rule": "auto_pre_shabbos", "key": key, "status": res.get("status")})

    # 2. Weekly Prep & Parashah Digest: Wednesday between 09:00 and 12:59
    if cfg.get("auto_weekly_prep") and wd == 2 and 9 <= hour < 13:
        key = f"weekly_prep:{today_str}"
        if not _already_sent_schedule(key):
            res = dispatch_campaign("weekly_prep", lang=lang, schedule_key=key)
            ran.append({"rule": "auto_weekly_prep", "key": key, "status": res.get("status")})

    # 3. Holidays & Chagim Alert: 3 days before next upcoming Jewish Holiday (morning 09:00..12:59)
    if cfg.get("auto_holiday_alert") and 9 <= hour < 13:
        cel = shul_events._compute_offline_shabbat_zmanim()
        for h in (cel.get("upcoming_holidays") or [])[:3]:
            if h.get("days_away") == 3:
                key = f"holiday:{h['name']}:{h['gregorian_date']}"
                if not _already_sent_schedule(key):
                    res = dispatch_campaign("holiday_chag", lang=lang, schedule_key=key)
                    ran.append({"rule": "auto_holiday_alert", "key": key, "status": res.get("status")})
                break

    # 4. Special Days / Rosh Chodesh Alert: 1 day before Rosh Chodesh (morning 09:00..12:59)
    if cfg.get("auto_special_days") and 9 <= hour < 13:
        cel = shul_events._compute_offline_shabbat_zmanim()
        nrc = cel.get("next_rosh_chodesh") or {}
        if nrc.get("days_away") == 1:
            key = f"rosh_chodesh:{nrc.get('month_en')}:{nrc.get('gregorian_date')}"
            if not _already_sent_schedule(key):
                res = dispatch_campaign("special_days", lang=lang, schedule_key=key)
                ran.append({"rule": "auto_special_days", "key": key, "status": res.get("status")})

    # 5. Event Reminder: 1 day before any dated Shul event (morning 09:00..12:59)
    if cfg.get("auto_event_reminder") and 9 <= hour < 13:
        tomorrow_str = (now.date() + datetime.timedelta(days=1)).isoformat()
        ev_bundle = shul_events.list_events()
        upcoming_tomorrow = [e for e in ev_bundle.get("events", []) if str(e.get("event_date", "")).startswith(tomorrow_str)]
        if upcoming_tomorrow:
            key = f"event_reminder:{tomorrow_str}"
            if not _already_sent_schedule(key):
                res = dispatch_campaign("event_notification", lang=lang, schedule_key=key)
                ran.append({"rule": "auto_event_reminder", "key": key, "status": res.get("status")})

    return {"ran": ran, "checked_at": now.isoformat(timespec="seconds")}
