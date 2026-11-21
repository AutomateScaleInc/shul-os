#!/usr/bin/env python3
"""
Seeds the curated Torah Sanctuary Markdown knowledge library:
- knowledge/stories/*.md   (Engaging Torah & Tanakh stories for kids, families & scholars)
- knowledge/history/*.md   (Historical, archaeological & broader Old Testament context)
- knowledge/guides/*.md    (PaRDeS interpretation framework & Classical Commentators guide)
"""

import pathlib

BASE = pathlib.Path(__file__).resolve().parent / "knowledge"

STORIES = [
    (
        "01-creation-and-shabbat",
        "Creation & the Gift of Shabbat",
        "בריאת העולם והשבת",
        "Light, human dignity in the Divine image, and the sanctuary in time",
        "Genesis 1:1-2:3",
        """Before there were oceans, mountains, or stars, the world was dark and still. Then God spoke, and with gentle, purposeful words, light spilled across the darkness! Over six days, God painted the sky blue, gathered the sparkling seas, sprouted fruit trees and wildflowers, hung the sun, moon, and stars like lanterns, filled the oceans with whales and the skies with birds, and brought every land animal to life.

Finally, on the sixth day, God created human beings — Adam and Eve — and breathed life into them, making every single person unique and precious, created in the image of God (*B'tzelem Elohim*). And then, on the seventh day, God did something wondrous: God rested. By resting, God created **Shabbat** — a weekly island of peace, gratitude, family, and joy where we stop making things and celebrate the wonder of being alive.""",
        """- **Peshat (Plain Meaning):** Creation unfolds in an orderly, intentional rhythm moving from chaos (*tohu va'vohu*) to harmony and goodness (*ki tov* — "it was good"), culminating in *tov me'od* ("very good") with humanity and holiness in time (*Shabbat*).
- **Remez (Allusion):** The Torah begins with the letter *Bet* (בְּרֵאשִׁית), which is closed on three sides and open forward — teaching that we look forward in purpose and service rather than speculating wildly beyond human reach.
- **Derash (Homiletical):** Why did God create only a single first human? The Mishnah (*Sanhedrin* 4:5) teaches: for the sake of peace among humanity, so no one can say "my ancestor is greater than yours," and so every person knows: *whoever saves a single life, it is as if they saved an entire world*.
- **Sod (Mystical):** Rabbi Abraham Joshua Heschel famously echoed the Zohar's insight: Judaism builds a **cathedral in time**. The first thing declared *kadosh* (holy) in the Torah is not a mountain or a building, but a day — Shabbat.""",
        """- **Rashi (Genesis 1:1):** Quoting Rabbi Isaac, asks why the Torah begins with Creation rather than the first mitzvah (*Exodus 12:2*). Answer: to declare that the entire earth belongs to God, who grants lands according to moral purpose. Rashi also explains *Bereshit bara* grammatically as "In the beginning of God's creating..."
- **Ramban (Nachmanides):** Emphasizes *creatio ex nihilo* (*yesh me'ayin* — something from nothing) in the Hebrew verb *bara*, establishing God's absolute sovereignty over nature.
- **Sforno:** Highlights that *B'tzelem Elohim* (Image of God) signifies human intellect, moral freedom, and the capacity to choose goodness.""",
        """1. Why do you think God declared *time* (Shabbat) holy before declaring any *place* holy?
2. What does it change in how we treat strangers if every person carries *B'tzelem Elohim* (the Divine image)?
3. What is one thing your family loves doing on Shabbat that slows the whole week down?"""
    ),
    (
        "02-noah-and-the-rainbow",
        "Noah, the Ark & the Rainbow Covenant",
        "נח והמבול וברית הקשת",
        "Integrity in a difficult generation, caring for creation, and the universal covenant",
        "Genesis 6:9-9:17",
        """Long after Adam and Eve, the world grew loud with selfishness and violence (*chamas*), where people stopped caring for one another. Yet one man named **Noah** walked quietly with God and tried to do what was right. God told Noah that a great flood would wash the earth clean, and asked him to build a huge wooden **Ark** (*Tevah*).

For years, Noah sawed and hammered while neighbors wondered what he was doing. Then, two by two — and seven pairs of clean animals — lions, doves, elephants, and butterflies marched safely inside with Noah's family. Rain fell for forty days and forty nights until only the Ark floated upon the water. When the waters subsided, Noah sent out a raven and then a dove. On her second flight, the dove returned holding a fresh **olive leaf** in her beak — a sign of peace and new life! When everyone stepped onto dry ground, God painted the first **rainbow** across the clouds as an everlasting promise never again to destroy the earth by flood.""",
        """- **Peshat:** The flood narrative addresses moral corruption (*chamas* — robbery, violence, breakdown of social trust) and establishes the **Seven Noahide Laws**, a universal ethical foundation for all humanity: justice, refraining from idolatry, blasphemy, murder, sexual immorality, theft, and cruelty to living animals.
- **Derash:** The Midrash notes that Noah spent twelve months feeding every creature in the Ark day and night without sleep — teaching that kindness (*chesed*) to animals and dependents is the price of surviving to rebuild the world.
- **Sod / Symbolism:** The Hebrew word for Ark (*Tevah*) also means **"word"** — hinting that honest, compassionate speech is an ark that carries us through life's storms.""",
        """- **Rashi (Genesis 6:9):** On "Noah was righteous *in his generations*," cites two Talmudic views (*Sanhedrin* 108a): some praise him (if he was righteous in a corrupt era, how much more so in Abraham's time!), while others note he focused on saving his family rather than pleading for his neighbors like Abraham later did.
- **Ramban:** Explains that *chamas* (everyday injustice and theft) sealed the generation's fate because even without revelation, basic fairness is written into human conscience.
- **Sforno:** Points out that God had Noah spend 120 years building the Ark slowly so people would ask questions and have a chance to repent (*teshuvah*).""",
        """1. Why did the dove choose a bitter olive leaf from God's hand over sweet food inside the Ark (as the Talmud asks)?
2. What is the difference between being privately good and actively helping a whole community improve?
3. Whenever we see a rainbow, Jewish tradition recites a blessing remembering God's covenant — what promise should *we* keep toward the earth?"""
    ),
    (
        "03-abraham-lech-lecha",
        "Abraham & Sarah: The Journey of Lech Lecha & Hospitality",
        "אברהם ושרה: לך-לך והכנסת אורחים",
        "Courage to walk a new path, welcoming strangers, and arguing for justice",
        "Genesis 12:1-18:33",
        """God called out to **Abram** and **Sarai**: *"Lech Lecha — Go forth from your land, your birthplace, and your father's house, to a land I will show you, and be a blessing!"* Imagine packing up your home without even having a map — trusting that kindness, honesty, and faith in the One God would light the way!

When Abraham and Sarah pitched their tent in Canaan, tradition says it was open on all four sides so travelers from north, south, east, or west could always smell warm bread and find cool water. One scorching afternoon, even while Abraham was recovering and speaking with God, he spotted three dusty travelers in the distance. He asked God to wait a moment, ran to greet them, washed their feet, and together with Sarah prepared a royal feast! Later, when Abraham learned that the wicked city of Sodom faced destruction, he stood bravely before God and pleaded: *"Shall the Judge of all the earth not do justice?"* — teaching the world that loving God also means caring deeply about fairness and compassion.""",
        """- **Peshat:** *Lech Lecha* launches the covenantal journey of the Jewish people — not for privilege, but for responsibility: *"through you all the families of the earth shall be blessed"* (Genesis 12:3).
- **Derash:** The Talmud (*Shabbat* 127a) derives from Abraham pausing his vision of God to welcome three strangers: **"Hospitality to guests (*Hachnasat Orchim*) is greater than welcoming the Divine Presence!"**
- **Moral Theology:** Abraham's negotiation over Sodom (50, 45, 40, 30, 20, 10 righteous people) models courageous moral advocacy — never rejoicing in the downfall of others.""",
        """- **Rashi (Genesis 12:1, 12:5):** Translates *Lech Lecha* as "Go *for your own benefit and growth*," and explains "the souls they had made in Haran" as the people Abraham and Sarah welcomed and inspired with ethical monotheism.
- **Ramban (Genesis 12:6):** Formulates the famous principle *Ma'aseh Avot Siman LaBanim* — "The deeds of the patriarchs and matriarchs are a signpost for their descendants."
- **Ibn Ezra:** Highlights the spiritual bravery required to leave idolatry and comfort behind for an unseen calling.""",
        """1. Why did Abraham's tent have openings on all four sides? How can a synagogue or home feel like that today?
2. What does it mean to "go to yourself" (*Lech Lecha*) — discovering who you truly are by stepping outside your comfort zone?
3. Why did God *welcome* Abraham's bold question about justice in Sodom?"""
    ),
    (
        "04-akeidat-yitzchak",
        "The Binding of Isaac (Akeidat Yitzchak)",
        "עקדת יצחק",
        "Devotion, the rejection of child sacrifice, and the call of the Shofar",
        "Genesis 22:1-19",
        """One of the most awe-inspiring and challenging stories in the entire Torah takes place on **Mount Moriah**. God called to Abraham, *"Abraham!"* and he answered *"Hineni — Here I am!"* God tested Abraham's faith by asking him to ascend the mountain with his beloved son **Isaac** (*Yitzchak*).

Father and son walked together in quiet trust (*"and the two of them walked together"*). At the decisive moment on the mountaintop, an angel called urgently from heaven: *"Do not lay your hand upon the lad, nor do anything to him!"* Looking up, Abraham saw a **ram** caught by its horns in a thicket. God showed Abraham — and the entire ancient world, where surrounding nations tragically practiced child sacrifice — that the God of Israel **never** desires human sacrifice, but rather a devoted, compassionate heart. Every **Rosh Hashanah**, we blow the **Shofar** (ram's horn) to remember Abraham and Isaac's devotion and God's boundless mercy.""",
        """- **Peshat & Historical Significance:** In the Ancient Near East, child sacrifice was widely practiced by neighboring cults (later fiercely outlawed in Leviticus 18:21, Deuteronomy 12:31, Jeremiah 7:31). The Akeidah turns that expectation upside down: God explicitly forbids harming Isaac and establishes reverence for human life.
- **Derash:** Notice the phrase *"Hineni"* ("Here I am") appears three times in the chapter — to God, to his son Isaac, and to the angel who stops the knife — modeling total presence and willingness to listen even when the command shifts.
- **Liturgical Memory:** Mount Moriah becomes the future site of the Temple in Jerusalem (*II Chronicles* 3:1), and the ram's horn becomes the voice of Rosh Hashanah calling us to wake up to *teshuvah* (return).""",
        """- **Rashi (Genesis 22:2, 22:12):** Notes the tender buildup ("your son, your only one, whom you love, Isaac") and explains God's words "Lift him up" (*ha'alehu*) never meant "slaughter him," only "bring him up to the mountain and bring him back down."
- **Ramban:** Explains that a Divine *nisayon* (test) is never so God can learn something new, but to turn a person's potential virtue into lived reality for all generations.
- **Midrash (Bereishit Rabbah 56):** Emphasizes that Isaac was a grown adult (37 according to tradition) who walked willingly alongside his father in shared spiritual resolve.""",
        """1. Why is it so important that the angel stops Abraham and declares "Do not harm the boy"?
2. What does saying *"Hineni"* ("Here I am") look like in everyday family and community life?
3. How does hearing the Shofar on Rosh Hashanah connect us back to Mount Moriah?"""
    ),
    (
        "05-jacobs-ladder-and-israel",
        "Jacob's Ladder & Becoming Israel",
        "חלום יעקב והמאבק עם המלאך",
        "Finding holiness anywhere, resilience through struggle, and healing family rifts",
        "Genesis 28:10-33:11",
        """Running away from home after a painful quarrel with his twin brother Esau, **Jacob** lay down under the open desert stars with a stone for a pillow. That night he dreamed of a magnificent **ladder** (*sulam*) standing on the earth with its top reaching the heavens, and angels ascending and descending! When Jacob woke, he whispered in wonder: *"Surely God is in this place, and I did not know it!"*

Twenty years later, returning home with a big family to make peace with Esau, Jacob stayed alone across the river at night and wrestled until dawn with a mysterious figure. Jacob refused to let go until he received a blessing — and was given a brand-new name: **Yisrael (Israel)**, meaning *"one who wrestles with God and people, and prevails."* The next morning, limping yet courageous, Jacob bowed to Esau — and Esau ran to hug him and wept. Two estranged brothers made peace.""",
        """- **Peshat:** Jacob's arc transforms him from *Ya'akov* ("heel-grasper," surviving through cleverness) into *Yisrael* (facing fear honestly, bearing the mark of struggle, and seeking reconciliation).
- **Remez / Gematria:** Classic commentators note that the Hebrew word *sulam* (ladder, סלם = 130) has the exact same numerical value as **Sinai** (סיני = 130) — connecting personal spiritual awakening to the communal revelation at Sinai.
- **Derash:** The Midrash observes that the angels first *ascended* and then *descended* — because holiness rises from our everyday actions on earth before blessing flows back down.""",
        """- **Rashi (Genesis 28:12, 32:25):** Explains the ascending angels as those who escorted Jacob in the Land of Israel handing off to angels of the diaspora; identifies the nighttime wrestler as the spiritual guardian of Esau — representing Jacob's inner fear and historical struggle.
- **Ramban:** Highlights Jacob's three-part preparation before meeting Esau: gifts (diplomacy), prayer (faith), and readiness (prudence) — a timeless blueprint for navigating danger.
- **Sforno:** Reads "Surely God is in this place and I did not know it" as the realization that God's Presence is never confined to one familiar home.""",
        """1. Have you ever had a moment where you realized "God is in this place, and I didn't notice it before"?
2. Why are the Jewish people named *Israel* ("God-wrestler") — what does it say about asking tough questions and persisting through struggle?
3. What helped Jacob and Esau finally embrace after twenty years apart?"""
    ),
    (
        "06-joseph-and-his-brothers",
        "Joseph, the Coat of Many Colors & Forgiveness",
        "יוסף ואחיו",
        "Resilience in hardship, moral integrity, and turning pain into healing",
        "Genesis 37:1-45:28",
        """**Joseph** (*Yosef*) was Jacob's young dreamer who received a beautiful multicolored coat (*ketonet passim*). Jealousy grew in the family, and tragically his older brothers threw him into a pit and sold him to a caravan heading to Egypt. Yet even as a servant — and later unfairly thrown into an Egyptian dungeon — Joseph never gave up his honesty, kindness, or trust in God.

When Pharaoh had troubling dreams of seven fat cows eaten by seven skinny cows, Joseph interpreted them as seven years of plenty followed by seven years of famine. Pharaoh made Joseph viceroy over all Egypt, and Joseph stored grain to save millions of people from starving. Years later, his very own brothers came bowing before him begging for food, not recognizing him! After testing whether they had truly changed — and watching Judah bravely offer himself to protect their youngest brother Benjamin — Joseph burst into tears and said: *"I am Joseph! Do not be angry with yourselves... God sent me ahead of you to save lives."*""",
        """- **Peshat:** The Joseph saga is the longest continuous literary narrative in Genesis, illustrating *Hashgachah Pratit* (quiet Divine providence working through human choices — without a single overt miracle!).
- **Derash:** Why did Joseph test his brothers with Benjamin? Rambam (*Laws of Teshuvah* 2:1) defines complete repentance as facing the exact same temptation again and choosing differently. Judah — who once suggested selling Joseph — now offers himself as a slave to save Benjamin, proving genuine transformation.
- **Ethical Lesson:** The Talmud (*Shabbat* 10b) warns parents never to play favorites among children, noting how two extra *selas* of fine wool for Joseph's coat set off generations of heartache.""",
        """- **Rashi (Genesis 37:3, 45:14):** Notes the Midrashic tenderness when Joseph and Benjamin wept on each other's necks — mourning the future Temples, while reassuring his brothers with gentle, shame-free forgiveness.
- **Ramban:** Explains why Joseph kept his brothers waiting before revealing himself: to fulfill his dreams and give them the opportunity to heal their guilt through defending Benjamin.
- **Sforno:** Celebrates Joseph's refusal to seek revenge when holding total power as one of the Torah's highest peaks of moral character.""",
        """1. Why did Joseph forgive his brothers instead of using his power to get even?
2. How did Judah show he had truly changed between Genesis 37 and Genesis 44?
3. When something hard happens to us, how can we look for a way to turn it into helping others?"""
    ),
    (
        "07-moses-and-the-burning-bush",
        "Moses, the Basket & the Burning Bush",
        "משה בתיבה והסנה הבוער",
        "Courageous women who saved a generation, noticing quiet wonders, and humble leadership",
        "Exodus 2:1-4:17",
        """Generations after Joseph, a cruel new Pharaoh enslaved the Israelites and issued a terrible decree against newborn baby boys. Brave Hebrew midwives **Shiphrah and Puah** refused to obey an unjust order. And a loving mother named **Yocheved** wove a waterproof basket of reeds, placed baby **Moses** (*Moshe*) gently among the Nile river grasses while his big sister **Miriam** watched closely. Pharaoh's own daughter discovered the crying baby, felt deep compassion, adopted him, and Miriam cleverly arranged for Moses' own mother to nurse him!

When Moses grew up, he couldn't ignore the suffering of his people and fled to Midian, becoming a gentle shepherd. One day, noticing a lost little lamb, Moses saw an astonishing sight on Mount Horeb: a small **thornbush blazing with fire, yet never burning up!** When Moses turned aside to look closely, God called his name and asked him to free the enslaved Israelites. Moses felt shy and stammered, *"Who am I?"* — yet God promised: *"Ehyeh Asher Ehyeh — I will be with you."*""",
        """- **Peshat:** Notice that **five courageous women** — Shiphrah, Puah, Yocheved, Miriam, and Batyah (Pharaoh's daughter) — launch the entire Redemption from Egypt before Moses speaks a single word!
- **Derash:** Why did God appear in a lowly thornbush (*sneh*) instead of a mighty cedar? Midrash (*Shemot Rabbah* 2:5) teaches: *"I am with them in their distress"* (Psalm 91:15) — God shares the pain of the humble and oppressed, and no place is devoid of the Divine Presence.
- **Leadership Lesson:** The Midrash explains God chose Moses as leader of Israel only after watching how tenderly he carried a thirsty little sheep on his shoulders as a shepherd.""",
        """- **Rashi (Exodus 3:2, 3:14):** Explains *Ehyeh Asher Ehyeh* ("I Will Be What I Will Be") as God's promise: *"I will be with them in this sorrow, and I will be with them in every future trial."*
- **Ramban:** Highlights Moses' humility (*"Who am I?"*) not as disobedience, but as genuine awe at the responsibility of representing an entire people.
- **Ibn Ezra:** Explores the philosophical depth of God's Eternal Name (*YHVH*) as the source of all being — past, present, and future simultaneously.""",
        """1. Why did God wait until Moses "turned aside to look" before speaking from the Burning Bush?
2. Who are the unsung heroes in the start of Exodus who risked everything to do what was right?
3. Why does the Torah make its greatest leader someone who felt nervous about speaking in public?"""
    ),
    (
        "08-exodus-passover-and-sea",
        "The Exodus, Passover & Crossing the Sea",
        "יציאת מצרים וקריעת ים סוף",
        "Freedom with purpose, empathy for the stranger, and stepping forward in faith",
        "Exodus 7:1-15:21",
        """Moses and his brother Aaron returned to Egypt with a bold message: *"Let My people go!"* Pharaoh hardened his heart again and again through **ten plagues** — blood, frogs, lice, wild beasts, pestilence, boils, hail, locusts, darkness, and finally the plague of the firstborn. On the night of the first **Passover (Pesach)**, Israelite families ate roasted lamb, bitter herbs (*maror*), and flat unleavened bread (**matzah**) in haste — and walked out of slavery toward freedom!

Soon Pharaoh changed his mind and chased them with chariots until the Israelites stood trapped between the roaring sea ahead and the Egyptian army behind. Tradition tells of **Nachshon ben Aminadav**, who stepped bravely into the waves up to his neck in faith — and Moses raised his staff! A mighty east wind blew all night, splitting the Sea of Reeds so the people crossed on dry ground. On the far shore, Moses, **Miriam** with her timbrel, and all the people burst into the joyous **Song of the Sea (*Shirat HaYam*)**!""",
        """- **Peshat & Ethics:** The Exodus is the cornerstone of Jewish memory — recalled daily in prayer, every Shabbat Kiddush, and every Passover Seder. Its supreme ethical takeaway is repeated **36 times** in the Torah: *"You shall not oppress a stranger, for you know the soul of a stranger, having been strangers in the land of Egypt."*
- **Derash (Compassion even for enemies):** The Talmud (*Megillah* 10b, *Sanhedrin* 39b) relates that when the angels began singing as the Egyptians drowned in the sea, God stopped them: *"My handiwork is drowning in the sea, and you want to sing songs?!"* That is why we spill drops of wine at the Seder for each plague — our joy is never complete when others suffer.
- **Historical / Literary:** Freedom in the Torah is never just freedom *from* bondage, but freedom *for* moral responsibility and service at Sinai.""",
        """- **Rashi (Exodus 12:39, 15:1):** Highlights Israel's trust in leaving Egypt with only unrisen dough (*matzah*) and notes the Hebrew future tense of *Az Yashir* ("Then Moses *will* sing") as a hint of eternal hope.
- **Ramban (Exodus 13:16):** Writes one of his most famous teachings: witnessing great open miracles teaches us to recognize the **hidden miracles** (*nissim nistarim*) sustaining every breath of ordinary life.
- **Sforno:** Explains that Pharaoh's "hardened heart" in the final plagues actually gave him the strength to choose freely rather than caving purely out of panic without true remorse.""",
        """1. Why do we spill a drop of wine for each of the Ten Plagues at the Passover Seder?
2. What does Nachshon stepping into the water before it split teach us about faith and action?
3. How should remembering slavery in Egypt shape how we welcome newcomers today?"""
    ),
    (
        "09-mount-sinai-ten-commandments",
        "Mount Sinai & the Ten Commandments",
        "מעמד הר סיני ועשרת הדברות",
        "Unity at the mountain, ethical monotheism, and love of God paired with love of neighbor",
        "Exodus 19:1-20:23",
        """Seven weeks after leaving Egypt — the very season we celebrate on **Shavuot** — the entire Israelite people arrived at **Mount Sinai**. The Torah says they camped there *"like one person with one heart."* Thunder rolled, lightning flashed, the Shofar sounded louder and louder, and the mountain was wrapped in cloud as God spoke the **Ten Commandments (*Aseret HaDibrot*)** directly to the entire nation!

Look closely at the **Two Tablets**: the first five commandments focus on our relationship with **God and family** (knowing God who freed us from slavery, no idols, honoring God's Name, keeping Shabbat, and honoring father and mother). The second five focus on our relationship with **other people** (do not murder, do not betray marriage, do not steal, do not bear false witness, and do not covet what belongs to others). Standing side by side on two equal tablets, they teach that you cannot truly love God without treating people with honesty, dignity, and care!""",
        """- **Peshat:** In Jewish tradition, the *Aseret HaDibrot* ("Ten Utterances") are the ethical pillars of the 613 mitzvot. Notice Commandment #1 is *"I am the Lord your God who brought you out of the house of bondage"* — anchoring faith in lived liberation and gratitude.
- **Derash:** Why was the Torah given in the open, ownerless **wilderness** on a modest mountain (Sinai) rather than a proud peak? Midrash (*Mekhilta*) teaches: because the Torah belongs to anyone who opens their heart to it in humility, regardless of wealth or status.
- **Two Tablets Symmetry:** Classical teachers pair Tablet 1 and Tablet 2 across rows: #1 (*I am God*) pairs with #6 (*Do not murder* — because every person is in God's image); #4 (*Shabbat*) pairs with #9 (*No false witness* — both testify truthfully to Creation!).""",
        """- **Rashi (Exodus 19:2, 20:1):** Celebrates *"and Israel camped there"* in the grammatical singular — *"like one person with one heart"* — as the prerequisite for receiving Torah; explains *Remember* (Exodus) and *Guard* (Deuteronomy) Shabbat were spoken in one utterance.
- **Ibn Ezra:** Explores why honoring parents sits on the first tablet (alongside duties to God): parents are God's partners in giving us life and teaching us gratitude.
- **Ramban:** Distinguishes *Zakhor* (positive celebration of Shabbat) and *Shamor* (guarding Shabbat rest) as love and awe working in harmony.""",
        """1. Why did the Torah have to be given in the open desert instead of inside a palace?
2. Notice how the Ten Commandments split evenly between duties to God and duties to people — why do both halves need each other?
3. What does *"Na'aseh v'Nishma"* ("We will do and we will listen/understand") teach about learning through action?"""
    ),
    (
        "10-golden-calf-and-mercy",
        "The Golden Calf & the Thirteen Attributes of Mercy",
        "חטא העגל ושלוש עשרה מידות הרחמים",
        "Human mistakes, Moses' selfless leadership, and the power of second chances (Yom Kippur)",
        "Exodus 32:1-34:35",
        """While Moses spent forty days high on Mount Sinai receiving the stone Tablets, the people below grew frightened when they miscounted the days and thought he wasn't coming back. In their panic, they made a **Golden Calf** (*Egel HaZahav*) to feel a visible symbol of security. Coming down the mountain, Moses saw what had happened and shattered the first Tablets in heartbreak.

Yet Moses did not walk away from his people. When God offered to start a whole new nation from Moses alone, Moses refused: *"Please forgive their sin — and if not, erase me from Your book!"* Moses climbed Mount Sinai again, prayed for forty days, and carved **Second Tablets**. On the tenth of Tishrei — the very first **Yom Kippur** — God forgave Israel and revealed the **Thirteen Attributes of Mercy (*Yud-Gimel Midot HaRachamim*)**: *"Compassionate and gracious, slow to anger, abounding in kindness and truth..."* The broken pieces of the first Tablets were placed right beside the whole Second Tablets inside the Ark, teaching that even our brokenness can be healed and made holy.""",
        """- **Peshat:** This episode establishes the core Jewish theology of **Teshuvah (Repentance & Return)**: even the most devastating failure right after Sinai is not the end of the covenant.
- **Derash:** The Talmud (*Berakhot* 8b) learns from storing both the *broken* first tablets and the *whole* second tablets in the Ark: we honor both elders whose memory fades and every person carrying scars of past mistakes — brokenness does not forfeit holiness.
- **Liturgical Heart:** The Thirteen Attributes of Mercy (Exodus 34:6–7) form the spiritual centerpiece of Selichot and Yom Kippur prayers across every synagogue in the world.""",
        """- **Rashi (Exodus 32:1, 34:6):** Explains the people's panic as a six-hour miscalculation of the 40 days; cites the Talmud (*Rosh Hashanah* 17b) that God wrapped Himself like a prayer leader to teach Moses how to invoke the Thirteen Attributes of Mercy whenever Israel needs forgiveness.
- **Ramban:** Clarifies that the people did not reject God outright, but erred deeply in trying to manufacture a physical intermediary to replace Moses.
- **Sforno:** Notes that the *Second Tablets* were carved by Moses' human hands while inscribed by God — symbolizing partnership between human effort and Divine grace.""",
        """1. Why were the *broken pieces* of the first Tablets kept inside the Holy Ark right next to the new whole Tablets?
2. What makes Moses' refusal to abandon the people ("erase me from Your book") the ultimate example of loving leadership?
3. How do the Thirteen Attributes of Mercy (slow to anger, compassionate, patient) give us a blueprint for how we should treat others?"""
    ),
    (
        "11-twelve-spies-and-courage",
        "The Twelve Spies & Seeing with Courage",
        "חטא המרגלים וכלב ויהושע",
        "Perspective, resisting fear-mongering, and trusting our own dignity",
        "Numbers 13:1-14:45",
        """Standing right at the doorstep of the Promised Land, Moses sent **twelve scouts** — one leader from each tribe — to explore the land for forty days. They returned carrying an enormous cluster of grapes on a pole between two men, plus pomegranates and figs! *"It truly flows with milk and honey!"* they reported.

Then ten of the scouts let fear take over: *"The cities are huge and the people look like giants! We seemed like grasshoppers in our own eyes — and so we must have looked to them!"* Only **Joshua** and **Caleb** stood tall and spoke with quiet courage: *"Do not be afraid! We can surely go up and succeed, for God is with us."* Because fear spread through the camp like wildfire, the generation wandered forty years in the wilderness so a new generation born in freedom — without the mindset of slavery — could enter the Land.""",
        """- **Peshat:** The tragedy of the scouts (*Parashat Sh'lach*) occurs on the **9th of Av (*Tisha B'Av*)** in Jewish tradition — turning a night of needless weeping into a historical day of mourning and reflection.
- **Psychological Insight:** Look at the spies' devastating confession: *"We were like grasshoppers in **our own eyes**, and so we were in their eyes"* (Numbers 13:33). How we see ourselves shapes how the world sees us.
- **Derash:** Notice the ten spies spoke *factual observations* (tall walls, strong cities) — yet twisted facts with despair (*lashon hara* against the Land). True leadership sees challenges honestly *and* still sees the path forward.""",
        """- **Rashi (Numbers 13:2, 13:33):** Points out *"Send for yourself"* (*Sh'lach Lecha*) — God permitted Moses to send scouts if the people wanted, though faith alone was enough; quotes the Midrash that the spies even projected their own insecurity onto the inhabitants.
- **Ramban:** Explains that the scouts' real sin was crossing from reporting facts (their assignment) to telling the nation *"We cannot go up"* (undermining trust in God's promise).
- **Kli Yakar & Sforno:** Contrast the ten spies' focus on obstacles with Caleb's calm focus on possibility and purpose.""",
        """1. Why did the spies say "we looked like grasshoppers in *our own eyes*" before saying how the giants saw them?
2. How is Caleb and Joshua's courage different from pretending challenges don't exist?
3. When everyone around us is panicking or negative, how can we be a steady, hopeful voice?"""
    ),
    (
        "12-shema-and-moses-farewell",
        "The Shema & Moses' Final Blessing: Choose Life!",
        "שמע ישראל ובחרת בחיים",
        "Oneness, passing Torah to our children, and moral freedom",
        "Deuteronomy 6:4-9; 30:11-20; 34:1-12",
        """At the end of forty years in the wilderness, **Moses** stood on the plains of Moab overlooking the Jordan River and gave his heartfelt farewell speeches — the entire Book of **Deuteronomy (*Devarim*)**. In the very heart of his message, he taught the six words that Jewish people have whispered morning and night for over three thousand years:

**"Shema Yisrael, Adonai Eloheinu, Adonai Echad — Hear, O Israel: the Lord is our God, the Lord is One!"**

Moses urged parents to teach these words warmly to their children *"when you sit at home, when you walk along the way, when you lie down, and when you rise up,"* and to place a **Mezuzah** on every doorpost as a reminder of love and integrity. Before climbing Mount Nebo to gaze across the Promised Land, Moses gave one final, luminous charge: *"This Torah is not up in heaven or across the sea — it is very close to you, in your mouth and in your heart to do it. Therefore, **choose life!**"*""",
        """- **Peshat:** *Devarim* transforms the Torah from commands spoken *to* the people into a living covenant carried *within* the heart and home — accessible to every generation, everywhere.
- **Derash (Talmud *Bava Metzia* 59b):** The phrase **"Lo baShamayim hi — It is not in heaven!"** (Deuteronomy 30:12) became the foundation of Rabbinic Jewish interpretation: once given at Sinai, Torah interpretation belongs to honest, reasoned human study and community responsibility.
- **Free Will:** *"I have set before you life and death, blessing and curse; therefore choose life"* (Deuteronomy 30:19) is the Torah's clearest declaration of human moral freedom — we are never trapped by fate.""",
        """- **Rashi (Deuteronomy 6:4-7):** Notes that *"your children"* (*vanecha*) also means *"your students"* — teaching is an act of spiritual parenthood; explains *"Echad"* (One) as the promise that one day all humanity will recognize unity and peace.
- **Ramban (Deuteronomy 30:11):** Emphasizes that *teshuvah* (returning to goodness) is always within reach — never too distant or too late.
- **Sforno:** Reads Moses' humble passing at Mount Nebo (with his burial place unknown) as safeguarding Israel from ever turning a human leader into an idol.""",
        """1. Why is the very first word of Judaism's central declaration **"Shema" — Listen**?
2. What does *"It is not in heaven"* mean for ordinary people studying Torah today?
3. What is one concrete way we "choose life" in our words and actions this week?"""
    ),
    (
        "13-ruth-and-chesed",
        "Ruth & Naomi: The Book of Loving-Kindness (Chesed)",
        "מגילת רות וחסד",
        "Loyalty, welcoming converts, caring for the poor, and the ancestor of King David",
        "Ruth 1:1-4:22",
        """Read every year on **Shavuot**, the Book of **Ruth** has no battles, no thunder, and no kings on thrones — just ordinary people doing extraordinary kindness! When **Naomi** lost her husband and sons in Moab and set out brokenhearted to return to Bethlehem, her Moabite daughter-in-law **Ruth** refused to leave her alone, speaking some of the most tender words in all of Scripture:

*"Where you go, I will go; where you lodge, I will lodge; your people shall be my people, and your God my God!"*

Back in Bethlehem during the barley harvest, Ruth worked humbly in the fields, gathering the fallen stalks that Torah law (*Leviticus* 19:9) leaves for the poor and the stranger. **Boaz**, the generous landowner, noticed Ruth's devotion to Naomi, protected her dignity, made sure extra sheaves were left quietly so she never felt embarrassed, and married her. Their great-grandson? **King David** — showing that the royal house of Israel was built on *chesed* (loving-kindness) and the welcoming of a sincere newcomer!""",
        """- **Peshat:** Ruth showcases the Torah's social-justice mitzvot in action (*Leket*, *Shikchah*, *Pe'ah* — dignified support for the vulnerable) alongside the beauty of chosen belonging (*gerut* / conversion).
- **Derash:** Midrash (*Ruth Rabbah* 2:14) asks why the Book of Ruth — which contains no laws of ritual purity or sacrifice — was included in the sacred Tanakh. Answer: **"To teach how great is the reward of those who perform acts of loving-kindness (*gemilut chasadim*)!"**
- **Shavuot Connection:** Reading Ruth on Shavuot (the birthday of Torah) pairs Mount Sinai's revelation with quiet everyday compassion — reminding us that *chesed* is the heartbeat of Torah.""",
        """- **Rashi (Ruth 1:16, 2:12):** Celebrates Ruth's dialogue with Naomi as the classical paradigm of sincere Jewish conversion — embracing both community and mitzvot out of love; notes Boaz's greeting *"May the Lord be with you"* to his harvest workers models treating every worker with dignity.
- **Ibn Ezra & Malbim:** Highlight Boaz's careful legal integrity at the city gate (*Ruth* 4) — honoring justice and family responsibility publicly and fairly.""",
        """1. Why do you think the Torah connects the festival of Mount Sinai (Shavuot) with a quiet story about kindness in a barley field?
2. How did Boaz help Ruth while protecting her pride and dignity?
3. What does King David descending from Ruth (a Moabite convert) teach a synagogue community about welcoming newcomers?"""
    ),
    (
        "14-david-and-goliath",
        "David & Goliath",
        "דוד וגלית",
        "Inner courage, being true to yourself, and trusting faith over appearances",
        "I Samuel 17:1-58",
        """The Philistine army camped across the valley with a towering champion named **Goliath**, clad in heavy bronze armor, mocking Israel for forty days while every trained soldier trembled. Into the camp walked **David**, the youngest of Jesse's eight sons — a shepherd boy sent simply to bring bread and cheese to his older brothers!

Hearing Goliath's insults, young David volunteered to face him. King Saul tried to dress David in heavy royal armor and a huge bronze helmet, but David could barely walk in it. *"I cannot wear these,"* David said honestly. Instead, he stepped down to the brook, picked up **five smooth stones**, carried his simple shepherd's sling, and walked toward the giant declaring: *"You come at me with sword and spear, but I come in the name of the Lord!"* One well-aimed stone ended the standoff — teaching every generation that God looks at the heart, not at height or armor.""",
        """- **Peshat:** Connected directly to the previous chapter (*I Samuel* 16:7): *"Humans see what is visible to the eyes, but God sees into the heart."* David succeeds precisely because he refuses to imitate Saul's armor and brings his authentic skills and faith.
- **Derash:** Midrash notes Goliath stood out for *40 days* morning and evening — intentionally interrupting the times of the morning and evening *Shema* — and that David chose five smooth stones representing the Five Books of the Torah (or the three Patriarchs, Moses, and Aaron).
- **Literary / Historical:** In Ancient Near Eastern warfare, champion single combat (*ish ha-beinayim*) was a known convention; slingers were actually highly skilled light-infantry specialists whose precision could outrange heavy infantry.""",
        """- **Rashi & Radak (I Samuel 17:40, 17:45):** Highlight David's refusal to trust brute force and his fearless defense of the dignity of Israel and God's Name (*Kiddush Hashem*).
- **Talmud (*Sotah* 42b):** Examines the contrast between arrogance (Goliath boasting in weapons) and humble courage (David relying on God and truth).""",
        """1. Why was it so important that David took OFF King Saul's armor before walking into the valley?
2. What "giants" (fears, challenges, peer pressure) do people face today where quiet courage matters more than looking big?
3. How do small everyday responsibilities (like tending sheep faithfully) prepare us for big moments?"""
    ),
    (
        "15-elijah-still-small-voice",
        "Elijah, Mount Carmel & the Still Small Voice",
        "אליהו הנביא וקול דממה דקה",
        "Standing for truth, recovering from burnout, and hearing God in quietness",
        "I Kings 18:19-19:18",
        """During a harsh drought under King Ahab and Queen Jezebel, the fearless prophet **Elijah (*Eliyahu*)** challenged 450 prophets of Baal on **Mount Carmel** to show the people that the God of Israel is real. Fire fell dramatically from heaven, rain finally poured down to end the famine, and the people cheered!

Yet right afterward, exhausted and threatened by Jezebel, Elijah ran all the way to the wilderness and sat under a broom tree feeling completely alone and burned out. Gently, an angel woke him — not with a lecture, but with warm baked bread and cool water! Rested, Elijah journeyed to **Mount Horeb (Sinai)**. First came a roaring wind that shattered rocks — *God was not in the wind*. Then a mighty earthquake — *God was not in the earthquake*. Then a blazing fire — *God was not in the fire*. And after the fire came a **Kol Demamah Dakah — a still, small, gentle voice**. That quiet whisper renewed Elijah's spirit and sent him back with hope and a successor, Elisha.""",
        """- **Peshat:** One of the most psychologically honest stories in all of Tanakh: even the mightiest prophet experiences exhaustion and despair — and healing begins with rest, food, gentle care, and stepping away from spectacle to listen in stillness.
- **Derash:** Jewish tradition treasures Elijah as the eternal messenger of hope and peace — welcomed at every Passover Seder (*Kos shel Eliyahu*), every Brit Milah (*Chair of Elijah*), and sung about every Saturday night at Havdalah (*Eliyahu HaNavi*).
- **Spiritual Contrast:** Mount Carmel was spectacle and fireworks; Mount Horeb teaches that lasting transformation lives in the *still, small voice* of conscience, prayer, and patient mentorship (mentoring Elisha).""",
        """- **Radak & Ralbag (I Kings 19:12):** Explain that wind, earthquake, and fire represent dramatic external forces, whereas *Kol Demamah Dakah* teaches Elijah that God prefers gentle compassion and patient guidance over harsh zealotry.
- **Talmud & Malachi 3:23-24:** Portray Elijah's ultimate mission as *"turning the hearts of parents to children, and the hearts of children to parents"* — healing generational divides.""",
        """1. Why did the angel first give Elijah bread, water, and a nap before asking him a single spiritual question?
2. Why was God *not* in the earthquake or the fire, but in the "still, small voice"?
3. Where in our busy week do we make room to actually hear that quiet voice?"""
    ),
    (
        "16-esther-jonah-daniel",
        "Esther, Jonah & Daniel: Faith in the Wider World",
        "אסתר, יונה ודניאל",
        "Hidden providence, universal compassion, and quiet courage in exile",
        "Esther 4:14; Jonah 1-4; Daniel 6",
        """Three unforgettable books in the Writings and Prophets show how Jewish faith shines even far from home:

- **Queen Esther & Purim (*Megillat Esther*):** When the wicked minister Haman plotted to destroy the Jewish people across the Persian Empire, Mordechai challenged young Queen Esther: *"Who knows whether it was for a moment just like this that you attained royalty?"* Risking her own life, Esther spoke with wisdom and courage, turning sorrow into the joyful festival of **Purim** — celebrated with gifts to friends (*mishloach manot*) and charity to the poor (*matanot la'evyonim*). Remarkably, God's Name never appears once in Esther — teaching that God works behind the scenes through brave human choices!
- **Jonah & the Great Fish (*Sefer Yonah*):** Sent to warn the foreign city of Nineveh to turn away from violence, Jonah tried to sail the opposite direction, was swallowed by a great fish in a storm, prayed from its belly, and finally delivered the message — and the whole city repented! Read every **Yom Kippur afternoon**, Jonah teaches that **God's mercy extends to every creature and every nation**, and no one is ever beyond forgiveness.
- **Daniel in the Lions' Den (*Daniel 6*):** Serving faithfully in Babylon and Persia, Daniel refused to stop praying three times a day facing Jerusalem even when a jealous decree forbade it. Thrown into the lions' den, he emerged unharmed at dawn — modeling quiet integrity, loyalty to God, and faithful civic service.""",
        """- **Esther (*Hester Panim*):** The name *Esther* echoes *hester* ("hidden") — celebrating hidden providence (*nes nistar*), where ordinary courage, solidarity, and strategic wisdom become God's hands in history.
- **Jonah (Universal Teshuvah):** Reading Jonah at Yom Kippur *Minchah* reminds the congregation that God cares about *"more than 120,000 people... and much cattle as well"* (Jonah 4:11) — rejecting narrow resentment and affirming universal compassion.
- **Daniel (Diaspora Faithfulness):** Written partially in Hebrew and partially in Aramaic, Daniel became the classic model for maintaining Jewish prayer, kosher observance (*Daniel* 1), and integrity while contributing honestly to the broader society.""",
        """- **Talmud (*Megillah* 12a-16b) & Ibn Ezra:** Explore the layers of irony in Esther (every plot of Haman flips *v'nahafoch hu* — "turned upside down") and note why Purim mandates giving to the poor alongside celebration.
- **Radak & Abravanel on Jonah:** Explain that Jonah didn't flee out of fear, but out of wrestling with strict justice vs. boundless mercy — until the gourd plant (*kikayon*) teaches him God's parental compassion for all creation.
- **Rashi on Daniel 6:** Notes Daniel's window facing Jerusalem (*Daniel* 6:11) as a classic anchor for the Jewish practice of orienting prayer toward Jerusalem.""",
        """1. Why is God's Name never written in the Book of Esther — and how does that make the story even more relatable to our lives?
2. Why do synagogues read the Book of Jonah (about a non-Jewish city being forgiven!) at the most solemn hour of Yom Kippur?
3. What does Daniel teach about staying true to your values while living respectfully in a diverse society?"""
    ),
]

