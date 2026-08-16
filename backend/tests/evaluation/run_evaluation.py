"""
Evaluation harness: runs the full research pipeline against every case in
test_cases.json and scores it against a handful of quality dimensions.

    python -m tests.evaluation.run_evaluation

This is what backs the "I maintain an evaluation dataset and measure
retrieval and response quality" story in the architecture doc (#20).
It exercises the REAL pipeline end to end (planner -> search -> evidence
-> synthesis), so run it with a real LLM_PROVIDER/SEARCH_PROVIDER
configured for meaningful results; against MOCK providers it mainly
validates that the pipeline doesn't crash and produces well-formed output.
"""
import asyncio
import json
import re
import uuid
from pathlib import Path

from app.db.database import SessionLocal, Base, engine
from app.models.research import ResearchSession
from app.models.user import User
from app.services.research_service import run_research_pipeline

TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"


async def evaluate_case(db, case: dict) -> dict:
    tenant_id = uuid.uuid4()
    user = User(id=uuid.uuid4(), tenant_id=tenant_id, email=f"{case['id']}@eval.local",
                password_hash="unused", role="member")
    db.add(user)
    db.commit()

    session = ResearchSession(tenant_id=tenant_id, user_id=user.id, query=case["question"], depth="standard")
    db.add(session)
    db.commit()
    db.refresh(session)

    await run_research_pipeline(db, session.id)
    db.refresh(session)

    result = {
        "id": case["id"],
        "status": session.status,
        "num_sub_questions": len(session.questions),
        "num_sources": len(session.sources),
        "has_report": session.report is not None,
        "checks": {},
    }

    result["checks"]["min_sub_questions"] = result["num_sub_questions"] >= case["expected_min_sub_questions"]
    result["checks"]["min_sources"] = result["num_sources"] >= case["expected_min_sources"]

    if case.get("must_cite") and session.report:
        result["checks"]["has_citations"] = bool(re.search(r"\[Source \d+\]", session.report.report_content))
    else:
        result["checks"]["has_citations"] = None

    if case.get("expect_conflicting_evidence"):
        any_conflicting = any(
            ev.is_conflicting for q in session.questions for ev in q.evidence_items
        )
        result["checks"]["conflicting_evidence_detected"] = any_conflicting

    result["passed"] = all(v for v in result["checks"].values() if v is not None)
    return result


async def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    cases = json.loads(TEST_CASES_PATH.read_text())
    results = []
    for case in cases:
        print(f"Running {case['id']}...")
        result = await evaluate_case(db, case)
        results.append(result)
        print(json.dumps(result, indent=2))

    db.close()

    passed = sum(1 for r in results if r["passed"])
    print(f"\n{passed}/{len(results)} evaluation cases passed.")


if __name__ == "__main__":
    asyncio.run(main())
