"""Loanword attribution — word → language of origin.
Pillar 3 (etymology).
"""
from __future__ import annotations

from tools.quizgen.grammar_generators.common import make_question


# (word, language_of_origin, brief_context)
LOANWORDS = [
    ("Robot", "Czech", "From Karel Čapek's 1920 play R.U.R.; Czech *robota* = 'forced labor'."),
    ("Pajamas", "Persian/Hindi", "From Persian *pāy-jāma* (leg garment); entered English via colonial India."),
    ("Shampoo", "Hindi", "From Hindi *chāmpo* meaning 'to massage'."),
    ("Bungalow", "Hindi/Bengali", "From Bengali *bāṅglā* (in the style of Bengal)."),
    ("Jungle", "Hindi", "From Hindi/Sanskrit *jaṅgala* (wild, forested)."),
    ("Loot", "Hindi", "From Hindi *lūṭ* (plunder)."),
    ("Thug", "Hindi", "From Hindi *thag* (cheat, swindler)."),
    ("Guru", "Sanskrit", "Sanskrit *guru* = teacher, weight, heavy."),
    ("Bandana", "Hindi", "From Hindi *bāndhnū* (tie-dye method)."),
    ("Ketchup", "Chinese (Hokkien)", "From Hokkien *kê-tsiap* (fermented fish sauce)."),
    ("Tea", "Chinese (Min)", "From Chinese Min dialect *tê*; vs. Mandarin *chá* (the other route gave us 'chai')."),
    ("Typhoon", "Chinese", "From Chinese *tài fēng* (great wind) — via Greek + Arabic influence."),
    ("Tofu", "Chinese", "From Chinese *dòufu*; entered via Japanese tōfu."),
    ("Tsunami", "Japanese", "From Japanese *tsu* (harbor) + *nami* (wave)."),
    ("Karaoke", "Japanese", "From Japanese *kara* (empty) + *oke* (orchestra)."),
    ("Tycoon", "Japanese", "From Japanese *taikun* (great prince); used for the shogun."),
    ("Honcho", "Japanese", "From Japanese *hancho* (squad leader)."),
    ("Emoji", "Japanese", "From Japanese *e* (picture) + *moji* (character)."),
    ("Sushi", "Japanese", "From Japanese *sushi*; original form *narezushi* used fermented rice."),
    ("Karate", "Japanese", "From Japanese *kara-te* (empty hand)."),
    ("Algebra", "Arabic", "From Arabic *al-jabr* (restoration); al-Khwarizmi's 825 AD text."),
    ("Alcohol", "Arabic", "From Arabic *al-kuḥl* (kohl, eye makeup powder); chemistry term came later."),
    ("Coffee", "Arabic", "From Arabic *qahwa* via Turkish *kahve*."),
    ("Sugar", "Arabic/Sanskrit", "Arabic *sukkar*; ultimately from Sanskrit *śarkarā*."),
    ("Magazine", "Arabic", "From Arabic *makhzan* (storehouse)."),
    ("Zenith", "Arabic", "From Arabic *samt* (path)."),
    ("Zero", "Arabic", "From Arabic *ṣifr* (empty)."),
    ("Cipher", "Arabic", "Same Arabic *ṣifr* root as 'zero'."),
    ("Boss", "Dutch", "From Dutch *baas* (master)."),
    ("Cookie", "Dutch", "From Dutch *koekje* (little cake)."),
    ("Yacht", "Dutch", "From Dutch *jacht* (hunting ship)."),
    ("Sketch", "Dutch", "From Dutch *schets*."),
    ("Caboose", "Dutch", "From Dutch *kabuis* (ship's cabin)."),
    ("Tomato", "Nahuatl", "From Nahuatl *tomatl* via Spanish."),
    ("Chocolate", "Nahuatl", "From Nahuatl *xocolātl*."),
    ("Coyote", "Nahuatl", "From Nahuatl *coyōtl*."),
    ("Avocado", "Nahuatl", "From Nahuatl *āhuacatl* (testicle, for shape)."),
    ("Hurricane", "Taíno", "From Taíno *huracán*, via Spanish."),
    ("Hammock", "Taíno", "From Taíno *hamaka*."),
    ("Barbecue", "Taíno", "From Taíno *barbacoa* (wooden grill)."),
    ("Canoe", "Carib", "From Carib *kana:wa* via Spanish."),
    ("Moose", "Algonquian", "From Algonquian *mooz* (he strips off)."),
    ("Raccoon", "Powhatan", "From Powhatan *arahkun* (he scratches with hands)."),
    ("Skunk", "Algonquian", "From Algonquian *seganku*."),
    ("Squash", "Narragansett", "From Narragansett *askutasquash*."),
    ("Persimmon", "Powhatan", "From Powhatan *pessamin*."),
    ("Lemon", "Persian", "Via Arabic *laymūn* from Persian *līmū*."),
    ("Paradise", "Persian", "From Old Persian *pairi-daēza* (enclosed garden)."),
    ("Bazaar", "Persian", "Persian *bāzār* (marketplace)."),
    ("Caravan", "Persian", "From Persian *kārwān*."),
    ("Sauna", "Finnish", "From Finnish — only Finnish word that entered global English."),
    ("Trek", "Afrikaans", "From Afrikaans *trek* (journey by ox-wagon)."),
    ("Aardvark", "Afrikaans", "Afrikaans *aardvark* (earth-pig)."),
    ("Banana", "Wolof", "From Wolof (West Africa) via Portuguese."),
    ("Safari", "Swahili", "From Swahili *safari* (journey), from Arabic root."),
    ("Sushi", "Japanese", "Already listed but a key example."),
    ("Polka", "Czech", "Czech dance — from Czech *půlka* (half-step) or Polish *polska* (Polish)."),
    ("Pistol", "Czech", "Possibly from Czech *píšťala* (pipe, whistle)."),
    ("Bohemian", "Czech", "From Bohemia region; the 'unconventional artist' sense developed in 19th-c France."),
]


def generate_loanword_origins() -> list[dict]:
    """T2-T3: loanword → language of origin."""
    out = []
    # All language names for distractor pool
    all_origins = sorted({lang for _, lang, _ in LOANWORDS})

    for word, origin, ctx in LOANWORDS:
        distractors = [o for o in all_origins if o != origin][:3]
        out.append(make_question(
            tier=2,
            topic_cell="etymology",
            strategy="loanword_origin",
            pillar="etymology",
            question=f"The English word '{word}' comes from which language?",
            answer=origin,
            distractors=distractors,
            context=ctx,
        ))
    return out


def generate_all_loanwords() -> list[dict]:
    return generate_loanword_origins()


if __name__ == "__main__":
    qs = generate_all_loanwords()
    print(f"Generated {len(qs)} loanword questions")
