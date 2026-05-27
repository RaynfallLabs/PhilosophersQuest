"""Hand-written weasel-v2 fixes for animal (4) + cooking (5).

Each rewrite replaces the meta-question closer with a pointed concrete
one. Story-in-stem substance preserved.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402

ANIMAL_FIXES = [
    # bank#122 T5: Egyptian vulture rock-on-egg
    {
        "bank_idx": 122,
        "new": {
            "tier": 5,
            "question": "Researchers documented an Egyptian vulture in Bulgaria flying with a rock in its beak across a kilometer of open ground, then dropping the rock on an unattended ostrich egg in a zoo enclosure. The bird had never been observed using a tool before. How could this novel behavior spread to other birds in the population?",
            "answer": "By one bird inventing it, then nearby birds copying it after watching, like a culture spreading ideas",
            "choices": [
                "By one bird inventing it, then nearby birds copying it after watching, like a culture spreading ideas",
                "Only through inherited genes, so the offspring of this vulture will be the only ones to ever do this",
                "Through cosmic-ray induced random mutations affecting only the brains of birds in that specific zoo",
                "Through magnetic alignment with the Earth's polar field, which forces vultures to drop objects daily",
            ],
            "context": "The behavior is documented in Van Lawick-Goodall + Van Lawick 1966 *Use of tools by the Egyptian vulture*. Social transmission of foraging innovations is observed across multiple bird groups — New Caledonian crows, Galapagos woodpecker finches, primates. The mechanism doesn't require genetic change; it requires brains that learn from watching.",
        },
    },
    # bank#350 T5: T. gondii parasite
    {
        "bank_idx": 350,
        "new": {
            "tier": 5,
            "question": "Toxoplasma gondii is a parasite that requires cats to complete its life cycle. Infected rodents lose their fear of cat odor — making them easier prey for cats, completing the parasite's cycle. Roughly a third of humans carry T. gondii antibodies. What kind of biological influence does the parasite exert on its rodent host?",
            "answer": "It manipulates the host's behavior in ways that help the parasite finish its life cycle",
            "choices": [
                "It manipulates the host's behavior in ways that help the parasite finish its life cycle",
                "It strengthens the rodent's immune defenses against cats, allowing escape from predation events",
                "It produces a chemical that kills cats on contact, eliminating the predator that threatens the rodent",
                "It has no effect on rodent behavior, since the cat-fear loss is purely coincidental observation",
            ],
            "context": "Behavior-manipulating parasites are well documented: Toxoplasma in rodents (Berdoy et al. 2000), Cordyceps fungi in insects, Leucochloridium in snails (eyestalk swelling), Spinochordodes hairworms forcing crickets into water. The human-toxoplasma link with behavioral or psychiatric effects (Flegr et al.) remains debated.",
        },
    },
    # bank#518 T3: dogs working not pets
    {
        "bank_idx": 518,
        "new": {
            "tier": 3,
            "question": "The vast majority of dogs in the world are not pets — they are working animals or semi-wild village dogs that earn their food. About 75-85% of the world's roughly 900 million dogs fall in that group. Which framing of the dog-human relationship does that statistic correct?",
            "answer": "Dogs evolved alongside humans as working partners, and the pet relationship is a recent minority",
            "choices": [
                "Dogs evolved alongside humans as working partners, and the pet relationship is a recent minority",
                "Dogs were domesticated only in the 1800s as Victorian show animals, and remain primarily pets globally",
                "Dogs are not domesticated at all in the genetic sense and most are still genuinely wild animals",
                "Dogs were domesticated independently by every culture in identical processes and outcomes worldwide",
            ],
            "context": "Coppinger & Coppinger *Dogs* (2001) made the village-dog argument central to canine biology. The pet relationship dates mostly to the 19th-20th century industrial cities; for most of dog-human history, dogs hunted, guarded, herded, hauled, or scavenged at human settlements.",
        },
    },
    # bank#893 T3: chytrid fungus + Xenopus
    {
        "bank_idx": 893,
        "new": {
            "tier": 3,
            "question": "The chytrid fungus probably spread globally via the international amphibian pet trade and African clawed frogs (Xenopus) shipped worldwide as lab animals or pregnancy tests. How does the chytrid story explain modern amphibian die-offs across continents?",
            "answer": "Global animal shipping moves pathogens to populations that have no immunity, causing catastrophic spread",
            "choices": [
                "Global animal shipping moves pathogens to populations that have no immunity, causing catastrophic spread",
                "Frogs everywhere developed the same allergy to humans simultaneously due to environmental toxins",
                "Climate change alone explains every die-off, with no role for human animal-movement networks",
                "The fungus was a deliberate WHO release for biological pest control, then accidentally escaped",
            ],
            "context": "Batrachochytrium dendrobatidis (Bd) has driven declines in over 500 amphibian species (Scheele et al., *Science*, 2019). Xenopus carry Bd asymptomatically and were exported worldwide for the Hogben pregnancy test (1930s-1960s). The pet-trade vector and African-clawed-frog hypothesis are the leading explanations.",
        },
    },
]


COOKING_FIXES = [
    # bank#589 T5: Edmond Albius hand-pollination
    {
        "bank_idx": 589,
        "new": {
            "tier": 5,
            "question": "Vanilla planifolia outside Mexico was sterile until 1841, when a 12-year-old enslaved gardener on Réunion named Edmond Albius devised hand-pollination. What specific physical block in the orchid's anatomy was Albius bypassing with his bamboo splint?",
            "answer": "The rostellum membrane that separates the orchid's male and female parts, preventing self-pollination",
            "choices": [
                "The rostellum membrane that separates the orchid's male and female parts, preventing self-pollination",
                "A thick wax layer on the petals that prevents bees from landing and reaching the flower at all",
                "The roots' allergic reaction to local Réunion soil, which Albius treated with sugar-cane fertilizer",
                "An invisible electric field around the flower that only stopped working at certain phases of the moon",
            ],
            "context": "Albius's technique remains the foundation of all commercial vanilla cultivation outside the Melipona-bee range of Central America. His method is barbaric history (he was enslaved and never freed) and brilliant botany — pressing anther directly to stigma with a thin tool, lifting the rostellum out of the way. Réunion became the world's largest vanilla producer.",
        },
    },
    # bank#594 T5: garum / colatura survival
    {
        "bank_idx": 594,
        "new": {
            "tier": 5,
            "question": "Roman garum survived as a high-volume industry through Late Antiquity. After Rome's collapse, the technique disappeared from most of Western Europe — but survived in one Italian village. What is the surviving sauce called, and what kept the technique alive?",
            "answer": "Colatura di alici of Cetara — preserved by Amalfi-coast fishing villages and nearby Benedictine monasteries",
            "choices": [
                "Colatura di alici of Cetara — preserved by Amalfi-coast fishing villages and nearby Benedictine monasteries",
                "Garum di Roma — preserved by the Vatican as a sacramental sauce never made outside Vatican walls",
                "Salsa romana — preserved by the Italian state under a single licensed factory in Bologna for centuries",
                "Anchovy paste — invented from scratch by Heinz in 1869 and unrelated to any Roman fish-sauce tradition",
            ],
            "context": "Colatura di alici is barrel-fermented anchovy liquid chemically close to ancient garum (Curtis 1991 *Garum and Salsamenta*). Cetara's fishermen and the Tre Calli monks kept the practice alive through the medieval gap. The sauce is now protected under Italian PAT designation.",
        },
    },
    # bank#602 T5: Boston Tea Party
    {
        "bank_idx": 602,
        "new": {
            "tier": 5,
            "question": "The Boston Tea Party destroyed 92,000 pounds of Bohea black tea over a constitutional dispute. Why was tea — an everyday beverage — an effective lightning rod for protests that abstract tax debates would not have been?",
            "answer": "A mass-consumption daily commodity makes constitutional questions concrete and the protest visible to everyone",
            "choices": [
                "A mass-consumption daily commodity makes constitutional questions concrete and the protest visible to everyone",
                "Tea was the only legal product to destroy in colonial law, so protesters had no other option for protest",
                "Tea contained a sedative the British put in to keep colonists passive, making it the natural protest target",
                "Tea was so expensive that destroying it punished British merchants but cost the colonists nothing at all",
            ],
            "context": "The Tea Act 1773 actually reduced the price of tea (the East India Company got a monopoly). Colonists destroyed it anyway because the issue was 'no taxation without representation' — the principle, not the price. The Tea Party's daily-object framing made the constitutional question visible in every household.",
        },
    },
    # bank#689 T4: Pemmican Proclamation 1814
    {
        "bank_idx": 689,
        "new": {
            "tier": 4,
            "question": "Native American pemmican — dried lean meat pounded fine, mixed with rendered fat and berries — was the energy bar of the fur trade for 200 years. The 1814 Pemmican Proclamation banned its export from Red River. Why would a colonial governor ban a food's export?",
            "answer": "Pemmican was strategic infrastructure, since controlling it controlled who could move freight across North America",
            "choices": [
                "Pemmican was strategic infrastructure, since controlling it controlled who could move freight across North America",
                "Pemmican was a religious object for Métis settlers and the governor wanted to suppress their worship widely",
                "Pemmican was banned to protect bison populations from over-hunting by Native American Indians directly",
                "Pemmican was banned because it caused food poisoning outbreaks in colonial settlements during 1814 winter",
            ],
            "context": "Hudson's Bay Company governor Miles Macdonell issued the 1814 Pemmican Proclamation to starve out the rival North West Company's voyageur brigades. The Métis defied it; the conflict escalated to the Seven Oaks confrontation (1816). Pemmican's role in continental logistics is comparable to fuel depots in modern military supply chains.",
        },
    },
    # bank#889 T2: Lyon mâchon tradition
    {
        "bank_idx": 889,
        "new": {
            "tier": 2,
            "question": "A Lyonnaise cook splits a winter morning between charcuterie shops and tiny bistros, eating small dishes and drinking Beaujolais before noon. The tradition has a name. What is it called, and what kind of food does it feature?",
            "answer": "Mâchon, Lyon's morning meal tradition for workers, centered on hearty charcuterie dishes",
            "choices": [
                "Mâchon, Lyon's morning meal tradition for workers, centered on hearty charcuterie dishes",
                "Brunch lyonnais, a postwar copy of the American Sunday brunch with eggs and pancakes added",
                "Apéritif royal, Louis XIV's invention of a morning food court for the visiting French aristocracy",
                "Petit-déjeuner standard, France's identical-everywhere morning meal originating in Lyon's bakery",
            ],
            "context": "Mâchon is a Lyon working-class tradition — a hearty mid-morning meal of charcuterie (saucisson, andouillette, sabodet), often with a glass of Beaujolais. The bouchons (small Lyonnaise restaurants) preserve the tradition. The word 'mâchon' comes from 'mâcher,' to chew.",
        },
    },
]


bank_paths = {
    "animal": Path("data/questions/animal.json"),
    "cooking": Path("data/questions/cooking.json"),
}

for subject, fixes in [("animal", ANIMAL_FIXES), ("cooking", COOKING_FIXES)]:
    bank = json.loads(bank_paths[subject].read_text(encoding="utf-8"))
    dup, ans = build_bank_indices(bank)
    for fix in fixes:
        idx = fix["bank_idx"]
        new_q = fix["new"]
        r = validate_rewrite(subject, new_q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
        status = "PASS" if r["verdict"] != "FAIL" else "FAIL"
        print(f"{subject} bank#{idx}: {status}")
        if r["verdict"] == "FAIL":
            for g, reason in r["hard_fails"][:3]:
                print(f"    {g}: {reason}")

# Write the patches
Path("_weasel_v2_fix_animal.json").write_text(json.dumps(ANIMAL_FIXES, indent=2, ensure_ascii=False), encoding="utf-8")
Path("_weasel_v2_fix_cooking.json").write_text(json.dumps(COOKING_FIXES, indent=2, ensure_ascii=False), encoding="utf-8")
print()
print("Wrote _weasel_v2_fix_animal.json + _weasel_v2_fix_cooking.json")
