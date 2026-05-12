"""Attribution generators: animal → class, breed → species, mythological
figure → tradition, dinosaur → period, etc.

Largest deterministic generator for animal. Strategies:
- vertebrate_class_attribution (T1)
- dinosaur_period_attribution (T2)
- cattle_breed_origin (T2)
- mythological_figure_tradition (T2-T3)
- famous_animal_owner (T2-T3)
- extinct_animal_year (T2-T3)
"""
from __future__ import annotations

from tools.quizgen.animal_generators.common import (
    make_question,
    pick_length_balanced_distractors,
)


# ----- Animal → Vertebrate Class -----
ANIMALS_BY_CLASS = {
    "Mammal": [
        "Cow", "Pig", "Sheep", "Goat", "Horse", "Dog", "Cat", "Whale", "Dolphin", "Bat",
        "Lion", "Tiger", "Bear", "Wolf", "Fox", "Rabbit", "Deer", "Elk", "Moose", "Bison",
        "Elephant", "Rhino", "Hippo", "Giraffe", "Camel", "Llama", "Kangaroo", "Koala",
        "Platypus", "Echidna", "Otter", "Beaver", "Squirrel", "Mouse", "Rat", "Hedgehog",
        "Sloth", "Armadillo", "Anteater", "Skunk", "Raccoon", "Possum", "Mole",
    ],
    "Bird": [
        "Eagle", "Hawk", "Owl", "Sparrow", "Robin", "Crow", "Raven", "Magpie", "Pigeon",
        "Dove", "Chicken", "Duck", "Goose", "Swan", "Turkey", "Quail", "Pheasant",
        "Penguin", "Ostrich", "Emu", "Flamingo", "Pelican", "Heron", "Stork", "Albatross",
        "Hummingbird", "Cardinal", "Parrot", "Cockatoo", "Toucan", "Kingfisher",
        "Woodpecker", "Falcon", "Vulture", "Condor", "Puffin", "Kiwi",
    ],
    "Reptile": [
        "Crocodile", "Alligator", "Komodo dragon", "Iguana", "Gecko", "Chameleon",
        "Cobra", "Python", "Boa", "Rattlesnake", "Viper", "Turtle", "Tortoise",
        "Sea turtle", "Lizard", "Skink", "Anole",
    ],
    "Amphibian": [
        "Frog", "Toad", "Salamander", "Newt", "Axolotl", "Bullfrog", "Tree frog",
        "Caecilian",
    ],
    "Fish": [
        "Salmon", "Tuna", "Cod", "Trout", "Bass", "Carp", "Catfish", "Pike",
        "Shark", "Ray", "Stingray", "Eel", "Anchovy", "Sardine", "Halibut", "Flounder",
        "Marlin", "Swordfish", "Pufferfish", "Anglerfish", "Clownfish", "Mahi-mahi",
        "Barracuda", "Grouper", "Tilapia",
    ],
}

CLASS_DESCRIPTIONS = {
    "Mammal": "Mammary glands, hair/fur, three middle-ear bones; mostly live-bearing.",
    "Bird": "Feathers, beaks, eggs, warm-blooded, hollow bones; evolved from theropod dinosaurs.",
    "Reptile": "Scales, mostly egg-laying, ectothermic; lack feathers/fur.",
    "Amphibian": "Smooth wet skin, life cycle with aquatic larval phase, ectothermic.",
    "Fish": "Gills, fins, mostly aquatic; bony or cartilaginous skeleton.",
}


def generate_vertebrate_class_attribution() -> list[dict]:
    """T1: animal → which vertebrate class."""
    out = []
    all_classes = list(ANIMALS_BY_CLASS.keys())

    for cls, animals in ANIMALS_BY_CLASS.items():
        other_classes = [c for c in all_classes if c != cls]
        for animal in animals:
            out.append(make_question(
                tier=1,
                topic_cell="biology",
                strategy="vertebrate_classes_basic",
                pillar="biology",
                question=f"A {animal} belongs to which vertebrate class?",
                answer=cls,
                distractors=other_classes[:3],
                context=CLASS_DESCRIPTIONS[cls],
            ))
    return out


