#!/usr/bin/env python3
"""
Torah Sanctuary OS — Living Liturgy, Psalms (Tehillim), Tefillin, Meal Blessings,
Sacred Songs (Zemirot), and Multi-Layered Holiday & High Holiday Historical Encyclopedia.

100% offline-capable, anchored directly in verbatim Hebrew + English verses from data/torah.db
and synchronized in real time with sacred_astronomy.py (Hebrew date, Zmanim, Shabbat & Festivals).
"""

from datetime import datetime
import sacred_astronomy
import torah_db


# =============================================================================
# 1. DAILY PSALMS (TEHILLIM): SHIR SHEL YOM (7-DAY TEMPLE CYCLE) + 30-DAY MONTHLY CYCLE
# =============================================================================

# Python weekday(): Mon=0..Sun=6 -> map to Jewish day of week (Sun=0..Sat=6)
SHIR_SHEL_YOM = {
    0: {
        "day_en": "Sunday (Yom Rishon)",
        "day_he": "יוֹם רִאשׁוֹן",
        "chapter": 24,
        "title": "Psalm 24 — 'The Earth Is the Lord's and All Its Fullness'",
        "he_intro": "הַיּוֹם יוֹם רִאשׁוֹן בַּשַּׁבָּת, שֶׁבּוֹ הָיוּ הַלְוִיִּם אוֹמְרִים בְּבֵית הַמִּקְדָּשׁ:",
        "temple_history": "Sung by the Levites in the Jerusalem Temple every Sunday (Talmud Rosh Hashanah 31a) to celebrate Day One of Creation — when God created the cosmos as sole Sovereign before any human hand had yet built a city.",
        "prominent_note": "Midrash & Talmud (Shabbat 30a) recount that when King Solomon carried the Ark into the First Temple, the massive golden gates refused to open until he sang Psalm 24:7–10 invoking the merit of his father King David!",
    },
    1: {
        "day_en": "Monday (Yom Sheni)",
        "day_he": "יוֹם שֵׁנִי",
        "chapter": 48,
        "title": "Psalm 48 — 'Great Is the Lord in the City of Our God'",
        "he_intro": "הַיּוֹם יוֹם שֵׁנִי בַּשַּׁבָּת, שֶׁבּוֹ הָיוּ הַלְוִיִּם אוֹמְרִים בְּבֵית הַמִּקְדָּשׁ:",
        "temple_history": "Sung every Monday commemorating Day Two of Creation when God separated the upper and lower waters and established His throne on high — mirrored on earth by Mount Zion in Jerusalem.",
        "prominent_note": "Composed by the Sons of Korach who chose Teshuvah (repentance) rather than joining their father's rebellion — turning ancestral shame into timeless sanctuary song.",
    },
    2: {
        "day_en": "Tuesday (Yom Shlishi)",
        "day_he": "יוֹם שְׁלִישִׁי",
        "chapter": 82,
        "title": "Psalm 82 — 'God Stands in the Divine Assembly of Justice'",
        "he_intro": "הַיּוֹם יוֹם שְׁלִישִׁי בַּשַּׁבָּת, שֶׁבּוֹ הָיוּ הַלְוִיִּם אוֹמְרִים בְּבֵית הַמִּקְדָּשׁ:",
        "temple_history": "Sung every Tuesday honoring Day Three when dry land appeared and humanity was called to build fair, compassionate courts defending the orphan, poor, and vulnerable.",
        "prominent_note": "Rabbi Akiva & the Sages cited Psalm 82:1 in Pirkei Avot 3:6 to prove that whenever even ten — or two — people gather to study Torah or pursue honest justice, the Divine Presence dwells among them.",
    },
    3: {
        "day_en": "Wednesday (Yom Revi'i)",
        "day_he": "יוֹם רְבִיעִי",
        "chapter": 94,
        "title": "Psalm 94 — 'O God of Justice, Shine Forth'",
        "he_intro": "הַיּוֹם יוֹם רְבִיעִי בַּשַּׁבָּת, שֶׁבּוֹ הָיוּ הַלְוִיִּם אוֹמְרִים בְּבֵית הַמִּקְדָּשׁ:",
        "temple_history": "Sung every Wednesday commemorating Day Four when Sun, Moon, and Stars were set in the heavens — rejecting pagan star-worship and affirming moral accountability.",
        "prominent_note": "According to the Talmud (Ta'anit 29a), the Levites were standing on the Temple platform singing Psalm 94:23 at the exact moment the Second Temple fell in 70 CE — leaving its closing promise on Israel's lips across exile.",
    },
    4: {
        "day_en": "Thursday (Yom Chamishi)",
        "day_he": "יוֹם חֲמִישִׁי",
        "chapter": 81,
        "title": "Psalm 81 — 'Sing Joyfully to God Our Strength! Sound the Shofar!'",
        "he_intro": "הַיּוֹם יוֹם חֲמִישִׁי בַּשַּׁבָּת, שֶׁבּוֹ הָיוּ הַלְוִיִּם אוֹמְרִים בְּבֵית הַמִּקְדָּשׁ:",
        "temple_history": "Sung every Thursday honoring Day Five (birds and sea life filling creation with song) — celebrating Joseph's release from Egypt's prison on Rosh Hashanah and the sounding of the Shofar.",
        "prominent_note": "Verse 4 ('Sound the Shofar at the New Moon, on the hidden day of our festival') is the Talmud's anchor verse explaining why Rosh Hashanah falls on the 1st of Tishrei when the crescent moon is newly hidden.",
    },
    5: {
        "day_en": "Friday (Yom Shishi)",
        "day_he": "יוֹם שִׁשִּׁי",
        "chapter": 93,
        "title": "Psalm 93 — 'The Lord Reigns, Robed in Majesty'",
        "he_intro": "הַיּוֹם יוֹם שִׁשִּׁי בַּשַּׁבָּת, שֶׁבּוֹ הָיוּ הַלְוִיִּם אוֹמְרִים בְּבֵית הַמִּקְדָּשׁ:",
        "temple_history": "Sung every Friday commemorating Day Six when humanity was created to recognize the Creator — and repeated every Friday evening at Kabbalat Shabbat as the world crowns Shabbat.",
        "prominent_note": "Rashi notes the world was incomplete until Adam stood up on Friday afternoon and proclaimed 'The Lord reigns!' — making conscious human gratitude the crown of Creation.",
    },
    6: {
        "day_en": "Shabbat (Yom HaShabbat)",
        "day_he": "יוֹם שַׁבָּת קֹדֶשׁ",
        "chapter": 92,
        "title": "Psalm 92 — 'Mizmor Shir L'Yom HaShabbat' (A Psalm for the Sabbath Day)",
        "he_intro": "הַיּוֹם יוֹם שַׁבָּת קֹדֶשׁ, שֶׁבּוֹ הָיוּ הַלְוִיִּם אוֹמְרִים בְּבֵית הַמִּקְדָּשׁ:",
        "temple_history": "Sung every Shabbat in the Temple and at every Friday night Kabbalat Shabbat worldwide — celebrating a world completely at peace ('a day that is wholly Shabbat and rest for eternal life').",
        "prominent_note": "Midrash Bereishit Rabbah (22:13) teaches that Adam himself composed Psalm 92 on the very first Shabbat after experiencing Teshuvah and waking up to the mercy of the Seventh Day!",
    },
}

# Classic Chabad / Traditional 30-Day Monthly Tehillim Cycle (day 1..30 -> list of Psalm chapters)
MONTHLY_TEHILLIM = {
    1: list(range(1, 10)),       2: list(range(10, 18)),      3: list(range(18, 23)),
    4: list(range(23, 29)),      5: list(range(29, 35)),      6: list(range(35, 39)),
    7: list(range(39, 44)),      8: list(range(44, 49)),      9: list(range(49, 55)),
    10: list(range(55, 60)),     11: list(range(60, 66)),     12: list(range(66, 69)),
    13: list(range(69, 72)),     14: list(range(72, 77)),     15: list(range(77, 79)),
    16: list(range(79, 83)),     17: list(range(83, 88)),     18: list(range(88, 90)),
    19: list(range(90, 97)),     20: list(range(97, 104)),    21: list(range(104, 106)),
    22: list(range(106, 108)),   23: list(range(108, 113)),   24: list(range(113, 119)),
    25: [119],                   26: [119],                   27: list(range(120, 135)),
    28: list(range(135, 140)),   29: list(range(140, 145)),   30: list(range(145, 151)),
}

TOPICAL_PSALMS = [
    {"chapter": 23, "tag": "Comfort & Trust", "title": "Psalm 23 — 'The Lord Is My Shepherd'", "note": "King David's timeless song of calm trust through shadowed valleys; sung at Shabbat meals."},
    {"chapter": 20, "tag": "Healing & Protection", "title": "Psalm 20 — 'May God Answer You in Distress'", "note": "Recited worldwide in synagogues for healing (Refuah Shleimah), safety, and peace."},
    {"chapter": 27, "tag": "Courage & High Holidays", "title": "Psalm 27 — 'L'David Hashem Ori'", "note": "Recited morning and evening throughout Elul, Rosh Hashanah, Yom Kippur & Sukkot."},
    {"chapter": 100, "tag": "Pure Gratitude", "title": "Psalm 100 — 'Mizmor L'Todah'", "note": "Song of Thanksgiving: 'Serve God with joy; come before Him with song!'"},
    {"chapter": 121, "tag": "Travel & Guardian", "title": "Psalm 121 — 'I Lift My Eyes to the Mountains'", "note": "Song of Ascents recited for protection, journeys, and steadfast faith."},
    {"chapter": 130, "tag": "Repentance & Hope", "title": "Psalm 130 — 'Out of the Depths I Call'", "note": "Recited during the Ten Days of Teshuvah and times of deep heartfelt prayer."},
    {"chapter": 150, "tag": "Symphony of Praise", "title": "Psalm 150 — 'Let Every Breath Praise God'", "note": "The grand finale of Tehillim: trumpets, harp, lyre, timbrel, dance, and strings."},
]


# =============================================================================
# 2. TEFILLIN, TALLIT & MORNING PRAYERS (COMPLETE GUIDED COMPANION)
# =============================================================================

