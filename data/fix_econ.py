import json

data = json.load(open('data/questions/economics.json', encoding='utf-8'))

new_questions = {
    95: ("What is a current account surplus?",
         "When a country's total income from trade and investments exceeds its total payments abroad",
         ["When exports exceed imports only in goods",
          "When a country's total income from trade and investments exceeds its total payments abroad",
          "When a country has no foreign debt",
          "When government revenue exceeds spending"]),

    166: ("What is a bilateral monopoly?",
          "A market with only one seller and one buyer, such as a single employer and a single union",
          ["A monopoly owned by two partners",
           "A market with only one seller and one buyer, such as a single employer and a single union",
           "Two monopolies competing in the same market",
           "A monopoly regulated by two government agencies"]),

    202: ("What is cyclical unemployment?",
          "Unemployment caused by downturns in the business cycle when demand for goods falls",
          ["Unemployment that repeats in annual cycles",
           "Unemployment due to workers changing jobs",
           "Unemployment caused by downturns in the business cycle when demand for goods falls",
           "Unemployment resulting from skill mismatches"]),

    334: ("What is the difference between a need and a want?",
          "A need is essential for survival (food, shelter); a want is desirable but not necessary",
          ["Needs cost more than wants",
           "A need is essential for survival (food, shelter); a want is desirable but not necessary",
           "Wants are always luxuries; needs are always free",
           "There is no economic difference"]),

    347: ("What is stagflation?",
          "A combination of stagnant economic growth, high unemployment, and high inflation",
          ["High inflation with low unemployment",
           "A combination of stagnant economic growth, high unemployment, and high inflation",
           "Rapid growth that quickly collapses",
           "Deflation combined with economic growth"]),

    352: ("What is price elasticity of supply?",
          "A measure of how much the quantity supplied changes when the price changes",
          ["The relationship between price and quantity demanded",
           "A measure of how much the quantity supplied changes when the price changes",
           "How price changes affect a producer's profits",
           "The ratio of supply to demand in a market"]),

    353: ("What is cross-price elasticity of demand?",
          "A measure of how demand for one good changes when the price of another good changes",
          ["How price changes affect demand within the same product",
           "A measure of how demand for one good changes when the price of another good changes",
           "The elasticity of demand for luxury goods",
           "How consumers respond to income changes"]),

    354: ("What is a trade surplus?",
          "When a country's exports exceed its imports",
          ["When the government runs a budget surplus",
           "When a country's exports exceed its imports",
           "When foreign investment exceeds domestic spending",
           "When a country has no import tariffs"]),

    357: ("What is frictional unemployment?",
          "Short-term unemployment that occurs when workers are between jobs or searching for new work",
          ["Unemployment caused by economic recessions",
           "Short-term unemployment that occurs when workers are between jobs or searching for new work",
           "Unemployment caused by outdated skills",
           "Permanent unemployment in a depressed region"]),

    359: ("What is a prosumer?",
          "A person who both produces and consumes a product, often in digital or energy markets",
          ["A professional consumer who buys in bulk",
           "A consumer with very high purchasing power",
           "A person who both produces and consumes a product, often in digital or energy markets",
           "A business that sells directly to consumers"]),

    360: ("What is purchasing power parity (PPP)?",
          "A theory that exchange rates should adjust so identical goods cost the same across countries",
          ["The buying power of high-income earners",
           "A theory that exchange rates should adjust so identical goods cost the same across countries",
           "A measure of how inflation reduces purchasing power",
           "The ratio of exports to imports"]),

    361: ("What is a depression in economics?",
          "A severe and prolonged downturn in economic activity with very high unemployment",
          ["A recession lasting more than one quarter",
           "A severe and prolonged downturn in economic activity with very high unemployment",
           "A period of very low inflation",
           "A fall in stock market prices"]),

    363: ("What is a natural monopoly?",
          "A monopoly that arises when one firm can serve the entire market at lower cost than multiple firms",
          ["A monopoly of natural resources",
           "A monopoly that forms without government involvement",
           "A monopoly that arises when one firm can serve the entire market at lower cost than multiple firms",
           "A monopoly granted by the government"]),

    365: ("What is a non-tariff barrier?",
          "A trade restriction other than a tariff, such as quotas, regulations, or licensing requirements",
          ["A trade agreement between countries",
           "A tariff disguised as a regulation",
           "A trade restriction other than a tariff, such as quotas, regulations, or licensing requirements",
           "A subsidy to domestic producers"]),

    367: ("What is a price floor?",
          "A minimum price set by the government to prevent prices from falling too low",
          ["The lowest price consumers will pay",
           "A minimum price set by the government to prevent prices from falling too low",
           "The price at which supply equals demand",
           "A maximum price limit in essential markets"]),

    378: ("What is implicit cost?",
          "The opportunity cost of using resources the firm already owns rather than selling or renting them",
          ["Money paid to employees",
           "The opportunity cost of using resources the firm already owns rather than selling or renting them",
           "The cost of borrowing capital",
           "Taxes paid on business revenue"]),

    381: ("What is a duopoly?",
          "A market dominated by exactly two competing firms",
          ["A market with two buyers",
           "A market dominated by exactly two competing firms",
           "A joint venture between two companies",
           "When two governments control a market"]),

    382: ("What is the accelerator effect in economics?",
          "The tendency for investment to rise more than proportionally when output increases",
          ["The effect of interest rate cuts on consumption",
           "The tendency for investment to rise more than proportionally when output increases",
           "How productivity gains accelerate growth",
           "The speed at which inflation affects prices"]),

    383: ("What is income elasticity of demand?",
          "A measure of how consumer demand for a good changes as income changes",
          ["How quantity demanded responds to price",
           "A measure of how consumer demand for a good changes as income changes",
           "The price sensitivity of luxury goods only",
           "How supply responds to income changes"]),

    386: ("What is a proportional tax?",
          "A tax where everyone pays the same percentage of their income regardless of earnings",
          ["A tax that takes a higher percentage from the wealthy",
           "A tax that takes a higher percentage from low earners",
           "A tax where everyone pays the same absolute amount",
           "A tax where everyone pays the same percentage of their income regardless of earnings"]),

    388: ("What is a merit good?",
          "A good considered beneficial to society that the government subsidizes or mandates (e.g., education)",
          ["A luxury good that the market undersupplies",
           "A good considered beneficial to society that the government subsidizes or mandates (e.g., education)",
           "A good produced by government enterprises",
           "A product with no negative externalities"]),

    392: ("What is a Giffen good?",
          "An inferior good for which demand increases as price rises, violating the normal law of demand",
          ["A luxury good with high price elasticity",
           "A good whose demand rises with income",
           "An inferior good for which demand increases as price rises, violating the normal law of demand",
           "A good with perfectly inelastic demand"]),

    393: ("What is economic profit?",
          "Revenue minus total costs, including both explicit and implicit (opportunity) costs",
          ["Revenue minus only the costs paid to suppliers",
           "Revenue minus total costs, including both explicit and implicit (opportunity) costs",
           "The profit before taxes",
           "The surplus above the normal market return"]),

    396: ("What is the tragedy of the commons?",
          "The overuse of a shared resource because individuals acting in self-interest deplete it",
          ["A market failure caused by monopoly power",
           "The overuse of a shared resource because individuals acting in self-interest deplete it",
           "When government intervention causes inefficiency",
           "A public good that becomes too costly to maintain"]),

    397: ("What is a positive externality?",
          "A benefit to a third party not involved in a transaction, such as vaccination benefiting society",
          ["A harmful side effect of production",
           "A benefit to a third party not involved in a transaction, such as vaccination benefiting society",
           "A government subsidy for public goods",
           "The positive effect of tariffs on domestic producers"]),

    404: ("What is price fixing?",
          "An illegal agreement between competitors to set prices at a certain level rather than competing",
          ["When the government sets a mandatory price",
           "An illegal agreement between competitors to set prices at a certain level rather than competing",
           "The natural convergence of prices in a competitive market",
           "Setting a price equal to the cost of production"]),

    408: ("What is helicopter money?",
          "Directly distributing money to the public to stimulate spending, bypassing the banking system",
          ["Airlifting emergency supplies to disaster areas",
           "Directly distributing money to the public to stimulate spending, bypassing the banking system",
           "Central bank loans to commercial banks at zero interest",
           "Government bond purchases from the public"]),

    410: ("What is a price ceiling's main unintended consequence?",
          "Shortages, because suppliers reduce output when they cannot charge market prices",
          ["Surpluses, because consumers buy too much",
           "Shortages, because suppliers reduce output when they cannot charge market prices",
           "Inflation, because producers raise other prices",
           "Black markets grow because official prices are lower"]),

    429: ("What does the Producer Price Index (PPI) measure?",
          "The average change in prices received by domestic producers for their output",
          ["Consumer prices in retail stores",
           "The average change in prices received by domestic producers for their output",
           "The cost of living for urban workers",
           "Wholesale prices of imported goods"]),

    450: ("What is third-degree price discrimination?",
          "Charging different prices to different market segments based on their willingness to pay",
          ["Charging different prices at different times of day",
           "Offering bulk discounts to large buyers",
           "Charging different prices to different market segments based on their willingness to pay",
           "Charging different prices based on the quantity bought"]),
}

changed = 0
for idx, (q, a, c) in new_questions.items():
    data[idx]['question'] = q
    data[idx]['answer'] = a
    data[idx]['choices'] = c
    changed += 1

print(f'Changed {changed} questions')

with open('data/questions/economics.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('Saved')

# Verify
data2 = json.load(open('data/questions/economics.json', encoding='utf-8'))
seen = {}
dupes = []
for i, q in enumerate(data2):
    key = q['question'].strip().lower()
    if key in seen:
        dupes.append((seen[key]+1, i+1, q['tier'], q['question'][:60]))
    else:
        seen[key] = i

from collections import Counter
tiers = Counter(q['tier'] for q in data2)
print(f'Total: {len(data2)}, Tiers: {dict(sorted(tiers.items()))}')
print(f'Remaining dupes: {len(dupes)}')
for d in dupes:
    print(f'  {d[0]}&{d[1]} (t{d[2]}): {d[3]}')