# ----- Dinosaur → Period -----
DINOSAURS_BY_PERIOD = {
    "Triassic": [
        ("Coelophysis", "Late Triassic"),
        ("Eoraptor", "Late Triassic"),
        ("Plateosaurus", "Late Triassic"),
        ("Herrerasaurus", "Late Triassic"),
    ],
    "Jurassic": [
        ("Stegosaurus", "Late Jurassic"),
        ("Allosaurus", "Late Jurassic"),
        ("Brachiosaurus", "Late Jurassic"),
        ("Diplodocus", "Late Jurassic"),
        ("Apatosaurus", "Late Jurassic"),
        ("Archaeopteryx", "Late Jurassic"),
        ("Brontosaurus", "Late Jurassic"),
    ],
    "Cretaceous": [
        ("Tyrannosaurus rex", "Late Cretaceous"),
        ("Triceratops", "Late Cretaceous"),
        ("Velociraptor", "Late Cretaceous"),
        ("Ankylosaurus", "Late Cretaceous"),
        ("Spinosaurus", "Mid Cretaceous"),
        ("Argentinosaurus", "Late Cretaceous"),
        ("Pachycephalosaurus", "Late Cretaceous"),
        ("Iguanodon", "Early Cretaceous"),
        ("Carnotaurus", "Late Cretaceous"),
        ("Deinonychus", "Early Cretaceous"),
    ],
}


def generate_dinosaur_period() -> list[dict]:
    """T2: dinosaur → which Mesozoic period."""
    out = []
    periods = ["Triassic", "Jurassic", "Cretaceous"]

    for period, dinos in DINOSAURS_BY_PERIOD.items():
        other_periods = [p for p in periods if p != period]
        for name, _detail in dinos:
            out.append(make_question(
                tier=2,
                topic_cell="evolution",
                strategy="dinosaur_period_attribution",
                pillar="evolution",
                question=f"{name} lived during which Mesozoic period?",
                answer=period,
                distractors=other_periods + ["Permian"],
                context=f"{name} is a {period}-period dinosaur. The Mesozoic = Triassic (252-201M) → Jurassic (201-145M) → Cretaceous (145-66M).",
            ))
    return out


# ----- Mythological figure → Tradition -----
MYTH_ANIMALS = [
    ("Anubis", "Egyptian", "Jackal-headed god of embalming and the afterlife."),
    ("Bastet", "Egyptian", "Cat-headed goddess of home and protection."),
    ("Horus", "Egyptian", "Falcon-headed sky god; symbol of kingship."),
    ("Sobek", "Egyptian", "Crocodile-headed Nile god."),
    ("Sekhmet", "Egyptian", "Lioness-headed goddess of war and healing."),
    ("Thoth", "Egyptian", "Ibis-headed god of wisdom and writing."),
    ("Pegasus", "Greek", "Winged horse born from Medusa's blood."),
    ("Cerberus", "Greek", "Three-headed guard dog of Hades."),
    ("Minotaur", "Greek", "Bull-headed creature in the Cretan labyrinth."),
    ("Centaur", "Greek", "Half-human, half-horse creature."),
    ("Sleipnir", "Norse", "Odin's eight-legged horse."),
    ("Fenrir", "Norse", "Giant wolf, son of Loki, bound until Ragnarok."),
    ("Jormungandr", "Norse", "World serpent encircling Midgard."),
    ("Hanuman", "Hindu", "Monkey-faced god of strength and devotion."),
    ("Ganesha", "Hindu", "Elephant-headed remover of obstacles."),
    ("Nandi", "Hindu", "Shiva's bull mount, guardian of temples."),
    ("Garuda", "Hindu", "Vishnu's eagle mount, enemy of serpents."),
    ("Thunderbird", "Native American", "Supernatural bird; thunder from wing beats."),
    ("Quetzalcoatl", "Mesoamerican", "Feathered serpent god of Mesoamerica."),
    ("Phoenix", "Greek/Egyptian", "Mythical bird that resurrects from its ashes."),
]


def generate_mythological_figure_tradition() -> list[dict]:
    """T2-T3: mythological figure → which religious tradition."""
    out = []
    traditions = sorted({t for _, t, _ in MYTH_ANIMALS})

    for name, tradition, desc in MYTH_ANIMALS:
        distractors = pick_length_balanced_distractors(
            tradition, [t for t in traditions if t != tradition], k=3
        )
        if distractors is None:
            continue
        out.append(make_question(
            tier=2,
            topic_cell="culture",
            strategy="mythological_figure_tradition",
            pillar="culture",
            question=f"{name} appears in which tradition's mythology?",
            answer=tradition,
            distractors=distractors,
            context=desc,
        ))
    return out


