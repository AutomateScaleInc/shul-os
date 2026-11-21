# ✡ Torah Sanctuary OS

**An open-source, 100% offline-capable Sacred Operating Framework for Synagogues, Batei Midrash, Jewish Schools, and Homes.**

Turn any Linux or [Omarchy](https://omarchy.org) computer (even a donated 2012–2019 iMac or mini PC) into a living Torah & Tanakh sanctuary synchronized from the ground up with the **exact Jewish calendar, real-time Sun & Moon astronomy, Halachic Zmanim, weekly Parashah, classical commentaries, illuminated art, and warm local voice AI.**

---

## ✨ What Makes It Holy From the Ground Up

| Layer | Capabilities |
|---|---|
| **🌙 100% Offline Astronomical Engine** (`sacred_astronomy.py`) | Pure-Python NOAA/Meeus Solar & Lunar Ephemeris + Dershowitz–Reingold Hebrew Calendar. Real-time Sun altitude & azimuth, Moon illumination %, phase angle, lunar age (`29.53d`), Moonrise/Moonset, topocentric elevation, **Kiddush Levana** window, **Rosh Chodesh** countdown, **Mizrach** bearing to Jerusalem, all 14 GRA/MGA **Halachic Zmanim**, halachic sunset rollover, **Four Tekufot**, **Sefirat HaOmer** + daily Sefirah, **Chanukah** nights, and active **Tefillah** inserts (*Mashiv HaRuach*, *V'ten Tal uMatar*, *Ya'aleh V'Yavo*). |
| **🖥 Living Holy OS Layer** (`sacred-os-daemon.py`) | Synchronizes the operating system itself with the Jewish day: gently shifts Wayland/Hyprland monitor warmth via `hyprsunset` (`6200K` Shacharit → `4700K` Plag HaMincha → `4000K` Bein HaShmashot → `3700K` Maariv), honors **Shabbat & Yom Tov Sanctuary Stillness** automatically from Candle Lighting to Havdalah, publishes `/run/user/$UID/torah-sanctuary-state.json`, and greets every terminal via `torah-motd`. |
| **📜 Complete Offline Corpus** (`data/torah.db`) | All **39 books of the Tanakh / Old Testament** (`23,206` verses in nikud Hebrew + English), **`21,344` classical commentaries** (Rashi, Ramban, Ibn Ezra, Sforno, Pirkei Avot, Bereishit & Shemot Rabbah), all **54 weekly Parashiyot** with daily 7-Aliyah rotation, and 22 curated story & historical dossiers — searchable instantly via SQLite FTS5 with zero internet. |
| **🎨 Illuminated Art, Characters, Symbols & Rabbi Presentations** | 12 Orthodox-respectful illuminated Torah oil paintings, 12 Main Characters gallery, 12 Sacred Jewish Symbols SVG atlas, *"Applying It in Today's Terms"* takeaways on every story, and a full-screen **7-Slide Cinematic Presentation Mode** (`🎬 Present`, keyboard `←/→/Space/Esc`, Auto-Play, warm baritone narration). |
| **🎙 100% Local Voice AI & Scholarly Q&A** | Grounded RAG answers via local **Ollama** (`qwen2.5:1.5b` / `3b`) + optional cloud upgrade, warm natural baritone offline **Piper TTS** (`en_US-ryan-high`), and offline Whisper STT (`voxtype`). |
| **📅 Synagogue Calendar & Weekly Mailings** | Syncs any synagogue `.ics` feed + local events + kiosk mailing list signups + 1-click HTML/Text weekly newsletter composer. |

---

## 🚀 1-Command Install (Any Linux / Omarchy Machine)

```bash
git clone https://github.com/YOUR-ORG/torah-sanctuary-os.git
cd torah-sanctuary-os
./install.sh --synagogue "The European Synagogue · Torah Sanctuary" --city brussels
```

Available built-in city presets: `brussels`, `antwerp`, `jerusalem`, `tel_aviv`, `london`, `paris`, `new_york`, `miami`, `los_angeles` (or set any custom latitude, longitude, and timezone in **Settings**).

---

## 🔁 1-Command Clone to Another Node

Already running Torah Sanctuary OS on one machine? Clone it (including the pre-built 69 MB offline corpus and all 12 illuminated paintings) onto a new computer in one command:

```bash
./scripts/clone-to-node.sh user@new-imac --synagogue "Congregation Ohel Eliezer" --city brussels
```

Before donating a computer to a synagogue, run the privacy handoff sanitizer:

```bash
./scripts/sanitize-for-synagogue.sh
```

---

## 🔌 Open OS Integration

- **Web & Kiosk UI**: `http://127.0.0.1:8080`
- **Live Astronomical JSON API**: `GET /api/celestial`
- **System-Wide State File**: `$XDG_RUNTIME_DIR/torah-sanctuary-state.json` (updated every 2 minutes by `torah-celestial.timer`)
- **CLI**: `torah-ctl today | parasha | search <query> | ask <question>`
- **Terminal Greeting**: `torah-motd`
- **MCP Server**: `torah-mcp` (exposes the local Tanakh & commentary library to AI agents)

---

## 📄 License

Released under the [MIT License](LICENSE). Built with deep respect for Jewish tradition and shared freely for communities everywhere.