HISTORIES = [
    (
        "01-canon-tanakh-and-old-testament",
        "The Canon of Tanakh & How It Relates to the Old Testament",
        "תנ״ך והתהוות הקאנון",
        "Understanding the 24/39 books, Hebrew ordering vs. Christian Old Testament ordering, and Masoretic preservation",
        "Torah, Nevi'im, Ketuvim",
        """## Structure of the Hebrew Bible (Tanakh)
**TaNaKh** (תנ״ך) is an acronym formed from the three traditional divisions of the Hebrew Scriptures:
1. **Torah (תורה — Instruction / Five Books of Moses):** Genesis (*Bereshit*), Exodus (*Shemot*), Leviticus (*Vayikra*), Numbers (*Bamidbar*), Deuteronomy (*Devarim*). In Jewish life, the Torah is the foundational covenant read aloud in full across the synagogue year in 54 weekly *Parashiyot*.
2. **Nevi'im (נביאים — Prophets):**
   - *Former Prophets:* Joshua, Judges, Samuel (I & II), Kings (I & II) — theological history from entering the Land to the Babylonian Exile.
   - *Latter Prophets:* Isaiah, Jeremiah, Ezekiel, and the Twelve Minor Prophets (*Trei Asar*: Hosea through Malachi) — moral, social, and spiritual conscience of Israel.
3. **Ketuvim (כתובים — Writings):** Psalms (*Tehillim*), Proverbs (*Mishlei*), Job (*Iyov*), the Five Scrolls (*Chamesh Megillot*: Song of Songs, Ruth, Lamentations, Ecclesiastes, Esther), Daniel, Ezra-Nehemiah, and Chronicles (I & II).

## Why 24 Books (Jewish) = 39 Books (Protestant Old Testament)?
The exact same Hebrew texts are counted as **24 books** in Jewish tradition (counting Samuel, Kings, Chronicles, and Ezra-Nehemiah as one book each, and the Twelve Minor Prophets as a single scroll *Trei Asar*) and **39 books** in English/Protestant Bibles (splitting those books individually). Catholic and Eastern Orthodox Old Testaments also include **Deuterocanonical** works (such as Maccabees, Ben Sira/Sirach, Judith, Tobit, and Wisdom of Solomon) preserved in the ancient Greek **Septuagint** translation — works of great Jewish historical value from the Second Temple era (I & II Maccabees are key historical sources for Chanukah!) though not included in the Hebrew Masoretic canon.

## Differences in Ordering & Theological Arc
- **Jewish Tanakh Order** ends with **II Chronicles 36:23** — King Cyrus of Persia's decree inviting the exiles back to rebuild Jerusalem: *"Whoever is among you of all His people, may the Lord his God be with him, and let him go up!"* — closing on return, hope, and rebuilding.
- **Christian Old Testament Order** places the Prophets last (ending with **Malachi 4**'s promise of Elijah's return), positioning the Old Testament as a bridge leading directly into the New Testament Gospels.
- Understanding both orderings helps Jewish readers, interfaith visitors, and students appreciate each tradition's integrity without conflating them.

## Masoretic Preservation
Between the 6th and 10th centuries CE, Jewish scholar-scribes called the **Masoretes** (most famously the Ben Asher family in Tiberias) perfected a meticulous system of vowel points (*nikud*), cantillation marks (*ta'amim*), and marginal counts (*masorah*) to preserve the Hebrew text letter-for-letter. Famous surviving Masoretic manuscripts include the **Aleppo Codex** (c. 930 CE) and the **Leningrad Codex** (1008 CE), which remains the basis of modern Hebrew Bibles.""",
    ),
    (
        "02-dead-sea-scrolls-second-temple",
        "The Dead Sea Scrolls & Second Temple Judaism",
        "מגילות מדבר יהודה ובית שני",
        "Qumran discoveries, 2,000-year textual fidelity, and the birth of the Synagogue",
        "Isaiah, Psalms, Deuteronomy, Ezra, Nehemiah",
        """## The Discovery at Qumran (1947–1956)
In 1947, Bedouin shepherds exploring limestone caves near **Khirbet Qumran** along the northwestern shore of the Dead Sea uncovered clay jars holding leather and papyrus scrolls dating from roughly **250 BCE to 68 CE**. Over 900 manuscripts — tens of thousands of fragments — were recovered across eleven caves, transforming our knowledge of Second Temple Judaism by pushing surviving biblical manuscripts **more than a thousand years earlier** than the medieval Masoretic codices!

## Textual Fidelity: The Great Isaiah Scroll
- Every single book of the Hebrew Tanakh except Esther (whose absence may simply be accidental or tied to Qumran's calendar debates) was found at Qumran, with **Psalms, Deuteronomy, and Isaiah** the most frequently copied.
- The **Great Isaiah Scroll (1QIsaᵃ)**, dating to ~125 BCE, preserves all 66 chapters of Isaiah almost intact — and matches the medieval Masoretic Text used in synagogues today with remarkable word-for-word fidelity (mostly minor spelling/orthographic differences).
- Qumran also revealed that in the Second Temple period, minor variant textual families circulated side-by-side (proto-Masoretic, pre-Samaritan, and Hebrew Vorlagen behind the Greek Septuagint) before the Rabbis standardized the proto-Masoretic text after 70 CE.

## Second Temple Communities & the Birth of the Synagogue
During the Persian, Hellenistic, Hasmonean, and Roman eras (516 BCE–70 CE), Jewish life was vibrant and diverse:
- **Pharisees (*Perushim*):** Championing both Written and Oral Torah, accessible lay study, prayer, and ethical compassion — the spiritual ancestors of **Rabbinic Judaism** (Mishnah, Talmud, and modern synagogue life).
- **Sadducees (*Tzedukim*):** Priestly aristocracy centered on the Jerusalem Temple service.
- **Essenes / Qumran Community:** Ascetic desert community emphasizing ritual purity, apocalyptic expectation, and meticulous scroll copying.
- **Rise of the Synagogue (*Beit Knesset*):** Beginning during the Babylonian Exile and flourishing throughout Judea and the Diaspora (from Alexandria to Galilee, as seen in the 1st-century **Magdala Synagogue** and **Theodotus Inscription** in Jerusalem), the synagogue emerged as a revolutionary institution — a house of **gathering, Torah reading, study, and prayer** that enabled Jewish life to endure and thrive even after the Second Temple's destruction in 70 CE.""",
    ),
    (
        "03-archaeology-and-ancient-near-east",
        "Biblical Archaeology & Ancient Near East Context",
        "ארכיאולוגיה מקראית והמזרח הקדום",
        "Real inscriptions, artifacts, and historical anchors illuminating the Tanakh",
        "Numbers 6:24-26; II Kings 18-25; Ezra 1",
        """## Remarkable Archaeological Anchors of the Tanakh
Archaeology does not "prove" or replace faith, but it vividly illuminates the real historical world in which the stories of the Torah, Prophets, and Writings unfolded:

1. **Ketef Hinnom Silver Amulet Scrolls (c. 600 BCE, Jerusalem):**
   - Discovered in 1979 overlooking the Hinnom Valley in Jerusalem, two tiny rolled silver amulets from the late First Temple period contain the **oldest surviving biblical text ever found** — the **Priestly Blessing (*Birkat Kohanim*)** from **Numbers 6:24–26** (*"May the Lord bless you and keep you; may the Lord shine His face upon you..."*), predating the Dead Sea Scrolls by over 400 years!
2. **Tel Dan Stele (9th century BCE, Northern Israel):**
   - An Aramaic victory inscription erected by an Aramean king (likely Hazael of Damascus) explicitly referencing the **"House of David" (*Beit David*)** — the earliest extra-biblical archaeological reference to King David's dynasty.
3. **Mesha Stele / Moabite Stone (c. 840 BCE):**
   - Erected by King Mesha of Moab, directly paralleling events in **II Kings 3**, mentioning King Omri of Israel, the tribe of Gad, and the four-letter Divine Name (*YHVH*).
4. **Hezekiah's Tunnel & the Siloam Inscription (c. 701 BCE, Jerusalem):**
   - A 533-meter water tunnel carved through solid bedrock beneath the City of David to protect Jerusalem's water supply ahead of the Assyrian King Sennacherib's siege — directly recorded in **II Kings 20:20** and **II Chronicles 32:30**, alongside Sennacherib's own **Taylor Prism** confirming he besieged Hezekiah in Jerusalem ("like a bird in a cage") yet never captured the city!
5. **Lachish Letters (c. 588 BCE):**
   - Ink-on-pottery military dispatches written in classical Biblical Hebrew during the final days of King Nebuchadnezzar's Babylonian invasion, echoing the exact urgency of **Jeremiah 34:7**.
6. **The Cyrus Cylinder (539 BCE, British Museum):**
   - Clay barrel inscription of King **Cyrus the Great of Persia** proclaiming his policy of allowing exiled peoples to return home and restore their temples — providing stunning historical confirmation of the policy celebrated in **Ezra 1** and **II Chronicles 36:22–23**.

## Ancient Near East Literary Context
Reading the Torah alongside contemporary Ancient Near Eastern literature (such as *Enuma Elish*, the *Epic of Gilgamesh*, and the *Code of Hammurabi*) highlights what made the Torah morally revolutionary:
- Instead of warring, capricious gods fighting over chaos, **Genesis 1** presents One sovereign Creator calling an orderly cosmos *good* and placing **every** human being — not only the king — in the Divine image (*B'tzelem Elohim*).
- Instead of class-tiered law codes where harming a noble carried harsher penalties than harming a laborer, **Torah law** insists on *"one law for the citizen and the stranger alike"* (Exodus 12:49; Leviticus 24:22) and establishes **Shabbat** — universal weekly rest for workers, servants, strangers, and even animals!""",
    ),
    (
        "04-hebrew-calendar-and-festivals",
        "The Hebrew Calendar, Shabbat & Festival Cycle",
        "לוח השנה העברי, שבת ומועדים",
        "Lunisolar rhythm, the weekly Parashah cycle, and the spiritual meaning of every Jewish holiday",
        "Leviticus 23; Exodus 12; Deuteronomy 16",
        """## The Lunisolar Calendar & Weekly Parashah
The Jewish calendar is **lunisolar**: months follow the moon (~29.5 days, beginning at *Rosh Chodesh*), while an occasional leap month (*Adar II*, 7 times every 19 years) keeps Passover anchored in the spring (*Chag HaAviv*). Across the year, synagogues read the entire Five Books of Moses in **54 weekly portions (*Parashiyot*)**, completing Deuteronomy and immediately rolling back to Genesis 1:1 on **Simchat Torah** — because Torah study never ends!

## The Sacred Year at a Glance
- **Shabbat (Weekly — Friday sunset to Saturday nightfall):** The crown jewel of Jewish time; remembering both Creation and liberation from Egypt through candles, Kiddush, Challah, Torah reading, song, rest, and Havdalah.
- **Rosh Hashanah (1–2 Tishrei):** Jewish New Year, birthday of humanity, sounding of the Shofar, apples & honey, and spiritual renewal.
- **Yom Kippur (10 Tishrei):** Day of Atonement — 25 hours of fasting, honest reflection (*teshuvah*), seeking forgiveness first from people we have hurt and then from God, culminating in *Ne'ilah*.
- **Sukkot & Simchat Torah (15–23 Tishrei):** Dwelling in temporary booths (*sukkot*) under the stars with the Four Species (*lulav* & *etrog*), celebrating gratitude, hospitality, and joy in the Torah.
- **Chanukah (25 Kislev, 8 nights):** Commemorating the Maccabean rededication of the Temple (164 BCE) and the miracle of the oil — increasing light night by night (*ma'alin ba'kodesh*).
- **Tu BiShvat (15 Shevat):** New Year of the Trees — celebrating nature, stewardship, and the Seven Species of the Land of Israel.
- **Purim (14 Adar):** Reading *Megillat Esther*, costumes, joy, food gifts to friends (*mishloach manot*), and charity to those in need (*matanot la'evyonim*).
- **Pesach / Passover (15–22 Nisan):** The Festival of Freedom — Seder storytelling (*Haggadah*), matzah, bitter herbs, Four Questions, and passing memory from generation to generation.
- **Shavuot (6 Sivan):** Festival of Weeks (50 days after Passover via Counting the Omer) — celebrating the Giving of the Torah at Mount Sinai and reading the Book of Ruth.
- **Tisha B'Av (9 Av):** Solemn fast commemorating the destruction of both the First and Second Temples in Jerusalem and praying for peace and rebuilding.""",
    ),
]