# ----- Famous animal → owner/event -----
FAMOUS_ANIMALS = [
    ("Bucephalus", "Alexander the Great", "Alexander tamed Bucephalus at age 12 by noticing the horse feared its own shadow."),
    ("Incitatus", "Caligula", "Roman emperor Caligula's horse — fed gold-flecked oats; rumor of consul appointment."),
    ("Marengo", "Napoleon", "Napoleon's Arabian stallion; carried him at Marengo, Austerlitz, Waterloo."),
    ("Bo", "Barack Obama", "Portuguese Water Dog, first family dog in Obama White House."),
    ("Sergeant Stubby", "Robert Conroy", "Most decorated dog of WWI; 17 engagements with 102nd Infantry."),
    ("Cher Ami", "US Army Signal Corps", "Carrier pigeon, WWI, saved 194 men of Lost Battalion."),
    ("Laika", "Soviet Union", "First living being in orbit (Sputnik 2, Nov 1957); died within hours."),
    ("Hachiko", "Hidesaburo Ueno", "Akita waited 9 years at Shibuya Station after his master's death (1925-1935)."),
    ("Balto", "Gunnar Kaasen", "Sled dog led final leg of 1925 diphtheria serum run to Nome, Alaska."),
    ("Togo", "Leonhard Seppala", "Sled dog covered longest stretch (261 mi) of 1925 serum run to Nome."),
    ("Wojtek", "Polish 22nd Artillery", "Syrian brown bear officially enlisted; carried shells at Monte Cassino 1944."),
    ("Smoky", "Bill Wynne", "4-lb Yorkie pulled communication wire through 70-ft conduit in WWII Pacific."),
    ("Trigger", "Roy Rogers", "Palomino stallion called 'smartest horse in the movies'."),
    ("Secretariat", "Penny Chenery", "1973 Triple Crown winner; won Belmont by 31 lengths."),
    ("Mister Ed", "Allan Lane", "Palomino who 'talked' in the 1960s American sitcom."),
]


def generate_famous_animal_owner() -> list[dict]:
    """T2-T3: famous animal → owner / commanding figure."""
    out = []
    owners = sorted({o for _, o, _ in FAMOUS_ANIMALS})

    for name, owner, desc in FAMOUS_ANIMALS:
        distractors = pick_length_balanced_distractors(
            owner, [o for o in owners if o != owner], k=3
        )
        if distractors is None:
            continue
        out.append(make_question(
            tier=2,
            topic_cell="culture",
            strategy="famous_animal_owner",
            pillar="culture",
            question=f"{name} was famously the animal of:",
            answer=owner,
            distractors=distractors,
            context=desc,
        ))
    return out


# ----- Extinct animal → year of extinction -----
EXTINCTIONS = [
    ("Dodo", "1681", "Mauritius — sailors, dogs, pigs; flightless + fearless."),
    ("Great auk", "1844", "Last pair killed on Eldey Island, Iceland; for museum specimens."),
    ("Passenger pigeon", "1914", "Martha died September 1, 1914 at Cincinnati Zoo, age ~29."),
    ("Carolina parakeet", "1918", "Incas died at Cincinnati Zoo; only North American native parrot."),
    ("Thylacine", "1936", "Benjamin died September 7, 1936 at Hobart Zoo; sheep-killing reputation."),
    ("Steller's sea cow", "1768", "Extinct only 27 years after Georg Steller described them (1741)."),
    ("Quagga", "1883", "Last died Amsterdam Zoo; subspecies of plains zebra; hunted to extinction."),
    ("Western black rhino", "2011", "Declared extinct 2011 — poaching for horn."),
    ("Heath hen", "1932", "Last male 'Booming Ben' died Martha's Vineyard; eastern prairie chicken."),
    ("Pyrenean ibex", "2000", "Last died January 2000; later cloned but offspring died within minutes."),
    ("Tasmanian emu", "1865", "Mainland Tasmanian subspecies; hunted out."),
    ("Bali tiger", "1937", "Last shot at Sumbar Kima 1937; Panthera tigris balica subspecies."),
    ("Javan tiger", "1976", "Last reliable sighting 1976; Panthera tigris sondaica subspecies."),
]


def generate_extinct_animal_year() -> list[dict]:
    """T2-T3: extinct animal → year of last individual."""
    out = []
    years = sorted({y for _, y, _ in EXTINCTIONS})

    for name, year, desc in EXTINCTIONS:
        distractors = pick_length_balanced_distractors(
            year, [y for y in years if y != year], k=3
        )
        if distractors is None:
            continue
        out.append(make_question(
            tier=3,
            topic_cell="hunting",
            strategy="famous_extinctions",
            pillar="hunting",
            question=f"The {name} was driven to extinction by what year?",
            answer=year,
            distractors=distractors,
            context=desc,
        ))
    return out


