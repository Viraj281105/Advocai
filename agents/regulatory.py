"""
agents/regulatory.py

Regulatory Agent — Law & Statute Reasoner
Identifies relevant coverage mandates (ACA, ERISA, state statutes).

UPDATED: Now uses pgvector semantic search (cosine similarity over Gemini embeddings)
with graceful fallback to keyword matching if pgvector is unavailable or query fails.
"""

import os
import json
import logging
from typing import Optional


logger = logging.getLogger(__name__)

# ── Gemini setup ──────────────────────────────────────────────────────────────
_gemini_configured = False

def _configure_gemini():
    global _gemini_configured
    if not _gemini_configured:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            _gemini_configured = True
        else:
            logger.warning("GEMINI_API_KEY not set — Gemini calls will fail.")


# ── Embedding helper ───────────────────────────────────────────────────────────

def embed_query(query: str) -> Optional[list[float]]:
    """
    Embed a query string using Gemini text-embedding-004 (768 dims).

    Returns:
        List of floats, or None if embedding fails.
    """
    try:
        _configure_gemini()
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"
        )
        return result["embedding"]
    except Exception as e:
        logger.warning(f"Gemini embedding failed for query: {e}")
        return None


# ── Statute retrieval (pgvector → keyword fallback) ───────────────────────────

def retrieve_relevant_statutes(
    query: str,
    top_k: int = 5,
    postgres_url: Optional[str] = None
) -> list[dict]:
    """
    Retrieve relevant statutes for a query.

    Strategy:
    1. Try pgvector semantic search (cosine similarity over Gemini embeddings).
    2. Fall back to PostgreSQL keyword search if pgvector fails or unavailable.
    3. Fall back to in-memory JSON law library if no DB connection exists.

    Args:
        query: Natural language query about the denial/procedure.
        top_k: Number of statutes to retrieve.
        postgres_url: Optional PostgreSQL connection string.

    Returns:
        List of statute dicts with statute_name, statute_text, jurisdiction, etc.
    """
    postgres_url = postgres_url or os.getenv("POSTGRES_URL")

    # ── Strategy 1: pgvector semantic search ──────────────────────────────────
    if postgres_url:
        try:
            import psycopg2
            from storage.postgres.embeddings import (
                get_connection,
                is_pgvector_available,
                search_by_embedding,
                search_by_keyword,
            )

            conn = get_connection(postgres_url)

            if is_pgvector_available(conn):
                query_embedding = embed_query(query)
                if query_embedding:
                    logger.info("Using pgvector semantic search for statute retrieval.")
                    results = search_by_embedding(conn, query_embedding, top_k=top_k)
                    conn.close()
                    if results:
                        return results
                    logger.warning("pgvector returned 0 results — falling back to keyword search.")
                else:
                    logger.warning("Embedding failed — falling back to keyword search.")
            else:
                logger.info("pgvector not available — using keyword search.")

            # ── Strategy 2: Keyword fallback ──────────────────────────────────
            logger.info("Using keyword search for statute retrieval.")
            results = search_by_keyword(conn, query, top_k=top_k)
            conn.close()
            if results:
                return results

        except ImportError:
            logger.warning("psycopg2 not installed — skipping DB statute search.")
        except Exception as e:
            logger.warning(f"DB statute search failed: {e} — falling back to in-memory library.")

    # ── Strategy 3: In-memory JSON law library (offline fallback) ─────────────
    logger.info("Using in-memory JSON law library for statute retrieval.")
    return _search_law_library(query, top_k=top_k)


def _search_law_library(query: str, top_k: int = 5) -> list[dict]:
    """
    Search the local JSON law library using simple keyword matching.
    This is the offline fallback when no database is available.

    Returns:
        List of matching statute dicts.
    """
    library_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "knowledge", "law_library.json"
    )
    library_path = os.path.abspath(library_path)

    statutes = []
    try:
        with open(library_path, "r") as f:
            law_library = json.load(f)
        statutes = law_library if isinstance(law_library, list) else law_library.get("statutes", [])
    except FileNotFoundError:
        logger.warning(f"Law library not found at {library_path}. Using built-in stubs.")
        statutes = _builtin_statute_stubs()
    except Exception as e:
        logger.error(f"Failed to load law library: {e}. Using built-in stubs.")
        statutes = _builtin_statute_stubs()

    # Simple keyword match — score by how many query words appear in statute text
    query_words = set(query.lower().split())
    scored = []
    for statute in statutes:
        text = (statute.get("statute_text", "") + " " + statute.get("statute_name", "")).lower()
        score = sum(1 for word in query_words if word in text)
        if score > 0:
            scored.append((score, statute))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:top_k]]


