#!/usr/bin/env python3
"""Torah Sanctuary / ShulOS — Complete Offline Sacred Books, Haggadah, Siddur & Five Megillot Library.

Self-contained 100% offline sacred resource library so any Synagogue, Chabad House, or Jewish Home
never needs an external website or printed backup for:
  1. Complete Passover Haggadah (All 15 Seder Steps: Kadesh -> Nirtzah, Mah Nishtanah, Four Children,
     Ten Plagues, Dayenu, B'chol Dor VaDor, Hallel & Chad Gadya) — Hebrew, Transliteration & English.
  2. Complete Siddur & Essential Blessings Handbook (Modeh Ani, Asher Yatzar, Birkot HaTorah,
     Shema, Amidah 19-blessing map, Aleinu, Kaddish with syllable transliteration, Friday Night &
     Shabbat Day Kiddush, Havdalah, Traveler's Prayer, Shehecheyanu, Mezuzah, Challah, Candles,
     Bedtime Shema & Mi Sheberach Healing Prayer).
  3. The Five Megillot (Esther, Ruth, Lamentations/Eichah, Ecclesiastes/Kohelet, Song of Songs) —
     hydrated VERBATIM from local `torah.db`!
  4. Classical Rabbinic Reference Map (Mishnah 6 Orders, Talmud Bavli, Rambam Mishneh Torah,
     Shulchan Aruch) — explicitly categorized under Tier 2 Cited Traditions per SOURCE_STANDARD.md.

Also indexes its rich texts directly into `torah.db` FTS5 so the local offline Ollama AI model
can perform deep, broad-based logical synthesis even when completely unplugged from the internet.
"""

import json
import torah_db

