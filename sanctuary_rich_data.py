#!/usr/bin/env python3
"""
Torah Sanctuary — Rich Visual Atlas:
- 12 Sacred Jewish Symbols (with inline vector SVG emblems, Hebrew names, verses & modern meaning)
- 12 Main Torah & Tanakh Characters (with Hebrew meanings, archetypes, Rashi/Sages & "In Today's Terms")
- Story Enrichment Map (linking all 16 stories to museum-grade illuminated artwork, characters,
  symbols, and concrete "Applying It in Today's Terms" modern takeaways)
- 7-Slide Full-Screen Rabbi & Synagogue Presentation Deck Builder
"""

import re
import torah_db

SYMBOLS = [
    {
        "slug": "sefer-torah",
        "name": "Sefer Torah (Torah Scroll)",
        "he_name": "סֵפֶר תּוֹרָה",
        "source_ref": "Deuteronomy 31:19 · Proverbs 3:18",
        "art": "/art/sacred-symbols.jpg",
        "meaning": "The Five Books of Moses handwritten by a trained scribe (Sofer) with quill and ink on parchment — the living covenant and heartbeat of Jewish continuity across 3,300 years.",
        "classical": "The Talmud (Menachot 30a) teaches that even a single missing letter renders a scroll incomplete — symbolizing that every single person in the community is indispensable.",
        "today": "In an age of disposable feeds and fleeting hot takes, the Torah Scroll anchors us to timeless wisdom, patient study, and the discipline of reading carefully before reacting.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="14" y="14" width="36" height="36" rx="3"/><line x1="14" y1="8" x2="14" y2="56"/><line x1="50" y1="8" x2="50" y2="56"/><circle cx="14" cy="7" r="2.5" fill="currentColor"/><circle cx="50" cy="7" r="2.5" fill="currentColor"/><circle cx="14" cy="57" r="2.5" fill="currentColor"/><circle cx="50" cy="57" r="2.5" fill="currentColor"/><line x1="22" y1="24" x2="42" y2="24"/><line x1="22" y1="32" x2="42" y2="32"/><line x1="22" y1="40" x2="36" y2="40"/></svg>""",
    },
    {
        "slug": "menorah",
        "name": "Seven-Branched Menorah",
        "he_name": "מְנוֹרָה",
        "source_ref": "Exodus 25:31-40 · Zechariah 4:6",
        "art": "/art/sacred-symbols.jpg",
        "meaning": "Hammered from a single solid piece of pure gold in the Mishkan and Temple, its seven branches radiate outward from one central shaft — light spreading from unity into the world.",
        "classical": "The Talmud (Shabbat 22b) notes God does not need physical light; rather, the Menorah is testimony to all humanity that Divine wisdom dwells among people who kindle light for others.",
        "today": "Notice the Menorah's windows in the Temple were narrow inside and wide outside — designed to shine light OUT into the world. Real leadership and faith don't hoard warmth; they brighten dark rooms.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="32" y1="14" x2="32" y2="54"/><path d="M10 18 C10 38, 54 38, 54 18"/><path d="M17 18 C17 32, 47 32, 47 18"/><path d="M24 18 C24 27, 40 27, 40 18"/><line x1="20" y1="54" x2="44" y2="54"/><circle cx="10" cy="14" r="1.8" fill="currentColor"/><circle cx="17" cy="14" r="1.8" fill="currentColor"/><circle cx="24" cy="14" r="1.8" fill="currentColor"/><circle cx="32" cy="10" r="2" fill="currentColor"/><circle cx="40" cy="14" r="1.8" fill="currentColor"/><circle cx="47" cy="14" r="1.8" fill="currentColor"/><circle cx="54" cy="14" r="1.8" fill="currentColor"/></svg>""",
    },
    {
        "slug": "luchot",
        "name": "The Two Tablets (Luchot)",
        "he_name": "לוּחוֹת הַבְּרִית",
        "source_ref": "Exodus 20:1-14 · Exodus 34:1",
        "art": "/art/sinai-tablets.jpg",
        "meaning": "Two equal stone tablets pairing duties to God (1–5) directly across from duties to fellow human beings (6–10) — proving spirituality and ethics are inseparable.",
        "classical": "Both the broken pieces of the first Tablets and the whole Second Tablets rested together inside the Ark (Berakhot 8b) — honoring resilience and repair.",
        "today": "You cannot claim to be spiritual while cutting corners on honesty, kindness, or respect for people. And carrying scars from past mistakes doesn't disqualify you — repaired wholeness is sacred.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M10 52 V22 A10 10 0 0 1 30 22 V52 Z"/><path d="M34 52 V22 A10 10 0 0 1 54 22 V52 Z"/><line x1="16" y1="26" x2="24" y2="26"/><line x1="16" y1="33" x2="24" y2="33"/><line x1="16" y1="40" x2="24" y2="40"/><line x1="40" y1="26" x2="48" y2="26"/><line x1="40" y1="33" x2="48" y2="33"/><line x1="40" y1="40" x2="48" y2="40"/></svg>""",
    },
    {
        "slug": "shofar",
        "name": "The Shofar (Ram's Horn)",
        "he_name": "שׁוֹפָר",
        "source_ref": "Genesis 22:13 · Leviticus 23:24 · Exodus 19:19",
        "art": "/art/sacred-symbols.jpg",
        "meaning": "An unadorned ram's horn sounded at Sinai, on Rosh Hashanah, and at the close of Yom Kippur — an unpolished cry straight from the heart without words.",
        "classical": "Rambam (Laws of Teshuvah 3:4) writes: the Shofar calls out, 'Sleepers, awake from your slumber! Examine your deeds, remember your Creator, and return to who you truly are.'",
        "today": "The Shofar is a spiritual alarm clock against living on autopilot — waking us up from distraction, phone-scrolling, and routine to reconnect with what actually matters.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M12 44 C22 44, 34 38, 48 18 C52 24, 54 30, 50 35 C38 46, 24 50, 12 48 Z"/><path d="M52 14 C56 12, 58 10, 58 10" stroke-linecap="round"/><path d="M55 20 C59 20, 61 20, 61 20" stroke-linecap="round"/></svg>""",
    },
    {
        "slug": "shabbat-candles",
        "name": "Shabbat Candles (Nerot Shabbat)",
        "he_name": "נֵרוֹת שַׁבָּת",
        "source_ref": "Genesis 2:1-3 · Exodus 20:8 · Deuteronomy 5:12",
        "art": "/art/creation-shabbat.jpg",
        "meaning": "Two candles lit before Friday sunset representing Zakhor ('Remember' Shabbat) and Shamor ('Guard' Shabbat) — bringing Shalom Bayit (peace in the home).",
        "classical": "Abraham Joshua Heschel called Shabbat 'a palace in time' — the very first thing declared holy in the Torah is not a building, but a day of rest and presence.",
        "today": "In a 24/7 always-on economy of notifications and burnout, lighting Shabbat candles draws a sacred boundary: one day every week where your worth isn't measured by productivity, emails, or status.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M22 14 C19 19, 19 23, 22 25 C25 23, 25 19, 22 14 Z" fill="currentColor"/><path d="M42 14 C39 19, 39 23, 42 25 C45 23, 45 19, 42 14 Z" fill="currentColor"/><rect x="18" y="27" width="8" height="24" rx="1.5"/><rect x="38" y="27" width="8" height="24" rx="1.5"/><line x1="13" y1="53" x2="31" y2="53"/><line x1="33" y1="53" x2="51" y2="53"/></svg>""",
    },
    {
        "slug": "jacobs-ladder",
        "name": "Jacob's Ladder (Sulam Ya'akov)",
        "he_name": "סֻלָּם יַעֲקֹב",
        "source_ref": "Genesis 28:12-16 (Parashat Vayetzei)",
        "art": "/art/jacobs-ladder.jpg",
        "meaning": "A bridge rooted firmly on earth whose top reaches the heavens, with angels ascending and descending — linking daily earthly life with higher purpose.",
        "classical": "Classic gematria notes Sulam (ladder = 130) equals Sinai (= 130), and angels ascend first because spiritual elevation begins with concrete human choices down on earth.",
        "today": "You don't have to escape your job, city, or responsibilities to live a spiritual life. Keep your feet planted on the ground while aiming your integrity and vision toward heaven — one rung at a time.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="22" y1="8" x2="18" y2="56"/><line x1="42" y1="8" x2="46" y2="56"/><line x1="21.5" y1="16" x2="42.5" y2="16"/><line x1="21" y1="26" x2="43" y2="26"/><line x1="20" y1="36" x2="44" y2="36"/><line x1="19" y1="46" x2="45" y2="46"/></svg>""",
    },
    {
        "slug": "burning-bush",
        "name": "The Burning Bush (HaSneh)",
        "he_name": "הַסְּנֶה הַבּוֹעֵר",
        "source_ref": "Exodus 3:2-14",
        "art": "/art/burning-bush.jpg",
        "meaning": "A humble desert thornbush blazing with fire yet never consumed — God's declaration of enduring solidarity with the humble and persecuted.",
        "classical": "Midrash Shemot Rabbah (2:5) teaches God chose a lowly thornbush over a towering cedar to show: 'I am with them in their distress' — and the flame of Jewish identity endures every storm.",
        "today": "Real calling rarely starts with a spotlight; it starts when you slow down enough to 'turn aside and notice' something quiet others walked right past — and care enough to step up.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M32 10 C24 22, 20 30, 26 40 C22 36, 16 39, 18 46 C22 52, 42 52, 46 46 C48 39, 42 36, 38 40 C44 30, 40 22, 32 10 Z"/><path d="M32 24 C29 30, 29 35, 32 39 C35 35, 35 30, 32 24 Z" fill="currentColor"/></svg>""",
    },
    {
        "slug": "rainbow-covenant",
        "name": "The Rainbow Covenant (Keshet)",
        "he_name": "קֶשֶׁת בֶּעָנָן",
        "source_ref": "Genesis 9:12-17",
        "art": "/art/noah-rainbow.jpg",
        "meaning": "God's universal covenant with Noah and every living creature on earth — turning a hunter's bow (keshet) upward away from earth as an eternal emblem of peace and mercy.",
        "classical": "Ramban notes the bow points upward, away from humanity, like a warrior laying down a weapon in lasting peace; Jewish law recites a dedicated blessing upon seeing a rainbow.",
        "today": "A rainbow only appears when sunlight shines through rain clouds — reminding us that beauty and renewal emerge through adversity, and that all humanity shares stewardship of one fragile planet.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M10 46 A22 22 0 0 1 54 46"/><path d="M17 46 A15 15 0 0 1 47 46"/><path d="M24 46 A8 8 0 0 1 40 46"/><line x1="8" y1="48" x2="56" y2="48"/></svg>""",
    },
    {
        "slug": "etz-chaim",
        "name": "Tree of Life (Etz Chaim)",
        "he_name": "עֵץ חַיִּים",
        "source_ref": "Genesis 2:9 · Proverbs 3:18",
        "art": "/art/ruth-harvest.jpg",
        "meaning": "Sung every Shabbat as the Torah returns to the Ark: 'It is a Tree of Life to those who hold fast to it, and all its paths are peace.'",
        "classical": "The wooden rollers of every Torah scroll are themselves called Atzei Chaim ('Trees of Life') — teaching that Torah is not frozen stone, but a living, fruit-bearing organism.",
        "today": "Strong trees grow deep roots before they grow wide branches. Deep roots in values, family, and heritage give us the stability to bend without breaking in modern winds.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="32" y1="26" x2="32" y2="54"/><path d="M32 42 L22 32 M32 38 L42 28"/><circle cx="32" cy="20" r="11"/><path d="M22 54 C26 50, 38 50, 42 54"/></svg>""",
    },
    {
        "slug": "mezuzah",
        "name": "Mezuzah (Doorpost Scroll)",
        "he_name": "מְזוּזָה",
        "source_ref": "Deuteronomy 6:9 · Deuteronomy 11:20",
        "art": "/art/jerusalem-scroll.jpg",
        "meaning": "Handwritten parchment of the Shema placed slanted on the doorpost — sanctifying the threshold between private home and public world.",
        "classical": "Why slanted? A loving compromise between Rashi (vertical) and his grandson Rabbeinu Tam (horizontal) — teaching that peaceful harmony in a home outweighs winning every argument!",
        "today": "Touching the Mezuzah as you cross your doorway is a daily mindfulness reset: carry integrity and compassion from home out into the workplace, and leave stress at the door when returning to family.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="24" y="10" width="16" height="44" rx="5" transform="rotate(-14 32 32)"/><line x1="28" y1="22" x2="36" y2="20"/><line x1="29" y1="30" x2="37" y2="28"/><line x1="30" y1="38" x2="38" y2="36"/></svg>""",
    },
    {
        "slug": "magen-david",
        "name": "Magen David (Star of David)",
        "he_name": "מָגֵן דָּוִד",
        "source_ref": "Psalm 18:3 · II Samuel 22:3",
        "art": "/art/david-harp.jpg",
        "meaning": "Two interlocking triangles — one pointing heavenward (human striving upward), one pointing earthward (Divine blessing flowing down) — symbolizing protection, unity, and Jewish peoplehood.",
        "classical": "The six outer points with the seventh center recall the six days of Creation surrounding the heart of Shabbat.",
        "today": "True resilience is never solitary — the interlocking geometry reminds us that community, mutual responsibility (Arvut), and shared purpose hold us strong together.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="32,8 52,44 12,44"/><polygon points="32,56 52,20 12,20"/></svg>""",
    },
    {
        "slug": "tzitzit",
        "name": "Tallit & Tzitzit (Fringes)",
        "he_name": "טַלִּית וְצִיצִית",
        "source_ref": "Numbers 15:37-41",
        "art": "/art/sinai-tablets.jpg",
        "meaning": "Knotted fringes on the four corners of a garment — a visual reminder of the 613 mitzvot (gematria of Tzitzit 600 + 8 strings + 5 knots = 613) and moral clarity.",
        "classical": "The Talmud (Menachot 43b) notes the thread of tekhelet (sky-blue) recalls the sea, which recalls the sky, which recalls the Throne of Glory — lifting our eyes above impulse.",
        "today": "Like tying a string around your finger for what truly counts, Tzitzit teaches habit design: put visible reminders of your core values right in your line of sight before you make tough choices.",
        "svg": """<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="12" y="14" width="40" height="28" rx="3"/><line x1="12" y1="21" x2="52" y2="21"/><line x1="12" y1="35" x2="52" y2="35"/><line x1="16" y1="42" x2="14" y2="56"/><line x1="20" y1="42" x2="20" y2="56"/><line x1="44" y1="42" x2="44" y2="56"/><line x1="48" y1="42" x2="50" y2="56"/></svg>""",
    },
]