TEFILLIN_AND_MORNING = {
    "overview": {
        "title": "Tallit, Tefillin & Morning Awakening (Shacharit)",
        "he_title": "טַלִּית, תְּפִלִּין וּבִרְכוֹת הַשַּׁחַר",
        "source_ref": "Deuteronomy 6:8 · 11:18 · Exodus 13:9, 16 · Hosea 2:21–22",
        "meaning": "Tefillin unite mind (Shel Rosh — opposite the brain), heart (Shel Yad — facing the heart on the bicep), and action (bound down the arm and hand), aligning intellect, emotion, and daily deeds in service of God and ethics.",
        "history": "Archaeologists uncovered intact 2,000-year-old Tefillin scrolls at Qumran (Dead Sea Scrolls, c. 1st century BCE) containing the exact four Torah passages worn by Jews today — word for word identical!",
    },
    "steps": [
        {
            "step": "1",
            "title": "Modeh Ani — First Words Upon Waking",
            "he_title": "מוֹדֶה אֲנִי",
            "when": "Immediately upon opening your eyes (even before washing hands)",
            "hebrew": "מוֹדֶה אֲנִי לְפָנֶיךָ מֶלֶךְ חַי וְקַיָּם, שֶׁהֶחֱזַרְתָּ בִּי נִשְׁמָתִי בְּחֶמְלָה, רַבָּה אֱמוּנָתֶךָ.",
            "translit": "Modeh ani l'fanecha, Melech chai v'kayam, shehechezarta bi nishmati b'chemlah, rabbah emunatecha.",
            "english": "I gratefully thank You, living and enduring King, for You have returned my soul within me with compassion — great is Your faithfulness!",
            "note": "Women say 'Modah ani' (מוֹדָה אֲנִי). Notice we begin every morning with gratitude ('Modeh') before 'I' ('Ani').",
        },
        {
            "step": "2",
            "title": "Netilat Yadayim & Birchot HaTorah",
            "he_title": "נְטִילַת יָדַיִם וּבִרְכוֹת הַתּוֹרָה",
            "when": "Upon washing hands alternating 3× right/left & before studying Torah",
            "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ לַעֲסֹק בְּדִבְרֵי תוֹרָה.",
            "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, asher kid'shanu b'mitzvotav v'tzivanu la'asok b'divrei Torah.",
            "english": "Blessed are You, Lord our God, King of the universe, Who has sanctified us with His commandments and commanded us to immerse ourselves in the words of Torah.",
            "note": "Notice it says 'la'asok' — to engage/immerse in Torah — celebrating the joyful journey of learning, not merely memorizing.",
        },
        {
            "step": "3",
            "title": "Tallit (Prayer Shawl) — Wrapping in Light",
            "he_title": "עֲטִיפַת טַלִּית",
            "when": "Standing, from Misheyakir (earliest morning light) onward",
            "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ לְהִתְעַטֵּף בַּצִּיצִית.",
            "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, asher kid'shanu b'mitzvotav v'tzivanu l'hit'atef ba'tzitzit.",
            "english": "Blessed are You, Lord our God, King of the universe, Who has sanctified us with His commandments and commanded us to wrap ourselves in Tzitzit.",
            "note": "Inspect the four knotted fringes before blessing, wrap the Tallit over head & shoulders like a canopy of presence, then drape gracefully over both shoulders.",
        },
        {
            "step": "4",
            "title": "Tefillin Shel Yad (Arm) — Binding Heart & Strength",
            "he_title": "תְּפִלִּין שֶׁל יָד",
            "when": "Weekdays (Sun–Fri) from Misheyakir until Sunset — NOT worn on Shabbat or Yom Tov",
            "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ לְהָנִיחַ תְּפִלִּין.",
            "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, asher kid'shanu b'mitzvotav v'tzivanu l'haniach tefillin.",
            "english": "Blessed are You, Lord our God, King of the universe, Who has sanctified us with His commandments and commanded us to put on Tefillin.",
            "note": "Place on the weaker bicep (left arm for right-handers), angled inward facing the heart. Tighten after the blessing and wrap 7 full coils down the forearm (Chabad/Sefard wrap outward; Ashkenaz wrap inward). Do not speak until the Head Tefillin is placed!",
        },
        {
            "step": "5",
            "title": "Tefillin Shel Rosh (Head) — Crown of Mind & Clarity",
            "he_title": "תְּפִלִּין שֶׁל רֹאשׁ",
            "when": "Immediately after the 7 forearm wraps (with zero interruption)",
            "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ עַל מִצְוַת תְּפִלִּין. בָּרוּךְ שֵׁם כְּבוֹד מַלְכוּתוֹ לְעוֹלָם וָעֶד.",
            "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, asher kid'shanu b'mitzvotav v'tzivanu al mitzvat tefillin. (Ashkenaz custom; Sefard/Chabad omit second blessing unless interrupted.) Baruch shem k'vod malchuto l'olam va'ed.",
            "english": "Blessed are You, Lord our God, King of the universe, Who has sanctified us with His commandments and commanded us concerning the mitzvah of Tefillin. Blessed is the Name of His glorious kingdom forever and ever.",
            "note": "Center the box high above the hairline (never on the forehead below the hairline), centered directly between the eyes, with the knot resting at the base of the skull.",
        },
        {
            "step": "6",
            "title": "Binding the Finger — The Three Eternal Vows of Hosea",
            "he_title": "וְאֵרַשְׂתִּיךְ לִי לְעוֹלָם",
            "when": "Wrapping the remaining strap 3 times around the middle finger (forming the Hebrew letter Shin/Dalet)",
            "hebrew": "וְאֵרַשְׂתִּיךְ לִי לְעוֹלָם, וְאֵרַשְׂתִּיךְ לִי בְּצֶדֶק וּבְמִשְׁפָּט וּבְחֶסֶד וּבְרַחֲמִים, וְאֵרַשְׂתִּיךְ לִי בֶּאֱמוּנָה וְיָדַעַתְּ אֶת ה׳.",
            "translit": "V'erastich li l'olam; v'erastich li b'tzedek u'v'mishpat u'v'chesed u'v'rachamim; v'erastich li b'emunah, v'yada'at et Adonai.",
            "english": "I will betroth you to Me forever; I will betroth you to Me in righteousness, justice, loving-kindness, and compassion; I will betroth you to Me in faithfulness, and you shall know the Lord. (Hosea 2:21–22)",
            "note": "Like wedding rings between Israel and Heaven — wrapping the strap around the finger pledges every weekday's work to justice, kindness, and compassion.",
        },
        {
            "step": "7",
            "title": "Shema Yisrael — Declaration of Oneness",
            "he_title": "שְׁמַע יִשְׂרָאֵל",
            "when": "Covering the eyes with the right hand, concentrating deeply on the Unity of God",
            "hebrew": "שְׁמַע יִשְׂרָאֵל ה׳ אֱלֹהֵינוּ ה׳ אֶחָד. (בָּרוּךְ שֵׁם כְּבוֹד מַלְכוּתוֹ לְעוֹלָם וָעֶד.) וְאָהַבְתָּ אֵת ה׳ אֱלֹהֶיךָ בְּכָל־לְבָבְךָ וּבְכָל־נַפְשְׁךָ וּבְכָל־מְאֹדֶךָ... וּקְשַׁרְתָּם לְאוֹת עַל־יָדֶךָ וְהָיוּ לְטֹטָפֹת בֵּין עֵינֶיךָ.",
            "translit": "Shema Yisrael, Adonai Eloheinu, Adonai Echad! (Whispered: Baruch shem k'vod malchuto l'olam va'ed.) V'ahavta et Adonai Elohecha b'chol l'vavcha u'v'chol nafsh'cha u'v'chol m'odecha...",
            "english": "Hear, O Israel: the Lord our God, the Lord is One! (Blessed is the Name of His glorious kingdom forever and ever.) You shall love the Lord your God with all your heart, with all your soul, and with all your might... Bind them as a sign upon your hand and as frontlets between your eyes. (Deuteronomy 6:4–9)",
            "note": "The enlarged Ayin (ע) of Shema and Dalet (ד) of Echad spell 'Ed' (עֵד — Witness).",
        },
    ],
}


# =============================================================================
# 3. BEFORE & AFTER DINNER / MEAL BLESSINGS (BRACHOT & BIRKAT HAMAZON)
# =============================================================================

BEFORE_MEAL_BLESSINGS = [
    {
        "id": "netilat",
        "emoji": "💧",
        "name": "Netilat Yadayim (Washing Hands for Bread)",
        "he_name": "עַל נְטִילַת יָדַיִם",
        "for_foods": "Before eating any bread or Challah meal (pour 2× or 3× on each hand, bless, dry hands, stay silent until HaMotzi)",
        "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ עַל נְטִילַת יָדָיִם.",
        "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, asher kid'shanu b'mitzvotav v'tzivanu al netilat yadayim.",
        "english": "Blessed are You, Lord our God, King of the universe, Who has sanctified us with His commandments and commanded us concerning the washing of hands.",
    },
    {
        "id": "hamotzi",
        "emoji": "🍞",
        "name": "HaMotzi (Bread & Shabbat Challah)",
        "he_name": "הַמּוֹצִיא לֶחֶם מִן הָאָרֶץ",
        "for_foods": "Challah, loaves, pita, rolls, matzah — covers the entire seated dinner!",
        "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, הַמּוֹצִיא לֶחֶם מִן הָאָרֶץ.",
        "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, hamotzi lechem min ha'aretz.",
        "english": "Blessed are You, Lord our God, King of the universe, Who brings forth bread from the earth.",
    },
    {
        "id": "hagafen",
        "emoji": "🍷",
        "name": "Borei Pri HaGafen (Wine & Grape Juice)",
        "he_name": "בּוֹרֵא פְּרִי הַגָּפֶן",
        "for_foods": "Kiddush wine, grape juice, Havdalah & celebratory toasts (L'Chaim!)",
        "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, בּוֹרֵא פְּרִי הַגָּפֶן.",
        "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, borei pri hagafen.",
        "english": "Blessed are You, Lord our God, King of the universe, Who creates the fruit of the vine.",
    },
    {
        "id": "mezonot",
        "emoji": "🥐",
        "name": "Borei Minei Mezonot (Grain, Cake, Pasta, Rice)",
        "he_name": "בּוֹרֵא מִינֵי מְזוֹנוֹת",
        "for_foods": "Pastries, cookies, kugel, crackers, oatmeal, pasta, cooked rice",
        "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, בּוֹרֵא מִינֵי מְזוֹנוֹת.",
        "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, borei minei mezonot.",
        "english": "Blessed are You, Lord our God, King of the universe, Who creates various kinds of nourishment.",
    },
    {
        "id": "haetz",
        "emoji": "🍎",
        "name": "Borei Pri HaEtz (Fruits of the Tree)",
        "he_name": "בּוֹרֵא פְּרִי הָעֵץ",
        "for_foods": "Apples, pomegranates, figs, dates, grapes, olives, oranges, almonds, walnuts",
        "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, בּוֹרֵא פְּרִי הָעֵץ.",
        "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, borei pri ha'etz.",
        "english": "Blessed are You, Lord our God, King of the universe, Who creates the fruit of the tree.",
    },
    {
        "id": "haadamah",
        "emoji": "🥕",
        "name": "Borei Pri HaAdamah (Vegetables & Ground Produce)",
        "he_name": "בּוֹרֵא פְּרִי הָאֲדָמָה",
        "for_foods": "Salads, potatoes, carrots, tomatoes, bananas, berries, melons, peanuts",
        "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, בּוֹרֵא פְּרִי הָאֲדָמָה.",
        "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, borei pri ha'adamah.",
        "english": "Blessed are You, Lord our God, King of the universe, Who creates the fruit of the earth.",
    },
    {
        "id": "shehakol",
        "emoji": "💧",
        "name": "Shehakol Nihiyah Bidvaro (Drinks, Meat, Fish, Dairy)",
        "he_name": "שֶׁהַכֹּל נִהְיָה בִּדְבָרוֹ",
        "for_foods": "Water, coffee, tea, juice, soup, chicken, fish, eggs, cheese, chocolate",
        "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, שֶׁהַכֹּל נִהְיָה בִּדְבָרוֹ.",
        "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, shehakol nihiyah bidvaro.",
        "english": "Blessed are You, Lord our God, King of the universe, through Whose word everything came into being.",
    },
]

AFTER_MEAL_BLESSINGS = {
    "birkat_hamazon": {
        "title": "Birkat HaMazon — Grace After Meals (After Bread)",
        "he_title": "בִּרְכַּת הַמָּזוֹן",
        "source_ref": "Deuteronomy 8:10 · Talmud Berakhot 48b",
        "history": "The Torah's own commandment of gratitude: 'You shall eat, be satisfied, and bless the Lord your God' (Deut. 8:10). The Talmud teaches each of the four blessings was composed at a landmark moment in Jewish history: Moses (Manna in Sinai), Joshua (entering Israel), David & Solomon (Jerusalem & Temple), and the Sages of Yavneh (resilience after Betar)!",
        "sections": [
            {
                "num": "0 · Opening Song",
                "title": "Shir HaMa'alot (Psalm 126 — Shabbat & Festivals)",
                "hebrew": "שִׁיר הַמַּעֲלוֹת, בְּשׁוּב ה׳ אֶת־שִׁיבַת צִיּוֹן הָיִינוּ כְּחֹלְמִים. אָז יִמָּלֵא שְׂחוֹק פִּינוּ וּלְשׁוֹנֵנוּ רִנָּה...",
                "translit": "Shir hama'alot, b'shuv Adonai et shivat Tzion hayinu k'cholmim. Az yimalei s'chok pinu u'l'shoneinu rinah...",
                "english": "A Song of Ascents: When the Lord restored the returnees to Zion, we were like dreamers! Then our mouths were filled with laughter and our tongues with joyful song.",
            },
            {
                "num": "Zimmun (3+ Adults)",
                "title": "Communal Invitation to Bless Together",
                "hebrew": "רַבּוֹתַי נְבָרֵךְ! — יְהִי שֵׁם ה׳ מְבֹרָךְ מֵעַתָּה וְעַד עוֹלָם. — נְבָרֵךְ (בַּעֲשָׂרָה: אֱלֹהֵינוּ) שֶׁאָכַלְנוּ מִשֶּׁלּוֹ. — בָּרוּךְ שֶׁאָכַלְנוּ מִשֶּׁלּוֹ וּבְטוּבוֹ חָיִינוּ.",
                "translit": "Leader: Rabotai n'varech! All: Y'hi shem Adonai m'vorach mei'atah v'ad olam. Leader: N'varech (with 10+: Eloheinu) she'achalnu mishelo. All: Baruch she'achalnu mishelo u'v'tuvo chayinu!",
                "english": "Friends, let us bless! — May the Name of God be blessed now and forever. — Let us bless Him of Whose bounty we have eaten! — Blessed is He of Whose bounty we have eaten and through Whose goodness we live!",
            },
            {
                "num": "Blessing 1 · Moses",
                "title": "Birkat HaZan — Sustainer of All Living Creatures",
                "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, הַזָּן אֶת־הָעוֹלָם כֻּלּוֹ בְּטוּבוֹ בְּחֵן בְּחֶסֶד וּבְרַחֲמִים... בָּרוּךְ אַתָּה ה׳, הַזָּן אֶת־הַכֹּל.",
                "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, hazan et ha'olam kulo b'tuvo, b'chein b'chesed u'v'rachamim... Baruch atah Adonai, hazan et hakol.",
                "english": "Blessed are You, Lord our God, King of the universe, Who nourishes the entire world with goodness, grace, loving-kindness, and compassion... Blessed are You, Lord, Who nourishes all.",
            },
            {
                "num": "Blessing 2 · Joshua",
                "title": "Birkat HaAretz — Gratitude for Land, Covenant & Torah",
                "hebrew": "נוֹדֶה לְךָ ה׳ אֱלֹהֵינוּ עַל שֶׁהִנְחַלְתָּ לַאֲבוֹתֵינוּ אֶרֶץ חֶמְדָּה טוֹבָה וּרְחָבָה... וְעַל תּוֹרָתְךָ שֶׁלִּמַּדְתָּנוּ... בָּרוּךְ אַתָּה ה׳, עַל הָאָרֶץ וְעַל הַמָּזוֹן.",
                "translit": "Nodeh l'cha Adonai Eloheinu al shehinchalta la'avoteinu eretz chemdah tovah u'r'chavah... v'al Torat'cha shelimadtanu... Baruch atah Adonai, al ha'aretz v'al hamazon.",
                "english": "We thank You, Lord our God, for giving our ancestors a desirable, good, and spacious Land, for Your covenant and Your Torah which You taught us... Blessed are You, Lord, for the Land and for the food.",
            },
            {
                "num": "Blessing 3 · David & Solomon",
                "title": "Boneh Yerushalayim — Compassion & Rebuilding Jerusalem",
                "hebrew": "רַחֵם נָא ה׳ אֱלֹהֵינוּ עַל יִשְׂרָאֵל עַמֶּךָ וְעַל יְרוּשָׁלַיִם עִירֶךָ... וּבְנֵה יְרוּשָׁלַיִם עִיר הַקֹּדֶשׁ בִּמְהֵרָה בְיָמֵינוּ. בָּרוּךְ אַתָּה ה׳, בּוֹנֵה בְרַחֲמָיו יְרוּשָׁלָיִם. אָמֵן.",
                "translit": "Rachem na Adonai Eloheinu al Yisrael amecha v'al Yerushalayim irecha... U'v'nei Yerushalayim ir hakodesh bimheira v'yameinu. Baruch atah Adonai, boneh v'rachamav Yerushalayim. Amen.",
                "english": "Have compassion, Lord our God, upon Israel Your people and upon Jerusalem Your city... Rebuild Jerusalem the holy city speedily in our days. Blessed are You, Lord, Who in His mercy rebuilds Jerusalem. Amen.",
            },
            {
                "num": "Blessing 4 · Sages of Yavneh",
                "title": "HaTov v'HaMeitiv — Goodness, Hospitality & Peace",
                "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם... הָאֵל הַטּוֹב וְהַמֵּטִיב לַכֹּל... עֹשֶׂה שָׁלוֹם בִּמְרוֹמָיו הוּא יַעֲשֶׂה שָׁלוֹם עָלֵינוּ וְעַל כָּל־יִשְׂרָאֵל, וְאִמְרוּ אָמֵן.",
                "translit": "Baruch atah Adonai Eloheinu Melech ha'olam... ha'El hatov v'hameitiv lakol... Oseh shalom bimromav, Hu ya'aseh shalom aleinu v'al kol Yisrael, v'imru Amen.",
                "english": "Blessed are You, Lord our God, King of the universe, the God Who is good and does good to all... May He Who makes peace in His heights make peace for us and for all Israel — Amen!",
            },
        ],
    },
    "short_after": [
        {
            "id": "al-hamichyah",
            "title": "Al HaMichyah / Me'ein Shalosh (After Pastry, Wine, or Seven Species)",
            "he_title": "בְּרָכָה מֵעֵין שָׁלוֹשׁ (עַל הַמִּחְיָה)",
            "for_foods": "After Mezonot (cake/pasta), Wine/Grape Juice (Al HaGefen), or Figs, Pomegranates, Olives, Dates, Grapes (Al HaEtz)",
            "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, עַל הַמִּחְיָה וְעַל הַכַּלְכָּלָה (עַל הַגֶּפֶן / עַל הָעֵץ)... וְעַל אֶרֶץ חֶמְדָּה טוֹבָה וּרְחָבָה... בָּרוּךְ אַתָּה ה׳, עַל הָאָרֶץ וְעַל הַמִּחְיָה.",
            "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, al hamichyah v'al hakalkalah (or al hagefen / al ha'etz)... v'al eretz chemdah tovah u'r'chavah... Baruch atah Adonai, al ha'aretz v'al hamichyah.",
            "english": "Blessed are You, Lord our God, King of the universe, for the nourishment and sustenance (or vine / tree fruit) and for the good, spacious Land You gave our ancestors... Blessed are You, Lord, for the Land and the nourishment.",
        },
        {
            "id": "borei-nefashot",
            "title": "Borei Nefashot (After Drinks, Fruit, Vegetables, Meat, Dairy)",
            "he_title": "בּוֹרֵא נְפָשׁוֹת רַבּוֹת",
            "for_foods": "After water, coffee, apples, salads, meat, fish, snacks — anything other than Bread or Me'ein Shalosh",
            "hebrew": "בָּרוּךְ אַתָּה ה׳ אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם, בּוֹרֵא נְפָשׁוֹת רַבּוֹת וְחֶסְרוֹנָן עַל כָּל־מַה שֶּׁבָּרָא לְהַחֲיוֹת בָּהֶם נֶפֶשׁ כָּל־חָי. בָּרוּךְ חֵי הָעוֹלָמִים.",
            "translit": "Baruch atah Adonai Eloheinu Melech ha'olam, borei nefashot rabot v'chesronan, al kol mah shebara l'hachayot bahem nefesh kol chai. Baruch chei ha'olamim.",
            "english": "Blessed are You, Lord our God, King of the universe, Who creates countless living beings and their needs, for all that He created to sustain the soul of every living thing. Blessed is the Life of all worlds.",
        },
    ],
}