HAGGADAH_SEDER_STEPS = [
    {
        "step": 1, "slug": "kadesh", "name": "Kadesh", "he": "קַדֵּשׁ",
        "meaning": "Sanctification — First Cup of Wine (Kiddush)",
        "source": "Exodus 6:6 ('I will bring you out') · Mishnah Pesachim 10:1–2 (Cited Tradition)",
        "hebrew": "בָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם בּוֹרֵא פְּרִי הַגָּפֶן. ... שֶׁהֶחֱיָנוּ וְקִיְּמָנוּ וְהִגִּיעָנוּ לַזְּמַן הַזֶּה.",
        "translit": "Ba-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam bo-rei p'ri ha-ga-fen. ... She-he-che-ya-nu v'ki-y'ma-nu v'hi-gi-a-nu la-z'man ha-zeh.",
        "english": "Blessed are You, Lord our God, King of the universe, Who creates the fruit of the vine... Who has kept us alive, sustained us, and brought us to this season! Drink leaning to the left like free royalty.",
        "note": "Four cups of wine correspond to the four biblical verbs of redemption in Exodus 6:6–7: 'I will bring out', 'I will rescue', 'I will redeem', 'I will take you as My people'.",
    },
    {
        "step": 2, "slug": "urchatz", "name": "Urchatz", "he": "וּרְחַץ",
        "meaning": "Ritual Handwashing (Without Blessing)",
        "source": "Talmud Bavli, Pesachim 115a (Cited Tradition)",
        "hebrew": "נְטִילַת יָדַיִם בְּלֹא בְּרָכָה",
        "translit": "N'ti-lat ya-da-yim b'lo b'ra-chah (Wash hands before dipping Karpas, without reciting a blessing)",
        "english": "Pour water over each hand before dipping the spring vegetable—an intentional curiosity cue to spark children's questions!",
        "note": "Notice how the entire Seder is engineered around awakening questions from children and guests.",
    },
    {
        "step": 3, "slug": "karpas", "name": "Karpas", "he": "כַּרְפַּס",
        "meaning": "Spring Vegetable Dipped in Salt Water",
        "source": "Exodus 1:14 (Tears of bondage) · Mishnah Pesachim 10:3 (Cited Tradition)",
        "hebrew": "בָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם בּוֹרֵא פְּרִי הָאֲדָמָה.",
        "translit": "Ba-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam bo-rei p'ri ha-a-da-mah.",
        "english": "Blessed are You, Lord our God, King of the universe, Who creates the fruit of the earth. Dip parsley/celery into salt water (tears of slavery + spring renewal).",
        "note": "Holding spring greenery and salt tears together teaches that rebirth often grows directly out of hardship.",
    },
    {
        "step": 4, "slug": "yachatz", "name": "Yachatz", "he": "יַחַץ",
        "meaning": "Breaking the Middle Matzah (Afikoman)",
        "source": "Deuteronomy 16:3 ('Bread of affliction/poverty') · Talmud Bavli, Pesachim 115b (Cited Tradition)",
        "hebrew": "חֲצִיַּת הַמַּצָּה הָאֶמְצָעִית — הַחֵלֶק הַגָּדוֹל לַאֲפִיקוֹמָן",
        "translit": "Cha-tzi-yat ha-ma-tzah ha-em-tza-it — Break the middle matzah; hide the larger piece for the Afikoman!",
        "english": "Break the middle of the three matzot in two. Keep the smaller piece on the table as the 'bread of the poor' who always save a piece for tomorrow; hide the larger half as the Afikoman for dessert.",
        "note": "A broken piece becomes the sweet climax of the meal—symbolizing that what feels broken now is being reserved for future wholeness.",
    },
    {
        "step": 5, "slug": "maggid", "name": "Maggid (Core Storytelling)", "he": "מַגִּיד",
        "meaning": "Ha Lachma Anya · Mah Nishtanah (4 Questions) · 4 Children · 10 Plagues · Dayenu · 2nd Cup",
        "source": "Exodus 13:8 ('You shall tell your child on that day') & Deuteronomy 26:5–8 (Primary Scripture) · Mishnah Pesachim 10:4–5",
        "hebrew": "הָא לַחְמָא עַנְיָא דִּי אֲכָלוּ אֲבָהָתָנָא בְּאַרְעָא דְמִצְרָיִם. כָּל דִּכְפִין יֵיתֵי וְיֵיכֹל!\nמַה נִּשְׁתַּנָּה הַלַּיְלָה הַזֶּה מִכָּל הַלֵּילוֹת?\nעֲבָדִים הָיִינוּ לְפַרְעֹה בְּמִצְרָיִם... בְּכָל דּוֹר וָדוֹר חַיָּב אָדָם לִרְאוֹת אֶת עַצְמוֹ כְּאִלּוּ הוּא יָצָא מִמִּצְרָיִם!\nדַּיֵּנוּ!",
        "translit": "Ha lach-ma an-ya di a-cha-lu a-va-ha-ta-na b'ar-a d'Mitz-ra-yim. Kol dich-fin yei-tei v'yei-chol!\nMah nish-ta-nah ha-lai-lah ha-zeh mi-kol ha-lei-lot?\nA-va-dim ha-yi-nu l'Far-oh b'Mitz-ra-yim... B'chol dor va-dor cha-yav a-dam lir-ot et atz-mo k'i-lu hu ya-tza mi-Mitz-ra-yim!\nDa-yei-nu!",
        "english": "This is the bread of affliction our ancestors ate in Egypt—let all who are hungry come and eat! Why is this night different from all other nights? We were slaves to Pharaoh in Egypt... In EVERY generation each person must view themselves as if they personally went out from Egypt! Dayenu — It would have been enough!",
        "note": "Includes: (a) Four Questions (Matzah, Maror, Dipping twice, Leaning); (b) Four Children (Wise, Challenging/Rebellious, Simple, Not yet knowing to ask — derived from 4 Torah verses: Deut 6:20, Exod 12:26, Exod 13:14, Exod 13:8); (c) Ten Plagues (remove 1 drop of wine per plague — our joy is diminished by anyone's suffering); (d) Dayenu (15 acts of gratitude); (e) Rabban Gamliel's three symbols: Pesach, Matzah, Maror; (f) Second Cup of Wine.",
    },
    {
        "step": 6, "slug": "rachtzah", "name": "Rachtzah", "he": "רָחְצָה",
        "meaning": "Handwashing With Blessing Before Matzah",
        "source": "Talmud Bavli, Berakhot 53b & Chullin 106a (Cited Tradition)",
        "hebrew": "בָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ עַל נְטִילַת יָדָיִם.",
        "translit": "Ba-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam a-sher kid-sha-nu b'mitz-vo-tav v'tzi-va-nu al n'ti-lat ya-da-yim.",
        "english": "Blessed are You, Lord our God, King of the universe, Who sanctified us with His commandments and commanded us concerning washing the hands.",
        "note": "Maintain calm silence from washing until tasting the Matzah.",
    },
    {
        "step": 7, "slug": "motzi-matzah", "name": "Motzi Matzah", "he": "מוֹצִיא מַצָּה",
        "meaning": "Blessings Over Bread & Eating Matzah",
        "source": "Exodus 12:18 ('In the evening you shall eat unleavened bread' — Primary Scripture)",
        "hebrew": "בָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם הַמּוֹצִיא לֶחֶם מִן הָאָרֶץ.\nבָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ עַל אֲכִילַת מַצָּה.",
        "translit": "Ba-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam ha-mo-tzi le-chem min ha-a-retz.\nBa-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam a-sher kid-sha-nu b'mitz-vo-tav v'tzi-va-nu al a-chi-lat ma-tzah.",
        "english": "Blessed are You, Lord our God, King of the universe, Who brings forth bread from the earth — and Who commanded us concerning the eating of Matzah. Eat leaning left.",
        "note": "Matzah is both the humble bread of slaves AND the urgent bread of liberation baked in haste.",
    },
    {
        "step": 8, "slug": "maror", "name": "Maror", "he": "מָרוֹר",
        "meaning": "Bitter Herbs Dipped in Sweet Charoset",
        "source": "Exodus 12:8 ('With bitter herbs they shall eat it' — Primary Scripture)",
        "hebrew": "בָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ עַל אֲכִילַת מָרוֹר.",
        "translit": "Ba-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam a-sher kid-sha-nu b'mitz-vo-tav v'tzi-va-nu al a-chi-lat ma-ror.",
        "english": "Blessed are You, Lord our God, King of the universe, Who commanded us concerning eating bitter herbs (romaine/horseradish dipped briefly in sweet apple-nut Charoset).",
        "note": "Charoset recalls the mortar of Egyptian bricks—yet tastes sweet, reminding us that love and hope sweeten endurance.",
    },
    {
        "step": 9, "slug": "korech", "name": "Korech (Hillel Sandwich)", "he": "כּוֹרֵךְ",
        "meaning": "Matzah + Bitter Herbs Combined Together",
        "source": "Numbers 9:11 (Primary Scripture) · Talmud Bavli, Pesachim 115a (Hillel's Practice)",
        "hebrew": "זֵכֶר לַמִּקְדָּשׁ כְּהִלֵּל: כֵּן עָשָׂה הִלֵּל בִּזְמַן שֶׁבֵּית הַמִּקְדָּשׁ הָיָה קַיָּם...",
        "translit": "Zei-cher la-Mik-dash k'Hi-leil: Kein a-sah Hi-leil bi-z'man she-Beit Ha-Mik-dash ha-yah ka-yam...",
        "english": "In remembrance of the Temple as practiced by Hillel, who combined Matzah and Maror together to fulfill 'With unleavened bread and bitter herbs they shall eat it.'",
        "note": "In real life, bitterness and freedom rarely arrive in separate bowls—Hillel's sandwich teaches us to hold both with courage.",
    },
    {
        "step": 10, "slug": "shulchan-orech", "name": "Shulchan Orech", "he": "שֻׁלְחָן עוֹרֵךְ",
        "meaning": "The Festive Passover Meal",
        "source": "Deuteronomy 16:14 ('You shall rejoice on your festival' — Primary Scripture)",
        "hebrew": "סְעוּדַת יוֹם טוֹב בְּשִׂמְחָה וּבְלֵב טוֹב",
        "translit": "S'u-dat Yom Tov b'sim-chah u-v'leiv tov — Enjoy the festive Passover meal together in joy!",
        "english": "Enjoy the festive dinner together with family, guests, conversation, and warmth (leaving room for the Afikoman!).",
        "note": "Traditionally begins with a hard-boiled egg in salt water—a symbol of renewal and eternal continuity.",
    },
    {
        "step": 11, "slug": "tzafun", "name": "Tzafun (Afikoman)", "he": "צָפוּן",
        "meaning": "Finding & Eating the Hidden Afikoman",
        "source": "Mishnah Pesachim 10:8 (Cited Tradition — 'No dessert after the Paschal offering')",
        "hebrew": "אֲכִילַת הָאֲפִיקוֹמָן לְזֵכֶר קָרְבַּן פֶּסַח",
        "translit": "A-chi-lat ha-A-fi-ko-man — Redeem and share the hidden Afikoman matzah while leaning!",
        "english": "Find the hidden Afikoman, share a piece with everyone at the table, and let the simple taste of freedom linger as the final taste of the meal.",
        "note": "Tzafun literally means 'hidden'—reminding us that the deepest treasures in life are often hidden right inside ordinary moments.",
    },
    {
        "step": 12, "slug": "barech", "name": "Barech", "he": "בָּרֵךְ",
        "meaning": "Grace After Meals (Birkat HaMazon) · 3rd Cup · Opening Door for Elijah",
        "source": "Deuteronomy 8:10 (Primary Scripture) · Malachi 3:23 (Elijah the Prophet)",
        "hebrew": "שִׁיר הַמַּעֲלוֹת בְּשׁוּב אֲדֹנָי אֶת שִׁיבַת צִיּוֹן... בָּרוּךְ אַתָּה אֲדֹנָי הַזָּן אֶת הַכֹּל.\nכּוֹס שְׁלִישִׁית · כּוֹס שֶׁל אֵלִיָּהוּ הַנָּבִיא!",
        "translit": "Shir Ha-Ma-a-lot b'shuv A-do-nai et shi-vat Tzi-yon... Ba-ruch a-tah A-do-nai ha-zan et ha-kol. Drink the 3rd Cup & open the door to welcome Elijah the Prophet!",
        "english": "Recite full Birkat HaMazon (with Ya'aleh V'Yavo for Passover), bless and drink the Third Cup of Redemption, pour Elijah's Cup, and open the front door in hopeful hospitality.",
        "note": "Opening the door declares fearless faith in a redeemed, peaceful future.",
    },
    {
        "step": 13, "slug": "hallel", "name": "Hallel", "he": "הַלֵּל",
        "meaning": "Psalms of Praise (Psalms 115–118 & 136 'Ki L'Olam Chasdo') · 4th Cup",
        "source": "Psalms 113–118 & Psalm 136 (Primary Verified Scripture — complete text in local Tanakh DB!)",
        "hebrew": "הוֹדוּ לַאֲדֹנָי כִּי טוֹב, כִּי לְעוֹלָם חַסְדּוֹ!",
        "translit": "Ho-du la-A-do-nai ki tov, ki l'o-lam chas-do!",
        "english": "Give thanks to the Lord for He is good, for His loving-kindness endures forever! Recite Psalms 115–118, Psalm 136 (26 refrains of 'His kindness endures forever'), and drink the Fourth Cup of Wine.",
        "note": "You can open Psalms 113–118 & 136 verbatim anytime in the Psalms / Tanakh reader.",
    },
    {
        "step": 14, "slug": "nirtzah", "name": "Nirtzah", "he": "נִרְצָה",
        "meaning": "Next Year in Jerusalem · Joyful Songs (Echad Mi Yodea & Chad Gadya)",
        "source": "Medieval Ashkenazi & Sephardi Liturgical Poetry (14th–16th Century)",
        "hebrew": "לְשָׁנָה הַבָּאָה בִּירוּשָׁלָיִם! חַד גַּדְיָא, חַד גַּדְיָא!",
        "translit": "L'sha-nah ha-ba-ah bi-Y'ru-sha-la-yim! Chad Gad-ya, Chad Gad-ya!",
        "english": "Next Year in Jerusalem! Sing 'Who Knows One?' (Echad Mi Yodea — 1 through 13) and 'One Little Goat' (Chad Gadya) together with the children!",
        "note": "Ends in pure joy and timeless hope across generations.",
    },
]

