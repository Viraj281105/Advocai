"""
tools/build_law_library.py

Builds and populates the law library for the Regulatory Agent.

UPDATED: Now also populates pgvector embeddings for all statutes on first run,
using Gemini text-embedding-004 (768 dims). Statutes without embeddings are
batch-embedded and stored. Safe to re-run — skips already-embedded rows.
"""

import os
import json
import logging
import time
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

import psycopg2

logger = logging.getLogger(__name__)

from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ── Embedding helper ───────────────────────────────────────────────────────────

def embed_statute_text(text: str) -> Optional[list[float]]:
    """
    Embed a statute text string using SentenceTransformers (MiniLM) (256 dims).

    Args:
        text: Statute text to embed.

    Returns:
        256-dim embedding vector, or None on failure.
    """
    try:
        embedding = embedding_model.encode(text)
        return embedding.tolist()
    except Exception as e:
        logger.exception("Embedding failed HARD")
        raise

# ── Law library data ───────────────────────────────────────────────────────────

BUILTIN_STATUTES = [
    {
        "statute_name": "ACA §2713 — Preventive Care Coverage",
        "statute_text": (
            "Requires non-grandfathered group health plans and health insurance issuers to "
            "provide coverage for preventive health services without cost-sharing, including "
            "evidence-based items or services with an A or B rating from the U.S. Preventive "
            "Services Task Force (USPSTF), recommended immunizations, and preventive care for "
            "infants, children, and adolescents."
        ),
        "jurisdiction": "federal",
        "category": "preventive_care",
        "source": "Affordable Care Act",
    },
    {
        "statute_name": "ACA §2719 — Internal and External Appeals",
        "statute_text": (
            "Requires group health plans and health insurance issuers to implement an effective "
            "internal appeals process for coverage determinations and claims, and to provide "
            "access to an independent external review process for adverse benefit determinations."
        ),
        "jurisdiction": "federal",
        "category": "appeals",
        "source": "Affordable Care Act",
    },
    {
        "statute_name": "ERISA §502(a) — Civil Enforcement",
        "statute_text": (
            "Authorizes participants or beneficiaries to bring civil actions to recover benefits "
            "due under the terms of a plan, to enforce rights under the plan, or to clarify "
            "rights to future benefits under the plan. Also authorizes suits against plan "
            "fiduciaries who breach their duties."
        ),
        "jurisdiction": "federal",
        "category": "claims_enforcement",
        "source": "Employee Retirement Income Security Act",
    },
    {
        "statute_name": "ERISA §503 — Claims Procedure",
        "statute_text": (
            "Requires every employee benefit plan to establish and maintain reasonable claims "
            "procedures, including notice of adverse benefit determinations and a full and fair "
            "review of denied claims. Insurers must provide specific reasons for denial and "
            "reference relevant plan provisions."
        ),
        "jurisdiction": "federal",
        "category": "claims_procedure",
        "source": "Employee Retirement Income Security Act",
    },
    {
        "statute_name": "Mental Health Parity and Addiction Equity Act (MHPAEA)",
        "statute_text": (
            "Requires that financial requirements and treatment limitations for mental health and "
            "substance use disorder benefits be no more restrictive than the predominant financial "
            "requirements and treatment limitations applied to substantially all medical/surgical "
            "benefits in a classification. Prohibits discriminatory coverage limits for mental "
            "health conditions."
        ),
        "jurisdiction": "federal",
        "category": "mental_health",
        "source": "Mental Health Parity and Addiction Equity Act of 2008",
    },
    {
        "statute_name": "ACA §1557 — Non-Discrimination in Health Programs",
        "statute_text": (
            "Prohibits discrimination in health programs and activities receiving federal "
            "financial assistance on the basis of race, color, national origin, sex, age, or "
            "disability. Applies to health insurers participating in ACA marketplaces and "
            "providers receiving federal funds."
        ),
        "jurisdiction": "federal",
        "category": "non_discrimination",
        "source": "Affordable Care Act",
    },
    {
        "statute_name": "ACA §2711 — No Lifetime or Annual Limits",
        "statute_text": (
            "Prohibits group health plans and health insurance issuers from imposing lifetime "
            "dollar limits on essential health benefits. Annual dollar limits on essential health "
            "benefits for plan years beginning on or after January 1, 2014, are also prohibited."
        ),
        "jurisdiction": "federal",
        "category": "benefit_limits",
        "source": "Affordable Care Act",
    },
    {
        "statute_name": "ACA §2712 — Prohibition on Rescissions",
        "statute_text": (
            "Prohibits group health plans and health insurance issuers from rescinding coverage "
            "of an individual, except in the case of fraud or intentional misrepresentation of "
            "material fact. Requires at least 30 days advance notice before rescinding coverage."
        ),
        "jurisdiction": "federal",
        "category": "coverage_stability",
        "source": "Affordable Care Act",
    },
    {
        "statute_name": "ERISA §701 — Portability and Nondiscrimination",
        "statute_text": (
            "Limits pre-existing condition exclusion periods to 12 months (18 months for late "
            "enrollees), requires crediting prior coverage, and prohibits discrimination based "
            "on health status factors including genetic information, disability, and prior claims."
        ),
        "jurisdiction": "federal",
        "category": "portability",
        "source": "Employee Retirement Income Security Act",
    },
    {
        "statute_name": "ACA Essential Health Benefits — 10 Categories",
        "statute_text": (
            "Health insurance plans sold in individual and small group markets must cover ten "
            "essential health benefit categories: ambulatory patient services, emergency services, "
            "hospitalization, maternity and newborn care, mental health and substance use disorder "
            "services, prescription drugs, rehabilitative and habilitative services and devices, "
            "laboratory services, preventive and wellness services, and pediatric services."
        ),
        "jurisdiction": "federal",
        "category": "essential_benefits",
        "source": "Affordable Care Act §1302",
    },
]


