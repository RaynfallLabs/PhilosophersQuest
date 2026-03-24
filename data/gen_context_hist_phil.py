#!/usr/bin/env python3
"""
Generate educational context for history and philosophy quiz questions.
For each question without a "context" field, adds one from the CONTEXTS dict.
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── HISTORY CONTEXTS ─────────────────────────────────────────────────────────

HISTORY_CONTEXTS = {
    # ── Tier 1 ──────────────────────────────────────────────────────────────

    "Julius Caesar was a leader of ___?":
        "Julius Caesar rose from Roman politician to dictator perpetuo, reshaping the Republic forever. His military genius conquered Gaul and his crossing of the Rubicon in 49 BC sparked civil war. He was assassinated on the Ides of March, 44 BC, by senators who feared his power.",

    "Cleopatra was Queen of ___?":
        "Cleopatra VII was the last active ruler of Egypt's Ptolemaic dynasty, a Greek family that had ruled since Alexander the Great's general Ptolemy took power in 305 BC. She spoke nine languages, was a shrewd political strategist, and her death in 30 BC marked the end of ancient Egypt as an independent kingdom.",

    "Alexander the Great was king of ___?":
        "Alexander inherited the throne of Macedonia at age 20 after his father Philip II was assassinated in 336 BC. Though often called Greek, Macedonia was a distinct kingdom north of the Greek city-states. Alexander united Greece under Macedonian rule before conquering the Persian Empire.",

    "Alexander the Great is famous for ___?":
        "By the time he died at 32, Alexander had built one of the largest empires in history, stretching from Greece to northwest India. He never lost a single battle, and the cities he founded -- including Alexandria in Egypt -- became centers of learning for centuries.",

    "The American Civil War lasted from 1861 to ___?":
        "The Civil War began when Confederate forces fired on Fort Sumter in April 1861 and ended with Lee's surrender at Appomattox Court House in April 1865. It remains the deadliest conflict in American history, claiming roughly 620,000 lives.",

    "Which side won the American Civil War?":
        "The Union victory preserved the United States as one nation and ended slavery through the 13th Amendment. The war's final year saw Sherman's devastating March to the Sea and Grant's relentless pressure on Lee's army in Virginia.",

    "The Gettysburg Address was delivered by ___?":
        "Lincoln delivered his famous 272-word speech on November 19, 1863, at the dedication of a military cemetery in Gettysburg, Pennsylvania. In just two minutes, he redefined the war as a struggle for equality and democratic self-government.",

    "The French Revolution's slogan 'Liberty, Equality, Fraternity' ultimately gave way to what?":
        "The ideals of 1789 descended into the Reign of Terror by 1793, when Robespierre's Committee of Public Safety sent thousands to the guillotine. The revolution devoured its own children -- even Robespierre himself was executed in 1794.",

    "The Reign of Terror during the French Revolution killed thousands. What did this demonstrate?":
        "Between September 1793 and July 1794, an estimated 17,000 people were officially executed, with thousands more dying in prison. The Terror showed that utopian visions enforced by unlimited state power can produce horrors worse than the tyranny they replaced.",

    "Rome was traditionally founded in ___?":
        "According to legend, Romulus and Remus -- twin brothers raised by a she-wolf -- founded Rome on the Palatine Hill. The date 753 BC comes from the Roman scholar Varro, who calculated it centuries later. Archaeological evidence shows settlements on the site dating to around the same period.",

    "The Black Death was a devastating ___?":
        "The Black Death was a bubonic plague pandemic that swept through Europe from 1347 to 1353, carried by fleas on rats traveling along trade routes from Central Asia. It killed an estimated 75-200 million people and transformed European society, economics, and religion.",

    "Gutenberg invented the printing press around ___?":
        "Johannes Gutenberg's movable-type printing press, developed around 1440 in Mainz, Germany, revolutionized the spread of knowledge. His first major work, the Gutenberg Bible, was completed around 1455. Within 50 years, an estimated 20 million books had been printed across Europe.",

    "Who was the first man to walk on the Moon?":
        "Neil Armstrong stepped onto the lunar surface on July 20, 1969, during the Apollo 11 mission, declaring 'That's one small step for man, one giant leap for mankind.' He and Buzz Aldrin spent about two hours walking on the Moon while Michael Collins orbited above.",

    "The first human in space was ___?":
        "Soviet cosmonaut Yuri Gagarin orbited Earth on April 12, 1961, aboard Vostok 1, making the flight in just 108 minutes. His famous words, 'I see Earth! It is so beautiful!' captured the wonder of the moment. He became an instant global hero at age 27.",

    "The Soviet Union's 1991 dissolution resulted primarily from ___?":
        "After seven decades of communist rule, the Soviet economy was stagnant, technology lagged the West, and citizens demanded freedom. Gorbachev's reforms of glasnost (openness) and perestroika (restructuring) unleashed forces he could not control, and the union dissolved into 15 independent states.",

    "The Berlin Wall's fall in 1989 symbolized ___?":
        "On November 9, 1989, East German authorities unexpectedly opened the Berlin Wall after weeks of mass protests. Jubilant crowds from both sides danced atop the wall and tore it apart with hammers. Within a year, Germany was reunified and the communist bloc was crumbling.",

    "D-Day (the Normandy invasion) occurred in ___?":
        "On June 6, 1944, over 156,000 Allied troops stormed five beaches in Normandy, France, in the largest amphibious invasion in history. Despite fierce German resistance and heavy casualties, the Allies established a foothold that led to the liberation of Western Europe.",

    "Adolf Hitler was the leader of ___?":
        "Hitler rose from a failed artist and WWI corporal to dictator of Germany, exploiting economic despair and antisemitism. His regime murdered six million Jews in the Holocaust and plunged Europe into World War II, which killed an estimated 70-85 million people.",

    "Benito Mussolini was the leader of ___?":
        "Mussolini founded Italian Fascism and ruled as Il Duce from 1922 to 1943. He pioneered the totalitarian playbook -- state-controlled media, secret police, cult of personality -- that Hitler later imitated. He was captured and executed by partisans in April 1945.",

    "The Holocaust resulted in the murder of approximately ___?":
        "The Nazi regime systematically murdered six million Jews -- roughly two-thirds of Europe's Jewish population -- along with millions of Roma, disabled people, political prisoners, and others. The industrial scale of the genocide, carried out in camps like Auschwitz, shocked the conscience of the world.",

    "Nelson Mandela became South Africa's president in ___?":
        "After 27 years in prison, Mandela emerged to lead South Africa's transition from apartheid to democracy. He won the 1994 election and governed with a spirit of reconciliation rather than revenge, earning global admiration and the Nobel Peace Prize.",

    "The United Nations was founded in ___?":
        "The UN was established on October 24, 1945, with 51 member nations, born from the ashes of WWII and the failure of the League of Nations. Its charter committed nations to maintaining peace, developing friendly relations, and promoting human rights.",

    "The Cold War was between the USA and ___?":
        "The Cold War (1947-1991) was a geopolitical rivalry between the US-led Western bloc and the Soviet-led Eastern bloc. Though the superpowers never fought directly, they waged proxy wars in Korea, Vietnam, and Afghanistan, and built nuclear arsenals capable of destroying civilization.",

    "The Emancipation Proclamation was issued in ___?":
        "Lincoln signed the Emancipation Proclamation on January 1, 1863, declaring all enslaved people in Confederate states 'forever free.' While it did not immediately free anyone in practice, it transformed the Union cause and opened the door for Black soldiers to join the fight.",

    "Winston Churchill was Prime Minister of ___?":
        "Churchill led Britain through its darkest hours in WWII, rallying the nation with electrifying speeches when it stood alone against Nazi Germany. His famous line 'We shall fight on the beaches' became a symbol of defiance against tyranny.",

    "The Titanic sank in ___?":
        "The RMS Titanic, billed as 'unsinkable,' struck an iceberg on its maiden voyage and sank in the early hours of April 15, 1912. Over 1,500 of the 2,224 passengers and crew perished in the freezing North Atlantic, partly because the ship carried too few lifeboats.",

    "The Great Depression began in ___?":
        "The stock market crash of October 1929 triggered the worst economic downturn in modern history. By 1933, US unemployment hit 25%, banks failed by the thousands, and the crisis spread worldwide. It ended only with the massive spending of World War II.",

    "Franklin D. Roosevelt served as US President during ___?":
        "FDR led America through the Great Depression and most of WWII, serving an unprecedented four terms. His New Deal programs reshaped the federal government's role in American life, and his wartime leadership helped forge the Allied victory.",

    "Japan attacked Pearl Harbor in ___?":
        "On December 7, 1941 -- 'a date which will live in infamy,' as FDR called it -- Japan launched a surprise attack on the US naval base at Pearl Harbor, Hawaii. The attack killed 2,403 Americans and drew the United States into World War II the very next day.",

    "The Great Wall of China was primarily built during which dynasty?":
        "While earlier dynasties built walls along the northern border, the iconic stone-and-brick Great Wall we see today was mostly constructed during the Ming Dynasty (1368-1644). It stretches over 13,000 miles and was built to defend against Mongol and Manchu invasions.",

    "The Eiffel Tower was built in ___?":
        "Gustave Eiffel's iron tower was erected as the entrance arch for the 1889 World's Fair celebrating the centennial of the French Revolution. Parisians initially hated it -- writer Guy de Maupassant allegedly ate lunch at its restaurant just to avoid seeing it. It became the world's most-visited paid monument.",

    "Who was the second President of the United States?":
        "John Adams served from 1797 to 1801, following George Washington. A key architect of American independence, he had been Washington's vice president. He was the father of the sixth president, John Quincy Adams -- one of only two father-son presidential pairs in US history.",

    "The American Revolution ended in ___?":
        "Though the last major battle was at Yorktown in 1781, the war officially ended with the Treaty of Paris in 1783. Britain recognized American independence, and the new nation stretched from the Atlantic to the Mississippi River.",

    "The Pacific theater of World War II ended with Japan's surrender in ___?":
        "Japan surrendered on August 15, 1945, after the atomic bombings of Hiroshima and Nagasaki and the Soviet Union's declaration of war. The formal surrender was signed aboard the USS Missouri on September 2, 1945, ending the deadliest conflict in human history.",

    "The Magna Carta's primary significance was that it established ___?":
        "When English barons forced King John to sign the Magna Carta at Runnymede in 1215, they established a revolutionary principle: even the king must obey the law. This document became the cornerstone of constitutional governance and individual rights throughout the English-speaking world.",

    "George Washington served how many terms as President?":
        "Washington voluntarily stepped down after two terms (1789-1797), setting a precedent that held for 144 years until FDR broke it. His restraint was remarkable -- as King George III supposedly said, it made Washington 'the greatest man in the world.'",

    "India's independence leader was ___?":
        "Mahatma Gandhi led India's independence movement through nonviolent civil disobedience, inspiring millions to resist British rule through peaceful protest. His philosophy of satyagraha (truth-force) influenced civil rights leaders worldwide, including Martin Luther King Jr.",

    "The French Revolution produced the slogan Liberty, Equality, ___?":
        "Fraternity -- brotherhood -- completed the revolutionary trinity that still adorns French coins and public buildings today. The motto captured the Enlightenment dream that citizens could be free, equal, and united. The reality proved far bloodier than the dream.",

    "Which two Roman leaders did Cleopatra famously ally with?":
        "Cleopatra first allied with Julius Caesar around 48 BC, bearing him a son. After Caesar's assassination, she formed a political and romantic alliance with Mark Antony. Their combined forces were defeated by Octavian (later Augustus) at the Battle of Actium in 31 BC.",

    "The Black Death killed approximately what fraction of Europe's population?":
        "The plague wiped out roughly one-third of Europe's population between 1347 and 1353 -- approximately 25 million people. The massive labor shortage that followed actually improved conditions for surviving peasants, as their labor became far more valuable.",

    "The Magna Carta was signed in ___?":
        "King John was forced to affix his seal to the Magna Carta at Runnymede on June 15, 1215, under pressure from rebellious barons. Though John repudiated it within weeks, the charter was reissued multiple times and became a foundational document of English law.",

    "The Battle of Hastings was won by ___?":
        "William, Duke of Normandy, defeated King Harold Godwinson on October 14, 1066, fundamentally changing English history. The Norman Conquest introduced French language and culture to England, reshaped the aristocracy, and led to the creation of the Domesday Book.",

    "The Cuban Missile Crisis occurred in ___?":
        "For thirteen days in October 1962, the world stood on the brink of nuclear war as the US and Soviet Union confronted each other over Soviet missiles in Cuba. It was the closest the Cold War ever came to turning hot, and both sides pulled back from the abyss.",

    "The Vietnam War ended in ___?":
        "The fall of Saigon on April 30, 1975, marked the end of a conflict that had killed over 58,000 Americans and millions of Vietnamese. The last US personnel were evacuated by helicopter from the embassy roof in one of the most iconic images of the 20th century.",

    "Who assassinated Archduke Franz Ferdinand?":
        "Gavrilo Princip, a 19-year-old Bosnian Serb nationalist, shot Franz Ferdinand and his wife Sophie in Sarajevo on June 28, 1914. The assassination set off a chain of alliances and ultimatums that plunged Europe into World War I within weeks.",

    "The 13th Amendment's abolition of slavery was the culmination of what movement?":
        "The abolitionist movement grew from a small group of moral crusaders in the early 1800s into a powerful political force. Figures like Frederick Douglass, Harriet Tubman, and William Lloyd Garrison argued that slavery was a fundamental violation of the natural rights proclaimed in the Declaration of Independence.",

    "The 19th Amendment granting women the vote reflected what principle?":
        "Ratified in 1920 after decades of struggle by suffragists like Susan B. Anthony and Elizabeth Cady Stanton, the 19th Amendment recognized that a government claiming to represent 'the people' cannot exclude half of them. The movement began at the Seneca Falls Convention in 1848.",

    "The Spanish Armada was sent to invade ___?":
        "In 1588, Spain's King Philip II assembled a massive fleet of 130 ships to overthrow England's Protestant Queen Elizabeth I. The Armada was scattered by English fireships and storms, ending Spain's dream of conquering England and marking the rise of English naval power.",

    "India gained independence from Britain in ___?":
        "After nearly two centuries of British rule, India won independence on August 15, 1947. The moment was bittersweet: the subcontinent was simultaneously partitioned into Hindu-majority India and Muslim-majority Pakistan, triggering massive violence and the displacement of millions.",

    "The Chinese Communist Revolution succeeded in ___?":
        "Mao Zedong's Communist forces defeated Chiang Kai-shek's Nationalists after a brutal civil war, proclaiming the People's Republic on October 1, 1949. The Nationalists fled to Taiwan, where they established a rival government that persists to this day.",

    "Mao Zedong led ___?":
        "Mao founded the People's Republic of China and ruled until his death in 1976. His policies, including the Great Leap Forward and Cultural Revolution, caused tens of millions of deaths. He remains one of the most consequential and controversial figures in modern history.",

    "The Hundred Years' War was between ___?":
        "This series of conflicts (1337-1453) was fought over English claims to the French throne. It produced legendary figures like Joan of Arc, devastated the French countryside, and ultimately ended with France driving England off the continent.",

    "Charles Darwin published 'On the Origin of Species' in ___?":
        "Darwin's revolutionary work, published in 1859, presented his theory of evolution by natural selection. He had delayed publication for over 20 years, fearing the controversy it would cause. The first printing of 1,250 copies sold out on the first day.",

    "The Communist Manifesto was written by Marx and ___?":
        "Karl Marx and Friedrich Engels published the Communist Manifesto in 1848, calling on workers of the world to unite. Engels was the son of a wealthy factory owner, and his firsthand observations of working conditions informed the document that would inspire revolutions worldwide.",

    "The Battle of Waterloo was in ___?":
        "Napoleon's final defeat came on June 18, 1815, near Waterloo in modern-day Belgium. The Duke of Wellington's allied forces, aided by Prussian reinforcements, ended Napoleon's Hundred Days comeback and sent him into permanent exile on the remote island of Saint Helena.",

    "Martin Luther's 95 Theses in 1517 challenged the Church primarily over ___?":
        "Luther, an Augustinian monk, was outraged by Johann Tetzel selling indulgences -- essentially offering forgiveness of sins for money. His 95 Theses, nailed to the Wittenberg church door, sparked the Protestant Reformation and shattered the religious unity of Western Europe.",

    "The Louisiana Purchase was made from ___?":
        "In 1803, Napoleon sold the vast Louisiana Territory to the United States for approximately $15 million -- about 3 cents per acre. Napoleon needed money for his European wars, and the deal doubled the size of the young American nation overnight.",

    "The Titanic struck an iceberg in ___?":
        "On the night of April 14, 1912, the Titanic struck an iceberg in the North Atlantic on its maiden voyage from Southampton to New York. The ship, carrying over 2,200 people, sank in less than three hours in freezing waters.",

    "The Protestant Reformation challenged Church authority by arguing that ___?":
        "Reformers like Luther, Calvin, and Zwingli argued that each person could read and interpret Scripture for themselves, without needing a priest as intermediary. This idea of individual conscience over institutional authority would reshape not just religion, but politics and culture across the Western world.",

    "The Russian Revolution took place in ___?":
        "Two revolutions shook Russia in 1917: the February Revolution that toppled the Tsar, and the October Revolution in which Lenin's Bolsheviks seized power. The result was the world's first communist state, which would shape global politics for the rest of the century.",

    "The first transcontinental railroad in the US was completed in ___?":
        "On May 10, 1869, the Central Pacific and Union Pacific railroads met at Promontory Summit, Utah, where a golden spike was driven to mark the connection. A journey that once took months by wagon could now be made in days, transforming the American West.",

    "The New Deal was implemented by President ___?":
        "Franklin D. Roosevelt launched the New Deal in 1933 to combat the Great Depression, creating programs like Social Security, the SEC, and the WPA. It represented the largest expansion of federal government power in American history up to that point.",

    "The Marshall Plan helped rebuild ___?":
        "The Marshall Plan (1948-1952) pumped roughly $13 billion into rebuilding war-devastated Western Europe. Named after Secretary of State George Marshall, it helped prevent the spread of communism by restoring prosperity and stability to America's allies.",

    "NATO was founded in ___?":
        "The North Atlantic Treaty Organization was established on April 4, 1949, with 12 founding members. Its core principle -- that an attack on one is an attack on all -- was designed to deter Soviet aggression against Western Europe during the Cold War.",

    "The Nuremberg Trials judged ___?":
        "From 1945 to 1946, Allied nations prosecuted major Nazi leaders for war crimes, crimes against peace, and crimes against humanity. The trials established the principle that individuals -- even heads of state -- can be held personally responsible for atrocities.",

    # ── Tier 2 ──────────────────────────────────────────────────────────────

    "The Magna Carta limited the power of ___?":
        "The Magna Carta specifically limited the power of King John of England, but its real legacy was establishing that no ruler is above the law. Its principles of due process and limited government echoed through the centuries into the US Constitution and Bill of Rights.",

    "Who commanded the Allied forces on D-Day?":
        "General Dwight D. Eisenhower commanded the massive invasion from his headquarters in England. Before giving the order to go, he drafted a message accepting full blame in case the invasion failed. He later became the 34th President of the United States.",

    "The Bastille was stormed in ___?":
        "On July 14, 1789, a Parisian mob stormed the Bastille fortress-prison, a hated symbol of royal tyranny. Though it held only seven prisoners at the time, the act became the defining moment of the French Revolution. July 14 is still France's national holiday.",

    "Lewis and Clark's expedition was sent west by President ___?":
        "Thomas Jefferson commissioned Meriwether Lewis and William Clark to explore the newly acquired Louisiana Territory in 1804. Their epic journey to the Pacific and back lasted over two years, mapping unknown territory and establishing American claims to the West.",

    "The Battle of Gettysburg was in ___?":
        "The three-day battle of July 1-3, 1863, was the bloodiest of the Civil War, with roughly 50,000 casualties. The Union victory ended Lee's second invasion of the North and is widely considered the turning point of the war.",

    "The founding of Rome is traditionally dated to ___?":
        "Roman tradition placed the city's founding in 753 BC by Romulus, who according to legend killed his twin brother Remus in a dispute over where to build. From this mythic beginning grew an empire that would dominate the Mediterranean for centuries.",

    "Under which Khan was the Mongol Empire last unified before it fragmented into khanates?":
        "Mongke Khan, grandson of Genghis Khan, ruled the united Mongol Empire from 1251 until his death in 1259. After him, the empire fractured into four khanates that gradually went their separate ways, ending the era of unified Mongol power.",

    "The French Revolution ended with the rise of ___?":
        "After a decade of revolution, terror, and political chaos, Napoleon Bonaparte seized power in a coup in 1799. The French had overthrown a king only to end up with an emperor -- a pattern that has repeated throughout history.",

    "The Spanish-American War occurred in ___?":
        "The brief war of 1898 saw the US defeat Spain in just ten weeks, gaining control of Cuba, Puerto Rico, Guam, and the Philippines. It marked America's emergence as a global imperial power and the end of Spain's centuries-old colonial empire.",

    "The sinking of the Lusitania occurred in ___?":
        "A German U-boat torpedoed the British ocean liner RMS Lusitania off the coast of Ireland on May 7, 1915, killing 1,198 people, including 128 Americans. The sinking outraged the American public and helped shift US opinion toward entering World War I.",

    "Vladimir Lenin led the ___?":
        "Lenin masterminded the October Revolution of 1917, seizing power from the provisional government and establishing the world's first communist state. His slogan 'Peace, Land, and Bread' won popular support, though the reality of Bolshevik rule proved far grimmer than the promise.",

    "The Hiroshima atomic bomb was dropped on ___?":
        "The B-29 bomber Enola Gay dropped 'Little Boy' on Hiroshima at 8:15 AM on August 6, 1945, killing an estimated 80,000 people instantly. Three days later, a second bomb struck Nagasaki. Japan surrendered on August 15, ending World War II.",

    "The Berlin Blockade began in ___?":
        "In June 1948, the Soviet Union blocked all road, rail, and canal access to West Berlin, hoping to force the Western Allies out. The US and Britain responded with a massive airlift, flying in food and supplies for nearly a year until the Soviets lifted the blockade.",

    "Sputnik, the first satellite, was launched in ___?":
        "The Soviet Union launched Sputnik on October 4, 1957, shocking the world with its beeping signal from orbit. The basketball-sized satellite sparked the Space Race and prompted the US to create NASA and invest heavily in science education.",

    "The Bay of Pigs invasion was in ___?":
        "In April 1961, CIA-trained Cuban exiles attempted to overthrow Fidel Castro by landing at the Bay of Pigs. The invasion was a humiliating failure -- the exiles were quickly defeated and captured, embarrassing the new Kennedy administration.",

    "The Iranian Revolution occurred in ___?":
        "In 1979, a popular uprising toppled Shah Mohammad Reza Pahlavi and replaced his secular monarchy with an Islamic republic under Ayatollah Khomeini. The revolution stunned the world and reshaped Middle Eastern politics for decades to come.",

    "The Soviet invasion of Afghanistan began in ___?":
        "Soviet forces invaded Afghanistan in December 1979 to prop up a communist government. The ensuing ten-year war -- the Soviet Union's 'Vietnam' -- cost over a million Afghan lives and contributed to the USSR's eventual collapse.",

    "The Russo-Japanese War ended in ___?":
        "Japan's victory in 1905 stunned the world -- it was the first time in modern history that an Asian nation had defeated a European power. The humiliation contributed to the Russian Revolution of 1905 and established Japan as a major military force.",

    "The Meiji Restoration in Japan began in ___?":
        "In 1868, reformers overthrew the Tokugawa shogunate and restored power to Emperor Meiji. Japan transformed from a feudal society to an industrialized world power in just a few decades, one of the most remarkable modernizations in history.",

    "The Boxer Rebellion was against foreign influence in ___?":
        "In 1899-1901, the 'Boxers' -- Chinese martial artists formally known as the Society of Righteous and Harmonious Fists -- rose up against foreign powers and Chinese Christians. An eight-nation alliance crushed the rebellion, further humiliating the declining Qing Dynasty.",

    "Franz Ferdinand was assassinated in ___?":
        "Archduke Franz Ferdinand, heir to the Austro-Hungarian throne, was shot on June 28, 1914, in Sarajevo. The assassination triggered a chain reaction of alliances, ultimatums, and mobilizations that plunged Europe into the Great War within five weeks.",

    "The assassination of Franz Ferdinand triggered ___?":
        "Austria-Hungary blamed Serbia for the assassination and issued an ultimatum. Russia mobilized to defend Serbia, Germany backed Austria, France backed Russia, and Britain entered when Germany invaded Belgium. A single bullet in Sarajevo set off a war that killed 20 million people.",

    "The Battle of Trafalgar (1805) was won by ___?":
        "The Royal Navy under Admiral Nelson destroyed the combined French and Spanish fleets off Cape Trafalgar, Spain. The victory ensured British naval supremacy for a century and ended Napoleon's dreams of invading England.",

    "Horatio Nelson died at the Battle of ___?":
        "Admiral Nelson was shot by a French sniper during the Battle of Trafalgar on October 21, 1805. He died knowing his fleet had won a decisive victory. His last words were reportedly 'Thank God, I have done my duty.'",

    "The Emancipation Proclamation freed enslaved people in ___?":
        "The proclamation applied only to enslaved people in Confederate states -- not the border states that remained loyal to the Union. This was a strategic choice: Lincoln could not risk pushing the border states into the Confederacy.",

    "The Glorious Revolution of 1688 was significant because it ___?":
        "When Parliament replaced the Catholic King James II with the Protestant William and Mary, it established that Parliament -- not the monarch -- held supreme authority. The resulting Bill of Rights (1689) limited royal power and guaranteed key civil liberties.",

    "Genghis Khan died in ___?":
        "Genghis Khan died in 1227, leaving behind the largest contiguous land empire in history. The exact cause of his death remains a mystery -- theories range from a fall from his horse to illness. Even his burial site has never been found.",

    "The Aztec Empire was conquered by ___?":
        "Hernan Cortes arrived in Mexico in 1519 with about 600 men and conquered the Aztec Empire within two years. He exploited divisions among native peoples, formed alliances with the Aztecs' enemies, and used European weapons and diseases as devastating advantages.",

    "The Ottoman Empire captured Constantinople in ___?":
        "Sultan Mehmed II conquered Constantinople on May 29, 1453, ending over 1,000 years of Byzantine rule. The massive walls that had protected the city for centuries were breached by Ottoman cannons -- the largest ever built. The city was renamed Istanbul.",

    "The Seven Years' War lasted from 1756 to ___?":
        "Often called the first true 'world war,' the Seven Years' War was fought across Europe, North America, India, and the seas. Britain emerged as the dominant global power, gaining Canada and India, while France was left weakened and in debt.",

    "The Battle of Lexington and Concord was in ___?":
        "On April 19, 1775, British troops marched to seize colonial weapons stores and clashed with American militia at Lexington and Concord, Massachusetts. 'The shot heard round the world' began the American Revolution.",

    "The US Constitution was ratified in ___?":
        "After intense debate between Federalists and Anti-Federalists, the Constitution was ratified on June 21, 1788, when New Hampshire became the ninth state to approve it. The Bill of Rights was added in 1791 to address concerns about protecting individual liberties.",

    "The Battle of Yorktown ended the ___?":
        "In October 1781, combined American and French forces trapped British General Cornwallis at Yorktown, Virginia. The British surrender effectively ended the fighting in the American Revolution, though the formal peace treaty was not signed until 1783.",

    "The Molotov-Ribbentrop Pact (1939) between the USSR and Nazi Germany was significant because ___?":
        "Hitler and Stalin, sworn ideological enemies, secretly agreed to divide Eastern Europe between them. The pact freed Hitler to invade Poland without facing a two-front war. Stalin was shocked when Hitler broke the pact and invaded the Soviet Union in 1941.",

    "Kristallnacht (Night of Broken Glass) was in ___?":
        "On November 9-10, 1938, Nazi mobs attacked Jewish homes, businesses, and synagogues across Germany and Austria, shattering thousands of windows. Over 30,000 Jewish men were sent to concentration camps. It marked the shift from discrimination to outright persecution.",

    "The Molotov-Ribbentrop Pact was signed between the USSR and ___?":
        "The August 1939 non-aggression pact between sworn enemies Hitler and Stalin stunned the world. A secret protocol divided Poland and the Baltic states between them. The deal gave Hitler freedom to attack Poland, triggering World War II.",

    "The Battle of Stalingrad ended in German defeat in ___?":
        "The battle lasted from August 1942 to February 1943, with fighting so intense that the average life expectancy of a Soviet soldier was 24 hours. Germany's surrender of an entire army of 91,000 men marked the turning point of the war on the Eastern Front.",

    "The Battle of Midway was a turning point against ___?":
        "In June 1942, the US Navy sank four Japanese aircraft carriers at the Battle of Midway, just six months after Pearl Harbor. The victory shifted the balance of naval power in the Pacific and put Japan on the defensive for the rest of the war.",

    "The Treaty of Versailles is blamed for contributing to WWII because it ___?":
        "The treaty forced Germany to accept sole guilt for WWI, pay crippling reparations, and surrender territory. The resulting economic devastation and national humiliation created fertile ground for Hitler's rise to power and his promise to restore German greatness.",

    "Julius Caesar's assassination in 44 BC failed to save the Roman Republic because ___?":
        "Brutus and the other conspirators had no plan for what came after. Caesar's death sparked civil wars among his heirs and allies. Within 17 years, Caesar's adopted son Octavian became Augustus -- the first Roman Emperor -- proving that the Republic's institutions were already too broken to save.",

    "The Battle of the Somme began in ___?":
        "The British suffered nearly 60,000 casualties on the first day alone -- July 1, 1916 -- making it the bloodiest day in British military history. The battle dragged on for five months, gaining just six miles of ground at the cost of over a million total casualties.",

    "The Suez Canal was opened in ___?":
        "The canal, connecting the Mediterranean and Red Seas, opened on November 17, 1869, after ten years of construction. It cut the sea route from Europe to Asia by thousands of miles and became one of the most strategically important waterways in the world.",

    "Joan of Arc fought for ___?":
        "A teenage peasant girl who claimed divine visions, Joan of Arc led French armies to stunning victories during the Hundred Years' War. She lifted the siege of Orleans in 1429 and helped crown Charles VII. Captured by the English, she was burned at the stake at age 19.",

    "The Battle of Hastings was in ___?":
        "The battle on October 14, 1066, lasted a single day but changed England forever. King Harold was killed -- legend says by an arrow through his eye -- and William the Conqueror claimed the English throne, beginning the Norman era.",

    "The Yalta Conference of 1945 allowed Stalin to dominate Eastern Europe because ___?":
        "At Yalta in February 1945, Roosevelt and Churchill made concessions to Stalin partly because Soviet troops already occupied most of Eastern Europe. Stalin's promise of free elections was broken almost immediately, as communist regimes were installed across the region.",

    "The Battle of Marathon (490 BC) was between Athens and ___?":
        "Vastly outnumbered Athenian hoplites charged the Persian invaders at Marathon and won a decisive victory. A messenger reportedly ran 26 miles to Athens to announce the triumph -- the origin of the modern marathon race.",

    "The Rwandan Genocide of 1994, in which ~800,000 Tutsi were killed, was enabled primarily by ___?":
        "In just 100 days, Hutu extremists used radio propaganda and pre-distributed weapons lists to orchestrate mass murder. The international community, including the UN, failed to intervene despite clear warnings, making it one of the greatest moral failures of the late 20th century.",

    "Henry VIII broke from the Catholic Church to form ___?":
        "When Pope Clement VII refused to annul his marriage to Catherine of Aragon, Henry declared himself head of the Church of England in 1534. His break with Rome was driven by the desire for a male heir, but it permanently altered English religious and political life.",

    "The Scramble for Africa by European powers peaked in the ___?":
        "Between 1881 and 1914, European powers divided nearly the entire African continent among themselves. By 1914, only Ethiopia and Liberia remained independent. The arbitrary borders drawn by colonizers ignored ethnic and cultural boundaries, creating conflicts that persist today.",

    "The Boxer Rebellion occurred in ___?":
        "In 1900, the Boxer uprising reached its peak when rebels besieged foreign embassies in Beijing for 55 days. An eight-nation military force relieved the siege and imposed harsh terms on China, further weakening the Qing Dynasty.",

    "The Battle of Tsushima (1905) was a decisive victory for ___?":
        "Japan's fleet annihilated the Russian Baltic Fleet after it had sailed halfway around the world to reach the battle. The shocking victory established Japan as a major naval power and was the first modern defeat of a European nation by an Asian one.",

    "Stalin's Great Purge took place primarily in the ___?":
        "Between 1936 and 1938, Stalin executed an estimated 750,000 people and sent over a million more to the Gulag. He eliminated virtually all potential rivals, including most of Lenin's original Bolsheviks, military leaders, and countless ordinary citizens accused of imaginary crimes.",

    "The Anschluss was the annexation of Austria by ___?":
        "In March 1938, German troops marched into Austria unopposed, uniting it with Nazi Germany. Hitler, himself an Austrian, received a rapturous welcome in Vienna. The Western democracies protested but took no action -- emboldening Hitler to push further.",

    "The American Revolution was unique compared to the French Revolution because ___?":
        "The American revolutionaries sought to preserve their existing English legal rights, not to tear down society and rebuild it from scratch. They created a constitutional government with checks and balances, while the French Revolution descended into terror and dictatorship.",

    "The Yalta Conference was held in ___?":
        "Roosevelt, Churchill, and Stalin met in February 1945 at the Crimean resort of Yalta, with the war in Europe nearing its end. The conference shaped the post-war world order, dividing Europe into spheres of influence that would define the Cold War.",

    "The Iranian Revolution was led by ___?":
        "Ayatollah Ruhollah Khomeini, a Shia cleric exiled for 15 years, returned to Iran in February 1979 to lead an Islamic republic. His revolution overthrew the US-backed Shah and established a theocratic government that still rules Iran today.",

    "The Rwandan Genocide occurred in ___?":
        "In just 100 days from April to July 1994, Hutu extremists murdered approximately 800,000 Tutsi and moderate Hutu. The killing was carried out largely with machetes by neighbors against neighbors, while the world watched and did almost nothing.",

    "The Good Friday Agreement ended conflict in ___?":
        "The 1998 agreement brought an end to 'The Troubles' -- three decades of sectarian violence between Catholic nationalists and Protestant unionists in Northern Ireland that killed over 3,500 people. It established power-sharing government and disarmament of paramilitary groups.",

    "The Gulf War (Operation Desert Storm) was in ___?":
        "A US-led coalition of 35 nations liberated Kuwait from Iraqi occupation in just 42 days of combat in early 1991. The war showcased precision-guided weapons for the first time and demonstrated America's post-Cold War military dominance.",

    "The September 11 attacks occurred in ___?":
        "On September 11, 2001, al-Qaeda terrorists hijacked four airliners, crashing two into the World Trade Center, one into the Pentagon, and one into a Pennsylvania field after passengers fought back. Nearly 3,000 people died in the deadliest terrorist attack in history.",

    "The Fashoda Crisis (1898) was a standoff between Britain and ___?":
        "British and French forces faced off at Fashoda (now Kodok) in Sudan, where competing imperial ambitions collided. France ultimately backed down, avoiding war. The crisis actually helped push the two nations toward the Entente Cordiale alliance of 1904.",

    "The Battle of Hastings occurred in ___?":
        "October 14, 1066, saw William of Normandy defeat the English King Harold II. The Norman Conquest that followed replaced the Anglo-Saxon ruling class, introduced Norman French to the language, and reshaped English law and society for centuries.",

    "The Magna Carta's 'no taxation without consent' clause was the ancestor of what American principle?":
        "The Magna Carta's clause requiring the king to seek baronial consent before levying taxes planted the seed that grew into 'no taxation without representation' -- the rallying cry of the American Revolution 560 years later.",

    "Habeas corpus, the right not to be imprisoned without trial, originated in ___?":
        "The principle that no person can be held in prison without being charged and brought before a judge traces back to the Magna Carta and centuries of English common law. It remains one of the most fundamental protections against government tyranny.",

    "The English Bill of Rights of 1689 was passed after the Glorious Revolution and established ___?":
        "The Bill of Rights enshrined parliamentary sovereignty, guaranteeing that the monarch could not suspend laws, levy taxes, or maintain a standing army without Parliament's consent. It directly influenced the American Bill of Rights a century later.",

    "The Federalist Papers argued for ratifying the US Constitution primarily by defending ___?":
        "Written by Hamilton, Madison, and Jay under the pen name 'Publius,' the 85 Federalist essays made the case that dividing power among branches of government was the best safeguard against tyranny. Federalist No. 10, on factions, remains a masterpiece of political theory.",

    "John Locke's theory of natural rights, which influenced the Declaration of Independence, held that government derives its authority from ___?":
        "Locke argued that people form governments to protect their natural rights to life, liberty, and property. If a government violates those rights, the people may withdraw their consent and replace it. Jefferson drew heavily on Locke when drafting the Declaration.",

    "Montesquieu's concept of the separation of powers, which influenced the US Constitution, was designed to ___?":
        "In 'The Spirit of the Laws' (1748), Montesquieu argued that concentrating legislative, executive, and judicial power in one body inevitably produces tyranny. The American founders built his insight directly into the Constitution's three-branch structure.",

    "The Gulag system in the Soviet Union imprisoned millions of people for ___?":
        "The Gulag network of forced labor camps held an estimated 18 million people between 1930 and 1953. Prisoners included political dissidents, ethnic minorities, and ordinary citizens denounced by neighbors. Millions perished from overwork, starvation, and brutal conditions.",

    "Cuba under Castro's communist rule since 1959 has been characterized by ___?":
        "Despite promises of equality and prosperity, Castro's Cuba became a one-party state with rationed food, restricted travel, and political imprisonment. Over a million Cubans -- roughly 10% of the population -- fled the island, many risking their lives on makeshift rafts to reach Florida.",

    "Adam Smith's 'Wealth of Nations' (1776) argued that economic prosperity comes from ___?":
        "Smith showed that when individuals freely pursue their own interests in a competitive market, an 'invisible hand' guides resources to their most productive uses. His insight that voluntary exchange benefits both parties remains the foundation of modern economics.",

    "The Nuremberg Trials (1945-46) established the important legal principle that ___?":
        "The trials rejected the defense of 'superior orders,' holding that individuals have a moral duty to refuse criminal commands. This principle -- that obedience does not excuse atrocity -- became a cornerstone of international criminal law.",

    "North Korea's communist economy under the Kim dynasty demonstrates that ___?":
        "North Korea is the world's most isolated and repressive state, where chronic food shortages and political prison camps coexist with a nuclear weapons program. Its GDP per capita is roughly one-fortieth of South Korea's -- the starkest comparison of free vs. planned economies on Earth.",

    "The Athenian democracy of the 5th century BC was limited because it ___?":
        "Only adult male citizens -- roughly 10-15% of the total population -- could vote or hold office. Women, enslaved people, and foreign residents (metics) were excluded entirely. Yet even this limited democracy was revolutionary for its time.",

    "The Roman Senate's role in the Republic was to ___?":
        "The Senate was Rome's most powerful political institution, composed of about 300 wealthy men who controlled state finances, directed foreign policy, and advised elected magistrates. Its prestige was so great that Roman laws began with the phrase 'Senatus Populusque Romanus' -- the Senate and People of Rome.",

    "The Abolition of the Slave Trade Act (1807) in Britain was historically significant because it ___?":
        "Britain, then the world's most powerful naval nation, used its Royal Navy to enforce the ban, intercepting slave ships on the high seas. The act began the slow process of dismantling the Atlantic slave trade that had forcibly transported over 12 million Africans.",

    "The concept of judicial review, established in Marbury v. Madison (1803), means that ___?":
        "Chief Justice John Marshall's ruling established that the Supreme Court has the power to strike down laws that violate the Constitution. This power, not explicitly stated in the Constitution, made the judiciary a co-equal branch of government and the guardian of constitutional rights.",

    "The Second Amendment to the US Constitution protects the right to bear arms in the context of ___?":
        "The Second Amendment reads: 'A well regulated Militia, being necessary to the security of a free State, the right of the people to keep and bear Arms, shall not be infringed.' Its exact scope has been debated since its ratification in 1791.",

    "The trial by jury system, rooted in English common law, protects individuals by ___?":
        "Trial by jury means that ordinary citizens -- not government officials -- decide guilt or innocence. This principle, traceable to the Magna Carta, places a check on government power by requiring that the state convince twelve of a defendant's peers beyond a reasonable doubt.",

    "The Reconstruction Amendments (13th, 14th, 15th) after the Civil War were designed to ___?":
        "The 13th Amendment abolished slavery (1865), the 14th granted citizenship and equal protection (1868), and the 15th prohibited denying the vote based on race (1870). Together, they represent the most profound constitutional transformation since the founding.",

    "The American founding principle of 'limited government' means that ___?":
        "The founders believed government is a necessary but dangerous institution. They designed a system where federal powers are explicitly listed (enumerated) in the Constitution, and all other powers are reserved to the states or the people.",

    "The Enlightenment philosophers of the 18th century argued that government should be based on ___?":
        "Thinkers like Locke, Voltaire, Montesquieu, and Rousseau challenged the divine right of kings, arguing instead that reason and natural rights should be the basis of political authority. Their ideas directly inspired both the American and French Revolutions.",

    "The US Declaration of Independence asserted that when government fails to protect natural rights, citizens have the right to ___?":
        "Jefferson's Declaration laid out a radical argument: governments exist to protect rights, and when they fail, the people may 'alter or abolish' them. This was not just rhetoric -- it was the philosophical foundation for armed revolution against the British crown.",

    "Venezuela's socialist economic policies under Chavez and Maduro resulted in ___?":
        "Despite sitting atop the world's largest proven oil reserves, Venezuela's socialist policies produced hyperinflation exceeding 1,000,000%, widespread food shortages, and the emigration of over 7 million people. It stands as a cautionary tale about the consequences of state economic control.",

    "The US Supreme Court case Brown v. Board of Education (1954) ruled that ___?":
        "Chief Justice Earl Warren's unanimous ruling declared that 'separate but equal' schools were inherently unequal, overturning the 1896 Plessy v. Ferguson decision. The ruling was a landmark victory for the civil rights movement and began the desegregation of American public life.",

    "The appeasement policy toward Hitler at Munich (1938) failed because ___?":
        "British PM Chamberlain returned from Munich proclaiming 'peace for our time,' but Hitler saw the West's willingness to sacrifice Czechoslovakia as proof they would not fight. Within six months, Hitler seized the rest of Czechoslovakia and prepared to invade Poland.",

    "The Battle of Britain (1940) was significant because ___?":
        "For four months, the Royal Air Force fought off the German Luftwaffe in history's first major air campaign. Churchill captured the moment: 'Never in the field of human conflict was so much owed by so many to so few.' Britain's survival kept hope alive in occupied Europe.",

    "The phrase 'inalienable rights' in the Declaration of Independence means that ___?":
        "Jefferson chose the word 'unalienable' deliberately -- these rights cannot be given away, sold, or taken by any government because they are inherent to human nature itself. This philosophical claim was revolutionary: rights come from nature, not from kings.",

    "The Iron Curtain, as Churchill described it in 1946, divided Europe between ___?":
        "In his Fulton, Missouri speech, Churchill warned that 'from Stettin in the Baltic to Trieste in the Adriatic, an iron curtain has descended across the Continent.' The phrase became the defining metaphor for the Cold War division of Europe.",

    "Ronald Reagan's 'tear down this wall' speech at the Berlin Wall (1987) called for ___?":
        "Standing at the Brandenburg Gate, Reagan directly challenged Soviet leader Gorbachev to prove his reform credentials. Two years later, the Wall fell -- not because of a single speech, but because the system behind it could no longer sustain itself.",

    "The US Civil Rights Movement of the 1950s-60s succeeded primarily through ___?":
        "Leaders like Martin Luther King Jr. used nonviolent tactics -- sit-ins, boycotts, marches -- to expose the injustice of segregation on national television. By appealing to the Constitution's own promises, they shamed the nation into living up to its ideals.",

    "Martin Luther King Jr.'s 'I Have a Dream' speech appealed to ___?":
        "King masterfully invoked the Declaration of Independence's promise that 'all men are created equal,' calling it a 'promissory note' that America had yet to cash. His dream was not revolution but fulfillment -- asking America to honor its own founding principles.",

    "The US Supreme Court's role in protecting individual rights is based on ___?":
        "Through judicial review, the Court can declare laws unconstitutional, protecting individual rights even against the will of the majority. This counter-majoritarian role is one of the Constitution's most important safeguards against the tyranny of the majority.",

    "The fall of communism in Eastern Europe (1989-1991) was preceded by ___?":
        "Communist economies had stagnated for decades while the West prospered. When Gorbachev signaled that the Soviet Union would no longer use force to prop up satellite states, citizens who had lived under repression for 40 years seized their moment and demanded freedom.",

    "The Cuban Missile Crisis of 1962 ended when ___?":
        "After thirteen harrowing days, Kennedy and Khrushchev reached a deal: the Soviets would remove missiles from Cuba, the US would pledge not to invade Cuba and secretly remove missiles from Turkey. The crisis led directly to the nuclear 'hotline' between Washington and Moscow.",

    "The Tiananmen Square massacre (1989) demonstrated that ___?":
        "On June 4, 1989, Chinese troops and tanks killed hundreds -- possibly thousands -- of pro-democracy protesters in Beijing. The image of a lone man standing before a column of tanks became an iconic symbol of resistance against authoritarian power.",

    "The formation of NATO in 1949 was significant because it ___?":
        "NATO's Article 5 -- declaring that an attack on one member is an attack on all -- was the strongest peacetime military commitment in American history. It was first invoked after the September 11 attacks in 2001.",

    "The Berlin Airlift (1948-49) was the Western response to ___?":
        "When Stalin blockaded West Berlin, the Western Allies flew over 200,000 flights to deliver 2.3 million tons of food, fuel, and supplies. Planes landed every 30 seconds at the height of the operation, demonstrating Western resolve without firing a shot.",

    "The Civil Rights Act of 1964 prohibited discrimination based on ___?":
        "The landmark law outlawed discrimination in employment, public accommodations, and federally funded programs. It was the most sweeping civil rights legislation since Reconstruction, and President Johnson reportedly told an aide he had 'just delivered the South to the Republican Party.'",

    "The concept of 'popular sovereignty' in American democracy means that ___?":
        "This principle holds that the government's authority flows upward from the people, not downward from rulers. Lincoln captured it perfectly at Gettysburg: 'government of the people, by the people, for the people.'",

    "The ending of the Cold War demonstrated that ___?":
        "The peaceful collapse of the Soviet bloc showed that a system built on central planning and political repression could not compete with free market democracies over the long run. The contrast between the two Germanys -- prosperous West vs. stagnant East -- told the story.",

    "The 4th Amendment to the US Constitution protects against ___?":
        "The Fourth Amendment requires police to obtain a warrant based on probable cause before searching a person's home or belongings. It was inspired by the colonists' outrage at British 'writs of assistance' that allowed arbitrary searches.",

    "The Gettysburg Address argued that the Civil War was a test of whether ___?":
        "In just 272 words, Lincoln reframed the war from a fight to preserve the Union into a test of whether a nation 'conceived in liberty and dedicated to the proposition that all men are created equal' could survive.",

    "The abolitionist movement in America argued primarily that slavery was wrong because ___?":
        "Abolitionists invoked the Declaration of Independence's assertion that 'all men are created equal' and endowed with natural rights. Frederick Douglass asked the devastating question: 'What, to the American slave, is your Fourth of July?'",

    "The Monroe Doctrine (1823) was significant because it ___?":
        "President Monroe declared that the Western Hemisphere was closed to further European colonization. While the US lacked the military power to enforce it at the time, the doctrine became a cornerstone of American foreign policy for two centuries.",

    "Freedom of the press is considered essential to liberty because it ___?":
        "A free press acts as a 'watchdog' on government, exposing corruption and holding officials accountable. Thomas Jefferson famously wrote that if he had to choose between 'a government without newspapers or newspapers without a government, I should not hesitate a moment to prefer the latter.'",

    "The US Bill of Rights was added to the Constitution in 1791 primarily to ___?":
        "Anti-Federalists refused to ratify the Constitution without explicit protections for individual rights. James Madison drafted the ten amendments that became the Bill of Rights, guaranteeing freedoms of speech, religion, press, assembly, and protections against government overreach.",

    "The US Constitution's system of checks and balances was designed to prevent ___?":
        "Madison argued in Federalist No. 51 that 'ambition must be made to counteract ambition' -- each branch must have the power to check the others. The system was designed for a world where leaders are not angels and power must be restrained.",

    "The First Amendment to the US Constitution protects freedom of speech primarily to ___?":
        "The First Amendment protects not popular speech, which needs no protection, but unpopular and dissenting speech. The founders knew that a government that can silence its critics will inevitably become tyrannical.",

    "The concept of 'innocent until proven guilty' in Anglo-American law means ___?":
        "This bedrock principle shifts the burden of proof onto the state. A defendant need not prove innocence -- the prosecution must prove guilt beyond a reasonable doubt. It protects individuals from being convicted on suspicion alone.",

    "The Boston Tea Party (1773) was a protest against ___?":
        "On December 16, 1773, colonists disguised as Mohawk Indians dumped 342 chests of British East India Company tea into Boston Harbor. Their rallying cry -- 'no taxation without representation' -- became the philosophical foundation of the American Revolution.",

    "The English Civil War (1642-1651) was fought over the question of ___?":
        "King Charles I claimed divine right to rule without Parliament's consent. Parliament fought back, defeated the king's forces, and executed Charles in 1649 -- the first time a reigning monarch was publicly tried and put to death by his own subjects.",

    "The Underground Railroad was significant as a historical institution because it ___?":
        "This secret network of safe houses and routes helped an estimated 100,000 enslaved people escape to freedom between 1850 and 1860. Harriet Tubman, the most famous 'conductor,' personally guided about 70 people to freedom on 13 trips.",

    "The Stamp Act of 1765 provoked colonial outrage because it ___?":
        "The Stamp Act taxed every piece of printed paper in the colonies -- newspapers, legal documents, even playing cards. Colonists had no representatives in Parliament to vote on the tax. The resulting protest forced its repeal within a year.",

    "The Voting Rights Act of 1965 was passed to enforce ___?":
        "Despite the 15th Amendment (1870) guaranteeing the right to vote regardless of race, Southern states used literacy tests, poll taxes, and intimidation to disenfranchise Black voters. The Voting Rights Act finally gave the federal government teeth to enforce the constitutional guarantee.",

    "The US Supreme Court's Miranda v. Arizona (1966) ruling required that ___?":
        "The Court ruled 5-4 that suspects must be informed of their rights before police interrogation. The now-famous Miranda warning -- 'You have the right to remain silent...' -- became one of the most recognized phrases in American law.",

    "The Stonewall Riots (1969) in New York City launched ___?":
        "When police raided the Stonewall Inn, a gay bar in Greenwich Village, the patrons fought back for the first time. The three nights of protests that followed galvanized the modern LGBTQ+ rights movement and led to the first Gay Pride marches.",

    "The 10th Amendment to the US Constitution states that ___?":
        "The Tenth Amendment was included to reassure states that the new federal government would not swallow up their authority. It affirms the principle of federalism: the national government has only those powers specifically granted by the Constitution.",

    "Gandhi's nonviolent resistance movement in India demonstrated that ___?":
        "Gandhi's methods -- marches, boycotts, hunger strikes, and civil disobedience -- proved that organized moral courage could defeat an empire without firing a shot. His Salt March of 1930, protesting the British salt tax, drew worldwide attention to India's cause.",

    "The United States Constitution's system of federalism divides power between ___?":
        "Federalism was the founders' solution to the problem of governing a large, diverse nation. The national government handles defense, foreign policy, and interstate commerce, while states retain power over education, criminal law, and most daily governance.",

    "The 5th Amendment's protection against self-incrimination means that ___?":
        "This right, often invoked as 'pleading the Fifth,' prevents the government from forcing anyone to become a witness against themselves. It exists because the founders knew that coerced confessions are unreliable and that governments will use torture to extract them.",

    # ── Tier 3 ──────────────────────────────────────────────────────────────

    "The Treaty of Versailles ended ___?":
        "The treaty, signed on June 28, 1919, officially ended WWI but planted the seeds of WWII. Germany lost 13% of its territory, all overseas colonies, and was saddled with massive reparations. The humiliation fueled the nationalism that Hitler exploited.",

    "The main causes of WWI are summarized by the acronym ___?":
        "MAIN stands for Militarism, Alliance systems, Imperialism, and Nationalism -- the four forces that turned a regional crisis into a world war. Like dry kindling waiting for a spark, these tensions made a continental conflict almost inevitable.",

    "In MAIN, the 'M' stands for ___?":
        "Militarism -- the arms race between European powers, especially between Britain and Germany's naval buildup -- created an atmosphere where war seemed not only possible but almost desirable. Nations measured their prestige by the size of their armies and navies.",

    "In MAIN, the 'A' stands for ___?":
        "The complex web of alliances meant that a conflict between any two nations could drag in all the others. What should have been a localized dispute between Austria-Hungary and Serbia cascaded into a world war because of binding alliance commitments.",

    "Julius Caesar was assassinated in ___?":
        "On March 15, 44 BC, a group of senators stabbed Caesar to death on the floor of the Roman Senate. Shakespeare's version has Caesar say 'Et tu, Brute?' to his friend Brutus, but historians debate whether he actually spoke those words.",

    "Caesar was assassinated on the ___?":
        "The Ides of March -- March 15 in the Roman calendar -- became synonymous with betrayal and doom. A soothsayer had reportedly warned Caesar to 'beware the Ides of March,' but Caesar ignored the prophecy and walked to his death in the Senate.",

    "The Roman Republic transitioned to the Roman Empire under ___?":
        "Octavian, Caesar's adopted son, defeated all rivals in a series of civil wars and became Augustus Caesar in 27 BC. He cleverly maintained the appearance of republican government while holding absolute power -- creating a system that lasted for centuries.",

    "Emperor Theodosius I made Christianity the official religion of which empire?":
        "In 380 AD, Theodosius declared Nicene Christianity the state religion of the Roman Empire, banning pagan worship. This decision shaped Western civilization for the next 1,500 years, making Christianity the dominant force in European culture, politics, and art.",

    "The Silk Road was primarily used for ___?":
        "This network of trade routes stretched over 4,000 miles from China to the Mediterranean, carrying silk, spices, precious metals, and ideas. Along with goods, it transmitted religions, technologies, and -- unfortunately -- diseases like the Black Death.",

    "The Renaissance began approximately in which century?":
        "The Renaissance emerged in 14th-century Italy, particularly in Florence, where wealthy patrons like the Medici family funded artists and scholars. It was a 'rebirth' of classical Greek and Roman learning after the relative cultural stagnation of the Middle Ages.",

    "The Battle of Bunker Hill (1775) actually took place on ___?":
        "Despite the name, most of the fighting occurred on nearby Breed's Hill. The British won but suffered over 1,000 casualties -- far more than the Americans. The battle proved that colonial militia could stand against professional British soldiers.",

    "The Boston Massacre occurred in ___?":
        "On March 5, 1770, British soldiers fired into a crowd of colonists, killing five. Paul Revere's famous engraving of the event was propaganda -- the soldiers had been provoked by a rock-throwing mob -- but it brilliantly inflamed anti-British sentiment.",

    "The Continental Congress first met in ___?":
        "Delegates from twelve colonies (Georgia abstained) gathered in Philadelphia in September 1774 to coordinate their response to the Intolerable Acts. It was the first time the colonies acted together as something resembling a unified nation.",

    "The Articles of Confederation preceded the ___?":
        "America's first constitution (1781-1789) created a deliberately weak central government that could not tax, regulate commerce, or enforce its own laws. Its failure to address Shays' Rebellion and other crises proved that a stronger framework was needed.",

    "The War of 1812 ended in ___?":
        "The Treaty of Ghent, signed on December 24, 1814, ended the war with neither side gaining territory. Ironically, the Battle of New Orleans -- Andrew Jackson's famous victory -- was fought two weeks after the peace treaty was signed, because news traveled slowly.",

    "The 13th Amendment was ratified in ___?":
        "Ratified on December 6, 1865, the 13th Amendment permanently abolished slavery throughout the United States. Lincoln had pushed hard for it before his assassination, knowing that the Emancipation Proclamation alone was a wartime measure that might not survive peacetime.",

    "The Mexican-American War ended in ___?":
        "The Treaty of Guadalupe Hidalgo (1848) gave the US vast territories including California, Nevada, Utah, and parts of Arizona, New Mexico, Colorado, and Wyoming. The US paid Mexico $15 million -- a price many Americans and Mexicans considered a thinly veiled land grab.",

    "The Spanish-American War gave the US control of ___?":
        "The 1898 Treaty of Paris transferred Puerto Rico, Guam, and the Philippines to the United States. The war lasted just ten weeks but transformed America from a continental power into a global empire, sparking fierce debate about imperialism at home.",

    "The 14th Amendment granted citizenship to ___?":
        "Ratified in 1868, the 14th Amendment's sweeping language -- 'all persons born or naturalized in the United States' -- was designed to overturn the Dred Scott decision and guarantee citizenship to freed slaves. Its Equal Protection Clause became the basis for civil rights law.",

    "The Mughal Empire was founded by ___?":
        "Babur, a descendant of both Genghis Khan and Tamerlane, invaded India from Central Asia and defeated the Delhi Sultanate at the Battle of Panipat in 1526. His dynasty would rule most of the Indian subcontinent for over 300 years.",

    "The Mughal Empire was founded in ___?":
        "Babur's victory at Panipat in 1526 established a dynasty that produced some of India's greatest cultural achievements, including the Taj Mahal. At its peak under Akbar, the Mughal Empire governed roughly 150 million people.",

    "The Ottoman Empire was dissolved in ___?":
        "After ruling for over 600 years and controlling territory from Hungary to Yemen, the Ottoman Empire officially ended on November 1, 1922. Mustafa Kemal Ataturk abolished the sultanate and transformed the remnants into the modern Republic of Turkey.",

    "The Republic of Turkey was founded by ___?":
        "Mustafa Kemal Ataturk ('Father of the Turks') proclaimed the Republic on October 29, 1923. He launched sweeping reforms: replacing Arabic script with Latin, separating religion from government, and granting women the right to vote -- all in a single generation.",

    "The Battle of Thermopylae was between the Greeks and ___?":
        "In 480 BC, 300 Spartans and a few thousand Greek allies held the narrow pass of Thermopylae against hundreds of thousands of Persian invaders for three days. Their sacrifice became the ultimate symbol of courage against overwhelming odds.",

    "The Edict of Milan (313 AD) granted ___?":
        "Emperor Constantine's edict did not make Christianity the state religion -- it granted religious tolerance to all faiths, ending the persecution of Christians. Full establishment of Christianity came later under Theodosius I in 380 AD.",

    "Mao's Cultural Revolution (1966-1976) primarily targeted ___?":
        "Mao unleashed millions of fanatical Red Guards to destroy 'old customs, old culture, old habits, and old ideas.' Teachers were humiliated, temples were demolished, and an estimated 1-2 million people died. It was the most thorough attempt to erase a civilization's heritage in modern history.",

    "Charlemagne was crowned Emperor of the Romans in ___?":
        "Pope Leo III crowned Charlemagne on Christmas Day, 800 AD, in Rome -- the first time anyone had claimed the title of Roman Emperor in the West since 476. This moment laid the foundation for the idea of a united Christian Europe.",

    "The Protestant Reformation split the Christian church in the ___?":
        "Beginning with Luther's 95 Theses in 1517, the Reformation shattered the religious unity of Western Christendom within a generation. By mid-century, Lutheranism, Calvinism, and Anglicanism had established themselves as permanent alternatives to Roman Catholicism.",

    "The American Revolution was inspired partly by ___?":
        "Enlightenment thinkers like John Locke provided the intellectual ammunition for revolution. His ideas about natural rights, the social contract, and the right to revolt against tyranny permeate the Declaration of Independence almost word for word.",

    "The Berlin Conference (1884-85) partitioned ___?":
        "European powers sat around a table in Berlin and drew lines on a map of Africa, dividing an entire continent among themselves. No Africans were invited. The arbitrary borders, drawn through ethnic homelands, created conflicts that persist to this day.",

    "The Raj referred to British rule over ___?":
        "The British Raj (1858-1947) governed the Indian subcontinent as a colony after the Crown took control from the East India Company. At its height, it ruled over 300 million people -- the 'jewel in the crown' of the British Empire.",

    "Castro's Cuban Revolution of 1959, which replaced Batista with communism, resulted in ___?":
        "Castro promised democracy but delivered a communist dictatorship. Over the following decades, Cuba experienced persistent poverty, political repression, and mass emigration. Over a million Cubans fled, while those who remained lived under one-party rule.",

    "The Camp David Accords brought peace between Israel and ___?":
        "Egyptian President Anwar Sadat and Israeli PM Menachem Begin signed the historic peace agreement in 1978, brokered by President Carter. Sadat paid with his life -- he was assassinated in 1981 by Egyptian extremists who opposed peace with Israel.",

    "The Camp David Accords were signed in ___?":
        "After twelve intense days of negotiations at the presidential retreat in Maryland, Sadat and Begin signed the accords on September 17, 1978. It was the first peace treaty between Israel and an Arab nation, earning Sadat and Begin the Nobel Peace Prize.",

    "The Rwandan Genocide killed approximately ___?":
        "An estimated 800,000 people -- roughly 70% of the Tutsi population -- were murdered in just 100 days. The killing rate exceeded even the Holocaust in its intensity. UN peacekeepers on the ground were forbidden from intervening.",

    "The Good Friday Agreement was signed in ___?":
        "Signed on April 10, 1998 (Good Friday), the agreement established power-sharing between unionists and nationalists in Northern Ireland. It required compromise from all sides and was approved by referendums in both Northern Ireland and the Republic of Ireland.",

    "The Cuban Revolution succeeded in ___?":
        "Fidel Castro's guerrilla forces overthrew the Batista dictatorship on January 1, 1959. Castro initially denied being communist, but within two years he had nationalized industry, aligned with the Soviet Union, and established a one-party state.",

    "The Non-Aligned Movement was co-founded by ___?":
        "Indian PM Nehru, Egyptian President Nasser, and Yugoslav President Tito created the Non-Aligned Movement in 1961 to give developing nations a voice independent of both the US and Soviet superpowers. At its peak, it included over 100 nations.",

    "The Helsinki Accords were signed in ___?":
        "Signed on August 1, 1975, by 35 nations including the US and USSR, the accords recognized post-war borders in Europe while committing all signatories to respect human rights. Dissident groups in Eastern Europe used the human rights provisions to challenge communist rule.",

    "The Weimar Republic was established in Germany after ___?":
        "Germany's first democracy was born from the chaos of WWI's end in 1918. Burdened by the Treaty of Versailles, hyperinflation, and political extremism from both left and right, the Weimar Republic struggled for 14 years before Hitler destroyed it.",

    "The Bretton Woods Conference established ___?":
        "In July 1944, delegates from 44 nations met in Bretton Woods, New Hampshire, and created the International Monetary Fund and World Bank. These institutions established the dollar-based international monetary system that shaped the post-war global economy.",

    "The Yalta Conference divided post-war Europe among ___?":
        "Roosevelt, Churchill, and Stalin met at Yalta in February 1945 to plan the post-war order. The 'Big Three' agreed to divide Germany into occupation zones and hold free elections in liberated countries -- though Stalin had no intention of keeping that promise.",

    "The Bandung Conference of nonaligned nations was in ___?":
        "Twenty-nine Asian and African nations gathered in Bandung, Indonesia, in April 1955 to assert their independence from both Cold War blocs. The conference represented over half the world's population and signaled the rising voice of the postcolonial world.",

    "The OPEC oil embargo targeted ___?":
        "In October 1973, OPEC's Arab members cut oil production and banned exports to the US and other nations that supported Israel in the Yom Kippur War. Oil prices quadrupled, causing gas lines and economic shock across the Western world.",

    "The Crimean War (1853-1856) involved Russia and ___?":
        "Britain, France, and the Ottoman Empire fought Russia over control of territories in the declining Ottoman Empire. The war is remembered for the disastrous Charge of the Light Brigade and for Florence Nightingale's pioneering work in military nursing.",

    "Florence Nightingale became famous during which war?":
        "During the Crimean War (1853-1856), Nightingale and her team of nurses dramatically reduced death rates at British military hospitals by improving sanitation and care. Known as 'The Lady with the Lamp,' she founded modern nursing as a profession.",

    "The Missouri Compromise of 1820 addressed ___?":
        "The compromise admitted Missouri as a slave state and Maine as a free state, maintaining the balance of power in the Senate. It also drew a line across the Louisiana Territory: slavery was forbidden north of 36 degrees 30 minutes latitude. The compromise delayed civil war for 40 years.",

    "The Dred Scott decision ruled that enslaved people were ___?":
        "In 1857, Chief Justice Roger Taney ruled that enslaved people were property, not citizens, and had 'no rights which the white man was bound to respect.' The decision outraged the North and pushed the nation closer to civil war.",

    "Abraham Lincoln's Gettysburg Address was delivered at ___?":
        "Lincoln spoke for just two minutes on November 19, 1863, at the dedication of a cemetery for soldiers killed in the battle. The main speaker, Edward Everett, talked for two hours but wrote to Lincoln afterward: 'I wish I could flatter myself that I had come as near to the central idea of the occasion in two hours as you did in two minutes.'",

    "The Emancipation Proclamation applied to states ___?":
        "Lincoln carefully limited the proclamation to states 'in rebellion,' deliberately excluding the border states. This was a military order, not a moral one -- Lincoln was acting as commander-in-chief to weaken the Confederacy. Full abolition required the 13th Amendment.",

    "The Seneca Falls Convention of 1848 launched the ___?":
        "Organized by Elizabeth Cady Stanton and Lucretia Mott, the convention produced a Declaration of Sentiments modeled on the Declaration of Independence: 'We hold these truths to be self-evident: that all men and women are created equal.' It took 72 more years to win the vote.",

    "The Dreyfus Affair exposed antisemitism in ___?":
        "Captain Alfred Dreyfus, a French Jewish officer, was falsely convicted of treason in 1894 based on forged evidence. The affair divided France for over a decade and revealed deep currents of antisemitism in European society. Emile Zola's 'J'accuse!' helped expose the injustice.",

    "The Black Death reached Europe through ___?":
        "The plague traveled along the Silk Road trade routes from Central Asia, arriving on Genoese trading ships from the Black Sea port of Caffa in 1347. Legend has it that the Mongol besiegers catapulted plague-infected corpses over the city walls.",

    "The Renaissance is associated with a rebirth of ___?":
        "Artists and scholars rediscovered the works of ancient Greece and Rome, which had been largely forgotten in Western Europe during the Middle Ages. This rediscovery sparked an explosion of creativity in art, architecture, science, and philosophy that transformed European civilization.",

    "The Reign of Terror (1793-1794) during the French Revolution resulted in approximately how many executions?":
        "The guillotine became the symbol of revolutionary 'justice,' claiming 17,000 official victims, while tens of thousands more died in prison or in mass drownings ordered by local committees. Robespierre himself was eventually consumed by the machine he had helped create.",

    "Maximilien Robespierre justified the Reign of Terror by arguing that ___?":
        "Robespierre declared that 'Terror is nothing more than speedy, severe, and inflexible justice -- it is thus an emanation of virtue.' This chilling logic -- that extreme violence is justified in pursuit of a perfect society -- has been used by tyrants ever since.",

    "Stalin's Great Purge of the 1930s resulted in approximately how many deaths?":
        "Stalin's paranoia drove him to execute approximately 750,000 people and imprison millions more. He eliminated nearly all of Lenin's original Bolsheviks, most of the military high command, and countless ordinary citizens on fabricated charges.",

    "Mao's Great Leap Forward (1958-1962) caused a famine that killed approximately ___?":
        "Mao's forced collectivization of agriculture and delusional production targets caused the deadliest famine in human history. Local officials reported fake bumper harvests while peasants starved. Estimates range from 15 to 55 million dead.",

    "The Khmer Rouge's collectivist regime in Cambodia (1975-1979) killed what proportion of the country's population?":
        "Pol Pot's regime murdered roughly 2 million people -- one-quarter of Cambodia's entire population -- in just four years. Intellectuals, city-dwellers, and anyone wearing glasses (seen as a sign of education) were targeted for death.",

    "Nazi Germany's economic policy under the Third Reich was characterized by ___?":
        "The Nazis did not abolish private ownership but directed all economic activity toward state goals, especially rearmament. Companies that cooperated were rewarded; those that resisted were nationalized or destroyed. It was neither free-market capitalism nor Soviet communism, but a third path to totalitarianism.",

    "The term 'National Socialism' (Nazism) reflected that the Nazi party ___?":
        "The name was deliberately chosen to appeal to both nationalist and working-class voters. The Nazis rejected Marxist internationalism but embraced state control of economic life. Hitler himself said the party was 'socialist' in putting the national community above the individual.",

    "The collapse of socialist economies in Eastern Europe after 1989 demonstrated that ___?":
        "When the Iron Curtain fell, the world saw the stark contrast: West Germany's GDP per capita was roughly triple East Germany's. The failure was not just economic -- central planning had also produced environmental devastation and technological stagnation.",

    "The English common law tradition is significant to individual liberty because it ___?":
        "Common law builds rights through centuries of judicial precedent, case by case, creating protections that no single ruler can easily sweep away. This bottom-up legal tradition contrasts sharply with top-down civil law systems where the state grants rights by decree.",

    "William Wilberforce's campaign to abolish the British slave trade succeeded because he argued that ___?":
        "For 20 years, Wilberforce introduced abolition bills in Parliament, appealing to Christian conscience and natural rights. His persistence finally paid off in 1807. He died in 1833, just three days after hearing that the Slavery Abolition Act had passed.",

    "The Glorious Revolution of 1688 influenced the American founding because it ___?":
        "The bloodless replacement of James II with William and Mary showed that rulers who violate the law can be peacefully removed. The American founders drew on this precedent -- government exists by consent, and consent can be withdrawn.",

    "The Dred Scott decision (1857) was later overturned because it ___?":
        "The 14th Amendment (1868) directly repudiated the Dred Scott ruling by declaring that all persons born in the United States are citizens. Chief Justice Taney's assertion that Black people had 'no rights which the white man was bound to respect' became one of the most reviled statements in American legal history.",

    "George Washington's Farewell Address warned against ___?":
        "Washington cautioned that 'the spirit of party' and 'permanent alliances with foreign nations' could destroy the republic. His warnings about partisan faction tearing the nation apart have proven remarkably prescient over two centuries.",

    "The Chinese Cultural Revolution's campaign against 'the Four Olds' targeted ___?":
        "Red Guards destroyed temples, burned books, smashed artworks, and humiliated teachers and intellectuals. The campaign sought to erase thousands of years of Chinese civilization in the name of communist purity. Countless irreplaceable cultural treasures were lost forever.",

    "The concept of 'natural law' in Western political philosophy holds that ___?":
        "From Cicero to Aquinas to Locke, natural law theory holds that certain moral principles are woven into the fabric of reality itself. No law made by humans can legitimately violate these principles -- a tyrant's decree is not truly 'law' at all.",

    "The Petition of Right (1628) in England established that ___?":
        "When Parliament forced King Charles I to accept the Petition of Right, it reaffirmed that the king could not imprison subjects arbitrarily or impose taxes without parliamentary consent. Charles later ignored these limits, leading to the English Civil War.",

    "The Bolshevik Revolution of 1917 promised 'peace, land, and bread' but delivered ___?":
        "Lenin's promises won popular support, but the reality was continued war (the Russian Civil War), collectivized land (not given to peasants), and eventual famine. The revolution consumed an estimated 7-12 million lives in its first decade.",

    "The Thirty Years' War (1618-1648) began as a conflict over ___?":
        "The war started when Protestant Bohemians threw Catholic imperial officials out of a window in Prague (the 'Defenestration of Prague'). What began as a religious conflict in the Holy Roman Empire escalated into a continent-wide power struggle that killed roughly 8 million people.",

    "The Peace of Westphalia (1648) was historically significant because it ___?":
        "The treaties that ended the Thirty Years' War established the principle of state sovereignty -- that each nation has the right to govern its own affairs without outside interference. This idea became the foundation of the modern international system.",

    "Pericles described Athenian democracy in his Funeral Oration as a government that ___?":
        "Pericles declared that Athens 'does not copy the laws of neighboring states; we are rather a pattern to others.' His speech, recorded by Thucydides, remains one of history's most powerful defenses of democratic self-government.",

    "The Roman Republic's constitution was notable for having ___?":
        "The dual consulship was designed so that each consul could veto the other, preventing any one person from accumulating too much power. This principle of divided executive authority directly influenced the American founders' thinking about checks and balances.",

    "The concept of veto power originated in the Roman Republic when tribunes could ___?":
        "The tribunes of the plebs could cry 'Veto!' ('I forbid!') to block any action by the Senate or magistrates. This power was created after a plebeian secession -- the common people literally walked out of Rome until the aristocrats agreed to give them a voice.",

    "Frederick Douglass's autobiography was significant because it ___?":
        "Douglass's 'Narrative of the Life of Frederick Douglass' (1845) was a literary masterpiece written by a formerly enslaved man, demolishing the racist myth that Black people were intellectually inferior. It became one of the most influential works in American literature.",

    "The Fugitive Slave Act of 1850 was controversial in the North because it ___?":
        "The law compelled Northern citizens to assist in capturing escaped slaves or face fines and imprisonment. It turned every Northerner into a potential slave-catcher and radicalized many who had been indifferent to abolition.",

    "The Louisiana Purchase of 1803 was controversial because ___?":
        "Jefferson, a strict constructionist, agonized over whether the Constitution allowed the president to purchase territory. He went ahead anyway, doubling the nation's size for about 3 cents an acre. Even his political opponents admitted it was a remarkable bargain.",

    "The Soviet collectivization of agriculture in the early 1930s caused a famine in Ukraine known as ___?":
        "The Holodomor ('death by hunger') killed an estimated 3-7 million Ukrainians between 1932-1933. Stalin's regime confiscated grain from starving peasants to export abroad and punish Ukrainian resistance to collectivization. Many scholars consider it a deliberate genocide.",

    "The Warsaw Pact's 1956 crushing of the Hungarian Uprising demonstrated that ___?":
        "When Hungarian students and workers demanded freedom, Soviet tanks rolled into Budapest and killed an estimated 2,500 Hungarians. The West watched but did nothing, revealing that nuclear deterrence made it impossible to liberate nations behind the Iron Curtain.",

    "The Solidarity trade union movement in Poland was significant because it ___?":
        "Founded in 1980 by Lech Walesa at the Gdansk shipyard, Solidarity grew to 10 million members -- a quarter of Poland's population. Despite martial law and years of repression, it survived underground and led Poland's transition to democracy in 1989.",

    "The Holocaust was made possible partly by ___?":
        "The Nazis applied industrial efficiency to mass murder, building death camps with gas chambers and crematoria. Hannah Arendt called it the 'banality of evil' -- ordinary bureaucrats processed paperwork that sent millions to their deaths.",

    "The Nuremberg Principles established by the post-WWII trials held that individuals can be guilty of ___?":
        "The Nuremberg Principles declared that 'the fact that a person acted pursuant to order of his Government or of a superior does not relieve him from responsibility.' This principle -- that moral duty transcends obedience -- remains the foundation of international criminal law.",

    "The Nuremberg Laws (1935) in Nazi Germany stripped Jews of ___?":
        "These laws classified people by 'blood' and stripped German Jews of citizenship, the right to vote, and the right to marry non-Jews. They were the legal foundation for the escalating persecution that culminated in the Holocaust.",

    "The Soviet Union's use of 'show trials' in the 1930s Purges was designed to ___?":
        "Old Bolsheviks like Bukharin and Zinoviev were forced to publicly 'confess' to absurd charges of treason and sabotage before being executed. The confessions were extracted through torture and threats against family members. The trials served as theater of terror to intimidate the entire population.",

    "The American founding doctrine of 'natural rights' holds that rights are ___?":
        "This doctrine holds that rights exist before government and cannot be created or destroyed by it. Government's purpose is to protect these pre-existing rights -- and when it fails, the people may replace it. Jefferson put it simply: rights come from 'the Laws of Nature and of Nature's God.'",

    "The Emancipation Proclamation (1863) was limited in scope because it ___?":
        "Lincoln freed slaves only in Confederate states because the proclamation was a military measure -- depriving the South of labor. Border states like Kentucky and Missouri, which remained loyal to the Union, were excluded to keep them from joining the Confederacy.",

    "The Kansas-Nebraska Act of 1854 inflamed sectional tensions because it ___?":
        "Senator Stephen Douglas's act allowed settlers in Kansas and Nebraska to decide slavery for themselves, effectively repealing the Missouri Compromise's prohibition on slavery north of 36 degrees 30 minutes. The result was 'Bleeding Kansas' -- a mini civil war on the frontier.",

    "The Articles of Confederation (1781-1789) failed as a governing document because ___?":
        "Under the Articles, Congress could not tax, regulate trade, or enforce its laws. When Shays' Rebellion threatened Massachusetts in 1786 and Congress could not raise troops to respond, the founders realized the Articles had to be replaced.",

    "The Three-Fifths Compromise in the original US Constitution ___?":
        "The compromise counted each enslaved person as three-fifths of a person for purposes of congressional representation. It gave Southern states disproportionate political power without giving enslaved people any rights. It was finally nullified by the 14th Amendment.",

    "John Adams's defense of British soldiers after the Boston Massacre demonstrated ___?":
        "Adams, a patriot, defended the soldiers because he believed that even the most despised defendants deserve a fair trial. He won acquittals for six of eight soldiers, proving that the rule of law must apply even to one's enemies.",

    "The Truman Doctrine (1947) marked a shift in US foreign policy by committing to ___?":
        "When Britain could no longer support Greece and Turkey against communist insurgencies, Truman asked Congress for $400 million in aid. His speech declared that the US would 'support free peoples who are resisting attempted subjugation' -- launching the containment strategy.",

    "The Marshall Plan's goal of rebuilding European economies after WWII was partly motivated by ___?":
        "Secretary of State George Marshall recognized that hungry, desperate people are vulnerable to communist promises. By rebuilding Western Europe's economies, the US created prosperous democracies that had no interest in Soviet-style revolution.",

    "The containment strategy in the Cold War, articulated by George Kennan, held that ___?":
        "Kennan argued that communism's internal contradictions would eventually destroy it -- if the West could prevent its spread in the meantime. The strategy required patience: contain Soviet expansion for decades and wait for the system to collapse under its own weight.",

    "The Great Leap Forward's failure in China (1958-1962) was caused primarily by ___?":
        "Mao ordered peasants to abandon farming and make steel in backyard furnaces while officials reported impossible crop yields to avoid punishment. The resulting agricultural collapse caused the worst famine in recorded history.",

    "Margaret Thatcher's economic reforms in Britain (1979-1990) reversed ___?":
        "Britain in the 1970s suffered from nationalized industries, powerful unions, and economic stagnation -- the 'British disease.' Thatcher privatized state enterprises, broke union power, and cut taxes, transforming Britain's economy at the cost of significant social upheaval.",

    "The American Anti-Federalists opposed the Constitution because they feared ___?":
        "Anti-Federalists like Patrick Henry and George Mason warned that the Constitution created a government so powerful it would swallow state sovereignty and individual liberty. Their insistence on a Bill of Rights as a condition of ratification proved prescient.",

    "The Prague Spring of 1968 in Czechoslovakia was an attempt to create ___?":
        "Alexander Dubcek tried to reform communism from within, allowing greater freedom of speech and press while maintaining the socialist system. Soviet tanks crushed the experiment in August, and Dubcek's dream of 'socialism with a human face' died in the streets of Prague.",

    "Winston Churchill's 'Iron Curtain' speech (1946) was significant because it ___?":
        "Speaking in Fulton, Missouri, with President Truman in the audience, Churchill warned that Soviet domination of Eastern Europe was a fait accompli. The speech helped crystallize Western public opinion that the wartime alliance with Stalin was over.",

    "The League of Nations' failure to stop Italian aggression in Ethiopia (1935) showed that ___?":
        "When Mussolini invaded Ethiopia, the League imposed weak sanctions but refused to use military force. Emperor Haile Selassie's plea to the League -- 'It is us today. It will be you tomorrow.' -- was tragically prophetic.",

    "The US Senate's rejection of the Treaty of Versailles in 1919 was based on opposition to ___?":
        "Senator Henry Cabot Lodge led opposition to the League of Nations, arguing it could commit American troops to foreign wars without Congressional approval. The rejection marked a return to isolationism that lasted until World War II.",

    "The Reconstruction period (1865-1877) after the Civil War failed to protect Black civil rights because ___?":
        "When federal troops withdrew from the South in 1877 as part of a political compromise, Southern states quickly imposed Jim Crow laws, poll taxes, and literacy tests. The promise of Reconstruction would not be fulfilled for nearly a century.",

    "The Industrial Revolution began in Britain rather than elsewhere partly because Britain had ___?":
        "Britain's unique combination of secure property rights, rule of law, coal deposits, navigable rivers, and a culture that respected commerce and innovation created the conditions for the first Industrial Revolution. Inventors could profit from their innovations without fear of confiscation.",

    "The New Deal's expansion of federal government in the 1930s was based on the argument that ___?":
        "FDR argued that the Great Depression proved that unregulated markets could produce catastrophic failures requiring government intervention. Programs like Social Security, bank insurance, and labor protections permanently expanded the federal role in American economic life.",

    "The Weimar Republic's hyperinflation crisis of 1923 was caused primarily by ___?":
        "The German government printed money furiously to pay reparations and support striking workers in the French-occupied Ruhr. At its peak, prices doubled every few days -- workers were paid twice daily and rushed to spend their wages before they became worthless.",

    "Thomas Paine's 'Common Sense' (1776) argued that ___?":
        "Paine's pamphlet, written in plain language anyone could understand, sold over 500,000 copies in a few months. He argued that hereditary monarchy was absurd -- 'Of more worth is one honest man to society than all the crowned ruffians that ever lived.'",

    "The Constitution's Commerce Clause gives Congress power to regulate ___?":
        "The Commerce Clause was designed to prevent states from imposing tariffs on each other, creating a single national market. Over time, courts have interpreted it broadly, making it one of the most powerful -- and contested -- provisions in the Constitution.",

    "The Northwest Ordinance of 1787 was significant because it ___?":
        "The Ordinance established that new territories could become states with full equality to the original thirteen. This was revolutionary -- rather than being permanent colonies, new lands would join the Union as equals. It also banned slavery in the Northwest Territory.",

    "The Treaty of Paris of 1763 ended the Seven Years' War and gave Britain ___?":
        "Britain's victory gave it virtually all of France's North American territory east of the Mississippi, plus Canada. Ironically, removing the French threat made the American colonies feel less dependent on British military protection -- paving the way for revolution.",

    "The Chartist movement in Britain (1838-1857) demanded ___?":
        "The Chartists presented Parliament with petitions bearing millions of signatures demanding universal male suffrage, secret ballots, and equal electoral districts. Though the movement failed in the short term, nearly all its demands were eventually enacted into law.",

    "The Dreyfus Affair (1894-1906) in France was significant because it ___?":
        "The false conviction of Captain Alfred Dreyfus revealed that antisemitism, military cover-ups, and forged evidence could pervert justice even in a republic. Emile Zola's 'J'Accuse!' letter risked everything to expose the truth.",

    "The Meiji Restoration's rapid modernization of Japan showed that ___?":
        "In less than 50 years, Japan went from a feudal society closed to the outside world to an industrialized nation that defeated a European power (Russia) in war. Japan proved that modernization does not require abandoning national identity.",

    "The Gulf War (1991) was authorized by the United Nations because ___?":
        "Saddam Hussein's invasion and annexation of Kuwait in August 1990 was a clear violation of the UN Charter. The Security Council authorized force to restore Kuwaiti sovereignty -- one of the few times the UN collective security system worked as intended.",

    "The Reagan economic policies ('Reaganomics') were based on the theory that ___?":
        "Supply-side economics held that cutting taxes, especially on businesses and higher earners, would spur investment and growth. The US economy did grow significantly in the 1980s, though debate continues over how much credit goes to tax cuts versus other factors.",

    "The Sykes-Picot Agreement (1916) drew borders in the Middle East that ___?":
        "Britain and France secretly divided the Ottoman Empire's Arab lands between themselves, drawing borders with rulers and pencils that ignored centuries of ethnic, religious, and tribal geography. The artificial states they created -- Iraq, Syria, Lebanon, Jordan -- have struggled with internal conflicts ever since.",

    "The Missouri Compromise admitted Missouri as a slave state and ___?":
        "Henry Clay brokered the deal: Missouri entered as a slave state, Maine as a free state, and slavery was banned north of 36 degrees 30 minutes in the Louisiana Territory. Thomas Jefferson called the crisis 'a firebell in the night' that foretold the coming Civil War.",

    "The Dred Scott decision was made by the ___?":
        "Chief Justice Roger Taney's Supreme Court ruling in 1857 was one of the most reviled decisions in American history. Rather than settling the slavery question, it inflamed tensions and pushed the nation closer to civil war.",

    "The Spanish-American War began in ___?":
        "The explosion of the USS Maine in Havana harbor in February 1898 -- likely an accident -- was blamed on Spain. 'Remember the Maine!' became a rallying cry, and the resulting war lasted just ten weeks but made the US a colonial power.",

    "The Progressive Era in the US occurred primarily in the ___?":
        "From roughly 1900 to 1920, Progressive reformers attacked corruption, child labor, unsafe food, and political machine politics. Their achievements included the Pure Food and Drug Act, women's suffrage, and the direct election of senators.",

    "The 16th Amendment established ___?":
        "Ratified in 1913, the 16th Amendment gave Congress the power to levy an income tax. The original rate was just 1% on income over $3,000 -- a far cry from modern rates. It transformed the federal government's ability to raise revenue.",

    "The 17th Amendment established ___?":
        "Before 1913, US senators were chosen by state legislatures, which often led to corruption and deadlock. The 17th Amendment allowed voters to elect senators directly, making the Senate more democratic and responsive to the public.",

    "The 18th Amendment established ___?":
        "Ratified in 1919, the 18th Amendment banned the manufacture, sale, and transportation of alcohol. Prohibition lasted 13 years but proved unenforceable -- it spawned organized crime, speakeasies, and widespread contempt for the law.",

    "The 21st Amendment ___?":
        "Ratified in 1933, the 21st Amendment is the only constitutional amendment that repeals another. It ended the 'noble experiment' of Prohibition after 13 years of bootlegging, gang violence, and widespread lawbreaking had proven the policy a failure.",

    "The Reconstruction Amendments (13th, 14th, 15th) after the Civil War were designed to ___?":
        "The 13th Amendment abolished slavery (1865), the 14th granted citizenship and equal protection (1868), and the 15th prohibited denying the vote based on race (1870). Together they represent the most sweeping constitutional transformation since the founding.",

    # ── Tier 4 ──────────────────────────────────────────────────────────────

    "Who was crowned 'Emperor of the Romans' by Pope Leo III in 800 AD?":
        "Charlemagne, King of the Franks, was crowned on Christmas Day 800 AD in St. Peter's Basilica. The event symbolized the merger of Germanic, Roman, and Christian traditions that would define medieval Europe. Legend says Charlemagne was surprised by the coronation.",

    "The Hundred Years' War lasted from 1337 to ___?":
        "The war actually lasted 116 years, ending in 1453 when France finally expelled England from the continent (except Calais). It began as a dynastic dispute but became a war of national identity that forged the modern nations of England and France.",

    "The Spanish Armada was defeated in ___?":
        "In 1588, English fireships scattered the Spanish fleet in the English Channel, and storms finished the job. Only about half of Spain's 130 ships made it home. The defeat marked the decline of Spanish naval power and the rise of England's.",

    "The Thirty Years' War began in ___?":
        "The war started in 1618 when Protestant Bohemian nobles threw two Catholic imperial officials out of a window in Prague. This 'Defenestration of Prague' escalated into Europe's most devastating conflict before the 20th century.",

    "The Peace of Augsburg (1555) established ___?":
        "The principle 'cuius regio, eius religio' -- 'whose realm, his religion' -- meant each ruler could determine whether their territory would be Catholic or Lutheran. It preserved peace for 63 years but left Calvinists and other Protestants unprotected.",

    "The Battle of Lepanto (1571) was fought between Christendom and ___?":
        "A massive fleet of the Holy League destroyed the Ottoman navy at Lepanto, Greece, on October 7, 1571. The victory halted Ottoman expansion in the western Mediterranean. Miguel de Cervantes, author of Don Quixote, lost the use of his left hand in the battle.",

    "The Sykes-Picot Agreement divided the ___?":
        "In 1916, British diplomat Mark Sykes and French diplomat Francois Georges-Picot secretly drew lines on a map, carving up the Ottoman Empire's Arab provinces. When the agreement was exposed, it was seen as a betrayal of Arab allies who had been promised independence.",

    "The Balfour Declaration (1917) supported ___?":
        "British Foreign Secretary Arthur Balfour wrote a 67-word letter supporting 'the establishment in Palestine of a national home for the Jewish people.' This single letter, driven by wartime politics, set in motion one of the 20th century's most enduring conflicts.",

    "The Treaty of Versailles imposed war guilt on ___?":
        "Article 231 -- the 'War Guilt Clause' -- forced Germany to accept sole responsibility for causing WWI. This humiliation, combined with massive reparations, created the resentment and economic desperation that Hitler would later exploit.",

    "The Night of the Long Knives eliminated the ___?":
        "On June 30, 1934, Hitler ordered the murder of SA leader Ernst Rohm and other potential rivals. The purge eliminated the SA (brownshirt) leadership and consolidated Hitler's power. The army, which had feared the SA, swore personal loyalty to Hitler in return.",

    "The Anschluss occurred in ___?":
        "German troops marched into Austria on March 12, 1938, to cheering crowds. The annexation had been explicitly forbidden by the Treaty of Versailles, but the Western democracies did nothing. A rigged plebiscite showed 99.73% approval.",

    "The Battle of El Alamein was fought in ___?":
        "In October-November 1942, British Field Marshal Montgomery defeated Rommel's Afrika Korps in the Egyptian desert. Churchill called it 'the end of the beginning' -- the first major British land victory against Germany and a turning point in the North African campaign.",

    "The Battle of Midway was in ___?":
        "In June 1942, US codebreakers cracked Japanese naval communications and set a trap at Midway atoll. American dive-bombers sank four Japanese carriers in five minutes, turning the tide of the Pacific War just six months after Pearl Harbor.",

    "The Zimmermann Telegram was sent in ___?":
        "In January 1917, Germany's Foreign Secretary Arthur Zimmermann sent a coded telegram to Mexico proposing a military alliance against the United States. British intelligence intercepted and decoded it. When published, the telegram's revelation helped push America into WWI.",

    "The Mughal Emperor Akbar was known for ___?":
        "Akbar the Great (r. 1556-1605) abolished the hated jizya tax on non-Muslims, married Hindu princesses, and invited scholars of all faiths to debate at his court. His policy of 'sulh-i-kul' (universal tolerance) made him one of history's most enlightened rulers.",

    "The Taj Mahal was built by Mughal Emperor ___?":
        "Shah Jahan built the Taj Mahal as a tomb for his beloved wife Mumtaz Mahal, who died giving birth to their 14th child in 1631. It took 22 years and 20,000 workers to complete. Many consider it the most beautiful building ever created.",

    "The Thirty Years' War ended with the ___?":
        "The Peace of Westphalia (1648) ended the war and established the modern concept of state sovereignty -- the idea that each nation has the right to govern its own affairs without outside interference. It became the foundation of international relations.",

    "The English Civil War ended with ___?":
        "King Charles I was tried for treason and publicly beheaded on January 30, 1649, in front of the Banqueting House in London. It was the first time a reigning European monarch had been put on trial and executed by his own subjects.",

    "The Thirty Years' War was primarily fought over ___?":
        "What began as a religious conflict between Catholics and Protestants in the Holy Roman Empire evolved into a general European power struggle. France, a Catholic nation, fought on the Protestant side to weaken the Habsburgs -- proving that politics trumped religion.",

    "The Second Sino-Japanese War began in ___?":
        "Japan's full-scale invasion of China in 1937 marked the beginning of WWII in Asia. The Nanjing Massacre, in which Japanese troops killed an estimated 200,000-300,000 Chinese civilians, remains one of the war's most horrific atrocities.",

    "The Battle of the Marne (1914) stopped the German advance into ___?":
        "In September 1914, French and British forces halted the German army just 30 miles from Paris. The battle wrecked Germany's Schlieffen Plan for a quick victory and condemned both sides to four years of trench warfare.",

    "The Easter Rising in Ireland occurred in ___?":
        "On Easter Monday 1916, about 1,500 Irish republicans seized key buildings in Dublin and proclaimed an Irish Republic. The British crushed the rebellion in six days, but their execution of 16 leaders turned public opinion sharply against British rule.",

    "The Irish Free State was established in ___?":
        "The Anglo-Irish Treaty of 1921 created the Irish Free State as a British dominion in 1922. Six northern counties remained part of the UK. The partition triggered a brief but bitter Irish Civil War between pro- and anti-treaty factions.",

    "The Berlin Conference (1884) was convened by ___?":
        "Chancellor Otto von Bismarck hosted the conference to regulate European colonization of Africa. Fourteen nations attended -- not a single African was present. The conference formalized the 'Scramble for Africa' and divided the continent along arbitrary lines.",

    "The Congress of Vienna was convened to ___?":
        "After Napoleon's defeat, the great powers met to restore order to Europe. Led by Metternich, the congress sought to prevent another French revolution by restoring monarchies and maintaining a balance of power. The resulting 'Concert of Europe' kept relative peace for decades.",

    "The Sepoy Mutiny (Indian Rebellion) was in ___?":
        "In 1857, Indian soldiers (sepoys) in the British East India Company's army rebelled over cultural and religious grievances, including the infamous greased cartridges. The revolt was brutally suppressed, and Britain transferred control of India from the Company to the Crown.",

    "The Italian unification (Risorgimento) was completed in ___?":
        "In 1861, the Kingdom of Italy was proclaimed, unifying a peninsula that had been divided into competing states since the fall of the Roman Empire. Full unification came in 1870 when Italian troops captured Rome from the Pope.",

    "Garibaldi is associated with the unification of ___?":
        "Giuseppe Garibaldi, the 'Hero of Two Worlds,' led his volunteer 'Redshirts' to conquer Sicily and southern Italy in 1860. His military genius and romantic idealism made him one of the most admired figures of the 19th century.",

    "The Crimean War ended with the ___?":
        "The Treaty of Paris (1856) ended Russia's ambitions in the declining Ottoman Empire. The war is remembered for the Charge of the Light Brigade, Florence Nightingale's nursing reforms, and some of history's earliest war photography.",

    "The Commune of Paris was established in ___?":
        "After France's defeat in the Franco-Prussian War, Parisian radicals established a socialist commune in March 1871. It lasted just 72 days before French government troops crushed it in the 'Bloody Week,' killing an estimated 10,000-20,000 communards.",

    "The Meiji Constitution was promulgated in ___?":
        "The 1889 constitution created Asia's first parliamentary system, modeled partly on Prussia's. It balanced imperial authority with an elected legislature, symbolizing Japan's rapid transformation from feudal isolation to modern constitutional governance.",

    "The Korean War armistice was signed in ___?":
        "The armistice was signed at the border village of Panmunjom on July 27, 1953, ending three years of fighting that killed roughly 2.5 million civilians. No peace treaty was ever signed -- technically, the Korean War never ended.",

    "The Potsdam Conference divided Germany into ___?":
        "In July-August 1945, the victorious Allies divided Germany into four occupation zones: American, British, French, and Soviet. Berlin, deep in the Soviet zone, was similarly divided. This arrangement hardened into the permanent division of Germany during the Cold War.",

    "The four Geneva Conventions were adopted in ___?":
        "The 1949 conventions established the modern rules of war, protecting wounded soldiers, prisoners of war, and civilians. They were a direct response to the horrors of WWII and have been ratified by every nation on Earth.",

    "The Strategic Arms Limitation Talks (SALT I) concluded in ___?":
        "Nixon and Brezhnev signed SALT I in Moscow on May 26, 1972, placing the first limits on nuclear arsenals. It froze the number of strategic missile launchers and was a landmark in Cold War diplomacy, proving that rivals could negotiate mutual survival.",

    "The Camp David Accords were brokered by President ___?":
        "Jimmy Carter personally mediated between Sadat and Begin for 13 days at the Camp David retreat. At several points, negotiations nearly collapsed. Carter's persistence produced the first peace treaty between Israel and an Arab nation.",

    "The Falklands War was fought between Britain and ___?":
        "Argentina invaded the Falkland Islands in April 1982, assuming Britain would not fight for distant, sparsely populated islands. Prime Minister Thatcher sent a naval task force 8,000 miles, recaptured the islands in 74 days, and restored British sovereignty.",

    "The Iran-Iraq War lasted from 1980 to ___?":
        "The eight-year war between Saddam Hussein's Iraq and Khomeini's Iran killed roughly one million people and ended in a stalemate. Iraq used chemical weapons, and both sides sent waves of soldiers into trench warfare reminiscent of WWI.",

    "The Gulf War coalition was led by ___?":
        "The United States assembled a coalition of 35 nations and deployed over 500,000 troops to liberate Kuwait. The ground war lasted just 100 hours, making it one of the most decisive military victories in modern history.",

    "The Oslo Accords were signed between Israel and ___?":
        "The 1993 accords saw Israel and the PLO mutually recognize each other for the first time. Yitzhak Rabin and Yasser Arafat shook hands on the White House lawn in one of the most iconic images of the 1990s. Rabin was assassinated by an Israeli extremist two years later.",

    "The Maastricht Treaty founded ___?":
        "Signed in 1992, the Maastricht Treaty created the European Union, transforming the European Economic Community into a political union with common citizenship, foreign policy, and eventually a shared currency -- the euro.",

    "The Maastricht Treaty was signed in ___?":
        "The treaty was signed on February 7, 1992, in the Dutch city of Maastricht. It represented the most ambitious step toward European integration since the Treaty of Rome in 1957, creating the three-pillar structure of the European Union.",

    "Nelson Mandela was imprisoned on ___?":
        "Mandela spent 18 of his 27 years in prison on Robben Island, a bleak outpost off Cape Town. He was confined to a tiny cell and forced to do hard labor. Rather than break him, imprisonment made him an international symbol of resistance.",

    "The apartheid system in South Africa was formally abolished in ___?":
        "President F.W. de Klerk began dismantling apartheid laws in 1990-1991, including the Population Registration Act that classified South Africans by race. The first multiracial elections followed in 1994, bringing Mandela to power.",

    "The Bosnian War ended with the ___?":
        "The Dayton Accords, signed in November 1995, ended three years of brutal ethnic conflict that killed over 100,000 people. The agreement was reached at Wright-Patterson Air Force Base in Ohio, after NATO airstrikes forced the warring parties to negotiate.",

    "The Battle of Tsushima was a naval battle in which ___?":
        "Japan's Admiral Togo destroyed Russia's Baltic Fleet on May 27-28, 1905, after it had sailed 18,000 miles from Europe. Japan sank 21 Russian ships while losing only 3 torpedo boats -- the most decisive naval battle since Trafalgar.",

    "The Entente Cordiale (1904) allied Britain with ___?":
        "The agreement resolved colonial disputes between Britain and France, particularly over Egypt and Morocco. More importantly, it ended centuries of Anglo-French rivalry and laid the groundwork for their alliance in both World Wars.",

    "The Triple Entente before WWI was Russia, France, and ___?":
        "Britain's alliance with France (1904) and Russia (1907) created the Triple Entente that would face the Triple Alliance of Germany, Austria-Hungary, and Italy. This rigid alliance system meant that any conflict between two nations could drag in all six.",

    "The Taiping Rebellion lasted from 1850 to ___?":
        "The Taiping Rebellion was the deadliest civil war in history, killing an estimated 20-30 million people. Led by Hong Xiuquan, who claimed to be Jesus's brother, the rebels controlled much of southern China for 14 years before the Qing Dynasty crushed them.",

    "The Sepoy Mutiny (Indian Rebellion) was suppressed by ___?":
        "The British East India Company, reinforced by Crown troops and loyal Indian soldiers, brutally suppressed the rebellion. The aftermath saw the dissolution of the Company and direct British Crown rule over India -- the beginning of the British Raj.",

    "The First Boer War was in ___?":
        "The Boers (Dutch-descended settlers) defeated the British at Majuba Hill in 1881, winning self-governance for the Transvaal. Britain's humiliation set the stage for the larger, far bloodier Second Boer War two decades later.",

    "The Second Boer War ended in ___?":
        "Britain eventually won in 1902 but at enormous cost: over 22,000 British soldiers died, many from disease. The British also created concentration camps for Boer civilians -- the first modern use of the term -- where 28,000 died from neglect and disease.",

    "The Zulu Kingdom was defeated by Britain at the Battle of ___?":
        "The decisive Battle of Ulundi on July 4, 1879, ended the Anglo-Zulu War. Earlier, at Isandlwana, the Zulus had inflicted one of the worst defeats in British colonial history. The Zulus' courage and military skill earned the respect of their enemies.",

    "The Opium Wars resulted in ___?":
        "Britain forced China to open treaty ports and cede Hong Kong after defeating it in the Opium Wars (1839-1842 and 1856-1860). The 'unequal treaties' that followed began China's 'Century of Humiliation' -- a wound in Chinese national consciousness that has not fully healed.",

    "Hong Kong was ceded to Britain after the ___?":
        "The Treaty of Nanking (1842) ended the First Opium War and ceded Hong Kong Island to Britain 'in perpetuity.' Britain had gone to war partly to force China to continue importing opium -- one of the most cynical causes for conflict in modern history.",

    "The Tongzhi Restoration attempted to revive ___?":
        "In the 1860s-1870s, reformers tried to save the Qing Dynasty by adopting Western military technology while preserving Confucian values. The approach -- 'Chinese learning for the foundation, Western learning for practical use' -- proved insufficient to match the West's industrial power.",

    "The Self-Strengthening Movement in China occurred in the ___?":
        "From the 1860s to 1890s, Chinese officials built modern arsenals, shipyards, and railways. But the movement's half-measures -- modernizing technology without reforming institutions -- failed spectacularly when Japan crushed China in the Sino-Japanese War of 1895.",

    "The Boxer Protocol (1901) forced China to pay indemnity to ___?":
        "After the eight-nation alliance crushed the Boxer Rebellion, the protocol imposed a staggering indemnity of 450 million taels of silver -- more than the Qing government's annual revenue. The humiliation accelerated the dynasty's collapse.",

    "Sun Yat-sen founded the ___?":
        "Sun Yat-sen, the 'Father of the Nation,' founded the Kuomintang (Nationalist Party) and promoted his Three Principles of the People: nationalism, democracy, and livelihood. He died in 1925 before seeing China unified, and both the Nationalists and Communists claim his legacy.",

    "The Republic of China was founded in ___?":
        "The Qing Dynasty's last emperor, the six-year-old Puyi, abdicated on February 12, 1912. Sun Yat-sen's republic replaced over 2,000 years of imperial rule, though China would face decades of warlordism, civil war, and Japanese invasion before achieving stability.",

    "The Long March was undertaken by ___?":
        "In 1934-1935, Mao's Communist forces marched roughly 6,000 miles through some of China's harshest terrain to escape Nationalist encirclement. Of the 80,000 who began the march, only about 8,000 survived to reach Yan'an. It became the founding myth of Communist China.",

    "The Long March ended in ___?":
        "The surviving Communists reached Yan'an in northern China, where Mao established his base and rebuilt his forces. From this remote outpost, he would eventually conquer all of mainland China and proclaim the People's Republic in 1949.",

    "The Nanking Treaty (1842) ended the ___?":
        "The Treaty of Nanking was the first of the 'unequal treaties' that Western powers imposed on China. It opened five ports to British trade, ceded Hong Kong, and imposed a massive indemnity -- all because China had tried to stop Britain from selling opium to its people.",

    "The Scramble for Africa began formally at the ___?":
        "The Berlin Conference of 1884-1885 established the rules by which European powers could claim African territory. All they had to do was occupy and administer it -- no concern for the wishes of the millions of Africans already living there.",

    "King Leopold II controlled which African territory personally?":
        "Leopold II of Belgium ran the Congo Free State as his personal fief from 1885 to 1908, exploiting its rubber and ivory through forced labor, mutilation, and murder. An estimated 10 million Congolese died under his rule -- one of history's worst colonial atrocities.",

    "The Mau Mau Uprising (1952-1960) was in ___?":
        "Kikuyu people in Kenya revolted against British colonial rule and the seizure of their ancestral lands. The British suppressed the uprising with mass detention and forced relocations. Kenya gained independence in 1963, and Jomo Kenyatta became its first president.",

    "Kwame Nkrumah led independence in ___?":
        "Nkrumah led the Gold Coast to independence as Ghana in 1957, becoming the first Black African country to free itself from European colonial rule. His pan-African vision inspired independence movements across the continent.",

    "Ghana's independence in 1957 was the first sub-Saharan African country to gain independence from ___?":
        "Ghana's independence from Britain on March 6, 1957, electrified Africa. Within a decade, most of the continent had followed suit. Nkrumah declared, 'We prefer self-government with danger to servitude in tranquility.'",

    "The Year of Africa (mass independence) was ___?":
        "In 1960, seventeen African nations gained independence -- more than in any other year. France granted independence to most of its African colonies, while Belgium hastily withdrew from the Congo. The wave of freedom reshaped the global political landscape.",

    "The ANC (African National Congress) was founded in ___?":
        "Founded in 1912 as the South African Native National Congress, the ANC spent decades fighting for Black South Africans' rights through petitions and protests. Banned in 1960, it turned to armed resistance before eventually winning power through negotiations in 1994.",

    "The Sharpeville Massacre occurred in ___?":
        "On March 21, 1960, South African police opened fire on peaceful protesters in Sharpeville, killing 69 people -- many shot in the back as they fled. The massacre shocked the world and led to the banning of the ANC and PAC.",

    "The Iran Hostage Crisis lasted from 1979 to ___?":
        "Iranian students seized 52 American embassy staff on November 4, 1979, holding them for 444 days. The crisis humiliated the Carter administration, contributed to his election loss, and poisoned US-Iran relations for decades.",

    "The Iran-Iraq War was triggered by Iraq's invasion of ___?":
        "Saddam Hussein invaded Iran in September 1980, expecting a quick victory against a revolution-weakened country. Instead, he got an eight-year war that killed roughly a million people and ended in a stalemate.",

    "Iraq invaded Kuwait in ___?":
        "On August 2, 1990, Saddam Hussein's forces overran tiny, oil-rich Kuwait in just two days. The invasion shocked the world and united an unprecedented international coalition to liberate Kuwait.",

    "The Oslo Accords of 1993 were signed at the ___?":
        "After secret negotiations in Norway, Rabin and Arafat signed the accords on the White House lawn on September 13, 1993. President Clinton presided over the famous handshake between two former enemies. The promised lasting peace, however, has remained elusive.",

    "The first Palestinian intifada began in ___?":
        "The uprising began in December 1987 in Gaza and spread to the West Bank. Young Palestinians threw stones at Israeli soldiers in images that shocked the world. The intifada lasted until the Oslo Accords in 1993 and resulted in over 1,000 Palestinian and 160 Israeli deaths.",

    "The founding of the PLO (Palestine Liberation Organization) was in ___?":
        "The PLO was founded in 1964 in Jerusalem with the goal of liberating Palestine through armed struggle. Under Yasser Arafat's leadership from 1969, it eventually shifted toward diplomacy, culminating in the Oslo Accords.",

    "Yasser Arafat led the ___?":
        "Arafat led the PLO for 35 years, transforming from guerrilla fighter to Nobel Peace Prize laureate. He was the embodiment of the Palestinian national movement -- loved by his people, feared by Israel, and a fixture of international diplomacy.",

    "The Velvet Divorce split ___?":
        "On January 1, 1993, Czechoslovakia peacefully divided into the Czech Republic and Slovakia. It was one of history's most amicable national separations -- no violence, no border disputes, just two peoples who decided they'd rather go their own ways.",

    "Alexis de Tocqueville warned in 'Democracy in America' that democracy faces a danger from ___?":
        "Tocqueville observed in the 1830s that democratic majorities can be just as tyrannical as any king. He warned that social pressure to conform could silence dissent as effectively as censorship. His insights remain startlingly relevant.",

    "The Federalist No. 51 argued that 'ambition must be made to counteract ambition' as a reason for ___?":
        "Madison argued that since men are not angels, government power must be divided so that each branch checks the others. This realistic view of human nature -- that power corrupts and must be restrained -- is the genius of the American constitutional system.",

    "George Kennan's 'Long Telegram' (1946) argued that the Soviet Union was driven by ___?":
        "Kennan, writing from the US Embassy in Moscow, argued that Soviet expansionism was driven by Communist ideology and Russian insecurity, not legitimate security needs. His analysis became the intellectual foundation for the entire containment strategy of the Cold War.",

    "The Hungarian Uprising of 1956 was significant because the West's failure to help showed ___?":
        "Thousands of Hungarians died fighting Soviet tanks while the West watched helplessly. The lesson was brutal: in the nuclear age, the West could not use force to liberate nations behind the Iron Curtain without risking annihilation.",

    "The Enlightenment thinker Jean-Jacques Rousseau's concept of the 'general will' was dangerous because ___?":
        "Rousseau argued that the 'general will' represents what the community truly wants, even if individuals disagree. This opened the door for leaders to claim they were forcing people to be 'truly free' -- a logic used by Robespierre, Lenin, and other tyrants.",

    "Czechoslovakia's Velvet Revolution of 1989 succeeded with little violence because ___?":
        "When hundreds of thousands filled Prague's streets, the communist government realized it had lost all legitimacy. Without Soviet tanks to prop them up -- Gorbachev had abandoned the Brezhnev Doctrine -- the regime simply crumbled. Playwright Vaclav Havel went from prison to president in six weeks.",

    "The Dawes Plan of 1924 restructured German reparations payments in order to ___?":
        "American banker Charles Dawes designed a plan that loaned US money to Germany, which paid reparations to Britain and France, which repaid war debts to the US. This circular flow stabilized the German economy -- until the Great Depression broke the cycle.",

    "The Kellogg-Briand Pact (1928), which outlawed war, failed because ___?":
        "Sixty-two nations signed a pact renouncing war 'as an instrument of national policy.' It had no enforcement mechanism whatsoever. Japan invaded Manchuria three years later, and nobody invoked the pact. It proved that idealistic treaties without teeth are worthless.",

    "The Atlantic Charter (1941) signed by Roosevelt and Churchill committed both nations to ___?":
        "Roosevelt and Churchill met secretly aboard warships off Newfoundland and agreed on war aims before the US had even entered the war. The Charter's principles -- self-determination, free trade, freedom from fear and want -- became the foundation of the post-war order.",

    "Athenian democracy under Cleisthenes introduced what key reform that expanded citizen participation?":
        "Cleisthenes reorganized Athenian society in 508 BC, replacing the old aristocratic tribes with ten new tribes based on geography. This mixed rich and poor, urban and rural citizens together, breaking the power of noble families and creating the world's first democracy.",

    "The Stoic philosophy of ancient Rome argued that natural law applied to ___?":
        "The Stoics taught that all humans share in universal reason (logos) and therefore possess equal dignity regardless of wealth, nationality, or social status. This radical idea -- that a slave and an emperor are moral equals -- would profoundly influence Christianity and modern human rights.",

    "Solon's legal reforms in Athens (594 BC) were significant because they ___?":
        "Solon freed Athenians who had been enslaved for debt and gave common citizens access to the courts. He did not create democracy, but he dismantled the aristocratic monopoly on justice. Cleisthenes would build on his foundation a generation later.",

    "Draco's code of laws in ancient Athens (621 BC) was historically notable because ___?":
        "Draco's code was so harsh that the word 'draconian' entered the language. But its real significance was that for the first time, laws were written down where everyone could see them. Before Draco, justice was whatever the aristocrats said it was.",

    "Thomas Jefferson's ideal of 'ward republics' held that the best government is ___?":
        "Jefferson envisioned dividing counties into small 'wards' where citizens would directly govern their own schools, roads, and local affairs. He believed that the more decisions are made at the local level, the freer and more engaged citizens remain.",

    "The Second Reform Act of 1867 in Britain was significant because it ___?":
        "The act nearly doubled the British electorate by giving the vote to urban working-class men. Prime Minister Disraeli called it a 'leap in the dark.' It was a major step on Britain's long road from oligarchy to democracy.",

    "Emile Zola's 'J'Accuse' letter during the Dreyfus Affair was an act of ___?":
        "Zola's open letter in L'Aurore newspaper, published on January 13, 1898, accused the French military of framing Dreyfus and covering up the truth. Zola was convicted of libel and fled to England, but his courage helped secure Dreyfus's eventual exoneration.",

    "The Helsinki Accords (1975) were strategically significant because they ___?":
        "By signing the accords, the Soviet Union committed to respecting human rights on paper. Dissident groups like Charter 77 in Czechoslovakia and Helsinki Watch committees across Eastern Europe used these commitments to challenge communist repression with the regimes' own words.",

    "The Iran-Iraq War (1980-1988) began when Iraq invaded Iran under Saddam Hussein because ___?":
        "Saddam saw revolutionary Iran as both a threat and an opportunity. Iran's military had been purged after the revolution, and Saddam hoped to seize the oil-rich Khuzestan province. Instead, he got an eight-year quagmire.",

    "The Enclosure Movement in England (16th-19th centuries) contributed to the Industrial Revolution by ___?":
        "When common lands were enclosed and turned into private farms, millions of rural workers lost their traditional livelihoods. They migrated to cities in search of work, providing the labor force that powered the new factories of the Industrial Revolution.",

    "Frederick the Great of Prussia was notable for ___?":
        "Frederick II (r. 1740-1786) embodied the 'enlightened despot' ideal. He played the flute, corresponded with Voltaire, abolished torture, and declared, 'In my state, every man can be saved after his own fashion.' He also built Prussia into a European military powerhouse.",

    "Slavery in the American South was defended by John C. Calhoun on the grounds that ___?":
        "Calhoun argued that slavery was a 'positive good' for both races and that states had the right to nullify federal laws they considered unconstitutional. His defense of states' rights as a shield for slavery became the philosophical foundation of secession.",

    "The British Parliament's Corn Laws, repealed in 1846, were opposed by free traders because they ___?":
        "The Corn Laws imposed tariffs on imported grain, keeping bread prices high to benefit wealthy landowners. Workers and industrialists alike demanded repeal. Richard Cobden and the Anti-Corn Law League triumphed, marking a victory for free trade that defined British economic policy for decades.",

    "Richard Cobden and the Anti-Corn Law League argued that free trade would ___?":
        "Cobden believed free trade would not only lower food prices but promote international peace -- nations that trade with each other have less reason to fight. The repeal of the Corn Laws in 1846 made Britain the world's leading champion of free trade.",

    "The principle of comparative advantage in economics, developed by David Ricardo, argues that ___?":
        "Ricardo showed that even if one country is better at producing everything, both countries benefit from specializing in what they do relatively best and trading. This counterintuitive insight remains one of the most powerful ideas in economics.",

    # ── Tier 5 ──────────────────────────────────────────────────────────────

    "The Congress of Vienna met in ___?":
        "The Congress of Vienna (1814-1815) redrew the map of Europe after Napoleon's defeat. The diplomats danced and feasted while deciding the fates of millions. The balance of power they created kept Europe relatively peaceful for a century.",

    "The Congress of Vienna was presided over by ___?":
        "Austrian Chancellor Klemens von Metternich masterfully orchestrated the Congress, balancing the interests of five great powers while preventing France from ever again dominating Europe. His conservative vision shaped European politics until the revolutions of 1848.",

    "The Peace of Augsburg established the principle ___?":
        "'Cuius regio, eius religio' -- 'whose realm, his religion' -- was a pragmatic solution to religious war that let each German prince choose Catholicism or Lutheranism for his territory. It bought 63 years of uneasy peace before the Thirty Years' War erupted.",

    "Who was the last Byzantine Emperor?":
        "Constantine XI Palaiologos died fighting on the walls of Constantinople on May 29, 1453, as Ottoman forces breached the city. His body was never identified. With his death, the last remnant of the Roman Empire -- which had endured for over 1,500 years -- finally fell.",

    "The Sykes-Picot Agreement was signed in ___?":
        "In 1916, Sir Mark Sykes and Francois Georges-Picot secretly carved up the Ottoman Empire's Arab territories. When the Bolsheviks published the agreement after the Russian Revolution, it confirmed Arab suspicions of Western betrayal and poisoned relations for decades.",

    "The Balfour Declaration was issued in ___?":
        "Arthur Balfour's 67-word letter of November 2, 1917, promised British support for a Jewish homeland in Palestine while vaguely protecting existing non-Jewish communities. This ambiguous document planted the seeds of a conflict that rages over a century later.",

    "The Battle of Thermopylae was in ___?":
        "In 480 BC, King Leonidas and his 300 Spartans held the narrow pass of Thermopylae for three days against Xerxes' Persian army. Their sacrifice bought time for Greece to organize its defense and ultimately defeat the Persian invasion at Salamis and Plataea.",

    "The Marshall Plan distributed approximately ___?":
        "The US invested roughly $13 billion (about $170 billion in today's dollars) to rebuild Western Europe between 1948 and 1952. The aid was offered to the Soviet bloc too, but Stalin refused it. The plan's success in restoring prosperity helped keep Western Europe democratic.",

    "The Fourth Lateran Council (1215) was convened by Pope ___?":
        "Pope Innocent III, perhaps the most powerful pope in history, summoned over 1,200 bishops to Rome. The council defined the doctrine of transubstantiation, required annual confession, and launched the Fifth Crusade. It was the medieval papacy at its zenith.",

    "The Edict of Milan (313 AD) was issued by Emperor ___?":
        "Constantine issued the edict after reportedly seeing a Christian symbol in the sky before battle and being told 'In this sign, you shall conquer.' Whether his conversion was genuine or political, the edict ended three centuries of Christian persecution and changed history.",

    "The Delian League was led by ___?":
        "Athens formed the Delian League after the Persian Wars, ostensibly to defend Greece from future attacks. Over time, Athens transformed the league into an empire, using its allies' tribute to build the Parthenon and fund Athenian democracy.",

    "The Spartan constitution was attributed to ___?":
        "Lycurgus, whether a real historical figure or a legend, was credited with creating Sparta's famously austere system. Spartan boys entered military training at age 7, and the entire society was organized around producing the finest warriors in Greece.",

    "The Peace of Nicias (421 BC) temporarily ended which war?":
        "The peace was supposed to last 50 years but collapsed within 7. Athens and Sparta were too fundamentally different -- one a democracy and naval power, the other an oligarchy and land power -- to coexist peacefully for long.",

    "The Treaty of Verdun (843 AD) divided ___?":
        "Charlemagne's grandsons divided his empire into three kingdoms: West Francia (future France), East Francia (future Germany), and a Middle Kingdom (future Low Countries and Italy). This partition laid the foundation for the modern nations of Europe.",

    "The Black Death entered Europe primarily through ___?":
        "Genoese trading ships from Caffa in Crimea brought the plague to Sicilian ports in October 1347. From Sicily, it spread along trade routes to every corner of Europe within five years, killing roughly one-third of the continent's population.",

    "The Plague of Justinian (541-549 AD) killed approximately ___?":
        "This earlier bubonic plague pandemic struck the Byzantine Empire at its height, killing an estimated 25-50 million people -- up to half the world's population. It weakened the empire so severely that Justinian's dream of restoring Roman glory died with its victims.",

    "The Magna Carta clause 39 guaranteed ___?":
        "Clause 39 stated: 'No free man shall be seized, imprisoned, or stripped of his rights except by the lawful judgment of his equals or by the law of the land.' This principle -- the right not to be imprisoned without trial -- became habeas corpus.",

    "The Model Parliament of 1295 was convened by ___?":
        "Edward I summoned representatives from every county, city, and borough in England -- not out of democratic idealism, but because he needed money for wars. Nevertheless, the Model Parliament established the precedent that taxation required representation.",

    "The Pragmatic Sanction of 1713 concerned succession to the ___?":
        "Emperor Charles VI spent decades persuading European powers to accept that his daughter Maria Theresa could inherit the Habsburg throne. When he died in 1740, most of them reneged on their promises, plunging Europe into the War of the Austrian Succession.",

    "The War of the Austrian Succession ended with the ___?":
        "The Treaty of Aix-la-Chapelle (1748) essentially restored the pre-war status quo, but Maria Theresa kept her throne. The real winner was Prussia's Frederick the Great, who had seized Silesia and established Prussia as a major European power.",

    "NSC-68 (1950) argued the US should massively expand defense spending to ___?":
        "This classified policy document urged tripling the defense budget to counter the Soviet threat. It argued that mere diplomacy was insufficient -- only overwhelming military strength could deter Soviet expansion. NSC-68 defined American strategy for the entire Cold War.",

    "The Holy Alliance (1815) was proposed by ___?":
        "Tsar Alexander I proposed that European monarchs govern according to Christian principles of charity and peace. Metternich dismissed it as 'a loud-sounding nothing,' and Castlereagh called it 'a piece of sublime mysticism and nonsense.' It had no practical effect.",

    "The Brest-Litovsk Treaty was between Germany and ___?":
        "In March 1918, Lenin's Bolshevik government signed a humiliating peace with Germany, surrendering vast territories including Ukraine, Poland, and the Baltic states. Lenin accepted the losses to consolidate power at home, betting -- correctly -- that Germany would eventually lose the war.",

    "The Stresa Front (1935) allied Britain, France, and ___?":
        "The three nations agreed to oppose German violations of the Treaty of Versailles. The front collapsed within months when Britain signed a separate naval agreement with Germany and Italy invaded Ethiopia. The failure showed that collective security without commitment is useless.",

    "The Munich Agreement (1938) conceded the Sudetenland to ___?":
        "Chamberlain and Daladier handed Hitler the Sudetenland without consulting Czechoslovakia. Churchill called it 'a total and unmitigated defeat.' Within six months, Hitler swallowed the rest of Czechoslovakia, proving that appeasement only feeds aggression.",

    "The Molotov-Ribbentrop Pact secretly divided ___?":
        "A secret protocol to the 1939 pact drew a line across Eastern Europe, giving the Baltic states and eastern Poland to the Soviet Union and western Poland to Germany. When the Soviets released the protocol decades later, it confirmed what historians had long suspected.",

    "The Atlantic Charter was signed by Roosevelt and ___?":
        "Churchill and Roosevelt met aboard warships in Placentia Bay, Newfoundland, in August 1941. The Charter outlined their vision for the post-war world -- self-determination, free trade, and collective security. Remarkably, the US was still officially neutral at the time.",

    "The Atlantic Charter was signed in ___?":
        "The Charter was announced on August 14, 1941 -- nearly four months before Pearl Harbor brought the US into the war. Roosevelt committed to war aims before he had officially committed to war, sending a clear signal about where America's sympathies lay.",

    "The Platt Amendment gave the US control over ___?":
        "The 1901 amendment, forced into Cuba's constitution, gave the US the right to intervene in Cuban affairs and maintain a naval base at Guantanamo Bay. It effectively made Cuba a US protectorate -- a relationship that bred resentment for decades.",

    "The United Nations Charter was signed in ___?":
        "Delegates from 50 nations signed the Charter in San Francisco on June 26, 1945. The ceremony took place in the War Memorial Opera House. President Truman told the delegates, 'You have created a great instrument for peace.'",

    "The Prague Spring was crushed by Soviet forces in ___?":
        "On August 20-21, 1968, 200,000 Warsaw Pact troops and 2,000 tanks invaded Czechoslovakia to crush Dubcek's reforms. The message was clear: the Soviet Union would not tolerate dissent within its sphere. The 'Brezhnev Doctrine' justified intervention to 'protect socialism.'",

    "The Solidarity trade union movement emerged in ___?":
        "Solidarity, founded in Poland's Gdansk shipyard in 1980, became the first independent labor union in the Soviet bloc. At its peak, it had 10 million members. Though crushed by martial law in 1981, it survived underground and led Poland to freedom in 1989.",

    "Lech Walesa led the Solidarity movement in ___?":
        "An electrician from Gdansk, Walesa climbed a fence to join a shipyard strike in 1980 and emerged as the leader of a movement that shook the Soviet empire. He won the Nobel Peace Prize in 1983 and became Poland's first democratically elected president in 1990.",

    "The velvet revolution overthrew communism in ___?":
        "Czechoslovakia's 1989 revolution was so peaceful that it earned the name 'Velvet.' Hundreds of thousands filled Prague's Wenceslas Square, jingling their keys as a signal that it was time for the communists to go home. The regime fell in eleven days.",

    "The velvet revolution was led by ___?":
        "Vaclav Havel, a playwright who had been repeatedly imprisoned for dissident activities, led Czechoslovakia's transition to democracy. He went from prison to the presidency in just six weeks -- proof that the pen can indeed be mightier than the tank.",

    "The Maastricht Treaty was formally the Treaty on ___?":
        "Formally titled the Treaty on European Union, it transformed the European Economic Community into a far more ambitious political project. It established European citizenship, a common foreign policy, and laid the groundwork for the single European currency.",

    "German reunification occurred in ___?":
        "East and West Germany were formally reunited on October 3, 1990 -- less than a year after the Berlin Wall fell. The process was remarkably swift: the East German state simply ceased to exist and its territory was absorbed into the Federal Republic.",

    "The International Criminal Court was established in ___?":
        "The ICC began operating in 2002, fulfilling the promise of Nuremberg: that individuals who commit genocide, war crimes, and crimes against humanity will face justice. It is based in The Hague, Netherlands.",

    "The Srebrenica massacre occurred in ___?":
        "In July 1995, Bosnian Serb forces killed over 8,000 Bosnian Muslim men and boys in Srebrenica -- a UN-designated 'safe area' that Dutch peacekeepers failed to protect. It was the worst massacre on European soil since World War II.",

    "The Khmer Rouge regime in Cambodia lasted from 1975 to ___?":
        "Pol Pot's regime emptied cities, abolished money, and killed roughly 2 million people in just four years. The 'Killing Fields' targeted anyone associated with education, foreign influence, or the previous government. Vietnamese forces finally overthrew the regime in 1979.",

    "The Partition of India occurred in ___?":
        "When Britain withdrew in August 1947, the subcontinent was split along religious lines. The partition triggered the largest mass migration in history -- 15 million people moved across new borders -- and communal violence killed an estimated 1-2 million people.",

    "The NSC-68 document (1950) outlined ___?":
        "This classified document argued that the Soviet Union posed an existential threat requiring massive US military buildup. Written by Paul Nitze, it recommended tripling defense spending and became the blueprint for American Cold War strategy after the Korean War began.",

    "The Domino Theory held that if one country fell to communism ___?":
        "The theory compared nations to dominoes -- if one fell to communism, its neighbors would follow in a chain reaction. This logic drove US intervention in Korea and Vietnam. After Vietnam fell in 1975, the predicted regional domino effect did not fully materialize.",

    "The Long Telegram (1946) warning about Soviet expansionism was written by ___?":
        "George Kennan's 8,000-word telegram from Moscow in February 1946 argued that the Soviet Union was inherently expansionist and could only be contained through firm, patient resistance. His analysis shaped American foreign policy for the next 45 years.",

    "The Nuclear Test Ban Treaty (1963) prohibited tests in ___?":
        "The treaty banned nuclear tests in the atmosphere, underwater, and in outer space -- but not underground. It was the first arms control agreement of the nuclear age, signed by the US, UK, and USSR in the aftermath of the terrifying Cuban Missile Crisis.",

    "Nixon's 'opening to China' visit was in ___?":
        "Nixon's visit to China in February 1972 stunned the world. By reaching out to Mao, Nixon exploited the Sino-Soviet split, gained leverage against the Soviet Union, and transformed the geopolitics of the Cold War.",

    "The SALT II treaty was signed but never ratified because of the Soviet invasion of ___?":
        "Carter and Brezhnev signed SALT II in Vienna in June 1979, but the Soviet invasion of Afghanistan in December killed any chance of Senate ratification. The invasion ended detente and plunged US-Soviet relations to their lowest point since the Cuban Missile Crisis.",

    "The Battle of Adwa (1896) was a victory for ___?":
        "Emperor Menelik II's Ethiopian forces crushed the Italian army at Adwa on March 1, 1896, killing or capturing roughly 11,000 Italian soldiers. It was the most decisive African victory over a European colonial power and preserved Ethiopian independence.",

    "The Fashoda Crisis was resolved in favor of ___?":
        "France withdrew from Fashoda in November 1898, conceding the Upper Nile to Britain. The humiliation stung French national pride but cleared the way for the Entente Cordiale -- the Anglo-French alliance that would prove crucial in both World Wars.",

    "The Algeciras Conference (1906) defused the First ___?":
        "Germany had provoked the Moroccan Crisis by challenging French influence in Morocco. At Algeciras, only Austria-Hungary supported Germany, while France had broad backing. The conference revealed Germany's diplomatic isolation and strengthened the Anglo-French Entente.",

    "The First Moroccan Crisis (1905) was provoked by ___?":
        "Kaiser Wilhelm II landed at Tangier and declared his support for Moroccan independence, directly challenging France's growing influence. The gambit backfired: instead of splitting France and Britain, it pushed them closer together.",

    "The Bosnian Crisis (1908) was caused by Austria-Hungary annexing ___?":
        "Austria-Hungary's annexation of Bosnia and Herzegovina enraged Serbia, which saw the provinces as part of its future. Russia backed Serbia but was too weak after the 1905 war to act. The crisis planted seeds of resentment that bloomed into World War I six years later.",

    "The Sarajevo assassinations of 1914 killed Archduke Franz Ferdinand and ___?":
        "Princip's bullets killed both Franz Ferdinand and his wife Sophie on their wedding anniversary. The Archduke's last words to his dying wife were reportedly 'Sophie, Sophie! Don't die! Live for our children!' Their deaths triggered a world war.",

    "The Schlieffen Plan called for Germany to first defeat ___?":
        "The plan called for a massive right-hook through Belgium to encircle and crush France in six weeks before Russia could fully mobilize. It nearly worked -- German forces reached within 30 miles of Paris before being stopped at the Battle of the Marne.",

    "The Gallipoli Campaign (1915-1916) was an Allied attempt to seize ___?":
        "Winston Churchill championed the ill-fated plan to force the Dardanelles strait and knock the Ottoman Empire out of the war. The campaign cost over 250,000 Allied casualties and was a humiliating failure. It nearly ended Churchill's political career.",

    "The Balfour Declaration was issued by which British official?":
        "Foreign Secretary Arthur James Balfour sent his famous letter to Lord Rothschild on November 2, 1917. In just 67 words, he committed Britain to supporting a Jewish homeland in Palestine -- a promise made to one people about land largely inhabited by another.",

    "The League of Nations Covenant was part of the ___?":
        "President Wilson insisted on embedding the League of Nations Covenant in the Treaty of Versailles, making acceptance of one dependent on the other. Ironically, the US Senate rejected both -- the League's chief architect never joined his own creation.",

    "The Permanent Court of International Justice was established in ___?":
        "Created by the League of Nations in 1920, the court in The Hague was the world's first permanent international judicial body. It issued advisory opinions and rulings on disputes between states. After WWII, it was succeeded by the International Court of Justice.",

    "The Dawes Plan (1924) restructured German ___?":
        "The plan set realistic reparations payments and arranged American loans to stabilize the German economy. Its success brought a brief period of prosperity to Weimar Germany -- the 'Golden Twenties' -- before the Great Depression swept it all away.",

    "The Locarno Treaties (1925) guaranteed the western borders of ___?":
        "Germany voluntarily accepted its western borders with France and Belgium, earning readmission to the European community and a seat on the League of Nations Council. The 'Spirit of Locarno' raised hopes for lasting peace -- hopes that proved cruelly premature.",

    "The Kellogg-Briand Pact (1928) renounced ___?":
        "Sixty-two nations solemnly promised to resolve their disputes peacefully. The pact won its architects the Nobel Peace Prize but lacked any enforcement mechanism. Within a decade, the signatories were fighting the deadliest war in human history.",

    "The Decolonization of French Indochina after 1954 led to the independence of ___?":
        "The Geneva Accords of 1954 divided Vietnam at the 17th parallel and recognized the independence of Laos and Cambodia. France's colonial era in Southeast Asia was over, but American involvement was just beginning.",

    "The Battle of Dien Bien Phu (1954) was France's defeat by ___?":
        "Ho Chi Minh's Viet Minh forces besieged and overran the French garrison at Dien Bien Phu in 55 days. General Giap's brilliant strategy -- hauling artillery up mountains that the French thought impassable -- ended French rule in Vietnam.",

    "The Geneva Accords (1954) temporarily divided Vietnam at the ___?":
        "The accords divided Vietnam along the 17th parallel, with Ho Chi Minh's communist government in the North and a US-backed government in the South. Reunification elections, promised for 1956, were never held -- the US and South Vietnam feared Ho Chi Minh would win.",

    "The Northwest Ordinance of 1787 banned slavery in territories north of the Ohio River, establishing ___?":
        "By banning slavery in the Northwest Territory, Congress established the principle that new territories did not automatically inherit slavery. This precedent -- that Congress had the power to restrict slavery's expansion -- became the central constitutional question leading to the Civil War.",

    "Property rights are considered foundational to liberty because ___?":
        "John Locke argued that without secure property, individuals have no means of supporting themselves independently of the state. Property gives people the economic independence needed to exercise their political freedom. A person who depends entirely on government for livelihood is not truly free.",

    "The Magna Carta's importance to future generations was that it ___?":
        "Though originally a feudal document protecting barons' privileges, the Magna Carta's principle -- that rulers are bound by law -- became universal. It inspired the Petition of Right, the English Bill of Rights, and ultimately the US Constitution. Its legacy far exceeded its authors' intentions.",

    "The principle of 'separation of church and state' in the First Amendment means that ___?":
        "The Establishment Clause prevents government from creating an official religion or favoring one faith over another. The Free Exercise Clause protects individuals' right to practice their religion. Together, they keep religion free from government control and government free from religious domination.",

    "Ronald Reagan's economic policies ('Reaganomics') were based on the theory that ___?":
        "Supply-side economics held that high taxes discourage investment and growth. By cutting marginal tax rates from 70% to 28%, Reagan aimed to unleash entrepreneurship and economic expansion. The US economy did grow significantly, though critics debate how much credit belongs to the tax cuts.",
}

# ── PHILOSOPHY CONTEXTS ──────────────────────────────────────────────────────

PHILOSOPHY_CONTEXTS = {
    # ── Tier 1 ──────────────────────────────────────────────────────────────

    "Socrates said 'The unexamined life is not worth living.' What philosophical practice does this statement defend?":
        "Socrates made this declaration at his trial, choosing death over a life without questioning. For Socrates, philosophy was not an academic exercise but a way of life -- the daily practice of questioning your own beliefs, assumptions, and values.",

    "Plato's Republic argues that only philosopher-kings should rule. What philosophical justification does Plato give for this?":
        "Plato argued that just as you want an expert pilot to fly a ship, you need an expert in justice to run a state. Only those who have grasped the Form of the Good -- the ultimate reality behind appearances -- can make truly just decisions.",

    "Confucianism emphasizes 'ren' as the highest virtue. What does 'ren' mean?":
        "Ren is often translated as 'benevolence' or 'humaneness,' but it literally contains the Chinese characters for 'person' and 'two' -- it is the virtue that arises between people. Confucius taught that ren is expressed through treating others with empathy and respect.",

    "Plato argued the soul survives death because it knows eternal truths before birth. What is the name of this doctrine?":
        "In the Meno, Socrates demonstrates anamnesis by showing that an uneducated slave boy can derive geometric truths through questioning alone. Plato argued this proved the soul already knew these truths before birth and was simply 'remembering' them.",

    "The Socratic method proceeds by asking probing questions that expose contradictions in a person's beliefs. What is the name for the part of this process that reveals false beliefs?":
        "Elenchus literally means 'cross-examination' or 'refutation.' Socrates would ask seemingly innocent questions until his conversation partner discovered their own beliefs were contradictory. The experience was humbling but liberating -- you cannot seek truth until you realize you do not have it.",

    "Aristotle argued that happiness (eudaimonia) requires living in accordance with virtue. What distinguishes his view from simple pleasure-seeking?":
        "For Aristotle, eudaimonia is not a feeling but an activity -- the lifelong practice of living well and doing well. A couch potato experiencing pleasure is not achieving eudaimonia. Only a person actively exercising virtues like courage, justice, and wisdom can truly flourish.",

    "Socrates was condemned for impiety and corrupting youth. What does his willingness to accept the death penalty rather than flee reveal about his philosophy?":
        "In the Crito, Socrates argued that he had benefited from Athens' laws his entire life. To flee would be to undermine the rule of law itself. He chose death over hypocrisy -- proving that his commitment to principle was not just talk.",

    "What did Aristotle call the highest human good?":
        "Eudaimonia -- often translated as 'happiness' or 'flourishing' -- is not a momentary emotion but the result of a lifetime of virtuous activity. Aristotle argued it is the one thing we pursue for its own sake; everything else -- wealth, honor, pleasure -- we pursue because we think it will make us happy.",

    "Heraclitus said 'You cannot step in the same river twice.' What philosophical claim about reality does this illustrate?":
        "Heraclitus observed that the water in a river is always changing, so the river you step into the second time is literally different. His deeper point: all of reality is in constant flux. Change is not an interruption of reality -- it IS reality.",

    "Thales proposed that everything is made of water. Why is this historically significant as a philosophical move?":
        "Thales (c. 624-546 BC) was the first thinker in the Western tradition to seek a natural explanation for the world rather than a mythological one. His answer was wrong, but his method -- looking for natural principles rather than divine stories -- launched philosophy and science.",

    "Which philosopher created the concept of the 'Forms' or 'Ideas'?":
        "Plato argued that behind every imperfect circle, table, or act of justice in our world lies a perfect, eternal Form. Physical objects are just shadows of these Forms -- an idea he dramatized brilliantly in the Allegory of the Cave.",

    "Protagoras said 'Man is the measure of all things.' What philosophical position does this express?":
        "Protagoras was the most famous of the Sophists -- traveling teachers who charged fees for instruction. His claim that truth is relative to the individual was revolutionary and controversial. Plato devoted an entire dialogue (Theaetetus) to arguing against him.",

    "Marcus Aurelius wrote 'Meditations' as a private journal of Stoic practice. What is the core Stoic teaching illustrated by his distinguishing what is 'up to us' from what is not?":
        "The Roman Emperor, ruling during plagues and wars, reminded himself nightly that he could not control events -- only his response to them. His journal, never meant for publication, became one of the most beloved works of practical philosophy ever written.",

    "What does 'ethics' study?":
        "Ethics -- from the Greek 'ethos' (character) -- is the branch of philosophy that investigates how we ought to live. It asks questions like: What makes an action right or wrong? What does a good life look like? What do we owe each other?",

    "What branch of philosophy deals with the study of knowledge?":
        "Epistemology -- from the Greek 'episteme' (knowledge) and 'logos' (study) -- asks fundamental questions: What can we know? How do we know it? What is the difference between knowledge and mere belief? These questions are harder than they sound.",

    "Berkeley argued 'To be is to be perceived.' What philosophical position does this defend?":
        "Bishop Berkeley's idealism was radical: he argued that material objects exist only as perceptions in a mind. When you leave a room, the furniture exists only because God perceives it. Samuel Johnson famously 'refuted' Berkeley by kicking a stone and saying 'I refute it thus!'",

    "What is the branch of philosophy that deals with beauty and art?":
        "Aesthetics asks questions like: What makes something beautiful? Is beauty objective or subjective? Is art valuable for its own sake, or only as a means to something else? The word comes from the Greek 'aisthesis,' meaning perception or sensation.",

    "Which philosopher said 'To be is to be perceived'?":
        "George Berkeley (1685-1753), an Irish bishop, argued that material objects are nothing but collections of ideas in the mind. He was not crazy -- he was making a profound point about the limits of what we can know about the world outside our perceptions.",

    "Democritus proposed that reality consists entirely of atoms moving in a void. Which philosophical problem does this atomic theory attempt to solve?":
        "Democritus faced a puzzle: how can the world contain so many different things, all constantly changing? His answer was elegant -- everything is made of tiny, indivisible particles (atomos) in endless combinations. He was remarkably close to modern atomic theory, 2,400 years early.",

    "Who is the founder of Stoicism?":
        "Zeno of Citium (c. 334-262 BC) founded Stoicism by teaching on the 'Stoa Poikile' (Painted Porch) in Athens. His philosophy -- that virtue and reason lead to inner peace regardless of circumstances -- would influence figures from Emperor Marcus Aurelius to modern cognitive therapy.",

    "Which philosopher founded Epicureanism?":
        "Epicurus (341-270 BC) taught in his Garden in Athens that the goal of life is pleasure -- but he meant tranquility and freedom from pain, not wild indulgence. His ideal was a simple life among friends. 'Do not spoil what you have by desiring what you have not.'",

    "Who was Confucius's most influential follower who extended his teachings?":
        "Mencius (372-289 BC) argued that human nature is fundamentally good -- like water naturally flows downhill, humans naturally tend toward virtue. This optimistic view of human nature shaped Confucianism for centuries and contrasted sharply with Xunzi's view that humans are naturally selfish.",

    "Hobbes argued the natural condition of mankind is war of 'every man against every man.' What does he conclude governments must do to prevent this?":
        "Hobbes, writing during the English Civil War, argued that without an absolute sovereign, life would be 'solitary, poor, nasty, brutish, and short.' Only an unchallengeable authority -- his 'Leviathan' -- could impose order on naturally self-interested humans.",

    "Which philosopher wrote 'On the Nature of Things', describing a world of atoms?":
        "Lucretius (c. 99-55 BC) wrote his epic poem to spread Epicurean philosophy. He described a universe of atoms and void with no divine intervention, argued that death is nothing to fear, and that the soul dies with the body. The poem was lost for centuries before being rediscovered in 1417.",

    "What is the central concern of philosophical theology?":
        "Philosophical theology uses reason rather than revelation to explore questions about God. Does God exist? If so, what is God like? How can an all-good, all-powerful God allow suffering? These questions have driven some of history's greatest philosophical debates.",

    "Nietzsche declared 'God is dead' in The Gay Science. What did he mean by this philosophical claim?":
        "Nietzsche was not celebrating atheism -- he was issuing a warning. If the Christian framework that had given Western civilization its moral compass was no longer believed, what would replace it? He feared the answer might be nihilism, and proposed the Ubermensch as an alternative.",

    "Which philosopher said 'In the beginning was the Word'?":
        "The Gospel of John opens with this philosophical statement, identifying Christ with the Logos -- the rational principle that orders the universe. John was writing in Greek philosophical language, connecting Jewish theology with Greek philosophy in a way that shaped Western thought.",

    "What is 'Plato's cave' an allegory for?":
        "Imagine prisoners chained in a cave, seeing only shadows on the wall and believing them to be reality. One prisoner escapes and sees the sun -- true reality. When he returns to tell the others, they think he is mad. Plato's point: most people mistake appearances for truth.",

    "What is 'metaphysics'?":
        "The word 'metaphysics' literally means 'after physics' -- it was the title Aristotle's editors gave to the works that came after his physics lectures. It asks the deepest questions: What is real? Why does anything exist? What is the relationship between mind and matter?",

    "What word means the opposite of 'true'?":
        "In philosophy, 'false' is not just the opposite of true -- it is one side of a fundamental distinction. Philosophers have debated for millennia what makes a statement true or false, and whether truth is objective or depends on perspective.",

    "If all dogs are animals, and Rex is a dog, what is Rex?":
        "This is a classic example of a syllogism -- the basic form of logical reasoning identified by Aristotle. If both premises are true and the form is valid, the conclusion must be true. Logic is the philosopher's most basic tool.",

    "What do we call a statement that cannot be both true and false at the same time?":
        "The law of non-contradiction -- that something cannot be both true and false at the same time and in the same respect -- is one of the most fundamental principles of logic. Aristotle called it 'the most certain of all principles.'",

    "Which word means 'to think carefully about something'?":
        "Reflection is the heart of philosophy. Socrates insisted that the unexamined life is not worth living. To reflect is to step back from your immediate experience and think about what it means -- a uniquely human capability.",

    "What is the study of right and wrong called?":
        "Ethics has been a central concern of philosophy since Socrates asked 'How should one live?' in the streets of Athens 2,400 years ago. Every day, we make ethical choices -- philosophy helps us think about whether we are making good ones.",

    "If A is bigger than B and B is bigger than C, which is smallest?":
        "This is an example of transitive reasoning -- if A > B and B > C, then A > C and C is smallest. This logical principle seems obvious, but recognizing and applying it correctly is the foundation of clear thinking.",

    "What do we call a question that has no single correct answer?":
        "Open questions drive philosophy forward. 'What is justice?' and 'What makes a good life?' have no final answers, but the process of wrestling with them makes us wiser. As Rilke advised, 'Live the questions now.'",

    "Which word best means 'using your mind to figure something out'?":
        "Reasoning -- the ability to think logically and draw conclusions from evidence -- is what separates philosophy from mere opinion. It is the tool that allows us to evaluate arguments, detect errors, and pursue truth.",

    "What is an 'opinion'?":
        "In philosophy, the distinction between opinion (doxa) and knowledge (episteme) goes back to Plato. An opinion may be true, but it becomes knowledge only when it is justified -- when you can explain why it is true.",

    "If you always tell the truth, you are said to be what?":
        "Honesty is a virtue -- a character trait that philosophers from Aristotle to Kant have considered essential to a good life. Kant argued that lying is always wrong, even to protect someone, because it undermines the trust that makes society possible.",

    "What word means to prove that something is wrong?":
        "Disproof is central to good reasoning. Karl Popper argued that the mark of a genuinely scientific theory is that it can, in principle, be disproved. A claim that nothing could ever disprove is not knowledge -- it is dogma.",

    "Which philosopher asked 'What is the good life?'":
        "Socrates spent his life asking Athenians what they meant by virtue, justice, and the good life. He believed that most people had never seriously examined their own beliefs. His relentless questioning made him both the most loved and most hated man in Athens.",

    "What does it mean for two things to be 'equal'?":
        "Equality is one of the most debated concepts in philosophy. Do we mean equal in value, equal in treatment, equal in outcome, or equal in opportunity? Each interpretation leads to very different political and ethical conclusions.",

    "A statement that is always true, no matter what, is called what?":
        "Universal truths -- like the laws of logic or mathematics -- hold regardless of time, place, or circumstance. Philosophers debate whether moral truths can also be universal, or whether right and wrong vary by culture.",

    "What do we call the reasons we give to support an idea?":
        "In philosophy, an argument is not a fight -- it is a structured set of reasons (premises) leading to a conclusion. Good philosophy demands that you give evidence and arguments for your claims, not just assert them.",

    "Which word means doing something because it is the right thing to do?":
        "Duty -- what Kant called 'pflicht' -- is acting from moral obligation rather than desire or self-interest. Kant argued that the only truly moral actions are those done from duty. Doing the right thing because it benefits you does not count.",

    "What is the opposite of 'certain'?":
        "Uncertainty is where philosophy begins. If we were certain about everything, there would be no need to think. The greatest philosophers -- Socrates, Descartes, Hume -- started by acknowledging how much we do not know.",

    "If every person in a group agrees on something, that agreement is called what?":
        "Consensus can be a powerful tool for decision-making, but philosophers warn it is no guarantee of truth. The majority has been wrong many times throughout history. As Mill argued, even a single dissenting voice deserves to be heard.",

    "What do we call something that can be seen or measured by anyone?":
        "Objectivity -- the idea that some facts exist independently of what anyone thinks about them -- is a cornerstone of science and much of philosophy. The challenge is distinguishing what is truly objective from what merely seems that way.",

    "What word means making a conclusion from clues or evidence?":
        "Inference is the engine of reasoning. We observe evidence and draw conclusions that go beyond what we directly see. Every detective, scientist, and philosopher relies on inference -- the art of reading between the lines of reality.",

    "If something is 'fair', what does that mean?":
        "Fairness is one of philosophy's oldest puzzles. Does it mean equal treatment, equal opportunity, or equal outcomes? Aristotle said justice means treating equals equally and unequals unequally -- but who decides what counts as equal?",

    "What do we call a belief held by almost everyone in a society?":
        "Shared values bind societies together, but philosophers remind us that popular beliefs are not necessarily true. The majority once believed the Earth was flat, that slavery was natural, and that women should not vote.",

    "Which word means 'not depending on feelings or personal views'?":
        "Objectivity is an ideal that philosophy and science strive for -- judging claims by evidence and reason rather than personal preference. Perfect objectivity may be impossible, but the pursuit of it makes our thinking better.",

    "What is 'wisdom'?":
        "Wisdom is more than knowledge -- it is knowing how to use knowledge well. Aristotle called it 'phronesis' (practical wisdom): the ability to discern what is truly good and act accordingly. It comes from experience, reflection, and humility about what you do not know.",

    "What do we call choosing between two possible actions?":
        "Decision-making is where philosophy meets real life. Ethics helps us think about which choices are right, epistemology helps us evaluate our evidence, and logic helps us reason clearly about consequences.",

    "Aristotle, Plato, and Socrates were all famous what?":
        "These three giants form a chain of teacher and student: Socrates taught Plato, Plato taught Aristotle. Together, they created the foundations of Western philosophy. Alfred North Whitehead said all of Western philosophy is 'a series of footnotes to Plato.'",

    "What is a 'hypothesis'?":
        "A hypothesis is an educated guess that can be tested. In science, hypotheses must be falsifiable -- there must be some possible observation that could prove them wrong. Hypotheses that cannot be tested are not scientific claims.",

    "What word means caring about others' feelings and suffering?":
        "Empathy -- the ability to feel what another person feels -- is the emotional foundation of morality. Philosophers like David Hume and Adam Smith argued that moral sentiments, including empathy, are as natural to humans as self-interest.",

    "Which of these is an example of a fact, not an opinion?":
        "The boiling point of water can be measured and verified by anyone -- it is objective and independent of personal preference. 'Chocolate is the best flavor' depends on personal taste. Philosophy helps us distinguish facts from opinions.",

    "What do we call the ability to think about your own thoughts?":
        "Self-reflection is what makes philosophy possible. Animals think, but only humans can think about their thinking. This ability -- what philosophers call 'metacognition' -- allows us to examine our beliefs, correct our errors, and grow wiser.",

    "If a rule applies to everyone equally, it is described as what?":
        "Universality is a key test in ethics. Kant's categorical imperative asks: could you will your action to become a universal law? If everyone did what you are doing, would the world still work? If not, your action may be wrong.",

    "What is a 'dilemma'?":
        "A dilemma forces you to choose between two options, both of which have significant costs. The trolley problem is philosophy's most famous dilemma: do you divert a runaway trolley to kill one person instead of five? There is no painless answer.",

    "What word means something that is not real but exists as an idea?":
        "Abstract concepts like justice, numbers, and beauty cannot be touched or seen, yet they are central to human life. Plato argued that abstract Forms are actually more real than physical objects. Whether abstract things truly 'exist' is one of philosophy's deepest questions.",

    "What is 'morality'?":
        "Morality is the system of principles that guides our judgments about right and wrong. Every culture has moral rules, but philosophers ask whether there are universal moral truths or whether morality is simply a human invention that varies across societies.",

    "What do we call thinking through a problem step by step using logic?":
        "Reasoning is the philosopher's primary tool. Unlike intuition or emotion, reasoning can be checked step by step. If the premises are true and the logic is valid, the conclusion must follow -- that is the power of rigorous thought.",

    "What does 'justify' mean?":
        "In philosophy, justification is what turns mere belief into knowledge. You might believe something true by accident -- but you only know it when you can give good reasons for why it is true. Epistemologists have debated what counts as 'good reasons' for 2,500 years.",

    "A 'contradiction' is when two things are what?":
        "A contradiction -- like 'it is raining and it is not raining at the same time and place' -- cannot be true. Aristotle called the law of non-contradiction the most fundamental principle of thought. If contradictions were allowed, rational discussion would be impossible.",

    "Which Greek word is the root of 'philosophy'?":
        "Philosophia literally means 'love of wisdom' -- from 'philos' (love) and 'sophia' (wisdom). Pythagoras reportedly coined the term, saying he was not wise (sophos) but merely a lover of wisdom (philosophos). True philosophy begins with knowing you do not know.",

    "What do we call a rule that tells us how we should act?":
        "Moral principles -- like 'do not steal' or 'treat others as you wish to be treated' -- are rules of conduct. Philosophers disagree about where these principles come from: God, reason, nature, or social agreement.",

    "What is 'curiosity'?":
        "Aristotle opened his Metaphysics with the words 'All men by nature desire to know.' Curiosity is the spark that ignites philosophy. Without the desire to understand why things are the way they are, there would be no science, no philosophy, and no progress.",

    "What does 'perspective' mean?":
        "In philosophy, recognizing that every person sees the world from a particular point of view is crucial. Nietzsche's perspectivism holds that all knowledge is shaped by perspective. Understanding this makes us more humble and open-minded thinkers.",

    "If you break a promise on purpose, you have acted without what?":
        "Integrity comes from the Latin 'integer,' meaning whole or complete. A person of integrity is undivided -- their actions match their words. Breaking a promise fractures that wholeness, which is why it feels like a betrayal of character, not just of a commitment.",

    "What do we call the branch of philosophy dealing with beauty?":
        "Aesthetics was named by the German philosopher Alexander Baumgarten in 1735. It asks questions like: Is beauty in the eye of the beholder, or is it an objective quality? Can art be morally good or bad? What is the purpose of art?",

    "What word means following the same rules all the time?":
        "Consistency is a basic requirement of rational thought. If you apply a rule in one situation but not in an identical situation, you are being inconsistent -- and inconsistency is a sign that something has gone wrong in your reasoning.",

    "What is a 'premise'?":
        "In a logical argument, premises are the starting statements from which a conclusion is drawn. The strength of any argument depends entirely on whether its premises are true and whether the conclusion follows logically from them.",

    "What do we call the act of thinking about whether something is good or bad?":
        "Moral judgment is something every human being exercises daily, often without thinking about it. Philosophy asks us to slow down and examine our moral judgments: Why do we believe this is wrong? What principles are we applying?",

    "What is the name for a statement that follows logically from the premises?":
        "A conclusion is only as strong as the reasoning that supports it. In a valid argument, if the premises are true, the conclusion must be true. Learning to evaluate whether conclusions truly follow from premises is one of philosophy's most practical skills.",

    "What does 'impartial' mean?":
        "Impartiality -- judging without favoritism -- is central to justice. The blindfolded figure of Lady Justice represents this ideal. Philosophers like Rawls argue that fair principles of justice can only be chosen from behind a 'veil of ignorance' about your own position.",

    "Which ancient city was home to Socrates?":
        "Athens in the 5th century BC was the intellectual capital of the ancient world. It gave birth to democracy, tragedy, comedy, history, and philosophy. Socrates walked its agora (marketplace) daily, engaging anyone willing to talk about virtue, justice, and the good life.",

    # ── Tier 2 ──────────────────────────────────────────────────────────────

    "What is the core belief of Stoicism?":
        "The Stoics taught that virtue is the only true good and that external circumstances -- wealth, health, reputation -- are 'indifferent.' By aligning your will with reason and accepting what you cannot change, you can achieve inner peace regardless of what life throws at you.",

    "What is the Trolley Problem?":
        "Philippa Foot introduced this thought experiment in 1967: a runaway trolley will kill five people unless you divert it to a track where it will kill one. Most people say divert it. But in a variant where you must push a man off a bridge to stop the trolley, most refuse. Why the difference?",

    "John Locke argued people are born as a 'tabula rasa' (blank slate). What does this imply about the source of human knowledge?":
        "Locke rejected Plato's idea that the soul carries knowledge from before birth. He argued that at birth the mind is like a blank sheet of paper, and all knowledge comes from experience. This empiricist view helped launch modern psychology and education theory.",

    "Nietzsche's concept of the Ubermensch (Superman) was his proposed response to nihilism. What was the Ubermensch supposed to do?":
        "With 'God dead' and traditional morality collapsing, Nietzsche feared humanity would sink into nihilism. The Ubermensch would be a human who creates their own values and meaning, rising above the herd. Nietzsche's sister later distorted this idea to fit Nazi ideology -- a perversion he would have despised.",

    "What is a 'syllogism'?":
        "Aristotle formalized the syllogism as the basic unit of logical reasoning: 'All men are mortal; Socrates is a man; therefore Socrates is mortal.' This structure -- two premises yielding a necessary conclusion -- dominated logic for over 2,000 years.",

    "Who was the famous Stoic philosopher who was born a Roman slave?":
        "Epictetus (c. 50-135 AD) was born enslaved and lived with a permanent limp, possibly from abuse by his master. Yet he taught that true freedom is internal: 'It is not what happens to you, but how you react to it that matters.' His philosophy influenced Marcus Aurelius and modern cognitive behavioral therapy.",

    "Descartes used mind-body dualism to separate the thinking mind from physical matter. What major philosophical problem did this create?":
        "If mind and body are completely different substances -- one physical, one mental -- how do they interact? How does a thought (non-physical) cause your arm to move (physical)? This 'interaction problem' has plagued philosophy of mind ever since Descartes posed it.",

    "What is the 'social contract' theory about?":
        "Social contract theory asks: Why should anyone obey the government? The answer: because we have implicitly agreed to surrender some freedoms in exchange for protection and order. Hobbes, Locke, and Rousseau each gave different versions of this contract -- and different conclusions about what it requires.",

    "What is the 'categorical imperative' associated with?":
        "Immanuel Kant argued that moral rules must be universal and unconditional -- 'categorical' means they apply to everyone, no exceptions. His famous test: before acting, ask whether you could will that everyone act the same way. If not, your action is immoral.",

    "Which philosopher said 'God is dead'?":
        "Friedrich Nietzsche (1844-1900) was not celebrating -- he was diagnosing a crisis. He saw that modern Europeans no longer truly believed in God but had not yet found an alternative foundation for morality. 'God is dead, and we have killed him,' he wrote. 'How shall we comfort ourselves?'",

    "What does 'skepticism' mean in philosophy?":
        "Philosophical skepticism does not mean cynicism or denial -- it means carefully questioning whether our beliefs are truly justified. From Pyrrho in ancient Greece to Descartes in the 17th century, skeptics have used doubt as a tool to separate genuine knowledge from mere assumption.",

    "Who wrote 'Two Treatises of Government'?":
        "John Locke published the Two Treatises in 1689 to justify the Glorious Revolution. He argued that government exists to protect natural rights to life, liberty, and property. If it fails, the people may replace it. Thomas Jefferson drew heavily on Locke when writing the Declaration of Independence.",

    "What is utilitarianism?":
        "Utilitarianism holds that the right action is whichever produces the most happiness (or least suffering) for the most people. It sounds simple, but it raises hard questions: Should you sacrifice one innocent person to save five? A utilitarian might say yes.",

    "Who founded utilitarianism?":
        "Jeremy Bentham (1748-1832) developed the 'felicific calculus' to measure pleasure and pain. His embalmed body, topped with a wax head, still sits in a glass cabinet at University College London. He wanted to be useful even after death -- a fitting legacy for a utilitarian.",

    "Who was the most famous Cynic philosopher?":
        "Diogenes of Sinope lived in a barrel, walked Athens carrying a lantern 'looking for an honest man,' and reportedly told Alexander the Great to 'stand out of my sunlight.' The Cynics believed that civilization was corrupt and that virtue required living according to nature.",

    "What is 'Zeno's paradox' about?":
        "Zeno argued that to reach a destination, you must first cross half the distance, then half the remaining distance, then half again -- infinitely. So motion should be impossible! The paradox challenged mathematicians for centuries until calculus provided the tools to resolve it.",

    "What is the 'problem of evil' in philosophy?":
        "If God is all-good, all-powerful, and all-knowing, why does suffering exist? Either God cannot prevent evil (not all-powerful), does not want to (not all-good), or does not know about it (not all-knowing). This trilemma has challenged theologians and philosophers for millennia.",

    "Which philosopher wrote 'An Essay Concerning Human Understanding'?":
        "Locke's masterwork (1689) argued that all knowledge comes from experience, not innate ideas. He compared the mind at birth to 'white paper, void of all characters.' This empiricist approach became the foundation of modern psychology and the scientific method.",

    "What did John Locke believe people are born with?":
        "Locke's 'tabula rasa' (blank slate) theory rejected the ancient idea that humans are born with innate knowledge. Instead, he argued that experience -- both sensation and reflection -- writes everything we know onto the blank page of the mind.",

    "Hegel's dialectic describes how history and thought progress through thesis, antithesis, and synthesis. What does Marx claim to have done with this method?":
        "Marx said he found Hegel's dialectic 'standing on its head' and 'turned it right side up.' Where Hegel saw ideas driving history, Marx saw material and economic forces as the engine. For Marx, the clash of economic classes -- not abstract ideas -- drives historical change.",

    "What is 'deontological ethics'?":
        "Deontology, from the Greek 'deon' (duty), judges actions by whether they follow moral rules, not by their consequences. Kant is the most famous deontologist: lying is always wrong, even if it would save a life, because it violates a universal moral duty.",

    "What does the Socratic method involve?":
        "Socrates never lectured -- he asked questions. By gently probing, he led people to discover contradictions in their own beliefs. The method works because it makes the student, not the teacher, do the thinking. It is still used in law schools worldwide.",

    "What is 'Occam's Razor'?":
        "William of Ockham (c. 1287-1347), an English friar, argued that 'entities should not be multiplied beyond necessity.' In other words: if two explanations fit the facts equally well, choose the simpler one. This principle guides scientific thinking to this day.",

    "Who wrote 'The Art of War', a philosophical military text?":
        "Sun Tzu's ancient Chinese text (c. 5th century BC) teaches that the supreme art of war is to subdue the enemy without fighting. Its principles -- know yourself, know your enemy, use deception, exploit weakness -- have been applied to business, sports, and diplomacy for 2,500 years.",

    "What is the concept of 'wu wei' in Taoism?":
        "Wu wei means 'non-action' or 'effortless action' -- not laziness, but acting in harmony with the natural flow of things. Like water flowing around rocks, the Taoist sage achieves goals without forcing or straining. Laozi taught that the greatest leaders are those whose people say 'we did it ourselves.'",

    "Which philosopher believed in the existence of innate ideas?":
        "Descartes argued that certain ideas -- like the idea of God, infinity, and mathematical truths -- are 'born with us' rather than learned from experience. This rationalist view put him in direct opposition to Locke's empiricism.",

    "Who is associated with founding modern empiricism?":
        "Francis Bacon (1561-1626) argued that knowledge should be built from careful observation and experiment, not from ancient authorities. His 'Novum Organum' proposed an inductive method of reasoning from evidence -- a foundation of the scientific revolution.",

    "What does 'a posteriori' mean in philosophy?":
        "A posteriori knowledge -- 'from what comes after' -- requires experience. You cannot know the boiling point of water or the color of a flamingo without observation. It contrasts with a priori knowledge, which can be known through reasoning alone.",

    "Which philosopher is associated with the concept of the 'will to power'?":
        "Nietzsche's 'will to power' is often misunderstood as a desire to dominate others. He meant something deeper: the fundamental drive in all living things to grow, overcome, and create. An artist creating a masterpiece expresses will to power as much as a conqueror.",

    "What is the 'prisoner's dilemma'?":
        "Two prisoners, unable to communicate, must choose: cooperate (stay silent) or betray (confess). If both cooperate, both get light sentences. If one betrays, the betrayer goes free while the other gets a harsh sentence. Rational self-interest says betray -- but mutual cooperation is better for both.",

    "Who said 'Hell is other people'?":
        "Sartre put these words in a character's mouth in his play 'No Exit' (1944), where three people are trapped together in a room in hell. Sartre meant that we are constantly judged by others' gazes, making them a source of anguish. The line is often misquoted as simple misanthropy.",

    "What is 'nihilism'?":
        "Nihilism -- from the Latin 'nihil' (nothing) -- is the view that life has no inherent meaning or value. Nietzsche warned that the death of God would lead to nihilism unless humanity created new values. Existentialists like Camus argued we must create meaning despite the universe's silence.",

    "What is the 'veil of ignorance' in political philosophy?":
        "Rawls asks: what principles of justice would you choose if you did not know whether you would be rich or poor, male or female, talented or disabled? Behind this 'veil of ignorance,' Rawls argued, rational people would choose principles that protect the worst-off members of society.",

    "Who developed the 'veil of ignorance' thought experiment?":
        "John Rawls (1921-2002) published 'A Theory of Justice' in 1971, reviving political philosophy. His veil of ignorance became one of the most influential thought experiments of the 20th century, offering a powerful framework for thinking about fairness.",

    "Which philosopher wrote 'The Communist Manifesto' with Friedrich Engels?":
        "Karl Marx (1818-1883) and Friedrich Engels published the Manifesto in 1848, calling on workers to overthrow capitalism. Marx spent the rest of his life in London, often in poverty, writing 'Das Kapital.' His ideas inspired revolutions that reshaped the 20th century.",

    "Who said 'I only know that I know nothing'?":
        "Socrates, as reported by Plato, claimed this was the source of his wisdom. The Oracle at Delphi had declared him the wisest man in Athens -- and Socrates concluded it was because he alone recognized his own ignorance. True wisdom begins with humility.",

    "Kant argued that moral duty requires treating persons as ends in themselves, never merely as means. What political implication follows from this principle?":
        "Kant's principle means that no person can be used as a mere tool for someone else's benefit -- not even for the 'greater good.' This rules out slavery, forced labor, and any policy that treats individuals as disposable instruments of collective goals.",

    "What is the concept of 'karma' in Eastern philosophy?":
        "Karma literally means 'action' in Sanskrit. The principle holds that every action creates consequences -- good deeds lead to good results, bad deeds to bad results, whether in this life or the next. It is the universe's moral accounting system.",

    "Who is associated with the philosophical concept of Yin and Yang?":
        "Yin and Yang represent the Taoist understanding that all things exist in complementary pairs: light and dark, hot and cold, active and passive. Neither is superior -- balance between them is the key to harmony. The famous black-and-white symbol shows each containing a seed of the other.",

    "Who wrote 'Discourses' and taught that only virtue is truly good?":
        "Epictetus, born a slave, became one of the most influential Stoic teachers. His Discourses, recorded by his student Arrian, teach that external things like wealth and health are 'preferred indifferents' -- nice to have but not essential. Only virtue -- the right use of impressions -- is truly good.",

    "What is the term for a conclusion that follows necessarily from the premises?":
        "Deduction is the gold standard of logical reasoning: if the premises are true and the argument is valid, the conclusion is guaranteed to be true. 'All humans are mortal; Socrates is human; therefore Socrates is mortal' is a deductive argument.",

    "What do we call reasoning from specific examples to a general rule?":
        "Inductive reasoning moves from particular observations to general conclusions: 'Every swan I have seen is white, therefore all swans are white.' It is powerful but risky -- a single black swan can overturn the conclusion. Hume showed we can never be certain that induction will work.",

    "Socrates was famously put to death for what reason?":
        "In 399 BC, an Athenian jury convicted Socrates of impiety and corrupting the youth. He was sentenced to drink hemlock poison. His real crime was embarrassing powerful people by exposing their ignorance through relentless questioning.",

    "What is 'relativism' in ethics?":
        "Ethical relativism holds that moral truth varies by culture, time, or individual -- there are no universal moral facts. Critics argue this makes it impossible to condemn practices like slavery or genocide as objectively wrong.",

    "Who wrote 'The Republic', describing an ideal society?":
        "Plato wrote the Republic (c. 375 BC) as a dialogue exploring justice. His ideal state is ruled by philosopher-kings, defended by guardians, and supported by producers. The work includes the famous Allegory of the Cave and remains one of the most influential books ever written.",

    "What does 'empirical' mean?":
        "Empirical knowledge comes from observation and experiment -- testing ideas against the real world rather than relying on pure reasoning. The word comes from the Greek 'empeiria' (experience). Modern science is fundamentally empirical.",

    "What is 'utilitarianism'?":
        "Utilitarianism says the right action is the one that produces the greatest happiness for the greatest number. It sounds democratic and fair, but critics point out it could justify terrible things -- like torturing one person if it somehow made millions happy.",

    "What does it mean to commit a 'logical fallacy'?":
        "A logical fallacy is an error in reasoning that makes an argument invalid. They are like optical illusions for the mind -- they look convincing but are actually flawed. Learning to spot fallacies is one of the most practical skills philosophy teaches.",

    "What is 'free will'?":
        "The free will debate asks whether we truly choose our actions or whether everything we do is determined by prior causes -- genetics, upbringing, brain chemistry. If all our choices are predetermined, can we be held morally responsible for them?",

    "What is a 'straw man' argument?":
        "A straw man is created when you misrepresent someone's argument to make it easier to attack. It is called a 'straw man' because you are not fighting your opponent's real position -- you are fighting a weaker version you constructed yourself.",

    "Which philosopher created the concept of the 'Forms' -- perfect versions of things?":
        "Plato argued that behind every imperfect physical object lies a perfect, eternal Form. The circles we draw are imperfect copies of the Form of the Circle. The just acts we see are imperfect reflections of the Form of Justice. True knowledge is knowledge of the Forms.",

    "What is 'episteme' in Greek philosophy?":
        "Episteme is genuine knowledge -- justified, true understanding of how things really are. The Greeks distinguished it from doxa (mere opinion), which might happen to be true but lacks rational justification. This distinction remains central to epistemology.",

    "What fallacy occurs when you attack the person rather than their argument?":
        "The ad hominem fallacy is one of the most common errors in reasoning. Pointing out that a scientist is rude does not disprove their research. An argument's validity depends on its logic and evidence, not on the character of the person making it.",

    "What does 'subjective' mean?":
        "Subjective claims depend on personal experience or opinion -- 'chocolate ice cream is the best' is subjective. The philosophical challenge is determining which claims are genuinely subjective and which are objective truths that merely feel subjective.",

    "Who said 'I think, therefore I am'?":
        "Rene Descartes (1596-1650) arrived at his famous 'cogito ergo sum' by doubting everything he could. He could doubt his senses, his body, even mathematics -- but he could not doubt that he was thinking. The act of doubting proved the existence of a thinking being.",

    "What is the 'golden rule' in ethics?":
        "The golden rule appears independently in almost every major world culture and religion. Confucius said it, Jesus said it, Hillel said it. Its universality suggests something deep about human moral intuition -- we naturally understand that fairness requires reciprocity.",

    "What is an 'argument from authority'?":
        "Citing an expert is not always fallacious -- it is reasonable to trust a doctor about medicine. The fallacy occurs when the authority is not relevant (a celebrity endorsing a scientific claim) or when authority is used as the only basis for a claim, replacing evidence and reasoning.",

    "What did Aristotle call the 'final cause' of something?":
        "Aristotle identified four 'causes' or explanations for anything: material (what it is made of), formal (its structure), efficient (what made it), and final (its purpose). The final cause of a knife is to cut. This teleological thinking dominated philosophy for 2,000 years.",

    "What is 'skepticism' in philosophy?":
        "Philosophical skepticism is not paranoia -- it is the disciplined practice of questioning whether our beliefs are justified. Descartes used radical doubt to find one thing he could not doubt (his own existence), building all knowledge from that foundation.",

    "What is the 'is-ought problem'?":
        "Hume observed that many moral arguments slide from 'is' statements (facts about the world) to 'ought' statements (moral claims) without justification. Just because something is natural does not mean it ought to be valued. This gap between fact and value remains one of ethics' deepest challenges.",

    "Which philosopher is known for the concept of the 'Categorical Imperative'?":
        "Immanuel Kant (1724-1804) lived his entire life in Konigsberg, Prussia, and was so punctual that neighbors set their clocks by his daily walk. His categorical imperative -- 'Act only according to rules you could will to be universal laws' -- is one of the most influential ideas in moral philosophy.",

    "What is 'doxa' in ancient Greek philosophy?":
        "Doxa means mere opinion or belief -- what you think is true without being able to prove it. Plato sharply distinguished doxa from episteme (true knowledge). Democracy was sometimes criticized as the rule of doxa -- the uninformed opinions of the masses.",

    "What does it mean to say an argument is 'valid'?":
        "A valid argument is one where the conclusion follows necessarily from the premises -- even if the premises are false! 'All cats are blue; Fluffy is a cat; therefore Fluffy is blue' is valid but unsound (because the first premise is false). Validity is about logical structure, not truth.",

    "What fallacy is committed when a small first step is said to inevitably lead to extreme consequences?":
        "The slippery slope fallacy assumes that one step inevitably leads to a chain of events ending in disaster, without showing why each step necessarily follows. However, some slippery slope arguments are legitimate if each step in the chain can be justified.",

    "What does 'altruism' mean?":
        "Altruism -- selfless concern for others' well-being -- is a puzzle for philosophers. If evolution favors selfish genes, why do humans help strangers? Some argue altruism is disguised self-interest; others, like Peter Singer, argue it is a genuine moral capacity we should cultivate.",

    "What did Plato call people who mistake shadows for reality?":
        "In the Allegory of the Cave, prisoners chained since birth see only shadows cast on a wall and believe them to be real. Plato's point: most people are 'prisoners' of appearances, mistaking the visible world for ultimate reality. Education is the process of turning toward the light.",

    "What does 'a priori' mean?":
        "A priori knowledge -- 'from what comes before' -- can be known independently of experience. Mathematical truths like '2+2=4' and logical truths like 'all bachelors are unmarried' are a priori. You do not need to observe anything to know they are true.",

    "What is the 'fallacy of false dilemma'?":
        "A false dilemma presents only two options when more exist: 'You are either with us or against us.' Real life usually offers more nuanced positions. Recognizing false dilemmas is crucial for clear thinking in politics and everyday life.",

    "What is 'hedonism'?":
        "Hedonism holds that pleasure is the only intrinsic good and pain the only intrinsic evil. Epicurus was a hedonist, but he meant intellectual pleasure and tranquility, not wild indulgence. Bentham's utilitarianism is a form of hedonism applied to social policy.",

    "What is 'reductionism'?":
        "Reductionism explains complex phenomena by breaking them into simpler parts. Chemistry reduces to physics, biology reduces to chemistry. Critics argue that some things -- consciousness, meaning, beauty -- are lost in the reduction. The whole may be more than the sum of its parts.",

    "What is a 'thought experiment'?":
        "Thought experiments let philosophers test ideas without laboratories. Descartes's evil demon, Plato's cave, the trolley problem, and the brain in a vat are all thought experiments. They work by isolating a specific philosophical question and forcing us to confront our intuitions.",

    "Which philosopher identified 'happiness' (eudaimonia) as the highest human goal?":
        "Aristotle argued in the Nicomachean Ethics that eudaimonia is the ultimate end of all human activity. But he did not mean fleeting pleasure -- he meant a life of virtuous activity, excellence, and fulfillment. It is something you achieve over an entire lifetime, not in a moment.",

    "What is an 'inference to the best explanation'?":
        "When a detective encounters evidence and picks the hypothesis that best explains all the clues, they are using inference to the best explanation (also called abduction). It is how scientists choose between theories and how we make sense of everyday life.",

    "What does 'cogito ergo sum' translate to?":
        "Descartes's 'I think, therefore I am' was his unshakeable foundation. Even if an evil demon is deceiving him about everything, the very act of being deceived proves he exists as a thinking being. From this single certainty, he attempted to rebuild all knowledge.",

    "What does 'ad hoc' mean in reasoning?":
        "An ad hoc explanation is invented after the fact specifically to save a theory from being disproved. If your theory predicts X and you observe not-X, adding an ad hoc excuse weakens the theory. Good theories make predictions before the evidence comes in.",

    "John Stuart Mill developed which ethical theory?":
        "Mill refined Bentham's utilitarianism by distinguishing between 'higher' and 'lower' pleasures. He argued that intellectual pleasures are qualitatively superior to physical ones: 'It is better to be Socrates dissatisfied than a fool satisfied.'",

    "John Locke argued that people have natural rights to life, liberty, and property that no government may violate. Where do these rights come from, according to Locke?":
        "Locke grounded natural rights in God-given reason and natural law. Rights exist before government and independently of it. Government's sole purpose is to protect them -- and if it fails, the people may withdraw their consent.",

    "Locke argued that government derives its legitimate authority from the consent of the governed. What right do people retain if a government violates their natural rights?":
        "Locke's right of revolution was his most radical claim. He argued that when a government systematically violates natural rights, it breaks the social contract and the people are justified in dissolving it. Jefferson echoed this argument word for word in the Declaration of Independence.",

    "Mill's harm principle states that the only justification for society to restrict individual liberty is to prevent harm to others. Which of the following does Mill explicitly say is NOT sufficient justification for restricting freedom?":
        "Mill drew a sharp line between actions that affect others (which society may regulate) and self-regarding actions (which it may not). Your body and mind are your own -- society has no right to force you to be healthy, moral, or wise against your will.",

    "Mill defended freedom of speech even for false and harmful opinions. What was his primary justification?":
        "Mill argued that silencing an opinion robs us of the chance to replace error with truth -- and even if the silenced opinion is wrong, challenging it keeps our understanding of truth alive and vigorous. Unchallenged truths become 'dead dogmas.'",

    "The philosophical distinction between 'negative rights' and 'positive rights' is crucial in political philosophy. What is a negative right?":
        "Negative rights require only that others leave you alone -- the right not to be killed, robbed, or imprisoned without cause. They are 'negative' because they oblige inaction. The American Bill of Rights is primarily a list of negative rights.",

    "What is the 'ad hominem' fallacy, and why is it relevant to evaluating political and philosophical arguments?":
        "Attacking a person's character, motives, or background instead of their argument is a tempting shortcut that short-circuits rational debate. A hypocrite can still make a valid argument. Judge the reasoning, not the reasoner.",

    "What is 'confirmation bias' in epistemology, and why is it a threat to good reasoning?":
        "We all tend to notice evidence that supports what we already believe and ignore evidence that contradicts it. This bias makes us feel more certain than we should be. The antidote is actively seeking out information that could prove us wrong.",

    "What is a 'circular argument' (begging the question), and why does it fail as proof?":
        "A circular argument assumes the very thing it is trying to prove. 'God exists because the Bible says so, and the Bible is true because it is the word of God' goes in a circle. It may sound convincing, but it proves nothing beyond its own assumptions.",

    "Epictetus taught that we should distinguish between what is 'up to us' and what is not. According to Stoicism, what is truly 'up to us'?":
        "Epictetus taught that only our own judgments, desires, and choices are truly within our control. Everything else -- our health, reputation, wealth, even our lives -- depends on factors beyond us. Freedom comes from focusing entirely on what you can control.",

    "Thomas Paine argued in 'Common Sense' that government even at its best is a 'necessary evil.' What was his philosophical reasoning?":
        "Paine argued that government exists only because humans lack the virtue to live peacefully without it. Since government restricts freedom by its very nature, its power must be kept to the absolute minimum necessary to maintain order.",

    "Aristotle argued in the 'Politics' that humans are by nature 'political animals.' What does this mean?":
        "Aristotle meant that humans can only achieve their full potential -- eudaimonia -- within a community. Language, reason, and morality all develop through social interaction. A human living completely alone would be, as Aristotle said, 'either a beast or a god.'",

    "What logical fallacy occurs when someone argues that because something has always been done a certain way, it must be correct?":
        "The appeal to tradition assumes that longevity equals truth. But slavery, child labor, and denying women the vote were all ancient traditions. Just because something has always been done does not mean it should continue.",

    "Which of the following is an example of a 'false dilemma' (either-or fallacy) in political philosophy?":
        "False dilemmas force complex issues into black-and-white choices. In reality, most political questions have a range of possible answers. Recognizing when someone presents only two extreme options is essential for clear political thinking.",

    "What is utilitarianism's main philosophical objection from a rights-based perspective?":
        "Utilitarianism can justify horrifying acts against individuals if the math works out. If torturing one person would prevent a war, utilitarianism might approve. Rights-based theories insist that some things are wrong regardless of consequences.",

    "Classical liberalism holds that governments are instituted to protect pre-existing rights, not to create them. Which philosopher most clearly stated this principle?":
        "Locke's Second Treatise argues that rights to life, liberty, and property exist in the 'state of nature' -- before any government. Government is created by consent to protect those rights. If it violates them, it has broken the contract.",

    "Why did classical liberals like Locke insist that legitimate government requires the 'consent of the governed'?":
        "Without consent, the relationship between ruler and ruled is no different from that between master and slave. Consent transforms power from mere force into legitimate authority. This idea was revolutionary -- it overturned millennia of divine-right monarchy.",

    # ── Tier 3 ──────────────────────────────────────────────────────────────

    "What is 'epistemology'?":
        "Epistemology asks the most fundamental questions about knowledge: What can we know? How can we know it? When is a belief justified? These questions sound abstract, but they have enormous practical implications -- they determine how we evaluate evidence, assess claims, and distinguish truth from falsehood.",

    "What is Kant's 'categorical imperative'?":
        "Kant offered a moral test as rigorous as a mathematical proof: before acting, ask whether you could will that everyone act the same way. If universalizing your action leads to a contradiction (like 'everyone should lie' -- which destroys trust and makes lying pointless), then the action is immoral.",

    "What is the 'brain in a vat' thought experiment designed to question?":
        "Imagine a mad scientist removes your brain, places it in a vat, and feeds it electrical signals simulating normal experience. How would you know the difference? You could not. The experiment shows that we cannot prove the external world exists based on experience alone.",

    "Who created the thought experiment of the 'evil demon' to doubt all knowledge?":
        "Descartes imagined an all-powerful evil demon devoted to deceiving him about everything -- mathematics, the external world, even his own body. This radical doubt stripped away every belief until only one remained: 'I think, therefore I am.'",

    "Who is often considered the father of existentialism?":
        "Soren Kierkegaard (1813-1855) insisted that philosophy must address the individual's lived experience, not abstract systems. He argued that life's most important choices -- faith, love, identity -- cannot be resolved by reason alone. You must make a 'leap of faith.'",

    "What is the 'problem of other minds'?":
        "You experience your own consciousness directly, but you can never directly experience anyone else's. How do you know other people are conscious and not just very convincing robots? This problem has never been solved -- we all take other minds on faith.",

    "Who wrote 'Critique of Pure Reason'?":
        "Immanuel Kant's 1781 masterwork attempted to resolve the conflict between rationalism and empiricism. His revolutionary insight: the mind actively shapes experience through innate categories (space, time, causation), so we never perceive 'things in themselves' -- only things as they appear to us.",

    "Who is most associated with virtue ethics in ancient Greece?":
        "Aristotle argued that ethics is not about following rules or maximizing outcomes, but about developing good character. Virtues like courage, temperance, and justice are habits we cultivate through practice -- just as a musician becomes skilled through playing.",

    "Who wrote 'Utilitarianism', expanding Bentham's theory?":
        "John Stuart Mill (1806-1873) was a child prodigy who had a nervous breakdown at 20 and emerged with a richer understanding of human happiness. His 'Utilitarianism' (1863) argued that intellectual pleasures are qualitatively superior to physical ones, giving utilitarianism a more sophisticated form.",

    "What is 'moral relativism'?":
        "Moral relativism holds that there are no objective moral truths -- what is right or wrong varies by culture or individual. It sounds tolerant, but critics point out it makes it impossible to condemn practices like human sacrifice or slavery as universally wrong.",

    "Which philosopher's work developed the concept of 'dialectics'?":
        "Hegel (1770-1831) saw all of history as a dialectical process: a thesis generates its antithesis, and the tension between them produces a synthesis, which becomes the new thesis. This process drives history toward greater freedom and self-understanding.",

    "Who said 'Whatever does not kill me makes me stronger'?":
        "Nietzsche wrote this in 'Twilight of the Idols' (1888). It captures his philosophy of amor fati (love of fate) -- embracing suffering as a catalyst for growth. Nietzsche himself suffered terribly from illness throughout his life, giving the maxim personal weight.",

    "What is the 'Chinese Room' thought experiment?":
        "Searle imagines a person locked in a room, following rules to produce Chinese-language responses to Chinese questions. The person does not understand Chinese -- they are just manipulating symbols. Searle argues that computers similarly manipulate symbols without understanding meaning.",

    "Who proposed the 'Chinese Room' argument?":
        "John Searle (born 1932) devised the argument in 1980 to challenge the idea that a computer running the right program could truly think or understand. His point: syntax (following rules) is not sufficient for semantics (understanding meaning).",

    "What is 'phenomenology'?":
        "Phenomenology studies the structures of conscious experience -- how things appear to us from the first-person perspective. Edmund Husserl founded it by insisting that philosophy must begin with careful description of experience, setting aside assumptions about what lies behind it.",

    "What does 'ontology' study?":
        "Ontology asks the most basic of all questions: What exists? Do numbers exist? Do abstract concepts like justice exist? Is the mind a separate entity from the brain? Every philosophical position rests on ontological assumptions about what is real.",

    "What is 'solipsism'?":
        "Solipsism is the view that only your own mind is certain to exist. Everything else -- the external world, other people -- could be a projection of your mind. It is almost impossible to disprove, which is why philosophers consider it a serious challenge even if no one actually believes it.",

    "Which philosopher wrote 'Being and Time'?":
        "Martin Heidegger (1889-1976) published 'Being and Time' in 1927, asking the question philosophy had forgotten: What does it mean for something to 'be'? His analysis of human existence (Dasein) as 'being-toward-death' profoundly influenced existentialism and continental philosophy.",

    "What is 'absurdism' in philosophy?":
        "Albert Camus argued that humans desperately seek meaning in a universe that offers none. This clash between our need for meaning and the universe's silence is 'the absurd.' Rather than despair or religion, Camus proposed rebellion: 'One must imagine Sisyphus happy.'",

    "What does 'free will' mean in philosophy?":
        "The free will problem asks: if every event has a cause, and our decisions are events, then are our decisions caused by prior events beyond our control? If so, are we really free -- or just complex dominoes falling in a predetermined sequence?",

    "What is 'determinism'?":
        "Determinism holds that every event, including every human decision, is the inevitable result of prior causes. If you rewound the universe to exactly the same state, everything would happen the same way again. This view challenges our sense of personal responsibility.",

    "Who wrote 'The Second Sex', a foundational feminist philosophical text?":
        "Simone de Beauvoir (1908-1986) argued in 'The Second Sex' (1949) that 'one is not born, but rather becomes, a woman.' She showed how society constructs femininity as 'the Other' -- defined in relation to men rather than on its own terms.",

    "Which philosopher first introduced the concept of the 'Ubermensch' (Superman)?":
        "Nietzsche introduced the Ubermensch in 'Thus Spoke Zarathustra' (1883). The Ubermensch creates their own values and meaning in a godless world. Nietzsche would have been horrified by the Nazi appropriation of this concept -- he despised nationalism and antisemitism.",

    "Who founded philosophical pragmatism in America?":
        "Charles Sanders Peirce (1839-1914) argued that the meaning of any concept lies in its practical consequences. If two theories have identical practical effects, any difference between them is meaningless. William James and John Dewey later developed pragmatism into a major philosophical movement.",

    "Isaiah Berlin distinguished 'negative liberty' (freedom from interference) from 'positive liberty' (capacity to act). Why did Berlin warn that 'positive liberty' could justify totalitarianism?":
        "Berlin showed that once you define freedom as achieving your 'true self,' a government can claim to know your true interests better than you do -- and 'liberate' you by overriding your choices. Every tyrant who 'forces people to be free' is exploiting positive liberty.",

    "'Positive liberty' means the capacity to act on your free will. Critics argue this concept can be misused. Which of the following best illustrates the danger?":
        "When a state claims to know citizens' 'true' interests and overrides their actual choices for their 'own good,' it is using positive liberty as a weapon. Berlin warned that this reasoning has justified every totalitarian regime in modern history.",

    "Which philosopher identified 'substance' as one infinite thing he called God or Nature?":
        "Baruch Spinoza (1632-1677) was excommunicated from his Jewish community for arguing that God and Nature are the same thing. His 'Ethics,' written in geometric proof format, argued that everything is a mode of one infinite substance. Einstein said he believed in 'Spinoza's God.'",

    "Who wrote 'Tractatus Logico-Philosophicus'?":
        "Ludwig Wittgenstein (1889-1951) published the Tractatus in 1921, believing he had solved all the problems of philosophy. Its famous last line: 'Whereof one cannot speak, thereof one must be silent.' He later rejected his own work and started over with a completely new approach.",

    "Who identified the 'is-ought problem'?":
        "David Hume (1711-1776) noticed that moral arguments often slide from statements about what 'is' to claims about what 'ought' to be without justification. You cannot derive moral conclusions from factual premises alone. This insight remains one of the most important in ethics.",

    "What is the 'Gettier problem'?":
        "Edmund Gettier showed in a three-page paper in 1963 that you can have a justified true belief that is not really knowledge. Example: you see what looks like a sheep in a field. There is a sheep there -- but what you saw was actually a dog in a sheep costume. Your belief is justified and true, but it is not knowledge.",

    "What does 'teleology' mean?":
        "Teleology explains things by their purpose or end goal. Aristotle was teleological: he asked 'What is it for?' about everything from acorns (to become oaks) to humans (to achieve eudaimonia). Modern science mostly rejects teleological explanation in nature, but it remains relevant in ethics.",

    "Which philosopher argued that humans have natural rights to life, liberty, and property?":
        "John Locke's argument that rights precede government and cannot be taken away by it became the philosophical foundation of liberal democracy. Jefferson changed 'property' to 'pursuit of happiness' in the Declaration of Independence, but the Lockean framework is unmistakable.",

    "What is 'natural law theory'?":
        "Natural law theory holds that certain moral truths are built into the fabric of reality and can be discovered through reason. Aquinas argued that human law must conform to natural law, which in turn derives from divine law. An unjust law, he said, 'is no law at all.'",

    "Who wrote 'Meditations on First Philosophy'?":
        "Descartes published his Meditations in 1641, seeking an absolutely certain foundation for knowledge. Over six meditations, he doubted everything, found certainty in 'I think, therefore I am,' and attempted to rebuild all knowledge from that foundation. The work launched modern philosophy.",

    "What is 'moral absolutism'?":
        "Moral absolutism holds that some acts are always wrong, regardless of circumstances or consequences. Kant argued that lying is always wrong, even to save a life. Critics say this is too rigid -- surely context matters -- but absolutists reply that moral rules must be universal or they are not truly moral.",

    "Who proposed the philosophical concept of the 'eternal recurrence'?":
        "Nietzsche asked: What if you had to live your exact life over and over for eternity? Would you embrace it joyfully or recoil in horror? He proposed this as the ultimate test of how well you have lived -- the person who can say 'Yes!' to eternal recurrence has truly affirmed life.",

    "What is 'social constructivism'?":
        "Social constructivism holds that much of what we take to be 'natural' or 'given' -- gender roles, racial categories, even scientific knowledge -- is actually constructed through social processes. This does not mean these things are unreal, but that they could have been constructed differently.",

    "Who wrote 'The Origin of Species', influencing philosophy of nature?":
        "Darwin's 1859 work did not just revolutionize biology -- it transformed philosophy by showing that the apparent design in nature could arise through blind, purposeless processes. This undermined the teleological argument for God's existence and raised profound questions about human nature.",

    "What is 'epistemic justification'?":
        "Epistemologists ask: What makes a belief justified? Is it evidence? Coherence with other beliefs? Reliability of the process that produced it? Getting this right matters enormously -- the difference between knowledge and mere opinion depends on justification.",

    "J.L. Austin identified 'performative utterances' in speech act theory. Which example below is a performative rather than a descriptive statement?":
        "When you say 'I promise to pay you back,' you are not describing a pre-existing promise -- you are creating one. The words themselves perform an action. Austin's insight launched an entire field studying how language does things, not just says things.",

    "The central claim of existentialism?":
        "Sartre declared that 'existence precedes essence' -- meaning we are not born with a predetermined purpose. We exist first, then define ourselves through our choices. This is both liberating and terrifying: there is no script, no excuse, and no one to blame but yourself.",

    "What is 'phenomenology' in philosophy?":
        "Founded by Edmund Husserl, phenomenology studies the structures of conscious experience. It asks: What is it like to perceive, remember, imagine, or judge? Rather than explaining consciousness in terms of brain chemistry, it describes experience from the inside.",

    "What did Kant mean by the 'Categorical Imperative'?":
        "Kant's test is elegantly simple: before acting, ask 'Could I will that everyone do this?' If universalizing your action leads to a contradiction -- like 'everyone should break promises,' which would destroy the institution of promising itself -- then the action is immoral.",

    "Which philosopher argued that 'God is dead'?":
        "Nietzsche was not making an atheist argument -- he was observing a cultural crisis. Modern Europeans had lost genuine religious belief but had nothing to replace it. Without the Christian moral framework, Nietzsche feared, humanity would face nihilism and moral chaos.",

    "What is 'dialectic' in Hegel's philosophy?":
        "Hegel's dialectic describes how thought and history develop through contradiction: a thesis generates an antithesis, and the tension between them is resolved in a synthesis at a higher level. Marx later applied this pattern to economics and class struggle.",

    "What is the 'ship of Theseus' paradox about?":
        "If you replace every plank of a ship one by one until no original material remains, is it still the same ship? And if you build a new ship from the old planks, which one is the real Ship of Theseus? This ancient puzzle reveals deep questions about identity and change.",

    "What did John Locke believe about the mind at birth?":
        "Locke rejected Plato's theory that the soul carries knowledge from before birth. He argued the mind begins as a 'white paper' on which experience writes everything. This empiricist view influenced everything from education to psychology.",

    "What did Thomas Hobbes describe as 'nasty, brutish, and short'?":
        "Hobbes described life in the 'state of nature' -- human existence without government -- as a 'war of every man against every man.' Without a powerful sovereign to keep order, humans would live in constant fear and violence.",

    "What is 'compatibilism' in the free will debate?":
        "Compatibilists argue that free will and determinism are not contradictory. You are free when you act according to your own desires without external coercion -- even if those desires were themselves determined by prior causes. Most contemporary philosophers are compatibilists.",

    "What is 'social contract theory'?":
        "Social contract theory explains why we should obey government: we have implicitly agreed to give up some freedoms in exchange for order and protection. Hobbes, Locke, and Rousseau each gave different versions -- and reached very different conclusions about what kind of government is legitimate.",

    "What is the 'problem of induction' identified by Hume?":
        "Hume showed that we cannot logically prove that the future will resemble the past. Just because the sun has risen every morning does not guarantee it will rise tomorrow. We rely on induction constantly, but we cannot justify it without circular reasoning.",

    "What is the Euthyphro dilemma?":
        "Socrates asked: Is something good because the gods command it, or do the gods command it because it is good? If the first, morality is arbitrary -- the gods could command anything. If the second, goodness is independent of the gods. This dilemma still challenges divine command theory.",

    "What is 'panopticism' as described by Foucault?":
        "Foucault used Jeremy Bentham's panopticon prison design -- where inmates can always be watched but never know when -- as a metaphor for modern society. We internalize surveillance and regulate our own behavior, making external force unnecessary.",

    "What did Aristotle call the 'unmoved mover'?":
        "Aristotle reasoned that all motion must have a cause, but this chain of causes cannot go back forever. There must be a first cause that sets everything in motion without itself being moved. This 'unmoved mover' -- pure thought thinking itself -- became a foundation for later theological arguments.",

    "What is 'empiricism'?":
        "Empiricism holds that all knowledge comes from sensory experience. Locke, Berkeley, and Hume developed this tradition in opposition to rationalists like Descartes who believed reason alone could discover truth. Modern science is fundamentally empiricist in method.",

    "What is the 'naturalistic fallacy'?":
        "G.E. Moore argued that 'good' cannot be defined in terms of any natural property (like pleasure or evolutionary fitness). Just because something is natural does not make it good -- and just because something produces pleasure does not mean it is what 'good' means.",

    "What is 'Plato's cave' meant to illustrate?":
        "Most people live like prisoners in a cave, mistaking shadows on the wall for reality. Education is the painful process of turning toward the light and seeing things as they really are. Those who make it out have a duty to return and help the others.",

    "What is 'moral intuitionism'?":
        "Moral intuitionists argue that we can perceive moral truths directly, just as we perceive colors or sounds. We simply 'see' that cruelty is wrong without needing an argument. Critics counter that moral intuitions vary between cultures and individuals.",

    "What is 'ontology'?":
        "Ontology -- the study of being and existence -- asks the most fundamental questions possible. What kinds of things exist? Do numbers exist? Do abstract concepts like justice exist? Your answers to these questions shape everything else you believe about the world.",

    "What did Jean-Paul Sartre mean by 'bad faith'?":
        "Sartre argued that humans constantly flee from their own freedom by pretending they have no choice. The waiter who is 'playing at being a waiter,' the person who says 'I had no choice' -- both are in bad faith, denying the radical freedom that defines human existence.",

    "What is the 'trolley problem' designed to explore?":
        "The trolley problem forces a confrontation between two moral intuitions: the utilitarian impulse to save the most lives and the deontological reluctance to actively kill. Why does pulling a lever feel different from pushing a person, even if the outcome is identical?",

    "What is 'deontology'?":
        "Deontological ethics judges actions by whether they follow moral rules or duties, regardless of consequences. For a deontologist like Kant, a good outcome does not justify a wrong action. Lying to save a life is still lying -- and lying is always wrong.",

    "Which philosopher is most associated with the concept of 'will to power'?":
        "Nietzsche's 'will to power' is not about political domination. It is the fundamental drive in all living things to grow, create, and overcome obstacles. An artist, a scientist, and an athlete all express will to power -- the desire to excel and become more than you are.",

    "What is 'confirmation bias'?":
        "Confirmation bias is the tendency to seek out and remember evidence that supports what you already believe while ignoring contradictory evidence. It affects everyone, and recognizing it in yourself is one of the most important steps toward clear thinking.",

    "What is 'Rawlsian justice'?":
        "Rawls argued that a just society is one whose rules would be chosen by rational people who do not know their own position in it. Behind the 'veil of ignorance,' you would choose rules that protect the worst-off -- because you might be the worst-off person.",

    "What is 'philology' in its historical relation to philosophy?":
        "Philology -- the study of language and texts -- was essential to philosophy before the modern era. Understanding what ancient philosophers actually wrote requires mastering Greek, Latin, and the cultural context of their words. Nietzsche was a professor of philology before becoming a philosopher.",

    "What is 'contractarianism'?":
        "Contractarianism argues that moral rules are those that rational people would agree to under fair conditions. It traces back to Hobbes, Locke, and Rousseau, and was revived by Rawls. The key insight: moral rules must be justifiable to everyone they affect.",

    "What is 'Marxist alienation'?":
        "Marx argued that capitalism alienates workers from the products of their labor, from the work process itself, from other workers, and from their own human nature. A factory worker who makes car parts all day but can never afford a car experiences alienation.",

    "What is 'Zeno's paradox of motion'?":
        "Zeno showed that to walk across a room, you must first cross half the distance, then half the remaining distance, then half again -- infinitely. Since you can never complete an infinite number of steps, motion should be impossible. Calculus eventually resolved the mathematical puzzle.",

    "What is 'realism' in philosophy?":
        "Philosophical realism holds that the external world exists independently of our minds. There really are trees, rocks, and stars out there, whether or not anyone perceives them. This seems obvious, but Berkeley, Kant, and others have given powerful arguments against it.",

    "What did Hegel mean by 'geist'?":
        "Geist (mind/spirit) is the driving force of Hegel's philosophy. He argued that history is the process of Geist coming to understand itself through human civilization. Each era represents a stage in this self-unfolding, progressing dialectically toward absolute knowledge.",

    "What is the 'paradox of tolerance'?":
        "Karl Popper argued that unlimited tolerance leads to the disappearance of tolerance. If a society tolerates those who wish to destroy tolerance -- hate groups, totalitarians -- it will eventually be destroyed. A tolerant society must be intolerant of intolerance to survive.",

    "What is 'aporia' in Socratic philosophy?":
        "Aporia is the state of bewilderment that comes when Socrates's questioning reveals that you do not actually know what you thought you knew. It is uncomfortable but essential: you cannot begin to learn until you realize your ignorance.",

    "What is 'anti-realism'?":
        "Anti-realism argues that the world as we experience it is shaped by our minds, language, or conceptual frameworks rather than simply mirroring an independent reality. It does not necessarily deny that something exists beyond our minds -- just that we cannot access it directly.",

    "What is 'Bentham's utilitarian calculus'?":
        "Bentham proposed measuring pleasure and pain along seven dimensions: intensity, duration, certainty, nearness, fecundity, purity, and extent. While the idea of a precise 'pleasure calculator' seems naive, Bentham's systematic approach to ethics was revolutionary.",

    "What is 'essentialism'?":
        "Essentialism holds that things have fixed, innate properties that make them what they are. A triangle essentially has three sides. Existentialists reject essentialism about humans -- Sartre argued that humans have no fixed nature and define themselves through choices.",

    "What is 'the examined life' according to Socrates?":
        "Socrates argued at his trial that 'the unexamined life is not worth living for a human being.' He meant that the daily practice of questioning your own beliefs, values, and actions is what makes life genuinely human. Without it, we are just sleepwalking.",

    "Kant argued moral worth comes from:":
        "Kant held that only actions done from duty have genuine moral worth. If you help someone because it makes you feel good, your action is not truly moral -- you were just following your inclinations. Moral worth requires acting because it is right, even when it costs you.",

    "According to Locke's labor theory of property, how does a person legitimately acquire ownership of something from nature?":
        "Locke argued that when you mix your labor with something from nature -- farming land, gathering fruit, building a house -- you add your own effort to it and thereby make it yours. This theory became the philosophical basis for property rights in the English-speaking world.",

    "Hobbes argued people surrender their rights to a sovereign to escape the state of nature. What did he call the political entity that results?":
        "Hobbes called the state 'Leviathan' -- after the biblical sea monster -- because it must be powerful enough to terrify everyone into obedience. Without this overwhelming power, humans would revert to their natural state of constant war.",

    "Locke's contract is limited: government holds power in trust and loses authority if it violates natural rights":
        "Unlike Hobbes, who demanded an absolute sovereign, Locke insisted that government holds power as a trust from the people. When that trust is violated, the contract is broken and the people may replace the government -- a principle the American founders took to heart.",

    "Hayek argued that economic central planning must fail because of what he called the 'knowledge problem.' What is the knowledge problem?":
        "Hayek showed that the knowledge needed to run an economy is dispersed among millions of individuals -- each knowing local conditions that no central authority could ever gather. Only the price system, emerging spontaneously from free exchange, can coordinate this scattered information.",

    "Hayek's concept of 'spontaneous order' describes how complex beneficial patterns emerge without central direction. Which of the following is his primary example?":
        "Markets, language, law, and scientific knowledge all emerged without anyone designing them. Hayek argued that the most beneficial and complex social institutions are those no single mind could have planned. Attempts to replace spontaneous order with central planning destroy the very knowledge that makes order possible.",

    "Karl Popper argued that Marxism is not a science but a pseudoscience. What was his criterion for making this distinction?":
        "Popper argued that a genuinely scientific theory must make specific, testable predictions that could, in principle, prove it wrong. Marxism immunizes itself against refutation by reinterpreting every failed prediction -- making it unfalsifiable and therefore unscientific.",

    "Popper criticized Marxism and Freudianism as pseudosciences because they could explain any outcome after the fact. What does Popper call a theory that can account for every possible result?":
        "An unfalsifiable theory is one that makes no predictions that could prove it wrong. If a theory can explain every possible observation, it actually explains nothing. The mark of genuine science is the willingness to be proven wrong.",

    "Frederic Bastiat described 'legal plunder' as a perversion of the law. What does he mean by this term?":
        "Bastiat argued that when the law takes from some to give to others, it has been perverted from its proper purpose. The law exists to protect rights, not to redistribute wealth. When it does the latter, it becomes 'legalized plunder' -- and everyone scrambles to plunder legally.",

    "Bastiat argued that the proper purpose of the law is limited to one function. What is that function?":
        "For Bastiat, the law is simply 'the organization of the natural right of lawful defense.' Its only legitimate purpose is to protect individuals' pre-existing rights to life, liberty, and property. Anything beyond that is a perversion.",

    "Robert Nozick argued in 'Anarchy, State, and Utopia' that the only just state is a minimal state. What did he mean by a 'minimal state'?":
        "Nozick's minimal state handles only protection against force, theft, and fraud, and enforcement of contracts. Anything more -- even taxation for redistribution -- violates individual rights. His work is the most rigorous philosophical defense of libertarianism.",

    "Rawls's 'veil of ignorance' asks us to choose principles of justice without knowing our place in society. What type of principles does Rawls believe rational people would choose?":
        "Rawls argued that rational people behind the veil would choose 'maximin' -- principles that maximize the position of the worst-off group. Since you might end up at the bottom, you would want a society that treats its least fortunate members as well as possible.",

    "Ayn Rand argued that rational self-interest is the highest virtue. How does she respond to the objection that selfishness is destructive to society?":
        "Rand distinguished rational self-interest -- productive work, honest trade, genuine achievement -- from the predatory selfishness people usually mean. Her ideal person creates value through their own effort and trades freely with others. Force and fraud are not in one's rational self-interest.",

    "Ayn Rand called her philosophy 'Objectivism.' What did she argue is the foundation of all knowledge?":
        "Rand began with three axioms: existence exists, consciousness is conscious, and A is A (the law of identity). From these, she argued that reality is objective, reason is our only means of knowledge, and rational self-interest is the basis of morality.",

    "The 'utility monster' thought experiment critiques utilitarianism. What does it illustrate?":
        "Robert Nozick imagined a being that derives enormous pleasure from resources. Since utilitarianism maximizes total happiness, the utility monster should get everything -- leaving everyone else with nothing. The thought experiment exposes utilitarianism's inability to protect individual rights.",

    "Marx argued history is driven by 'historical materialism': the material conditions of production determine consciousness. What does this imply about ideas such as justice or liberty?":
        "For Marx, ideas about justice, liberty, and morality are not universal truths but ideological reflections of the ruling class's economic interests. The bourgeoisie promotes 'freedom of contract' because it serves their economic power. Understanding this is Marx's key to unmasking ideology.",

    "A 'positive right' requires someone to actively provide something to the rights-holder. Critics of positive rights argue they are problematic. Why?":
        "If you have a 'right to healthcare,' someone must provide it -- and compelling that provision infringes on their liberty. Negative rights (like the right not to be killed) require only that others leave you alone. Positive rights inevitably create conflicts between one person's right and another's freedom.",

    "What did Socrates mean by claiming that 'no one does wrong willingly'?":
        "Socrates believed that all wrongdoing is a form of ignorance. If you truly understood that honesty is better than dishonesty, you would always choose honesty. People do wrong because they mistake apparent goods for real ones -- they are confused, not evil.",

    "What is the 'appeal to authority' fallacy, and when is it NOT a fallacy?":
        "Citing an expert within their field of expertise is perfectly legitimate -- that is how we navigate a world too complex for any one person to understand. The fallacy occurs when the 'authority' has no relevant expertise, or when authority is used as a substitute for evidence.",

    "Kant's categorical imperative includes the 'formula of humanity': treat humanity, in yourself or others, never merely as a means, but always also as an end. What does this rule out?":
        "Kant's principle means you may never use a person as a mere tool for achieving some goal -- not even a noble goal. Slavery, forced labor, and sacrificing one person to save many all violate this principle. Every human being has inherent dignity that cannot be overridden.",

    "Popper's falsifiability criterion distinguishes science from pseudoscience. According to Popper, which of the following would make a theory genuinely scientific?":
        "A scientific theory must stick its neck out: it must predict specific, observable results that, if they do not occur, would prove the theory wrong. The willingness to be proven wrong is what distinguishes science from faith, ideology, and pseudoscience.",

    "What logical fallacy occurs when someone dismisses an argument by claiming the speaker is acting from self-interest?":
        "The genetic fallacy judges an idea by its source rather than its content. Even if someone argues for lower taxes because they would benefit personally, that does not make the argument wrong. A good idea is a good idea regardless of who proposes it or why.",

    "Popper's 'Open Society and Its Enemies' argued against 'historicism.' What is historicism as Popper defines it?":
        "Popper attacked the idea -- found in Plato, Hegel, and Marx -- that history follows inevitable laws toward a predetermined destination. This thinking, he argued, justifies totalitarianism: if history is heading somewhere inevitable, individuals can be sacrificed to hasten the journey.",

    "Edmund Burke defended tradition against the French Revolution. What was his philosophical argument for why inherited institutions deserve respect?":
        "Burke argued that society's institutions embody the accumulated wisdom of countless generations who tested them against reality. One generation's abstract reason cannot replace centuries of practical experience. Radical revolution destroys this inherited wisdom and produces chaos.",

    # ── Tier 4+ (selected key ones) ─────────────────────────────────────────

    "Who coined the term 'hard problem of consciousness'?":
        "David Chalmers introduced the term in 1995, distinguishing the 'easy problems' (how the brain processes information) from the 'hard problem' (why there is subjective experience at all). Science can map neural correlates of consciousness but cannot yet explain why physical processes feel like anything.",

    "What is 'qualia' in philosophy of mind?":
        "Qualia are the subjective qualities of experience -- the redness of red, the painfulness of pain, the taste of chocolate. You can describe light wavelengths and neural activity, but none of that captures what it is like to see red. That gap is the mystery of qualia.",

    "What is 'physicalism'?":
        "Physicalism holds that everything that exists is physical or depends on the physical. There are no souls, spirits, or non-physical minds. Consciousness, emotions, and thoughts are all ultimately physical processes in the brain. It is the dominant view in contemporary philosophy of mind.",

    "What is 'idealism' in philosophy?":
        "Philosophical idealism argues that reality is fundamentally mental or spiritual, not physical. Berkeley argued that material objects exist only as perceptions in minds. Hegel saw all of reality as the unfolding of Absolute Spirit. It may sound strange, but idealism has a long and distinguished history.",

    "What is Hobbes's 'state of nature'?":
        "Hobbes asked: What would human life be like without government? His answer was grim -- a 'war of every man against every man' where life is 'solitary, poor, nasty, brutish, and short.' This hypothetical state of nature justified surrendering freedom to a powerful sovereign.",

    "Foucault's 'panopticon' describes a prison where inmates cannot know when they are watched, so they self-regulate. What is Foucault's broader philosophical point about modern society?":
        "Foucault argued that modern institutions -- schools, hospitals, workplaces -- function like Bentham's panopticon. We internalize their surveillance and discipline ourselves. Power no longer needs whips and chains; it operates through norms, examinations, and the fear of being watched.",

    "What is Rawls's 'difference principle'?":
        "Rawls argued that economic inequalities are just only if they benefit the least advantaged members of society. A CEO earning millions is acceptable only if the system that produces that wealth also makes the poorest better off than they would be under any alternative arrangement.",

    "What is 'compatibilism' in philosophy?":
        "Compatibilism resolves the free will debate by redefining freedom. You are free when you act according to your own desires without external coercion, even if those desires were determined by prior causes. What matters is not the origin of your will, but whether you can act on it.",

    "What is the 'mind-body problem'?":
        "How does the mind relate to the brain? Is consciousness identical to neural activity, or is it something more? Can a purely physical brain produce subjective experience? The mind-body problem has been called 'the hardest problem in philosophy' and remains unsolved.",

    "What is Kant's 'transcendental idealism'?":
        "Kant argued that space and time are not features of reality itself but structures that our minds impose on experience. We can never know 'things in themselves' -- only things as they appear to us through the lens of our cognitive framework. This was his revolutionary 'Copernican turn' in philosophy.",

    "What is 'the hard problem of consciousness' as framed by David Chalmers?":
        "Why does physical processing in the brain produce subjective experience? Why does it feel like something to see red or taste coffee? We can explain how the brain processes information, but not why that processing is accompanied by consciousness. That is the hard problem.",

    "What is 'panpsychism'?":
        "Panpsychism holds that consciousness is a fundamental feature of the universe, present at every level of matter -- from electrons to ecosystems. It sounds exotic, but some contemporary philosophers argue it is the most promising solution to the hard problem of consciousness.",

    "What is Hegel's 'Aufhebung' (sublation)?":
        "Aufhebung is untranslatable because it means three things at once: to cancel, to preserve, and to lift up. When a thesis and antithesis produce a synthesis, the original ideas are cancelled as standalone positions, preserved as elements in the synthesis, and lifted to a higher level of understanding.",

    "What is 'the experience machine' thought experiment by Robert Nozick?":
        "Nozick asks: If you could plug into a machine that gives you any experience you want -- but none of it is real -- would you plug in? Most people say no. This suggests that we value more than just experiences: we want to actually do things, be certain kinds of people, and live in contact with reality.",

    "What is 'Chalmers's zombie argument'?":
        "Chalmers asks us to conceive of a being physically identical to you but with no inner experience -- a 'philosophical zombie.' If such a being is conceivable, then consciousness is not fully explained by physical facts. The argument challenges physicalism at its core.",

    "What is 'Nagel's bat argument' about consciousness?":
        "Thomas Nagel's 1974 paper 'What Is It Like to Be a Bat?' argued that even if we knew everything about bat neurology and echolocation, we could never know what it feels like to be a bat. Subjective experience cannot be fully captured by objective scientific description.",

    "Who proposed that science advances through 'paradigm shifts'?":
        "Thomas Kuhn's 'The Structure of Scientific Revolutions' (1962) argued that science does not progress through steady accumulation of facts but through revolutionary shifts -- from Ptolemy to Copernicus, from Newton to Einstein. These paradigm shifts change not just theories but the very questions scientists ask.",

    "What is Popper's 'falsificationism'?":
        "Popper argued that science does not progress by verifying theories but by attempting to falsify them. A theory that survives rigorous attempts at disproof is 'corroborated' but never proven. The moment a prediction fails, the theory must be revised or abandoned.",

    "Popper argued that Plato's ideal state in the 'Republic' was a blueprint for totalitarianism. What feature of Plato's state did Popper most object to?":
        "Popper saw Plato's philosopher-kings as a recipe for tyranny: a ruling class that claims to know the Good and subordinates all individual lives to the collective. For Popper, any system that claims to know the ultimate truth and imposes it on others is fundamentally dangerous.",

    "Nozick used the 'Wilt Chamberlain argument' to challenge Rawls's egalitarianism. What does this argument show?":
        "Imagine a perfectly equal distribution. If thousands of people freely choose to pay 25 cents to watch Wilt Chamberlain play, he ends up much richer. To maintain equality, the state must continually interfere with free choices. Nozick's point: equality and liberty are in fundamental tension.",

    "Hannah Arendt argued in 'The Origins of Totalitarianism' that both Nazism and Stalinism shared a defining feature. What was it?":
        "Arendt identified a distinctly modern form of evil: totalitarian regimes use ideology and terror to destroy people's capacity for independent thought and spontaneous action. They do not merely coerce behavior -- they aim to remake human nature itself.",

    "Arendt described the 'banality of evil' after observing Adolf Eichmann's trial. What philosophical claim does this phrase make?":
        "Eichmann was not a monster but a bureaucrat who 'just followed orders' without thinking about what those orders meant. Arendt's disturbing insight: the worst evils are often committed not by fanatics but by thoughtless people who fail to exercise moral judgment.",

    "The 'motte and bailey' fallacy?":
        "Named after a medieval fortification, this fallacy works by defending a bold, controversial claim (the bailey) but retreating to an obvious, defensible claim (the motte) when challenged. Once the challenge passes, the person advances the bold claim again. It is devastatingly effective in political rhetoric.",

    "Nietzsche rejected both Christian morality and utilitarianism as 'slave moralities.' What did he mean by this term?":
        "Nietzsche argued that 'slave moralities' arise when the weak redefine their weakness as virtue: humility, meekness, and self-sacrifice. The strong create values through action; the weak create values by resenting the strong. Christianity, he claimed, glorified suffering as a way for the powerless to feel superior.",

    "Hayek described the price system as a mechanism for transmitting information. What makes prices superior to central planning for allocating resources?":
        "A price captures enormous amounts of dispersed information in a single number. When copper becomes scarce, its price rises, telling millions of people to use less -- without any of them needing to know why. No central planner could process the information that prices transmit effortlessly.",

    "Hayek warned in 'The Road to Serfdom' that economic central planning leads to totalitarianism. What was his philosophical argument?":
        "Hayek argued that central planning requires ever-increasing coercion because people will not voluntarily follow the plan. As resistance grows, planners need more power to enforce compliance. The logic of planning inevitably favors those willing to use the most ruthless force.",

    "Nozick argued that taxation for redistribution is equivalent to forced labor. What is his philosophical argument for this claim?":
        "If the government takes 30% of your earnings to give to others, it is claiming ownership of 30% of your labor time. You worked those hours not for yourself but at the state's direction, for the state's chosen beneficiaries. That, Nozick argues, is structurally identical to forced labor.",

    "Popper's critique of Marx as a pseudoscientist rests on what observation about Marxist predictions?":
        "Marx predicted that revolution would occur in the most advanced industrial nations. When it happened in backward Russia instead, Marxists modified the theory rather than admitting it was wrong. A theory that explains every possible outcome, Popper argued, explains nothing.",

    "The 'economic calculation problem' (Mises-Hayek) holds that socialist central planning cannot work. What is the core argument?":
        "Without market prices for capital goods, central planners have no way to calculate the most efficient use of resources. Prices emerge from voluntary exchange -- but socialism abolishes voluntary exchange. Without the information prices provide, rational economic calculation is impossible.",

    "Alexis de Tocqueville warned of 'soft despotism' in democratic societies. What did he mean?":
        "Tocqueville foresaw a paternal government that 'covers the surface of society with a network of small, complicated rules.' It does not tyrannize -- it simply 'hinders, restrains, enervates, stifles, and stupefies' until the people are 'nothing better than a flock of timid and industrialized animals.'",

    "The 'is-ought gap' (Hume) and the naturalistic fallacy (G.E. Moore) both concern deriving values from facts. Why does this matter for collectivist political arguments?":
        "When someone argues that society 'naturally' functions as a collective and therefore individuals should sacrifice for the group, they are committing the naturalistic fallacy. Even if collectivism were 'natural,' that would not make it morally right. You cannot derive 'ought' from 'is.'",

    "The 'slippery slope' fallacy occurs when someone claims that one step inevitably leads to extreme consequences without justification. Which of the following is a legitimate philosophical concern, not a fallacy?":
        "Hayek's argument is not a fallacy because he provides a causal mechanism: economic planning creates institutional pressures that reward those willing to use force. Each step in the chain is explained, not merely asserted. The distinction matters enormously.",

    "What is the 'naturalistic fallacy' as identified by G.E. Moore, and how does it relate to collectivist political arguments?":
        "Moore showed that 'good' cannot be reduced to any natural property. Defining 'good' as 'what promotes social harmony' is just as fallacious as defining it as 'what produces pleasure.' Any attempt to reduce 'good' to something else commits this error.",

    "John Stuart Mill's 'On Liberty' argues that the only legitimate use of power over a free person is to prevent harm to others. What kind of authority does this argument limit?":
        "Mill recognized that social pressure can be as tyrannical as law. The majority's disapproval can silence dissent as effectively as a prison. His harm principle limits not only government coercion but the 'tyranny of prevailing opinion' that crushes individuality.",

    "Popper argued that the proper scientific method is not to verify theories but to try to falsify them. What is the name of the logical form that demonstrates why verification alone is insufficient?":
        "The problem of induction, identified by Hume, shows that no number of confirming observations can prove a universal claim. You could see a million white swans and still not prove 'all swans are white' -- but one black swan would disprove it. Falsification, not verification, is the engine of science.",

    "John Stuart Mill distinguished between 'higher' and 'lower' pleasures in his version of utilitarianism. What did he argue about intellectual versus physical pleasures?":
        "Mill argued that anyone who has experienced both will always prefer intellectual to physical pleasures. 'It is better to be Socrates dissatisfied than a fool satisfied.' This qualitative distinction rescued utilitarianism from the charge that it was a 'philosophy for swine.'",

    # ── Additional Tier 4 philosophy ────────────────────────────────────────

    "What is 'eliminative materialism'?":
        "Eliminative materialism makes a radical prediction: as neuroscience advances, our everyday mental vocabulary -- 'beliefs,' 'desires,' 'feelings' -- will be replaced by precise neural descriptions. Just as 'demonic possession' was replaced by mental illness, folk psychology will be replaced by brain science.",

    "Who proposed 'eliminative materialism'?":
        "Paul and Patricia Churchland, a married couple both teaching at UCSD, became the most prominent defenders of eliminative materialism. They argue that our commonsense understanding of the mind is a failed theory that neuroscience will eventually replace entirely.",

    "What is 'aesthetic formalism'?":
        "Formalism holds that a work of art should be judged solely by its formal properties -- composition, color, line, shape -- not by its subject matter, emotional content, or social context. Clive Bell's concept of 'significant form' captures this idea: art moves us through form alone.",

    "Who wrote 'The Phenomenology of Spirit'?":
        "Hegel published his 'Phenomenology of Spirit' in 1807, tracing consciousness's journey from simple sense-certainty to absolute knowledge. It is one of the most difficult and influential books in Western philosophy, describing how mind comes to understand itself through history.",

    "What is 'intersubjectivity'?":
        "Intersubjectivity refers to shared understanding between subjects -- the common ground that makes communication possible. Husserl asked how we know other minds exist; intersubjectivity is the space where individual perspectives overlap, creating a shared world of meaning.",

    "Who wrote 'The Social Contract'?":
        "Jean-Jacques Rousseau (1712-1778) opened 'The Social Contract' with the famous line: 'Man is born free, and everywhere he is in chains.' He argued that legitimate government must express the 'general will' of the people, an idea that inspired both democratic reformers and revolutionary tyrants.",

    "Who is associated with 'negative liberty'?":
        "Isaiah Berlin (1909-1997) made the distinction between negative and positive liberty famous in his 1958 lecture 'Two Concepts of Liberty.' His defense of negative liberty -- freedom from interference -- was shaped by his experience of totalitarian regimes that promised 'liberation' while crushing freedom.",

    "What is 'negative liberty'?":
        "Negative liberty is freedom from external constraints -- no one is stopping you from acting. It asks 'How much am I governed?' rather than 'Who governs me?' The Bill of Rights primarily protects negative liberties: the government shall not restrict speech, religion, or assembly.",

    "What is 'positive liberty'?":
        "Positive liberty is the capacity to fulfill your potential -- having the resources, education, and opportunities to act on your free will. Berlin warned that while positive liberty sounds appealing, it can justify paternalism: 'I know what you really need better than you do.'",

    "What is 'communitarianism'?":
        "Communitarians like Alasdair MacIntyre and Charles Taylor argue that liberalism's emphasis on the isolated individual ignores how communities shape identity and values. We are not blank slates choosing our values from scratch -- we inherit traditions, languages, and ways of life.",

    "What is 'formal logic'?":
        "Formal logic studies the structure of valid reasoning, abstracting away from content. It does not care whether your premises are about cats or quarks -- only whether the conclusion follows from the premises. It is the skeleton of all rational thought.",

    "Who invented modern formal logic?":
        "Gottlob Frege (1848-1925) created a symbolic language for logic in his 'Begriffsschrift' (1879) that went far beyond Aristotle's syllogisms. His system could express complex reasoning with mathematical precision and became the foundation for all modern logic and computer science.",

    "What is a 'tautology' in logic?":
        "A tautology is true no matter what -- like 'It is raining or it is not raining.' It tells you nothing about the world because it cannot possibly be false. While tautologies seem trivial, they reveal the deep structure of logical truth.",

    "What is 'modus ponens'?":
        "Modus ponens is the most basic rule of logical inference: if P implies Q, and P is true, then Q must be true. 'If it rains, the ground is wet. It is raining. Therefore the ground is wet.' Simple, but this pattern underlies all deductive reasoning.",

    "What is 'the problem of universals'?":
        "Do abstract properties like 'redness' or 'triangularity' exist independently, or are they just names we give to collections of similar things? Plato said universals are real (Forms); nominalists say only particular things exist. This debate has raged for over 2,000 years.",

    "What is 'nominalism'?":
        "Nominalists deny that abstract entities like 'justice' or 'redness' exist independently. Only particular things are real -- the word 'red' is just a name (nomen) we apply to similar-looking things. William of Ockham was the most famous medieval nominalist.",

    "What is the 'correspondence theory of truth'?":
        "The correspondence theory holds that a statement is true if it matches reality -- if it 'corresponds' to the facts. 'Snow is white' is true because snow really is white. It seems obvious, but defining what 'correspondence' means precisely has proven surprisingly difficult.",

    "What is the 'coherence theory of truth'?":
        "The coherence theory holds that a belief is true if it fits consistently with all our other beliefs. Truth is not about matching an external reality but about internal consistency within a system of beliefs. It appeals to those who doubt we can directly access reality.",

    "Who wrote 'Principia Mathematica' attempting to reduce math to logic?":
        "Bertrand Russell and Alfred North Whitehead spent ten years writing three massive volumes (1910-1913) proving that mathematics can be derived from pure logic. It took 362 pages to prove that 1+1=2. Godel later showed their project could not be completed.",

    "What is 'Hume's fork'?":
        "Hume divided all knowledge into two types: 'relations of ideas' (like math and logic, true by definition) and 'matters of fact' (empirical claims about the world). Anything that falls into neither category -- like metaphysics -- should be 'committed to the flames' as meaningless.",

    "What did Hume argue about causation?":
        "Hume argued that we never actually observe causation -- we only see one event followed by another. Our belief that the future will resemble the past is a habit of mind, not a logical necessity. This devastating insight challenged the foundations of science and philosophy.",

    "What is 'analytic philosophy'?":
        "Analytic philosophy, dominant in the English-speaking world, emphasizes logical rigor, clarity of language, and careful analysis of concepts. It grew from the work of Frege, Russell, and Wittgenstein and tends to tackle problems piece by piece rather than building grand systems.",

    "What is 'continental philosophy'?":
        "Continental philosophy, predominant in France and Germany, includes existentialism, phenomenology, hermeneutics, and critical theory. It tends to address big questions about human existence, history, and society. The analytic-continental divide has been called the deepest rift in modern philosophy.",

    "Who wrote 'The Birth of Tragedy' connecting Apollonian and Dionysian impulses?":
        "The young Nietzsche published 'The Birth of Tragedy' in 1872, arguing that Greek art emerged from the tension between the Apollonian (order, form, reason) and the Dionysian (chaos, passion, ecstasy). Great art requires both -- pure reason is sterile; pure passion is destructive.",

    "Who wrote 'On Liberty', defending freedom of speech?":
        "John Stuart Mill's 'On Liberty' (1859) is the most influential defense of individual freedom ever written. Mill argued that silencing any opinion -- even a false one -- is wrong because it robs society of the chance to strengthen truth through debate.",

    "What is 'moral psychology'?":
        "Moral psychology investigates the psychological mechanisms behind moral judgment. Why do we feel guilt? How do emotions influence ethical decisions? Recent research shows that moral intuitions often come first, and rational justifications follow -- we feel first, then reason.",

    "What is 'Leibniz's monadology'?":
        "Leibniz proposed that reality is composed of 'monads' -- simple, indivisible substances that are like tiny, windowless minds. Each monad reflects the entire universe from its own perspective. God chose to create this particular arrangement because it is 'the best of all possible worlds.'",

    "What does 'a fortiori' mean in philosophical argument?":
        "A fortiori reasoning says: if a stronger claim is true, then a weaker one must also be true. 'If you can lift 200 pounds, then a fortiori you can lift 100.' It is a powerful tool for extending arguments from harder cases to easier ones.",

    "What is the 'genetic fallacy' in logic?":
        "Judging an idea by where it came from rather than by its merits is the genetic fallacy. Dismissing a theory because its inventor was eccentric, or accepting it because it comes from a prestigious university, are both forms of this error. Ideas stand or fall on their own logic.",

    "What is 'ad hominem' in logic?":
        "An ad hominem attack targets the person making an argument rather than the argument itself. 'You only support free trade because you are rich' does not address whether free trade is actually beneficial. The character of the arguer is irrelevant to the validity of the argument.",

    # ── Tier 5 philosophy (remaining) ───────────────────────────────────────

    "What is 'Heidegger's concept of Dasein'?":
        "Dasein (literally 'being-there') is Heidegger's term for human existence. Unlike rocks or animals, humans are the beings for whom their own existence is an issue. We do not just exist -- we are always concerned about what our existence means.",

    "What is 'thrownness' in Heidegger's philosophy?":
        "Heidegger used 'Geworfenheit' (thrownness) to describe how we find ourselves already in a world we did not choose -- born into a particular time, culture, family, and body. We do not design our starting conditions; we must make something of what we have been thrown into.",

    "What is 'Husserlian epoche'?":
        "Husserl's epoche (Greek for 'suspension') means bracketing all assumptions about the external world to focus purely on the structures of experience itself. You set aside the question of whether a tree really exists and study how it appears in consciousness.",

    "What is 'intentionality' in phenomenology?":
        "Husserl argued that consciousness is always 'about' something -- perception is always perception of something, fear is always fear of something. This directedness of consciousness toward an object is intentionality. There is no consciousness that is not consciousness of something.",

    "Who developed 'speech act theory'?":
        "J.L. Austin (1911-1960) showed that language does not just describe the world -- it does things. When a judge says 'I sentence you,' or a couple says 'I do,' the words themselves perform actions. Austin distinguished between locutionary, illocutionary, and perlocutionary acts.",

    "What is a 'performative utterance'?":
        "When you say 'I promise,' 'I apologize,' or 'I name this ship the Queen Elizabeth,' you are not describing a pre-existing reality -- you are creating one. Austin called these performative utterances because the speaking itself is the action.",

    "What is 'structuralism' in philosophy?":
        "Structuralism holds that meaning does not come from individual elements but from the system of differences between them. A word means what it means not because of some intrinsic property but because of how it differs from other words. Language is a system of differences.",

    "Who is associated with structuralism in linguistics?":
        "Ferdinand de Saussure (1857-1913) revolutionized linguistics by arguing that language is a system of signs where meaning arises from differences between signs, not from any natural connection to reality. His ideas became the foundation for structuralism across the humanities.",

    "What is 'post-structuralism'?":
        "Post-structuralists like Derrida and Foucault argued that the stable structures the structuralists relied on are themselves unstable. Meaning is always shifting, power shapes knowledge, and binary oppositions (male/female, nature/culture) always privilege one term over the other.",

    "Who is the main figure associated with 'deconstruction'?":
        "Jacques Derrida (1930-2004) developed deconstruction to show how texts undermine their own apparent meanings. Every text contains contradictions and tensions that reveal hidden assumptions. Derrida did not destroy meaning -- he showed that meaning is always more complex than it appears.",

    "What is 'deconstruction'?":
        "Deconstruction reads texts against themselves, finding moments where the author's stated intentions are contradicted by the text's own logic. Derrida showed that Western philosophy rests on binary oppositions (speech/writing, presence/absence) that privilege one term while suppressing the other.",

    "What is Foucault's concept of 'power-knowledge'?":
        "Foucault argued that power and knowledge are inseparable -- power produces knowledge, and knowledge enables power. The prison creates criminology; the asylum creates psychiatry. What counts as 'knowledge' is always shaped by who has the power to define it.",

    "Who wrote 'Discipline and Punish'?":
        "Michel Foucault (1926-1984) traced how modern societies shifted from punishing bodies (public execution) to disciplining souls (surveillance, normalization). The prison, the school, and the hospital all use similar techniques to produce obedient, productive individuals.",

    "What is the 'panopticon' as used by Foucault?":
        "Jeremy Bentham designed the panopticon as a prison where guards can see every cell but inmates never know when they are being watched. Foucault used it as a metaphor: modern society functions like a panopticon, making us police ourselves through internalized surveillance.",

    "What is 'hermeneutics'?":
        "Hermeneutics began as the art of interpreting biblical and legal texts but became a general theory of understanding. How do we understand a text, a person, or a culture different from our own? The hermeneutic circle says we understand parts through the whole and the whole through the parts.",

    "Who is associated with 'philosophical hermeneutics'?":
        "Hans-Georg Gadamer (1900-2002) argued that all understanding is shaped by our historical situation -- our 'prejudices' (pre-judgments). Rather than obstacles, these are the conditions that make understanding possible. You cannot step outside your own horizon; you can only expand it.",

    "What is 'Gadamer's fusion of horizons'?":
        "Gadamer described understanding as a 'fusion of horizons' between reader and text. The reader brings their own historical perspective; the text carries another. Genuine understanding occurs when these horizons merge, creating something neither possessed alone.",

    "What is 'Wittgenstein's private language argument'?":
        "In the 'Philosophical Investigations,' Wittgenstein argued that a language only one person could understand is impossible. Language requires shared rules, and rules require a community to enforce them. A private sensation word with no public criteria for correct use has no meaning.",

    "What are 'language games' in Wittgenstein's later philosophy?":
        "The later Wittgenstein abandoned his earlier search for a single logical structure of language. Instead, he saw language as a collection of 'games' -- each with its own rules, embedded in particular forms of life. Asking for the 'real' meaning of a word outside its game is like asking what the 'real' rules of games are.",

    "What is 'Kripke's causal theory of reference'?":
        "Kripke argued that names refer to objects not through descriptions (like 'the philosopher who drank hemlock') but through a causal chain going back to an original 'baptism.' Someone named the baby 'Socrates,' and the name was passed down. Reference is a historical chain, not a description.",

    "Who wrote 'Naming and Necessity'?":
        "Saul Kripke delivered the lectures that became 'Naming and Necessity' in 1970 at Princeton -- without notes. The resulting book revolutionized philosophy of language by showing that some truths are necessary but known only through experience, overturning a centuries-old assumption.",

    "What is 'Quine's thesis of the indeterminacy of translation'?":
        "Quine asked: if you encounter a tribe that points at a rabbit and says 'gavagai,' does the word mean 'rabbit,' 'undetached rabbit part,' or 'rabbit stage'? He argued that all the evidence could support multiple translations equally well, so there is no single correct translation.",

    "What is 'the naturalistic fallacy' in ethics?":
        "G.E. Moore argued that defining 'good' in terms of any natural property (like pleasure, evolutionary fitness, or God's will) is a mistake. 'Good' is a simple, indefinable property. Whenever someone says 'good just means X,' you can always sensibly ask 'But is X good?'",

    "Who coined 'the naturalistic fallacy'?":
        "G.E. Moore (1873-1958) introduced the term in 'Principia Ethica' (1903). His 'open question argument' showed that for any proposed definition of 'good,' it is always meaningful to ask 'But is that really good?' -- proving that 'good' cannot be defined in terms of anything else.",

    "What is 'moral realism'?":
        "Moral realism holds that moral facts are as real as scientific facts -- they exist independently of what anyone thinks or feels. Murder is not wrong because we believe it is wrong; we believe it is wrong because it IS wrong. This view gives morality objective authority.",

    "What is 'error theory' in metaethics?":
        "J.L. Mackie's error theory makes a startling claim: all moral statements are false because they presuppose objective moral facts that do not exist. When we say 'murder is wrong,' we speak as if there are moral facts, but there are not. We are all systematically in error.",

    "Who proposed 'error theory' in ethics?":
        "J.L. Mackie (1917-1981) argued in 'Ethics: Inventing Right and Wrong' (1977) that moral properties are too 'queer' to fit into a naturalistic worldview. If moral facts existed, they would be utterly unlike anything else in the universe. Therefore, he concluded, they do not exist.",

    "What is 'emotivism' in metaethics?":
        "A.J. Ayer and Charles Stevenson argued that moral statements are not truth-claims at all -- they are expressions of emotion. 'Murder is wrong' really means something like 'Boo, murder!' This view strips morality of objective authority but explains why moral debates feel so passionate.",

    "What is 'supervenience' in philosophy of mind?":
        "Supervenience means that mental properties depend on and are determined by physical properties. Two beings identical in every physical respect must be identical in every mental respect too. It is a weaker claim than identity -- the mind depends on the brain but may not be reducible to it.",

    "Who wrote 'Simulacra and Simulation'?":
        "Jean Baudrillard (1929-2007) argued that in the modern age, images and signs have become more real than reality itself. We live in a 'hyperreality' of simulations with no original. The book famously appeared in 'The Matrix' and influenced the film's concept of simulated reality.",

    "What is a 'simulacrum' in Baudrillard's philosophy?":
        "A simulacrum is a copy that has no original. Baudrillard argued that modern culture produces endless copies -- of experiences, images, products -- that bear no relationship to any underlying reality. Disneyland, he said, exists to make us believe the rest of America is real.",

    "What is 'Lyotard's concept of the postmodern condition'?":
        "Jean-Francois Lyotard defined postmodernism as 'incredulity toward metanarratives' -- skepticism about the grand stories (Progress, Enlightenment, Marxism) that Western civilization tells to explain itself. In the postmodern era, no single story can claim universal authority.",

    "What is a 'metanarrative' in postmodern philosophy?":
        "Metanarratives are the big stories cultures tell to make sense of history -- 'History is progress,' 'God guides human affairs,' 'The proletariat will triumph.' Postmodernists argue these stories are not neutral descriptions but power structures that marginalize alternative voices.",

    "What is the philosophy of Emmanuel Levinas centered on?":
        "Levinas (1906-1995) argued that ethics -- responsibility to the Other -- is the foundation of all philosophy, not an afterthought. The face of another person makes an infinite ethical demand on us. Before we are thinkers, we are beings called to responsibility.",

    "What is 'apophatic theology'?":
        "Apophatic theology approaches God through negation -- saying what God is NOT rather than what God is. God is not finite, not material, not limited. Thinkers like Pseudo-Dionysius and Meister Eckhart argued that God so transcends human categories that only negative statements approach truth.",

    "What is 'Alain Badiou's concept of the event'?":
        "Badiou defines an 'event' as a radical break with the existing order that creates entirely new possibilities for truth. The French Revolution, the discovery of relativity, and falling in love are all events. They cannot be predicted from what came before -- they are genuinely new.",

    "What is 'object-oriented ontology'?":
        "Object-oriented ontology (OOO) argues that all objects -- from quarks to corporations to dreams -- have equal ontological status. Humans are not the center of being. A rock's relationship to the rain is just as philosophically interesting as a human's relationship to the world.",

    "What is 'speculative realism'?":
        "Speculative realism rejects the post-Kantian assumption that philosophy can only study the human-world relationship. It insists that reality exists independently of human thought and that philosophy can and should speculate about the nature of things-in-themselves.",

    "What is Hilary Putnam's 'twin earth' thought experiment about?":
        "Imagine a planet exactly like Earth, but where the clear liquid in rivers is XYZ instead of H2O. Putnam argued that 'water' on Earth means H2O and 'water' on Twin Earth means XYZ -- even if the inhabitants cannot tell the difference. Meaning, therefore, is not just in the head.",

    "What is 'Frankfurt's concept of freedom of will'?":
        "Harry Frankfurt argued that free will is not about having alternative possibilities -- it is about having the will you want to have. A person is free when their first-order desires (wanting to smoke) align with their second-order desires (wanting to want to be healthy).",

    "Who is associated with 'second-order desires' in philosophy of action?":
        "Harry Frankfurt distinguished between first-order desires (wanting coffee) and second-order desires (wanting to want coffee, or not wanting to want it). A drug addict may want drugs (first-order) but wish they did not want them (second-order). This conflict is the essence of unfreedom.",

    "What is 'epistemic injustice' in Miranda Fricker's work?":
        "Fricker identified injustice that occurs in our capacity as knowers. When someone is not believed because of their gender or race (testimonial injustice), or when a group lacks concepts to make sense of their experience (hermeneutical injustice), knowledge itself becomes a site of oppression.",

    "What is 'Judith Butler's concept of gender performativity'?":
        "Butler argued that gender is not an innate essence but something we 'perform' through repeated acts -- ways of walking, talking, dressing. There is no 'natural' gender behind the performance. Gender is constituted by the very expressions that are said to be its results.",

    "What is 'Gilles Deleuze's concept of the rhizome'?":
        "Deleuze and Guattari contrasted the rhizome (a root system that spreads horizontally, like grass) with the tree (a hierarchical structure). Knowledge, culture, and thought are rhizomatic -- they spread in multiple directions without a center or hierarchy.",

    "Who co-authored 'Anti-Oedipus' with Felix Guattari?":
        "Gilles Deleuze (1925-1995) and psychoanalyst Felix Guattari wrote 'Anti-Oedipus' (1972) to challenge Freudian psychoanalysis and capitalism simultaneously. They argued that desire is not about lack (as Freud claimed) but about production and creativity.",

    "What is 'the eternal recurrence' in Nietzsche's philosophy?":
        "Nietzsche asked: What if you had to live your exact life over and over, forever? Would you say 'Yes!' or recoil in horror? This thought experiment is the ultimate test of life-affirmation. The Ubermensch is the one who can embrace eternal recurrence with joy.",

    "What is 'Peirce's pragmatic maxim'?":
        "Peirce stated: 'Consider what effects, which might conceivably have practical bearings, we conceive the object of our conception to have.' In plain English: the meaning of a concept is the sum of its practical consequences. If two ideas have identical practical effects, they mean the same thing.",

    "What is 'inferentialism' in philosophy of language?":
        "Robert Brandom's inferentialism holds that the meaning of a sentence is determined by its role in reasoning -- what you can infer from it and what it follows from. Meaning is not about reference to objects but about inferential relationships between claims.",

    "Who is associated with inferentialism in contemporary philosophy?":
        "Robert Brandom (born 1950), building on Sellars and Wittgenstein, developed inferentialism in 'Making It Explicit' (1994). His work is one of the most ambitious attempts in recent philosophy to explain how language and thought work.",

    "What is 'the myth of the given' in Sellars's epistemology?":
        "Wilfrid Sellars attacked the idea that some experiences are 'given' directly to the mind without any conceptual interpretation. Even our most basic perceptions are shaped by concepts we have learned. There is no raw, uninterpreted 'given' at the foundation of knowledge.",

    "What is Axel Honneth's philosophy of recognition based on?":
        "Honneth argues that social struggles for recognition -- to be acknowledged as a person, a rights-bearer, and a contributor to society -- drive moral and political development. Disrespect and humiliation are not just unpleasant -- they damage people's ability to form a positive identity.",

    "What is 'moral particularism'?":
        "Jonathan Dancy argues that there are no fixed moral principles that hold in every situation. A feature that makes one action right (honesty) might make another action wrong (telling a murderer where their victim is hiding). Moral judgment requires sensitivity to context, not rule-following.",

    "Who is associated with 'moral particularism'?":
        "Jonathan Dancy (born 1946) has been the leading defender of moral particularism since the 1980s. His view challenges the entire tradition of moral philosophy that seeks universal principles, arguing instead for context-sensitive moral perception.",

    "Who wrote 'Reasons and Persons', a landmark work in population ethics and personal identity?":
        "Derek Parfit (1942-2017) published 'Reasons and Persons' in 1984. It changed how philosophers think about personal identity (the self is not what matters), future generations (we have obligations to people who do not yet exist), and rationality (self-interest is not always rational).",

    "What is 'the repugnant conclusion' in Derek Parfit's population ethics?":
        "Parfit showed that total utilitarianism implies that a world of billions of people whose lives are barely worth living is better than a world of millions of very happy people -- simply because the total happiness is greater. Most people find this repugnant, but it is hard to avoid without abandoning core utilitarian principles.",

    "What is 'effective altruism' in contemporary ethics?":
        "Effective altruism applies evidence and reason to maximize the good done by charitable giving. Instead of donating to whatever cause tugs your heartstrings, you should calculate where each dollar saves the most lives or prevents the most suffering. It is utilitarianism applied to philanthropy.",

    "Who is a key philosopher associated with effective altruism?":
        "Peter Singer (born 1946) argued in 'Famine, Affluence, and Morality' (1972) that if we can prevent suffering without sacrificing anything of comparable importance, we ought to do so. His work launched a movement that has redirected billions of dollars to the world's most effective charities.",

    "What is 'testimonial injustice' as described by Miranda Fricker?":
        "Testimonial injustice occurs when a speaker receives less credibility than they deserve due to prejudice -- when a woman's testimony is doubted because she is a woman, or a poor person's claim is dismissed because of their class. It is a wrong done to someone in their capacity as a knower.",

    "What is 'hermeneutical injustice' as described by Miranda Fricker?":
        "Hermeneutical injustice occurs when a group lacks the concepts to make sense of their own experience -- as when sexual harassment had no name, victims could not articulate what was happening to them. The gap in shared interpretive resources harms those who most need them.",

    "What is 'Nancy Fraser's concept of recognition'?":
        "Fraser argues that justice has two dimensions: redistribution (fair allocation of resources) and recognition (respect for identity). Focusing on redistribution alone ignores cultural oppression; focusing on recognition alone ignores economic inequality. Both are needed.",

    "What is 'mereology' in philosophy?":
        "Mereology studies the relationship between parts and wholes. When do parts compose a whole? Is a heap of sand one thing or many? Does the universe have parts, or is it one undivided whole? These questions connect to deep issues about identity and existence.",

    "What is 'counterfactual reasoning' in philosophy?":
        "Counterfactual reasoning asks 'What would have happened if...?' It is essential for understanding causation, moral responsibility, and science. If the match had not been struck, the fire would not have started -- therefore the striking caused the fire.",

    "What is 'modal logic'?":
        "Modal logic extends classical logic with operators for possibility and necessity. It asks: Is this claim merely true, or necessarily true? Could things have been otherwise? Modal logic is essential for analyzing philosophical arguments about free will, causation, and the nature of existence.",

    "What is the 'ontological argument' for God's existence?":
        "The ontological argument reasons from the concept of God to God's existence: God is the greatest conceivable being. A being that exists is greater than one that does not. Therefore, God must exist. The argument has fascinated philosophers for nearly 1,000 years.",

    "Who first formulated the ontological argument?":
        "Anselm of Canterbury (1033-1109) first stated the argument in his 'Proslogion.' A monk named Gaunilo immediately objected that the same logic could prove the existence of a perfect island. The debate over whether the argument works has continued ever since.",

    "What is the 'cosmological argument' for God's existence?":
        "The cosmological argument reasons that everything that exists has a cause. Since causes cannot go back infinitely, there must be an uncaused first cause -- which we call God. Thomas Aquinas gave the most famous version, but the argument dates back to Aristotle.",

    "What is the 'teleological argument' (argument from design) for God's existence?":
        "The world exhibits remarkable order, complexity, and apparent purpose. Just as a watch implies a watchmaker, the universe implies a designer. Darwin's theory of evolution provided a powerful naturalistic alternative, but the argument remains influential in philosophy of religion.",

    "What is 'Alvin Plantinga's reformed epistemology'?":
        "Plantinga argues that belief in God can be 'properly basic' -- rational without needing evidence or argument, just as our belief in other minds or the reliability of memory is basic. We do not need to prove God's existence any more than we need to prove the external world exists.",

    "What is 'the Chinese room's' implication about artificial intelligence?":
        "Searle's argument implies that no computer program, no matter how sophisticated, can genuinely understand language or think. A computer manipulates symbols according to rules but has no understanding of what the symbols mean. Syntax alone does not produce semantics.",

    "What does 'opacity of reference' mean in philosophy of language?":
        "In certain contexts (like belief reports), you cannot freely substitute co-referring terms. Lois Lane believes Superman can fly but does not believe Clark Kent can fly -- even though Superman IS Clark Kent. The context is 'opaque' to substitution.",

    "What is 'Quine's naturalism' in philosophy?":
        "Quine argued that philosophy is not a higher tribunal sitting in judgment of science. Philosophy should be continuous with science -- using the same methods and subject to the same standards of evidence. There is no 'first philosophy' that stands above empirical inquiry.",

    "What is 'the inscrutability of reference' in Quine's philosophy?":
        "Quine argued there is no fact of the matter about what our words refer to. 'Rabbit' could refer to rabbits, undetached rabbit parts, or temporal rabbit stages -- all are consistent with our evidence. Reference is indeterminate, not merely difficult to discover.",

    "What is 'thick ethical concepts' in Bernard Williams's philosophy?":
        "Thick concepts like 'cruel,' 'generous,' or 'courageous' blend description and evaluation. To call someone 'cruel' is both to describe their behavior and to condemn it. Williams argued that these concepts show the fact-value distinction is not as clean as philosophers assume.",

    "What is 'agent-relative reasons' in moral philosophy?":
        "An agent-relative reason is one that essentially refers to the person who has it. Your reason to care for YOUR children is agent-relative -- it applies to you because they are YOUR children. Not all moral reasons are universal; some are tied to particular relationships and commitments.",

    "What is 'philosophy of science' primarily concerned with?":
        "Philosophy of science asks: What makes science scientific? How do theories relate to evidence? What is the nature of scientific explanation? Is scientific knowledge objective or socially constructed? These questions matter because science is our most powerful tool for understanding reality.",

    "What is 'social epistemology'?":
        "Social epistemology studies how social factors shape knowledge. How does peer review work? Can groups be smarter than individuals? How does trust between knowers function? In an age of misinformation, understanding the social dimensions of knowledge has never been more important.",

    "What is 'feminist epistemology'?":
        "Feminist epistemology examines how gender shapes what counts as knowledge and who counts as a knower. It asks why women's experiences were historically excluded from philosophy and science, and how including diverse perspectives improves our understanding of reality.",

    "What is 'situated knowledge' in feminist philosophy?":
        "Donna Haraway argued that all knowledge is produced from a particular standpoint -- there is no 'view from nowhere.' Rather than being a limitation, acknowledging our situated perspective makes knowledge more honest and accountable than pretending to be objective.",

    "What is the central claim of existentialism?":
        "Sartre's famous formula -- 'existence precedes essence' -- means that humans have no predetermined nature or purpose. We are 'condemned to be free,' thrown into existence and forced to create ourselves through our choices. There are no excuses and no one to blame.",

    "What is Wittgenstein's 'private language argument'?":
        "Wittgenstein argued that a language only one person could understand is impossible. Meaning requires rules, rules require the possibility of following them correctly or incorrectly, and that requires a community. A purely private sensation-word has no standard of correctness.",

    "What does 'supervenience' mean in philosophy?":
        "If the physical facts about two situations are identical, then all the higher-level facts (mental, moral, aesthetic) must also be identical. Mental properties supervene on physical properties -- you cannot change the mind without changing the brain.",

    "What is Quine's critique of the analytic-synthetic distinction?":
        "In 'Two Dogmas of Empiricism' (1951), Quine attacked the idea that some truths are true by definition (analytic) while others depend on experience (synthetic). He argued that no statement is immune to revision -- all beliefs face experience together as a web.",

    "What is the 'Munchhausen trilemma'?":
        "Named after the Baron who pulled himself up by his own hair, the trilemma shows that any attempt to justify a belief leads to one of three dead ends: infinite regress (justification never ends), circularity (A justifies B which justifies A), or arbitrary axioms (we just stop somewhere).",

    "What is 'abductive reasoning'?":
        "Abduction, or inference to the best explanation, is how we reason in everyday life and science. Given a set of observations, we choose the hypothesis that best explains them. It is less certain than deduction but far more useful -- it is how discoveries are made.",

    "What did Foucault argue about 'discourse'?":
        "Foucault showed that discourse -- the rules governing what can be said and thought in a given era -- shapes reality rather than merely reflecting it. Medical discourse creates 'the patient,' legal discourse creates 'the criminal.' Language does not just describe power; it is power.",

    "What is 'transcendental idealism' according to Kant?":
        "Kant argued that space, time, and causality are not features of the world 'in itself' but forms that our minds impose on experience. We can never know things as they really are (noumena) -- only as they appear to us through these mental structures (phenomena).",

    "What is 'hard determinism'?":
        "Hard determinists accept that all events, including human decisions, are fully determined by prior causes -- and conclude that free will is an illusion. Since we could not have done otherwise in any situation, moral responsibility is a comforting fiction.",

    "Who developed 'speech act theory' in philosophy of language?":
        "J.L. Austin developed speech act theory, and John Searle later systematized and extended it. Austin showed that utterances do not just describe -- they promise, warn, command, and create. Searle classified these 'illocutionary acts' into five types.",

    "What is the 'Chinese Room' argument by Searle?":
        "Searle imagines following Chinese symbol-manipulation rules without understanding Chinese. The room passes the Turing test -- its outputs look intelligent -- but no understanding occurs. Searle concludes that running a program is not sufficient for genuine comprehension.",

    "What is 'thick ethical concepts'?":
        "Concepts like 'cruel,' 'brave,' and 'generous' are 'thick' because they combine factual description with moral evaluation. Calling someone 'cruel' describes their behavior AND condemns it. This challenges the idea that facts and values can be cleanly separated.",

    "What did Rawls call 'overlapping consensus'?":
        "Rawls recognized that citizens in a diverse society hold different comprehensive doctrines (religious, philosophical, moral). An overlapping consensus occurs when people of different views can agree on basic principles of justice -- each for their own reasons. Political stability requires this common ground.",

    "What is 'perspectivism' in Nietzsche?":
        "Nietzsche argued that there are no facts, only interpretations. Every claim to knowledge is made from a particular perspective shaped by one's psychology, culture, and will to power. Objectivity is not seeing from no point of view but seeing from as many perspectives as possible.",

    "What is 'reflective equilibrium' in ethics?":
        "Rawls described moral reasoning as a process of adjusting general principles and specific moral judgments until they cohere. If a principle yields an unacceptable conclusion, revise the principle. If a judgment contradicts a well-supported principle, reconsider the judgment. Morality is a work in progress.",

    "What is Nagel's argument in 'What Is It Like to Be a Bat'?":
        "Nagel argued that even complete knowledge of bat neurology would not tell us what echolocation feels like from the inside. Subjective experience has an irreducible first-person character that objective science cannot capture. This is the heart of the mind-body problem.",

    "What is 'epistemic injustice' as described by Miranda Fricker?":
        "Fricker identified two forms: testimonial injustice (being disbelieved due to prejudice) and hermeneutical injustice (lacking concepts to understand your own experience). Both are wrongs done to a person specifically in their capacity as a knower -- a uniquely philosophical form of injustice.",

    "What is 'coherentism' in epistemology?":
        "Coherentism holds that beliefs are justified not by resting on a foundation of basic beliefs (foundationalism) but by how well they cohere with one another. It is like a web where each strand supports and is supported by others. The whole web holds together even without a single anchor point.",

    "What is 'normative ethics'?":
        "Normative ethics asks: What moral rules should we follow? The three main answers are consequentialism (judge by outcomes), deontology (judge by rules and duties), and virtue ethics (judge by character). Each captures something important, and the debate between them continues.",

    "What is 'moral luck'?":
        "Bernard Williams and Thomas Nagel observed that factors beyond our control affect how we are morally judged. A drunk driver who kills a pedestrian is judged more harshly than one who gets home safely -- yet both made the same reckless choice. Luck should not affect moral judgment, yet it does.",

    "What is 'the principle of charity' in philosophy?":
        "The principle of charity says you should interpret others' arguments in their strongest, most reasonable form before critiquing them. Attacking a weak version of an argument (a straw man) proves nothing. Engaging the strongest version shows intellectual honesty and produces better philosophical discussion.",

    "What does Heidegger mean by 'thrownness'?":
        "We do not choose our birth, our body, our culture, our era, or our language -- we are 'thrown' into them. Heidegger's point is that existence is not something we design from scratch. We must work with the situation we have been thrown into.",

    "What is 'positivism' in the philosophy of science?":
        "Logical positivists like the Vienna Circle argued that only statements verifiable through observation or logic are meaningful. Metaphysical, ethical, and religious statements that cannot be empirically tested are literally nonsense. This radical view shaped 20th-century philosophy of science.",

    "What is the 'demarcation problem'?":
        "The demarcation problem asks: What distinguishes science from non-science? Popper's answer was falsifiability. Kuhn emphasized paradigms and puzzle-solving. The question matters enormously -- it determines what counts as legitimate knowledge and what gets dismissed as pseudoscience.",

    "What is 'the naturalistic fallacy' as defined by G.E. Moore?":
        "Moore argued that any attempt to define 'good' in terms of a natural property (pleasure, survival, God's will) commits a fallacy. For any proposed definition, you can always sensibly ask 'But is that really good?' -- the 'open question argument.' Good is indefinable.",

    "What is 'dialectical materialism'?":
        "Marx and Engels applied Hegel's dialectic to material conditions: history progresses through contradictions between economic forces (thesis) that generate opposition (antithesis) and resolve into new social formations (synthesis). Capitalism's contradictions, they argued, would inevitably produce communism.",

    "What is 'personal identity' concerned with in philosophy?":
        "What makes you the same person you were ten years ago? Your body's cells have been replaced, your beliefs have changed, and your memories may be unreliable. Is there a continuous 'self,' or are you a different person at each moment? Parfit argued that personal identity is not what matters.",

    "What is 'the bundle theory of the self' (Hume)?":
        "Hume looked inward for a 'self' and found only a stream of perceptions -- thoughts, feelings, sensations. He concluded there is no underlying 'I' holding them together. The self is just a bundle of experiences, like a river -- always flowing, never the same.",

    "What is 'strong AI' in philosophy of mind?":
        "Strong AI claims that a properly programmed computer does not just simulate thinking -- it actually thinks. It has genuine understanding, consciousness, and mental states. Searle's Chinese Room argument was designed specifically to refute this claim.",

    "What is 'the problem of other minds'?":
        "You know you are conscious because you experience it directly. But you cannot directly experience anyone else's consciousness. Other people might be philosophical zombies -- perfectly mimicking conscious behavior with no inner experience. We all assume other minds exist, but we cannot prove it.",

    "What is 'Marxist base and superstructure'?":
        "Marx argued that the economic 'base' (who owns the means of production, how work is organized) determines the 'superstructure' (law, politics, religion, art, philosophy). Ideas do not drive history -- material conditions do. Law and morality serve the interests of the ruling class.",

    "What is 'the regress problem' in epistemology?":
        "If every belief needs justification, and every justification needs further justification, we face an infinite regress. Foundationalists stop the regress with basic beliefs; coherentists say beliefs justify each other in a web; infinitists accept the regress. None of these solutions is fully satisfying.",

    "What is 'expressivism' in meta-ethics?":
        "Expressivism holds that moral statements do not describe facts but express attitudes. 'Stealing is wrong' does not state a fact about stealing -- it expresses disapproval, like saying 'Boo, stealing!' Modern expressivists like Simon Blackburn have developed sophisticated versions of this view.",

    "What is 'political philosophy' concerned with?":
        "Political philosophy asks the most fundamental questions about government: What justifies political authority? What rights do individuals have? What is justice? When, if ever, is revolution justified? These questions are not merely academic -- they determine how we organize our lives together.",

    "What is 'the paradox of the heap' (sorites paradox)?":
        "Remove one grain from a heap of sand. Still a heap? Remove another. And another. At some point it is clearly not a heap, but where was the boundary? The paradox reveals that many of our concepts have vague boundaries that resist precise definition.",

    "What is 'epistemic humility'?":
        "Epistemic humility means recognizing that you might be wrong. It does not mean lacking conviction -- it means holding your convictions with an awareness of your own fallibility. Socrates modeled it: the wisest person knows how little they know.",

    "What is 'compatibilism' about freedom?":
        "Compatibilists argue that being free means acting according to your own will without external coercion -- even in a deterministic universe. You are free when you do what you want to do, even if your wants were shaped by causes beyond your control.",

    "What did Plato argue about knowledge vs. belief?":
        "Plato distinguished knowledge (episteme) from mere belief (doxa) in the Theaetetus and Republic. Knowledge requires a 'true, justified account' -- you must believe something, it must be true, and you must be able to explain why it is true. Mere belief might be true by accident.",

    "What is 'value pluralism' as argued by Isaiah Berlin?":
        "Berlin argued that there are many genuine human values -- liberty, equality, justice, mercy -- that can genuinely conflict with no higher principle to resolve the tension. Life requires tragic choices between goods that cannot all be fully realized. There is no utopia where all values harmonize.",

    "What is 'the Gettier problem'?":
        "Gettier showed that justified true belief is not sufficient for knowledge. You might believe your colleague is in the office (justified by seeing their car), and they are (true), but the car belongs to someone else and your colleague came by bus. Your belief is justified and true -- but it is not knowledge.",

    "What is 'the original position' in Rawls's theory?":
        "Rawls imagines people choosing principles of justice from behind a 'veil of ignorance' -- not knowing their own talents, wealth, or social position. In this 'original position,' rational self-interest would lead everyone to choose fair principles, since anyone could end up at the bottom.",

    "What is 'the myth of the given' in Sellars?":
        "Sellars attacked the empiricist idea that some experiences directly 'give' us knowledge without any conceptual interpretation. Even seeing a red patch requires the concept 'red.' There is no purely non-conceptual foundation for knowledge -- concepts go 'all the way down.'",

    "What is 'process philosophy' as developed by Whitehead?":
        "Alfred North Whitehead argued that reality is not made of static substances but of processes -- events, experiences, becomings. A rock is not a thing but a very slow process. This view challenges the dominant substance-based metaphysics that has ruled Western philosophy since Aristotle.",

    "What is Wittgenstein's 'language games' concept?":
        "The later Wittgenstein saw language not as a single system with one set of rules but as a family of 'games,' each with its own rules embedded in particular ways of life. Scientific language, religious language, and poetic language are different games -- and confusing them causes philosophical problems.",

    "What is 'the principle of sufficient reason'?":
        "Leibniz stated that nothing happens without a reason -- every fact has an explanation. This principle drives scientific inquiry (why does this happen?) and supports the cosmological argument for God (why does the universe exist rather than nothing?). Some philosophers question whether the principle is self-evident.",

    "What is 'Frankfurt cases' in the free will debate?":
        "Harry Frankfurt imagined a neuroscientist who will intervene to make you choose A if you are about to choose B -- but you choose A on your own. You could not have done otherwise, yet you seem morally responsible. Frankfurt concluded that alternative possibilities are not required for moral responsibility.",

    "What is 'the linguistic turn' in 20th-century philosophy?":
        "In the early 20th century, many philosophers concluded that traditional philosophical problems were really problems about language. Instead of directly studying mind, reality, or morality, they analyzed the language used to talk about these things. Wittgenstein, Russell, and Carnap led this shift.",

    "What is 'the cosmological argument' for God's existence?":
        "The argument reasons backward from the existence of the universe: everything has a cause, and causes cannot regress infinitely, so there must be an uncaused first cause. Aquinas gave the most famous version, arguing that this first cause is what everyone calls 'God.'",

    "What is 'mereology'?":
        "Mereology studies how parts relate to wholes. When do parts compose a whole? Are you identical to the sum of your parts? If you replace all your parts one by one, are you still the same whole? These questions connect to personal identity, physics, and the nature of objects.",

    "What is 'the experience machine' thought experiment by Nozick?":
        "Nozick asks: Would you plug into a machine that gives you any experience you want, perfectly simulated? Most people say no, suggesting we value more than just experiences. We want to actually do things, actually be certain kinds of people, and live in contact with actual reality.",

    "What is 'dialetheism'?":
        "Dialetheism is the startling view that some contradictions are true. The liar sentence ('This sentence is false') might be both true and false simultaneously. Graham Priest has developed paraconsistent logics that can handle contradictions without everything collapsing into triviality.",

    "What is 'the explanatory gap'?":
        "Even if neuroscience perfectly maps which brain states correspond to which experiences, we still would not know WHY those physical processes feel like something from the inside. The gap between objective brain science and subjective experience is the explanatory gap.",

    "What is 'structural realism' in philosophy of science?":
        "Structural realism argues that science reveals the mathematical structure of reality but not its intrinsic nature. When scientific theories are overturned, the mathematical relationships often survive. What science captures is the relational structure of the world, not what things are 'in themselves.'",

    "What is 'the paradox of the knower'?":
        "Consider: 'This sentence is not known to be true.' If you know it, then it is true -- but it says it is not known, so you do not know it. If you do not know it, then it is true -- but can a true sentence be unknowable? The paradox reveals deep tensions in our concept of knowledge.",

    "What is 'thick description' in philosophy of social science (Geertz)?":
        "Clifford Geertz distinguished 'thin description' (recording what happened: 'he winked') from 'thick description' (interpreting what it meant in context: 'he was signaling conspiracy'). Understanding human behavior requires grasping the web of cultural meanings behind actions.",

    "Wittgenstein claimed the limits of my language are:":
        "Wittgenstein wrote in the Tractatus: 'The limits of my language mean the limits of my world.' If you cannot express something in language, you cannot think it. Language does not just describe our world -- it determines its boundaries.",

    "Locke argued property rights include a 'sufficiency proviso': one may appropriate from nature only if there is 'enough and as good left for others.' What philosophical purpose does this limitation serve?":
        "Locke's proviso prevents property rights from becoming a license to harm others. If you fence off the only water supply in a desert, you have not legitimately acquired property -- you have trapped people into dependence. Individual rights have limits where they begin to destroy others' ability to survive.",

    "Hobbes argued that in the social contract, people surrender natural liberty to a sovereign in exchange for security. How did Locke's social contract differ from Hobbes's?":
        "Hobbes demanded an absolute sovereign; Locke insisted on limited government. For Locke, government holds power in trust, not in ownership. If the government violates the people's natural rights, the trust is broken and the people may dissolve it. This distinction is the philosophical DNA of the American Revolution.",

    "Utilitarianism judges actions solely by their consequences for overall happiness. What is the main philosophical objection from a rights-based perspective?":
        "If torturing one innocent person would somehow make a million people happy, utilitarianism seems to approve. Rights-based theories insist that individuals have inviolable dignity that cannot be overridden by calculations of aggregate happiness. Some things are simply wrong, no matter the consequences.",

    "What is the 'motte and bailey' fallacy, common in philosophical and political debate?":
        "The fallacy is named after a castle with an easy-to-hold stone tower (motte) and a desirable but hard-to-defend courtyard (bailey). The debater advances a bold claim (bailey), retreats to an obvious one (motte) when challenged, then re-advances the bold claim once the challenge passes.",
}


def main():
    hist_path = os.path.join(SCRIPT_DIR, "questions", "history.json")
    phil_path = os.path.join(SCRIPT_DIR, "questions", "philosophy.json")

    # ── Load ──────────────────────────────────────────────────────────────
    with open(hist_path, "r", encoding="utf-8") as f:
        history = json.load(f)
    with open(phil_path, "r", encoding="utf-8") as f:
        philosophy = json.load(f)

    # ── Apply contexts ────────────────────────────────────────────────────
    h_added = 0
    for q in history:
        if "context" not in q and q["question"] in HISTORY_CONTEXTS:
            q["context"] = HISTORY_CONTEXTS[q["question"]]
            h_added += 1

    p_added = 0
    for q in philosophy:
        if "context" not in q and q["question"] in PHILOSOPHY_CONTEXTS:
            q["context"] = PHILOSOPHY_CONTEXTS[q["question"]]
            p_added += 1

    # ── Report missing ────────────────────────────────────────────────────
    h_missing = [q["question"] for q in history if "context" not in q]
    p_missing = [q["question"] for q in philosophy if "context" not in q]

    print(f"History:    {h_added} contexts added, {len(h_missing)} still missing")
    print(f"Philosophy: {p_added} contexts added, {len(p_missing)} still missing")

    if h_missing:
        print("\n-- Missing history questions --")
        for q in h_missing[:20]:
            print(f"  {q[:90]}")
        if len(h_missing) > 20:
            print(f"  ... and {len(h_missing) - 20} more")

    if p_missing:
        print("\n-- Missing philosophy questions --")
        for q in p_missing[:20]:
            print(f"  {q[:90]}")
        if len(p_missing) > 20:
            print(f"  ... and {len(p_missing) - 20} more")

    # ── Write ─────────────────────────────────────────────────────────────
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        f.write("\n")

    with open(phil_path, "w", encoding="utf-8") as f:
        json.dump(philosophy, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("\nDone. Files updated.")


if __name__ == "__main__":
    main()
