import json
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from finance_llm.rag_engine import FinanceRAGEngine

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
        found = [t for t in topics if t in answer_lower]
        hit = len(found) >= 2
        if hit:
            correct += 1
        results.append({
            "question": q,
            "topics_found": found,
            "topics_missed": [t for t in topics if t not in answer_lower],
            "has_sources": len(result["sources"]) > 0,
            "passed": hit,
            "answer_preview": result["answer"][:200],
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
    print(f"  RAG Evaluation Report")
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


if __name__ == "__main__":
    rag = FinanceRAGEngine()
    stats = rag.get_collection_stats()
    print(f"Knowledge base: {stats['document_chunks']} chunks\n")

    result = evaluate_retrieval(rag)
    print_report(result)

    report_path = Path("eval_report.json")
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nFull report saved to {report_path}")
