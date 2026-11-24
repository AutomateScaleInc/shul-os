<p align="center">
  <img src="static/branding/shulos-logo-wordmark.jpg" alt="Shul.OS — The Living Synagogue OS" width="760">
</p>

# ✡ Shul.OS — Living Synagogue Operating System

**An open-source, 100% offline-capable Sacred Operating System for Synagogues, Chabad Houses, Jewish Schools, and Homes.**

Turn any Linux computer (even a donated 2012–2019 iMac or mini PC) into **Shul.OS** — a living Torah & Tanakh sanctuary synchronized from the ground up with the **exact Jewish calendar, real-time Sun & Moon astronomy, Halachic Zmanim, weekly Parashah, classical commentaries, illuminated art, and warm local voice AI.**

---

## ✨ What Makes It Holy From the Ground Up

| Layer | Capabilities |
|---|---|
| **🌙 100% Offline Astronomical Engine** (`sacred_astronomy.py`) | Pure-Python NOAA/Meeus Solar & Lunar Ephemeris + Dershowitz–Reingold Hebrew Calendar. Real-time Sun altitude & azimuth, Moon illumination %, phase angle, lunar age (`29.53d`), Moonrise/Moonset, topocentric elevation, **Kiddush Levana** window, **12/13-Month Jewish Year Wheel SVG**, **Shabbat Mevarchim / Rosh Chodesh & Holidays** countdown, **Mizrach** bearing to Jerusalem, all 14 GRA/MGA **Halachic Zmanim**, halachic sunset rollover, **Four Tekufot**, **Sefirat HaOmer** + daily Sefirah, **Chanukah** nights, and active **Tefillah** inserts. |
| **🖥 Living Holy OS Layer** (`sacred-os-daemon.py`) | Synchronizes the operating system itself with the Jewish day: gently shifts Wayland/Hyprland monitor warmth via `hyprsunset` (`6200K` Shacharit → `4700K` Plag HaMincha → `4000K` Bein HaShmashot → `3700K` Maariv), enforces a gentle **Sanctuary Volume Ceiling** (`<= 42%`), honors **Shabbat & Yom Tov Sanctuary Stillness** automatically from Candle Lighting to Havdalah, publishes `$XDG_RUNTIME_DIR/torah-sanctuary-state.json`, and greets every terminal via `torah-motd`. |
| **📜 Complete Offline Corpus** (`data/torah.db`) | All **39 books of the Tanakh / Old Testament** (`23,206` verses in nikud Hebrew + English), **`21,500+` classical commentaries** (Rashi, Or HaChaim, Ramban, Ibn Ezra, Sforno, Pirkei Avot, Bereishit & Shemot Rabbah — continuously expanded by Mini-Orca), all **54 weekly Parashiyot** with daily 7-Aliyah rotation, and curated story, historical & Living Scribe dossiers — searchable instantly via multi-commentator SQLite FTS5 RAG with zero internet. |
| **🎨 Hands-Free Living Torah Cinema, Art & Rabbi Presentations** | **16 Orthodox-respectful illuminated Torah & Tanakh oil paintings** with GPU Ken Burns motion & bespoke animated SVG scene overlays, **walking illustrated Characters & Angels in the open margins** (Protagonist, Antagonist, Angels, Allies, Setting & Patterns across 14 iconic Parashot without interrupting the serious Torah timeline), **35 auto-reveal Guess-Before-Reveal Quizzes**, **15 Animated Character Dialogues**, **10 Animated Hebrew 3-Letter Root Explorers**, **10-Era Interactive Torah Timeline**, **Kids & Family Sanctuary Corner**, and **7-Slide Cinematic Presentations (`🎬 Present`)** with **📡 Live Broadcast Mode (`/watch` + SVG QR + Cloudflare public URL + Companion House-Node Sync)**. |
| **🎙 100% Local Voice AI & Scholarly Q&A** | Multi-commentator diversified RAG via local **Ollama** (`qwen2.5:1.5b` / `3b`) + optional cloud upgrade, warm natural baritone offline **Piper TTS** (`en_US-ryan-high`), and offline Whisper STT (`voxtype`). |
| **🧠 Mini-Orca · Living Torah Scribe** (`torah_scribe.py`) | Autonomous background scholar running every 30 minutes (`torah-scribe.timer`, low CPU `Nice=15`, automatically rests during Shabbat & Yom Tov stillness): incrementally expands classical commentaries (*Or HaChaim*, *Rashi on Nevi'im/Ketuvim*, *Kli Yakar*, *Chizkuni*, *Rashbam*, *Metzudat David*) when online, and uses local Ollama + verbatim verses/Rashi to author grounded Parashah & Tanakh study sheets indexed directly back into SQLite FTS5 RAG. |
| **📅 Synagogue Calendar & Supercharged Weekly Mailings** | Syncs any synagogue `.ics` feed + local events + kiosk mailing list signups + 1-click responsive HTML & Plain-Text weekly newsletter composer auto-embedding **offline Zmanim, Candle Lighting/Havdalah, Lunar/Rosh Chodesh Watch, "In Today's Terms", Hebrew Root of the Week, and Shabbat Table Riddle**. |

---

## 🚀 1-Command Install (Shul.OS)

```bash
git clone https://github.com/YOUR-ORG/torah-sanctuary-os.git
cd torah-sanctuary-os
./install.sh --synagogue "The European Synagogue · Torah Sanctuary" --city brussels
```

Available built-in city presets: `brussels`, `antwerp`, `jerusalem`, `tel_aviv`, `london`, `paris`, `new_york`, `miami`, `los_angeles` (or set any custom latitude, longitude, and timezone in **Settings**).

---

## 🔁 1-Command Clone to Another Node

Already running Torah Sanctuary OS on one machine? Clone it (including the pre-built offline corpus and all 16 illuminated paintings) onto a new computer in one command:

```bash
# Main Synagogue Node
./scripts/clone-to-node.sh user@new-imac --synagogue "Congregation Ohel Eliezer" --city brussels

# Companion House Node (automatically follows the Synagogue's live broadcast slides!)
./scripts/clone-to-node.sh user@house-node --synagogue "Rabbi Michoel Home" --city brussels --follow-url https://live.theshul.eu
```

Run the built-in pure-stdlib automated verification suite anytime:

```bash
python3 -m unittest discover -s tests -v
# Include live HTTP endpoint checks against a running Sanctuary:
TORAH_TEST_URL=http://127.0.0.1:8080 python3 -m unittest discover -s tests -v
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
