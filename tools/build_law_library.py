import os
import requests
import time

# --- CONFIGURATION: The "Gold Standard" Library ---
# These are direct links to the official Policy Wording PDFs.
POLICY_URLS = {
    "Star_Comprehensive_Policy.pdf": "https://irdai.gov.in/documents/37343/931203/SHAHLIP22028V072122_HEALTH2050.pdf/70aade12-d528-1155-a8b7-c03d2cfecd15?version=1.1&t=1668769970678&download=true",
    "Niva_Bupa_ReAssure_2.0.pdf": "https://transactions.nivabupa.com/pages/doc/policy_wording/ReAssure-2.0-Policy-Wording.pdf",
    "HDFC_ERGO_Optima_Restore.pdf": "https://algatesinsurance.in/resources/policy-documents/hdfc-ergo/optima-restore-policy-wordings.pdf", # Reliable mirror
    "ICICI_Lombard_iHealth.pdf": "https://www.icicilombard.com/docs/default-source/policy-wordings-product-brochure/complete-health-insurance-(ihealth)-new.pdf",
    "IRDAI_Master_Circular_2024.pdf": "https://irdai.gov.in/documents/37343/991022/%E0%A4%B8%E0%A5%8D%E0%A4%B5%E0%A4%B0%E0%A5%8D%E0%A4%B5%E0%A4%B8%E0%A5%8D%E0%A4%A5%E0%A5%8D%E0%A4%AF+%E0%A4%AC%E0%A5%80%E0%A4%AE%E0%A4%BE+%E0%A4%B5%E0%A5%8D%E0%A4%AF%E0%A4%B5%E0%A4%B8%E0%A4%AF+%E0%A4%AA%E0%A4%B0+%E0%A4%AE%E0%A4%BE%E0%A4%B8%E0%A5%8D%E0%A4%9F%E0%A4%B0+%E0%A4%AA%E0%A4%B0%E0%A4%BF%E0%A4%AA%E0%A4%A4%E0%A5%8D%E0%A4%B0-%E0%A4%85%E0%A4%82%E0%A4%97%E0%A5%8D%E0%A4%B0%E0%A5%87%E0%A4%9C%E0%A5%80+_+Master+Circular+on+Health+Insurance+Business+-English.pdf/08a32828-dc1d-116f-0549-6db86d448651?version=1.0&t=1719833433399"
}

# The "Ultimate Truth" Statutes File Content
STATUTES_CONTENT = """# INDIAN LEGAL KNOWLEDGE BASE (IRDAI & CONSUMER PROTECTION)

## 1. CLAIM SETTLEMENT TIMELINES (IRDAI Reg 2016)
**Regulation 27 (Settlement of Claims):**
- An insurer must settle or reject a claim within **30 days** from the date of receipt of the last necessary document.
- **Penalty Interest:** If the insurer delays payment beyond 30 days, they must pay interest at **2% above the Bank Rate** (set by RBI).

## 2. MORATORIUM PERIOD (The "Incontestable" Clause)
**Master Circular on Health Insurance 2024:**
- The Moratorium Period is **60 months (5 Years)**.
- **Rule:** After 60 months of continuous coverage, an insurer **cannot** contest a claim on grounds of "Non-Disclosure" or "Misrepresentation" (except for proven fraud).

## 3. PRE-EXISTING DISEASES (PED)
**IRDAI Standardization of Exclusions (Code Excl01):**
- Pre-Existing Diseases can only be excluded for a maximum of **48 months** (4 years).
- **Definition:** A PED is any condition diagnosed or treated within 48 months *prior* to the first policy issuance.

## 4. CONSUMER PROTECTION ACT, 2019 (CPA)
**Section 2(42) - Definition of "Service":**
- Healthcare is considered a "Service." Patients are "Consumers."
- **Key Precedent:** Doctors/Hospitals are liable for "Deficiency in Service" unless the treatment was provided free of charge.

## 5. GRIEVANCE REDRESSAL (Ombudsman)
**Rule 14 (Insurance Ombudsman Rules, 2017):**
- If an insurer rejects a complaint or does not reply within **30 days**, the policyholder can approach the **Insurance Ombudsman**.
- **Condition:** The claim value must not exceed **₹30 Lakhs**.
- **Cost:** No fee for filing.
"""

def setup_directories():
    """Creates the folder structure if it doesn't exist."""
    base_path = os.path.join("data", "knowledge")
    policy_path = os.path.join(base_path, "policies")
    
    os.makedirs(policy_path, exist_ok=True)
    print(f"✅ Created directory: {policy_path}")
    return base_path, policy_path

def download_file(url, filename, folder):
    """Downloads a single file with a progress indicator."""
    filepath = os.path.join(folder, filename)
    
    if os.path.exists(filepath):
        print(f"⚠️  File already exists: {filename}")
        return

    print(f"⬇️  Downloading: {filename}...")
    try:
        # Some Indian gov sites block scripts, so we use a browser User-Agent
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Saved: {filename}")
        
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")

def create_statutes_file(folder):
    """Writes the Markdown statutes file."""
    filepath = os.path.join(folder, "statutes.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(STATUTES_CONTENT)
    print(f"✅ Generated Knowledge Base: {filepath}")

def main():
    print("--- 🏛️  INITIALIZING ADVOCAI LAW LIBRARY 🏛️  ---")
    
    # 1. Setup Folders
    knowledge_dir, policy_dir = setup_directories()
    
    # 2. Create Statutes File (The Regulatory Brain)
    create_statutes_file(knowledge_dir)
    
    # 3. Download Policies (The Auditor Brain)
    print("\n--- 📥 DOWNLOADING POLICY DOCUMENTS ---")
    for name, url in POLICY_URLS.items():
        download_file(url, name, policy_dir)
        time.sleep(1) # Be polite to the servers

    print("\n--- 🎉 SETUP COMPLETE ---")
    print(f"1. Use 'data/knowledge/statutes.md' for your Regulatory Agent.")
    print(f"2. Use 'data/knowledge/policies/*.pdf' for your Auditor Agent testing.")

if __name__ == "__main__":
    main()