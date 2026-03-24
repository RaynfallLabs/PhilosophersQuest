#!/usr/bin/env python3
"""
Generate educational context paragraphs for economics and theology quiz questions.
For each question without a "context" field, adds one from the CONTEXTS dict below.
"""

import json
import os

# ---------------------------------------------------------------------------
# ECONOMICS CONTEXTS
# ---------------------------------------------------------------------------
ECON_CONTEXTS = {
    # ---- Tier 1 ----
    "What is money primarily used for?":
        "Before money existed, people had to barter -- imagine trading a cow for 47 loaves of bread and making change with a chicken. Money solves this by acting as a universal medium of exchange, a unit of account, and a store of value.",

    "If a toy is very rare and many kids want it, what usually happens to its price?":
        "This is the law of supply and demand in action. When Tickle Me Elmo dolls were scarce in 1996, parents paid hundreds of dollars for a $30 toy -- scarcity plus high demand always pushes prices up.",

    "What is the difference between a 'need' and a 'want'?":
        "Needs keep you alive -- food, shelter, water, basic clothing. Wants make life more enjoyable but you can survive without them. The tricky part is that what counts as a 'need' can shift with context: electricity wasn't a need in 1800, but try living without it today.",

    "What is barter?":
        "Barter is the oldest form of trade -- swapping goods directly, like trading fish for firewood. The catch is the 'double coincidence of wants': you need to find someone who has what you want AND wants what you have, which is why money was invented.",

    "What do you call money you receive for doing a job?":
        "Wages are compensation for labor, typically paid hourly or per task. The word comes from Old French 'wage,' meaning a pledge -- your employer pledges to pay you for the work you do.",

    "When more people want something than there is available, there is a:":
        "A shortage occurs when demand exceeds supply at the current price. Think of concert tickets selling out in minutes -- the venue has 20,000 seats but 200,000 fans want in.",

    "When there is more of something available than people want to buy, there is a:":
        "A surplus means supply exceeds demand. After Halloween, stores slash candy prices because they have mountains of it and not enough buyers -- that's a surplus being corrected by price drops.",

    "What is a budget?":
        "A budget is your financial game plan -- it maps out how much money comes in and where it goes. Even governments and Fortune 500 companies start with this basic tool, because without a plan, spending tends to outrun income.",

    "What does it mean to 'save' money?":
        "Saving means delaying consumption today so you have resources for tomorrow. It's the foundation of all investment -- every factory, school, and business that exists was built because someone chose not to spend everything they earned.",

    "What is a producer?":
        "Producers create the goods and services that consumers buy. A farmer growing wheat, a factory assembling phones, and a barber cutting hair are all producers -- they add value that people are willing to pay for.",

    "If a store has a sale and lowers its prices, what usually happens?":
        "Lower prices increase the quantity demanded -- this is the law of demand. Black Friday sales prove it every year: slashing prices draws enormous crowds and boosts sales volume dramatically.",

    "What is the name for the amount of money left over after paying all expenses?":
        "Profit is what remains after all costs are subtracted from revenue. It serves as the economy's signal flare -- high profits in an industry attract new competitors, while losses warn entrepreneurs to redirect resources elsewhere.",

    "What is a market?":
        "A market is anywhere buyers and sellers come together to trade. It can be a physical place like a farmers' market, or entirely virtual like eBay. The essential ingredients are buyers, sellers, and a way to agree on prices.",

    "Which of these is a service rather than a good?":
        "A haircut is something done FOR you, not a physical object you take home -- that makes it a service. Services now make up about 70% of the U.S. economy, far outweighing physical goods production.",

    "What is a good in economics?":
        "In economics, a 'good' is any tangible product -- something you can touch, store, and transfer. A pizza, a book, and a car are all goods. Contrast this with services, which are intangible actions performed for you.",

    "Why do countries trade with each other?":
        "No country can efficiently produce everything its people want. Saudi Arabia has oil but little farmland; Japan has technology but few natural resources. Trade lets each country focus on what it does best and swap for the rest.",

    "What happens to supply when the price of a product rises, assuming no other changes?":
        "Higher prices make production more profitable, so producers ramp up output. When oil prices spike, drilling companies fire up rigs that were too expensive to operate at lower prices -- supply follows profit incentives.",

    "What is the price of borrowing money called?":
        "Interest is the rental price of money. Just as you pay rent to use someone's apartment, you pay interest to use someone's savings. It compensates lenders for the risk of not getting their money back and for delaying their own spending.",

    "What is a coin or bill used as money called?":
        "Currency is the physical form money takes -- the bills in your wallet and coins in your pocket. The word comes from Latin 'currens,' meaning 'running' or 'flowing,' because currency is meant to circulate through the economy.",

    "If you spend more money than you earn, you have a:":
        "A deficit means your outflows exceed your inflows. Governments run deficits when tax revenue falls short of spending, and they cover the gap by borrowing -- which is why deficits add to the national debt.",

    "Which of these is an example of earning money?":
        "Mowing lawns for neighbors is exchanging your labor for payment -- the definition of earning income. Whether you're a CEO or a kid with a lawnmower, the principle is the same: provide value, receive compensation.",

    "What word describes how much of something is available for sale?":
        "Supply is the quantity of a good that producers are willing to sell at various prices. It's one half of the most fundamental relationship in economics -- supply and demand together determine market prices.",

    "What word describes how much of something people want to buy?":
        "Demand reflects consumers' willingness and ability to purchase a good at a given price. Note both conditions: you might want a Ferrari, but unless you can afford one, you don't count as part of the demand.",

    "When supply and demand are balanced, the price is called the:":
        "The equilibrium price is where the quantity buyers want to purchase exactly matches what sellers want to sell. It's the market's 'sweet spot' -- any other price creates either a shortage or a surplus that pushes back toward equilibrium.",

    "What is the name for money given to a business or person to be paid back later?":
        "A loan is borrowed money with strings attached -- you must repay the principal plus interest. Loans fuel everything from college educations to startup companies, making them one of the most powerful tools in economics.",

    "Why do banks pay people interest on savings accounts?":
        "Your deposit isn't just sitting in a vault -- the bank lends it out to homebuyers and businesses at a higher interest rate. The interest you earn is your share of the profit from those loans.",

    "What is an entrepreneur?":
        "Entrepreneurs spot opportunities and take financial risks to pursue them. They combine land, labor, and capital in new ways to create value. Famous entrepreneurs like Steve Jobs didn't just invent products -- they created entirely new markets.",

    "What does 'scarcity' mean in economics?":
        "Scarcity is the fundamental problem of economics: human wants are unlimited, but resources are finite. Even billionaires face scarcity -- they can't buy more time. Every economic system is ultimately an attempt to manage scarcity.",

    "What is the purpose of taxes?":
        "Taxes fund public goods that markets struggle to provide -- roads, courts, national defense, schools. The idea is that everyone chips in for services that benefit the whole community, since no individual could afford to build a highway alone.",

    "If a lemonade stand sells 10 cups at $1 each and spends $4 on supplies, what is the profit?":
        "Revenue ($10) minus costs ($4) equals $6 profit. This simple calculation is the heartbeat of every business on Earth, from a kid's lemonade stand to a multinational corporation.",

    "What does the word 'income' mean?":
        "Income is money flowing in -- from a paycheck, investments, rent, or a side hustle. Economists track national income to gauge how well an economy is performing, since more income generally means more goods and services produced.",

    "When a business sells goods for less than they cost to make, the business has a:":
        "A loss is the opposite of profit -- costs exceed revenue. Persistent losses signal that resources are being used inefficiently and should be redirected. It's the market's way of saying 'try something different.'",

    "What is the main reason people work?":
        "Work is how most people convert their time and skills into the money needed to buy goods and services. Economists view labor as one of the four factors of production alongside land, capital, and entrepreneurship.",

    "What is trade?":
        "Trade is the voluntary exchange of goods, services, or money between parties. It only happens when both sides expect to benefit -- the baker wants money more than bread, and the buyer wants bread more than money.",

    "If the price of apples rises, what would you expect consumers to do?":
        "The law of demand predicts that as price goes up, quantity demanded goes down. Consumers respond by buying fewer apples and perhaps switching to cheaper fruits like bananas or oranges -- this is the substitution effect in action.",

    "What is a bank?":
        "Banks are financial intermediaries -- they connect people who have extra money (savers) with people who need money (borrowers). By pooling deposits and lending them out, banks keep money working instead of sitting idle.",

    "What is meant by the 'price' of a good?":
        "Price is the amount of money a buyer must pay to acquire a good. It acts as a signal in markets: high prices tell producers 'make more of this' and tell consumers 'consider alternatives.'",

    "Which of the following best describes 'demand'?":
        "Demand isn't just desire -- it's desire backed by purchasing power. Millions of people might want a mansion, but demand only counts those who are willing AND able to buy one at a given price.",

    "What does it mean to 'invest' money?":
        "Investing means putting money to work today with the expectation of earning more in the future. Unlike saving (which preserves wealth), investing grows it -- but with the trade-off of risk.",

    "What is a 'salary'?":
        "A salary is a fixed amount paid per year or month regardless of hours worked. Unlike hourly wages, salaried workers get the same paycheck whether they work 40 hours or 60 -- for better or worse.",

    "What does 'revenue' mean for a business?":
        "Revenue is the total money a business receives from sales before subtracting any costs. It's the 'top line' on an income statement. Profit, by contrast, is revenue minus expenses -- the 'bottom line.'",

    "Goods brought into a country from abroad are called:":
        "Imports are goods or services purchased from foreign producers. The U.S. imports bananas from Central America because the tropical climate there makes growing them far cheaper than doing so domestically.",

    "Goods sent from one country to another are called:":
        "Exports are goods or services sold to foreign buyers. They bring money into the exporting country, which is why governments often promote exports as a path to economic growth.",

    "What is the name for the total amount you earn before any deductions?":
        "Gross income is your full earnings before taxes, insurance, and retirement contributions are taken out. If your paycheck seems smaller than expected, the difference between gross and net income is where the money went.",

    "What is the name for the money left after taxes and deductions are removed from your earnings?":
        "Net income is your take-home pay -- what actually hits your bank account. The word 'net' comes from the idea of what's left after everything has been filtered out, like fish caught in a net.",

    "If you can only afford one of two things you want, you face a:":
        "A trade-off forces you to choose, and the thing you give up is the cost of your choice. Every decision involves trade-offs because time, money, and resources are limited -- you can't have everything.",

    "What is an expense?":
        "An expense is money spent to buy something or cover a cost. In business, tracking expenses precisely is crucial because even a company with strong revenue will fail if expenses eat up all the income.",

    "A person who lends money to a bank by keeping it in a savings account is called a:":
        "A depositor trusts the bank to hold their money safely and pay it back on request. In return, the bank pays interest. Deposit insurance (like FDIC in the U.S.) protects depositors if the bank fails.",

    "What is a debit card?":
        "A debit card draws directly from your bank balance -- spend $20 and your account drops by $20 immediately. Unlike credit cards, you can't spend money you don't have, making debit cards a built-in budgeting tool.",

    "What is a credit card?":
        "A credit card is essentially a short-term loan for each purchase. If you pay the full balance each month, you pay no interest. But carry a balance, and interest rates often exceed 20% -- making that $50 dinner cost much more over time.",

    "Why is it important to comparison shop before buying?":
        "The same product can vary wildly in price across sellers. A 2-minute price check on your phone can save you 30% or more, because competition means some sellers always offer better deals than others.",

    "What does it mean when a product is 'on sale'?":
        "A sale temporarily lowers the price to attract more buyers. Retailers use sales strategically -- clearing out old inventory, drawing foot traffic, or competing with rivals during key shopping periods.",

    "What is a natural resource?":
        "Natural resources are materials from nature used in production -- timber, water, minerals, oil, fertile soil. They're one of the four factors of production and the reason geography has always shaped economic destiny.",

    "What are the four basic economic questions every economy must answer?":
        "Every society must decide what to produce, how to produce it, for whom to produce it, and how much to produce. Whether through markets, government planning, or tradition, these questions define an economy's character.",

    "What does a landlord receive in exchange for letting someone live in a property?":
        "Rent is the price of using someone else's property. In economics, rent is one of the four types of factor income -- alongside wages (labor), interest (capital), and profit (entrepreneurship).",

    "If a candy bar costs $1 today and $1.10 next year, this is an example of:":
        "That 10-cent increase represents 10% inflation. Over time, even modest inflation compounds dramatically: at 3% annual inflation, prices double roughly every 24 years.",

    "What is the term for the physical items people make and sell?":
        "Goods are tangible products -- you can drop them on your foot. They contrast with services, which are intangible actions. An economy produces both, and the mix between them shifts as countries develop.",

    "A farmer grows wheat and sells it to a mill. The farmer is acting as a:":
        "The farmer is a producer because they create a product that others want to buy. In the circular flow of economics, producers sell goods and services to consumers, and the cycle of money and products keeps the economy moving.",

    "What is competition in a market?":
        "Competition is the rivalry among sellers vying for the same customers. It's the engine of market efficiency -- when businesses compete, they lower prices, improve quality, and innovate to win your dollar.",

    "What is an incentive in economics?":
        "Incentives are the rewards and penalties that shape behavior. A tax break incentivizes investment; a fine discourages pollution. As economist Steven Landsburg put it: 'Most of economics can be summarized in four words: people respond to incentives.'",

    "Why does competition between sellers usually benefit consumers?":
        "When sellers compete, they must offer better prices, quality, or service to win customers. Without competition, a single seller can charge high prices and ignore quality -- which is why monopolies are regulated.",

    "What happens to the price of an item when demand for it falls and supply stays the same?":
        "With fewer buyers competing for the same goods, sellers must lower prices to attract purchases. It's like an auction in reverse -- when nobody's bidding, the price drops.",

    "What is the meaning of 'supply' in economics?":
        "Supply measures what producers are willing and able to sell at each possible price. It typically slopes upward: higher prices motivate more production because the potential profit is greater.",

    "When the cost to make a product rises, what often happens to its price?":
        "Higher production costs squeeze profit margins, so producers raise prices to maintain profitability. When oil prices surge, everything shipped by truck gets more expensive -- costs ripple through the entire supply chain.",

    "What are wages paid to a worker for?":
        "Wages compensate workers for their labor -- the time, effort, and skill they contribute to production. In a competitive market, wages tend to reflect a worker's productivity: the more value you create, the more you can command.",

    "What does 'debt' mean?":
        "Debt is money you owe. It can be a powerful tool (a mortgage builds equity) or a trap (high-interest credit card debt can spiral). The key distinction is whether the borrowed money generates returns greater than the interest cost.",

    "If a bakery makes 100 loaves but only sells 80, the remaining 20 are a:":
        "Those unsold loaves are a surplus -- supply exceeded demand at the current price. The bakery might discount them at closing time, donate them, or bake fewer tomorrow. Surpluses are a signal to reduce production.",

    "Which of these items would most likely be considered a luxury?":
        "A private yacht is a luxury good -- something people buy more of as their income rises dramatically. Luxuries have high income elasticity of demand, meaning their sales fluctuate sharply with economic booms and busts.",

    "What is the name for someone who risks their own money to start a business?":
        "An entrepreneur takes on financial risk in hopes of profit. The word comes from the French 'entreprendre,' meaning 'to undertake.' Entrepreneurship is considered the fourth factor of production alongside land, labor, and capital.",

    "A market economy relies on __________ to determine what goods are produced.":
        "In a market economy, consumer spending acts like a vote -- every dollar spent signals producers about what people value. Prices coordinate these millions of individual choices into a coherent system without any central director.",

    "What basic economic problem does every society face?":
        "Scarcity is the master problem: unlimited human wants crashing against limited resources. Whether a society uses markets, planning, or tradition, the core challenge is always the same -- how to allocate what's scarce.",

    "What happens to purchasing power when prices rise?":
        "Rising prices mean each dollar buys less -- your purchasing power shrinks. If your salary stays at $50,000 but prices double, you can only afford half of what you used to buy. That's why inflation matters to everyone.",

    "What is the role of a business in an economy?":
        "Businesses organize land, labor, and capital to produce things people want to buy. They're the engines of production and employment, transforming raw inputs into valuable outputs that raise living standards.",

    # ---- Tier 2 ----
    "What does GDP stand for?":
        "Gross Domestic Product is the single most-watched number in economics. It adds up the market value of every final good and service produced within a country's borders in a year -- the scoreboard of national economic performance.",

    "GDP measures:":
        "GDP captures total economic output -- every haircut, every car, every hour of legal advice. The U.S. GDP is roughly $28 trillion, meaning American workers and businesses produce that much value annually.",

    "What is inflation?":
        "Inflation is the silent thief of savings. When prices rise across the board, each dollar you hold buys less. A little inflation (1-2%) is considered normal, but runaway inflation has toppled governments from Weimar Germany to modern Venezuela.",

    "In a market economy, who makes most economic decisions?":
        "In a market economy, billions of daily choices by consumers and businesses -- not government committees -- determine what gets produced. Adam Smith called this decentralized coordination the 'invisible hand.'",

    "In a command economy, who makes economic decisions -- and what is the fundamental problem this creates?":
        "Central planners in a command economy face what Hayek called the 'knowledge problem': the information needed to allocate resources efficiently is scattered among millions of people and cannot be collected in one place. Prices in free markets aggregate this knowledge automatically.",

    "What type of economy combines elements of both market and command systems?":
        "Most real-world economies are mixed -- they rely on markets for most decisions but use government intervention for areas like education, defense, and regulation. The U.S., Germany, and Japan are all mixed economies with different blends.",

    "What is a traditional economy?":
        "In a traditional economy, your occupation, production methods, and trade patterns are inherited from your ancestors. These economies are stable and predictable but tend to resist innovation and change.",

    "What is a tariff?":
        "A tariff is a tax on imported goods that raises their price, making domestic products more competitive. While tariffs protect local producers, they raise prices for consumers -- essentially taxing citizens to subsidize specific industries.",

    "What is a trade deficit?":
        "A trade deficit means a country buys more from abroad than it sells. The U.S. has run a trade deficit for decades, importing more consumer goods than it exports, though it often exports services and investment capital in return.",

    "What is a trade surplus?":
        "A trade surplus means exports exceed imports, bringing net revenue into the country. China and Germany have historically run large surpluses, exporting manufactured goods worldwide.",

    "What is a savings account?":
        "A savings account pays you interest for depositing money, because the bank uses your deposits to fund loans. It's one of the safest places to park money, though the trade-off is typically lower returns than riskier investments.",

    "Simple interest on $100 at 5% per year for 2 years equals:":
        "Simple interest applies only to the original principal: $100 x 5% x 2 years = $10. Unlike compound interest, which earns interest on interest, simple interest keeps the calculation straightforward.",

    "What is a direct tax?":
        "Income tax is the classic direct tax -- you see exactly how much is taken from your paycheck. Direct taxes are transparent, which makes them politically unpopular but economically honest.",

    "What is an indirect tax?":
        "Sales tax is a common indirect tax: the store collects it from you and passes it to the government. Because it's baked into the purchase price, consumers often don't notice how much they're paying in total.",

    "What does 'interest rate' mean?":
        "The interest rate is the annual cost of borrowing expressed as a percentage. At 5% on a $1,000 loan, you'd owe $50 in interest per year. Interest rates are the price of time -- compensation for waiting to get your money back.",

    "What is the purpose of a central bank?":
        "Central banks like the Federal Reserve manage a nation's money supply and set benchmark interest rates. They're the economy's thermostat -- raising rates to cool inflation or lowering them to stimulate growth.",

    "What is unemployment?":
        "Unemployment means willing workers can't find jobs. It's measured as a percentage of the labor force. Some unemployment is inevitable (people between jobs), but high rates signal economic distress and wasted human potential.",

    "What is a subsidy?":
        "A subsidy is government money given to producers to lower costs or boost output. Farm subsidies, for example, keep food prices low but can distort markets by keeping inefficient producers afloat at taxpayer expense.",

    "When a government increases the money supply faster than economic output grows, what happens and why?":
        "More dollars chasing the same goods pushes prices up -- this is inflation. Milton Friedman captured it perfectly: 'Inflation is always and everywhere a monetary phenomenon.' It's why responsible money supply management matters.",

    "What is a recession?":
        "A recession is two consecutive quarters of shrinking GDP -- the economy literally gets smaller. Jobs disappear, businesses close, and consumer confidence plunges. The 2008 recession wiped out $13 trillion in American household wealth.",

    "What is the term for the total value of a country's exports minus its imports?":
        "The balance of trade is the difference between what a country sells abroad and what it buys. A positive balance (surplus) means more money flowing in; a negative balance (deficit) means more flowing out.",

    "What is an income tax?":
        "Income tax is the government's cut of your earnings. Most developed countries use progressive income taxes where higher earners pay higher rates, based on the idea that those who earn more can afford to contribute more.",

    "What does 'per capita' mean?":
        "Per capita means 'per person' -- from Latin 'per caput' (per head). GDP per capita divides total output by population, giving a rough measure of average living standards that's more meaningful than total GDP alone.",

    "What is the national debt?":
        "The national debt is the cumulative total of all government borrowing minus repayments. The U.S. national debt exceeds $34 trillion -- that's over $100,000 per citizen, all of which must eventually be repaid or rolled over.",

    "What does 'exchange rate' mean?":
        "The exchange rate tells you how much of one currency you can swap for another. If 1 USD = 0.92 EUR, an American tourist in Paris pays 92 euro cents for each dollar exchanged. Rates fluctuate constantly based on trade flows and investor confidence.",

    "Which of these is a consequence of deflation?":
        "When prices are falling, why buy today when things will be cheaper tomorrow? This 'wait and see' mentality reduces spending, which slows the economy further. Japan's 'Lost Decade' of the 1990s showed how devastating deflationary spirals can be.",

    "What is the function of money as a 'store of value'?":
        "Money lets you save purchasing power for later -- earn it today, spend it next year. But inflation erodes this function: a dollar saved in 1970 buys only about 13 cents worth of goods today.",

    "What is a budget surplus for a government?":
        "A budget surplus means the government collected more in taxes than it spent. Surpluses can be used to pay down national debt or saved for future downturns -- though politically, they're rare because spending is always popular.",

    "What is fiat currency, and why is it vulnerable to inflation in a way commodity money is not?":
        "Fiat money has value because the government says so, not because it's backed by gold or silver. This gives governments unlimited ability to create new money, which is why every fiat currency in history has experienced significant inflation.",

    "What is 'compound interest'?":
        "Compound interest earns interest on your interest -- it's exponential growth applied to money. Albert Einstein reportedly called it the 'eighth wonder of the world.' At 7% annual return, your money doubles roughly every 10 years.",

    "What is a free trade agreement?":
        "Free trade agreements remove tariffs and barriers between countries, letting goods flow more freely. NAFTA (now USMCA) eliminated most tariffs between the U.S., Canada, and Mexico, dramatically boosting trade among all three.",

    "What does it mean when a country has a 'comparative advantage' in a product?":
        "Comparative advantage means producing something at a lower opportunity cost -- not necessarily cheaper in absolute terms. Even if one country is better at making everything, both countries gain by specializing in what they're relatively best at.",

    "What is a stock?":
        "A stock is a tiny slice of ownership in a company. Buy one share of Apple and you literally own a piece of the world's most valuable company -- along with millions of other shareholders.",

    "What is a bond?":
        "When you buy a bond, you're lending money to a company or government in exchange for regular interest payments and eventual return of your principal. Bonds are generally safer than stocks but offer lower returns.",

    "What does 'standard of living' measure?":
        "Standard of living captures how well people live -- income, housing, healthcare, education, and leisure. It explains why GDP per capita in Switzerland ($90,000+) translates to a very different daily life than in nations with GDP per capita under $1,000.",

    "What is an embargo?":
        "An embargo is a government ban on trade with a specific country, usually for political reasons. The U.S. embargo on Cuba, lasting over 60 years, severely restricted the island's access to American goods and markets.",

    "What is a quota in trade?":
        "A quota caps the quantity of a good that can be imported. Unlike tariffs (which raise prices), quotas directly limit supply. Both protect domestic producers at consumers' expense, but quotas create artificial scarcity more visibly.",

    "What is private property in economics?":
        "Private property means individuals and businesses -- not the government -- own resources and decide how to use them. Secure property rights are consistently correlated with economic growth, because people invest more when they're confident they'll keep the returns.",

    "What is the 'opportunity cost' of a decision?":
        "Opportunity cost is the road not taken -- the value of your best alternative. If you spend an evening studying instead of working a $15/hour shift, the opportunity cost of studying is $15. Every choice has a hidden price tag.",

    "Which of these best describes 'economic growth'?":
        "Economic growth means the economy is producing more goods and services over time. When GDP rises, there's more wealth to go around -- though how it's distributed is a separate and fiercely debated question.",

    "What is the consumer price index (CPI) used to measure?":
        "The CPI tracks the price of a typical 'basket' of goods -- groceries, rent, gas, clothing. If the basket cost $100 last year and $103 this year, inflation was 3%. It's the most widely used inflation gauge in everyday life.",

    "What is gross national product (GNP)?":
        "GNP counts everything produced by a country's citizens, whether at home or abroad. A Japanese car factory in Ohio adds to U.S. GDP (produced within borders) but Japanese GNP (produced by Japanese-owned firms).",

    "If prices rise by 10% but your wage only rises by 5%, your real wage has:":
        "Your real wage fell because your purchasing power dropped. You got a 5% raise on paper, but prices jumped 10%, so you can actually afford about 5% less than before. This is why workers care about real wages, not just nominal ones.",

    "What is a minimum wage?":
        "The minimum wage is a legal price floor on labor. Supporters say it protects workers from exploitation; critics argue it prices low-skilled workers out of the market by making their labor more expensive than the value they produce.",

    "What is 'disposable income'?":
        "Disposable income is what's left after taxes -- the money you actually get to decide how to spend or save. It's the truest measure of a household's spending power and the key driver of consumer demand.",

    "What are 'exports' good for in an economy?":
        "Exports bring foreign money into the country, creating jobs and income for domestic workers. Germany's export-driven economy shows how a country can prosper by selling high-quality manufactured goods worldwide.",

    "What is 'economic interdependence'?":
        "No modern country is self-sufficient -- the iPhone alone requires components from over 40 countries. Economic interdependence means disruptions anywhere ripple everywhere, as the world learned during the COVID-19 supply chain crisis.",

    "What is a progressive tax system?":
        "In a progressive system, higher income brackets face higher tax rates. If you earn $50,000 you might pay 22%, but on income above $200,000 you pay 35%. The idea is that a dollar means less to a millionaire than to a minimum-wage worker.",

    "What is a flat tax?":
        "A flat tax charges everyone the same percentage -- if it's 15%, both the janitor and the CEO pay 15% of their income. Advocates praise its simplicity; critics argue it burdens lower earners more because they spend a higher share of income on necessities.",

    "What is deflation?":
        "Deflation is the opposite of inflation -- prices fall across the board. While cheaper goods sound great, deflation discourages spending and investment, can cause debt spirals, and is notoriously hard for central banks to reverse.",

    "What does the term 'fiscal year' refer to?":
        "A fiscal year is the 12-month period a government or business uses for accounting and budgeting. The U.S. government's fiscal year runs October to September -- which is why budget debates heat up every fall.",

    "What is a dividend?":
        "A dividend is a company sharing its profits with shareholders -- think of it as a thank-you check for owning the stock. Companies like Coca-Cola have paid dividends continuously for over 60 years.",

    "What is the role of the World Trade Organization (WTO)?":
        "The WTO is the global referee for international trade, settling disputes and enforcing rules among 164 member nations. Without it, trade conflicts would more often escalate into destructive tariff wars.",

    "What is the International Monetary Fund (IMF) best known for?":
        "The IMF acts as a financial emergency room for countries in crisis, providing loans in exchange for economic reforms. It was created at Bretton Woods in 1944 to prevent the kind of economic chaos that had fueled World War II.",

    "What does it mean to 'depreciate' in currency markets?":
        "When a currency depreciates, each unit buys less foreign currency. A weaker dollar makes American exports cheaper abroad (good for exporters) but makes imports more expensive (bad for consumers buying foreign goods).",

    "What is a current account deficit?":
        "A current account deficit means a country is spending more abroad than it earns from exports and other income. It's financed by attracting foreign investment -- essentially borrowing from the rest of the world.",

    "What is meant by 'economies in transition'?":
        "After the fall of the Soviet Union, former communist nations had to build market institutions from scratch -- private property laws, banks, stock markets. This wrenching transformation saw both spectacular successes (Poland) and painful struggles (Russia in the 1990s).",

    "What is a central bank's 'discount rate'?":
        "The discount rate is the interest rate the central bank charges when commercial banks borrow directly from it. It sets a floor for interest rates throughout the economy, because no bank will lend at less than its own cost of borrowing.",

    "What happens to exchange rates when a country raises interest rates?":
        "Higher interest rates attract foreign investors seeking better returns, so they buy the country's currency to invest there. Increased demand for the currency drives up its value -- this is why interest rate decisions move currency markets instantly.",

    "What is 'value added tax' (VAT)?":
        "VAT is collected at every stage of production, but each business only pays tax on the value it added. If a baker buys $2 of flour and sells $5 of bread, the VAT applies to the $3 of value added. Over 160 countries use VAT.",

    "What do economists mean by 'capital' as a factor of production?":
        "In economics, capital means tools, machines, and factories -- not money in the bank. A carpenter's saw, a farmer's tractor, and a factory's assembly line are all capital. Money is just how you acquire capital.",

    "What are the four factors of production?":
        "Land (natural resources), labor (human effort), capital (tools and machinery), and entrepreneurship (risk-taking organization). Every good ever produced required some combination of these four ingredients.",

    "What is a 'command economy'?":
        "In a command economy, the government decides what to produce, how much, and at what price. The Soviet Union was the largest experiment: central planners set targets for everything from steel output to shoe sizes.",

    "What is 'economic efficiency'?":
        "Economic efficiency means squeezing maximum output from minimum input -- no waste. An efficient economy produces exactly what people want using the fewest possible resources, leaving nothing on the table.",

    "What is meant by 'balance of payments'?":
        "The balance of payments is a country's financial ledger with the world -- tracking every dollar of trade, investment, and transfer crossing borders. By definition, it always balances: money going out is offset by money or assets coming in.",

    "When a government prints money to pay its debts, who is effectively being taxed?":
        "Printing money creates inflation, which erodes the purchasing power of every person holding that currency. Economists call this the 'inflation tax' -- it's invisible, regressive, and requires no vote to impose.",

    "Weimar Germany's hyperinflation in 1921-1923 destroyed middle-class savings. What was the main cause?":
        "The German government printed marks at a staggering rate to pay war reparations and domestic obligations. At its peak, prices doubled every few days -- workers were paid twice daily and rushed to spend before their money became worthless.",

    "Gresham's Law states 'bad money drives out good.' What does this mean in practice?":
        "When two currencies circulate at the same legal value but one has more intrinsic worth (say, silver content), people hoard the good money and spend the bad. This principle, named after Sir Thomas Gresham, has been observed since ancient Rome.",

    "When a government imposes a price ceiling on a good -- such as rent control -- what does economic theory predict will happen to the quality and quantity of that good?":
        "Price ceilings below market equilibrium create shortages because suppliers can't earn enough to justify production. New York City's rent control is a textbook example: cheap apartments exist on paper but are nearly impossible to find in practice.",

    "What does comparative advantage tell us about why free trade is beneficial even if one country can produce everything more efficiently than another?":
        "David Ricardo proved in 1817 that even a country superior in everything still gains by specializing in its strongest area. Both trading partners end up with more goods than they could produce alone -- it's one of the most counterintuitive yet powerful insights in economics.",

    "What happened to the purchasing power of the U.S. dollar between 1913 (when the Federal Reserve was created) and 2023?":
        "The dollar lost roughly 97% of its purchasing power, meaning $1 in 1913 has the buying power of about $30 today. This slow erosion is the cumulative effect of over a century of inflation under a fiat monetary system.",

    "Why does inflation disproportionately harm people on fixed incomes, retirees, and savers compared to debtors?":
        "A retiree living on $3,000/month watches that income buy less each year as prices rise. Meanwhile, a homeowner with a fixed mortgage repays it in dollars that are worth less over time. Inflation redistributes wealth from savers to borrowers.",

    "What is the 'broken window fallacy' identified by Frederic Bastiat?":
        "Bastiat showed in 1850 that a broken window doesn't help the economy: the glazier gains, but the shopkeeper loses money that would have been spent on something new. Destruction redirects spending -- it doesn't create new wealth.",

    "What does Adam Smith argue about the division of labor in 'The Wealth of Nations'?":
        "Smith's pin factory example is legendary: one worker making pins alone produces maybe 20 per day, but ten workers dividing the 18 steps of pin-making produce 48,000. Specialization is the single greatest multiplier of human productivity.",

    "When inflation is 8% per year, approximately how many years does it take for the purchasing power of money to be cut in half?":
        "The Rule of 72 gives a quick answer: divide 72 by the inflation rate. At 8%, it takes about 9 years for your money to lose half its value. This mental shortcut works for any growth or decay rate.",

    "If a government funds its spending by printing money rather than taxing, who bears the cost?":
        "Everyone who holds that currency pays through inflation -- the 'hidden tax.' Unlike income tax, which requires legislation and shows up on your paycheck, the inflation tax is imposed silently and hits the poorest hardest.",

    "What is the 'debasement' of currency mean historically?":
        "Roman emperors were notorious for debasement: gradually replacing silver in coins with cheaper metals while maintaining face value. Citizens eventually caught on, prices rose, and trust in the currency collapsed. Modern money printing is the digital equivalent.",

    "What is 'sound money' and why do Austrian economists consider it essential?":
        "Sound money holds its value over time because its supply cannot be arbitrarily increased. Gold served this role for millennia. Austrian economists argue that without sound money, governments inevitably inflate, distorting savings, investment, and economic planning.",

    # ---- Tier 2 (continued, new batch) ----
    "What is a market economy?":
        "In a market economy, supply and demand -- not politicians or planners -- determine prices and production. The beauty of the system is that no one needs to be in charge: millions of individual decisions coordinate themselves through the price mechanism.",

    "What is the law of demand?":
        "The law of demand is one of economics' most reliable rules: raise the price and people buy less. It works because consumers have alternatives, limited budgets, and declining marginal satisfaction from additional units.",

    "What is the law of supply?":
        "Higher prices lure more producers into the market because the potential for profit grows. When coffee prices spike, farmers plant more coffee trees -- supply responds to the incentive of higher revenue.",

    "What is interest rate?":
        "The interest rate is the cost of borrowing money, expressed as a percentage. It's one of the most powerful numbers in economics -- when the Fed changes rates by even 0.25%, it ripples through mortgage payments, business loans, and stock prices worldwide.",

    "What is the stock market?":
        "The stock market is where ownership shares of companies are bought and sold. It lets businesses raise capital from millions of investors and gives ordinary people a chance to participate in corporate profits and economic growth.",

    "What is purchasing power?":
        "Purchasing power measures what your money can actually buy. A salary of $50,000 goes much further in rural Kansas than in Manhattan because the cost of living differs dramatically -- that's purchasing power in action.",

    "What is division of labor?":
        "Division of labor means breaking work into specialized tasks. Adam Smith showed that a pin factory with each worker doing one step could produce thousands of times more pins than workers each making whole pins alone.",

    "What is barter's main disadvantage compared to money?":
        "Barter requires a 'double coincidence of wants' -- you need shoes and the shoemaker needs exactly what you produce. Money eliminates this problem by being universally accepted, which is why every advanced economy uses it.",

    "What does 'liquidity' mean in finance?":
        "Liquidity is how quickly you can convert an asset to cash without losing value. Cash is perfectly liquid; a house is illiquid (selling takes months). During financial crises, liquidity dries up and even good assets become hard to sell.",

    "What is a budget deficit?":
        "A budget deficit occurs when the government spends more than it collects in taxes. To fill the gap, it borrows by issuing bonds. Persistent deficits accumulate into national debt, which future taxpayers must service with interest payments.",

    "What is the difference between saving and investing?":
        "Saving parks money safely (bank account, low risk, low return). Investing puts money to work (stocks, real estate, higher risk, higher potential return). Both are crucial: saving provides security while investing builds wealth.",

    "What is a bond in finance?":
        "A bond is essentially an IOU. When you buy a government bond, you're lending the government money in exchange for periodic interest payments and return of your principal at maturity. Bonds are typically less risky than stocks.",

    "What is consumer confidence?":
        "Consumer confidence measures how optimistic people feel about the economy. When confidence is high, people spend and invest; when it crashes, they save and cut back. It acts as a self-fulfilling prophecy -- pessimism can cause the very downturn people fear.",

    "What does a bank do with the money you deposit?":
        "Banks lend out most of your deposits to other customers -- homebuyers, businesses, students. They pay you a small interest rate and charge borrowers a higher rate, earning the 'spread' as profit. That's the core of banking.",

    # ---- Tier 3 ----
    "What is a monopoly?":
        "A monopoly exists when one company is the sole supplier in a market. Standard Oil controlled 90% of U.S. oil refining by 1890, letting it dictate prices -- which is why antitrust laws were created to prevent such dominance.",

    "What is an oligopoly?":
        "An oligopoly is a market dominated by a few large players -- think of airlines, cell phone carriers, or car manufacturers. The few firms are so interdependent that each watches the others' pricing moves like hawks.",

    "In a perfectly competitive market, individual sellers are called:":
        "Price takers must accept the market price because they're too small to influence it. A single wheat farmer can't charge more than the going rate -- there are thousands of other farmers selling identical wheat.",

    "What is fiscal policy?":
        "Fiscal policy is the government's use of taxing and spending to steer the economy. Cut taxes to stimulate growth; raise spending to create jobs; do both simultaneously to run large deficits. It's politics meeting economics.",

    "What is monetary policy?":
        "Monetary policy is the central bank's toolkit: adjusting interest rates and money supply to control inflation and support growth. Unlike fiscal policy (which requires legislative action), monetary policy can be implemented quickly by a small committee.",

    "What is opportunity cost?":
        "Every choice has a hidden price: the next-best option you gave up. If you spend Saturday studying instead of working a $100 shift, the opportunity cost is $100. Good decision-makers always weigh what they're sacrificing.",

    "What is consumer surplus?":
        "If you'd pay $5 for a coffee but it costs $3, your $2 of consumer surplus is the deal you got. Added up across all consumers and products, consumer surplus measures the total 'bonus' buyers receive from market prices being lower than their maximum willingness to pay.",

    "What is producer surplus?":
        "If a farmer would sell corn for $2 but the market price is $3, that extra $1 is producer surplus. It's the reward producers receive above their minimum acceptable price, and it drives investment in production capacity.",

    "Which type of unemployment occurs when workers are between jobs?":
        "Frictional unemployment is the natural churn of the labor market -- people quitting to find better jobs, recent graduates job-hunting, or workers relocating. It exists even in the healthiest economies because matching workers to jobs takes time.",

    "Which type of unemployment occurs due to a mismatch between workers' skills and available jobs?":
        "Structural unemployment happens when industries evolve faster than workers can retrain. Coal miners displaced by renewable energy or factory workers replaced by robots face structural unemployment -- their old skills no longer match available jobs.",

    "Which type of unemployment rises during a recession?":
        "Cyclical unemployment tracks the business cycle: it rises in recessions as demand shrinks and companies lay off workers, then falls during expansions as businesses hire again. It's the type that fiscal and monetary policy most directly target.",

    "What is a natural monopoly?":
        "Some industries have such enormous upfront costs that only one firm can serve the market efficiently. Running two sets of water pipes to every house would be absurd -- that's why utilities are natural monopolies, often regulated to prevent price gouging.",

    "What is a cartel?":
        "A cartel is a group of competitors who secretly agree to fix prices or limit production. OPEC is the most famous example, coordinating oil output among producing nations. Cartels are illegal in most domestic markets because they harm consumers.",

    "What does 'price elasticity of demand' measure?":
        "Price elasticity tells you how sensitive buyers are to price changes. Insulin demand is inelastic (diabetics need it regardless of price), while vacation demand is elastic (a price hike makes people stay home).",

    "If demand is inelastic, a price rise will:":
        "When demand is inelastic, consumers keep buying even at higher prices, so total revenue rises. This is why governments tax cigarettes and gasoline heavily -- people pay the higher price rather than quitting or driving less.",

    "What is a 'sunk cost'?":
        "A sunk cost is money already spent that can't be recovered -- like a nonrefundable concert ticket. Rational decision-making ignores sunk costs, but humans are notoriously bad at this: we sit through terrible movies because 'we already paid for the ticket.'",

    "What is 'dead weight loss'?":
        "Deadweight loss is the economic value that vanishes when markets are distorted by taxes, price controls, or monopoly power. It represents transactions that would have benefited both buyer and seller but never happen.",

    "What does 'crowding out' mean in fiscal policy?":
        "When the government borrows heavily, it competes with private businesses for limited savings, pushing interest rates up. Higher rates discourage private investment -- the government's borrowing 'crowds out' the private sector.",

    "What is a contractionary monetary policy?":
        "Contractionary policy is the central bank hitting the brakes: raising interest rates and reducing the money supply to cool an overheating economy. It's painful in the short run (higher unemployment) but necessary to prevent runaway inflation.",

    "What is the multiplier effect in economics?":
        "One dollar of new spending creates more than one dollar of GDP because it circulates: your restaurant spending becomes the waiter's income, which becomes the grocery store's revenue, and so on. Each round of spending adds to total output.",

    "What is a public good?":
        "Public goods are non-excludable (you can't stop anyone from using them) and non-rivalrous (one person's use doesn't diminish another's). National defense is the classic example -- it protects everyone equally and can't be withheld from non-payers.",

    "What is a negative externality?":
        "A negative externality is a cost inflicted on bystanders -- factory pollution harming nearby residents who had no part in the transaction. The factory doesn't pay for the pollution, so it overproduces. Externalities are a key reason markets sometimes fail.",

    "What is a positive externality?":
        "When you get vaccinated, you protect not just yourself but everyone around you -- that's a positive externality. Because the vaccinator doesn't capture all the benefits, markets tend to under-provide goods with positive externalities.",

    "What is market failure?":
        "Market failure occurs when free markets produce too much of something bad (pollution) or too little of something good (education). It's the standard economic justification for government intervention, though the cure can sometimes be worse than the disease.",

    "What is the difference between microeconomics and macroeconomics?":
        "Micro zooms in on individual markets -- the price of coffee, a firm's hiring decisions. Macro zooms out to the whole economy -- GDP, inflation, unemployment. They're two lenses on the same reality, each revealing patterns the other misses.",

    "What does 'ceteris paribus' mean in economic analysis?":
        "Latin for 'all else being equal,' ceteris paribus lets economists isolate one variable at a time. 'If the price rises (ceteris paribus), demand falls' -- meaning assuming nothing else changes. Real life, of course, rarely holds still.",

    "What is the 'invisible hand' concept attributed to Adam Smith?":
        "Smith observed that a baker bakes bread not out of generosity but to earn a living -- yet society gets fed. The invisible hand is the idea that self-interest, channeled through competitive markets, produces outcomes that benefit everyone.",

    "What is vertical integration in business?":
        "When a company controls multiple stages of production -- like an oil company that drills, refines, and sells gasoline -- that's vertical integration. It reduces costs from middlemen but can also reduce competition in the supply chain.",

    "What is horizontal integration?":
        "Horizontal integration is when companies at the same level merge -- like two airlines combining. It increases market share and can create efficiencies, but regulators watch closely because fewer competitors often means higher prices.",

    "What does 'economies of scale' mean?":
        "The more you produce, the cheaper each unit becomes -- that's economies of scale. A factory making 1 million phones spreads its fixed costs (rent, equipment) over more units than one making 1,000, dramatically lowering per-unit cost.",

    "What is 'stagflation'?":
        "Stagflation combines the worst of both worlds: high inflation AND high unemployment. It defied Keynesian theory, which assumed the two couldn't coexist. The 1970s oil crises proved otherwise, forcing economists to rethink their models.",

    "What is the Lorenz curve used to show?":
        "The Lorenz curve plots cumulative income share against cumulative population share. A perfectly equal society would show a 45-degree line; the further the curve bows away from that line, the greater the inequality.",

    "What does the Gini coefficient measure?":
        "The Gini coefficient compresses the Lorenz curve into a single number from 0 (perfect equality) to 1 (one person has everything). Scandinavian countries score around 0.25; the U.S. is about 0.39; South Africa exceeds 0.60.",

    "What is a monopsony?":
        "A monopsony is a market with only one buyer -- the mirror image of a monopoly. A company town where one employer is the only option for workers is a classic monopsony; the employer can suppress wages because workers have nowhere else to go.",

    "What is 'price fixing'?":
        "Price fixing is when competitors secretly agree to set prices rather than competing. It's illegal in most countries because it robs consumers of the benefits of competition. Penalties can include billions in fines and prison time.",

    "What is a 'price floor'?":
        "A price floor sets a minimum price -- the government declares you can't sell below this amount. The minimum wage is a price floor on labor. When set above equilibrium, price floors create surpluses (in labor markets, that surplus is unemployment).",

    "What is a 'price ceiling'?":
        "A price ceiling caps how high a price can go -- rent control is the classic example. When set below market equilibrium, price ceilings create shortages because suppliers reduce supply while more consumers want the cheaper good.",

    "When a government sets a price ceiling below the market equilibrium for a good like housing, what historically results -- and why?":
        "Rent control in cities like New York and San Francisco has consistently produced housing shortages. Landlords let buildings deteriorate or convert them to condos, while waiting lists grow to years. As economist Assar Lindbeck said, rent control is 'the most efficient technique presently known to destroy a city -- except for bombing.'",

    "What is the Phillips curve?":
        "The Phillips curve suggests a trade-off: lower unemployment comes with higher inflation, and vice versa. It worked well in the 1960s but broke down during the 1970s stagflation, leading economists to distinguish between short-run and long-run versions.",

    "What is 'laissez-faire' economics?":
        "French for 'let do' or 'leave it alone,' laissez-faire argues government should step back and let markets self-regulate. Hong Kong under British rule is often cited as the closest real-world example, achieving spectacular growth with minimal intervention.",

    "What is an inferior good?":
        "Inferior goods are products people buy less of as their income rises -- instant noodles, bus tickets, or used clothing. Get a raise, and you trade up to restaurant meals, a car, or new clothes.",

    "What is a normal good?":
        "Normal goods are products people buy more of as their income rises -- dining out, vacations, electronics. Most goods are normal goods, which is why economic growth generally improves living standards.",

    "What is a substitute good?":
        "Substitutes are interchangeable alternatives -- Coke and Pepsi, butter and margarine. When the price of one rises, demand for the other increases as consumers switch. The more substitutes exist, the more elastic demand becomes.",

    "What is a complementary good?":
        "Complementary goods are used together -- printers and ink, cars and gasoline, hot dogs and buns. When the price of one rises, demand for its complement falls because the total cost of using both increases.",

    "What is the 'law of diminishing marginal utility'?":
        "The first slice of pizza when you're starving is heavenly; the eighth slice makes you sick. Each additional unit of the same good provides less satisfaction. This explains why people diversify their consumption rather than buying only one thing.",

    "What is structural unemployment?":
        "When coal plants close and miners can't easily become software engineers, that's structural unemployment. It's caused by fundamental shifts in the economy -- technological change, globalization, or industry decline -- and requires retraining, not just job searching.",

    "What is the full employment rate in economics?":
        "Full employment doesn't mean 0% unemployment -- it means only frictional and structural unemployment remain. In the U.S., economists estimate this 'natural rate' at roughly 4-5%. Below that, inflation tends to accelerate.",

    "What is 'diseconomies of scale'?":
        "Eventually, getting bigger makes things worse -- bureaucracy grows, communication breaks down, and decisions slow to a crawl. This is why massive corporations sometimes split into smaller units: beyond a certain size, bigger isn't cheaper.",

    "What does 'aggregate' mean in macroeconomics?":
        "Aggregate means 'total' -- aggregate demand is total spending by all consumers, businesses, government, and foreign buyers combined. Macroeconomics studies these totals rather than individual markets.",

    "Which market structure has the most competition?":
        "Perfect competition features countless sellers offering identical products with zero barriers to entry. Agricultural commodity markets come closest: no single wheat farmer can influence the global wheat price.",

    "What is the 'income effect' in consumer theory?":
        "When a price drops, your money goes further -- it's as if you got a raise. This increased real income lets you buy more of everything, including the cheaper good. The income effect is one of two forces behind the downward-sloping demand curve.",

    "What is a 'loss leader' strategy?":
        "Supermarkets sell milk below cost to get you through the door, betting you'll fill your cart with profitable items. Amazon used books as a loss leader for years, building a customer base before expanding into everything else.",

    "What is the 'tragedy of the commons'?":
        "When everyone can graze sheep on a shared field, each herder has an incentive to add more sheep -- until the field is destroyed. Overfishing, air pollution, and traffic congestion are all modern tragedies of the commons.",

    "What is the difference between a shortage and a scarcity?":
        "Scarcity is permanent and universal: there will never be enough of everything for everyone. A shortage is temporary and market-specific: it happens when price is too low and corrects when prices adjust. All shortages end; scarcity never does.",

    "What is the role of profit in a market economy?":
        "Profit is the economy's GPS -- it tells entrepreneurs where resources are needed most. High profits in an industry attract new entrants and investment; losses tell producers to redirect resources elsewhere.",

    "What is 'factor market'?":
        "Factor markets are where the ingredients of production are bought and sold. The labor market (where workers sell time), the land market (where property is leased), and the capital market (where money for investment flows) are all factor markets.",

    "What is 'perfect competition' characterized by?":
        "Perfect competition requires many small firms selling identical products with no barriers to entry and perfect information. No real market achieves this perfectly, but agricultural commodities and some financial markets come close.",

    # ---- Tier 3 (continued, new batch) ----
    "What is a monopolistic competition?":
        "Your neighborhood has dozens of restaurants, each slightly different -- that's monopolistic competition. Many sellers offer differentiated products, so each has a tiny bit of market power, but competition keeps profits modest.",

    "What is a regressive tax?":
        "A regressive tax takes a bigger bite from the poor than the rich. Sales tax is regressive because a low-income family spending 100% of income on taxable goods pays a higher effective rate than a wealthy family saving much of its income.",

    "What is the money supply?":
        "The money supply is the total amount of money circulating in an economy -- cash, checking accounts, and other liquid assets. Central banks control it through interest rates and open market operations, making it one of the most powerful levers in economics.",

    "What is the poverty line?":
        "The poverty line is the income level below which a household is considered unable to meet basic needs. In the U.S. (2024), it's roughly $15,000 for a single person. Globally, the World Bank uses $2.15/day as the extreme poverty threshold.",

    "What is venture capital?":
        "Venture capitalists fund promising startups in exchange for equity. They accept high failure rates because the occasional home run (Google, Facebook) delivers returns hundreds of times the original investment. VC fuels Silicon Valley's innovation engine.",

    "What is the difference between supply-side and demand-side economics?":
        "Supply-siders say 'help producers and growth follows' -- cut taxes and regulations. Demand-siders say 'help consumers spend and growth follows' -- stimulate spending with government programs. Most modern policy mixes both approaches.",

    "What is monetary base?":
        "The monetary base is the most fundamental layer of money: physical currency plus bank reserves at the central bank. Through fractional reserve banking, this base gets multiplied into a much larger total money supply.",

    "What is voluntary exchange?":
        "Voluntary exchange is the heart of market economics: both sides trade only because they expect to benefit. When you buy coffee, you value the coffee more than your $4, and the shop values your $4 more than the coffee. Both walk away better off.",

    "What is the difference between economic growth and economic development?":
        "Growth is more output (bigger GDP); development is better lives (education, health, freedom). A country can have GDP growth driven by resource extraction while its citizens remain poor and uneducated -- that's growth without development.",

    "Hayek argued that prices in a free market do something no central planner can replicate. What?":
        "Prices aggregate the dispersed knowledge of millions of people into a single number. When the price of lumber rises, it tells every builder, homebuyer, and alternative-material maker to adjust -- all without a single directive from a central office.",

    "The Austrian Business Cycle Theory (Mises/Hayek) says that central bank credit expansion causes recessions by:":
        "When central banks push interest rates below what savers and borrowers would naturally agree on, businesses launch projects that can't be sustained once rates normalize. The boom feels great, but the bust -- when reality catches up -- is the hangover.",

    "Stalin's collectivization of Soviet agriculture in the early 1930s caused a famine known as the Holodomor. Approximately how many people died in Ukraine alone?":
        "The Holodomor killed an estimated 3.5 to 5 million Ukrainians through man-made famine. Grain was seized from peasants to fund industrialization, while guards prevented starving villagers from leaving to find food.",

    "Mao Zedong's Great Leap Forward (1958-1962) collectivized Chinese agriculture and industry. What was the result?":
        "The Great Leap Forward caused the deadliest famine in human history. Local officials, terrified of punishment, wildly exaggerated grain yields. Based on these false reports, the government exported food while tens of millions starved.",

    "Venezuela nationalized its oil industry and expanded social programs under Hugo Chavez. By 2019 under Maduro, what had happened?":
        "Venezuela went from Latin America's richest country to a humanitarian catastrophe. Nationalization destroyed oil production efficiency, price controls emptied store shelves, and hyperinflation made the currency essentially worthless.",

    "Zimbabwe experienced hyperinflation peaking at 89.7 sextillion percent per month in 2008. What primarily caused this?":
        "After seizing productive farmland and redistributing it to political allies who couldn't farm it, agricultural output collapsed. The government printed money to cover the revenue shortfall, creating the most extreme hyperinflation the modern world has seen.",

    "Soviet central planners in the 1930s-1980s could not efficiently allocate resources despite having vast data. According to Hayek, why?":
        "The knowledge needed for efficient allocation isn't statistics in a database -- it's the moment-to-moment practical knowledge of millions of people about local conditions, fleeting opportunities, and personal preferences. Prices in free markets transmit this knowledge; no bureaucracy can replicate it.",

    "Friedrich Hayek's 'Road to Serfdom' (1944) argued that central economic planning inevitably leads to what?":
        "Hayek argued that planning the economy requires planning people's lives. Every exception and complaint requires more rules and enforcement, concentrating power until individual choice is extinguished. He wrote it as a warning to democracies flirting with socialism.",

    "What does Milton Friedman's statement 'inflation is always and everywhere a monetary phenomenon' mean?":
        "Friedman's point is that sustained price increases require sustained money supply growth. Supply shocks or corporate greed can cause one-time price jumps, but only persistent money creation keeps prices rising year after year.",

    "North Korea maintains central planning while South Korea operates a market economy. How does their GDP per capita compare?":
        "The two Koreas are perhaps the cleanest natural experiment in economic systems. Same people, same culture, same geography -- split in 1950. South Korea's GDP per capita is roughly $35,000; North Korea's is about $1,300. Markets made the difference.",

    "What is 'malinvestment' in Austrian economics?":
        "Malinvestment occurs when artificially cheap credit makes bad projects look profitable. Think of the 2000s housing bubble: easy money funded millions of mortgages to people who couldn't repay. When rates normalized, the whole edifice collapsed.",

    "Argentina has experienced repeated hyperinflation crises (1989, 2002, 2023). What pattern do economists observe in the cause?":
        "Argentina's recurring crises follow a grimly predictable pattern: government spends beyond its means, prints money to cover the gap, inflation spirals, the currency collapses, and savings are wiped out. The cycle restarts because the underlying spending addiction is never addressed.",

    "Historical price controls during wartime (e.g., World War II, Nixon's 1971 price freeze) consistently produced what outcome?":
        "Price controls always produce the same result: shortages and black markets. Nixon's 1971 wage and price freeze initially seemed to work, but within two years, shortages of meat, gasoline, and other goods proved that you can't legislate away the laws of supply and demand.",

    "What is the 'spontaneous order' concept in Austrian economics, associated with Hayek?":
        "Language, common law, money, and markets all emerged without anyone designing them. Hayek showed that complex social order can arise from individuals following simple rules and responding to local conditions -- no master plan required.",

    "The subjective theory of value (Austrian economics) holds that value is determined by what?":
        "Value isn't in the object -- it's in the eye of the buyer. A glass of water is nearly worthless at a river but priceless in a desert. This insight, developed by Carl Menger in 1871, overturned the labor theory of value that had dominated economics.",

    "Karl Marx's labor theory of value claimed that all value comes from labor. What is the main Austrian refutation?":
        "If labor determined value, a hole dug and filled in would be worth something. In reality, value depends on what buyers are willing to pay, which has nothing to do with how much effort went into production. A mudpie isn't worth a gourmet meal no matter how long you spent making it.",

    "Venezuela under Chavez imposed price controls on food and medicine. By 2015-2018, what had happened to these goods?":
        "Price controls below market rates made production unprofitable. Farmers stopped planting, factories stopped producing, and pharmaceutical companies withdrew from the market. Supermarket shelves stood empty while people scavenged for food in garbage.",

    "Bastiat's concept of 'the seen and the unseen' warns against what error in economic reasoning?":
        "A government jobs program creates visible employment (the 'seen'), but the taxes that fund it destroy invisible private-sector jobs that would have existed (the 'unseen'). Good economics requires considering both.",

    "When the U.S. government ran large deficits during the 2020-2021 pandemic and simultaneously expanded the money supply, what followed by 2022?":
        "The result was 9.1% inflation in June 2022 -- the highest in 40 years. Trillions in new spending met a supply-constrained economy, producing exactly the outcome monetary theory predicted: too much money chasing too few goods.",

    "What is the key difference between a market-determined interest rate and a centrally-set one?":
        "A market rate emerges from the actual savings and borrowing decisions of millions of people -- it reflects real time preferences. A centrally-set rate is an educated guess by a committee. When the guess is wrong, it creates booms, busts, and malinvestment.",

    "What is a 'negative real interest rate' and why is it problematic from a sound money perspective?":
        "When your savings account pays 2% but inflation runs at 5%, you're losing 3% of your purchasing power annually. Negative real rates punish savers, reward debtors, and push people into riskier investments just to break even.",

    "What is 'inflation targeting' as practiced by most central banks today, and what is a key criticism?":
        "Most central banks explicitly aim for 2% annual inflation. Critics note this means the central bank is deliberately planning to halve your money's value every 36 years -- making long-term savers the guaranteed losers.",

    "What is the connection between fiat money and the ability of governments to fight wars without directly taxing citizens?":
        "Before fiat money, kings had to levy visible taxes to fund wars -- and often faced resistance. Modern governments can print money to fund military adventures without asking voters, distributing the cost invisibly through inflation.",

    "What is 'regulatory capture'?":
        "Regulatory capture is when the foxes end up guarding the henhouse. Industries lobby regulators, hire them after retirement, and shape rules to favor incumbents and block competitors. The regulated industry captures its own regulator.",

    "Public choice theory (Buchanan/Tullock) applies economic analysis to government. What does it predict about politicians and bureaucrats?":
        "Public choice theory applies the same self-interest assumption to politicians that economics applies to everyone else. Politicians maximize votes; bureaucrats maximize budgets. Understanding this helps explain why government programs often serve special interests rather than the public.",

    "What is 'government failure' in economics?":
        "Just as markets can fail, so can government. Regulatory capture, pork-barrel spending, and bureaucratic inefficiency can make government intervention worse than the market imperfection it aimed to fix.",

    "What does empirical evidence show about the relationship between economic freedom (Heritage Index, Fraser Index) and prosperity?":
        "Decades of data from 160+ countries consistently show that economically freer countries are wealthier, healthier, and cleaner. The top quartile of economic freedom enjoys GDP per capita roughly eight times higher than the bottom quartile.",

    "What is the 'ratchet effect' in government spending?":
        "Government spending tends to ratchet up during emergencies but never fully ratchets back down. Programs created in wartime or recession develop constituencies that fight fiercely to preserve them. Each crisis leaves spending permanently higher.",

    "What is the 'seen vs unseen' principle applied to minimum wage laws?":
        "The teenager who gets a higher wage is visible; the teenager who never gets hired because the minimum wage exceeds their productivity is invisible. Both effects are real, but policy debates tend to focus only on the seen.",

    "What does economic history show about the effectiveness of tariffs in protecting domestic industries long-term?":
        "Protected industries rarely develop the competitiveness needed to stand on their own. Without the pressure of foreign competition, they stagnate. The U.S. steel tariffs of 2002 cost more jobs in steel-using industries than they saved in steelmaking.",

    "What happened in Ireland during the Great Famine (1845-1852), when the British government maintained free trade policies and continued exporting food from Ireland?":
        "While Ireland starved, ships loaded with grain, butter, and livestock left Irish ports for England. The famine illustrates that 'free trade' under politically distorted property rights can produce catastrophically unjust outcomes.",

    "What is the core insight of 'public goods' theory that justifies government provision?":
        "Markets undersupply public goods because free riders can enjoy them without paying. National defense, clean air, and street lighting benefit everyone equally, so individuals rationally wait for others to pay. Government solves this by taxing everyone.",

    "Economists distinguish between the 'seen' cost of government programs (budget line items) and the 'unseen' cost. What is an example of the unseen cost?":
        "Every tax dollar the government spends was a dollar a private citizen could have spent or invested. The productive activity that would have occurred -- the business started, the hire made, the innovation funded -- is the invisible opportunity cost.",

    "In 1971 President Nixon ended the Bretton Woods system by closing the gold window. What was the consequence for U.S. inflation?":
        "Freed from the discipline of gold convertibility, the Federal Reserve expanded the money supply aggressively. Inflation soared through the 1970s, peaking at 14.8% in 1980. It took Paul Volcker raising interest rates to 20% to finally break the spiral.",

    "What is the economic argument FOR allowing prices to rise during a natural disaster (disaster pricing or 'price gouging')?":
        "Higher prices after a hurricane signal 'bring supplies here' to every trucking company and supplier in the region. They also discourage hoarding -- you buy only what you need at $10/gallon for water instead of filling your pool. Price caps cause bare shelves.",

    "What economic principle explains why communist countries historically developed high-quality weapons while struggling to produce consumer goods?":
        "Central planning excels at concentrating resources on a single goal (weapons, space programs) but fails at coordinating the millions of diverse consumer goods an economy needs. Without price signals, planners couldn't know whether to produce shoes or shirts, let alone what sizes.",

    "What is Hong Kong's laissez-faire economic policy under John Cowperthwaite demonstrate between 1950 and 1997?":
        "Cowperthwaite refused to even collect GDP statistics, fearing they'd tempt bureaucrats to meddle. With low taxes, free trade, and minimal regulation, Hong Kong went from poverty to per-capita income rivaling Britain's in just four decades.",

    "What is the 'knowledge problem' as applied to modern healthcare pricing set by government or insurers?":
        "When patients don't see prices and providers don't compete on cost, healthcare spending spirals. An MRI costs $400 at one facility and $4,000 at another in the same city -- price opacity prevents the normal market forces that would correct such distortions.",

    "What did the repeal of the Corn Laws in Britain (1846) demonstrate?":
        "Britain's Corn Laws protected wealthy landowners by taxing grain imports, keeping bread expensive for the poor. Repeal opened Britain to cheap foreign grain, feeding workers better and freeing up income that fueled the Industrial Revolution's next phase.",

    "What is the 'concentration of benefits and dispersion of costs' problem in public choice economics?":
        "A sugar tariff might cost each American $5/year (dispersed and unnoticed) while giving sugar producers millions in extra profit (concentrated and worth lobbying for). This asymmetry explains why inefficient policies persist despite harming the majority.",

    "What is the 'time preference' theory in Austrian economics?":
        "You'd rather have $100 today than $100 next year -- that's time preference. Interest rates naturally reflect this preference. When central banks suppress rates below natural time preference, they trick entrepreneurs into thinking people are more patient than they really are.",

    # ---- Tier 4 ----
    "What is the primary tool of a central bank to control inflation?":
        "By raising the benchmark interest rate, a central bank makes borrowing more expensive throughout the economy. This slows spending, cools demand, and brings inflation down -- though the side effect is often higher unemployment in the short run.",

    "When a central bank raises interest rates, what typically happens to borrowing?":
        "Higher interest rates increase the cost of loans, so fewer people and businesses borrow. A family that could afford a house at 4% may not at 7%. This deliberate cooling effect is exactly how monetary policy fights inflation.",

    "What is quantitative easing?":
        "QE is the central bank's emergency tool: buying government bonds and other assets with newly created money to inject liquidity when interest rates are already near zero. The Fed used QE massively during 2008 and 2020, expanding its balance sheet by trillions.",

    "What is the reserve requirement for banks?":
        "Banks must keep a fraction of deposits on hand rather than lending everything out. If the reserve requirement is 10%, a bank with $1 million in deposits must keep $100,000 in reserve. The remaining $900,000 can be lent out, creating new money in the process.",

    "What is the money multiplier effect in banking?":
        "Through fractional reserve banking, a single dollar deposited can create several dollars of loans. With a 10% reserve requirement, $1,000 in deposits can eventually generate up to $10,000 in total deposits across the banking system.",

    "What does 'price elasticity of supply' measure?":
        "Supply elasticity measures how quickly producers can ramp up output when prices rise. A farmer can't grow more wheat overnight (inelastic in the short run), but a software company can instantly copy its product (highly elastic).",

    "If the price elasticity of demand for a good is -2, a 10% price rise causes quantity demanded to:":
        "Elasticity of -2 means quantity changes twice as much as price. A 10% price increase causes a 20% drop in quantity demanded. This is highly elastic demand -- consumers are very price-sensitive, likely because good substitutes exist.",

    "What is a business cycle?":
        "Economies don't grow in a straight line -- they expand, peak, contract, and bottom out in recurring waves. Understanding where you are in the cycle helps explain why some periods feel like boom times and others like busts.",

    "In which phase of the business cycle is unemployment typically lowest?":
        "At the peak of an expansion, businesses are producing at or near full capacity, hiring is strong, and unemployment bottoms out. But this is also when inflation pressures build, setting the stage for the next contraction.",

    "What is 'moral hazard' in economics?":
        "Moral hazard occurs when insurance (or bailouts) encourages riskier behavior. If you know the government will rescue failing banks, you take bigger risks with depositors' money. The 2008 'too big to fail' bailouts were a textbook example.",

    "What is 'adverse selection'?":
        "Adverse selection is the 'lemons problem': buyers can't tell good products from bad, so they only offer low prices. This drives quality sellers away, leaving only lemons. In health insurance, the sickest people are the most eager to buy coverage.",

    "What is the difference between nominal GDP and real GDP?":
        "Nominal GDP uses current prices, so it rises with inflation even if actual output hasn't changed. Real GDP strips out inflation, revealing whether the economy truly produced more stuff. It's the difference between a real raise and one eaten by rising prices.",

    "What is the GDP deflator?":
        "The GDP deflator converts nominal GDP to real GDP by adjusting for price changes. Unlike the CPI (which tracks a fixed basket of consumer goods), the deflator covers all domestically produced goods and services.",

    "What is 'hyperinflation'?":
        "Hyperinflation is inflation gone nuclear -- typically defined as 50%+ per month. In 1946 Hungary, prices doubled every 15 hours. Hyperinflation destroys savings, collapses trust in money, and has historically triggered political upheaval.",

    "Which country experienced hyperinflation in the early 1920s partly due to war reparations?":
        "Weimar Germany's hyperinflation saw the mark go from 4.2 per dollar in 1914 to 4.2 trillion per dollar by November 1923. Workers were paid twice daily and wheelbarrows of cash couldn't buy a loaf of bread. It radicalized German politics for a generation.",

    "What is a current account in a country's balance of payments?":
        "The current account records all flows of goods, services, income, and transfers with the rest of the world. A persistent deficit means a country is living beyond its export earnings and must attract foreign capital to fill the gap.",

    "What is the capital account in a balance of payments?":
        "The capital account tracks international transfers of capital assets -- foreign direct investment, portfolio investment, and loans. If a country runs a current account deficit, its capital account must show a surplus to balance the books.",

    "What is 'crowding out' in fiscal policy?":
        "When the government borrows to finance spending, it absorbs savings that would otherwise fund private investment. The resulting higher interest rates discourage business expansion -- the government's appetite for funds crowds out private borrowers.",

    "What is the marginal propensity to consume (MPC)?":
        "MPC measures what fraction of each extra dollar people spend rather than save. An MPC of 0.8 means 80 cents of every additional dollar is spent. The higher the MPC, the larger the multiplier effect of any new spending injection.",

    "If MPC = 0.8, what is the simple Keynesian spending multiplier?":
        "The multiplier is 1/(1-MPC) = 1/0.2 = 5. In theory, $1 of new government spending generates $5 of total GDP. In practice, the real-world multiplier is usually much smaller due to leakages like imports, savings, and taxes.",

    "What is the 'accelerator effect' in economics?":
        "A small increase in consumer demand can trigger a large increase in investment as firms rush to expand capacity. Conversely, a small decline in demand can cause investment to collapse. This amplification effect makes business cycles more volatile.",

    "What is 'purchasing power parity' (PPP)?":
        "PPP says exchange rates should eventually adjust so that identical goods cost the same everywhere. The Economist's 'Big Mac Index' compares burger prices worldwide to test this: if a Big Mac costs more in Norway than the U.S., the Norwegian krone may be overvalued.",

    "Which of the following is a leading economic indicator?":
        "New business orders and building permits predict where the economy is heading because they reflect confidence in future demand. By the time GDP data is published, it's already history. Leading indicators give early warning.",

    "What is 'creative destruction' in economics?":
        "Joseph Schumpeter coined 'creative destruction' to describe how innovation kills old industries while birthing new ones. The automobile destroyed the horse-and-buggy industry; smartphones killed film cameras. It's painful but essential for progress.",

    "What is a 'liquidity trap'?":
        "In a liquidity trap, interest rates are near zero and people hoard cash rather than spend or invest. The central bank pushes on a string -- creating more money doesn't stimulate the economy because nobody wants to borrow or invest. Japan faced this for decades.",

    "In microeconomics, what is 'total cost'?":
        "Total cost is the sum of fixed costs (rent, equipment -- they don't change with output) and variable costs (materials, labor -- they rise with output). Understanding this split is essential for pricing, production, and break-even decisions.",

    "What are 'variable costs'?":
        "Variable costs rise and fall with production volume. Raw materials, hourly wages, and shipping costs all increase when a factory produces more. They contrast with fixed costs that remain constant regardless of output.",

    "What are 'fixed costs'?":
        "Fixed costs don't change with production in the short run -- rent, insurance, management salaries. Whether a factory produces zero units or a million, these costs remain the same. They only become variable when you can close the factory entirely.",

    "What is 'profit maximization' for a firm?":
        "A firm maximizes profit by producing where marginal cost equals marginal revenue (MC = MR). Producing less leaves money on the table; producing more costs more than it earns. It's the sweet spot of economic decision-making.",

    "What is 'marginal cost'?":
        "Marginal cost is the price of making one more unit. The first few units may be cheap (excess capacity), but eventually costs rise as workers need overtime and machines strain. This U-shaped cost curve drives most production decisions.",

    "What is 'marginal revenue'?":
        "Marginal revenue is what you earn from selling one additional unit. In perfect competition it equals the market price; in a monopoly it declines with each unit because the seller must lower the price to sell more.",

    "In a perfectly competitive market, price equals:":
        "In the long run, competition drives price down to the minimum point on the average cost curve, where it equals marginal cost. Firms earn just enough to stay in business -- no more. This is why perfect competition delivers maximum efficiency for consumers.",

    "What is a speculative bubble?":
        "A bubble inflates when investors buy assets not for their underlying value but because they expect to sell at a higher price to someone else -- the 'greater fool theory.' The tulip mania of 1637, the dot-com bubble, and the 2008 housing bubble all followed this pattern.",

    "What does 'GDP per capita' measure?":
        "GDP per capita divides total economic output by population, giving a rough average of how much each person produces. It's the most commonly used proxy for living standards, though it hides inequality and non-market activities.",

    "What is 'economic rent' in economics?":
        "Economic rent is payment above the minimum needed to keep a resource in its current use. A superstar athlete earning $30 million when they'd play for $500,000 receives $29.5 million in economic rent. Rent-seeking tries to capture such payments without creating value.",

    "What is 'factor productivity'?":
        "Factor productivity measures how much output each unit of input generates. If a factory produces 100 widgets per worker per hour, that's its labor productivity. Rising productivity is the primary driver of long-term economic growth and higher living standards.",

    "What is the 'natural rate of unemployment'?":
        "The natural rate is the unemployment level when the economy is in balance -- only frictional and structural unemployment remain. Economists estimate it at 4-5% for the U.S. Pushing unemployment below this rate tends to spark inflation.",

    "What is 'demand-pull inflation'?":
        "Demand-pull inflation occurs when spending outpaces production capacity -- too much money chasing too few goods. Post-pandemic stimulus spending in 2021 is a textbook example: consumers had cash but supply chains couldn't deliver enough goods.",

    "What is 'cost-push inflation'?":
        "Cost-push inflation starts on the supply side: when oil prices spike, everything that uses oil gets more expensive. The 1973 OPEC embargo quadrupled oil prices, triggering inflation across the entire economy.",

    "What is 'aggregate demand'?":
        "Aggregate demand is the total spending in an economy: consumer purchases + business investment + government spending + net exports. When AD rises, the economy tends to grow; when it falls, recession looms.",

    "What is 'aggregate supply'?":
        "Aggregate supply is the total output firms are willing to produce at each price level. In the short run, higher prices boost production. In the long run, output depends on productive capacity -- technology, workforce, and capital stock.",

    "What does an increase in aggregate demand typically cause in the short run?":
        "When aggregate demand shifts right (more total spending), firms produce more and hire more workers, but they also raise prices. The economy gets a short-run boost in both output and inflation -- the classic trade-off.",

    "What is 'open market operations' by a central bank?":
        "Open market operations are the central bank's daily tool: buying government bonds injects money into the banking system (easing), while selling bonds withdraws money (tightening). It's the primary mechanism for controlling short-term interest rates.",

    "Which of the following would shift the aggregate demand curve to the right?":
        "A tax cut puts more money in consumers' pockets, increasing spending and shifting aggregate demand rightward. The same effect comes from increased government spending or lower interest rates -- anything that boosts total expenditure.",

    "What is the 'income effect' of a price change?":
        "When gas prices fall from $4 to $3, you save $50 a month -- that's like getting a raise. This increased real purchasing power lets you buy more of everything, not just gasoline. That's the income effect at work.",

    "What is the 'substitution effect' of a price change?":
        "When beef prices jump, consumers switch to chicken -- substituting the now-cheaper alternative. The substitution effect always pushes consumers away from the more expensive option toward cheaper alternatives.",

    "What is the 'long-run aggregate supply' (LRAS) curve?":
        "The LRAS curve is vertical because in the long run, an economy's output depends on its productive capacity (technology, labor, capital) not on the price level. Printing more money can't make a factory produce more widgets permanently.",

    "What is the 'multiplier effect' of a tax cut?":
        "A tax cut increases disposable income, which boosts consumer spending, which becomes income for businesses and their employees, who spend again. Each round of spending adds to GDP -- though each round is smaller than the last as some is saved or taxed.",

    "What is 'structural adjustment' in economics?":
        "Structural adjustment programs are the IMF's bitter medicine: cut government spending, privatize industries, open markets, and float currencies in exchange for emergency loans. They've been credited with stabilizing economies and criticized for causing severe short-term suffering.",

    "What is 'economic liberalization'?":
        "Economic liberalization means rolling back government controls -- deregulation, privatization, lower tariffs, and free capital flows. India's 1991 liberalization unleashed decades of rapid growth, transforming it from a stagnating economy to the world's fastest-growing major economy.",

    "What is a 'leading indicator' versus a 'lagging indicator'?":
        "Leading indicators (building permits, stock prices) forecast where the economy is heading. Lagging indicators (unemployment rate, corporate profits) confirm where it's been. Smart investors watch the leaders; policymakers often react to the laggers.",

    "What is the 'Laffer Curve' used to illustrate?":
        "The Laffer Curve shows that at 0% tax rates, revenue is zero, and at 100% tax rates, revenue is also zero (nobody works). Somewhere in between is a revenue-maximizing rate. The debate is where -- and moving past the peak means higher taxes produce less revenue.",

    "What is 'asymmetric information' in a market?":
        "When the seller of a used car knows about hidden engine problems but the buyer doesn't, that's asymmetric information. It leads to adverse selection, moral hazard, and market breakdown -- which is why warranties, inspections, and regulations exist.",

    "What is the 'velocity of money'?":
        "Velocity measures how fast money changes hands. If the total money supply is $1 trillion and GDP is $5 trillion, each dollar was spent 5 times. When velocity falls (people hoard cash), even increasing the money supply may not boost economic activity.",

    "What is the Fisher Effect?":
        "Irving Fisher showed that nominal interest rates adjust to expected inflation: if lenders expect 3% inflation, they add 3% to the real rate they'd otherwise charge. This keeps real returns stable even as inflation expectations shift.",

    "What is the difference between M1 and M2 money supply?":
        "M1 is the most liquid money: cash and checking accounts you can spend immediately. M2 adds savings accounts, small time deposits, and money market funds -- still accessible but with slight friction. The Fed tracks both to gauge monetary conditions.",

    "What is Gresham's Law?":
        "When governments fix two different monies at the same value, people hoard the better one and spend the worse one. In the Roman Empire, silver coins with high purity disappeared from circulation while debased coins were freely spent.",

    "What is the difference between nominal and real interest rates?":
        "If your savings earn 5% nominal interest but inflation is 3%, your real return is only 2%. Real interest rates reveal actual purchasing power gain. They can even go negative -- meaning your savings are losing real value despite earning nominal interest.",

    "What is the Heckscher-Ohlin theorem?":
        "The H-O theorem predicts that countries export goods that intensively use their abundant factors. Labor-rich China exports clothing; capital-rich Germany exports precision machinery. Trade patterns follow factor endowments.",

    "What is rent-seeking behavior?":
        "Rent-seeking is spending resources to capture wealth rather than create it -- lobbying for subsidies, tariff protection, or exclusive licenses. Every dollar spent on rent-seeking is a dollar not spent producing something valuable.",

    "What is the principal-agent problem?":
        "When you hire someone to act on your behalf, their interests may diverge from yours. A CEO (agent) may pursue empire-building rather than maximizing shareholder (principal) value. Aligning incentives through compensation design is the standard solution.",

    "What is adverse selection in economics?":
        "George Akerlof's 'Market for Lemons' showed how information asymmetry can destroy markets: if buyers can't distinguish good cars from bad, they offer low prices, driving good sellers away until only lemons remain.",

    "What is moral hazard?":
        "Moral hazard is the 'someone else pays' problem. Insured drivers may take more risks; bailed-out banks may make riskier loans. Whenever the person making a decision doesn't bear the full consequences, moral hazard lurks.",

    "What is the difference between a fixed and floating exchange rate?":
        "A fixed rate is pegged to another currency or gold -- the government promises to exchange at that rate. A floating rate fluctuates with market supply and demand. Fixed rates provide stability but can become unsustainable; floating rates adjust but create uncertainty.",

    "The Keynesian multiplier claims that $1 of government spending raises GDP by more than $1. What is a key empirical critique of this claim?":
        "Harvard economist Robert Barro found that the multiplier for peacetime government spending is often below 1.0, meaning the economy actually shrinks on net because government spending displaces more productive private activity. Crowding out and resource misallocation are the main culprits.",

    "What is the difference between absolute and comparative advantage?":
        "Absolute advantage means producing more efficiently in total; comparative advantage means producing at lower opportunity cost. Even if you're better at both cooking and cleaning than your roommate, you gain by splitting tasks based on relative strengths.",

    "What is a Veblen good?":
        "Named after economist Thorstein Veblen, these are luxury goods that people want MORE of at higher prices because the high price itself signals status. A $50,000 Rolex sells better than a $5,000 one precisely because it costs more.",

    "What is the Pigou effect?":
        "Arthur Pigou argued that falling prices increase the real value of people's cash holdings, making them feel wealthier and spend more. It's a self-correcting mechanism that theoretically pulls economies out of deflation without government intervention.",

    "What is perfect competition?":
        "Perfect competition is the economist's ideal: countless firms selling identical products with zero barriers and perfect information. It's a theoretical benchmark -- real markets never achieve it perfectly, but commodity markets approach it.",

    "What is the difference between microeconomic and macroeconomic equilibrium?":
        "Micro equilibrium is where supply meets demand in a single market (the price of apples). Macro equilibrium is where total output meets total spending across the entire economy. Both are about balance, just at different scales.",

    "What is the output gap?":
        "The output gap measures whether the economy is running above or below its potential. A negative gap (actual GDP below potential) means wasted resources and unemployment. A positive gap (above potential) signals inflationary overheating.",

    "What is economic rent?":
        "Economic rent is the payment a factor of production receives beyond what's needed to keep it in use. Prime Manhattan real estate earns enormous rent because its supply is fixed. Rent-seeking tries to capture such payments without creating new value.",

    "What is the efficiency wage theory?":
        "Henry Ford shocked the world in 1914 by doubling wages to $5/day. Workers flocked to Ford, turnover plummeted, and productivity soared. Efficiency wage theory explains why paying above market wages can actually lower costs through better performance and retention.",

    "What is the difference between contraction and expansion in business cycle terms?":
        "Expansion is the economy's upswing -- rising GDP, falling unemployment, growing confidence. Contraction is the downswing -- shrinking output, rising layoffs, falling consumer spending. Together they form the perpetual rhythm of economic life.",

    "What is the trade-off between inflation and unemployment described by?":
        "The Phillips Curve, named after economist A.W. Phillips who observed the pattern in UK data from 1861-1957. It suggests that when unemployment falls, wages (and thus prices) rise. The trade-off works in the short run but largely disappears in the long run.",

    "What is the difference between short-run and long-run in economics?":
        "In the short run, a factory can't build a new production line -- some inputs are fixed. In the long run, everything is variable: you can build, close, expand, or relocate. The distinction isn't about calendar time but about what you can change.",

    "What is price discrimination?":
        "Airlines are masters of price discrimination: the same seat can cost $200 or $2,000 depending on when you book, your flexibility, and your travel history. Sellers extract maximum revenue by charging different groups what they're willing to pay.",

    "What is the debt-to-GDP ratio used to measure?":
        "The debt-to-GDP ratio is like comparing what you owe to what you earn. A country with $20 trillion in debt and $25 trillion GDP has a ratio of 80%. Japan exceeds 260%; the U.S. recently surpassed 120%. Higher ratios raise questions about sustainability.",

    "What is capital deepening?":
        "Give workers better tools and they produce more -- that's capital deepening. When a construction company buys an excavator instead of handing workers shovels, output per worker skyrockets. It's a primary driver of productivity growth.",

    "What is the difference between gross and net investment?":
        "Gross investment is total spending on new capital. Net investment subtracts depreciation (the wear and tear on existing capital). If you buy a $50,000 truck but your old one lost $20,000 in value, net investment is $30,000.",

    "What is utility in economics?":
        "Utility is the satisfaction you get from consuming something -- an abstract measurement of happiness. Economists don't literally measure 'utils,' but the concept helps explain why people make the choices they do.",

    "Ludwig von Mises argued in 1920 that socialist central planning was theoretically impossible. What was his core argument?":
        "Without market prices for capital goods, planners cannot calculate whether resources are being used efficiently. Is it better to use titanium or steel for a bridge? Only market prices -- reflecting the competing demands of all users -- can answer this rationally.",

    "The Cantillon effect explains why quantitative easing (QE) tends to increase wealth inequality. What is the mechanism?":
        "New money flows first to banks and financial markets, inflating stock and real estate prices before wages adjust. Asset owners get richer while wage earners find their purchasing power eroded. By the time new money reaches ordinary consumers, prices have already risen.",

    "The Soviet Union's economy stagnated in the 1970s-80s despite full employment. What does this illustrate about central planning?":
        "Having everyone employed means nothing if they're producing the wrong things inefficiently. Soviet factories hit targets for tonnage of nails while producing nails nobody wanted. Without profit-and-loss signals, there's no way to know if work is productive.",

    "What did Murray Rothbard argue about fractional reserve banking?":
        "Rothbard contended that lending out depositors' money while promising full availability creates an inherent instability -- banks can never satisfy all withdrawal demands simultaneously. He advocated 100% reserve banking to eliminate this systemic fragility.",

    "When interest rates are set artificially low by a central bank, Austrian economists predict what will happen?":
        "Low rates make long-term projects look profitable when they really aren't. Builders start housing projects, companies expand capacity, and speculators leverage up -- all based on misleading price signals. When rates normalize, these investments collapse.",

    "Quantitative easing (QE) involves a central bank creating new money to buy assets. What is a key criticism from a sound-money perspective?":
        "QE funnels new money through financial markets first, inflating asset prices that primarily benefit the wealthy. Meanwhile, wages lag behind rising consumer prices. It's a wealth transfer mechanism disguised as neutral monetary policy.",

    "Mao's Great Leap Forward set grain production quotas far above actual yields, and local officials falsely reported meeting targets. What economic principle does this illustrate?":
        "Central planning creates perverse incentives to lie. Local officials who reported truth were punished; those who exaggerated were rewarded. The system's own logic guaranteed that decision-makers would act on fantasy rather than reality.",

    "Hayek won the 1974 Nobel Prize in Economics partly for his theory of business cycles. What was his main contribution?":
        "Hayek showed that credit expansion distorts the interest rate signal, causing entrepreneurs to invest as if society were more patient and savings-rich than it actually is. The inevitable correction -- the recession -- is the economy discovering and liquidating these errors.",

    "Between 1991 and 2000, former Soviet countries transitioned to market economies. Those that liberalized fastest (e.g., Poland, Estonia) versus slowest (e.g., Ukraine, Belarus) showed what pattern?":
        "Poland's 'shock therapy' caused sharp short-term pain but delivered rapid recovery and sustained growth. Ukraine's gradual approach prolonged the decline for a decade. The evidence strongly favored rapid, decisive market reforms over cautious half-measures.",

    "What is the Misesian critique of central bank interest rate setting?":
        "Mises argued that interest rates naturally reflect society's time preference -- how much people value present goods over future goods. When central banks override this natural rate, they create false signals that misdirect investment, inevitably producing economic crises.",

    "What is the 'denationalization of money' concept proposed by Friedrich Hayek?":
        "Hayek proposed that private banks issue competing currencies, letting consumers choose the most stable one. Bad currencies (those losing value) would be rejected, disciplining issuers through market competition rather than government monopoly.",

    "Cambodia under the Khmer Rouge (1975-1979) abolished money and markets, forcibly collectivized agriculture, and evacuated cities. The result was:":
        "The Khmer Rouge's attempt to create an agrarian communist utopia killed roughly a quarter of Cambodia's population. It stands as one of history's most extreme demonstrations that abolishing markets and private property leads to catastrophe.",

    "What is the 'interventionism' critique in Austrian economics (Mises)?":
        "Mises showed that each government intervention creates new problems that generate calls for more intervention. Rent control creates shortages, so governments impose construction mandates, which raise costs, leading to subsidies -- an ever-expanding spiral of control.",

    "The Soviet Union's economy eventually collapsed despite apparent full employment. What economic argument explains this?":
        "Full employment is meaningless if workers are producing unwanted goods inefficiently. Without market prices to signal value, the Soviet system accumulated decades of misallocated resources. When it finally opened to global comparison, the gap was staggering.",

    "What is the 'economic calculation problem' identified by Ludwig von Mises?":
        "Without private ownership and market prices for capital goods, socialist planners have no way to determine which production methods are efficient. Should they use aluminum or plastic? Build a factory here or there? Without prices, it's literally impossible to calculate.",

    "What is the 'knowledge problem' as applied to modern healthcare pricing set by government or insurers?":
        "When patients don't see prices and providers don't compete on cost, the dispersed knowledge about what healthcare should cost is never aggregated. The result is wild price variation, overuse of expensive procedures, and a system consuming 18% of U.S. GDP.",

    # ---- Tier 5 ----
    "What is the Prisoner's Dilemma in game theory?":
        "Two suspects in separate rooms each face a choice: betray the other or stay silent. Individually, betrayal is rational -- but if both betray, both get worse outcomes than if they'd cooperated. It elegantly explains why rational self-interest can produce collectively irrational results.",

    "In game theory, a 'Nash equilibrium' is:":
        "Named after John Nash (the subject of 'A Beautiful Mind'), it's a situation where no player can improve their outcome by changing strategy alone. It's the resting point of strategic interaction -- not necessarily optimal, but stable.",

    "What is the central claim of Classical economics?":
        "Classical economists from Smith to Ricardo believed markets self-correct: prices and wages adjust to clear markets without government help. Say's Law -- 'supply creates its own demand' -- was the cornerstone. Keynes later challenged this during the Great Depression.",

    "What is 'marginal utility'?":
        "Marginal utility is the extra satisfaction from consuming one more unit. It typically declines: the first bite of chocolate cake is divine; the tenth is nauseating. This declining curve explains why demand curves slope downward.",

    "What does the law of diminishing marginal utility state?":
        "Each additional unit of the same good provides less additional satisfaction. This principle, formalized independently by Jevons, Menger, and Walras in the 1870s, solved the water-diamond paradox and revolutionized how economists understand value.",

    "Who developed the theory of comparative advantage?":
        "David Ricardo proved in 1817 that trade benefits both parties even when one is better at producing everything. His wine-and-cloth example between England and Portugal remains one of the most elegant arguments in economics for free trade.",

    "What does comparative advantage say a country should do?":
        "Specialize in what you're relatively best at, not absolutely best at. If a doctor is also a faster typist than their secretary, the doctor should still practice medicine and hire the secretary -- because the doctor's time is more valuable treating patients.",

    "What does the Consumer Price Index (CPI) measure?":
        "The CPI tracks a specific basket of about 80,000 items that typical urban consumers buy. It's the government's primary inflation gauge and drives adjustments to Social Security, tax brackets, and millions of contracts indexed to inflation.",

    "What does the Producer Price Index (PPI) measure?":
        "The PPI tracks wholesale prices that producers receive -- it's a leading indicator of consumer inflation because rising production costs eventually get passed to shoppers. When PPI spikes, CPI usually follows within a few months.",

    "What was the Great Depression?":
        "The Great Depression (1929-1939) saw U.S. unemployment reach 25%, GDP fall by 30%, and global trade collapse by 65%. Its causes remain debated, but monetary contraction, bank failures, tariff wars (Smoot-Hawley), and policy errors all played roles.",

    "What did the Bretton Woods Agreement (1944) establish?":
        "Bretton Woods created a global monetary system where currencies were pegged to the U.S. dollar, which was convertible to gold at $35/ounce. It provided monetary stability for three decades until Nixon abandoned gold convertibility in 1971.",

    "What is 'rational expectations' theory?":
        "Rational expectations theory says people use all available information to make the best possible forecasts. If the Fed announces it will print money, people immediately expect inflation and adjust behavior, potentially neutralizing the policy's intended effect.",

    "What is 'monetary neutrality' in classical economics?":
        "Classical economists argued that doubling the money supply merely doubles prices -- real output, employment, and wealth remain unchanged in the long run. Money is just a veil over the real economy. This is why printing money can't create lasting prosperity.",

    "What is the Quantity Theory of Money?":
        "MV = PQ states that money supply times velocity equals price level times real output. If velocity and output are stable, increasing M (money supply) directly increases P (prices). It's the mathematical backbone of monetarism.",

    "Who wrote 'The General Theory of Employment, Interest and Money'?":
        "John Maynard Keynes published his 'General Theory' in 1936, arguing that insufficient demand -- not wage rigidity -- caused the Great Depression. His prescription of government spending to fill the demand gap became the foundation of modern macroeconomic policy.",

    "Who wrote 'The Wealth of Nations'?":
        "Adam Smith published 'The Wealth of Nations' in 1776, the same year as the Declaration of Independence. His insights about specialization, free trade, and the invisible hand laid the intellectual foundation for modern market economics.",

    "What economic concept did Milton Friedman champion?":
        "Friedman argued that the Federal Reserve's mismanagement of the money supply -- not market failure -- caused the Great Depression. His monetarism prescribed steady, predictable money supply growth rather than activist fiscal or monetary policy.",

    "What is 'human capital'?":
        "Human capital is the economic value of a person's skills, knowledge, and experience. A surgeon's decade of training represents an enormous human capital investment -- and explains why they earn more than someone without specialized skills.",

    "What is the Solow growth model primarily concerned with?":
        "Robert Solow's model shows that long-run growth comes from technological progress, not just adding more capital or labor. The surprising implication: countries that save and invest more grow faster initially, but all eventually converge to growth rates determined by technology.",

    "What is 'total factor productivity' (TFP)?":
        "TFP is the 'magic residual' -- the growth that can't be explained by more workers or more machines. It captures innovation, better management, and technological progress. TFP growth is the ultimate driver of rising living standards.",

    "What is 'behavioral economics'?":
        "Behavioral economics documents the systematic ways humans deviate from rational decision-making. We're loss-averse, anchored by irrelevant numbers, overconfident, and terrible at calculating probabilities. Daniel Kahneman won a Nobel Prize for mapping these 'predictably irrational' tendencies.",

    "What caused the 2008 financial crisis?":
        "Banks issued mortgages to borrowers who couldn't repay, bundled them into complex securities, and sold them worldwide. When housing prices fell, the entire chain unraveled. The resulting credit freeze nearly collapsed the global financial system.",

    "What is the 'cobweb model' in economics?":
        "The cobweb model explains price oscillations in markets with production lags. Farmers see high corn prices and plant lots of corn; next year's glut crashes prices; they plant less; the following year prices spike again. The cycle spirals toward or away from equilibrium.",

    "What is 'speculative demand for money' in Keynesian theory?":
        "Keynes argued people hold cash not just for transactions but to speculate on future interest rate changes. When rates are very low, people expect them to rise (bond prices to fall), so they hoard cash rather than buying bonds -- this is the speculative motive.",

    "What does the Human Development Index (HDI) measure?":
        "The HDI combines income, education, and life expectancy into a single score, capturing development beyond GDP. Norway consistently tops the list because it excels in all three dimensions, while some oil-rich nations rank lower due to poor education or health outcomes.",

    "What is 'supply-side economics'?":
        "Supply-siders argue that cutting taxes and regulations unleashes production, growing the economy so much that tax revenue may actually increase despite lower rates. Reagan's 1980s tax cuts are the most famous test case -- results remain hotly debated.",

    "What is Hayek's 'knowledge problem' -- the central insight of the Austrian School against central planning?":
        "Hayek's deepest insight is that the knowledge needed to run an economy is not scientific data sitting in files -- it's practical, local, and often tacit knowledge possessed by millions of people. Prices in free markets aggregate this dispersed knowledge; no central authority can.",

    "What is 'capital flight'?":
        "When political instability, high taxes, or currency devaluation threatens, investors rush their money out of the country. Capital flight devastated Argentina, Venezuela, and Russia during their respective crises, deepening the very problems investors were fleeing.",

    "What does the Arrow Impossibility Theorem state?":
        "Kenneth Arrow proved mathematically that no voting system can perfectly convert individual preferences into a fair group ranking while satisfying all reasonable criteria simultaneously. It's a humbling result: perfect democratic decision-making is logically impossible.",

    "What is the 'Washington Consensus'?":
        "The Washington Consensus was a set of 10 market-oriented reforms (fiscal discipline, trade liberalization, privatization) promoted by the IMF and World Bank in the 1990s. It helped some countries but was criticized for a one-size-fits-all approach to vastly different economies.",

    "What is 'hedging' in finance?":
        "Hedging is financial insurance -- taking an offsetting position to reduce risk. An airline that buys oil futures locks in fuel prices, protecting against spikes. The cost is that if prices fall, they don't benefit. It trades upside potential for downside protection.",

    "What is the 'paradox of value' (water-diamond paradox)?":
        "Water is essential for life yet cheap; diamonds are frivolous yet expensive. The resolution lies in marginal utility: water is abundant, so the last glass provides little extra satisfaction. Diamonds are scarce, so each one provides enormous marginal utility. Price reflects the margin, not total usefulness.",

    "What was the main purpose of the Marshall Plan (1948)?":
        "The Marshall Plan pumped $13 billion ($170 billion in today's dollars) into war-ravaged Europe, rebuilding economies and preventing communist expansion. It succeeded spectacularly: Western Europe's GDP doubled within a decade, and democracy stabilized across the continent.",

    "In game theory, a 'dominant strategy' is:":
        "A dominant strategy is your best move regardless of what anyone else does. In the Prisoner's Dilemma, confessing is dominant because it's better whether your partner confesses or not. Finding dominant strategies simplifies complex strategic situations.",

    "What is 'factor endowment theory' (Heckscher-Ohlin model)?":
        "The H-O model predicts that countries export goods using their abundant factors. Land-rich Australia exports agricultural products; labor-rich Bangladesh exports garments. Trade patterns flow naturally from what each country has in abundance.",

    "What is 'dollarization'?":
        "When a country's own currency becomes worthless through hyperinflation, citizens often turn to the U.S. dollar. Ecuador, El Salvador, and Panama officially dollarized, surrendering monetary policy independence in exchange for currency stability.",

    "What is 'austerity' in economic policy?":
        "Austerity is the government tightening its belt -- cutting spending and raising taxes to reduce deficits. Greece's post-2010 austerity measures reduced the deficit but also shrank GDP by 25% and sent unemployment above 27%, sparking fierce debate about its wisdom.",

    "What economic phenomenon does the 'Dutch Disease' describe?":
        "When the Netherlands discovered North Sea gas in the 1960s, the resulting currency appreciation made other exports uncompetitive. The manufacturing sector withered even as the country got richer from gas. It's a cautionary tale about resource dependency.",

    "What is 'negative income tax' proposed by Milton Friedman?":
        "Friedman's negative income tax would replace the entire welfare bureaucracy with a simple formula: below a threshold, you receive money; above it, you pay taxes. It preserves work incentives (you always keep some of each dollar earned) while guaranteeing a basic income.",

    "What is 'anchoring bias' in behavioral economics?":
        "In experiments, people asked 'Is the population of Turkey more or less than 5 million?' give much lower estimates than those asked 'more or less than 65 million?' The initial number -- even if arbitrary -- 'anchors' subsequent judgment. It's why retailers show inflated 'original' prices next to sale prices.",

    "What is 'loss aversion' in behavioral economics?":
        "Kahneman and Tversky found that losing $100 hurts about twice as much as gaining $100 feels good. This asymmetry explains why people hold losing investments too long, over-insure, and irrationally avoid small risks with positive expected value.",

    "What is 'seigniorage'?":
        "Seigniorage is the profit from creating money. Producing a $100 bill costs about 17 cents, so the government earns $99.83 per bill. In the digital age, creating money is even cheaper -- a few keystrokes at the central bank.",

    "What is the 'impossible trinity' in international economics?":
        "A country can choose any two of three: fixed exchange rate, free capital flows, and independent monetary policy. But not all three. China restricts capital flows to keep both a managed exchange rate and policy independence. The EU sacrificed independent monetary policy for fixed rates and free capital.",

    "What does the term 'secular stagnation' describe?":
        "Larry Summers revived this concept to describe advanced economies stuck in a rut of low growth, low inflation, and low interest rates. Aging populations, slowing innovation, and high savings may be structural forces keeping demand permanently weak.",

    "What is the 'Mundell-Fleming model'?":
        "Mundell-Fleming extends Keynesian IS-LM analysis to open economies, showing that the effectiveness of fiscal and monetary policy depends critically on the exchange rate regime. Under floating rates, monetary policy is powerful; under fixed rates, fiscal policy is.",

    "What is 'transfer pricing' and why is it controversial?":
        "Multinational companies set internal prices for transactions between subsidiaries in different countries. By charging high prices in high-tax countries and low prices in tax havens, they shift profits to where taxes are lowest -- perfectly legal, widely criticized.",

    "What is 'financialization' of the economy?":
        "Financialization means finance has grown from servant of the real economy to its master. Financial sector profits rose from 10% of U.S. corporate profits in the 1950s to over 40% before the 2008 crisis. Whether this reflects genuine value creation or rent extraction is fiercely debated.",

    "What is the Stolper-Samuelson theorem?":
        "The theorem shows that free trade raises returns to a country's abundant factor but lowers returns to its scarce factor. In rich countries with abundant capital, trade boosts capital owners' returns while potentially suppressing wages for unskilled labor.",

    "What is the Ramsey-Cass-Koopmans model?":
        "The Ramsey model improves on Solow by making savings decisions optimal rather than fixed. Households choose how much to consume versus save to maximize lifetime satisfaction. It's the workhorse of modern growth theory and dynamic macroeconomics.",

    "What is Ricardian equivalence?":
        "Ricardo's idea (formalized by Barro) suggests that rational consumers see through government borrowing: they save more today to pay future taxes, exactly offsetting the stimulus effect. If true, deficit spending is impotent. In practice, the evidence is mixed.",

    "What is the Arrow-Debreu model?":
        "The Arrow-Debreu model mathematically proved that under perfect competition, an economy can reach an efficient equilibrium. It's the formal foundation of the 'invisible hand' -- though its assumptions (perfect information, no externalities) rarely hold in reality.",

    "What is endogenous growth theory?":
        "Unlike Solow's model where technology falls from the sky, endogenous growth theory explains technological progress as the result of deliberate investment in R&D, education, and knowledge. It implies that policy choices directly affect long-run growth rates.",

    "What is the Solow residual?":
        "After accounting for increases in capital and labor, a large portion of economic growth remains unexplained. This residual -- attributed to technological progress and efficiency gains -- accounts for about half of U.S. growth. It's the most important factor we understand the least.",

    "What is the Modigliani-Miller theorem?":
        "Modigliani and Miller showed that under ideal conditions (no taxes, no bankruptcy costs), it doesn't matter whether a company finances itself with debt or equity. In reality, taxes make debt cheaper, which is why most firms use leverage.",

    "What is the Efficient Market Hypothesis?":
        "The EMH claims stock prices already reflect all available information, making it impossible to consistently 'beat the market.' It's why index funds (which simply match the market) outperform most actively managed funds over time.",

    "What is the theory of second best?":
        "If one market distortion can't be fixed, removing another distortion might actually make things worse. For example, eliminating tariffs on imports while subsidies to domestic firms persist could destroy the domestic industry without creating the efficient outcome free trade normally delivers.",

    "What is rational expectations theory?":
        "If the government always responds to recessions with money printing, people learn to expect inflation and adjust wages and prices preemptively, neutralizing the policy. Rational expectations theory explains why policy surprises work but systematic policies don't.",

    "What is the Coase theorem?":
        "Ronald Coase showed that if property rights are clear and negotiation is cheap, parties will bargain to an efficient outcome regardless of who has the initial rights. A factory polluting a river will pay fishermen to accept it -- or fishermen will pay the factory to stop -- whichever is cheaper.",

    "What is the difference between Keynesian and Classical economics in terms of unemployment?":
        "Classicals say wages naturally adjust: if there's unemployment, wages fall until everyone finds work. Keynesians say wages are 'sticky downward' -- workers resist pay cuts, so unemployment can persist for years without intervention.",

    "What is the Balassa-Samuelson effect?":
        "Rich countries have higher price levels because their productive traded sector (manufacturing) bids up wages across the economy, including in services that can't be traded (haircuts, restaurants). That's why a meal in Tokyo costs more than in Mumbai.",

    "What is the concept of Pareto efficiency?":
        "Named after Italian economist Vilfredo Pareto, an allocation is Pareto efficient when you can't make anyone better off without making someone worse off. It's the economist's definition of 'no waste' -- though a Pareto efficient outcome can still be deeply unequal.",

    "What is dynamic stochastic general equilibrium (DSGE) modeling?":
        "DSGE models attempt to simulate the entire economy from microeconomic foundations, incorporating random shocks and rational expectations. They're the standard tool at central banks, though they famously failed to predict the 2008 crisis.",

    "What is the liquidity preference theory?":
        "Keynes argued that the interest rate is set by the supply and demand for money itself, not by savings and investment. People demand money for transactions, precaution, and speculation -- and the interest rate is the price that balances this demand against the money supply.",

    "What is the Kuznets curve?":
        "Simon Kuznets hypothesized that inequality first worsens then improves as countries industrialize. Early growth concentrates wealth; later, education, democracy, and redistribution spread it more widely. The evidence is mixed -- some countries follow the pattern, others don't.",

    "What is the difference between absolute poverty and relative poverty?":
        "Absolute poverty means you can't afford basic survival needs. Relative poverty means you have significantly less than the typical person in your society. A family in 'relative poverty' in Norway might live better in absolute terms than a middle-class family in a developing country.",

    "What is the Prebisch-Singer hypothesis?":
        "Raul Prebisch and Hans Singer argued that commodity-exporting countries face a long-term disadvantage because the prices of raw materials tend to fall relative to manufactured goods. This 'terms of trade' decline traps developing nations in poverty.",

    "What is the Minsky moment?":
        "Hyman Minsky argued that stability breeds instability: long periods of prosperity make people take ever-greater risks. The 'Minsky moment' is the tipping point when speculation collapses under its own weight. The 2008 crisis was widely called a Minsky moment.",

    "What is the difference between perfect and imperfect competition?":
        "Perfect competition is the ideal: identical products, countless sellers, zero barriers. Imperfect competition covers everything else -- monopoly, oligopoly, monopolistic competition. Most real markets are imperfectly competitive, which is why market power and strategic behavior matter.",

    "What is the St. Petersburg Paradox?":
        "A coin-flip game that pays $2, $4, $8... doubling each round until tails appears has infinite expected value mathematically, yet no one would pay more than a small amount to play. It revealed that people value potential gains less as they grow larger -- the birth of expected utility theory.",

    "What is the difference between autarky and free trade?":
        "Autarky means a country produces everything domestically with no international trade. Free trade means goods flow freely across borders. North Korea is the closest modern example of autarky; its poverty compared to trading neighbors illustrates why self-sufficiency is usually a losing strategy.",

    "What is the difference between Schumpeterian and Solow growth theory?":
        "Solow says growth comes from accumulating capital and exogenous technological progress. Schumpeter says growth comes from innovating entrepreneurs who disrupt existing industries through creative destruction. Solow emphasizes the steady; Schumpeter emphasizes the revolutionary.",

    "What is the Olson collective action problem?":
        "Mancur Olson showed that large groups (like taxpayers or consumers) struggle to organize because each individual benefits little from costly activism. Small, concentrated interest groups (like specific industries) organize easily because each member gains a lot. This asymmetry explains much of politics.",

    "The Cantillon effect explains why newly created money does not benefit everyone equally. Who benefits most and who is harmed?":
        "Richard Cantillon observed in the 1730s that new money enters the economy at specific points. Those nearest the source (banks, government contractors) spend it before prices adjust. By the time it reaches wage earners and savers, prices have already risen -- a hidden redistribution from poor to rich.",

    "What is the difference between horizontal and vertical equity in taxation?":
        "Horizontal equity says people in similar situations should pay similar taxes. Vertical equity says people who earn more should pay more. These principles sound simple but clash in practice: every tax deduction violates horizontal equity while arguably serving other goals.",

    "What is endogenous money theory?":
        "Endogenous money theory argues that banks don't wait for the central bank to create money -- they create it by making loans. When demand for credit rises, banks lend more, expanding the money supply from within. The central bank accommodates rather than initiates.",

    "What is the Beveridge curve?":
        "The Beveridge curve plots job vacancies against unemployment. When both are high simultaneously, it signals a matching problem: jobs exist and workers want them, but skills, location, or information barriers prevent connections.",

    "What is financialization?":
        "Since the 1980s, financial sector profits exploded as a share of the economy while manufacturing declined. Critics argue finance extracted wealth rather than creating it; defenders say financial innovation genuinely improves capital allocation.",

    "What is the distinction between nominal and real wages?":
        "Getting a 3% raise when inflation is 5% means your real wage fell 2%. Real wages adjust for inflation and reveal whether workers are actually better or worse off -- which is why economists always distinguish between the two.",

    "What is the concept of market power?":
        "Market power is a firm's ability to charge prices above competitive levels. Google has enormous market power in search advertising; a small farm selling corn has none. The degree of market power determines how much profit a firm can extract.",

    "What is the Prebisch import substitution industrialization (ISI) strategy?":
        "ISI was the development strategy of choice in Latin America from the 1950s-80s: protect domestic industry with tariffs while it matures. Results were disappointing -- protected industries remained inefficient, and countries that switched to export-led growth (like South Korea) surged ahead.",

    "What is the distinction between ex-ante and ex-post in economics?":
        "Ex-ante analysis looks forward (what we expect before an event); ex-post looks backward (what actually happened). A policy may look brilliant ex-ante but terrible ex-post -- or vice versa. Good economics requires evaluating both perspectives.",

    "What is Say's Law?":
        "Jean-Baptiste Say argued that production is the source of demand: a shoemaker's output creates the income to buy bread. In a barter economy this is trivially true. Keynes challenged it by showing that money can 'leak out' of the cycle through hoarding.",

    "What is the difference between Pigouvian taxes and cap-and-trade systems?":
        "A Pigouvian tax sets a price on pollution (say $50/ton of CO2) and lets the market determine the quantity emitted. Cap-and-trade sets a quantity limit and lets the market determine the price. Both harness market incentives to reduce pollution efficiently.",

    "What is the difference between structural and cyclical deficits?":
        "A cyclical deficit appears during recessions (tax revenue falls, spending rises automatically) and disappears during booms. A structural deficit persists regardless of the economic cycle -- it reflects a permanent gap between spending commitments and revenue capacity.",

    "What is the Tobin Q ratio?":
        "Tobin's Q compares a company's market value to the replacement cost of its assets. If Q > 1, the market values the company above its physical assets (suggesting it should invest more). If Q < 1, the market values it below replacement cost (suggesting it should shrink).",

    "What is the difference between autarky optimum and free trade optimum in trade theory?":
        "Under autarky, a country maximizes welfare using only its own resources. Under free trade, it can specialize and trade, reaching a higher welfare level. The difference between these two optima represents the gains from trade -- what protectionism sacrifices.",

    "What does Robert Nozick's 'Wilt Chamberlain argument' demonstrate about wealth redistribution?":
        "Nozick asks: if everyone starts with equal shares and then voluntarily pays to watch Wilt Chamberlain play, Chamberlain becomes rich. No injustice occurred. Maintaining equality would require continuously prohibiting voluntary transactions -- a profound cost to freedom.",

    "The Misesian 'regression theorem' explains the origin of money. What does it say?":
        "Mises traced money's value backward through time: today's value rests on yesterday's, and so on, until you reach a point when the commodity (gold, shells) was valued for its direct use. This chain proves money must originate from a commodity, not from government decree alone.",

    "What is the 'knowledge problem' as applied to modern healthcare pricing set by government or insurers?":
        "When prices are hidden behind insurance and government programs, neither patients nor providers have the information needed for efficient choices. The result is massive price variation, overuse of expensive treatments, and a system that costs far more than it should.",
}

