"""Deep coverage audit for the theology bank.

For each pillar, check the canonical named figures + events + objects
+ episodes against the bank. Report counts + gaps.

Output: console report + _theology_coverage_audit.json
"""
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

bank = json.loads(Path("data/questions/theology.json").read_text(encoding="utf-8"))
print(f"Auditing {len(bank)} theology questions for pillar coverage\n")


def count_term(term: str) -> tuple[int, int, int]:
    """Returns (stem_uses, answer_uses, context_uses) — case-insensitive."""
    pat = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    stem = sum(1 for q in bank if pat.search(q.get("question", "")))
    answer = sum(1 for q in bank if pat.search(q.get("answer", "")))
    context = sum(1 for q in bank if pat.search(q.get("context", "")))
    return stem, answer, context


CHRISTIAN_COVERAGE = {
    "Genesis narratives": ["Adam", "Eve", "Cain", "Abel", "Noah", "Babel", "Abraham", "Isaac", "Jacob", "Esau", "Joseph", "Sodom", "Lot's wife", "Hagar", "Ishmael", "Rebekah", "Rachel", "Leah"],
    "Exodus + wilderness": ["Moses", "burning bush", "Pharaoh", "Aaron", "Miriam", "Red Sea", "Sinai", "Ten Commandments", "golden calf", "bronze serpent", "Korah", "Balaam"],
    "Joshua + Judges": ["Joshua", "Jericho", "Rahab", "Achan", "Deborah", "Jael", "Gideon", "Samson", "Delilah"],
    "Kings + Prophets": ["Saul", "David", "Goliath", "Bathsheba", "Nathan", "Solomon", "temple", "Elijah", "Elisha", "Ahab", "Jezebel", "Naboth", "Mt Carmel", "still small voice", "chariot of fire", "Hezekiah", "Sennacherib", "Isaiah", "Jeremiah", "Ezekiel"],
    "Exile + return": ["Daniel", "lions' den", "Shadrach", "Meshach", "Abednego", "fiery furnace", "Belshazzar", "Esther", "Mordecai", "Haman", "Nehemiah", "Ezra"],
    "Wisdom + minor prophets": ["Job", "Jonah", "Ruth", "Boaz", "Hannah", "Samuel"],
    "Christmas + infancy": ["Mary", "Joseph", "angel", "manger", "Bethlehem", "shepherds", "magi", "Herod", "Egypt", "Annunciation"],
    "Christ public ministry": ["Jesus", "John the Baptist", "Peter", "Andrew", "James", "John", "Matthew", "Judas", "Lazarus", "Mary Magdalene", "Martha", "Zacchaeus", "Nicodemus", "Samaritan woman", "Cana", "loaves", "walking on water", "Transfiguration", "Sermon on the Mount", "Beatitudes", "Good Samaritan", "Prodigal Son", "mustard seed"],
    "Passion + Resurrection": ["Last Supper", "Gethsemane", "Pilate", "Barabbas", "Caiaphas", "Simon of Cyrene", "Golgotha", "Calvary", "crucifixion", "Resurrection", "empty tomb", "Thomas", "Emmaus", "Ascension"],
    "Acts + early church": ["Pentecost", "Stephen", "Saul", "Paul", "Damascus", "Silas", "Lydia", "Apollos", "Areopagus", "Athens", "Malta", "shipwreck", "Bereans"],
    "Saints": ["Polycarp", "Sebastian", "Lawrence", "Patrick", "Joan", "George", "Francis", "Becket", "Augustine", "Anthony", "Catherine", "Athanasius", "Boniface", "Columba", "Benedict"],
}