GUIDES = [
    (
        "01-pardes-interpretation-guide",
        "PaRDeS: The Four Classic Levels of Torah Interpretation",
        "פרד״ס — ארבע דרכי פירוש התורה",
        "How Jewish tradition reads every verse in four rich, harmonious dimensions",
        "Genesis 1:1; Proverbs 25:11",
        """## What Is PaRDeS (פרד״ס)?
*Pardes* literally means **"orchard"** — and serves as the classic Jewish acronym for four complementary ways of interpreting any Torah passage (often described as the **"70 faces of the Torah"** — *Shiv'im Panim LaTorah*):

1. **Peshat (פְּשָׁט — Plain / Contextual Meaning):**
   - What do the Hebrew words, grammar, literary flow, and historical context directly say?
   - Guided by the Talmudic principle (*Shabbat* 63a): *"A verse never departs from its plain contextual meaning."* Masters include **Ibn Ezra**, **Rashbam**, and **Rashi** (who weaves *peshat* and *midrash* seamlessly).
2. **Remez (רֶמֶז — Hint / Allusion):**
   - Deeper patterns, cross-references between verses, wordplay, unusual spellings, or numerical resonances (*gematria*).
   - Example: Jacob's ladder (*sulam* = 130) hinting at *Sinai* (= 130).
3. **Derash (דְּרַשׁ — Homiletical / Midrashic Inquiry):**
   - Drawing out ethical lessons, stories behind the silences of the text, and practical legal applications (*Midrash Aggadah* and *Midrash Halakhah*).
   - Asks: *Why did the Torah mention this detail here? What does this teach us about how to live with kindness and justice today?*
4. **Sod (סוֹד — Mystical / Inner Meaning):**
   - The contemplative, spiritual, and Kabbalistic dimension (explored in the *Zohar*, *Ramban*, and Hasidic masters) — seeing Torah as a living map of the soul and the hidden unity of creation.

## How to Study Any Verse in 4 Steps
1. Read the **Hebrew & English** aloud slowly (*Peshat*).
2. Notice what surprises you — a repeated word, a pause, an unanswered question (*Remez*).
3. Open **Rashi, Ramban, Ibn Ezra, Sforno, and Midrash** to hear centuries of conversation (*Derash*).
4. Ask: *What does this verse ask of my heart and my community this week?* (*Sod* & lived Torah).""",
    ),
    (
        "02-meet-the-classical-commentators",
        "Meet the Classical Torah Commentators",
        "פרשני המקרא הקלאסיים",
        "Your guides across a thousand years of Jewish scholarship loaded locally on this station",
        "Rashi, Ramban, Ibn Ezra, Sforno, Pirkei Avot, Midrash Rabbah",
        """## The Voices Inside This Synagogue Library
Every verse in the Five Books of the Torah on this station is linked locally — 100% offline — to four of the greatest pillars of Jewish biblical commentary, alongside **Pirkei Avot** and **Midrash Rabbah**:

- **Rashi — Rabbi Shlomo Yitzchaki (1040–1105, Troyes, France):**
  - The single most beloved commentator in Jewish history. In crisp, sparkling prose, Rashi answers the exact questions a careful reader notices in the Hebrew text, weaving together grammar (*peshat*) and the best of Rabbinic *Midrash*. Children and lifelong scholars alike begin with Rashi.
- **Ibn Ezra — Rabbi Avraham ibn Ezra (1089–1167, Spain):**
  - Poet, astronomer, grammarian, and razor-sharp rationalist. Ibn Ezra focuses fiercely on Hebrew linguistics, plain literary meaning (*peshat*), and logical coherence, often writing with dry wit and concise brilliance.
- **Ramban — Rabbi Moshe ben Nachman / Nachmanides (1194–1270, Girona, Spain & Jerusalem):**
  - Master Talmudist, physician, philosopher, and mystic. Unlike Rashi's verse-by-verse brevity, Ramban zooms out to explain the **big picture** — why chapters are ordered as they are, psychological depth of biblical characters, and deep spiritual symbolism (*"the deeds of the ancestors are a signpost for their children"*).
- **Sforno — Rabbi Ovadia Sforno (c. 1475–1550, Italy):**
  - Renaissance physician and humanist scholar. Sforno writes with remarkable clarity and warmth, focusing on human moral purpose, dignity, and how every mitzvah elevates character and society.
- **Pirkei Avot (Ethics of the Fathers):**
  - The beloved Mishnah tractate of Jewish wisdom (*"If I am not for myself, who will be for me? And if I am only for myself, what am I? And if not now, when?"* — Hillel, 1:14; *"It is not your duty to finish the work, yet neither are you free to desist from it"* — Rabbi Tarfon, 2:16).
- **Midrash Rabbah (Bereishit & Shemot Rabbah):**
  - The classical treasury of Rabbinic parables, dialogues, and imaginative inquiries compiled in the Land of Israel, bringing the human heartbeat of Genesis and Exodus to life.""",
    ),
]


