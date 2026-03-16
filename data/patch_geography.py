#!/usr/bin/env python3
"""
patch_geography.py
Appends new geography questions to bring each tier to exactly 100 questions (500 total).
Reads existing geography.json, deduplicates by question text, appends new questions, writes back.
"""

import json
import sys
from pathlib import Path

DATA_PATH = Path(__file__).parent / "questions" / "geography.json"

NEW_QUESTIONS = [
    # ── TIER 1 additions (need 7 more to reach 100) ───────────────────────────
    {"tier": 1, "question": "Capital of Poland?", "answer": "Warsaw",
     "choices": ["Krakow", "Warsaw", "Gdansk", "Wroclaw"]},
    # ^ duplicate guard will skip if already present

    {"tier": 1, "question": "Which continent is Mexico on?", "answer": "North America",
     "choices": ["South America", "North America", "Central America", "Europe"]},
    {"tier": 1, "question": "The Himalaya mountain range is in which continent?", "answer": "Asia",
     "choices": ["Africa", "Europe", "Asia", "South America"]},
    {"tier": 1, "question": "Capital of Turkey?", "answer": "Ankara",
     "choices": ["Istanbul", "Ankara", "Izmir", "Bursa"]},
    {"tier": 1, "question": "Which ocean lies between Europe and North America?", "answer": "Atlantic Ocean",
     "choices": ["Pacific Ocean", "Atlantic Ocean", "Indian Ocean", "Arctic Ocean"]},
    {"tier": 1, "question": "The longest river in Africa is the ___?", "answer": "Nile",
     "choices": ["Congo", "Nile", "Niger", "Zambezi"]},
    {"tier": 1, "question": "Which country is the largest in Africa by area?", "answer": "Algeria",
     "choices": ["Sudan", "Algeria", "Democratic Republic of Congo", "Libya"]},
    {"tier": 1, "question": "Capital of South Korea?", "answer": "Seoul",
     "choices": ["Busan", "Incheon", "Seoul", "Daegu"]},
    {"tier": 1, "question": "The world's second most populous country is ___?", "answer": "India",
     "choices": ["United States", "India", "Indonesia", "Brazil"]},
    {"tier": 1, "question": "Which continent is the smallest by area?", "answer": "Australia/Oceania",
     "choices": ["Europe", "South America", "Australia/Oceania", "Antarctica"]},
    {"tier": 1, "question": "Capital of Nigeria?", "answer": "Abuja",
     "choices": ["Lagos", "Kano", "Abuja", "Ibadan"]},

    # ── TIER 2 additions (need 13 more to reach 100) ──────────────────────────
    {"tier": 2, "question": "Capital of Honduras?", "answer": "Tegucigalpa",
     "choices": ["San Pedro Sula", "Tegucigalpa", "La Ceiba", "Choloma"]},
    {"tier": 2, "question": "Capital of El Salvador?", "answer": "San Salvador",
     "choices": ["Santa Ana", "San Salvador", "San Miguel", "Soyapango"]},
    {"tier": 2, "question": "Capital of Nicaragua?", "answer": "Managua",
     "choices": ["León", "Managua", "Granada", "Masaya"]},
    {"tier": 2, "question": "Capital of Costa Rica?", "answer": "San José",
     "choices": ["Alajuela", "San José", "Cartago", "Heredia"]},
    {"tier": 2, "question": "Capital of Panama?", "answer": "Panama City",
     "choices": ["Colón", "Panama City", "David", "La Chorrera"]},
    {"tier": 2, "question": "The Volga River flows into the ___?", "answer": "Caspian Sea",
     "choices": ["Black Sea", "Baltic Sea", "Caspian Sea", "Aral Sea"]},
    {"tier": 2, "question": "The Murray-Darling river system is in ___?", "answer": "Australia",
     "choices": ["New Zealand", "Australia", "South Africa", "Brazil"]},
    {"tier": 2, "question": "The Ganges River flows through ___?", "answer": "India",
     "choices": ["Pakistan", "India", "Bangladesh", "Nepal"]},
    {"tier": 2, "question": "The Indus River flows primarily through ___?", "answer": "Pakistan",
     "choices": ["India", "Pakistan", "Afghanistan", "Iran"]},
    {"tier": 2, "question": "Which two countries share Niagara Falls?", "answer": "US and Canada",
     "choices": ["US and Mexico", "US and Canada", "Canada and UK", "US and UK"]},
    {"tier": 2, "question": "The highest mountain in Africa is ___?", "answer": "Mount Kilimanjaro",
     "choices": ["Mount Kenya", "Mount Kilimanjaro", "Ras Dashen", "Mount Elgon"]},
    {"tier": 2, "question": "Capital of Cuba?", "answer": "Havana",
     "choices": ["Santiago de Cuba", "Havana", "Camagüey", "Holguín"]},
    {"tier": 2, "question": "The Tigris and Euphrates rivers flow through ___?", "answer": "Iraq",
     "choices": ["Iran", "Iraq", "Syria", "Turkey"]},
    {"tier": 2, "question": "Lake Superior is on the border of the US and ___?", "answer": "Canada",
     "choices": ["Mexico", "Canada", "Greenland", "Cuba"]},
    # (Iberian Peninsula and Ethiopia capital already in existing — omitted)

    # ── TIER 3 additions (need 31 more to reach 100) ──────────────────────────
    {"tier": 3, "question": "Capital of Wisconsin?", "answer": "Madison",
     "choices": ["Milwaukee", "Madison", "Green Bay", "Racine"]},
    {"tier": 3, "question": "Capital of Missouri?", "answer": "Jefferson City",
     "choices": ["St. Louis", "Kansas City", "Jefferson City", "Springfield"]},
    {"tier": 3, "question": "Capital of Indiana?", "answer": "Indianapolis",
     "choices": ["Fort Wayne", "Evansville", "Indianapolis", "South Bend"]},
    {"tier": 3, "question": "Capital of Kentucky?", "answer": "Frankfort",
     "choices": ["Louisville", "Lexington", "Frankfort", "Bowling Green"]},
    {"tier": 3, "question": "Capital of Alabama?", "answer": "Montgomery",
     "choices": ["Birmingham", "Huntsville", "Montgomery", "Mobile"]},
    {"tier": 3, "question": "Capital of South Carolina?", "answer": "Columbia",
     "choices": ["Charleston", "Columbia", "Greenville", "Spartanburg"]},
    {"tier": 3, "question": "Capital of Maryland?", "answer": "Annapolis",
     "choices": ["Baltimore", "Annapolis", "Rockville", "Frederick"]},
    {"tier": 3, "question": "Capital of Hawaii?", "answer": "Honolulu",
     "choices": ["Hilo", "Honolulu", "Kailua", "Maui"]},
    {"tier": 3, "question": "The Pyrenees Mountains form the border between France and ___?", "answer": "Spain",
     "choices": ["Italy", "Spain", "Andorra", "Portugal"]},
    {"tier": 3, "question": "The Carpathian Mountains are primarily in ___?", "answer": "Romania",
     "choices": ["Poland", "Romania", "Ukraine", "Slovakia"]},
    {"tier": 3, "question": "The Black Sea is bordered to the north by ___?", "answer": "Ukraine",
     "choices": ["Russia", "Ukraine", "Bulgaria", "Romania"]},
    {"tier": 3, "question": "Which country is completely surrounded by Italy?", "answer": "San Marino",
     "choices": ["Vatican City", "San Marino", "Monaco", "Andorra"]},
    {"tier": 3, "question": "Which country is completely surrounded by France?", "answer": "Monaco",
     "choices": ["Andorra", "Monaco", "Luxembourg", "Liechtenstein"]},
    {"tier": 3, "question": "Liechtenstein is bordered by Switzerland and ___?", "answer": "Austria",
     "choices": ["Germany", "Austria", "Italy", "France"]},
    {"tier": 3, "question": "The island of Sri Lanka is off the southern tip of ___?", "answer": "India",
     "choices": ["Bangladesh", "India", "Myanmar", "Indonesia"]},
    {"tier": 3, "question": "Taiwan is an island off the coast of ___?", "answer": "China",
     "choices": ["Japan", "China", "Philippines", "Vietnam"]},
    {"tier": 3, "question": "The island of Borneo is primarily owned by ___?", "answer": "Indonesia",
     "choices": ["Malaysia", "Indonesia", "Brunei", "Philippines"]},
    {"tier": 3, "question": "Which sea lies between Italy and the Balkans?", "answer": "Adriatic Sea",
     "choices": ["Tyrrhenian Sea", "Adriatic Sea", "Ionian Sea", "Aegean Sea"]},
    {"tier": 3, "question": "The Aegean Sea is between Greece and ___?", "answer": "Turkey",
     "choices": ["Bulgaria", "Turkey", "Cyprus", "Lebanon"]},
    {"tier": 3, "question": "Capital of Ivory Coast (Côte d'Ivoire)?", "answer": "Yamoussoukro",
     "choices": ["Abidjan", "Yamoussoukro", "Bouaké", "Daloa"]},
    {"tier": 3, "question": "Capital of Guinea?", "answer": "Conakry",
     "choices": ["Freetown", "Conakry", "Monrovia", "Bamako"]},
    {"tier": 3, "question": "Capital of Sierra Leone?", "answer": "Freetown",
     "choices": ["Monrovia", "Freetown", "Conakry", "Banjul"]},
    {"tier": 3, "question": "Capital of Liberia?", "answer": "Monrovia",
     "choices": ["Freetown", "Monrovia", "Abidjan", "Accra"]},
    {"tier": 3, "question": "Capital of Togo?", "answer": "Lomé",
     "choices": ["Accra", "Lomé", "Cotonou", "Abidjan"]},
    {"tier": 3, "question": "Capital of Benin?", "answer": "Porto-Novo",
     "choices": ["Cotonou", "Porto-Novo", "Lomé", "Accra"]},
    {"tier": 3, "question": "Capital of Burundi?", "answer": "Gitega",
     "choices": ["Bujumbura", "Gitega", "Ngozi", "Muyinga"]},
    {"tier": 3, "question": "The Strait of Hormuz connects the Persian Gulf to the ___?", "answer": "Gulf of Oman",
     "choices": ["Red Sea", "Gulf of Oman", "Arabian Sea", "Bay of Bengal"]},
    {"tier": 3, "question": "Which mountain range separates Europe from Asia in Russia?", "answer": "Ural Mountains",
     "choices": ["Caucasus Mountains", "Ural Mountains", "Altai Mountains", "Carpathian Mountains"]},
    {"tier": 3, "question": "The Yucatán Peninsula is in ___?", "answer": "Mexico",
     "choices": ["Guatemala", "Mexico", "Belize", "Cuba"]},
    {"tier": 3, "question": "Lake Tanganyika is on the border of Tanzania and ___?", "answer": "Democratic Republic of Congo",
     "choices": ["Uganda", "Democratic Republic of Congo", "Rwanda", "Zambia"]},
    {"tier": 3, "question": "Capital of Sudan?", "answer": "Khartoum",
     "choices": ["Omdurman", "Khartoum", "Port Sudan", "Kassala"]},
    {"tier": 3, "question": "Capital of Mozambique?", "answer": "Maputo",
     "choices": ["Beira", "Maputo", "Nampula", "Quelimane"]},
    {"tier": 3, "question": "The Deccan Plateau is in ___?", "answer": "India",
     "choices": ["Pakistan", "India", "Sri Lanka", "Bangladesh"]},

    # ── TIER 4 additions (need 44 more to reach 100) ──────────────────────────
    {"tier": 4, "question": "Capital of Kiribati?", "answer": "South Tarawa",
     "choices": ["Funafuti", "South Tarawa", "Apia", "Port Vila"]},
    {"tier": 4, "question": "Capital of Tuvalu?", "answer": "Funafuti",
     "choices": ["South Tarawa", "Funafuti", "Yaren", "Ngerulmud"]},
    {"tier": 4, "question": "Capital of Nauru?", "answer": "Yaren",
     "choices": ["South Tarawa", "Yaren", "Funafuti", "Apia"]},
    {"tier": 4, "question": "Capital of Palau?", "answer": "Ngerulmud",
     "choices": ["Koror", "Ngerulmud", "Palikir", "Majuro"]},
    {"tier": 4, "question": "Capital of Marshall Islands?", "answer": "Majuro",
     "choices": ["Palikir", "Majuro", "Yaren", "Funafuti"]},
    {"tier": 4, "question": "Capital of Micronesia?", "answer": "Palikir",
     "choices": ["Ngerulmud", "Palikir", "Majuro", "Honiara"]},
    {"tier": 4, "question": "Which country owns Réunion Island?", "answer": "France",
     "choices": ["Portugal", "France", "United Kingdom", "Spain"]},
    {"tier": 4, "question": "The island of Corsica belongs to ___?", "answer": "France",
     "choices": ["Italy", "France", "Spain", "Monaco"]},
    {"tier": 4, "question": "The island of Sardinia belongs to ___?", "answer": "Italy",
     "choices": ["France", "Italy", "Spain", "Croatia"]},
    {"tier": 4, "question": "The island of Sicily belongs to ___?", "answer": "Italy",
     "choices": ["Tunisia", "Italy", "Malta", "Greece"]},
    {"tier": 4, "question": "Which country owns the Galápagos Islands?", "answer": "Ecuador",
     "choices": ["Peru", "Ecuador", "Colombia", "Chile"]},
    {"tier": 4, "question": "The Falkland Islands are administered by ___?", "answer": "United Kingdom",
     "choices": ["Argentina", "United Kingdom", "Chile", "Brazil"]},
    {"tier": 4, "question": "Which country has the largest land area in Africa?", "answer": "Algeria",
     "choices": ["Sudan", "Algeria", "Libya", "Democratic Republic of Congo"]},
    {"tier": 4, "question": "Which country has the largest population in Africa?", "answer": "Nigeria",
     "choices": ["Ethiopia", "Nigeria", "Egypt", "Democratic Republic of Congo"]},
    {"tier": 4, "question": "The highest point in North America is ___?", "answer": "Denali",
     "choices": ["Mount Logan", "Denali", "Pico de Orizaba", "Mount Whitney"]},
    {"tier": 4, "question": "Denali (Mount McKinley) is in which US state?", "answer": "Alaska",
     "choices": ["Montana", "Alaska", "Colorado", "Wyoming"]},
    {"tier": 4, "question": "The highest point in Australia is ___?", "answer": "Mount Kosciuszko",
     "choices": ["Mount Bartle Frere", "Mount Kosciuszko", "Blue Mountain", "Mount Bogong"]},
    {"tier": 4, "question": "The lowest point in Australia is ___?", "answer": "Lake Eyre",
     "choices": ["Lake Frome", "Lake Eyre", "Lake Gairdner", "Lake Torrens"]},
    {"tier": 4, "question": "Which country is Svalbard an archipelago of?", "answer": "Norway",
     "choices": ["Denmark", "Norway", "Sweden", "Russia"]},
    {"tier": 4, "question": "New Caledonia is an overseas territory of ___?", "answer": "France",
     "choices": ["Australia", "France", "United Kingdom", "New Zealand"]},
    {"tier": 4, "question": "French Guiana is an overseas region of ___?", "answer": "France",
     "choices": ["Brazil", "France", "Portugal", "Netherlands"]},
    {"tier": 4, "question": "Which country owns the island of Madeira?", "answer": "Portugal",
     "choices": ["Spain", "Portugal", "Morocco", "France"]},
    {"tier": 4, "question": "The Rio de la Plata estuary separates Argentina from ___?", "answer": "Uruguay",
     "choices": ["Brazil", "Uruguay", "Paraguay", "Bolivia"]},
    {"tier": 4, "question": "The Pantanal wetland is primarily in ___?", "answer": "Brazil",
     "choices": ["Bolivia", "Brazil", "Argentina", "Paraguay"]},
    {"tier": 4, "question": "The Okavango Delta is in ___?", "answer": "Botswana",
     "choices": ["Namibia", "Botswana", "Zambia", "Zimbabwe"]},
    {"tier": 4, "question": "The world's largest hot desert is the ___?", "answer": "Sahara",
     "choices": ["Arabian Desert", "Sahara", "Gobi Desert", "Great Victoria Desert"]},
    {"tier": 4, "question": "The Barents Sea is part of which ocean?", "answer": "Arctic Ocean",
     "choices": ["Atlantic Ocean", "Arctic Ocean", "Pacific Ocean", "Indian Ocean"]},
    {"tier": 4, "question": "The Labrador Sea is between Canada and ___?", "answer": "Greenland",
     "choices": ["Iceland", "Greenland", "Norway", "Ireland"]},
    {"tier": 4, "question": "The Timor Sea separates Australia from ___?", "answer": "Timor-Leste",
     "choices": ["Indonesia", "Timor-Leste", "Papua New Guinea", "Malaysia"]},
    {"tier": 4, "question": "Capital of Equatorial Guinea?", "answer": "Malabo",
     "choices": ["Bata", "Malabo", "Ebebiyín", "Mongomo"]},
    {"tier": 4, "question": "Capital of São Tomé and Príncipe?", "answer": "São Tomé",
     "choices": ["Príncipe", "São Tomé", "Malabo", "Libreville"]},
    {"tier": 4, "question": "Capital of Cape Verde?", "answer": "Praia",
     "choices": ["Mindelo", "Praia", "Assomada", "Santa Maria"]},
    {"tier": 4, "question": "Capital of Gambia?", "answer": "Banjul",
     "choices": ["Serekunda", "Banjul", "Brikama", "Farafenni"]},
    {"tier": 4, "question": "Capital of Guinea-Bissau?", "answer": "Bissau",
     "choices": ["Bafatá", "Bissau", "Gabu", "Cacheu"]},
    {"tier": 4, "question": "Capital of Eswatini (Swaziland)?", "answer": "Mbabane",
     "choices": ["Manzini", "Mbabane", "Lobamba", "Siteki"]},
    {"tier": 4, "question": "Which country borders the most African countries?", "answer": "Democratic Republic of Congo",
     "choices": ["Sudan", "Democratic Republic of Congo", "Ethiopia", "Tanzania"]},
    {"tier": 4, "question": "The Caucasus Mountains separate Russia from ___?", "answer": "Georgia and Azerbaijan",
     "choices": ["Turkey and Iran", "Georgia and Azerbaijan", "Armenia and Turkey", "Ukraine and Moldova"]},
    {"tier": 4, "question": "The Strait of Dover separates England from ___?", "answer": "France",
     "choices": ["Belgium", "France", "Netherlands", "Ireland"]},
    {"tier": 4, "question": "Which country has the most UNESCO World Heritage Sites?", "answer": "Italy",
     "choices": ["China", "Italy", "Spain", "France"]},
    {"tier": 4, "question": "The mouth of the Amazon River is in which Brazilian state?", "answer": "Pará",
     "choices": ["Amazonas", "Pará", "Maranhão", "Amapá"]},
    {"tier": 4, "question": "The Iguazu Falls are on the border of Brazil and ___?", "answer": "Argentina",
     "choices": ["Paraguay", "Argentina", "Uruguay", "Bolivia"]},
    {"tier": 4, "question": "The Kola Peninsula is in ___?", "answer": "Russia",
     "choices": ["Norway", "Russia", "Finland", "Sweden"]},
    {"tier": 4, "question": "The Kamchatka Peninsula is in ___?", "answer": "Russia",
     "choices": ["Japan", "Russia", "China", "North Korea"]},
    {"tier": 4, "question": "Which ocean does the Lena River flow into?", "answer": "Arctic Ocean",
     "choices": ["Pacific Ocean", "Arctic Ocean", "Indian Ocean", "Atlantic Ocean"]},

    # ── TIER 5 additions (need 47 more to reach 100) ──────────────────────────
    {"tier": 5, "question": "Laguna del Carbón, the lowest point in the Southern Hemisphere, is in ___?", "answer": "Argentina",
     "choices": ["Chile", "Argentina", "Bolivia", "Peru"]},
    {"tier": 5, "question": "Death Valley is in which US state?", "answer": "California",
     "choices": ["Nevada", "California", "Arizona", "Utah"]},
    {"tier": 5, "question": "The world's longest cave system is ___?", "answer": "Mammoth Cave",
     "choices": ["Carlsbad Caverns", "Mammoth Cave", "Lechuguilla Cave", "Krubera Cave"]},
    {"tier": 5, "question": "The deepest cave in the world is ___?", "answer": "Veryovkina Cave",
     "choices": ["Krubera Cave", "Veryovkina Cave", "Voronya Cave", "Snezhnaya Cave"]},
    {"tier": 5, "question": "Veryovkina Cave is in ___?", "answer": "Georgia",
     "choices": ["Russia", "Georgia", "Ukraine", "Armenia"]},
    {"tier": 5, "question": "The highest active volcano in the world is ___?", "answer": "Ojos del Salado",
     "choices": ["Cotopaxi", "Ojos del Salado", "Mauna Loa", "Mount Etna"]},
    {"tier": 5, "question": "Ojos del Salado is on the border of Chile and ___?", "answer": "Argentina",
     "choices": ["Bolivia", "Argentina", "Peru", "Brazil"]},
    {"tier": 5, "question": "The world's largest volcanic caldera is ___?", "answer": "Toba Caldera",
     "choices": ["Yellowstone Caldera", "Toba Caldera", "Valles Caldera", "Aira Caldera"]},
    {"tier": 5, "question": "Toba Caldera is in ___?", "answer": "Indonesia",
     "choices": ["Philippines", "Indonesia", "Japan", "Papua New Guinea"]},
    {"tier": 5, "question": "The Vernadsky Research Base is operated by ___?", "answer": "Ukraine",
     "choices": ["Russia", "Ukraine", "Poland", "Bulgaria"]},
    {"tier": 5, "question": "The geographic South Pole is in ___?", "answer": "Antarctica",
     "choices": ["Southern Ocean", "Antarctica", "Sub-Antarctic islands", "Ice shelf"]},
    {"tier": 5, "question": "The Ross Ice Shelf is in ___?", "answer": "Antarctica",
     "choices": ["Arctic", "Antarctica", "Greenland", "Iceland"]},
    {"tier": 5, "question": "The largest desert in Asia is the ___?", "answer": "Gobi Desert",
     "choices": ["Taklamakan Desert", "Gobi Desert", "Karakum Desert", "Rub al Khali"]},
    {"tier": 5, "question": "The Rub' al Khali (Empty Quarter) is in ___?", "answer": "Saudi Arabia",
     "choices": ["Yemen", "Saudi Arabia", "Oman", "UAE"]},
    {"tier": 5, "question": "The Taklamakan Desert is in ___?", "answer": "China",
     "choices": ["Kazakhstan", "China", "Mongolia", "Uzbekistan"]},
    {"tier": 5, "question": "The Banda Sea is in ___?", "answer": "Indonesia",
     "choices": ["Philippines", "Indonesia", "Papua New Guinea", "Timor-Leste"]},
    {"tier": 5, "question": "The Lofoten Islands are in ___?", "answer": "Norway",
     "choices": ["Iceland", "Norway", "Sweden", "Denmark"]},
    {"tier": 5, "question": "The Algarve is a coastal region in ___?", "answer": "Portugal",
     "choices": ["Spain", "Portugal", "Morocco", "France"]},
    {"tier": 5, "question": "The Douro River forms part of the border between Spain and ___?", "answer": "Portugal",
     "choices": ["France", "Portugal", "Andorra", "Morocco"]},
    {"tier": 5, "question": "The Ebro River is in ___?", "answer": "Spain",
     "choices": ["Portugal", "Spain", "France", "Italy"]},
    {"tier": 5, "question": "The Po River is the longest river in ___?", "answer": "Italy",
     "choices": ["France", "Italy", "Spain", "Greece"]},
    {"tier": 5, "question": "The Tagus River flows into the Atlantic at ___?", "answer": "Lisbon",
     "choices": ["Porto", "Lisbon", "Seville", "Madrid"]},
    {"tier": 5, "question": "The Loire is the longest river in ___?", "answer": "France",
     "choices": ["Belgium", "France", "Germany", "Switzerland"]},
    {"tier": 5, "question": "The Ob River in Russia drains into the ___?", "answer": "Arctic Ocean",
     "choices": ["Pacific Ocean", "Arctic Ocean", "Caspian Sea", "Black Sea"]},
    {"tier": 5, "question": "The Yenisei River flows through ___?", "answer": "Russia",
     "choices": ["Kazakhstan", "Russia", "Mongolia", "China"]},
    {"tier": 5, "question": "The Amur River forms part of the border between Russia and ___?", "answer": "China",
     "choices": ["Mongolia", "China", "North Korea", "Kazakhstan"]},
    {"tier": 5, "question": "The Ganges River flows into the ___?", "answer": "Bay of Bengal",
     "choices": ["Arabian Sea", "Bay of Bengal", "Indian Ocean", "Andaman Sea"]},
    {"tier": 5, "question": "The Irrawaddy River is in ___?", "answer": "Myanmar",
     "choices": ["Thailand", "Myanmar", "Laos", "Cambodia"]},
    {"tier": 5, "question": "The Brahmaputra River originates in ___?", "answer": "Tibet",
     "choices": ["Nepal", "Tibet", "Bhutan", "India"]},
    {"tier": 5, "question": "Cape Horn is the southernmost point of ___?", "answer": "South America",
     "choices": ["Antarctica", "South America", "Africa", "New Zealand"]},
    {"tier": 5, "question": "Cape Agulhas is the southernmost point of ___?", "answer": "Africa",
     "choices": ["South America", "Africa", "Antarctica", "Australia"]},
    {"tier": 5, "question": "The northernmost country capital in the world is ___?", "answer": "Reykjavik",
     "choices": ["Oslo", "Reykjavik", "Helsinki", "Nuuk"]},
    {"tier": 5, "question": "The southernmost national capital in the world is ___?", "answer": "Wellington",
     "choices": ["Buenos Aires", "Wellington", "Canberra", "Cape Town"]},
    {"tier": 5, "question": "The Makgadikgadi Pans are in ___?", "answer": "Botswana",
     "choices": ["Namibia", "Botswana", "Zimbabwe", "Zambia"]},
    {"tier": 5, "question": "The Danakil Depression is in ___?", "answer": "Ethiopia",
     "choices": ["Eritrea", "Ethiopia", "Djibouti", "Somalia"]},
    {"tier": 5, "question": "The Transylvania region is historically part of ___?", "answer": "Romania",
     "choices": ["Hungary", "Romania", "Bulgaria", "Serbia"]},
    {"tier": 5, "question": "The Hindu Kush mountain range is primarily in ___?", "answer": "Afghanistan",
     "choices": ["Pakistan", "Afghanistan", "Iran", "Tajikistan"]},
    {"tier": 5, "question": "The Karakoram Range is in ___?", "answer": "Pakistan and China",
     "choices": ["India and Nepal", "Pakistan and China", "Afghanistan and Tajikistan", "Kyrgyzstan and Kazakhstan"]},
    {"tier": 5, "question": "The Ngorongoro Crater is in ___?", "answer": "Tanzania",
     "choices": ["Kenya", "Tanzania", "Uganda", "Rwanda"]},
    {"tier": 5, "question": "The Skeleton Coast is in ___?", "answer": "Namibia",
     "choices": ["South Africa", "Namibia", "Angola", "Mozambique"]},
    {"tier": 5, "question": "The Limpopo River forms part of the border between South Africa and ___?", "answer": "Zimbabwe",
     "choices": ["Mozambique", "Zimbabwe", "Botswana", "Zambia"]},
    {"tier": 5, "question": "The Orange River flows into the ___?", "answer": "Atlantic Ocean",
     "choices": ["Indian Ocean", "Atlantic Ocean", "Southern Ocean", "Mediterranean Sea"]},
    {"tier": 5, "question": "The Zagros Mountains are in ___?", "answer": "Iran",
     "choices": ["Turkey", "Iran", "Iraq", "Afghanistan"]},
    {"tier": 5, "question": "The Elburz (Alborz) Mountains are in ___?", "answer": "Iran",
     "choices": ["Turkey", "Iran", "Azerbaijan", "Armenia"]},
    {"tier": 5, "question": "The highest peak in the Caucasus range is ___?", "answer": "Mount Elbrus",
     "choices": ["Mount Kazbek", "Mount Elbrus", "Mount Ararat", "Mount Shkhara"]},
    {"tier": 5, "question": "Mount Elbrus is in ___?", "answer": "Russia",
     "choices": ["Georgia", "Russia", "Armenia", "Azerbaijan"]},
    {"tier": 5, "question": "The Pamir Mountains are known as ___?", "answer": "Roof of the World",
     "choices": ["Top of the World", "Roof of the World", "Crown of Asia", "Peak of Eurasia"]},
    {"tier": 3, "question": "Capital of Malawi?", "answer": "Lilongwe",
     "choices": ["Blantyre", "Lilongwe", "Mzuzu", "Zomba"]},
    {"tier": 3, "question": "Capital of South Sudan?", "answer": "Juba",
     "choices": ["Malakal", "Juba", "Wau", "Yei"]},
]