CHARACTERS = [
    {
        "slug": "abraham-sarah",
        "name": "Abraham & Sarah",
        "he_name": "אַבְרָהָם וְשָׂרָה",
        "he_meaning": "Father of Many Nations & Princess",
        "archetype": "Pioneers of Chesed (Loving-Kindness) & Moral Courage",
        "era": "Patriarchs & Matriarchs · Genesis 12–25",
        "refs": "Genesis 12:1-3; 18:1-33; 22:1-19",
        "art": "/art/abraham-stars.jpg",
        "traits": ["Radical Hospitality", "Ethical Monotheism", "Courage to Stand Alone", "Advocacy for Justice"],
        "story": "Called by God with 'Lech Lecha' to leave everything familiar and become a blessing to all families of the earth. They pitched their tent open on all four sides to welcome dusty strangers, taught ethical monotheism in Haran and Canaan, and Abraham even dared argue with God for justice in Sodom.",
        "sages_say": "Rashi (Genesis 12:5) highlights that Abraham welcomed the men and Sarah welcomed the women; the Talmud (Shabbat 127a) learns from Abraham pausing his vision of God to serve guests that hospitality to people is greater than welcoming the Divine Presence.",
        "today": "In a polarized, lonely modern world, Abraham and Sarah model counter-cultural warmth: build an 'open-tent' home and workplace where outsiders feel genuinely seen, and never stay silent when fairness is at stake.",
    },
    {
        "slug": "isaac-rebecca",
        "name": "Isaac & Rebecca",
        "he_name": "יִצְחָק וְרִבְקָה",
        "he_meaning": "He Will Laugh & Captivating/Unifying",
        "archetype": "Quiet Depth, Inner Strength & Generous Initiative",
        "era": "Patriarchs & Matriarchs · Genesis 21–28",
        "refs": "Genesis 22:1-19; 24:1-67; 26:12-25",
        "art": "/art/abraham-stars.jpg",
        "traits": ["Quiet Perseverance", "Digging Deep Wells", "Generosity in Action", "Peacemaking"],
        "story": "Isaac — survivor of Mount Moriah — never leaves the Land of Israel; instead of fighting when neighbors plug his wells, he calmly digs new ones until he reaches 'Rechovot' (room for all). Rebecca proves her character at the well by eagerly drawing water not just for a tired traveler, but for all ten thirsty camels.",
        "sages_say": "Ramban teaches that Isaac re-digging his father's stopped-up wells symbolizes preserving heritage across generations; Rebecca's kindness to animals became the timeless test of true character.",
        "today": "Not every leader shouts. Isaac teaches sustainable grit — don't waste your life fighting over plugged wells; keep digging deeper until you create space for everyone. And Rebecca reminds us character shows up in how you treat those who can't pay you back.",
    },
    {
        "slug": "jacob-rachel-leah",
        "name": "Jacob (Israel), Rachel & Leah",
        "he_name": "יַעֲקֹב (יִשְׂרָאֵל), רָחֵל וְלֵאָה",
        "he_meaning": "God-Wrestler · Ewe · Weary/Devoted",
        "archetype": "Transformation Through Struggle & Family Resilience",
        "era": "This Week's Parashah (Vayetzei) · Genesis 25–49",
        "refs": "Genesis 28:10-33:11 (Parashat Vayetzei & Vayishlach)",
        "art": "/art/jacobs-ladder.jpg",
        "traits": ["Wrestling with Purpose", "Unconditional Compassion", "Gratitude (Judah/Hod)", "Reconciliation"],
        "story": "Fleeing family conflict, Jacob dreams of the Ladder reaching heaven at Beit El, labors fourteen years out of love for Rachel, builds the twelve tribes of Israel with Leah and Rachel, wrestles the angel until dawn to become 'Israel', and bravely reconciles with his brother Esau. Leah names Judah ('Gratitude'), and Rachel's selfless compassion protects her sister's dignity.",
        "sages_say": "Midrash Eicha Rabbah recounts that in Israel's darkest hour, it was Rachel's quiet mercy — sharing her secret wedding signs so Leah wouldn't be shamed — that moved heaven to promise 'your children will return to their borders.'",
        "today": "None of us comes from a flawless family or a straight career path. Jacob-Israel shows you can wrestle with your hardest nights, carry a limp, and still grow into someone who heals old rifts and builds a lasting legacy.",
    },
    {
        "slug": "joseph",
        "name": "Joseph (Yosef HaTzaddik)",
        "he_name": "יוֹסֵף הַצַּדִּיק",
        "he_meaning": "May God Add / Increase",
        "archetype": "Integrity Under Pressure, Visionary Strategy & Forgiveness",
        "era": "Genesis 37–50",
        "refs": "Genesis 37:3; 41:1-45; 45:1-15; 50:20",
        "art": "/art/joseph-egypt.jpg",
        "traits": ["Unshakeable Integrity", "Strategic Foresight", "Resilience in Crisis", "Radical Forgiveness"],
        "story": "Betrayed by his brothers, sold into slavery, and falsely imprisoned in Egypt, Joseph refuses bitterness or compromise. Interpreting Pharaoh's dreams, he saves the region from seven years of famine — and when his brothers stand helpless before him, he chooses healing over revenge: 'You meant it for harm, yet God wove it for good, to save many lives.'",
        "sages_say": "Sforno celebrates Joseph's restraint when holding absolute power as a pinnacle of human nobility; Rambam points to Judah defending Benjamin as the ultimate proof of genuine Teshuvah.",
        "today": "Joseph is the Torah's ultimate executive & crisis-leader archetype: stay ethical when nobody is watching, prepare during fat years for lean years, and refuse to let past betrayals turn you into a bitter person.",
    },
    {
        "slug": "moses",
        "name": "Moses (Moshe Rabbeinu)",
        "he_name": "מֹשֶׁה רַבֵּינוּ",
        "he_meaning": "Drawn from the Water · Our Teacher",
        "archetype": "Humble Servant-Leader, Emancipator & Lawgiver",
        "era": "Exodus · Leviticus · Numbers · Deuteronomy",
        "refs": "Exodus 2–3; 14; 19–20; 32–34; Numbers 12:3; Deuteronomy 34",
        "art": "/art/burning-bush.jpg",
        "traits": ["Deep Humility", "Moral Outrage Against Injustice", "Fierce Loyalty to His People", "Lifelong Teacher"],
        "story": "Saved from the Nile by five brave women, raised in Pharaoh's palace yet refusing to ignore Hebrew slaves' pain, Moses answers God at the Burning Bush despite a speech impediment. He leads Israel from slavery to Sinai, pleads 'erase me from Your book' to save his people after the Golden Calf, and gives his final charge: 'Choose life!'",
        "sages_say": "The Torah's highest praise of Moses isn't his miracles — it's Numbers 12:3: 'Moses was the most humble person on the face of the earth.' That's why Jews call him 'Moshe Rabbeinu' — Moses Our Teacher, never 'King Moses.'",
        "today": "True leadership isn't charisma or ego. Notice Moses stammered, doubted himself, and took advice from his father-in-law Jethro on delegating! Great leaders share credit, defend their team when things go wrong, and measure success by the teachers they leave behind.",
    },
    {
        "slug": "miriam-aaron",
        "name": "Miriam & Aaron",
        "he_name": "מִרְיָם וְאַהֲרֹן",
        "he_meaning": "Prophetess of Hope & Pursuer of Peace",
        "archetype": "Joyful Resilience (Miriam) & Peacemaking (Aaron)",
        "era": "Exodus & Wilderness Journey",
        "refs": "Exodus 2:4-8; 15:20-21; Numbers 6:24-26; Pirkei Avot 1:12",
        "art": "/art/exodus-sea.jpg",
        "traits": ["Foresight & Faith", "Musical Joy", "Priestly Blessing", "Pursuing Peace"],
        "story": "As a young girl, Miriam watched over baby Moses in the Nile and boldly arranged for his mother to raise him; at the Sea of Reeds she brought timbrels packed in advance in Egypt because she *knew* there would be a miracle to celebrate! Aaron, the first High Priest, blessed Israel daily with peace and walked between quarreling neighbors to reconcile them.",
        "sages_say": "Pirkei Avot 1:12 immortalizes Aaron: 'Be of the disciples of Aaron — loving peace and pursuing peace, loving humanity and drawing them close to Torah.' And the Talmud credits the sustained well of water in the desert to Miriam's merit.",
        "today": "Miriam teaches packing your tambourine *before* the breakthrough arrives — bringing hope into dark seasons. Aaron teaches active peacemaking: don't just wish for peace passively; build bridges between people who stopped talking.",
    },
    {
        "slug": "joshua-caleb",
        "name": "Joshua & Caleb",
        "he_name": "יְהוֹשֻׁעַ וְכָלֵב",
        "he_meaning": "God Saves & Whole-Hearted",
        "archetype": "Moral Courage Against the Crowd",
        "era": "Wilderness & Entry to the Land · Numbers & Joshua",
        "refs": "Numbers 13:30; 14:6-9; Joshua 1:6-9",
        "art": "/art/sinai-tablets.jpg",
        "traits": ["Independent Thinking", "Calm Under Panic", "Loyal Mentorship", "Stepping Into Leadership"],
        "story": "When ten scouts spread panic across the camp claiming 'we looked like grasshoppers,' Caleb quieted the crowd and stood with Joshua: 'We can surely go up and succeed!' Joshua served Moses faithfully for forty years before hearing God's charge: 'Chazak v'Ematz — Be strong and courageous!'",
        "sages_say": "Numbers 14:24 praises Caleb for having 'a different spirit' (ruach acheret) — the strength to resist groupthink without losing compassion for his community.",
        "today": "In an era of viral panic, doomscrolling, and herd mentality, Joshua and Caleb model grounded optimism: look squarely at real obstacles without shrinking yourself into a 'grasshopper.'",
    },
    {
        "slug": "ruth-boaz",
        "name": "Ruth & Boaz",
        "he_name": "רוּת וּבֹעַז",
        "he_meaning": "Companion/Friendship & In Him Is Strength",
        "archetype": "Quiet Everyday Loving-Kindness (Chesed) & Dignity",
        "era": "Period of the Judges · Book of Ruth (Read on Shavuot)",
        "refs": "Ruth 1:16-17; 2:1-16; 4:13-22",
        "art": "/art/ruth-harvest.jpg",
        "traits": ["Fierce Loyalty", "Welcoming the Stranger", "Dignified Charity", "Quiet Integrity"],
        "story": "Refusing to abandon her bereaved mother-in-law Naomi, Moabite-born Ruth chooses Jewish belonging out of pure love ('Your people shall be my people'). In Bethlehem's barley fields, Boaz greets workers warmly, protects Ruth's dignity while leaving extra grain quietly, and marries her — becoming the great-grandparents of King David.",
        "sages_say": "Midrash Ruth Rabbah teaches the entire Book of Ruth exists to show the immeasurable power of quiet acts of kindness — and why Shavuot pairs Mount Sinai's laws with Ruth's tender heart.",
        "today": "How you help someone matters as much as *that* you help. Boaz and Ruth show that real generosity preserves the other person's dignity, and that welcoming newcomers enriches the whole community for generations.",
    },
    {
        "slug": "king-david",
        "name": "King David",
        "he_name": "דָּוִד הַמֶּלֶךְ",
        "he_meaning": "Beloved",
        "archetype": "Poet-Warrior, Sweet Singer of Psalms & Honest Repentance",
        "era": "United Monarchy · I & II Samuel · Psalms",
        "refs": "I Samuel 16–17; II Samuel 12; Psalm 23; Psalm 51",
        "art": "/art/david-harp.jpg",
        "traits": ["Authentic Courage", "Emotional Honesty in Prayer", "Owning Mistakes", "Uniting Jerusalem"],
        "story": "Overlooked youngest shepherd who refused King Saul's heavy armor to face Goliath with a sling and faith, united Jerusalem as Israel's capital, and poured every human emotion — joy, grief, gratitude, fear, and awe — into the Book of Psalms (Tehillim). When confronted by the prophet Nathan over his greatest moral failure, David spoke two historic words: 'Chatati — I have sinned.'",
        "sages_say": "The Talmud (Moed Katan 16b) honors David as 'the sweet singer of Israel' and 'the one who raised the banner of Teshuvah' — proving greatness isn't perfection, but radical honesty when you fall.",
        "today": "David's Psalms still comfort millions 3,000 years later because he never faked his feelings. And his instant 'I was wrong' — zero excuses, zero spin — is the rarest superpower in modern leadership and marriage.",
    },
    {
        "slug": "king-solomon",
        "name": "King Solomon (Shlomo)",
        "he_name": "שְׁלֹמֹה הַמֶּלֶךְ",
        "he_meaning": "Peace / Wholeness (Shalom)",
        "archetype": "Wisdom, Discernment & Builder of the First Temple",
        "era": "First Temple Era · I Kings 3–11 · Proverbs · Ecclesiastes",
        "refs": "I Kings 3:5-28; 8:22-43; Proverbs 3:5-18; Ecclesiastes 3:1",
        "art": "/art/jerusalem-scroll.jpg",
        "traits": ["Listening Heart (Lev Shome'a)", "Discernment", "Universal Hospitality", "Builder of Peace"],
        "story": "When God offered young Solomon anything he wished, he didn't ask for wealth, victory, or long life — he asked for a 'Lev Shome'a' (a listening, understanding heart) to judge fairly. He built the First Temple in Jerusalem, dedicating it as a house of prayer even for the distant foreigner who comes seeking God (I Kings 8:41-43), and authored Proverbs' timeless practical wisdom.",
        "sages_say": "Notice Solomon's dedication prayer asks God to answer the stranger from a far land — showing the Temple was envisioned as a beacon of peace for all humanity.",
        "today": "In a noisy world obsessed with talking over one another, Solomon's greatest request — a *listening heart* — is the highest form of wisdom in business, parenting, and community.",
    },
    {
        "slug": "elijah",
        "name": "Elijah the Prophet (Eliyahu)",
        "he_name": "אֵלִיָּהוּ הַנָּבִיא",
        "he_meaning": "My God Is the Lord",
        "archetype": "Fearless Truth-Teller, Healer of Burnout & Messenger of Peace",
        "era": "Prophets · I & II Kings · Malachi 3:23-24",
        "refs": "I Kings 18:19-19:18; Malachi 3:23-24",
        "art": "/art/jerusalem-scroll.jpg",
        "traits": ["Courage Under Pressure", "Honesty About Burnout", "Listening for the Still Small Voice", "Reconciling Generations"],
        "story": "After confronting idolatry dramatically on Mount Carmel, Elijah collapses in exhaustion under a desert tree. An angel gently feeds him warm bread and lets him rest — and at Sinai he discovers God is not in the roaring wind, earthquake, or fire, but in a 'Kol Demamah Dakah' — a still, small voice. Welcomed at every Passover Seder and Havdalah as herald of peace.",
        "sages_say": "Malachi concludes the Prophets promising Elijah will 'turn the hearts of parents to children, and children to parents' — bridging generational divides.",
        "today": "Even heroes burn out. Elijah's story validates rest, nourishment, and stepping away from loud spectacle and outrage cycles to hear the quiet voice of clarity and compassion.",
    },
    {
        "slug": "esther-mordechai",
        "name": "Queen Esther & Mordechai",
        "he_name": "אֶסְתֵּר הַמַּלְכָּה וּמָרְדְּכַי",
        "he_meaning": "Hidden Star & Steadfast Servant",
        "archetype": "Quiet Courage, Strategic Wisdom & Diaspora Solidarity",
        "era": "Persian Period · Book of Esther (Purim)",
        "refs": "Esther 4:13-16; 9:22",
        "art": "/art/jerusalem-scroll.jpg",
        "traits": ["Rising to the Moment", "Strategic Patience", "Solidarity", "Joy Paired with Tzedakah"],
        "story": "When Haman plots to annihilate the Jewish people across 127 provinces of Persia, Mordechai challenges Esther: 'Who knows if you reached this royal place for just such a moment as this?' Risking her life, Esther uses timing, wisdom, and courage to save her people — establishing Purim with gifts to friends and charity to the poor.",
        "sages_say": "God's Name never appears once in Megillat Esther — teaching 'Hester Panim' (hidden providence): when heaven seems quiet, brave human action becomes the miracle.",
        "today": "You don't need to wait for an obvious miracle to make a difference. Ask Mordechai's timeless question about your own talents, position, and community: 'What if I am right here for just such a moment as this?'",
    },
]