# =============================================================================
# 4. SACRED SONGS & ZEMIROT SONGBOOK (SHABBAT, HAVDALAH, HOLIDAYS & DAILY JOY)
# =============================================================================

SACRED_SONGS = [
    {
        "slug": "shalom-aleichem",
        "title": "Shalom Aleichem (Peace Unto You, Ministering Angels)",
        "he_title": "שָׁלוֹם עֲלֵיכֶם",
        "occasion": "Friday Night · Before Kiddush",
        "composer": "Kabbalists of Safed (17th Century) · Based on Talmud Shabbat 119b",
        "art": "/art/creation-shabbat.jpg",
        "hebrew": "שָׁלוֹם עֲלֵיכֶם מַלְאֲכֵי הַשָּׁרֵת מַלְאֲכֵי עֶלְיוֹן, מִמֶּלֶךְ מַלְכֵי הַמְּלָכִים הַקָּדוֹשׁ בָּרוּךְ הוּא.\nבּוֹאֲכֶם לְשָׁלוֹם... בָּרְכוּנִי לְשָׁלוֹם... צֵאתְכֶם לְשָׁלוֹם...",
        "translit": "Shalom aleichem malachei hasharet, malachei Elyon, miMelech malchei hamelachim HaKadosh Baruch Hu.\nBo'achem l'shalom... Barchuni l'shalom... Tzeit'chem l'shalom...",
        "english": "Peace be upon you, ministering angels, messengers of the Most High, from the Supreme King of Kings, the Holy One, Blessed be He! May your coming be in peace; bless me with peace; may your departure be in peace!",
        "story": "Talmud Shabbat 119b tells that two angels escort every Jew home from synagogue on Friday evening; seeing lit candles, a set table, and peaceful warmth, they bless the home: 'May it be like this next Shabbat too!'",
    },
    {
        "slug": "lecha-dodi",
        "title": "Lecha Dodi (Come, My Beloved, to Meet the Shabbat Bride)",
        "he_title": "לְכָה דוֹדִי",
        "occasion": "Friday Evening · Kabbalat Shabbat",
        "composer": "Rabbi Shlomo Alkabetz (Safed, c. 1540 CE) — Acrostic spells 'Shlomo HaLevi'",
        "art": "/art/creation-shabbat.jpg",
        "hebrew": "לְכָה דוֹדִי לִקְרַאת כַּלָּה, פְּנֵי שַׁבָּת נְקַבְּלָה.\nשָׁמוֹר וְזָכוֹר בְּדִבּוּר אֶחָד, הִשְׁמִיעָנוּ אֵל הַמְּיוּחָד...\nבּוֹאִי בְשָׁלוֹם עֲטֶרֶת בַּעְלָהּ, גַּם בְּשִׂמְחָה וּבְצָהֳלָה!",
        "translit": "Lecha dodi likrat kalah, p'nei Shabbat n'kabelah.\nShamor v'zachor b'dibur echad, hishmi'anu El hameyuchad...\nBo'i v'shalom ateret ba'alah, gam b'simchah u'v'tzaholah!",
        "english": "Come, my beloved, to welcome the Bride; let us greet the presence of Shabbat! 'Guard' and 'Remember' in one single utterance the One God caused us to hear... Enter in peace, crown of your Beloved, with joy and gladness!",
        "story": "Every Friday before sunset, Rabbi Isaac Luria (the Arizal) and his disciples dressed in white and walked into the olive fields of Safed singing Lecha Dodi toward the sunset — bowing toward the west on the final verse!",
    },
    {
        "slug": "eshet-chayil",
        "title": "Eshet Chayil (A Woman of Valor)",
        "he_title": "אֵשֶׁת חַיִל",
        "occasion": "Friday Night · Honoring Wife, Mother & Home",
        "composer": "King Solomon · Proverbs 31:10–31 (Hebrew Alef–Tav Acrostic)",
        "art": "/art/ruth-harvest.jpg",
        "hebrew": "אֵשֶׁת חַיִל מִי יִמְצָא וְרָחֹק מִפְּנִינִים מִכְרָהּ... פִּיהָ פָּתְחָה בְחָכְמָה וְתוֹרַת חֶסֶד עַל לְשׁוֹנָהּ... רַבּוֹת בָּנוֹת עָשׂוּ חָיִל וְאַתְּ עָלִית עַל כֻּלָּנָה!",
        "translit": "Eshet chayil mi yimtza, v'rachok mip'ninim michrah... Piha pat'chah v'chochmah, v'Torat chesed al l'shonah... Rabot banot asu chayil, v'at alit al kulanah!",
        "english": "A woman of valor, who can find? Her worth is far beyond rubies... She opens her mouth with wisdom, and the Torah of loving-kindness is on her tongue... Many daughters have done valiantly, yet you surpass them all!",
        "story": "Midrash Mishlei links each of the 22 verses (Alef to Tav) to the great heroines of Israel — Sarah, Rebecca, Rachel, Leah, Miriam, Deborah, Ruth, Hannah, and Queen Esther!",
    },
    {
        "slug": "yedid-nefesh",
        "title": "Yedid Nefesh (Beloved of the Soul)",
        "he_title": "יְדִיד נֶפֶשׁ",
        "occasion": "Kabbalat Shabbat & Seudah Shlishit (Shabbat Twilight)",
        "composer": "Rabbi Elazar Azikri (Safed, 1588 CE) — Acrostic spells God's Four-Letter Name",
        "art": "/art/jacobs-ladder.jpg",
        "hebrew": "יְדִיד נֶפֶשׁ אָב הָרַחֲמָן, מְשׁוֹךְ עַבְדְּךָ אֶל רְצוֹנֶךָ, יָרוּץ עַבְדְּךָ כְּמוֹ אַיָּל, יִשְׁתַּחֲוֶה אֶל מוּל הֲדָרֶךָ.",
        "translit": "Yedid nefesh Av harachaman, m'shoch avd'cha el r'tzonecha; yarutz avd'cha k'mo ayal, yishtachaveh el mul hadarecha.",
        "english": "Beloved of the soul, Compassionate Father, draw Your servant toward Your will! Your servant will run swiftly like a deer to bow before Your majesty.",
        "story": "Written by Rabbi Elazar Azikri (Sefer Charedim) in 16th-century Safed — sung softly at dusk during the Third Shabbat Meal as the sky turns sapphire and gold.",
    },
    {
        "slug": "adon-olam",
        "title": "Adon Olam (Master of the Universe)",
        "he_title": "אֲדוֹן עוֹלָם",
        "occasion": "Daily Morning, Shabbat Closing & Bedtime Shema",
        "composer": "Attributed to Rabbi Solomon ibn Gabirol (Spain, 11th Century)",
        "art": "/art/abraham-stars.jpg",
        "hebrew": "אֲדוֹן עוֹלָם אֲשֶׁר מָלַךְ בְּטֶרֶם כָּל־יְצִיר נִבְרָא... בְּיָדוֹ אַפְקִיד רוּחִי בְּעֵת אִישַׁן וְאָעִירָה, וְעִם רוּחִי גְּוִיָּתִי, ה׳ לִי וְלֹא אִירָא!",
        "translit": "Adon olam asher malach b'terem kol yetzir nivra... B'yado afkid ruchi b'et ishan v'a'irah, v'im ruchi g'viyati, Adonai li v'lo ira!",
        "english": "Master of the universe, Who reigned before any form was created... Into His hand I entrust my spirit when I sleep and when I wake; and with my spirit, my body too — the Lord is with me, I shall not fear!",
        "story": "Because its poetic meter is pure iambic rhythm, synagogues around the world joyfully sing Adon Olam to dozens of beloved melodies — closing Shabbat morning services with children leading from the Bimah!",
    },
    {
        "slug": "dror-yikra",
        "title": "Dror Yikra (He Shall Proclaim Freedom)",
        "he_title": "דְּרוֹר יִקְרָא",
        "occasion": "Shabbat Day Table Song (Zemirot)",
        "composer": "Dunash ben Labrat (Baghdad & Cordoba, c. 960 CE) — Acrostic spells 'Dunash'",
        "art": "/art/promised-land.jpg",
        "hebrew": "דְּרוֹר יִקְרָא לְבֵן עִם בַּת, וְיִנְצָרְכֶם כְּמוֹ בָבַת, נְעִים שִׁמְכֶם וְלֹא יֻשְׁבַּת, שְׁבוּ וְנוּחוּ בְּיוֹם שַׁבָּת!",
        "translit": "Dror yikra l'ven im bat, v'yintzorchem k'mo vavat; na'im shimchem v'lo yushbat, sh'vu v'nuchu b'yom Shabbat!",
        "english": "He shall proclaim freedom to son and daughter alike, and guard you like the apple of His eye! Sweet is your name and it shall never cease — sit and rest in joy on the Shabbat day!",
        "story": "One of the oldest surviving Hebrew Shabbat table songs (over 1,050 years old!), written in Golden Age Spain by the student of Rabbi Saadia Gaon — cherished equally by Ashkenazi, Sephardi, and Yemenite tables.",
    },
    {
        "slug": "eliyahu-hanavi",
        "title": "Eliyahu HaNavi (Elijah the Prophet — Havdalah Song)",
        "he_title": "אֵלִיָּהוּ הַנָּבִיא",
        "occasion": "Saturday Night · Immediately After Havdalah",
        "composer": "Traditional Medieval Ashkenazi & Sephardi Zemirah (Malachi 3:23)",
        "art": "/art/elijah-horeb.jpg",
        "hebrew": "אֵלִיָּהוּ הַנָּבִיא, אֵלִיָּהוּ הַתִּשְׁבִּי, אֵלִיָּהוּ הַגִּלְעָדִי — בִּמְהֵרָה בְיָמֵינוּ יָבוֹא אֵלֵינוּ עִם מָשִׁיחַ בֶּן דָּוִד!",
        "translit": "Eliyahu haNavi, Eliyahu haTishbi, Eliyahu haGiladi — bimheirah v'yameinu yavo eleinu, im Mashiach ben David!",
        "english": "Elijah the Prophet, Elijah the Tishbite, Elijah of Gilead — speedily in our days may he come to us, bringing peace and redemption!",
        "story": "Talmud Eruvin 43b notes Elijah will not arrive on Shabbat to disturb our rest — so the moment three stars appear Saturday night, families sing Eliyahu HaNavi with braided candle and spices to greet the new week with hope!",
    },
    {
        "slug": "maoz-tzur",
        "title": "Maoz Tzur (Rock of Ages — Chanukah Anthem)",
        "he_title": "מָעוֹז צוּר יְשׁוּעָתִי",
        "occasion": "Chanukah · Every Night After Lighting the Menorah",
        "composer": "Mordechai (13th-Century Germany — Acrostic spells 'Mordechai Chazak')",
        "art": "/art/solomon-temple.jpg",
        "hebrew": "מָעוֹז צוּר יְשׁוּעָתִי לְךָ נָאֶה לְשַׁבֵּחַ, תִּכּוֹן בֵּית תְּפִלָּתִי וְשָׁם תּוֹדָה נְזַבֵּחַ... יְוָנִים נִקְבְּצוּ עָלַי... וּמִנּוֹתַר קַנְקַנִּים נַעֲשָׂה נֵס לַשּׁוֹשַׁנִּים!",
        "translit": "Maoz tzur yeshu'ati, l'cha na'eh l'shabeiach; tikon beit t'filati, v'sham todah n'zabeiach... Yevanim nikb'tzu alai... u'minotar kankanim na'asah nes lashoshanim!",
        "english": "Mighty Rock of my salvation, to You it is fitting to sing praise! Restore my House of Prayer, and there we shall offer thanksgiving... From the one remaining sealed cruse of oil, a miracle was wrought for the roses of Israel!",
        "story": "Every stanza recounts a chapter of Jewish survival — Egypt, Babylon, Purim/Haman, and the Maccabees' rededication of the Temple Menorah — spanning 2,000 years of history in six verses!",
    },
    {
        "slug": "dayenu",
        "title": "Dayenu (It Would Have Been Enough — Passover Seder)",
        "he_title": "דַּיֵּנוּ",
        "occasion": "Passover Seder Night · 15 Nisan",
        "composer": "Ancient Geonic Haggadah Liturgy (over 1,200 years old!)",
        "art": "/art/exodus-sea.jpg",
        "hebrew": "אִלּוּ הוֹצִיאָנוּ מִמִּצְרַיִם — דַּיֵּנוּ! אִלּוּ קָרַע לָנוּ אֶת הַיָּם — דַּיֵּנוּ! אִלּוּ נָתַן לָנוּ אֶת הַשַּׁבָּת — דַּיֵּנוּ! אִלּוּ נָתַן לָנוּ אֶת הַתּוֹרָה — דַּיֵּנוּ!",
        "translit": "Ilu hotzi'anu miMitzrayim — Dayenu! Ilu kara lanu et hayam — Dayenu! Ilu natan lanu et haShabbat — Dayenu! Ilu natan lanu et haTorah — Dayenu!",
        "english": "Had He only brought us out of Egypt — it would have been enough! Had He only split the Sea — Dayenu! Had He only given us Shabbat — Dayenu! Had He only given us the Torah — Dayenu!",
        "story": "15 stanzas corresponding to the 15 steps of the Temple courtyard — teaching the psychology of gratitude: savor EVERY individual blessing along the journey, not just the finish line!",
    },
    {
        "slug": "avinu-malkeinu",
        "title": "Avinu Malkeinu (Our Father, Our King — High Holidays)",
        "he_title": "אָבִינוּ מַלְכֵּנוּ",
        "occasion": "Rosh Hashanah, Ten Days of Teshuvah & Yom Kippur Neilah",
        "composer": "Initiated by Rabbi Akiva during a severe drought (Talmud Ta'anit 25b)",
        "art": "/art/sinai-tablets.jpg",
        "hebrew": "אָבִינוּ מַלְכֵּנוּ חָנֵּנוּ וַעֲנֵנוּ כִּי אֵין בָּנוּ מַעֲשִׂים, עֲשֵׂה עִמָּנוּ צְדָקָה וָחֶסֶד וְהוֹשִׁיעֵנוּ!",
        "translit": "Avinu Malkeinu, choneinu va'aneinu, ki ein banu ma'asim; asei imanu tzedakah vachesed, v'hoshi'einu!",
        "english": "Our Father, Our King, be gracious to us and answer us, though we have no worthy deeds — act toward us with charity and loving-kindness, and save us!",
        "story": "Talmud Ta'anit 25b tells how during a devastating famine, after 24 formal prayers went unanswered, Rabbi Akiva stepped up and cried just two heartfelt lines — 'Avinu Malkeinu!' — and rain poured down immediately.",
    },
    {
        "slug": "hinei-ma-tov",
        "title": "Hinei Ma Tov & Oseh Shalom (Brotherhood & Peace)",
        "he_title": "הִנֵּה מַה טּוֹב וְעֹשֶׂה שָׁלוֹם",
        "occasion": "Community Gatherings, Kids Shul & Closing of Prayer",
        "composer": "King David (Psalm 133:1) & Job 25:2",
        "art": "/art/david-harp.jpg",
        "hebrew": "הִנֵּה מַה טּוֹב וּמַה נָּעִים שֶׁבֶת אַחִים גַּם יָחַד! — עֹשֶׂה שָׁלוֹם בִּמְרוֹמָיו הוּא יַעֲשֶׂה שָׁלוֹם עָלֵינוּ וְעַל כָּל־יִשְׂרָאֵל!",
        "translit": "Hinei mah tov u'mah na'im, shevet achim gam yachad! — Oseh shalom bimromav, Hu ya'aseh shalom aleinu v'al kol Yisrael!",
        "english": "Behold how good and how pleasant it is when brothers and sisters dwell together in unity! — May He Who makes peace in His heights grant peace to us and to all Israel!",
        "story": "Sung around Shabbat tables, synagogues, and Jewish communities across every continent — uniting children, guests, and elders in one joyful circle.",
    },
]


