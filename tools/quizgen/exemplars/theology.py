"""Theology bank voice anchors (30 exemplars).

These 30 questions are the Wonder Pattern (adapted for theology) made
concrete. Six anchors per tier, each anchor hitting a specific role in
the framework:

  Per tier (T1-T5):
    P1  Christian — Bible narrative / saint legend
    P2  Arthurian + Western-medieval legend — sword, knight, oath
    P3  Greek myth — Olympian / hero / Trojan / Odyssey
    P4  Norse myth — Aesir / Vanir / Yggdrasil / Ragnarok
    P5  Christian symbolism / liturgy / second Bible scene
    SIG Signature wonder (Robin Hood / Roland / Beowulf / Faust /
        William Tell / second classical hero)

All exemplars are gate-validated and serve as anchors for bulk-gen
agents when they ask "what does a good X tier Y theology question
look like?"

See `proposals/v2_audit/THEOLOGY_FRAMEWORK.md` for the Wonder Pattern
adapted for theology and `proposals/v2_audit/THEOLOGY_TEMPLATES.md`
for stem patterns.
"""
from __future__ import annotations

EXEMPLARS: list[dict] = [
    # =========================================================================
    # T1 — grade 5 — crisp scene + named character/object + the wonder (cap 280)
    # =========================================================================

    # T1-P1 Christian — David + Goliath
    {
        "tier": 1,
        "question": "A giant warrior named Goliath stood nine feet tall and dared Israel's army to send one champion. A shepherd boy stepped out with only a sling and five smooth stones. What was the boy's name?",
        "answer": "David",
        "choices": [
            "David",
            "Saul",
            "Samson",
            "Joshua",
        ],
        "context": "The story is in 1 Samuel 17. David became Israel's greatest king. The stone struck Goliath's forehead and the boy then used the giant's own sword to cut off his head.",
    },

    # T1-P2 Arthurian — sword in the stone
    {
        "tier": 1,
        "question": "A young squire pulled a sword from a stone that no knight in Britain could move. The deed proved he was the rightful king. What was the boy's name?",
        "answer": "Arthur",
        "choices": [
            "Arthur",
            "Lancelot",
            "Galahad",
            "Percival",
        ],
        "context": "Sir Ector raised Arthur as a foster son, not knowing he was the secret heir to Uther Pendragon. The wizard Merlin had hidden the sword in the stone in a London churchyard until Arthur's hand alone could draw it.",
    },

    # T1-P3 Greek — Athena's birth
    {
        "tier": 1,
        "question": "When Zeus had a terrible headache, the smith god Hephaestus split his skull with an axe. Out leaped a fully-armed warrior goddess in a bronze helmet. Who came out?",
        "answer": "Athena",
        "choices": [
            "Athena",
            "Hera",
            "Artemis",
            "Aphrodite",
        ],
        "context": "Athena was the goddess of wisdom, weaving, and strategic war. Her sacred bird was the owl. She was Zeus's favorite child and the patron goddess of Athens.",
    },

    # T1-P4 Norse — Thor's hammer
    {
        "tier": 1,
        "question": "The Norse thunder god rode a chariot pulled by two goats and carried a hammer powerful enough to level mountains. What was the hammer's name?",
        "answer": "Mjolnir",
        "choices": [
            "Mjolnir",
            "Gungnir",
            "Gram",
            "Durendal",
        ],
        "context": "Mjolnir was forged by the dwarf brothers Sindri and Brokkr. It always returned to Thor's hand when thrown. The goats were named Tanngrisnir and Tanngnjostr; Thor could eat them at night and they returned alive in the morning.",
    },

    # T1-P5 Christian — Noah's ark
    {
        "tier": 1,
        "question": "God warned a righteous man named Noah that a flood would cover the earth, telling him to build a huge wooden ark and load it with two of every animal. How long did the rain fall?",
        "answer": "Forty days and forty nights",
        "choices": [
            "Forty days and forty nights",
            "Twelve days and nights of storm",
            "One hundred years of rain",
            "Seven days only",
        ],
        "context": "The story is in Genesis 6-9. After the flood, God set a rainbow in the sky as a promise never to destroy the earth by water again. Noah's three sons (Shem, Ham, and Japheth) repopulated the earth.",
    },

    # T1-SIG Robin Hood
    {
        "tier": 1,
        "question": "An outlaw with a longbow lived in Sherwood Forest, robbing rich travelers to give to the poor. His best friend was a giant called Little John, and his band wore Lincoln green. Who was he?",
        "answer": "Robin Hood",
        "choices": [
            "Robin Hood",
            "King Arthur",
            "William Tell",
            "Friar Tuck",
        ],
        "context": "The Robin Hood ballads first circulated in late-medieval England. His chief enemy was the Sheriff of Nottingham; his love was Maid Marian; his trusted advisor was Friar Tuck, a fighting monk.",
    },

    # =========================================================================
    # T2 — grade 6 — one-paragraph story + named figure + the action (cap 480)
    # =========================================================================

    # T2-P1 Christian — Joseph's coat
    {
        "tier": 2,
        "question": "Joseph's brothers, jealous of his coat of many colors, threw him into a pit and sold him to traders bound for Egypt. Years later, famine struck and those same brothers came to Egypt begging for grain, not knowing the powerful official they faced was Joseph. What did he do for them?",
        "answer": "Forgave them and saved his family from starvation",
        "choices": [
            "Forgave them and saved his family from starvation",
            "Had them all executed for their old crime",
            "Sent them away empty-handed to die in famine",
            "Made them his permanent slaves in Egypt",
        ],
        "context": "The story is in Genesis 37-50. Joseph rose to be second only to Pharaoh by interpreting the king's dreams of seven years of plenty followed by seven of famine. He moved his entire family (including their flocks) to Egypt to save them.",
    },

    # T2-P2 Arthurian — Lady of the Lake
    {
        "tier": 2,
        "question": "A mysterious arm draped in white silk rose from a misty lake holding a sword aloft. King Arthur rowed out in a small boat with Merlin and the Lady of the Lake gave him this enchanted blade — a sword whose scabbard could protect its bearer from losing blood. What was the sword's name?",
        "answer": "Excalibur",
        "choices": [
            "Excalibur",
            "Gram",
            "Durendal",
            "Olifant",
        ],
        "context": "In Thomas Malory's *Le Morte d'Arthur* (1485), Excalibur was distinct from the sword Arthur drew from the stone. As Arthur lay dying after Camlann, he ordered Sir Bedivere to throw Excalibur back into the lake, where the same arm rose to catch it.",
    },

    # T2-P3 Greek — Nemean Lion
    {
        "tier": 2,
        "question": "King Eurystheus ordered Hercules to bring back the skin of the Nemean Lion, a beast whose hide no arrow or sword could pierce. Hercules tracked the lion to its two-mouthed cave, blocked one entrance with boulders, and confronted it inside. Since weapons were useless, how did he kill it?",
        "answer": "He strangled it with his bare hands",
        "choices": [
            "He strangled it with his bare hands",
            "He shot it with the bow of Apollo",
            "He drowned it in the River Styx",
            "He fed it poisoned meat from Olympus",
        ],
        "context": "Hercules wore the lion's pelt afterward as armor, since nothing could pierce it. The skinning was almost impossible — Athena finally suggested using one of the lion's own claws. This was the first of Hercules's twelve labors.",
    },

    # T2-P4 Norse — Thor in the wedding veil
    {
        "tier": 2,
        "question": "Thor woke one morning and his hammer Mjolnir was gone — stolen by the giant Thrym, who demanded the goddess Freyja as ransom. Loki dressed Thor in a wedding veil and bridal gown so he could enter Thrym's hall in disguise as the bride. What did Thor do once he had Mjolnir back?",
        "answer": "Killed Thrym and every giant in the hall",
        "choices": [
            "Killed Thrym and every giant in the hall",
            "Made peace and signed a treaty with the giants",
            "Returned home quietly without revealing himself",
            "Gave Freyja to the giants as he had promised",
        ],
        "context": "The story is in the *Thrymskvitha* of the Poetic Edda. At the wedding feast, Thor ate an entire ox and drank three barrels of mead — Loki covered for him by claiming the bride had fasted for eight days in anticipation. When the hammer was placed in Thor's lap to consecrate the marriage, he seized it and struck.",
    },

    # T2-P5 Christian — Loaves and fishes
    {
        "tier": 2,
        "question": "A crowd of five thousand had followed Jesus into the wilderness all day with nothing to eat. His disciples wanted to send them home, but a boy in the crowd offered the only food anyone had brought. Jesus blessed it, broke it, and fed everyone. How much food did the boy have?",
        "answer": "Five loaves of bread and two fish",
        "choices": [
            "Five loaves of bread and two fish",
            "Three barley cakes and a jar of honey",
            "A skin of wine and a basket of dates",
            "Twelve fig cakes and a dried lamb",
        ],
        "context": "The Feeding of the Five Thousand is the only miracle (other than the Resurrection) recorded in all four Gospels. Twelve baskets of leftover scraps were gathered. The Greek term used for the boy's basket is *kophinos* — a small lunch basket.",
    },

    # T2-SIG Polycarp
    {
        "tier": 2,
        "question": "In 155 AD, the elderly bishop Polycarp of Smyrna was arrested and ordered by the Roman proconsul to curse Christ or burn at the stake. Polycarp was 86 years old. He answered: 'Eighty-six years I have served Him, and He never did me wrong. How can I now curse my King who saved me?' What happened next?",
        "answer": "He was burned alive at the stake",
        "choices": [
            "He was burned alive at the stake",
            "The proconsul released him out of pity",
            "He fled into the mountains in disguise",
            "He recanted and made the required sacrifice",
        ],
        "context": "The *Martyrdom of Polycarp* (c. 156 AD) is the earliest detailed account of a Christian martyr's death outside the New Testament. Witnesses reported that the flames bent away from him, so a soldier finally stabbed him with a sword.",
    },

    # =========================================================================
    # T3 — grade 7 — scene + stakes + dramatic moment + the cool detail (cap 680)
    # =========================================================================

    # T3-P1 Christian — Daniel in the lion's den
    {
        "tier": 3,
        "question": "King Darius signed a decree that anyone praying to any god but the king for thirty days would be thrown to the lions. The Hebrew official Daniel kept praying toward Jerusalem three times a day with his window open in full view. The king's other officials reported him at once. Darius tried all night to find a way out of his own decree but found none. Daniel was thrown to the lions and the den was sealed with a stone. When the stone was rolled away at dawn, what did the king's guards find?",
        "answer": "Daniel alive, the lions had not touched him",
        "choices": [
            "Daniel alive, the lions had not touched him",
            "Only his bloodied robe and the sleeping lions",
            "Daniel hidden in a tunnel he had dug overnight",
            "Daniel transformed into a lion himself",
        ],
        "context": "The story is in Daniel 6. Darius then threw the conspiring officials AND their families into the same den, and the lions devoured them before they hit the floor. Daniel said an angel had shut the lions' mouths.",
    },

    # T3-P2 Arthurian — Lancelot and Guinevere discovered
    {
        "tier": 3,
        "question": "Sir Lancelot was King Arthur's greatest knight but had fallen in love with Arthur's queen, Guinevere. The traitor knight Sir Mordred and twelve others ambushed them together in the queen's chamber. Lancelot, unarmed, killed every attacker except Mordred and escaped. Arthur was forced to sentence Guinevere to burn at the stake for treason. Lancelot rescued her from the flames at the last moment but in the chaos accidentally killed two of his oldest friends — knights who had refused to fight him. Who were those two friends?",
        "answer": "Sir Gareth and Sir Gaheris, Gawain's brothers",
        "choices": [
            "Sir Gareth and Sir Gaheris, Gawain's brothers",
            "Sir Percival and Sir Galahad, the Grail knights",
            "Sir Tristan and Sir Palamedes, the Cornish knights",
            "Sir Kay and Sir Bedivere, Arthur's seneschals",
        ],
        "context": "In Malory's *Le Morte d'Arthur*, the killings turned Sir Gawain — once Lancelot's friend — into his sworn enemy. The resulting civil war drew Arthur away from Britain, allowing Mordred to seize the throne and forcing the final battle of Camlann.",
    },

    # T3-P3 Greek — Theseus and Minotaur
    {
        "tier": 3,
        "question": "King Minos of Crete kept a half-man, half-bull monster called the Minotaur deep in a vast labyrinth designed by Daedalus. Every nine years he demanded seven Athenian youths and seven maidens as tribute, fed to the beast. The Athenian prince Theseus volunteered as one of the tributes, vowing to kill the Minotaur. Princess Ariadne, who had fallen in love with him, gave him something at the labyrinth entrance that let him kill the beast AND find his way back out. What did she give him?",
        "answer": "A ball of thread to mark his path back",
        "choices": [
            "A ball of thread to mark his path back",
            "An enchanted bronze sword that glowed in the dark",
            "A magic helmet that turned him invisible",
            "A pair of winged sandals from Hermes",
        ],
        "context": "Theseus tied the thread at the entrance and unwound it as he went. After killing the Minotaur with his bare hands, he followed the thread back. He took Ariadne with him when he sailed home but later abandoned her on the island of Naxos.",
    },

    # T3-P4 Norse — Sigurd and Fafnir
    {
        "tier": 3,
        "question": "The Volsung hero Sigurd was raised by the dwarf smith Regin, who reforged the broken sword Gram from his ancestor's fragments. Sigurd rode out to fight the dragon Fafnir, who guarded a cursed treasure hoard once stolen from Odin. Sigurd dug a pit on the path the dragon used to drink from a river, hid below, and stabbed upward into Fafnir's heart as the dragon slithered overhead. When Sigurd accidentally tasted Fafnir's blood while roasting the heart, what new power did he gain?",
        "answer": "He could understand the speech of birds",
        "choices": [
            "He could understand the speech of birds",
            "He became invulnerable to all weapons",
            "He gained the strength of ten warriors",
            "He could shape-shift into a dragon at will",
        ],
        "context": "The two birds warned Sigurd that Regin planned to kill him for the hoard, so Sigurd killed Regin first. Sigurd's story is told in the *Volsunga Saga* and inspired Wagner's *Ring of the Nibelung* operas. Sigurd was later betrayed and murdered in his sleep through the schemes of Brunhild, the Valkyrie he had wronged.",
    },

    # T3-P5 Christian — Pentecost
    {
        "tier": 3,
        "question": "Fifty days after the Resurrection, the eleven remaining apostles plus Matthias (who replaced Judas Iscariot) were gathered in an upper room in Jerusalem. A sound like a violent wind filled the house. Tongues of flame appeared above each of their heads. They poured into the street and began preaching — and the Parthians, Medes, Elamites, Egyptians, Romans, and Arabs in the city for the festival each heard the apostles speaking in their own native languages. What language did the apostles think they were speaking?",
        "answer": "Their own Galilean Aramaic — the miracle was in the hearing",
        "choices": [
            "Their own Galilean Aramaic — the miracle was in the hearing",
            "Hebrew — the temple's holy language alone",
            "Greek — the trade language of the Roman world",
            "Latin — the imperial language of Rome",
        ],
        "context": "The Pentecost story is in Acts 2. About 3,000 were baptized that day, marking the traditional birthday of the Christian Church. The Jewish festival of Shavuot (Weeks) had brought pilgrims from across the diaspora to Jerusalem.",
    },

    # T3-SIG Roland at Roncevaux
    {
        "tier": 3,
        "question": "In 778 AD, the rear-guard of Charlemagne's army returning from Spain was ambushed by Basque mountain warriors in the narrow pass of Roncevaux in the Pyrenees. The paladin Roland commanded the rear-guard. He carried an ivory war-horn called Olifant that could summon Charlemagne's main army back to fight — but Roland refused to blow it until almost every man was dead, too proud to admit defeat. When he finally blew the horn three times, the third blast burst the veins in his temples and killed him. What was the name of Roland's sword?",
        "answer": "Durendal",
        "choices": [
            "Durendal",
            "Joyeuse",
            "Excalibur",
            "Gram",
        ],
        "context": "*The Song of Roland* (c. 1100) is the oldest surviving major work of French literature. Roland tried to break Durendal against a rock to keep the Saracens from capturing it, but the blade only split the rock. He died holding the sword and the horn together. Charlemagne arrived too late.",
    },

    # =========================================================================
    # T4 — grade 8 — multi-sentence narrative + named specifics + payoff (cap 900)
    # =========================================================================

    # T4-P1 Christian — Last Supper / betrayal
    {
        "tier": 4,
        "question": "On the night before his crucifixion, Jesus gathered the twelve disciples in an upper room in Jerusalem for the Passover meal — what would become known as the Last Supper. He took bread, broke it, and said 'This is my body, given for you. Do this in remembrance of me.' He took the cup of wine and said 'This is my blood of the new covenant, poured out for many.' During the meal he announced that one of the twelve at the table would betray him that very night. Each disciple asked: 'Surely not I, Lord?' One slipped out into the darkness shortly after, leading the temple guards to Jesus in the Garden of Gethsemane and identifying him to the soldiers with a kiss. For what price did he sell Jesus to the chief priests?",
        "answer": "Thirty pieces of silver",
        "choices": [
            "Thirty pieces of silver",
            "A purse of forty gold dinars",
            "Three years of tax exemption",
            "A high priest's robe and signet ring",
        ],
        "context": "The betrayer was Judas Iscariot. The thirty pieces of silver fulfilled Zechariah 11:12-13. Judas later hanged himself from a tree (Matthew 27:5); the priests used the returned silver to buy a potter's field as a burial ground for foreigners. The site became known as Akeldama, the Field of Blood.",
    },

    # T4-P2 Arthurian — Grail quest / Galahad in the Siege Perilous
    {
        "tier": 4,
        "question": "Among King Arthur's Round Table knights, one seat called the Siege Perilous remained always empty. Merlin had prophesied that any unworthy knight sitting there would be swallowed by the earth or burst into flame, and the seat was reserved for the knight pure enough to achieve the Holy Grail. On the feast of Pentecost, a young knight in white armor arrived at Camelot with an old hermit. He sat down in the Siege Perilous without harm, the first ever to do so. That evening a vision of the Grail appeared at the Round Table, veiled in white samite, and Galahad, his father Lancelot, Percival, and Bors set out on the quest. Of those four, who alone saw the unveiled Grail?",
        "answer": "Galahad alone, who died in ecstasy at the vision",
        "choices": [
            "Galahad alone, who died in ecstasy at the vision",
            "Percival alone, who became its lifelong guardian",
            "Lancelot alone, who repented his adultery first",
            "All four together, on the shores of Sarras",
        ],
        "context": "The Grail tradition appears in Chretien de Troyes (12th c.) and is fully developed in the *Queste del Saint Graal* (13th c.). The Grail was believed to be the cup Christ used at the Last Supper, later used by Joseph of Arimathea to catch his blood at the cross. Lancelot, blocked by his sin with Guinevere, glimpsed the Grail through a curtain but could not enter.",
    },

    # T4-P3 Greek — Orpheus and Eurydice
    {
        "tier": 4,
        "question": "When the nymph Eurydice died of a snake bite on her wedding day, her grieving husband Orpheus took only his lyre and descended into the underworld. He charmed Charon to ferry him across the Styx and lulled three-headed Cerberus to sleep with his music. So beautifully did he play before Hades and Persephone that the king and queen of the dead wept and granted him an impossible gift. Eurydice could follow him back to the living, but on one strict condition: Orpheus must walk ahead of her all the way out and not turn to look back. They were nearly out, sunlight visible at the cave's mouth, when something made Orpheus turn. What was Eurydice's fate when he looked?",
        "answer": "She vanished forever, drawn back into the underworld",
        "choices": [
            "She vanished forever, drawn back into the underworld",
            "She was transformed into a laurel tree at his feet",
            "Hades let her stay despite the broken condition",
            "Both were granted immortality on Mount Olympus",
        ],
        "context": "Orpheus wandered Thrace mourning and refusing to play music for anyone. He was eventually torn apart by maenads (frenzied followers of Dionysus) who could not bear his rejection. His severed head, still singing, floated down the river Hebrus to the island of Lesbos, where it became an oracle.",
    },

    # T4-P4 Norse — Death of Balder
    {
        "tier": 4,
        "question": "Balder the Beautiful, the most beloved son of Odin and Frigg, began having dreams of his own death. His mother Frigg traveled through the nine worlds extracting promises from every thing in creation — every fire, every water, every iron, every stone, every plant, every animal, every disease — that none would ever harm Balder. The gods then amused themselves at feasts by throwing weapons and rocks at him, watching them bounce off harmlessly. But Loki, jealous of Balder's invulnerability, discovered that Frigg had skipped one plant, thinking it too young and small to bother asking. Loki carved a dart from it and gave it to Balder's blind brother Hodr to throw 'as a gift' — and Balder fell dead. What was the plant?",
        "answer": "Mistletoe",
        "choices": [
            "Mistletoe",
            "Holly berries",
            "Yew sapling",
            "Rowan twig",
        ],
        "context": "Hermod, another of Odin's sons, rode Sleipnir down to Hel to beg for Balder's return. Hel agreed, but only if every living thing in the nine worlds wept for Balder. All did — except one giantess named Tokk (Loki in disguise), who refused. Balder stayed in Hel until after Ragnarok.",
    },

    # T4-P5 Christian — Becket murdered in Canterbury
    {
        "tier": 4,
        "question": "On December 29, 1170, four knights of King Henry II of England rode into Canterbury Cathedral. They were responding to the king's rhetorical outburst about Archbishop Thomas Becket — once Henry's closest friend and chancellor, then named archbishop, then bitterly opposed to Henry over Church-versus-Crown authority. The knights demanded Becket leave the cathedral with them. Becket refused, declaring himself ready to die for the freedom of the Church. They drew their swords on the cathedral's stone steps as the monks watched in horror. Reginald FitzUrse struck the first blow, slicing off the top of Becket's skull. What had Henry said in his rage that the knights had taken as a royal command to act?",
        "answer": "Will no one rid me of this turbulent priest?",
        "choices": [
            "Will no one rid me of this turbulent priest?",
            "He must be silenced before the Christmas feast",
            "Let his blood run to teach the bishops obedience",
            "I want him dead by my own birthday next month",
        ],
        "context": "Becket was canonized just three years later, in 1173. His shrine at Canterbury became one of medieval Europe's greatest pilgrimage destinations — the destination of the pilgrims in Chaucer's *Canterbury Tales*. Henry II did public penance in 1174, walking barefoot to the cathedral and being whipped by the monks at Becket's tomb.",
    },

    # T4-SIG William Tell
    {
        "tier": 4,
        "question": "The Habsburg bailiff Hermann Gessler hung his hat on a pole in the central square of Altdorf, Switzerland, and decreed that every passerby must bow to it as a sign of submission to Austrian rule. The hunter William Tell, walking through with his young son Walter, refused to bow. Gessler ordered Tell shot — unless the famous archer could shoot an apple off Walter's head from eighty paces with a single arrow. Tell asked for two arrows from his quiver, took careful aim, and split the apple cleanly without grazing his son's hair. Gessler, suspicious, demanded to know why Tell had taken a second arrow. Tell answered honestly. What was his answer?",
        "answer": "If I had killed my son, the second arrow was for you",
        "choices": [
            "If I had killed my son, the second arrow was for you",
            "The second was a backup if the first arrow snapped",
            "I always carry two, one for game and one for war",
            "The second was for my own heart if I had failed",
        ],
        "context": "Gessler ordered Tell arrested for the threat. Tell escaped on a stormy lake crossing, hid in the mountains, and later ambushed Gessler on the road near Kussnacht, killing him with a single arrow. The story is the founding legend of Swiss independence, dramatized in Friedrich Schiller's 1804 play *Wilhelm Tell*.",
    },

    # =========================================================================
    # T5 — grade 9-10 — deep story + characters + most memorable detail (cap 1100)
    # =========================================================================

    # T5-P1 Christian — Passion / sign on the cross
    {
        "tier": 5,
        "question": "On the night of his arrest, Jesus prayed in the Garden of Gethsemane while his disciples slept. Roman soldiers led by the temple guard arrived, with Judas Iscariot pointing him out by a kiss in exchange for thirty pieces of silver. He was taken first to the high priest Caiaphas, then before the Roman governor Pontius Pilate, who tried to release him by offering the Passover crowd a choice between Jesus and the bandit Barabbas. The crowd chose Barabbas. Pilate washed his hands publicly to declare himself innocent of Jesus's blood and turned him over to be flogged and crucified. He was led to a hill outside Jerusalem called Golgotha — 'Place of the Skull' — where two thieves were also crucified beside him. A sign was nailed above his cross by Pilate's order, declaring the charge against him. The Gospels record that it was written in three languages so that everyone passing could read it. What did the sign say?",
        "answer": "Jesus of Nazareth, King of the Jews",
        "choices": [
            "Jesus of Nazareth, King of the Jews",
            "Jesus of Galilee, False Prophet of Israel",
            "Jesus the Carpenter, Enemy of Caesar",
            "Jesus of Bethlehem, Blasphemer Against God",
        ],
        "context": "The languages were Latin, Greek, and Hebrew. The Latin phrase *Iesus Nazarenus Rex Iudaeorum* gives the abbreviation INRI seen above many crucifixes. The chief priests objected to the wording, demanding it read 'He said, I am King of the Jews' — Pilate refused, replying 'What I have written, I have written.'",
    },

    # T5-P2 Arthurian — Mordred / Camlann
    {
        "tier": 5,
        "question": "While King Arthur was campaigning in France against Lancelot (who had fled after the discovery of his affair with Queen Guinevere), Arthur left his kingdom in the care of his nephew Mordred — who was also, in the later traditions, his secret son by his half-sister Morgause. Mordred seized the throne, declared Arthur dead, forced Guinevere into marriage (she escaped to a convent), and rallied a rebel army. Arthur raced home and the two armies met on Salisbury Plain at the Battle of Camlann. A truce was negotiated — but a soldier on one side drew his sword to kill a snake near his foot. The other side saw the sudden movement and the slaughter began. Arthur killed Mordred with his spear, but with his final strength Mordred drove his own blade through Arthur's helmet into his skull. What did Arthur order Sir Bedivere to do with Excalibur?",
        "answer": "Throw it back into the lake where the arm rose to catch it",
        "choices": [
            "Throw it back into the lake where the arm rose to catch it",
            "Bury it with him in the tomb at Glastonbury Abbey",
            "Carry it home to Camelot for his heirs to inherit",
            "Break the blade across his knee so none could wield it",
        ],
        "context": "Sir Bedivere twice hid Excalibur in the reeds and lied to the dying Arthur, claiming he had thrown it. Arthur knew he lied. The third time Bedivere obeyed and an arm rose from the lake to catch the sword. Three queens then arrived on a barge to take Arthur to the island of Avalon — and the legends differ on whether he died there or sleeps awaiting Britain's hour of need.",
    },

    # T5-P3 Greek — Hercules and Cerberus
    {
        "tier": 5,
        "question": "The twelfth and final labor of Hercules was to descend to the underworld and bring back Cerberus, the three-headed dog guarding the gates of Hades, without using any weapon. Hercules first sought initiation in the Eleusinian Mysteries to prepare his soul for the journey, then descended at Cape Tainaron in the Peloponnese, guided by Hermes and his patron goddess Athena. He found Hades on his throne and politely requested permission to take Cerberus. Hades agreed on one condition: Hercules must subdue the beast bare-handed. Hercules wrestled all three heads simultaneously until Cerberus submitted, and carried the dog up alive to King Eurystheus's court. The king took one look and dove into a large bronze jar in terror, ordering Hercules to take the beast away at once. What happened to Cerberus afterward?",
        "answer": "Hercules returned him peacefully to the gates of Hades",
        "choices": [
            "Hercules returned him peacefully to the gates of Hades",
            "The dog escaped and now roams the Greek countryside",
            "Hercules killed the beast and skinned all three heads",
            "Cerberus was given to Eurystheus as a guard dog",
        ],
        "context": "The twelve labors were imposed on Hercules by King Eurystheus as penance for killing his own wife Megara and their children in a fit of madness sent by Hera. The completion of the labors made Hercules the only mortal in Greek myth to be raised to full godhood on Mount Olympus after his death — eventually reconciling with Hera and marrying her daughter Hebe.",
    },

    # T5-P4 Norse — Ragnarok / Surt
    {
        "tier": 5,
        "question": "The Norse myths describe Ragnarok, the fated doom of the gods, with terrifying specifics drawn from the *Voluspa* in the Poetic Edda. The cock Gullinkambi crows in Valhalla. Three winters of unbroken Fimbulwinter cover the earth. Heimdall blows the Gjallarhorn from his post on the rainbow Bifrost. The wolf Fenrir, who once bit off the war-god Tyr's hand and was bound with the magical fetter Gleipnir, breaks free. The world serpent Jormungandr rises from the sea and floods the land with venom. Thor slays the serpent with Mjolnir but staggers nine steps and dies of its poison. Odin himself is swallowed whole by Fenrir, then avenged by his silent son Vidar, who tears the wolf's jaws apart with iron-shod boots. Loki and Heimdall kill each other. Finally the fire-giant Surt rides out from Muspelheim, the realm of fire in the south, with a flaming sword brighter than the sun. What does Surt do with his sword that ends the world?",
        "answer": "Ignites Yggdrasil, burning all nine worlds",
        "choices": [
            "Ignites Yggdrasil, burning all nine worlds",
            "Cuts the rainbow bridge Bifrost in two",
            "Decapitates Odin's slain corpse on the field",
            "Splits the sky open to let in the chaos",
        ],
        "context": "After the fire, a new earth rises from the sea, green and fair. Two human survivors, Lif and Lifthrasir, emerge from hiding in the wood Hoddmimir to repopulate it. Balder returns from Hel. The sons of Thor inherit Mjolnir. The cycle begins again — the Norse imagined renewal, not just ending.",
    },

    # T5-P5 Christian — Stephen / first martyr
    {
        "tier": 5,
        "question": "Soon after Pentecost, the apostles appointed seven men to administer the daily distribution of food to the Greek-speaking Christian widows in Jerusalem. The first named of the seven was Stephen, full of grace and power, who performed wonders and signs among the people. Members of the Synagogue of the Freedmen argued with Stephen but could not stand up to his wisdom, so they brought false witnesses against him and dragged him before the Sanhedrin on charges of blasphemy. Stephen gave a long speech reviewing the history of Israel — Abraham, Joseph, Moses, the prophets — and concluded by accusing his accusers of being just like their fathers who had killed the prophets, and of murdering the Righteous One whose coming the prophets foretold. The crowd covered their ears, rushed at him, dragged him outside the city, and stoned him. As he died, he saw a vision and cried out specifically what he saw. What was his vision?",
        "answer": "Jesus standing at the right hand of God",
        "choices": [
            "Jesus standing at the right hand of God",
            "Twelve angels with flaming swords descending",
            "His own mother Mary weeping in heaven",
            "The temple of Jerusalem turned to gold",
        ],
        "context": "Stephen's story is in Acts 6-7. As he died he prayed 'Lord Jesus, receive my spirit' and 'Lord, do not hold this sin against them' — echoing Christ's words from the cross. A young Pharisee named Saul of Tarsus stood watching, holding the cloaks of those throwing stones, approving the killing. That same Saul would later be struck down on the road to Damascus and become the Apostle Paul.",
    },

    # T5-SIG Faust's bargain
    {
        "tier": 5,
        "question": "Doctor Faustus, a learned scholar at the University of Wittenberg, despaired of finding ultimate meaning in books — he had mastered law, medicine, philosophy, and theology, yet still felt empty. He summoned the demon Mephistopheles by inscribing a magical pentagram on his study floor and reading from a forbidden grimoire. They struck a bargain: Mephistopheles would serve Faust for twenty-four years on earth, granting any knowledge, pleasure, or power Faust desired. In exchange, Faust signed away his soul in his own blood. During the twenty-four years Mephistopheles showed Faust the imperial court of Charles V, conjured the spirit of Helen of Troy as his bedmate, and worked countless lesser magics — but each pleasure left Faust emptier than before. As the final hour approached, Faust desperately tried to repent. Christopher Marlowe's 1604 play *The Tragical History of Doctor Faustus* ends with the clock striking midnight, the demons appearing in the study to drag Faust to hell. What is Faust's final cry as they seize him?",
        "answer": "I'll burn my books!",
        "choices": [
            "I'll burn my books!",
            "Christ, my Savior, save me now!",
            "Spare me, just one more year of life!",
            "Helen, my love, return to me!",
        ],
        "context": "The historical Johann Faust was a real wandering 16th-century German alchemist. The legend grew quickly after his death in the 1540s. Marlowe wrote the first great dramatic version; Goethe wrote a vast two-part *Faust* (1808 and 1832) in which Faust is ultimately redeemed. The phrase 'Faustian bargain' for selling out one's soul for short-term gain comes from this story.",
    },
]