def write_all():
    (BASE / "stories").mkdir(parents=True, exist_ok=True)
    (BASE / "history").mkdir(parents=True, exist_ok=True)
    (BASE / "guides").mkdir(parents=True, exist_ok=True)

    for slug, title, he_title, subtitle, refs, kid, adult, comm, disc in STORIES:
        md = f"""---
title: "{title}"
he_title: "{he_title}"
subtitle: "{subtitle}"
refs: "{refs}"
---

## The Story (For Kids & Families)
{kid}

## Deeper Meaning & PaRDeS Interpretation
{adult}

## What the Classical Commentators Say
{comm}

## Shabbat Table & Discussion Questions
{disc}
"""
        (BASE / "stories" / f"{slug}.md").write_text(md, encoding="utf-8")

    for slug, title, he_title, subtitle, refs, body in HISTORIES:
        md = f"""---
title: "{title}"
he_title: "{he_title}"
subtitle: "{subtitle}"
refs: "{refs}"
---

{body}
"""
        (BASE / "history" / f"{slug}.md").write_text(md, encoding="utf-8")

    for slug, title, he_title, subtitle, refs, body in GUIDES:
        md = f"""---
title: "{title}"
he_title: "{he_title}"
subtitle: "{subtitle}"
refs: "{refs}"
---

{body}
"""
        (BASE / "guides" / f"{slug}.md").write_text(md, encoding="utf-8")

    print(f"Seeded {len(STORIES)} stories, {len(HISTORIES)} history dossiers, {len(GUIDES)} guides into {BASE}")


if __name__ == "__main__":
    write_all()