# =============================================================================
# 5. DEEP MULTI-LAYERED HOLIDAY, HIGH HOLIDAY & SACRED CALENDAR ENCYCLOPEDIA
#    (Biblical Origins + Deep History + Prominent Historical Figures + Rituals + Today)
# =============================================================================

HOLIDAY_ENCYCLOPEDIA = [
    {
        "slug": "shabbat",
        "name": "Shabbat — Queen of Time",
        "he_name": "שַׁבָּת קֹדֶשׁ",
        "emoji": "🕯",
        "hebrew_date_label": "Every 7th Day · Sunset Friday to 3 Stars Saturday",
        "category": "Weekly Covenant",
        "art": "/art/creation-shabbat.jpg",
        "biblical_origins": "Genesis 2:1–3 ('God blessed the Seventh Day and declared it holy' — the VERY FIRST thing called holy in the Torah!), Exodus 20:8–11 ('Remember'), Deuteronomy 5:12–15 ('Guard'), and Isaiah 58:13 ('Call the Sabbath a delight — Oneg Shabbat').",
        "deep_history": "While ancient empires worked laborers without a single day off, Judaism gifted humanity the revolutionary concept of a universal weekly day of rest — protecting workers, strangers, and even animals (Ex. 20:10). Roman writers like Seneca marveled at Jews resting every seventh day; Second Temple pilgrims lit oil lamps in Jerusalem; Safed Kabbalists crowned Shabbat with Lecha Dodi.",
        "prominent_celebrations": [
            "Shammai & Hillel (1st c. BCE, Talmud Beitzah 16a): Shammai spent all week saving the finest food he found 'in honor of Shabbat'; Hillel lived every single day in active trust that God provides — two complementary models of Shabbat joy!",
            "Rabbi Chanina (Talmud Shabbat 119a): Stood dressed in royal robes at Friday twilight calling out 'Come, let us go forth to greet Queen Shabbat!'",
            "Rabbi Isaac Luria (Arizal, Safed 1570s): Walked with students into the Galilean hills in white garments before sunset singing Lecha Dodi and welcoming the Sabbath Bride.",
            "Rashi & European Communities (11th c. Troyes): Paired Torah study of the weekly Parashah twice in Hebrew and once in Targum (Shnayim Mikra) with warm slow-cooked Cholent and family Zemirot.",
        ],
        "rituals_and_prayers": "Candle lighting 18 min before sunset · Kabbalat Shabbat & Psalm 92 · Shalom Aleichem & Eshet Chayil · Kiddush over wine & Two Challot (remembering double Manna!) · Shabbat Shacharit & 7 Aliyot Torah Reading · Retzeh in Birkat HaMazon · Seudah Shlishit · Havdalah with braided candle, fragrant spices (Besamim) & Eliyahu HaNavi.",
        "today_meaning": "Rabbi Abraham Joshua Heschel called Shabbat 'a Cathedral in Time.' In a 24/7 digital age of burnout and notifications, Shabbat declares that human dignity is never measured by productivity.",
        "match_month": None,
        "match_day": None,
    },
    {
        "slug": "chanukah",
        "name": "Chanukah — Festival of Dedication & Light",
        "he_name": "חֲנֻכָּה · חַג הָאוּרִים",
        "emoji": "🕎",
        "hebrew_date_label": "25 Kislev – 2/3 Tevet (8 Nights)",
        "category": "Festival of Light",
        "art": "/art/solomon-temple.jpg",
        "biblical_origins": "Rooted in the Temple Menorah (Exodus 25:31–40; Numbers 8:1–4) and Prophet Zechariah's Haftarah vision (Zechariah 4:6): 'Not by might, nor by power, but by My spirit, says the Lord of Hosts!'",
        "deep_history": "In 167–164 BCE, Seleucid ruler Antiochus IV outlawed Shabbat, Torah study, and circumcision, desecrating the Second Temple. Mattathias and Judah the Maccabee led a stunning victory for religious freedom, entering Jerusalem on 25 Kislev 164 BCE. Finding only ONE pure cruse of olive oil sealed by the High Priest (enough for 1 day), the Menorah burned miraculously for 8 days — inspiring 'Pirsumei Nisa' (publicizing light in every window).",
        "prominent_celebrations": [
            "Judah the Maccabee & the Second Temple Priests (164 BCE, I Maccabees 4): Rededicated the Altar for 8 days with harps, cymbals, and joyful Hallel songs — mirroring King Solomon's 8-day Temple dedication!",
            "Hillel vs. Shammai (1st c. BCE, Talmud Shabbat 21b): Shammai argued start with 8 candles and decrease; Hillel won Jewish law forever with 'Ma'alin BaKodesh' — add one light every night (1 → 8) because holiness always grows!",
            "Maimonides (Rambam, Laws of Chanukah 4:12): Called the Chanukah lamp 'exceedingly beloved' — even someone in deep poverty should ensure they light a flame at their doorway to spread light outward.",
            "Rabbi Akiva Eiger & Modern Brussels / European Synagogues: Lighting giant public Menorahs in city squares (like Brussels' EU Quarter!) while singing Maoz Tzur, eating olive-oil latkes & sufganiyot, and giving Chanukah Gelt + Tzedakah.",
        ],
        "rituals_and_prayers": "Light Menorah right to left (1 → 8 nights) after Tzeit HaKochavim (before candles on Friday!) · Say Full Hallel every morning · Insert 'Al HaNisim' in Amidah & Birkat HaMazon · Sing Maoz Tzur · Spin Dreidel (Nes Gadol Hayah Sham/Poh) · Eat foods cooked in olive oil.",
        "today_meaning": "A single small candle dispels an entire room of darkness. Chanukah teaches proud Jewish identity without compromise, adding one extra spark of kindness every single evening.",
        "match_month": 9,
        "match_day": 25,
    },
    {
        "slug": "rosh-hashanah",
        "name": "Rosh Hashanah — Head of the Year & Day of the Shofar",
        "he_name": "רֹאשׁ הַשָּׁנָה · יוֹם תְּרוּעָה",
        "emoji": "📯",
        "hebrew_date_label": "1–2 Tishrei (High Holidays)",
        "category": "High Holiday (Yamim Noraim)",
        "art": "/art/sinai-tablets.jpg",
        "biblical_origins": "Leviticus 23:24 ('A sacred convocation, a remembrance of Shofar blasts'), Numbers 29:1 ('Day of Teruah'), Genesis 21–22 (Birth of Isaac & Akeidat Yitzchak read on Days 1 & 2!), and Nehemiah 8:1–12!",
        "deep_history": "Celebrates the 6th day of Creation — the birthday of Humanity (Adam & Eve) and universal moral accountability. Over 2,450 years ago on 1 Tishrei (Nehemiah 8), Ezra the Scribe stood on a wooden tower in Jerusalem reading Torah aloud to the returning exiles, telling weeping crowds: 'Do not mourn — eat festive foods, share portions with those who have nothing, for the joy of the Lord is your strength!'",
        "prominent_celebrations": [
            "Ezra the Scribe & Nehemiah (c. 444 BCE, Nehemiah 8:9–12): Turned 1 Tishrei into a day of public Torah illumination, festive joy, and sending food parcels to families in need.",
            "Rabban Yochanan ben Zakkai (Yavneh, 70 CE, Talmud Rosh Hashanah 29b): After the Temple fell, preserved Shofar sounding in every community so Jewish renewal could flourish anywhere on earth.",
            "Rabbi Amnon of Mainz (11th c. Germany): Composed the haunting hymn 'Unetaneh Tokef' ('Repentance, Prayer, and Charity transform the harsh decree'), sung in every synagogue worldwide.",
            "Maimonides (Rambam, Laws of Teshuvah 3:4): Taught the Shofar's wordless cry is a spiritual alarm clock: 'Awake, sleepers, from your slumber — remember who you truly are!'",
        ],
        "rituals_and_prayers": "100 Shofar blasts (Tekiah, Shevarim, Teruah) · Dip round Challah & sweet Apples in Honey · Simanim (pomegranate, dates, honey) · Tashlich beside flowing water · Psalm 27 & Avinu Malkeinu · Ya'aleh V'Yavo in Birkat HaMazon.",
        "today_meaning": "Unlike a noisy midnight countdown, the Jewish New Year begins with awe, sweetness, honesty, and hope — crowning empathy and purpose over autopilot.",
        "match_month": 7,
        "match_day": 1,
    },
    {
        "slug": "yom-kippur",
        "name": "Yom Kippur — Day of Atonement & Purest Forgiveness",
        "he_name": "יוֹם כִּפּוּר · שַׁבַּת שַׁבָּתוֹן",
        "emoji": "🤍",
        "hebrew_date_label": "10 Tishrei (High Holidays)",
        "category": "High Holiday (Yamim Noraim)",
        "art": "/art/elijah-horeb.jpg",
        "biblical_origins": "Leviticus 16 & 23:27–32, Exodus 34:1–10 (Moses descending Mount Sinai with the Second Whole Tablets and the 13 Attributes of Mercy!), Isaiah 58 (true fasting means feeding the hungry!), and the entire Book of Jonah.",
        "deep_history": "On 10 Tishrei, after the Golden Calf crisis, God forgave Israel completely and handed Moses the Second Tablets. In the Temple, the High Priest (Kohen Gadol) entered the Holy of Holies once a year in pure white linen, praying for peace and plenty for ALL humanity; when he emerged safely, Jerusalem erupted in white-robed celebration (Mishnah Ta'anit 4:8)!",
        "prominent_celebrations": [
            "Moses (Sinai, 1313 BCE): Returned with the Second Tablets on 10 Tishrei — establishing Yom Kippur as the anniversary of second chances!",
            "Rabbi Akiva (Mishnah Yoma 8:9): Proclaimed 'How fortunate are you, Israel! Who purifies you? Your Father in Heaven!' — while Mishnah Yoma 8:9 simultaneously teaches Yom Kippur ONLY atones for hurts between people AFTER we sincerely apologize face-to-face!",
            "Rabbi Levi Yitzchak of Berditchev (18th c.): Turned Yom Kippur into a loving defense of every single Jew, pointing out their hidden goodness before Heaven.",
            "King David & Communities Worldwide: Wearing white (like angels!), singing Kol Nidrei at sunset, reading Book of Jonah at Mincha, and crying 'Shema Yisrael!' at Neilah before the final triumphant Shofar blast!",
        ],
        "rituals_and_prayers": "25-hour fast from sunset to nightfall · Kol Nidrei · 5 Prayer Services (Maariv, Shacharit, Musaf Avodah, Mincha + Jonah, Neilah) · Yizkor Memorial · Al Chet communal confession · Final Tekiah Gedolah Shofar & Havdalah.",
        "today_meaning": "No mistake is ever the final chapter of your life. Repairing relationships with people first — then standing honestly before Heaven — lets you begin completely fresh.",
        "match_month": 7,
        "match_day": 10,
    },
    {
        "slug": "sukkot",
        "name": "Sukkot & Simchat Torah — Season of Our Joy",
        "he_name": "סֻכּוֹת וְשִׂמְחַת תּוֹרָה",
        "emoji": "🌿",
        "hebrew_date_label": "15–23 Tishrei (Pilgrimage Festival)",
        "category": "Three Pilgrimage Festivals (Shalosh Regalim)",
        "art": "/art/promised-land.jpg",
        "biblical_origins": "Leviticus 23:33–43 ('Dwell in booths 7 days' + the Four Species: Etrog, Lulav, Hadas, Aravah), Deuteronomy 16:14 ('And you shall be completely joyful!'), and Book of Ecclesiastes (Kohelet).",
        "deep_history": "During the Temple era, Sukkot featured the breathtaking 'Simchat Beit HaShoevah' (Water-Drawing Festival) — giant golden candelabras lit up all of Jerusalem while Sages danced with flaming torches until dawn! Meanwhile 70 offerings were brought for ALL 70 nations of the world (Talmud Sukkah 55b) — praying for universal rain and peace.",
        "prominent_celebrations": [
            "King Solomon (I Kings 8, c. 957 BCE): Dedicated the First Temple specifically during Sukkot, praying that even strangers from distant lands be answered in Jerusalem!",
            "Rabban Shimon ben Gamliel (Talmud Sukkah 53a): Juggled 8 flaming torches in the Temple courtyard during Simchat Beit HaShoevah, declaring 'Whoever hasn't seen this joy has never seen true joy in their life!'",
            "The Zohar & Mystics of Safed: Instituted 'Ushpizin' — welcoming Abraham, Isaac, Jacob, Moses, Aaron, Joseph, and David as honored guests into every family Sukkah (plus sharing meals with real guests!).",
            "Simchat Torah Communities Worldwide: Dancing 7 joyous Hakafot circles hugging the Torah scrolls as we finish the very last verse of Deuteronomy and roll immediately back to Genesis 1:1!",
        ],
        "rituals_and_prayers": "Eat & welcome guests inside a leaf-roofed Sukkah · Wave the Four Species (Lulav & Etrog — uniting all four kinds of people into one bundle!) · Full Hallel & Hoshanot · Ya'aleh V'Yavo in Birkat HaMazon · Simchat Torah Hakafot dancing.",
        "today_meaning": "Leaving solid walls for a fragile booth right after Yom Kippur teaches true security isn't concrete or wealth — it's gratitude, hospitality, and community under the open sky.",
        "match_month": 7,
        "match_day": 15,
    },
    {
        "slug": "tu-bshvat",
        "name": "Tu B'Shvat — New Year of the Trees",
        "he_name": "ט״ו בִּשְׁבָט · רֹאשׁ הַשָּׁנָה לָאִילָנוֹת",
        "emoji": "🌳",
        "hebrew_date_label": "15 Shevat",
        "category": "Sacred Ecological & Kabbalistic Day",
        "art": "/art/promised-land.jpg",
        "biblical_origins": "Deuteronomy 8:8 (The Seven Species of Israel: wheat, barley, grapes, figs, pomegranates, olives, dates) & Deuteronomy 20:19 ('For humanity is like a tree of the field').",
        "deep_history": "Established in Mishnah Rosh Hashanah 1:1 as the agricultural cutoff for tithes because winter rains have saturated Israel's soil and sap begins rising silently inside dormant trees. In the 16th century, Safed Kabbalists created the mystical 'Tu B'Shvat Seder' with four cups of white-to-red wine and fruits of Israel.",
        "prominent_celebrations": [
            "Beit Hillel (1st c. CE, Mishnah RH 1:1): Fixed 15 Shevat (full moon of Shevat!) as the New Year of Trees.",
            "Choni HaMe'agel (Talmud Ta'anit 23a): Met an elder planting a carob tree that takes 70 years to bear fruit — 'Just as my ancestors planted for me, I plant for my grandchildren!'",
            "Rabbi Isaac Luria & Safed Sages (1570s): Hosted joyful Tu B'Shvat Seders blessing Israel's Seven Species and celebrating renewal hidden beneath winter bark.",
        ],
        "rituals_and_prayers": "Eat Israel's Seven Species & new fruit (Shehecheyanu) · Tu B'Shvat Seder with 4 symbolic cups · Plant trees & teach stewardship of creation.",
        "today_meaning": "Even when branches still look bare in January, hidden sap is already rising inside — growth and renewal begin invisibly long before blossoms appear!",
        "match_month": 11,
        "match_day": 15,
    },
    {
        "slug": "purim",
        "name": "Purim — Hidden Providence & Joyous Solidarity",
        "he_name": "פּוּרִים · מְגִלַּת אֶסְתֵּר",
        "emoji": "👑",
        "hebrew_date_label": "14 Adar (Adar II in Leap Years like 5787!)",
        "category": "Festival of Courage & Joy",
        "art": "/art/esther-shushan.jpg",
        "biblical_origins": "The entire Book of Esther (Megillat Esther) — where God's explicit Name never appears once, teaching 'Hester Panim' (Divine providence woven through human courage) — plus Exodus 17:8–16.",
        "deep_history": "Set in 5th-century BCE Shushan (Susa, Persian Empire) under King Ahasuerus. When royal vizier Haman cast lots ('Purim') to annihilate Jews across 127 provinces, Mordechai challenged Queen Esther: 'Who knows if you reached this moment for just such a time as this?' Through fasting, unity, and brilliance, the decree flipped completely ('V'Nahafoch Hu').",
        "prominent_celebrations": [
            "Queen Esther & Mordechai (Esther 9:22): Established Purim's four timeless mitzvot — not merely a military victory, but gifts of food to friends and direct charity to the poor!",
            "Maimonides (Rambam, Laws of Megillah 2:17): Ruled that giving generously to the poor on Purim ('Matanot L'Evyonim') brings greater spiritual joy than even the grandest banquet!",
            "European & Brussels Synagogues: Bustling family Megillah readings with groggers, children in biblical costumes, Mishloach Manot baskets, Hamantaschen, and joyful Seudat Purim!",
        ],
        "rituals_and_prayers": "Hear Megillat Esther twice (night & day) · Give Mishloach Manot (food gifts to friends) · Give Matanot L'Evyonim (charity to at least 2 people in need) · Festive Purim Meal · Insert 'Al HaNisim' in Amidah & Birkat HaMazon.",
        "today_meaning": "When heaven seems quiet, YOUR voice, timing, and solidarity ARE the miracle. And true Jewish joy always makes sure nobody in the community is left out.",
        "match_month": 13,
        "match_day": 14,
    },
    {
        "slug": "pesach",
        "name": "Pesach (Passover) — Festival of Freedom & Memory",
        "he_name": "פֶּסַח · זְמַן חֵרוּתֵנוּ",
        "emoji": "🍷",
        "hebrew_date_label": "15–22 Nisan (Pilgrimage Festival)",
        "category": "Three Pilgrimage Festivals (Shalosh Regalim)",
        "art": "/art/exodus-sea.jpg",
        "biblical_origins": "Exodus 12–15 (The Exodus from Egypt, Matzah, Splitting of the Sea, Song of Miriam & Moses) and Song of Songs (Shir HaShirim).",
        "deep_history": "The oldest continuously celebrated freedom meal on planet Earth — observed uninterrupted for over 3,300 years! From King Josiah's great Jerusalem Passover (II Kings 23) and King Hezekiah's reunification Passover (II Chronicles 30) to the 5th-c. BCE Elephantine Passover Papyrus in Egypt and the five Sages debating until sunrise in Bnei Brak.",
        "prominent_celebrations": [
            "King Hezekiah (II Chronicles 30, c. 715 BCE): Sent runners across all tribes of Israel inviting estranged northern brothers to reunite in Jerusalem for a joyous 14-day Passover!",
            "Rabbis Eliezer, Yehoshua, Elazar ben Azaryah, Akiva & Tarfon (Haggadah): Stayed awake ALL night in Bnei Brak discussing the Exodus until their students knocked: 'Rabbis, it is already time for morning Shema!'",
            "Hillel the Elder (1st c. BCE): Invented the 'Korech' sandwich (Matzah + Bitter Herbs together!) — still eaten at every Passover Seder 2,000 years later!",
            "Families Everywhere: Opening the door for Prophet Elijah, letting the youngest child ask the Four Questions (Mah Nishtanah), spilling wine drops in empathy for Egyptian suffering, and singing Dayenu!",
        ],
        "rituals_and_prayers": "Remove Chametz & eat Matzah · 15-Step Passover Seder (4 Cups of Wine, Four Questions, Maggid storytelling, Maror, Hillel Sandwich, Afikoman) · Begin Counting the Omer on Night 2 · Full Hallel & Ya'aleh V'Yavo.",
        "today_meaning": "In every single generation, each person must see themselves as personally leaving Egypt — turning our memory of oppression into lifelong empathy for the vulnerable.",
        "match_month": 1,
        "match_day": 15,
    },
    {
        "slug": "shavuot",
        "name": "Shavuot — Receiving the Torah at Mount Sinai",
        "he_name": "שָׁבוּעוֹת · זְמַן מַתַּן תּוֹרָתֵנוּ",
        "emoji": "📜",
        "hebrew_date_label": "6–7 Sivan (50th Day After Pesach)",
        "category": "Three Pilgrimage Festivals (Shalosh Regalim)",
        "art": "/art/sinai-tablets.jpg",
        "biblical_origins": "Exodus 19–20 (Revelation at Mount Sinai & Ten Commandments), Leviticus 23:15–21 (Counting 49 days of the Omer to Day 50), and the entire Book of Ruth!",
        "deep_history": "Links freedom (Passover) to purpose (Sinai): leaving Egypt was only the beginning — Israel counted every single day with eager anticipation until standing 'like one person with one heart' at Sinai. In the Temple, farmers marched up to Jerusalem in musical processions carrying decorated baskets of First Fruits (Bikkurim) while even King Agrippa carried a basket on his shoulder!",
        "prominent_celebrations": [
            "King Agrippa (Mishnah Bikkurim 3:4): Walked straight into the Temple courtyard carrying his own wicker basket of First Fruits on his royal shoulder like every ordinary farmer!",
            "Rabbi Yosef Karo & Rabbi Shlomo Alkabetz (Safed, 1533 CE): Popularized 'Tikkun Leil Shavuot' — staying awake ALL night studying Torah together before sunrise to show Israel's love for wisdom!",
            "King David (Tradition): Both born and passed away on Shavuot — which is why we read the Book of Ruth (King David's great-grandmother!) and recite Tehillim.",
        ],
        "rituals_and_prayers": "All-night Tikkun Leil Shavuot study · Hear the Ten Commandments standing (bring the kids!) · Read Book of Ruth · Decorate the synagogue with fresh flowers & greenery · Enjoy festive dairy cheesecake & blintzes ('Torah is like honey and milk') · Yizkor on Day 2.",
        "today_meaning": "Freedom without values drifts; values without kindness harden. Pairing Mount Sinai's laws with Ruth's tender Chesed reveals the living heart of Judaism.",
        "match_month": 3,
        "match_day": 6,
    },
    {
        "slug": "tisha-bav",
        "name": "Tisha B'Av — Remembrance, Grief & Unbreakable Hope",
        "he_name": "תִּשְׁעָה בְּאָב",
        "emoji": "🕯",
        "hebrew_date_label": "9 Av",
        "category": "Day of Historical Mourning & Renewal",
        "art": "/art/jerusalem-scroll.jpg",
        "biblical_origins": "Numbers 13–14 (The night of needless weeping after the Ten Spies' report) and the Book of Lamentations (Eichah) by Prophet Jeremiah.",
        "deep_history": "Marks the destruction of BOTH the First Temple (586 BCE) and Second Temple (70 CE) on the exact same Hebrew date, as well as the 1492 Spanish Expulsion. The Talmud (Yoma 9b) asks WHY the Second Temple fell despite widespread Torah study — answering 'Sinat Chinam' (baseless hatred between neighbors). Therefore the cure is 'Ahavat Chinam' (unconditional love)!",
        "prominent_celebrations": [
            "Rabbi Akiva (Talmud Makkot 24b): Walking past Jerusalem's smoking ruins while his colleagues wept at a fox emerging from the Holy of Holies, Rabbi Akiva LAUGHED with radiant faith — 'If Jeremiah's prophecy of ruin came true literally, then Zechariah's prophecy of children playing happily in Jerusalem's streets will surely come true too!'",
            "Rabbi Yehudah HaLevi (12th c. Spain): Composed the breathtaking 'Tzion HaLo Tishali' (Ode to Zion) recited in Kinot every Tisha B'Av morning.",
        ],
        "rituals_and_prayers": "25-hour fast · Read Book of Lamentations (Eichah) by soft candlelight sitting low · Recite Kinot (elegies) · Wear Tallit & Tefillin at Mincha afternoon as comfort begins · Immediately followed by 7 Weeks of Consolation ('Nachamu!') leading to Rosh Hashanah!",
        "today_meaning": "Judaism never buries grief — it transforms historical tragedy into a fierce commitment to unity, kindness (Ahavat Chinam), and rebuilding broken communities.",
        "match_month": 5,
        "match_day": 9,
    },
    {
        "slug": "rosh-chodesh",
        "name": "Rosh Chodesh — Renewal of the New Moon",
        "he_name": "רֹאשׁ חֹדֶשׁ",
        "emoji": "🌙",
        "hebrew_date_label": "1st (and 30th) of Every Hebrew Month",
        "category": "Monthly Sacred Renewal",
        "art": "/art/abraham-stars.jpg",
        "biblical_origins": "Exodus 12:2 ('This month shall be for you the head of months' — the VERY FIRST national mitzvah given to Israel!) and Numbers 10:10 & 28:11.",
        "deep_history": "In Second Temple Jerusalem, eyewitnesses raced to the Sanhedrin court to testify they had spotted the razor-thin crescent New Moon; bonfires were then lit from hilltop to hilltop all the way from the Mount of Olives to Babylon to announce Rosh Chodesh! Jewish tradition especially honors Rosh Chodesh as a special women's festival (Pirkei DeRabbi Eliezer 45) because the women refused to contribute their gold to the Golden Calf!",
        "prominent_celebrations": [
            "King Saul, Jonathan & David (I Samuel 20:5): Celebrated Rosh Chodesh with a royal multi-day family feast!",
            "Rabban Gamliel (Mishnah Rosh Hashanah 2:8): Kept lunar phase diagrams mounted on his study wall to cross-check witnesses' exact sighting of the crescent moon!",
            "Jewish Women Across Generations: Gathering for monthly Rosh Chodesh Torah circles, gratitude, and joyful renewal.",
        ],
        "rituals_and_prayers": "Half Hallel · Special Torah Reading (Numbers 28:1–15) · Musaf · Insert 'Ya'aleh V'Yavo' in Amidah & Birkat HaMazon · Followed days later by Kiddush Levana (Sanctification of the Waxing Moon outdoors!).",
        "today_meaning": "Just like the Moon shrinks to darkness yet ALWAYS returns to fullness, every single month offers a fresh start — renewal is built straight into the cosmos!",
        "match_month": None,
        "match_day": 1,
    },
]