ARTHURIAN_COVERAGE = {
    "Arthur + early": ["Uther Pendragon", "Igraine", "Ector", "Arthur", "sword in the stone", "Merlin", "Vivienne", "Nimue", "Excalibur", "Lady of the Lake"],
    "Round Table knights": ["Lancelot", "Galahad", "Gawain", "Percival", "Bors", "Kay", "Bedivere", "Tristan", "Iseult", "Mordred", "Guinevere", "Morgan le Fay"],
    "Grail + quest": ["Holy Grail", "Siege Perilous", "Joseph of Arimathea", "Fisher King"],
    "Battles + end": ["Camelot", "Camlann", "Avalon", "Sir Bedivere", "three queens"],
    "Other Arthurian episodes": ["Green Knight", "Gareth", "Gaheris", "Meleagant", "Knight of the Cart", "Stonehenge", "Vortigern", "two dragons"],
    "Robin Hood + Sherwood": ["Robin Hood", "Sherwood", "Little John", "Friar Tuck", "Maid Marian", "Sheriff of Nottingham", "Will Scarlett", "Much", "Allan a Dale", "Lincoln green", "longbow", "archery contest", "Kirklees", "Richard the Lionheart", "Tyburn", "Major Oak"],
    "Charlemagne + Roland": ["Charlemagne", "Roland", "Olifant", "Durendal", "Roncevaux", "Ganelon", "Oliver", "Turpin", "paladins"],
    "Beowulf": ["Beowulf", "Heorot", "Grendel", "Hrothgar", "Hrunting", "Wiglaf", "Hronesness"],
    "El Cid + Faust + Tell + Pied Piper": ["El Cid", "Babieca", "Tizona", "Valencia", "Faust", "Mephistopheles", "Wittenberg", "Helen of Troy", "William Tell", "Gessler", "Altdorf", "Kussnacht", "Rütli", "Pied Piper", "Hamelin", "Hereward"],
}

GREEK_COVERAGE = {
    "Olympians (12)": ["Zeus", "Hera", "Poseidon", "Hades", "Athena", "Apollo", "Artemis", "Ares", "Hermes", "Dionysus", "Aphrodite", "Hephaestus", "Demeter", "Hestia"],
    "Titans + creation": ["Cronos", "Cronus", "Rhea", "Prometheus", "Pandora", "Atlas", "Typhon", "Gigantomachy"],
    "Hercules's 12 labors": ["Nemean Lion", "Hydra", "Ceryneian Hind", "Erymanthian Boar", "Augean Stables", "Stymphalian Birds", "Cretan Bull", "Mares of Diomedes", "Hippolyta", "Geryon", "Hesperides", "Cerberus", "Hercules", "Iolaus", "Eurystheus"],
    "Hercules death + apotheosis": ["Megara", "Nessus", "Deianira", "Mount Oeta", "Philoctetes", "Hebe"],
    "Trojan War heroes": ["Achilles", "Patroclus", "Hector", "Andromache", "Priam", "Paris", "Helen of Troy", "Agamemnon", "Menelaus", "Briseis", "Cassandra", "Aeneas", "Odysseus", "Ajax", "Diomedes", "Nestor"],
    "Trojan War episodes": ["Judgment of Paris", "Apple of Discord", "Eris", "wooden horse", "Trojan Horse", "Sinon", "Laocoön", "Iphigenia", "Aulis"],
    "Odyssey episodes": ["Penelope", "Telemachus", "Polyphemus", "Cyclops", "Aeolus", "Circe", "Tiresias", "Sirens", "Scylla", "Charybdis", "Calypso", "Nausicaa", "Eurycleia", "Argos", "olive-tree bed", "moly"],
    "Other heroes": ["Theseus", "Minotaur", "Ariadne", "Aegeus", "Daedalus", "Icarus", "Perseus", "Medusa", "Andromeda", "Danaë", "Polydectes", "Graeae", "Jason", "Argo", "Argonauts", "Golden Fleece", "Medea", "Phineus", "Harpies", "Clashing Rocks", "Pirithous", "Procrustes", "Bellerophon", "Pegasus", "Cadmus", "Sphinx", "Oedipus", "Antigone", "Jocasta"],
    "Other Olympian episodes": ["Persephone", "Orpheus", "Eurydice", "Echo", "Narcissus", "Atalanta", "Daphne", "Marsyas", "Arachne", "Niobe", "Actaeon", "Sisyphus", "Tantalus", "Midas", "Phaethon", "Castor", "Pollux", "Pan", "Syrinx", "Tiresias", "Furies", "Fates", "Muses", "Chiron"],
    "Mysteries + cults": ["Eleusinian Mysteries", "Delphi", "Pythia", "Python", "Olympic Games", "Pelops"],
    "Curse of Atreus": ["Atreus", "Thyestes", "Agamemnon", "Clytemnestra", "Orestes", "Electra", "Iphigenia"],
}