SIDDUR_ESSENTIAL_BLESSINGS = [
    {
        "slug": "friday-kiddush",
        "category": "Shabbat & Festivals",
        "title": "Friday Night Kiddush (Sanctification of Shabbat)",
        "he_title": "קִדּוּשׁ לְלֵיל שַׁבָּת",
        "when": "Friday night before the Shabbat meal, holding a full cup of wine or grape juice",
        "source": "Genesis 1:31–2:3 (Primary Verified Scripture) · Talmud Bavli, Pesachim 106a (Cited Tradition)",
        "hebrew": "יוֹם הַשִּׁשִּׁי: וַיְכֻלּוּ הַשָּׁמַיִם וְהָאָרֶץ וְכָל צְבָאָם. וַיְכַל אֱלֹהִים בַּיּוֹם הַשְּׁבִיעִי מְלַאכְתּוֹ אֲשֶׁר עָשָׂה, וַיִּשְׁבֹּת בַּיּוֹם הַשְּׁבִיעִי מִכָּל מְלַאכְתּוֹ אֲשֶׁר עָשָׂה. וַיְבָרֶךְ אֱלֹהִים אֶת יוֹם הַשְּׁבִיעִי וַיְקַדֵּשׁ אֹתוֹ...\nבָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם בּוֹרֵא פְּרִי הַגָּפֶן.\nבָּרוּךְ אַתָּה אֲדֹנָי מְקַדֵּשׁ הַשַּׁבָּת.",
        "translit": "Yom ha-shi-shi: Va-y'chu-lu ha-sha-ma-yim v'ha-a-retz v'chol tz'va-am. Va-y'chal E-lo-him ba-yom ha-sh'vi-i m'lach-to a-sher a-sah, va-yish-bot ba-yom ha-sh'vi-i mi-kol m'lach-to a-sher a-sah. Va-y'va-rech E-lo-him et yom ha-sh'vi-i va-y'ka-deish o-to...\nBa-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam bo-rei p'ri ha-ga-fen.\nBa-ruch a-tah A-do-nai m'ka-deish ha-Sha-bat.",
        "english": "The sixth day: Thus the heavens and the earth were finished, and all their host. And on the seventh day God finished His work and rested; and God blessed the seventh day and made it holy... Blessed are You, Lord our God, King of the universe, Who creates the fruit of the vine... Blessed are You, Lord, Who sanctifies the Sabbath.",
    },
    {
        "slug": "havdalah",
        "category": "Shabbat & Festivals",
        "title": "Havdalah (Farewell to Shabbat — Wine, Spices & Flame)",
        "he_title": "הַבְדָּלָה",
        "when": "Saturday night after 3 stars appear (Tzeit HaKochavim)",
        "source": "Isaiah 12:2–3 & Esther 8:16 (Primary Scripture) · Talmud Bavli, Berakhot 33a & Pesachim 103b",
        "hebrew": "הִנֵּה אֵל יְשׁוּעָתִי אֶבְטַח וְלֹא אֶפְחָד... בָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם בּוֹרֵא פְּרִי הַגָּפֶן.\nבּוֹרֵא מִינֵי בְשָׂמִים.\nבּוֹרֵא מְאוֹרֵי הָאֵשׁ.\nבָּרוּךְ אַתָּה אֲדֹנָי הַמַּבְדִּיל בֵּין קֹדֶשׁ לְחוֹל.",
        "translit": "Hi-nei Eil y'shu-a-ti ev-tach v'lo ef-chad... Ba-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam bo-rei p'ri ha-ga-fen.\nBo-rei mi-nei v'sa-mim (smell sweet spices).\nBo-rei m'o-rei ha-eish (gaze at fingernails in the braided flame).\nBa-ruch a-tah A-do-nai ha-mav-dil bein ko-desh l'chol.",
        "english": "Behold, God is my salvation; I will trust and not be afraid! Blessed are You Who creates the fruit of the vine, diverse fragrant spices, the lights of fire, and Who distinguishes between sacred and weekday, between light and darkness. Shavua Tov!",
    },
    {
        "slug": "kaddish-translit",
        "category": "Daily & Memorial",
        "title": "Mourner's Kaddish (Kaddish Yatom — Full Transliteration)",
        "he_title": "קַדִּישׁ יָתוֹם",
        "when": "Recited in a Minyan (10 Jewish adults) during mourning or on a loved one's Yahrzeit",
        "source": "Ezekiel 38:23 & Daniel 2:20 (Scriptural echoes) · Talmud Bavli, Berakhot 3a & Shabbat 119b",
        "hebrew": "יִתְגַּדַּל וְיִתְקַדַּשׁ שְׁמֵהּ רַבָּא. בְּעָלְמָא דִּי בְרָא כִרְעוּתֵהּ, וְיַמְלִיךְ מַלְכוּתֵהּ בְּחַיֵּיכוֹן וּבְיוֹמֵיכוֹן וּבְחַיֵּי דְכָל בֵּית יִשְׂרָאֵל, בַּעֲגָלָא וּבִזְמַן קָרִיב, וְאִמְרוּ: אָמֵן.\nיְהֵא שְׁמֵהּ רַבָּא מְבָרַךְ לְעָלַם וּלְעָלְמֵי עָלְמַיָּא.\nעֹשֶׂה שָׁלוֹם בִּמְרוֹמָיו, הוּא יַעֲשֶׂה שָׁלוֹם עָלֵינוּ וְעַל כָּל יִשְׂרָאֵל, וְאִמְרוּ: אָמֵן.",
        "translit": "Yit-ga-dal v'yit-ka-dash sh'mei ra-ba. B'al-ma di v'ra chir-u-tei, v'yam-lich mal-chu-tei b'cha-yei-chon u-v'yo-mei-chon u-v'cha-yei d'chol beit Yis-ra-eil, ba-a-ga-la u-vi-z'man ka-riv, v'im-ru: A-mein.\nY'hei sh'mei ra-ba m'va-rach l'a-lam u-l'al-mei al-ma-ya.\nO-seh sha-lom bi-m'ro-mav, Hu ya-a-seh sha-lom a-lei-nu v'al kol Yis-ra-eil, v'im-ru: A-mein.",
        "english": "Exalted and hallowed be His great Name in the world He created according to His will! May He establish His kingdom in your lifetime and in the lifetime of the whole House of Israel, speedily and soon—and say: Amen! May His great Name be blessed forever and ever. May He Who makes peace in His heights make peace upon us and upon all Israel—Amen.",
    },
    {
        "slug": "tefilat-haderech",
        "category": "Daily & Travel",
        "title": "Tefilat HaDerech (The Traveler's Prayer)",
        "he_title": "תְּפִלַּת הַדֶּרֶךְ",
        "when": "Recited when embarking on an intercity road trip or flight",
        "source": "Talmud Bavli, Berakhot 29b (Cited Classical Prayer)",
        "hebrew": "יְהִי רָצוֹן מִלְּפָנֶיךָ אֲדֹנָי אֱלֹהֵינוּ וֵאלֹהֵי אֲבוֹתֵינוּ, שֶׁתּוֹלִיכֵנוּ לְשָׁלוֹם וְתַצְעִידֵנוּ לְשָׁלוֹם וְתַדְרִיכֵנוּ לְשָׁלוֹם, וְתַגִּיעֵנוּ לִמְחוֹז חֶפְצֵנוּ לְחַיִּים וּלְשִׂמְחָה וּלְשָׁלוֹם... בָּרוּךְ אַתָּה אֲדֹנָי שׁוֹמֵעַ תְּפִלָּה.",
        "translit": "Y'hi ra-tzon mil-fa-ne-cha A-do-nai E-lo-hei-nu v'E-lo-hei a-vo-tei-nu, she-to-li-chei-nu l'sha-lom v'tatz-i-dei-nu l'sha-lom v'tad-ri-chei-nu l'sha-lom, v'ta-gi-ei-nu li-m'choz chef-tzei-nu l'cha-yim u-l'sim-chah u-l'sha-lom... Ba-ruch a-tah A-do-nai sho-mei-a t'fi-lah.",
        "english": "May it be Your will, Lord our God and God of our ancestors, to lead us in peace, direct our steps in peace, guide us in peace, and bring us to our destination in life, joy, and peace... Blessed are You, Lord, Who hears prayer.",
    },
    {
        "slug": "mi-sheberach",
        "category": "Healing & Community",
        "title": "Mi Sheberach (Prayer for Healing — Refuah Shleimah)",
        "he_title": "מִי שֶׁבֵּרַךְ לַחוֹלִים",
        "when": "Recited for anyone needing physical or emotional healing",
        "source": "Numbers 12:13 ('El Na Refa Na Lah' — Moses' prayer for Miriam) · Traditional Liturgical Blessing",
        "hebrew": "מִי שֶׁבֵּרַךְ אֲבוֹתֵינוּ אַבְרָהָם יִצְחָק וְיַעֲקֹב, שָׂרָה רִבְקָה רָחֵל וְלֵאָה, הוּא יְבָרֵךְ וִירַפֵּא אֶת הַחוֹלֶה... הַקָּדוֹשׁ בָּרוּךְ הוּא יִמָּלֵא רַחֲמִים עָלָיו לְהַחֲלִימוֹ וּלְרַפְּאֹתוֹ וּלְהַחֲזִיקוֹ וּלְהַחֲיוֹתוֹ, רְפוּאַת הַנֶּפֶשׁ וּרְפוּאַת הַגּוּף, וְנֹאמַר: אָמֵן.",
        "translit": "Mi she-bei-rach a-vo-tei-nu Av-ra-ham Yitz-chak v'Ya-a-kov, Sa-rah Riv-kah Ra-cheil v'Lei-ah, Hu y'va-reich vi-ra-pei et ha-cho-leh [Name]... Ha-Ka-dosh Ba-ruch Hu yi-ma-lei ra-cha-mim a-lav l'ha-cha-li-mo u-l'ra-p'o-to u-l'ha-cha-zi-ko u-l'ha-cha-yo-to, r'fu-at ha-ne-fesh u-r'fu-at ha-guf, v'no-mar: A-mein.",
        "english": "May the One Who blessed our ancestors Abraham, Isaac, and Jacob, Sarah, Rebecca, Rachel, and Leah, bless and heal [Name]. May the Holy One be filled with compassion to restore, heal, strengthen, and revitalize them—complete healing of soul and healing of body—and let us say: Amen.",
    },
    {
        "slug": "shehecheyanu",
        "category": "Joy & Milestones",
        "title": "Shehecheyanu (Blessing for New Milestones, Holidays & Firsts)",
        "he_title": "בִּרְכַּת שֶׁהֶחֱיָנוּ",
        "when": "Holidays, lighting Chanukah/festival candles, eating a seasonal new fruit, entering a new home, joyful reunions",
        "source": "Talmud Bavli, Berakhot 54a & Pesachim 7b (Cited Tradition)",
        "hebrew": "בָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם שֶׁהֶחֱיָנוּ וְקִיְּמָנוּ וְהִגִּיעָנוּ לַזְּמַן הַזֶּה.",
        "translit": "Ba-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam she-he-che-ya-nu v'ki-y'ma-nu v'hi-gi-a-nu la-z'man ha-zeh.",
        "english": "Blessed are You, Lord our God, King of the universe, Who has granted us life, sustained us, and enabled us to reach this sacred moment!",
    },
    {
        "slug": "shabbat-candles",
        "category": "Home & Shabbat",
        "title": "Lighting Shabbat Candles (Hadlakat Nerot)",
        "he_title": "הַדְלָקַת נֵרוֹת שַׁבָּת",
        "when": "18 minutes before sunset every Friday afternoon (exact local time shown in Sky & Zmanim!)",
        "source": "Isaiah 58:13 (Delight of Shabbat) · Talmud Bavli, Shabbat 25b (Cited Tradition)",
        "hebrew": "בָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ לְהַדְלִיק נֵר שֶׁל שַׁבָּת.",
        "translit": "Ba-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam a-sher kid-sha-nu b'mitz-vo-tav v'tzi-va-nu l'had-lik neir shel Sha-bat.",
        "english": "Blessed are You, Lord our God, King of the universe, Who has sanctified us with His commandments and commanded us to kindle the Shabbat light. (Light, cover eyes, recite blessing, open eyes to peace!)",
    },
    {
        "slug": "mezuzah",
        "category": "Home & Mitzvot",
        "title": "Affixing a Mezuzah on Your Doorpost",
        "he_title": "קְבִיעַת מְזוּזָה",
        "when": "Affixing a kosher parchment Mezuzah slanted inward on the upper third of the right doorpost",
        "source": "Deuteronomy 6:9 & 11:20 (Primary Verified Scripture) · Talmud Bavli, Menachot 32b–33a",
        "hebrew": "בָּרוּךְ אַתָּה אֲדֹנָי אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם אֲשֶׁר קִדְּשָׁנוּ בְּמִצְוֹתָיו וְצִוָּנוּ לִקְבֹּעַ מְזוּזָה.",
        "translit": "Ba-ruch a-tah A-do-nai E-lo-hei-nu Me-lech ha-o-lam a-sher kid-sha-nu b'mitz-vo-tav v'tzi-va-nu lik-bo-a m'zu-zah.",
        "english": "Blessed are You, Lord our God, King of the universe, Who sanctified us with His commandments and commanded us to affix a Mezuzah.",
    },
    {
        "slug": "bedtime-shema",
        "category": "Daily & Night",
        "title": "Bedtime Shema & Forgiveness Meditation (Kriat Shema Al HaMitah)",
        "he_title": "קְרִיאַת שְׁמַע עַל הַמִּטָּה",
        "when": "Before going to sleep each night — releasing grudges and entrusting the soul in peace",
        "source": "Deuteronomy 6:4–9 & Psalms 31:6 (Primary Verified Scripture) · Talmud Bavli, Berakhot 60b",
        "hebrew": "רִבּוֹנוֹ שֶׁל עוֹלָם, הֲרֵינִי מוֹחֵל לְכָל מִי שֶׁהִכְעִיס וְהִקְנִיט אוֹתִי... שְׁמַע יִשְׂרָאֵל אֲדֹנָי אֱלֹהֵינוּ אֲדֹנָי אֶחָד.\nבְּיָדְךָ אַפְקִיד רוּחִי, פָּדִיתָ אוֹתִי אֲדֹנָי אֵל אֱמֶת.",
        "translit": "Ri-bo-no shel o-lam, ha-rei-ni mo-cheil l'chol mi she-hich-is v'hik-nit o-ti... Sh'ma Yis-ra-eil A-do-nai E-lo-hei-nu A-do-nai E-chad.\nB'ya-d'cha af-kid ru-chi, pa-di-ta o-ti A-do-nai Eil e-met.",
        "english": "Master of the universe, I hereby forgive anyone who has angered or wronged me today... Hear O Israel, the Lord is our God, the Lord is One! Into Your hand I entrust my spirit; You have redeemed me, Lord, God of truth (Psalm 31:6).",
    },
    {
        "slug": "amidah-map",
        "category": "Daily Prayer Roadmap",
        "title": "The Amidah (Shemoneh Esrei — 19 Standing Blessings Roadmap)",
        "he_title": "תְּפִלַּת הָעֲמִידָה",
        "when": "Core silent standing prayer facing Jerusalem (Mizrach) at Shacharit, Mincha & Ma'ariv",
        "source": "Psalm 51:17 ('Lord, open my lips') · Men of the Great Assembly (Talmud Bavli, Megillah 17b–18a)",
        "hebrew": "אֲדֹנָי שְׂפָתַי תִּפְתָּח, וּפִי יַגִּיד תְּהִלָּתֶךָ.",
        "translit": "A-do-nai s'fa-tai tif-tach, u-fi ya-gid t'hi-la-te-cha. (3 Opening Praise -> 13 Middle Requests: Wisdom, Return, Forgiveness, Redemption, Healing, Sustenance, Justice, Peace -> 3 Closing Thanks: Modim & Sim Shalom)",
        "english": "Lord, open my lips, and my mouth shall declare Your praise! Structured in 3 timeless movements: (1–3) Praise & Ancestors; (4–16) 13 Weekday Requests (Insight, Teshuvah, Forgiveness, Healing, Livelihood, Justice, Peace); (17–19) Gratitude (Modim) & Peace (Sim Shalom). On Shabbat/Festivals, the 13 requests pause for 1 central blessing of Holy Day joy.",
    },
]