# Deep "This Month in Biblical & Jewish History" Chronicle (Hebrew month 1..13)
HEBREW_MONTH_CHRONICLES = {
    1:  {"month": "Nisan", "he": "נִיסָן", "theme": "Month of Spring, Liberation & Miracles", "events": ["1 Nisan: Tabernacle (Mishkan) dedicated in Sinai (Ex. 40:2)", "14–15 Nisan: First Passover & Exodus from Egypt (Ex. 12)", "21 Nisan: Splitting of the Sea & Song of Miriam (Ex. 14–15)"]},
    2:  {"month": "Iyyar", "he": "אִיָּיר", "theme": "Month of Healing (Ani Hashem Rofecha) & Counting the Omer", "events": ["1 Iyyar: King Solomon begins building the First Temple (I Kings 6:1)", "14 Iyyar: Pesach Sheni — Second Chance Passover (Num. 9)", "18 Iyyar: Lag BaOmer — Joy of Rabbi Shimon bar Yochai & unity"]},
    3:  {"month": "Sivan", "he": "סִיוָן", "theme": "Month of Unity & Revelation at Mount Sinai", "events": ["1 Sivan: Israel camps beneath Mount Sinai 'like one person with one heart' (Ex. 19:2)", "6 Sivan: Giving of the Ten Commandments (Shavuot) & King David's legacy"]},
    4:  {"month": "Tammuz", "he": "תַּמּוּז", "theme": "Month of Vigilance, Reflection & Inner Light", "events": ["17 Tammuz: Moses shatters the First Tablets; beginning of the Three Weeks of reflection on Jerusalem"]},
    5:  {"month": "Av", "he": "אָב", "theme": "From Mourning to Comfort (Menachem Av) & Tu B'Av Joy", "events": ["9 Av: Tisha B'Av remembrance & Rabbi Akiva's unbreakable laughter of hope", "15 Av: Tu B'Av — ancient festival of reconciliation, dancing in Jerusalem's vineyards & love"]},
    6:  {"month": "Elul", "he": "אֱלוּל", "theme": "Month of Compassion — 'The King Is in the Field'", "events": ["1 Elul: Moses ascends Sinai for 40 days of mercy; daily Shofar sounded & Psalm 27 begins", "25 Elul: Traditional anniversary of Day One of Creation ('Let there be light!')"]},
    7:  {"month": "Tishrei", "he": "תִּשְׁרֵי", "theme": "Crown of the Year — Awe, Forgiveness & Joy", "events": ["1–2 Tishrei: Rosh Hashanah (Birthday of Humanity & Ezra's public Torah reading)", "10 Tishrei: Yom Kippur (Second Tablets & Purest Forgiveness)", "15–23 Tishrei: Sukkot, First Temple Dedication & Simchat Torah"]},
    8:  {"month": "Cheshvan", "he": "חֶשְׁוָן", "theme": "Quiet Depth, Rain Prayers & Matriarch Rachel", "events": ["7 Cheshvan: Prayers for winter rain begin in Israel", "11 Cheshvan: Yahrzeit of Matriarch Rachel Imeinu (Genesis 35:19)", "17 Cheshvan: Noah enters the Ark — trusting renewal through the storm"]},
    9:  {"month": "Kislev", "he": "כִּסְלֵו", "theme": "Month of Dreams, Trust (Bitachon) & Kindling Light in Darkness", "events": ["1 Kislev: Noah's Rainbow Covenant appears in the clearing sky after the Flood!", "14 Kislev: Birth of Reuben; Jacob's family grows into the Twelve Tribes", "19 Kislev: Chassidic New Year of Inner Wisdom (1798)", "25 Kislev: Maccabees rededicate the Second Temple Menorah — Chanukah begins!"]},
    10: {"month": "Tevet", "he": "טֵבֵת", "theme": "Steadfastness Through Midwinter & Esther Crowned", "events": ["1–2 Tevet: Climax of Chanukah (8 full flames blazing!)", "10 Tevet: Historical fast remembering Jerusalem's siege", "24 Tevet: Esther brought to the royal palace — setting Purim's salvation in motion (Esther 2:16)"]},
    11: {"month": "Shevat", "he": "שְׁבָט", "theme": "Hidden Renewal Rising Beneath Winter Bark", "events": ["1 Shevat: Moses begins his majestic farewell address — Book of Deuteronomy (Deut. 1:3)!", "15 Shevat: Tu B'Shvat — New Year of the Trees & Israel's Seven Species"]},
    12: {"month": "Adar / Adar I", "he": "אֲדָר", "theme": "Multiplying Joy ('Mishenichnas Adar Marbin B'Simchah!')", "events": ["7 Adar: Birth & passing of Moses (Moshe Rabbeinu)!", "14 Adar: Purim (or Purim Katan in Leap Year 5787!) — turning dread into joy"]},
    13: {"month": "Adar II", "he": "אֲדָר ב׳", "theme": "Leap-Year Double Joy & Megillat Esther", "events": ["13 Adar II: Fast of Esther (Taanit Esther)", "14 Adar II: Purim — Megillat Esther, Mishloach Manot & Matanot L'Evyonim!", "23 Adar II: First day of Mishkan inauguration"]},
}