def _builtin_statute_stubs() -> list[dict]:
    """Minimal built-in statute stubs for when no data source is available."""
    return [
        {
            "statute_name": "ACA §2713",
            "statute_text": (
                "Requires non-grandfathered group health plans and insurers to provide "
                "coverage for preventive health services without cost-sharing, including "
                "evidence-based items or services with an A or B rating from the USPSTF."
            ),
            "jurisdiction": "federal",
            "category": "preventive_care",
        },
        {
            "statute_name": "ERISA §502(a)",
            "statute_text": (
                "Authorizes participants or beneficiaries to bring civil actions to recover "
                "benefits due under the terms of a plan, to enforce rights under the plan, "
                "or to clarify rights to future benefits under the plan."
            ),
            "jurisdiction": "federal",
            "category": "claims_enforcement",
        },
        {
            "statute_name": "ACA §2719 — Internal Appeals",
            "statute_text": (
                "Requires group health plans and health insurance issuers to implement an "
                "effective internal appeals process for coverage determinations and claims."
            ),
            "jurisdiction": "federal",
            "category": "appeals",
        },
        {
            "statute_name": "Mental Health Parity and Addiction Equity Act (MHPAEA)",
            "statute_text": (
                "Requires that financial requirements and treatment limitations for mental "
                "health and substance use disorder benefits be no more restrictive than those "
                "applied to medical/surgical benefits."
            ),
            "jurisdiction": "federal",
            "category": "mental_health",
        },
        {
            "statute_name": "ACA §1557 — Non-Discrimination",
            "statute_text": (
                "Prohibits discrimination in health programs receiving federal financial "
                "assistance on the basis of race, color, national origin, sex, age, or "
                "disability."
            ),
            "jurisdiction": "federal",
            "category": "non_discrimination",
        },
    ]


# ── Main agent function ────────────────────────────────────────────────────────

def run_regulatory_agent(
    denial_data: dict,
    postgres_url: Optional[str] = None
) -> dict:
    """
    Run the Regulatory Agent.

    Identifies relevant statutes and produces a legal compliance brief
    based on the denial data from the Auditor Agent.

    Args:
        denial_data: Structured output from the Auditor Agent.
        postgres_url: Optional PostgreSQL connection string.

    Returns:
        Dict with legal_points list and supporting metadata.
    """
    _configure_gemini()

    procedure = denial_data.get("procedure_denied", "")
    denial_reason = denial_data.get("insurer_reason_snippet", "")
    denial_code = denial_data.get("denial_code", "")

    # Build a rich query from denial context
    query = f"""
    Insurance claim denied for: {procedure}.
    Denial reason: {denial_reason}.
    Denial code: {denial_code}.
    Find relevant federal and state statutes, ACA provisions, ERISA rules,
    and coverage mandates that support the patient's appeal.
    """.strip()

    logger.info(f"Regulatory Agent querying for: {procedure}")

    # Retrieve statutes (pgvector → keyword → in-memory)
    statutes = retrieve_relevant_statutes(
        query=query,
        top_k=5,
        postgres_url=postgres_url
    )

    if not statutes:
        logger.warning("No statutes retrieved — using Gemini to reason from built-in knowledge.")
        return _gemini_regulatory_reasoning(denial_data)

    # Format results
    legal_points = []
    for statute in statutes:
        legal_points.append({
            "statute": statute.get("statute_name", "Unknown"),
            "summary": statute.get("statute_text", "")[:400],
            "jurisdiction": statute.get("jurisdiction", "federal"),
            "category": statute.get("category", "general"),
            "similarity_score": statute.get("similarity", None),
        })

    return {
        "legal_points": legal_points,
        "retrieval_method": _get_retrieval_method(statutes),
        "query_used": query,
        "statute_count": len(legal_points),
    }


def _get_retrieval_method(statutes: list[dict]) -> str:
    """Infer which retrieval method was used based on result shape."""
    if statutes and "similarity" in statutes[0] and statutes[0]["similarity"] is not None:
        return "pgvector_cosine" if statutes[0]["similarity"] > 0 else "keyword"
    return "in_memory_keyword"


def _gemini_regulatory_reasoning(denial_data: dict) -> dict:
    """
    Use Gemini to generate legal points directly when no statute DB is available.
    This is the pure-LLM fallback.
    """
    try:
        _configure_gemini()
        model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

        prompt = f"""
You are a legal expert in US health insurance law (ACA, ERISA, state mandates).

A patient's insurance claim was denied:
- Procedure: {denial_data.get('procedure_denied', 'Unknown')}
- Denial reason: {denial_data.get('insurer_reason_snippet', 'Unknown')}
- Denial code: {denial_data.get('denial_code', 'Unknown')}

List 3-5 specific federal statutes, ACA provisions, or ERISA sections that support
an appeal of this denial. For each, provide the statute name and a 1-2 sentence summary
of how it applies.

Respond ONLY with valid JSON in this format:
{{
  "legal_points": [
    {{"statute": "ACA §2713", "summary": "...", "jurisdiction": "federal", "category": "preventive_care"}}
  ]
}}
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())

    except Exception as e:
        logger.error(f"Gemini regulatory reasoning failed: {e}")
        # Return built-in stubs as last resort
        stubs = _builtin_statute_stubs()
        return {
            "legal_points": [
                {"statute": s["statute_name"], "summary": s["statute_text"][:300],
                 "jurisdiction": s["jurisdiction"], "category": s["category"]}
                for s in stubs[:3]
            ],
            "retrieval_method": "builtin_stub_fallback",
        }