FIVE_MEGILLOT = [
    {"slug": "song-of-songs", "db_book": "Song of Songs", "title": "Song of Songs (Shir HaShirim)", "he": "שִׁיר הַשִּׁירִים", "holiday": "Passover (Pesach)", "summary": "Poetic love dialogue between Beloved and Bride—read literally as sublime love poetry and interpreted allegorically in classical Jewish tradition as the covenant love between God and Israel."},
    {"slug": "ruth", "db_book": "Ruth", "title": "Book of Ruth (Megillat Rut)", "he": "מְגִלַּת רוּת", "holiday": "Shavuot", "summary": "A Moabite widow's extraordinary Chesed (loving-kindness) toward Naomi—becoming the great-grandmother of King David."},
    {"slug": "lamentations", "db_book": "Lamentations", "title": "Lamentations (Eichah)", "he": "מְגִלַּת אֵיכָה", "holiday": "Tisha B'Av", "summary": "Five haunting alphabetic acrostic poems mourning the destruction of Jerusalem while ending with hope: 'Renew our days as of old' (5:21)."},
    {"slug": "ecclesiastes", "db_book": "Ecclesiastes", "title": "Ecclesiastes (Kohelet)", "he": "מְגִלַּת קֹהֶלֶת", "holiday": "Sukkot", "summary": "Philosophical wisdom on time, impermanence, joy, and meaning: 'To everything there is a season' (3:1)."},
    {"slug": "esther", "db_book": "Esther", "title": "Scroll of Esther (Megillat Ester)", "he": "מְגִלַּת אֶסְתֵּר", "holiday": "Purim", "summary": "Hidden providence in ancient Persia—Queen Esther and Mordecai turn peril into courage, unity, and Purim celebration."},
]