TEFILLIN_SAY_WITH_ME = [
    {
        "step": 1,
        "title": "Tallit Blessing (Optional — Before Tefillin)",
        "cue": "Stand, hold the Tallit open, inspect the fringes (Tzitzit), and recite before wrapping around your shoulders.",
        "source": "Numbers 15:38–39 (Primary Scripture) · Talmud Bavli, Menachot 43a (Cited Halachic Tradition)",
        "phrases": [
            {"he": "בָּרוּךְ אַתָּה אֲדֹנָי", "translit": "Ba-ruch a-tah A-do-nai", "en": "Blessed are You, Lord", "pause_ms": 2800},
            {"he": "אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם", "translit": "E-lo-hei-nu Me-lech ha-o-lam", "en": "our God, King of the universe", "pause_ms": 3000},
            {"he": "אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו", "translit": "a-sher kid-sha-nu b'mitz-vo-tav", "en": "Who has sanctified us with His commandments", "pause_ms": 3200},
            {"he": "וְצִוָּנוּ לְהִתְעַטֵּף בַּצִּיצִת", "translit": "v'tzi-va-nu l'hit-a-teif ba-tzi-tzit", "en": "and commanded us to wrap ourselves in Tzitzit.", "pause_ms": 3200},
        ],
    },
    {
        "step": 2,
        "title": "Arm Tefillin (Shel Yad)",
        "cue": "Place the Arm Tefillin box on your weaker bicep angled slightly toward your heart. Say the blessing BEFORE tightening the knot, then wrap 7 times down the forearm.",
        "source": "Deuteronomy 6:8 & Exodus 13:9 (Primary Scripture) · Talmud Bavli, Menachot 36a (Cited Tradition)",
        "phrases": [
            {"he": "בָּרוּךְ אַתָּה אֲדֹנָי", "translit": "Ba-ruch a-tah A-do-nai", "en": "Blessed are You, Lord", "pause_ms": 2800},
            {"he": "אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם", "translit": "E-lo-hei-nu Me-lech ha-o-lam", "en": "our God, King of the universe", "pause_ms": 3000},
            {"he": "אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו", "translit": "a-sher kid-sha-nu b'mitz-vo-tav", "en": "Who has sanctified us with His commandments", "pause_ms": 3200},
            {"he": "וְצִוָּנוּ לְהָנִיחַ תְּפִלִּין", "translit": "v'tzi-va-nu l'ha-ni-ach t'fi-lin", "en": "and commanded us to put on Tefillin.", "pause_ms": 3400},
        ],
    },
    {
        "step": 3,
        "title": "Head Tefillin (Shel Rosh)",
        "cue": "Without talking between arm and head, center the Head Tefillin above your hairline aligned between your eyes (knot at the base of the skull). Ashkenazi custom adds the second blessing + Baruch Shem.",
        "source": "Deuteronomy 6:8 (Primary Scripture) · Talmud Bavli, Menachot 36a (Ashkenazi vs. Sephardi customs noted)",
        "phrases": [
            {"he": "בָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם", "translit": "Ba-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam", "en": "Blessed are You, Lord our God, King of the universe", "pause_ms": 3400},
            {"he": "אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו", "translit": "a-sher kid-sha-nu b'mitz-vo-tav", "en": "Who has sanctified us with His commandments", "pause_ms": 3000},
            {"he": "וְצִוָּנוּ עַל מִצְוַת תְּפִלִּין", "translit": "v'tzi-va-nu al mitz-vat t'fi-lin", "en": "and commanded us concerning the mitzvah of Tefillin.", "pause_ms": 3400},
            {"he": "בָּרוּךְ שֵׁם כְּבוֹד מַלְכוּתוֹ לְעוֹלָם וָעֶד", "translit": "Ba-ruch shem k'vod mal-chu-to l'o-lam va-ed", "en": "Blessed is the name of His glorious kingdom forever and ever.", "pause_ms": 3600},
        ],
    },
    {
        "step": 4,
        "title": "Wrapping the Fingers — Hosea 2:21–22",
        "cue": "Wrap the remaining strap 3 times around your middle finger (like a covenant ring) while reciting the prophet Hosea's vows of faithfulness.",
        "source": "Hosea 2:21–22 (Primary Verified Prophetic Scripture)",
        "phrases": [
            {"he": "וְאֵרַשְׂתִּיךְ לִי לְעוֹלָם", "translit": "V'ei-ras-tich li l'o-lam", "en": "And I will betroth you to Me forever;", "pause_ms": 3000},
            {"he": "וְאֵרַשְׂתִּיךְ לִי בְּצֶדֶק וּבְמִשְׁפָּט", "translit": "v'ei-ras-tich li b'tze-dek u-v'mish-pat", "en": "I will betroth you to Me in righteousness and in justice,", "pause_ms": 3400},
            {"he": "וּבְחֶסֶד וּבְרַחֲמִים", "translit": "u-v'che-sed u-v'ra-cha-mim", "en": "and in loving-kindness and in compassion.", "pause_ms": 3200},
            {"he": "וְאֵרַשְׂתִּיךְ לִי בֶּאֱמוּנָה", "translit": "V'ei-ras-tich li be-e-mu-nah", "en": "And I will betroth you to Me in faithfulness,", "pause_ms": 3200},
            {"he": "וְיָדַעַתְּ אֶת אֲדֹנָי", "translit": "v'ya-da-at et A-do-nai", "en": "and you shall know the Lord.", "pause_ms": 3000},
        ],
    },
    {
        "step": 5,
        "title": "Shema Yisrael — Deuteronomy 6:4–5",
        "cue": "Cover your eyes gently with your right hand, focus your heart on the Oneness of God, and repeat slowly.",
        "source": "Deuteronomy 6:4–9 (Primary Verified Torah Scripture)",
        "phrases": [
            {"he": "שְׁמַע יִשְׂרָאֵל", "translit": "Sh'ma Yis-ra-eil", "en": "Hear, O Israel:", "pause_ms": 2800},
            {"he": "אֲדֹנָי אֱלֹהֵינוּ אֲדֹנָי אֶחָד", "translit": "A-do-nai E-lo-hei-nu, A-do-nai E-chad", "en": "the Lord is our God, the Lord is One!", "pause_ms": 3600},
            {"he": "בָּרוּךְ שֵׁם כְּבוֹד מַלְכוּתוֹ לְעוֹלָם וָעֶד", "translit": "(Whisper) Ba-ruch shem k'vod mal-chu-to l'o-lam va-ed", "en": "Blessed is the name of His glorious kingdom forever and ever.", "pause_ms": 3500},
            {"he": "וְאָהַבְתָּ אֵת אֲדֹנָי אֱלֹהֶיךָ", "translit": "V'a-hav-ta eit A-do-nai E-lo-hei-cha", "en": "And you shall love the Lord your God", "pause_ms": 3400},
            {"he": "בְּכָל לְבָבְךָ וּבְכָל נַפְשְׁךָ וּבְכָל מְאֹדֶךָ", "translit": "b'chol l'va-v'cha u-v'chol naf-sh'cha u-v'chol m'o-de-cha", "en": "with all your heart, with all your soul, and with all your might.", "pause_ms": 4000},
        ],
    },
]