STORY_ENRICHMENT = {
    "01-creation-and-shabbat": {
        "art": "/art/creation-shabbat.jpg",
        "characters": ["Adam & Eve (First Humanity)"],
        "symbols": ["shabbat-candles", "etz-chaim", "sefer-torah"],
        "today_title": "Protecting Your Sanctuary in Time",
        "today_points": [
            "Every person you meet — colleague, stranger, or critic — carries B'tzelem Elohim (inherent infinite dignity).",
            "Unplugging on Shabbat is the world's oldest antidote to digital burnout: stepping off the treadmill to actually *be* with family.",
            "Creation starts with speech ('And God said...'): our words literally build or tear down the worlds around us every day.",
        ],
    },
    "02-noah-and-the-rainbow": {
        "art": "/art/noah-rainbow.jpg",
        "characters": ["Noah & His Family"],
        "symbols": ["rainbow-covenant", "etz-chaim"],
        "today_title": "Integrity When Nobody Else Is Doing It",
        "today_points": [
            "Noah built the Ark for years before a single drop of rain fell — long-term character and preparation often look odd until the storm hits.",
            "The Seven Noahide Laws remind us that fairness, honesty, and compassion to animals are universal human responsibilities.",
            "Tevah means both 'Ark' and 'Word': building a home of calm, respectful words protects your family through life's floods.",
        ],
    },
    "03-abraham-lech-lecha": {
        "art": "/art/abraham-stars.jpg",
        "characters": ["abraham-sarah"],
        "symbols": ["sefer-torah", "mezuzah"],
        "today_title": "Open-Tent Hospitality & Stepping Into Growth",
        "today_points": [
            "Lech Lecha ('Go to yourself'): real self-discovery happens when you leave comfort zones for a higher calling.",
            "Abraham paused a Divine vision to serve three dusty strangers — never get so 'busy' or 'important' that you walk past someone needing kindness.",
            "Like Abraham arguing over Sodom, healthy faith asks hard moral questions and stands up for fairness.",
        ],
    },
    "04-akeidat-yitzchak": {
        "art": "/art/abraham-stars.jpg",
        "characters": ["abraham-sarah", "isaac-rebecca"],
        "symbols": ["shofar"],
        "today_title": "Showing Up with 'Hineni' & Reverence for Life",
        "today_points": [
            "The Akeidah permanently shattered ancient pagan child sacrifice, enshrining the sanctity of human life at the heart of Jewish ethics.",
            "Saying 'Hineni' ('Here I am — fully present') to your spouse, child, or community is the rarest gift in an age of divided attention.",
            "Hearing the Shofar reminds us we can always pivot when heaven calls us to a higher path of mercy.",
        ],
    },
    "05-jacobs-ladder-and-israel": {
        "art": "/art/jacobs-ladder.jpg",
        "characters": ["jacob-rachel-leah"],
        "symbols": ["jacobs-ladder", "mezuzah"],
        "today_title": "Finding Meaning Right Where You Stand",
        "today_points": [
            "Jacob discovered holiness on a hard stone in exile — you don't need perfect circumstances to feel connected to God and purpose.",
            "Being named 'Israel' (one who wrestles and prevails) normalizes honest struggle: wrestling with doubts or hardship makes you stronger, not weaker.",
            "Jacob's reunion with Esau shows it is never too late to take the humble first step toward healing a family rift.",
        ],
    },
    "06-joseph-and-his-brothers": {
        "art": "/art/joseph-egypt.jpg",
        "characters": ["joseph", "jacob-rachel-leah"],
        "symbols": ["etz-chaim"],
        "today_title": "Integrity in the Pit & Forgiveness at the Top",
        "today_points": [
            "Joseph stayed trustworthy in Potiphar's house and in prison — character built in obscurity is what prepares you for opportunity.",
            "Holding power over people who hurt you is the ultimate test: Joseph used his influence to feed and heal rather than settle scores.",
            "Real apology isn't just words; like Judah standing up for Benjamin, it's acting differently when the exact same test returns.",
        ],
    },
    "07-moses-and-the-burning-bush": {
        "art": "/art/burning-bush.jpg",
        "characters": ["moses", "miriam-aaron"],
        "symbols": ["burning-bush", "menorah"],
        "today_title": "Noticing Quiet Wonders & Reluctant Leadership",
        "today_points": [
            "Five brave women launched the Exodus before Moses spoke a word — everyday moral courage often comes from unexpected people.",
            "God waited for Moses to 'turn aside and look': slow down enough to notice the quiet burning bushes of need and beauty around you.",
            "Feeling unqualified ('Who am I?') doesn't disqualify you — humility is actually the prerequisite for trustworthy leadership.",
        ],
    },
    "08-exodus-passover-and-sea": {
        "art": "/art/exodus-sea.jpg",
        "characters": ["moses", "miriam-aaron"],
        "symbols": ["shabbat-candles", "menorah"],
        "today_title": "Empathy Born From Memory & Taking the First Step",
        "today_points": [
            "Nachshon stepped into the sea before it split: clarity often arrives *after* you take the first courageous step, not before.",
            "Spilling drops of wine at the Seder for the plagues teaches mature empathy — never gloat over anyone's suffering.",
            "Freedom isn't just 'nobody tells me what to do' — real freedom is using your liberty for purpose, family, and lifting up the stranger.",
        ],
    },
    "09-mount-sinai-ten-commandments": {
        "art": "/art/sinai-tablets.jpg",
        "characters": ["moses", "miriam-aaron"],
        "symbols": ["luchot", "shofar", "sefer-torah"],
        "today_title": "Why Ethics & Faith Belong on Two Paired Tablets",
        "today_points": [
            "Israel received Torah only when they camped 'like one person with one heart' — unity and mutual respect unlock breakthroughs.",
            "Pairing duties to God with duties to neighbors proves honest business, truthful speech, and honoring parents ARE sacred acts.",
            "Giving Torah in the ownerless desert teaches that wisdom belongs to every curious heart, regardless of background or wealth.",
        ],
    },
    "10-golden-calf-and-mercy": {
        "art": "/art/sinai-tablets.jpg",
        "characters": ["moses", "miriam-aaron"],
        "symbols": ["luchot", "shofar"],
        "today_title": "Keeping the Broken Pieces Beside the Whole",
        "today_points": [
            "Storing the shattered First Tablets right beside the whole Second Tablets teaches that our mistakes and scars don't erase our worth.",
            "The Thirteen Attributes of Mercy ('slow to anger, abounding in kindness') give us a daily blueprint for patience with loved ones and ourselves.",
            "Panic makes us build 'golden calves' (quick fixes and distractions); true stability comes from patient trust and second chances.",
        ],
    },
    "11-twelve-spies-and-courage": {
        "art": "/art/sinai-tablets.jpg",
        "characters": ["joshua-caleb", "moses"],
        "symbols": ["tzitzit", "magen-david"],
        "today_title": "Overcoming the 'Grasshopper Mindset'",
        "today_points": [
            "'We were like grasshoppers in our own eyes, and so we were in theirs' — self-doubt projects outward before anyone else judges you.",
            "Truthful reporting vs. demoralizing negativity: Caleb and Joshua saw the exact same challenges yet spoke with calm possibility.",
            "Guard the energy you bring into your team, synagogue, and family — courage is just as contagious as fear.",
        ],
    },
    "12-shema-and-moses-farewell": {
        "art": "/art/jerusalem-scroll.jpg",
        "characters": ["moses", "joshua-caleb"],
        "symbols": ["mezuzah", "sefer-torah", "etz-chaim"],
        "today_title": "'It Is Not in Heaven' — Living Torah Every Day",
        "today_points": [
            "The Shema starts with 'Listen' — active, whole-hearted listening is the foundation of faith, marriage, and friendship.",
            "'It is not in heaven' empowers every generation to study, ask questions, and apply Jewish ethics thoughtfully to modern realities.",
            "'Choose life!' reminds us every morning that our attitude, kindness, and integrity are active daily choices.",
        ],
    },
    "13-ruth-and-chesed": {
        "art": "/art/ruth-harvest.jpg",
        "characters": ["ruth-boaz"],
        "symbols": ["etz-chaim", "shabbat-candles"],
        "today_title": "Dignified Kindness & Belonging",
        "today_points": [
            "No miracles, no thunder — Ruth shows that quiet loyalty and showing up for a grieving friend reshape history.",
            "Boaz greeted his workers warmly and helped Ruth without embarrassing her — model dignified leadership and discreet tzedakah.",
            "Welcoming newcomers with warmth (as Bethlehem welcomed Ruth) strengthens the entire synagogue for generations.",
        ],
    },
    "14-david-and-goliath": {
        "art": "/art/david-harp.jpg",
        "characters": ["king-david"],
        "symbols": ["magen-david", "shofar"],
        "today_title": "Take Off Someone Else's Armor",
        "today_points": [
            "David won only after taking OFF King Saul's oversized armor — don't imitate someone else's style; bring your authentic strengths.",
            "'Humans see outward appearances, God sees the heart' — resist social-media comparison and invest in quiet inner character.",
            "Faithfulness in small unseen tasks (tending sheep) builds the quiet mastery needed when your big moment arrives.",
        ],
    },
    "15-elijah-still-small-voice": {
        "art": "/art/jerusalem-scroll.jpg",
        "characters": ["elijah"],
        "symbols": ["menorah", "shabbat-candles"],
        "today_title": "Healing Burnout & Hearing the Still Small Voice",
        "today_points": [
            "Before giving Elijah a mission, the angel gave him bread, water, and sleep — caring for your body and rest IS spiritual work.",
            "God wasn't in the loud wind, earthquake, or fire: step back from noisy outrage feeds to hear your own still, small voice of clarity.",
            "Passing the mantle to Elisha shows that sustainable impact comes through mentoring the next generation, not carrying everything alone.",
        ],
    },
    "16-esther-jonah-daniel": {
        "art": "/art/jerusalem-scroll.jpg",
        "characters": ["esther-mordechai", "king-solomon"],
        "symbols": ["sefer-torah", "magen-david", "menorah"],
        "today_title": "Rising to 'Such a Time as This'",
        "today_points": [
            "Esther teaches hidden providence: when you don't see obvious miracles, *your* courage and solidarity ARE the miracle.",
            "Jonah reminds us that compassion extends beyond our own circle — nobody is beyond repair and Teshuvah.",
            "Daniel models proud Jewish identity paired with excellence, integrity, and respectful citizenship in the wider world (just like Brussels' European Quarter!).",
        ],
    },
}


