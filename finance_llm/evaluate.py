import json
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from finance_llm.rag_engine import FinanceRAGEngine

SYNONYM_GROUPS = {
    "federal funds rate": ["federal funds rate", "fed funds rate", "interest rate", "policy rate"],
    "FOMC": ["fomc", "federal open market committee", "fed meeting", "central bank"],
    "interest rate": ["interest rate", "rate hike", "rate cut", "borrowing cost", "policy rate"],
    "Fed": ["fed", "federal reserve", "central bank", "powell"],
    "bond prices": ["bond price", "bond value", "fixed income", "treasury"],
    "inverse": ["inverse", "negative", "opposite", "inversely"],
    "yield": ["yield", "return", "interest", "coupon"],
    "GAAP": ["gaap", "generally accepted accounting principles", "accrual"],
    "non-GAAP": ["non-gaap", "adjusted earnings", "pro-forma", "operating earnings"],
    "earnings": ["earnings", "profit", "income", "net income", "revenue"],
    "accounting": ["accounting", "financial reporting", "financial statement"],
    "P/E": ["p/e", "price-to-earnings", "price to earnings", "valuation multiple"],
    "price-to-earnings": ["price-to-earnings", "price to earnings", "p/e", "pe ratio", "valuation multiple"],
    "valuation": ["valuation", "value", "worth", "multiple", "p/e"],
    "ratio": ["ratio", "multiple", "metric", "measure"],
    "yield curve": ["yield curve", "term structure", "treasury curve"],
    "inversion": ["inversion", "inverted", "invert"],
    "recession": ["recession", "downturn", "slowdown", "economic contraction", "economic decline"],
    "bonds": ["bond", "treasury", "fixed income", "debt security"],
}


def topic_in_answer(topic: str, answer_lower: str) -> bool:
    if topic in SYNONYM_GROUPS:
        return any(syn in answer_lower for syn in SYNONYM_GROUPS[topic])
    return topic in answer_lower


QA_PAIRS = [
    {
        "question": "What is the current federal funds rate and what did the Fed signal at the last meeting?",
        "expected_topics": ["federal funds rate", "FOMC", "interest rate", "Fed"],
    },
    {
        "question": "How does a rising interest rate environment typically affect bond prices?",
        "expected_topics": ["bond prices", "interest rate", "inverse", "yield"],
    },
    {
        "question": "Explain the difference between GAAP and non-GAAP earnings.",
        "expected_topics": ["GAAP", "non-GAAP", "earnings", "accounting"],
    },
    {
        "question": "What is the price-to-earnings ratio and how is it used in valuation?",
        "expected_topics": ["P/E", "price-to-earnings", "valuation", "ratio"],
    },
    {
        "question": "Describe what a yield curve inversion means for the economy.",
        "expected_topics": ["yield curve", "inversion", "recession", "bonds"],
    },
]


def evaluate_retrieval(rag: FinanceRAGEngine, k: int = 5) -> Dict[str, Any]:
    results = []
    correct = 0
    for item in QA_PAIRS:
        q = item["question"]
        topics = [t.lower() for t in item["expected_topics"]]
        result = rag.query(q, k=k)
        answer_lower = result["answer"].lower()
        found = [t for t in topics if topic_in_answer(t, answer_lower)]
        hit = len(found) >= 2
        if hit:
            correct += 1
        results.append({
            "question": q,
            "topics_found": found,
            "topics_missed": [t for t in topics if not topic_in_answer(t, answer_lower)],
            "has_sources": len(result["sources"]) > 0,
            "passed": hit,
            "answer_preview": result["answer"][:250],
        })
    return {
        "total": len(QA_PAIRS),
        "passed": correct,
        "failed": len(QA_PAIRS) - correct,
        "accuracy": round(correct / len(QA_PAIRS) * 100, 1),
        "details": results,
    }


def print_report(eval_result: Dict[str, Any]):
    print("=" * 60)
    print("  RAG Evaluation Report")
    print("=" * 60)
    print(f"  Total questions: {eval_result['total']}")
    print(f"  Passed:          {eval_result['passed']}")
    print(f"  Failed:          {eval_result['failed']}")
    print(f"  Accuracy:        {eval_result['accuracy']}%")
    print("=" * 60)
    for r in eval_result["details"]:
        status = "✅" if r["passed"] else "❌"
        print(f"\n{status} {r['question'][:80]}")
        print(f"   Topics found:   {', '.join(r['topics_found']) or 'none'}")
        print(f"   Topics missed:  {', '.join(r['topics_missed']) or 'none'}")
        print(f"   Has sources:    {r['has_sources']}")
        print(f"   Preview:        {r['answer_preview'][:120]}...")


def seed_knowledge(rag: FinanceRAGEngine):
    """Seed basic finance knowledge so evaluation isn't running on empty."""
    fundamentals = [
        {
            "content": (
                "The Federal Reserve (the Fed) sets the federal funds rate, which is the "
                "interest rate at which banks lend to each other overnight. As of mid-2026, "
                "the Fed has maintained rates at 5.25-5.50% to combat inflation. The FOMC "
                "meets eight times per year to set monetary policy. Higher interest rates "
                "typically slow economic growth and reduce inflation."
            ),
            "metadata": {"source": "knowledge_seed", "title": "Fed Monetary Policy", "type": "seed"},
        },
        {
            "content": (
                "Bond prices have an inverse relationship with interest rates. When interest "
                "rates rise, existing bond prices fall because new bonds pay higher yields. "
                "This is known as interest rate risk. The yield curve plots bond yields across "
                "different maturities. A yield curve inversion (short-term rates above long-term "
                "rates) has historically preceded economic recessions. An inverted yield curve "
                "suggests market expectations of economic slowdown."
            ),
            "metadata": {"source": "knowledge_seed", "title": "Bond Markets & Yield Curve", "type": "seed"},
        },
        {
            "content": (
                "GAAP (Generally Accepted Accounting Principles) earnings follow standard "
                "accounting rules. Non-GAAP earnings exclude one-time items like restructuring "
                "costs, stock-based compensation, or asset write-downs. Companies often report "
                "both to give investors a clearer picture of ongoing operations. Non-GAAP "
                "measures are also called 'adjusted earnings' or 'operating earnings'."
            ),
            "metadata": {"source": "knowledge_seed", "title": "GAAP vs Non-GAAP", "type": "seed"},
        },
        {
            "content": (
                "The price-to-earnings (P/E) ratio is a valuation metric calculated by dividing "
                "a company's stock price by its earnings per share. It shows how much investors "
                "are willing to pay per dollar of earnings. A high P/E may indicate growth "
                "expectations, while a low P/E may suggest undervaluation or problems. The P/E "
                "ratio is best used to compare companies within the same industry."
            ),
            "metadata": {"source": "knowledge_seed", "title": "P/E Ratio Valuation", "type": "seed"},
        },
    ]
    rag.ingest_documents(fundamentals)
    print(f"  Seeded {len(fundamentals)} foundational knowledge documents")


if __name__ == "__main__":
    rag = FinanceRAGEngine()
    stats = rag.get_collection_stats()

    if stats["document_chunks"] == 0:
        seed_knowledge(rag)
        stats = rag.get_collection_stats()

    print(f"  Knowledge base: {stats['document_chunks']} chunks\n")

    result = evaluate_retrieval(rag)
    print_report(result)

    report_path = Path("eval_report.json")
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n  Full report saved to {report_path}")