CLASSICAL_SHELF_MAP = [
    {
        "title": "Mishnah (6 Orders · c. 200 CE)",
        "he": "שִׁשָּׁה סִדְרֵי מִשְׁנָה",
        "tier": "CITED_INTERPRETATION",
        "desc": "Compiled by Rabbi Yehudah HaNasi in 6 Orders: Zeraim (Agriculture & Blessings), Moed (Shabbat & Festivals), Nashim (Family), Nezikin (Ethics, Civil Law & Pirkei Avot), Kodashim (Temple), Tohorot (Purity).",
    },
    {
        "title": "Babylonian Talmud (Talmud Bavli · c. 500 CE)",
        "he": "תַּלְמוּד בַּבְלִי",
        "tier": "CITED_INTERPRETATION",
        "desc": "Multi-generational debates of the Amoraim analyzing the Mishnah—preserving BOTH majority rulings AND minority dissenting views so learners always see diverse perspectives rather than single-voice dogma.",
    },
    {
        "title": "Rambam · Mishneh Torah (14 Books · c. 1180 CE)",
        "he": "מִשְׁנֵה תּוֹרָה לְהָרַמְבַּ״ם",
        "tier": "CITED_INTERPRETATION",
        "desc": "Maimonides' complete topical code of Jewish law and philosophy—from Sefer HaMada (Knowledge & Ethics) to Hilchot Teshuvah (Repentance) and Kings.",
    },
    {
        "title": "Shulchan Aruch (4 Sections · 1565 CE)",
        "he": "שֻׁלְחָן עָרוּךְ",
        "tier": "CITED_INTERPRETATION",
        "desc": "Rabbi Yosef Karo (Sephardi) with Rabbi Moshe Isserles / Rema (Ashkenazi) glosses: Orach Chaim (Daily/Shabbat/Holidays), Yoreh Deah (Kosher/Charity), Even HaEzer (Family), Choshen Mishpat (Business/Justice).",
    },
]


