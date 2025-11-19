# agents/barrister.py

from google import genai
from google.genai import types
from typing import Optional
from .auditor import StructuredDenial
from .clinician import EvidenceList # Assuming you added the correct imports to main.py

def run_barrister_agent(
    client: genai.Client,
    denial_details: StructuredDenial,
    clinical_evidence: EvidenceList
) -> Optional[str]:
    """
    The Barrister Agent workflow. It synthesizes all structured inputs 
    (denial reason, policy text, and clinical evidence) into a formal appeal letter.
    """
    print("\n[Barrister Status] Assembling final appeal arguments...")

    # Format the Clinical Evidence list into a persuasive, readable bulleted list
    evidence_text = "\n".join([
        f"- **{e.article_title}:** {e.summary_of_finding} (PMID: {e.pubmed_id})"
        for e in clinical_evidence.root
    ])
    
    # Construct a comprehensive, legally-toned system instruction
    system_instruction = (
        "You are the Barrister Agent, an expert legal counsel specializing in health insurance appeals. "
        "Your task is to draft a formal, professional, and highly persuasive appeal letter. "
        "Use the supplied policy, denial, and clinical evidence to construct a factual argument "
        "demonstrating that the denied procedure meets all requirements for medical necessity. "
        "The tone must be firm, respectful, and authoritative. Do not use placeholders or brackets."
    )
    
    # Construct the final user prompt containing all inputs
    final_prompt = f"""
    Draft a Formal Appeal Letter based on the following structured data:

    --- 1. INSURER DENIAL DETAILS ---
    Denial Code: {denial_details.denial_code}
    Insurer's Reason: "{denial_details.insurer_reason_snippet}"
    Policy Clause Cited: "{denial_details.policy_clause_text}"
    Procedure Denied: {denial_details.procedure_denied}

    --- 2. CLINICAL EVIDENCE FOR APPEAL (MUST BE CITED) ---
    {evidence_text}

    Format the output clearly with:
    1. A formal address section (use placeholders like [Insurer Address]).
    2. A clear subject line referencing the patient ID and date of service.
    3. The Clinical Argument section, which integrates the evidence above.
    4. A final, definitive request to overturn the denial.
    """

    print("[Barrister Status] Sending final context to Gemini for drafting...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", # Use the fast model for generation
            contents=[
                types.Content(role="system", parts=[types.Part.from_text(system_instruction)]),
                types.Content(role="user", parts=[types.Part.from_text(final_prompt)]),
            ],
        )
        
        print("[Barrister Success] Appeal Letter Drafted.")
        return response.text
        
    except Exception as e:
        print(f"[Barrister Error] Failed to generate appeal letter: {e}")
        return None

if __name__ == '__main__':
    # Testing is done in main.py
    pass