# ----- Cattle breed → origin -----
CATTLE_BREEDS = [
    ("Angus", "Scotland", "Black, polled; most popular US beef breed."),
    ("Hereford", "England", "White face, red body; foundational US ranching breed."),
    ("Jersey", "Channel Islands", "Small, fawn-colored; highest butterfat in milk."),
    ("Holstein", "Netherlands", "Black-and-white from Friesland; most productive dairy."),
    ("Wagyu", "Japan", "Marbled beef breed; Tajima bloodline."),
    ("Brahman", "India", "Humped, heat-tolerant; key in southern US ranching."),
    ("Charolais", "France", "White, large-framed; major beef breed."),
    ("Simmental", "Switzerland", "Red-and-white; dual-purpose beef and dairy."),
    ("Limousin", "France", "Red-coated; lean beef breed."),
    ("Texas Longhorn", "Spain", "Spanish Andalusian descent; iconic American."),
    ("Galloway", "Scotland", "Black, polled, hardy; double-coated."),
    ("Highland", "Scotland", "Shaggy hair, long horns; hardy Scottish breed."),
]


def generate_cattle_breed_origin() -> list[dict]:
    """T2: cattle breed → country of origin."""
    out = []
    origins = sorted({o for _, o, _ in CATTLE_BREEDS})

    for breed, origin, desc in CATTLE_BREEDS:
        distractors = pick_length_balanced_distractors(
            origin, [o for o in origins if o != origin], k=3
        )
        if distractors is None:
            continue
        out.append(make_question(
            tier=2,
            topic_cell="husbandry",
            strategy="cattle_breed_origin",
            pillar="husbandry",
            question=f"The {breed} cattle breed originated in:",
            answer=origin,
            distractors=distractors,
            context=desc,
        ))
    return out


# ----- Dog breed → group / origin -----
DOG_BREEDS = [
    ("Border Collie", "Herding", "Most intelligent breed per Stanley Coren; herds via 'eye'."),
    ("German Shepherd", "Herding", "Max von Stephanitz 1899; police + military + service."),
    ("Belgian Malinois", "Herding", "Most common modern US military working dog."),
    ("Siberian Husky", "Working", "Chukchi origin; sled racing; thick double coat."),
    ("Labrador Retriever", "Sporting", "Long-time most popular AKC breed (until 2022)."),
    ("Golden Retriever", "Sporting", "Scottish breed; iconic family dog."),
    ("Beagle", "Hound", "Scent hound; English origin; hunting rabbits."),
    ("Greyhound", "Hound", "Fastest dog breed; ancient Egyptian + Greek origin."),
    ("Dachshund", "Hound", "German 'badger dog'; bred to enter setts."),
    ("Yorkshire Terrier", "Toy", "English origin; ratters then companion dogs."),
    ("Chihuahua", "Toy", "Mexican origin; smallest dog breed."),
    ("Pug", "Toy", "Chinese origin; brachycephalic concerns."),
    ("Rottweiler", "Working", "Roman drover-dog descent; German butcher's dog."),
    ("Saint Bernard", "Working", "Swiss Great St. Bernard Pass monks; avalanche rescue."),
    ("Great Pyrenees", "Working", "Pyrenees mountains; livestock guardian dog."),
    ("Bulldog", "Non-Sporting", "English origin; bull-baiting history; brachycephalic."),
    ("Poodle", "Non-Sporting", "German origin; water retriever; intelligent."),
    ("Akita", "Working", "Japanese origin; Hachiko was an Akita."),
    ("Shiba Inu", "Non-Sporting", "Japanese; fox-like; oldest native Japanese breed."),
    ("Australian Shepherd", "Herding", "Despite name, developed in American West."),
]


def generate_dog_breed_group() -> list[dict]:
    """T2: dog breed → AKC group."""
    out = []
    groups = sorted({g for _, g, _ in DOG_BREEDS})

    for breed, group, desc in DOG_BREEDS:
        distractors = pick_length_balanced_distractors(
            group, [g for g in groups if g != group], k=3
        )
        if distractors is None:
            continue
        out.append(make_question(
            tier=2,
            topic_cell="husbandry",
            strategy="dog_groups_akc",
            pillar="husbandry",
            question=f"{breed} is classified in which AKC group?",
            answer=group,
            distractors=distractors,
            context=desc,
        ))
    return out


def generate_all_attribution() -> list[dict]:
    out = []
    out.extend(generate_vertebrate_class_attribution())
    out.extend(generate_dinosaur_period())
    out.extend(generate_mythological_figure_tradition())
    out.extend(generate_famous_animal_owner())
    out.extend(generate_extinct_animal_year())
    out.extend(generate_cattle_breed_origin())
    out.extend(generate_dog_breed_group())
    return out


if __name__ == "__main__":
    qs = generate_all_attribution()
    print(f"Generated {len(qs)} attribution questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
    print("By tier:", dict(Counter(q["tier"] for q in qs)))
    print("By pillar:", dict(Counter(q["_meta"]["strategy_pillar"] for q in qs)))