def main():
    # Load existing questions
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        existing = json.load(f)

    # Build set of existing question texts (lowercased for dedup check)
    existing_texts = {q["question"].strip().lower() for q in existing}

    # Verify all existing answers are in choices
    errors_before = []
    for q in existing:
        if q["answer"] not in q["choices"]:
            errors_before.append(q["question"])
    if errors_before:
        print(f"WARNING: {len(errors_before)} existing questions have answer not in choices!")
        for e in errors_before:
            print(f"  - {e}")

    # Filter new questions: skip exact text duplicates, validate answer in choices
    added = 0
    skipped_dup = 0
    errors_new = []
    new_valid = []
    for q in NEW_QUESTIONS:
        key = q["question"].strip().lower()
        if key in existing_texts:
            skipped_dup += 1
            continue
        if q["answer"] not in q["choices"]:
            errors_new.append(q["question"])
            continue
        new_valid.append(q)
        existing_texts.add(key)
        added += 1

    if errors_new:
        print(f"ERROR: {len(errors_new)} new questions have answer not in choices — NOT added:")
        for e in errors_new:
            print(f"  - {e}")
        sys.exit(1)

    combined = existing + new_valid

    # Count per tier
    tier_counts = {}
    for q in combined:
        t = q["tier"]
        tier_counts[t] = tier_counts.get(t, 0) + 1

    print(f"Skipped {skipped_dup} duplicate questions.")
    print(f"Added {added} new questions.")
    print(f"Tier counts after merge: {dict(sorted(tier_counts.items()))}")
    print(f"Total: {len(combined)}")

    # Check targets
    target = 100
    ok = True
    for t in [1, 2, 3, 4, 5]:
        count = tier_counts.get(t, 0)
        status = "OK" if count == target else f"MISMATCH (need {target})"
        print(f"  T{t}: {count} {status}")
        if count != target:
            ok = False

    # Final validation: answer in choices
    final_errors = [q["question"] for q in combined if q["answer"] not in q["choices"]]
    print(f"Validation errors (answer not in choices): {len(final_errors)}")
    if final_errors:
        for e in final_errors:
            print(f"  - {e}")
        ok = False

    if not ok:
        print("\nABORTING — targets or validation not met. File NOT written.")
        sys.exit(1)

    # Write back
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"\nSuccessfully wrote {len(combined)} questions to {DATA_PATH}")


if __name__ == "__main__":
    main()