def list_symbols() -> list:
    return SYMBOLS


def list_characters() -> list:
    return CHARACTERS


def get_story_enrichment(slug: str) -> dict:
    en = STORY_ENRICHMENT.get(slug)
    if not en:
        return {
            "art": "/art/sacred-symbols.jpg",
            "characters": [],
            "symbols": ["sefer-torah", "menorah"],
            "today_title": "Living Torah Today",
            "today_points": [
                "Torah wisdom speaks directly into modern ethics, family life, integrity, and community.",
            ],
        }
    char_map = {c["slug"]: c for c in CHARACTERS}
    sym_map = {s["slug"]: s for s in SYMBOLS}
    chars = []
    for c_ref in en.get("characters", []):
        if c_ref in char_map:
            c = char_map[c_ref]
            chars.append({"slug": c["slug"], "name": c["name"], "he_name": c["he_name"], "archetype": c["archetype"], "today": c["today"], "art": c["art"]})
        else:
            chars.append({"slug": "", "name": c_ref, "he_name": "", "archetype": "Central Figure", "today": "", "art": en["art"]})
    syms = [sym_map[s] for s in en.get("symbols", []) if s in sym_map]
    return {
        "art": en["art"],
        "characters": chars,
        "symbols": syms,
        "today_title": en["today_title"],
        "today_points": en["today_points"],
    }