# ── Core build functions ───────────────────────────────────────────────────────

def build_json_library(output_path: Optional[str] = None) -> str:
    """
    Write the built-in statute list to a JSON file.

    Args:
        output_path: Path to write law_library.json. Defaults to data/knowledge/.

    Returns:
        Absolute path to the written file.
    """
    if output_path is None:
        output_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "data", "knowledge", "law_library.json")
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump({"statutes": BUILTIN_STATUTES}, f, indent=2)

    logger.info(f"Law library written to {output_path} ({len(BUILTIN_STATUTES)} statutes)")
    return output_path


def seed_statutes_to_postgres(conn) -> int:
    """
    Insert built-in statutes into the PostgreSQL statutes table if they don't exist.

    Args:
        conn: Active psycopg2 connection.

    Returns:
        Number of statutes inserted.
    """


    inserted = 0
    try:
        with conn.cursor() as cur:
            for statute in BUILTIN_STATUTES:
                cur.execute(
                    """
                    INSERT INTO statutes (statute_name, statute_text, jurisdiction, category, source)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (statute_name) DO NOTHING
                    RETURNING id
                    """,
                    (
                        statute["statute_name"],
                        statute["statute_text"],
                        statute["jurisdiction"],
                        statute["category"],
                        statute.get("source", ""),
                    )
                )
                if cur.fetchone():
                    inserted += 1
        conn.commit()
        logger.info(f"Seeded {inserted} new statutes to PostgreSQL.")
    except Exception as e:
        logger.error(f"Failed to seed statutes: {e}")
        conn.rollback()

    return inserted


def populate_embeddings(
    conn,
    batch_size: int = 10,
    delay_seconds: float = 0.5
) -> int:
    """
    Embed all statutes that don't yet have an embedding vector.

    Fetches statutes with NULL embedding, generates embeddings via Gemini,
    and stores them back using pgvector. Safe to re-run; skips already-embedded rows.

    Args:
        conn: Active psycopg2 connection with pgvector enabled.
        batch_size: How many statutes to embed per batch before committing.
        delay_seconds: Seconds to wait between Gemini API calls (rate limiting).

    Returns:
        Number of statutes successfully embedded.
    """
    from storage.postgres.embeddings import (
        get_statutes_without_embeddings,
        store_embedding,
        is_pgvector_available,
    )

    if not is_pgvector_available(conn):
        logger.warning(
            "pgvector extension not available. Run migration 003_add_embeddings.sql first. "
            "Skipping embedding population."
        )
        return 0

    statutes = get_statutes_without_embeddings(conn)
    if not statutes:
        logger.info("All statutes already have embeddings. Nothing to do.")
        return 0

    logger.info(f"Embedding {len(statutes)} statutes using SentenceTransformers (MiniLM)...")
    embedded_count = 0

    for i, statute in enumerate(statutes):
        statute_id = statute["id"]
        # Combine name + text for richer embedding context
        content = f"{statute['statute_name']}\n\n{statute['statute_text']}"

        embedding = embed_statute_text(content)
        if embedding:
            success = store_embedding(conn, statute_id, embedding)
            if success:
                embedded_count += 1
                if (i + 1) % batch_size == 0:
                    logger.info(f"  Embedded {i + 1}/{len(statutes)} statutes...")
        else:
            logger.warning(f"  Skipping statute {statute_id} — embedding failed.")

        # Rate limit: avoid hammering the Gemini API
        if delay_seconds > 0 and i < len(statutes) - 1:
            time.sleep(delay_seconds)

    logger.info(f"Embedding complete. {embedded_count}/{len(statutes)} statutes embedded.")
    return embedded_count


def build_law_library(
    postgres_url: Optional[str] = None,
    json_output_path: Optional[str] = None
) -> dict:
    """
    Main entry point for building the full law library.

    Steps:
    1. Write built-in statutes to JSON (offline fallback).
    2. If PostgreSQL URL is provided:
       a. Seed statutes to statutes table.
       b. Populate pgvector embeddings for all unembedded statutes.

    Args:
        postgres_url: Optional PostgreSQL connection string.
        json_output_path: Optional path for JSON output.

    Returns:
        Summary dict with counts and status.
    """
    result = {"json_written": False, "statutes_seeded": 0, "embeddings_populated": 0}

    # Step 1: Build JSON library
    try:
        path = build_json_library(json_output_path)
        result["json_written"] = True
        result["json_path"] = path
    except Exception as e:
        logger.error(f"Failed to write JSON library: {e}")

    # Step 2: PostgreSQL operations
    postgres_url = postgres_url or os.getenv("POSTGRES_URL")
    if not postgres_url:
        logger.info("No POSTGRES_URL — skipping PostgreSQL seed and embedding population.")
        return result

    try:
        conn = psycopg2.connect(postgres_url)

        result["statutes_seeded"] = seed_statutes_to_postgres(conn)
        result["embeddings_populated"] = populate_embeddings(conn)

        conn.close()
        logger.info("Law library build complete.")

    except Exception as e:
        logger.error(f"PostgreSQL law library operations failed: {e}")

    return result


# ── CLI entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

    postgres_url = os.getenv("POSTGRES_URL")
    result = build_law_library(postgres_url=postgres_url)

    print("\n✅ Law Library Build Summary")
    print(f"   JSON written:          {result.get('json_written')}")
    print(f"   Statutes seeded to DB: {result.get('statutes_seeded')}")
    print(f"   Embeddings populated:  {result.get('embeddings_populated')}")

    if not result.get("json_written"):
        sys.exit(1)