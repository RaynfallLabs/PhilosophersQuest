"""Audit the economics bank for entrepreneur/financial-literacy terms."""
import json
import re
from pathlib import Path

bank = json.loads(Path("data/questions/economics.json").read_text(encoding="utf-8"))

TERMS = {
    "Business basics": [
        "revenue", "profit margin", "gross profit", "net profit",
        "cash flow", "overhead", "break.?even", "unit economic",
    ],
    "Accounting": [
        "balance sheet", "income statement", "assets", "liabilities",
        "equity", "accounts receivable", "accounts payable",
        "depreciation", "amortization",
    ],
    "Funding": [
        "venture capital", "angel invest", "Series A", "Series B",
        "bootstrap", "burn rate", "runway", "valuation", "IPO",
        "initial public offering",
    ],
    "Personal banking": [
        "checking account", "savings account", "credit score", "FICO",
        "overdraft", "ATM", "wire transfer", "ACH",
    ],
    "Credit + debt": [
        "mortgage", "APR", "annual percentage rate", "principal",
        "amortiz", "auto loan", "student loan", "credit card",
        "minimum payment", "collateral",
    ],
    "Investing": [
        "compound interest", "compound return", "index fund", "ETF",
        "401k", "IRA", "Roth", "mutual fund", "bond yield",
        "stock split", "dividend", "P/E ratio", "diversification",
        "asset allocation",
    ],
    "Taxes": [
        "income tax", "FICA", "payroll tax", "capital gains",
        "tax bracket", "standard deduction", "self.?employment tax",
        "sales tax", "property tax", "estate tax",
    ],
    "Business structure": [
        "LLC", "sole proprietor", "S-?corp", "C-?corp", "partnership",
        "limited liability",
    ],
    "Insurance": [
        "insurance premium", "deductible", "health insurance",
        "liability insurance", "term life", "whole life",
    ],
    "Entrepreneurship metrics": [
        "customer acquisition", "CAC", "lifetime value", "LTV",
        "churn", "MRR", "recurring revenue", "gross margin",
    ],
    "Personal finance": [
        "emergency fund", "budget", "rule of 72", "time value of money",
    ],
    "Risk concepts": [
        "risk pool", "underwriting", "actuarial", "moral hazard",
        "adverse selection",
    ],
}

print(f"Bank size: {len(bank)} questions\n")

total_covered = 0
total_terms = 0
for category, terms in TERMS.items():
    print(f"=== {category} ===")
    for term in terms:
        total_terms += 1
        pat = re.compile(r"\b" + term + r"\b", re.IGNORECASE)
        hits = sum(
            1 for q in bank
            if pat.search(q.get("question", ""))
            or pat.search(q.get("answer", ""))
            or any(pat.search(c) for c in q.get("choices", []))
        )
        marker = "[ OK ]" if hits > 0 else "[MISS]"
        if hits > 0:
            total_covered += 1
        print(f"  {marker} {term:<32} {hits:>3} questions")
    print()

print(f"Overall coverage: {total_covered}/{total_terms} terms hit at least once")
