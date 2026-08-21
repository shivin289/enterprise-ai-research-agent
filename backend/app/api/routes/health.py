from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/debug/groq-test")
async def groq_test():
    """
    TEMPORARY diagnostic endpoint. Directly tests the Groq connection and
    returns the exact error in the HTTP response -- avoids needing to dig
    through platform logs, which are easy to truncate when copy-pasting.
    Delete this route once the underlying connection issue is resolved.
    """
    import traceback
    from app.ai.llm_client import get_llm_provider

    try:
        provider = get_llm_provider()
        result = await provider.generate_json(
            'Return JSON: {"sub_questions": ["test"]}',
            system="Respond only with the exact JSON requested.",
        )
        return {"success": True, "result": result}
    except Exception as exc:
        return {
            "success": False,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "cause_type": type(exc.__cause__).__name__ if exc.__cause__ else None,
            "cause_message": str(exc.__cause__) if exc.__cause__ else None,
            "full_traceback": traceback.format_exc(),
        }