# Authentic traditional Jewish liturgical melodies (note name + beat duration) for warm polyphonic harp/choir playback
SONG_MELODIES = {
    "shalom-aleichem": {
        "mode": "D Minor (Traditional Goldfarb Niggun)",
        "bpm": 96,
        "notes": [
            ["D4", 1], ["F4", 1], ["A4", 1.5], ["G4", 0.5], ["F4", 1], ["E4", 1], ["D4", 2],
            ["F4", 1], ["A4", 1], ["C5", 1.5], ["Bb4", 0.5], ["A4", 1], ["G4", 1], ["A4", 2],
            ["D5", 1], ["C5", 1], ["Bb4", 1], ["A4", 1], ["G4", 1], ["F4", 1], ["E4", 1], ["A4", 1],
            ["F4", 1], ["E4", 1], ["D4", 1], ["C#4", 1], ["D4", 3],
        ],
    },
    "lecha-dodi": {
        "mode": "Freygish / Ahavah Rabbah (Safed Welcome)",
        "bpm": 106,
        "notes": [
            ["E4", 1], ["G#4", 1], ["A4", 1], ["B4", 1], ["C5", 1.5], ["B4", 0.5], ["A4", 2],
            ["B4", 1], ["A4", 1], ["G#4", 1], ["F4", 1], ["E4", 2.5], ["E4", 0.5],
            ["A4", 1], ["B4", 1], ["C5", 1], ["D5", 1], ["C5", 1], ["B4", 1], ["A4", 2],
            ["G#4", 1], ["A4", 1], ["F4", 1], ["E4", 3],
        ],
    },
    "adon-olam": {
        "mode": "F Major (Joyful Synagogue Anthem)",
        "bpm": 112,
        "notes": [
            ["C4", 1], ["F4", 1], ["A4", 1], ["F4", 1], ["G4", 1], ["Bb4", 1], ["A4", 2],
            ["G4", 1], ["A4", 1], ["Bb4", 1], ["G4", 1], ["A4", 1], ["G4", 1], ["F4", 2],
            ["A4", 1], ["C5", 1], ["D5", 1], ["C5", 1], ["Bb4", 1], ["A4", 1], ["G4", 2],
            ["C5", 1], ["Bb4", 1], ["A4", 1], ["G4", 1], ["F4", 3],
        ],
    },
    "eshet-chayil": {
        "mode": "G Minor (Warm Shabbat Home Niggun)",
        "bpm": 92,
        "notes": [
            ["D4", 1], ["G4", 1.5], ["A4", 0.5], ["Bb4", 1], ["A4", 1], ["G4", 2],
            ["Bb4", 1], ["C5", 1.5], ["D5", 0.5], ["C5", 1], ["Bb4", 1], ["A4", 2],
            ["D5", 1], ["C5", 1], ["Bb4", 1], ["A4", 1], ["G4", 1.5], ["F#4", 0.5], ["G4", 3],
        ],
    },
    "yedid-nefesh": {
        "mode": "E Minor (Twilight Yearning — Zweig Style)",
        "bpm": 86,
        "notes": [
            ["E4", 1], ["G4", 1], ["B4", 2], ["A4", 1], ["G4", 1], ["F#4", 2],
            ["G4", 1], ["A4", 1], ["B4", 1.5], ["C5", 0.5], ["B4", 2],
            ["E5", 1.5], ["D5", 0.5], ["C5", 1], ["B4", 1], ["A4", 1], ["G4", 1], ["F#4", 1], ["E4", 3],
        ],
    },
    "maoz-tzur": {
        "mode": "C Major (Classic Chanukah Rock of Ages)",
        "bpm": 108,
        "notes": [
            ["C4", 1], ["G4", 1], ["C4", 1], ["F4", 1], ["E4", 1], ["D4", 1], ["C4", 2],
            ["G4", 1], ["A4", 1], ["D4", 1], ["G4", 1], ["F#4", 1], ["E4", 1], ["D4", 2],
            ["G4", 1], ["G4", 1], ["A4", 1], ["G4", 1], ["F4", 1], ["E4", 1], ["D4", 2],
            ["E4", 1], ["F4", 1], ["G4", 1], ["E4", 1], ["D4", 1], ["D4", 1], ["C4", 3],
        ],
    },
    "default": {
        "mode": "Warm Chasidic Niggun (D Minor)",
        "bpm": 100,
        "notes": [
            ["D4", 1], ["F4", 1], ["A4", 1.5], ["G4", 0.5], ["F4", 1], ["E4", 1], ["D4", 2],
            ["A4", 1], ["Bb4", 1], ["C5", 1], ["A4", 1], ["G4", 1], ["F4", 1], ["E4", 2],
            ["F4", 1], ["G4", 1], ["A4", 1], ["F4", 1], ["E4", 1], ["D4", 3],
        ],
    },
}


def get_psalm_chapter(chapter: int) -> dict:
    ch = max(1, min(150, int(chapter)))
    data = torah_db.get_chapter("Psalms", ch)
    verses = data.get("verses", [])
    return {
        "chapter": ch,
        "title": f"Psalm {ch} (Tehillim {ch})",
        "he_title": f"תְּהִלִּים פֶּרֶק {ch}",
        "verses_count": len(verses),
        "verses": verses,
    }


def get_today_liturgy() -> dict:
    """Build today's complete offline Liturgy bundle synced to exact Hebrew date, day-of-week & Zmanim."""
    snap = sacred_astronomy.get_sacred_moment()
    he = snap["hebrew_date"]
    h_day = int(he["day"])
    h_month = int(he["month"])
    zmap = {z["key"]: z["time"] for z in snap.get("zmanim", [])}

    # Jewish weekday: Sunday=0 .. Saturday=6
    py_wd = datetime.now().weekday()  # Mon=0..Sun=6
    j_wd = (py_wd + 1) % 7
    if snap.get("after_sunset"):
        j_wd = (j_wd + 1) % 7

    shir = dict(SHIR_SHEL_YOM[j_wd])
    shir_data = get_psalm_chapter(shir["chapter"])
    shir["verses"] = shir_data["verses"]

    # Monthly Tehillim chapters for today's Hebrew day of month
    m_chapters = MONTHLY_TEHILLIM.get(h_day, [1])
    if h_day == 29 and he.get("month_length") == 29:
        m_chapters = sorted(set(MONTHLY_TEHILLIM[29] + MONTHLY_TEHILLIM[30]))
    monthly_psalms = [get_psalm_chapter(ch) for ch in m_chapters[:4]]

    # Dynamic calendar-aware Birkat HaMazon inserts
    active_inserts = []
    yc = snap.get("year_context") or {}
    if snap.get("is_shabbat") or snap.get("shabbat_mode"):
        active_inserts.append({
            "name": "Retzeh v'Hachalitzeinu (Shabbat Insert)",
            "he": "רְצֵה וְהַחֲלִיצֵנוּ",
            "note": "Recited in the 3rd blessing of Birkat HaMazon throughout Shabbat!",
        })
    if h_day in (1, 30) or yc.get("is_yom_tov"):
        active_inserts.append({
            "name": "Ya'aleh V'Yavo (Rosh Chodesh / Festival Insert)",
            "he": "יַעֲלֶה וְיָבֹא",
            "note": "Recited in the 3rd blessing of Birkat HaMazon & Amidah on Rosh Chodesh and Festivals.",
        })
    if yc.get("chanukah_night") or (h_month in (12, 13) and h_day == 14):
        active_inserts.append({
            "name": "Al HaNisim (Chanukah / Purim Miracle Insert)",
            "he": "עַל הַנִּסִּים",
            "note": "Recited in the 2nd blessing of Birkat HaMazon & Amidah thanking God for the miracles!",
        })

    # Live Tefillin window status from real Zmanim
    def _hm_to_min(hm_str: str) -> int | None:
        try:
            hh, mm = str(hm_str).strip().split(":")[:2]
            return int(hh) * 60 + int(mm)
        except Exception:
            return None

    now_min = _hm_to_min(snap.get("local_time", ""))
    mish_min = _hm_to_min(zmap.get("misheyakir", ""))
    sun_min = _hm_to_min(zmap.get("sunset", ""))

    if snap.get("is_shabbat") or snap.get("shabbat_mode") or yc.get("is_yom_tov"):
        tefillin_status = {
            "wear_today": False,
            "active_now": False,
            "badge": "🕯 Shabbat / Yom Tov — Tefillin Rest Today",
            "short_cta": "🕯 Shabbat · No Tefillin Today",
            "detail": "Tefillin are not worn on Shabbat or Yom Tov because the holy day itself is our living sign ('Ot') of the Covenant!",
        }
    else:
        in_window = bool(
            now_min is not None and mish_min is not None and sun_min is not None
            and mish_min <= now_min < sun_min
        )
        if in_window:
            short_cta = f"🟦 Tefillin Time · Say With Me (until {zmap.get('sunset', '')})"
        elif now_min is not None and mish_min is not None and now_min < mish_min:
            short_cta = f"🌅 Tefillin Opens at {zmap.get('misheyakir', '')} · Practice Now"
        else:
            short_cta = f"🌙 After Sunset · Tefillin Resumes {zmap.get('misheyakir', '')}"
        tefillin_status = {
            "wear_today": True,
            "active_now": in_window,
            "misheyakir": zmap.get("misheyakir", ""),
            "sunset": zmap.get("sunset", ""),
            "badge": f"🕯 Weekday Tefillin Window: {zmap.get('misheyakir', '')} – {zmap.get('sunset', '')}",
            "short_cta": short_cta,
            "detail": f"Earliest Tallit & Tefillin (Misheyakir): {zmap.get('misheyakir', '')} · Sof Zman Shema (GRA): {zmap.get('shema_gra', '')} · Sunset: {zmap.get('sunset', '')} ({snap['location']['city']}).",
        }

    enriched_songs = []
    for s in SACRED_SONGS:
        mel = SONG_MELODIES.get(s["slug"], SONG_MELODIES["default"])
        enriched_songs.append({**s, "melody": mel})

    month_chronicle = HEBREW_MONTH_CHRONICLES.get(h_month, HEBREW_MONTH_CHRONICLES[9])

    return {
        "hebrew_date": he,
        "location": snap["location"]["city"],
        "watch": snap["watch"],
        "shir_shel_yom": shir,
        "monthly_tehillim": {
            "hebrew_day": h_day,
            "chapters": m_chapters,
            "label": f"Day {h_day} of {he['month_name_en']} · Psalms {m_chapters[0]}" + (f"–{m_chapters[-1]}" if len(m_chapters) > 1 else ""),
            "psalms": monthly_psalms,
        },
        "topical_psalms": TOPICAL_PSALMS,
        "tefillin": {**TEFILLIN_AND_MORNING, "live_status": tefillin_status, "say_with_me": TEFILLIN_SAY_WITH_ME},
        "before_meal_blessings": BEFORE_MEAL_BLESSINGS,
        "after_meal_blessings": {**AFTER_MEAL_BLESSINGS, "active_inserts": active_inserts},
        "songs": enriched_songs,
        "month_chronicle": month_chronicle,
    }


def get_holidays_encyclopedia() -> dict:
    """Return all deep multi-layered Holiday & High Holiday dossiers with live Hebrew calendar proximity."""
    snap = sacred_astronomy.get_sacred_moment()
    he = snap["hebrew_date"]
    ms = (snap.get("year_context") or {}).get("milestones") or {}
    upcoming = ms.get("upcoming_holidays") or []
    month_chronicle = HEBREW_MONTH_CHRONICLES.get(int(he["month"]), HEBREW_MONTH_CHRONICLES[9])

    # Match upcoming countdown days where possible
    enriched = []
    for h in HOLIDAY_ENCYCLOPEDIA:
        item = dict(h)
        days_away = None
        next_greg = ""
        for u in upcoming:
            u_low = (u.get("name") or "").lower()
            if (h["slug"] == "chanukah" and "chanukah" in u_low) or \
               (h["slug"] == "tu-bshvat" and "shvat" in u_low) or \
               (h["slug"] == "purim" and "purim" in u_low) or \
               (h["slug"] == "pesach" and "pesach" in u_low) or \
               (h["slug"] == "shavuot" and "shavuot" in u_low) or \
               (h["slug"] == "rosh-hashanah" and "rosh hashanah" in u_low) or \
               (h["slug"] == "yom-kippur" and "yom kippur" in u_low) or \
               (h["slug"] == "sukkot" and "sukkot" in u_low) or \
               (h["slug"] == "tisha-bav" and "tisha" in u_low):
                days_away = u.get("days_away")
                next_greg = u.get("gregorian_date", "")
                break
        if h["slug"] == "rosh-chodesh" and ms.get("next_rosh_chodesh"):
            days_away = ms["next_rosh_chodesh"].get("days_away")
            next_greg = ms["next_rosh_chodesh"].get("gregorian_date", "")
        item["days_away"] = days_away
        item["next_gregorian"] = next_greg
        item["is_active_today"] = bool(
            (h["slug"] == "shabbat" and (snap.get("is_shabbat") or snap.get("shabbat_mode"))) or
            (h["slug"] == "chanukah" and (snap.get("year_context") or {}).get("chanukah_night")) or
            (h["match_month"] == int(he["month"]) and h["match_day"] == int(he["day"]))
        )
        enriched.append(item)

    return {
        "hebrew_date": he,
        "location": snap["location"]["city"],
        "month_chronicle": month_chronicle,
        "upcoming_milestones": upcoming,
        "next_rosh_chodesh": ms.get("next_rosh_chodesh"),
        "holidays": enriched,
    }