def build_presentation(kind: str = "story", slug: str = "") -> dict:
    """
    Build a polished, 7-slide full-screen Synagogue / Rabbi Presentation Deck for:
    - kind='story'     (any of the 16 Torah & Tanakh stories)
    - kind='parasha'   (this week's live Parashat Hashavua & Today's Aliyah!)
    - kind='character' (any of the 12 Main Torah Characters)
    """
    if kind == "parasha":
        daily = torah_db.get_daily_portion()
        p = daily["parasha"]
        ms = daily.get("matching_story")
        en = get_story_enrichment(ms["slug"]) if ms else get_story_enrichment("05-jacobs-ladder-and-israel")
        # Grab top 3 verses + commentaries from today's Aliyah
        v_slides = [s for s in daily.get("slides", []) if s.get("kind") == "verse"]
        anchor_v = v_slides[0] if v_slides else {}
        comm_items = []
        for vs in v_slides[:8]:
            if vs.get("commentary"):
                comm_items.append({"author": vs.get("commentator", "Rashi"), "ref": vs.get("ref", ""), "text": vs.get("commentary", "")})
            if len(comm_items) >= 3:
                break
        return {
            "deck_title": f"Parashat {p['en_name']} — {daily['day_en']} Presentation",
            "he_title": f"פרשת {p['he_name']}",
            "subtitle": f"{daily['aliyah_en']} ({daily['aliyah_ref']}) · The European Synagogue (theshul.eu)",
            "art": en["art"],
            "slides": [
                {
                    "type": "title",
                    "kicker": f"Weekly Torah Presentation · {daily['date_str']}",
                    "title": f"Parashat {p['en_name']}",
                    "he_title": f"פרשת {p['he_name']}",
                    "subtitle": f"Today's Reading ({daily['day_en']} · {daily['aliyah_en']}): {daily['aliyah_ref']}  |  Haftarah: {p['haftarah']}",
                    "art": en["art"],
                    "narration": f"Shalom and welcome to our Torah presentation on Parashat {p['en_name']}. Today we focus on {daily['aliyah_en']}, {daily['aliyah_ref']}. {p['summary']}",
                },
                {
                    "type": "story",
                    "kicker": "1 · The Living Narrative & Key Verse",
                    "title": anchor_v.get("ref") or p["ref"],
                    "he_text": anchor_v.get("he_text", ""),
                    "body": p["summary"] + ("\n\n" + anchor_v.get("en_text", "") if anchor_v.get("en_text") else ""),
                    "art": en["art"],
                    "narration": f"The heart of Parashat {p['en_name']}: {p['summary']}",
                },
                {
                    "type": "characters",
                    "kicker": "2 · Main Characters & Human Depth",
                    "title": "Who We Meet in This Portion",
                    "characters": en["characters"] or CHARACTERS[:2],
                    "narration": "Every Torah portion is a mirror of real human character, courage, and growth.",
                },
                {
                    "type": "symbols",
                    "kicker": "3 · Sacred Symbols & Imagery",
                    "title": "Symbols Hidden Inside the Story",
                    "symbols": en["symbols"],
                    "narration": "Look closely at the sacred symbols woven into this week's reading.",
                },
                {
                    "type": "commentators",
                    "kicker": "4 · Classical Commentators (PaRDeS)",
                    "title": "What Rashi, Ramban & the Sages Teach",
                    "items": comm_items or [{"author": "Classical Tradition", "ref": p["ref"], "text": p["summary"]}],
                    "narration": " ".join(f"{c['author']} teaches: {c['text'][:180]}" for c in comm_items[:2]) or p["summary"],
                },
                {
                    "type": "today",
                    "kicker": "5 · Applying It in Today's Terms",
                    "title": en["today_title"],
                    "points": en["today_points"],
                    "art": en["art"],
                    "narration": f"Applying this in today's terms — {en['today_title']}. " + " ".join(en["today_points"]),
                },
                {
                    "type": "discussion",
                    "kicker": "6 · Synagogue & Shabbat Table Discussion",
                    "title": "Questions for Rabbi Michoel's Community",
                    "questions": [
                        f"Where do you see yourself in today's reading of Parashat {p['en_name']}?",
                        "Which character's choice speaks most honestly to a decision you face this week?",
                        "How can we bring one concrete teaching from this Parashah into our home and community?",
                    ],
                    "narration": f"To close our presentation on Parashat {p['en_name']}, consider: how can we bring one living lesson from this portion into our week?",
                },
            ],
        }

    if kind == "character":
        char = next((c for c in CHARACTERS if c["slug"] == slug), CHARACTERS[0])
        return {
            "deck_title": f"{char['name']} — Character Portrait",
            "he_title": char["he_name"],
            "subtitle": f"{char['archetype']} · {char['refs']}",
            "art": char["art"],
            "slides": [
                {
                    "type": "title",
                    "kicker": f"Torah Character Study · {char['era']}",
                    "title": char["name"],
                    "he_title": char["he_name"],
                    "subtitle": f"Name Meaning: {char['he_meaning']}  ·  {char['archetype']}",
                    "art": char["art"],
                    "narration": f"Character portrait: {char['name']}, whose Hebrew name means {char['he_meaning']}. {char['archetype']}.",
                },
                {
                    "type": "story",
                    "kicker": "1 · Life & Turning Points",
                    "title": f"The Journey of {char['name']}",
                    "he_text": char["he_name"],
                    "body": char["story"],
                    "traits": char["traits"],
                    "art": char["art"],
                    "narration": char["story"],
                },
                {
                    "type": "commentators",
                    "kicker": "2 · Through the Eyes of the Sages",
                    "title": "Rashi, Midrash & Talmud Insights",
                    "items": [{"author": "Classical Sages", "ref": char["refs"], "text": char["sages_say"]}],
                    "narration": char["sages_say"],
                },
                {
                    "type": "today",
                    "kicker": "3 · Applying It in Today's Terms",
                    "title": f"What {char['name']} Teaches Us Today",
                    "points": [char["today"]] + [f"Core Strength to Practice: {t}" for t in char["traits"][:3]],
                    "art": char["art"],
                    "narration": f"In today's terms: {char['today']}",
                },
                {
                    "type": "discussion",
                    "kicker": "4 · Reflection & Community Discussion",
                    "title": "Bringing This Character Into Our Week",
                    "questions": [
                        f"Which trait of {char['name']} ({', '.join(char['traits'][:2])}) feels hardest to practice in modern life?",
                        f"If {char['name']} walked into Brussels today, what would they notice first?",
                        "Who in our own family or synagogue reminds you of this strength?",
                    ],
                    "narration": f"As we reflect on {char['name']}, which of their strengths can we practice this week?",
                },
            ],
        }

    # Default: Story presentation (any of the 16 curated stories!)
    doc = torah_db.get_document(slug) if slug else None
    if not doc:
        docs = torah_db.list_documents("story")
        doc = docs[0] if docs else {}
    en = get_story_enrichment(doc.get("slug", ""))
    verses = torah_db.lookup_verses(doc.get("refs", ""), max_verses=3)
    anchor_v = verses[0] if verses else {}

    # Parse commentary bullets & discussion questions cleanly
    comm_lines = [l.lstrip("-• ").strip() for l in (doc.get("commentators_note") or "").splitlines() if l.strip()]
    comm_items = []
    for cl in comm_lines[:4]:
        if ":" in cl:
            au, tx = cl.split(":", 1)
            comm_items.append({"author": au.replace("**", "").strip(), "ref": doc.get("refs", ""), "text": tx.replace("**", "").strip()})
        else:
            comm_items.append({"author": "Classical Tradition", "ref": doc.get("refs", ""), "text": cl.replace("**", "")})
    disc_lines = [re.sub(r"^\d+\.\s*", "", l).strip() for l in (doc.get("discussion_questions") or "").splitlines() if l.strip()]

    return {
        "deck_title": doc.get("title", "Torah Presentation"),
        "he_title": doc.get("he_title", ""),
        "subtitle": f"{doc.get('subtitle', '')} · {doc.get('refs', '')}",
        "art": en["art"],
        "slides": [
            {
                "type": "title",
                "kicker": f"Torah Story Presentation · {doc.get('refs', '')}",
                "title": doc.get("title", ""),
                "he_title": doc.get("he_title", ""),
                "subtitle": doc.get("subtitle", ""),
                "art": en["art"],
                "narration": f"Welcome to our presentation on {doc.get('title', '')}. {doc.get('subtitle', '')}.",
            },
            {
                "type": "story",
                "kicker": "1 · The Story",
                "title": doc.get("title", ""),
                "he_text": anchor_v.get("he_text", ""),
                "body": doc.get("kid_story", "") or doc.get("body_md", "")[:900],
                "art": en["art"],
                "narration": doc.get("kid_story", "")[:900],
            },
            {
                "type": "characters",
                "kicker": "2 · Main Characters",
                "title": "Meet the Voices in This Story",
                "characters": en["characters"],
                "narration": "Let's meet the main characters whose choices shape this timeless story.",
            },
            {
                "type": "symbols",
                "kicker": "3 · Sacred Symbols & Imagery",
                "title": "Symbols That Unlock the Meaning",
                "symbols": en["symbols"],
                "narration": "Every detail in the Torah carries enduring symbolic meaning.",
            },
            {
                "type": "commentators",
                "kicker": "4 · Classical Commentators & PaRDeS",
                "title": "Rashi, Ramban, Ibn Ezra & Midrash",
                "items": comm_items,
                "pardes": doc.get("adult_analysis", ""),
                "narration": " ".join(f"{c['author']}: {c['text'][:170]}" for c in comm_items[:2]),
            },
            {
                "type": "today",
                "kicker": "5 · Applying It in Today's Terms",
                "title": en["today_title"],
                "points": en["today_points"],
                "art": en["art"],
                "narration": f"Applying this in today's terms: {en['today_title']}. " + " ".join(en["today_points"]),
            },
            {
                "type": "discussion",
                "kicker": "6 · Shabbat Table & Synagogue Discussion",
                "title": "Conversation Starters",
                "questions": disc_lines or ["What lesson from this story resonates most with your life this week?"],
                "narration": "Questions for reflection together: " + " ".join(disc_lines[:2]),
            },
        ],
    }
