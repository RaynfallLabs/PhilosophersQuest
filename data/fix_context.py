"""Fix sample context to match actual questions."""
import sys; sys.path.insert(0, 'src')
import json
from paths import data_path

MATCHED = {
    'math': {
        "2 x 2 = ?": "Multiplication is repeated addition. 2 x 2 means adding 2 twice: 2 + 2 = 4. Multiplication is one of the four fundamental operations in math, and the times tables are the building blocks for algebra, geometry, and beyond.",
        "2 x 3 = ?": "2 x 3 means two groups of three, or 3 + 3 = 6. You can also think of it as three groups of two: 2 + 2 + 2 = 6. Multiplication is commutative -- the order doesn't matter, the answer is the same.",
        "2 x 4 = ?": "2 x 4 = 8. A quick way to multiply by 2 is to double the number: double 4 is 8. Doubling is one of the oldest mental math tricks, used by ancient Egyptian scribes to perform all their calculations.",
        "2 x 5 = ?": "2 x 5 = 10. Multiplying by 5 always gives a number ending in 0 or 5. This is because 5 is half of 10, our number base -- so two fives make a complete ten.",
        "2 x 6 = ?": "2 x 6 = 12. There are 12 inches in a foot, 12 months in a year, and 12 hours on a clock face. The number 12 is special because it divides evenly by 1, 2, 3, 4, and 6 -- making it useful for splitting things into equal groups.",
    },
    'geography': {
        "Capital of France?": "Paris has been the capital of France since the 10th century. It sits on the River Seine and is home to the Eiffel Tower, the Louvre Museum, and Notre-Dame Cathedral. With over 2 million residents, it is one of Europe's most important cultural and economic centers.",
        "Capital of the United States?": "Washington, D.C. was established as the capital in 1790 as a compromise between northern and southern states. The 'D.C.' stands for District of Columbia -- it's not part of any state. The city was designed by Pierre Charles L'Enfant and named after George Washington.",
        "Capital of Japan?": "Tokyo, meaning 'Eastern Capital,' became Japan's capital in 1868 when the emperor moved there from Kyoto. Greater Tokyo is the most populous metropolitan area on Earth, with over 37 million people.",
        "Capital of Germany?": "Berlin became Germany's capital when the country unified in 1871. Divided by the Berlin Wall from 1961 to 1989 during the Cold War, the city's reunification became a symbol of freedom worldwide.",
        "Capital of the United Kingdom?": "London has been England's capital for nearly a thousand years, since William the Conqueror built the Tower of London in 1066. It sits on the River Thames and was the center of the British Empire.",
    },
    'science': {
        "Water is made of hydrogen and ___?": "Water (H2O) is two hydrogen atoms bonded to one oxygen atom. It is the only common substance found naturally in all three states: solid (ice), liquid (water), and gas (steam). Water is essential for all known life.",
        "Gravity pulls objects toward Earth because of Earth's ___?": "Mass is the amount of matter in an object, and gravity is the force of attraction between masses. The more massive an object, the stronger its gravitational pull. Earth's mass is what keeps us on the ground and the Moon in orbit.",
        "The Sun produces energy through nuclear fusion, which means it converts ___ into helium?": "The Sun fuses hydrogen atoms into helium at its core, where temperatures reach 15 million degrees Celsius. This nuclear fusion releases enormous energy -- the Sun converts about 600 million tons of hydrogen every second.",
        "What organ pumps blood through the body?": "The human heart beats about 100,000 times per day, pumping roughly 7,500 liters of blood. It has four chambers and the blood it circulates delivers oxygen and nutrients to every cell in your body.",
        "Plants make food using sunlight in a process called ___?": "Photosynthesis converts sunlight, water, and carbon dioxide into glucose and oxygen. The green pigment chlorophyll in plant leaves captures light energy. Almost all life on Earth depends on photosynthesis.",
    },
    'history': {
        "George Washington's decision to step down after two terms established what crucial precedent?": "George Washington voluntarily gave up power after two terms as president (1789-1797), setting a precedent that lasted until Franklin Roosevelt broke it in 1940. His restraint helped establish American democracy as a system of laws, not rulers.",
        "The Declaration of Independence grounded the colonists' right to revolt in ___?": "Thomas Jefferson drew on Enlightenment philosophy -- especially John Locke -- to argue that governments derive authority from the consent of the governed. When a government violates the people's rights, the people may alter or abolish it.",
        "Christopher Columbus's 1492 voyage had what immediate consequence for Europe?": "Columbus's arrival in the Caribbean began the Columbian Exchange -- a massive transfer of plants, animals, diseases, and cultures between the Old and New Worlds. Europe gained potatoes, tomatoes, and corn; the Americas received horses and wheat.",
        "The Emancipation Proclamation was significant primarily because it ___?": "Lincoln issued the Emancipation Proclamation on January 1, 1863, declaring enslaved people in Confederate states 'forever free.' It transformed the Civil War from a fight to preserve the Union into a moral crusade against slavery.",
        "Napoleon's rise to power after the French Revolution illustrated what historical pattern?": "Napoleon seized power in 1799, just ten years after the Revolution promised liberty, equality, and fraternity. This pattern -- revolution producing a new strongman -- has repeated throughout history. Destroying a system is easier than building a better one.",
    },
    'philosophy': {
        "Who is known as the 'Father of Western Philosophy'?": "Socrates (469-399 BC) never wrote a single word -- everything we know comes from his students, especially Plato. He wandered Athens asking questions that exposed contradictions in people's beliefs, a technique now called the Socratic Method.",
        "Who was the tutor of Alexander the Great?": "Aristotle tutored the young Alexander from age 13 to 16 in Macedonia. He taught him philosophy, science, medicine, and literature. Alexander went on to conquer most of the known world by age 30, spreading Greek culture across three continents.",
        "Confucius taught that social harmony flows from proper roles within family and society. What is the term for this Confucian concept of correct role-fulfillment?": "Li encompasses ritual propriety, correct behavior, and fulfilling one's social role. Confucius believed that if everyone performed their role with sincerity and respect, society would be harmonious. This idea shaped Chinese civilization for over 2,500 years.",
        "What was Socrates's most famous philosophical claim?": "Socrates's claim 'I know that I know nothing' was his way of saying that true wisdom begins with recognizing the limits of your own knowledge. The Oracle at Delphi declared him the wisest man in Athens -- because he alone understood how much he didn't know.",
        "Which philosopher tutored Alexander the Great?": "Aristotle (384-322 BC) was one of the most influential thinkers in history. He wrote on logic, biology, physics, ethics, politics, and poetry. His systematic approach to knowledge essentially invented the scientific method.",
    },
}

for subj, contexts in MATCHED.items():
    path = data_path('data', 'questions', f'{subj}.json')
    with open(path, encoding='utf-8') as f:
        qs = json.load(f)

    applied = 0
    for q in qs:
        q.pop('context', None)
        ctx = contexts.get(q['question'])
        if ctx:
            q['context'] = ctx
            applied += 1

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(qs, f, indent=2, ensure_ascii=False)
    print(f"  {subj}: {applied} matched contexts")

print("\nDone")