# =============================================================================
# 6. COMMUNITY HERITAGE CHRONICLE: FAMOUS JEWISH BIRTHDAYS, IN MEMORIAM
#    (YAHRZEITS OF GREAT HISTORICAL FIGURES), BRUSSELS/GLOBAL FACTS & WIT
# =============================================================================

COMMUNITY_HERITAGE_ITEMS = [
    # --- FAMOUS JEWISH BIRTHDAYS ---
    {
        "kind": "birthday", "badge": "🎂 JEWISH BIRTHDAY", "g_month": 11, "g_day": 22,
        "title": "Rodney Dangerfield & November Legends", "date_label": "Nov 22 · 1921",
        "subtitle": "Comedy, Science & Cultural Impact",
        "text": "Born Jacob Rodney Cohen on Nov 22 — part of a cherished tradition of Jewish humorists who turned sharp wit into universal joy.",
    },
    {
        "kind": "birthday", "badge": "🎂 JEWISH BIRTHDAY", "g_month": 11, "g_day": 27,
        "title": "Chaim Weizmann", "date_label": "Nov 27 · 1874",
        "subtitle": "Biochemist & First President of Israel",
        "text": "Pioneered industrial fermentation chemistry and helped found both the Hebrew University of Jerusalem and the Weizmann Institute.",
    },
    {
        "kind": "birthday", "badge": "🎂 JEWISH BIRTHDAY", "g_month": 12, "g_day": 18,
        "title": "Steven Spielberg", "date_label": "Dec 18 · 1946",
        "subtitle": "Filmmaker & Shoah Foundation Founder",
        "text": "Beyond shaping modern cinema, he founded the USC Shoah Foundation — preserving over 55,000 Holocaust survivor testimonies forever.",
    },
    {
        "kind": "birthday", "badge": "🎂 JEWISH BIRTHDAY", "g_month": 12, "g_day": 21,
        "title": "Henrietta Szold", "date_label": "Dec 21 · 1860",
        "subtitle": "Founder of Hadassah & Youth Aliyah",
        "text": "Built modern healthcare across Jerusalem for all people and led Youth Aliyah — rescuing over 11,000 Jewish children from Nazi Europe.",
    },
    {
        "kind": "birthday", "badge": "🎂 JEWISH BIRTHDAY", "g_month": 3, "g_day": 8,
        "title": "Rabbi Lord Jonathan Sacks", "date_label": "Mar 8 · 1948",
        "subtitle": "Philosopher, Author & Chief Rabbi",
        "text": "Templeton Prize laureate who bridged Torah wisdom and civic ethics: 'To heal a fractured world, start with the dignity of difference.'",
    },
    {
        "kind": "birthday", "badge": "🎂 JEWISH BIRTHDAY", "g_month": 3, "g_day": 14,
        "title": "Albert Einstein", "date_label": "Mar 14 · 1879",
        "subtitle": "Nobel Laureate in Physics",
        "text": "Revolutionized our understanding of space, time, and light — and championed human rights and the Hebrew University of Jerusalem.",
    },
    {
        "kind": "birthday", "badge": "🎂 JEWISH BIRTHDAY", "g_month": 10, "g_day": 28,
        "title": "Dr. Jonas Salk", "date_label": "Oct 28 · 1914",
        "subtitle": "Creator of the Polio Vaccine",
        "text": "When asked who owned the patent to his life-saving polio vaccine, he famously replied: 'There is no patent. Could you patent the sun?'",
    },
    {
        "kind": "birthday", "badge": "🎂 JEWISH BIRTHDAY", "g_month": 7, "g_day": 25,
        "title": "Rosalind Franklin", "date_label": "Jul 25 · 1920",
        "subtitle": "DNA Pioneer · Photo 51",
        "text": "Her X-ray crystallography unlocked the double-helix structure of DNA and RNA viruses — one of biology's greatest breakthroughs.",
    },
    {
        "kind": "birthday", "badge": "🎂 JEWISH BIRTHDAY", "g_month": 5, "g_day": 3,
        "title": "Golda Meir", "date_label": "May 3 · 1898",
        "subtitle": "Stateswoman & 4th Prime Minister of Israel",
        "text": "From a schoolteacher in Milwaukee to one of the first female heads of government in the modern world — remembered for courage and warmth.",
    },
    {
        "kind": "birthday", "badge": "🎂 JEWISH BIRTHDAY", "g_month": 8, "g_day": 25,
        "title": "Leonard Bernstein", "date_label": "Aug 25 · 1918",
        "subtitle": "Composer, Conductor & Educator",
        "text": "Wove Jewish liturgical motifs into symphonies and Broadway classics alike, inspiring generations through his televised concerts.",
    },
    # --- IN MEMORIAM / YAHRZEITS OF SIGNIFICANT JEWISH FIGURES ---
    {
        "kind": "memoriam", "badge": "🕯 IN MEMORIAM · ז״ל", "h_month": 9, "h_day": 9,
        "title": "Rabbi DovBer of Lubavitch (Mitteler Rebbe)", "date_label": "9 Kislev · 1827",
        "subtitle": "Born & Passed on the Exact Same Hebrew Date",
        "text": "Authored profound works of contemplative philosophy and established the Chabad community in Hebron; remembered for rivers of kindness.",
    },
    {
        "kind": "memoriam", "badge": "🕯 IN MEMORIAM · ז״ל", "h_month": 8, "h_day": 20,
        "title": "Rabbi Lord Jonathan Sacks (ז״ל)", "date_label": "20 Cheshvan · 2020",
        "subtitle": "Voice of Moral Clarity Across Nations",
        "text": "Taught that optimism is passive, while hope is active: 'Hope is the belief that together we can make things better.'",
    },
    {
        "kind": "memoriam", "badge": "🕯 IN MEMORIAM · ז״ל", "h_month": 8, "h_day": 21,
        "title": "Hannah Senesh (ז״ל)", "date_label": "21 Cheshvan · 1944",
        "subtitle": "Poet & Heroic Parachutist",
        "text": "Parachuted into Nazi-occupied Europe at age 22 to rescue Jews; her poem 'Eli, Eli' remains one of the most beloved prayers for peace.",
    },
    {
        "kind": "memoriam", "badge": "🕯 IN MEMORIAM · ז״ל", "h_month": 10, "h_day": 20,
        "title": "Maimonides — The Rambam (ז״ל)", "date_label": "20 Tevet · 1204",
        "subtitle": "Physician, Philosopher & Codifier",
        "text": "Royal physician in Cairo who authored the Mishneh Torah and Guide for the Perplexed — uniting medicine, philosophy, and Torah.",
    },
    {
        "kind": "memoriam", "badge": "🕯 IN MEMORIAM · ז״ל", "h_month": 4, "h_day": 29,
        "title": "Rashi — Rabbi Shlomo Yitzchaki (ז״ל)", "date_label": "29 Tammuz · 1105",
        "subtitle": "Master Commentator of Troyes, France",
        "text": "Vintner and scholar whose crystal-clear commentary on the entire Torah and Talmud has guided learners of every age for 900+ years.",
    },
    {
        "kind": "memoriam", "badge": "🕯 IN MEMORIAM · זצ״ל", "h_month": 4, "h_day": 3,
        "title": "The Lubavitcher Rebbe (זצ״ל)", "date_label": "3 Tammuz · 1994",
        "subtitle": "Architect of Global Jewish Outreach",
        "text": "Built a global network of over 5,000 Chabad Houses — turning every corner of the world into a warm, open-door home for Shabbat.",
    },
    {
        "kind": "memoriam", "badge": "🕯 IN MEMORIAM · ז״ל", "h_month": 12, "h_day": 15,
        "title": "Dona Gracia Mendes Nasi (ז״ל)", "date_label": "1569 · Antwerp",
        "subtitle": "Renaissance Philanthropist & Rescuer",
        "text": "Led a daring underground rescue network right from Antwerp, Belgium — saving thousands from the Inquisition and rebuilding Tiberias.",
    },
    # --- COMMUNITY, BRUSSELS & JEWISH INNOVATION FACTS ---
    {
        "kind": "community", "badge": "🌍 BRUSSELS HERITAGE", "g_month": 0, "g_day": 0,
        "title": "The Great Synagogue of Europe", "date_label": "Brussels · 1878",
        "subtitle": "Heart of Belgian Jewish History",
        "text": "Built in 1878 on Rue de la Régence in Romanesque-Byzantine style, it survived WWII and became the Great Synagogue of Europe in 2008.",
    },
    {
        "kind": "community", "badge": "🌍 BELGIAN HEROISM", "g_month": 0, "g_day": 0,
        "title": "1,790+ Belgian Righteous Among Nations", "date_label": "Yad Vashem",
        "subtitle": "Courage & Solidarity in Belgium",
        "text": "Through the Belgian Committee for the Defense of Jews and brave families, over 25,000 Jews — including 3,000+ children — were sheltered.",
    },
    {
        "kind": "community", "badge": "💡 JEWISH INNOVATION", "g_month": 0, "g_day": 0,
        "title": "22% of All Nobel Prize Laureates", "date_label": "Global Impact",
        "subtitle": "Culture of Questions & Lifelong Study",
        "text": "Representing under 0.2% of humanity, Jewish thinkers have received 210+ Nobel Prizes across Physics, Medicine, Chemistry & Peace.",
    },
    {
        "kind": "community", "badge": "🌍 LIVING LANGUAGE", "g_month": 0, "g_day": 0,
        "title": "Hebrew — The Only Revived Ancient Tongue", "date_label": "3,300+ Years",
        "subtitle": "From Dead Sea Scrolls to Everyday Street",
        "text": "A child in Jerusalem or Brussels today can read a 2,100-year-old Dead Sea Scroll of Isaiah aloud — the only revived ancient mother tongue.",
    },
    {
        "kind": "community", "badge": "💡 EVERYDAY INVENTIONS", "g_month": 0, "g_day": 0,
        "title": "Drip Irrigation, USB Drives & PillCam", "date_label": "Tikkun Olam",
        "subtitle": "Innovation That Feeds & Heals Millions",
        "text": "Modern drip irrigation, the USB flash drive, Waze navigation, and the swallowable PillCam diagnostic camera all grew out of Israeli labs.",
    },
    {
        "kind": "wit", "badge": "✨ JEWISH WISDOM", "g_month": 0, "g_day": 0,
        "title": "Classic Community Proverb", "date_label": "L'Dor VaDor",
        "subtitle": "From Generation to Generation",
        "text": "“A single candle can light a thousand others without diminishing its own flame — and when you teach a child, you teach generations.”",
    },
]


def get_community_heritage() -> dict:
    """Return date-prioritized Jewish Birthdays, In Memoriam (Yahrzeits), Brussels/Global Facts & Wit."""
    snap = sacred_astronomy.get_sacred_moment()
    he = snap["hebrew_date"]
    h_month, h_day = int(he["month"]), int(he["day"])
    now = datetime.now()
    g_month, g_day = now.month, now.day

    def _score(it):
        if it["kind"] == "birthday" and it.get("g_month"):
            dist = abs((it["g_month"] * 31 + it["g_day"]) - (g_month * 31 + g_day))
            return (0 if dist <= 14 else 2, dist)
        if it["kind"] == "memoriam" and it.get("h_month"):
            dist = abs((it["h_month"] * 30 + it["h_day"]) - (h_month * 30 + h_day))
            return (0 if dist <= 20 else 2, dist)
        return (1, 0)

    ranked = sorted(COMMUNITY_HERITAGE_ITEMS, key=_score)
    # Interleave Birthday -> In Memoriam -> Community Fact -> Wit so rotation feels rich & varied!
    buckets = {k: [x for x in ranked if x["kind"] == k] for k in ("birthday", "memoriam", "community", "wit")}
    ordered = []
    # 0. Prioritize active Community Yahrzeits, Kiddush Honors, Refuah & Simcha dedications first!
    try:
        import community_hub
        deds = community_hub.list_dedications(active_only=True, limit=12)
        badge_map = {
            "yahrzeit": ("🕯 COMMUNITY YAHRZEIT · ז״ל", "In Loving Memory · Ner Neshama"),
            "kiddush": ("🥂 SHABBAT KIDDUSH HONOR", "Sponsored by Our Community"),
            "refuah": ("💚 REFUAH SHLEIMAH", "Community Prayer for Healing"),
            "simcha": ("🎉 COMMUNITY SIMCHA", "Mazal Tov from The Shul!"),
        }
        for d in deds:
            b_lbl, sub_default = badge_map.get(d.get("kind"), ("🕯 COMMUNITY HONOR", "The European Synagogue"))
            by = f"Dedicated by {d['submitted_by']}" if d.get("submitted_by") else sub_default
            ordered.append({
                "kind": "memoriam" if d.get("kind") == "yahrzeit" else "community",
                "badge": b_lbl,
                "title": d.get("honoree_name", ""),
                "date_label": d.get("hebrew_date_label") or he.get("en_str", "This Week"),
                "subtitle": by,
                "text": d.get("message", ""),
                "is_community_dedication": True,
            })
    except Exception:
        pass

    for i in range(max(len(v) for v in buckets.values())):
        for k in ("birthday", "memoriam", "community", "wit"):
            if i < len(buckets[k]):
                ordered.append(buckets[k][i])
    return {
        "hebrew_date": he,
        "items": ordered,
        "count": len(ordered),
    }
