"""
agents/regulatory.py

Regulatory Agent — Law & Statute Reasoner
Identifies relevant coverage mandates (ACA, ERISA, state statutes).

Strategy (in order):
1. pgvector semantic search using local sentence-transformer embeddings
2. PostgreSQL keyword search fallback
3. In-memory JSON law library keyword search
4. Ollama LLM fallback (generates legal points from built-in knowledge)
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── Local embedding helper ─────────────────────────────────────────────────────

_embedding_model = None

def _get_embedding_model():
    """
    Lazy-load the local sentence-transformer model.
    Cached after first load — no reload on subsequent calls.
    """
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        model_path = os.path.join(
            os.path.dirname(__file__), "..", "models", "local-embedder"
        )
        model_path = os.path.abspath(model_path)

        if os.path.exists(model_path):
            logger.info(f"Loading local embedding model from {model_path}")
            _embedding_model = SentenceTransformer(model_path)
        else:
            # Fallback: load from HuggingFace cache (already downloaded)
            logger.warning(
                f"Local model not found at {model_path}. "
                "Loading all-MiniLM-L6-v2 from cache."
            )
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    return _embedding_model


def embed_query(query: str) -> Optional[list]:
    """
    Embed a query string using the local sentence-transformer model.
    Returns list of floats or None on failure.
    """
    try:
        model = _get_embedding_model()
        embedding = model.encode(query, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        logger.warning(f"Local embedding failed: {e}")
        return None


# ── Statute retrieval ──────────────────────────────────────────────────────────

def retrieve_relevant_statutes(
    query: str,
    top_k: int = 5,
    postgres_url: Optional[str] = None,
) -> list:
    """
    Retrieve relevant statutes for a query.

    Strategy:
    1. pgvector semantic search (local embeddings — no Gemini)
    2. PostgreSQL keyword search fallback
    3. In-memory JSON law library keyword search
    """
    postgres_url = postgres_url or os.getenv("POSTGRES_URL")

    # ── Strategy 1 & 2: PostgreSQL ────────────────────────────────────────
    if postgres_url:
        try:
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
                    logger.info("Using pgvector semantic search (local embeddings).")
                    results = search_by_embedding(conn, query_embedding, top_k=top_k)
                    conn.close()
                    if results:
                        return results
                    logger.warning("pgvector returned 0 results — trying keyword search.")
                else:
                    logger.warning("Embedding failed — trying keyword search.")
            else:
                logger.info("pgvector not available — using keyword search.")

            logger.info("Using PostgreSQL keyword search.")
            results = search_by_keyword(conn, query, top_k=top_k)
            conn.close()
            if results:
                return results

        except ImportError:
            logger.warning("psycopg2 not installed — skipping DB search.")
        except Exception as e:
            logger.warning(f"DB search failed: {e} — falling back to in-memory library.")

    # ── Strategy 3: In-memory JSON law library ────────────────────────────
    logger.info("Using in-memory JSON law library.")
    return _search_law_library(query, top_k=top_k)


def _search_law_library(query: str, top_k: int = 5) -> list:
    """
    Search the local JSON law library using keyword matching.
    Offline fallback — no DB, no LLM needed.
    """
    library_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "knowledge", "law_library.json")
    )

    statutes = []
    try:
        with open(library_path, "r") as f:
            law_library = json.load(f)
        statutes = (
            law_library if isinstance(law_library, list)
            else law_library.get("statutes", [])
        )
    except FileNotFoundError:
        logger.warning(f"Law library not found at {library_path}. Using built-in stubs.")
        statutes = _builtin_statute_stubs()
    except Exception as e:
        logger.error(f"Failed to load law library: {e}. Using built-in stubs.")
        statutes = _builtin_statute_stubs()

    # Score by keyword overlap
    query_words = set(query.lower().split())
    scored = []
    for statute in statutes:
        text = (
            statute.get("statute_text", "") + " " +
            statute.get("statute_name", "")
        ).lower()
        score = sum(1 for word in query_words if word in text)
        if score > 0:
            scored.append((score, statute))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:top_k]]


def _builtin_statute_stubs() -> list:
    """Hard-coded stubs — last resort when no file and no DB."""
    return [
        {
            "statute_name": "ACA §2713 — Preventive Care Coverage",
            "statute_text": (
                "Requires non-grandfathered group health plans and insurers to provide "
                "coverage for preventive health services without cost-sharing, including "
                "evidence-based items or services with an A or B rating from the USPSTF."
            ),
            "jurisdiction": "federal",
            "category": "preventive_care",
        },
        {
            "statute_name": "ERISA §502(a) — Civil Enforcement",
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
                "assistance on the basis of race, color, national origin, sex, age, or disability."
            ),
            "jurisdiction": "federal",
            "category": "non_discrimination",
        },
    ]


# ── Ollama fallback reasoner ───────────────────────────────────────────────────

def _ollama_regulatory_reasoning(denial_data: dict, client) -> dict:
    """
    Use local Ollama to generate legal points when no statutes are retrieved.
    Replaces the old _gemini_regulatory_reasoning().
    """
    sys_instr = (
        "You are a legal expert in US health insurance law (ACA, ERISA, state mandates).\n"
        "Output STRICT JSON ONLY. No markdown. No explanation.\n"
        "Follow this exact format:\n"
        '{"legal_points": [{"statute": "...", "summary": "...", '
        '"jurisdiction": "federal", "category": "..."}]}'
    )

    prompt = (
        "A patient insurance claim was denied.\n"
        f"Procedure: {denial_data.get('procedure_denied', 'Unknown')}\n"
        f"Denial reason: {denial_data.get('insurer_reason_snippet', 'Unknown')}\n"
        f"Denial code: {denial_data.get('denial_code', 'Unknown')}\n\n"
        "List 3 to 5 specific federal statutes, ACA provisions, or ERISA sections "
        "that support an appeal of this denial.\n"
        "For each provide the statute name and a 1-2 sentence summary of how it applies.\n"
        "Output the JSON object now:"
    )

    raw = client.generate(
        prompt=prompt,
        system=sys_instr,
        temperature=0.1,
        max_tokens=1024,
        json_mode=True,
    )

    if not raw:
        logger.error("Ollama regulatory reasoning returned empty response.")
        return _stub_fallback()

    # Clean and parse
    try:
        return json.loads(raw)
    except Exception:
        import re
        # Try to extract JSON block
        start = raw.find("{")
        if start != -1:
            cleaned = re.sub(r",\s*([}\]])", r"\1", raw[start:])
            try:
                return json.loads(cleaned)
            except Exception:
                pass

    logger.error("Could not parse Ollama regulatory response.")
    return _stub_fallback()


def _stub_fallback() -> dict:
    """Return built-in stubs formatted as legal_points."""
    stubs = _builtin_statute_stubs()
    return {
        "legal_points": [
            {
                "statute": s["statute_name"],
                "summary": s["statute_text"][:300],
                "jurisdiction": s["jurisdiction"],
                "category": s["category"],
            }
            for s in stubs[:3]
        ],
        "retrieval_method": "builtin_stub_fallback",
    }


# ── Main agent function ────────────────────────────────────────────────────────

def run_regulatory_agent(
    denial_data: dict,
    postgres_url: Optional[str] = None,
    client=None,            # OllamaClient — used only if statute retrieval fails
) -> dict:
    """
    Run the Regulatory Agent.

    Args:
        denial_data: Structured output from the Auditor Agent (dict).
        postgres_url: Optional PostgreSQL connection string.
        client: OllamaClient instance for LLM fallback.

    Returns:
        Dict with legal_points list and supporting metadata.
    """
    procedure = denial_data.get("procedure_denied", "")
    denial_reason = denial_data.get("insurer_reason_snippet", "")
    denial_code = denial_data.get("denial_code", "")

    # Build rich query for retrieval
    query = (
        f"Insurance claim denied for: {procedure}. "
        f"Denial reason: {denial_reason}. "
        f"Denial code: {denial_code}. "
        "Find relevant federal statutes, ACA provisions, ERISA rules, "
        "and coverage mandates that support the patient appeal."
    )

    logger.info(f"[Regulatory] Querying for: {procedure}")

    # Retrieve statutes (pgvector → keyword → in-memory)
    statutes = retrieve_relevant_statutes(
        query=query,
        top_k=5,
        postgres_url=postgres_url,
    )

    # If nothing retrieved and we have a client, use Ollama
    if not statutes:
        logger.warning("[Regulatory] No statutes retrieved.")
        if client is not None:
            logger.info("[Regulatory] Using Ollama fallback reasoning.")
            return _ollama_regulatory_reasoning(denial_data, client)
        else:
            logger.warning("[Regulatory] No client available — using stub fallback.")
            return _stub_fallback()

    # Format retrieved statutes into legal_points
    legal_points = [
        {
            "statute": s.get("statute_name", "Unknown"),
            "summary": s.get("statute_text", "")[:1500],
            "jurisdiction": s.get("jurisdiction", "federal"),
            "category": s.get("category", "general"),
            "similarity_score": s.get("similarity", None),
        }
        for s in statutes
    ]

    retrieval_method = (
        "pgvector_cosine"
        if statutes and statutes[0].get("similarity") is not None
        else "in_memory_keyword"
    )

    logger.info(f"[Regulatory] Retrieved {len(legal_points)} statutes via {retrieval_method}.")

    return {
        "legal_points": legal_points,
        "retrieval_method": retrieval_method,
        "query_used": query,
        "statute_count": len(legal_points),
    }