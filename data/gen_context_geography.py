#!/usr/bin/env python3
"""Add context strings to geography questions that are missing them.

Run:  python data/gen_context_geography.py
"""

import json, pathlib

SRC = pathlib.Path(__file__).resolve().parent / "questions" / "geography.json"

# ── question text  →  context string ──────────────────────────────────────────
CONTEXTS: dict[str, str] = {

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — World Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of China?":
        "Beijing, meaning 'Northern Capital,' has served as China's political center for most of the last 800 years. The Forbidden City at its heart housed 24 emperors across two dynasties and contains 9,999 rooms.",

    "Capital of Russia?":
        "Moscow has been Russia's capital since 1918 when the Bolsheviks moved it from St. Petersburg. The Kremlin, a medieval fortress at its center, is the world's largest active fortress and seat of Russian power.",

    "Capital of Brazil?":
        "Brasilia was built from scratch in just 41 months (1956-1960) in the country's interior to spur inland development. Seen from above, the city's layout resembles an airplane or bird in flight.",

    "Capital of India?":
        "New Delhi was designed by British architects Edwin Lutyens and Herbert Baker and inaugurated in 1931 to replace Calcutta as the colonial capital. It sits adjacent to Old Delhi, which served as the Mughal capital for centuries.",

    "Capital of Australia?":
        "Canberra was purpose-built as a compromise after Sydney and Melbourne both wanted to be the capital. The name likely comes from an Aboriginal word meaning 'meeting place.'",

    "Capital of Canada?":
        "Ottawa was chosen as capital in 1857 by Queen Victoria, partly because it sat on the border of English-speaking Ontario and French-speaking Quebec. It was also far enough from the US border to be defensible.",

    "Capital of Mexico?":
        "Mexico City was built on the ruins of Tenochtitlan, the Aztec capital that amazed Spanish conquistadors with its canals and floating gardens. At 2,240 meters elevation, it is one of the highest major cities in the world.",

    "Capital of Italy?":
        "Rome was the center of the Roman Empire for over 500 years and remains home to the Vatican, the world's smallest independent state. The saying 'All roads lead to Rome' dates back to the empire's vast road network.",

    "Capital of Spain?":
        "Madrid sits almost exactly at the geographic center of the Iberian Peninsula, which is why Philip II chose it as Spain's capital in 1561. At 650 meters elevation, it is one of Europe's highest capitals.",

    "Capital of Egypt?":
        "Cairo, the largest city in Africa and the Middle East, sits near the ancient capital of Memphis and the Giza pyramids. Its Arabic name, al-Qahirah, means 'The Victorious.'",

    "Capital of Nigeria?":
        "Abuja replaced Lagos as Nigeria's capital in 1991 because it was centrally located and ethnically neutral territory. Lagos, still the country's largest city, remains the economic powerhouse.",

    "Capital of South Africa (executive)?":
        "South Africa uniquely has three capitals: Pretoria (executive), Cape Town (legislative), and Bloemfontein (judicial). This arrangement was a compromise when the Union of South Africa formed in 1910.",

    "Capital of Argentina?":
        "Buenos Aires, whose name means 'Fair Winds,' is sometimes called the 'Paris of South America' for its European-style architecture. Nearly one-third of Argentina's population lives in its metropolitan area.",

    "Capital of South Korea?":
        "Seoul has been Korea's capital for over 600 years, since the Joseon Dynasty chose it in 1394. Its name simply means 'capital' in Korean. The city sits just 35 miles from the North Korean border.",

    "Capital of Saudi Arabia?":
        "Riyadh, meaning 'The Gardens,' was once a small oasis town before the House of Saud captured it in a daring 1902 raid with just 40 men. Today it is a sprawling metropolis of over 7 million people.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — Continents
    # ══════════════════════════════════════════════════════════════════════════

    "Which continent is Brazil on?":
        "Brazil occupies nearly half of South America's total land area. It is the only Portuguese-speaking country on the continent, surrounded by Spanish-speaking neighbors on every land border.",

    "Which continent is Japan on?":
        "Japan is an island nation off the east coast of Asia, separated from the mainland by the Sea of Japan. Despite being in Asia, its island isolation allowed it to develop a uniquely distinct culture.",

    "Which continent is Egypt on?":
        "Egypt sits in the northeastern corner of Africa, though the Sinai Peninsula technically extends into Asia. This position made it a crossroads of civilizations for thousands of years.",

    "Which continent is France on?":
        "France sits in Western Europe, bordered by the Atlantic Ocean, the Mediterranean Sea, and six countries. However, if you count overseas territories, France technically has land on five continents.",

    "Which continent is Australia on?":
        "Australia is both a country and the world's smallest continent, sometimes grouped with nearby Pacific islands as 'Oceania.' It is the only continent entirely in the Southern and Eastern Hemispheres.",

    "Which continent is Canada on?":
        "Canada occupies the northern portion of North America and is the second-largest country in the world by total area. It shares the world's longest international land border with the United States.",

    "Which continent is Russia mostly on?":
        "About 77% of Russia's territory lies in Asia (Siberia), though about 77% of its population lives in the European part west of the Ural Mountains. This makes it a transcontinental giant straddling two worlds.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — Oceans
    # ══════════════════════════════════════════════════════════════════════════

    "The largest ocean is the ___?":
        "The Pacific Ocean covers about 63 million square miles -- more than all of Earth's land area combined. Its name, given by Ferdinand Magellan in 1520, means 'peaceful,' though it hosts some of Earth's most violent typhoons.",

    "The second largest ocean is the ___?":
        "The Atlantic Ocean covers about 41 million square miles and is still growing wider by about 2.5 centimeters per year as tectonic plates drift apart along the Mid-Atlantic Ridge.",

    "The smallest ocean is the ___?":
        "The Arctic Ocean is the shallowest and coldest of all five oceans, and much of it stays frozen year-round. During summer, the North Pole sits on floating sea ice with no land beneath it.",

    "The ocean between Africa and Australia is the ___?":
        "The Indian Ocean is the warmest ocean in the world and was the first to be used as a major trade highway, connecting African, Arab, Indian, and Southeast Asian civilizations for millennia.",

    "The ocean surrounding Antarctica is the ___?":
        "The Southern Ocean was officially recognized as the fifth ocean in 2000 by the International Hydrographic Organization. It is defined by the Antarctic Circumpolar Current, the strongest ocean current on Earth.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — General Geography Facts
    # ══════════════════════════════════════════════════════════════════════════

    "The largest country by area is ___?":
        "Russia spans 11 time zones and covers over 17 million square kilometers, nearly twice the size of Canada, the second-largest country. It stretches from the Baltic Sea to the Pacific Ocean.",

    "The most populous country is ___?":
        "India surpassed China as the world's most populous country in 2023, with over 1.4 billion people. Its population is remarkably young, with a median age of about 28 years.",

    "The longest river in Africa is the ___?":
        "The Nile stretches approximately 6,650 kilometers from central Africa to the Mediterranean. Ancient Egyptians called it 'Iteru,' meaning 'great river,' and built their entire civilization around its annual floods.",

    "The tallest mountain in the world is ___?":
        "Mount Everest stands 8,849 meters above sea level and grows about 4 millimeters taller each year due to tectonic activity. The Tibetans call it Chomolungma, meaning 'Goddess Mother of the World.'",

    "Mount Everest is in which mountain range?":
        "The Himalayas stretch 2,400 kilometers across five countries and contain all 14 of the world's peaks above 8,000 meters. The range is still rising as the Indian tectonic plate pushes into Asia.",

    "The Amazon River is primarily in ___?":
        "The Amazon carries more water than the next seven largest rivers combined, discharging about 20% of all river water entering the oceans. During flood season, it can be 30 miles wide in places.",

    "The Sahara Desert is on which continent?":
        "The Sahara is roughly the size of the United States and covers about 25% of Africa. Remarkably, only about 25% of the Sahara is sand dunes -- most of it is rocky plateau and gravel plains.",

    "Which continent has the most countries?":
        "Africa has 54 recognized sovereign nations, more than any other continent. Many of its borders were drawn by European colonial powers at the 1884 Berlin Conference with little regard for ethnic or geographic boundaries.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — More World Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Turkey?":
        "Ankara replaced Istanbul as Turkey's capital in 1923 when Ataturk founded the modern republic. He chose this central Anatolian city to break from the Ottoman past and signal a new, inward-looking national identity.",

    "Capital of Greece?":
        "Athens is considered the cradle of Western civilization and the birthplace of democracy around 508 BC. The Parthenon atop the Acropolis has stood for nearly 2,500 years as a symbol of classical culture.",

    "Capital of Portugal?":
        "Lisbon was one of Europe's great Age of Exploration ports, launching Vasco da Gama's voyage to India in 1497. A massive earthquake in 1755 destroyed much of the city and reshaped Enlightenment philosophy.",

    "Capital of Poland?":
        "Warsaw was almost entirely destroyed during World War II -- about 85% of the city was reduced to rubble. Its historic Old Town was meticulously rebuilt from paintings and photographs and is now a UNESCO World Heritage Site.",

    "Capital of the Netherlands?":
        "Amsterdam was built on millions of wooden poles driven into marshy ground. The city has more canals than Venice and more bicycles than people, with an estimated 881,000 bikes for 873,000 residents.",

    "Capital of Sweden?":
        "Stockholm is built on 14 islands connected by 57 bridges where Lake Malaren meets the Baltic Sea. The Nobel Prize ceremony has been held here every December since 1901.",

    "Capital of Norway?":
        "Oslo sits at the head of a 100-kilometer fjord and is surrounded by forested hills. It was founded around 1040 AD by King Harald Hardrada and was known as Christiania from 1624 to 1925.",

    "Capital of Switzerland?":
        "Bern is technically not the 'capital' but the 'Federal City' of Switzerland -- the country has no official capital. Its medieval old town, built on a peninsula in the Aare River, is a UNESCO World Heritage Site.",

    "Capital of Austria?":
        "Vienna was the seat of the Habsburg Empire for over 600 years and the cultural capital of classical music, home to Mozart, Beethoven, Schubert, and Strauss. Its coffee house culture is UNESCO-recognized.",

    "Capital of Belgium?":
        "Brussels serves as the de facto capital of the European Union, hosting the European Commission and Council. The city is officially bilingual, split between French-speaking and Dutch-speaking communities.",

    "Capital of Israel?":
        "Jerusalem is considered holy by three major religions: Judaism, Christianity, and Islam. The Old City, barely one square kilometer, contains the Western Wall, the Church of the Holy Sepulchre, and the Dome of the Rock.",

    "Capital of Iran?":
        "Tehran sits at the foot of the Alborz Mountains and became Iran's capital in 1796 under the Qajar dynasty. It grew from a small village to a sprawling megacity of over 9 million people.",

    "Capital of Pakistan?":
        "Islamabad was purpose-built in the 1960s to replace Karachi as Pakistan's capital. Designed on a grid pattern by Greek architect Constantinos Doxiadis, its name means 'City of Islam.'",

    "Capital of Indonesia?":
        "Jakarta is sinking so rapidly -- up to 25 centimeters per year in some areas -- that Indonesia is building a new capital called Nusantara on the island of Borneo. Jakarta has been the capital since Dutch colonial times.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — Rivers, Coasts, and Features
    # ══════════════════════════════════════════════════════════════════════════

    "The Nile River flows into the ___?":
        "The Nile's delta where it meets the Mediterranean is one of the most fertile regions on Earth and has supported agriculture for over 5,000 years. The Greek letter delta was named after the shape of this very river mouth.",

    "The country with the longest coastline is ___?":
        "Canada's coastline stretches about 243,000 kilometers -- enough to circle the Earth six times. This includes the intricate coastlines of its Arctic archipelago, with thousands of islands and fjords.",

    "Which continent has no countries?":
        "Antarctica has no permanent human population and is governed by the Antarctic Treaty of 1959, which dedicates the continent to peaceful scientific research. About 70% of Earth's fresh water is locked in its ice sheet.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — More Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Kenya?":
        "Nairobi was founded in 1899 as a railway depot on the Uganda Railway and grew into East Africa's largest city. Its name comes from the Maasai phrase 'Enkare Nairobi,' meaning 'cool water.'",

    "Capital of Ukraine?":
        "Kyiv is one of Europe's oldest cities, founded in the 5th century. It was the center of Kyivan Rus, the medieval state that gave rise to Ukrainian, Russian, and Belarusian cultures.",

    "Capital of the Czech Republic?":
        "Prague's historic center survived both World Wars nearly untouched, giving it one of Europe's best-preserved collections of medieval, baroque, and art nouveau architecture. Its Charles Bridge dates to 1357.",

    "Capital of Hungary?":
        "Budapest was formed in 1873 by merging three cities: Buda and Obuda on the hilly west bank of the Danube with Pest on the flat east bank. The city sits atop the largest thermal water cave system in the world.",

    "Capital of Romania?":
        "Bucharest's Palace of Parliament, built by dictator Nicolae Ceausescu, is the world's heaviest building and second-largest administrative structure after the Pentagon. Building it required demolishing a fifth of the city center.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — Mountain Ranges
    # ══════════════════════════════════════════════════════════════════════════

    "The Andes Mountains are on which continent?":
        "The Andes are the world's longest continental mountain range at 7,000 kilometers, running the entire western edge of South America. They were home to the Inca Empire, the largest empire in pre-Columbian America.",

    "The Rocky Mountains are on which continent?":
        "The Rockies stretch about 4,800 kilometers from British Columbia to New Mexico. They form the Continental Divide, where rivers on one side flow to the Pacific and on the other to the Atlantic or Arctic.",

    "The Alps are on which continent?":
        "The Alps stretch across eight European countries and contain hundreds of peaks above 4,000 meters. Hannibal famously crossed them with war elephants in 218 BC to attack Rome.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — Southeast Asia, South America, Oceania Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Thailand?":
        "Bangkok's full ceremonial name in Thai is 168 letters long, making it the world's longest place name. The city is famous for its ornate Buddhist temples, including Wat Phra Kaew, home to the Emerald Buddha.",

    "Capital of Vietnam?":
        "Hanoi has been Vietnam's political center for over a thousand years, since Emperor Ly Thai To moved the capital there in 1010 AD. Its Old Quarter has streets named after the goods traditionally sold on each one.",

    "Capital of Malaysia?":
        "Kuala Lumpur, meaning 'Muddy Confluence,' was founded at the meeting point of the Klang and Gombak rivers during the 1850s tin mining boom. The Petronas Twin Towers were the world's tallest buildings from 1998 to 2004.",

    "Capital of the Philippines?":
        "Manila, located on the shores of Manila Bay, was a thriving center of the Spanish colonial galleon trade linking Asia to the Americas for 250 years. It is one of the most densely populated cities on Earth.",

    "Capital of Colombia?":
        "Bogota sits at 2,640 meters elevation on a high Andean plateau. Despite being just 4 degrees north of the equator, its altitude gives it a cool, spring-like climate year-round.",

    "Capital of Peru?":
        "Lima was founded by Spanish conquistador Francisco Pizarro in 1535 and served as the capital of Spain's South American empire. It almost never rains in Lima despite being a city of 10 million people.",

    "Capital of Chile?":
        "Santiago sits in a valley between the Andes and the Chilean Coastal Range, giving it stunning mountain views but terrible air quality on still days. Chile's unusual shape makes Santiago closer to the Atacama Desert than to Patagonia.",

    "Capital of New Zealand?":
        "Wellington is the world's southernmost capital of a sovereign state. It is notoriously windy -- sitting in the 'Roaring Forties' wind belt -- and was once called 'Windy Welly' by settlers.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — Continents and Rivers (continued)
    # ══════════════════════════════════════════════════════════════════════════

    "Which continent is India on?":
        "India occupies most of the Indian subcontinent, a large peninsula jutting into the Indian Ocean. It is sometimes called a 'subcontinent' because its tectonic plate was once a separate landmass that crashed into Asia.",

    "The Mississippi River is on which continent?":
        "The Mississippi-Missouri river system drains about 40% of the continental United States, covering all or part of 31 states. Mark Twain immortalized the river in his novels about life along its banks.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — Africa Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Morocco?":
        "Rabat became Morocco's capital under French colonial rule in 1912, replacing the traditional imperial cities of Fez and Marrakech. The city's Kasbah of the Udayas, a 12th-century fortress, overlooks the Atlantic Ocean.",

    "Capital of Algeria?":
        "Algiers, known as 'The White City' for its gleaming Ottoman-era buildings cascading down hillsides to the sea, has been a center of Mediterranean civilization since the Phoenicians founded a trading post here.",

    "Capital of Ethiopia?":
        "Addis Ababa, meaning 'New Flower,' sits at 2,355 meters elevation, making it the third-highest capital in the world. It serves as the headquarters of the African Union, earning it the nickname 'political capital of Africa.'",

    "Capital of Ghana?":
        "Accra was built around 17th-century European trading forts and became the capital of the Gold Coast colony. Ghana, which Accra now leads, was the first sub-Saharan African nation to gain independence from colonial rule in 1957.",

    "Capital of Tanzania?":
        "Dodoma officially replaced Dar es Salaam as Tanzania's capital in 1996, though many government functions still operate from Dar es Salaam on the coast. Dodoma was chosen for its central location.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 1 — Features and Remaining Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "The Great Barrier Reef is off the coast of ___?":
        "The Great Barrier Reef stretches over 2,300 kilometers along Australia's northeast coast and is the largest living structure on Earth -- visible from space. It contains over 2,900 individual reef systems.",

    "The world's largest rainforest is the ___?":
        "The Amazon Rainforest produces about 6% of the world's oxygen and contains an estimated 390 billion individual trees representing 16,000 species. It covers an area roughly the size of the contiguous United States.",

    "Capital of Ireland?":
        "Dublin's name comes from the Irish 'Dubh Linn,' meaning 'black pool,' referring to a dark tidal pool where the River Poddle met the Liffey. The city was founded as a Viking settlement around 841 AD.",

    "Capital of Denmark?":
        "Copenhagen started as a Viking fishing village and grew into Scandinavia's largest city. Its famous Tivoli Gardens amusement park, opened in 1843, inspired Walt Disney to create Disneyland.",

    "Capital of Finland?":
        "Helsinki was founded by Swedish King Gustav Vasa in 1550 and became Finland's capital when the country gained independence from Russia in 1917. It is one of the northernmost capitals in the world.",

    "Capital of Singapore?":
        "Singapore is a rare city-state where the capital and country are one and the same. This tiny island nation went from a developing country to one of the world's wealthiest per-capita economies in a single generation.",

    "Capital of Cuba?":
        "Havana was Spain's launching point for conquering the Americas and a key stop for treasure fleets carrying gold back to Europe. Its crumbling colonial architecture and vintage 1950s cars make it feel frozen in time.",

    "The Gobi Desert is on which continent?":
        "The Gobi stretches across northern China and southern Mongolia and is one of the world's great fossil treasure troves. The first scientifically recognized dinosaur eggs were discovered here in 1923.",

    "Which ocean lies between Africa and South America?":
        "The Atlantic is narrowest between Brazil and West Africa -- only about 2,850 kilometers -- which is why scientists believe these continents were once joined as part of the supercontinent Gondwana.",

    "Which continent is Argentina on?":
        "Argentina is the second-largest country in South America and the eighth-largest in the world. Its territory stretches from subtropical jungles in the north to glaciers near Antarctica in the south.",

    "Capital of Iraq?":
        "Baghdad was founded in 762 AD as the capital of the Abbasid Caliphate and became the intellectual center of the Islamic Golden Age. Its House of Wisdom was the world's greatest library and center of learning for centuries.",

    "Capital of Venezuela?":
        "Caracas sits in a narrow mountain valley at about 900 meters elevation, giving it a milder climate than its tropical latitude would suggest. It was the birthplace of Simon Bolivar, the liberator of South America.",

    "The Yangtze River is in ___?":
        "The Yangtze is Asia's longest river at 6,300 kilometers and has been the cradle of Chinese civilization for thousands of years. The Three Gorges Dam on the Yangtze is the world's largest hydroelectric power station.",

    "Capital of Jamaica?":
        "Kingston sits on the world's seventh-largest natural harbor and was founded in 1692 after an earthquake destroyed the nearby pirate haven of Port Royal. The city is the birthplace of reggae music and Bob Marley's legacy.",

    "Capital of Ecuador?":
        "Quito sits at 2,850 meters elevation in a valley flanked by volcanoes, making it the second-highest official capital in the world after La Paz. Its well-preserved colonial center was one of the first UNESCO World Heritage Sites.",

    "Capital of Bolivia?":
        "Sucre is Bolivia's constitutional capital, but La Paz serves as the seat of government. Sucre is named after Antonio Jose de Sucre, a hero of South American independence and Bolivia's first president.",

    "Capital of Uruguay?":
        "Montevideo is home to nearly half of Uruguay's entire population. The city hosted the first FIFA World Cup in 1930, which Uruguay won, and its port on the Rio de la Plata has been vital to South American trade.",

    "Which continent is Mexico on?":
        "Mexico is in North America, not Central or South America, despite common confusion. Geographically, North America extends from Canada through Panama, with Mexico occupying the southern portion of the continent.",

    "Capital of North Korea?":
        "Pyongyang was almost entirely rebuilt after being leveled during the Korean War, when US bombing destroyed an estimated 75% of the city. Today it is filled with monumental Soviet-style architecture and propaganda landmarks.",

    "Capital of Mongolia?":
        "Ulaanbaatar, meaning 'Red Hero,' is the coldest capital city in the world, with winter temperatures regularly dropping below -30 C. Nearly half of Mongolia's entire population lives in this one city.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 — Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Bangladesh?":
        "Dhaka is one of the most densely populated cities on Earth, with over 23,000 people per square kilometer. The city sits on the Ganges-Brahmaputra delta, making it extremely vulnerable to flooding.",

    "Capital of Myanmar?":
        "Naypyidaw was secretly built in the jungle and became Myanmar's capital in 2006, replacing Yangon in a surprise move. The city's roads are famously wide and empty -- it was built for a population that never came.",

    "Capital of Nepal?":
        "Kathmandu sits in a bowl-shaped valley at 1,400 meters in the Himalayas and has been a trading crossroads between India and Tibet for centuries. The valley contains seven UNESCO World Heritage Sites within 15 kilometers.",

    "Capital of Afghanistan?":
        "Kabul has been a strategic prize for over 3,500 years, fought over by Alexander the Great, Genghis Khan, the British Empire, the Soviet Union, and the United States. It sits at 1,800 meters in a narrow valley surrounded by mountains.",

    "Capital of Jordan?":
        "Amman has been continuously inhabited for over 8,000 years, making it one of the oldest cities in the world. The ancient Roman city of Philadelphia lies beneath the modern capital, and its amphitheater still stands.",

    "Capital of Lebanon?":
        "Beirut has been destroyed and rebuilt seven times throughout its 5,000-year history, earning it the nickname 'the city that refuses to die.' Before civil war in 1975, it was known as 'the Paris of the Middle East.'",

    "Capital of Syria?":
        "Damascus is widely considered the oldest continuously inhabited city in the world, with evidence of settlement dating back to 10,000 BC. The Umayyad Mosque at its center has been a place of worship for over 3,000 years.",

    "Capital of Yemen?":
        "Sanaa's Old City contains over 6,000 buildings that are more than 400 years old, many of them distinctive multi-story tower houses decorated with geometric patterns. It sits at 2,300 meters elevation.",

    "Capital of Sudan?":
        "Khartoum sits at the exact confluence of the Blue Nile and White Nile, where the two great rivers merge to form the main Nile. Its name means 'elephant's trunk' in Arabic, describing the shape of the land at the junction.",

    "Capital of Libya?":
        "Tripoli was founded by the Phoenicians in the 7th century BC and has been ruled by Romans, Arabs, Ottomans, Italians, and independent Libyans. Its name comes from the Greek 'Tripolis,' meaning 'three cities.'",

    "Capital of Tunisia?":
        "Tunis sits adjacent to the ruins of ancient Carthage, the great Phoenician city that rivaled Rome for Mediterranean supremacy. Carthage's legendary general Hannibal launched his famous Alpine invasion from this coast.",

    "Capital of Senegal?":
        "Dakar sits on the Cap-Vert peninsula, the westernmost point of mainland Africa. Nearby Goree Island was one of the largest slave-trading centers on the African coast from the 15th to 19th centuries.",

    "Capital of Cameroon?":
        "Yaounde was chosen as the capital over the larger port city of Douala because its inland hilltop location was considered more defensible. Cameroon is called 'Africa in miniature' because it contains nearly every type of African landscape.",

    "Capital of DR Congo?":
        "Kinshasa and Brazzaville, capitals of two different countries (DR Congo and Republic of Congo), face each other across the Congo River -- the closest pair of national capitals in the world, just 10 km apart.",

    "Capital of Angola?":
        "Luanda was founded by Portuguese colonists in 1575 and became a major hub for the Atlantic slave trade. After oil was discovered, it briefly became one of the most expensive cities in the world for expatriates.",

    "Capital of Zimbabwe?":
        "Harare was known as Salisbury during the British colonial era and was renamed in 1982 after independence. Zimbabwe itself is named after Great Zimbabwe, a medieval stone city whose ruins are among Africa's most impressive.",

    "Capital of Mozambique?":
        "Maputo was called Lourenco Marques during Portuguese colonial rule and sits on a bay in the far south of the country. Its distinctive iron house, designed by Gustave Eiffel (of Eiffel Tower fame), is a local landmark.",

    "Capital of Paraguay?":
        "Asuncion was founded on August 15, 1537, making it one of the oldest cities in South America. It served as the base for Spanish colonial expansion and earned the title 'Mother of Cities' for spawning many other settlements.",

    "Capital of Haiti?":
        "Port-au-Prince was devastated by a 7.0-magnitude earthquake in 2010 that killed over 200,000 people. Haiti was the first independent Black republic in the world, gaining freedom from France in 1804.",

    "Capital of the Dominican Republic?":
        "Santo Domingo, founded in 1496 by Bartholomew Columbus (Christopher's brother), is the oldest continuously inhabited European settlement in the Americas. Its Colonial Zone is a UNESCO World Heritage Site.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 — Geographic Features
    # ══════════════════════════════════════════════════════════════════════════

    "The Congo River is on which continent?":
        "The Congo is Africa's second-longest river and the world's deepest, reaching depths of over 220 meters. Its basin contains the second-largest rainforest on Earth after the Amazon.",

    "The Mississippi River flows into the ___?":
        "The Mississippi's delta extends into the Gulf of Mexico, creating vast wetlands that are disappearing at an alarming rate -- Louisiana loses about a football field of land every 100 minutes to coastal erosion.",

    "The Amazon River flows into the ___?":
        "The Amazon discharges so much freshwater into the Atlantic that you can find drinkable water up to 160 kilometers offshore. Its mouth is so wide that the island of Marajo sitting in it is larger than Switzerland.",

    "The Arabian Desert is on which continent?":
        "The Arabian Desert covers most of the Arabian Peninsula in southwestern Asia. Its Rub al Khali (Empty Quarter) is the largest continuous sand desert in the world, roughly the size of France.",

    "The Gobi Desert is in ___?":
        "The Gobi is a cold desert where temperatures can swing from 40 C in summer to -40 C in winter. It is expanding southward at an alarming rate, swallowing about 3,600 square kilometers of Chinese grassland annually.",

    "Which sea separates Europe from Africa?":
        "The Mediterranean, meaning 'middle of the land,' is almost completely enclosed by three continents. It was the superhighway of the ancient world -- the Romans called it 'Mare Nostrum' (Our Sea).",

    "The Red Sea separates Africa from the ___?":
        "The Red Sea is one of the saltiest bodies of water in the world and one of the warmest. It is widening by about 1 centimeter per year as the African and Arabian tectonic plates drift apart.",

    "Which continent is Madagascar off the coast of?":
        "Madagascar separated from Africa about 160 million years ago and from India about 88 million years ago. This isolation created extraordinary biodiversity -- about 90% of its wildlife is found nowhere else on Earth.",

    "Which continent is Morocco on?":
        "Morocco sits at the northwestern tip of Africa, only 14 kilometers from Spain across the Strait of Gibraltar. It has coastlines on both the Atlantic Ocean and the Mediterranean Sea.",

    "Which continent is Turkey mostly on?":
        "About 97% of Turkey's land is in Asia (Anatolia), while just 3% lies in Europe (Thrace). Istanbul, which straddles the Bosphorus Strait, is the only major city in the world sitting on two continents.",

    "The Bering Strait separates Russia from ___?":
        "The Bering Strait is only 82 kilometers wide, and on clear days you can see Russia from Alaska's Little Diomede Island. During ice ages, a land bridge here allowed humans to migrate from Asia to the Americas.",

    "The English Channel separates England from ___?":
        "The English Channel is only 34 kilometers wide at its narrowest point (the Strait of Dover). The Channel Tunnel, completed in 1994, runs 50 kilometers underwater and is the world's longest undersea tunnel.",

    "The Strait of Gibraltar separates Europe from ___?":
        "The Strait of Gibraltar is only 14 kilometers wide at its narrowest point. In Greek mythology, the rocks on either side were the Pillars of Hercules, marking the edge of the known world.",

    "The largest island in the world is ___?":
        "Greenland covers about 2.2 million square kilometers but has only 56,000 inhabitants, making it the least densely populated territory on Earth. About 80% of it is covered by an ice sheet up to 3 km thick.",

    "Greenland belongs to ___?":
        "Greenland has been a self-governing territory of Denmark since 1979, though it lies geographically in North America. Viking explorer Erik the Red named it 'Greenland' around 985 AD to attract settlers.",

    "Japan consists of how many main islands?":
        "Japan's four main islands are Honshu, Hokkaido, Kyushu, and Shikoku, but the country actually has over 6,800 islands in total. Honshu alone is the seventh-largest island in the world.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 — More Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Taiwan?":
        "Taipei sits in a basin surrounded by mountains and volcanic hot springs. Taipei 101, once the world's tallest building, has a 730-ton pendulum ball inside that acts as a damper against typhoon winds and earthquakes.",

    "Capital of Kazakhstan?":
        "Astana (briefly renamed Nur-Sultan from 2019-2022) replaced Almaty as capital in 1997. It is one of the coldest capitals in the world, with winter temperatures dropping to -40 C, and features futuristic architecture rising from the steppe.",

    "Capital of Uzbekistan?":
        "Tashkent is Central Asia's largest city and was a major stop on the ancient Silk Road. A devastating earthquake in 1966 destroyed much of the city, and the Soviet Union rebuilt it with wide boulevards and brutalist architecture.",

    "Capital of Bulgaria?":
        "Sofia has been continuously inhabited for at least 7,000 years, making it one of Europe's oldest settlements. It sits at the foot of Mount Vitosha and was a major Roman city called Serdica.",

    "Capital of Serbia?":
        "Belgrade, meaning 'White City,' sits at the strategic confluence of the Danube and Sava rivers. The Belgrade Fortress has been fought over in 115 wars and destroyed 44 times throughout history.",

    "Capital of Croatia?":
        "Zagreb's Upper Town (Gradec) and Lower Town (Kaptol) were rival medieval settlements that merged in 1850. Every day at noon, a cannon fires from the Lotrscak Tower -- a tradition since 1877.",

    "Capital of Slovakia?":
        "Bratislava is the only national capital that borders two other countries (Austria and Hungary). Vienna is just 60 kilometers away, making them the two closest national capitals in Europe.",

    "Capital of Estonia?":
        "Tallinn's medieval Old Town is one of the best-preserved in Europe and a UNESCO World Heritage Site. Estonia became the first country to hold legally binding national elections online in 2005.",

    "Capital of Latvia?":
        "Riga is the largest city in the Baltic states and was a major Hanseatic League trading port. Its art nouveau district contains over 800 buildings, the highest concentration of art nouveau architecture in the world.",

    "Capital of Lithuania?":
        "Vilnius has one of the largest surviving medieval old towns in Europe. The city was a major center of Jewish culture before World War II, earning it the nickname 'Jerusalem of the North.'",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 — European Rivers and Lakes
    # ══════════════════════════════════════════════════════════════════════════

    "The Rhine River flows through ___?":
        "The Rhine flows 1,230 kilometers from the Swiss Alps to the North Sea in the Netherlands and has been Europe's most important commercial waterway since Roman times. The Rhine Gorge is dotted with medieval castles.",

    "The Volga River is in ___?":
        "The Volga is Europe's longest river at 3,530 kilometers and drains an area larger than any other European river. Russians call it 'Mother Volga' and it features prominently in folk songs and literature.",

    "The Danube River flows into the ___?":
        "The Danube flows through more countries than any other river in the world -- ten in total, from Germany to Romania. Its delta on the Black Sea is Europe's best-preserved wetland and home to over 300 bird species.",

    "Lake Victoria is on which continent?":
        "Lake Victoria, shared by Tanzania, Uganda, and Kenya, is Africa's largest lake by area and the world's largest tropical lake. It was named by British explorer John Hanning Speke after Queen Victoria in 1858.",

    "The largest lake in Africa is ___?":
        "Lake Victoria covers 68,800 square kilometers -- roughly the size of Ireland. It is the primary source of the White Nile and supports the livelihoods of over 30 million people living around its shores.",

    "The largest lake in North America is ___?":
        "Lake Superior contains 10% of the world's surface fresh water and is so large it creates its own weather systems. Its deepest point is 400 meters below sea level. Ships that sink in its cold waters are remarkably well preserved.",

    "The Bay of Bengal is part of which ocean?":
        "The Bay of Bengal is the world's largest bay and is fed by major rivers including the Ganges, Brahmaputra, and Irrawaddy. It is prone to devastating cyclones that have killed hundreds of thousands of people.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 — Middle East and Mediterranean Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Qatar?":
        "Doha was a small pearl-diving village until natural gas made Qatar the richest country per capita in the world. The city has transformed from a dusty fishing port to a futuristic skyline in just two decades.",

    "Capital of the United Arab Emirates?":
        "Abu Dhabi, not Dubai, is the UAE's capital and by far its largest emirate, holding about 90% of the country's oil reserves. The city's name means 'Father of the Gazelle' in Arabic.",

    "Capital of Kuwait?":
        "Kuwait City sits on a natural harbor on the Persian Gulf that made it a center of pearl diving and sea trade for centuries. After oil was discovered in 1938, it became one of the wealthiest cities in the world.",

    "Capital of Oman?":
        "Muscat is surrounded by mountains on three sides and the Gulf of Oman on the fourth, making it one of the hottest capitals in the world. Oman was a major maritime empire that controlled trade routes to East Africa and India.",

    "The Caspian Sea is technically the world's largest ___?":
        "Despite its name, the Caspian is classified as a lake because it is enclosed by land on all sides. It is five times larger than Lake Superior and contains about 40-44% of the world's total lacustrine (lake) water.",

    "Which country owns the Canary Islands?":
        "The Canary Islands are named not after canary birds, but after the Latin word for dog ('canis') -- the Romans reported large dogs on the islands. The birds were later named after the islands, not the other way around.",

    "Capital of Iceland?":
        "Reykjavik, meaning 'Smoky Bay,' is the world's northernmost capital of a sovereign nation. Nearly all of its energy comes from geothermal and hydroelectric sources, making it one of the cleanest cities on Earth.",

    "Capital of Luxembourg?":
        "Luxembourg City sits on dramatic sandstone cliffs above the Alzette and Petrusse rivers. The tiny Grand Duchy of Luxembourg has the highest GDP per capita in the world, driven by its banking and steel industries.",

    "Capital of Malta?":
        "Valletta is the smallest national capital in the EU and was built by the Knights of St. John after they withstood the Great Siege of Malta by the Ottoman Empire in 1565. The entire city is a UNESCO World Heritage Site.",

    "Which ocean lies between the US West Coast and Asia?":
        "The Pacific stretches over 12,000 miles from California to the Philippines. It was named by Portuguese explorer Ferdinand Magellan, who encountered calm seas after navigating the stormy Strait of Magellan in 1520.",

    "The Panama Canal connects the Atlantic Ocean to the ___?":
        "The Panama Canal saves ships a 12,000-mile journey around South America. Completed in 1914, it was one of the largest engineering projects in history and cost over 25,000 workers' lives, mostly from disease.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 — Africa/Oceania Capitals and Features
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Papua New Guinea?":
        "Port Moresby sits on the Coral Sea coast and was a key battleground during World War II. Papua New Guinea is the world's most linguistically diverse country, with over 840 living languages.",

    "Capital of South Sudan?":
        "Juba became the capital of the world's newest country when South Sudan gained independence from Sudan in 2011 after decades of civil war. It sits on the White Nile and is growing rapidly.",

    "Capital of Uganda?":
        "Kampala is built on seven hills, like Rome, and surrounds Mengo Hill, the traditional seat of the Buganda Kingdom. Winston Churchill called Uganda 'the pearl of Africa' after visiting in 1907.",

    "Capital of Rwanda?":
        "Kigali is often called the cleanest city in Africa. After the devastating 1994 genocide, Rwanda rebuilt itself into one of Africa's fastest-growing economies. Plastic bags are banned nationwide.",

    "Capital of Zambia?":
        "Lusaka was a tiny village when it was chosen as the capital of Northern Rhodesia in 1935 because of its central location on the railway line. Zambia is home to one half of Victoria Falls.",

    "Capital of Namibia?":
        "Windhoek sits at 1,700 meters elevation on the central Namibian highland. Namibia is one of the least densely populated countries on Earth, and the Namib Desert that gives it its name is the oldest desert in the world.",

    "The Andes mountain range runs along which coast of South America?":
        "The Andes run along South America's entire Pacific coast for 7,000 km, forming a nearly unbroken wall that creates one of the driest places on Earth (the Atacama Desert) in its rain shadow.",

    "Capital of Cambodia?":
        "Phnom Penh sits at the 'Four Faces' confluence where the Mekong, Bassac, and Tonle Sap rivers meet. The city was nearly emptied entirely by the Khmer Rouge in 1975, who forced all residents into rural labor camps.",

    "Capital of Laos?":
        "Vientiane is one of the quietest and most laid-back capitals in Asia, sitting on the banks of the Mekong River directly across from Thailand. Its name means 'City of Sandalwood.'",

    "The Ganges River is in ___?":
        "The Ganges is considered sacred in Hinduism, and millions of pilgrims bathe in its waters each year. It provides water for about 40% of India's population -- nearly 500 million people -- making it one of the most important rivers on Earth.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 — Central America Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Costa Rica?":
        "San Jose sits in the fertile Central Valley at 1,170 meters elevation. Costa Rica abolished its military in 1948 and redirected that spending to education and healthcare, earning it the nickname 'the Switzerland of Central America.'",

    "Capital of Honduras?":
        "Tegucigalpa is one of the few capital cities in the Americas without a railroad. Built in a mountain valley at 990 meters, its name comes from the Nahuatl language meaning 'Silver Mountain.'",

    "Capital of El Salvador?":
        "San Salvador has been destroyed by earthquakes multiple times throughout its history. El Salvador is the smallest and most densely populated country in Central America, roughly the size of Massachusetts.",

    "Capital of Nicaragua?":
        "Managua sits on the shores of Lake Managua and was devastated by a massive earthquake in 1972. Unusually for a capital city, it has no traditional downtown -- the quake's destruction was never fully rebuilt.",

    "Capital of Panama?":
        "Panama City is the only capital in Latin America with a major international banking center. Its modern skyline, visible right next to the historic Casco Viejo district, makes for one of the most dramatic contrasts in the Americas.",

    "Capital of Guatemala?":
        "Guatemala City is built on a plateau at 1,500 meters elevation and has been plagued by sinkholes -- a massive one swallowed an entire city block in 2010. Guatemala was the heart of the ancient Maya civilization.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 — Misc Geography
    # ══════════════════════════════════════════════════════════════════════════

    "Which landlocked country borders China to the north?":
        "Mongolia is the world's most sparsely populated sovereign country, with just 2 people per square kilometer. In the 13th century, the Mongol Empire under Genghis Khan was the largest contiguous land empire in history.",

    "The Himalayan mountain range borders India and ___?":
        "The Himalayas form a massive natural wall between the Indian subcontinent and the Tibetan Plateau of China. The range contains 9 of the 10 tallest peaks on Earth and is still rising about 5 mm per year.",

    "Capital of Botswana?":
        "Gaborone has grown from a tiny village of 3,855 people at independence in 1966 to a city of over 230,000 today. Botswana is often called Africa's greatest success story, transforming diamond wealth into stable democracy.",

    "The Strait of Hormuz is at the entrance to which gulf?":
        "About 20% of the world's oil supply passes through the Strait of Hormuz, making it arguably the most strategically important chokepoint on Earth. At its narrowest, shipping lanes are only 3 kilometers wide.",

    "Which country is Greenland geographically closest to?":
        "Greenland's closest point to Canada is only 26 kilometers across Nares Strait. Despite its proximity to North America, Greenland has been politically linked to Denmark and Europe since the 18th century.",

    "Capital of Ivory Coast (Cote d'Ivoire)?":
        "Yamoussoukro is famous for the Basilica of Our Lady of Peace, the largest church in the world by some measures -- even bigger than St. Peter's in Vatican City. It was built by President Houphouet-Boigny in his home village.",

    "Capital of Belarus?":
        "Minsk was almost completely destroyed during World War II and rebuilt in grandiose Soviet style with wide boulevards and monumental buildings. Archaeological evidence shows the city has been settled since 1067.",

    "Capital of Georgia (country)?":
        "Tbilisi was founded in the 5th century by King Vakhtang Gorgasali, who reportedly discovered the site's hot sulfur springs while hunting. The city's name comes from the Georgian word 'tbili,' meaning 'warm.'",

    "Capital of Armenia?":
        "Yerevan is one of the oldest continuously inhabited cities in the world, founded in 782 BC -- 29 years before Rome. On clear days, the twin peaks of Mount Ararat, where Noah's Ark supposedly landed, dominate the skyline.",

    "Capital of Azerbaijan?":
        "Baku sits on the Caspian Sea coast and has been called the 'City of Winds' for its fierce gales. Natural gas seeping from the ground has produced eternal flames here for millennia, inspiring ancient Zoroastrian fire worship.",

    "Capital of Slovenia?":
        "Ljubljana is one of Europe's greenest capitals, with extensive pedestrian zones and 542 square meters of public green space per resident. The city's dragon-adorned bridge reflects a legend that Jason of the Argonauts slew a dragon here.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 — Additional Geography and Seas
    # ══════════════════════════════════════════════════════════════════════════

    "The Dardanelles strait is in ___?":
        "The Dardanelles connects the Aegean Sea to the Sea of Marmara, forming part of the crucial waterway between the Mediterranean and Black Sea. In Greek mythology, it was named after Dardanus, ancestor of the Trojans.",

    "The Adriatic Sea is bordered by Italy and ___?":
        "The Adriatic is a narrow arm of the Mediterranean stretching between Italy and the Balkans. Its eastern Croatian coast has over 1,200 islands, making it one of the most island-rich coastlines in the world.",

    "The Aegean Sea is bordered by Greece and ___?":
        "The Aegean is dotted with over 2,000 islands and was the cradle of ancient Greek and later Byzantine civilizations. Its name may come from the mythical King Aegeus, who drowned himself in it.",

    "Which ocean is between North America and Europe?":
        "The Atlantic has been the world's most commercially important ocean since the Age of Exploration. The Mid-Atlantic Ridge running down its center is the longest mountain range on Earth, mostly underwater.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 2 — Long-form geographic/historical questions
    # ══════════════════════════════════════════════════════════════════════════

    "What geographic feature made ancient Athens and other Greek city-states develop as independent units rather than a single empire?":
        "Greece is about 80% mountainous, and its deep valleys and peninsulas created natural isolation between communities. This rugged terrain made unified governance nearly impossible but fostered fierce independence and political experimentation.",

    "Why did the Mediterranean Sea serve as the foundation of Western civilization rather than the Atlantic or Pacific?":
        "The Mediterranean's enclosed geography creates calm, predictable sailing conditions with visible coastlines almost everywhere. Ancient sailors could hug the shore and island-hop, making long-distance trade possible even with primitive ships.",

    "What geographic advantage allowed Rome to dominate the Mediterranean world?":
        "Italy's central position in the Mediterranean meant Roman fleets could reach any coast faster than rivals traveling from the periphery. The Alps provided a northern shield while the peninsula's length gave access to both western and eastern basins.",

    "The Silk Road was a network of trade routes connecting China to Europe. What geographic obstacle made the sea route around Africa preferable when Portugal discovered it in the 1490s?":
        "The overland Silk Road crossed the Taklamakan Desert, the Pamir Mountains, and territories controlled by dozens of rulers who all demanded tolls. A single ship could carry more cargo than a thousand camels without paying middlemen.",

    "Britain became the center of the Industrial Revolution partly because of its geography. Which geographic advantage was most important?":
        "Britain's coal deposits were unusually close to the surface and near navigable waterways, making them cheap to mine and transport. Rivers like the Severn and Trent connected coalfields directly to ports.",

    "The location of Constantinople (modern Istanbul) was chosen by the Roman Emperor Constantine because it ___?":
        "Constantinople sat on the Bosphorus Strait, the only sea passage between the Mediterranean and Black Sea grain regions. Its triangular peninsula, protected by water on three sides, was nearly impregnable for over 1,000 years.",

    "Why did the Cape of Good Hope route around Africa, pioneered by Portugal, transform world trade patterns after 1498?":
        "For centuries, spices worth more than gold traveled overland through Arab and Venetian middlemen who marked up prices enormously. The sea route let European ships buy directly from Asian producers, cutting out every middleman.",

    "Why is free trade between nations generally beneficial according to economic geography?":
        "David Ricardo's principle of comparative advantage shows that even if one country is better at making everything, both nations gain by specializing. Geography determines each nation's natural advantages in climate, resources, and location.",

    "What made the Nile River valley uniquely suited for supporting one of the earliest and most stable civilizations?":
        "Unlike Mesopotamia's unpredictable floods, the Nile flooded like clockwork every July, depositing rich black silt. The surrounding desert acted as a natural fortress, protecting Egyptian civilization from invasion for thousands of years.",

    "The location of Gibraltar, controlled by Britain since 1704, gives Britain strategic control over ___?":
        "Gibraltar's Rock rises 426 meters above the narrow strait, giving its controllers a commanding view of every ship entering or leaving the Mediterranean. Napoleon called it 'the key to the Mediterranean.'",

    "The geographic term 'landlocked' describes a country with no sea access. Landlocked developing countries face a particular economic challenge because ___?":
        "Landlocked countries pay an estimated 50% more for shipping than coastal nations. Their goods must cross borders and use foreign ports, making them economically dependent on neighbors' political stability and infrastructure.",

    "The term 'maritime climate' describes regions near large water bodies. What geographic effect causes cities like London and Seattle to be warmer in winter than inland cities at the same latitude?":
        "Water has a much higher heat capacity than land, absorbing summer warmth and releasing it slowly in winter. This 'thermal flywheel' effect moderates temperature swings for coastal cities up to 100 km inland.",

    "What geographic principle explains why most of the world's great ancient civilizations (Egypt, Mesopotamia, Indus Valley, Yellow River) arose in river valleys?":
        "River valleys provided the 'holy trinity' of early civilization: fertile floodplain soil for agriculture, water for irrigation, and a natural highway for trade. Dense populations could form only where reliable food surpluses existed.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 3 — US State Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Texas?":
        "Austin was named after Stephen F. Austin, the 'Father of Texas,' and chose its Capitol Hill site for its commanding view of the surrounding plains. The Texas State Capitol building is actually taller than the US Capitol in Washington.",

    "Capital of California?":
        "Sacramento became California's capital in 1854 partly because of its location at the confluence of the Sacramento and American Rivers, which made it a supply hub during the 1849 Gold Rush.",

    "Capital of New York State?":
        "Albany has been the capital since 1797, beating out New York City because legislators wanted the capital away from the distracting influence of the nation's largest metropolis. It is one of the oldest surviving European settlements in the US.",

    "Capital of Florida?":
        "Tallahassee was chosen as Florida's capital in 1824 as a midpoint between the two main cities of the era, St. Augustine and Pensacola. It is the only state capital in Florida's panhandle region.",

    "Capital of Georgia (USA)?":
        "Atlanta was originally called Terminus because it was the end point of the Western and Atlantic Railroad. The city was burned to the ground during Sherman's March to the Sea in 1864 and rebuilt from the ashes.",

    "Capital of Illinois?":
        "Springfield is best known as the home of Abraham Lincoln, who lived there for 24 years before becoming president. His tomb and presidential library are the city's most visited landmarks.",

    "Capital of Ohio?":
        "Columbus is the most populous state capital in the US, named after Christopher Columbus. Ohio has contributed more US presidents (eight) than any state except Virginia.",

    "Capital of Pennsylvania?":
        "Harrisburg sits on the Susquehanna River and was the site of the Three Mile Island nuclear accident in 1979. Pennsylvania's name means 'Penn's Woods,' after the Quaker William Penn.",

    "Capital of Michigan?":
        "Lansing was chosen as capital in 1847 partly because it was far from the Canadian border (Michigan had just fought a border dispute). Despite being the capital, it is only the fifth-largest city in Michigan.",

    "Capital of Virginia?":
        "Richmond served as the capital of the Confederacy during the Civil War and was the target of multiple Union campaigns. Virginia has been called the 'Mother of Presidents' for producing eight US presidents.",

    "Capital of North Carolina?":
        "Raleigh was founded in 1792 as a planned capital city and named after Sir Walter Raleigh, who established the lost colony of Roanoke nearby. The Research Triangle (Raleigh-Durham-Chapel Hill) is a major tech and academic hub.",

    "Capital of Massachusetts?":
        "Boston played a central role in the American Revolution, from the Boston Tea Party to the Battle of Bunker Hill. Harvard University, just across the river in Cambridge, is the oldest institution of higher education in the US (founded 1636).",

    "Capital of Colorado?":
        "Denver is called the 'Mile High City' because its official elevation is exactly one mile (5,280 feet) above sea level. A step on the west side of the State Capitol building is engraved to mark the precise altitude.",

    "Capital of Washington State?":
        "Olympia sits at the southern tip of Puget Sound and was named after the nearby Olympic Mountains. Despite Seattle's fame, Olympia has been the capital since Washington became a territory in 1853.",

    "Capital of Arizona?":
        "Phoenix is the hottest state capital in the US, with summer temperatures regularly exceeding 43 C (110 F). Named after the mythical bird, the city rose from the ruins of an ancient Hohokam canal system.",

    "Capital of Nevada?":
        "Carson City was named after frontiersman Kit Carson and boomed during the Comstock Lode silver rush. Despite Las Vegas's fame, Carson City has been the capital since Nevada became a state in 1864.",

    "Capital of Oregon?":
        "Salem comes from the Hebrew word 'Shalom,' meaning peace. Oregon was the destination of the famous Oregon Trail, which brought over 400,000 settlers westward in the mid-1800s.",

    "Capital of Minnesota?":
        "Saint Paul and neighboring Minneapolis form the 'Twin Cities,' with Saint Paul as the older sibling. Minnesota's name comes from the Dakota Sioux word for 'sky-tinted water,' reflecting its 10,000+ lakes.",

    "Capital of Louisiana?":
        "Baton Rouge, meaning 'Red Stick' in French, was named after a reddish cypress pole that marked the boundary between two Native American tribal territories. Louisiana is the only US state that uses parishes instead of counties.",

    "Capital of Tennessee?":
        "Nashville is world-famous as 'Music City,' the birthplace of country music and home to the Grand Ole Opry since 1925. It also has a full-scale replica of the Greek Parthenon in its Centennial Park.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 3 — Physical Geography
    # ══════════════════════════════════════════════════════════════════════════

    "The deepest lake in the world is ___?":
        "Lake Baikal in Siberia holds about 20% of the world's unfrozen surface fresh water -- more than all the Great Lakes combined. It is home to about 2,500 species found nowhere else on Earth, including the Baikal seal.",

    "Lake Baikal is in ___?":
        "Lake Baikal is located in southern Siberia, Russia, and is the oldest lake in the world at about 25 million years old. In winter, the ice becomes so clear you can see 40 meters down into the water.",

    "The longest mountain range in the world is the ___?":
        "The Andes stretch 7,000 kilometers from Venezuela to the southern tip of Chile, passing through seven countries. They contain the world's highest volcanoes, including Ojos del Salado at 6,893 meters.",

    "The largest cold desert in the world is ___?":
        "Antarctica receives less than 200 mm of precipitation per year, qualifying it as a desert -- the largest on Earth at 14 million square kilometers. Some of its interior valleys have not seen rain for 2 million years.",

    "The Strait of Gibraltar connects the Atlantic Ocean to the ___?":
        "The strait's powerful currents create a two-layer flow: Atlantic water rushes in on the surface, while saltier Mediterranean water flows out along the bottom. Ancient mariners called it the gateway between worlds.",

    "The Bosphorus Strait is in ___?":
        "The Bosphorus divides Istanbul in two, making it the only city in the world on two continents. Only 700 meters wide at its narrowest, it is one of the world's most difficult waterways to navigate.",

    "The Strait of Malacca separates Malaysia from ___?":
        "The Strait of Malacca carries about 25% of all global trade, making it the most important shipping lane in the world. At its narrowest point, it is only 2.8 kilometers wide.",

    "A peninsula is land surrounded by water on ___?":
        "The word 'peninsula' comes from the Latin 'paene' (almost) and 'insula' (island), literally meaning 'almost an island.' Famous peninsulas include Florida, Korea, Italy, and the Iberian Peninsula.",

    "An isthmus is a narrow strip of land connecting ___?":
        "The most famous isthmus is Panama, which connects North and South America. The Suez Isthmus connecting Africa and Asia was cut by the Suez Canal in 1869, turning Africa into an effective island.",

    "An archipelago is ___?":
        "The word comes from the Greek 'archi' (chief) and 'pelagos' (sea), originally referring to the Aegean Sea. Indonesia is the world's largest archipelago, with over 17,000 islands spread across 5,000 km.",

    "The Panama Isthmus connects North America to ___?":
        "The Isthmus of Panama formed about 3 million years ago, triggering the Great American Interchange where animals migrated between the two continents. Armadillos went north; big cats went south.",

    "The Iberian Peninsula is home to Spain and ___?":
        "The Iberian Peninsula is the westernmost point of continental Europe, with Cape Roca in Portugal marking the spot. The Pyrenees mountains along the northern edge separate the peninsula from the rest of Europe.",

    "The largest landlocked country is ___?":
        "Kazakhstan covers 2.7 million square kilometers -- larger than all of Western Europe combined -- yet has only 19 million people. It spans from the Caspian Sea to the Altai Mountains but has no ocean access.",

    "The highest navigable lake in the world is ___?":
        "Lake Titicaca sits at 3,812 meters above sea level on the border of Peru and Bolivia. The Uru people have lived on floating islands made of totora reeds on its surface for centuries.",

    "Lake Titicaca is on the border of Peru and ___?":
        "Lake Titicaca covers 8,372 square kilometers and reaches depths of 281 meters. In Inca mythology, the creator god Viracocha emerged from its waters to create the sun, moon, and stars.",

    "The Great Rift Valley is on which continent?":
        "The Great Rift Valley stretches 6,000 km from Lebanon to Mozambique and is literally the place where Africa is splitting in two. In millions of years, East Africa will become a separate continent.",

    "The Suez Canal connects the Red Sea to the ___?":
        "The Suez Canal eliminated the need to sail around Africa, cutting the London-to-Mumbai journey by about 7,000 kilometers. About 12% of all global trade passes through it today.",

    "The Suez Canal is in ___?":
        "The Suez Canal was built by French engineer Ferdinand de Lesseps and opened in 1869 after 10 years of construction. Egypt nationalized it in 1956, triggering an international crisis with Britain, France, and Israel.",

    "Which US state is the largest by area?":
        "Alaska is over twice the size of Texas and larger than the combined areas of the next three largest states. If placed over the contiguous US, it would stretch from coast to coast.",

    "Which US state is the smallest by area?":
        "Rhode Island covers only 4,001 square kilometers -- you could fit it inside Alaska about 425 times. Despite its size, its official name is the longest of any state: 'Rhode Island and Providence Plantations.'",

    "The Great Lakes are shared between the US and ___?":
        "The Great Lakes contain about 21% of the world's surface fresh water and form the largest group of freshwater lakes on Earth. Only Lake Michigan is entirely within the United States.",

    "How many Great Lakes are there?":
        "The five Great Lakes are Superior, Michigan, Huron, Erie, and Ontario. A handy mnemonic is HOMES. Together they have a combined coastline longer than the US Atlantic seaboard.",

    "Capital of Albania?":
        "Tirana was founded by an Ottoman general in 1614 and became Albania's capital in 1920. Once one of the most isolated cities in Europe under communist rule, it has been transformed with colorful painted buildings.",

    "The Dead Sea is on the border of Israel and ___?":
        "The Dead Sea sits 430 meters below sea level, making its shore the lowest point on Earth's surface. Its water is nearly 10 times saltier than the ocean, so dense that swimmers float effortlessly.",

    "The Cape of Good Hope is in ___?":
        "The Cape of Good Hope was originally named the 'Cape of Storms' by Portuguese navigator Bartolomeu Dias in 1488. King John II renamed it to encourage sailors that a sea route to India was possible.",

    "The Aleutian Islands belong to ___?":
        "The Aleutian chain stretches 1,900 kilometers from Alaska toward Russia and contains about 80 volcanoes, 36 of which are still active. The Battle of Attu in 1943 was the only World War II battle fought on US soil.",

    "The Maldives is in which ocean?":
        "The Maldives is the world's lowest-lying country, with an average elevation of just 1.5 meters above sea level. Rising sea levels threaten to make it the first nation to be entirely submerged.",

    "The Apennine Mountains run through ___?":
        "The Apennines form the 'backbone' of Italy, running 1,200 kilometers down the length of the peninsula. They divide the country into eastern and western watersheds and contain active volcanoes like Vesuvius.",

    "Capital of Moldova?":
        "Chisinau was devastated by a catastrophic earthquake in 1940 and bombing in World War II, and was rebuilt in Soviet style. Moldova is one of Europe's least-visited and poorest countries, known for its wine industry.",

    "The island of Honshu is part of ___?":
        "Honshu is Japan's largest and most populous island, home to about 80% of Japan's population and all of its major cities: Tokyo, Osaka, Yokohama, and Kyoto. It is the seventh-largest island in the world.",

    "Capital of Brunei?":
        "Bandar Seri Begawan is the capital of one of the world's smallest and wealthiest nations, thanks to vast oil and gas reserves. The Sultan of Brunei's Istana Nurul Iman palace is the world's largest residential palace.",

    "Capital of East Timor?":
        "Dili became the capital of one of the world's youngest nations when East Timor gained independence from Indonesia in 2002. The tiny half-island nation was colonized by Portugal for over 400 years.",

    "The Gulf of Mexico borders how many US states?":
        "The five US states bordering the Gulf are Florida, Alabama, Mississippi, Louisiana, and Texas. The Gulf is a major source of seafood, oil production, and unfortunately, destructive hurricanes.",

    "The Great Victoria Desert is in ___?":
        "The Great Victoria Desert is Australia's largest desert, stretching across South and Western Australia. Despite its harsh conditions, Aboriginal Australians have lived here for tens of thousands of years.",

    "The Rio Grande forms the border between the US and ___?":
        "The Rio Grande stretches 3,051 kilometers from Colorado to the Gulf of Mexico. In Mexico it is called the Rio Bravo del Norte. Its waters are so heavily used for irrigation that it sometimes fails to reach the sea.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 3 — More US State Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Utah?":
        "Salt Lake City was founded in 1847 by Brigham Young and Mormon pioneers who declared 'This is the place' upon seeing the Salt Lake Valley. The city hosted the 2002 Winter Olympics.",

    "Capital of Indiana?":
        "Indianapolis is home to the famous Indy 500, the world's largest single-day sporting event with over 300,000 spectators. The city's name simply combines 'Indiana' with 'polis' (Greek for city).",

    "Capital of Wisconsin?":
        "Madison is built on a narrow isthmus between two lakes, Mendota and Monona, giving it an unusual waterfront setting for a capital city. It is consistently ranked as one of the most livable cities in America.",

    "Capital of Missouri?":
        "Jefferson City sits on bluffs above the Missouri River and was named after Thomas Jefferson. Missouri's central location earned it the nickname 'Gateway to the West,' symbolized by the St. Louis Gateway Arch.",

    "Capital of Alabama?":
        "Montgomery was the first capital of the Confederacy in 1861, but more importantly, it was where Rosa Parks refused to give up her bus seat in 1955, sparking the Civil Rights Movement.",

    "Capital of South Carolina?":
        "Columbia was founded as a planned capital in 1786 at the geographic center of the state. It was largely burned during Sherman's March in 1865, and the charred ruins of the old state house still stand.",

    "Capital of Kentucky?":
        "Frankfort is one of the smallest state capitals in the US, with a population under 30,000. Kentucky is famous for horse racing (the Kentucky Derby), bourbon whiskey, and bluegrass music.",

    "Capital of Connecticut?":
        "Hartford was the insurance capital of the United States for over a century. Connecticut's Fundamental Orders of 1639 was one of the first written constitutions in the Western world.",

    "Capital of New Jersey?":
        "Trenton is where George Washington crossed the Delaware River on Christmas night 1776 to surprise Hessian troops in a pivotal Revolutionary War battle. 'Trenton Makes, The World Takes' is the city's industrial motto.",

    "Capital of Maryland?":
        "Annapolis briefly served as the US national capital (1783-1784) and is home to the US Naval Academy, founded in 1845. Its colonial-era architecture includes the oldest state house still in continuous legislative use.",

    "Capital of New Mexico?":
        "Santa Fe, founded in 1610, is the oldest state capital in the United States and the highest at 2,194 meters. Its distinctive adobe architecture reflects centuries of Pueblo Native American and Spanish colonial influence.",

    "Capital of Iowa?":
        "Des Moines plays an outsized role in American politics because Iowa holds the first presidential caucuses every four years, making it a mandatory stop for every presidential hopeful.",

    "Capital of Kansas?":
        "Topeka made history in 1954 when the Supreme Court case Brown v. Board of Education, originating from its schools, declared racial segregation in public education unconstitutional.",

    "Capital of Oklahoma?":
        "Oklahoma City is one of the few state capitals where the capital city shares the state's name. The city sits atop one of the largest oil fields in North America, and working oil wells dot the grounds of the State Capitol.",

    "Capital of Arkansas?":
        "Little Rock takes its name from a small rock formation on the Arkansas River that early French explorers used as a landmark. The city made civil rights history in 1957 when federal troops escorted nine Black students into Central High School.",

    "Capital of Mississippi?":
        "Jackson is named after Andrew Jackson, the seventh US president. Mississippi is named after the great river forming its western border -- the Ojibwe word 'Misi-ziibi' means 'Great River.'",

    "Capital of West Virginia?":
        "Charleston sits in the Kanawha Valley and became the capital of a state born during the Civil War -- West Virginia split from Virginia in 1863 over the issue of slavery. Its Kanawha River was once a major salt-producing region.",

    "Capital of Idaho?":
        "Boise's name comes from French-Canadian trappers who called the tree-lined river 'la riviere boisee' (the wooded river) after crossing miles of barren desert. Idaho's Hells Canyon is deeper than the Grand Canyon.",

    "Capital of Montana?":
        "Helena was founded as a gold mining camp in 1864 after four prospectors struck gold in what they called 'Last Chance Gulch.' By the 1880s it had more millionaires per capita than any city in the US.",

    "Capital of Wyoming?":
        "Cheyenne was named after the Cheyenne people and grew as a stop on the Union Pacific Railroad. Wyoming was the first US territory to grant women the right to vote, in 1869.",

    "Capital of North Dakota?":
        "Bismarck was named after German Chancellor Otto von Bismarck in hopes of attracting German immigrant investment in the railroad. It sits on the Missouri River where Lewis and Clark passed through in 1804.",

    "Capital of South Dakota?":
        "Pierre (pronounced 'peer') is the least populous state capital in the US, with only about 14,000 residents. South Dakota is home to Mount Rushmore, carved into the Black Hills 25 miles southwest of Rapid City.",

    "Capital of Nebraska?":
        "Lincoln was originally called Lancaster but was renamed after Abraham Lincoln when Nebraska became a state in 1867. Nebraska's unicameral legislature (one chamber) is unique among US states.",

    "Capital of Hawaii?":
        "Honolulu means 'sheltered harbor' in Hawaiian and sits on the island of Oahu. The attack on Pearl Harbor here on December 7, 1941, drew the United States into World War II.",

    "Capital of Delaware?":
        "Dover has been Delaware's capital since 1777. Delaware was the first state to ratify the US Constitution on December 7, 1787, earning it the nickname 'The First State.'",

    "Capital of New Hampshire?":
        "Concord is home to the famous Concord Coach, a stagecoach so well-built it was called 'the coach that won the West.' New Hampshire holds the first US presidential primary every election cycle.",

    "Capital of Vermont?":
        "Montpelier is the smallest state capital by population in the US, with fewer than 8,000 residents. It is the only state capital without a McDonald's restaurant.",

    "Capital of Maine?":
        "Augusta sits on the Kennebec River, which was one of the earliest areas of European settlement in New England. Maine is the only US state that shares a border with exactly one other state (New Hampshire).",

    "Capital of Rhode Island?":
        "Providence was founded in 1636 by Roger Williams, who fled Massachusetts seeking religious freedom. Its name reflects his gratitude for 'God's merciful Providence.'",

    "Capital of Alaska?":
        "Juneau is the only US state capital accessible only by air or sea -- there are no roads connecting it to the rest of Alaska. It is also larger in area than the entire state of Rhode Island.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 3 — Peninsulas, Seas, and Regions
    # ══════════════════════════════════════════════════════════════════════════

    "The Balkan Peninsula includes countries such as ___?":
        "The Balkans have been called 'the powder keg of Europe' because ethnic and political tensions here sparked World War I. The region's mountains and river valleys created fragmented nations with complex cultural boundaries.",

    "The Strait of Dover is between England and ___?":
        "At only 34 km wide, the Strait of Dover is the narrowest point of the English Channel. About 400 ships pass through it daily, making it the busiest shipping lane in the world.",

    "The North Sea borders which countries to the east?":
        "The North Sea sits atop vast oil and gas reserves that transformed the economies of Norway, the UK, and the Netherlands starting in the 1960s. It was also the hunting ground of Viking longships for centuries.",

    "The Iberian Peninsula is in ___?":
        "The Iberian Peninsula is separated from the rest of Europe by the Pyrenees mountains, giving it a distinct cultural identity. It was ruled by Islamic Moors for nearly 800 years (711-1492), deeply shaping its architecture and language.",

    "The Korean Peninsula extends from ___?":
        "The Korean Peninsula has been divided since 1945, with a heavily fortified Demilitarized Zone (DMZ) separating North and South Korea. Despite the name, the DMZ is one of the most militarized borders in the world.",

    "The Indochina Peninsula includes Vietnam, Laos, Cambodia, and ___?":
        "The name 'Indochina' reflects the region's position as a cultural crossroads between Indian and Chinese civilizations. The Mekong River, flowing through all five mainland Southeast Asian countries, is the peninsula's lifeline.",

    "The largest country in South America by area is ___?":
        "Brazil covers 8.5 million square kilometers -- about 47% of South America's land area. It is the fifth-largest country in the world and shares a border with every South American country except Chile and Ecuador.",

    "The largest country in Africa by area is ___?":
        "Algeria became Africa's largest country after South Sudan split from Sudan in 2011. About 80% of Algeria is Saharan desert, and most of its 45 million people live along the narrow Mediterranean coast.",

    "The Adriatic Sea borders which Italian region on the west?":
        "Italy's eastern coast along the Adriatic includes regions like Puglia, Abruzzo, and Emilia-Romagna. This coast tends to be flatter and sandier than the rugged western coast facing the Tyrrhenian Sea.",

    "The Himalayan nation of Bhutan borders India and ___?":
        "Bhutan measures national success not by GDP but by 'Gross National Happiness.' This mountainous kingdom was the last country in the world to introduce television, waiting until 1999.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 3 — Long-form questions
    # ══════════════════════════════════════════════════════════════════════════

    "Why did the Netherlands become a major trading empire in the 17th century despite being a small nation with few natural resources?":
        "The Rhine, Europe's busiest commercial river, empties into the sea right at the Netherlands. This geographic lottery made Dutch ports the natural warehouse for all goods moving between inland Europe and the world.",

    "David Ricardo's theory of comparative advantage in trade is fundamentally a geographic argument. It holds that nations should ___?":
        "Ricardo showed that Portugal should make wine and England cloth even if Portugal could make both more cheaply, because the opportunity cost of switching production differs. Geography dictates those opportunity costs.",

    "The Roman road network connected Britain to Mesopotamia at its height. What was the primary strategic purpose of this road system?":
        "Roman roads were engineered for speed: legions could march 30-40 km per day on them, reaching any trouble spot in weeks rather than months. The phrase 'All roads lead to Rome' was literally true -- they radiated from a golden milestone in the Forum.",

    "Why did the discovery of the Americas by Columbus in 1492 ultimately destroy the Portuguese advantage in Eastern trade?":
        "New World silver, especially from Potosi in Bolivia, became so abundant that the global price of silver collapsed. The purchasing power that had made the spice trade profitable shifted dramatically, and new Atlantic routes bypassed Portuguese monopolies.",

    "The Hanseatic League (1200s-1600s) was a trading alliance of cities along the Baltic and North Sea coasts. What geographic feature united these cities?":
        "Hanseatic cities like Lubeck, Hamburg, and Bruges controlled narrow sea passages and river mouths. Their geographic chokehold on northern European trade made them collectively wealthier and more powerful than many kingdoms.",

    "Why did the Appalachian Mountains pose such a significant barrier to early American westward expansion?":
        "The Appalachians run nearly continuously from Maine to Alabama with few natural passes. The Cumberland Gap, discovered by Daniel Boone, became the funnel through which over 300,000 settlers poured into Kentucky and beyond.",

    "Why did New Orleans become the most important port city in North America in the early 19th century?":
        "Every bushel of grain and barrel of pork from the entire Mississippi watershed -- covering 31 modern states -- had to pass through New Orleans to reach world markets. Controlling this choke point was why Jefferson bought Louisiana.",

    "What geographic advantage did Britain possess that allowed it to maintain dominance of world trade even after losing the American colonies in 1783?":
        "Britain's island geography meant the Royal Navy could blockade any European rival while remaining unblockable itself. No enemy army could march to Britain, and its ports faced every ocean.",

    "The location of Venice made it the dominant trading city of medieval Europe because it ___?":
        "Venice's lagoon was too shallow for enemy warships but deep enough for Venetian merchant galleys. This natural moat, combined with its position connecting the Adriatic to Alpine trade routes, made it unassailable and irreplaceable.",

    "What geographic factor explains why the Industrial Revolution began in the coal fields of northern England and the Ruhr Valley in Germany rather than in France or Spain?":
        "Northern England's coalfields around Newcastle and Manchester sat directly on rivers and canals connecting to major ports. The Ruhr Valley similarly had coal, iron ore, and the Rhine for transport -- a geographic trifecta.",

    "Why did the Atlantic slave trade route form a triangle between Europe, West Africa, and the Americas rather than more direct routes?":
        "The North Atlantic's clockwise gyre of winds and currents naturally pushed ships from Europe to Africa, then across to the Caribbean, and back to Europe. Sailing against these patterns was slow and dangerous.",

    "The concept of 'natural borders' holds that rivers and mountains create defensible boundaries. Which European border is the classic example of a river as a natural boundary?":
        "Julius Caesar made the Rhine the boundary of the Roman world, a line that persisted for centuries. The river's width and current made it a genuine military obstacle, and the cultural divide it created still echoes in language and customs today.",

    "Why did the Black Death (1347-1353) spread so rapidly across Europe from its entry point at Sicilian ports?":
        "Medieval Europe's trade networks were like a circulatory system carrying infected rats and fleas along the same routes that carried silk, spice, and grain. The denser the trade network, the faster the plague spread.",

    "The Strait of Hormuz, through which about 20% of global oil passes, is strategically controlled by which two nations?":
        "Iran controls the strait's northern shore and Oman the southern tip. At its narrowest, the strait is just 33 km wide, with shipping lanes only 3 km across -- a geographic bottleneck of enormous strategic importance.",

    "Why did ancient Phoenicia (modern Lebanon) develop as a major trading civilization despite its small size?":
        "Phoenicia was squeezed between mountains and sea, with little farmland but excellent harbors and Lebanon's famous cedar forests for shipbuilding. Geography forced them to become sailors, and they became the greatest navigators of the ancient world.",

    "Why did the fall of Constantinople to the Ottomans in 1453 have such a significant impact on European trade?":
        "Constantinople controlled the only sea route between the Mediterranean and the Black Sea, and sat astride the best overland route to Asia. When it fell, European merchants suddenly faced Ottoman tolls and restrictions.",

    "What geographic factor best explains why Sub-Saharan Africa was the last major region to be colonized and industrialized by Europeans?":
        "Africa's rivers, unlike Europe's, drop sharply near the coast with cataracts and waterfalls, making them useless for inland navigation. The tsetse fly and malaria created a 'disease barrier' that killed European explorers.",

    "The geographic concept of 'chokepoints' refers to narrow passages in trade routes. Which chokepoint most threatens global oil supply if blocked?":
        "The Strait of Hormuz handles tankers carrying roughly 20 million barrels of oil daily. If Iran blocked this 33-km-wide passage, global oil prices would skyrocket overnight and economies worldwide would reel.",

    "Which of these best explains why Switzerland, a landlocked country with no natural resources, became one of the world's wealthiest nations?":
        "Switzerland's mountain passes were the only practical routes between northern and southern Europe for centuries. The Swiss collected tolls, provided banking services to traders, and leveraged their neutrality into permanent prosperity.",

    "The Amazon basin contains approximately 10% of all species on Earth. Why does this region have such extraordinary biodiversity?":
        "The Amazon basin has been continuously warm and wet for over 50 million years -- an evolutionary laboratory with stable conditions. Rivers fragment the forest into 'islands,' allowing species to diverge on either bank.",

    "The European Plain stretching from France to Russia enabled which recurring pattern in European history?":
        "The Great European Plain is essentially a highway for armies. From the Huns to the Mongols to Napoleon to Hitler, every major land invasion of Europe or Russia has exploited this flat, unobstructed corridor.",

    "Why did Portugal establish its colonial empire by sailing around Africa to Asia rather than sailing west like Spain?":
        "Prince Henry the Navigator had established a systematic program of African coastal exploration starting in the 1420s. By the time Columbus proposed going west, Portugal had already invested 70 years mapping the African route.",

    "What is the main reason the Sahara Desert expanded northward into what is now called the Sahel region during the 20th century?":
        "Desertification in the Sahel is a human-accelerated feedback loop: overgrazing strips vegetation, exposed soil reflects more heat, which reduces rainfall, which kills more vegetation. The result is desert advancing at 48 km per year in some areas.",

    "Why does the Gulf Stream give Northwestern Europe a climate far milder than its latitude would suggest?":
        "London and Paris are at the same latitude as southern Canada, but the Gulf Stream delivers warm Caribbean water northeastward. Without it, much of Western Europe would resemble Labrador -- cold, icy, and largely uninhabitable.",

    "What geographic factor most explains why ancient Mesopotamia (modern Iraq) struggled to maintain stable civilization compared to Egypt?":
        "Mesopotamia sat on a flat, open plain with no natural barriers against invasion from any direction. The Tigris and Euphrates flooded unpredictably, and the soil eventually became too salty from irrigation -- a problem Egypt never faced.",

    "The term 'choke point geography' explains why small countries like Singapore and Panama punch above their economic weight. What is the common geographic feature?":
        "Singapore controls the Strait of Malacca (25% of global trade); Panama controls the canal (5% of global trade). Tiny nations sitting on geographic bottlenecks can charge tolls that make them disproportionately wealthy.",

    "Why did the Erie Canal (completed 1825) make New York City the dominant commercial city in North America within a decade of its opening?":
        "The Erie Canal turned a 580-km ditch across New York State into a water highway linking the Great Lakes to the Atlantic. Shipping costs dropped 90%, and all that interior produce funneled through New York Harbor.",

    "The geographic isolation of Japan from mainland Asia (separated by 120 miles of sea) had what primary historical consequence?":
        "The 120-mile Korea Strait was close enough for cultural exchange but wide enough to stop invasions. The Mongols tried twice (1274 and 1281) and both times typhoons destroyed their fleets -- the divine wind, or 'kamikaze.'",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 4 — Obscure Capitals
    # ══════════════════════════════════════════════════════════════════════════

    "Capital of Kyrgyzstan?":
        "Bishkek was known as Frunze during the Soviet era, named after a Bolshevik general born there. Kyrgyzstan is over 90% mountainous, and its people have a proud nomadic heritage of yurt-dwelling and eagle hunting.",

    "Capital of Tajikistan?":
        "Dushanbe means 'Monday' in Tajik because the city grew from a village that held its market on Mondays. Tajikistan is the poorest former Soviet republic, but its Pamir Highway is considered one of the world's most spectacular roads.",

    "Capital of Turkmenistan?":
        "Ashgabat is famous for its white marble buildings -- the Guinness Book of Records certified it as having the highest density of white marble buildings in the world. The city was rebuilt after a devastating 1948 earthquake.",

    "Capital of Fiji?":
        "Suva sits on Fiji's largest island, Viti Levu, and is the largest city in the South Pacific islands. Fiji was a British colony until 1970, and the practice of cannibalism was widespread there until the 19th century.",

    "Capital of Vanuatu?":
        "Port Vila sits on the island of Efate in a nation of 83 islands. Vanuatu is the most at-risk country in the world for natural disasters, sitting squarely in the Pacific Ring of Fire and cyclone belt.",

    "Capital of Tonga?":
        "Nuku'alofa is the capital of the only remaining monarchy in the Pacific. Tonga was never colonized by a European power, making it unique among Pacific island nations.",

    "Capital of Samoa?":
        "Apia sits on the north coast of Upolu island and was the home of Robert Louis Stevenson (author of Treasure Island) during the last years of his life. The Samoans called him 'Tusitala' -- the storyteller.",

    "Capital of Solomon Islands?":
        "Honiara sits on the island of Guadalcanal, site of one of the bloodiest battles of the Pacific theater in World War II. The 1942-1943 campaign was the first major Allied offensive against Japan.",

    "Which country borders both France and Spain?":
        "Andorra is a tiny principality of just 468 square kilometers nestled in the Pyrenees mountains. It has two co-heads of state: the President of France and the Bishop of Urgell in Spain -- a unique arrangement dating to 1278.",

    "Which country is completely surrounded by South Africa?":
        "Lesotho is one of only three countries completely enclosed by another (along with Vatican City and San Marino). Its lowest point is 1,400 meters, making it the country with the highest lowest point in the world.",

    "Lake Baikal's depth is approximately ___?":
        "At 1,642 meters deep, Lake Baikal could swallow five stacked Eiffel Towers. It holds more fresh water than all five Great Lakes combined and is so ancient that unique species evolved in its depths over 25 million years.",

    "The Dead Sea shore is the lowest point on land at ___?":
        "At 430 meters below sea level, the Dead Sea shore is dropping further every year as the sea shrinks due to water diversion. Its extreme saltiness (about 34%) means nothing larger than microbes can survive in it.",

    "Angel Falls, the world's tallest waterfall, is in ___?":
        "Angel Falls plunges 979 meters from a flat-topped tepui (table mountain) called Auyantepui. The falls are so tall that much of the water evaporates or is blown away as mist before reaching the ground.",

    "The world's smallest country is ___?":
        "Vatican City covers only 0.44 square kilometers -- about the size of a golf course -- and has roughly 800 residents. Despite its tiny size, it has its own postal service, radio station, and even a small railway station.",

    "Which Scandinavian country has the most islands?":
        "Sweden has approximately 267,570 islands, far more than Norway or Finland. Most are tiny uninhabited rocky skerries along its coast, but about 1,000 are permanently inhabited.",

    "Which country exists in all 4 hemispheres?":
        "Kiribati's 33 atolls are scattered across 3.5 million square kilometers of the Pacific, straddling the equator and the International Date Line. This tiny nation spans all four hemispheres despite having only 119,000 people.",

    "The Strait of Malacca connects the Indian Ocean to the ___?":
        "The Strait of Malacca is one of the most important shipping lanes in the world, carrying about 25% of all global trade. Its narrowest point is only 2.8 km wide, making piracy a persistent problem.",

    "Mauna Kea is tallest when measured from ___?":
        "Measured from its base on the Pacific Ocean floor, Mauna Kea rises over 10,200 meters -- more than a kilometer taller than Everest. However, only 4,207 meters poke above the waves.",

    "How many land borders does Russia share with other countries?":
        "Russia's 14 land neighbors range from North Korea and China in the east to Norway and Finland in the northwest. Its total land border stretches over 20,000 kilometers, the longest of any country.",

    "Russia shares borders with how many countries?":
        "Russia's 14 neighbors are Norway, Finland, Estonia, Latvia, Lithuania (via Kaliningrad), Poland (via Kaliningrad), Belarus, Ukraine, Georgia, Azerbaijan, Kazakhstan, China, Mongolia, and North Korea.",

    "Capital of Eritrea?":
        "Asmara was built as the capital of Italian Eritrea in the 1930s and features one of the world's finest collections of Art Deco and Futurist architecture, earning it UNESCO World Heritage status. Its elevation of 2,325 meters keeps it cool.",

    "Capital of Djibouti?":
        "Djibouti City sits at the entrance to the Red Sea and hosts military bases from France, the US, China, Japan, and Italy. Its strategic location near the Bab el-Mandeb Strait makes it a geopolitical hotspot.",

    "Capital of Somalia?":
        "Mogadishu was once a thriving medieval trading port connecting East Africa to Arabia, Persia, and India. Founded by Arab settlers in the 10th century, its decline during decades of civil war made it infamous as one of the world's most dangerous cities.",

    "Capital of Niger?":
        "Niamey sits on the Niger River and is the capital of one of the hottest and most arid countries on Earth. Niger has the world's highest fertility rate, with women having an average of about 7 children.",

    "Capital of Mali?":
        "Bamako sits on the Niger River and is one of the fastest-growing cities in Africa. Mali's ancient city of Timbuktu was once one of the world's great centers of Islamic scholarship and trans-Saharan gold trade.",

    "Capital of Burkina Faso?":
        "Ouagadougou (often shortened to 'Ouaga') hosts FESPACO, Africa's largest and most prestigious film festival. Burkina Faso means 'Land of Honest People' -- the name was adopted in 1984 to replace the colonial name Upper Volta.",

    "Capital of Chad?":
        "N'Djamena sits at the confluence of the Chari and Logone rivers near Lake Chad. The lake it borders has shrunk by 90% since the 1960s, turning what was once one of Africa's largest lakes into an environmental crisis.",

    "Capital of Central African Republic?":
        "Bangui sits on the Ubangi River across from the DR Congo. The Central African Republic is one of the least developed countries in the world, despite sitting atop significant diamond and gold deposits.",

    "Capital of Gabon?":
        "Libreville, meaning 'Free Town,' was founded by freed slaves in 1849, similar to Freetown in Sierra Leone and Monrovia in Liberia. Gabon's oil wealth has made it one of the more prosperous countries in sub-Saharan Africa.",

    "Capital of Republic of Congo?":
        "Brazzaville and Kinshasa face each other across the Congo River, making them the closest pair of national capitals in the world. Brazzaville was named after French-Italian explorer Pierre de Brazza.",

    "Capital of Mauritius?":
        "Port Louis was founded by the French in 1735 and named after King Louis XV. Mauritius was home to the dodo bird, which went extinct by 1681 -- less than a century after humans first arrived on the island.",

    "The Atacama Desert is in ___?":
        "The Atacama is the driest non-polar desert on Earth -- some weather stations there have never recorded rain. NASA tests Mars rovers in the Atacama because its soil is the closest analog to the Martian surface.",

    "The Niger River empties into the sea in ___?":
        "The Niger River's delta in southern Nigeria is one of the world's largest wetlands and sits atop enormous oil reserves. The river unusually flows away from the sea first (northeast into the Sahara) before turning south.",

    "The Zambezi River empties into the sea in ___?":
        "The Zambezi is Africa's fourth-longest river and flows through six countries before reaching the Indian Ocean in Mozambique. Its most famous feature is Victoria Falls, one of the Seven Natural Wonders of the World.",

    "Victoria Falls is on the border of Zambia and ___?":
        "Victoria Falls is about twice the height of Niagara Falls and over 1,700 meters wide. The local Tonga name is 'Mosi-oa-Tunya,' meaning 'The Smoke That Thunders,' for the spray visible from 50 km away.",

    "The Mekong River flows through how many countries?":
        "The Mekong flows through China, Myanmar, Laos, Thailand, Cambodia, and Vietnam. It is Southeast Asia's most important river, feeding over 60 million people and supporting the world's largest inland fishery.",

    "The highest capital city in the world is ___?":
        "La Paz sits at approximately 3,640 meters elevation, nestled in a canyon below the Altiplano. Visitors often experience altitude sickness upon arrival. Bolivia's constitutional capital is actually Sucre, but La Paz is the seat of government.",

    "The Faroe Islands belong to ___?":
        "The Faroe Islands are a self-governing territory of Denmark located between Norway, Iceland, and Scotland. With about 50,000 people and 70,000 sheep, the islands have more sheep than humans.",

    "The Azores archipelago belongs to ___?":
        "The Azores are nine volcanic islands in the mid-Atlantic, about 1,500 km west of mainland Portugal. They sit atop the Mid-Atlantic Ridge where the European, African, and North American tectonic plates meet.",

    "Capital of Kosovo?":
        "Pristina is the capital of Europe's newest state, which declared independence from Serbia in 2008. Kosovo's status remains disputed -- it is recognized by over 100 countries but not by Serbia, Russia, or China.",

    "Capital of Montenegro?":
        "Podgorica sits at the confluence of the Ribnica and Moraca rivers. Montenegro, whose name means 'Black Mountain,' has one of the world's most beautiful coastlines along the Adriatic, including the famous Bay of Kotor.",

    "Capital of Bosnia and Herzegovina?":
        "Sarajevo is known as the 'Jerusalem of Europe' for its centuries-old religious diversity, with mosques, churches, and synagogues in close proximity. The assassination of Archduke Franz Ferdinand here in 1914 triggered World War I.",

    "Capital of North Macedonia?":
        "Skopje was devastated by an earthquake in 1963 that destroyed 80% of the city. International aid rebuilt it with contributions from around the world, including designs by famous Japanese architect Kenzo Tange.",

    "Capital of Cyprus?":
        "Nicosia is the last divided capital in the world -- a UN buffer zone has split it between Greek Cypriots in the south and Turkish Cypriots in the north since 1974. The old walled city is shaped like a star.",

    "The Mariana Trench is in which ocean?":
        "The Mariana Trench is the deepest part of any ocean on Earth, plunging nearly 11 km below the surface. If Mount Everest were dropped into the trench, its peak would still be more than 2 km underwater.",

    "The longest river in Europe is the ___?":
        "The Volga flows 3,530 km through central Russia and drains an area home to about one-third of Russia's population. Russians call it 'Mother Volga' and it has been central to Russian culture, trade, and folklore for centuries.",

    "Capital of Suriname?":
        "Paramaribo's historic inner city is a UNESCO World Heritage Site, featuring a remarkable mix of Dutch colonial and Creole architecture. Suriname is the smallest country in South America and the only one where Dutch is the official language.",

    "Capital of Guyana?":
        "Georgetown sits below sea level, protected by a system of Dutch-built sea walls. Guyana is the only English-speaking country in South America and its name means 'Land of Many Waters' in an indigenous language.",

    "The Orinoco River is in ___?":
        "The Orinoco is Venezuela's lifeline, draining about 80% of the country. Its delta is one of the world's largest, and the river is connected to the Amazon basin via the Casiquiare canal -- a natural river that joins two major river systems.",

    "Capital of Bahrain?":
        "Manama sits on the northeastern tip of Bahrain island in the Persian Gulf. Bahrain was the first Gulf state to discover oil (in 1932) and has since diversified into banking, making it the financial hub of the Persian Gulf.",

    "Capital of Comoros?":
        "Moroni sits on Grande Comore island at the foot of Mount Karthala, one of the world's most active volcanoes. The Comoros archipelago sits between Madagascar and Mozambique and was an important stop on Indian Ocean trade routes.",

    "Capital of Benin?":
        "Porto-Novo is the official capital, but most government activities take place in Cotonou, Benin's largest city. Benin was the heart of the Kingdom of Dahomey, famous for its all-female warrior regiment, the Amazons.",

    "Capital of Togo?":
        "Lome is unusual for a capital -- it sits right on the border with Ghana, with the frontier running through the outskirts of the city. Togo is one of the smallest countries in Africa, barely 56 km wide at its narrowest.",

    "Capital of Guinea?":
        "Conakry occupies the Kaloum Peninsula and nearby islands on the Atlantic coast. Guinea was the first French colony in Africa to gain independence, voting 'No' in a 1958 French referendum, which prompted France to withdraw all support overnight.",

    "Capital of Guinea-Bissau?":
        "Bissau sits on the Geba River estuary and is the capital of one of the world's least developed nations. The country's Bijagos Archipelago off the coast is a UNESCO Biosphere Reserve with unique wildlife.",

    "Capital of Sierra Leone?":
        "Freetown was founded in 1792 as a settlement for freed African American and Caribbean slaves. The famous Cotton Tree in its center, under which freed slaves prayed upon arrival, still stands as a national symbol.",

    "Capital of Liberia?":
        "Monrovia is named after US President James Monroe and was founded by freed American slaves in 1822. Liberia and Ethiopia are the only two African countries never colonized by European powers.",

    "Capital of Gambia?":
        "Banjul sits on St. Mary's Island at the mouth of the Gambia River. The Gambia is the smallest country on mainland Africa, essentially a narrow strip of land on either side of the river, completely surrounded by Senegal.",

    "Capital of Cape Verde?":
        "Praia sits on Santiago, the largest island in this volcanic archipelago 570 km off West Africa. Cape Verde was uninhabited until Portuguese explorers settled it in the 15th century, making it a hub for the Atlantic slave trade.",

    "Capital of Equatorial Guinea?":
        "Malabo sits on the volcanic island of Bioko, about 40 km off the coast of Cameroon. Equatorial Guinea became one of sub-Saharan Africa's wealthiest nations per capita after oil was discovered in the 1990s.",

    "Capital of Burundi?":
        "Gitega replaced Bujumbura as Burundi's political capital in 2019, moving the seat of government inland. Burundi, along with Rwanda, is one of the smallest and most densely populated countries in Africa.",

    "Capital of Lesotho?":
        "Maseru sits on the Caledon River border with South Africa and is Lesotho's only large city. Lesotho is entirely above 1,000 meters elevation, earning it the nickname 'The Kingdom in the Sky.'",

    "Capital of Eswatini (Swaziland)?":
        "Mbabane is one of two capitals -- Lobamba serves as the traditional and legislative capital. Eswatini is one of the last absolute monarchies in the world, ruled by King Mswati III.",

    "Capital of Seychelles?":
        "Victoria on the island of Mahe is one of the smallest capital cities in the world by population. The Seychelles were uninhabited until French settlers arrived in 1770, and the islands are home to the world's largest tortoise population.",

    "Capital of Mauritania?":
        "Nouakchott was a tiny fishing village of about 200 people when it was chosen as the capital at independence in 1960. Today over a million people live there, many in sprawling informal settlements on the edge of the Sahara.",

    "Capital of Nauru?":
        "Yaren is the de facto capital of Nauru, the world's smallest island nation at just 21 square kilometers. Nauru was once wealthy from phosphate mining but is now one of the world's most economically struggling countries.",

    "Capital of Tuvalu?":
        "Funafuti is an atoll with a maximum elevation of just 4.6 meters, making Tuvalu one of the first nations that could disappear entirely due to rising sea levels. Its total population is about 11,000.",

    "Capital of Kiribati?":
        "South Tarawa, an atoll in the central Pacific, is one of the most densely populated places on Earth relative to its size. Kiribati spans 3.5 million square kilometers of ocean but has only 811 square kilometers of land.",

    "Capital of Marshall Islands?":
        "Majuro is an atoll that served as a US nuclear testing ground in the 1940s and 1950s. Nearby Bikini Atoll gave its name to the bikini swimsuit, introduced the same year as the nuclear tests there.",

    "Capital of Micronesia?":
        "Palikir is one of the world's smallest and least-known capitals, located on the island of Pohnpei. Nearby are the mysterious ruins of Nan Madol, an ancient city built on artificial islands sometimes called 'the Venice of the Pacific.'",

    "Capital of Palau?":
        "Ngerulmud replaced Koror as Palau's capital in 2006 and is one of the least populated capital cities in the world. Palau's Rock Islands, a UNESCO World Heritage Site, contain a marine lake filled with millions of non-stinging jellyfish.",

    "The world's largest delta is the ___?":
        "The Ganges-Brahmaputra Delta covers about 105,000 square kilometers across Bangladesh and India. It is formed by the sediment of two of Asia's mightiest rivers and is home to the Sundarbans, the world's largest mangrove forest.",

    "The longest river in South America is the ___?":
        "The Amazon carries more water than any other river on Earth -- about 20% of all fresh water discharged into the oceans. Some scientists argue it is also the world's longest river, narrowly edging out the Nile.",

    "The island of Borneo is shared by how many countries?":
        "Borneo is divided among Malaysia, Indonesia, and Brunei. It is the third-largest island in the world and contains some of the oldest rainforests on Earth, estimated at 130 million years old.",

    "The Sahel region borders which desert?":
        "The Sahel (Arabic for 'shore') is the semi-arid band south of the Sahara stretching from Senegal to Sudan. It acts as a transition zone between the desert and the savannas, and its fragile ecology is under constant threat.",

    "Capital of Malawi?":
        "Lilongwe replaced Zomba as Malawi's capital in 1975 because of its more central location. Malawi is called 'The Warm Heart of Africa' for its famously friendly people, and Lake Malawi contains more fish species than any other lake.",

    "Capital of Madagascar?":
        "Antananarivo, often shortened to 'Tana,' sits on hills at 1,280 meters elevation in the central highlands. Madagascar split from India about 88 million years ago, and its isolation created wildlife found nowhere else -- including over 100 species of lemur.",

    "Capital of Sao Tome and Principe?":
        "Sao Tome is the capital of Africa's smallest country, a tiny volcanic archipelago on the equator in the Gulf of Guinea. The islands were uninhabited until Portuguese explorers arrived in the 1470s and established sugar plantations.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 4 — Rivers and Seas
    # ══════════════════════════════════════════════════════════════════════════

    "The Kimberley Plateau is in ___?":
        "The Kimberley is one of Australia's last true wilderness areas, with a population density of fewer than 0.3 people per square kilometer. Its ancient Bungle Bungle Range features beehive-shaped sandstone towers over 350 million years old.",

    "The Carpathian Mountains span several countries including Romania and ___?":
        "The Carpathians arc 1,500 km across Central and Eastern Europe and contain Europe's largest remaining area of virgin forest. The range is home to Europe's largest populations of brown bears, wolves, and lynx.",

    "The Po River is in ___?":
        "The Po is Italy's longest river, flowing 652 km across the fertile Po Valley, which produces about 40% of Italy's agricultural output. The valley is also Italy's industrial heartland, home to Milan and Turin.",

    "The Loire River is in ___?":
        "The Loire is France's longest river at 1,012 km and its valley is famous for over 300 chateaux built by French nobility. The Loire Valley is often called 'the Garden of France' for its wine, fruit, and artichoke production.",

    "The Ebro River is in ___?":
        "The Ebro is Spain's longest river and flows into the Mediterranean. Its name comes from the ancient Iberian word for river, and the entire Iberian Peninsula takes its name from this waterway.",

    "The Elbe River flows through ___?":
        "The Elbe flows 1,091 km from the Czech mountains through Germany to the North Sea at Hamburg. During the Cold War, it roughly marked the border between East and West Germany.",

    "The Oder River forms the border between Germany and ___?":
        "The Oder-Neisse line became the German-Polish border after World War II, a decision made at the Potsdam Conference in 1945. Millions of Germans were expelled from east of this line.",

    "The Vistula River flows through ___?":
        "The Vistula is Poland's longest river at 1,047 km and flows through Krakow and Warsaw before reaching the Baltic Sea at Gdansk. It has been Poland's geographic backbone and main transportation artery for centuries.",

    "The Dnieper River flows through ___?":
        "The Dnieper is Ukraine's lifeline, flowing through Kyiv and providing hydroelectric power, irrigation, and drinking water for millions. It is the fourth-longest river in Europe at 2,200 km.",

    "The Don River flows into the ___?":
        "The Don flows into the shallow Sea of Azov, connected to the Black Sea by the Kerch Strait. The Don region is the homeland of the Cossacks, fierce horsemen who played a key role in Russian military history.",

    "The Sea of Azov is connected to the ___?":
        "The Sea of Azov is the shallowest sea in the world, with an average depth of only about 7 meters. It connects to the Black Sea through the narrow Kerch Strait, which Russia bridged in 2018.",

    "Lake Malawi borders Malawi, Tanzania, and ___?":
        "Lake Malawi (also called Lake Nyasa) contains more species of fish than any other lake on Earth -- over 1,000, most of them colorful cichlids found nowhere else. It is the third-largest lake in Africa.",

    "Lake Chad is shared by Chad, Niger, Nigeria, and ___?":
        "Lake Chad has shrunk by about 90% since the 1960s due to irrigation and climate change, turning from one of Africa's largest lakes into a fraction of its former self. It once covered an area larger than Lake Erie.",

    "The Limpopo River forms the border between South Africa and ___?":
        "The Limpopo flows in a great arc across southern Africa, and Rudyard Kipling described it as 'the great grey-green, greasy Limpopo River, all set about with fever trees' in his Just So Stories.",

    "The Orange River is in ___?":
        "The Orange is South Africa's longest river at 2,200 km and was named by Dutch colonists after the House of Orange. It forms part of the border between South Africa and Namibia before reaching the Atlantic.",

    "The Tigris and Euphrates rivers are in ___?":
        "The land between the Tigris and Euphrates -- 'Mesopotamia' (Greek for 'between two rivers') -- is where civilization began. Writing, the wheel, mathematics, and agriculture were all invented in this fertile crescent.",

    "The Jordan River flows into the ___?":
        "The Jordan River is only about 251 km long but is one of the most historically significant rivers in the world. In Christianity, Jesus was baptized in its waters; in Judaism, the Israelites crossed it to enter the Promised Land.",

    "The Indus River flows through ___?":
        "The Indus gave its name to India and to Hinduism, even though most of the river now flows through Pakistan. The Indus Valley Civilization (3300-1300 BC) was one of the world's first great urban cultures.",

    "The Brahmaputra River flows through ___?":
        "The Brahmaputra is one of the few rivers that flows from east to west. Known as the Tsangpo in Tibet, it makes a dramatic U-turn around a Himalayan peak and drops through the world's deepest gorge before entering Bangladesh.",

    "Lake Balaton is in ___?":
        "Lake Balaton is Central Europe's largest freshwater lake and Hungary's top holiday destination, known as the 'Hungarian Sea.' Its shallow warm waters (average depth just 3 meters) make it ideal for swimming.",

    "The Ionian Sea is between Greece and ___?":
        "The Ionian Sea was the stage for Homer's Odyssey, where Odysseus wandered for ten years trying to reach his home island of Ithaca. Its Greek islands, including Corfu and Zakynthos, are among the most beautiful in the Mediterranean.",

    "The Tyrrhenian Sea is west of ___?":
        "The Tyrrhenian Sea is bounded by Italy's western coast, Sicily, Sardinia, and Corsica. Its floor contains active underwater volcanoes, and the islands of Stromboli and Vulcano have erupted continuously for thousands of years.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 4 — Long-form questions
    # ══════════════════════════════════════════════════════════════════════════

    "Why did the discovery of gold and silver in the Americas in the 1500s ultimately weaken Spain rather than making it permanently dominant?":
        "Spain's flood of New World silver caused the Price Revolution -- prices across Europe doubled or tripled in a century. Spanish domestic industry withered because it was cheaper to buy foreign goods with silver than to manufacture locally.",

    "Which geographic feature of England meant that no English town was more than 70 miles from the sea or a navigable river, making the Industrial Revolution possible?":
        "England's deeply indented coastline and crisscrossing rivers meant raw materials and finished goods could be transported cheaply by water almost anywhere in the country. This natural transport network made factory production profitable.",

    "The term 'heartland theory,' formulated by Halford Mackinder in 1904, argued that whoever controlled the Eurasian heartland would dominate world power. What geographic area is the 'heartland'?":
        "Mackinder's heartland was the vast interior of Eurasia -- unreachable by naval power and rich in resources. He argued that railroads would unlock this region's potential, potentially creating a superpower immune to blockade.",

    "Venice, Genoa, and Pisa competed fiercely for Mediterranean trade in the Middle Ages. What geographic advantage gave Venice the ultimate edge?":
        "Venice controlled the Adriatic's northern exit, where goods could travel overland through the Brenner Pass to German markets in just days. Genoa and Pisa had to ship goods the long way around to reach the same customers.",

    "Why are resource-rich countries in the tropics often poorer than resource-poor temperate countries? This phenomenon is sometimes called the ___?":
        "The 'resource curse' or 'paradox of plenty' occurs when easy wealth from oil or minerals removes the incentive to build productive institutions, diversify the economy, or invest in education. Geography provides the resources; institutions determine outcomes.",

    "What geographic feature enabled the Dutch East India Company (VOC) to dominate Asian trade in the 17th century?":
        "Dutch navigator Hendrik Brouwer discovered in 1611 that sailing east along latitude 40 S from the Cape of Good Hope, riding the Roaring Forties westerlies, then turning north to Java, was far faster than hugging the African coast.",

    "The phrase 'whoever rules the sea rules trade; whoever rules trade rules the world's riches' was associated with which classical concept of maritime power?":
        "Thalassocracy dates to ancient Athens and was perfected by Venice, Portugal, the Netherlands, and Britain. Each controlled sea lanes rather than vast territory, proving that geographic chokepoints matter more than land area.",

    "Why did the construction of the transcontinental railroad (completed 1869) dramatically reduce the economic importance of San Francisco compared to what geography alone would predict?":
        "Before the railroad, San Francisco was the only gateway to California's gold and agricultural wealth. The railroad let goods flow directly between the Midwest and East Coast, reducing the need to ship everything by sea via San Francisco.",

    "What geographic conditions made Britain the world's leading exporter of cotton textiles in the early Industrial Revolution, despite producing no cotton itself?":
        "Lancashire's damp climate was perfect for cotton spinning (dry air causes thread to snap), while nearby coal powered the mills and Liverpool's port imported raw cotton and exported finished cloth. Geography aligned every factor.",

    "The economic geography concept of 'agglomeration' refers to why industries cluster in cities. The main benefit is ___?":
        "Alfred Marshall identified three agglomeration forces: a shared labor pool (workers can switch firms), specialized local suppliers, and knowledge spillovers (ideas travel faster between neighbors). Silicon Valley is the modern textbook example.",

    "Why did the invention of refrigerated shipping in the 1880s transform the economic geography of South America?":
        "Before refrigeration, Argentina's vast grasslands could only export dried beef, wool, and hides. Refrigerated ships suddenly let them export fresh meat to European tables, turning the Pampas into one of the world's wealthiest agricultural regions.",

    "In economic geography, the 'gravity model of trade' predicts that trade between two countries is proportional to their economic size and inversely proportional to their distance. This model predicts that ___?":
        "The gravity model consistently explains about 70-80% of all international trade patterns. Canada-US trade is the world's largest bilateral trading relationship precisely because they combine huge economies with shared borders.",

    "What geographic factor made Amsterdam the center of the Dutch Golden Age economy in the 17th century?":
        "Amsterdam's IJ waterway connected the city to the North Sea while the Rhine and Meuse rivers delivered goods from deep inside Europe. This position made it the natural warehouse of the continent.",

    "The 'North-South divide' in global economics refers to the general pattern that wealthy nations are in the Northern Hemisphere and poor ones in the South. Which of these geographic explanations for this pattern is most widely accepted?":
        "Jared Diamond's 'Guns, Germs, and Steel' thesis argues that Eurasia's east-west orientation allowed crops and livestock to spread along similar latitudes, while Africa and the Americas' north-south orientation created climate barriers to diffusion.",

    "Alfred Thayer Mahan's 1890 book 'The Influence of Sea Power upon History' argued that national greatness depended on ___?":
        "Mahan's book directly influenced the US, Germany, and Japan to build massive navies. He argued that six geographic factors -- position, physical conformation, extent of territory, population, national character, and government -- determined naval power.",

    "What physical geographic feature explains why Western Europe has proportionally more navigable rivers than Eastern Europe, contributing to its faster economic development?":
        "Western Europe's rivers flow from central mountain ranges toward the Atlantic, passing through temperate zones that keep them ice-free year-round. Eastern European rivers often freeze in winter or flow into landlocked seas.",

    "The geographic concept of 'corridor states' describes small nations positioned between great powers. Historically, which European nation best illustrates this concept?":
        "Belgium has been invaded by foreign armies more times than almost any country in history. Its flat terrain between France and Germany made it the preferred invasion route in both World Wars, earning it the grim title 'the cockpit of Europe.'",

    "The term 'rimland theory,' proposed by Nicholas Spykman in 1944 as a response to Mackinder's heartland theory, held that global power was controlled by ___?":
        "Spykman argued that the coastal fringe of Eurasia -- from Western Europe through the Middle East to East Asia -- was more important than the heartland. This theory directly influenced US Cold War strategy of containing the Soviet Union along this rim.",

    # ══════════════════════════════════════════════════════════════════════════
    # TIER 5 — Advanced Geographic Knowledge
    # ══════════════════════════════════════════════════════════════════════════

    "The Mariana Trench's deepest point (Challenger Deep) is approximately ___?":
        "Challenger Deep was first reached by Jacques Piccard and Don Walsh in the bathyscaphe Trieste in 1960, and by James Cameron solo in 2012. The water pressure at the bottom is over 1,000 times atmospheric pressure.",

    "Which country has the most time zones?":
        "France has 12 time zones thanks to its overseas territories scattered across the globe, from French Polynesia in the Pacific to Reunion in the Indian Ocean. Metropolitan France itself uses only one time zone.",

    "The prime meridian passes through ___?":
        "The prime meridian at 0 degrees longitude was established at the 1884 International Meridian Conference. It passes through the Royal Observatory in Greenwich, where a brass strip on the ground marks the exact line.",

    "The Tropic of Cancer is at latitude ___?":
        "The Tropic of Cancer marks the northernmost latitude where the sun can appear directly overhead, during the June solstice. It passes through Mexico, the Sahara, Saudi Arabia, India, and southern China.",

    "The Tropic of Capricorn is at latitude ___?":
        "The Tropic of Capricorn marks the southernmost latitude where the sun can appear directly overhead, during the December solstice. It passes through Australia, Chile, southern Brazil, and southern Africa.",

    "The Arctic Circle is at approximately latitude ___?":
        "The Arctic Circle marks the latitude above which the sun does not set on the summer solstice ('midnight sun') and does not rise on the winter solstice ('polar night'). About 4 million people live north of this line.",

    "The Antarctic Circle is at approximately latitude ___?":
        "The Antarctic Circle mirrors the Arctic Circle in the Southern Hemisphere. South of it, you can experience 24 hours of continuous daylight in December and continuous darkness in June.",

    "The Mercator projection distorts ___?":
        "On a Mercator map, Greenland appears the same size as Africa, when Africa is actually 14 times larger. The projection preserves direction (useful for navigation) at the cost of wildly distorting size near the poles.",

    "The Peters projection prioritizes ___?":
        "The Peters projection shows each country at its true relative size, revealing how much Mercator inflates northern nations. Africa, which looks smaller than Greenland on Mercator maps, is shown at its actual massive size.",

    "An enclave is a territory ___?":
        "Enclaves create unique political situations -- residents must cross foreign territory to reach the rest of their own country. The Cooch Behar district between India and Bangladesh once had the world's most complex enclave system, with enclaves within enclaves.",

    "Lesotho is an enclave within ___?":
        "Lesotho is one of only three countries completely surrounded by a single other country (Vatican City and San Marino are the other two). Every import and export must pass through South Africa.",

    "An exclave is a territory separated from its main country by ___?":
        "Famous exclaves include Alaska (separated from the US by Canada), Kaliningrad (separated from Russia by Lithuania and Poland), and Ceuta and Melilla (Spanish cities on the African coast surrounded by Morocco).",

    "Kaliningrad is a Russian exclave bordering ___?":
        "Kaliningrad was Konigsberg, the capital of East Prussia, until the Soviet Union annexed it after World War II and expelled the German population. It remains Russia's westernmost territory and only ice-free Baltic port.",

    "The latitude of the equator is ___?":
        "The equator circles the Earth at 40,075 km and passes through 13 countries. Standing on the equator, you are spinning eastward at about 1,670 km/h due to Earth's rotation, though you feel nothing.",

    "Mount Everest's height is approximately ___?":
        "China and Nepal jointly announced Everest's latest official height of 8,848.86 meters in 2020 after a collaborative resurvey. The mountain was named after Sir George Everest, a British Surveyor General of India.",

    "K2, the second-tallest mountain, is in ___?":
        "K2 sits on the China-Pakistan border in the Karakoram Range and has a much higher fatality rate than Everest -- about 1 in 4 climbers who attempt the summit die. Its name simply means it was the second peak catalogued in the Karakoram survey.",

    "The Sahara Desert covers approximately ___?":
        "The Sahara is roughly the same size as the United States or China. Remarkably, about 5,000-10,000 years ago it was a green savanna with lakes, rivers, and hippos -- a period called the 'African Humid Period.'",

    "Pangaea refers to ___?":
        "Pangaea (Greek for 'all land') began breaking apart about 200 million years ago. If you look at a map, you can see how South America's east coast fits into Africa's west coast like puzzle pieces -- evidence of their former union.",

    "The Himalayas were formed by the collision of which two tectonic plates?":
        "The Indian plate has been crashing into the Eurasian plate for about 50 million years, and the Himalayas are still rising about 5 mm per year as a result. Before the collision, a sea called Tethys separated the two landmasses.",

    "Nuku'alofa is the capital of ___?":
        "Tonga is the only Pacific island nation that was never formally colonized by a European power. The country consists of 169 islands, of which only 36 are inhabited, spread across 700,000 square kilometers of ocean.",

    "Funafuti is the capital of ___?":
        "Tuvalu has a total land area of just 26 square kilometers, making it the world's fourth-smallest country. With a maximum elevation of 4.6 meters, it faces existential threat from rising sea levels.",

    "The Torres Strait separates Australia from ___?":
        "The Torres Strait contains over 270 islands, many of them inhabited by Torres Strait Islander peoples with distinct cultures from Aboriginal Australians. The strait is only 150 km wide at its narrowest.",

    "The Drake Passage separates South America from ___?":
        "The Drake Passage is one of the roughest stretches of ocean on Earth, with waves that can reach 12 meters. It was named after Sir Francis Drake, whose ship was blown south through the area in 1578.",

    "The Kerguelen Islands are an overseas territory of ___?":
        "The Kerguelen Islands, sometimes called the 'Desolation Islands,' are among the most remote places on Earth -- over 3,300 km from the nearest inhabited land. They have no permanent population, only a rotating staff of scientists.",

    "Mount Kilimanjaro is in ___?":
        "Kilimanjaro is Africa's tallest peak at 5,895 meters and is the tallest freestanding mountain in the world (not part of a mountain range). Its glaciers have shrunk by about 85% since 1912 and may disappear entirely by 2040.",

    "Aconcagua is the highest peak in ___?":
        "Aconcagua stands at 6,961 meters, making it the tallest mountain outside Asia. It is the highest point in both the Western and Southern Hemispheres.",

    "Aconcagua is in ___?":
        "Aconcagua sits in western Argentina near the Chilean border in the Andes. Despite its height, it is technically not a difficult climb -- no ropes or technical equipment are required for the normal route.",

    "Mont Blanc is on the border of France and ___?":
        "Mont Blanc is Western Europe's highest peak at 4,808 meters. The Mont Blanc Tunnel underneath it, opened in 1965, connects France and Italy through 11.6 km of mountain.",

    "The Adriatic Sea separates Italy from ___?":
        "The Adriatic is remarkably shallow in its northern half, averaging only about 35 meters deep. Venice, built on wooden piles in a northern Adriatic lagoon, has been sinking into it for centuries.",

    "Tierra del Fuego is shared by Argentina and ___?":
        "Tierra del Fuego ('Land of Fire') was named by Ferdinand Magellan, who saw the fires of indigenous Selk'nam people as he sailed through the strait. It is the southernmost inhabited region before Antarctica.",

    "The Deccan Plateau is in ___?":
        "The Deccan Plateau covers most of southern India and is one of the oldest landmasses on Earth, with rocks dating back over 3 billion years. Its volcanic basalt deposits (the Deccan Traps) may have contributed to the dinosaurs' extinction.",

    "The Serengeti plain is in ___?":
        "The Serengeti hosts the world's largest terrestrial animal migration, with over 1.5 million wildebeest and hundreds of thousands of zebras trekking in a circular path following the rains. The name means 'endless plains' in Maasai.",

    "The Kalahari Desert is in ___?":
        "The Kalahari is technically a semi-arid savanna, not a true desert, receiving more rainfall than the Sahara. It has been home to the San (Bushmen) people for at least 20,000 years -- among the oldest continuous cultures on Earth.",

    "The Namib Desert is in ___?":
        "The Namib is considered the world's oldest desert, having been arid for at least 55 million years. Its towering red sand dunes, some over 300 meters tall, are among the highest in the world.",

    "The Altai Mountains span Russia, China, Mongolia, and ___?":
        "The Altai Mountains are where Siberia meets Central Asia. In 2012, scientists discovered the remains of a previously unknown human species, the Denisovans, in an Altai cave, revolutionizing our understanding of human evolution.",

    "The Oymyakon region of Russia holds the record for ___?":
        "Oymyakon recorded a temperature of -67.7 C in 1933. About 500 people live there year-round. Cars must be kept running continuously in winter because turning them off risks the engine freezing solid.",

    "The Aral Sea has mostly dried up due to ___?":
        "Soviet planners diverted the Amu Darya and Syr Darya rivers to irrigate cotton fields, causing one of the worst environmental disasters in history. The sea shrank from the world's fourth-largest lake to a fraction of its former size in just decades.",

    "The geographic North Pole's longitude is ___?":
        "At the North Pole, every direction is south, and all lines of longitude converge to a single point. Time zones become meaningless -- scientists at the North Pole conventionally use UTC (Coordinated Universal Time).",

    "The Coriolis effect causes winds to deflect which way in the Northern Hemisphere?":
        "The Coriolis effect occurs because the Earth rotates faster at the equator than at the poles. This deflection creates the major wind patterns (trade winds, westerlies, polar easterlies) and causes hurricanes to spin counterclockwise in the north.",

    "The Falkland Islands are controlled by ___?":
        "Argentina fought a 74-day war with Britain over the Falklands in 1982, losing about 650 soldiers. The islands' population of about 3,500 voted 99.8% to remain British in a 2013 referendum.",

    "The Dardanelles strait connects the Aegean Sea to the ___?":
        "The Sea of Marmara is the world's smallest sea, connecting the Dardanelles to the Bosphorus. Together, this waterway system is the only route for Russian warships to reach the Mediterranean from the Black Sea.",

    "The Suez Canal is approximately how long?":
        "The Suez Canal's 193 km length makes it one of the most heavily used shipping lanes in the world. A massive expansion in 2015 allowed two-way traffic along parts of the canal, doubling its capacity.",

    "The Panama Canal is approximately how long?":
        "At 82 km, the Panama Canal uses a system of locks to raise and lower ships 26 meters above sea level through Gatun Lake. A ship transit takes about 8-10 hours and saves a 15,000-km journey around South America.",

    "The deepest point in the Atlantic Ocean is the ___?":
        "The Puerto Rico Trench reaches 8,376 meters deep, making it the deepest point in the Atlantic. It sits at the boundary where the North American plate is subducting beneath the Caribbean plate.",

    "The Volga River flows into the ___?":
        "The Volga empties into the Caspian Sea through a vast delta that is one of Europe's most important wetlands for migratory birds. The Caspian is landlocked, so the Volga's water has no route to the ocean.",

    "The Congo River is the world's ___?":
        "The Congo reaches depths of over 220 meters in some places, far deeper than any other river. Its immense volume of water -- second only to the Amazon -- powers the Inga Falls, which has the greatest hydroelectric potential of any site on Earth.",

    "Cape Horn is the southernmost tip of ___?":
        "Rounding Cape Horn in a sailing ship was one of the most dangerous voyages in maritime history, with ferocious winds, massive waves, and icebergs. Many ships and thousands of sailors were lost attempting the passage.",

    "The world's largest hot desert is the ___?":
        "The Sahara was not always a desert -- cave paintings show hippos, crocodiles, and green savanna. The 'Green Sahara' period ended about 5,000 years ago, and the resulting drought may have driven people to the Nile Valley, sparking Egyptian civilization.",

    "The Wallace Line separates the fauna of Asia from ___?":
        "Alfred Russel Wallace noticed in the 1850s that animals on Bali were Asian (tigers, monkeys) while those on Lombok, just 35 km away, were Australasian (marsupials, cockatoos). The deep water between them prevented animal migration even during ice ages.",

    "The Zagros Mountains are in ___?":
        "The Zagros range stretches 1,500 km along Iran's western border and was the birthplace of some of the world's earliest farming communities. The mountains contain significant oil reserves trapped in their folded rock layers.",

    "The Hindu Kush mountain range is in ___?":
        "The Hindu Kush stretches 800 km through Afghanistan and Pakistan, with peaks exceeding 7,700 meters. The name may mean 'Hindu Killer,' referring to the deadly mountain passes that claimed many lives on ancient trade routes.",

    "The geographic term 'rain shadow' refers to ___?":
        "As moist air rises over a mountain, it cools and dumps rain on the windward side. By the time it descends the leeward side, it is dry. This is why the Atacama Desert exists right next to the wet Amazon -- the Andes create a massive rain shadow.",

    "The Tibetan Plateau is often called ___?":
        "The Tibetan Plateau averages 4,500 meters elevation across an area the size of Western Europe. Its glaciers feed Asia's major rivers (Yangtze, Mekong, Indus, Ganges), providing water for over 2 billion people downstream.",

    "The Ural Mountains divide Europe from ___?":
        "The Urals are among the oldest mountains in the world, having formed about 300 million years ago. They are relatively low (highest peak 1,895 m) and have never been a significant barrier to migration or invasion.",

    "The island of New Guinea is shared by Indonesia and ___?":
        "New Guinea is the world's second-largest island and one of the most linguistically diverse places on Earth, with over 1,000 languages. Its central highlands were unknown to the outside world until the 1930s.",

    "The deepest lake in Africa is ___?":
        "Lake Tanganyika reaches 1,470 meters deep and is the world's second-deepest lake after Baikal. Its extreme age (9-12 million years) has allowed hundreds of unique cichlid fish species to evolve in its waters.",

    "The Pampas grasslands are in ___?":
        "The Pampas are one of the most fertile grasslands on Earth, supporting Argentina's massive cattle industry and grain production. The gaucho cowboys who once roamed them are as iconic to Argentine culture as cowboys are to America.",

    "The Pantanal wetland, the world's largest, is in ___?":
        "The Pantanal covers about 150,000 square kilometers during the flood season -- larger than England. It has the highest concentration of wildlife in South America, including jaguars, giant otters, and hyacinth macaws.",

    "The Sundarbans mangrove forest is in ___?":
        "The Sundarbans is the largest mangrove forest in the world, covering 10,000 square kilometers across the Ganges delta. It is home to the Bengal tiger, which has uniquely adapted to swimming between islands and hunting in tidal waters.",

    "The Strait of Dover is the narrowest part of the ___?":
        "At the Strait of Dover, England and France are separated by just 34 km of some of the busiest shipping waters in the world. Captain Matthew Webb became the first person to swim across it in 1875, taking nearly 22 hours.",

    "The Gulf Stream is a warm ocean current in the ___?":
        "The Gulf Stream moves about 30 million cubic meters of water per second -- more than all the world's rivers combined. It carries warm water from the tropics northeastward, keeping European ports ice-free year-round.",

    "The Humboldt Current flows along the coast of ___?":
        "The cold Humboldt Current brings nutrient-rich water from the deep ocean to the surface, creating one of the world's most productive fishing grounds off Peru and Chile. It also makes coastal Peru much cooler and drier than expected for its tropical latitude.",

    "The geographic term 'taiga' refers to ___?":
        "The taiga (also called boreal forest) is the world's largest land biome, stretching across Russia, Canada, and Scandinavia. It stores more carbon than all tropical and temperate forests combined.",

    "The Caucasus Mountains separate Europe from ___?":
        "The Caucasus region between the Black Sea and Caspian Sea is one of the most linguistically diverse places on Earth, with over 50 distinct languages. Mount Elbrus in the Caucasus, at 5,642 m, is Europe's highest peak.",

    "The Huang He (Yellow River) is in ___?":
        "The Yellow River gets its color from loess -- fine yellow silt -- that it carries from China's interior. Called 'China's Sorrow' for its devastating floods, it has changed course drastically at least 26 times in recorded history.",

    "The Irrawaddy River flows through ___?":
        "The Irrawaddy is Myanmar's most important river, flowing 2,170 km from the Himalayas to the Andaman Sea. It is lined with thousands of ancient Buddhist pagodas, especially around the former capital of Bagan.",

    "The Three Gorges Dam is on which river?":
        "The Three Gorges Dam on the Yangtze is the world's largest hydroelectric dam, generating 22,500 megawatts. Building it required displacing 1.3 million people and submerging hundreds of historical sites.",

    "The Rub al Khali (Empty Quarter) is in ___?":
        "The Rub al Khali covers 650,000 square kilometers of the Arabian Peninsula and is the largest continuous sand desert in the world. Temperatures can exceed 55 C, and parts of it were not crossed by Westerners until 1931.",

    "The world's largest archipelago by number of islands is ___?":
        "Indonesia comprises over 17,000 islands stretching 5,100 km from east to west. If you superimposed it on a map of Europe, it would stretch from Ireland to Iran. About 6,000 of its islands are inhabited.",

    "The Lake Assal in Djibouti is ___?":
        "Lake Assal sits 155 meters below sea level and is the saltiest lake outside Antarctica, with salinity ten times that of the ocean. Local Afar people have harvested its salt for trade for centuries.",

    "The geographic poles experience up to how much continuous daylight in summer?":
        "The six months of continuous summer daylight at the poles occur because Earth's 23.5-degree axial tilt keeps the pole pointed toward the sun for half the year. At the equinoxes, the entire globe gets equal day and night.",

    "The Meseta is the central plateau of ___?":
        "The Meseta covers about 40% of Spain's land area and sits at an average elevation of 600-700 meters. Its harsh continental climate (freezing winters, scorching summers) inspired the saying 'Nine months of winter and three of hell.'",

    "The Alborz mountain range is in ___?":
        "The Alborz range stretches along Iran's northern coast, trapping moisture from the Caspian Sea and creating lush green forests on one side and arid desert on the other. Mount Damavand (5,610 m) is the highest volcano in Asia.",

    "The Tian Shan mountain range spans China and ___?":
        "The Tian Shan (meaning 'Celestial Mountains' in Chinese) stretch 2,500 km across Central Asia. Their glaciers feed the rivers that sustain the oasis cities of the Silk Road, including Samarkand and Kashgar.",

    "The Pamir Mountains are primarily located in which country?":
        "The Pamirs are called 'the Roof of the World' and meet four other major ranges (Tian Shan, Karakoram, Kunlun, Hindu Kush) at the 'Pamir Knot.' Marco Polo described crossing them in the 13th century.",

    "The Hindu Kush ranges from Afghanistan into ___?":
        "The Hindu Kush's Khyber Pass has been the gateway between Central and South Asia for millennia, used by Alexander the Great, Genghis Khan, and countless armies and traders. It reaches 1,070 meters at its highest point.",

    "The Drakensberg mountains are in ___?":
        "The Drakensberg (meaning 'Dragon Mountains' in Afrikaans) form a dramatic escarpment rising to 3,482 meters. The range contains San rock art dating back thousands of years and is a UNESCO World Heritage Site.",

    "The Blue Nile originates in ___?":
        "The Blue Nile springs from Lake Tana in the Ethiopian Highlands and provides about 80% of the Nile's total water during flood season. Ethiopia's Grand Renaissance Dam on the Blue Nile is Africa's largest hydroelectric project.",

    "The White Nile originates near ___?":
        "The White Nile's ultimate source was one of geography's greatest mysteries until the 19th century. Explorers Speke and Burton, Stanley and Livingstone all sought it. It rises from streams feeding Lake Victoria in the mountains of Burundi.",

    "The Blue Nile and White Nile meet in ___?":
        "The two Niles converge at Khartoum, Sudan, creating a dramatic visual: the Blue Nile's sediment-laden water runs alongside the clearer White Nile for several kilometers before mixing. From here, the united Nile flows north through Egypt.",

    "The Okavango Delta is in ___?":
        "The Okavango is the world's largest inland delta -- a river that empties into the Kalahari Desert rather than the ocean. Its annual flood transforms dry savanna into a lush wetland teeming with elephants, hippos, and crocodiles.",

    "The world's highest plateau, the Tibetan Plateau, has an average elevation of ___?":
        "At 4,500 meters average elevation, the Tibetan Plateau is higher than most mountains in Europe. The thin air at this altitude contains about 40% less oxygen than at sea level, and the plateau's mass actually bends jet stream patterns.",

    "The Mato Grosso Plateau is in ___?":
        "Mato Grosso means 'Thick Forest' in Portuguese, though much of it has been cleared for soybean farming and cattle ranching. The plateau is a major watershed, with rivers flowing north to the Amazon and south to the Parana.",

    "Death Valley in California holds the world temperature record for ___?":
        "Death Valley recorded 56.7 C (134 F) on July 10, 1913, the highest reliably recorded air temperature on Earth. The valley's below-sea-level elevation, narrow shape, and dark rock absorb and trap heat like an oven.",

    "The geographic term 'fjord' describes ___?":
        "Norway's fjords were carved by glaciers during ice ages, creating dramatic waterways up to 1,300 meters deep flanked by sheer cliffs. The word 'fjord' comes from Old Norse and is related to the English word 'ford.'",

    "The geographic term 'atoll' describes ___?":
        "Atolls form when a volcanic island sinks below the ocean while its surrounding coral reef continues to grow upward. Charles Darwin first explained this process in 1842, and modern drilling confirmed his theory.",

    "The Coriolis effect deflects winds to the left in the ___?":
        "The leftward deflection in the Southern Hemisphere means that cyclones spin clockwise there, opposite to the Northern Hemisphere. This is also why toilets do NOT actually flush in opposite directions -- that is a myth too small-scale for Coriolis to affect.",

    "The deepest point in the Indian Ocean is the ___?":
        "The Java Trench (also called Sunda Trench) reaches 7,290 meters deep and runs along the southern coast of Indonesia's islands. It marks where the Australian plate dives beneath the Eurasian plate, causing the region's frequent earthquakes.",

    "The Faeroe Islands are located between Norway and ___?":
        "The Faeroes' 18 islands support about 54,000 people and nearly 80,000 sheep -- the name 'Faroe' likely derives from Old Norse for 'sheep islands.' The islands have been inhabited since at least the 9th century by Norse settlers.",

    "The Sargasso Sea is unique in that it has no ___?":
        "The Sargasso Sea is the only sea on Earth defined entirely by ocean currents rather than land. Bounded by the Gulf Stream and other Atlantic currents, it is filled with floating Sargassum seaweed and is the spawning ground of European and American eels.",

    "The Banda Sea is part of which ocean?":
        "The Banda Sea sits within the Indonesian archipelago and is part of the western Pacific. Its extraordinary depth (up to 7,440 m) and volcanic islands make it one of the most geologically active bodies of water on Earth.",

    "The geographic term 'isohyet' refers to a line connecting points of equal ___?":
        "Isohyets are essential tools for agricultural planning and water resource management. On an isohyet map, you can see at a glance where droughts threaten and where floods are most likely.",

    "The geographic term 'isotherm' refers to a line connecting points of equal ___?":
        "Isotherms on weather maps show temperature patterns and are key to forecasting. The 10 C July isotherm roughly marks the boundary between the subarctic and temperate zones, and the treeline closely follows it.",

    "The geographic term 'isobar' refers to a line connecting points of equal ___?":
        "Closely spaced isobars on a weather map indicate steep pressure gradients and strong winds. Meteorologists use isobar patterns to identify and track storms, high-pressure systems, and frontal boundaries.",

    "The world's longest submarine mountain range is the ___?":
        "The Mid-Atlantic Ridge stretches about 65,000 km through the center of the Atlantic and is the longest mountain range on Earth. Iceland is one of the few places where this underwater ridge rises above the surface.",

    "The Laurentian Abyss is in the ___?":
        "The Laurentian Abyss is a deep underwater valley in the North Atlantic near the mouth of the Gulf of St. Lawrence. It reaches depths of about 6,000 meters and was featured (loosely) in the film 'The Abyss.'",

    "The geographic term 'peninsula' derives from Latin meaning ___?":
        "From Latin 'paene' (almost) + 'insula' (island), a peninsula is literally 'almost an island.' Florida, Italy, Korea, India, and Scandinavia are all large peninsulas whose shapes define their regions.",

    "The Tropic of Cancer passes through which US state?":
        "The Tropic of Cancer clips the southern tip of the Big Island of Hawaii. This makes Hawaii the only US state where the sun can be directly overhead, which happens around the summer solstice.",

    "The Antarctic ice sheet contains approximately what fraction of Earth's fresh water?":
        "If the Antarctic ice sheet melted entirely, global sea levels would rise about 58 meters, flooding every coastal city on Earth. The ice sheet has been stable for about 34 million years but is now losing mass due to warming.",
}


def main() -> None:
    with open(SRC, "r", encoding="utf-8") as f:
        questions = json.load(f)

    added = 0
    skipped_already = 0
    missing = []

    for q in questions:
        if "context" in q:
            skipped_already += 1
            continue

        text = q["question"]
        if text in CONTEXTS:
            q["context"] = CONTEXTS[text]
            added += 1
        else:
            missing.append(text)

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    print(f"Done.  Added context to {added} questions.")
    print(f"Already had context: {skipped_already}")
    if missing:
        print(f"\nWARNING — {len(missing)} questions had no mapping:")
        for m in missing:
            print(f"  - {m}")
    else:
        print("All questions now have context.")


if __name__ == "__main__":
    main()