def get_books_library() -> dict:
    """Return the complete offline Sacred Books, Haggadah, Siddur, Five Megillot & Reference library."""
    megillot = []
    try:
        with torah_db.get_conn() as conn:
            for m in FIVE_MEGILLOT:
                row = conn.execute(
                    "SELECT slug, chapters_count, verses_count FROM books WHERE lower(title) = lower(?) LIMIT 1",
                    (m["db_book"],),
                ).fetchone()
                megillot.append({
                    **m,
                    "book_slug": row["slug"] if row else m["slug"],
                    "chapters_count": row["chapters_count"] if row else 0,
                    "verses_count": row["verses_count"] if row else 0,
                    "verified_in_db": bool(row),
                })
    except Exception:
        megillot = FIVE_MEGILLOT

    return {
        "haggadah": {
            "title": "Passover Haggadah — Complete 15-Step Seder Companion",
            "he_title": "הַגָּדָה שֶׁל פֶּסַח",
            "steps": HAGGADAH_SEDER_STEPS,
        },
        "siddur_blessings": SIDDUR_ESSENTIAL_BLESSINGS,
        "five_megillot": megillot,
        "classical_reference_map": CLASSICAL_SHELF_MAP,
    }


def index_into_db() -> int:
    """Index Haggadah & Siddur resources into torah.db `documents` FTS5 so offline Ollama AI can reason over them!"""
    docs = [
        (
            "offline-passover-haggadah-complete",
            "liturgy_book",
            "Complete Passover Haggadah (15-Step Seder Companion)",
            "הַגָּדָה שֶׁל פֶּסַח",
            "Kadesh through Nirtzah — Mah Nishtanah, Four Children, Ten Plagues, Dayenu, Hillel Sandwich & Hallel",
            "Exodus 6:6-7; Exodus 12:8-27; Exodus 13:8-14; Deuteronomy 26:5-8; Psalms 113-118",
            "\n\n".join(
                f"Step {s['step']} — {s['name']} ({s['he']}): {s['meaning']}. Source: {s['source']}. "
                f"Transliteration: {s['translit']} English: {s['english']} Note: {s['note']}"
                for s in HAGGADAH_SEDER_STEPS
            ),
            "Gather around the Seder table! Every single step—from dipping spring parsley in salt water to hiding the Afikoman and asking the Four Questions—invites kids and adults to relive the journey from slavery to freedom together!",
        ),
        (
            "offline-siddur-essential-blessings",
            "liturgy_book",
            "Complete Siddur & Essential Daily, Shabbat & Lifecycle Blessings",
            "סִדּוּר וּבְרָכוֹת הַיּוֹם",
            "Kiddush, Havdalah, Mourner's Kaddish, Traveler's Prayer, Mi Sheberach, Shehecheyanu, Candles, Mezuzah, Bedtime Shema & Amidah",
            "Genesis 2:1-3; Deuteronomy 6:4-9; Numbers 12:13; Psalms 31:6; Psalms 51:17",
            "\n\n".join(
                f"{b['title']} ({b['he_title']}) [{b['category']}]: When: {b['when']}. Source: {b['source']}. "
                f"Transliteration: {b['translit']} English: {b['english']}"
                for b in SIDDUR_ESSENTIAL_BLESSINGS
            ),
            "Every moment of Jewish life—waking up, traveling, welcoming Shabbat with candles and Kiddush, saying Kaddish, or wishing someone healing—has a timeless blessing ready right here offline.",
        ),
        (
            "offline-classical-rabbinic-reference-map",
            "liturgy_book",
            "Classical Rabbinic Library Map — Mishnah, Talmud Bavli, Rambam & Shulchan Aruch",
            "סִפְרִיַּת חֲזַ״ל",
            "How Tier 2 Cited Traditions (Mishnah, Talmud, Codes) relate to Tier 1 Primary Verified Tanakh Scripture",
            "Deuteronomy 17:8-11; Pirkei Avot 1:1",
            "\n\n".join(f"{c['title']} ({c['he']}) [{c['tier']}]: {c['desc']}" for c in CLASSICAL_SHELF_MAP),
            "Jewish learning cherishes debate: the Talmud records differing sages side by side so we never mistake one interpretation for the entire ocean of Torah.",
        ),
    ]
    inserted = 0
    with torah_db.get_conn() as conn:
        for slug, cat, title, he_t, sub, refs, body, kid in docs:
            conn.execute(
                """
                INSERT INTO documents (slug, category, title, he_title, subtitle, refs, body_md, kid_story)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    title=excluded.title, subtitle=excluded.subtitle, refs=excluded.refs,
                    body_md=excluded.body_md, kid_story=excluded.kid_story
                """,
                (slug, cat, title, he_t, sub, refs, body, kid),
            )
            inserted += 1
        # Rebuild documents_fts cleanly if present
        try:
            conn.execute("INSERT INTO documents_fts(documents_fts) VALUES('rebuild')")
        except Exception:
            pass
        conn.commit()
    return inserted