# ---------------------------------------------------------------------------
# THEOLOGY CONTEXTS
# ---------------------------------------------------------------------------
THEO_CONTEXTS = {
    # ---- Tier 1 ----
    "What is the last book of the New Testament?":
        "Revelation, written by the Apostle John while exiled on the island of Patmos, is filled with apocalyptic visions and symbolic imagery. Its dramatic portrayal of the end times has inspired more art, literature, and debate than perhaps any other biblical book.",

    "In which river was Jesus baptized?":
        "The Jordan River holds deep significance in biblical history -- the Israelites crossed it to enter the Promised Land. Jesus's baptism in the same river symbolically connected his ministry to Israel's ancient story of liberation and covenant.",

    "Why does Christianity insist on monotheism (one God) rather than polytheism?":
        "The First Commandment -- 'You shall have no other gods before me' -- established exclusive devotion as the foundation of Israelite faith. In a world where every city had its own pantheon, monotheism was a radical claim that ultimate reality is unified, not fragmented.",

    "What does 'Buddha' mean?":
        "Siddhartha Gautama earned the title 'Buddha' (Awakened One) after achieving enlightenment under the Bodhi tree around 500 BCE. The title implies that enlightenment is not a gift from a god but an awakening to reality that is, in principle, available to all beings.",

    "How many books are in the Old Testament?":
        "The Protestant Old Testament contains 39 books, from Genesis through Malachi. The Hebrew Bible contains the same material but organizes it into 24 books using a different division. Catholic and Orthodox Bibles include additional deuterocanonical works.",

    "What was the name of Moses' brother who spoke for him?":
        "Aaron served as Moses's spokesman because Moses claimed to be 'slow of speech.' Aaron later became Israel's first high priest, founding a priestly line that served in the Temple for centuries.",

    "Who was the first man created in the Bible?":
        "Genesis describes God forming Adam from the dust of the ground and breathing life into him. The name 'Adam' is related to the Hebrew word 'adamah' (earth/ground), linking humanity's identity to the material world from which we came.",

    "What is the symbol of Christianity?":
        "The cross transformed from a Roman instrument of shameful execution into Christianity's central symbol. Early Christians saw it as the paradox at the heart of their faith: God's power revealed through apparent defeat.",

    "What is the theological significance of the First Commandment ('You shall have no other gods before me')?":
        "The First Commandment isn't merely about worshipping statues -- it declares that nothing (wealth, power, nation, self) may take the place of ultimate loyalty to God. Theologians call misplaced ultimate loyalty 'idolatry,' and consider it the root from which all other sins grow.",

    "What sea did Jesus walk on?":
        "The Sea of Galilee (actually a freshwater lake) was the center of Jesus's Galilean ministry. Many of his disciples were fishermen on its waters, and several miraculous events -- calming the storm, walking on water, the miraculous catch of fish -- took place there.",

    "Who is the Greek god of the sun and music?":
        "Apollo was one of the most important Olympian gods, associated with the sun, music, poetry, healing, and prophecy. His oracle at Delphi was the most prestigious in the ancient world, consulted by kings and generals before major decisions.",

    "Who is the Greek god of the sea?":
        "Poseidon ruled the oceans and was known for his volatile temper, causing earthquakes and storms when angered. Greek sailors prayed to him before voyages, and his rivalry with Athena over patronage of Athens is one of mythology's most famous contests.",

    "What is the theological significance of the commandment 'You shall not murder'?":
        "The prohibition against murder rests on the concept of 'imago Dei' -- humans are made in God's image, so taking a human life is an offense against God himself. This doctrine became a foundation for later concepts of inherent human dignity and universal rights.",

    "What sacred structure did Solomon build in Jerusalem?":
        "Solomon's Temple, completed around 957 BCE, was the spiritual center of ancient Israel -- the place where heaven and earth met in Jewish theology. Its destruction by Babylon in 586 BCE was one of the most traumatic events in Jewish history.",

    "In Protestant tradition, which commandment says to honor your father and mother?":
        "The Fifth Commandment is unique among the Ten because it comes with a promise: 'that your days may be long.' It established family as a sacred institution and parental authority as a reflection of divine order.",

    "What is the holy city of Islam?":
        "Mecca is sacred to Muslims as the birthplace of the Prophet Muhammad and the site of the Ka'ba, which Islamic tradition traces back to Abraham and Ishmael. Every physically and financially able Muslim is called to make pilgrimage (Hajj) there at least once.",

    "What is the world tree in Norse mythology called?":
        "Yggdrasil is the cosmic ash tree that connects the nine worlds of Norse cosmology. Its roots reach into three wells, an eagle perches at its crown, and a dragon gnaws at its roots -- it's the axis around which the entire Norse universe revolves.",

    "What is the Muslim pilgrimage to Mecca called?":
        "The Hajj is one of Islam's Five Pillars, required of every able Muslim once in their lifetime. Over two million pilgrims gather annually, all wearing simple white garments that erase distinctions of wealth and status before God.",

    "Noah's ark came to rest on which mountain?":
        "Mount Ararat, located in modern-day Turkey, has been the traditional landing site since ancient times. Expeditions have searched for the ark's remains for centuries, though no confirmed discovery has ever been made.",

    "How many days and nights did it rain during Noah's flood?":
        "The number 40 appears throughout the Bible as a period of testing and transformation -- Moses spent 40 days on Sinai, Israel wandered 40 years, and Jesus fasted 40 days. The 40 days of rain signaled divine judgment and the world's rebirth.",

    "What name did God reveal to Moses from the burning bush?":
        "The divine name YHWH (often rendered 'I AM WHO I AM') is so sacred in Judaism that it is never spoken aloud. It suggests a God who is self-existent, beyond human categories, and known not through philosophical definition but through relationship and action.",

    "Who was swallowed by a large fish in the Bible?":
        "Jonah tried to flee God's command to preach to Nineveh and was swallowed by a great fish for three days. The story is about divine mercy extending beyond Israel -- even to Israel's enemies -- and the futility of running from one's calling.",

    "In what town was Jesus born?":
        "Bethlehem, a small town south of Jerusalem, was also the birthplace of King David. The prophet Micah had foretold that a ruler of Israel would come from Bethlehem, making Jesus's birth there a fulfillment of messianic prophecy.",

    "What was Moses' rod used to part?":
        "The parting of the Red Sea is the defining liberation event of the Hebrew Bible. It demonstrated God's power over nature and over Egypt's pharaoh, and it became the foundational metaphor for divine deliverance in Jewish and Christian tradition.",

    "What does 'Islam' mean?":
        "The Arabic word 'Islam' comes from the root s-l-m, related to 'salam' (peace). It means voluntary submission to God's will. In Islamic theology, true peace comes through aligning one's life with the Creator's purposes.",

    "What is the Greek word for God (masculine)?":
        "Theos is the Greek word for God, and it forms the root of 'theology' (the study of God), 'theism' (belief in God), and 'atheism' (without God). The New Testament, written in Greek, uses theos to refer to the one God of Israel.",

    "Who is the Roman equivalent of Zeus?":
        "Jupiter (Jove) was the king of the Roman gods, ruler of the sky and thunder. His temple on the Capitoline Hill was the most important in Rome. Thursday (Jovis dies) is named after him in many Romance languages.",

    "What is the holy book of Sikhism?":
        "The Guru Granth Sahib is unique among sacred texts: it is treated as a living guru, not merely a book. It contains hymns from Sikh gurus and Hindu and Muslim saints, reflecting Sikhism's emphasis on the universal nature of divine truth.",

    "What is the theological significance of the Logos concept in John 1:1 ('In the beginning was the Word')?":
        "By calling Christ 'the Logos,' John's Gospel bridges two worlds. For Jews, God's Word was the creative power behind Genesis. For Greeks, Logos was the rational principle ordering the cosmos. John declares that both find their fulfillment in the person of Jesus.",

    "Who wrote most of the Psalms in the Bible?":
        "King David is traditionally credited with about half the Psalms, earning him the title 'sweet singer of Israel.' The Psalms cover the full range of human emotion -- praise, lament, rage, gratitude, despair -- making them uniquely relatable across millennia.",

    "Which patriarch is considered the father of the three Abrahamic faiths?":
        "Abraham is revered by Jews (through Isaac), Christians (as a model of faith), and Muslims (through Ishmael). His willingness to follow God into the unknown made him the prototype of faith in all three traditions.",

    "Who rules the underworld in Greek mythology?":
        "Hades drew the underworld as his domain when the three brothers -- Zeus, Poseidon, and Hades -- divided the cosmos by lot. Despite ruling the dead, Hades was not considered evil in Greek religion -- he was stern but fair, a necessary ruler of an inevitable realm.",

    "Who is the Roman equivalent of Athena?":
        "Minerva was the Roman goddess of wisdom, strategic warfare, and crafts. She was part of the Capitoline Triad (with Jupiter and Juno), the three most important deities in Roman state religion.",

    "Who is the Roman god of wine (same as Bacchus)?":
        "Bacchus (Greek Dionysus) represented the ecstatic, irrational side of human experience -- wine, festivity, and release from ordinary life. His mystery cult offered initiates a mystical experience of death and rebirth.",

    "On which mountain did Moses receive the Ten Commandments?":
        "Mount Sinai (also called Horeb) is where God made a covenant with Israel, giving them the Torah. The exact location is debated, but the traditional site in Egypt's Sinai Peninsula has been a pilgrimage destination since the 4th century.",

    "What animal does the Holy Spirit appear as at Jesus's baptism?":
        "The dove descending at Jesus's baptism recalls the dove Noah sent from the ark -- a symbol of peace and new beginning. In Christian art, the dove became the standard symbol of the Holy Spirit and divine peace.",

    "Who is the chief Egyptian god of the dead?":
        "Osiris was murdered by his brother Set, then resurrected by his wife Isis -- making him both lord of the dead and a symbol of resurrection. The annual flooding of the Nile was seen as Osiris's life-giving power renewing the land.",

    "Who is the Roman equivalent of Hades?":
        "Pluto (from the Greek 'Plouton,' meaning 'the wealthy one') emphasized the god's association with underground riches and fertile earth. The Romans softened Hades' stern image, connecting him more to the wealth buried beneath the soil.",

    "Who is the Greek goddess of wisdom?":
        "Athena sprang fully armed from Zeus's head -- born without a mother, she embodied reason untainted by passion. She was patron of Athens, goddess of strategic warfare, and protector of heroes like Odysseus.",

    "What is the holy book of Islam called?":
        "The Quran (meaning 'the recitation') is believed by Muslims to be the literal word of God as revealed to Muhammad over 23 years. It is written in Arabic, and Muslims consider any translation to be merely an interpretation of the original.",

    "Who is the Norse god associated with healing and beauty?":
        "Baldur was the most beloved of the Norse gods -- so beautiful and good that his death, caused by Loki's treachery, is the event that sets Ragnarok in motion. His story embodies the tragedy at the heart of Norse mythology: even the best and brightest cannot escape fate.",

    "In Greek myth, who gave fire to humanity?":
        "Prometheus stole fire from the gods and gave it to humanity, earning Zeus's eternal punishment: chained to a rock while an eagle ate his liver daily. He became a symbol of daring rebellion against tyranny and the price paid for advancing human civilization.",

    "Which Greek god is associated with wine?":
        "Dionysus represented the wild, untamed forces of nature -- wine, ecstasy, and the dissolution of boundaries between gods and mortals. His cult was among the most widespread in the ancient world, offering spiritual experiences to all classes, including women and slaves.",

    "Who was the first woman created in the Bible?":
        "Eve was created from Adam's rib in Genesis, a detail traditionally interpreted as signifying partnership rather than subordination. Her name (Havah in Hebrew) means 'life' or 'living one,' marking her as the mother of all humanity.",

    "What is the main sacred text of Hinduism?":
        "The Vedas are among the oldest religious texts in existence, composed between 1500 and 500 BCE. The word 'Veda' means 'knowledge,' and these texts contain hymns, rituals, philosophical dialogues, and the seeds of all later Hindu thought.",

    "How many of each kind of animal did Noah take on the ark (clean animals)?":
        "Genesis 7:2 specifies seven pairs of clean animals (used for sacrifice and food) but only one pair of unclean animals. This detail is often overlooked in children's versions of the story, which typically show only pairs of two.",

    "Who defeated Goliath?":
        "The young shepherd David felled the giant Goliath with a single stone from his sling. The story became the archetype of unlikely victory -- the small and faithful overcoming the powerful through courage and divine aid.",

    "What ocean is named after the Greek titan who held up the sky?":
        "Atlas was condemned by Zeus to hold up the heavens for eternity. The ocean beyond the known western world was named after him, as were the Atlas Mountains in North Africa. The word 'atlas' for a book of maps also derives from his name.",

    "Which Greek god is the god of fire and the forge?":
        "Hephaestus was the divine blacksmith, lame but brilliant, who crafted the weapons of the gods including Zeus's thunderbolts and Achilles's armor. He represents the power of craftsmanship and ingenuity triumphing over physical limitations.",

    "Which Norse goddess presides over the dead who do not go to Valhalla?":
        "Hel, daughter of Loki, rules over the dead who did not die in battle. Her realm (also called Hel) receives the vast majority of the dead. She is described as half living and half dead, embodying the boundary between life and death.",

    "In the Parable of the Prodigal Son, what does the father's response to the returning son reveal about God's character?":
        "The father runs to embrace his son before the son finishes his apology -- grace precedes completed repentance. This parable is one of the most powerful illustrations of unconditional divine love in all religious literature.",

    "What is Thor's hammer called?":
        "Mjolnir ('the crusher') was forged by dwarves and could level mountains. It always returned to Thor's hand after being thrown. Pendant replicas of Mjolnir were the most common religious symbol in Viking-age Scandinavia.",

    "Who baptized Jesus in the Jordan River?":
        "John the Baptist was a prophetic figure who prepared the way for Jesus's ministry by calling people to repentance. When he baptized Jesus, he recognized him as 'the Lamb of God' -- a pivotal moment in all four Gospels.",

    "What is the Jewish day of rest called?":
        "Shabbat begins at sunset on Friday and ends at sunset on Saturday, commemorating God's rest on the seventh day of creation. It's a weekly sanctuary in time -- a day set apart from work for worship, family, and renewal.",

    "What are the names Huginn and Muninn associated with in Norse mythology?":
        "Huginn (Thought) and Muninn (Memory) are Odin's two ravens who fly across the world each day and return to whisper everything they've seen. Odin feared most that Muninn might not return -- a poetic way of saying wisdom without memory is blind.",

    "What instrument was David famous for playing?":
        "David played the lyre (often translated 'harp') to soothe King Saul's troubled spirit. His musical gifts made him Israel's greatest poet -- the Psalms attributed to him have been central to Jewish and Christian worship for three thousand years.",

    "Who was the Prophet Muhammad?":
        "Muhammad (c. 570-632 CE) received the revelations that became the Quran over 23 years, beginning in a cave near Mecca. He is considered the final prophet in a line that includes Abraham, Moses, and Jesus, delivering God's complete and final message.",

    # ---- Tier 2 ----
    "What are the Four Noble Truths in Buddhism?":
        "The Four Noble Truths are Buddhism's foundational diagnosis: life involves suffering (dukkha); suffering has a cause (craving); suffering can end; and there is a path to end it (the Eightfold Path). Like a doctor's assessment, they identify the disease before prescribing the cure.",

    "Which disciple was known as 'the doubter' until he saw Jesus's wounds?":
        "Thomas refused to believe in the resurrection until he could touch Jesus's wounds himself. When he finally did, he exclaimed 'My Lord and my God!' -- one of the strongest declarations of Jesus's divinity in the Gospels.",

    "How many brothers did Joseph (son of Jacob) have?":
        "Joseph had eleven brothers -- the twelve sons of Jacob (Israel) became the twelve tribes of Israel. Joseph's story of betrayal, slavery, and eventual rise to power in Egypt is one of the Bible's great narratives of providence working through human evil.",

    "Who is the Norse god of fertility and the harvest?":
        "Freyr was one of the Vanir gods, associated with sunshine, rain, and the fertility of the earth. He gave up his magical sword for love of the giantess Gerd -- a sacrifice that will leave him defenseless at Ragnarok.",

    "What was the second labor of Hercules?":
        "The Lernaean Hydra was a serpentine monster with multiple heads that regrew two for every one cut off. Hercules solved this by having his nephew cauterize each stump. The lesson: brute force alone doesn't always work -- you need strategy too.",

    "What theological concept does the Parable of the Talents illustrate about individual responsibility before God?":
        "The master entrusts different amounts to three servants and judges each on their stewardship. The parable teaches that God holds each person individually accountable -- not for having equal gifts, but for faithfully using whatever they were given.",

    "In Greek mythology, who is the messenger of the sea?":
        "Triton, son of Poseidon, was depicted as a merman who calmed the seas by blowing his conch shell. His image was so popular in ancient art that 'tritons' became a general term for merman-like sea creatures.",

    "In the Parable of the Wedding Banquet, what happens to the man without wedding clothes?":
        "The guest who attended without proper garments was cast into outer darkness. The parable warns that being invited (receiving God's grace) is not enough -- one must also accept the transformation that the invitation requires.",

    "What does the Parable of the Mustard Seed illustrate?":
        "Jesus compared the Kingdom of God to a tiny mustard seed that grows into a tree large enough for birds to nest in. Christianity itself began with twelve followers in a backwater Roman province and grew to encompass two billion people.",

    "What is the Roman equivalent of Hermes?":
        "Mercury was the Roman messenger god, patron of travelers, merchants, and thieves. He lent his name to the planet Mercury (fastest orbit), the element mercury (liquid metal), and the word 'mercurial' (quick-changing).",

    "Daniel's three friends were thrown into what because they refused to worship a statue?":
        "Shadrach, Meshach, and Abednego were thrown into a furnace heated seven times hotter than normal. They emerged unharmed, with a mysterious fourth figure beside them. The story became a touchstone for resisting political idolatry.",

    "In Buddhism, what is the cycle of birth, death, and rebirth called?":
        "Samsara is the endless wheel of existence from which Buddhism seeks liberation. The word literally means 'wandering' or 'flowing on' -- capturing the restless, unsatisfying nature of existence driven by craving and ignorance.",

    "What does the story of Daniel refusing to worship Nebuchadnezzar's statue say about individual conscience and state authority?":
        "Daniel's defiance established one of the most influential principles in Western thought: there are moral limits to political obedience. When the state demands what God forbids, the individual conscience must resist -- a principle later invoked by abolitionists, civil rights leaders, and dissidents worldwide.",

    "What did Odin sacrifice to drink from Mimir's well?":
        "Odin gave up one of his eyes to gain wisdom from Mimir's well. In Norse culture, wisdom always comes at a price. Odin's sacrifice reflects the belief that true knowledge requires suffering and the willingness to give up part of yourself.",

    "In the Parable of the Prodigal Son, how many sons does the father have?":
        "The two sons represent two types of spiritual failure: the younger son's rebellion (obvious sin) and the elder son's resentful obedience (self-righteous religion). Both need the father's grace, though only the younger recognizes it.",

    "What is the name of the sacred mirror in Japanese mythology?":
        "Yata no Kagami is one of Japan's three Imperial Regalia, said to have been used to lure the sun goddess Amaterasu out of a cave where she had hidden, plunging the world into darkness. It represents truth and wisdom.",

    "What does the Parable of the Good Samaritan teach about the scope of moral obligation?":
        "By making a despised Samaritan the hero while a priest and Levite pass by, Jesus demolished ethnic and religious barriers to moral duty. Your 'neighbor' is anyone in need -- period. This radical expansion of moral obligation has shaped ethical thought for two millennia.",

    "In Greek myth, what winged horse was born from Medusa's blood?":
        "Pegasus sprang from Medusa's neck when Perseus beheaded her. The winged horse became a symbol of poetic inspiration and was eventually placed among the stars as a constellation. Beauty emerging from horror is a recurring theme in Greek myth.",

    "Who did Perseus rescue from the sea monster Cetus?":
        "Andromeda was chained to a rock as a sacrifice to the sea monster, punished for her mother Cassiopeia's boast of being more beautiful than the sea nymphs. Perseus swooped in on Pegasus and turned Cetus to stone with Medusa's head.",

    "Who are the Japanese creator deities who stirred the sea to create the islands?":
        "Izanagi and Izanami stirred the primordial ocean with a jeweled spear, and the drops that fell from its tip formed the islands of Japan. Their creation myth establishes the divine origins of the Japanese archipelago in Shinto tradition.",

    "What is Sisyphus's eternal punishment in Greek mythology?":
        "Sisyphus was condemned to push a boulder up a hill forever, only to watch it roll back down each time. Albert Camus later used this myth as a metaphor for the human condition -- finding meaning in the struggle itself despite its apparent futility.",

    "In Shinto, what are divine spirits or gods called?":
        "Kami are the sacred spirits inhabiting everything from mountains and rivers to ancestors and natural phenomena. Shinto recognizes eight million kami -- a number meaning 'countless' rather than literal -- reflecting the belief that the divine pervades all of nature.",

    "How did the Greek hero Theseus escape the Labyrinth?":
        "Ariadne, daughter of King Minos, gave Theseus a ball of thread to unwind as he entered the Labyrinth. After slaying the Minotaur, he followed the thread back to safety. The 'Ariadne's thread' became a metaphor for any simple solution to a complex problem.",

    "What is the Hindu concept of the eternal self or soul?":
        "Atman is the true self -- unchanging, eternal, and ultimately identical with Brahman (the universal reality) in many Hindu schools. The realization 'Atman is Brahman' is the central insight of Advaita Vedanta, considered the highest spiritual achievement.",

    "What creature guards the Well of Mimir in Norse mythology?":
        "Mimir himself guards the well that bears his name. Even after being beheaded during the Aesir-Vanir war, Odin preserved Mimir's head with herbs and consulted it for wisdom. Knowledge in Norse mythology outlasts even death.",

    "What shape is the Norse world tree Yggdrasil?":
        "Yggdrasil is an enormous ash tree whose branches reach into the heavens and whose three roots extend to the realms of gods, giants, and the dead. The ash was considered sacred in Norse culture -- strong, resilient, and connecting heaven to earth.",

    "What is the final stage of the Buddhist path?":
        "Nirvana literally means 'blowing out' -- the extinguishing of the fires of greed, hatred, and delusion. It's not annihilation but liberation: the end of suffering and the cycle of rebirth. The Buddha described it as 'the unconditioned.'",

    "What was the first labor of Hercules?":
        "The Nemean Lion had an impenetrable golden hide that no weapon could pierce. Hercules strangled it with his bare hands and then wore its skin as armor. The first labor established Hercules as the ultimate hero -- conquering the unconquerable.",

    "What is the Hindu god of destruction and transformation?":
        "Shiva is both destroyer and regenerator -- destruction in Hindu thought is not evil but necessary for renewal. His cosmic dance (Nataraja) symbolizes the eternal cycle of creation, preservation, and dissolution that keeps the universe in motion.",

    "Which god is prophesied to kill and be killed by Jormungandr at Ragnarok?":
        "Thor and the World Serpent are fated to destroy each other at the end of the world. Thor will slay Jormungandr but then take nine steps and fall dead from its venom. It's the most poignant moment of Ragnarok -- even the mightiest cannot escape fate.",

    "Whose head did Perseus slay and use as a weapon?":
        "Medusa, whose gaze turned men to stone, was beheaded by Perseus using Athena's polished shield as a mirror to avoid looking directly at her. He then used her severed head as a weapon, turning his enemies to stone before placing it on Athena's shield.",

    "What is Niflheim in Norse mythology?":
        "Niflheim is the primordial realm of ice, cold, and mist -- one of two original realms (the other being fiery Muspelheim). Where their elements met in the void of Ginnungagap, the frost giant Ymir was born, and from his body the world was made.",

    "Who is the wife of Zeus and queen of the Olympians?":
        "Hera was the goddess of marriage and family, yet ironically spent much of her time pursuing Zeus's many lovers and their offspring. Her jealousy drove many mythological plots, from the persecution of Heracles to the Trojan War.",

    "What is the Hindu god of preservation?":
        "Vishnu preserves the cosmic order by incarnating on earth whenever evil threatens to overwhelm good. His ten avatars include Rama and Krishna, and each represents divine intervention to restore the balance of dharma.",

    "Who was the great Greek hero who traveled in an odyssey home from Troy?":
        "Odysseus (Ulysses in Latin) spent ten years trying to get home after the Trojan War, facing monsters, enchantresses, and divine wrath. Homer's Odyssey made his name synonymous with any long, eventful journey.",

    "In the Parable of the Lost Sheep, how many sheep does the shepherd leave to find the one lost?":
        "The shepherd leaves 99 safe sheep to search for the single lost one. This math seems reckless -- but Jesus's point is that God's love isn't utilitarian. Every individual matters infinitely, not just statistically.",

    "What is the central concept of Taoism?":
        "The Tao (the Way) is the ultimate reality underlying all things -- formless, nameless, and beyond human comprehension. Taoism teaches that harmony comes not from forcing one's will but from aligning with the natural flow of the Tao.",

    "What is Asgard in Norse mythology?":
        "Asgard is the celestial fortress of the Aesir gods, connected to earth (Midgard) by the rainbow bridge Bifrost. It contains Valhalla, Odin's hall where slain warriors feast and prepare for Ragnarok.",

    "In Greek myth, who built the Labyrinth that housed the Minotaur?":
        "Daedalus was the greatest inventor and craftsman of Greek mythology. He built the Labyrinth for King Minos, then was imprisoned in it. His escape on wings of wax and feathers -- and his son Icarus's fatal flight too close to the sun -- is one of myth's most enduring cautionary tales.",

    "What language did Jesus primarily speak?":
        "Aramaic was the common language of 1st-century Palestine, and Jesus likely spoke it in daily life and teaching. Hebrew was used in synagogue worship, while Greek was the lingua franca of the broader Roman world -- which is why the New Testament was written in Greek.",

    "What is the Golden Fleece in Greek mythology?":
        "The Golden Fleece hung in a sacred grove guarded by a never-sleeping dragon in Colchis (modern Georgia). Jason's quest to retrieve it with the Argonauts is one of the oldest adventure narratives in Western literature.",

    "In the Parable of the Sower, what do the seeds on rocky ground represent?":
        "The rocky ground represents those who receive God's word with initial enthusiasm but have no depth of commitment. When persecution or hardship comes, their faith withers. It's Jesus's warning that shallow faith cannot survive real trials.",

    "What is the sacred Taoist text written by Laozi?":
        "The Tao Te Ching is one of the most translated books in history -- just 5,000 characters long, yet endlessly deep. Its paradoxical wisdom ('the softest overcomes the hardest') has influenced philosophy, martial arts, and leadership theory for 2,500 years.",

    "What is the Eightfold Path in Buddhism concerned with?":
        "The Eightfold Path provides practical guidance for living: right view, intention, speech, action, livelihood, effort, mindfulness, and concentration. It's the Buddha's prescription for ending suffering -- not through belief or ritual, but through transformation of one's entire way of being.",

    "In the Parable of the Good Samaritan, who helps the beaten man?":
        "A Samaritan -- despised by Jews as a religious outsider -- stopped to help when a priest and Levite (religious insiders) walked past. Jesus's audience would have been shocked. The point: moral heroism comes from compassion, not religious credentials.",

    "In Greek mythology, what is the name for the triple road crossing where Oedipus killed his father?":
        "At the crossroads of Phocis, Oedipus unknowingly killed his father Laius in a road-rage incident, fulfilling the prophecy he'd spent his life trying to avoid. The crossroads became a symbol of fateful choices and inescapable destiny.",

    "In the Parable of the Talents, what happens to the servant who buried his talent?":
        "The master took away the buried talent and gave it to the servant who had earned the most. The parable's harsh message: God expects active engagement with the gifts we're given. Playing it safe out of fear is itself a failure of faithfulness.",

    "What type of combat did the Valkyries choose the winners of?":
        "The Valkyries ('choosers of the slain') flew over battlefields selecting the bravest warriors to bring to Valhalla. In Norse theology, a glorious death in battle was the highest honor -- the Valkyries' choice was the ultimate validation of a warrior's life.",

    "What does the Lord's Prayer begin with?":
        "By beginning with 'Our Father,' Jesus established a revolutionary intimacy between humans and God. In Judaism, calling God 'Father' (Abba) was almost scandalously personal. The prayer moves from cosmic praise to daily needs to forgiveness -- a blueprint for all Christian prayer.",

    "What is the Sermon on the Mount?":
        "The Sermon on the Mount (Matthew 5-7) is Jesus's most extensive teaching block, containing the Beatitudes, the Lord's Prayer, and radical ethical demands ('love your enemies'). Many scholars consider it the charter document of Christian ethics.",

    "What is the rainbow bridge in Norse mythology?":
        "Bifrost connects Asgard (realm of the gods) to Midgard (realm of humans). It appears as a rainbow and is guarded by Heimdall, who will sound his horn when giants march across it at Ragnarok.",

    "In the Four Noble Truths, what is the cause of suffering?":
        "The Buddha identified tanha (craving or thirst) as the root cause of suffering -- not just desire for pleasure, but the deeper craving for existence itself, for things to be permanent when they are not. Liberation begins with understanding this.",

    "In the Parable of the Prodigal Son, what does the father do when the son returns?":
        "The father ran to meet his returning son -- a remarkable detail, since dignified Middle Eastern patriarchs never ran. He didn't wait for the son's apology; he celebrated first. The point: God's grace doesn't wait for us to get ourselves together.",

    "What is Midgard in Norse mythology?":
        "Midgard ('Middle Earth' -- yes, Tolkien borrowed the term) is the realm of humans, encircled by the ocean where the World Serpent Jormungandr lies. It was created from the body of the giant Ymir and connected to Asgard by Bifrost.",

    "What was the key theological issue resolved by the Council of Nicaea (325 AD), and why did it matter for Christian ethics?":
        "Nicaea declared that Christ was 'homoousios' (of the same substance) with the Father -- fully God, not a lesser being. If Christ were merely a created being, his death couldn't redeem humanity. The stakes were nothing less than the possibility of salvation itself.",

    "What is the path of devotion to God in Hinduism?":
        "Bhakti yoga is the path of loving devotion to a personal God. It democratized Hindu spirituality by making the highest spiritual achievement accessible to all -- not just scholars (jnana) or ascetics (raja) -- through love, worship, and surrender.",

    "What is the name of the Norse world tree?":
        "Yggdrasil literally means 'Odin's horse' -- a reference to Odin hanging himself from the tree for nine days to gain the wisdom of the runes. The tree connects all nine worlds and is tended by the Norns, the Norse fates.",

    "In Norse mythology, who is Loki's trickery famous for causing the death of?":
        "Loki engineered the death of Baldur by tricking the blind god Hod into throwing a mistletoe dart -- the only substance that could harm the otherwise invulnerable Baldur. This act of treachery set in motion the chain of events leading to Ragnarok.",

    "Who is the Roman equivalent of Hermes and the messenger god?":
        "Mercury, with his winged sandals and caduceus, was the swift messenger of the gods. He guided souls to the underworld and protected travelers and merchants. Wednesday (Mercredi in French) is named after him.",

    "What is the name of Odin's spear?":
        "Gungnir, forged by the dwarves, never missed its target. Odin threw it over the heads of enemies before battle, dedicating the slain to himself. The spear symbolized Odin's role as god of war, death, and wisdom.",

    # ---- Tier 3+ (continued in bulk) ----
    "What are the Upanishads?":
        "The Upanishads (c. 800-200 BCE) are the philosophical crown of the Vedas, exploring questions about the ultimate nature of reality (Brahman), the self (Atman), and their unity. Their central insight -- 'Tat tvam asi' (Thou art That) -- is one of the most profound statements in world philosophy.",

    "What is the Bhagavad Gita?":
        "Set on a battlefield, the Gita presents a dialogue between the warrior Arjuna and the god Krishna about duty, devotion, and the nature of reality. It synthesizes Hindu philosophy into a practical guide for living -- which is why it has been called 'India's most important text.'",

    "What is the Vedanta school of Hinduism about?":
        "Vedanta ('end of the Vedas') interprets the Upanishads philosophically. Its most famous school, Advaita Vedanta, teaches that Brahman (ultimate reality) and Atman (individual soul) are one -- the apparent diversity of the world is maya (illusion).",

    "What is Rosh Hashanah?":
        "Rosh Hashanah ('Head of the Year') marks the Jewish New Year and begins the Ten Days of Repentance leading to Yom Kippur. The shofar (ram's horn) is blown to awaken the soul to self-examination and return to God.",

    "In the book of Job, who tests Job's faith?":
        "Satan (Hebrew: 'the adversary') challenges God that Job is faithful only because of his blessings. God permits Satan to strip everything away. The book's deeper question -- why do the righteous suffer? -- remains one of theology's most challenging problems.",

    "What are the names of Odin's two ravens?":
        "Huginn (Thought) and Muninn (Memory) serve as Odin's intelligence-gathering network, flying across the world each day. Odin worries most about Muninn not returning -- a poignant detail suggesting that wisdom fears forgetfulness above all.",

    "What is 'Tanakh' in Judaism?":
        "Tanakh is an acronym: Torah (Law), Nevi'im (Prophets), Ketuvim (Writings). It contains the same books as the Protestant Old Testament but in a different order, reflecting different theological priorities in how the story of God and Israel unfolds.",

    "What is 'moksha' in Hinduism?":
        "Moksha is liberation from samsara -- the endless cycle of birth, death, and rebirth. It's achieved through self-knowledge, devotion, or righteous action. Once attained, the individual soul recognizes its unity with Brahman and is freed from suffering permanently.",

    "What is 'theosis' in Eastern Orthodox theology?":
        "Theosis (divinization) is the Orthodox teaching that humans can participate in God's divine nature without becoming God. As Athanasius famously put it: 'God became man so that man might become god.' It's the ultimate goal of Christian life in Eastern theology.",

    "What is 'Monophysitism'?":
        "Monophysitism held that Christ had only one nature (divine), effectively absorbing his humanity. The Council of Chalcedon (451) rejected this, insisting Christ is fully God AND fully human in one person -- two natures without confusion or separation.",

    "What is the Mishnah?":
        "Compiled around 200 CE by Rabbi Judah ha-Nasi, the Mishnah organized centuries of oral legal tradition into a systematic code. It became the foundation of the Talmud, which remains the authoritative source of Jewish law to this day.",

    "In Greek mythology, what is the Elysian Fields?":
        "Elysium was the paradise where heroes and the virtuous enjoyed eternal reward after death -- a realm of perpetual spring and contentment. Unlike the Christian heaven, it was reserved for the exceptional few rather than all believers.",

    "What does 'gospel' mean?":
        "The English word 'gospel' comes from Old English 'godspell' (good story), translating the Greek 'euangelion' (good news). In the Roman world, euangelion announced military victories or imperial births -- Christians co-opted it for the announcement of God's victory in Christ.",

    "What is 'Arianism' in Christian theology?":
        "Arius taught that the Son was the first and greatest of God's creations but not co-eternal with the Father. The Council of Nicaea condemned this in 325, but Arianism nearly won -- for decades, most Christians in the Roman Empire held Arian views.",

    "In what language was the New Testament originally written?":
        "The New Testament was written in Koine Greek -- the common Greek of the marketplace, not the literary Greek of philosophers. This reflects Christianity's origins as a movement that spread through ordinary people across the Greek-speaking Roman Empire.",

    "Who was Philo of Alexandria?":
        "Philo (c. 20 BCE - 50 CE) pioneered the allegorical interpretation of scripture, reading the Torah through the lens of Plato. His synthesis of Jewish theology and Greek philosophy profoundly influenced early Christian thinkers like Clement and Origen.",

    "What is 'Docetism' in early Christian theology?":
        "Docetists claimed Christ only 'seemed' (Greek: dokein) to have a body. If true, his suffering and death were illusions -- gutting the meaning of the cross. The church vigorously rejected this because a God who doesn't truly share human suffering can't truly redeem it.",

    "What is the Seder in Jewish tradition?":
        "The Passover Seder is a ritual meal retelling the Exodus story through symbolic foods: bitter herbs (slavery), unleavened bread (hasty departure), and salt water (tears). Each generation is commanded to experience the Exodus as if they personally were freed from Egypt.",

    "What is Yom Kippur?":
        "Yom Kippur (Day of Atonement) is the holiest day in Judaism -- a 25-hour fast devoted to repentance and reconciliation with God. The ancient Temple ritual involved a scapegoat symbolically bearing the people's sins into the wilderness.",

    "What is 'Nestorianism'?":
        "Nestorius taught that Christ's human and divine natures were so distinct that Mary bore only the human Jesus, not God. The Council of Ephesus (431) condemned this, insisting that the two natures are united in one person -- making Mary truly 'Theotokos' (God-bearer).",

    "Which three gifts did the Magi bring to Jesus?":
        "Gold (for a king), frankincense (for a priest or deity), and myrrh (used for burial) -- each gift foreshadowed an aspect of Jesus's identity and mission. The Magi's journey from the East symbolizes that Christ's significance extends beyond Israel to all nations.",

    "Which Roman Emperor called the Council of Nicaea?":
        "Constantine I convened Nicaea in 325 to resolve the Arian controversy that was dividing the empire. He wanted theological unity for political stability -- the first time a Roman emperor intervened directly in Christian doctrinal disputes.",

    "What is the significance of Pentecost in Christianity?":
        "Fifty days after Easter, the Holy Spirit descended on the disciples with tongues of fire, and they spoke in languages everyone could understand. Pentecost reversed the Tower of Babel's division of languages and is considered the birthday of the Christian church.",

    "What is a 'koan' in Zen Buddhism?":
        "A koan is a paradoxical statement or question ('What is the sound of one hand clapping?') designed to break through rational thinking into direct insight. Koans can't be solved by logic -- that's the point. They force the mind beyond its ordinary categories.",

    "What are the Eleusinian Mysteries associated with?":
        "The Mysteries, based on Demeter's search for her kidnapped daughter Persephone, were ancient Greece's most prestigious secret initiation rites. Participants (including emperors) reported life-changing spiritual experiences, but the details were so well guarded that we still don't know exactly what happened.",

    "What are the Dead Sea Scrolls?":
        "Discovered by a Bedouin shepherd in 1947, the Dead Sea Scrolls include the oldest known copies of Hebrew Bible texts -- some 1,000 years older than previously existing manuscripts. They revolutionized our understanding of ancient Judaism and confirmed the remarkable accuracy of biblical text transmission.",

    "Who is the Theotokos?":
        "The title 'Theotokos' (God-bearer) for Mary was affirmed at the Council of Ephesus in 431. It's not primarily a statement about Mary but about Christ: if she bore God incarnate, then Jesus was truly divine from the moment of his conception.",

    "In Norse myth, who is the god of single combat and heroic glory?":
        "Tyr sacrificed his right hand by placing it in the mouth of the wolf Fenrir as a pledge of good faith -- knowing the wolf would bite it off. His sacrifice for the greater good made him the god of justice and self-sacrifice as well as war.",

    "What is the term for the study of the nature and attributes of God?":
        "Theology literally means 'the study of God' (theos + logos). It encompasses everything from biblical interpretation to philosophical arguments for God's existence to ethical implications of divine commands.",

    "What coin was placed in the mouth of the dead in ancient Greece to pay Charon?":
        "An obol (a small silver coin worth about a sixth of a drachma) was placed in the mouth or on the eyes of the dead to pay Charon's fare across the river Styx. Those who couldn't pay were said to wander the riverbank for a hundred years.",

    "What does Augustine's concept of 'original sin' imply about the human condition and the need for grace?":
        "Augustine argued that Adam's fall corrupted all humanity -- not just making sin possible but making it inevitable without divine help. This doctrine grounds the Christian insistence that salvation comes through grace, not moral self-improvement.",

    "What does 'Shema Yisrael' mean?":
        "The Shema ('Hear, O Israel: the LORD our God, the LORD is one') is Judaism's most fundamental prayer, recited morning and evening. It's the first prayer Jewish children learn and traditionally the last words on a dying person's lips.",

    "What does 'polytheism' mean?":
        "Polytheism is belief in many gods, as practiced in ancient Greece, Rome, Egypt, and Norse cultures. Each god typically governed a specific domain (war, love, harvest), reflecting how ancient peoples understood the diverse forces shaping their world.",

    "What is the Synoptic Problem in New Testament scholarship?":
        "Matthew, Mark, and Luke share so much material (sometimes word-for-word) that they clearly have a literary relationship. Most scholars believe Mark was written first and that Matthew and Luke used Mark plus another source ('Q'). Working out the exact relationship is the Synoptic Problem.",

    "Which Norse god guards the Bifrost bridge?":
        "Heimdall, the watchman of the gods, has hearing so keen he can hear grass growing and sight so sharp he can see for hundreds of miles. At Ragnarok, he will sound his horn Gjallarhorn to summon the gods to their final battle.",

    "Why did the Great Schism of 1054 matter beyond church politics, and what theological principle was at stake?":
        "The Schism split Christianity into Roman Catholic and Eastern Orthodox branches over papal authority and the Filioque clause. At its core was a fundamental question: is Christian truth governed by a single supreme authority (the Pope) or by consensus among equal bishops? The answer shaped two civilizations.",

    "What is 'Limbo' in traditional Catholic theology?":
        "Limbo was proposed as a solution to a painful theological dilemma: if baptism is necessary for salvation, what happens to unbaptized infants who bear no personal sin? Limbo offered a place of natural happiness without the beatific vision -- never official dogma, it was quietly set aside by modern theology.",

    "What is the name of the monstrous wolf in Norse mythology who will swallow Odin at Ragnarok?":
        "Fenrir, son of Loki, grew so powerful that the gods bound him with a magical chain. At Ragnarok, he will break free, swallow Odin whole, and then be killed by Odin's son Vidar -- a cycle of destruction and vengeance that defines Norse eschatology.",

    "In Norse mythology, what is Helheim?":
        "Helheim is the cold, dark realm of the dead ruled by Hel, Loki's half-living, half-dead daughter. Unlike Valhalla's glorious warriors, most of the Norse dead -- those who died of illness, old age, or accident -- ended up here.",

    "What community likely produced the Dead Sea Scrolls?":
        "The Essenes were a separatist Jewish sect who withdrew from Jerusalem's Temple establishment to live in ritual purity near the Dead Sea. They preserved and copied scriptures with extraordinary care, giving us texts that illuminate Judaism in Jesus's time.",

    "In Greek mythology, what are the three regions of the underworld?":
        "The Greek underworld was more nuanced than simple heaven-or-hell. Elysium rewarded the virtuous, the Asphodel Meadows held the unremarkable masses, and Tartarus punished the wicked. This three-tiered afterlife reflected Greek views that most people were neither particularly good nor evil.",

    "What are kitsune in Japanese mythology?":
        "Kitsune are foxes that gain supernatural powers and wisdom as they age, growing additional tails (up to nine). They can be benevolent guardians or mischievous tricksters. In Shinto, white kitsune serve as messengers of the rice god Inari.",

    "What is the difference between the Aesir and the Vanir in Norse mythology?":
        "The Aesir (Odin, Thor, Tyr) are warrior gods; the Vanir (Freyr, Freya, Njord) are fertility gods. After a war, the two divine tribes made peace and exchanged hostages, symbolizing the Norse understanding that a society needs both martial strength and agricultural abundance.",

    "What is the Greek concept of the immortal soul called?":
        "Psyche means both 'soul' and 'butterfly' in Greek -- the butterfly's metamorphosis from caterpillar symbolized the soul's transformation beyond death. Plato's philosophy of the immortal soul profoundly influenced Christian, Jewish, and Islamic theology.",

    "In which year was the Council of Nicaea held?":
        "The Council of Nicaea in 325 AD was the first ecumenical (worldwide) council of the Christian church. It established the Nicene Creed, settled the date of Easter, and set precedents for how the church would resolve theological disputes for centuries to come.",

    "What is 'Wu Wei' in Taoism?":
        "Wu Wei ('non-action') doesn't mean laziness but effortless action in harmony with nature's flow. Water is the Taoist model: it's soft yet carves canyons, always finding the path of least resistance while achieving enormous results.",

    "What does 'Te' mean in the Tao Te Ching?":
        "Te is the virtue or power that comes from living in alignment with the Tao. It's not moral virtue earned by effort but natural excellence that flows from harmony with reality -- like a tree growing toward sunlight without trying.",

    "What is the Confucian concept of moral virtue or benevolence?":
        "Ren (humaneness) is the highest Confucian virtue -- the quality that makes us truly human. Confucius defined it as loving others, and it manifests in all proper relationships. A person of ren naturally practices propriety, loyalty, and reciprocity.",

    "What does the Protestant principle of Sola Scriptura mean for the relationship between individual conscience and institutional authority?":
        "Sola Scriptura ('Scripture alone') meant any literate believer could read the Bible and challenge the church if its teachings contradicted scripture. This principle helped democratize religious authority and planted seeds that would flower into broader concepts of individual rights.",

    "What is Sukkot?":
        "Sukkot (Feast of Booths) commemorates the Israelites' 40-year wilderness journey by having families live in temporary shelters for a week. It's a harvest festival that celebrates both divine provision and human vulnerability.",

    "What is the Greek term for the Hebrew underworld or realm of the dead?":
        "Hades served as the Greek translation for the Hebrew Sheol -- the shadowy realm where all the dead resided. In the New Testament, the Greek word Hades is used where the Hebrew Bible would say Sheol, reflecting the cultural translation of afterlife concepts.",

    "What is the symbolic significance of the Tao Te Ching's opening line 'The Tao that can be spoken is not the eternal Tao'?":
        "Laozi's opening line warns that ultimate reality can never be fully captured in language. Words divide, categorize, and limit -- but the Tao precedes all distinctions. It's an invitation to experience reality directly rather than through concepts.",

    "In what year did the Great Schism divide Christianity?":
        "The Great Schism of 1054 was the culmination of centuries of cultural, political, and theological drift between Rome and Constantinople. The mutual excommunications that year formalized a division that persists nearly a thousand years later.",

    "What is the significance of the Peace of Augsburg (1555) for the development of religious liberty and individual conscience?":
        "The Peace of Augsburg established 'cuius regio, eius religio' -- the ruler's religion determines the subjects' religion. Paradoxically, by making religion a matter of territorial politics rather than individual choice, it actually hindered personal religious freedom and set the stage for the Thirty Years' War.",

    "What is 'eschatology' the study of?":
        "Eschatology (from Greek 'eschatos,' meaning 'last') examines ultimate questions: What happens after death? Will history reach a climax? What is the final destiny of creation? Every major religion has eschatological teachings that shape how believers understand the meaning of present suffering.",

    "What is 'satori' in Zen Buddhism?":
        "Satori is a sudden flash of insight that transcends rational thought -- like lightning illuminating a dark landscape. Unlike gradual enlightenment, satori comes in an instant, though years of meditation may prepare the ground. It's Zen's signature experience.",

    "What was Martin Luther's deeper theological objection to indulgences, beyond the corruption of selling them?":
        "Luther's objection went far deeper than the money: indulgences implied that salvation could be earned or purchased, contradicting the gospel's core message that God's forgiveness is a free gift received through faith alone. The entire structure of merit-based religion was at stake.",

    "What is the purpose of a 'mikveh' in Judaism?":
        "The mikveh is a ritual immersion pool used for spiritual purification. It's required before marriage, after menstruation, and for conversion to Judaism. The concept of cleansing through water connects to baptism, which likely drew from Jewish mikveh practice.",

    "What frost giants and fire will signal Ragnarok's approach?":
        "Fimbulwinter is a three-year winter with no summer in between -- the harshest cold the world has ever known. It signals the beginning of the end, as social bonds collapse, brothers kill brothers, and the world descends into chaos before the final battle.",

    "What does 'homoousios' mean in the Nicene Creed?":
        "Homoousios ('of the same substance') was the most controversial word in early Christianity. It declared that the Son shares the identical divine nature with the Father -- not merely similar (homoiousios). That single letter 'i' was literally the difference between orthodoxy and heresy.",

    "What is Hanukkah commemorating?":
        "Hanukkah celebrates the rededication of the Temple in 164 BCE after the Maccabees' revolt against the Seleucid Empire. According to tradition, one day's worth of sacred oil miraculously burned for eight days, which is why Hanukkah is the 'Festival of Lights.'",

    "What are the four Gospels in the New Testament?":
        "Matthew, Mark, Luke, and John each present Jesus from a different angle: Matthew for a Jewish audience, Mark with breathless urgency, Luke with literary polish and concern for outsiders, and John with deep theological reflection. Together they create a multi-dimensional portrait.",

    "What does the term 'monotheism' mean?":
        "Monotheism (from Greek monos 'one' + theos 'god') is the belief in a single God. Judaism, Christianity, and Islam are the three great monotheistic traditions, all tracing their roots to Abraham's radical rejection of the many gods of his culture.",

    "In Greek mythology, who is the goddess of the harvest and agriculture?":
        "Demeter's grief over losing her daughter Persephone to Hades caused the earth to become barren, explaining the origin of winter. When Persephone returns each spring, the earth blooms again. The myth tied agriculture's rhythms to divine emotion.",

    "What is the theological term for the belief that God is all-powerful?":
        "Omnipotence raises one of theology's deepest puzzles: Can God make a stone so heavy he can't lift it? Thomas Aquinas resolved this by arguing that omnipotence means God can do anything logically possible -- logical impossibilities aren't things at all.",

    "What is 'Zen' an abbreviation for?":
        "Zen traces a linguistic journey from the Sanskrit 'Dhyana' (meditation) through Chinese 'Chan' to Japanese 'Zen.' Each translation carried the practice into a new culture, but the core remained the same: direct insight into the nature of mind through meditation.",

    "What is the Haggadah?":
        "The Haggadah is the script for the Passover Seder, retelling the Exodus through questions, songs, and rituals. Its most famous prompt -- 'Why is this night different from all other nights?' -- is asked by the youngest child, ensuring each generation learns the story.",

    "Who descended into the underworld to bring back his wife Eurydice?":
        "Orpheus's music was so beautiful it moved even Hades to release Eurydice -- on the condition that Orpheus not look back until they reached the surface. He looked. The story is one of literature's most heartbreaking explorations of love, trust, and irreversible loss.",

    "What festival commemorates the liberation of the Israelites from Egypt?":
        "Passover (Pesach) recalls the night the angel of death 'passed over' Israelite homes marked with lamb's blood. The Exodus it commemorates became the defining narrative of liberation in Western civilization, invoked by everyone from medieval monks to Martin Luther King Jr.",

    "What is the Nicene-Constantinopolitan Creed?":
        "The expanded Nicene Creed (381 AD) added important statements about the Holy Spirit ('who proceeds from the Father, the Lord and giver of life'). It became the standard creed of Christianity worldwide and is still recited in most Christian worship services today.",

    "What is the concept of 'karma' in Hinduism and Buddhism?":
        "Karma (literally 'action') teaches that every intentional act has consequences that shape your future -- in this life or the next. It's not fatalism but moral physics: you are responsible for the seeds you plant, and you will harvest what grows.",

    "What is Vanaheim in Norse mythology?":
        "Vanaheim is the home of the Vanir gods -- deities of fertility, prosperity, and nature. After the Aesir-Vanir war, the two tribes of gods made peace, and key Vanir like Freyr and Freya came to live in Asgard as honored guests.",

    "What is the Apostles' Creed?":
        "The Apostles' Creed is one of Christianity's oldest statements of faith, traditionally (though not historically) attributed to the twelve apostles. Its simple, declarative structure -- 'I believe in God, the Father Almighty...' -- has been recited by Christians for over 1,500 years.",

    "What does the Protestant concept of justification by faith alone (Sola Fide) imply about human equality before God?":
        "If salvation is a free gift received through faith -- not earned by wealth, learning, or social status -- then the king and the beggar stand on exactly equal ground before God. This theological leveling had revolutionary social implications.",

    "What is 'pantheism'?":
        "Pantheism identifies God with the totality of the universe -- God IS nature, not a being separate from it. Spinoza is its most famous philosophical advocate. Critics argue it eliminates any meaningful distinction between creator and creation.",

    "What major issue did the Council of Nicaea primarily address?":
        "Nicaea's central question was whether Christ was truly God or merely God's greatest creation (Arianism). The answer -- 'begotten, not made, of one substance with the Father' -- established the theological foundation for all subsequent Christian doctrine.",

    # Short entries for remaining theology questions to avoid exceeding limits
    # (Continuing with the same pattern for all remaining questions)

    "What does 'Solus Christus' mean in Reformation theology?":
        "Solus Christus ('Through Christ alone') declares that no saint, priest, or institution mediates between God and humanity except Jesus Christ. It stripped away centuries of accumulated intermediaries and restored a direct relationship between each person and God.",

    "What is Martin Luther's doctrine of 'consubstantiation' (real presence)?":
        "Luther rejected the Catholic view that bread becomes Christ's body, but also rejected the symbolic view. His position: Christ is truly present 'in, with, and under' the bread -- like heat in iron. The bread remains bread, but Christ is really there.",

    "What is the Teleological Argument for God's existence?":
        "The argument from design reasons backward from the order and complexity of nature to an intelligent designer. William Paley's famous analogy: finding a watch on a heath, you'd conclude someone designed it. The universe is far more complex than a watch.",

    "What was the theological consequence of Calvin's doctrine of double predestination for the concept of individual moral agency?":
        "Calvin's doctrine creates a genuine paradox: if God determines who is saved and who is damned before creation, how can humans be morally responsible? Calvin insisted both are true -- divine sovereignty and human responsibility coexist, even if we can't fully reconcile them.",

    "What is 'supralapsarianism' in Calvinist theology?":
        "This tongue-twisting term addresses the logical order of God's decrees: did God choose the elect before or after deciding to permit the Fall? Supralapsarians say election came first, making the Fall a means to an already-determined end.",

    "What is the Deuterocanon?":
        "The Deuterocanonical books (Tobit, Judith, Wisdom, Sirach, Maccabees, etc.) are included in Catholic and Orthodox Bibles but excluded from Protestant ones. The Protestant Reformers followed the Jewish canon, which omitted these Greek-language works.",

    "What is the Immaculate Conception in Catholic teaching?":
        "Commonly confused with the virgin birth of Jesus, the Immaculate Conception actually refers to Mary being conceived without original sin -- a grace applied to her in anticipation of her role as the mother of Christ.",

    "What is the central promise of the Eleusinian Mysteries?":
        "Initiates were promised a blessed afterlife and freedom from the fear of death. Cicero called the Mysteries 'the greatest gift Athens gave the world.' The specific rituals remained secret, but the transformative effect on participants was universally attested.",

    "What was the Augsburg Confession of 1530?":
        "The Augsburg Confession is Lutheranism's founding document, presented to Emperor Charles V by Lutheran princes and theologians. Written primarily by Philip Melanchthon, it sought to demonstrate that Lutheran theology was a reform of Catholicism, not a rejection of it.",

    "Who is famous for the 'watchmaker analogy' argument for God's existence?":
        "William Paley argued in 1802 that just as a watch implies a watchmaker, the complexity of nature implies a divine designer. Darwin's theory of natural selection later offered an alternative explanation, but the argument remains influential in modified form.",

    "Who is considered the father of Reformed theology?":
        "John Calvin's 'Institutes of the Christian Religion' (1536) systematized Protestant theology with a rigor that shaped churches from Geneva to Scotland to the American colonies. His emphasis on God's sovereignty, predestination, and disciplined living defined an entire branch of Christianity.",

    "What is 'deism'?":
        "Deism imagines God as a cosmic watchmaker who built the universe, wound it up, and stepped back. Many Founding Fathers (Jefferson, Franklin, Paine) were deists. It affirms God's existence through reason while rejecting miracles, revelation, and divine intervention.",

    "What was Martin Luther's primary objection to the Catholic Church?":
        "Luther's 95 Theses (1517) targeted the sale of indulgences -- payments that allegedly reduced time in Purgatory. His deeper objection was that the church was selling what only God could freely give: forgiveness. This challenge ignited the Protestant Reformation.",

    "Who formulated the Five Ways (arguments for God's existence)?":
        "Thomas Aquinas presented five logical arguments in the Summa Theologica: from motion, causation, contingency, degrees of perfection, and design. Seven centuries later, they remain the most discussed philosophical arguments for God's existence.",

    "What is the millennium in Christian eschatology?":
        "Revelation 20 describes a 1,000-year reign of Christ. Whether this is literal or symbolic, future or present, has divided Christians for centuries into premillennialists, postmillennialists, and amillennialists -- each with radically different visions of history's direction.",

    "What is 'theologia gloriae' (theology of glory) -- Luther's criticism of it?":
        "Luther contrasted the 'theology of glory' (knowing God through success and power) with the 'theology of the cross' (knowing God through suffering and weakness). The cross reveals that God works through what the world considers failure.",

    "Who was Luis de Molina, and what is he known for in theology?":
        "Molina proposed 'middle knowledge' -- God knows not only what will happen and what could happen, but what would happen in any possible scenario. This elegant solution attempted to preserve both divine sovereignty and human free will.",

    "What is the 'Moral Argument' for God's existence?":
        "If objective moral truths exist (torturing innocents is really wrong, not just unpopular), they seem to require a transcendent foundation. The moral argument reasons from the reality of moral obligation to the existence of a moral lawgiver.",

    "What does Aquinas's theory of natural law imply about the possibility of universal human rights?":
        "If moral law is embedded in human nature and discoverable by reason, then rights aren't granted by governments -- they're inherent. This insight traveled from Aquinas through Locke to Jefferson's 'self-evident truths' in the Declaration of Independence.",

    "What is natural theology?":
        "Natural theology argues that God's existence and attributes can be known through reason and observation of nature alone, without special revelation. It's the foundation for the cosmological, teleological, and moral arguments for God's existence.",

    "What is 'theodicy'?":
        "If God is all-good, all-powerful, and all-knowing, why does evil exist? This is 'the problem of evil,' and theodicy is the attempt to answer it. Proposed solutions include free will, soul-making, and the incomprehensibility of divine purposes.",

    "What is 'natural evil' in theodicy?":
        "Natural evil (earthquakes, disease, tsunamis) is distinct from moral evil (human cruelty) because no human chose it. It poses a sharper challenge to theodicy: free will explains why humans harm each other, but why does nature harm innocents?",

    "What is 'pneumatology' the study of?":
        "Pneumatology (from Greek pneuma, 'spirit' or 'breath') is the study of the Holy Spirit. It addresses the Spirit's role in creation, inspiration of scripture, sanctification of believers, and empowerment of the church.",

    "What is 'double predestination' in strict Calvinist theology?":
        "Double predestination holds that God actively chose some for salvation and others for damnation before creation. It's the most controversial point of Calvinist theology, pushing divine sovereignty to its logical extreme.",

    "What is the hypostatic union?":
        "The hypostatic union, defined at Chalcedon (451), states that Christ is one person with two complete natures -- fully divine and fully human -- united without confusion, change, division, or separation. It's Christianity's most precise and paradoxical doctrinal statement.",

    "What is 'natural law' in Aquinas's theology?":
        "Natural law is moral truth discoverable by reason, reflecting God's eternal law in creation. It grounds ethics in human nature rather than divine command alone, making moral reasoning accessible to all people regardless of religious belief.",

    "What is 'cataphatic theology'?":
        "Cataphatic (positive) theology describes God by affirming attributes: God is good, wise, loving, powerful. It contrasts with apophatic (negative) theology, which describes God only by what God is not. Most theology uses both approaches.",

    "What were the Eleusinian Mysteries?":
        "Held annually at Eleusis near Athens for nearly 2,000 years, the Mysteries were ancient Greece's most important religious ceremony. Initiates from emperors to slaves participated, and all reported transformative experiences -- yet the secret of what actually happened remains unbroken.",

    "What did John Calvin's theology heavily emphasize?":
        "Calvin's theology revolves around God's absolute sovereignty over all things. If God is truly God, Calvin reasoned, nothing can happen outside his will -- including who is saved. This unflinching logic produced one of Christianity's most systematic and controversial theological systems.",

    "What is the Ontological Argument for God's existence?":
        "Anselm's argument is breathtaking in its audacity: if you can conceive of a being greater than which nothing can be conceived, that being must exist in reality (not just in your mind), because existing is greater than not existing. Philosophers have debated it for 900 years.",

    "What is the Euthyphro Dilemma in the philosophy of religion?":
        "Plato's question cuts deep: if God commands what is good, is it good because God says so (making morality arbitrary) or does God command it because it is good (making morality independent of God)? Most theologians answer with a third option: goodness flows from God's nature.",

    "What is 'Dispensationalism'?":
        "Dispensationalism divides history into distinct eras (dispensations) in which God relates to humanity differently. Popular in American evangelicalism, it shapes beliefs about the rapture, tribulation, and the state of Israel.",

    "What was the Council of Trent (1545-1563)?":
        "Trent was the Catholic Church's response to the Protestant Reformation. It reaffirmed Catholic doctrines on scripture-plus-tradition, transubstantiation, and salvation through faith-and-works, while also reforming genuine abuses that had fueled Protestant criticism.",

    "What is 'justification by faith' in Protestant theology?":
        "Justification by faith means God declares sinners righteous based on Christ's merits received through faith -- not based on their own good works. Luther called it 'the article on which the church stands or falls.'",

    "What does 'parousia' mean in New Testament eschatology?":
        "Parousia (Greek for 'arrival' or 'presence') refers to Christ's promised return. In the Roman world, parousia described an emperor's visit to a city -- so applying it to Christ carried the subversive implication that Jesus, not Caesar, is the true ruler of the world.",

    "What is 'perseverance of the saints' in Calvinist theology?":
        "The 'P' in TULIP teaches that the truly elect will never permanently fall away from faith. It's not that they can't sin, but that God's grace will always bring them back. This doctrine provides assurance of salvation -- once saved, always saved.",

    "What is William of Ockham famous for in medieval philosophy?":
        "Ockham's Razor -- 'do not multiply entities beyond necessity' -- became one of the most powerful principles in both philosophy and science. It favors simpler explanations over complex ones, and it's been shaving unnecessary assumptions from theories for 700 years.",

    "In which year did Martin Luther post his 95 Theses?":
        "October 31, 1517, is considered the birthday of the Protestant Reformation. Luther nailed (or mailed) his 95 Theses to the Wittenberg church door, challenging the sale of indulgences. Thanks to the printing press, his arguments spread across Europe within weeks.",

    "What is 'penal substitution' in atonement theory?":
        "Penal substitution holds that Christ took the punishment humanity deserved for sin, satisfying God's justice while offering mercy. It's the dominant atonement theory in Protestant theology, though other models (moral exemplar, Christus Victor) have their advocates.",

    "What is 'soteriology' the study of?":
        "Soteriology (from Greek soteria, 'salvation') is the study of how salvation works. How is a person saved? By faith? Works? Grace? Predestination? Free choice? These questions have generated Christianity's most passionate and divisive debates.",

    "Who was Jacob Arminius?":
        "Arminius (1560-1609) challenged Calvinist predestination, arguing that God's grace can be resisted by human free will. His followers, the Remonstrants, were condemned at the Synod of Dort, but Arminian theology lives on in Methodism and much of global Christianity.",

    "What is 'federal headship' in Reformed theology?":
        "Federal headship teaches that Adam acted as humanity's representative -- like a president declaring war on behalf of a nation. When Adam sinned, his guilt was imputed to all his descendants. Christ, the 'second Adam,' reverses this by representing believers before God.",

    "What is the 'via media' concept in Anglican theology?":
        "The 'middle way' positions Anglicanism between Roman Catholicism's hierarchy and Protestantism's radical reform. It retains bishops and liturgy while affirming scripture's authority -- a compromise that gives Anglicanism remarkable theological breadth.",

    "Who wrote 'Summa Theologica', the great synthesis of Christian theology?":
        "Thomas Aquinas's Summa Theologica (1265-1274) is one of the most ambitious intellectual achievements in Western history. It systematically addresses virtually every theological and philosophical question using Aristotelian logic, and it remains the foundation of Catholic intellectual tradition.",

    "What is the Septuagint?":
        "The Septuagint (LXX) is the Greek translation of the Hebrew scriptures, completed in Alexandria around the 3rd-2nd centuries BCE. When New Testament authors quote the Old Testament, they usually quote the Septuagint -- making it enormously influential in shaping Christian theology.",

    "Who are the Norns in Norse mythology?":
        "The three Norns -- Urd (Past), Verdandi (Present), and Skuld (Future) -- weave the fate of gods and mortals at the foot of Yggdrasil. Even Odin cannot override their decrees. In Norse thought, fate is the one power greater than the gods.",

    "Where was Martin Luther excommunicated and asked to recant?":
        "At the Diet of Worms in 1521, Luther famously declared: 'Here I stand, I can do no other.' His refusal to recant before Emperor Charles V established the principle that individual conscience, informed by scripture, can stand against the most powerful institutions on earth.",

    "What is the 'analogia fidei' (analogy of faith) principle?":
        "The analogy of faith means scripture interprets scripture -- obscure passages should be read in light of clear ones. It prevents pulling individual verses out of context and ensures that the Bible's overall message guides interpretation of its parts.",

    "What is Arminianism?":
        "Arminianism, following Jacob Arminius, teaches that God's grace enables but doesn't force the human will -- people can freely accept or reject salvation. It's the theological engine behind Methodism, most Pentecostalism, and much of global evangelical Christianity.",

    "What is 'realized eschatology' in New Testament scholarship?":
        "C.H. Dodd argued that when Jesus said 'the kingdom of God is at hand,' he meant it had already arrived in his ministry. The miracles, teachings, and resurrection weren't pointing to a future kingdom -- they WERE the kingdom breaking into the present.",

    "What was Jan Hus's fate at the Council of Constance?":
        "Jan Hus was burned at the stake in 1415 despite having been promised safe conduct. His execution for advocating reform -- a century before Luther -- made him a martyr and national hero in Bohemia, and it demonstrated why Luther wisely refused to attend councils without armed protection.",

    "Who founded Pietism?":
        "Philipp Jakob Spener's 'Pia Desideria' (1675) launched Pietism by calling for personal Bible study, lay participation, and heart-felt faith over dry orthodoxy. Pietism's emphasis on experiential religion influenced Methodism, evangelicalism, and modern worship culture.",

    "What was Ulrich Zwingli's view of the Eucharist?":
        "Zwingli insisted that 'This is my body' means 'This represents my body' -- pure symbol, no real presence. His disagreement with Luther on this point at the Marburg Colloquy (1529) prevented Protestant unity and shaped two distinct streams of Reformation theology.",

    "What is 'compatibilism' in the debate about free will and God?":
        "Compatibilism argues that divine sovereignty and human freedom aren't contradictory -- they operate at different levels. God can ordain events through secondary causes (human choices) that are genuinely free from the human perspective. It's the mainstream position in most Reformed theology.",

    "Who were the Anabaptists during the Reformation?":
        "The Anabaptists ('re-baptizers') insisted that only adults who consciously chose faith should be baptized. This seemingly simple position was revolutionary: it implied separation of church and state, voluntary religion, and pacifism. Modern Mennonites, Amish, and Baptists trace their heritage to them.",

    "Who founded Methodism?":
        "John Wesley (1703-1791) founded Methodism within the Church of England, emphasizing personal holiness, disciplined spiritual life, and social justice. His open-air preaching reached coal miners and factory workers whom the established church had largely ignored.",

    "What is 'inaugurated eschatology'?":
        "Inaugurated eschatology holds that Christ's kingdom has 'already' begun but is 'not yet' fully realized. We live between D-Day (Christ's decisive victory) and V-Day (his final return). This 'already but not yet' framework resolves the tension between present suffering and future hope.",

    "What is 'hermeneutics' in biblical studies?":
        "Hermeneutics is the art and science of interpretation -- the rules for understanding what a text means. Biblical hermeneutics considers historical context, literary genre, original language, and theological tradition to determine what scripture intended to communicate.",

    "What was John Wycliffe's contribution to the Reformation?":
        "Wycliffe translated the Bible into English in the 1380s -- 130 years before Luther. He argued that scripture, not the Pope, was the ultimate authority. Though condemned as a heretic, his ideas traveled to Bohemia and influenced Jan Hus, who influenced Luther.",

    "What is 'unconditional election' in Calvinism?":
        "Unconditional election means God chose who would be saved based solely on his sovereign will, not on anything foreseen in the person -- no predicted faith, no moral merit, nothing. It's the 'U' in TULIP and one of the most debated doctrines in Christian history.",

    "What is 'total depravity' in Calvinist theology?":
        "Total depravity doesn't mean humans are as evil as possible -- it means every part of human nature (mind, will, emotions) is affected by sin. Without grace, we consistently choose self over God. It's the 'T' in TULIP.",

    "What is 'process theology'?":
        "Process theology, influenced by philosopher Alfred North Whitehead, reimagines God as not omnipotent but as one who persuades rather than coerces. God grows and changes with the world, experiencing creation's joys and sorrows. Traditional theists find this a radical departure from classical theism.",

    "What is Calvin's doctrine of predestination?":
        "Calvin taught that before creation, God sovereignly determined who would be saved and who would not. This doctrine follows logically from God's omniscience and sovereignty but creates profound tension with human intuitions about justice and free will.",

    "What are the names of the three main Norns?":
        "Urd (What Has Become), Verdandi (What Is Becoming), and Skuld (What Shall Be) represent past, present, and future. They water Yggdrasil and carve runes of fate. Even the gods cannot change what the Norns decree.",

    "What is 'open theism'?":
        "Open theism proposes that God chose to limit his knowledge of future free choices to preserve genuine human freedom. It's controversial because it challenges classical theism's insistence on exhaustive divine foreknowledge.",

    "What is 'irresistible grace' in Calvinist theology (TULIP)?":
        "The 'I' in TULIP teaches that when God's Spirit calls the elect, they cannot ultimately resist. It doesn't mean they're dragged kicking and screaming -- rather, grace transforms their desires so they freely and gladly respond to God.",

    "What is Fimbulwinter in Norse mythology?":
        "Fimbulwinter ('great winter') is a three-year winter with no summer that heralds Ragnarok. It's not just bad weather -- it's cosmic breakdown. Morality collapses, families turn on each other, and the world prepares for its final destruction and renewal.",

    "What is 'theologia crucis' (theology of the cross) in Luther?":
        "Luther's theology of the cross insists that God is revealed not in power and glory but in suffering and weakness. The cross looks like defeat but is actually victory. This paradox -- God's strength made perfect in weakness -- is the theological heart of Lutheranism.",

    "What is 'premillennialism'?":
        "Premillennialism teaches that Christ will return before the 1,000-year reign described in Revelation 20. The world will get worse before it gets better, and only Christ's physical return will establish justice on earth.",

    "What is 'limited atonement' in Calvinist theology?":
        "The 'L' in TULIP holds that Christ died specifically to save the elect -- his death was sufficient for all but intended only for those God chose. Arminians counter that Christ died for everyone, but its efficacy depends on individual faith.",

    "Who proposed the 'Christus Victor' theory of atonement?":
        "Gustaf Aulen's 1931 book revived the early church's view that Christ's death was a victory over the powers of sin, death, and the devil -- not a payment to God or moral example, but a cosmic liberation. It's the oldest theory of atonement.",

    "What is Anselm's 'satisfaction theory' of atonement?":
        "Anselm argued that humanity's sin dishonored God's infinite dignity, creating a debt only a God-man could pay. Christ's death 'satisfied' this debt. The theory shaped medieval theology and remains influential in Catholic thought.",

    "What is the Synod of Dort (1618-1619)?":
        "Dort was Calvinism's defining council, convened to address the Arminian challenge. Its five points of Calvinism (TULIP) became the gold standard of Reformed orthodoxy, and the condemned Arminians were expelled from the Dutch Reformed Church.",

    "Who originally formulated the Ontological Argument?":
        "Anselm of Canterbury proposed the argument in his Proslogion (1078). Even Anselm's contemporary Gaunilo objected (could you prove a 'perfect island' exists the same way?), but the argument has fascinated and frustrated philosophers for nearly a millennium.",

    "What does TULIP stand for in Calvinist theology?":
        "TULIP summarizes Calvinist soteriology: Total depravity, Unconditional election, Limited atonement, Irresistible grace, Perseverance of the saints. These five points were systematized at the Synod of Dort (1618-19) in response to Arminian challenges.",

    "Who is most associated with the phrase 'leap of faith' in theology?":
        "Kierkegaard argued that authentic faith requires a leap beyond what reason can prove. You can't argue your way to God -- at some point you must jump. This existentialist insight influenced Protestant theology, Catholic existentialism, and even secular philosophy.",

    "What is the Reformation principle of 'Sola Gratia'?":
        "Sola Gratia ('by grace alone') means salvation is entirely God's gift -- humans cannot earn, deserve, or contribute to it. This principle levels all human pretensions: the saint and the sinner are equally dependent on divine mercy.",

    "What is 'Transubstantiation' in Catholic teaching?":
        "Transubstantiation holds that during Mass, the bread and wine literally become Christ's body and blood while retaining their physical appearances. This doctrine, formalized at the Fourth Lateran Council (1215), is one of the sharpest theological divides between Catholics and Protestants.",

    "What is the Book of Concord (1580)?":
        "The Book of Concord is Lutheranism's doctrinal constitution, collecting the Augsburg Confession, Luther's catechisms, and other key documents. It defines what Lutherans believe on every major theological question and remains binding for confessional Lutheran churches.",

    # Tier 5 theology (select key questions)
    "What is 'demythologization' in modern theology?":
        "Rudolf Bultmann argued that the New Testament's miracles and cosmic imagery are mythological packaging for existential truths. Demythologization reinterprets them: the resurrection isn't a historical event but a symbol of new authentic existence. Critics say this guts Christianity of its content.",

    "Who wrote 'Revelations of Divine Love'?":
        "Julian of Norwich, a 14th-century English anchoress, received 16 visions during a near-death illness and spent 20 years meditating on their meaning. Her optimistic theology -- 'All shall be well' -- stands out in an era dominated by plague, war, and fear.",

    "What is John Scotus Eriugena known for?":
        "This 9th-century Irish philosopher daringly argued that God both creates and is created through the universe -- a form of Christian panentheism. His 'Periphyseon' was one of the most original philosophical works of the early medieval period, and it was eventually condemned.",

    "Who wrote 'De Principiis' (On First Principles), the first systematic Christian theology?":
        "Origen of Alexandria (c. 185-254) was Christianity's first great systematic thinker. His controversial ideas -- including the pre-existence of souls and the eventual salvation of all beings -- pushed the boundaries of orthodoxy while laying the groundwork for all subsequent theology.",

    "What is 'sunyata' in Buddhism?":
        "Sunyata (emptiness) doesn't mean 'nothingness' but the absence of inherent, independent existence. Everything arises in dependence on conditions. Realizing this liberates from attachment -- you can't cling to what was never solid in the first place.",

    "What is Pascal's Wager?":
        "Blaise Pascal argued that believing in God is the rational bet: if God exists, you gain everything; if not, you lose nothing. Critics note that it doesn't specify which god to believe in and that calculating one's way to faith seems inauthentic.",

    "In Gnosticism, what is the Demiurge?":
        "The Demiurge is a lesser, ignorant deity who mistakenly created the material world. In Gnostic thought, the true God is utterly transcendent, and our physical existence is a cosmic mistake. Salvation means escaping matter through secret knowledge (gnosis).",

    "What is 'the cloud of unknowing'?":
        "This anonymous 14th-century English text teaches that God cannot be reached by thought but only by love. The contemplative must place a 'cloud of forgetting' beneath them (all concepts) and reach upward through a 'cloud of unknowing' with the heart alone.",

    "What is 'dependent origination' (pratityasamutpada) in Buddhism?":
        "Everything arises in dependence on conditions -- nothing exists independently or permanently. This 12-linked chain explains how ignorance leads to craving, craving to attachment, and attachment to suffering. Understanding it breaks the chain.",

    "Who is Surtr in Norse mythology?":
        "Surtr is the fire giant who will set the entire world ablaze at Ragnarok, destroying everything so that a new, green earth can rise from the sea. He embodies the Norse belief that destruction is the necessary precursor to renewal.",

    "Who are the children Loki had with the giantess Angrboda?":
        "Fenrir (the wolf who will swallow Odin), Jormungandr (the World Serpent who will kill Thor), and Hel (ruler of the dead). Loki's monstrous children are the agents of Ragnarok -- chaos itself, born from the trickster god.",

    "What is the Havamal?":
        "The Havamal ('Sayings of the High One') contains Odin's practical wisdom: advice on hospitality, friendship, caution, and the pursuit of knowledge. It's the closest thing to Norse scripture -- earthy, pragmatic, and deeply human.",

    "What is the Zohar in Jewish mysticism?":
        "The Zohar is Kabbalah's foundational text, a mystical commentary on the Torah traditionally attributed to the 2nd-century sage Shimon bar Yochai but likely compiled in 13th-century Spain. It reveals hidden spiritual dimensions in every verse of scripture.",

    "Who was Meister Eckhart?":
        "Eckhart (c. 1260-1328) was a German Dominican mystic who taught that the soul's deepest ground is identical with God's ground. His sermons were so radical that some were condemned as heretical, yet his influence on Western mysticism is immeasurable.",

    "What is apophatic theology?":
        "Apophatic theology describes God only by negation: God is not finite, not limited, not comprehensible. By stripping away everything God is NOT, it gestures toward a reality beyond all human categories. It's the mystical tradition's most rigorous method.",

    "Who is the supreme god of Zoroastrianism?":
        "Ahura Mazda ('Wise Lord') is the supreme deity of Zoroastrianism, the world's first major monotheistic religion. Founded by the prophet Zoroaster (c. 1000 BCE), its concepts of heaven, hell, angels, and a final judgment influenced Judaism, Christianity, and Islam.",

    "What is the evil spirit opposed to Ahura Mazda in Zoroastrianism?":
        "Angra Mainyu (Ahriman) is the destructive spirit locked in cosmic battle with Ahura Mazda. Zoroastrianism's moral dualism -- good versus evil as cosmic forces -- profoundly influenced later religious thought about Satan, demons, and the struggle between light and darkness.",

    "What is 'tikkun olam' in Jewish theology?":
        "Tikkun olam ('repair of the world') teaches that humans are God's partners in completing creation. In Lurianic Kabbalah, divine sparks scattered at creation must be gathered through righteous action. It grounds social justice in mystical theology.",

    "What is the theological concept of 'imago Dei,' and what are its implications for human rights?":
        "If every human bears God's image, then every human has inherent, inviolable dignity. This principle became the theological foundation for universal human rights, the abolition of slavery, and the recognition that no state can grant or revoke a person's fundamental worth.",

    "How did Augustine's 'just war' criteria limit the permissible use of violence by Christian rulers?":
        "Augustine established that war must have a just cause, legitimate authority, and right intention. These criteria didn't abolish war but placed moral constraints on it -- rulers could no longer wage war for plunder or personal glory without theological condemnation.",

    "What did Aquinas add to Augustine's just war criteria that is most relevant to limiting civilian casualties?":
        "Aquinas added proportionality: the harm caused by war must not exceed the good achieved, and noncombatants must be protected. This principle remains central to international humanitarian law and the Geneva Conventions.",

    "How did the Protestant Reformation's emphasis on Scripture and individual conscience contribute to modern concepts of freedom of religion?":
        "By insisting that each person must read and interpret Scripture for themselves, the Reformers established that faith cannot be coerced. This principle -- conscience must be free -- became the seedbed from which modern religious liberty grew.",

    "What was the theological argument used by abolitionists like William Wilberforce against the institution of slavery?":
        "Wilberforce argued from imago Dei: if all humans are made in God's image, then enslaving any person violates their God-given dignity. This theological argument, combined with relentless political activism, ended the British slave trade in 1807.",

    "What is the theological concept of 'conscience' in Christian moral theology, and why does it create a limit on state authority?":
        "Conscience is the inner tribunal where each person discerns right from wrong before God. Because conscience answers to God rather than the state, it creates an inviolable space that no government can legitimately invade -- the theological root of all civil liberties.",

    "What was Luther's argument at the Diet of Worms that established the primacy of individual conscience?":
        "Luther's famous declaration -- 'Unless I am convicted by Scripture and plain reason, I cannot and will not recant, for it is neither safe nor right to go against conscience' -- established that individual moral conviction, grounded in reason and revelation, can legitimately defy institutional authority.",

    "What theological principle grounds the idea that governments derive their just powers from the consent of the governed?":
        "Covenant theology taught that God relates to people through binding agreements with mutual obligations. If God himself governs through covenant rather than raw power, then human rulers too must be accountable to those they govern -- authority is conditional, not absolute.",

    "What is the theological concept of 'redemption' in Christianity, and why does it emphasize individual rather than collective salvation?":
        "Christ redeems persons individually through personal faith. You cannot be saved by your family, nation, or church membership -- each soul must respond to God personally. This emphasis on individual spiritual responsibility helped shape Western individualism.",

    "What does Jesus's teaching 'Render unto Caesar what is Caesar's, and unto God what is God's' establish in Christian political theology?":
        "This deceptively simple statement established that civil and divine authority operate in distinct domains. Caesar has legitimate claims (taxes, civil order) but NOT over the soul. It planted the seed of church-state separation that would reshape Western civilization.",

    "How does the historical record of theocratic governments compare to secular ones in protecting individual rights?":
        "History shows that concentrating both religious and political power in the same hands reliably produces oppression. The separation of these two powers -- each checking the other -- has proven the most effective arrangement for protecting individual freedom.",

    "What was the significance of the Edict of Milan (313 AD) for religious freedom in Christian history?":
        "The Edict of Milan declared religious tolerance throughout the Roman Empire, ending centuries of persecution. Its revolutionary principle -- that religious belief must not be coerced -- was frequently violated in later centuries but remained an ideal that reformers could invoke.",

    "What was the Inquisition's theological rationale, and why did most later Christian thinkers reject it?":
        "The Inquisition claimed authority to enforce correct belief by punishment. Later theologians recognized the fatal flaw: coerced faith is not genuine faith. As Roger Williams argued, forced religion produces hypocrisy, not holiness.",

    "How did the theology of the Sermon on the Mount challenge Roman concepts of power and status?":
        "By blessing the poor, the meek, and the persecuted, Jesus turned Roman values upside down. In a culture that worshipped military conquest and social dominance, declaring that the humble inherit the earth was revolutionary -- and it remains so.",

    "What is the theological concept of 'stewardship,' and how does it define the human relationship to property and creation?":
        "Stewardship means humans are caretakers, not absolute owners. Everything belongs to God; we manage it on trust. This creates moral obligations: wealth must serve the common good, and creation must be tended, not exploited.",

    "What theological principle did Roger Williams invoke to argue for separation of church and state in colonial Rhode Island?":
        "Williams argued that a state-enforced church corrupts genuine religion by turning authentic faith into mere civic compliance. Only voluntary, freely chosen faith honors God. His colony of Rhode Island became America's first experiment in full religious freedom.",

    "What is the theological concept of 'sin' as personal moral failure, and how does it differ from the idea of sin as merely ritual impurity?":
        "Prophetic Judaism and Christianity transformed sin from ritual impurity (fixable by ceremonies) into personal moral failure (requiring inner change). Sin damages your relationship with God and others -- and only genuine repentance, not ritual, can repair it.",

    "How did early Christianity's concept of the soul's equal worth before God challenge ancient Greco-Roman social hierarchies?":
        "Paul's declaration that 'in Christ there is neither slave nor free, male nor female' was dynamite in a rigidly hierarchical society. If every soul has infinite worth before God, then social distinctions -- however powerful -- are ultimately provisional and secondary.",

    "What is the prophetic tradition in Judaism, and how does it create a moral check on political power?":
        "The Hebrew prophets -- Nathan confronting David, Elijah opposing Ahab -- established that even kings answer to a higher moral law. No political power is absolute because God's justice stands in judgment over every ruler. This tradition shaped the entire Western concept of accountable government.",

    "What does the theology of the 'image of God' (imago Dei) imply about how criminals and enemies should be treated?":
        "If even the worst criminal bears God's image, then there are limits on punishment. Torture, degradation, and denial of due process violate the divine image in every person. This principle has been invoked from the abolition of torture to modern human rights declarations.",

    "How did the Puritan concept of 'calling' (vocation) transform the idea that ordinary work has spiritual value?":
        "Luther and Calvin taught that a farmer plowing a field serves God just as much as a monk praying in a cell. This 'democratization of holiness' dignified all honest labor and motivated the work ethic that Max Weber famously linked to capitalism's rise.",

    "What is 'covenant' in biblical theology, and how does it differ from a simple contract?":
        "A covenant creates a relationship -- like marriage -- not just a transaction. God's covenant with Israel involves total mutual commitment: 'I will be your God, and you will be my people.' Breaking a covenant isn't just a legal violation; it's a betrayal of relationship.",

    "What is the theological argument of Martin Luther King Jr. for civil disobedience against unjust laws?":
        "King drew directly on Aquinas: an unjust law contradicts natural moral law and therefore has no true authority. Conscience must resist it -- not through violence but through nonviolent witness that exposes injustice and appeals to the oppressor's own moral sense.",

    "What is the theological basis for the concept of 'human dignity' in Catholic Social Teaching?":
        "Catholic Social Teaching grounds human dignity in three facts: every person is created in God's image, redeemed by Christ, and called to eternal life. Because dignity comes from God, no government, institution, or social condition can diminish it.",

    "What is the significance of the concept of 'repentance' (metanoia) in Christianity for individual moral responsibility?":
        "Metanoia means a complete turning around -- not just feeling sorry but fundamentally reorienting your life toward God. It requires personal acknowledgment of specific wrongs, placing moral responsibility squarely on the individual.",

    "How does Buddhism's concept of individual karma differ from the Judeo-Christian concept of individual moral responsibility?":
        "Both hold individuals accountable, but karma operates as an impersonal moral law (actions automatically produce consequences), while Judeo-Christian morality involves a personal God who judges, forgives, and restores. The Buddhist path emphasizes understanding; the Abrahamic path emphasizes relationship.",

    "What is the theological concept of 'grace' in Reformation thought, and why did it matter for how individuals approach God?":
        "Grace is God's unearned, unmerited favor. If salvation is purely God's gift, then no one can buy, earn, or inherit it through social status or religious performance. Grace is the great equalizer -- every person approaches God on exactly the same footing.",

    "What does Thomas Aquinas argue about whether an unjust law has moral authority?":
        "Aquinas declared flatly: 'An unjust law is no law at all.' Laws that violate natural moral law lack the binding force of genuine law. This principle was directly invoked by Martin Luther King Jr. in his 'Letter from Birmingham Jail.'",

    "What is the concept of 'theodicy' and what does the problem of evil reveal about the limits of our understanding of God?":
        "If God is all-good and all-powerful, why does evil exist? No fully satisfying answer has ever been found. The honest theological response is humility: the problem reveals that human reason has limits when confronting the mystery of divine purposes.",

    "What is the theological concept of 'forgiveness' in Christianity, and how does it differ from mere tolerance or indifference?":
        "Forgiveness isn't pretending no wrong occurred or shrugging it off. It acknowledges the genuine evil of the offense and then voluntarily releases the claim for retribution. It requires moral courage precisely because it takes wrong seriously.",

    "What does the Book of Job conclude about the relationship between suffering and moral deserving?":
        "Job's suffering was undeserved, and God's answer from the whirlwind never explains why it happened. Instead, God reveals a cosmic perspective that transcends human moral accounting. The book's conclusion: sometimes suffering has no discernible moral cause, and demanding an explanation may be the wrong response.",

    "What does the Hebrew concept of 'shalom' mean beyond simple peace?":
        "Shalom encompasses wholeness, flourishing, justice, health, and right relationship -- the state of all things being as they should be. It's not merely the absence of conflict but the active presence of complete well-being in every dimension of life.",

    "What theological concept does the Parable of the Lost Sheep illustrate about God's concern for individuals?":
        "The shepherd's willingness to leave 99 sheep to find one lost lamb reveals a God whose love is not utilitarian. Every individual has irreducible worth. This parable is a standing rebuke to any system that sacrifices persons for the sake of the collective.",

    "What is the theological concept of the 'incarnation' (God becoming human), and why does it matter for Christian ethics?":
        "If God entered material existence as a human being, then bodies, physical needs, and earthly suffering are not mere distractions from spiritual life -- they are the very arena where God chose to act. The incarnation makes all of human life sacred.",

    "What does the Islamic concept of 'khilafa' (human vicegerency) imply about humanity's role toward creation?":
        "In Islam, humans serve as God's stewards (khalifa) on earth -- trusted with authority over creation but accountable to God for how they exercise it. Dominion is a responsibility, not a license for exploitation.",

    "What was the Barmen Declaration (1934) and why is it theologically significant?":
        "The Confessing Church's declaration against Nazism affirmed that Christ alone -- not the state, not a political leader -- is Lord. It established that the church must say 'No' when any ideology claims absolute authority that belongs to God alone.",

    "What is the concept of 'anonymous Christianity' proposed by Karl Rahner, and what is the main objection to it?":
        "Rahner argued that people who've never heard the gospel may be saved through Christ unknowingly if they follow their conscience. The main objection: it's patronizing to call someone a 'Christian' without their knowledge or consent.",

    "What did Kierkegaard mean by his 'three stages' of human existence (aesthetic, ethical, religious)?":
        "Kierkegaard mapped three ways of living: for pleasure (aesthetic), for duty (ethical), and for God (religious). Each reveals the inadequacy of the previous stage. The move from ethical to religious requires a 'leap of faith' beyond what reason can justify.",

    "What is the theological concept of 'simul justus et peccator' in Luther's theology?":
        "Luther insisted that Christians are simultaneously wholly righteous (through Christ's imputed righteousness) and wholly sinful (in their own nature). This paradox captures the lived experience of faith: justified yet still struggling with sin every day.",

    "What was the theological basis of the Social Gospel movement in early 20th century America?":
        "The Social Gospel argued that the Kingdom of God demands transforming unjust social structures, not just saving individual souls. Poverty, child labor, and exploitation are collective sins requiring collective repentance. Walter Rauschenbusch was its most influential voice.",

    "What is the principle of 'double effect' in Catholic moral theology?":
        "Double effect permits actions with harmful side effects IF the good effect is intended, the harm is unintended though foreseen, and the good proportionately outweighs the harm. It's applied in medical ethics, military decisions, and everyday moral dilemmas.",

    "What does the concept of the 'common good' in Catholic Social Teaching require of individuals and political institutions?":
        "The common good demands conditions in which all persons can flourish. Neither pure individualism (ignoring community needs) nor collectivism (ignoring individual rights) satisfies it. Both persons and institutions must actively pursue the conditions that enable everyone to thrive.",

    "What does the theological concept of 'lament' in the Psalms reveal about honest faith?":
        "The lament psalms show that authentic faith includes wrestling with God -- crying out in grief, anger, and confusion. Faith that only praises is incomplete. The Psalms teach that God can handle our honesty, including our darkest questions.",

    "What is the theological concept of 'agape' (divine love), and how does it differ from erotic love or friendship?":
        "Agape is unconditional love that seeks the other's good regardless of merit or return. Unlike eros (romantic desire) or philia (reciprocal friendship), agape loves even when there is nothing to gain. It's the love that defines God's character and the ideal for Christian ethics.",

    "What does the Decalogue's prohibition 'You shall not bear false witness' imply about the social foundations of justice?":
        "Without truthful testimony, justice systems become tools of power rather than instruments of truth. The commandment protects the integrity of legal proceedings on which the weak depend for protection against the strong.",

    "How does the biblical concept of the Jubilee Year challenge absolutist claims about private property?":
        "The Jubilee (Leviticus 25) commanded cancellation of debts and return of land every 50 years, asserting God's ultimate ownership over all things. Property rights are real but not absolute -- they are limited by the community's need for justice and equity.",

    "What does the story of Cain and Abel establish about moral responsibility in the Judeo-Christian tradition?":
        "God's question 'Where is your brother?' establishes that we ARE our brother's keeper. Individual moral responsibility extends beyond ourselves -- indifference to another's suffering is itself a moral failure, not a neutral position.",

    "What is the theological concept of 'eschatological hope' and how does it motivate moral action in the present?":
        "Belief that God will ultimately set all things right doesn't produce passivity -- it motivates action. If justice is the destination of history, then working for justice now aligns with the deepest currents of reality. Hope is fuel for engagement, not escape.",

    "How does Buddhist ethics differ from Christian ethics in its approach to moral motivation?":
        "Buddhism motivates moral behavior through understanding: clearly seeing reality removes greed, hatred, and delusion. Christianity motivates through love of a personal God and neighbor. Both produce compassionate action, but through fundamentally different inner dynamics.",

    "What is the theological concept of 'free will' mean in the context of salvation, and why is it philosophically difficult?":
        "If God foreknows everything, can choices be genuinely free? If humans are truly free, can God guarantee anything? This tension between divine sovereignty and human freedom has generated centuries of debate among Calvinists, Arminians, Molinists, and open theists -- with no resolution in sight.",

    "What is the concept of 'subsidiarity' in Catholic Social Teaching, and what does it imply about the organization of society?":
        "Subsidiarity holds that decisions should be made at the lowest competent level -- families and local communities before the state. It's a theological check on centralized power, arguing that human dignity requires the greatest possible scope for local initiative and personal responsibility.",

    "How did the theology of the Exodus narrative function as a liberation theology throughout Western history?":
        "The Exodus -- God delivering enslaved Israel from Pharaoh -- has been invoked by every liberation movement in Western history: American slaves singing 'Go Down, Moses,' civil rights marchers, and Latin American liberation theologians. It's the paradigmatic story of God siding with the oppressed.",

    "What was the theological argument for the separation of church and state in John Locke's Letter Concerning Toleration?":
        "Locke argued that the magistrate's authority covers civil goods (life, property) but not the soul, because coercion cannot produce genuine belief. A state church doesn't create real Christians -- it creates hypocrites who conform outwardly while dissenting inwardly.",

    "What is the concept of 'prevenient grace' in Arminian theology, and why does it matter for free will?":
        "Prevenient grace is God's enabling grace that goes before human decision, giving the will the ability (but not the compulsion) to respond to God. It preserves genuine free choice while acknowledging that without divine help, humans cannot choose salvation.",

    "What is the relationship between the Ten Commandments and natural law in Aquinas's theology?":
        "Aquinas argued that the Commandments don't introduce new moral knowledge -- they clarify what human reason could already discover. They're divine confirmation of natural moral law, which is why even non-believers can recognize their basic moral content.",

    "How does the Torah's command to love the stranger ('you were strangers in Egypt') function as a theological basis for human rights?":
        "By grounding obligation to outsiders in shared memory of vulnerability, the Torah establishes that moral duty extends beyond one's own community. Because Israel knew what it was like to be powerless, they must protect those who are powerless now.",

    "What is the theological concept of 'vicarious atonement,' and what does it imply about collective vs. individual guilt?":
        "Vicarious atonement -- one person bearing punishment for others -- raises the question of whether guilt can be transferred. It's theologically powerful (Christ bearing humanity's sin) but philosophically controversial (how can the innocent justly suffer for the guilty?).",

    "What is the significance of the biblical injunction to not oppress the widow, the orphan, the poor, or the stranger?":
        "These four categories represent the most vulnerable members of ancient society -- those without male protectors in a patriarchal world. God declares their protection not as optional charity but as mandatory justice, with divine consequences for failure.",

    "What is the Augustinian concept of the 'Two Cities,' and what does it imply about the limits of political life?":
        "Augustine distinguished the City of God (ordered by love of God) from the City of Man (ordered by self-love). Political life can create order but never ultimate fulfillment -- a permanent check on utopian politics and a reminder that no earthly regime is God's kingdom.",

    "How does the Sermon on the Mount's command 'Love your enemies' challenge ordinary tribal moral logic?":
        "Most moral systems limit obligations to the in-group. Jesus's command to love enemies breaks this boundary entirely, modeling ethics on God's own character: 'He sends rain on the just and unjust alike.' It's perhaps the most challenging moral demand in any religious tradition.",

    "What was John Paul II's theological argument for human dignity as the basis for resisting communist totalitarianism?":
        "John Paul II argued that human dignity comes from God, not the state. Because the state cannot grant dignity, it cannot revoke it. Totalitarianism -- which claims absolute authority over persons -- is therefore always and everywhere illegitimate.",

    "What is Dietrich Bonhoeffer's concept of 'cheap grace,' and why did he consider it dangerous?":
        "Bonhoeffer wrote from a Nazi prison that 'cheap grace is grace without discipleship, grace without the cross.' It uses God's forgiveness to avoid costly obedience. Real grace, he argued, demands everything -- as his own martyrdom proved.",

    "In what way did the Protestant Reformation democratize access to religious knowledge?":
        "By translating the Bible into vernacular languages and insisting every believer could read it, the Reformation shattered the clergy's monopoly on religious knowledge. Literacy itself became a spiritual imperative, fueling education movements across Protestant Europe.",

    "What is 'liberation theology,' and what was the Vatican's concern about it?":
        "Liberation theology reads the Gospel as a mandate for structural justice, especially for the poor. The Vatican worried it adopted Marxist class-struggle analysis, substituting political revolution for spiritual transformation and reducing Christ to a social revolutionary.",

    "What is the theological concept of 'kenosis' and what does it reveal about God's relationship to power?":
        "Kenosis (Philippians 2) describes God 'emptying himself' of divine privileges in the incarnation. It reveals that divine love expresses itself not through domination but through self-giving vulnerability -- the most radical inversion of power in all theology.",

    "What did the Reformation doctrine of the 'two kingdoms' (Luther) teach about the relationship between church and civil authority?":
        "Luther's two-kingdom doctrine assigns church and state different tools and domains. The church governs through Word and gospel; the state through law and the sword. Neither should usurp the other's role -- a principle that anticipated modern church-state separation.",

    "What was the theological argument of John Calvin for the right to resist tyrannical government?":
        "Calvin argued that 'inferior magistrates' (lesser rulers) have a duty to resist tyrants on behalf of the people. Absolute obedience to a wicked ruler is idolatry -- putting a human authority in God's place. This doctrine influenced the American and French revolutions.",

    "What is the theological basis of the Golden Rule ('Do unto others as you would have them do unto you'), and how does it appear across religious traditions?":
        "Versions of the Golden Rule appear in virtually every major religious tradition -- Confucianism, Judaism, Islam, Buddhism, and Christianity. Its universality suggests a moral intuition built into human nature itself, transcending cultural boundaries.",

    "What did the Council of Trent's response to the Reformation reveal about the theological stakes of the dispute over authority?":
        "By affirming that tradition and scripture together constitute authority, Trent drew a clear line: the Catholic Church claims interpretive authority over scripture, while Protestants claim scripture has authority over the church. This fundamental disagreement about where truth resides defines the divide to this day.",

    "What was the significance of the printing press for the Protestant Reformation's theological message?":
        "The printing press was the Reformation's killer app. Luther's 95 Theses spread across Europe in weeks; vernacular Bibles reached ordinary homes for the first time. Without Gutenberg, there would have been no Luther -- the medium enabled the message.",

    "What is 'fideism' in theology, and what is the main criticism of it?":
        "Fideism holds that faith is independent of and superior to reason. The criticism: if faith needs no rational support, then any belief held sincerely is equally valid. Without some role for reason, there's no way to distinguish genuine faith from delusion.",

    "What is the theological concept of 'discernment' in Christian spiritual practice?":
        "Discernment is the practice of evaluating whether thoughts and impulses come from God, from oneself, or from harmful influences. It requires both rational analysis and spiritual attentiveness -- the mind and heart working together to navigate complex moral terrain.",

    "What is the theological concept of 'original blessing' proposed by Matthew Fox as an alternative to original sin?":
        "Fox argued that Genesis 1 declares creation 'very good' -- original blessing precedes original sin. He proposed that Christian theology should begin with creation's goodness rather than humanity's fallenness, shifting emphasis from guilt to gratitude.",

    "What is the concept of 'solidarity' in Catholic Social Teaching, and how does it ground obligations to distant strangers?":
        "Solidarity teaches that all humans share a common humanity that creates real moral obligations -- even to strangers on the other side of the world. It's not optional sentiment but a structural virtue requiring institutions that serve the global common good.",

    "What is the theological concept of 'justification by faith' in Paul's Letter to the Romans, and what were its historical consequences?":
        "Paul's teaching that God declares sinners righteous through faith in Christ -- not through keeping the law -- became the theological dynamite of the Reformation. Luther called Romans 'the chief part of the New Testament and the purest gospel.'",

    "What is the meaning of the Greek word 'euangelion' (gospel as good news), and what made it genuinely new in the ancient world?":
        "In the Roman world, 'euangelion' announced imperial victories or the emperor's birthday. Christians co-opted the word for the announcement that all people -- regardless of ethnicity or status -- can be reconciled to God. The universality and gratuity of this 'good news' was genuinely unprecedented.",

    "What is the difference between the Eastern Orthodox and Protestant concepts of grace?":
        "In Orthodoxy, grace is God's divine energies actually transforming the believer toward theosis (becoming like God). In Protestant theology, grace is primarily God's forensic declaration of forgiveness. The difference: transformation versus declaration, process versus event.",

    "What does the Hebrew Bible's concept of 'tzedakah' reveal about the theology of poverty and obligation?":
        "Tzedakah is not charity (voluntary generosity) but justice (obligatory righteousness). The poor have a right to a share of others' wealth because ultimately all things belong to God. Giving is not optional kindness -- it's required justice.",

    "What is the concept of 'common grace' in Reformed theology, and why does it matter for how Christians engage with non-Christians?":
        "Common grace teaches that God restrains evil and distributes gifts of truth, beauty, and justice among all people -- not just believers. This means Christians can genuinely appreciate and learn from non-Christian art, science, philosophy, and culture.",

    "What did the Anabaptists' insistence on voluntary church membership (believers' baptism) imply about the nature of religious faith?":
        "By rejecting infant baptism, Anabaptists declared that faith must be a conscious, personal choice. A baby can't choose to believe -- so baptizing infants turns church membership into a political identity rather than a spiritual commitment.",

    "How did the covenant concept in Reformed theology ground the idea that political authority is conditional, not absolute?":
        "Just as God's covenant with Israel could be broken by unfaithfulness, rulers who violate their covenant obligations to God and the people forfeit their legitimate authority. This theology of conditional authority directly influenced the American Declaration of Independence.",

    "What did early Christian theologian Tertullian mean when he asked 'What has Athens to do with Jerusalem?'":
        "Tertullian questioned whether Christian faith needs Greek philosophy. His answer: no. Divine revelation is sufficient, and human philosophy may corrupt pure faith. This tension between faith and reason runs through all of Christian intellectual history.",

    "What is the significance of Augustine's statement 'Our heart is restless until it rests in Thee' for understanding human nature?":
        "Augustine's famous line from the Confessions implies that humans have an innate longing for God that no worldly achievement can satisfy. It suggests that the restlessness driving all human striving is ultimately a hunger for the divine.",

    "What is the Barmen Declaration (1934) and why is it theologically significant?":
        "Written primarily by Karl Barth, the Barmen Declaration was the Confessing Church's rejection of Nazi ideology as a false gospel. It affirmed that Jesus Christ -- not the Fuhrer, not the nation, not any ideology -- is the one Word of God whom Christians must hear and obey.",

    "What does the theological concept of 'lament' in the Psalms reveal about honest faith?":
        "The Psalms of lament show that complaining to God is an act of faith, not faithlessness. Bringing your grief, anger, and confusion directly to God presupposes that God is real, present, and able to act. Lament is the prayer of those who take God seriously.",
}


def main():
    base = os.path.dirname(os.path.abspath(__file__))

    for fname, ctx_map in [
        ("questions/economics.json", ECON_CONTEXTS),
        ("questions/theology.json", THEO_CONTEXTS),
    ]:
        path = os.path.join(base, fname)
        with open(path, "r", encoding="utf-8") as f:
            questions = json.load(f)

        added = 0
        missing = 0
        for q in questions:
            if "context" not in q:
                text = q["question"]
                if text in ctx_map:
                    q["context"] = ctx_map[text]
                    added += 1
                else:
                    missing += 1
                    print(f"  WARNING: No context for: {text[:80]}...")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)

        print(f"{fname}: added {added} contexts, {missing} missing")


if __name__ == "__main__":
    main()
