"""
patch_animal.py — Appends new animal quiz questions to bring each tier to 100.
Current counts: T1=97, T2=78, T3=53, T4=51, T5=51
Target counts:  T1=100, T2=100, T3=100, T4=100, T5=100
Adds: T1=3, T2=22, T3=47, T4=49, T5=49
"""

import json
import sys

INPUT_PATH = "data/questions/animal.json"

NEW_QUESTIONS = [
    # ─── TIER 1 (3 new) ────────────────────────────────────────────────────
    {"tier": 1, "question": "A baby rabbit is called a ___?", "answer": "Kit", "choices": ["Pup", "Cub", "Kit", "Kitten"]},
    {"tier": 1, "question": "A baby pig is called a ___?", "answer": "Piglet", "choices": ["Cub", "Lamb", "Piglet", "Foal"]},
    {"tier": 1, "question": "A group of pigs is called a ___?", "answer": "Herd", "choices": ["Pack", "Herd", "Flock", "Litter"]},

    # ─── TIER 2 (22 new) ───────────────────────────────────────────────────
    {"tier": 2, "question": "Which animal is the only bird that can swim but cannot fly?", "answer": "Penguin", "choices": ["Ostrich", "Penguin", "Emu", "Kiwi"]},
    {"tier": 2, "question": "The mandrill is a type of ___?", "answer": "Primate", "choices": ["Rodent", "Primate", "Carnivore", "Marsupial"]},
    {"tier": 2, "question": "A group of tigers is called a ___?", "answer": "Streak", "choices": ["Pride", "Pack", "Streak", "Coalition"]},
    {"tier": 2, "question": "A group of cheetahs is called a ___?", "answer": "Coalition", "choices": ["Pride", "Pack", "Streak", "Coalition"]},
    {"tier": 2, "question": "A group of otters is called a ___?", "answer": "Romp", "choices": ["Pack", "Colony", "Romp", "Sleuth"]},
    {"tier": 2, "question": "Which animal has black and white stripes?", "answer": "Zebra", "choices": ["Okapi", "Zebra", "Tapir", "Panda"]},
    {"tier": 2, "question": "Frogs are classified as ___?", "answer": "Amphibians", "choices": ["Reptiles", "Amphibians", "Fish", "Mammals"]},
    {"tier": 2, "question": "Toads are classified as ___?", "answer": "Amphibians", "choices": ["Reptiles", "Amphibians", "Insects", "Mammals"]},
    {"tier": 2, "question": "A group of butterflies is called a ___?", "answer": "Flutter", "choices": ["Colony", "Swarm", "Flutter", "Cluster"]},
    {"tier": 2, "question": "A group of penguins is called a ___?", "answer": "Colony", "choices": ["Flock", "Pack", "Colony", "Huddle"]},
    {"tier": 2, "question": "A group of rhinos is called a ___?", "answer": "Crash", "choices": ["Herd", "Pack", "Crash", "Troop"]},
    {"tier": 2, "question": "A group of hippos is called a ___?", "answer": "Bloat", "choices": ["Herd", "Crash", "Bloat", "Pod"]},
    {"tier": 2, "question": "What type of diet does a koala have?", "answer": "Herbivore", "choices": ["Carnivore", "Omnivore", "Herbivore", "Insectivore"]},
    {"tier": 2, "question": "The African elephant has ___ ears compared to the Asian elephant?", "answer": "Larger", "choices": ["Smaller", "Larger", "The same size", "Rounder"]},
    {"tier": 2, "question": "Which large land mammal cannot jump?", "answer": "Elephant", "choices": ["Hippopotamus", "Rhinoceros", "Elephant", "Giraffe"]},
    {"tier": 2, "question": "A porcupine's defensive spines are called ___?", "answer": "Quills", "choices": ["Spines", "Thorns", "Quills", "Bristles"]},
    {"tier": 2, "question": "An armadillo's shell is made of ___?", "answer": "Bone plates covered by skin", "choices": ["Keratin scales", "Calcium carbonate", "Bone plates covered by skin", "Chitin"]},
    {"tier": 2, "question": "The electric eel is actually classified as a ___?", "answer": "Fish (knifefish)", "choices": ["Eel (true eel)", "Amphibian", "Fish (knifefish)", "Reptile"]},
    {"tier": 2, "question": "A group of giraffes is called a ___?", "answer": "Tower", "choices": ["Herd", "Pack", "Tower", "Troop"]},
    {"tier": 2, "question": "A group of zebras is called a ___?", "answer": "Dazzle", "choices": ["Herd", "Stripe", "Dazzle", "Pack"]},
    {"tier": 2, "question": "Which bird is the fastest in level flight?", "answer": "Common swift", "choices": ["Peregrine falcon", "Common swift", "Frigate bird", "Hummingbird"]},
    {"tier": 2, "question": "Which bird is the fastest in a dive?", "answer": "Peregrine falcon", "choices": ["Golden eagle", "Peregrine falcon", "Common swift", "Gyrfalcon"]},

    # ─── TIER 3 (47 new) ───────────────────────────────────────────────────
    {"tier": 3, "question": "The scientific name for the domestic pig is ___?", "answer": "Sus scrofa domesticus", "choices": ["Sus scrofa domesticus", "Ovis aries", "Bos taurus", "Capra aegagrus hircus"]},
    {"tier": 3, "question": "The scientific name for the domestic cow is ___?", "answer": "Bos taurus", "choices": ["Sus scrofa", "Bos taurus", "Ovis aries", "Equus caballus"]},
    {"tier": 3, "question": "The scientific name for the red fox is ___?", "answer": "Vulpes vulpes", "choices": ["Canis lupus", "Vulpes vulpes", "Canis latrans", "Urocyon cinereoargenteus"]},
    {"tier": 3, "question": "The scientific name for the brown rat is ___?", "answer": "Rattus norvegicus", "choices": ["Mus musculus", "Rattus rattus", "Rattus norvegicus", "Apodemus sylvaticus"]},
    {"tier": 3, "question": "The scientific name for the African lion is ___?", "answer": "Panthera leo", "choices": ["Panthera tigris", "Panthera leo", "Panthera onca", "Panthera pardus"]},
    {"tier": 3, "question": "The scientific name for the snow leopard is ___?", "answer": "Panthera uncia", "choices": ["Panthera pardus", "Neofelis nebulosa", "Panthera uncia", "Acinonyx jubatus"]},
    {"tier": 3, "question": "An animal that lives in trees is described as ___?", "answer": "Arboreal", "choices": ["Fossorial", "Arboreal", "Aquatic", "Cursorial"]},
    {"tier": 3, "question": "An animal that lives underground is described as ___?", "answer": "Fossorial", "choices": ["Arboreal", "Aquatic", "Fossorial", "Cursorial"]},
    {"tier": 3, "question": "An animal adapted for running is described as ___?", "answer": "Cursorial", "choices": ["Arboreal", "Fossorial", "Cursorial", "Natatorial"]},
    {"tier": 3, "question": "An animal adapted for swimming is described as ___?", "answer": "Natatorial", "choices": ["Cursorial", "Natatorial", "Volant", "Fossorial"]},
    {"tier": 3, "question": "Territory marking with scent is an example of ___?", "answer": "Chemical communication", "choices": ["Visual communication", "Chemical communication", "Acoustic communication", "Tactile communication"]},
    {"tier": 3, "question": "The mating call of a frog is an example of ___?", "answer": "Acoustic communication", "choices": ["Chemical communication", "Visual communication", "Acoustic communication", "Tactile communication"]},
    {"tier": 3, "question": "A food web differs from a food chain in that it shows ___?", "answer": "Multiple interconnected feeding relationships", "choices": ["A single linear feeding path", "Multiple interconnected feeding relationships", "Only apex predators", "Only decomposers"]},
    {"tier": 3, "question": "Detritivores feed on ___?", "answer": "Dead organic matter", "choices": ["Living plants", "Living animals", "Dead organic matter", "Fungi only"]},
    {"tier": 3, "question": "Decomposers break down organic matter into ___?", "answer": "Inorganic nutrients", "choices": ["Complex organic compounds", "Inorganic nutrients", "Fatty acids only", "Oxygen"]},
    {"tier": 3, "question": "A nymph is the juvenile form of ___?", "answer": "Hemimetabolous insects (e.g. grasshoppers)", "choices": ["Butterflies", "Beetles", "Hemimetabolous insects (e.g. grasshoppers)", "Moths"]},
    {"tier": 3, "question": "Incomplete metamorphosis has ___ stages?", "answer": "3", "choices": ["2", "3", "4", "5"]},
    {"tier": 3, "question": "The three stages of incomplete metamorphosis are egg, nymph, and ___?", "answer": "Adult", "choices": ["Pupa", "Larva", "Adult", "Instar"]},
    {"tier": 3, "question": "A group of penguins on land huddles to ___?", "answer": "Conserve heat", "choices": ["Attract mates", "Conserve heat", "Coordinate hunting", "Establish hierarchy"]},
    {"tier": 3, "question": "The scientific name for the common octopus is ___?", "answer": "Octopus vulgaris", "choices": ["Sepia officinalis", "Loligo vulgaris", "Octopus vulgaris", "Enteroctopus dofleini"]},
    {"tier": 3, "question": "The scientific name for the Nile crocodile is ___?", "answer": "Crocodylus niloticus", "choices": ["Alligator mississippiensis", "Crocodylus porosus", "Crocodylus niloticus", "Gavialis gangeticus"]},
    {"tier": 3, "question": "The scientific name for the saltwater crocodile is ___?", "answer": "Crocodylus porosus", "choices": ["Crocodylus niloticus", "Crocodylus porosus", "Alligator mississippiensis", "Caiman crocodilus"]},
    {"tier": 3, "question": "The scientific name for the American alligator is ___?", "answer": "Alligator mississippiensis", "choices": ["Crocodylus acutus", "Alligator sinensis", "Alligator mississippiensis", "Caiman latirostris"]},
    {"tier": 3, "question": "Social hierarchy in wolves is maintained by ___?", "answer": "Alpha wolves", "choices": ["Oldest females", "Alpha wolves", "Largest wolves", "All adults equally"]},
    {"tier": 3, "question": "Imprinting in animals occurs ___?", "answer": "During a critical early developmental period", "choices": ["Throughout adulthood", "Only during mating season", "During a critical early developmental period", "After the first hibernation"]},
    {"tier": 3, "question": "Operant conditioning involves learning through ___?", "answer": "Rewards and punishments", "choices": ["Association of stimuli", "Rewards and punishments", "Observation of others", "Instinct alone"]},
    {"tier": 3, "question": "Classical conditioning was discovered by ___?", "answer": "Ivan Pavlov", "choices": ["B.F. Skinner", "Ivan Pavlov", "Charles Darwin", "Konrad Lorenz"]},
    {"tier": 3, "question": "Konrad Lorenz is famous for studying ___?", "answer": "Imprinting in geese", "choices": ["Conditioning in rats", "Imprinting in geese", "Echolocation in bats", "Migration in salmon"]},
    {"tier": 3, "question": "Altruistic behavior in animals is behavior that benefits ___?", "answer": "Others at a cost to the actor", "choices": ["The actor primarily", "Others at a cost to the actor", "Both parties equally", "Neither party"]},
    {"tier": 3, "question": "The poison dart frog gets its toxins from ___?", "answer": "Its diet of arthropods", "choices": ["Internal glands it is born with", "Its diet of arthropods", "Skin bacteria", "Environmental absorption"]},
    {"tier": 3, "question": "Bioluminescent animals are most commonly found in ___?", "answer": "Deep ocean environments", "choices": ["Tropical rainforests", "Deep ocean environments", "Arctic tundra", "Desert caves"]},
    {"tier": 3, "question": "Osmoregulation in fish is the process of controlling ___?", "answer": "Internal salt and water balance", "choices": ["Body temperature", "Internal salt and water balance", "Blood pH only", "Reproductive hormones"]},
    {"tier": 3, "question": "A saltwater fish must constantly ___ water to avoid dehydration?", "answer": "Drink", "choices": ["Excrete", "Drink", "Absorb through skin", "Produce internally"]},
    {"tier": 3, "question": "The migration of eels from freshwater to the Sargasso Sea is called ___?", "answer": "Catadromous migration", "choices": ["Anadromous migration", "Catadromous migration", "Diadromous migration only", "Potamodromous migration"]},
    {"tier": 3, "question": "The migration of salmon from ocean to freshwater is called ___?", "answer": "Anadromous migration", "choices": ["Catadromous migration", "Anadromous migration", "Potamodromous migration", "Oceanodromous migration"]},
    {"tier": 3, "question": "The scientific name for the common goldfish is ___?", "answer": "Carassius auratus", "choices": ["Carassius carassius", "Cyprinus carpio", "Carassius auratus", "Danio rerio"]},
    {"tier": 3, "question": "The scientific name for zebrafish (a model organism) is ___?", "answer": "Danio rerio", "choices": ["Carassius auratus", "Danio rerio", "Brachydanio albolineatus", "Cyprinus carpio"]},
    {"tier": 3, "question": "A group of stingrays is called a ___?", "answer": "Fever", "choices": ["School", "Pod", "Fever", "Colony"]},
    {"tier": 3, "question": "A group of sharks is called a ___?", "answer": "Shiver", "choices": ["Pack", "Shiver", "School", "Pod"]},
    {"tier": 3, "question": "A group of meerkats is called a ___?", "answer": "Mob", "choices": ["Pack", "Troop", "Mob", "Colony"]},
    {"tier": 3, "question": "A group of badgers is called a ___?", "answer": "Cete", "choices": ["Pack", "Skulk", "Cete", "Colony"]},
    {"tier": 3, "question": "A group of squirrels is called a ___?", "answer": "Scurry", "choices": ["Pack", "Colony", "Scurry", "Dray"]},
    {"tier": 3, "question": "A group of hedgehogs is called a ___?", "answer": "Array", "choices": ["Pack", "Array", "Colony", "Prickle"]},
    {"tier": 3, "question": "An animal that feeds on carrion is called a ___?", "answer": "Scavenger", "choices": ["Predator", "Scavenger", "Parasite", "Herbivore"]},
    {"tier": 3, "question": "The cuttlefish is classified as a ___?", "answer": "Cephalopod mollusk", "choices": ["Crustacean", "Fish", "Cephalopod mollusk", "Echinoderm"]},
    {"tier": 3, "question": "The nautilus is classified as a ___?", "answer": "Cephalopod mollusk", "choices": ["Gastropod mollusk", "Cephalopod mollusk", "Bivalve mollusk", "Echinoderm"]},
    {"tier": 3, "question": "Hermaphroditic animals possess ___?", "answer": "Both male and female reproductive organs", "choices": ["No reproductive organs", "Only male organs", "Both male and female reproductive organs", "Asexual reproduction only"]},

    # ─── TIER 4 (49 new) ───────────────────────────────────────────────────
    {"tier": 4, "question": "The order Chiroptera contains ___?", "answer": "Bats", "choices": ["Birds", "Bats", "Butterflies", "Beetles"]},
    {"tier": 4, "question": "The order Cetacea contains ___?", "answer": "Whales and dolphins", "choices": ["Seals and sea lions", "Whales and dolphins", "Manatees and dugongs", "Sharks and rays"]},
    {"tier": 4, "question": "The order Artiodactyla (even-toed ungulates) includes ___?", "answer": "Deer, cattle, pigs", "choices": ["Horses, rhinos, tapirs", "Deer, cattle, pigs", "Elephants, hyraxes, manatees", "Rabbits, pikas"]},
    {"tier": 4, "question": "The order Perissodactyla (odd-toed ungulates) includes ___?", "answer": "Horses, rhinos, tapirs", "choices": ["Deer, cattle, pigs", "Horses, rhinos, tapirs", "Elephants, hyraxes", "Camels, llamas"]},
    {"tier": 4, "question": "The order Rodentia is the ___ order of mammals?", "answer": "Largest", "choices": ["Smallest", "Largest", "Second largest", "Third largest"]},
    {"tier": 4, "question": "The order Lagomorpha contains ___?", "answer": "Rabbits and pikas", "choices": ["Rats and mice", "Rabbits and pikas", "Shrews and moles", "Hedgehogs and tenrecs"]},
    {"tier": 4, "question": "The order Proboscidea contains ___?", "answer": "Elephants", "choices": ["Tapirs", "Rhinoceroses", "Elephants", "Hippos"]},
    {"tier": 4, "question": "The order Sirenia contains ___?", "answer": "Manatees and dugongs", "choices": ["Seals and walruses", "Manatees and dugongs", "Dolphins and porpoises", "Sea otters and sea lions"]},
    {"tier": 4, "question": "Monotremes include only the platypus and ___?", "answer": "Echidna", "choices": ["Wombat", "Echidna", "Wallaby", "Bandicoot"]},
    {"tier": 4, "question": "The class Chondrichthyes contains ___?", "answer": "Sharks, rays, skates", "choices": ["Bony fish", "Sharks, rays, skates", "Jawless fish", "Lungfish"]},
    {"tier": 4, "question": "The class Actinopterygii contains ___?", "answer": "Ray-finned fish", "choices": ["Sharks and rays", "Jawless fish", "Ray-finned fish", "Lobe-finned fish"]},
    {"tier": 4, "question": "The class Agnatha contains ___?", "answer": "Jawless fish (lampreys, hagfish)", "choices": ["Ray-finned fish", "Sharks", "Jawless fish (lampreys, hagfish)", "Lobe-finned fish"]},
    {"tier": 4, "question": "Lobe-finned fish belong to class ___?", "answer": "Sarcopterygii", "choices": ["Actinopterygii", "Chondrichthyes", "Sarcopterygii", "Agnatha"]},
    {"tier": 4, "question": "The suborder Serpentes contains ___?", "answer": "Snakes", "choices": ["Lizards", "Turtles", "Snakes", "Crocodilians"]},
    {"tier": 4, "question": "The order Testudines contains ___?", "answer": "Turtles and tortoises", "choices": ["Snakes and lizards", "Turtles and tortoises", "Crocodiles and alligators", "Tuataras"]},
    {"tier": 4, "question": "The order Crocodilia contains ___?", "answer": "Crocodiles, alligators, caimans, gharials", "choices": ["Lizards and snakes", "Turtles and tortoises", "Crocodiles, alligators, caimans, gharials", "Salamanders and newts"]},
    {"tier": 4, "question": "The order Anura contains ___?", "answer": "Frogs and toads", "choices": ["Salamanders", "Frogs and toads", "Caecilians", "Newts only"]},
    {"tier": 4, "question": "The order Urodela contains ___?", "answer": "Salamanders and newts", "choices": ["Frogs and toads", "Caecilians", "Salamanders and newts", "Limbless amphibians"]},
    {"tier": 4, "question": "Caecilians belong to order ___?", "answer": "Gymnophiona", "choices": ["Anura", "Urodela", "Gymnophiona", "Apoda only"]},
    {"tier": 4, "question": "The lymphatic system in animals primarily functions to ___?", "answer": "Return fluid to the bloodstream and support immunity", "choices": ["Carry oxygen", "Return fluid to the bloodstream and support immunity", "Digest food", "Regulate hormones"]},
    {"tier": 4, "question": "The glomerulus is found in the ___?", "answer": "Kidney (nephron)", "choices": ["Liver (hepatocyte)", "Heart (ventricle)", "Kidney (nephron)", "Lung (alveolus)"]},
    {"tier": 4, "question": "Gas exchange in mammals occurs in the ___?", "answer": "Alveoli", "choices": ["Bronchi", "Trachea", "Alveoli", "Pleural cavity"]},
    {"tier": 4, "question": "The four chambers of the mammalian heart are: left atrium, left ventricle, right atrium, and ___?", "answer": "Right ventricle", "choices": ["Right pulmonary", "Right ventricle", "Aortic chamber", "Sinus node"]},
    {"tier": 4, "question": "Oxygenated blood is carried from the lungs to the heart by the ___?", "answer": "Pulmonary veins", "choices": ["Pulmonary arteries", "Pulmonary veins", "Aorta", "Vena cava"]},
    {"tier": 4, "question": "The largest artery in the mammalian body is the ___?", "answer": "Aorta", "choices": ["Vena cava", "Femoral artery", "Aorta", "Carotid artery"]},
    {"tier": 4, "question": "The IUCN Red List category 'CR' stands for ___?", "answer": "Critically Endangered", "choices": ["Critically Rare", "Critically Reduced", "Critically Endangered", "Conservation Required"]},
    {"tier": 4, "question": "The IUCN Red List category 'EN' stands for ___?", "answer": "Endangered", "choices": ["Extant", "Endemic", "Endangered", "Evaluated Negligible"]},
    {"tier": 4, "question": "The IUCN Red List category 'VU' stands for ___?", "answer": "Vulnerable", "choices": ["Variable", "Vulnerable", "Viable Under study", "Very Uncertain"]},
    {"tier": 4, "question": "The IUCN Red List category 'EX' stands for ___?", "answer": "Extinct", "choices": ["Extirpated", "Extinct", "Extremely Rare", "Extended Range"]},
    {"tier": 4, "question": "A species extinct in the wild but surviving in captivity is classified as ___?", "answer": "EW (Extinct in the Wild)", "choices": ["EX (Extinct)", "CR (Critically Endangered)", "EW (Extinct in the Wild)", "EN (Endangered)"]},
    {"tier": 4, "question": "Population viability analysis estimates the probability of ___?", "answer": "A population's extinction over time", "choices": ["A species' geographic spread", "A population's extinction over time", "Genetic diversity in a species", "Habitat carrying capacity"]},
    {"tier": 4, "question": "The minimum viable population (MVP) concept refers to ___?", "answer": "The smallest population size with a good chance of long-term survival", "choices": ["Maximum population density", "The smallest population size with a good chance of long-term survival", "Optimal breeding group size", "Minimum habitat area needed"]},
    {"tier": 4, "question": "Hindgut fermenters (e.g. horses) digest cellulose in the ___?", "answer": "Cecum and colon", "choices": ["Rumen", "Abomasum", "Cecum and colon", "Small intestine primarily"]},
    {"tier": 4, "question": "Ruminants (e.g. cows) regurgitate and re-chew food called ___?", "answer": "Cud", "choices": ["Bolus", "Cud", "Chyme", "Pulp"]},
    {"tier": 4, "question": "The four-chambered stomach of ruminants includes the rumen, reticulum, omasum, and ___?", "answer": "Abomasum", "choices": ["Duodenum", "Cecum", "Abomasum", "Ileum"]},
    {"tier": 4, "question": "Countercurrent heat exchange in Arctic animals conserves ___?", "answer": "Body heat", "choices": ["Oxygen", "Water", "Body heat", "Glucose"]},
    {"tier": 4, "question": "The family Mustelidae includes ___?", "answer": "Weasels, otters, badgers", "choices": ["Dogs and wolves", "Weasels, otters, badgers", "Bears and raccoons", "Cats and mongooses"]},
    {"tier": 4, "question": "The family Cervidae includes ___?", "answer": "Deer, elk, moose", "choices": ["Cattle and bison", "Deer, elk, moose", "Goats and sheep", "Antelope and gazelles"]},
    {"tier": 4, "question": "The family Bovidae includes ___?", "answer": "Cattle, goats, sheep, antelope", "choices": ["Deer and moose", "Horses and rhinos", "Cattle, goats, sheep, antelope", "Pigs and hippos"]},
    {"tier": 4, "question": "The family Equidae includes ___?", "answer": "Horses, zebras, donkeys", "choices": ["Deer and elk", "Cattle and bison", "Horses, zebras, donkeys", "Pigs and peccaries"]},
    {"tier": 4, "question": "The family Suidae includes ___?", "answer": "Pigs and warthogs", "choices": ["Horses and tapirs", "Deer and antelope", "Pigs and warthogs", "Hippos and peccaries"]},
    {"tier": 4, "question": "The family Elephantidae includes ___?", "answer": "African and Asian elephants", "choices": ["Mammoths only (extinct)", "African and Asian elephants", "Mastodons only (extinct)", "Elephants and tapirs"]},
    {"tier": 4, "question": "Neoteny is the retention of ___ traits in adults?", "answer": "Juvenile", "choices": ["Ancestral", "Juvenile", "Senescent", "Secondary sexual"]},
    {"tier": 4, "question": "The axolotl is famous for exhibiting lifelong neoteny because it ___?", "answer": "Retains gills and larval form as an adult", "choices": ["Regrows lost limbs rapidly", "Retains gills and larval form as an adult", "Lives entirely underground", "Changes sex throughout life"]},
    {"tier": 4, "question": "Parthenogenesis is a form of reproduction where ___?", "answer": "Females produce offspring without fertilization", "choices": ["Males produce eggs", "Females produce offspring without fertilization", "Two females share parental duties", "Eggs are fertilized externally"]},
    {"tier": 4, "question": "Animals capable of regenerating lost limbs include ___?", "answer": "Axolotl and sea stars", "choices": ["Cats and dogs", "Axolotl and sea stars", "Sharks and dolphins", "Birds and reptiles"]},
    {"tier": 4, "question": "Biomass decreases at higher trophic levels because of ___?", "answer": "Energy loss as heat at each level", "choices": ["Fewer species at higher levels", "Energy loss as heat at each level", "Increased predation pressure", "Greater reproduction rates"]},
    {"tier": 4, "question": "Ecological succession from bare rock to climax community is ___?", "answer": "Primary succession", "choices": ["Secondary succession", "Primary succession", "Tertiary succession", "Climax cycling"]},
    {"tier": 4, "question": "Ecological succession following a forest fire is ___?", "answer": "Secondary succession", "choices": ["Primary succession", "Secondary succession", "Tertiary succession", "Disturbance ecology"]},
    # ─── TIER 5 (49 new) ───────────────────────────────────────────────────
    {"tier": 5, "question": "The scientific name for the cheetah is ___?", "answer": "Acinonyx jubatus", "choices": ["Panthera leo", "Acinonyx jubatus", "Panthera pardus", "Puma concolor"]},
    {"tier": 5, "question": "The scientific name for the jaguar is ___?", "answer": "Panthera onca", "choices": ["Panthera pardus", "Puma concolor", "Panthera onca", "Neofelis nebulosa"]},
    {"tier": 5, "question": "The scientific name for the cougar (puma) is ___?", "answer": "Puma concolor", "choices": ["Panthera onca", "Acinonyx jubatus", "Puma concolor", "Lynx rufus"]},
    {"tier": 5, "question": "The scientific name for the North American black bear is ___?", "answer": "Ursus americanus", "choices": ["Ursus arctos", "Ursus thibetanus", "Ursus americanus", "Ursus maritimus"]},
    {"tier": 5, "question": "The scientific name for the grizzly bear is ___?", "answer": "Ursus arctos horribilis", "choices": ["Ursus americanus", "Ursus arctos horribilis", "Ursus arctos middendorffi", "Ursus maritimus"]},
    {"tier": 5, "question": "The scientific name for the polar bear is ___?", "answer": "Ursus maritimus", "choices": ["Ursus arctos", "Ursus americanus", "Ursus maritimus", "Ailuropoda melanoleuca"]},
    {"tier": 5, "question": "The scientific name for the red wolf is ___?", "answer": "Canis rufus", "choices": ["Canis lupus", "Canis latrans", "Canis rufus", "Canis aureus"]},
    {"tier": 5, "question": "The scientific name for the coyote is ___?", "answer": "Canis latrans", "choices": ["Canis lupus", "Canis rufus", "Canis latrans", "Vulpes vulpes"]},
    {"tier": 5, "question": "The scientific name for the African wild dog is ___?", "answer": "Lycaon pictus", "choices": ["Canis lupus", "Lycaon pictus", "Cuon alpinus", "Speothos venaticus"]},
    {"tier": 5, "question": "The scientific name for the bonobo is ___?", "answer": "Pan paniscus", "choices": ["Pan troglodytes", "Gorilla beringei", "Pan paniscus", "Pongo pygmaeus"]},
    {"tier": 5, "question": "The scientific name for the Bornean orangutan is ___?", "answer": "Pongo pygmaeus", "choices": ["Pongo abelii", "Pan troglodytes", "Pongo pygmaeus", "Gorilla gorilla"]},
    {"tier": 5, "question": "The scientific name for the mountain gorilla is ___?", "answer": "Gorilla beringei beringei", "choices": ["Gorilla gorilla gorilla", "Gorilla beringei beringei", "Pan troglodytes schweinfurthii", "Gorilla gorilla diehli"]},
    {"tier": 5, "question": "The scientific name for the blue whale is ___?", "answer": "Balaenoptera musculus", "choices": ["Balaenoptera physalus", "Megaptera novaeangliae", "Balaenoptera musculus", "Physeter macrocephalus"]},
    {"tier": 5, "question": "The scientific name for the sperm whale is ___?", "answer": "Physeter macrocephalus", "choices": ["Balaenoptera musculus", "Physeter macrocephalus", "Orcinus orca", "Kogia breviceps"]},
    {"tier": 5, "question": "The scientific name for the orca (killer whale) is ___?", "answer": "Orcinus orca", "choices": ["Tursiops truncatus", "Delphinus delphis", "Orcinus orca", "Globicephala melas"]},
    {"tier": 5, "question": "The scientific name for the Amur leopard is ___?", "answer": "Panthera pardus orientalis", "choices": ["Panthera pardus pardus", "Panthera uncia", "Panthera pardus orientalis", "Neofelis nebulosa"]},
    {"tier": 5, "question": "Müllerian mimicry differs from Batesian mimicry in that all mimics are ___?", "answer": "Genuinely harmful (unpalatable or venomous)", "choices": ["Harmless imitators", "Genuinely harmful (unpalatable or venomous)", "Nocturnal species only", "Color-blind to each other"]},
    {"tier": 5, "question": "Aggressive mimicry is when a predator or parasite mimics ___?", "answer": "Something harmless to lure prey", "choices": ["A more dangerous predator", "Something harmless to lure prey", "Its own species for mating", "Abiotic features like rocks"]},
    {"tier": 5, "question": "The neutral theory of molecular evolution proposes that most mutations are ___?", "answer": "Neither beneficial nor harmful (neutral)", "choices": ["Beneficial and selected for", "Harmful and selected against", "Neither beneficial nor harmful (neutral)", "Always expressed in phenotype"]},
    {"tier": 5, "question": "Punctuated equilibrium proposes that evolution proceeds by ___?", "answer": "Long stasis punctuated by rapid change", "choices": ["Constant gradual change", "Long stasis punctuated by rapid change", "Only catastrophic extinction events", "Exclusively genetic drift"]},
    {"tier": 5, "question": "Phylogeography studies the relationship between ___?", "answer": "Evolutionary history and geographic distribution", "choices": ["Climate and body size", "Evolutionary history and geographic distribution", "Genetic drift and speciation rates", "Reproductive isolation and morphology"]},
    {"tier": 5, "question": "Bergmann's rule states that in endotherms, body size is ___ at higher latitudes?", "answer": "Larger", "choices": ["Smaller", "Larger", "Unchanged", "Variable by sex"]},
    {"tier": 5, "question": "Allen's rule states that appendages (ears, limbs) are ___ in colder climates?", "answer": "Shorter", "choices": ["Longer", "Shorter", "Thicker", "More numerous"]},
    {"tier": 5, "question": "Cope's rule describes the evolutionary tendency toward ___?", "answer": "Increasing body size over time in a lineage", "choices": ["Decreasing body size over time", "Increasing body size over time in a lineage", "Bilateral symmetry development", "Increased metabolic rate"]},
    {"tier": 5, "question": "The coelacanth (Latimeria chalumnae) is significant because it ___?", "answer": "Was thought extinct and is a lobe-finned fish", "choices": ["Is the fastest fish alive", "Was thought extinct and is a lobe-finned fish", "Breathes air exclusively", "Is the deepest-diving vertebrate"]},
    {"tier": 5, "question": "The hagfish is significant for having no ___?", "answer": "Jaws or vertebrae", "choices": ["Eyes", "Gills", "Jaws or vertebrae", "Fins"]},
    {"tier": 5, "question": "A zoonotic disease is one that ___?", "answer": "Can be transmitted between animals and humans", "choices": ["Only affects zoo animals", "Can be transmitted between animals and humans", "Is caused by parasitic worms only", "Affects multiple species simultaneously"]},
    {"tier": 5, "question": "Cryptic species are species that are ___?", "answer": "Morphologically identical but genetically distinct", "choices": ["Behaviorally identical only", "Morphologically identical but genetically distinct", "Geographically isolated subspecies", "Extinct but known from DNA only"]},
    {"tier": 5, "question": "Hybridization between species can produce ___?", "answer": "Fertile or sterile offspring depending on the species", "choices": ["Only sterile offspring always", "Fertile or sterile offspring depending on the species", "Only fertile offspring", "No offspring due to genetic barriers"]},
    {"tier": 5, "question": "The prezygotic reproductive barrier of temporal isolation means species ___?", "answer": "Breed at different times", "choices": ["Live in different habitats", "Breed at different times", "Have incompatible genitalia", "Produce inviable hybrids"]},
    {"tier": 5, "question": "Postzygotic reproductive barriers include hybrid inviability and ___?", "answer": "Hybrid sterility", "choices": ["Temporal isolation", "Habitat isolation", "Hybrid sterility", "Behavioral isolation"]},
    {"tier": 5, "question": "Horizontal gene transfer (HGT) in animals has been documented primarily via ___?", "answer": "Viral vectors (retroviruses)", "choices": ["Bacterial conjugation", "Viral vectors (retroviruses)", "Direct DNA uptake from soil", "Spore formation"]},
    {"tier": 5, "question": "The mitochondrial genome is typically inherited from ___?", "answer": "The mother", "choices": ["The father", "The mother", "Both parents equally", "Random parent each generation"]},
    {"tier": 5, "question": "Cytochrome c oxidase I (COI) gene is used in ___?", "answer": "DNA barcoding to identify species", "choices": ["Gene therapy for diseases", "DNA barcoding to identify species", "Determining fossil age", "Measuring metabolic rate"]},
    {"tier": 5, "question": "The Hardy-Weinberg p + q = 1 equation assumes ___ alleles at a locus?", "answer": "Two", "choices": ["One", "Two", "Three", "Any number"]},
    {"tier": 5, "question": "Stabilizing selection favors ___?", "answer": "Intermediate phenotypes", "choices": ["Extreme phenotypes", "Intermediate phenotypes", "The rarest phenotype", "All phenotypes equally"]},
    {"tier": 5, "question": "Directional selection favors ___?", "answer": "One extreme phenotype", "choices": ["Both extreme phenotypes", "Intermediate phenotypes", "One extreme phenotype", "Random phenotypes"]},
    {"tier": 5, "question": "Disruptive selection favors ___?", "answer": "Both extreme phenotypes", "choices": ["Intermediate phenotypes", "Both extreme phenotypes", "One extreme phenotype", "The modal phenotype"]},
    {"tier": 5, "question": "Inclusive fitness includes an individual's own fitness plus ___?", "answer": "Fitness benefits to related individuals", "choices": ["Fitness of unrelated group members", "Fitness benefits to related individuals", "Environmental carrying capacity", "Reproductive output of competitors"]},
    {"tier": 5, "question": "Reciprocal altruism is altruism based on ___?", "answer": "The expectation of future return", "choices": ["Genetic relatedness", "The expectation of future return", "Group hierarchy", "Parental investment theory"]},
    {"tier": 5, "question": "The scientific name for the wandering albatross is ___?", "answer": "Diomedea exulans", "choices": ["Phoebastria irrorata", "Thalassarche melanophris", "Diomedea exulans", "Phoebetria palpebrata"]},
    {"tier": 5, "question": "The scientific name for the peregrine falcon is ___?", "answer": "Falco peregrinus", "choices": ["Falco rusticolus", "Falco columbarius", "Falco peregrinus", "Accipiter gentilis"]},
    {"tier": 5, "question": "The scientific name for the harpy eagle is ___?", "answer": "Harpia harpyja", "choices": ["Aquila chrysaetos", "Haliaeetus leucocephalus", "Harpia harpyja", "Spizaetus ornatus"]},
    {"tier": 5, "question": "The scientific name for the Komodo dragon is ___?", "answer": "Varanus komodoensis", "choices": ["Varanus salvator", "Varanus niloticus", "Varanus komodoensis", "Iguana iguana"]},
    {"tier": 5, "question": "The scientific name for the inland taipan (most venomous snake) is ___?", "answer": "Oxyuranus microlepidotus", "choices": ["Oxyuranus scutellatus", "Pseudonaja textilis", "Oxyuranus microlepidotus", "Notechis scutatus"]},
    {"tier": 5, "question": "The scientific name for the Galápagos tortoise is ___?", "answer": "Chelonoidis niger", "choices": ["Aldabrachelys gigantea", "Testudo graeca", "Chelonoidis niger", "Geochelone elegans"]},
    {"tier": 5, "question": "The scientific name for the axolotl is ___?", "answer": "Ambystoma mexicanum", "choices": ["Ambystoma tigrinum", "Salamandra salamandra", "Ambystoma mexicanum", "Necturus maculosus"]},
    {"tier": 5, "question": "The scientific name for the poison dart frog genus most studied is ___?", "answer": "Dendrobates", "choices": ["Phyllobates", "Oophaga", "Dendrobates", "Ranitomeya"]},
    {"tier": 5, "question": "Sensory ecology studies how animals ___?", "answer": "Perceive and use sensory information in their environment", "choices": ["Evolve new sensory organs", "Perceive and use sensory information in their environment", "Communicate only through chemicals", "Navigate using magnetic fields only"]},
]


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        existing = json.load(f)

    existing_questions = {q["question"] for q in existing}

    # Filter out any exact duplicates (by question text)
    new_unique = []
    duplicates = []
    for q in NEW_QUESTIONS:
        if q["question"] in existing_questions:
            duplicates.append(q["question"])
        else:
            new_unique.append(q)

    if duplicates:
        print(f"WARNING: {len(duplicates)} duplicate question(s) skipped:")
        for d in duplicates:
            print(f"  - {d}")

    combined = existing + new_unique

    # Validation
    errors = []
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for i, q in enumerate(combined):
        t = q.get("tier")
        if t in tier_counts:
            tier_counts[t] += 1
        if q["answer"] not in q["choices"]:
            errors.append(f"  Row {i}: answer '{q['answer']}' not in choices {q['choices']}")

    print(f"\nValidation results:")
    print(f"  Total questions: {len(combined)}")
    for tier, count in sorted(tier_counts.items()):
        status = "OK" if count == 100 else f"WARN (expected 100, got {count})"
        print(f"  Tier {tier}: {count}  [{status}]")
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print(f"  Errors: 0  [OK]")

    with open(INPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(combined)} questions to {INPUT_PATH}")


if __name__ == "__main__":
    main()