NORSE_COVERAGE = {
    "Aesir": ["Odin", "Thor", "Loki", "Frigg", "Baldur", "Balder", "Tyr", "Heimdall", "Bragi", "Idunn", "Hel", "Sif", "Vidar", "Vali", "Hodr"],
    "Vanir": ["Freyja", "Freyr", "Njord", "Skadi"],
    "Odin's items + companions": ["Gungnir", "Sleipnir", "Huginn", "Muninn", "Geri", "Freki", "Mimir", "well of Mimir", "Yggdrasil", "Hávamál", "runes"],
    "Thor's items": ["Mjolnir", "Mjölnir", "Tanngrisnir", "Tanngnjostr", "Megingjörð", "Járngreipr", "Bilskirnir", "Thrym"],
    "Other named items": ["Brísingamen", "Brisingamen", "Gjallarhorn", "Bifrost", "Gleipnir", "Skíðblaðnir", "Gullinbursti", "Draupnir", "Gram"],
    "Jötnar + monsters": ["Fenrir", "Jormungandr", "Jörmungandr", "Skoll", "Hati", "Surt", "Hymir", "Skrymir", "Utgard-Loki", "Geirrod", "Suttungr", "Gunnlöð", "Kvasir", "Fafnir", "Regin"],
    "Cosmology": ["Asgard", "Midgard", "Jotunheim", "Vanaheim", "Muspelheim", "Niflheim", "Alfheim", "Svartalfheim", "Hel", "Valhalla", "Sessrumnir", "Ratatoskr", "Nidhogg"],
    "Adventures": ["Thrym's wedding", "Jotunheim journey", "Geirrod hall", "Sif's hair", "Sindri", "Brokkr", "Idunn's apples", "Thiazi", "Asgard's wall", "Svadilfari"],
    "Death of Balder": ["mistletoe", "Tokk", "Hermod", "Hringhorni", "Nanna"],
    "Sigurd / Volsungs": ["Sigurd", "Brunhild", "Gunnar", "Gudrun", "Atli", "Gutthorm", "Andvari", "Sigmund"],
    "Mead of Poetry": ["Bolverk", "Hnitbjorg", "Bödn", "Són", "Óðrerir"],
    "Ragnarok": ["Ragnarok", "Fimbulwinter", "Gullinkambi", "Gjallarhorn", "Garm", "Lif", "Lifthrasir", "Hoddmimir", "Mödi", "Magni", "Gimle"],
}

PILLARS = {
    "Christian": CHRISTIAN_COVERAGE,
    "Arthurian + medieval": ARTHURIAN_COVERAGE,
    "Greek": GREEK_COVERAGE,
    "Norse": NORSE_COVERAGE,
}


report = {}

for pillar, categories in PILLARS.items():
    print(f"\n========== {pillar} ==========")
    pillar_report = {}
    for category, terms in categories.items():
        gaps = []
        partials = []
        covered = []
        for term in terms:
            s, a, c = count_term(term)
            total = s + a + c
            if total == 0:
                gaps.append(term)
            elif total < 2 and s == 0:
                partials.append(f"{term} (s={s},a={a},c={c})")
            else:
                covered.append(f"{term}({total})")

        status = "✓"
        if gaps:
            status = "✗"
        elif partials:
            status = "⚠"

        print(f"\n  {status} {category} ({len(covered)}/{len(terms)} covered)")
        if gaps:
            print(f"    GAPS: {', '.join(gaps)}")
        if partials:
            print(f"    PARTIAL: {', '.join(partials)}")

        pillar_report[category] = {
            "covered_count": len(covered),
            "total_count": len(terms),
            "gaps": gaps,
            "partials": partials,
        }
    report[pillar] = pillar_report

# Summary stats
print("\n\n========== SUMMARY ==========")
total_gaps_all = 0
total_partials_all = 0
total_terms_all = 0
total_covered_all = 0
for pillar, categories in report.items():
    pillar_gaps = sum(len(c["gaps"]) for c in categories.values())
    pillar_partials = sum(len(c["partials"]) for c in categories.values())
    pillar_total = sum(c["total_count"] for c in categories.values())
    pillar_covered = sum(c["covered_count"] for c in categories.values())
    total_gaps_all += pillar_gaps
    total_partials_all += pillar_partials
    total_terms_all += pillar_total
    total_covered_all += pillar_covered
    print(f"  {pillar:>25}: {pillar_covered}/{pillar_total} covered ({100*pillar_covered//pillar_total}%), {pillar_gaps} gaps, {pillar_partials} partials")
print(f"\n  {'TOTAL':>25}: {total_covered_all}/{total_terms_all} covered ({100*total_covered_all//total_terms_all}%), {total_gaps_all} gaps")

Path("_theology_coverage_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print("\nWrote _theology_coverage_audit.json")
